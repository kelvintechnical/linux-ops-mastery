# Lab 02c: Verifying Standard Error Redirection (Capstone) — Audit + Persistence Drill

- **Series:** linux-ops-mastery — Shells, Terminals & Redirection
- **Trilogy:** [`02a`](../lab-02a-stderr-redirection-rhcsa/) (RHCSA hand-typed) → [`02b`](../lab-02b-stderr-redirection-ansible/) (Ansible — `ansible.builtin.shell` with `register:` exposing `stderr_lines`) → **`02c`** (Verify — you are here)
- **Career arcs covered:** RHCSA EX200 (every "save stderr separately" task), SRE (post-incident stderr archeology — was the `Permission denied` really there, or did somebody redirect it away?), DevOps (CI failure forensics), AI/MLOps (training-job error capture audit)
- **Prerequisite:** [`Lab 02a`](../lab-02a-stderr-redirection-rhcsa/) completed; `/root/rhcsa_journal/lab-02a/task1/` and `task2/` populated
- **Time Estimate:** 25–35 minutes
- **Tasks:** 2 (Task 1 = audit 02a artifacts: stdout/stderr separation, ownership, Form A vs Form B · Task 2 = destroy-restore drill for the cumulative error log — **T41 rehearsal**)
- **Practice Directory (rotation #02):** `/var/log` (same as 02a)
- **Sandbox (Tier B per Section 1.5):** `/tmp/lab02c` with `USER=labuser_02_verify`, `GROUP=labgrp_02_verify`, `USER_HOME=/tmp/lab02c/home_labuser_02_verify`. Built in Lab-Wide Setup; torn down + audited in **Lab Closeout** after Task 2.
- **Traps rehearsed this lab:** **T02-A** (order-trap proof — verify Form A and Form B captured different things) · **T41** (destroy-restore drill against the cumulative error log) · **T42** (fix-live-forget-persistent — verbalize before Lab Closeout) · **T44** (cleanup audit)

> **This lab's practice directory is: `/var/log`** — same source as 02a. We don't re-generate the errors; we audit the captured evidence from 02a and prove the stderr/stdout files can be destroyed and rebuilt from the journal.

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
echo "⚠️  TRAP REMINDERS THIS LAB: T02-A T41 T42 T44"
echo "📁  PRACTICE DIR: /var/log"
echo ""
echo "💡 /var/log context (stderr source for re-runs):"
ls -ld /var/log
ls /var/log | head -n 5
echo ""
echo "📓 02a journal (must already exist):"
ls -la /root/rhcsa_journal/lab-02a/task1/ /root/rhcsa_journal/lab-02a/task2/
echo "Shell version: $BASH_VERSION"
```

> **STOP — paste header output before running setup. If the `ls -la /root/rhcsa_journal/lab-02a/...` lines are empty, GO BACK and finish Lab 02a first.**

---

## Objective

02a built the stderr-capture reflex. 02c proves the evidence is real and survives a wipe.

1. **Audit** the four kinds of files 02a left in the journal: split-capture stdout (`log-files.txt`), split-capture stderr (`log-errors.txt`), Form A merged file (`formA.txt`), Form B "merged" file that actually wasn't (`formB.txt`).
2. **Prove the order-trap (T02-A) actually happened** — Form A must contain `Permission denied` lines IN the file; Form B must not. If both contain stderr, 02a's order-trap demo didn't run as designed.
3. **Verify the Tier B accumulation** — `cum-errors-asuser.txt` must be owned by `labuser_02_stderr` (02a's user) and have a non-zero line count. If owned by root, the `sudo -u` step never ran in 02a.
4. **Survive the destroy-restore drill (T41)** — wipe `/tmp/lab02a/` (if it lingers) and our `/tmp/lab02c/` sandbox; rebuild the cumulative error log from the journal; re-run a `find` *as* 02c's `${USER}` to confirm the rebuild still produces real `Permission denied` content.

---

## Concept: Verification Treats stderr as Evidence, Not Noise

In 02a, stderr was something to capture cleanly or silence. In 02c, stderr **is** the evidence you're auditing — because `Permission denied` lines prove a non-root user ran the command:

```
   ┌───────────────────────────────────────────────────────────────────┐
   │  02a outputs                  │  02c audit asks                   │
   ├───────────────────────────────────────────────────────────────────┤
   │  log-files.txt                │  Has lines? Are they real .log paths?
   │  log-errors.txt               │  Has lines? Are they Permission denied?
   │  formA.txt                    │  Contains stderr IN the file?
   │  formB.txt                    │  Does NOT contain stderr in the file?
   │  cum-errors-asuser.txt        │  Owned by labuser_02_stderr? Non-empty?
   └───────────────────────────────────────────────────────────────────┘
```

The four-way matrix above is the entire 02c reading list. Each row maps to one assertion. Every assertion fails loudly (`❌`) or passes loudly (`✅`).

---

## Lab-Wide Setup — Tier B Sandbox Stack (Section 1.5)

```bash
sudo -i

export LAB_NUM=02
export LAB_SLUG=verify
export SANDBOX=/tmp/lab02c
export GROUP=labgrp_${LAB_NUM}_${LAB_SLUG}
export USER=labuser_${LAB_NUM}_${LAB_SLUG}
export USER_HOME=${SANDBOX}/home_${USER}

mkdir -p "${SANDBOX}" "${USER_HOME}"
mkdir -p /root/rhcsa_journal/lab-02c/task1
mkdir -p /root/rhcsa_journal/lab-02c/task2

getent group  "${GROUP}" >/dev/null || groupadd "${GROUP}"
getent passwd "${USER}"  >/dev/null || useradd \
    -d "${USER_HOME}" -M -s /bin/bash -g "${GROUP}" "${USER}"
chown -R "${USER}:${GROUP}" "${SANDBOX}"

id     "${USER}"
ls -ld "${SANDBOX}" "${USER_HOME}"
getent group  "${GROUP}"
getent passwd "${USER}"
echo "Sandbox built by $(whoami) at $(date -Is)"
echo "exit was: $?"
```

> **STOP — paste the `id`, `ls -ld`, and `getent` lines before Task 1. `labuser_02_verify` is distinct from 02a's `labuser_02_stderr` on purpose — the auditor isn't the creator.**

---

## Task 1 — Audit the 02a stderr evidence

**Practice directory this task:** `/tmp/lab02c` for writes; reads against `/root/rhcsa_journal/lab-02a/`.

### Warm-Up

```bash
ls -la /root/rhcsa_journal/lab-02a/                    2>&1 | tee /tmp/lab02c/warmup.txt
find /root/rhcsa_journal/lab-02a -type f | sort
wc -l /root/rhcsa_journal/lab-02a/task*/*.txt 2>/dev/null
stat -c '%U:%G %a %n' /root/rhcsa_journal/lab-02a/task2/cum-errors-asuser.txt 2>/dev/null
set -o pipefail
echo "Warm-up done by $(whoami) at $(date -Is)"
echo "exit was: $?"
```

> Carry from Lab 02a: `wc -l`, `stat -c '%U:%G %a %n'`, `grep -c`, `find -type f`.

### Purpose

Five assertions over the 02a journal evidence:

1. **Completeness** — `log-files.txt`, `log-errors.txt`, `formA.txt`, `formB.txt`, `cum-results-asuser.txt`, `cum-errors-asuser.txt` are all present and non-empty.
2. **Stream separation (split capture)** — `log-files.txt` must contain log paths and NO `Permission denied`; `log-errors.txt` must contain `Permission denied` lines and NO log paths.
3. **Order-trap proof (T02-A)** — Form A contains `Permission denied`; Form B does not (errors went to the screen in 02a, not the file).
4. **Tier B accumulation** — `cum-errors-asuser.txt` is owned by `labuser_02_stderr` AND has stderr content (proves the `sudo -u` step ran).
5. **Cross-check** — independently rebuild a small split-capture (as 02c's `${USER}`) and confirm the same shape of evidence.

### WEAVE TRACE

| Warm-up / setup command         | Role inside Task 1                                                       |
|---------------------------------|--------------------------------------------------------------------------|
| `ls -la .../lab-02a/`           | Pre-flight: every file in the audit list must already exist             |
| `find -type f \| sort`          | Deterministic file inventory                                            |
| `wc -l ..../task*/*.txt`        | Baseline counts for the assertions                                       |
| `stat -c '%U:%G ...' cum-errors-asuser.txt` | Ownership check on the Tier B file                            |
| `set -o pipefail`               | The audit pipes `grep`/`wc` — pipefail surfaces missing files cleanly    |
| `${USER}` (Tier B)              | Part E re-runs `find /var/log` as `${USER}` (02c's user) and compares the new evidence to 02a's — the cross-check |

### Main command block

```bash
TASKLOG=/tmp/lab02c/task1.txt
A_JDIR=/root/rhcsa_journal/lab-02a

# ── Part A: completeness ──────────────────────────────────────────────
echo "═══ Part A: completeness audit ═══"               2>&1 | tee $TASKLOG
EXPECTED=(
    "${A_JDIR}/task1/log-files.txt"
    "${A_JDIR}/task1/log-errors.txt"
    "${A_JDIR}/task1/log-files-asuser.txt"
    "${A_JDIR}/task1/log-errors-asuser.txt"
    "${A_JDIR}/task2/formA.txt"
    "${A_JDIR}/task2/formB.txt"
    "${A_JDIR}/task2/cum-results-asuser.txt"
    "${A_JDIR}/task2/cum-errors-asuser.txt"
)
MISSING=0
for f in "${EXPECTED[@]}"; do
    if test -s "$f"; then
        echo "✅ $f ($(wc -l < "$f") lines)"
    else
        echo "❌ $f MISSING OR EMPTY"
        MISSING=$((MISSING + 1))
    fi
done                                                   2>&1 | tee -a $TASKLOG
echo "missing-or-empty files: ${MISSING}"              | tee -a $TASKLOG

# ── Part B: stream separation (split capture) ─────────────────────────
echo "═══ Part B: stream separation ═══"               | tee -a $TASKLOG

# log-files.txt should have ZERO 'Permission denied' lines
PD_IN_FILES=$(grep -c 'Permission denied' "${A_JDIR}/task1/log-files-asuser.txt" 2>/dev/null || echo 0)
LOGS_IN_FILES=$(grep -c '\.log$'           "${A_JDIR}/task1/log-files-asuser.txt" 2>/dev/null || echo 0)
echo "log-files-asuser.txt: PD=${PD_IN_FILES}  .log paths=${LOGS_IN_FILES}" | tee -a $TASKLOG
test "${PD_IN_FILES}" -eq 0 \
    && echo "✅ stdout file has NO Permission denied — stream separation worked" \
    || echo "❌ stdout file contaminated with stderr text" \
    | tee -a $TASKLOG

# log-errors.txt should have ZERO '.log' path lines AND non-zero PD lines
PD_IN_ERRORS=$(grep -c 'Permission denied' "${A_JDIR}/task1/log-errors-asuser.txt" 2>/dev/null || echo 0)
LOGS_IN_ERRORS=$(grep -c '\.log$'           "${A_JDIR}/task1/log-errors-asuser.txt" 2>/dev/null || echo 0)
echo "log-errors-asuser.txt: PD=${PD_IN_ERRORS}  .log paths=${LOGS_IN_ERRORS}" | tee -a $TASKLOG
test "${PD_IN_ERRORS}" -gt 0 -a "${LOGS_IN_ERRORS}" -eq 0 \
    && echo "✅ stderr file has PD lines and NO log paths" \
    || echo "❌ stderr file shape wrong" \
    | tee -a $TASKLOG

# ── Part C: order-trap proof (T02-A) ──────────────────────────────────
echo "═══ Part C: order-trap (T02-A) proof ═══"        | tee -a $TASKLOG

A_PD=$(grep -c 'Permission denied' "${A_JDIR}/task2/formA.txt" 2>/dev/null || echo 0)
B_PD=$(grep -c 'Permission denied' "${A_JDIR}/task2/formB.txt" 2>/dev/null || echo 0)
echo "formA.txt PD lines (correct merge): ${A_PD}"      | tee -a $TASKLOG
echo "formB.txt PD lines (order trap):    ${B_PD}"      | tee -a $TASKLOG

# Form A must have PD lines; Form B must not (errors went to screen in 02a)
if test "${A_PD}" -gt 0 -a "${B_PD}" -eq 0; then
    echo "✅ T02-A proven: Form A captured stderr, Form B did not" | tee -a $TASKLOG
else
    echo "❌ T02-A NOT proven — 02a's order-trap demo did not run as designed" | tee -a $TASKLOG
fi

# ── Part D: Tier B accumulation proof ─────────────────────────────────
echo "═══ Part D: Tier B accumulation proof ═══"       | tee -a $TASKLOG
stat -c '%U:%G %a %n' "${A_JDIR}/task2/cum-errors-asuser.txt"  | tee -a $TASKLOG
CUM_OWN=$(stat -c '%U' "${A_JDIR}/task2/cum-errors-asuser.txt")
CUM_LINES=$(wc -l < "${A_JDIR}/task2/cum-errors-asuser.txt")
echo "owner=${CUM_OWN}  lines=${CUM_LINES}"            | tee -a $TASKLOG

if test "${CUM_OWN}" = "labuser_02_stderr" -a "${CUM_LINES}" -gt 0; then
    echo "✅ cum-errors-asuser.txt owned by 02a's lab user AND non-empty" | tee -a $TASKLOG
else
    echo "❌ Tier B accumulation evidence wrong — either owner!=labuser_02_stderr or zero lines" | tee -a $TASKLOG
fi

# ── Part E: cross-check — re-run find as 02c's ${USER} ────────────────
echo "═══ Part E: cross-check as ${USER} ═══"          | tee -a $TASKLOG
sudo -u "${USER}" bash -c \
    'find /var/log -name "*.log" -type f \
        >  '"${USER_HOME}"'/crosscheck-files.txt \
        2> '"${USER_HOME}"'/crosscheck-errors.txt'

CC_OUT=$(wc -l < "${USER_HOME}/crosscheck-files.txt")
CC_ERR=$(wc -l < "${USER_HOME}/crosscheck-errors.txt")
echo "crosscheck stdout=${CC_OUT}  stderr=${CC_ERR}"   | tee -a $TASKLOG
stat -c '%U:%G %a %n' "${USER_HOME}/crosscheck-files.txt"  | tee -a $TASKLOG
stat -c '%U:%G %a %n' "${USER_HOME}/crosscheck-errors.txt" | tee -a $TASKLOG

# Same shape of evidence is what we expect — non-zero stderr from a non-root user
test "${CC_ERR}" -gt 0 \
    && echo "✅ cross-check reproduced the stderr pattern under ${USER}" \
    || echo "❌ cross-check produced empty stderr — sudo -u dropped privileges incorrectly" \
    | tee -a $TASKLOG

echo "exit was: $?"
```

### Human-readable breakdown

1. **Part A — completeness.** Eight expected files, looped. Empty files count as `❌` (a journal-write that ran but didn't actually copy something would create an empty file — caught here).
2. **Part B — stream separation.** Two complementary assertions: (a) the stdout file must NOT contain `Permission denied`; (b) the stderr file MUST contain `Permission denied` and must NOT contain log paths. Catches the most common 02a typo — writing `2>` when you meant `>` and vice versa.
3. **Part C — order-trap proof.** This is the assertion that proves 02a's Task 2 actually demonstrated T02-A. Form A has stderr in the file; Form B doesn't. If they look the same (both contain or both lack PD), 02a was run as root and the demo was meaningless.
4. **Part D — Tier B accumulation.** The owner string must be literally `labuser_02_stderr` — that's the lab user 02a created. Not `root`, not `labuser_02_verify`. The line count must be non-zero. Together: the `sudo -u` actually ran.
5. **Part E — cross-check.** Run the same `find /var/log` as 02c's `${USER}` (different from 02a's). Same shape of evidence: non-zero stdout, non-zero stderr, both files owned by 02c's `${USER}`. Confirms the audit isn't depending on 02a's specific files — the pattern is reproducible.

### Reading it left to right

```
grep -c 'Permission denied' file 2>/dev/null || echo 0
│       │                   │    │              │
│       │                   │    │              └─ if grep failed or file missing, default to "0"
│       │                   │    └─ throw away the "no such file" error
│       │                   └─ target file
│       └─ pattern (quoted)
└─ -c → count matching lines (no actual text)
```

```
if test "${A_PD}" -gt 0 -a "${B_PD}" -eq 0; then OK; else BAD; fi
   │    │           │     │  │           │
   │    │           │     │  │           └─ asserts Form B did NOT capture stderr
   │    │           │     │  └─ logical AND inside test
   │    │           │     └─ second condition
   │    │           └─ asserts Form A DID capture stderr
   │    └─ first count comparison
   └─ classic POSIX `test` — `-gt` greater than, `-eq` equal
```

### The story

The order-trap (T02-A) is the most subtle stderr bug in Unix. People intuit that `>` and `2>&1` "go together" and write them in whatever order feels natural. The shell processes them strictly left to right against the *current* state of the FD table at each token. By the time you read about it, you've already shipped a script with the wrong order to production.

The 02c audit is the only way you find out, on your own time, whether 02a's demo really proved the trap. The auditor proves the demo; the demo proves the trap. Three layers of evidence — and they all have to line up for the lab to count as complete.

`labuser_02_stderr` vs `labuser_02_verify`: distinct users isn't decoration. The audit reads files owned by a *different* identity than the auditor — exactly how a grader script reads your work without ever logging in as you.

### Expected output

```text
═══ Part A: completeness audit ═══
✅ /root/rhcsa_journal/lab-02a/task1/log-files.txt (24 lines)
✅ /root/rhcsa_journal/lab-02a/task1/log-errors.txt (3 lines)
✅ /root/rhcsa_journal/lab-02a/task1/log-files-asuser.txt (21 lines)
✅ /root/rhcsa_journal/lab-02a/task1/log-errors-asuser.txt (3 lines)
✅ /root/rhcsa_journal/lab-02a/task2/formA.txt (27 lines)
✅ /root/rhcsa_journal/lab-02a/task2/formB.txt (24 lines)
✅ /root/rhcsa_journal/lab-02a/task2/cum-results-asuser.txt (46 lines)
✅ /root/rhcsa_journal/lab-02a/task2/cum-errors-asuser.txt (6 lines)
missing-or-empty files: 0
═══ Part B: stream separation ═══
log-files-asuser.txt: PD=0  .log paths=21
✅ stdout file has NO Permission denied — stream separation worked
log-errors-asuser.txt: PD=3  .log paths=0
✅ stderr file has PD lines and NO log paths
═══ Part C: order-trap (T02-A) proof ═══
formA.txt PD lines (correct merge): 3
formB.txt PD lines (order trap):    0
✅ T02-A proven: Form A captured stderr, Form B did not
═══ Part D: Tier B accumulation proof ═══
labuser_02_stderr:labgrp_02_stderr 644 /root/rhcsa_journal/lab-02a/task2/cum-errors-asuser.txt
owner=labuser_02_stderr  lines=6
✅ cum-errors-asuser.txt owned by 02a's lab user AND non-empty
═══ Part E: cross-check as labuser_02_verify ═══
crosscheck stdout=21  stderr=3
labuser_02_verify:labgrp_02_verify 644 /tmp/lab02c/home_labuser_02_verify/crosscheck-files.txt
labuser_02_verify:labgrp_02_verify 644 /tmp/lab02c/home_labuser_02_verify/crosscheck-errors.txt
✅ cross-check reproduced the stderr pattern under labuser_02_verify
exit was: 0
```

### Switches

| Token                                | Meaning                                                            |
|--------------------------------------|--------------------------------------------------------------------|
| `test "${X}" -gt N`                  | True if X > N (numeric)                                            |
| `test STR1 -a STR2`                  | Both conditions true (logical AND)                                  |
| `test STR1 = STR2`                   | String equality                                                    |
| `wc -l < FILE`                       | Line count without filename                                        |
| `wc -c < FILE`                       | Byte count without filename                                        |
| `grep -c PAT FILE`                   | Count matching lines (0 lines printed)                             |
| `grep -c PAT FILE 2>/dev/null \|\| echo 0` | If file missing, default to "0" instead of error            |
| `stat -c '%U' FILE`                  | Print owner only                                                   |
| `sudo -u USER bash -c '...'`         | Run quoted shell as USER                                           |

### Concept Card

| Concept | What it does |
|---|---|
| Completeness loop | `for f in ARR; test -s` — catches empty journal artifacts |
| Stream-separation assertion | Stdout file has 0 `Permission denied`; stderr file has 0 log paths |
| Order-trap proof | Form A has PD lines in file; Form B does not |
| Tier B accumulation proof | `cum-errors-asuser.txt` owned by literal `labuser_02_stderr` AND non-empty |
| Cross-check | Re-run as 02c's `${USER}` and confirm same shape of evidence |
| Defensive grep | `grep -c PAT FILE 2>/dev/null \|\| echo 0` defaults to 0 on missing file |
| **🪤 Trap Risk T02-A** | Audit catches the order-trap if 02a's demo didn't actually run — Form A and Form B would have identical content |
| **🪤 Trap Risk T44** | Lab Closeout audit catches orphan users/groups — four `✅` lines required |

### 🔁 PERSISTENCE CHECK

| What was configured | Verification command | Why it matters |
|---|---|---|
| 02a journal complete | `find /root/rhcsa_journal/lab-02a -type f \| wc -l` returns 13+ | Every artifact survived |
| Stream separation worked | `grep -c 'Permission denied' .../log-files-asuser.txt` returns 0 | FD 1 ≠ FD 2 in 02a |
| Order trap proven | `grep -c 'Permission denied' .../formA.txt` > 0 AND `.../formB.txt` returns 0 | T02-A was a real demo |
| Tier B sudo-u ran | `stat -c '%U' .../cum-errors-asuser.txt` returns `labuser_02_stderr` | Sudo-u actually dropped privileges |
| Cross-check reproducible | `${USER_HOME}/crosscheck-errors.txt` non-empty | Pattern is portable to a new user |

### Journal write

```bash
LAB=lab-02c
TASK=task1
JDIR="/root/rhcsa_journal/${LAB}/${TASK}"
mkdir -p "$JDIR"
cp /tmp/lab02c/task1.txt                          "$JDIR/evidence.txt"
cp "${USER_HOME}/crosscheck-files.txt"            "$JDIR/crosscheck-files.txt"
cp "${USER_HOME}/crosscheck-errors.txt"           "$JDIR/crosscheck-errors.txt"

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
TOPIC:    Audit Lab 02a stderr evidence — completeness, stream separation, order-trap proof, Tier B ownership, cross-check
COMMANDS: test -s, test -gt -a, grep -c, stat -c '%U', wc -l, sudo -u ${USER} bash -c
TRAPS:    T02-A audited (Form A had PD, Form B did not); T44 deferred to Lab Closeout
TIER B:   Cross-check files owned by ${USER}:${GROUP}; stderr non-empty proves sudo -u dropped privileges
MISSED:   (fill in if any ⚠️ flags)
NEXT:     task2 — destroy-restore drill (T41) for cum-errors-asuser.txt; reboot reasoning (T42)
EOF

ls -la "$JDIR"
echo "exit was: $?"
```

### Cleanup (per-task — leaves Tier B sandbox intact)

```bash
rm -f /tmp/lab02c/warmup.txt /tmp/lab02c/task1.txt
# Keep crosscheck-files.txt and crosscheck-errors.txt — Task 2 consumes them
getent passwd "${USER}"  >/dev/null && echo "✅ ${USER} still present"
getent group  "${GROUP}" >/dev/null && echo "✅ ${GROUP} still present"
test -d       "${SANDBOX}"          && echo "✅ ${SANDBOX} still present"
ls /tmp/lab02c
echo "exit was: $?"
```

### Troubleshoot

| Symptom | Fix |
|---|---|
| Part A: any `❌ MISSING` | 02a journal-write step skipped a file. Re-run the relevant 02a journal block, retry |
| Part B: `❌ stdout file contaminated` | 02a Task 1 wrote `>>` instead of `2>`. Rerun the split-capture run, retry |
| Part C: `❌ T02-A NOT proven` (Form B also has PD) | 02a was run as root, OR Form A and Form B had the order reversed accidentally. Rerun 02a Task 2 Part B as a non-root user |
| Part D: `❌ owner!=labuser_02_stderr` | 02a Task 1 Part D ran without sudo -u. Rerun 02a Task 1 Part D, retry |
| Part E: `crosscheck stderr=0` | The 02c sandbox built but `${USER}` has read access to all of `/var/log` (e.g. SELinux disabled). Verify with `id ${USER}` and `getfacl /var/log/audit` |

> **STOP — paste the five `✅` lines from Parts A–E before Task 2.**

---

## Task 2 — Destroy-restore drill for cumulative error log (T41 + T42)

**Practice directory this task:** `/tmp/lab02c` — destroys `/tmp/lab02a/` (if it lingers) and rebuilds the cumulative error log from `/root/rhcsa_journal/lab-02a/task2/`.

### Warm-Up

```bash
ls -la /tmp/lab02c /tmp/lab02a 2>/dev/null             2>&1 | tee /tmp/lab02c/warmup2.txt
df -h /tmp | tail -1
findmnt /tmp 2>/dev/null || echo "/tmp not separately mounted"
sha256sum /root/rhcsa_journal/lab-02a/task2/cum-errors-asuser.txt
set -o pipefail
echo "Warm-up done by $(whoami) at $(date -Is)"
echo "exit was: $?"
```

> Carry from Task 1: `wc -l`, `stat -c '%U:%G %a %n'`, `grep -c`. Add `sha256sum` for the byte-fidelity check across destroy/restore.

### Purpose

1. **Snapshot** the cumulative error log's content (line count + sha256).
2. **Destroy** `/tmp/lab02a/` and `/tmp/lab02c/` so the working copy is gone (simulated reboot of tmpfs).
3. **Restore** the cumulative error log from `/root/rhcsa_journal/lab-02a/task2/cum-errors-asuser.txt` into 02c's sandbox. Re-apply `${USER}:${GROUP}` ownership and `0664` mode.
4. **Continue** the log: append a fresh `find /var/log` run as 02c's `${USER}` using `2>>` (append mode) so the file grows. Proves the restored file is *operationally usable*, not just a static copy.
5. **Verify** the first N lines match the journal byte-for-byte (sha256 of head -N) AND the file grew by exactly the new stderr lines.

### WEAVE TRACE

| Warm-up / setup command          | Role inside Task 2                                                       |
|----------------------------------|--------------------------------------------------------------------------|
| `ls -la /tmp/lab02c /tmp/lab02a` | Captures pre-destroy state so the comparison post-destroy is honest      |
| `df -h /tmp \| tail -1`          | Free-space pre-flight before `rm -rf` and re-mkdir                       |
| `findmnt /tmp`                   | Confirms /tmp is tmpfs (the persistence story depends on this)            |
| `sha256sum cum-errors-asuser.txt`| The fingerprint we compare against the restored copy's head -N           |
| `${USER}` (Tier B)               | Part D continues the restored log by appending NEW stderr as `${USER}` — proves the file is live, not a museum piece |

### Main command block

```bash
TASKLOG=/tmp/lab02c/task2.txt
A_CUM=/root/rhcsa_journal/lab-02a/task2/cum-errors-asuser.txt

# ── Part A: snapshot ──────────────────────────────────────────────────
echo "═══ Part A: pre-destroy snapshot ═══"            2>&1 | tee $TASKLOG
A_LINES=$(wc -l < "${A_CUM}")
A_HASH=$(sha256sum "${A_CUM}" | awk '{print $1}')
echo "journal cum-errors lines:  ${A_LINES}"           | tee -a $TASKLOG
echo "journal cum-errors sha256: ${A_HASH}"            | tee -a $TASKLOG
ls -la /tmp/lab02a /tmp/lab02c 2>&1                    | tee -a $TASKLOG

# ── Part B: destroy ───────────────────────────────────────────────────
echo "═══ Part B: destroy /tmp/lab02a and /tmp/lab02c ═══" | tee -a $TASKLOG
rm -rf /tmp/lab02a /tmp/lab02c

if test ! -d /tmp/lab02a -a ! -d /tmp/lab02c; then
    echo "✅ destroy clean (both directories gone)"     | tee -a $TASKLOG
else
    echo "❌ destroy incomplete"                        | tee -a $TASKLOG
fi

# ── Part C: restore ───────────────────────────────────────────────────
echo "═══ Part C: restore from journal ═══"            | tee -a $TASKLOG
mkdir -p "${SANDBOX}" "${USER_HOME}"
chown -R "${USER}:${GROUP}" "${SANDBOX}"

cp "${A_CUM}" "${USER_HOME}/cum-errors-restored.txt"
chown "${USER}:${GROUP}" "${USER_HOME}/cum-errors-restored.txt"
chmod 0664               "${USER_HOME}/cum-errors-restored.txt"

# Verify byte-fidelity: first ${A_LINES} lines must match the journal exactly
RESTORE_HEAD_HASH=$(head -n "${A_LINES}" "${USER_HOME}/cum-errors-restored.txt" \
    | sha256sum | awk '{print $1}')
echo "restored head sha256: ${RESTORE_HEAD_HASH}"      | tee -a $TASKLOG
if test "${RESTORE_HEAD_HASH}" = "${A_HASH}"; then
    echo "✅ first ${A_LINES} lines match journal byte-for-byte" | tee -a $TASKLOG
else
    echo "❌ restored file drifted from journal"        | tee -a $TASKLOG
fi

# ── Part D: continue the log AS ${USER} using 2>> ─────────────────────
echo "═══ Part D: continue the log AS ${USER} ═══"     | tee -a $TASKLOG
sudo -u "${USER}" bash -c \
    'find /var/log -name "*.log" -type f \
        >> '"${USER_HOME}"'/cum-results-restored.txt \
        2>> '"${USER_HOME}"'/cum-errors-restored.txt'

# ── Part E: verify forward motion ─────────────────────────────────────
echo "═══ Part E: forward-motion verification ═══"     | tee -a $TASKLOG
NEW_LINES=$(wc -l < "${USER_HOME}/cum-errors-restored.txt")
APPENDED=$((NEW_LINES - A_LINES))
echo "lines now: ${NEW_LINES}  (added ${APPENDED} via 2>>)" | tee -a $TASKLOG
test "${APPENDED}" -gt 0 \
    && echo "✅ 2>> appended new stderr — restored file is live" \
    || echo "❌ 2>> did not append — restored file is not live" \
    | tee -a $TASKLOG

# Ownership of the live file
stat -c '%U:%G %a %n' "${USER_HOME}/cum-errors-restored.txt" | tee -a $TASKLOG

echo "exit was: $?"
```

### Human-readable breakdown

1. **Part A — snapshot.** Capture line count + sha256 of the journal's cumulative error log. This is the "ground truth" for the comparison.
2. **Part B — destroy.** `rm -rf /tmp/lab02a /tmp/lab02c`. Then verify both directories are actually gone with a single combined `test -a -a`. The `❌` branch fires if either lingered (e.g., a process holds an fd open).
3. **Part C — restore.** Recreate the Tier B sandbox dirs, copy the file from the journal, chown/chmod to make it writable by group. Then take a sha256 of just the first `${A_LINES}` lines and compare. If they match, the restore is byte-faithful.
4. **Part D — continue.** Run `find /var/log` as 02c's `${USER}` and APPEND its stderr to the restored file with `2>>`. This proves the restored file is operationally usable, not a static museum piece.
5. **Part E — forward motion.** New line count must be strictly greater than the journal's. Subtract to get the number of new stderr lines from the append.

### Reading it left to right

```
head -n "${A_LINES}" file | sha256sum | awk '{print $1}'
│       │             │   │            │   │
│       │             │   │            │   └─ first whitespace-delimited field (the hash)
│       │             │   │            └─ keep only the hash, drop the filename
│       │             │   └─ hash of the head's output
│       │             └─ pipe to sha256sum
│       └─ from FILE
└─ first N lines
```

```
test "${RESTORE_HEAD_HASH}" = "${A_HASH}" && echo "✅" || echo "❌"
│    │                       │            │           │
│    │                       │            │           └─ fires when test returns 1 (hashes differ)
│    │                       │            └─ fires when test returns 0 (hashes match)
│    │                       └─ string equality (POSIX `test`)
│    └─ left operand
└─ POSIX `test`
```

### The story

`sha256sum | awk '{print $1}'` is the "give me JUST the hash" idiom that production scripts use everywhere. `sha256sum` prints `<hash>  <filename>`; you almost always want only the hash for comparison. `awk '{print $1}'` peels off the first field. Memorize this pair — it appears in every artifact-verification context.

The `head -n N | sha256sum` trick is how you compare the *known* prefix of a growing file against a snapshot. Without `head -n N`, the sha256 of the live file would differ from the journal the moment Part D appends one line. With it, you assert the first N lines are unchanged AND new lines were added — both at once.

T42 (fix-live, forget-persistent) is the trap that the journal write at the end of every task exists to prevent. Without journal writes, every Lab Closeout `rm -rf` is destroying the only evidence the work was done. `/root/` survives reboots; `/tmp/` doesn't. The journal IS the persistent config — verbalize that aloud before you tear anything down.

### Expected output

```text
═══ Part A: pre-destroy snapshot ═══
journal cum-errors lines:  6
journal cum-errors sha256: 9f3a1c…
═══ Part B: destroy /tmp/lab02a and /tmp/lab02c ═══
✅ destroy clean (both directories gone)
═══ Part C: restore from journal ═══
restored head sha256: 9f3a1c…
✅ first 6 lines match journal byte-for-byte
═══ Part D: continue the log AS labuser_02_verify ═══
═══ Part E: forward-motion verification ═══
lines now: 9  (added 3 via 2>>)
✅ 2>> appended new stderr — restored file is live
labuser_02_verify:labgrp_02_verify 664 /tmp/lab02c/home_labuser_02_verify/cum-errors-restored.txt
exit was: 0
```

### Switches

| Token                                | Meaning                                                            |
|--------------------------------------|--------------------------------------------------------------------|
| `sha256sum FILE \| awk '{print $1}'` | Print only the hash, drop the filename                             |
| `head -n N FILE`                     | First N lines                                                      |
| `test ! -d DIR -a ! -d DIR2`         | Both directories absent                                            |
| `$((A - B))`                         | Arithmetic expansion (subtraction)                                 |
| `2>> FILE`                           | Append stderr to FILE                                              |
| `sudo -u USER bash -c '... 2>> ...'` | Append stderr to FILE while running as USER                       |
| `chmod 0664`                         | Owner rw, group rw, others r — group can write                    |
| `stat -c '%U:%G %a %n' FILE`         | Owner:group, mode, name in one line                                |

### Concept Card

| Concept | What it does |
|---|---|
| Sha256 head-only check | `head -n N \| sha256sum` proves the first N lines are unchanged |
| Restore-and-continue | After restore, append new content to prove the file is live, not static |
| Pre/post line-delta | `NEW - A_LINES > 0` is the forward-motion assertion |
| Group-writable restored file | `chmod 0664` lets `${USER}` append via `2>>` without re-becoming owner |
| **🪤 Trap Risk T41** | Skipping the destroy-restore drill = journal evidence is never actually validated. **Fix:** every c-lab Task 2 IS the drill |
| **🪤 Trap Risk T42** | Operating only on `/tmp/` artifacts means a reboot loses everything. **Fix:** journal writes to `/root/` before any cleanup |

### 🔁 PERSISTENCE CHECK

| What was configured | Verification command | Why it matters |
|---|---|---|
| Destroy clean | `test ! -d /tmp/lab02a` AND `test ! -d /tmp/lab02c` both return 0 right after rm | Wipe was complete |
| Restore byte-faithful | sha256 of `head -n ${A_LINES} restored` == journal sha256 | Lossless restore |
| Restore is live | `wc -l restored` > journal's count | New stderr appended after restore |
| Restored file is `${USER}`-owned | `stat -c '%U:%G' restored` returns `labuser_02_verify:labgrp_02_verify` | Permissions survived the wipe |
| Journal survives | `ls /root/rhcsa_journal/lab-02a/task2/cum-errors-asuser.txt` works | `/root/` is persistent (the entire point of T42) |

> **Reboot reasoning (verbalize before Lab Closeout):** "On a real reboot, `/tmp/lab02c/` evaporates. `/root/rhcsa_journal/lab-02a/task2/cum-errors-asuser.txt` survives. The restore procedure above is what I'd run post-reboot to bring the working copy back. T42 is the trap of patching `/tmp` and forgetting to write to `/root/`."

### Journal write

```bash
LAB=lab-02c
TASK=task2
JDIR="/root/rhcsa_journal/${LAB}/${TASK}"
mkdir -p "$JDIR"
cp /tmp/lab02c/task2.txt                              "$JDIR/evidence.txt"
cp "${USER_HOME}/cum-errors-restored.txt"             "$JDIR/cum-errors-restored.txt"
sha256sum "${USER_HOME}/cum-errors-restored.txt" \
          /root/rhcsa_journal/lab-02a/task2/cum-errors-asuser.txt \
              > "$JDIR/sha256sums.txt"

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
TOPIC:    Destroy-restore drill for cumulative error log; continue with 2>> after restore
COMMANDS: sha256sum | awk '{print $1}', head -n N | sha256sum, rm -rf, cp, chown USER:GROUP, chmod 0664, sudo -u ${USER} bash -c '2>>'
TRAPS:    T41 rehearsed (destroy-restore done); T42 verbalized; T44 deferred to Lab Closeout
TIER B:   restored file owned by ${USER}:${GROUP} 0664; new stderr lines appended via 2>>
PERSISTENCE: /tmp wiped; /root/rhcsa_journal/ survived; first ${A_LINES} lines byte-faithful
MISSED:   (fill in if any ⚠️ flags)
NEXT:     Lab 03a — Pipe Text Streams; tee splits stdout pre-redirect, same Tier B + verify pattern
EOF

ls -la "$JDIR"
echo "exit was: $?"
```

### Cleanup (per-task — leaves Tier B sandbox for Lab Closeout)

```bash
rm -f /tmp/lab02c/warmup2.txt /tmp/lab02c/task2.txt
rm -f "${USER_HOME}/cum-errors-restored.txt" "${USER_HOME}/cum-results-restored.txt"
rm -f "${USER_HOME}/crosscheck-files.txt" "${USER_HOME}/crosscheck-errors.txt"
getent passwd "${USER}"  >/dev/null && echo "✅ ${USER} still present"
getent group  "${GROUP}" >/dev/null && echo "✅ ${GROUP} still present"
test -d       "${SANDBOX}"          && echo "✅ ${SANDBOX} still present"
ls /tmp/lab02c
echo "exit was: $?"
```

### Troubleshoot

| Symptom | Fix |
|---|---|
| Part B `❌ destroy incomplete` | A process has /tmp/lab02a open — `lsof +D /tmp/lab02a 2>/dev/null`; close it; retry |
| Part C: `cp: cannot stat …cum-errors-asuser.txt` | 02a journal copy missing. Go to 02a Task 2 journal-write, run it, retry |
| Part C: `❌ restored file drifted` | The journal file was modified after 02a wrote it. Re-copy from 02a Task 2 evidence |
| Part E: `APPENDED == 0` | `${USER}` could read all of /var/log (e.g. SELinux disabled). Check `id ${USER}`, `getfacl /var/log/audit` |
| Part D: `Permission denied` writing to `cum-errors-restored.txt` | `chmod 0664` step skipped; file is mode 0600. Re-chmod and retry |

> **STOP — paste Part A snapshot hash, Part C `byte-for-byte` line, and Part E `APPENDED` count before running Lab Closeout.**

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
echo "── Lab 02c cleanup audit ──"
getent passwd "${USER}"  >/dev/null && echo "❌ user remains"    || echo "✅ user gone"
getent group  "${GROUP}" >/dev/null && echo "❌ group remains"   || echo "✅ group gone"
test -d "${SANDBOX}"                && echo "❌ sandbox remains" || echo "✅ sandbox gone"
test -d "${USER_HOME}"              && echo "❌ home remains"    || echo "✅ home gone"

set -e
echo "Cleanup complete by $(whoami) at $(date -Is)"
echo "exit was: $?"
```

> **STOP — paste the four `✅` audit lines. Lab 02 trilogy complete.**

---

## Lab 02c Checklist (2 tasks + closeout)

- [ ] Lab-Wide Setup — Tier B sandbox built; `${USER}=labuser_02_verify`
- [ ] Task 1 — completeness=0 missing; stream separation `✅`; T02-A proven `✅`; Tier B ownership = `labuser_02_stderr` `✅`; cross-check stderr non-zero `✅`
- [ ] Task 2 — pre-destroy hash captured; destroy clean; first ${A_LINES} lines byte-faithful; `2>>` appended new content; ownership correct
- [ ] Lab Closeout — four `✅` audit lines

---

## Related Labs

| Lab | Connection |
|---|---|
| **Lab 02a** — Stderr Redirection RHCSA | The creator-seat lab this audits |
| **Lab 02b** — Stderr Redirection Ansible | `ansible.builtin.shell` + `register:` splits the streams into `result.stdout_lines` and `result.stderr_lines` automatically. Trap rehearsal: T02-C (not checking `stderr_lines`) and T02-D (`ignore_errors: yes` vs `failed_when:`). |
| **Lab 01c** — Stdout Verify | Previous topic's verify — same destroy-restore pattern, FD 1 evidence |
| Lab 03a — Pipe Text Streams RHCSA | Next topic — `|` connects what `2>` and `>` capture |
| Lab 03c — Pipes Verify | The 03 verify analog |

---

## Author

**Kelvin R. Tobias**
[kelvinintech.com](https://kelvinintech.com) · [GitHub](https://github.com/kelvintechnical) · [LinkedIn](https://www.linkedin.com/in/kelvin-r-tobias-211949219)
