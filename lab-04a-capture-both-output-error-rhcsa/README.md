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

## Related Labs

| Lab | Connection |
|---|---|
| **Lab 04b** — Combined Output Ansible | `ansible.builtin.shell` with `2>&1` embedded in `cmd:` |
| **Lab 04c** — Combined Output Verify | Audits wrong-order vs correct-order evidence from this lab |
| **Lab 02a** — Stderr Redirection | Built the stderr half; this lab merges both streams |
| **Lab 01a** — Stdout Redirection | Built the stdout half |

---

## Author

**Kelvin R. Tobias**  
[kelvinintech.com](https://kelvinintech.com) · [GitHub](https://github.com/kelvintechnical) · [LinkedIn](https://www.linkedin.com/in/kelvin-r-tobias-211949219)
