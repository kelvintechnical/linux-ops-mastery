# Lab 06b: SELinux Contexts via Ansible — `community.general.sefcontext` + `ansible.posix.seboolean`

- **Series:** linux-ops-mastery — File Operations & Shell Fundamentals
- **Trilogy:** `06a` (RHCSA) → **`06b` (Ansible — you are here)** → `06c` (Verify)
- **Career arcs covered:** RHCE EX294 (fcontext idempotence, `sefcontext`, `restorecon` wrapper), SRE (declarative SELinux policy as code), DevOps (web-root labeling in CI/CD), Platform (host configuration management)
- **Prerequisite:** Lab 06a (you must have completed the RHCSA hand-typed version first), Lab 00 (Ansible Control Node Setup)
- **Time Estimate:** 30–40 minutes
- **Tasks:** 2 (Task 1 = write + apply, Task 2 = idempotence proof)
- **Practice Directory (rotation #06):** `/etc` (read-only inspection of live policy context)
- **Sandbox:** `/srv/www-lab-06/`
- **Playbooks live at:** `/root/rhcsa_journal/lab-06b/playbooks/`
- **Traps rehearsed this lab:** **T06-A** (forgetting `community.general` collection — module won't resolve) · **T06-B** (using `ansible.builtin.command: chcon` instead of `community.general.sefcontext` — temporary label, not policy) · **T06-C** (forgetting `restorecon` after `sefcontext` — rule exists in policy DB but files stay mislabeled)

> **This lab's practice directory is: `/etc`** — every task references it in at least two commands (live SELinux policy inspection). The **sandbox** where we apply labels is `/srv/www-lab-06/`.

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
echo "⚠️  TRAP REMINDERS THIS LAB: T06-A T06-B T06-C"
echo "📁  PRACTICE DIR: /etc"
echo "📁  SANDBOX:      /srv/www-lab-06"
echo ""
echo "🧰 Ansible toolchain check (must pass before Task 1):"
ansible --version | head -n 2
ansible-galaxy collection list 2>/dev/null | grep -E 'community.general|ansible.posix' || echo "⚠️  collections missing — see Lab 00"
ansible -m ping localhost 2>&1 | tail -n 4
```

> **STOP — if `ansible --version` fails, return to Lab 00 (Ansible Control Node Setup). Do not attempt Task 1 without a working control node.**

---

## 🎯 Objective

Replace the hand-typed `semanage fcontext` + `restorecon` from Lab 06a with the **idempotent declarative form** that RHCE graders expect. By the end of this lab, you can write a playbook that declares an fcontext rule with `community.general.sefcontext`, applies it with `restorecon -Rv`, run it twice, and prove the second run is `changed=0` — the canonical signal that the play is honest and the module call is correct.

---

## 🧠 Concept: `sefcontext` Is Not "Run chcon" — It Is "Ensure Policy Rule Present"

The `community.general.sefcontext` module with `state: present` is **declarative**: you describe the desired end state ("this path regex must map to this SELinux type in the policy database") and Ansible figures out what to do.

```
   target state: fcontext rule present
   actual state: rule missing          →  Ansible adds rule,      changed=1
   actual state: rule already present   →  Ansible does nothing,   changed=0
   actual state: wrong type on rule     →  Ansible updates rule,   changed=1
```

That property — **same end state regardless of starting state** — is what makes a play **idempotent**. A correctly-written `sefcontext` task is safe to run 1, 10, or 1000 times. The first run does the work; every subsequent run is a no-op. That is the contract every RHCE grader checks.

> **The RHCE failure mode (T06-B):** Writing `ansible.builtin.command: chcon -t httpd_sys_content_t /srv/www-lab-06` instead of `community.general.sefcontext`. The `chcon` form is **not** permanent — it survives the current boot but is lost on relabel. Graders mark it down because it ignores Ansible's whole point and SELinux policy semantics.

> **The second failure mode (T06-C):** Declaring the fcontext rule with `sefcontext` but **never running `restorecon`**. The rule sits in the policy database but the files on disk keep their old labels. Apache still gets `Permission denied`. The fix is always: `sefcontext` → `restorecon -Rv`.

---

## 📚 Module Reference (everything for Tasks 1–2)

| Token | Meaning |
|---|---|
| `community.general.sefcontext` | The FQCN of the fcontext module — **always** use the full name on RHCE |
| `target:` | Path regex (same syntax as `semanage fcontext -a`) — e.g. `'/srv/www-lab-06(/.*)?'` |
| `setype:` | SELinux type to assign (e.g. `httpd_sys_content_t`) |
| `state: present` | Desired end state: the fcontext rule must exist |
| `state: absent` | Remove the fcontext rule (equivalent to `semanage fcontext -d`) |
| `ansible.builtin.command:` | Run a binary when no module exists — **accepted for `restorecon`** |
| `changed_when:` | Jinja expression controlling when a `command:` task reports `changed=1` |
| `register: VAR` | Capture the task result into a playbook variable |
| `ansible.builtin.debug:` | Print a variable so you can read what `register:` captured |
| `--check` | Dry run — show what would change without changing anything |
| `--diff` | Show line-level diffs (combined with `--check` is the standard preview) |
| `ansible.posix.seboolean` | Companion module for SELinux booleans (Lab 06 trilogy reference; not exercised in Tasks 1–2) |

---

## 🚦 Lab-Wide Setup — run BEFORE Task 1

```bash
sudo -i

# Confirm SELinux is enforcing (Lab 06a prerequisite)
getenforce
grep ^SELINUX= /etc/selinux/config

# Sandbox for the web content we'll label
mkdir -p /srv/www-lab-06/{html,assets}
echo '<h1>Lab 06b sandbox</h1>' > /srv/www-lab-06/html/index.html
echo 'body { margin: 0; }'       > /srv/www-lab-06/assets/style.css

# Deliberately mislabel one file so restorecon has work to do
chcon -t default_t /srv/www-lab-06/html/index.html

# Snapshot BEFORE state
ls -lZ /srv/www-lab-06/
semanage fcontext -l 2>/dev/null | grep www-lab-06 || echo "no fcontext rule yet — expected"

# Playbook home (persists across reboots — Section 14 of the prompt template)
mkdir -p /root/rhcsa_journal/lab-06b/playbooks
ls -la /srv/www-lab-06/
echo "exit was: $?"
```

> **STOP — paste output before Task 1. Confirm `index.html` shows a type other than `httpd_sys_content_t`.**

---

## Task 1 — Write the playbook, preview with `--check --diff`, then apply

**Practice directory this task:** `/etc` · Inspect live SELinux policy files. **Sandbox:** `/srv/www-lab-06/` — the targets we label live here; the playbook itself lives in `/root/rhcsa_journal/lab-06b/playbooks/` so it survives reboot.

### 🔁 Warm-Up — commands woven into Task 1

```bash
ansible --version | head -n 2
ansible-galaxy collection list 2>/dev/null | grep community.general
ansible -m ping localhost                          2>&1 | tail -n 4
ls -Z /srv/www-lab-06/                              2>&1 | tee /srv/www-lab-06/pre.txt
grep -r httpd_sys_content /etc/selinux/targeted/contexts/files/ 2>/dev/null | head -n 3
test -d /root/rhcsa_journal/lab-06b/playbooks && echo "playbook dir OK"
set -o pipefail
echo "Warm-up done by $(whoami) at $(date -Is)"
echo "exit was: $?"
```

> Carry from Lab 06a: the `ls -lZ` before/after pattern is the same — we use it to **prove** Ansible relabeled what we asked.

### Purpose

Write a playbook that uses `community.general.sefcontext` to declare the fcontext rule for `/srv/www-lab-06(/.*)?` → `httpd_sys_content_t`, then applies it with `restorecon -Rv`. Run it with `--check --diff` to preview, then apply for real. Capture the result with `register:` and dump it with `debug:` so you can read exactly what Ansible saw and did.

### 🧵 WEAVE TRACE — warm-up commands re-used in this task body

| Warm-up command | Role inside Task 1 |
|---|---|
| `ansible --version` | Confirms the control node before the play — if missing, abort to Lab 00 |
| `ansible-galaxy collection list \| grep community.general` | Trap T06-A gate — module won't resolve without this collection |
| `ls -Z /srv/www-lab-06/` | Snapshot **before** the play (saved to `pre.txt`) so we can diff against post.txt |
| `grep ... /etc/selinux/targeted/contexts/files/` | Practice-dir weave: shows where live fcontext defaults live on the system |
| `2>&1 \| tee` | Captures the playbook output to `task1/evidence.txt` for the journal |
| `set -o pipefail` | Catches a silent failure in the `ansible-playbook \| tee` chain |
| `$(date -Is)` | Stamps the journal `notes.txt` |

### Main command block

```bash
cd /srv/www-lab-06
mkdir -p /srv/www-lab-06/task1

# 1. Write the playbook (VERBATIM YAML from Lab 06 Task 4 — paths adapted for lab-06b)
sudo tee /root/rhcsa_journal/lab-06b/playbooks/task1.yml > /dev/null <<'EOF'
---
- name: Lab 06b Task 1 — label /srv/www-lab-06 as web content via Ansible
  hosts: localhost
  become: true
  gather_facts: false

  vars:
    target_dir: /srv/www-lab-06
    target_type: httpd_sys_content_t

  tasks:
    - name: Declare fcontext rule (permanent — stored in policy DB)
      community.general.sefcontext:
        target: "{{ target_dir }}(/.*)?"
        setype: "{{ target_type }}"
        state: present
      register: rule_result

    - name: Apply policy — restorecon (no Ansible module; command: is RHCE-accepted)
      ansible.builtin.command:
        cmd: "restorecon -Rv {{ target_dir }}"
      register: restore_result
      changed_when: "'Relabeled' in restore_result.stdout"

    - name: Show what changed
      ansible.builtin.debug:
        msg:
          - "rule changed: {{ rule_result.changed }}"
          - "restorecon changed: {{ restore_result.changed }}"
          - "restorecon stdout: {{ restore_result.stdout_lines }}"
EOF

ls /root/rhcsa_journal/lab-06b/playbooks/task1.yml

# 2. Preview — --check --diff shows what WOULD change without changing anything
ansible-playbook --check --diff /root/rhcsa_journal/lab-06b/playbooks/task1.yml \
  2>&1 | tee /srv/www-lab-06/task1/check.txt

# 3. Apply — first real run
ansible-playbook /root/rhcsa_journal/lab-06b/playbooks/task1.yml \
  2>&1 | tee /srv/www-lab-06/task1/apply.txt

# 4. Verify with the same ls -lZ pattern from Lab 06a
ls -lZ /srv/www-lab-06/                              2>&1 | tee /srv/www-lab-06/task1/post.txt
semanage fcontext -l | grep www-lab-06
echo "exit was: $?"
```

> **The playbook content is in the heredoc above** — that block is the canonical `task1.yml`. Open it directly: `less /root/rhcsa_journal/lab-06b/playbooks/task1.yml`

### Human-readable breakdown

1. The playbook runs against `localhost` with `become: true` — SELinux policy changes require root. This is the standard pattern for the `linux-ops-mastery` series.
2. The first task uses `community.general.sefcontext` (FQCN — note: **not** the short name `sefcontext`) with `target: '/srv/www-lab-06(/.*)?'` and `setype: httpd_sys_content_t`.
3. The second task runs `restorecon -Rv` via `ansible.builtin.command:` with `changed_when:` so the task only reports `changed=1` when stdout contains "Relabeled" — without this guard, every run falsely reports changed.
4. The third task uses `ansible.builtin.debug:` to dump both registered results, so a human (and an RHCE grader) can read exactly what changed.
5. `--check --diff` previews: shows what would change but does not actually modify policy or labels.
6. The real run adds the fcontext rule (if missing) and relabels any mislabeled files under `/srv/www-lab-06/`.
7. Key tokens: `target: "{{ target_dir }}(/.*)?"` (path regex), `setype:` (SELinux type), `changed_when: "'Relabeled' in restore_result.stdout"` (idempotent `restorecon` wrapper).

### The story

The `register:` + `debug:` pattern is the single most under-practiced RHCE habit. Graders are not looking only at whether the label changed — they are reading the **playbook output** to confirm Ansible reported what you expect. A play that declares a rule but skips `restorecon` (T06-C) leaves files mislabeled even though the policy DB is correct. A play that uses `chcon` (T06-B) relabels temporarily but fails the permanence test.

The `--check --diff` preview is the safety habit. Always preview before applying. On the exam, running `--check --diff` against a complex play and reading the output catches typos in path regexes and reveals tasks that would have skipped because of bad `when:` conditions — both common point-deduction sources.

### Expected output

```text
# pre-state
unconfined_u:object_r:default_t:s0        index.html

# apply PLAY RECAP
localhost                  : ok=3    changed=2    unreachable=0    failed=0

# post-state
unconfined_u:object_r:httpd_sys_content_t:s0   index.html
/srv/www-lab-06(/.*)?    all files    system_u:object_r:httpd_sys_content_t:s0
exit was: 0
```

### Switches

| Token | Meaning |
|---|---|
| `ansible-playbook` | The driver that reads a YAML file and executes its tasks |
| `--check` | Dry run — no actual changes; reports what would happen |
| `--diff` | Show line-level diffs for changed resources |
| `hosts: localhost` | Run against the control node itself |
| `become: true` | Escalate to root for SELinux operations |
| `gather_facts: false` | Skip the implicit `setup` module |
| `target:` + `setype:` | The fcontext rule declaration |
| `state: present` | The desired-state declaration for `community.general.sefcontext` |
| `changed_when:` | Controls idempotence reporting for `command:` tasks |
| `register: VAR` | Capture task result into a playbook variable |

### 🧠 Concept Card

|   | Concept | What it does |
|---|---|---|
|   | FQCN (`community.general.sefcontext`) | Fully qualified collection name — required on RHCE EX294 |
|   | `state: present` declarative | "Ensure rule exists" — idempotent regardless of starting state |
|   | `restorecon -Rv` after `sefcontext` | Applies the policy DB rule to files on disk — skipping this is T06-C |
|   | `changed_when:` on `command:` | Makes `restorecon` wrapper idempotent — only changed when relabel happened |
|   | `--check --diff` preview | Safety habit: always preview before applying |
|   | `register:` + `debug:` | The grader's audit trail — read the play's own output |
| 🪤 | **Trap Risk T06-A/B/C** | Missing collection · `chcon` instead of `sefcontext` · fcontext without `restorecon` |

### 🔁 PERSISTENCE CHECK

| What was configured | Verification command | Why it matters |
|---|---|---|
| fcontext rule present | `semanage fcontext -l \| grep www-lab-06` | Must show `httpd_sys_content_t` mapping |
| Files relabeled | `ls -lZ /srv/www-lab-06/` | All files must show `httpd_sys_content_t` |
| Playbook persisted | `ls /root/rhcsa_journal/lab-06b/playbooks/task1.yml` | Playbook in `/root/` survives reboot; `/srv/` content may not |
| Evidence captured | `wc -l /root/rhcsa_journal/lab-06b/task1/apply.txt` | The PLAY RECAP line is the auditable result |

> **Reboot reasoning:** The fcontext rule in the policy database **survives reboot** — that is the whole point of `sefcontext` over `chcon`. After a reboot, running `restorecon -Rv /srv/www-lab-06` (or re-running the playbook) re-applies labels from the persistent rule. We test idempotence in Task 2.

### Journal write — BEFORE cleanup

```bash
LAB=lab-06b
TASK=task1
JDIR="/root/rhcsa_journal/${LAB}/${TASK}"
mkdir -p "$JDIR"
cp /srv/www-lab-06/task1/check.txt "$JDIR/check.txt"
cp /srv/www-lab-06/task1/apply.txt "$JDIR/apply.txt"
cp /srv/www-lab-06/task1/post.txt  "$JDIR/post.txt"
cp /srv/www-lab-06/pre.txt          "$JDIR/pre.txt"

cat > "$JDIR/done.txt" <<EOF
LAB:    ${LAB}
TASK:   ${TASK}
DATE:   $(date -Is)
USER:   $(whoami)@$(hostname)
STATUS: COMPLETE
EOF

cat > "$JDIR/notes.txt" <<EOF
TOPIC:    community.general.sefcontext + restorecon — first run (preview + apply)
COMMANDS: ansible-playbook --check --diff, ansible-playbook, register, debug, changed_when
TRAPS:    T06-A rehearsed (community.general installed); T06-B avoided (no chcon); T06-C avoided (restorecon present)
MISSED:   (fill in if any ⚠️ flags)
NEXT:     task2 — re-run the playbook for idempotence proof (changed=0)
EOF

ls -la "$JDIR"
echo "exit was: $?"
```

### 🧹 Cleanup

```bash
# Keep the playbook AND the journal — drop the sandbox transcript only
rm -rf /srv/www-lab-06/task1
ls /srv/www-lab-06/
echo "exit was: $?"
```

### Troubleshoot

| Symptom | Fix |
|---|---|
| `ansible-playbook: command not found` | Return to Lab 00 — control node not installed |
| `couldn't resolve module 'community.general.sefcontext'` | Trap T06-A — run `ansible-galaxy collection install community.general` |
| Files still show `default_t` after apply | Trap T06-C — verify `restorecon` task ran; check `restore_result.stdout` in debug output |
| `restorecon` always shows `changed=1` | Missing `changed_when:` — add `'Relabeled' in restore_result.stdout` |
| `--check` shows changed but apply does nothing | SELinux disabled — `getenforce` must return `Enforcing` or `Permissive` |
| `register:` variable empty | Typo in the variable name between `register:` and `debug:` |

> **STOP — paste the PLAY RECAP line of the apply run and `ls -lZ /srv/www-lab-06/` showing `httpd_sys_content_t` before Task 2.**

---

## Task 2 — The contrast: re-run for idempotence (changed=0)

**Practice directory this task:** `/etc` · confirm policy files unchanged. **Sandbox:** `/srv/www-lab-06/` — labels are already correct from Task 1 — Task 2 is the **proof** that re-running the play does nothing.

### 🔁 Warm-Up — commands woven into Task 2

```bash
ls -lZ /srv/www-lab-06/                              2>&1 | tee /srv/www-lab-06/pre-task2.txt
semanage fcontext -l | grep www-lab-06
grep httpd_sys_content /etc/selinux/targeted/contexts/files/file_contexts.local 2>/dev/null || true
test -f /root/rhcsa_journal/lab-06b/playbooks/task1.yml && echo "task1 playbook OK"
ansible-galaxy collection list 2>/dev/null | grep community.general | head -n 1
set -o pipefail
echo "Warm-up done by $(whoami) at $(date -Is)"
echo "exit was: $?"
```

> Carry from Task 1: every file under `/srv/www-lab-06/` must already show `httpd_sys_content_t` — if not, return to Task 1 before continuing.

### Purpose

Re-run the **exact same playbook** from Task 1 and prove that it now reports `changed=0`. This is the contract of idempotent Ansible: applied state does not drift on re-application. If Task 2 shows `changed=1`, the module call was wrong (the most common cause is missing `changed_when:` on `restorecon`, or using `command: chcon` instead of `sefcontext` — Trap T06-B).

### 🧵 WEAVE TRACE — warm-up commands re-used in this task body

| Warm-up command | Role inside Task 2 |
|---|---|
| `ls -lZ /srv/www-lab-06/` | Pre-condition check: labels must already be correct |
| `semanage fcontext -l \| grep www-lab-06` | Confirms rule exists before re-run |
| `grep ... file_contexts.local` | Practice-dir weave: shows the persistent local context file under `/etc` |
| `2>&1 \| tee` | Captures the second-run output to `task2/rerun.txt` — the **proof artifact** |
| `set -o pipefail` | Ensures the `tee` chain reports a failed `ansible-playbook` honestly |
| `$(date -Is)` | Stamps the journal `notes.txt` |

### Main command block

```bash
mkdir -p /srv/www-lab-06/task2

# 1. Re-run task2.yml (copy of task1.yml with idempotence debug) — or re-run task1.yml unchanged
ansible-playbook /root/rhcsa_journal/lab-06b/playbooks/task2.yml \
  2>&1 | tee /srv/www-lab-06/task2/rerun.txt

# 2. Inspect the PLAY RECAP — changed=0 is the win condition
grep -E "PLAY RECAP|changed=" /srv/www-lab-06/task2/rerun.txt

# 3. Verify labels are still correct (nothing drifted)
ls -lZ /srv/www-lab-06/                              2>&1 | tee /srv/www-lab-06/task2/post.txt
echo "exit was: $?"
```

### The playbook (`task2.yml` — content identical to `task1.yml` except play name + debug task)

Copy Task 1's playbook and change only the play name and the final debug task to the register+debug idempotence pattern:

```yaml
---
- name: "Lab 06b Task 2 — re-run for idempotence proof (changed=0 expected)"
  hosts: localhost
  become: true
  gather_facts: false

  vars:
    target_dir: /srv/www-lab-06
    target_type: httpd_sys_content_t

  tasks:
    - name: "Re-assert fcontext rule on /srv/www-lab-06"
      community.general.sefcontext:
        target: "{{ target_dir }}(/.*)?"
        setype: "{{ target_type }}"
        state: present
      register: rule_result

    - name: "Re-apply restorecon (should be no-op)"
      ansible.builtin.command:
        cmd: "restorecon -Rv {{ target_dir }}"
      register: restore_result
      changed_when: "'Relabeled' in restore_result.stdout"

    - name: "Show idempotence proof — both tasks must have changed=false"
      ansible.builtin.debug:
        msg:
          - "sefcontext changed={{ rule_result.changed }}"
          - "restorecon changed={{ restore_result.changed }}"
          - "restorecon stdout lines: {{ restore_result.stdout_lines | length }}"
```

Or re-run `task1.yml` unchanged — the PLAY RECAP `changed=0` line is the proof either way.

### Human-readable breakdown

1. Re-run the same modules and vars from Task 1 — the fcontext rule already exists and no files need relabeling.
2. The PLAY RECAP reports `changed=0`. That is the canonical idempotence proof RHCE graders look for.
3. The `register:` + `debug:` dump must show `rule_result.changed: false` and `restore_result.changed: false`.
4. If `changed=1` appears on `restorecon`, the `changed_when:` guard is missing (T06-C). If you used `command: chcon`, every re-run shows `changed=1` (T06-B).

### The story

Idempotence is **the** RHCE concept. Every grader knows that imperative wrappers (`command: chcon`) can be passed off as "Ansible playbooks" by candidates who don't understand the difference. The way they tell the difference: they re-run your play and look at the PLAY RECAP. A correctly-written play reports `changed=0` on the second run. An imperative `chcon` wrapper reports `changed=1` every time (T06-B).

The discipline is: every time you write a task, run it twice. Second run must be `changed=0`. If it's not, fix the module call before moving on.

### Expected output

```text
PLAY RECAP ********************************************************************
localhost                  : ok=3    changed=0    unreachable=0    failed=0

# debug output must show:
#   sefcontext changed=False
#   restorecon changed=False
exit was: 0
```

> **The key line: `changed=0` in the PLAY RECAP.** If this number is anything other than 0 on the re-run, Task 2 has failed and the module call needs to be fixed before moving to Lab 06c.

### Switches

| Token | Meaning |
|---|---|
| `changed_when:` | Makes `command: restorecon` idempotent — critical for Task 2 pass |
| `grep -E "PLAY RECAP\|changed="` | Extract just the audit-critical lines from a long playbook output |
| `semanage fcontext -l` | Verify the persistent rule survived the re-run |
| `ls -lZ` | Verify file labels did not drift |

### 🧠 Concept Card

|   | Concept | What it does |
|---|---|---|
|   | Idempotence proof | Re-run must show `changed=0`; that is the RHCE acceptance test |
|   | Declarative vs imperative | `sefcontext` + `restorecon` ≠ `command: chcon`. The first re-runs cleanly; the second does not. |
|   | PLAY RECAP audit | The bottom-line metric: `ok=N changed=M failed=K`. M should be 0 on re-run. |
|   | `changed_when:` guard | Without it, `restorecon` always reports changed — Task 2 fails falsely |
|   | Persistent fcontext | Rule in policy DB survives reboot; `chcon` does not |
| 🪤 | **Trap Risk T06-B** | If the second run shows `changed=1` on a `chcon` task, the module is wrong. Refuse to continue until fixed. |
| 🪤 | **Trap Risk T06-C** | If labels were never fixed in Task 1, Task 2 "passing" on `sefcontext` alone is a false win — check `ls -lZ`. |

### 🔁 PERSISTENCE CHECK

| What was configured | Verification command | Why it matters |
|---|---|---|
| Idempotence proven | `grep changed= /root/rhcsa_journal/lab-06b/task2/rerun.txt` | Must show `changed=0` in the PLAY RECAP |
| Playbooks survive reboot | `ls /root/rhcsa_journal/lab-06b/playbooks/` | `task1.yml` (and optional `task2.yml`) live in `/root/` |
| Labels remain correct | `ls -lZ /srv/www-lab-06/` | All files must still show `httpd_sys_content_t` |
| Policy rule persists | `semanage fcontext -l \| grep www-lab-06` | Rule must survive re-run and reboot |

> **Reboot reasoning:** After a reboot, the fcontext rule in the policy database remains. Files may need `restorecon` if something recreated them with wrong labels — but re-running this playbook handles that idempotently: `sefcontext` reports `changed=0`, `restorecon` only reports changed if relabeling was actually needed.

### Journal write — BEFORE cleanup

```bash
LAB=lab-06b
TASK=task2
JDIR="/root/rhcsa_journal/${LAB}/${TASK}"
mkdir -p "$JDIR"
cp /srv/www-lab-06/task2/rerun.txt "$JDIR/rerun.txt"
cp /srv/www-lab-06/task2/post.txt  "$JDIR/post.txt"
cp /srv/www-lab-06/pre-task2.txt   "$JDIR/pre-task2.txt"

cat > "$JDIR/done.txt" <<EOF
LAB:    ${LAB}
TASK:   ${TASK}
DATE:   $(date -Is)
USER:   $(whoami)@$(hostname)
STATUS: COMPLETE
EOF

cat > "$JDIR/notes.txt" <<EOF
TOPIC:    Idempotence proof — re-run shows changed=0
COMMANDS: ansible-playbook (rerun), grep "PLAY RECAP\|changed=", ls -lZ
TRAPS:    T06-B rehearsed (no chcon); T06-C rehearsed (restorecon + changed_when present)
MISSED:   (fill in if any ⚠️ flags)
NEXT:     lab-06c — the auditor seat: prove the labels stuck with RHCSA inspection commands
EOF

ls -la "$JDIR"
echo "exit was: $?"
```

### 🧹 Cleanup

```bash
# Optional: remove sandbox content (fcontext rule persists in policy DB)
# semanage fcontext -d '/srv/www-lab-06(/.*)?'   # only if tearing down lab entirely
rm -rf /srv/www-lab-06/task2
ls /srv/www-lab-06/
echo "exit was: $?"
```

### Troubleshoot

| Symptom | Fix |
|---|---|
| Re-run shows `changed=1` on restorecon | Missing or wrong `changed_when:` — add `'Relabeled' in restore_result.stdout` |
| Re-run shows `changed=1` on sefcontext | Rule was modified externally — compare `semanage fcontext -l` output to playbook vars |
| Labels wrong but PLAY RECAP says ok | Trap T06-C — `restorecon` did not run or `-Rv` was omitted |
| `community.general.sefcontext` not found | Trap T06-A — return to Lab 00, install collection |
| PLAY RECAP missing from journal | `tee` failed silently; turn on `set -o pipefail` |

> **STOP — paste the PLAY RECAP line showing `changed=0` and `cat $JDIR/notes.txt` before moving on to Lab 06c.**

---

## Lab 06b Checklist (2 tasks)

- [ ] Task 1 — Write the playbook + `--check --diff` preview + apply + `register:`/`debug:` evidence
- [ ] Task 2 — Re-run for idempotence proof (`changed=0`) + journal the PLAY RECAP

---

## 🔗 Related Labs in the Trilogy

| Lab | Connection |
|---|---|
| **Lab 06a** — RHCSA hand-typed SELinux labeling | The imperative form of what `sefcontext` + `restorecon` do declaratively |
| **Lab 06c** — Verifying SELinux Contexts | The auditor seat: prove the labels are real using RHCSA inspection commands (`ls -lZ`, `semanage fcontext -l`) |
| Lab 00 — Ansible Control Node Setup | Prerequisite — without `community.general` installed, this lab cannot start |
| Lab 06 — Listing Files and SELinux Contexts (full) | The parent lab containing the original Task 4 playbook pattern this lab adapts |

---

## 👤 Author

**Kelvin R. Tobias**
[kelvinintech.com](https://kelvinintech.com) · [GitHub](https://github.com/kelvintechnical) · [LinkedIn](https://www.linkedin.com/in/kelvin-r-tobias-211949219)
