# Lab 03c: Verifying Pipe Text Streams (Capstone) — Audit + Persistence Drill

- **Series:** linux-ops-mastery — Shells, Terminals & Redirection
- **Trilogy:** [`03a`](../lab-03a-pipe-text-streams-rhcsa/) (RHCSA hand-typed) → [`03b`](../lab-03b-pipe-text-streams-ansible/) (Ansible — pipelines via `ansible.builtin.shell` and `set -o pipefail`) → **`03c`** (Verify — you are here)
- **Career arcs covered:** RHCSA EX200 (every "filter, save the answer, count it" task — the grader reads only the file), SRE (alert-pipeline forensics), DevOps (CI summary verification), AI/MLOps (post-run dataset audits)
- **Prerequisite:** [`Lab 03a`](../lab-03a-pipe-text-streams-rhcsa/) completed; `/root/rhcsa_journal/lab-03a/task1/` and `task2/` populated
- **Time Estimate:** 25–35 minutes
- **Tasks:** 2 (Task 1 = audit 03a artifacts: nologin count, report shape, pipefail evidence · Task 2 = destroy-restore drill for `report.txt` + live append AS `${USER}` — **T41**)
- **Practice Directory (rotation #03):** `/etc` (same as 03a)
- **Sandbox (Tier B per Section 1.5):** `/tmp/lab03c` with `USER=labuser_03_verify`, `GROUP=labgrp_03_verify`, `USER_HOME=/tmp/lab03c/home_labuser_03_verify`. Built in Lab-Wide Setup; torn down + audited in **Lab Closeout** after Task 2.
- **Traps rehearsed this lab:** **T03-A** (audit the false\|true evidence file: EC_OFF=0, EC_ON=1) · **T41** (destroy-restore of report.txt) · **T42** (verbalize before Lab Closeout) · **T44** (Closeout audit must finish with four `✅`)

> **This lab's practice directory is: `/etc`** — same source as 03a. The audit verifies the pipeline products; Task 2 re-pipelines from `/etc` as 03c's user to prove the restored file is operationally live.

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
echo "⚠️  TRAP REMINDERS THIS LAB: T03-A T41 T42 T44"
echo "📁  PRACTICE DIR: /etc"
echo ""
echo "💡 /etc context (pipe source for the live append):"
ls -ld /etc
ls /etc | wc -l
echo ""
echo "📓 03a journal (must already exist):"
ls -la /root/rhcsa_journal/lab-03a/task1/ /root/rhcsa_journal/lab-03a/task2/
echo "Shell version: $BASH_VERSION"
```

> **STOP — paste header output. If 03a's journal `ls -la` is empty, GO BACK to 03a first.**

---

## Objective

03a built the pipeline reflex. 03c audits the products and proves the file artifacts can be rebuilt from the journal.

1. **Audit nologin count consistency** — `nologin-users.txt` and `nologin-asuser.txt` from 03a must have the same line count (same `grep` against the same `/etc/passwd`).
2. **Audit report shape** — `report.txt` from 03a Task 2 must contain exactly two `=== Report Pass ===` headers; the Pass-2 portion must include the `.d` directory list.
3. **Audit pipefail evidence** — `pipefail-asuser.txt` must show `EC_OFF=0` and `EC_ON=1` exactly. Proves 03a's Part D actually ran.
4. **Destroy-restore drill (T41)** — wipe `/tmp/lab03a/` and our sandbox; restore `report.txt` from the journal; continue it with a NEW pipeline pass AS 03c's `${USER}` using `tee -a` so the file *grows* post-restore.
5. **Verify** — sha256 of the first N lines matches the journal; line count after the live append is strictly greater than the journal's; new content is owned by `${USER}:${GROUP}`.

---

## Concept: Pipeline Evidence Is a Multi-File Story

A pipeline leaves more than one artifact. To audit 03a properly, 03c reads four kinds of files:

```
   ┌─────────────────────────────────────────────────────────────────┐
   │  03a output                       │  03c audit asks             │
   ├─────────────────────────────────────────────────────────────────┤
   │  nologin-users.txt (root tee)     │  line count = 24?           │
   │  nologin-asuser.txt (sudo -u tee) │  line count matches root?   │
   │                                   │  ownership = labuser_03_pipe?│
   │  report.txt (tee -a passes)       │  two "=== Report Pass" headers? │
   │                                   │  contains `.d` listing?      │
   │  pipefail-asuser.txt              │  EC_OFF=0 AND EC_ON=1?       │
   │                                   │  ownership = labuser_03_pipe?│
   └─────────────────────────────────────────────────────────────────┘
```

Five independent assertions over four files. Any one of them failing means 03a was incomplete somewhere — the audit tells you exactly where.

---

## Lab-Wide Setup — Tier B Sandbox Stack (Section 1.5)

```bash
sudo -i

export LAB_NUM=03
export LAB_SLUG=verify
export SANDBOX=/tmp/lab03c
export GROUP=labgrp_${LAB_NUM}_${LAB_SLUG}
export USER=labuser_${LAB_NUM}_${LAB_SLUG}
export USER_HOME=${SANDBOX}/home_${USER}

mkdir -p "${SANDBOX}" "${USER_HOME}"
mkdir -p /root/rhcsa_journal/lab-03c/task1
mkdir -p /root/rhcsa_journal/lab-03c/task2

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

> **STOP — paste setup output before Task 1.**

---

## Task 1 — Audit the 03a pipeline evidence

**Practice directory this task:** `/tmp/lab03c` for writes; reads against `/root/rhcsa_journal/lab-03a/` and `/etc/passwd`.

### Warm-Up

```bash
ls -la /root/rhcsa_journal/lab-03a/                    2>&1 | tee /tmp/lab03c/warmup.txt
find /root/rhcsa_journal/lab-03a -type f | sort
wc -l /root/rhcsa_journal/lab-03a/task*/*.txt 2>/dev/null
grep -c 'nologin' /etc/passwd
set -o pipefail
echo "Warm-up done by $(whoami) at $(date -Is)"
echo "exit was: $?"
```

> Carry from Lab 03a: `wc -l`, `grep -c`, `set -o pipefail`, `find -type f | sort`.

### Purpose

Five assertions:

1. **Completeness** — all six journal files from 03a exist and are non-empty.
2. **nologin count consistency** — `nologin-users.txt` (root tee) and `nologin-asuser.txt` (sudo -u tee) have identical line counts, both equal to `grep -c 'nologin' /etc/passwd` live.
3. **Tier B ownership** — `nologin-asuser.txt` is owned by `labuser_03_pipe`; `pipefail-asuser.txt` is owned by `labuser_03_pipe`. If owned by root, 03a's sudo -u steps never ran.
4. **report.txt shape** — contains exactly two `=== Report Pass` headers (Pass 1 + Pass 2); contains the `.d` listing.
5. **pipefail evidence** — `pipefail-asuser.txt` shows `EC_OFF=0` AND `EC_ON=1` (T03-A proved under sudo -u).

### WEAVE TRACE

| Warm-up / setup command          | Role inside Task 1                                                       |
|----------------------------------|--------------------------------------------------------------------------|
| `ls -la .../lab-03a/`            | Pre-flight                                                               |
| `find -type f \| sort`           | Deterministic inventory                                                  |
| `wc -l ..../task*/*.txt`         | Baseline counts                                                          |
| `grep -c 'nologin' /etc/passwd`  | Live oracle for the count-consistency assertion                          |
| `set -o pipefail`                | Audit pipes through `grep`/`wc` — pipefail surfaces missing files cleanly|
| `${USER}` (Tier B)               | Part E reproduces the `grep \| tee \| wc -l` pipeline as 03c's `${USER}` and `diff -u`s against the journal copy — Tier B drives the cross-check |

### Main command block

```bash
TASKLOG=/tmp/lab03c/task1.txt
A_JDIR=/root/rhcsa_journal/lab-03a

# ── Part A: completeness ──────────────────────────────────────────────
echo "═══ Part A: completeness audit ═══"               2>&1 | tee $TASKLOG
EXPECTED=(
    "${A_JDIR}/task1/nologin-users.txt"
    "${A_JDIR}/task1/nologin-asuser.txt"
    "${A_JDIR}/task1/evidence.txt"
    "${A_JDIR}/task2/report.txt"
    "${A_JDIR}/task2/pipefail-asuser.txt"
    "${A_JDIR}/task2/evidence.txt"
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

# ── Part B: nologin count consistency ─────────────────────────────────
echo "═══ Part B: nologin count consistency ═══"       | tee -a $TASKLOG
LIVE=$(grep -c 'nologin' /etc/passwd)
ROOT_LINES=$(wc -l < "${A_JDIR}/task1/nologin-users.txt")
USER_LINES=$(wc -l < "${A_JDIR}/task1/nologin-asuser.txt")
echo "live grep -c:        ${LIVE}"                    | tee -a $TASKLOG
echo "root tee file:       ${ROOT_LINES}"              | tee -a $TASKLOG
echo "sudo -u tee file:    ${USER_LINES}"              | tee -a $TASKLOG

if test "${LIVE}" -eq "${ROOT_LINES}" -a "${LIVE}" -eq "${USER_LINES}"; then
    echo "✅ all three counts match — pipeline+tee preserved row count" | tee -a $TASKLOG
else
    echo "❌ count mismatch — 03a pipeline lost or added rows"          | tee -a $TASKLOG
fi

# ── Part C: Tier B ownership ──────────────────────────────────────────
echo "═══ Part C: Tier B ownership audit ═══"          | tee -a $TASKLOG
stat -c '%U:%G %a %n' "${A_JDIR}/task1/nologin-asuser.txt"     | tee -a $TASKLOG
stat -c '%U:%G %a %n' "${A_JDIR}/task2/pipefail-asuser.txt"    | tee -a $TASKLOG

N_OWN=$(stat -c '%U' "${A_JDIR}/task1/nologin-asuser.txt")
P_OWN=$(stat -c '%U' "${A_JDIR}/task2/pipefail-asuser.txt")
if test "${N_OWN}" = "labuser_03_pipe" -a "${P_OWN}" = "labuser_03_pipe"; then
    echo "✅ both Tier B files owned by labuser_03_pipe"               | tee -a $TASKLOG
else
    echo "❌ ownership wrong — sudo -u steps in 03a did not actually run" | tee -a $TASKLOG
fi

# ── Part D: report.txt shape ──────────────────────────────────────────
echo "═══ Part D: report.txt shape audit ═══"          | tee -a $TASKLOG
PASS_HEADERS=$(grep -c '^=== Report Pass' "${A_JDIR}/task2/report.txt")
HAS_OS_REL=$(grep -c '^NAME='             "${A_JDIR}/task2/report.txt")
HAS_DOTD=$(grep -c '\.d$'                 "${A_JDIR}/task2/report.txt")
echo "Pass headers: ${PASS_HEADERS}  NAME= lines: ${HAS_OS_REL}  .d entries: ${HAS_DOTD}" | tee -a $TASKLOG

if test "${PASS_HEADERS}" -eq 2 -a "${HAS_OS_REL}" -ge 1 -a "${HAS_DOTD}" -ge 1; then
    echo "✅ report.txt has both passes, os-release content, and .d listing" | tee -a $TASKLOG
else
    echo "❌ report.txt shape wrong — tee/tee -a sequence in 03a was incomplete" | tee -a $TASKLOG
fi

# ── Part E: pipefail evidence audit ───────────────────────────────────
echo "═══ Part E: pipefail evidence audit ═══"         | tee -a $TASKLOG
cat "${A_JDIR}/task2/pipefail-asuser.txt"              | tee -a $TASKLOG

EC_OFF_OK=$(grep -c 'WITHOUT pipefail: 0' "${A_JDIR}/task2/pipefail-asuser.txt")
EC_ON_OK=$(grep -c  'WITH    pipefail: 1' "${A_JDIR}/task2/pipefail-asuser.txt")

if test "${EC_OFF_OK}" -ge 1 -a "${EC_ON_OK}" -ge 1; then
    echo "✅ T03-A proven under sudo -u (EC_OFF=0, EC_ON=1)"            | tee -a $TASKLOG
else
    echo "❌ pipefail evidence wrong — 03a Part D did not produce both lines" | tee -a $TASKLOG
fi

# ── Part F: cross-check pipeline AS ${USER} (Tier B weave) ────────────
echo "═══ Part F: cross-check grep | tee | wc -l AS ${USER} ═══" | tee -a $TASKLOG
sudo -u "${USER}" bash -c \
    'grep "nologin" /etc/passwd \
        | tee '"${USER_HOME}"'/nologin-crosscheck.txt \
        | wc -l'

CC_LINES=$(wc -l < "${USER_HOME}/nologin-crosscheck.txt")
stat -c '%U:%G %a %n' "${USER_HOME}/nologin-crosscheck.txt"    | tee -a $TASKLOG

# Compare against 03a's root-tee output byte-for-byte (same input, same filter)
diff -u "${A_JDIR}/task1/nologin-users.txt" \
        "${USER_HOME}/nologin-crosscheck.txt" \
    | tee -a $TASKLOG \
    && echo "✅ cross-check byte-identical to 03a root-tee output" \
    || echo "(diff above lists drift; clean diff = empty)" \
    | tee -a $TASKLOG

echo "exit was: $?"
```

### Human-readable breakdown

1. **Part A — completeness.** Loop six expected files. Empty files count as `❌`.
2. **Part B — count consistency.** Three numbers must be equal: live `grep -c`, root-tee file lines, sudo-u tee file lines. The same input through the same filter must give the same count regardless of who ran it.
3. **Part C — Tier B ownership.** Both `nologin-asuser.txt` and `pipefail-asuser.txt` must be literally `labuser_03_pipe`. If either is root, the sudo -u step in 03a never ran.
4. **Part D — report shape.** Two `=== Report Pass` headers (Pass 1 + Pass 2); at least one `NAME=` from `/etc/os-release`; at least one `.d` entry from the directory filter.
5. **Part E — pipefail.** `pipefail-asuser.txt` must contain both EC_OFF=0 and EC_ON=1 lines. Together they prove T03-A under non-root identity.
6. **Part F — cross-check.** Re-run the `grep | tee | wc -l` as 03c's `${USER}`. The output should be byte-identical to 03a's root-tee output because the input is the same `/etc/passwd` and the filter is the same `nologin` pattern. `diff -u` empty = success.

### Reading it left to right

```
test "${LIVE}" -eq "${ROOT_LINES}" -a "${LIVE}" -eq "${USER_LINES}"
│    │          │   │              │   │          │   │
│    │          │   │              │   │          │   └─ sudo -u tee file
│    │          │   │              │   │          └─ second equality
│    │          │   │              │   └─ live oracle
│    │          │   │              └─ AND
│    │          │   └─ root tee file
│    │          └─ equality
│    └─ live oracle (grep -c on /etc/passwd)
└─ POSIX test
```

### The story

The "same input, same filter, same count" principle is the foundation of every grading script. If a student's `grep -c | tee | wc -l` produces a different number than the grader's, *something diverged*. 03c trains you to think about pipelines as inputs, filters, and outputs that have to line up no matter who ran them.

Process substitution (`<(cmd)`) shows up again in production audits all the time — `diff -u <(sort file1) <(sort file2)` is the canonical "are these two unordered lists equivalent" check. Internalize the pattern; it's everywhere.

### Expected output

```text
═══ Part A: completeness audit ═══
✅ /root/rhcsa_journal/lab-03a/task1/nologin-users.txt (24 lines)
✅ /root/rhcsa_journal/lab-03a/task1/nologin-asuser.txt (24 lines)
✅ /root/rhcsa_journal/lab-03a/task1/evidence.txt (38 lines)
✅ /root/rhcsa_journal/lab-03a/task2/report.txt (10 lines)
✅ /root/rhcsa_journal/lab-03a/task2/pipefail-asuser.txt (2 lines)
✅ /root/rhcsa_journal/lab-03a/task2/evidence.txt (32 lines)
missing-or-empty files: 0
═══ Part B: nologin count consistency ═══
live grep -c:        24
root tee file:       24
sudo -u tee file:    24
✅ all three counts match — pipeline+tee preserved row count
═══ Part C: Tier B ownership audit ═══
labuser_03_pipe:labgrp_03_pipe 644 /root/rhcsa_journal/lab-03a/task1/nologin-asuser.txt
labuser_03_pipe:labgrp_03_pipe 644 /root/rhcsa_journal/lab-03a/task2/pipefail-asuser.txt
✅ both Tier B files owned by labuser_03_pipe
═══ Part D: report.txt shape audit ═══
Pass headers: 2  NAME= lines: 1  .d entries: 76
✅ report.txt has both passes, os-release content, and .d listing
═══ Part E: pipefail evidence audit ═══
as-labuser_03_pipe WITHOUT pipefail: 0
as-labuser_03_pipe WITH    pipefail: 1
✅ T03-A proven under sudo -u (EC_OFF=0, EC_ON=1)
═══ Part F: cross-check grep | tee | wc -l AS labuser_03_verify ═══
24
labuser_03_verify:labgrp_03_verify 644 /tmp/lab03c/home_labuser_03_verify/nologin-crosscheck.txt
✅ cross-check byte-identical to 03a root-tee output
exit was: 0
```

### Switches

| Token                                      | Meaning                                                            |
|--------------------------------------------|--------------------------------------------------------------------|
| `grep -c PAT FILE`                         | Count matching lines                                                |
| `test N -eq M -a N -eq O`                  | All three numbers equal                                             |
| `test STR1 = STR2 -a STR3 = STR4`          | Both string equalities true                                         |
| `diff -u FILE1 FILE2`                      | Unified diff; empty output = identical                              |
| `sudo -u USER bash -c '... \| tee FILE \| ...'` | Pipeline runs as USER; tee target lands on USER                |

### Concept Card

| Concept | What it does |
|---|---|
| Three-way count consistency | live `grep -c` = root-tee file = sudo-u-tee file (same input, same filter) |
| Tier B ownership assertion | Two files must be owned by literal `labuser_03_pipe` from 03a |
| Multi-condition `test` | `-a` joins assertions; one false fails the whole check |
| Cross-check via byte-diff | Pipeline reproducibility across identities — `diff -u` empty proves it |
| **🪤 Trap Risk T03-A** | Audit catches it if 03a's Part D didn't produce EC_OFF=0 / EC_ON=1 |
| **🪤 Trap Risk T44** | Closeout audit must end with four `✅` lines |

### 🔁 PERSISTENCE CHECK

| What was configured | Verification command | Why it matters |
|---|---|---|
| 03a journal complete | `find /root/rhcsa_journal/lab-03a -type f \| wc -l` returns 9+ | Every artifact survived |
| Count consistency | live `grep -c` matches both 03a tee files | Pipeline+tee preserved row count |
| Tier B ownership | both files owned by `labuser_03_pipe` | Sudo -u steps ran |
| pipefail evidence | `EC_OFF=0` AND `EC_ON=1` in the file | T03-A proved under non-root |
| Cross-check reproducible | `diff -u` empty | Same input + same filter = same bytes |

### Journal write

```bash
LAB=lab-03c
TASK=task1
JDIR="/root/rhcsa_journal/${LAB}/${TASK}"
mkdir -p "$JDIR"
cp /tmp/lab03c/task1.txt                          "$JDIR/evidence.txt"
cp "${USER_HOME}/nologin-crosscheck.txt"          "$JDIR/nologin-crosscheck.txt"

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
TOPIC:    Audit Lab 03a pipeline evidence — completeness, count consistency, Tier B ownership, report shape, pipefail evidence, byte-diff cross-check
COMMANDS: test -eq -a, grep -c, stat -c '%U', diff -u, sudo -u ${USER} bash -c, wc -l
TRAPS:    T03-A audited (EC_OFF=0, EC_ON=1 found); T44 deferred to Lab Closeout
TIER B:   Cross-check file owned by ${USER}:${GROUP}; byte-identical to 03a root-tee output
MISSED:   (fill in if any ⚠️ flags)
NEXT:     task2 — destroy-restore of report.txt (T41); live append AS ${USER}; reboot reasoning (T42)
EOF

ls -la "$JDIR"
echo "exit was: $?"
```

### Cleanup (per-task — leaves Tier B sandbox intact)

```bash
rm -f /tmp/lab03c/warmup.txt /tmp/lab03c/task1.txt
# Keep nologin-crosscheck.txt — Task 2 uses it as a comparator
getent passwd "${USER}"  >/dev/null && echo "✅ ${USER} still present"
getent group  "${GROUP}" >/dev/null && echo "✅ ${GROUP} still present"
test -d       "${SANDBOX}"          && echo "✅ ${SANDBOX} still present"
ls /tmp/lab03c
echo "exit was: $?"
```

### Troubleshoot

| Symptom | Fix |
|---|---|
| Part A: any `❌ MISSING` | 03a journal-write skipped a file. Re-run that block in 03a, retry |
| Part B: counts differ | Live `/etc/passwd` was edited between 03a and 03c (e.g., a new nologin user). Compare timestamps with `stat -c %y` and decide if you need to rerun 03a |
| Part C: `❌ ownership wrong` | 03a Task 1 Chain 6 or Task 2 Part D used `>` instead of `sudo -u`. Re-run those steps |
| Part D: Pass headers != 2 | 03a Task 2 Part A used `tee` (without `-a`) on Pass 2 and overwrote Pass 1. Re-run that block with `tee -a` |
| Part E: pipefail evidence missing | 03a Task 2 Part D `sudo -u` block had a typo or didn't run. Re-run it, retry |
| Part F: `diff` non-empty | `/etc/passwd` was modified between 03a and 03c. Decide whether to retry 03a or accept the drift and document it |

> **STOP — paste the five `✅` lines from Parts A–F before Task 2.**

---

## Task 2 — Destroy-restore drill for report.txt + live append (T41)

**Practice directory this task:** `/tmp/lab03c` for the restore + live append; reads against `/etc` for new pipeline content.

### Warm-Up

```bash
ls -la /tmp/lab03c /tmp/lab03a 2>/dev/null             2>&1 | tee /tmp/lab03c/warmup2.txt
df -h /tmp | tail -1
findmnt /tmp 2>/dev/null || echo "/tmp not separately mounted"
sha256sum /root/rhcsa_journal/lab-03a/task2/report.txt
set -o pipefail
echo "Warm-up done by $(whoami) at $(date -Is)"
echo "exit was: $?"
```

> Carry from Task 1: `wc -l`, `stat -c '%U:%G %a %n'`, `grep -c`, `diff -u`. Add `sha256sum` for the byte-fidelity check.

### Purpose

1. **Snapshot** `report.txt` (line count + sha256).
2. **Destroy** `/tmp/lab03a` (if it lingers) and `/tmp/lab03c`. Verify both gone.
3. **Restore** `report.txt` from the journal into 03c's sandbox; chown root:`${GROUP}`, chmod `0664` so `${USER}` can append.
4. **Live append** AS `${USER}`: run a fresh `grep '\.conf$' /etc | tee -a` pipeline; the restored file grows by exactly the new pipeline output.
5. **Verify** — head -N sha256 matches the journal, total line count is journal + new pipeline lines, and the new section is signed by `${USER}`.

### WEAVE TRACE

| Warm-up / setup command          | Role inside Task 2                                                       |
|----------------------------------|--------------------------------------------------------------------------|
| `ls -la /tmp/lab03c /tmp/lab03a` | Pre-destroy snapshot                                                     |
| `df -h /tmp \| tail -1`          | Free space sanity                                                        |
| `findmnt /tmp`                   | Confirms /tmp is tmpfs (the persistence story)                            |
| `sha256sum report.txt`           | The hash we compare against after restore                                |
| `${USER}` (Tier B)               | Part D runs the live append (`tee -a`) as `${USER}` and signs the appended section — Tier B carries the post-restore growth |

### Main command block

```bash
TASKLOG=/tmp/lab03c/task2.txt
A_REPORT=/root/rhcsa_journal/lab-03a/task2/report.txt

# ── Part A: snapshot ──────────────────────────────────────────────────
echo "═══ Part A: pre-destroy snapshot ═══"            2>&1 | tee $TASKLOG
A_LINES=$(wc -l < "${A_REPORT}")
A_HASH=$(sha256sum "${A_REPORT}" | awk '{print $1}')
echo "journal report.txt lines:  ${A_LINES}"           | tee -a $TASKLOG
echo "journal report.txt sha256: ${A_HASH}"            | tee -a $TASKLOG

# ── Part B: destroy ───────────────────────────────────────────────────
echo "═══ Part B: destroy /tmp/lab03a and /tmp/lab03c ═══" | tee -a $TASKLOG
rm -rf /tmp/lab03a /tmp/lab03c

if test ! -d /tmp/lab03a -a ! -d /tmp/lab03c; then
    echo "✅ destroy clean"                             | tee -a $TASKLOG
else
    echo "❌ destroy incomplete"                        | tee -a $TASKLOG
fi

# ── Part C: restore ───────────────────────────────────────────────────
echo "═══ Part C: restore report.txt from journal ═══" | tee -a $TASKLOG
mkdir -p "${SANDBOX}" "${USER_HOME}"
chown -R "${USER}:${GROUP}" "${SANDBOX}"

cp "${A_REPORT}" "${SANDBOX}/report-restored.txt"
chown root:"${GROUP}" "${SANDBOX}/report-restored.txt"
chmod 0664           "${SANDBOX}/report-restored.txt"

# Verify byte-fidelity: first ${A_LINES} lines must hash to ${A_HASH}
RESTORE_HASH=$(head -n "${A_LINES}" "${SANDBOX}/report-restored.txt" \
    | sha256sum | awk '{print $1}')
echo "restored head sha256: ${RESTORE_HASH}"           | tee -a $TASKLOG
if test "${RESTORE_HASH}" = "${A_HASH}"; then
    echo "✅ first ${A_LINES} lines byte-faithful"      | tee -a $TASKLOG
else
    echo "❌ restored file drifted"                     | tee -a $TASKLOG
fi

# ── Part D: live append AS ${USER} via tee -a ─────────────────────────
echo "═══ Part D: live append AS ${USER} via tee -a ═══" | tee -a $TASKLOG

sudo -u "${USER}" bash -c \
    'echo "=== Report Pass 3 (restored by '"${USER}"' at $(date -Is)) ===" \
        | tee -a '"${SANDBOX}"'/report-restored.txt'

sudo -u "${USER}" bash -c \
    'ls /etc | grep "\.conf$" \
        | tee -a '"${SANDBOX}"'/report-restored.txt \
        | wc -l'                                       | tee -a $TASKLOG

sudo -u "${USER}" bash -c \
    'echo "=== End Pass 3 ===" \
        | tee -a '"${SANDBOX}"'/report-restored.txt'   >/dev/null

# ── Part E: verify forward motion + ownership ─────────────────────────
echo "═══ Part E: forward-motion + ownership ═══"      | tee -a $TASKLOG

NEW_LINES=$(wc -l < "${SANDBOX}/report-restored.txt")
APPENDED=$((NEW_LINES - A_LINES))
echo "lines now: ${NEW_LINES}  added: ${APPENDED}"     | tee -a $TASKLOG
test "${APPENDED}" -gt 2 \
    && echo "✅ tee -a appended header, .conf list, and footer" \
    || echo "❌ append did not produce expected delta" \
    | tee -a $TASKLOG

# The new "Pass 3" header must contain ${USER}'s name
PASS3_LINES=$(grep -c "restored by ${USER}" "${SANDBOX}/report-restored.txt")
echo "Pass 3 header signed by ${USER}: ${PASS3_LINES} time(s)" | tee -a $TASKLOG
test "${PASS3_LINES}" -eq 1 \
    && echo "✅ Pass 3 signed exactly once by ${USER}" \
    || echo "❌ Pass 3 sign-count wrong" \
    | tee -a $TASKLOG

# Three Pass headers total now: original 1 + 2 from 03a + 1 from 03c
TOTAL_HEADERS=$(grep -c '^=== Report Pass' "${SANDBOX}/report-restored.txt")
echo "total Pass headers: ${TOTAL_HEADERS}"            | tee -a $TASKLOG
test "${TOTAL_HEADERS}" -eq 3 \
    && echo "✅ three Pass headers (03a Pass 1+2 + 03c Pass 3)" \
    || echo "❌ Pass header count wrong" \
    | tee -a $TASKLOG

stat -c '%U:%G %a %n' "${SANDBOX}/report-restored.txt" | tee -a $TASKLOG

echo "exit was: $?"
```

### Human-readable breakdown

1. **Part A — snapshot.** Save line count + sha256 of the journal's `report.txt`.
2. **Part B — destroy.** Wipe both `/tmp/lab03a` and `/tmp/lab03c`. Confirm both are gone.
3. **Part C — restore.** Rebuild the Tier B sandbox dirs, copy `report.txt` from journal, chown root:`${GROUP}`, chmod `0664`. Hash the first `${A_LINES}` lines and compare against the snapshot.
4. **Part D — live append.** Three sudo -u steps:
   - Append a `=== Report Pass 3 (restored by ${USER} at ${date}) ===` header line.
   - Append the `ls /etc | grep '\.conf$'` pipeline output via `tee -a`.
   - Append a `=== End Pass 3 ===` footer.
   All as `${USER}`. The file grows by header + .conf-count + footer = 2 + N lines, where N is the number of .conf entries in `/etc`.
5. **Part E — forward motion + ownership.** Three assertions:
   - `APPENDED > 2` (more than just the two boundary lines — the .conf list landed).
   - Exactly one `restored by ${USER}` line (sudo -u actually signed the header).
   - Exactly three `=== Report Pass` headers (03a's two + 03c's one).

### Reading it left to right (the multi-step sudo -u sequence)

```
sudo -u "${USER}" bash -c '
    ls /etc | grep "\.conf$" \
        | tee -a /path/report-restored.txt \
        | wc -l
'
│       │            │
│       │            └─ count what tee passed through (= line count of .conf list)
│       └─ also dump it to the file (tee -a = append)
└─ standard ls→grep filter
```

Note the single-quote / double-quote dance: the outer `bash -c` argument is single-quoted so `$(date -Is)` and `${USER}` get expanded by THIS shell, not the inner one. We want the *outer* shell to interpolate `${USER}` because the inner shell (running as `${USER}`) would re-evaluate `${USER}` to the same string anyway — same answer, less ambiguity.

### The story

The destroy-restore-and-continue drill is the strongest evidence that a journaled artifact is operationally useful. A static restore (just `cp` from journal) proves byte-fidelity. A continued restore (`cp` then `tee -a`) proves the file is still a *live file* — same group ownership, same writability, same place in the pipeline ecosystem.

`set -o pipefail` was the whole point of 03a Task 2. In Task 2 here, every pipeline runs through `tee -a` and `wc -l` — if pipefail were off and one of the upstream commands failed, the file would still get written (empty content) and `wc -l` would return 0. With pipefail on, the failure propagates, the file isn't corrupted, and the `❌` branch fires. That's the link 03c forges between two labs apart.

### Expected output

```text
═══ Part A: pre-destroy snapshot ═══
journal report.txt lines:  10
journal report.txt sha256: 7d2c8b…
═══ Part B: destroy /tmp/lab03a and /tmp/lab03c ═══
✅ destroy clean
═══ Part C: restore report.txt from journal ═══
restored head sha256: 7d2c8b…
✅ first 10 lines byte-faithful
═══ Part D: live append AS labuser_03_verify via tee -a ═══
8
═══ Part E: forward-motion + ownership ═══
lines now: 20  added: 10
✅ tee -a appended header, .conf list, and footer
Pass 3 header signed by labuser_03_verify: 1 time(s)
✅ Pass 3 signed exactly once by labuser_03_verify
total Pass headers: 3
✅ three Pass headers (03a Pass 1+2 + 03c Pass 3)
root:labgrp_03_verify 664 /tmp/lab03c/report-restored.txt
exit was: 0
```

### Switches

| Token                                | Meaning                                                            |
|--------------------------------------|--------------------------------------------------------------------|
| `sha256sum FILE \| awk '{print $1}'` | Print only the hash                                                |
| `head -n N FILE \| sha256sum`        | Hash of first N lines                                              |
| `chmod 0664`                         | Owner rw, group rw, others r — group can write                    |
| `chown root:GROUP`                   | Owner stays root, group becomes GROUP (lets GROUP write via 0664) |
| `sudo -u USER bash -c '...'`         | Pipeline runs as USER                                              |
| `tee -a FILE`                        | Append (vs `tee` which truncates)                                  |
| `grep -c '^=== Report Pass'`         | Count anchored Pass-header lines                                   |

### Concept Card

| Concept | What it does |
|---|---|
| Sha256 head-only check | Proves first N lines unchanged across destroy/restore |
| Restore-and-continue | Restored file is live: tee -a appends new content as `${USER}` |
| Multi-line `sudo -u` sequence | Three appends, each with its own sudo -u — keeps each step auditable |
| Group-writable restored file | `chown root:GROUP` + `chmod 0664` lets `${USER}` append without owning |
| Pass header tally | Total Pass headers after restore = original 2 + restore's 1 = 3 |
| **🪤 Trap Risk T41** | Destroy-restore drill is the proof the journal works; skipping it leaves T41 un-rehearsed |
| **🪤 Trap Risk T42** | Verbalize the reboot-reasoning before Closeout: `/tmp` evaporates, `/root/` survives |

### 🔁 PERSISTENCE CHECK

| What was configured | Verification command | Why it matters |
|---|---|---|
| Destroy clean | `test ! -d /tmp/lab03a -a ! -d /tmp/lab03c` returns 0 right after rm | Wipe was complete |
| Restore byte-faithful | `head -n ${A_LINES} restored \| sha256sum` matches journal hash | Lossless from journal |
| Pass 3 added | `grep -c '=== Report Pass' restored` returns 3 | New header appended |
| Pass 3 signed by `${USER}` | `grep -c "restored by ${USER}" restored` returns 1 | Sudo -u actually ran |
| Total grew | `wc -l restored` > A_LINES + 2 | tee -a added the .conf list |
| Group-writable | `stat -c '%a' restored` returns 664 | Lets `${USER}` keep appending |

> **Reboot reasoning (verbalize before Lab Closeout):** "On a real reboot, `/tmp/lab03c/report-restored.txt` is gone. `/root/rhcsa_journal/lab-03a/task2/report.txt` survives. The restore procedure above is what I'd run post-reboot to get back to a working state. T42 is the trap of editing the `/tmp` copy and never updating `/root/`."

### Journal write

```bash
LAB=lab-03c
TASK=task2
JDIR="/root/rhcsa_journal/${LAB}/${TASK}"
mkdir -p "$JDIR"
cp /tmp/lab03c/task2.txt                       "$JDIR/evidence.txt"
cp "${SANDBOX}/report-restored.txt"            "$JDIR/report-restored.txt"
sha256sum "${SANDBOX}/report-restored.txt" \
          /root/rhcsa_journal/lab-03a/task2/report.txt \
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
TOPIC:    Destroy-restore drill for report.txt + live append AS USER via tee -a
COMMANDS: sha256sum | awk '{print $1}', head -n N | sha256sum, rm -rf, cp, chown root:GROUP, chmod 0664, sudo -u ${USER} bash -c '...| tee -a ...'
TRAPS:    T41 rehearsed (destroy-restore); T42 verbalized; T44 deferred to Lab Closeout
TIER B:   Pass 3 signed once by ${USER}; group ${GROUP}; 0664 lets future appends work
PERSISTENCE: /tmp wiped; /root/rhcsa_journal/ survived; first ${A_LINES} lines byte-faithful
MISSED:   (fill in if any ⚠️ flags)
NEXT:     Lab 04a — Combined Redirection (&>, 2>&1); same Tier B + verify trilogy pattern
EOF

ls -la "$JDIR"
echo "exit was: $?"
```

### Cleanup (per-task — leaves Tier B sandbox intact for Lab Closeout)

```bash
rm -f /tmp/lab03c/warmup2.txt /tmp/lab03c/task2.txt
rm -f "${SANDBOX}/report-restored.txt" "${USER_HOME}/nologin-crosscheck.txt"
getent passwd "${USER}"  >/dev/null && echo "✅ ${USER} still present"
getent group  "${GROUP}" >/dev/null && echo "✅ ${GROUP} still present"
test -d       "${SANDBOX}"          && echo "✅ ${SANDBOX} still present"
ls /tmp/lab03c
echo "exit was: $?"
```

### Troubleshoot

| Symptom | Fix |
|---|---|
| Part B `❌ destroy incomplete` | Process has `/tmp/lab03a` open — `lsof +D /tmp/lab03a`; close it; retry |
| Part C: `cp: cannot stat …report.txt` | 03a journal copy missing. Re-run 03a Task 2 journal-write, retry |
| Part C: `❌ restored file drifted` | Journal file modified between 03a and 03c. Re-copy from 03a Task 2 evidence |
| Part D: `Permission denied` writing | `chmod 0664` step skipped — file is 0600. Re-chmod and retry |
| Part E: `❌ Pass 3 sign-count wrong` | sudo -u step didn't expand `${USER}` — single-quoting the entire `bash -c` argument swallowed the interpolation. Use double quotes around the inner string |
| Part E: `❌ total Pass headers` not 3 | 03a Pass 2 was missing (only 1 Pass header in journal) — re-run 03a Task 2 Part A |

> **STOP — paste Part A snapshot hash, Part C `byte-faithful` line, Part E `Pass 3 signed` line, and `total Pass headers=3` before Lab Closeout.**

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
echo "── Lab 03c cleanup audit ──"
getent passwd "${USER}"  >/dev/null && echo "❌ user remains"    || echo "✅ user gone"
getent group  "${GROUP}" >/dev/null && echo "❌ group remains"   || echo "✅ group gone"
test -d "${SANDBOX}"                && echo "❌ sandbox remains" || echo "✅ sandbox gone"
test -d "${USER_HOME}"              && echo "❌ home remains"    || echo "✅ home gone"

set -e
echo "Cleanup complete by $(whoami) at $(date -Is)"
echo "exit was: $?"
```

> **STOP — paste four `✅` audit lines. Lab 03 trilogy complete. The first three topics of Shells & Text Fluency are now in the ADHD-method trilogy format.**

---

## Lab 03c Checklist (2 tasks + closeout)

- [ ] Lab-Wide Setup — Tier B sandbox built; `${USER}=labuser_03_verify`
- [ ] Task 1 — completeness=0 missing; count consistency `✅`; Tier B ownership = `labuser_03_pipe`; report shape `✅`; pipefail evidence `✅`; cross-check byte-identical
- [ ] Task 2 — pre-destroy hash captured; destroy clean; first `${A_LINES}` lines byte-faithful; Pass 3 signed exactly once by `${USER}`; three Pass headers total
- [ ] Lab Closeout — four `✅` audit lines

---

## Related Labs

| Lab | Connection |
|---|---|
| **Lab 03a** — Pipe Text Streams RHCSA | The creator-seat lab this audits |
| **Lab 03b** — Pipe Text Streams Ansible | `ansible.builtin.shell` is the only honest path for a pipeline; the b-lab is kept here as a trap-rehearsal artifact (T03-B forgetting `set -o pipefail`, T03-C ignoring `${PIPESTATUS[@]}` when registering the result). |
| **Lab 01c / 02c** — Stdout / Stderr Verify | Previous topics' verify capstones — same Tier B + destroy-restore pattern |
| Lab 04a — Combined Redirection | Next topic — `&>` and `2>&1` deep dive |

---

## Author

**Kelvin R. Tobias**
[kelvinintech.com](https://kelvinintech.com) · [GitHub](https://github.com/kelvintechnical) · [LinkedIn](https://www.linkedin.com/in/kelvin-r-tobias-211949219)
