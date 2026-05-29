# Lab 07b: Creating Files & Setting Timestamps via Ansible — `ansible.builtin.file: state=touch` with `modification_time:` / `access_time:`

- **Series:** linux-ops-mastery — File Operations & Shell Fundamentals
- **Trilogy:** `07a` (RHCSA) → **`07b` (Ansible — you are here)** → `07c` (Verify)
- **Career arcs covered:** RHCE EX294 (`ansible.builtin.file: state=touch` is the declarative `touch -t`), SRE (sentinel-file timestamps as liveness probes), DevOps (CI cache busting via mtime), AI/MLOps (stale-checkpoint cleanup playbooks)
- **Prerequisite:** Lab 07a (you must have completed the RHCSA hand-typed version first), Lab 00 (Ansible Control Node Setup)
- **Time Estimate:** 30–40 minutes
- **Tasks:** 2 (Task 1 = write + apply, Task 2 = idempotence proof — including the deliberate "non-idempotent by default" trap)
- **Practice Directory (rotation #07):** `/var/log`
- **Sandbox:** `/tmp/touch-lab/`
- **Playbooks live at:** `/root/rhcsa_journal/lab-07b/playbooks/`
- **Traps rehearsed this lab:** **T07-A** (using `state: touch` WITHOUT pinning `modification_time:` and `access_time:` — second run reports `changed=1` because the default is "now"; graders mark it down as non-idempotent) · **T07-B** (using `ansible.builtin.command: touch FILE` instead of the real module — refused on RHCE grading) · **T07-C** (forgetting `modification_time_format: '%Y%m%d%H%M.%S'` when the input string is not in the default `touch -t` shape)

> **This lab's practice directory is: `/var/log`** — every task references it for cross-reference. We **read** `/var/log` only; we **write** only inside `/tmp/touch-lab/`.

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
echo "⚠️  TRAP REMINDERS THIS LAB: T07-A T07-B T07-C"
echo "📁  PRACTICE DIR: /var/log"
echo ""
echo "🧰 Ansible toolchain check (must pass before Task 1):"
ansible --version | head -n 2
ansible -m ping localhost 2>&1 | tail -n 4
```

> **STOP — if `ansible --version` fails, return to Lab 00 (Ansible Control Node Setup). Do not attempt Task 1 without a working control node.**

---

## 🎯 Objective

Replace the hand-typed `touch -t` from Lab 07a with the **declarative form** RHCE graders expect. By the end of this lab you can write a playbook that creates a file with a pinned modification time, run it twice, and prove the second run is `changed=0`. You will also see — deliberately — the **non-idempotent default** of `state: touch` (Trap T07-A) and how pinning `modification_time:` + `access_time:` is the fix.

---

## 🧠 Concept: `state: touch` Is NOT Idempotent by Default — Pin the Timestamps

`ansible.builtin.file: state=touch` is the declarative equivalent of `touch FILE`. Like the shell tool, it **sets atime+mtime to now**. That has a profound consequence:

```
   target state: touch  +  no modification_time:    →  mtime = now,  EVERY RUN
   actual state: any                                →  changed=1,    EVERY RUN

   target state: touch  +  modification_time: PINNED  →  mtime = PINNED
   actual state: mtime == PINNED                       →  changed=0
   actual state: mtime != PINNED                       →  changed=1 (once, then 0)
```

That is the trap. `state: present` and `state: absent` are idempotent by their declarative shape. `state: touch` **without explicit timestamps** is NOT — by design, because "I want this file to exist with a fresh mtime" is intentionally non-idempotent (it's the `touch` behaviour, lifted into a module). The fix is to pin both `modification_time:` and `access_time:` to fixed values — then the module sees "actual already matches desired" and reports `changed=0`.

> **The RHCE failure mode (T07-A):** writing `state: touch` with no `modification_time:`, then asking why the second run reports `changed=1`. The grader expects you to know **why** that happens AND how to make the play idempotent when idempotence is the requirement.

> **The RHCE cardinal sin (T07-B):** wrapping `ansible.builtin.command: touch FILE` instead of using `ansible.builtin.file: state=touch`. The `command:` form is imperative — always `changed=1`, no proper diff support, refused on RHCE grading.

---

## 📚 File Module Timestamp Reference (everything for Tasks 1–2)

| Token | Meaning |
|---|---|
| `ansible.builtin.file` | The FQCN of the file module — **always** use the full name on RHCE |
| `path:` | Target path |
| `state: touch` | Create if missing + bump timestamps (equivalent to `touch FILE`) |
| `state: file` | Path must already exist as a regular file — does NOT create |
| `state: directory` | Path must be a directory (equivalent to `mkdir -p`) |
| `state: absent` | Path must not exist (equivalent to `rm -rf`) |
| `modification_time:` | mtime as a `touch -t` formatted string (default `%Y%m%d%H%M.%S`) |
| `modification_time_format:` | strftime override — set for ISO 8601 or epoch input |
| `access_time:` | atime, same shape as `modification_time:` |
| `access_time_format:` | strftime override for `access_time:` |
| `mode:` | Octal mode — **always quote**: `'0644'` |
| `owner:` / `group:` | DAC ownership |
| `register: VAR` | Capture task result |
| `ansible.builtin.debug:` | Print a captured variable |
| `--check` | Dry run |
| `--diff` | Show line-level diffs |

---

## 🚦 Lab-Wide Setup — run BEFORE Task 1

```bash
sudo -i

mkdir -p /tmp/touch-lab
mkdir -p /root/rhcsa_journal/lab-07b/playbooks
cd /tmp/touch-lab

echo "lab07b reference content" > /tmp/touch-lab/reference.txt

ls -la /tmp/touch-lab
ls -la /root/rhcsa_journal/lab-07b/playbooks
ansible --version | head -n 1
echo "exit was: $?"
```

> **STOP — paste output before Task 1. Both the sandbox directory and the playbooks directory must exist.**

---

## Task 1 — Write the playbook, preview with `--check --diff`, then apply

**Practice directory this task:** `/var/log` (cross-reference target — we read real log mtimes after the play) · `/tmp/touch-lab/` (the playbook's write target) · `/root/rhcsa_journal/lab-07b/playbooks/` (where the playbook itself lives so it survives reboot).

### 🔁 Warm-Up — commands woven into Task 1

```bash
ansible --version | head -n 2
ansible -m ping localhost                           2>&1 | tail -n 4
ls /tmp/touch-lab                                   2>&1 | tee /tmp/touch-lab/pre.txt
test -d /root/rhcsa_journal/lab-07b/playbooks && echo "playbook dir OK"
find /var/log -maxdepth 1 -type f                   2>/dev/null | wc -l
set -o pipefail
echo "Warm-up done by $(whoami) at $(date -Is)"
echo "exit was: $?"
```

> Carry from Lab 07a: the `stat -c '%y'` reflex carries forward — every Ansible apply is followed by `stat` to prove the timestamp Ansible claimed actually stuck.

### Purpose

Write a playbook that uses `ansible.builtin.file: state=touch` to create two files: one with **pinned** `modification_time:` and `access_time:` (the idempotent form), and one with **no** explicit times (the deliberate non-idempotent form — Task 2 will prove the difference). Run with `--check --diff` first, then apply for real. Verify the timestamps with `stat`.

### 🧵 WEAVE TRACE — warm-up commands re-used in this task body

| Warm-up command | Role inside Task 1 |
|---|---|
| `ansible --version` | Confirms the control node before the play — abort to Lab 00 if missing |
| `ls /tmp/touch-lab` | Snapshot **before** the play (saved to `pre.txt`) for diff |
| `find /var/log -type f` | Real-world cross-reference for mtime ordering at the end |
| `2>&1 \| tee` | Captures the playbook output into `task1/evidence.txt` for the journal |
| `set -o pipefail` | Catches a silent failure in the `ansible-playbook \| tee` chain |
| `$(date -Is)` | Stamps the journal `notes.txt` |

### Main command block

```bash
cd /tmp/touch-lab
mkdir -p /tmp/touch-lab/task1

# 1. Write the playbook (lives in /root/ so it survives reboot)
sudo tee /root/rhcsa_journal/lab-07b/playbooks/task1.yml > /dev/null <<'EOF'
---
- name: "Lab 07b Task 1 — create files via ansible.builtin.file: state=touch"
  hosts: localhost
  connection: local
  gather_facts: false

  vars:
    sandbox: /tmp/touch-lab
    target_mtime: "202401151200.00"   # 2024-01-15 12:00:00 — touch -t format
    target_atime: "202001010000.00"   # 2020-01-01 00:00:00

  tasks:
    - name: "Ensure the sandbox directory exists"
      ansible.builtin.file:
        path: "{{ sandbox }}"
        state: directory
        mode: '0755'

    - name: "Touch ansible-pinned.txt — pinned mtime + atime (IDEMPOTENT FORM)"
      ansible.builtin.file:
        path: "{{ sandbox }}/ansible-pinned.txt"
        state: touch
        owner: root
        group: root
        mode: '0644'
        modification_time: "{{ target_mtime }}"
        access_time: "{{ target_atime }}"
      register: touch_pinned

    - name: "Touch ansible-now.txt — NO timestamps pinned (NON-IDEMPOTENT — T07-A demo)"
      ansible.builtin.file:
        path: "{{ sandbox }}/ansible-now.txt"
        state: touch
        mode: '0600'
      register: touch_now

    - name: "Show register results (the register: + debug: pattern RHCE graders look for)"
      ansible.builtin.debug:
        msg:
          - "pinned changed: {{ touch_pinned.changed }}"
          - "now    changed: {{ touch_now.changed }}"
EOF

ls /root/rhcsa_journal/lab-07b/playbooks/task1.yml

# 2. Preview — --check --diff shows what WOULD change
ansible-playbook --check --diff /root/rhcsa_journal/lab-07b/playbooks/task1.yml \
  2>&1 | tee /tmp/touch-lab/task1/check.txt

# 3. Apply — first real run
ansible-playbook /root/rhcsa_journal/lab-07b/playbooks/task1.yml \
  2>&1 | tee /tmp/touch-lab/task1/apply.txt

# 4. Verify with stat (the proof Ansible's claim is real)
{
  echo "═══ ansible-pinned.txt (PINNED → expect 2024-01-15 mtime, 2020-01-01 atime) ═══"
  stat /tmp/touch-lab/ansible-pinned.txt
  echo "═══ ansible-now.txt (NOW → expect mtime within last minute) ═══"
  stat /tmp/touch-lab/ansible-now.txt
} 2>&1 | tee /tmp/touch-lab/task1/post.txt

echo "exit was: $?"
```

### The playbook (`task1.yml`)

```yaml
---
- name: "Lab 07b Task 1 — create files via ansible.builtin.file: state=touch"
  hosts: localhost
  connection: local
  gather_facts: false

  vars:
    sandbox: /tmp/touch-lab
    target_mtime: "202401151200.00"   # 2024-01-15 12:00:00 — touch -t format
    target_atime: "202001010000.00"   # 2020-01-01 00:00:00

  tasks:
    - name: "Ensure the sandbox directory exists"
      ansible.builtin.file:
        path: "{{ sandbox }}"
        state: directory
        mode: '0755'

    - name: "Touch ansible-pinned.txt — pinned mtime + atime (IDEMPOTENT FORM)"
      ansible.builtin.file:
        path: "{{ sandbox }}/ansible-pinned.txt"
        state: touch
        owner: root
        group: root
        mode: '0644'
        modification_time: "{{ target_mtime }}"
        access_time: "{{ target_atime }}"
      register: touch_pinned

    - name: "Touch ansible-now.txt — NO timestamps pinned (NON-IDEMPOTENT — T07-A demo)"
      ansible.builtin.file:
        path: "{{ sandbox }}/ansible-now.txt"
        state: touch
        mode: '0600'
      register: touch_now

    - name: "Show register results (the register: + debug: pattern RHCE graders look for)"
      ansible.builtin.debug:
        msg:
          - "pinned changed: {{ touch_pinned.changed }}"
          - "now    changed: {{ touch_now.changed }}"
```

### Human-readable breakdown

1. `hosts: localhost` + `connection: local` keeps the play self-contained — no SSH, no inventory.
2. The first task is a defensive `state: directory` on `{{ sandbox }}` — guarantees `/tmp/touch-lab` exists before we try to write inside it. Idempotent: if the dir is already there, `changed=0`.
3. Task **"Touch ansible-pinned.txt"** is the **idempotent** form. `modification_time: "202401151200.00"` is exactly the same string `touch -t` accepts. The default `modification_time_format:` is `%Y%m%d%H%M.%S` — meaning "century-year-month-day-hour-minute, optional dot-seconds." That string `202401151200.00` parses to `2024-01-15 12:00:00`. Same for `access_time:`.
4. Task **"Touch ansible-now.txt"** is the deliberate **non-idempotent** demo. No `modification_time:` means the module defaults to **now** — and "now" is different on every run, so every run reports `changed=1`. We keep this in the play on purpose so Task 2 can demonstrate the contrast.
5. The `debug:` task is the **audit trail** RHCE graders look for. It reads both `register:` variables and prints which one changed.

### Reading it left to right

- `state: touch` — declarative shape of `touch FILE`. Creates if missing; updates timestamps.
- `modification_time: "{{ target_mtime }}"` — Jinja2 substitution of the var. Quoted so YAML keeps it as a string.
- `modification_time_format:` (not used here — we rely on the default `%Y%m%d%H%M.%S`) — if your input is ISO 8601 (`2024-01-15T12:00:00`), set `modification_time_format: "%Y-%m-%dT%H:%M:%S"`. **T07-C** is exactly this gap: providing an ISO 8601 string without overriding the format makes the module error out (or worse — silently parse it wrong).
- `mode: '0644'` — quoted octal. Unquoted `0644` is YAML-decimal 644 = octal 1204 — silently wrong mode. **Always quote mode strings.**
- `register: touch_pinned` — captures `{ changed: true/false, dest: ..., ... }` into the playbook scope.
- `ansible.builtin.debug: msg:` — prints a list of messages instead of dumping the full register var. Cleaner output for graders.

### The story

A grader's RHCE question: "create `/srv/sentinel.flag` with mode 0600, owned by root, with a modification time of January 1, 2025 — and the play must be idempotent." The complete answer is exactly the `ansible-pinned.txt` task above (path and date swapped). One module call replaces `touch` + `chmod` + `chown` + `touch -t` — and the **pinned** form is what makes it idempotent.

The deeper point is the **deliberate non-idempotence** of the bare `state: touch`. It is not a bug; it is the module documenting that "make this file have a fresh mtime right now" is genuinely a non-idempotent operation. The play tells the truth: `changed=1` every run. The grader's question — and the senior engineer's question — is "do you understand WHY, and do you know how to make it idempotent when the requirement demands it?"

### Expected output

```text
ansible [core 2.16.x] ...
localhost | SUCCESS => { "changed": false, "ping": "pong" }

# --- --check --diff preview ---
PLAY [Lab 07b Task 1 — ...] ***************************************************
TASK [Ensure the sandbox directory exists] ************************************
ok: [localhost]
TASK [Touch ansible-pinned.txt — pinned mtime + atime (IDEMPOTENT FORM)] ******
changed: [localhost]
TASK [Touch ansible-now.txt — NO timestamps pinned (NON-IDEMPOTENT — T07-A demo)]
changed: [localhost]
TASK [Show register results ...] **********************************************
ok: [localhost] => { "msg": ["pinned changed: True", "now    changed: True"] }
PLAY RECAP ********************************************************************
localhost                  : ok=4    changed=2    unreachable=0    failed=0

# --- apply (real run) — identical recap ---

# --- post-state verification ---
═══ ansible-pinned.txt (PINNED → expect 2024-01-15 mtime, 2020-01-01 atime) ═══
  File: /tmp/touch-lab/ansible-pinned.txt
  Size: 0  ...  regular empty file
Access: 2020-01-01 00:00:00.000000000 -0500
Modify: 2024-01-15 12:00:00.000000000 -0500
Change: 2026-05-27 15:00:01.xxx -0400
═══ ansible-now.txt (NOW → expect mtime within last minute) ═══
Modify: 2026-05-27 15:00:01.xxx -0400
exit was: 0
```

> The win condition: `ansible-pinned.txt` shows mtime `2024-01-15` and atime `2020-01-01`. `ansible-now.txt` shows mtime in the current minute. Both files have ctime in the current minute — because ctime always tracks the last inode write, regardless of what mtime/atime the module pinned.

### Switches

| Token | Meaning |
|---|---|
| `ansible-playbook` | The driver that reads YAML and runs tasks |
| `--check` | Dry run — no actual changes |
| `--diff` | Show line-level diffs |
| `hosts: localhost` | Run against the control node |
| `connection: local` | Skip SSH |
| `gather_facts: false` | Skip the `setup` module |
| `state: touch` | Create + bump timestamps |
| `modification_time:` | Pinned mtime (default `touch -t` format) |
| `access_time:` | Pinned atime |
| `modification_time_format:` | strftime override |
| `mode: '0644'` | Octal mode, quoted |
| `register: VAR` | Capture task result |

### 🧠 Concept Card

|   | Concept | What it does |
|---|---|---|
|   | FQCN (`ansible.builtin.file`) | Fully qualified collection name — required on RHCE EX294 |
|   | `state: touch` | Declarative `touch FILE` |
|   | Pinned timestamps | `modification_time:` + `access_time:` → idempotent run |
|   | Default = NOW | Without pinned timestamps, every run is `changed=1` (deliberate) |
|   | `modification_time_format:` | strftime override — set when input is not `%Y%m%d%H%M.%S` |
|   | Quote the mode | `mode: '0644'` not `mode: 0644` — YAML strips the leading 0 silently |
| 🪤 | **Trap Risk T07-A** | `state: touch` without pinned timestamps reports `changed=1` every run — graders mark it down |
| 🪤 | **Trap Risk T07-B** | Wrapping `command: touch FILE` instead of using the module — RHCE cardinal sin |
| 🪤 | **Trap Risk T07-C** | Forgetting `modification_time_format:` when feeding a non-default string (ISO 8601, epoch, etc.) |

### 🔁 PERSISTENCE CHECK

| What was configured | Verification command | Why it matters |
|---|---|---|
| Pinned file exists with right mtime | `stat -c '%y' /tmp/touch-lab/ansible-pinned.txt \| grep -c '2024-01-15'` | Must be `1` — proves the playbook claim |
| Playbook persisted | `ls /root/rhcsa_journal/lab-07b/playbooks/task1.yml` | Playbook in `/root/` survives reboot; `/tmp/` would not |
| Apply log captured | `wc -l /root/rhcsa_journal/lab-07b/task1/apply.txt` | The PLAY RECAP line is the auditable result |

> **Reboot reasoning:** The files in `/tmp/touch-lab` evaporate at reboot, but the playbook in `/root/rhcsa_journal/lab-07b/playbooks/` does not. After a reboot we could re-run `ansible-playbook .../task1.yml` and the **pinned** file would be recreated with mtime `2024-01-15` — proof of timestamp persistence by replay. We test that in Task 2.

### Journal write — BEFORE cleanup

```bash
LAB=lab-07b
TASK=task1
JDIR="/root/rhcsa_journal/${LAB}/${TASK}"
mkdir -p "$JDIR"
cp /tmp/touch-lab/task1/check.txt "$JDIR/check.txt"
cp /tmp/touch-lab/task1/apply.txt "$JDIR/apply.txt"
cp /tmp/touch-lab/task1/post.txt  "$JDIR/post.txt"

cat > "$JDIR/done.txt" <<EOF
LAB:    ${LAB}
TASK:   ${TASK}
DATE:   $(date -Is)
USER:   $(whoami)@$(hostname)
STATUS: COMPLETE
EOF

cat > "$JDIR/notes.txt" <<EOF
TOPIC:    ansible.builtin.file state=touch with pinned modification_time + access_time
COMMANDS: ansible-playbook --check --diff, ansible-playbook, register, debug
TRAPS:    T07-B rehearsed (used the module, NOT command: touch) · T07-C reviewed (kept default %Y%m%d%H%M.%S format)
MISSED:   (fill in if any ⚠️ flags)
NEXT:     task2 — re-run to expose T07-A (pinned=changed=0; bare=changed=1)
EOF

ls -la "$JDIR"
echo "exit was: $?"
```

### 🧹 Cleanup

```bash
# Keep the playbook AND the files — Task 2 re-runs against them
rm -rf /tmp/touch-lab/task1
ls /tmp/touch-lab/
echo "exit was: $?"
```

### Troubleshoot

| Symptom | Fix |
|---|---|
| `ansible-playbook: command not found` | Return to Lab 00 — control node not installed |
| `couldn't resolve module 'ansible.builtin.file'` | `ansible-core` broken — reinstall |
| Mode shows `0744` after `mode: 0644` | YAML stripped the leading 0 — **quote the mode string** |
| Timestamps not what you set | Check `modification_time_format:` — default is `%Y%m%d%H%M.%S`, NOT ISO 8601 (T07-C) |
| Apply succeeded but `stat` shows wrong mtime | Likely supplied `modification_time:` in ISO 8601 without overriding the format — fix and re-run |

> **STOP — paste the PLAY RECAP line of the apply run AND the `═══ ansible-pinned.txt` block from `post.txt` before Task 2.**

---

## Task 2 — The contrast: re-run for idempotence — pinned form (`changed=0`) vs bare-touch form (`changed=1`)

**Practice directory this task:** `/tmp/touch-lab/` — the same files from Task 1, re-evaluated. This task **deliberately demonstrates** Trap T07-A by re-running the same playbook and showing one task reports `changed=0` (the pinned form) and one reports `changed=1` (the bare-touch form).

### 🔁 Warm-Up — commands woven into Task 2

```bash
ls /tmp/touch-lab                                   2>&1 | tee /tmp/touch-lab/pre-task2.txt
test -f /tmp/touch-lab/ansible-pinned.txt && echo "pinned file OK"
test -f /tmp/touch-lab/ansible-now.txt    && echo "now file OK"
stat -c 'pinned mtime=%y' /tmp/touch-lab/ansible-pinned.txt
stat -c 'now    mtime=%y' /tmp/touch-lab/ansible-now.txt
ansible --version | head -n 1
set -o pipefail
echo "Warm-up done by $(whoami) at $(date -Is)"
echo "exit was: $?"
```

> Carry from Task 1: the `stat -c '%y'` reflex carries forward. Before AND after the re-run, we record the mtime so the diff is undeniable.

### Purpose

Re-run the **exact same playbook** from Task 1 and prove that the **pinned** task reports `changed=0` while the **bare-touch** task reports `changed=1`. This is the canonical RHCE proof of two things at once: pinned `state: touch` IS idempotent, and bare `state: touch` is NOT (by design) — and you, as the candidate, know exactly which form to use when idempotence is the requirement.

### 🧵 WEAVE TRACE — warm-up commands re-used in this task body

| Warm-up command | Role inside Task 2 |
|---|---|
| `stat -c '%y'` before AND after | The before/after pair is the proof of the contrast |
| `test -f` | Confirms each target is present before re-run |
| `2>&1 \| tee` | Captures the re-run output to `task2/rerun.txt` — the proof artifact |
| `set -o pipefail` | Ensures the `tee` chain reports a failed `ansible-playbook` honestly |
| `$(date -Is)` | Stamps the journal `notes.txt` |
| `ansible --version` | Confirms toolchain (rules out version-skew false negatives) |

### Main command block

```bash
mkdir -p /tmp/touch-lab/task2

# 1. Snapshot mtimes BEFORE the re-run
{
  echo "═══ BEFORE re-run ═══"
  stat -c 'pinned mtime=%y atime=%x' /tmp/touch-lab/ansible-pinned.txt
  stat -c 'now    mtime=%y atime=%x' /tmp/touch-lab/ansible-now.txt
} 2>&1 | tee /tmp/touch-lab/task2/rerun.txt

# 2. Re-run the SAME playbook from Task 1 — no edits
ansible-playbook /root/rhcsa_journal/lab-07b/playbooks/task1.yml \
  2>&1 | tee -a /tmp/touch-lab/task2/rerun.txt

# 3. The CRITICAL grep — extract the per-task changed flags
echo "═══ PER-TASK CHANGED FLAGS ═══" | tee -a /tmp/touch-lab/task2/rerun.txt
grep -E "TASK \[Touch|PLAY RECAP|changed=|ok: \[localhost\]|changed: \[localhost\]" \
  /tmp/touch-lab/task2/rerun.txt | tail -n 20 | tee -a /tmp/touch-lab/task2/rerun.txt

# 4. Snapshot mtimes AFTER the re-run — the proof artifact
{
  echo "═══ AFTER re-run ═══"
  stat -c 'pinned mtime=%y atime=%x' /tmp/touch-lab/ansible-pinned.txt
  stat -c 'now    mtime=%y atime=%x' /tmp/touch-lab/ansible-now.txt
} 2>&1 | tee -a /tmp/touch-lab/task2/rerun.txt

# 5. The DIFF — pinned mtime must be UNCHANGED; now mtime must be NEWER
echo "═══ DIFF SUMMARY ═══" | tee -a /tmp/touch-lab/task2/rerun.txt
echo "  PINNED expectation: mtime UNCHANGED between BEFORE and AFTER (still 2024-01-15)" | tee -a /tmp/touch-lab/task2/rerun.txt
echo "  NOW    expectation: mtime BUMPED — now reflects the re-run timestamp"           | tee -a /tmp/touch-lab/task2/rerun.txt

echo "exit was: $?"
```

### The playbook (`task2.yml` — the SAME playbook as task1, re-run for contrast)

```yaml
---
# Re-run /root/rhcsa_journal/lab-07b/playbooks/task1.yml — no edits.
# This task does NOT need a new YAML file; the proof is in re-applying
# the existing playbook and observing the per-task changed flags.
#
# If you want a separate task2.yml for grading clarity, it would be
# identical to task1.yml with only the play name changed:
#
- name: "Lab 07b Task 2 — re-run task1 for idempotence proof"
  hosts: localhost
  connection: local
  gather_facts: false

  vars:
    sandbox: /tmp/touch-lab
    target_mtime: "202401151200.00"
    target_atime: "202001010000.00"

  tasks:
    - name: "Re-assert pinned state=touch (must report changed=0)"
      ansible.builtin.file:
        path: "{{ sandbox }}/ansible-pinned.txt"
        state: touch
        owner: root
        group: root
        mode: '0644'
        modification_time: "{{ target_mtime }}"
        access_time: "{{ target_atime }}"
      register: re_touch_pinned

    - name: "Re-assert bare state=touch (DELIBERATELY reports changed=1 — T07-A demo)"
      ansible.builtin.file:
        path: "{{ sandbox }}/ansible-now.txt"
        state: touch
        mode: '0600'
      register: re_touch_now

    - name: "Show idempotence proof — pinned must be changed=False, now will be changed=True"
      ansible.builtin.debug:
        msg:
          - "pinned changed: {{ re_touch_pinned.changed }}  (expected: False — IDEMPOTENT)"
          - "now    changed: {{ re_touch_now.changed }}  (expected: True  — T07-A demo)"
```

### Human-readable breakdown

1. Structurally identical to `task1.yml` — same hosts, connection, vars, module calls. The only meaningful difference is the play name and the more useful debug message.
2. Re-running produces the canonical contrast:
   - **Pinned task** reports `changed=False`. The module reads the actual mtime (`2024-01-15`), compares to the requested `target_mtime` (`202401151200.00` → `2024-01-15 12:00`), sees they match, and does nothing.
   - **Bare-touch task** reports `changed=True`. With no `modification_time:`, the module defaults to "now" — and now is different from whatever was on disk a second ago, so the module updates atime+mtime and reports the change.
3. PLAY RECAP shows `changed=1` (not 0!) because one of the two `state: touch` calls really did make a change. That single `changed=1` is the **trap**: if a grader asked "make this play fully idempotent" you would have to **pin** both timestamps on the bare-touch task too.
4. The DIFF SUMMARY block makes the proof undeniable — pinned mtime is UNCHANGED between BEFORE and AFTER snapshots; now mtime is BUMPED. The filesystem itself confirms the contrast.

### Reading it left to right

- `grep -E "TASK \[Touch|PLAY RECAP|changed="` — extended regex matching three patterns: task headers starting with "Touch", the PLAY RECAP line, and any `changed=` mention. Captures just the audit-critical lines.
- `tail -n 20` — caps the captured lines to the last 20 so the journal stays readable.
- The two `stat -c '%y %x'` blocks (BEFORE and AFTER) are the **filesystem-side** proof. Even if the PLAY RECAP was misread, the on-disk mtimes settle the question.

### The story

Idempotence is **the** RHCE concept — and `state: touch` is the one module state that does NOT default to idempotent. Graders know this; they will write a question like "the play must be re-runnable and report no changes on second run" specifically to see whether candidates recognize the trap. The win is two-fold: (a) you wrote the pinned form correctly the first time, and (b) you can explain WHY the bare form is non-idempotent and demonstrate the fix on the fly.

The discipline that flows from this lab: every time you write `state: touch`, ask yourself "does this need to be idempotent?" If yes — pin both timestamps. If no — leave it bare, but **document the choice** (a comment in the play or a note in the journal) so the grader knows you made it on purpose.

### Expected output

```text
═══ BEFORE re-run ═══
pinned mtime=2024-01-15 12:00:00.000000000 -0500 atime=2020-01-01 00:00:00.000000000 -0500
now    mtime=2026-05-27 15:00:01.xxx -0400 atime=2026-05-27 15:00:01.xxx -0400

PLAY [Lab 07b Task 1 — create files via ansible.builtin.file: state=touch] ****
TASK [Ensure the sandbox directory exists] ************************************
ok: [localhost]
TASK [Touch ansible-pinned.txt — pinned mtime + atime (IDEMPOTENT FORM)] ******
ok: [localhost]                          <-- NOT changed — pinned matches
TASK [Touch ansible-now.txt — NO timestamps pinned (NON-IDEMPOTENT — T07-A demo)]
changed: [localhost]                     <-- changed=1 because default = NOW
TASK [Show register results] **************************************************
ok: [localhost] => { "msg": ["pinned changed: False", "now    changed: True"] }
PLAY RECAP ********************************************************************
localhost                  : ok=4    changed=1    unreachable=0    failed=0

═══ AFTER re-run ═══
pinned mtime=2024-01-15 12:00:00.000000000 -0500 atime=2020-01-01 00:00:00.000000000 -0500
now    mtime=2026-05-27 15:00:05.xxx -0400 atime=2026-05-27 15:00:05.xxx -0400

═══ DIFF SUMMARY ═══
  PINNED expectation: mtime UNCHANGED between BEFORE and AFTER (still 2024-01-15)
  NOW    expectation: mtime BUMPED — now reflects the re-run timestamp
exit was: 0
```

> The key line: in the PLAY RECAP, `changed=1`. The `1` is **not a bug** — it is the documented T07-A behaviour. The **pinned** task contributed `0` to that count; the **bare** task contributed `1`. To make the whole play `changed=0` on re-run, both tasks must pin their timestamps.

### Switches

| Token | Meaning |
|---|---|
| `grep -E "A\|B"` | Extended regex — match line containing A or B |
| `tail -n 20` | Last 20 lines — cap noisy output |
| `tee -a` | Append (not truncate) to the named file |
| `stat -c '%y %x'` | mtime + atime on one line — compact diff format |

### 🧠 Concept Card

|   | Concept | What it does |
|---|---|---|
|   | Idempotence proof | Re-run must show `changed=0`; that is the RHCE acceptance test |
|   | Pinned vs bare `state: touch` | Pinned = idempotent; bare = always `changed=1` (deliberate) |
|   | PLAY RECAP audit | The bottom-line metric: `ok=N changed=M`. M should be 0 on re-run unless you have an intentional bare-touch |
|   | Filesystem cross-check | The BEFORE/AFTER `stat` pair is the on-disk proof — independent of PLAY RECAP |
|   | Documenting non-idempotence | If you keep a bare-touch on purpose, comment WHY in the play or in the journal |
| 🪤 | **Trap Risk T07-A** | Re-run shows `changed=1` because timestamps were not pinned — graders mark it down. Fix: pin both `modification_time:` and `access_time:`. |

### 🔁 PERSISTENCE CHECK

| What was configured | Verification command | Why it matters |
|---|---|---|
| Pinned form is idempotent | `grep 'pinned changed: False' /tmp/touch-lab/task2/rerun.txt` | Must match |
| Bare form is non-idempotent | `grep 'now    changed: True' /tmp/touch-lab/task2/rerun.txt` | Must match (the T07-A demo) |
| Pinned mtime survived re-run | `stat -c '%y' /tmp/touch-lab/ansible-pinned.txt \| grep -c '2024-01-15'` | Must be `1` |
| Playbooks survive reboot | `ls /root/rhcsa_journal/lab-07b/playbooks/` | The playbook directory is on `/root/`, not `/tmp/` |

> **Reboot reasoning:** After a reboot, `/tmp/touch-lab` is empty. Re-running the Task 1 playbook **re-creates** `ansible-pinned.txt` with mtime `2024-01-15` (because the pinned timestamps are stored in the playbook itself, not on disk). That is the deepest form of cross-reboot idempotence: the play recreates the file AND restores the historic mtime — every time. Lab 07c Task 2 proves this end-to-end.

### Journal write — BEFORE cleanup

```bash
LAB=lab-07b
TASK=task2
JDIR="/root/rhcsa_journal/${LAB}/${TASK}"
mkdir -p "$JDIR"
cp /tmp/touch-lab/task2/rerun.txt "$JDIR/rerun.txt"

cat > "$JDIR/done.txt" <<EOF
LAB:    ${LAB}
TASK:   ${TASK}
DATE:   $(date -Is)
USER:   $(whoami)@$(hostname)
STATUS: COMPLETE
EOF

cat > "$JDIR/notes.txt" <<EOF
TOPIC:    Idempotence proof — pinned state=touch (changed=0) vs bare state=touch (changed=1)
COMMANDS: ansible-playbook (rerun), grep "PLAY RECAP|changed=", stat -c '%y %x'
TRAPS:    T07-A rehearsed (deliberately exposed the trap and explained the fix — pin both timestamps)
MISSED:   (fill in if any ⚠️ flags)
NEXT:     lab-07c — auditor seat: stat + find + ls --time=ctime + simulated-reboot persistence
EOF

ls -la "$JDIR"
echo "exit was: $?"
```

### 🧹 Cleanup

```bash
# Keep the journal + playbook; drop the sandbox transcript only
rm -rf /tmp/touch-lab/task2
ls /tmp/touch-lab/
echo "exit was: $?"
```

### Troubleshoot

| Symptom | Fix |
|---|---|
| Pinned task re-run shows `changed=1` | Either the file's actual mtime drifted (something else touched it) or the `modification_time_format:` doesn't match the input string (T07-C). |
| Bare task re-run shows `changed=0` | Almost impossible — would mean the file's mtime is exactly "now" (same second as Ansible's clock). If you see this, double-check the timestamp granularity on the filesystem. |
| `grep PLAY RECAP` returns nothing | `tee` failed silently — `set -o pipefail` was not active. |
| Both tasks show `changed=1` first run AND second run | Filesystem may not support sub-second precision; the second-run pinned task may see a tiny drift. Try storing mtime as `202401151200.00` (with `.00` seconds) — the explicit seconds force the comparison. |

> **STOP — paste the PLAY RECAP line, the `pinned changed: False` / `now changed: True` debug output, AND the BEFORE/AFTER stat block before moving on to Lab 07c.**

---

## Lab 07b Checklist (2 tasks)

- [ ] Task 1 — Write the playbook (pinned + bare forms) + `--check --diff` preview + apply + `register:`/`debug:` evidence + journal evidence
- [ ] Task 2 — Re-run for idempotence proof: pinned reports `changed=False`, bare deliberately reports `changed=True` (T07-A demonstrated and explained) + journal evidence

---

## 🔗 Related Labs in the Trilogy

| Lab | Connection |
|---|---|
| **Lab 07a** — RHCSA hand-typed timestamps | The imperative form: `touch -t / -d / -r / -a / -m` + `find -mtime` |
| **Lab 07c** — Verifying Timestamps | The auditor seat: prove with `stat` + `find -newer` + `ls --time=atime/ctime` + simulated reboot |
| Lab 00 — Ansible Control Node Setup | Prerequisite — without a working control node, this lab cannot start |
| Lab 11b — Removing Files via Ansible | The complementary declarative pattern: `state: absent` (always idempotent by design) |

---

## 👤 Author

**Kelvin R. Tobias**
[kelvinintech.com](https://kelvinintech.com) · [GitHub](https://github.com/kelvintechnical) · [LinkedIn](https://www.linkedin.com/in/kelvin-r-tobias-211949219)
