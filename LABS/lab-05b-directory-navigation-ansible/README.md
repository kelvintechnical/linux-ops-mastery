# Lab 05b: Directory Navigation via Ansible — the `cd` Boundary (`chdir:` only)

- **Series:** linux-ops-mastery — File Operations & Shell Fundamentals
- **Trilogy:** `05a` (RHCSA) → **`05b` (Ansible — you are here)** → `05c` (Verify)
- **Career arcs covered:** RHCE EX294 (the Ansible Boundary — what does NOT belong in a playbook), SRE (declarative state vs imperative motion), DevOps (per-task cwd is the only honest "cd" in IaC), Platform (knowing when to reach for a real module vs `command:`/`shell:`)
- **Prerequisite:** Lab 00 (Ansible Control Node Setup), Lab 05a (you must have completed the RHCSA hand-typed version first)
- **Time Estimate:** 25–35 minutes
- **Tasks:** 2 (Task 1 = boundary playbook + preview + apply, Task 2 = idempotence + RHCE-correct alternative)
- **Practice Directory (rotation #05):** `/usr`
- **Sandbox:** `/tmp/nav-lab`
- **Playbooks live at:** `/root/rhcsa_journal/lab-05b/playbooks/`
- **Traps rehearsed this lab:** **T43** (writing `command: cd /usr && ls` as if `command:` were a shell) · **T05-A** (reaching for `shell:` to make `cd` "work" instead of using a real module with absolute `path:`)

> **This lab's practice directory is: `/usr`** — every task references it in at least two commands.

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
echo "⚠️  TRAP REMINDERS THIS LAB: T43 T05-A"
echo "📁  PRACTICE DIR: /usr"
echo ""
echo "🧰 Ansible toolchain check (must pass before Task 1):"
ansible --version | head -n 2
ansible -m ping localhost 2>&1 | tail -n 4
```

> **STOP — if `ansible --version` fails, return to Lab 00 (Ansible Control Node Setup). Do not attempt Task 1 without a working control node.**

---

## 🎯 Objective

Translate the RHCSA navigation moves from Lab 05a into the smallest amount of Ansible that can honestly express them — and learn where the boundary is. By the end of this lab you can:

- Use `chdir:` on `ansible.builtin.command` to set per-task cwd (the only "cd" Ansible has)
- Prove with two consecutive tasks that Ansible has **no** persistent cwd between tasks
- Explain why `command: cd /usr` fails (no `/usr/bin/cd` binary; `cd` is a shell builtin)
- Recognize the RHCE-correct alternative: a module that takes an absolute `path:` (`ansible.builtin.file`, `ansible.builtin.copy`, …) — no cwd needed at all

---

## 🧠 Concept: Ansible Has No `cd` — It Has `chdir:` for One Task

Every Ansible task runs in a **fresh process**. There is no persistent shell, no `$PWD` carried between tasks, no `$OLDPWD` updated, no `cd -`. If two consecutive tasks both need to operate from `/usr`, they each say so via `chdir: /usr`.

```
   ┌──────────────────────────────────────────────────────────────┐
   │  TASK 1: command: pwd       chdir: /usr   →  pwd prints /usr │
   │                                                              │
   │  TASK 2: command: pwd       (no chdir)    →  pwd prints  /   │
   │                                                              │
   │  TASK 3: command: cd /usr   (no chdir)    →  FAILS           │
   │                              ↑ rc=2 — there is no /usr/bin/cd│
   └──────────────────────────────────────────────────────────────┘
```

`cd` is a **shell builtin** — only the shell can change its own cwd. `ansible.builtin.command` runs executables via `exec(3)`, which only finds files in `$PATH`. There is no `/usr/bin/cd` binary. Writing `command: cd /usr` is the canonical wrong answer (**T43**).

The second wrong answer is the wrapper-instinct: reaching for `shell:` to make `cd` "work" because `command:` "doesn't." That is **T05-A**. The grader's read: this candidate did not realize that the **right** answer is to call a module that takes an absolute `path:` — at which point cwd never matters.

> **The RHCE failure mode (T43 + T05-A):** Writing `command: cd /usr && ls` (T43) or upgrading to `shell: cd /usr && ls` (T05-A) instead of using a module that operates on absolute paths. Both forms work imperatively but are non-idempotent and refuse the whole point of declarative configuration management.

---

## 📚 Module Reference (everything for Tasks 1–2)

| Token | Meaning |
|---|---|
| `ansible.builtin.command` | Run an executable directly (no shell) — the right module 95% of the time |
| `ansible.builtin.shell` | Run a string through `/bin/sh -c` — needed for `\|`, `>`, `&&`, builtins |
| `chdir: PATH` | Change to PATH before running the command — the **only** "cd" Ansible has, scoped to one task |
| `cmd:` | The executable to run (NOT a shell command — no globbing, no pipes) |
| `ansible.builtin.file` | Real declarative module — takes `path:` (absolute) and a `state:`; **idempotent** |
| `path:` (file module) | Absolute path; the module never depends on cwd |
| `state: directory` | Ensure the path exists as a directory (idempotent — re-run is `changed=0`) |
| `register: VAR` | Capture the task result into a playbook variable |
| `ansible.builtin.debug:` | Print a variable so you can read what `register:` captured |
| `ignore_errors: true` | Continue the play even when a task fails (used to demonstrate T43) |
| `--check` | Dry run — show what would change without changing anything |
| `--diff` | Show line-level diffs (combined with `--check` is the standard preview) |

---

## 🚦 Lab-Wide Setup — run BEFORE Task 1

```bash
sudo -i

# Sandbox — same one Lab 05a used; recreate if reboot wiped /tmp/
mkdir -p /tmp/nav-lab
cd /tmp/nav-lab

# Playbook home (persists across reboots — the whole point of /root)
mkdir -p /root/rhcsa_journal/lab-05b/playbooks

# Confirm the control node still works before we write playbook code
ansible --version | head -n 2
ansible -m ping localhost                            2>&1 | tail -n 4

ls -ld /tmp/nav-lab /usr /root/rhcsa_journal/lab-05b/playbooks
echo "exit was: $?"
```

> **STOP — paste output before Task 1.**

---

## Task 1 — Write the boundary playbook, preview with `--check --diff`, then apply

**Practice directory this task:** `/usr` · referenced from the playbook via `chdir: /usr` (proves per-task cwd) and from the failing-`command:cd` task (proves `cd` is not an executable). The playbook itself lives in `/root/rhcsa_journal/lab-05b/playbooks/` so it survives a reboot.

### 🔁 Warm-Up — commands woven into Task 1

```bash
ansible --version | head -n 2
ansible -m ping localhost                          2>&1 | tail -n 4
ls /root/rhcsa_journal/lab-05b/playbooks            2>&1 | tee /tmp/nav-lab/pre-task1.txt
test -d /root/rhcsa_journal/lab-05b/playbooks && echo "playbook dir OK"
test -d /usr && echo "/usr OK"
set -o pipefail
echo "Warm-up done by $(whoami) at $(date -Is)"
echo "exit was: $?"
```

> Carry from Lab 05a: the `2>&1 | tee` pattern is the same — we use it to capture the playbook output for the journal.

### Purpose

Write `nav-boundary.yml` — a playbook that demonstrates the three facts of the Ansible navigation boundary:

1. `chdir: /usr` on `ansible.builtin.command: pwd` makes that one task see `/usr` as its cwd
2. The **next** task (no `chdir:`) does **not** remember `/usr` — proof of statelessness
3. `ansible.builtin.command: cd /usr` **fails** with `rc=2` — proof that `cd` is a shell builtin, not an executable

Preview with `--check --diff`, then apply. Capture results with `register:`+`debug:` so a reader can audit exactly what Ansible saw.

### 🧵 WEAVE TRACE — warm-up commands re-used in this task body

| Warm-up command | Role inside Task 1 |
|---|---|
| `ansible --version` | Confirms the control node before any playbook run — if missing, abort to Lab 00 |
| `ansible -m ping localhost` | Confirms the inventory + connection — if `pong` is missing, abort |
| `ls /root/rhcsa_journal/lab-05b/playbooks` | Snapshot **before** the play — shows the playbook landed where we expect |
| `test -d /usr` | Pre-flight: refuses to run the play if `/usr` is somehow not present |
| `2>&1 \| tee` | Captures the apply transcript into `task1/apply.log` for the journal |
| `set -o pipefail` | Catches a silent failure in the `ansible-playbook | tee` chain |
| `$(date -Is)` | Stamps the journal `notes.txt` |

### Main command block

```bash
mkdir -p /tmp/nav-lab/task1

# 1. Write the boundary-demonstration playbook
cat > /root/rhcsa_journal/lab-05b/playbooks/nav-boundary.yml <<'EOF'
---
- name: "Lab 05b Task 1 — Ansible boundary for cd / navigation"
  hosts: localhost
  connection: local
  become: true
  gather_facts: false

  tasks:

    - name: "STEP A — chdir replaces cd for ONE task only"
      ansible.builtin.command:
        cmd: pwd
        chdir: /usr
      register: chdir_result

    - name: "STEP A.echo — print the pwd we observed inside /usr"
      ansible.builtin.debug:
        msg: "chdir:/usr saw pwd = {{ chdir_result.stdout }}"

    - name: "STEP B — the NEXT task does NOT remember /usr"
      ansible.builtin.command:
        cmd: pwd
      register: next_task_result

    - name: "STEP B.echo — proof of stateless cwd"
      ansible.builtin.debug:
        msg: "next task pwd = {{ next_task_result.stdout }} (NOT /usr)"

    - name: "STEP C — what NOT to do — wrapping cd as a command"
      ansible.builtin.command:
        cmd: cd /usr
      register: bad_cd
      ignore_errors: true

    - name: "STEP C.echo — confirm cd-as-command fails"
      ansible.builtin.debug:
        msg: "cd-as-command rc={{ bad_cd.rc | default('n/a') }} stderr={{ bad_cd.stderr | default('n/a') }}"
EOF

# 2. Preview — --check --diff parses syntax and shows what WOULD change
ansible-playbook --check --diff \
  /root/rhcsa_journal/lab-05b/playbooks/nav-boundary.yml \
  2>&1 | tee /tmp/nav-lab/task1/check.log

# 3. Apply — first real run
ansible-playbook \
  /root/rhcsa_journal/lab-05b/playbooks/nav-boundary.yml \
  2>&1 | tee /tmp/nav-lab/task1/apply.log

# 4. Extract the three audit-critical lines from the apply transcript
grep -E "chdir:/usr saw pwd|next task pwd|cd-as-command rc" \
  /tmp/nav-lab/task1/apply.log                       2>&1 | tee /tmp/nav-lab/task1/proof.txt
echo "exit was: $?"
```

### The playbook (`nav-boundary.yml`)

```yaml
---
- name: "Lab 05b Task 1 — Ansible boundary for cd / navigation"
  hosts: localhost
  connection: local
  become: true
  gather_facts: false

  tasks:

    - name: "STEP A — chdir replaces cd for ONE task only"
      ansible.builtin.command:
        cmd: pwd
        chdir: /usr
      register: chdir_result

    - name: "STEP A.echo — print the pwd we observed inside /usr"
      ansible.builtin.debug:
        msg: "chdir:/usr saw pwd = {{ chdir_result.stdout }}"

    - name: "STEP B — the NEXT task does NOT remember /usr"
      ansible.builtin.command:
        cmd: pwd
      register: next_task_result

    - name: "STEP B.echo — proof of stateless cwd"
      ansible.builtin.debug:
        msg: "next task pwd = {{ next_task_result.stdout }} (NOT /usr)"

    - name: "STEP C — what NOT to do — wrapping cd as a command"
      ansible.builtin.command:
        cmd: cd /usr
      register: bad_cd
      ignore_errors: true

    - name: "STEP C.echo — confirm cd-as-command fails"
      ansible.builtin.debug:
        msg: "cd-as-command rc={{ bad_cd.rc | default('n/a') }} stderr={{ bad_cd.stderr | default('n/a') }}"
```

### Human-readable breakdown

1. `hosts: localhost` + `connection: local` runs everything on the control node — no SSH, no remote inventory. Standard for the linux-ops-mastery series.
2. `become: true` lifts to root so the `pwd` runs in the same context Lab 05a's hand-typed commands did.
3. **STEP A** uses `ansible.builtin.command: pwd` with `chdir: /usr`. Inside that single task only, the command runs as if you had `cd /usr` first. `register: chdir_result` captures the result; the next `debug:` prints `chdir_result.stdout` — which is the string `/usr`.
4. **STEP B** is the next task. It also runs `pwd`, with **no** `chdir:`. It returns `/` (the default cwd when Ansible runs as root via `become:`) — **not** `/usr`. That is the proof of statelessness.
5. **STEP C** demonstrates the wrong instinct: `command: cd /usr`. This **fails** because `cd` is a shell builtin (only the shell can change its own cwd) and `ansible.builtin.command` runs executables via `exec(3)`, which only finds files in `$PATH`. There is no `/usr/bin/cd` binary. The task errors with `rc=2`; `ignore_errors: true` lets the play continue so we can print the error in the next `debug:`.

### Reading it left to right

- `ansible.builtin.command:` — FQCN of the command module. Always use the full name on RHCE.
- `cmd: pwd` — the executable. No globbing, no pipes, no shell interpretation — `pwd` is `/usr/bin/pwd` (or the shell builtin if invoked through `shell:`, but `command:` always uses the binary).
- `chdir: /usr` — change to this directory **before** running the command. Per-task only.
- `register: chdir_result` — captures `{ stdout: "/usr", rc: 0, ... }` into the playbook scope.
- `ansible.builtin.debug: msg: "... {{ chdir_result.stdout }}"` — the Jinja2 `{{ }}` substitutes the captured value.
- `ignore_errors: true` — keeps the play going even if this task fails. Used here because we **want** STEP C to fail so we can show the error.
- `bad_cd.rc | default('n/a')` — the Jinja `default` filter gives a safe fallback if `rc` is undefined (e.g. when running in `--check` mode the task may be skipped entirely).

### The story

The RHCE failure mode for navigation is to write `command: cd /usr && ls`. A grader reading that thinks: "this candidate doesn't understand that `&&` inside `command:` doesn't work because `command:` is exec, not a shell." So they switch to `shell:` (no `&&` problem there) — and now the grader sees `shell: cd /usr && ls` and thinks: "this candidate used `shell` instead of a real module — partial credit at best." That second switch is **T05-A**: the wrapper-instinct that reaches for `shell:` to make `cd` "work" instead of asking "is there a module that takes an absolute path here?"

The right answer when you genuinely need to operate in `/usr` from Ansible is either:

- `chdir:` on `ansible.builtin.command` / `ansible.builtin.shell` for one task (this lab), OR
- Use a module that takes an absolute `path:` (`ansible.builtin.file`, `ansible.builtin.copy`, `ansible.posix.firewalld --service=...`) — no cwd ever needed. Task 2 of this lab does exactly that.

### Expected output

```text
PLAY [Lab 05b Task 1 — Ansible boundary for cd / navigation] *******************

TASK [STEP A — chdir replaces cd for ONE task only] ****************************
changed: [localhost]

TASK [STEP A.echo — print the pwd we observed inside /usr] *********************
ok: [localhost] => {
    "msg": "chdir:/usr saw pwd = /usr"
}

TASK [STEP B — the NEXT task does NOT remember /usr] ***************************
changed: [localhost]

TASK [STEP B.echo — proof of stateless cwd] ************************************
ok: [localhost] => {
    "msg": "next task pwd = / (NOT /usr)"
}

TASK [STEP C — what NOT to do — wrapping cd as a command] **********************
fatal: [localhost]: FAILED! => {"changed": false, "cmd": "cd /usr", "msg": "[Errno 2] No such file or directory: b'cd'", "rc": 2}
...ignoring

TASK [STEP C.echo — confirm cd-as-command fails] *******************************
ok: [localhost] => {
    "msg": "cd-as-command rc=2 stderr=[Errno 2] No such file or directory: b'cd'"
}

PLAY RECAP *********************************************************************
localhost                  : ok=6    changed=2    unreachable=0    failed=0    ignored=1
```

> The three audit-critical lines are: `chdir:/usr saw pwd = /usr`, `next task pwd = / (NOT /usr)`, and `cd-as-command rc=2`. All three must appear in `proof.txt`.

### Switches

| Token | Meaning |
|---|---|
| `ansible-playbook` | The driver that reads a YAML file and executes its tasks |
| `--check` | Dry run — no actual changes; reports what would happen |
| `--diff` | Show line-level diffs for changed resources |
| `hosts: localhost` | Run against the control node itself |
| `connection: local` | Skip SSH; run as the local user |
| `become: true` | Run tasks as root (privilege escalation) |
| `gather_facts: false` | Skip the implicit `setup` module (speed) |
| `chdir: /usr` | The per-task cwd override; lives only for that one task |
| `register: VAR` | Capture task result into a playbook variable |
| `ignore_errors: true` | Continue the play on task failure |
| `\| default('n/a')` | Jinja2 filter that returns a fallback when the value is undefined |

### 🧠 Concept Card

|   | Concept | What it does |
|---|---|---|
|   | FQCN (`ansible.builtin.command`) | Fully qualified collection name — required on RHCE EX294 |
|   | Task statelessness | Every task is a fresh process — no cwd, no env, no `$OLDPWD` between tasks |
|   | `chdir:` | Per-task cwd override for `command:`/`shell:` — the only "cd" Ansible has |
|   | Why `command: cd /usr` fails | `cd` is a shell builtin; there is no `/usr/bin/cd` binary for `exec(3)` to find |
|   | `register:` + `debug:` | The grader's audit trail — read the play's own output |
|   | `ignore_errors: true` | Allows us to demonstrate the failure path without aborting the play |
| 🪤 | **Trap Risk T43** | Writing `command: cd /usr && ls` — `&&` is shell syntax, `command:` is exec; the task fails |
| 🪤 | **Trap Risk T05-A** | Reaching for `shell:` to make `cd` "work" instead of using a real module with absolute `path:` (we fix this in Task 2) |
|   | **Boundary** | This entire lab is the boundary — Ansible does NOT do navigation; the RHCE answer is modules + absolute paths |

### 🔁 PERSISTENCE CHECK

| What was configured | Verification command | Why it matters |
|---|---|---|
| Playbook persisted | `ls -l /root/rhcsa_journal/lab-05b/playbooks/nav-boundary.yml` | Lives in `/root/`, survives reboot |
| chdir proof captured | `grep -c 'chdir:/usr saw pwd = /usr' /tmp/nav-lab/task1/apply.log` | Must be `1` — the audit line for per-task cwd |
| Stateless proof captured | `grep -c 'next task pwd = /' /tmp/nav-lab/task1/apply.log` | Must be `1` — the audit line for no-persistent-cwd |
| cd-fails proof captured | `grep -c 'cd-as-command rc=2' /tmp/nav-lab/task1/apply.log` | Must be `1` — the audit line for "cd is a builtin, not a binary" |

> **Reboot reasoning:** The `/tmp/nav-lab/task1/apply.log` evaporates at reboot — but the **playbook** in `/root/rhcsa_journal/lab-05b/playbooks/nav-boundary.yml` does not. After a reboot you can re-run `ansible-playbook .../nav-boundary.yml` and reproduce all three audit lines from scratch. We rely on that in Lab 05c Task 2.

### Journal write — BEFORE cleanup

```bash
LAB=lab-05b
TASK=task1
JDIR="/root/rhcsa_journal/${LAB}/${TASK}"
mkdir -p "$JDIR"
cp /tmp/nav-lab/task1/check.log "$JDIR/check.log"
cp /tmp/nav-lab/task1/apply.log "$JDIR/apply.log"
cp /tmp/nav-lab/task1/proof.txt "$JDIR/proof.txt"

cat > "$JDIR/done.txt" <<EOF
LAB:    ${LAB}
TASK:   ${TASK}
DATE:   $(date -Is)
USER:   $(whoami)@$(hostname)
STATUS: COMPLETE
EOF

cat > "$JDIR/notes.txt" <<EOF
TOPIC:    Ansible navigation boundary — chdir: works for one task only; cd-as-command fails
COMMANDS: ansible-playbook --check --diff, ansible-playbook, chdir:, register, debug, ignore_errors
TRAPS:    T43 rehearsed (STEP C demonstrates the failure path, not a shortcut)
MISSED:   (fill in if any ⚠️ flags)
NEXT:     task2 — re-run for idempotence (command: is non-idempotent BY DESIGN here) + introduce the RHCE-correct file: state=directory alternative
EOF

ls -la "$JDIR"
echo "exit was: $?"
```

### 🧹 Cleanup

```bash
# Keep the playbook AND the journal — drop the live sandbox transcript only
rm -rf /tmp/nav-lab/task1
ls /tmp/nav-lab
echo "exit was: $?"
```

### Troubleshoot

| Symptom | Fix |
|---|---|
| `ansible-playbook: command not found` | Return to Lab 00 — control node not installed |
| `Could not match supplied host pattern` | Inventory missing or wrong — check `ansible.cfg` `inventory =` line |
| STEP A `chdir:/usr saw pwd = /` | `become: true` interaction — verify the task has `become: true` (inherited from play) and `chdir:` is the absolute path `/usr` |
| STEP C does NOT fail | You are on a system where `cd` is a shim in `$PATH` — re-test with explicit `/usr/bin/cd` (still fails) |
| `--check` mode skips STEP C | Expected — `command:` is "command-like" and `--check` can short-circuit it; check `apply.log`, not `check.log`, for the failure proof |
| `bad_cd.rc` shows `undefined` | The `default('n/a')` filter is now doing its job — usually means the task was skipped (check mode) |

> **STOP — confirm `proof.txt` contains all three audit lines (chdir saw `/usr`, next task saw `/`, cd-as-command `rc=2`) before Task 2.**

---

## Task 2 — Idempotence + the RHCE-correct alternative (`file: state=directory`)

**Practice directory this task:** `/usr` (still referenced in `nav-boundary.yml`'s `chdir:`) plus the new sandbox path `/tmp/nav-lab/managed-dir` which is what the RHCE-correct `file:` task operates on. The boundary playbook from Task 1 is re-run **as-is** — Task 2 contains the *idempotence-and-alternative* playbook.

### 🔁 Warm-Up — commands woven into Task 2

```bash
ls /root/rhcsa_journal/lab-05b/playbooks            2>&1 | tee /tmp/nav-lab/pre-task2.txt
test -f /root/rhcsa_journal/lab-05b/playbooks/nav-boundary.yml && echo "task1 playbook OK"
ls -ld /tmp/nav-lab                                 2>&1 | tee -a /tmp/nav-lab/pre-task2.txt
ansible --version | head -n 1
set -o pipefail
echo "Warm-up done by $(whoami) at $(date -Is)"
echo "exit was: $?"
```

> Carry from Task 1: the `apply.log` from Task 1 is the **baseline** we compare against. If Task 2's re-run shows a different number of `changed=`, that is the **expected** part of the boundary — see below.

### Purpose

Two things in one task:

**Part A — idempotence on the boundary playbook.** Re-run `nav-boundary.yml` exactly as-is. The `debug:` and `ignore_errors` tasks correctly report `changed=0` (no-ops). The three `command:` tasks (STEP A, STEP B, STEP C) **will** report `changed=1` again because `command:` is non-idempotent by design — and this is **expected** because the *purpose* of this play is to demonstrate the boundary, not to converge state. Call this out explicitly in `notes.txt` so a grader knows we understand the trade-off.

**Part B — the RHCE-correct alternative.** Introduce `nav-correct.yml`: a play whose single substantive task is `ansible.builtin.file` with an **absolute** `path:` and `state: directory`. That task **is** idempotent — first run is `changed=1`, every subsequent run is `changed=0`. That is the form RHCE graders want when the question is "ensure a directory exists at path X."

### 🧵 WEAVE TRACE — warm-up commands re-used in this task body

| Warm-up command | Role inside Task 2 |
|---|---|
| `ls /root/rhcsa_journal/lab-05b/playbooks` | Confirms Task 1 playbook is on disk before we re-run it |
| `test -f .../nav-boundary.yml` | Pre-condition — refuses to continue if Task 1's artifact is missing |
| `ls -ld /tmp/nav-lab` | Snapshot of the sandbox before the `file:` task creates `managed-dir` |
| `ansible --version` | Re-confirms the toolchain (rules out version-skew false negatives) |
| `2>&1 \| tee` | Captures both the rerun and the alternative-play output |
| `set -o pipefail` | Ensures `ansible-playbook | tee` reports a real failure |
| `$(date -Is)` | Stamps the journal `notes.txt` |

### Main command block

```bash
mkdir -p /tmp/nav-lab/task2

# ── Part A: re-run the boundary playbook for idempotence inspection ──
ansible-playbook \
  /root/rhcsa_journal/lab-05b/playbooks/nav-boundary.yml \
  2>&1 | tee /tmp/nav-lab/task2/rerun-boundary.log

# Extract the PLAY RECAP — note: command: tasks remain changed=1; that's the point
grep -E "PLAY RECAP|changed=" /tmp/nav-lab/task2/rerun-boundary.log

# ── Part B: write the RHCE-correct alternative playbook ──
cat > /root/rhcsa_journal/lab-05b/playbooks/nav-correct.yml <<'EOF'
---
- name: "Lab 05b Task 2 — RHCE-correct alternative: real module + absolute path"
  hosts: localhost
  connection: local
  become: true
  gather_facts: false

  tasks:

    - name: "Ensure /tmp/nav-lab/managed-dir exists (idempotent — no cwd needed)"
      ansible.builtin.file:
        path: /tmp/nav-lab/managed-dir
        state: directory
        mode: '0755'
      register: file_result

    - name: "Show what the file: module decided"
      ansible.builtin.debug:
        msg: "path={{ file_result.path }} changed={{ file_result.changed }}"
EOF

# First run of the alternative — should be changed=1
ansible-playbook \
  /root/rhcsa_journal/lab-05b/playbooks/nav-correct.yml \
  2>&1 | tee /tmp/nav-lab/task2/correct-run1.log

# Second run — MUST be changed=0 (the RHCE acceptance test for idempotence)
ansible-playbook \
  /root/rhcsa_journal/lab-05b/playbooks/nav-correct.yml \
  2>&1 | tee /tmp/nav-lab/task2/correct-run2.log

# Extract the contrast — boundary play has changed≥1 on re-run, file: play has changed=0
echo "── nav-boundary.yml re-run PLAY RECAP ──"
grep "PLAY RECAP" /tmp/nav-lab/task2/rerun-boundary.log
grep "localhost" /tmp/nav-lab/task2/rerun-boundary.log | tail -n 1

echo "── nav-correct.yml run-2 PLAY RECAP (must be changed=0) ──"
grep "PLAY RECAP" /tmp/nav-lab/task2/correct-run2.log
grep "localhost" /tmp/nav-lab/task2/correct-run2.log | tail -n 1
echo "exit was: $?"
```

### The playbook (`nav-correct.yml`)

```yaml
---
- name: "Lab 05b Task 2 — RHCE-correct alternative: real module + absolute path"
  hosts: localhost
  connection: local
  become: true
  gather_facts: false

  tasks:

    - name: "Ensure /tmp/nav-lab/managed-dir exists (idempotent — no cwd needed)"
      ansible.builtin.file:
        path: /tmp/nav-lab/managed-dir
        state: directory
        mode: '0755'
      register: file_result

    - name: "Show what the file: module decided"
      ansible.builtin.debug:
        msg: "path={{ file_result.path }} changed={{ file_result.changed }}"
```

### Human-readable breakdown

**Part A — re-run inspection.** `ansible-playbook nav-boundary.yml` runs the same play from Task 1. The `debug:` tasks are no-ops (`changed=0`). The three `command:` tasks (STEP A, STEP B, STEP C) report `changed=1` again because `command:` always reports `changed=1` whether the command succeeded, failed, or did nothing — `command:` is **imperative**, not declarative. This is normally a problem (T11-D from Lab 11b), **except** when the entire purpose of the task is to capture stdout for inspection. That is what we are doing here, and the journal notes call this out so a grader cannot mistake it for a mistake.

**Part B — the RHCE-correct alternative.** `nav-correct.yml` uses `ansible.builtin.file` with `path: /tmp/nav-lab/managed-dir` (absolute) and `state: directory`. First run: the directory does not exist → Ansible creates it → `changed=1`. Second run: the directory already exists with the right mode → Ansible does nothing → `changed=0`. That is the RHCE acceptance test for idempotence. The absolute `path:` means cwd is irrelevant — we never needed `chdir:`, we never needed `cd`, we never needed `shell:`.

### Reading it left to right

- `ansible-playbook .../nav-boundary.yml` — re-runs Task 1's playbook unchanged.
- `grep -E "PLAY RECAP|changed="` — extended regex; matches lines containing either substring. The first picks the recap header; the second can pick task-level `changed=` lines.
- `ansible.builtin.file:` — FQCN of the file module, the declarative file-state primitive.
- `path: /tmp/nav-lab/managed-dir` — **absolute** path. The module never depends on cwd.
- `state: directory` — desired end state. Idempotent: if the directory exists and matches the other attributes, `changed=false`.
- `mode: '0755'` — POSIX mode. Quoted to keep YAML from interpreting `0755` as octal-syntax-might-be-decimal weirdness.
- `register: file_result` / `debug: msg: "... {{ file_result.changed }}"` — same audit-trail pattern as Task 1, now with the **declarative** value.

### The story

The RHCE failure mode is `command: cd /usr && ls > /etc/foo` (wrap a navigation move in a shell command). The Lab 05b boundary is teaching the reflex: when the question reads "do X in directory Y," your first move is to ask "is there a module that takes `path: Y/X`?" Nine times out of ten there is — and you avoid `command:`/`shell:` entirely, which means you avoid the idempotence trap, which means the grader's re-run shows `changed=0`, which means full credit.

The contrast between the two playbooks in this task is the **whole** point of the boundary. `nav-boundary.yml` is a teaching artifact — it intentionally uses `command:` so we can demonstrate that the boundary exists. `nav-correct.yml` is the production pattern — `ansible.builtin.file` with absolute `path:` is what you would actually deploy.

### Expected output

```text
── nav-boundary.yml re-run PLAY RECAP ──
PLAY RECAP *********************************************************************
localhost                  : ok=6    changed=2    unreachable=0    failed=0    ignored=1
── nav-correct.yml run-2 PLAY RECAP (must be changed=0) ──
PLAY RECAP *********************************************************************
localhost                  : ok=2    changed=0    unreachable=0    failed=0
exit was: 0
```

> The key contrast: `nav-boundary.yml` re-run shows `changed=2` (the two `command:` tasks that actually executed; STEP C was `ignored`). `nav-correct.yml` second run shows `changed=0`. The first is the boundary; the second is the RHCE acceptance criterion.

### Switches

| Token | Meaning |
|---|---|
| `ansible.builtin.file` | The real declarative module — takes `path:` and `state:` |
| `state: directory` | Ensure the path exists as a directory; idempotent |
| `state: file` | Ensure the path is a regular file |
| `state: absent` | Ensure the path does not exist (Lab 11b) |
| `path: /abs/path` | Absolute path; module is cwd-independent |
| `mode: '0755'` | POSIX mode — quote in YAML to be safe |
| `register: file_result` | Capture the file-module result; has `.changed`, `.path`, `.mode`, … |
| `grep -E "A\|B"` | Extended regex; matches A or B |

### 🧠 Concept Card

|   | Concept | What it does |
|---|---|---|
|   | `command:` is non-idempotent | Always reports `changed=1` if the command executed — wrong tool when convergence matters |
|   | Expected non-idempotence in Task 1's play | The play's purpose is to *demonstrate the boundary*, not to converge state — graders accept this when it's documented |
|   | `ansible.builtin.file` declarative | `state: directory` + absolute `path:` = full idempotence with no cwd |
|   | Absolute `path:` everywhere | Drops the cwd question entirely — the right answer 95% of the time |
|   | Two playbooks per lesson | Teaching artifact (`nav-boundary.yml`) + production pattern (`nav-correct.yml`) |
| 🪤 | **Trap Risk T43** | `command: cd /usr && ls` — fixed by deleting `cd` and using `chdir:` or, better, a real module |
| 🪤 | **Trap Risk T05-A** | Upgrading `command: cd ...` to `shell: cd ...` instead of using `file: path: absolute` — the wrapper-instinct that *still* fails the idempotence test |

### 🔁 PERSISTENCE CHECK

| What was configured | Verification command | Why it matters |
|---|---|---|
| Boundary re-run captured | `wc -l /tmp/nav-lab/task2/rerun-boundary.log` | Must be > 0 — proof the second run happened |
| Alternative play idempotent | `grep changed= /tmp/nav-lab/task2/correct-run2.log` | Must show `changed=0` in the PLAY RECAP |
| Both playbooks survive reboot | `ls /root/rhcsa_journal/lab-05b/playbooks/` | Should show both `nav-boundary.yml` and `nav-correct.yml` |
| Managed dir created | `ls -ld /tmp/nav-lab/managed-dir` | Mode `0755`, owner `root` |

> **Reboot reasoning:** After a reboot, `/tmp/nav-lab` (including `managed-dir`) evaporates — but the playbook `nav-correct.yml` in `/root/` does not. Re-running it would re-create `managed-dir` (`changed=1`) and a subsequent re-run would report `changed=0` again. **The idempotence contract holds across reboot.** That is what Lab 05c Task 2 verifies.

### Journal write — BEFORE cleanup

```bash
LAB=lab-05b
TASK=task2
JDIR="/root/rhcsa_journal/${LAB}/${TASK}"
mkdir -p "$JDIR"
cp /tmp/nav-lab/task2/rerun-boundary.log "$JDIR/rerun-boundary.log"
cp /tmp/nav-lab/task2/correct-run1.log   "$JDIR/correct-run1.log"
cp /tmp/nav-lab/task2/correct-run2.log   "$JDIR/correct-run2.log"

cat > "$JDIR/done.txt" <<EOF
LAB:    ${LAB}
TASK:   ${TASK}
DATE:   $(date -Is)
USER:   $(whoami)@$(hostname)
STATUS: COMPLETE
EOF

cat > "$JDIR/notes.txt" <<EOF
TOPIC:    Boundary re-run (expected changed≥1 — command: is non-idempotent BY DESIGN here) + RHCE-correct alternative (file: state=directory, changed=0 on re-run)
COMMANDS: ansible-playbook (rerun), grep "PLAY RECAP\|changed=", ansible.builtin.file, state: directory, path: absolute
TRAPS:    T43 rehearsed (we did NOT add cd to anything new), T05-A rehearsed (we did NOT reach for shell: — we used file: with absolute path)
NOTE:     The boundary playbook's command: tasks re-running as changed=2 is EXPECTED and documented — the play's purpose is to demonstrate the boundary, not to converge.
MISSED:   (fill in if any ⚠️ flags)
NEXT:     lab-05c — the auditor seat: prove the symlink, the cwd evidence, and that the playbooks still work after a simulated reboot
EOF

ls -la "$JDIR"
echo "exit was: $?"
```

### 🧹 Cleanup

```bash
# Keep the playbooks AND the journal — drop the live sandbox transcripts only
rm -rf /tmp/nav-lab/task2
ls /tmp/nav-lab
ls /root/rhcsa_journal/lab-05b/playbooks
echo "exit was: $?"
```

### Troubleshoot

| Symptom | Fix |
|---|---|
| Boundary re-run shows `changed=0` | A previous `command:` task is now being short-circuited — verify `nav-boundary.yml` matches Task 1 exactly |
| `nav-correct.yml` run-2 shows `changed=1` | Something deleted `/tmp/nav-lab/managed-dir` between runs (or a different user owns it) — check `ls -ld` and re-run |
| `file:` task fails with "Destination ... not writable" | `become: true` missing — verify it is set at the play level |
| `mode: 0755` warning | Quote it: `mode: '0755'` — YAML can mis-interpret bare numeric modes |
| PLAY RECAP missing from log | `tee` failed silently — turn on `set -o pipefail` |

> **STOP — paste both PLAY RECAP lines (the boundary re-run AND the `nav-correct.yml` run-2) and `cat $JDIR/notes.txt` before moving on to Lab 05c.**

---

## Lab 05b Checklist (2 tasks)

- [ ] Task 1 — Write `nav-boundary.yml`, preview with `--check --diff`, apply, capture all three audit lines (`chdir:/usr saw pwd = /usr`, `next task pwd = /`, `cd-as-command rc=2`)
- [ ] Task 2 — Re-run the boundary playbook (document the **expected** non-idempotence), then write + apply `nav-correct.yml` twice to prove the `file:` task IS idempotent (`changed=0` on re-run)

---

## 🔗 Related Labs in the Trilogy

| Lab | Connection |
|---|---|
| **Lab 05a** — RHCSA hand-typed navigation | The imperative form that this lab is the boundary against |
| **Lab 05c** — Verifying Directory Navigation | The auditor seat: prove the symlink, the cwd evidence, and that both playbooks still work after a simulated reboot |
| Lab 00 — Ansible Control Node Setup | Prerequisite — without a working control node, this lab cannot start |
| Lab 04 — Redirection | The `2>&1 \| tee` capture pattern reused for `check.log` / `apply.log` |
| Lab 06a — Listing Files (`ls`) | The next operator move after navigation — and the next lab where the boundary surfaces |

---

## 👤 Author

**Kelvin R. Tobias**
[kelvinintech.com](https://kelvinintech.com) · [GitHub](https://github.com/kelvintechnical) · [LinkedIn](https://www.linkedin.com/in/kelvin-r-tobias-211949219)
