# Lab 11b: Removing Files via Ansible — `ansible.builtin.file: state=absent`

- **Series:** linux-ops-mastery — File Operations & Shell Fundamentals
- **Trilogy:** `11a` (RHCSA) → **`11b` (Ansible — you are here)** → `11c` (Verify)
- **Career arcs covered:** RHCE EX294 (file-state idempotence), SRE (declarative cleanup as code), DevOps (CI fixture removal), Platform (host configuration management)
- **Prerequisite:** Lab 11a (you must have completed the RHCSA hand-typed version first), Lab 00 (Ansible Control Node Setup)
- **Time Estimate:** 25–35 minutes
- **Tasks:** 2 (Task 1 = write + apply, Task 2 = idempotence proof)
- **Practice Directory (rotation #11):** `/tmp`
- **Sandbox:** `/tmp/rm-ansible-lab`
- **Playbooks live at:** `/root/rhcsa_journal/lab-11b/playbooks/`
- **Traps rehearsed this lab:** **T11-C** (using `ansible.builtin.command: rm` instead of `ansible.builtin.file: state=absent`) · **T11-D** (Task 2 changed=1 means non-idempotent — the module call is wrong)

> **This lab's practice directory is: `/tmp`** — every task references it in at least two commands.

---

## 🖥️ LAB HEADER BLOCK — run this FIRST

```bash
echo "🖥️  ENV:   ${ENV:-DECLARE_ME}"
echo "💿  DISK:  $(lsblk 2>/dev/null | awk '$NF=="disk"{print "/dev/"$1}' | paste -sd, -)"
echo "🌐  NIC:   $(ip -o addr show 2>/dev/null | awk '$2!="lo"{print $2}' | sort -u | paste -sd, -)"
echo "🔐  SE:    $(getenforce 2>/dev/null || echo n/a)"
echo "📦  OS:    $(cat /etc/redhat-release 2>/dev/null || grep PRETTY_NAME /etc/os-release)"
echo "🕒  TIME:  $(date -Is)"
echo "👤  USER:  $(whoami)@$(hostname)"
echo "⚠️  TRAP REMINDERS THIS LAB: T11-C T11-D"
echo "📁  PRACTICE DIR: /tmp"
echo ""
echo "🧰 Ansible toolchain check (must pass before Task 1):"
ansible --version | head -n 2
ansible -m ping localhost 2>&1 | tail -n 4
```

> **STOP — if `ansible --version` fails, return to Lab 00 (Ansible Control Node Setup). Do not attempt Task 1 without a working control node.**

---

## 🎯 Objective

Replace the hand-typed `rm` from Lab 11a with the **idempotent declarative form** that RHCE graders expect. By the end of this lab, you can write a playbook that removes a file, run it twice, and prove the second run is `changed=0` — the canonical signal that the play is honest and the module call is correct.

---

## 🧠 Concept: `state=absent` Is Not "Run rm" — It Is "Ensure Not Present"

The `ansible.builtin.file` module with `state: absent` is **declarative**: you describe the desired end state ("this path must not exist") and Ansible figures out what to do.

```
   target state: absent
   actual state: file exists      →  Ansible removes it,   changed=1
   actual state: file missing     →  Ansible does nothing, changed=0
   actual state: directory exists →  Ansible removes tree, changed=1
   actual state: symlink exists   →  Ansible unlinks it,   changed=1
```

That property — **same end state regardless of starting state** — is what makes a play **idempotent**. A correctly-written `state=absent` task is safe to run 1, 10, or 1000 times. The first run does the work; every subsequent run is a no-op. That is the contract every RHCE grader checks.

> **The RHCE failure mode (T11-C):** Writing `ansible.builtin.command: rm /tmp/foo` instead of `ansible.builtin.file: path=/tmp/foo state=absent`. The `command:` form is **not** idempotent — every run reports `changed=1` (or fails with `rm: cannot remove: No such file`). Graders mark it down because it ignores Ansible's whole point.

---

## 📚 Module Reference (everything for Tasks 1–2)

| Token | Meaning |
|---|---|
| `ansible.builtin.file` | The FQCN of the file module — **always** use the full name on RHCE |
| `path:` | Target path (file, directory, symlink) |
| `state: absent` | Desired end state: the path must not exist |
| `state: file` | Path must be a regular file |
| `state: directory` | Path must be a directory |
| `register: VAR` | Capture the task result into a playbook variable |
| `ansible.builtin.debug:` | Print a variable so you can read what `register:` captured |
| `--check` | Dry run — show what would change without changing anything |
| `--diff` | Show line-level diffs (combined with `--check` is the standard preview) |

---

## 🚦 Lab-Wide Setup — run BEFORE Task 1

```bash
sudo -i

# Sandbox for the targets we'll remove
mkdir -p /tmp/rm-ansible-lab
cd /tmp/rm-ansible-lab

# Build fixture files the playbook will remove
touch /tmp/rm-ansible-lab/old.log
touch /tmp/rm-ansible-lab/stale.tmp
mkdir -p /tmp/rm-ansible-lab/cache/{a,b,c}
touch /tmp/rm-ansible-lab/cache/a/file1 /tmp/rm-ansible-lab/cache/b/file2

# Playbook home (persists across reboots — Section 14 of the prompt template)
mkdir -p /root/rhcsa_journal/lab-11b/playbooks
ls -la /tmp/rm-ansible-lab
find /tmp/rm-ansible-lab -type f
echo "exit was: $?"
```

> **STOP — paste output before Task 1.**

---

## Task 1 — Write the playbook, preview with `--check --diff`, then apply

**Practice directory this task:** `/tmp` · Temporary files, cleared on every reboot — the targets we are removing live in `/tmp/rm-ansible-lab/`, the playbook itself lives in `/root/rhcsa_journal/lab-11b/playbooks/` so it survives reboot.

### 🔁 Warm-Up — commands woven into Task 1

```bash
ansible --version | head -n 2
ansible -m ping localhost                          2>&1 | tail -n 4
ls /tmp/rm-ansible-lab                              2>&1 | tee /tmp/rm-ansible-lab/pre.txt
find /tmp/rm-ansible-lab -type f                    2>/dev/null | wc -l
test -d /root/rhcsa_journal/lab-11b/playbooks && echo "playbook dir OK"
set -o pipefail
echo "Warm-up done by $(whoami) at $(date -Is)"
echo "exit was: $?"
```

> Carry from Lab 11a: the `find ... | wc -l` before/after pattern is the same — we use it to **prove** Ansible removed what we asked.

### Purpose

Write a playbook that uses `ansible.builtin.file: state=absent` to remove three targets (two files + one directory tree). Run it with `--check --diff` to preview, then apply for real. Capture the result with `register:` and dump it with `debug:` so you can read exactly what Ansible saw and did.

### 🧵 WEAVE TRACE — warm-up commands re-used in this task body

| Warm-up command | Role inside Task 1 |
|---|---|
| `ansible --version` | Confirms the control node before the play — if missing, abort to Lab 00 |
| `ls /tmp/rm-ansible-lab` | Snapshot **before** the play (saved to `pre.txt`) so we can diff against post.txt |
| `find ... -type f \| wc -l` | Counts files before AND after — drops from 4 to 0 if the play worked |
| `2>&1 \| tee` | Captures the playbook output to `task1/evidence.txt` for the journal |
| `set -o pipefail` | Catches a silent failure in the `ansible-playbook | tee` chain |
| `$(date -Is)` | Stamps the journal `notes.txt` |

### Main command block

```bash
cd /tmp/rm-ansible-lab
mkdir -p /tmp/rm-ansible-lab/task1

# 1. The playbook is at /root/rhcsa_journal/lab-11b/playbooks/task1.yml
#    (See the playbook content below or open the file directly.)
ls /root/rhcsa_journal/lab-11b/playbooks/task1.yml

# 2. Preview — --check --diff shows what WOULD change without changing anything
ansible-playbook --check --diff /root/rhcsa_journal/lab-11b/playbooks/task1.yml \
  2>&1 | tee /tmp/rm-ansible-lab/task1/check.txt

# 3. Apply — first real run
ansible-playbook /root/rhcsa_journal/lab-11b/playbooks/task1.yml \
  2>&1 | tee /tmp/rm-ansible-lab/task1/apply.txt

# 4. Verify with the same find/wc pattern from Lab 11a
ls -la /tmp/rm-ansible-lab/                          2>&1 | tee /tmp/rm-ansible-lab/task1/post.txt
find /tmp/rm-ansible-lab -type f                    2>/dev/null | wc -l
echo "exit was: $?"
```

### The playbook (`task1.yml`)

```yaml
---
- name: "Lab 11b Task 1 — remove three targets idempotently"
  hosts: localhost
  connection: local
  gather_facts: false

  tasks:
    - name: "Remove the stale log, the tmp file, and the cache tree"
      ansible.builtin.file:
        path: "{{ item }}"
        state: absent
      loop:
        - /tmp/rm-ansible-lab/old.log
        - /tmp/rm-ansible-lab/stale.tmp
        - /tmp/rm-ansible-lab/cache
      register: removal_result

    - name: "Show what Ansible did (the register: pattern RHCE graders look for)"
      ansible.builtin.debug:
        var: removal_result
```

### Human-readable breakdown

1. The playbook runs against `localhost` with `connection: local` — no SSH, no remote inventory needed. This is the standard pattern for the `linux-ops-mastery` series.
2. The single task uses `ansible.builtin.file` (FQCN — note: **not** the short name `file`) with `state: absent` and a `loop:` of three paths.
3. The `register: removal_result` captures the per-loop-item result into a variable named `removal_result` that includes the `results:` list, one entry per loop item.
4. The second task uses `ansible.builtin.debug: var: removal_result` to dump the captured result, so a human (and an RHCE grader) can read exactly what changed.
5. `--check --diff` previews: shows `changed=1` per item but does not actually unlink anything. The `--diff` output shows the before/after for each path.
6. The real run does the same actions and reports `changed=1` for each path that existed and was removed.

### Reading it left to right

- `hosts: localhost` — limits the play to the control node itself.
- `connection: local` — skips SSH; runs commands as the user invoking `ansible-playbook`.
- `gather_facts: false` — speeds up the play by skipping the `setup` module; our task does not need facts.
- `ansible.builtin.file:` — FQCN form. RHCE graders penalize the bare `file:` form because it relies on collection-loading defaults that can change.
- `path: "{{ item }}"` — Jinja2 template that pulls the current value from the `loop:` list.
- `state: absent` — the desired-state declaration; idempotent by design.
- `loop: [...]` — three paths, three iterations of the same task.
- `register: removal_result` — captures `{ results: [item1_result, item2_result, item3_result] }` into the playbook scope.
- `ansible.builtin.debug: var: removal_result` — dumps the variable as YAML so you can inspect `.changed`, `.path`, `.diff`, etc.

### The story

The `register:` + `debug:` pattern is the single most under-practiced RHCE habit. Graders are not looking only at whether the file disappeared — they are reading the **playbook output** to confirm Ansible reported what you expect. A play that removes a file but reports `changed=0` (because the file was already gone) is **still a passing play** when written with `state: absent`. That is the entire point of declarative idempotence.

The `--check --diff` preview is the safety habit. Always preview before applying. On the exam, running `--check --diff` against a complex play and reading the output catches typos in paths and reveals tasks that would have skipped because of bad `when:` conditions — both common point-deduction sources.

### Expected output

```text
ansible [core 2.16.x] ...
localhost | SUCCESS => {
    "changed": false,
    "ping": "pong"
}
old.log  stale.tmp  cache
4

# --- --check --diff preview ---
PLAY [Lab 11b Task 1 — remove three targets idempotently] *********************
TASK [Remove the stale log, the tmp file, and the cache tree] *****************
changed: [localhost] => (item=/tmp/rm-ansible-lab/old.log)
changed: [localhost] => (item=/tmp/rm-ansible-lab/stale.tmp)
changed: [localhost] => (item=/tmp/rm-ansible-lab/cache)
TASK [Show what Ansible did (the register: pattern RHCE graders look for)] ****
ok: [localhost] => { ... results showing changed=true and path for each ... }
PLAY RECAP ********************************************************************
localhost                  : ok=2    changed=1    unreachable=0    failed=0

# --- apply (real run) ---
... same output as above ...

# --- post-state verification ---
total 8
drwxr-xr-x. 2 root root  6 May 27 ... .
drwxr-xr-x. 4 root root 81 May 27 ... ..
0
exit was: 0
```

### Switches

| Token | Meaning |
|---|---|
| `ansible-playbook` | The driver that reads a YAML file and executes its tasks |
| `--check` | Dry run — no actual changes; reports what would happen |
| `--diff` | Show line-level diffs for changed resources |
| `hosts: localhost` | Run against the control node itself |
| `connection: local` | Skip SSH; run as the local user |
| `gather_facts: false` | Skip the implicit `setup` module |
| `state: absent` | The desired-state declaration for `ansible.builtin.file` |
| `register: VAR` | Capture task result into a playbook variable |
| `loop: [...]` | Iterate the task over a list |

### 🧠 Concept Card

|   | Concept | What it does |
|---|---|---|
|   | FQCN (`ansible.builtin.file`) | Fully qualified collection name — required on RHCE EX294 |
|   | `state: absent` declarative | "Ensure not present" — idempotent regardless of starting state |
|   | `--check --diff` preview | Safety habit: always preview before applying |
|   | `register:` + `debug:` | The grader's audit trail — read the play's own output |
|   | `loop:` over a list | One task, many items — cleaner than three separate tasks |
|   | `hosts: localhost` + `connection: local` | The training pattern that keeps the lab focused on the module, not SSH |
| 🪤 | **Trap Risk T11-C** | Writing `ansible.builtin.command: rm` instead of `file: state=absent`. Refused on RHCE grading. |

### 🔁 PERSISTENCE CHECK

| What was configured | Verification command | Why it matters |
|---|---|---|
| Targets removed | `find /tmp/rm-ansible-lab -type f \| wc -l` | Must be `0` after the play |
| Playbook persisted | `ls /root/rhcsa_journal/lab-11b/playbooks/task1.yml` | Playbook in `/root/` survives reboot; `/tmp/` would not |
| Evidence captured | `wc -l /root/rhcsa_journal/lab-11b/task1/apply.txt` | The PLAY RECAP line ("ok=2 changed=1") is the auditable result |

> **Reboot reasoning:** The targets in `/tmp` evaporate at reboot, but the playbook in `/root/rhcsa_journal/lab-11b/playbooks/` does not. After a reboot, you could re-run `ansible-playbook .../task1.yml` and Ansible would report `changed=0` because the targets are already gone — **proof of idempotence across reboot**. We test that in Task 2.

### Journal write — BEFORE cleanup

```bash
LAB=lab-11b
TASK=task1
JDIR="/root/rhcsa_journal/${LAB}/${TASK}"
mkdir -p "$JDIR"
cp /tmp/rm-ansible-lab/task1/check.txt "$JDIR/check.txt"
cp /tmp/rm-ansible-lab/task1/apply.txt "$JDIR/apply.txt"
cp /tmp/rm-ansible-lab/task1/post.txt  "$JDIR/post.txt"

cat > "$JDIR/done.txt" <<EOF
LAB:    ${LAB}
TASK:   ${TASK}
DATE:   $(date -Is)
USER:   $(whoami)@$(hostname)
STATUS: COMPLETE
EOF

cat > "$JDIR/notes.txt" <<EOF
TOPIC:    ansible.builtin.file state=absent — first run (preview + apply)
COMMANDS: ansible-playbook --check --diff, ansible-playbook, register, debug
TRAPS:    T11-C rehearsed (we did NOT use command: rm — we used the real module)
MISSED:   (fill in if any ⚠️ flags)
NEXT:     task2 — re-run the playbook for idempotence proof (changed=0)
EOF

ls -la "$JDIR"
echo "exit was: $?"
```

### 🧹 Cleanup

```bash
# Keep the playbook AND the journal — drop the sandbox transcript only
rm -rf /tmp/rm-ansible-lab/task1
ls /tmp/rm-ansible-lab/
echo "exit was: $?"
```

### Troubleshoot

| Symptom | Fix |
|---|---|
| `ansible-playbook: command not found` | Return to Lab 00 — control node not installed |
| `Could not match supplied host pattern` | Inventory missing or wrong — check `ansible.cfg` `inventory =` line |
| Task says `changed=0` on first run | Target was already missing — that is correct idempotence, not a failure |
| `--check` reported a change but `--diff` showed nothing | Check mode for `state: absent` can't show file contents — that's normal |
| `register:` variable empty | Typo in the variable name between `register:` and `debug:` |

> **STOP — paste the PLAY RECAP line of the apply run and the final `find ... | wc -l = 0` output before Task 2.**

---

## Task 2 — The contrast: re-run for idempotence (changed=0)

**Practice directory this task:** `/tmp` · the targets are already gone from Task 1 — Task 2 is the **proof** that re-running the play does nothing.

### 🔁 Warm-Up — commands woven into Task 2

```bash
ls /tmp/rm-ansible-lab                              2>&1 | tee /tmp/rm-ansible-lab/pre-task2.txt
find /tmp/rm-ansible-lab -type f                    2>/dev/null | wc -l
test ! -f /tmp/rm-ansible-lab/old.log && echo "target1 already gone — expected"
test ! -d /tmp/rm-ansible-lab/cache && echo "target3 already gone — expected"
ansible --version | head -n 1
set -o pipefail
echo "Warm-up done by $(whoami) at $(date -Is)"
echo "exit was: $?"
```

> Carry from Task 1: the `find ... | wc -l` baseline must still be `0` — if it is not, something restored a target between tasks.

### Purpose

Re-run the **exact same playbook** from Task 1 and prove that it now reports `changed=0`. This is the contract of idempotent Ansible: applied state does not drift on re-application. If Task 2 shows `changed=1`, the module call was wrong (the most common cause is using `command:` or `shell:` instead of a real module — Trap T11-D).

### 🧵 WEAVE TRACE — warm-up commands re-used in this task body

| Warm-up command | Role inside Task 2 |
|---|---|
| `find ... \| wc -l` | Pre-condition check: must already be `0` before re-run |
| `test ! -f` / `test ! -d` | Confirms each target is gone before we re-run |
| `2>&1 \| tee` | Captures the second-run output to `task2/rerun.txt` — the **proof artifact** |
| `set -o pipefail` | Ensures the `tee` chain reports a failed `ansible-playbook` honestly |
| `$(date -Is)` | Stamps the journal `notes.txt` |
| `ansible --version` | Confirms control node still working (rules out version-skew false negatives) |

### Main command block

```bash
mkdir -p /tmp/rm-ansible-lab/task2

# 1. Re-run the SAME playbook from Task 1 — no edits
ansible-playbook /root/rhcsa_journal/lab-11b/playbooks/task2.yml \
  2>&1 | tee /tmp/rm-ansible-lab/task2/rerun.txt

# 2. Inspect the PLAY RECAP — changed=0 is the win condition
grep -E "PLAY RECAP|changed=" /tmp/rm-ansible-lab/task2/rerun.txt

# 3. Verify the targets are still absent (nothing restored them)
find /tmp/rm-ansible-lab -type f                    2>&1 | tee /tmp/rm-ansible-lab/task2/post.txt
echo "exit was: $?"
```

### The playbook (`task2.yml` — content identical to `task1.yml` except the play name)

```yaml
---
- name: "Lab 11b Task 2 — re-run for idempotence proof (changed=0 expected)"
  hosts: localhost
  connection: local
  gather_facts: false

  tasks:
    - name: "Re-assert state=absent on the same three targets"
      ansible.builtin.file:
        path: "{{ item }}"
        state: absent
      loop:
        - /tmp/rm-ansible-lab/old.log
        - /tmp/rm-ansible-lab/stale.tmp
        - /tmp/rm-ansible-lab/cache
      register: removal_result

    - name: "Show idempotence proof — every result must have changed=false"
      ansible.builtin.debug:
        msg: "Item {{ item.item }} changed={{ item.changed }}"
      loop: "{{ removal_result.results }}"
      loop_control:
        label: "{{ item.item }}"
```

### Human-readable breakdown

1. The playbook is structurally identical to `task1.yml` — same hosts, same connection, same module, same loop list. The only meaningful difference is the play name and the more useful debug message in the second task.
2. Running it produces `changed=0` for every loop item because the targets are already absent (the `state: absent` declaration sees the actual state already matches the desired state).
3. The PLAY RECAP at the end reports `changed=0`. That is the canonical idempotence proof RHCE graders look for.
4. If `changed=1` ever appears, the module call is wrong. The most common cause is using `command: rm` or `shell: rm` (T11-D) — those are imperative, not declarative, and always report `changed=1` whether they succeed, fail, or do nothing.

### Reading it left to right

- `loop: "{{ removal_result.results }}"` — Jinja expression iterating the `results:` list from the previous task's `register:`.
- `loop_control: label: "{{ item.item }}"` — the `loop_control` block shrinks the displayed task name from a giant blob to just the loop value, making the output readable.
- `item.item` — yes, that is correct. When iterating `removal_result.results`, each entry is itself a dict where the original loop value is stored under the key `item`. So `item.item` is "the original loop value of the registered item."
- `item.changed` — `true` if Ansible made a change for that item; `false` if it was already in the desired state.

### The story

Idempotence is **the** RHCE concept. Every grader knows that imperative wrappers (`command:`, `shell:`) can be passed off as "Ansible playbooks" by candidates who don't understand the difference. The way they tell the difference: they re-run your play and look at the PLAY RECAP. A correctly-written play reports `changed=0` on the second run. An imperative wrapper reports `changed=1` (or worse, fails because `rm` errored on a missing file).

The discipline is: every time you write a task, run it twice. Second run must be `changed=0`. If it's not, fix the module call before moving on.

### Expected output

```text
total 8
drwxr-xr-x. 2 root root  6 May 27 ... .
drwxr-xr-x. 4 root root 41 May 27 ... ..
0
target1 already gone — expected
target3 already gone — expected
ansible [core 2.16.x]

PLAY [Lab 11b Task 2 — re-run for idempotence proof (changed=0 expected)] ****
TASK [Re-assert state=absent on the same three targets] ***********************
ok: [localhost] => (item=/tmp/rm-ansible-lab/old.log)
ok: [localhost] => (item=/tmp/rm-ansible-lab/stale.tmp)
ok: [localhost] => (item=/tmp/rm-ansible-lab/cache)
TASK [Show idempotence proof — every result must have changed=false] *********
ok: [localhost] => (item=/tmp/rm-ansible-lab/old.log) => {
    "msg": "Item /tmp/rm-ansible-lab/old.log changed=False"
}
ok: [localhost] => (item=/tmp/rm-ansible-lab/stale.tmp) => {
    "msg": "Item /tmp/rm-ansible-lab/stale.tmp changed=False"
}
ok: [localhost] => (item=/tmp/rm-ansible-lab/cache) => {
    "msg": "Item /tmp/rm-ansible-lab/cache changed=False"
}
PLAY RECAP ********************************************************************
localhost                  : ok=2    changed=0    unreachable=0    failed=0
0
exit was: 0
```

> **The key line: `changed=0` in the PLAY RECAP.** If this number is anything other than 0 on the re-run, Task 2 has failed and the module call needs to be fixed before moving to Lab 11c.

### Switches

| Token | Meaning |
|---|---|
| `loop: "{{ var.results }}"` | Iterate over a registered task's per-item result list |
| `loop_control: label:` | Shorten the displayed task name for readable output |
| `item.item` | The original loop value when iterating a registered result list |
| `item.changed` | Per-item changed flag from the original task |
| `grep -E "PLAY RECAP\|changed="` | Extract just the audit-critical lines from a long playbook output |

### 🧠 Concept Card

|   | Concept | What it does |
|---|---|---|
|   | Idempotence proof | Re-run must show `changed=0`; that is the RHCE acceptance test |
|   | Declarative vs imperative | `file: state=absent` ≠ `command: rm`. The first re-runs cleanly; the second does not. |
|   | PLAY RECAP audit | The bottom-line metric: `ok=N changed=M failed=K`. M should be 0 on re-run. |
|   | `loop_control: label:` | Readable output for loop iterations |
|   | `item.item` indirection | When iterating a registered loop result, the original value lives at `item.item` |
| 🪤 | **Trap Risk T11-D** | If the second run shows `changed=1`, the module is wrong. Refuse to continue until fixed. |

### 🔁 PERSISTENCE CHECK

| What was configured | Verification command | Why it matters |
|---|---|---|
| Idempotence proven | `grep changed= /root/rhcsa_journal/lab-11b/task2/rerun.txt` | Must show `changed=0` in the PLAY RECAP |
| Playbooks survive reboot | `ls /root/rhcsa_journal/lab-11b/playbooks/` | Both `task1.yml` and `task2.yml` live in `/root/`, not `/tmp/` |
| Targets remain absent | `find /tmp/rm-ansible-lab -type f \| wc -l` | Must be `0` |

> **Reboot reasoning:** After a reboot, `/tmp/rm-ansible-lab` evaporates entirely — there are no targets left to remove. Running `task1.yml` again would report `changed=0` even though the directory itself is missing — because the **declaration** "ensure these paths do not exist" is satisfied. That is the deepest form of idempotence.

### Journal write — BEFORE cleanup

```bash
LAB=lab-11b
TASK=task2
JDIR="/root/rhcsa_journal/${LAB}/${TASK}"
mkdir -p "$JDIR"
cp /tmp/rm-ansible-lab/task2/rerun.txt "$JDIR/rerun.txt"
cp /tmp/rm-ansible-lab/task2/post.txt  "$JDIR/post.txt"

cat > "$JDIR/done.txt" <<EOF
LAB:    ${LAB}
TASK:   ${TASK}
DATE:   $(date -Is)
USER:   $(whoami)@$(hostname)
STATUS: COMPLETE
EOF

cat > "$JDIR/notes.txt" <<EOF
TOPIC:    Idempotence proof — re-run shows changed=0
COMMANDS: ansible-playbook (rerun), grep "PLAY RECAP\|changed=", loop_control
TRAPS:    T11-D rehearsed (we verified changed=0; if it had been 1 we would have stopped)
MISSED:   (fill in if any ⚠️ flags)
NEXT:     lab-11c — the auditor seat: prove the removals stuck with RHCSA inspection commands
EOF

ls -la "$JDIR"
echo "exit was: $?"
```

### 🧹 Cleanup

```bash
rm -rf /tmp/rm-ansible-lab
test -d /tmp/rm-ansible-lab || echo "sandbox gone — clean exit"
echo "exit was: $?"
```

### Troubleshoot

| Symptom | Fix |
|---|---|
| Re-run shows `changed=1` | Module is wrong — likely using `command:` or `shell:`. Switch to `ansible.builtin.file`. |
| Re-run fails with "No such file" | You used `command: rm` instead of `file: state=absent`. The fix: rewrite the task. |
| `loop_control: label:` not rendering | Older Ansible — upgrade `ansible-core` or remove `loop_control:` block |
| `item.item` returns `undefined` | The `register:` variable was not set in this play's scope — verify the `register:` line |
| PLAY RECAP missing from journal | `tee` failed silently; turn on `set -o pipefail` |

> **STOP — paste the PLAY RECAP line showing `changed=0` and `cat $JDIR/notes.txt` before moving on to Lab 11c.**

---

## Lab 11b Checklist (2 tasks)

- [ ] Task 1 — Write the playbook + `--check --diff` preview + apply + `register:`/`debug:` evidence
- [ ] Task 2 — Re-run for idempotence proof (`changed=0`) + journal the PLAY RECAP

---

## 🔗 Related Labs in the Trilogy

| Lab | Connection |
|---|---|
| **Lab 11a** — RHCSA hand-typed removal | The imperative form of what `state=absent` does declaratively |
| **Lab 11c** — Verifying File Removal | The auditor seat: prove the removals are real using RHCSA inspection commands |
| Lab 00 — Ansible Control Node Setup | Prerequisite — without a working control node, this lab cannot start |
| Lab 12b — Creating Nested Directories via Ansible | The complementary declarative pattern: `state: directory` |

---

## 👤 Author

**Kelvin R. Tobias**
[kelvinintech.com](https://kelvinintech.com) · [GitHub](https://github.com/kelvintechnical) · [LinkedIn](https://www.linkedin.com/in/kelvin-r-tobias-211949219)
