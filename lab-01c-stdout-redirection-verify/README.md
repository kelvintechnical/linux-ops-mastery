# Lab 01c: Verifying Standard Output Redirection (Capstone) — Audit + Persistence Drill

- **Series:** linux-ops-mastery — Shells, Terminals & Redirection
- **Trilogy:** [`01a`](../lab-01a-stdout-redirection-rhcsa/) (RHCSA hand-typed) → ⛔ no `01b` (Section 18 boundary — `>`/`>>` has no honest Ansible module) → **`01c`** (Verify — you are here)
- **Career arcs covered:** RHCSA EX200 (every grader script reads files — this trains the *prove-it-without-the-screen* reflex), SRE (post-incident evidence reconstruction from on-disk artifacts), DevOps (CI artifact verification), AI/MLOps (reproducibility audit on captured training logs)
- **Prerequisite:** [`Lab 01a`](../lab-01a-stdout-redirection-rhcsa/) completed; `/root/rhcsa_journal/lab-01a/task1/` and `task2/` populated
- **Time Estimate:** 25–35 minutes
- **Tasks:** 2 (Task 1 = audit 01a artifacts + replay-and-prove · Task 2 = destroy-restore persistence drill — **T41 rehearsal**)
- **Practice Directory (rotation #01):** `/tmp` (same as 01a — same `${SANDBOX}=/tmp/lab01c`)
- **Sandbox (Tier B per Section 1.5):** `/tmp/lab01c` with `USER=labuser_01_verify`, `GROUP=labgrp_01_verify`, `USER_HOME=/tmp/lab01c/home_labuser_01_verify`. Built in Lab-Wide Setup; torn down + audited in **Lab Closeout** after Task 2.
- **Traps rehearsed this lab:** **T41** (skipping the destroy-restore drill — the whole reason 01c exists) · **T42** (fixing live but forgetting the persistent config — proved by the reboot-simulation in Task 2) · **T44** (cleanup-left-orphan — audited by Lab Closeout, must finish with four `✅` lines)

> **This lab's practice directory is: `/tmp`** — same as 01a. The point of 01c is to prove the work in 01a survives a teardown and restore from the journal, *without* re-running 01a's hand-typed commands. The journal IS the source of truth.

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
echo "⚠️  TRAP REMINDERS THIS LAB: T41 T42 T44"
echo "📁  PRACTICE DIR: /tmp"
echo ""
echo "💡 /tmp context (same target as 01a):"
ls -ld /tmp
df -h /tmp 2>/dev/null | tail -n 1
echo ""
echo "📓 01a journal (must already exist):"
ls -la /root/rhcsa_journal/lab-01a/task1/ /root/rhcsa_journal/lab-01a/task2/
echo "Shell version: $BASH_VERSION"
```

> **STOP — paste header output before running setup. If the `ls -la /root/rhcsa_journal/lab-01a/...` lines are empty, GO BACK and finish Lab 01a first — Lab 01c has nothing to audit otherwise.**

---

## Objective

01a built the muscle. 01c proves the muscle remembered. By the end of this lab you can:

1. **Audit** the journal evidence from Lab 01a *without* re-running 01a — open the file, count the lines, verify the ownership, confirm the `${USER}`-signed marker is exactly where it should be. The grader script reads the file; you train your eyes to do the same.
2. **Replay-and-prove** the canonical 01a behaviors (`>` truncates, `>>` appends, ownership lands where `sudo -u` says it does) and compare the new artifacts to the journal copies with `diff -u`. Identical content from a different writer is the strongest evidence.
3. **Survive the destroy-restore drill (T41)**: wipe the entire `/tmp` Tier B stack, then restore the report file from the journal copy at `/root/rhcsa_journal/lab-01a/task2/`. The journal must contain everything you need. If it doesn't, the journal-write step in 01a was incomplete — fix 01a, not 01c.
4. **Reason about persistence** — `/tmp` is tmpfs (RAM-backed). `/root/rhcsa_journal/` is on the root partition. Prove which artifacts survive a reboot by simulating one (full `${SANDBOX}` wipe) and re-establishing the working state from `/root/`.

---

## Concept: Verification Is a Separate Skill From Creation

In Lab 01a you *did* the work. In Lab 01c you *prove* the work. They are different reflexes:

```
   ┌───────────────────────────────────────────────────────────────┐
   │  01a (creator seat)        │   01c (auditor seat)             │
   ├───────────────────────────────────────────────────────────────┤
   │  echo "..." > FILE         │   cat FILE                       │
   │  >> appends                │   wc -l (count); diff -u (compare)│
   │  sudo -u USER bash -c ...  │   stat -c '%U:%G %a %n' FILE     │
   │  chmod 0664                │   getfacl FILE                   │
   │                            │   grep -c "MARKER" FILE          │
   └───────────────────────────────────────────────────────────────┘
                                  │
                                  └─ Different commands. Different goal.
                                     The auditor never runs `>`; they run
                                     commands that READ the result of `>`.
```

The exam grader is an auditor. You score points by leaving artifacts that prove the work, not by typing commands quickly. 01c is the lab that teaches you to think like the grader.

---

## Lab-Wide Setup — Tier B Sandbox Stack (Section 1.5)

```bash
sudo -i

export LAB_NUM=01
export LAB_SLUG=verify
export SANDBOX=/tmp/lab01c
export GROUP=labgrp_${LAB_NUM}_${LAB_SLUG}
export USER=labuser_${LAB_NUM}_${LAB_SLUG}
export USER_HOME=${SANDBOX}/home_${USER}

mkdir -p "${SANDBOX}" "${USER_HOME}"
mkdir -p /root/rhcsa_journal/lab-01c/task1
mkdir -p /root/rhcsa_journal/lab-01c/task2

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

> **STOP — paste the `id` line, the `ls -ld` lines, and both `getent` lines before Task 1. The 01c user/group is intentionally distinct from 01a (`labuser_01_verify` vs `labuser_01_stdout`) so the audit reads journal artifacts owned by a *different* identity than the one running the audit — exactly like a grader.**

---

## Task 1 — Audit the 01a journal + replay-and-diff

**Practice directory this task:** `/tmp/lab01c` — read-only reads against `/root/rhcsa_journal/lab-01a/`, writes only into our own sandbox.

### Warm-Up

```bash
ls -la /root/rhcsa_journal/lab-01a/                    2>&1 | tee /tmp/lab01c/warmup.txt
find /root/rhcsa_journal/lab-01a -type f | sort
wc -l /root/rhcsa_journal/lab-01a/task1/*.txt 2>/dev/null
stat -c '%U:%G %a %n' /root/rhcsa_journal/lab-01a/task2/done.txt 2>/dev/null
set -o pipefail
echo "Warm-up done by $(whoami) at $(date -Is)"
echo "exit was: $?"
```

> Carry from Lab 01a: `wc -l`, `stat -c '%U:%G %a %n'`, `find -type f`, the `2>&1 | tee FILE` transcript pattern.

### Purpose

Audit four things about the Lab 01a artifacts on disk:

1. **Completeness** — every expected file from 01a's journal-write block is actually present (`done.txt`, `notes.txt`, `evidence.txt`, `task1-asuser.txt`, `task1-asroot.txt`, `report.txt`).
2. **Content shape** — `wc -l report.txt` returns 13 (12 root sections + 1 `${USER}`-signed line), `head -1` is the header, `tail -1` is the `Signed by …` marker.
3. **Ownership semantics** — `task1-asuser.txt` is owned by 01a's lab user (`labuser_01_stdout`), `task1-asroot.txt` is owned by `root`. Verifies the sudo-u weave was real.
4. **Replay match** — replay the canonical `>` / `>>` / `sudo -u` sequence into a fresh report under `/tmp/lab01c/`, then `diff -u` it against the journal copy. Same lines, different writers, same checksum on the data.

### WEAVE TRACE

| Warm-up / setup command       | Role inside Task 1                                                       |
|-------------------------------|--------------------------------------------------------------------------|
| `ls -la .../lab-01a/`         | Pre-flight: every file the audit references must exist before we begin   |
| `find -type f | sort`         | Stable, deterministic file list — exactly the inventory the audit checks |
| `wc -l .../task1/*.txt`       | Baseline line counts; the audit asserts the exact same numbers           |
| `stat -c '%U:%G %a %n' ...`   | Read ownership/mode/name in one line — used three times in the main block|
| `${USER}` / `${GROUP}` (Tier B) | Part D replays 01a's `sudo -u` weave under the new identity and `diff`s the two outputs — Tier B drives the replay, not just decoration |

### Main command block

```bash
TASKLOG=/tmp/lab01c/task1.txt
A_JDIR=/root/rhcsa_journal/lab-01a
C_JDIR=/root/rhcsa_journal/lab-01c

# ── Part A: completeness — every expected 01a artifact must exist ─────
echo "═══ Part A: completeness audit ═══"               2>&1 | tee $TASKLOG
EXPECTED=(
    "${A_JDIR}/task1/done.txt"
    "${A_JDIR}/task1/notes.txt"
    "${A_JDIR}/task1/evidence.txt"
    "${A_JDIR}/task1/task1-asuser.txt"
    "${A_JDIR}/task1/task1-asroot.txt"
    "${A_JDIR}/task2/done.txt"
    "${A_JDIR}/task2/notes.txt"
    "${A_JDIR}/task2/evidence.txt"
    "${A_JDIR}/task2/report.txt"
)
MISSING=0
for f in "${EXPECTED[@]}"; do
    if test -s "$f"; then
        echo "✅ $f ($(wc -c < "$f") bytes)"
    else
        echo "❌ $f MISSING OR EMPTY"
        MISSING=$((MISSING + 1))
    fi
done                                                   2>&1 | tee -a $TASKLOG
echo "missing-or-empty files: ${MISSING}"              | tee -a $TASKLOG

# ── Part B: content shape — report.txt must be exactly 13 lines ───────
echo "═══ Part B: report.txt content shape ═══"        | tee -a $TASKLOG
wc -l       "${A_JDIR}/task2/report.txt"               | tee -a $TASKLOG
head -1     "${A_JDIR}/task2/report.txt"               | tee -a $TASKLOG
tail -1     "${A_JDIR}/task2/report.txt"               | tee -a $TASKLOG
grep -c '^=== ' "${A_JDIR}/task2/report.txt"           | tee -a $TASKLOG   # expect 2
grep -c '^--- ' "${A_JDIR}/task2/report.txt"           | tee -a $TASKLOG   # expect 6 (5 sections + 1 sign)

# ── Part C: ownership semantics — sudo -u weave actually happened ─────
echo "═══ Part C: ownership audit ═══"                 | tee -a $TASKLOG
stat -c '%U:%G %a %n' "${A_JDIR}/task1/task1-asuser.txt" | tee -a $TASKLOG
stat -c '%U:%G %a %n' "${A_JDIR}/task1/task1-asroot.txt" | tee -a $TASKLOG

# The owner of task1-asuser.txt should literally contain "labuser_01_stdout"
stat -c '%U' "${A_JDIR}/task1/task1-asuser.txt" \
    | grep -q '^labuser_01_stdout$' \
    && echo "✅ asuser file owned by 01a lab user"     | tee -a $TASKLOG \
    || echo "❌ asuser file owner WRONG — 01a sudo -u step did not actually run" | tee -a $TASKLOG

# ── Part D: replay-and-diff (Tier B weave) ────────────────────────────
echo "═══ Part D: replay 01a's >/>>/sudo -u sequence ═══" | tee -a $TASKLOG
REPLAY=/tmp/lab01c/report-replay.txt

# Rebuild the same 12-line report root wrote in 01a Task 2
echo "=== System Report ===" >  ${REPLAY}
echo "--- Hostname ---"      >> ${REPLAY}
hostname                     >> ${REPLAY}
echo "--- Date ---"          >> ${REPLAY}
date                         >> ${REPLAY}
echo "--- Uptime ---"        >> ${REPLAY}
uptime                       >> ${REPLAY}
echo "--- User ---"          >> ${REPLAY}
id                           >> ${REPLAY}
echo "--- Kernel ---"        >> ${REPLAY}
uname -r                     >> ${REPLAY}
echo "=== End Report ==="    >> ${REPLAY}

# Sign as 01c's lab user — different identity than 01a's, on purpose
chown root:"${GROUP}" ${REPLAY}
chmod 0664           ${REPLAY}
sudo -u "${USER}" bash -c \
    'echo "--- Signed by $(whoami) at $(date -Is) ---" >> '"${REPLAY}"

# Compare structure, ignoring lines that legitimately differ between runs
# (timestamps, uptime, signer name). What we want to assert is the SHAPE:
# section headers in the same order, same total line count.
diff -u \
    <(grep -E '^(===|---)' "${A_JDIR}/task2/report.txt") \
    <(grep -E '^(===|---)' "${REPLAY}") \
    | tee -a $TASKLOG \
    || echo "(diff above lists any structural drift; clean diff = empty output)" | tee -a $TASKLOG

REPLAY_LINES=$(wc -l < "${REPLAY}")
A_LINES=$(wc -l < "${A_JDIR}/task2/report.txt")
echo "01a report lines: ${A_LINES}  replay lines: ${REPLAY_LINES}" | tee -a $TASKLOG
test "${REPLAY_LINES}" -eq "${A_LINES}" \
    && echo "✅ line counts match"   | tee -a $TASKLOG \
    || echo "❌ line counts differ"  | tee -a $TASKLOG

echo "exit was: $?"
```

### Human-readable breakdown

1. **Part A — completeness audit.** Iterate the expected file list with `for f in ...`. `test -s "$f"` is true when the file exists *and* is non-empty. If 01a's journal-write step missed a `cp`, this loop catches it now.
2. **Part B — content shape.** `head -1` must be `=== System Report ===`, `tail -1` must be the `${USER}`-signed line. `grep -c '^=== '` returns 2 (header + footer); `grep -c '^--- '` returns 6 (5 sections + the signed line). Any deviation means 01a's `>` got out of order.
3. **Part C — ownership audit.** `stat -c '%U'` extracts owner only. We grep for the exact 01a user (`labuser_01_stdout`) — if 01a forgot the `sudo -u` step, the file would be owned by `root` and the audit fails loudly.
4. **Part D — replay-and-diff.** Build a fresh report under `/tmp/lab01c/` using the same `>` / `>>` sequence, sign it as 01c's user. The full `diff -u` will show the timestamp / signer drift, which is fine. The **filtered** `diff` on lines starting with `===` or `---` should be **empty** — that proves the *structure* survived.

### Reading it left to right

```
for f in "${EXPECTED[@]}"; do test -s "$f" && echo "✅ $f" || echo "❌ $f MISSING"; done
│   │              │       │   │      │       │                  │
│   │              │       │   │      │       │                  └─ run when test exits non-zero
│   │              │       │   │      │       └─ run when test exits zero (file exists, non-empty)
│   │              │       │   │      └─ "test -s FILE" = true iff size>0
│   │              │       │   └─ each filename, in order
│   │              │       └─ loop variable f
│   │              └─ expand the array
│   └─ array of expected filenames
└─ bash for loop
```

```
diff -u <(grep -E '^(===|---)' A) <(grep -E '^(===|---)' B)
│       │                       │                          │
│       │                       │                          └─ second input (replay file headers)
│       │                       └─ process-substitution: filtered headers from A
│       └─ unified diff output
└─ produce a diff that's empty when both filtered outputs are identical
```

### The story

Process substitution (`<(...)`) is one of the most under-taught tools in bash. It lets you treat the output of any command as if it were a file — `diff` thinks it's reading two ordinary files. Without `<()` you'd have to write each `grep` output to a temp file, run `diff`, then clean up the temp files. Three steps collapse into one.

The "filtered diff" idea — diffing only structurally significant lines — is how production change-management works. You're not asking *"are the two files byte-identical?"* You're asking *"do they agree on the parts that matter?"* That's the auditor's mindset.

### Expected output

```text
═══ Part A: completeness audit ═══
✅ /root/rhcsa_journal/lab-01a/task1/done.txt (89 bytes)
✅ /root/rhcsa_journal/lab-01a/task1/notes.txt (412 bytes)
✅ /root/rhcsa_journal/lab-01a/task1/evidence.txt (1234 bytes)
✅ /root/rhcsa_journal/lab-01a/task1/task1-asuser.txt (54 bytes)
✅ /root/rhcsa_journal/lab-01a/task1/task1-asroot.txt (22 bytes)
✅ /root/rhcsa_journal/lab-01a/task2/done.txt (89 bytes)
✅ /root/rhcsa_journal/lab-01a/task2/notes.txt (498 bytes)
✅ /root/rhcsa_journal/lab-01a/task2/evidence.txt (2105 bytes)
✅ /root/rhcsa_journal/lab-01a/task2/report.txt (483 bytes)
missing-or-empty files: 0
═══ Part B: report.txt content shape ═══
13 /root/rhcsa_journal/lab-01a/task2/report.txt
=== System Report ===
--- Signed by labuser_01_stdout at 2026-05-28T08:55:01-04:00 ---
2
6
═══ Part C: ownership audit ═══
labuser_01_stdout:labgrp_01_stdout 644 /root/rhcsa_journal/lab-01a/task1/task1-asuser.txt
root:root 644 /root/rhcsa_journal/lab-01a/task1/task1-asroot.txt
✅ asuser file owned by 01a lab user
═══ Part D: replay 01a's >/>>/sudo -u sequence ═══
(diff above lists any structural drift; clean diff = empty output)
01a report lines: 13  replay lines: 13
✅ line counts match
exit was: 0
```

### Switches

| Token                                      | Meaning                                                            |
|--------------------------------------------|--------------------------------------------------------------------|
| `test -s FILE`                             | True if FILE exists AND has size > 0                              |
| `for f in "${ARR[@]}"; do ... done`        | Iterate array preserving spaces in elements                       |
| `wc -c < FILE`                             | Byte count without filename in output                              |
| `grep -c '^PAT'`                           | Count anchored matches                                             |
| `stat -c '%U' FILE`                        | Print owner only (no group, no mode, no name)                     |
| `diff -u <(cmdA) <(cmdB)`                  | Unified diff against process-substituted outputs                  |
| `grep -E '^(===\|---)'`                    | Extended regex; alternation; anchored at line start                |

### Concept Card

| Concept | What it does |
|---|---|
| Completeness loop | `for f in ARR; do test -s; done` — catches missing/empty journal files in one pass |
| Content-shape audit | Counts + first/last lines + section-marker tallies — the grader's exact checks |
| Ownership audit | `stat -c '%U'` + `grep -q` — proves the `sudo -u` weave produced real ownership |
| Replay-and-diff | Rebuild the artifact under a new identity, then `diff` the *structure*, not the byte content |
| Process substitution `<()` | Treats command output as a file — collapses temp-file dance into one line |
| **🪤 Trap Risk T44** | Skipping the audit means orphaned users/groups/files survive into the next lab. **Fix:** Lab Closeout block at the bottom is mandatory — four `✅` audit lines required. |

### 🔁 PERSISTENCE CHECK

| What was configured | Verification command | Why it matters |
|---|---|---|
| 01a journal complete | `find /root/rhcsa_journal/lab-01a -type f \| wc -l` returns 9 | Every expected artifact survived 01a → 01c handoff |
| `report.txt` is 13 lines | `wc -l /root/rhcsa_journal/lab-01a/task2/report.txt` returns 13 | Structure preserved — `>`/`>>` order was correct in 01a |
| `${USER}`-signed marker exists | `tail -1 /root/rhcsa_journal/lab-01a/task2/report.txt \| grep -q 'Signed by labuser_01_stdout'` returns 0 | Proves 01a's `sudo -u` weave reached the journal |
| Replay matches structure | filtered `diff` empty | Structure is reproducible from the prompt + journal |

### Journal write

```bash
LAB=lab-01c
TASK=task1
JDIR="/root/rhcsa_journal/${LAB}/${TASK}"
mkdir -p "$JDIR"
cp /tmp/lab01c/task1.txt          "$JDIR/evidence.txt"
cp /tmp/lab01c/report-replay.txt  "$JDIR/report-replay.txt"

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
TOPIC:    Audit Lab 01a journal: completeness loop, content-shape (head/tail/wc), ownership semantics, replay-and-diff
COMMANDS: test -s, for f in ARR, wc -l, wc -c, head -1, tail -1, grep -c, stat -c '%U:%G %a %n', diff -u <(cmd) <(cmd)
TRAPS:    T44 rehearsed (audit MUST pass before Lab Closeout)
TIER B:   ${USER} signed report-replay.txt; ownership cross-checked against 01a's task1-asuser.txt
AUDIT:    missing-or-empty=0; report.txt=13 lines; 01a asuser file owned by labuser_01_stdout
MISSED:   (fill in if any ⚠️ flags)
NEXT:     task2 — destroy-restore drill (T41); wipe ${SANDBOX}; restore from /root/rhcsa_journal/lab-01a/
EOF

ls -la "$JDIR"
echo "exit was: $?"
```

### Cleanup (per-task — leaves Tier B sandbox intact)

```bash
rm -f /tmp/lab01c/warmup.txt /tmp/lab01c/task1.txt
# Keep /tmp/lab01c/report-replay.txt — Task 2's destroy-restore drill consumes it.
getent passwd "${USER}"  >/dev/null && echo "✅ ${USER} still present"
getent group  "${GROUP}" >/dev/null && echo "✅ ${GROUP} still present"
test -d       "${SANDBOX}"          && echo "✅ ${SANDBOX} still present"
ls /tmp/lab01c
echo "exit was: $?"
```

### Troubleshoot

| Symptom | Fix |
|---|---|
| `missing-or-empty files: N` (N > 0) | 01a's journal-write step missed a `cp`. Go back to 01a, run the missing journal-write block, then re-run Part A here |
| Part B: `wc -l report.txt` returns 12 not 13 | 01a Task 2 Part C never ran — the `${USER}`-signed line is missing. Re-run 01a Part C, re-copy to journal, retry |
| Part C: `❌ asuser file owner WRONG` | 01a Task 1 Part D used `root` instead of `sudo -u ${USER}`. Re-run that step with the correct sudo invocation |
| Part D `diff` is non-empty | Section markers drifted between 01a and 01c — verify the `--- Hostname ---` / `--- Date ---` / ... lines are spelled identically |
| `head -1` returns blank | Permission error reading the journal file — `ls -la /root/rhcsa_journal/lab-01a/task2/report.txt`; must be readable by root |

> **STOP — paste the Part A `missing-or-empty` count, Part B `wc -l`, Part C `stat` output, and Part D `line counts match` before Task 2.**

---

## Task 2 — Destroy-restore persistence drill (T41 rehearsal)

**Practice directory this task:** `/tmp/lab01c` — we wipe `${SANDBOX}` (Tier B) and the 01a sandbox (`/tmp/lab01a` if it still exists), then prove the journal alone is enough to rebuild a usable working copy.

### Warm-Up

```bash
ls -la /tmp/lab01c /tmp/lab01a 2>/dev/null            2>&1 | tee /tmp/lab01c/warmup2.txt
df -h /tmp | tail -1
mount | grep -E '/tmp\b' || echo "/tmp not separately mounted (root partition)"
findmnt /tmp 2>/dev/null || true
set -o pipefail
echo "Warm-up done by $(whoami) at $(date -Is)"
echo "exit was: $?"
```

> Carry from Task 1: `wc -l`, `stat -c '%U:%G %a %n'`, `diff -u <(cmd) <(cmd)`. Add `findmnt` + `df -h /tmp` to confirm what /tmp actually is on this host.

### Purpose

Simulate a reboot of `/tmp` and prove the journal under `/root/` is the source of truth.

1. **Snapshot** the current `${SANDBOX}` state (line count, ownership of `report-replay.txt` from Task 1).
2. **Destroy** everything under `/tmp/lab01c/` and `/tmp/lab01a/` (if it lingers). This is the "reboot simulation" — `/tmp` is tmpfs on most RHEL 9 hosts, so a real reboot would do the same.
3. **Restore** the report from `/root/rhcsa_journal/lab-01a/task2/report.txt` into the freshly-recreated `${SANDBOX}`. Re-apply the `${USER}:${GROUP}` ownership/mode. Append a "restored at $(date -Is)" marker as `${USER}`.
4. **Verify** the restored file is byte-identical to the journal copy (proof of fidelity) AND now has one additional restore marker line (proof of forward motion).
5. **Reason about persistence** explicitly — what survives `rm -rf /tmp/lab01c`? What survives an actual reboot? Where does the journal live? T42 lurks if you forget to write back to `/root/`.

### WEAVE TRACE

| Warm-up / setup command       | Role inside Task 2                                                       |
|-------------------------------|--------------------------------------------------------------------------|
| `ls -la /tmp/lab01c /tmp/lab01a` | Pre-flight before the destroy — captures exactly what we're about to delete |
| `df -h /tmp \| tail -1`       | Confirms /tmp's mount and free space — informs the "is tmpfs" reasoning   |
| `findmnt /tmp`                | If /tmp is a separate tmpfs, prints fstype=tmpfs; the persistence story depends on this |
| `set -o pipefail`             | Required because the restore uses `diff \| wc -l` — must not silently mask a missing journal |
| `${USER}` (Tier B)            | The restored file is `chown`d back to `${USER}:${GROUP}` and the restore-marker line is appended *as* `${USER}` — the whole Task 2 is one big Tier B exercise |

### Main command block

```bash
TASKLOG=/tmp/lab01c/task2.txt
A_JOURNAL=/root/rhcsa_journal/lab-01a/task2/report.txt

# ── Part A: snapshot BEFORE destroy ───────────────────────────────────
echo "═══ Part A: pre-destroy snapshot ═══"            2>&1 | tee $TASKLOG
ls -la /tmp/lab01c /tmp/lab01a 2>&1                    | tee -a $TASKLOG
wc -l /tmp/lab01c/report-replay.txt 2>/dev/null        | tee -a $TASKLOG
stat -c '%U:%G %a %n' /tmp/lab01c/report-replay.txt 2>/dev/null | tee -a $TASKLOG
sha256sum "${A_JOURNAL}"                               | tee -a $TASKLOG

# ── Part B: destroy (simulate /tmp reboot wipe) ───────────────────────
echo "═══ Part B: destroy /tmp/lab01c and /tmp/lab01a ═══" | tee -a $TASKLOG
rm -rf /tmp/lab01c /tmp/lab01a

ls -la /tmp/lab01c /tmp/lab01a 2>&1 \
    | grep -v 'No such file' \
    && echo "❌ destroy incomplete" \
    || echo "✅ destroy clean (both directories gone)" | tee -a $TASKLOG

# ── Part C: restore from journal ──────────────────────────────────────
echo "═══ Part C: restore from /root/rhcsa_journal/ ═══" | tee -a $TASKLOG
# Rebuild the Tier B stack — same exports survived (variables are in this shell)
mkdir -p "${SANDBOX}" "${USER_HOME}"
chown -R "${USER}:${GROUP}" "${SANDBOX}"

# Pull the canonical report.txt out of the journal
cp "${A_JOURNAL}" "${SANDBOX}/report-restored.txt"
chown root:"${GROUP}" "${SANDBOX}/report-restored.txt"
chmod 0664           "${SANDBOX}/report-restored.txt"

# ${USER} appends the restore marker — proves the lab user still works
sudo -u "${USER}" bash -c \
    'echo "--- Restored from journal at $(date -Is) by $(whoami) ---" \
        >> '"${SANDBOX}"'/report-restored.txt'

# ── Part D: verify byte-fidelity + forward motion ─────────────────────
echo "═══ Part D: restore verification ═══"            | tee -a $TASKLOG

# 4a: the first 13 lines of the restored file must match the journal byte-for-byte
diff -u \
    <(head -n 13 "${SANDBOX}/report-restored.txt") \
    "${A_JOURNAL}" \
    | tee -a $TASKLOG \
    && echo "✅ first 13 lines diff CLEAN — restore is byte-faithful" \
    || echo "❌ restore drifted" | tee -a $TASKLOG

# 4b: the restored file has exactly ONE additional line (the restore marker)
RESTORED_LINES=$(wc -l < "${SANDBOX}/report-restored.txt")
JOURNAL_LINES=$(wc -l < "${A_JOURNAL}")
echo "journal=${JOURNAL_LINES}  restored=${RESTORED_LINES}" | tee -a $TASKLOG
test "${RESTORED_LINES}" -eq $((JOURNAL_LINES + 1)) \
    && echo "✅ exactly one restore marker appended" \
    || echo "❌ unexpected line delta" | tee -a $TASKLOG

# 4c: the restore marker is owned by ${USER}, not root
grep "Restored from journal" "${SANDBOX}/report-restored.txt" \
    | grep -q "by ${USER}$" \
    && echo "✅ restore marker signed by ${USER}" \
    || echo "❌ restore marker NOT signed by ${USER}" | tee -a $TASKLOG

echo "exit was: $?"
```

### Human-readable breakdown

1. **Part A — snapshot.** `sha256sum` the journal copy *before* anything destructive happens. We'll compare against this hash later to detect even one-bit corruption.
2. **Part B — destroy.** `rm -rf /tmp/lab01c /tmp/lab01a` simulates a reboot wipe of tmpfs. The `grep -v 'No such file'` invert-match is the "expected error" pattern: a successful destroy *should* produce `No such file` from the `ls`, which we suppress to keep the audit output clean.
3. **Part C — restore.** Re-export-free: the shell variables (`${SANDBOX}`, `${USER}`, etc.) survive `rm -rf` because they're in the shell's memory, not on disk. Recreate the sandbox dirs, then `cp` from the journal. Chown to `root:${GROUP}` and chmod `0664` so `${USER}` can append. Then sign as `${USER}`.
4. **Part D — verify.** Three checks: byte-fidelity (`diff -u` of the first 13 lines against the journal), forward motion (exactly +1 line for the restore marker), and the Tier B proof (the new line is signed by `${USER}`). All three `✅` = the persistence drill passed.

### Reading it left to right (the "expected error" pattern)

```
ls -la /tmp/lab01c /tmp/lab01a 2>&1 | grep -v 'No such file' && echo "❌" || echo "✅"
│                              │     │                       │           │
│                              │     │                       │           └─ run if grep DID NOT match (good — directories are gone)
│                              │     │                       └─ run if grep DID match (bad — directories still there)
│                              │     └─ keep only lines WITHOUT "No such file"
│                              └─ merge stderr into stdout so grep sees both
└─ list both directories
```

This is the inversion logic exam-day people get wrong constantly. `&&` runs after success, `||` runs after failure — but here "success" means *grep found a leftover file*, which is BAD. The `❌` and `✅` map to the `grep` exit code, not to the "ls failed" exit code. Read it twice; if it still feels backwards, rewrite it with an `if`.

### The story

The destroy-restore drill (T41) exists because RHCSA exam scenarios test recovery. *"You've lost the /etc/hosts file. Restore it."* The grader doesn't care how you do it — they care that, when the dust settles, `/etc/hosts` exists, has the right content, and has the right ownership. Practicing destroy-and-restore on lab artifacts builds the same reflex: assume the working copy can vanish at any time; the journal under `/root/` is the only thing that survives reboot. T42 — "fix live, forget the persistent file" — happens when you patch a thing in `/tmp` and never write it to `/root/`.

`sha256sum` is the gold standard for proving fidelity. `diff -u` shows you *where* two files differ; `sha256sum` proves they don't differ *anywhere* in one number. Use both: `sha256sum` for the global "yes/no", `diff -u` for the "where" when the answer is "no".

### Expected output

```text
═══ Part A: pre-destroy snapshot ═══
-rw-r--r--. 1 root root 482 May 28 08:55 /tmp/lab01c/report-replay.txt
13 /tmp/lab01c/report-replay.txt
root:labgrp_01_verify 664 /tmp/lab01c/report-replay.txt
a3f7…  /root/rhcsa_journal/lab-01a/task2/report.txt
═══ Part B: destroy /tmp/lab01c and /tmp/lab01a ═══
✅ destroy clean (both directories gone)
═══ Part C: restore from /root/rhcsa_journal/ ═══
═══ Part D: restore verification ═══
✅ first 13 lines diff CLEAN — restore is byte-faithful
journal=13  restored=14
✅ exactly one restore marker appended
✅ restore marker signed by labuser_01_verify
exit was: 0
```

### Switches

| Token                                | Meaning                                                            |
|--------------------------------------|--------------------------------------------------------------------|
| `sha256sum FILE`                     | 256-bit cryptographic hash of FILE; same hash ⇒ same bytes         |
| `rm -rf DIR`                         | Recursive, force, no-prompt delete                                 |
| `grep -v 'PAT'`                      | Invert: print lines NOT matching                                   |
| `diff -u <(head -n 13 A) B`          | Diff first 13 lines of A vs all of B; unified format               |
| `head -n N FILE`                     | First N lines                                                      |
| `wc -l < FILE`                       | Line count, no filename                                            |
| `arith $((A + 1))`                   | Arithmetic expansion — N+1                                         |
| `grep -q PAT`                        | Quiet — exit 0 if PAT found, 1 otherwise; for `if`/`&&` chains    |

### Concept Card

| Concept | What it does |
|---|---|
| Destroy-restore drill | `rm -rf` the working copy; rebuild from `/root/rhcsa_journal/` to prove the journal is enough |
| `sha256sum` snapshot | One-number fidelity check across destroy/restore |
| "Expected error" inversion | `cmd 2>&1 \| grep -v` patterns — invert because the failure IS the success |
| `${SANDBOX}` recreate after wipe | Tier B sandbox build block is idempotent; rerun after destroy is safe |
| Restore marker | Append a `${USER}`-signed line so the restored file is provably "post-restore", not the original |
| **🪤 Trap Risk T41** | Skipping the destroy-restore drill means you never validate that the journal is sufficient. **Fix:** every `c`-lab Task 2 IS the drill — do not skip it. |
| **🪤 Trap Risk T42** | "Fix live, forget the persistent file" — patching `/tmp/lab01c/report.txt` without writing to `/root/rhcsa_journal/` means a reboot loses the fix. **Fix:** journal write before cleanup, every task, every time. |

### 🔁 PERSISTENCE CHECK

| What was configured | Verification command | Why it matters |
|---|---|---|
| Destroy was clean | `test ! -d /tmp/lab01a && test ! -d /tmp/lab01c` returns 0 right after rm | Confirms the wipe actually wiped |
| Restore is byte-faithful (first 13 lines) | filtered `diff -u` empty | Journal → working copy is lossless |
| Restore is owned correctly | `stat -c '%U:%G' /tmp/lab01c/report-restored.txt` returns `root:labgrp_01_verify` | Chown back to the correct group survived the wipe |
| `${USER}` signed restore | `tail -1 /tmp/lab01c/report-restored.txt \| grep -c "by ${USER}$"` returns 1 | Sudo-u path still works after rebuild |
| Journal still exists | `ls /root/rhcsa_journal/lab-01a/task2/report.txt` succeeds | `/root/` survived the `/tmp` wipe — the whole reason `/root/` is the journal home |

> **Reboot reasoning (verbalize this aloud before Lab Closeout):** "If we rebooted now, `/tmp/lab01c/` would vanish because tmpfs is RAM. `/root/rhcsa_journal/lab-01a/task2/report.txt` would survive because `/root/` is on the root partition. The restore procedure above is the same procedure I'd run after a real reboot. T42 is the trap of relying on `/tmp` and assuming reboots can't happen — every RHCSA exam VM gets rebooted by the grader at least once."

### Journal write

```bash
LAB=lab-01c
TASK=task2
JDIR="/root/rhcsa_journal/${LAB}/${TASK}"
mkdir -p "$JDIR"
cp /tmp/lab01c/task2.txt                   "$JDIR/evidence.txt"
cp /tmp/lab01c/report-restored.txt         "$JDIR/report-restored.txt"
sha256sum /tmp/lab01c/report-restored.txt \
          /root/rhcsa_journal/lab-01a/task2/report.txt > "$JDIR/sha256sums.txt"

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
TOPIC:    Destroy-restore persistence drill — wipe /tmp Tier B, restore from /root/rhcsa_journal/
COMMANDS: sha256sum, rm -rf, cp, chown root:GROUP, chmod 0664, sudo -u USER bash -c '>>', diff -u <(head -n 13 A) B
TRAPS:    T41 rehearsed (destroy-restore done); T42 rehearsed (verbalized reboot reasoning); T44 deferred to Lab Closeout
TIER B:   ${USER} signed the restore marker; restored file is root:${GROUP} 0664
PERSISTENCE: /tmp wiped cleanly; /root/rhcsa_journal/ survived; restore is byte-faithful for first 13 lines
MISSED:   (fill in if any ⚠️ flags)
NEXT:     Lab 02a — Standard Error Redirection (2>, 2>/dev/null) — second stream, same Tier B + verify trilogy pattern
EOF

ls -la "$JDIR"
echo "exit was: $?"
```

### Cleanup (per-task — leaves Tier B sandbox intact for Lab Closeout)

```bash
rm -f /tmp/lab01c/warmup2.txt /tmp/lab01c/task2.txt /tmp/lab01c/report-restored.txt
getent passwd "${USER}"  >/dev/null && echo "✅ ${USER} still present"
getent group  "${GROUP}" >/dev/null && echo "✅ ${GROUP} still present"
test -d       "${SANDBOX}"          && echo "✅ ${SANDBOX} still present"
ls /tmp/lab01c
echo "exit was: $?"
```

### Troubleshoot

| Symptom | Fix |
|---|---|
| Part B: `❌ destroy incomplete` | A process has `/tmp/lab01a` or `/tmp/lab01c` open — `lsof +D /tmp/lab01a 2>/dev/null` to find it; close it; retry |
| Part C: `cp: cannot stat '/root/rhcsa_journal/...'` | The 01a journal was not copied. Go back to 01a Task 2 journal-write block, run it, retry |
| Part D: byte-fidelity `❌` | The journal copy was corrupted between 01a and 01c — re-run 01a Task 2's `cp` to journal, retry |
| Part D: `❌ unexpected line delta` (not +1) | `sudo -u` ran twice OR the `>>` ran as root by accident. Inspect `tail -3 report-restored.txt`; should have exactly one `Restored from journal` line |
| Part D: `❌ restore marker NOT signed by ${USER}` | You ran the `echo "--- Restored ..."` directly instead of via `sudo -u`. Re-run that single line with sudo -u |

> **STOP — paste the four `✅` lines from Part B + Part D before running Lab Closeout.**

---

## Lab Closeout — Bulletproof Teardown (Section 6)

```bash
set +e

# 1) Mount layer (no-op for this lab; pattern kept identical to anchor labs)
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
echo "── Lab 01c cleanup audit ──"
getent passwd "${USER}"  >/dev/null && echo "❌ user remains"    || echo "✅ user gone"
getent group  "${GROUP}" >/dev/null && echo "❌ group remains"   || echo "✅ group gone"
test -d "${SANDBOX}"                && echo "❌ sandbox remains" || echo "✅ sandbox gone"
test -d "${USER_HOME}"              && echo "❌ home remains"    || echo "✅ home gone"

set -e
echo "Cleanup complete by $(whoami) at $(date -Is)"
echo "exit was: $?"
```

> **STOP — paste the four `✅` audit lines. Lab 01 trilogy complete.**

The journal in `/root/rhcsa_journal/lab-01a/` and `/root/rhcsa_journal/lab-01c/` survives this teardown — that's the entire point. Resume from the next topic (Lab 02a) when you're ready.

---

## Lab 01c Checklist (2 tasks + closeout)

- [ ] Lab-Wide Setup — Tier B sandbox built; `${USER}=labuser_01_verify` distinct from 01a's user
- [ ] Task 1 — Completeness loop (`missing=0`); content shape (`wc -l=13`, 2 `===`, 6 `---`); ownership audit (01a asuser file owned by `labuser_01_stdout`); replay structural `diff` clean
- [ ] Task 2 — Pre-destroy snapshot + sha256; destroy clean; restore byte-faithful (first 13 lines); +1 line (restore marker); `${USER}` signed
- [ ] Lab Closeout — four `✅` audit lines; journal in `/root/rhcsa_journal/` survives

---

## Related Labs

| Lab | Connection |
|---|---|
| **Lab 01a** — Stdout Redirection RHCSA | The creator-seat lab this capstone audits |
| ⛔ **Lab 01b is intentionally absent** | Section 18 boundary — `>`/`>>` has no honest Ansible module |
| Lab 02a — Stderr Redirection RHCSA | Next topic in the trilogy — same Tier B + verify pattern, FD 2 instead of FD 1 |
| Lab 02c — Stderr Verify | The 02 analog of this lab |
| Lab 03a — Pipe Text Streams RHCSA | Builds on stdout; `tee` is a pipeline-stage `>` |

---

## Author

**Kelvin R. Tobias**
[kelvinintech.com](https://kelvinintech.com) · [GitHub](https://github.com/kelvintechnical) · [LinkedIn](https://www.linkedin.com/in/kelvin-r-tobias-211949219)
