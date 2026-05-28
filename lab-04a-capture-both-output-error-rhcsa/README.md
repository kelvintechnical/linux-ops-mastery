# Lab 04a: Capture Both Output and Error (RHCSA) - `&>`, `2>&1`, `> file 2>&1`

- **Series:** linux-ops-mastery - Shells, Terminals, and Redirection
- **Trilogy:** `04a` -> [`04b`](../lab-04b-capture-both-output-error-ansible/) -> [`04c`](../lab-04c-capture-both-output-error-verify/)
- **Prerequisite:** [`Lab 01a`](../lab-01a-stdout-redirection-rhcsa/), [`Lab 02a`](../lab-02a-stderr-redirection-rhcsa/), [`Lab 03a`](../lab-03a-pipe-text-streams-rhcsa/)
- **Focus traps:** `T04-A` (wrong order `2>&1 > file`), `T04-B` (`&>` is bash-only), `T41`, `T44`
- **Practice directory rotation #04:** `/lib64`
- **Time estimate:** 25-35 minutes
- **Tasks:** **exactly 2**

---

## LAB HEADER BLOCK

```bash
echo "ENV:  ${ENV:-DECLARE_ME}"
echo "DISK: $(lsblk 2>/dev/null | awk '$NF=="disk"{print "/dev/"$1}' | paste -sd, -)"
echo "NIC:  $(ip -o addr show 2>/dev/null | awk '$2!="lo"{print $2}' | sort -u | paste -sd, -)"
echo "SE:   $(getenforce 2>/dev/null || echo n/a)"
echo "OS:   $(cat /etc/redhat-release 2>/dev/null || grep PRETTY_NAME /etc/os-release)"
echo "TIME: $(date -Is)"
echo "USER: $(whoami)@$(hostname)"
echo "TRAPS THIS LAB: T04-A T04-B T41 T44"
echo "PRACTICE DIR: /lib64"
echo ""
echo "/lib64 quick context:"
ls -ld /lib64
readlink -f /lib64
echo "Shell: $BASH_VERSION"
```

> **STOP - Paste header output before Lab-Wide Setup.**

---

## Objective

By the end of this lab you can:

1. Capture stdout and stderr together using `> file 2>&1` and bash shorthand `&>`.
2. Explain why `2>&1 > file` is wrong for "capture both" intent.
3. Prove the difference with reproducible line-count checks.
4. Keep a full, reviewable transcript under Tier B sandbox controls.

---

## Lab-Wide Setup (Tier B Sandbox, required before Task 1)

```bash
sudo -i

export LAB_NUM=04
export LAB_SLUG=both
export SANDBOX=/tmp/lab04a
export GROUP=labgrp_${LAB_NUM}_${LAB_SLUG}
export USER=labuser_${LAB_NUM}_${LAB_SLUG}
export USER_HOME=${SANDBOX}/home_${USER}

mkdir -p "${SANDBOX}" "${USER_HOME}"
mkdir -p /root/rhcsa_journal/lab-04a/task1
mkdir -p /root/rhcsa_journal/lab-04a/task2

cat > "${SANDBOX}/THIS_DIRECTORY.txt" <<'EOF'
Practice directory: /lib64
/lib64 usually points to the architecture-specific 64-bit shared libraries path
(commonly /usr/lib64). Dynamic linker/loader dependencies for many binaries are
resolved from here. It is a realistic read target for RHCSA redirection drills
because commands against /lib64 can produce normal output and error output.
EOF

getent group "${GROUP}" >/dev/null || groupadd "${GROUP}"
getent passwd "${USER}" >/dev/null || useradd -d "${USER_HOME}" -M -s /bin/bash -g "${GROUP}" "${USER}"
chown -R "${USER}:${GROUP}" "${SANDBOX}"
chmod 755 "${SANDBOX}" "${USER_HOME}"

id "${USER}"
ls -ld "${SANDBOX}" "${USER_HOME}" /lib64
getent group "${GROUP}"
getent passwd "${USER}"
cat "${SANDBOX}/THIS_DIRECTORY.txt"
echo "setup exit: $?"
```

> **STOP - Paste `id`, `ls -ld`, both `getent` lines, and first two lines of `THIS_DIRECTORY.txt`.**

---

## Task 1 - Canonical capture both (`> file 2>&1` or `&>`)

### Warm-Up

```bash
ls -ld /lib64                                      2>&1 | tee /tmp/lab04a/warmup-task1.txt
ls /lib64 | head -n 5
id
set -o pipefail
echo "warm-up done $(date -Is)"
echo "exit: $?"
```

### WEAVE TRACE

| Warm-up / prep command | Role in task |
|---|---|
| `ls -ld /lib64` | Confirms source path exists |
| `ls /lib64 | head -n 5` | Shows expected stdout shape |
| `set -o pipefail` | Preserves non-zero status in pipe chains |
| `${USER}` sandbox vars | Enables Tier B proof run as non-root lab user |

### Purpose

Use the **correct combined redirection** form and verify that stderr text (`cannot access`) is captured in the same file as normal output.

### Main command block

```bash
TASKLOG=/tmp/lab04a/task1.txt
COMBINED=/tmp/lab04a/combined.log

echo "=== Task 1 canonical combined capture ===" 2>&1 | tee "${TASKLOG}"

# Canonical correct form (portable):
ls /lib64 /nonexistent > "${COMBINED}" 2>&1

# Bash equivalent (optional alternate):
# ls /lib64 /nonexistent &> "${COMBINED}"

echo "-- verification --" | tee -a "${TASKLOG}"
grep -c "cannot access" "${COMBINED}" | tee -a "${TASKLOG}"
wc -l "${COMBINED}" | tee -a "${TASKLOG}"
head -n 6 "${COMBINED}" | tee -a "${TASKLOG}"

echo "Trap reminder: order matters, but wrong-order demo is Task 2 (T04-A)." | tee -a "${TASKLOG}"

echo "=== Tier B run as ${USER} with 2>&1 | tee ===" | tee -a "${TASKLOG}"
sudo -u "${USER}" bash -c 'ls /lib64 /nonexistent 2>&1 | tee '"${USER_HOME}"'/task1-asuser.log >/dev/null'
stat -c '%U:%G %a %n' "${USER_HOME}/task1-asuser.log" | tee -a "${TASKLOG}"
grep -c "cannot access" "${USER_HOME}/task1-asuser.log" | tee -a "${TASKLOG}"

echo "task1 exit: $?"
```

### Human-readable breakdown

1. `> combined.log` redirects stdout to file.
2. `2>&1` then points stderr at the **current stdout destination** (same file).
3. `grep -c "cannot access"` proves stderr landed in the file.
4. Tier B run writes combined text as `${USER}` using `2>&1 | tee`.

### Reading left to right

- `ls /lib64 /nonexistent > combined.log 2>&1`
- `>` happens first: FD1 -> `combined.log`
- `2>&1` happens second: FD2 -> wherever FD1 is now (`combined.log`)

### The story

When an exam prompt says "save command output," graders often expect both useful data and errors. The reliable muscle memory is `> file 2>&1` (portable) or `&> file` (bash). This task locks that in before the order trap in Task 2.

### Expected output

```text
=== Task 1 canonical combined capture ===
-- verification --
1
23 /tmp/lab04a/combined.log
ls: cannot access '/nonexistent': No such file or directory
/lib64:
ld-linux-x86-64.so.2
...
=== Tier B run as labuser_04_both with 2>&1 | tee ===
labuser_04_both:labgrp_04_both 644 /tmp/lab04a/home_labuser_04_both/task1-asuser.log
1
```

### Switches table

| Token | Meaning |
|---|---|
| `> file` | Redirect stdout (FD1) to file (truncate/create) |
| `2>&1` | Redirect stderr (FD2) to current FD1 target |
| `&> file` | Bash shorthand for `> file 2>&1` |
| `grep -c` | Count matching lines |
| `wc -l` | Count total lines |
| `2>&1 \| tee file` | Merge, display, and write together |

### Concept Card

| Concept | What it means |
|---|---|
| Combined capture | Both stdout and stderr end up in one file |
| Canonical portable form | `> file 2>&1` works in POSIX shells |
| Bash shorthand | `&>` is shorter but bash-specific |
| Verification habit | Use `grep -c "cannot access"` + `wc -l` |
| Trap Risk - T04-A | Wrong order `2>&1 > file` leaves stderr on screen |
| Trap Risk - T04-B | `&>` may fail in `/bin/sh`; use `> file 2>&1` there |

### PERSISTENCE CHECK

| Check | Command | Pass condition |
|---|---|---|
| Combined file exists | `test -s /tmp/lab04a/combined.log` | non-empty |
| stderr captured | `grep -c "cannot access" /tmp/lab04a/combined.log` | `>= 1` |
| evidence transcript exists | `test -s /tmp/lab04a/task1.txt` | non-empty |
| Tier B user file ownership | `stat -c '%U:%G' "${USER_HOME}/task1-asuser.log"` | `${USER}:${GROUP}` |

### Journal write

```bash
LAB=lab-04a
TASK=task1
JDIR="/root/rhcsa_journal/${LAB}/${TASK}"
mkdir -p "${JDIR}"

cp /tmp/lab04a/task1.txt "${JDIR}/evidence.txt"
cp /tmp/lab04a/combined.log "${JDIR}/combined.log"
cp "${USER_HOME}/task1-asuser.log" "${JDIR}/task1-asuser.log"

cat > "${JDIR}/notes.txt" <<EOF
TOPIC: capture both output and error with > file 2>&1 (or &> in bash)
VERIFY: grep -c "cannot access", wc -l, head
TIER_B: sudo -u ${USER} wrote task1-asuser.log via 2>&1 | tee
NEXT: task2 contrast wrong order vs correct order
EOF

ls -la "${JDIR}"
echo "journal exit: $?"
```

### Cleanup (per-task, keep sandbox)

```bash
rm -f /tmp/lab04a/warmup-task1.txt /tmp/lab04a/combined.log /tmp/lab04a/task1.txt
rm -f "${USER_HOME}/task1-asuser.log"
ls -la /tmp/lab04a
echo "cleanup task1 exit: $?"
```

### Troubleshoot

| Symptom | Fix |
|---|---|
| `cannot access` count is 0 | You likely redirected stderr away (`2>/dev/null`) by mistake |
| `&>` gives syntax error | You are not in bash; use `> file 2>&1` |
| Tier B file owned by root | Your `sudo -u` block did not include the write operation |
| combined file missing | Re-run main block and verify path variables |

> **STOP - Paste Task 1 `grep -c`, `wc -l`, and Tier B `stat` line before Task 2.**

---

## Task 2 - Contrast trap (`2>&1 > file`) vs correct forms

### Warm-Up

```bash
ls -la /tmp/lab04a                                  2>&1 | tee /tmp/lab04a/warmup-task2.txt
ls /lib64 | head -n 3
id
set -o pipefail
echo "warm-up done $(date -Is)"
echo "exit: $?"
```

### WEAVE TRACE

| Warm-up / prep command | Role in task |
|---|---|
| `ls -la /tmp/lab04a` | Confirms task area is present |
| `ls /lib64 | head` | Baseline stdout data |
| `set -o pipefail` | Keeps errors visible in pipelines |
| `id` | Confirms current identity before Tier B append step |

### Purpose

Demonstrate **wrong order** first (`2>&1 > wrong.log`), then show two correct captures (`> right.log 2>&1` and `&> both.log`) and prove the difference numerically.

### Main command block

```bash
TASKLOG=/tmp/lab04a/task2.txt
WRONG=/tmp/lab04a/wrong.log
RIGHT=/tmp/lab04a/right.log
BOTH=/tmp/lab04a/both.log

echo "=== Task 2 order trap contrast ===" 2>&1 | tee "${TASKLOG}"

echo "-- WRONG order (T04-A) --" | tee -a "${TASKLOG}"
ls /lib64 /nonexistent 2>&1 > "${WRONG}"

echo "-- CORRECT order --" | tee -a "${TASKLOG}"
ls /lib64 /nonexistent > "${RIGHT}" 2>&1

echo "-- BASH shorthand --" | tee -a "${TASKLOG}"
ls /lib64 /nonexistent &> "${BOTH}"

W_ERR=$(grep -c "cannot access" "${WRONG}" 2>/dev/null || echo 0)
R_ERR=$(grep -c "cannot access" "${RIGHT}" 2>/dev/null || echo 0)
B_ERR=$(grep -c "cannot access" "${BOTH}" 2>/dev/null || echo 0)

echo "wrong cannot-access count: ${W_ERR}" | tee -a "${TASKLOG}"
echo "right cannot-access count: ${R_ERR}" | tee -a "${TASKLOG}"
echo "both  cannot-access count: ${B_ERR}" | tee -a "${TASKLOG}"
wc -l "${WRONG}" "${RIGHT}" "${BOTH}" | tee -a "${TASKLOG}"
head -n 4 "${WRONG}" | tee -a "${TASKLOG}"
head -n 4 "${RIGHT}" | tee -a "${TASKLOG}"
head -n 4 "${BOTH}"  | tee -a "${TASKLOG}"

# Tier B weave: ownership hardening + user append with signed line
chown "${USER}:${GROUP}" "${RIGHT}"
chmod 664 "${RIGHT}"
sudo -u "${USER}" bash -c 'echo "[signed $(date -Is)] '"${USER}"' validated right.log" 2>&1 | tee -a '"${RIGHT}"' >/dev/null'
stat -c '%U:%G %a %n' "${RIGHT}" | tee -a "${TASKLOG}"
tail -n 2 "${RIGHT}" | tee -a "${TASKLOG}"

echo "task2 exit: $?"
```

### Human-readable breakdown

1. Wrong order command sends stderr to screen, not to `wrong.log`.
2. Correct order and `&>` both capture stderr and stdout together.
3. `grep -c "cannot access"` proves wrong file has `0`, right/both have `>=1`.
4. Tier B weave sets ownership and mode, then appends a signed line as `${USER}` through `2>&1 | tee -a`.

### Reading left to right

- Wrong: `ls /lib64 /nonexistent 2>&1 > wrong.log`
  - Step 1: `2>&1` points stderr to current stdout (terminal)
  - Step 2: `>` moves stdout to file; stderr stays on terminal
- Correct: `ls /lib64 /nonexistent > right.log 2>&1`
  - Step 1: stdout to file
  - Step 2: stderr follows stdout into file

### The story

Most redirection incidents are not syntax failures - they are **order failures**. Engineers think both symbols are present, so behavior should match. Shells do not work that way: each token mutates FD state in sequence. Task 2 builds the exam-safe reflex: file redirect first, `2>&1` second.

### Expected output

```text
=== Task 2 order trap contrast ===
-- WRONG order (T04-A) --
ls: cannot access '/nonexistent': No such file or directory
-- CORRECT order --
-- BASH shorthand --
wrong cannot-access count: 0
right cannot-access count: 1
both  cannot-access count: 1
  22 /tmp/lab04a/wrong.log
  23 /tmp/lab04a/right.log
  23 /tmp/lab04a/both.log
...
labuser_04_both:labgrp_04_both 664 /tmp/lab04a/right.log
[signed 2026-05-28T... ] labuser_04_both validated right.log
```

### Switches table

| Token | Meaning |
|---|---|
| `2>&1 > file` | Wrong for combined capture intent |
| `> file 2>&1` | Correct portable combined capture |
| `&> file` | Bash shorthand for combined capture |
| `tee -a` | Append while also printing stream |
| `chown` | Set owner and group |
| `chmod 664` | Owner+group write, world read |

### Concept Card

| Concept | What it means |
|---|---|
| Left-to-right processing | Redirections are applied in sequence |
| Wrong-order result | stderr remains terminal-bound |
| Correct-order result | stderr and stdout both go to file |
| Proof pattern | `grep -c "cannot access"` on each file |
| Trap Risk - T04-A | `2>&1 > file` silently fails capture intent |
| Trap Risk - T44 | Skip cleanup and leave lab user/group behind |

### PERSISTENCE CHECK

| Check | Command | Pass condition |
|---|---|---|
| wrong file trap proven | `grep -c "cannot access" /tmp/lab04a/wrong.log` | `0` (or missing) |
| right file correct | `grep -c "cannot access" /tmp/lab04a/right.log` | `>=1` |
| both file correct | `grep -c "cannot access" /tmp/lab04a/both.log` | `>=1` |
| right ownership after Tier B append | `stat -c '%U:%G %a' /tmp/lab04a/right.log` | `${USER}:${GROUP} 664` |
| task2 transcript exists | `test -s /tmp/lab04a/task2.txt` | non-empty |

### Journal write

```bash
LAB=lab-04a
TASK=task2
JDIR="/root/rhcsa_journal/${LAB}/${TASK}"
mkdir -p "${JDIR}"

cp /tmp/lab04a/task2.txt "${JDIR}/evidence.txt"
cp /tmp/lab04a/wrong.log "${JDIR}/wrong.log"
cp /tmp/lab04a/right.log "${JDIR}/right.log"
cp /tmp/lab04a/both.log  "${JDIR}/both.log"

cat > "${JDIR}/notes.txt" <<EOF
TOPIC: wrong order vs correct order for 2>&1
PROOF: wrong=0 cannot-access, right>=1, both>=1
TIER_B: chown/chmod + sudo -u ${USER} signed append via 2>&1 | tee -a
NEXT: move to lab 04b then 04c in trilogy
EOF

ls -la "${JDIR}"
echo "journal exit: $?"
```

### Cleanup (per-task, keep sandbox)

```bash
rm -f /tmp/lab04a/warmup-task2.txt /tmp/lab04a/task2.txt
rm -f /tmp/lab04a/wrong.log /tmp/lab04a/right.log /tmp/lab04a/both.log
ls -la /tmp/lab04a
echo "cleanup task2 exit: $?"
```

### Troubleshoot

| Symptom | Fix |
|---|---|
| wrong log also has error lines | You likely ran the correct order by accident |
| right log has 0 errors | Check command included `/nonexistent` and `2>&1` |
| `&>` fails | Run in bash or use `> file 2>&1` |
| signed line missing | Validate `sudo -u ... tee -a` target path and permissions |

> **STOP - Paste wrong/right/both `grep -c` counts and final `stat` line.**

---

## Lab Closeout - Section 6 bulletproof teardown (run after Task 2)

```bash
set +e

# 1) Kill remaining processes owned by lab user (if any)
pkill -u "${USER}" 2>/dev/null

# 2) Remove sandbox artifacts
rm -rf "${SANDBOX}"

# 3) Remove lab user
if getent passwd "${USER}" >/dev/null 2>&1; then
  userdel -r "${USER}" 2>/dev/null
fi

# 4) Remove lab group
if getent group "${GROUP}" >/dev/null 2>&1; then
  groupdel "${GROUP}" 2>/dev/null
fi

# 5) Audit teardown state
echo "---- closeout audit ----"
getent passwd "${USER}" >/dev/null && echo "FAIL user remains" || echo "OK user removed"
getent group "${GROUP}" >/dev/null && echo "FAIL group remains" || echo "OK group removed"
test -d "${SANDBOX}" && echo "FAIL sandbox remains" || echo "OK sandbox removed"
test -d "${USER_HOME}" && echo "FAIL user_home remains" || echo "OK user_home removed"

# 6) Final exit and handoff note
set -e
echo "Lab 04a closeout complete at $(date -Is)"
echo "Proceed with trilogy: 04a -> 04b -> 04c"
```

> **STOP - Paste all four `OK ... removed` audit lines.**

---

## Lab 04a Checklist

- [ ] Lab header block captured
- [ ] Tier B setup complete with `LAB_SLUG=both` and `/tmp/lab04a/THIS_DIRECTORY.txt`
- [ ] Task 1 canonical combined capture verified
- [ ] Task 2 wrong-vs-right trap proven
- [ ] Section 6 closeout audit passed

---

## Author

**Kelvin R. Tobias**  
[kelvinintech.com](https://kelvinintech.com) - [GitHub](https://github.com/kelvintechnical) - [LinkedIn](https://www.linkedin.com/in/kelvin-r-tobias-211949219)
# Lab 04a: Capture Both Output and Error (RHCSA) — `&>`, `2>&1`

- **Series:** linux-ops-mastery — Shells, Terminals & Redirection
- **Trilogy:** `04a` (RHCSA hand-typed) → [`04b`](../lab-04b-capture-both-output-error-ansible/) (Ansible — `register:` splits stdout/stderr) → [`04c`](../lab-04c-capture-both-output-error-verify/) (Verify capstone — audit + persistence)
- **Career arcs covered:** RHCSA EX200 (every "save the output" task where errors matter as much as data), RHCE EX294 (Ansible `register:` exposes both streams separately), SRE (incident logs that must capture warnings and data together), DevOps (CI job logs are combined-stream by default)
- **Prerequisite:** [`Lab 01a`](../lab-01a-stdout-redirection-rhcsa/) + [`Lab 01c`](../lab-01c-stdout-redirection-verify/) (stdout + Tier B) · [`Lab 02a`](../lab-02a-stderr-redirection-rhcsa/) + [`Lab 02c`](../lab-02c-stderr-redirection-verify/) (stderr + Tier B) · [`Lab 03a`](../lab-03a-pipe-text-streams-rhcsa/) + [`Lab 03c`](../lab-03c-pipe-text-streams-verify/) (pipes + tee)
- **Time Estimate:** 25–35 minutes
- **Tasks:** 2 (Task 1 = bash `&>` merge + `&>>` append + `sudo -u ${USER}` weave · Task 2 = POSIX `> file 2>&1` vs wrong-order `2>&1 > file` — **T04-A**)
- **Practice Directory (rotation #10):** `/var`
- **Sandbox (Tier B per Section 1.5):** `/tmp/lab04a` with `USER=labuser_04_combo`, `GROUP=labgrp_04_combo`, `USER_HOME=/tmp/lab04a/home_labuser_04_combo`. Built in Lab-Wide Setup; torn down + audited in **Lab Closeout** after Task 2.
- **Traps rehearsed this lab:** **T04-A** (`2>&1` placed before `>` — stderr stays on terminal) · **T04-B** (two separate appends `>>file 2>>file` instead of `>> file 2>&1`) · **T41** (skipping verification — done in 04c) · **T44** (cleanup-left-orphan-user — Lab Closeout audit block proves no residue)

> **This lab's practice directory is: `/var`** — `/var` holds data that grows over time: logs in `/var/log`, mail spools, package databases. Every combined-stream capture in production eventually lands here. RHCSA exams love `find /var` and `grep /var/log` tasks that generate both useful output and `Permission denied` noise.

---

## LAB HEADER BLOCK

```bash
echo "🖥️  ENV:   ${ENV:-DECLARE_ME}"
echo "💿  DISK:  $(lsblk 2>/dev/null | awk '$NF=="disk"{print "/dev/"$1}' | paste -sd, -)"
echo "🌐  NIC:   $(ip -o addr show 2>/dev/null | awk '$2!="lo"{print $2}' | sort -u | paste -sd, -)"
echo "🔐  SE:    $(getenforce 2>/dev/null || echo n/a)"
echo "📦  OS:    $(cat /etc/redhat-release 2>/dev/null || grep PRETTY_NAME /etc/os-release)"
echo "🕒  TIME:  $(date -Is)"
echo "👤  USER:  $(whoami)@$(hostname)"
echo "⚠️  TRAP REMINDERS THIS LAB: T04-A T04-B T41"
echo "📁  PRACTICE DIR: /var"
echo ""
echo "💡 /var context (our combined-stream source):"
ls -ld /var /var/log
ls /var/log | wc -l
du -sh /var/log 2>/dev/null | head -1
echo "Shell version: $BASH_VERSION"
```

> **STOP — paste header output before running setup.**

---

## Objective

Stop missing half the evidence. By the end of this lab you can:

1. Merge stdout and stderr into one file with bash `&>` (overwrite) and `&>>` (append).
2. Use the POSIX-portable form `> file 2>&1` and explain why operator order matters.
3. Prove the **T04-A trap**: `2>&1 > file` sends stderr to the terminal, not the file.
4. Capture a combined stream AS `${USER}` so the evidence file lands with lab-user ownership.

The capstone pattern: *"Run `find /var/log -type f` and save both the matching paths and any `Permission denied` errors to a single log file."* Every RHCSA exam has a variation where stderr is part of the answer.

---

## Concept: Two Streams, One Destination

You already know stdout (FD 1) and stderr (FD 2) are independent. To capture both into one place, make FD 2 point at the same destination as FD 1.

```
   ┌─────────────────────────────────────────────────────┐
   │   Your command (find, ls, dnf, journalctl ...)    │
   ├─────────────────────────────────────────────────────┤
   │   FD 1  stdout  ────┐                               │
   │                     ├──>  ONE file (or /dev/null)   │
   │   FD 2  stderr  ────┘                               │
   └─────────────────────────────────────────────────────┘

   `cmd &> file`            bash shorthand — merge then write
   `cmd > file 2>&1`        POSIX — open file on FD1, THEN clone FD1 onto FD2
   `cmd 2>&1 > file`        WRONG — clones the terminal onto FD2, then redirects FD1 only
```

**Key facts:**
- Redirections are evaluated **left to right**.
- `2>&1` is a **snapshot** of where FD 1 currently points — whatever you do to FD 1 *after* `2>&1` does not retroactively change FD 2.
- `$?` after a redirect is the **command's** exit code, not the redirect's.

---

## Combined-Stream Reference

| Operator / Command | What it does |
|---|---|
| `cmd &> file` | Bash — both streams to file (truncate) |
| `cmd &>> file` | Bash — both streams to file (append) |
| `cmd > file 2>&1` | POSIX — both streams to file (truncate) |
| `cmd >> file 2>&1` | POSIX — both streams to file (append) |
| `cmd 2>&1 > file` | POSIX syntax, **wrong intent** — stderr stays on terminal |
| `cmd &> /dev/null` | Discard both streams |
| `cmd 2>&1 \| grep PAT` | Merge before pipe — stderr-aware filtering |
| `cmd 2>&1 \| tee file` | Merge, display, and save simultaneously |

---

## Lab-Wide Setup — Tier B Sandbox Stack (Section 1.5)

```bash
sudo -i

export LAB_NUM=04
export LAB_SLUG=combo
export SANDBOX=/tmp/lab04a
export GROUP=labgrp_${LAB_NUM}_${LAB_SLUG}
export USER=labuser_${LAB_NUM}_${LAB_SLUG}
export USER_HOME=${SANDBOX}/home_${USER}

mkdir -p "${SANDBOX}" "${USER_HOME}"
mkdir -p /root/rhcsa_journal/lab-04a/task1
mkdir -p /root/rhcsa_journal/lab-04a/task2

# Directory context file (Section 1 — rotation #10 /var)
cat > "${SANDBOX}/THIS_DIRECTORY.txt" <<'EOF'
Practice directory: /var
/var holds data that grows over time. /var/log has system logs.
/var/spool has print and mail queues. /var/lib has package manager
databases. Filling /var crashes logging and breaks package installs.
RHCSA exams constantly test log inspection and find/grep against /var.
Combined-stream capture (&>, 2>&1) is how you save a complete audit
trail from commands that read /var/log and hit Permission denied.
EOF

getent group  "${GROUP}" >/dev/null || groupadd "${GROUP}"
getent passwd "${USER}"  >/dev/null || useradd \
    -d "${USER_HOME}" -M -s /bin/bash -g "${GROUP}" "${USER}"
chown -R "${USER}:${GROUP}" "${SANDBOX}"

id     "${USER}"
ls -ld "${SANDBOX}" "${USER_HOME}" /var /var/log
getent group  "${GROUP}"
getent passwd "${USER}"
echo "Sandbox built by $(whoami) at $(date -Is)"
echo "exit was: $?"
```

> **STOP — paste the `id`, four `ls -ld`, and both `getent` lines before Task 1.**

> **Why `${USER}` matters for combined streams:** running `find /var/log` as root sees no permission errors. Running it as `${USER}` generates real `Permission denied` lines — the same scenario the exam presents when it says "save ALL output."

---

## Task 1 — Merge with bash `&>` and accumulate with `&>>`

**Practice directory this task:** `/var/log` — we `find` and `ls` against log files, capturing both successful paths and permission errors into one file.

### 🔁 Warm-Up

```bash
ls /var/log | wc -l                                    2>&1 | tee /tmp/lab04a/warmup.txt
ls /var/log /nope 2>/dev/null | head -n 3
find /var/log -maxdepth 1 -type f 2>/dev/null | wc -l
grep -c 'Permission denied' /tmp/lab04a/warmup.txt 2>/dev/null || echo "0 (warmup has no errors yet)"
set -o pipefail
echo "Warm-up done by $(whoami) at $(date -Is)"
echo "exit was: $?"
```

> Carry from Lab 03a: `2>&1 | tee FILE` captures transcripts. Carry from Lab 02a: `2>/dev/null` silences noise when you only want stdout.

### Purpose

Build the bash combined-stream muscle:

1. Prove `>` alone misses stderr (reconnect Lab 01a/02a).
2. Capture both streams with `&>` into a single evidence file.
3. Append a second capture with `&>>` without destroying the first.
4. Run the same capture AS `${USER}` so the file is owned by the lab user.

### 🧵 WEAVE TRACE

| Warm-up / setup command | Role inside Task 1 |
|---|---|
| `ls /var/log \| wc -l` | Baseline line count for the log directory |
| `ls /var/log /nope` | Generates both stdout and stderr on the same command |
| `find /var/log -maxdepth 1` | The find pattern reused in the main block |
| `2>&1 \| tee` | Transcript capture pattern from prior labs |
| `${USER}` (Tier B) | Part D runs `find \| &>` AS `${USER}` — file ownership proves sudo -u ran |

### Main command block

```bash
TASKLOG=/tmp/lab04a/task1.txt

# ── Part A: prove split streams (Lab 01a + 02a recap) ────────────────
echo "═══ Part A: split vs combined ═══"                  2>&1 | tee $TASKLOG
ls /var/log /nope > /tmp/lab04a/stdout-only.txt 2>/dev/null
wc -l /tmp/lab04a/stdout-only.txt                        | tee -a $TASKLOG
grep -c 'Permission denied' /tmp/lab04a/stdout-only.txt \
    || echo "stderr lines in stdout-only file: 0"          | tee -a $TASKLOG

# ── Part B: bash &> merge ─────────────────────────────────────────────
echo "═══ Part B: &> merge from /var/log ═══"              | tee -a $TASKLOG
find /var/log -maxdepth 2 -type f &> /tmp/lab04a/combined.txt
wc -l /tmp/lab04a/combined.txt                           | tee -a $TASKLOG
grep -c 'Permission denied' /tmp/lab04a/combined.txt     | tee -a $TASKLOG
head -n 3 /tmp/lab04a/combined.txt                       | tee -a $TASKLOG

# ── Part C: &>> append a second run ─────────────────────────────────
echo "═══ Part C: &>> append second capture ═══"          | tee -a $TASKLOG
echo "=== Pass 2 $(date -Is) ===" &>> /tmp/lab04a/combined.txt
ls /var/log /nope &>> /tmp/lab04a/combined.txt
wc -l /tmp/lab04a/combined.txt                           | tee -a $TASKLOG
grep -c '=== Pass 2' /tmp/lab04a/combined.txt            | tee -a $TASKLOG

# ── Part D: combined capture AS ${USER} (Tier B weave) ───────────────
echo "═══ Part D: find &> AS ${USER} ═══"                 | tee -a $TASKLOG
sudo -u "${USER}" bash -c \
    'find /var/log -maxdepth 2 -type f \
        &> '"${USER_HOME}"'/combined-asuser.txt'

stat -c '%U:%G %a %n' "${USER_HOME}/combined-asuser.txt" | tee -a $TASKLOG
U_LINES=$(wc -l < "${USER_HOME}/combined-asuser.txt")
U_ERRS=$(grep -c 'Permission denied' "${USER_HOME}/combined-asuser.txt" || echo 0)
echo "as-${USER} lines: ${U_LINES}  permission-denied: ${U_ERRS}" | tee -a $TASKLOG
test "${U_LINES}" -gt 0 \
    && echo "✅ combined capture ran as ${USER}, file owned by ${USER}:${GROUP}" \
    || echo "❌ Tier B combined capture produced empty output" \
    | tee -a $TASKLOG

echo "exit was: $?"
```

### Human-readable breakdown

1. **Part A** — `ls /var/log /nope > stdout-only.txt 2>/dev/null` deliberately silences stderr. The file has paths but zero `Permission denied` lines — incomplete evidence.
2. **Part B** — `find /var/log ... &>` opens one file and binds both FD 1 and FD 2. `grep -c 'Permission denied'` proves stderr landed in the same file as stdout.
3. **Part C** — `&>>` appends a second capture. The first pass's content is preserved — same lesson as `>>` vs `>` from Lab 01a, applied to combined streams.
4. **Part D** — `sudo -u ${USER}` runs the same `find &>` as the lab user. `stat` confirms ownership; line count proves real output.

### Reading it left to right

```
find /var/log -maxdepth 2 -type f   &>   /tmp/lab04a/combined.txt
│                                    │    │
│                                    │    └─ Target file — both streams land here
│                                    └─ Bash merge operator (shorthand for > file 2>&1)
└─ Command whose stdout AND stderr we capture
```

### The story

Cron jobs run unattended. When a nightly backup script uses `find /data > /backup/list.txt`, the `Permission denied` warnings scroll to nowhere — or worse, fill the mail spool. One character change — `&>` instead of `>` — keeps the complete record. That's why every production crontab worth running ends with `&>> /var/log/job.log`.

### Expected output

```text
═══ Part A: split vs combined ═══
234 /tmp/lab04a/stdout-only.txt
stderr lines in stdout-only file: 0
═══ Part B: &> merge from /var/log ═══
87 /tmp/lab04a/combined.txt
3
/var/log/audit/audit.log
/var/log/boot.log
/var/log/cron
═══ Part C: &>> append second capture ═══
295 /tmp/lab04a/combined.txt
1
═══ Part D: find &> AS labuser_04_combo ═══
labuser_04_combo:labgrp_04_combo 644 /tmp/lab04a/home_labuser_04_combo/combined-asuser.txt
as-labuser_04_combo lines: 84  permission-denied: 5
✅ combined capture ran as labuser_04_combo, file owned by labuser_04_combo:labgrp_04_combo
```

### Switches

| Token | Meaning |
|---|---|
| `&> file` | Bash — send stdout + stderr to file (truncate) |
| `&>> file` | Bash — send stdout + stderr to file (append) |
| `> file 2>/dev/null` | stdout only — stderr discarded (incomplete capture) |
| `grep -c 'PAT' file` | Count matching lines in file |
| `sudo -u USER bash -c 'cmd &> FILE'` | Combined capture as USER — file lands on USER |
| `stat -c '%U:%G %a %n' FILE` | Owner:group, mode, name |

### 🧠 Concept Card

| Concept | What it does |
|---|---|
| `&>` | Bash sugar for `> file 2>&1` — one operator, both streams |
| `&>>` | Append form — preserves prior combined-stream content |
| Split capture incomplete | `>` + `2>/dev/null` loses stderr evidence |
| Tier B `sudo -u` combined capture | Same `&>` as root, but file owned by `${USER}:${GROUP}` |
| **🪤 Trap Risk T04-B** | `>>file 2>>file` opens two separate appends — bytes can interleave. **Fix:** `>> file 2>&1` or `&>> file`. |
| **🪤 Trap Risk T41** | Saving only stdout when the prompt says "save the output" — grader checks for errors too. Always default to combined capture. |

### 🔁 PERSISTENCE CHECK

| What was configured | Verification command | Why it matters |
|---|---|---|
| Combined file has both streams | `grep -c 'Permission denied' /tmp/lab04a/combined.txt` > 0 | `&>` captured stderr |
| Append preserved prior content | `grep -c '=== Pass 2' /tmp/lab04a/combined.txt` returns 1 | `&>>` did not truncate |
| Tier B file owned by USER | `stat -c '%U' "${USER_HOME}/combined-asuser.txt"` returns `${USER}` | sudo -u actually ran |
| Task log exists | `test -s /tmp/lab04a/task1.txt` | Evidence ready for journal |

> **Reboot note:** `/tmp` is tmpfs. Journal copies survive reboot; `/tmp/lab04a/` does not.

### Journal write

```bash
LAB=lab-04a
TASK=task1
JDIR="/root/rhcsa_journal/${LAB}/${TASK}"
mkdir -p "$JDIR"
cp /tmp/lab04a/task1.txt                    "$JDIR/evidence.txt"
cp /tmp/lab04a/combined.txt                 "$JDIR/combined.txt"
cp "${USER_HOME}/combined-asuser.txt"       "$JDIR/combined-asuser.txt"

cat > "$JDIR/done.txt" <<EOF
LAB:    ${LAB}
TASK:   ${TASK}
DATE:   $(date -Is)
USER:   $(whoami)@$(hostname)
LAB_USER: ${USER}
LAB_GROUP: ${GROUP}
STATUS: COMPLETE
EOF

cat > "$JDIR/notes.txt" <<EOF
TOPIC:    &> merge, &>> append, split-vs-combined proof, sudo -u ${USER} combined capture
COMMANDS: &>, &>>, >, 2>/dev/null, find, grep -c, stat -c '%U:%G', sudo -u ${USER} bash -c
TRAPS:    T04-B preview (split >> vs combined &>>); T41 preview
TIER B:   combined-asuser.txt owned by ${USER}:${GROUP}; permission-denied lines present
MISSED:   (fill in if any ⚠️ flags)
NEXT:     task2 — POSIX > file 2>&1 vs wrong-order 2>&1 > file (T04-A) + sudo -u order proof
EOF

ls -la "$JDIR"
echo "exit was: $?"
```

### 🧹 Cleanup (per-task — leaves Tier B sandbox intact)

```bash
rm -f /tmp/lab04a/stdout-only.txt /tmp/lab04a/combined.txt
rm -f /tmp/lab04a/warmup.txt /tmp/lab04a/task1.txt
rm -f "${USER_HOME}/combined-asuser.txt"

getent passwd "${USER}"  >/dev/null && echo "✅ ${USER} still present"
getent group  "${GROUP}" >/dev/null && echo "✅ ${GROUP} still present"
test -d       "${SANDBOX}"          && echo "✅ ${SANDBOX} still present"

ls /tmp/lab04a
echo "exit was: $?"
```

### Troubleshoot

| Symptom | Fix |
|---|---|
| `grep -c 'Permission denied'` returns 0 on combined file | You ran as root — retry Part D as `${USER}`, or remove `2>/dev/null` from Part A |
| `&>` syntax error | You are in `/bin/sh` not bash — use `> file 2>&1` instead |
| `&>>` overwrote prior content | You wrote `&>` on the second run — use `&>>` for append |
| Part D: empty combined-asuser.txt | `${USER}` has no read access to `/var/log` — expected; file should still have *some* stderr lines |

> **STOP — paste the `grep -c 'Permission denied'` count from Part B and the Part D `✅ combined capture` line before Task 2.**

---

## Task 2 — POSIX `> file 2>&1` and the order-matters trap (T04-A)

**Practice directory this task:** `/var/log` — same source; we compare correct vs wrong operator order and prove the trap under `${USER}`.

### 🔁 Warm-Up

```bash
ls -la /tmp/lab04a                                     2>&1 | tee /tmp/lab04a/warmup2.txt
journalctl --no-pager -n 3 2>/dev/null | wc -l
ls /var/log /nope 2>&1 | wc -l
set -o pipefail
echo "Warm-up done by $(whoami) at $(date -Is)"
echo "exit was: $?"
```

> Carry from Task 1: `&>`, `grep -c`, `stat -c`. Add `2>&1 | wc -l` — merging before pipe.

### Purpose

Three skills:

1. **POSIX form** — `> file 2>&1` produces the same result as `&>` but works in `/bin/sh`.
2. **T04-A demonstration** — `2>&1 > file` sends stderr to the terminal; only stdout reaches the file.
3. **Merge-then-pipe** — `cmd 2>&1 | tee file` captures combined stream while passing it downstream.

### 🧵 WEAVE TRACE

| Warm-up / setup command | Role inside Task 2 |
|---|---|
| `ls -la /tmp/lab04a` | Confirms Task 1 cleanup ran |
| `journalctl --no-pager -n 3` | Another `/var`-adjacent command for the merge-then-pipe demo |
| `ls /var/log /nope 2>&1 \| wc -l` | Proves merge-before-pipe counts both streams |
| `set -o pipefail` | On by default — pipe stages fail loudly |
| `${USER}` (Tier B) | Part D runs the order trap AS `${USER}` — proves T04-A is identity-independent |

### Main command block

```bash
TASKLOG=/tmp/lab04a/task2.txt

# ── Part A: correct POSIX order ───────────────────────────────────────
echo "═══ Part A: > correct.log 2>&1 ═══"                2>&1 | tee $TASKLOG
ls /var/log /nope > /tmp/lab04a/correct.log 2>&1
CORRECT_LINES=$(wc -l < /tmp/lab04a/correct.log)
CORRECT_ERRS=$(grep -c 'Permission denied' /tmp/lab04a/correct.log || echo 0)
echo "correct.log lines: ${CORRECT_LINES}  errors: ${CORRECT_ERRS}" | tee -a $TASKLOG

# ── Part B: WRONG order — T04-A trap ─────────────────────────────────
echo "═══ Part B: 2>&1 > wrong.log (T04-A trap) ═══"      | tee -a $TASKLOG
ls /var/log /nope 2>&1 > /tmp/lab04a/wrong.log
WRONG_LINES=$(wc -l < /tmp/lab04a/wrong.log)
WRONG_ERRS=$(grep -c 'Permission denied' /tmp/lab04a/wrong.log || echo 0)
echo "wrong.log lines: ${WRONG_LINES}  errors: ${WRONG_ERRS}" | tee -a $TASKLOG

if test "${CORRECT_ERRS}" -gt 0 -a "${WRONG_ERRS}" -eq 0; then
    echo "✅ T04-A proven — wrong order lost stderr"       | tee -a $TASKLOG
else
    echo "❌ T04-A not demonstrated — re-check operator order" | tee -a $TASKLOG
fi

# ── Part C: merge-then-pipe with tee ─────────────────────────────────
echo "═══ Part C: 2>&1 | tee evidence ═══"               | tee -a $TASKLOG
find /var/log -maxdepth 1 -type f 2>&1 \
    | tee /tmp/lab04a/tee-evidence.txt \
    | wc -l                                              | tee -a $TASKLOG
grep -c 'Permission denied' /tmp/lab04a/tee-evidence.txt | tee -a $TASKLOG

# ── Part D: order trap under sudo -u (Tier B weave) ──────────────────
echo "═══ Part D: order trap AS ${USER} ═══"              | tee -a $TASKLOG
sudo -u "${USER}" bash -c '
    ls /var/log /nope > '"${USER_HOME}"'/order-correct.txt 2>&1
    ls /var/log /nope 2>&1 > '"${USER_HOME}"'/order-wrong.txt
    {
        echo "correct lines: $(wc -l < '"${USER_HOME}"'/order-correct.txt)"
        echo "wrong lines:   $(wc -l < '"${USER_HOME}"'/order-wrong.txt)"
        echo "correct errs:  $(grep -c "Permission denied" '"${USER_HOME}"'/order-correct.txt || echo 0)"
        echo "wrong errs:    $(grep -c "Permission denied" '"${USER_HOME}"'/order-wrong.txt || echo 0)"
    } > '"${USER_HOME}"'/order-trap.txt
'

cat "${USER_HOME}/order-trap.txt"                        | tee -a $TASKLOG
stat -c '%U:%G %a %n' "${USER_HOME}/order-trap.txt"      | tee -a $TASKLOG

grep -q 'wrong errs:    0' "${USER_HOME}/order-trap.txt" \
    && grep -q 'correct errs:' "${USER_HOME}/order-trap.txt" \
    && echo "✅ T04-A proven under sudo -u ${USER}" \
    || echo "❌ order trap did not produce expected contrast" \
    | tee -a $TASKLOG

echo "exit was: $?"
```

### Human-readable breakdown

1. **Part A** — `> correct.log 2>&1`: shell opens the file on FD 1, then duplicates FD 1 onto FD 2. Both streams flow into the file.
2. **Part B** — `2>&1 > wrong.log`: `2>&1` runs first when FD 1 still points at the terminal, so FD 2 also points at the terminal. The subsequent `>` only rebinds FD 1. stderr never reaches the file.
3. **Part C** — `2>&1 | tee` merges before the pipe, so `tee` receives both streams and writes the complete record.
4. **Part D** — same contrast AS `${USER}`. The order-trap.txt file documents line counts and error counts for both orderings.

### Reading it left to right

```
ls /var/log /nope   >   correct.log   2>&1
│                    │   │              │
│                    │   │              └─ "Send FD 2 to wherever FD 1 is NOW" (= the file)
│                    │   └─ FD 1 → file (opened with O_TRUNC)
│                    └─ Redirect FD 1
└─ Command

ls /var/log /nope   2>&1   >   wrong.log
│                    │      │
│                    │      └─ FD 1 → file (FD 2 still → terminal!)
│                    └─ "Send FD 2 to wherever FD 1 is NOW" (= terminal)
└─ Command
```

### The story

T04-A is the single most common shell redirection bug since 1977. Every senior engineer learned it by debugging a cron log that had data but no errors — or errors on screen but an empty file. The fix is one rule: **the operator that opens the file goes first; `2>&1` goes second.** Always.

### Expected output

```text
═══ Part A: > correct.log 2>&1 ═══
correct.log lines: 238  errors: 1
═══ Part B: 2>&1 > wrong.log (T04-A trap) ═══
wrong.log lines: 237  errors: 0
✅ T04-A proven — wrong order lost stderr
═══ Part C: 2>&1 | tee evidence ═══
42
0
═══ Part D: order trap AS labuser_04_combo ═══
correct lines: 238
wrong lines:   237
correct errs:  1
wrong errs:    0
labuser_04_combo:labgrp_04_combo 644 /tmp/lab04a/home_labuser_04_combo/order-trap.txt
✅ T04-A proven under sudo -u labuser_04_combo
exit was: 0
```

### Switches

| Token | Meaning |
|---|---|
| `> file 2>&1` | POSIX — correct order: open file, then clone FD 1 onto FD 2 |
| `2>&1 > file` | Wrong order — stderr stays on terminal |
| `2>&1 \| tee file` | Merge both streams, then split to file + stdout |
| `2>&1 \| wc -l` | Count lines from both streams combined |

### 🧠 Concept Card

| Concept | What it does |
|---|---|
| Left-to-right evaluation | Each redirection is processed in order; later ops don't retroactively fix earlier ones |
| `2>&1` snapshot | Copies FD 1's **current** destination onto FD 2 |
| `&>` vs `> file 2>&1` | Identical result; `&>` is bash-only, `2>&1` is POSIX |
| Merge-then-pipe | `2>&1 \| next` sends both streams into the pipeline |
| **🪤 Trap Risk T04-A** | `2>&1 > file` — stderr on screen, file has stdout only. **Fix:** always `> file 2>&1`. |
| **🪤 Trap Risk T04-B** | Two separate `>>` operators instead of one combined append. **Fix:** `>> file 2>&1`. |

### 🔁 PERSISTENCE CHECK

| What was configured | Verification command | Why it matters |
|---|---|---|
| Correct order captured stderr | `grep -c 'Permission denied' correct.log` > 0 | POSIX form works |
| Wrong order lost stderr | `grep -c 'Permission denied' wrong.log` = 0 | T04-A demonstrated |
| tee evidence complete | `test -s /tmp/lab04a/tee-evidence.txt` | Merge-then-pipe wrote file |
| Tier B order trap | `grep 'wrong errs:    0' order-trap.txt` | Trap reproducible under sudo -u |

### Journal write

```bash
LAB=lab-04a
TASK=task2
JDIR="/root/rhcsa_journal/${LAB}/${TASK}"
mkdir -p "$JDIR"
cp /tmp/lab04a/task2.txt                    "$JDIR/evidence.txt"
cp /tmp/lab04a/correct.log                  "$JDIR/correct.log"
cp /tmp/lab04a/wrong.log                    "$JDIR/wrong.log"
cp /tmp/lab04a/tee-evidence.txt             "$JDIR/tee-evidence.txt"
cp "${USER_HOME}/order-trap.txt"            "$JDIR/order-trap.txt"
cp "${USER_HOME}/order-correct.txt"         "$JDIR/order-correct.txt"
cp "${USER_HOME}/order-wrong.txt"           "$JDIR/order-wrong.txt"

cat > "$JDIR/done.txt" <<EOF
LAB:    ${LAB}
TASK:   ${TASK}
DATE:   $(date -Is)
USER:   $(whoami)@$(hostname)
LAB_USER: ${USER}
LAB_GROUP: ${GROUP}
STATUS: COMPLETE
EOF

cat > "$JDIR/notes.txt" <<EOF
TOPIC:    POSIX > file 2>&1; T04-A wrong order; 2>&1 | tee merge-then-pipe; sudo -u order trap
COMMANDS: > file 2>&1, 2>&1 > file, 2>&1 | tee, grep -c, wc -l, sudo -u ${USER} bash -c
TRAPS:    T04-A rehearsed (correct errs > 0, wrong errs = 0); T04-B noted
TIER B:   order-trap.txt owned by ${USER}:${GROUP}; T04-A identical under sudo -u
MISSED:   (fill in if any ⚠️ flags)
NEXT:     lab-04b — Ansible register: stdout_lines + stderr_lines; lab-04c — verify capstone
EOF

ls -la "$JDIR"
echo "exit was: $?"
```

### 🧹 Cleanup (per-task — leaves Tier B sandbox intact)

```bash
rm -f /tmp/lab04a/correct.log /tmp/lab04a/wrong.log
rm -f /tmp/lab04a/tee-evidence.txt /tmp/lab04a/warmup2.txt /tmp/lab04a/task2.txt
rm -f "${USER_HOME}/order-trap.txt" "${USER_HOME}/order-correct.txt" "${USER_HOME}/order-wrong.txt"

getent passwd "${USER}"  >/dev/null && echo "✅ ${USER} still present"
getent group  "${GROUP}" >/dev/null && echo "✅ ${GROUP} still present"
test -d       "${SANDBOX}"          && echo "✅ ${SANDBOX} still present"

ls /tmp/lab04a
echo "exit was: $?"
```

### Troubleshoot

| Symptom | Fix |
|---|---|
| T04-A not proven (both files have errors) | Operator order wrong in Part B — must be `2>&1 > wrong.log` with no space issues |
| `2>&1` printed as literal text | You quoted it — `'2>&1'` is a string, not a redirect |
| Part C tee file empty | Upstream `find` produced no output — check `/var/log` exists |
| Part D: order-trap.txt missing | sudo -u block had a quoting error — check nested quotes |

> **STOP — paste the `✅ T04-A proven` line from Part B and Part D before Lab Closeout.**

---

## Lab Closeout — Bulletproof Teardown (Section 6)

```bash
set +e

# 1) Mount layer (no-op)
awk -v s="${SANDBOX}" '$2 ~ s {print $2}' /proc/mounts \
    | tac | xargs -r -n1 umount -l 2>/dev/null

# 2) User / group teardown
if getent passwd "${USER}" >/dev/null 2>&1; then
    userdel -r "${USER}" 2>/dev/null
fi
if getent group "${GROUP}" >/dev/null 2>&1; then
    groupdel "${GROUP}"  2>/dev/null
fi

# 3) Sandbox dir
rm -rf "${SANDBOX}"

# 4) Audit
echo "── Lab 04a cleanup audit ──"
getent passwd "${USER}"  >/dev/null && echo "❌ user remains"    || echo "✅ user gone"
getent group  "${GROUP}" >/dev/null && echo "❌ group remains"   || echo "✅ group gone"
test -d "${SANDBOX}"                && echo "❌ sandbox remains" || echo "✅ sandbox gone"
test -d "${USER_HOME}"              && echo "❌ home remains"    || echo "✅ home gone"

set -e
echo "Cleanup complete by $(whoami) at $(date -Is)"
echo "exit was: $?"
```

> **STOP — paste the four `✅` audit lines before moving to Lab 04b.**

---

## Lab 04a Checklist (2 tasks + closeout)

- [ ] Lab-Wide Setup — Tier B sandbox built; `/var` context file created; `id ${USER}`, both `getent` lines visible
- [ ] Task 1 — `&>` captured stderr; `&>>` appended; Part D `sudo -u ${USER}` combined file owned by lab user
- [ ] Task 2 — correct order has errors, wrong order has zero (T04-A); merge-then-pipe tee works; Part D order trap under sudo -u
- [ ] Lab Closeout — four `✅` audit lines; journal in `/root/rhcsa_journal/lab-04a/` survives

---

## Related Labs

| Lab | Connection |
|---|---|
| **Lab 04b** — Combined Streams Ansible | `register:` splits stdout/stderr — the Ansible view of combined capture |
| **Lab 04c** — Combined Streams Verify | Audit + destroy-restore for combined-stream evidence |
| Lab 01a — Stdout Redirection | FD 1 side of combined capture |
| Lab 02a — Stderr Redirection | FD 2 side of combined capture |
| Lab 03a — Pipe Text Streams | `2>&1 \| tee` merge-then-pipe builds on pipe + tee |

---

## Author

**Kelvin R. Tobias**
[kelvinintech.com](https://kelvinintech.com) · [GitHub](https://github.com/kelvintechnical) · [LinkedIn](https://www.linkedin.com/in/kelvin-r-tobias-211949219)
