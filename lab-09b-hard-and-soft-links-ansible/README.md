# Lab 09b: Managing Links via Ansible — `ansible.builtin.file: state=link` / `state=hard` with `force: true`

- **Series:** linux-ops-mastery — File Operations & Shell Fundamentals
- **Trilogy:** `09a` (RHCSA) → **`09b` (Ansible — you are here)** → `09c` (Verify)
- **Career arcs covered:** RHCE EX294 (`ansible.builtin.file: state=link`, `state=hard`, `force: true`), SRE (atomic release promotion via declarative symlink swap), DevOps (blue-green deployments — change `src:` and re-run), Platform (idempotent link management in roles)
- **Prerequisite:** Lab 09a (you must have completed the RHCSA hand-typed version first), Lab 00 (Ansible Control Node Setup)
- **Time Estimate:** 25–35 minutes
- **Tasks:** 2 (Task 1 = write + apply, Task 2 = idempotence + atomic promote)
- **Practice Directory (lab-wide rotation #09):** `/var/log`
- **Sandbox:** `/tmp/links-lab/`
- **Playbooks live at:** `/root/rhcsa_journal/lab-09b/playbooks/`
- **Traps rehearsed this lab:** **T09-A** (omitting `force: true` causes the task to fail when the path already exists as a regular file) · **T09-B** (using `state: hard` across filesystems — fails the same way as `ln`) · **T09-C** (using `command: ln -sfn` instead of the module — non-idempotent)

> **This lab's practice directory is: `/var/log`** — every task references it in at least two commands for read-only symlink context.

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
echo "⚠️  TRAP REMINDERS THIS LAB: T09-A T09-B T09-C"
echo "📁  PRACTICE DIR: /var/log"
echo ""
echo "🧰 Ansible toolchain check (must pass before Task 1):"
ansible --version | head -n 2
ansible -m ping localhost 2>&1 | tail -n 4
find /var/log -maxdepth 2 -type l 2>/dev/null | head -3
```

> **STOP — if `ansible --version` fails, return to Lab 00 (Ansible Control Node Setup). Do not attempt Task 1 without a working control node.**

---

## 🎯 Objective

Replace the hand-typed `ln` and `ln -s` from Lab 09a with the **idempotent declarative form** RHCE graders expect. By the end of this lab you can write a playbook that creates soft and hard links via `ansible.builtin.file`, preview with `--check --diff`, prove idempotence on re-run (`changed=0`), and perform an atomic release promotion by changing `src:` and re-applying.

---

## 🧠 Concept: `state=link` / `state=hard` with `force` Semantics

The `ansible.builtin.file` module with link states is **declarative**: you describe the desired end state and Ansible figures out what to do.

```
   state: link                         state: hard
   ┌──────────────────────┐           ┌──────────────────────┐
   │ dest: ansible-soft   │           │ dest: ansible-hard   │
   │ src:  origin path    │           │ src:  origin file    │
   │ force: true          │           │ force: true          │
   └──────────┬───────────┘           └──────────┬───────────┘
              │                                  │
         equivalent to                      equivalent to
         ln -sfn src dest                   ln -f src dest
         (with idempotence)                (same fs only)
```

| Argument | For symlink | For hard link |
|---|---|---|
| `src:` | Target path the link points at | Existing file to hard-link |
| `dest:` (or `path:`) | The link name | The new hard-link name |
| `state: link` | Symlink | — |
| `state: hard` | — | Hard link |
| `force: true` | Replace dest if it exists (file, dir, or other link) | Same |

`force: true` is what makes link tasks re-applicable: without it, if `dest` already exists as something else, the task **fails** (T09-A). With it, the module replaces. On the second run, the link already points at the correct `src:` — module detects this and returns `changed=False`.

> **The RHCE failure mode (T09-C):** Writing `ansible.builtin.command: ln -sfn ...` instead of `ansible.builtin.file: state=link`. The `command:` form is **not** idempotent — every run reports `changed=1`. Graders mark it down.

---

## 📚 Module Reference (everything for Tasks 1–2)

| Token | Meaning |
|---|---|
| `ansible.builtin.file` | FQCN of the file module — **always** use the full name on RHCE |
| `src:` | Target path (symlink) or existing file (hard link) |
| `dest:` / `path:` | Link name to create |
| `state: link` | Symbolic link — equivalent to `ln -s` |
| `state: hard` | Hard link — equivalent to `ln` (no `-s`) |
| `force: true` | Replace dest if it exists — idempotence helper |
| `register: VAR` | Capture task result into a playbook variable |
| `ansible.builtin.debug:` | Print a variable — read `.changed` and `.diff` |
| `--check --diff` | Dry run with line-level diffs |

---

## 🚦 Lab-Wide Setup — run BEFORE Task 1

```bash
sudo -i

# Sandbox — seed with a real target file
mkdir -p /tmp/links-lab
test -e /tmp/links-lab/data.txt || echo "ansible origin" | tee /tmp/links-lab/data.txt

# Playbook home (persists across reboots)
mkdir -p /root/rhcsa_journal/lab-09b/playbooks
ls -li /tmp/links-lab/
find /var/log -maxdepth 2 -type l 2>/dev/null | head -3
echo "exit was: $?"
```

> **STOP — paste output before Task 1.**

---

## Task 1 — Write the playbook, preview with `--check --diff`, then apply

**Practice directory this task:** `/var/log` (read-only symlink context), `/tmp/links-lab/` (write targets), `/root/rhcsa_journal/lab-09b/playbooks/` (playbook persists)

### 🔁 Warm-Up — commands woven into Task 1

```bash
ansible --version | head -n 2
ansible -m ping localhost                          2>&1 | tail -n 4
ls -li /tmp/links-lab/                              2>&1 | tee /tmp/links-lab/pre-task1.txt
test -d /root/rhcsa_journal/lab-09b/playbooks && echo "playbook dir OK"
find /var/log -maxdepth 2 -type l 2>/dev/null | head -3
set -o pipefail
echo "Warm-up done by $(whoami) at $(date -Is)"
echo "exit was: $?"
```

> Carry from Lab 09a: `readlink -f` is how you verify a symlink after Ansible runs — we use it in the post-apply check.

### Purpose

Write a playbook with `ansible.builtin.file: state: link` (with `src:` + `dest:`) for a soft link, plus a second task using `state: hard` for a hard link. Use `force: true` to overwrite existing files/links at the target. Preview with `--check --diff` then apply. Capture results with `register:` and inspect with `debug:`.

### 🧵 WEAVE TRACE — warm-up commands re-used in this task body

| Warm-up command | Role inside Task 1 |
|---|---|
| `ansible --version` | Confirms control node before the play |
| `ls -li /tmp/links-lab/` | Baseline inode snapshot before Ansible creates links |
| `find /var/log -type l` | Practice-dir context — real symlinks Ansible roles mimic |
| `2>&1 \| tee` | Captures playbook output to `task1/apply.txt` |
| `set -o pipefail` | Catches silent failures in the `ansible-playbook \| tee` chain |

### Main command block

Ensure we have an origin file:

```bash
test -e /tmp/links-lab/data.txt || (echo "ansible origin" | tee /tmp/links-lab/data.txt)
mkdir -p /tmp/links-lab/task1
```

Write the playbook:

```bash
tee /root/rhcsa_journal/lab-09b/playbooks/links.yml > /dev/null <<'EOF'
---
- name: Lab 09b Task 1 — create symlink and hard link via ansible.builtin.file
  hosts: localhost
  become: true
  gather_facts: false

  vars:
    origin: /tmp/links-lab/data.txt
    soft: /tmp/links-lab/ansible-soft
    hard: /tmp/links-lab/ansible-hard

  tasks:
    - name: Ensure origin file exists (idempotent guard)
      ansible.builtin.copy:
        content: "ansible origin\n"
        dest: "{{ origin }}"
        owner: root
        group: root
        mode: '0644'
        force: false

    - name: Create soft (symbolic) link
      ansible.builtin.file:
        src: "{{ origin }}"
        dest: "{{ soft }}"
        state: link
        force: true
      register: soft_result

    - name: Create hard link
      ansible.builtin.file:
        src: "{{ origin }}"
        dest: "{{ hard }}"
        state: hard
        force: true
      register: hard_result

    - name: Show results
      ansible.builtin.debug:
        msg:
          - "soft changed: {{ soft_result.changed }}"
          - "hard changed: {{ hard_result.changed }}"
EOF
```

Check-mode first:

```bash
ansible-playbook --check --diff /root/rhcsa_journal/lab-09b/playbooks/links.yml \
  2>&1 | tee /tmp/links-lab/task1/check.log
```

Apply:

```bash
ansible-playbook /root/rhcsa_journal/lab-09b/playbooks/links.yml \
  2>&1 | tee /tmp/links-lab/task1/apply.log
```

Verify with RHCSA inspection commands:

```bash
ls -li /tmp/links-lab/ansible-soft /tmp/links-lab/ansible-hard /tmp/links-lab/data.txt
readlink /tmp/links-lab/ansible-soft
readlink -f /tmp/links-lab/ansible-soft
[ "$(stat -c '%i' /tmp/links-lab/ansible-hard)" = "$(stat -c '%i' /tmp/links-lab/data.txt)" ] && echo "hard link same inode"
echo "exit was: $?"
```

### Human-readable breakdown

1. The playbook runs against `localhost` with `become: true` — standard training pattern.
2. First task ensures the origin file exists with `force: false` (won't overwrite if present).
3. `state: link` + `src:` + `dest:` + `force: true` = declarative `ln -sfn`.
4. `state: hard` + same args = declarative `ln -f` (same filesystem only — T09-B if you cross fs).
5. `register:` captures `.changed` and `.diff` for the debug task — the grader's audit trail.
6. `--check --diff` previews without changing; real run creates the links.

### Reading it left to right

```yaml
ansible.builtin.file:
  src: /tmp/links-lab/data.txt
  dest: /tmp/links-lab/ansible-soft
  state: link
  force: true
```

- `src:` — target (what the link points at)
- `dest:` — link name (the file being created)
- `state: link` — symbolic link
- `force: true` — replace if dest already exists (T09-A without this = failure)

```yaml
ansible.builtin.file:
  src: /tmp/links-lab/data.txt
  dest: /tmp/links-lab/ansible-hard
  state: hard
  force: true
```

- `state: hard` — hard link; `src:` must exist on the same filesystem

### The story

A grader: "Create `/etc/myservice/config -> /opt/myservice/etc/config` as a symlink, owned by root, idempotent." Ansible answer is exactly the `state: link` task above (paths swapped). Second run = `changed=0`. Real-world Ansible roles use `state: link` constantly — for systemd target/wants links, alternatives, and config drop-ins.

### Expected output

```text
TASK [Ensure origin file exists] ***
ok: [localhost]

TASK [Create soft (symbolic) link] ***
changed: [localhost]

TASK [Create hard link] ***
changed: [localhost]

PLAY RECAP ***
localhost : ok=4 changed=2 unreachable=0 failed=0

12350 lrwxrwxrwx. 1 root root 22 ... ansible-soft -> /tmp/links-lab/data.txt
12345 -rw-r--r--. 3 root root ... ansible-hard
12345 -rw-r--r--. 3 root root ... data.txt
/tmp/links-lab/data.txt
/tmp/links-lab/data.txt
hard link same inode
exit was: 0
```

### Switches

| Token | Meaning |
|---|---|
| `state: link` | Symbolic link — equivalent to `ln -s` |
| `state: hard` | Hard link — equivalent to `ln` |
| `force: true` | Replace existing dest — enables idempotence |
| `src:` | Target path — required for both link states |
| `dest:` | Link name — required |
| `--check --diff` | Preview without applying |
| `register: VAR` | Capture result for inspection |

### 🧠 Concept Card

|   | Concept | What it does |
|---|---|---|
|   | `ansible.builtin.file: state=link` | RHCE answer for `ln -s` |
|   | `ansible.builtin.file: state=hard` | RHCE answer for `ln` (no `-s`) |
|   | `force: true` | Replace existing dest — enables idempotence |
|   | `--check --diff` | Safety habit: always preview before applying |
|   | `register:` + `debug:` | Grader's audit trail — read `.changed` and `.diff` |
| 🪤 | **Trap Risk T09-A** | Omitting `force: true` → task fails when dest exists as regular file |
| 🪤 | **Trap Risk T09-C** | `command: ln -sfn` instead of module — non-idempotent, refused on RHCE |

### 🔁 PERSISTENCE CHECK

| What was configured | Verification command | Why it matters |
|---|---|---|
| Symlink created | `test -L /tmp/links-lab/ansible-soft && echo OK` | Confirms soft link exists |
| Symlink target | `[ "$(readlink /tmp/links-lab/ansible-soft)" = "/tmp/links-lab/data.txt" ] && echo OK` | Points at origin |
| Hard link inode | `[ "$(stat -c '%i' /tmp/links-lab/ansible-hard)" = "$(stat -c '%i' /tmp/links-lab/data.txt)" ] && echo OK` | Same inode |
| Playbook persisted | `ls /root/rhcsa_journal/lab-09b/playbooks/links.yml` | Survives reboot in `/root/` |

> **Reboot reasoning:** `/tmp/links-lab/` evaporates at reboot. The playbook in `/root/rhcsa_journal/lab-09b/playbooks/` does not — that's the reproducibility guarantee.

### Journal write — BEFORE cleanup

```bash
LAB=lab-09b
TASK=task1
JDIR="/root/rhcsa_journal/${LAB}/${TASK}"
mkdir -p "$JDIR"
cp /tmp/links-lab/task1/check.log "$JDIR/check.txt"
cp /tmp/links-lab/task1/apply.log "$JDIR/apply.txt"

cat > "$JDIR/done.txt" <<EOF
LAB:    ${LAB}
TASK:   ${TASK}
DATE:   $(date -Is)
USER:   $(whoami)@$(hostname)
STATUS: COMPLETE
playbook=/root/rhcsa_journal/lab-09b/playbooks/links.yml
soft_target=$(readlink /tmp/links-lab/ansible-soft)
hard_inode_match=$([ "$(stat -c '%i' /tmp/links-lab/ansible-hard)" = "$(stat -c '%i' /tmp/links-lab/data.txt)" ] && echo yes || echo no)
EOF

cat > "$JDIR/notes.txt" <<EOF
TOPIC:    ansible.builtin.file state=link / state=hard — first run (preview + apply)
COMMANDS: ansible-playbook --check --diff, register, debug, readlink -f
TRAPS:    T09-A rehearsed (force: true present); T09-C avoided (used module not command: ln)
MISSED:   (fill in if any ⚠️ flags)
NEXT:     task2 — idempotence proof + atomic promote via src: change
EOF

ls -la "$JDIR"
echo "exit was: $?"
```

### 🧹 Cleanup

```bash
rm -rf /tmp/links-lab/task1
ls /tmp/links-lab/
echo "exit was: $?"
```

### Troubleshoot

| Symptom | Fix |
|---|---|
| `ansible-playbook: command not found` | Return to Lab 00 |
| Task fails: dest already exists | Add `force: true` (T09-A) |
| `state: hard` fails with cross-device | Same as `ln` — use `state: link` for cross-fs (T09-B) |
| `src 'X' is not readable` | Origin file missing — check first task |
| Second run shows `changed=1` | Dest exists but mismatched — re-check `readlink` and `stat -c %i` |

> **STOP — paste PLAY RECAP from apply run and `hard_inode_match=yes` before Task 2.**

---

## Task 2 — Idempotence proof + atomic "promote new release" via `src:` change

**Practice directory this task:** `/var/log` (context), `/tmp/links-lab/` (targets)

### 🔁 Warm-Up — commands woven into Task 2

```bash
ls -li /tmp/links-lab/ansible-soft /tmp/links-lab/data.txt  2>&1 | tee /tmp/links-lab/pre-task2.txt
readlink -f /tmp/links-lab/ansible-soft
test -L /tmp/links-lab/ansible-soft && echo "symlink OK"
find /var/log -maxdepth 2 -type l 2>/dev/null | head -3
ansible --version | head -n 1
set -o pipefail
echo "Warm-up done by $(whoami) at $(date -Is)"
echo "exit was: $?"
```

> Carry from Lab 09a: `ln -sfn NEW LINK` is the shell equivalent of changing `src:` and re-running with `force: true`.

### Purpose

Re-run the Task 1 playbook for idempotence proof (`changed=0`). Then demonstrate the atomic "promote new release" pattern: create a v2 target, change `src:` in the playbook, re-run, and confirm the link points at the new target via `readlink -f`. Show the `register:` result and `.diff` field.

### 🧵 WEAVE TRACE — warm-up commands re-used in this task body

| Warm-up command | Role inside Task 2 |
|---|---|
| `readlink -f` | Baseline symlink target before promote |
| `test -L` | Confirms symlink exists before idempotence re-run |
| `2>&1 \| tee` | Captures rerun + promote output to journal |
| `ansible --version` | Control node still working before second play |

### Main command block

**Part A — Idempotence re-run:**

```bash
mkdir -p /tmp/links-lab/task2

ansible-playbook /root/rhcsa_journal/lab-09b/playbooks/links.yml \
  2>&1 | tee /tmp/links-lab/task2/rerun.log

grep -E "PLAY RECAP|changed=" /tmp/links-lab/task2/rerun.log
```

**Part B — Atomic promote (change `src:` to new release):**

```bash
# Seed v2 release target
mkdir -p /tmp/links-lab/releases/v2
echo "release v2 content" | tee /tmp/links-lab/releases/v2/data.txt

# Write promote playbook — same structure, src: points at v2
tee /root/rhcsa_journal/lab-09b/playbooks/promote.yml > /dev/null <<'EOF'
---
- name: Lab 09b Task 2 — atomic promote new release via src change
  hosts: localhost
  become: true
  gather_facts: false

  vars:
    origin: /tmp/links-lab/releases/v2/data.txt
    soft: /tmp/links-lab/ansible-soft

  tasks:
    - name: Atomically repoint symlink to v2 release
      ansible.builtin.file:
        src: "{{ origin }}"
        dest: "{{ soft }}"
        state: link
        force: true
      register: promote_result

    - name: Show promote result and diff
      ansible.builtin.debug:
        var: promote_result
EOF

ansible-playbook --check --diff /root/rhcsa_journal/lab-09b/playbooks/promote.yml \
  2>&1 | tee /tmp/links-lab/task2/promote-check.log

ansible-playbook /root/rhcsa_journal/lab-09b/playbooks/promote.yml \
  2>&1 | tee /tmp/links-lab/task2/promote-apply.log

readlink -f /tmp/links-lab/ansible-soft
grep -A5 "promote_result" /tmp/links-lab/task2/promote-apply.log | head -20
echo "exit was: $?"
```

### Human-readable breakdown

1. Re-run `links.yml` unchanged — every link task should report `ok` with `changed=false` (idempotence).
2. Create a v2 release file at a new path.
3. `promote.yml` changes only `src:` — `force: true` atomically repoints the existing symlink (equivalent to `ln -sfn`).
4. `register: promote_result` captures `.changed=true` and `.diff` showing the old vs new target.
5. `readlink -f` confirms the live symlink now resolves to v2 — the persistence guarantee for symlink-based deployments.

### Reading it left to right

- Re-run with no edits → `changed=0` on all link tasks = idempotence proof.
- Change `src:` in vars → `force: true` + `state: link` = atomic repoint.
- `promote_result.diff` — Ansible's before/after for the symlink target string.
- `readlink -f /tmp/links-lab/ansible-soft` — independent verification (don't trust Ansible alone).

### The story

Blue-green and canary deployments often boil down to: build v2, flip the `current` symlink, verify with `readlink -f`, roll back by flipping back. Ansible encodes that flip as a one-line `src:` change with `force: true`. The idempotence re-run proves your baseline play is honest; the promote play proves you can swap releases without deleting and recreating the symlink name.

### Expected output

```text
TASK [Create soft (symbolic) link] ***
ok: [localhost]                    <-- NOT changed; symlink already correct

TASK [Create hard link] ***
ok: [localhost]                    <-- NOT changed; hard link already exists

PLAY RECAP ***
localhost : ok=4 changed=0 unreachable=0 failed=0

TASK [Atomically repoint symlink to v2 release] ***
changed: [localhost]

/tmp/links-lab/releases/v2/data.txt
exit was: 0
```

### Switches

| Token | Meaning |
|---|---|
| Re-run unchanged playbook | Idempotence test — must show `changed=0` |
| Change `src:` + re-run | Atomic promote — equivalent to `ln -sfn` |
| `register: promote_result` | Capture `.changed` and `.diff` for audit |
| `readlink -f` | Independent verification of new target |

### 🧠 Concept Card

|   | Concept | What it does |
|---|---|---|
|   | Idempotence proof | Re-run must show `changed=0` — RHCE acceptance test |
|   | Atomic promote | Change `src:` + `force: true` = `ln -sfn` declaratively |
|   | `.diff` field | Ansible shows old vs new symlink target in register output |
|   | PLAY RECAP audit | `changed=0` on re-run; `changed=1` on promote = correct behavior |
| 🪤 | **Trap Risk T09-B** | `state: hard` across filesystems fails like `ln` — use `state: link` |
| 🪤 | **Trap Risk T09-C** | `command: ln -sfn` always `changed=1` — use the module |

### 🔁 PERSISTENCE CHECK

| What was configured | Verification command | Why it matters |
|---|---|---|
| Idempotence proven | `grep 'changed=0' /root/rhcsa_journal/lab-09b/task2/rerun.log` | Second run must be no-op |
| Promote succeeded | `readlink -f /tmp/links-lab/ansible-soft` | Must show v2 path |
| Playbooks survive | `ls /root/rhcsa_journal/lab-09b/playbooks/` | Both yml files in `/root/` |

> **Reboot reasoning:** After reboot, `/tmp/links-lab/` is gone but playbooks persist. Re-running `links.yml` recreates links from scratch — that's the Ansible persistence guarantee symlinks don't have on their own in `/tmp/`.

### Journal write — BEFORE cleanup

```bash
LAB=lab-09b
TASK=task2
JDIR="/root/rhcsa_journal/${LAB}/${TASK}"
mkdir -p "$JDIR"
cp /tmp/links-lab/task2/rerun.log "$JDIR/rerun.txt"
cp /tmp/links-lab/task2/promote-apply.log "$JDIR/promote-apply.txt"

cat > "$JDIR/done.txt" <<EOF
LAB:    ${LAB}
TASK:   ${TASK}
DATE:   $(date -Is)
USER:   $(whoami)@$(hostname)
STATUS: COMPLETE
idempotent_rerun_changed_0=$(grep -c 'changed=0' /tmp/links-lab/task2/rerun.log)
promoted_target=$(readlink -f /tmp/links-lab/ansible-soft)
EOF

cat > "$JDIR/notes.txt" <<EOF
TOPIC:    Idempotence proof + atomic promote via src: change
COMMANDS: ansible-playbook rerun, promote.yml, readlink -f, register .diff
TRAPS:    T09-B noted (hard link same-fs only); T09-C avoided
MISSED:   (fill in if any ⚠️ flags)
NEXT:     lab-09c — auditor seat: verify links with RHCSA inspection commands
EOF

ls -la "$JDIR"
echo "exit was: $?"
```

### 🧹 Cleanup

```bash
rm -rf /tmp/links-lab/task2
ls /tmp/links-lab/
echo "exit was: $?"
```

### Troubleshoot

| Symptom | Fix |
|---|---|
| Re-run shows `changed=1` | Module call wrong — likely `command:` wrapper (T09-C) |
| Promote shows `changed=0` but wrong target | `src:` didn't change or symlink already pointed at v2 |
| `readlink -f` still shows v1 | Promote didn't apply — re-run `promote.yml` |
| Hard link task fails on promote play | Hard links can't be repointed — only symlinks promote this way |

> **STOP — paste PLAY RECAP showing `changed=0` on rerun and `readlink -f` showing v2 before Lab 09c.**

---

## Lab 09b Checklist (2 tasks)

- [ ] Task 1 — Write `links.yml` with `state=link` + `state=hard`, `--check --diff` preview, apply, `register:`/`debug:` evidence
- [ ] Task 2 — Re-run for idempotence (`changed=0`), atomic promote via `promote.yml` + `readlink -f` verification + journal

---

## 🔗 Related Labs in the Trilogy

| Lab | Connection |
|---|---|
| **Lab 09a** — RHCSA hand-typed links | The imperative form of what `state=link` / `state=hard` do declaratively |
| **Lab 09c** — Verifying Links | The auditor seat: prove links are real using RHCSA inspection commands |
| Lab 00 — Ansible Control Node Setup | Prerequisite — without a working control node, this lab cannot start |
| Lab 11b — Removing Files via Ansible | Complementary `ansible.builtin.file` pattern with `state=absent` |

---

## 👤 Author

**Kelvin R. Tobias**
[kelvinintech.com](https://kelvinintech.com) · [GitHub](https://github.com/kelvintechnical) · [LinkedIn](https://www.linkedin.com/in/kelvin-r-tobias-211949219)
