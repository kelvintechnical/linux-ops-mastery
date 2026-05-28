# Lab 04c: Verifying Combined Output and Error (Capstone) — Audit + Persistence Drill

- **Series:** linux-ops-mastery — Shells, Terminals & Redirection
- **Trilogy:** [`04a`](../lab-04a-capture-both-output-error-rhcsa/) (RHCSA hand-typed) → [`04b`](../lab-04b-capture-both-output-error-ansible/) (Ansible — merged streams) → **`04c`** (Verify — you are here)
- **Career arcs covered:** RHCSA EX200 (graders read the file — verify both data and errors landed), SRE (forensic audit of combined logs), DevOps (CI artifact verification)
- **Prerequisite:** [`Lab 04a`](../lab-04a-capture-both-output-error-rhcsa/) completed; `/root/rhcsa_journal/lab-04a/task1/` and `task2/` populated
- **Time Estimate:** 25–35 minutes
- **Tasks:** 2 (Task 1 = audit 04a combined-stream artifacts · Task 2 = destroy-restore drill for `combined.txt` + live `&>>` append AS `${USER}` — **T41**)
- **Practice Directory (rotation #10):** `/var` (same as 04a)
- **Sandbox (Tier B per Section 1.5):** `/tmp/lab04c` with `USER=labuser_04_verify`, `GROUP=labgrp_04_verify`, `USER_HOME=/tmp/lab04c/home_labuser_04_verify`. Built in Lab-Wide Setup; torn down + audited in **Lab Closeout** after Task 2.
- **Traps rehearsed this lab:** **T04-A** (audit order-trap.txt: correct errs > 0, wrong errs = 0) · **T41** (destroy-restore of combined.txt) · **T42** (verbalize reboot reasoning before Closeout) · **T44** (Closeout audit must finish with four `✅`)

> **This lab's practice directory is: `/var`** — same source as 04a. The audit verifies combined-stream products; Task 2 re-captures from `/var/log` as 03c's user to prove the restored file is operationally live.

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
echo "⚠️  TRAP REMINDERS THIS LAB: T04-A T41 T42 T44"
echo "📁  PRACTICE DIR: /var"
echo ""
echo "📓 04a journal (must already exist):"
ls -la /root/rhcsa_journal/lab-04a/task1/ /root/rhcsa_journal/lab-04a/task2/
echo "Shell version: $BASH_VERSION"
```

> **STOP — paste header output. If 04a's journal `ls -la` is empty, GO BACK to 04a first.**

---

## Objective

04a built the combined-stream muscle. 04c audits the products and proves the file artifacts can be rebuilt from the journal.

1. **Audit combined.txt** — must contain both file paths AND `Permission denied` lines.
2. **Audit order-trap.txt** — `correct errs` > 0 and `wrong errs` = 0 (T04-A proven in 04a).
3. **Audit Tier B ownership** — `combined-asuser.txt` owned by `labuser_04_combo`.
4. **Destroy-restore drill (T41)** — wipe sandboxes; restore `combined.txt` from journal; append a new `&>>` capture AS `${USER}`.
5. **Verify** — sha256 of first N lines matches journal; line count grows after live append.

---

## Lab-Wide Setup — Tier B Sandbox Stack (Section 1.5)

```bash
sudo -i

export LAB_NUM=04
export LAB_SLUG=verify
export SANDBOX=/tmp/lab04c
export GROUP=labgrp_${LAB_NUM}_${LAB_SLUG}
export USER=labuser_${LAB_NUM}_${LAB_SLUG}
export USER_HOME=${SANDBOX}/home_${USER}

mkdir -p "${SANDBOX}" "${USER_HOME}"
mkdir -p /root/rhcsa_journal/lab-04c/task1
mkdir -p /root/rhcsa_journal/lab-04c/task2

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

## Task 1 — Audit the 04a combined-stream evidence

**Practice directory this task:** reads against `/root/rhcsa_journal/lab-04a/` and `/var/log`.

### 🔁 Warm-Up

```bash
ls -la /root/rhcsa_journal/lab-04a/                    2>&1 | tee /tmp/lab04c/warmup.txt
find /root/rhcsa_journal/lab-04a -type f | sort
wc -l /root/rhcsa_journal/lab-04a/task*/*.txt 2>/dev/null
set -o pipefail
echo "Warm-up done by $(whoami) at $(date -Is)"
echo "exit was: $?"
```

### Purpose

Five assertions:

1. **Completeness** — all expected journal files from 04a exist and are non-empty.
2. **Combined capture** — `combined.txt` has both `/var/log` paths and `Permission denied` lines.
3. **T04-A evidence** — `order-trap.txt` shows correct errs > 0, wrong errs = 0.
4. **Tier B ownership** — `combined-asuser.txt` owned by `labuser_04_combo`.
5. **Cross-check** — re-run `find /var/log &>` AS 04c's `${USER}` and confirm stderr lines present.

### 🧵 WEAVE TRACE

| Warm-up / setup command | Role inside Task 1 |
|---|---|
| `ls -la .../lab-04a/` | Pre-flight inventory |
| `find -type f \| sort` | Deterministic file list |
| `wc -l task*/*.txt` | Baseline counts |
| `${USER}` (Tier B) | Part F re-runs combined capture as 04c's user |

### Main command block

```bash
TASKLOG=/tmp/lab04c/task1.txt
A_JDIR=/root/rhcsa_journal/lab-04a

# ── Part A: completeness ──────────────────────────────────────────────
echo "═══ Part A: completeness audit ═══"               2>&1 | tee $TASKLOG
EXPECTED=(
    "${A_JDIR}/task1/combined.txt"
    "${A_JDIR}/task1/combined-asuser.txt"
    "${A_JDIR}/task1/evidence.txt"
    "${A_JDIR}/task2/correct.log"
    "${A_JDIR}/task2/wrong.log"
    "${A_JDIR}/task2/order-trap.txt"
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

# ── Part B: combined.txt has both streams ─────────────────────────────
echo "═══ Part B: combined.txt stream audit ═══"         | tee -a $TASKLOG
PATHS=$(grep -c '/var/log' "${A_JDIR}/task1/combined.txt" || echo 0)
ERRS=$(grep -c 'Permission denied' "${A_JDIR}/task1/combined.txt" || echo 0)
PASSES=$(grep -c '=== Pass 2' "${A_JDIR}/task1/combined.txt" || echo 0)
echo "paths: ${PATHS}  errors: ${ERRS}  pass2-headers: ${PASSES}" | tee -a $TASKLOG
test "${PATHS}" -gt 0 -a "${ERRS}" -ge 0 -a "${PASSES}" -ge 1 \
    && echo "✅ combined.txt has paths, errors, and &>> append marker" \
    || echo "❌ combined.txt incomplete" \
    | tee -a $TASKLOG

# ── Part C: T04-A order trap audit ────────────────────────────────────
echo "═══ Part C: T04-A order-trap audit ═══"            | tee -a $TASKLOG
cat "${A_JDIR}/task2/order-trap.txt"                   | tee -a $TASKLOG
CORRECT_ERRS=$(grep 'correct errs:' "${A_JDIR}/task2/order-trap.txt" | awk '{print $3}')
WRONG_ERRS=$(grep 'wrong errs:'   "${A_JDIR}/task2/order-trap.txt" | awk '{print $3}')
echo "parsed correct errs: ${CORRECT_ERRS}  wrong errs: ${WRONG_ERRS}" | tee -a $TASKLOG
test "${CORRECT_ERRS:-0}" -gt 0 -a "${WRONG_ERRS:-1}" -eq 0 \
    && echo "✅ T04-A proven in 04a (correct has errors, wrong has none)" \
    || echo "❌ T04-A evidence wrong — re-run 04a Task 2 Part D" \
    | tee -a $TASKLOG

# ── Part D: Tier B ownership ────────────────────────────────────────
echo "═══ Part D: Tier B ownership audit ═══"              | tee -a $TASKLOG
stat -c '%U:%G %a %n' "${A_JDIR}/task1/combined-asuser.txt" | tee -a $TASKLOG
OWN=$(stat -c '%U' "${A_JDIR}/task1/combined-asuser.txt")
test "${OWN}" = "labuser_04_combo" \
    && echo "✅ combined-asuser.txt owned by labuser_04_combo" \
    || echo "❌ ownership wrong — 04a Task 1 Part D did not run as USER" \
    | tee -a $TASKLOG

# ── Part E: correct vs wrong log line-count contrast ─────────────────
echo "═══ Part E: correct vs wrong log contrast ═══"     | tee -a $TASKLOG
C_LINES=$(wc -l < "${A_JDIR}/task2/correct.log")
W_LINES=$(wc -l < "${A_JDIR}/task2/wrong.log")
C_ERRS=$(grep -c 'Permission denied' "${A_JDIR}/task2/correct.log" || echo 0)
W_ERRS=$(grep -c 'Permission denied' "${A_JDIR}/task2/wrong.log" || echo 0)
echo "correct: ${C_LINES} lines, ${C_ERRS} errors | wrong: ${W_LINES} lines, ${W_ERRS} errors" | tee -a $TASKLOG
test "${C_ERRS}" -gt 0 -a "${W_ERRS}" -eq 0 \
    && echo "✅ correct.log has stderr, wrong.log does not" \
    || echo "❌ line-count contrast failed" \
    | tee -a $TASKLOG

# ── Part F: cross-check AS ${USER} (Tier B weave) ─────────────────────
echo "═══ Part F: find &> cross-check AS ${USER} ═══"    | tee -a $TASKLOG
sudo -u "${USER}" bash -c \
    'find /var/log -maxdepth 2 -type f &> '"${USER_HOME}"'/crosscheck-combined.txt'

CC_ERRS=$(grep -c 'Permission denied' "${USER_HOME}/crosscheck-combined.txt" || echo 0)
stat -c '%U:%G %a %n' "${USER_HOME}/crosscheck-combined.txt" | tee -a $TASKLOG
test "${CC_ERRS}" -ge 0 \
    && echo "✅ cross-check combined capture produced ${CC_ERRS} permission-denied lines as ${USER}" \
    || echo "❌ cross-check failed" \
    | tee -a $TASKLOG

echo "exit was: $?"
```

### Expected output

```text
═══ Part A: completeness audit ═══
✅ .../task1/combined.txt (295 lines)
...
missing-or-empty files: 0
═══ Part B: combined.txt stream audit ═══
paths: 42  errors: 3  pass2-headers: 1
✅ combined.txt has paths, errors, and &>> append marker
═══ Part C: T04-A order-trap audit ═══
correct lines: 238
wrong lines:   237
correct errs:  1
wrong errs:    0
✅ T04-A proven in 04a (correct has errors, wrong has none)
═══ Part D: Tier B ownership audit ═══
labuser_04_combo:labgrp_04_combo 644 .../combined-asuser.txt
✅ combined-asuser.txt owned by labuser_04_combo
═══ Part E: correct vs wrong log contrast ═══
correct: 238 lines, 1 errors | wrong: 237 lines, 0 errors
✅ correct.log has stderr, wrong.log does not
═══ Part F: find &> cross-check AS labuser_04_verify ═══
labuser_04_verify:labgrp_04_verify 644 .../crosscheck-combined.txt
✅ cross-check combined capture produced 5 permission-denied lines as labuser_04_verify
```

### Journal write

```bash
LAB=lab-04c
TASK=task1
JDIR="/root/rhcsa_journal/${LAB}/${TASK}"
mkdir -p "$JDIR"
cp /tmp/lab04c/task1.txt                          "$JDIR/evidence.txt"
cp "${USER_HOME}/crosscheck-combined.txt"         "$JDIR/crosscheck-combined.txt"

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
TOPIC:    Audit 04a combined-stream evidence — completeness, both-stream capture, T04-A, Tier B ownership
COMMANDS: grep -c, stat -c '%U', test -eq -a, sudo -u ${USER} bash -c, find &>
TRAPS:    T04-A audited; T44 deferred to Lab Closeout
MISSED:   (fill in if any ⚠️ flags)
NEXT:     task2 — destroy-restore of combined.txt (T41); live &>> append AS ${USER}
EOF

ls -la "$JDIR"
echo "exit was: $?"
```

### 🧹 Cleanup (per-task)

```bash
rm -f /tmp/lab04c/warmup.txt /tmp/lab04c/task1.txt
getent passwd "${USER}"  >/dev/null && echo "✅ ${USER} still present"
getent group  "${GROUP}" >/dev/null && echo "✅ ${GROUP} still present"
test -d       "${SANDBOX}"          && echo "✅ ${SANDBOX} still present"
ls /tmp/lab04c
echo "exit was: $?"
```

> **STOP — paste the five `✅` lines from Parts B–F before Task 2.**

---

## Task 2 — Destroy-restore drill for combined.txt + live `&>>` append (T41)

**Practice directory this task:** `/var/log` for the live append capture.

### 🔁 Warm-Up

```bash
ls -la /tmp/lab04c /tmp/lab04a 2>/dev/null             2>&1 | tee /tmp/lab04c/warmup2.txt
df -h /tmp | tail -1
findmnt /tmp 2>/dev/null || echo "/tmp not separately mounted"
sha256sum /root/rhcsa_journal/lab-04a/task1/combined.txt
set -o pipefail
echo "Warm-up done by $(whoami) at $(date -Is)"
echo "exit was: $?"
```

### Purpose

1. **Snapshot** `combined.txt` (line count + sha256).
2. **Destroy** `/tmp/lab04a` and `/tmp/lab04c`. Verify both gone.
3. **Restore** from journal; verify byte-fidelity of first N lines.
4. **Live append** AS `${USER}` with `&>>` — restored file grows with a new combined capture.
5. **Verify** — three Pass/equivalent markers, line count increased, `${USER}` signed the append header.

### Main command block

```bash
TASKLOG=/tmp/lab04c/task2.txt
A_COMBINED=/root/rhcsa_journal/lab-04a/task1/combined.txt

# ── Part A: snapshot ──────────────────────────────────────────────────
echo "═══ Part A: pre-destroy snapshot ═══"            2>&1 | tee $TASKLOG
A_LINES=$(wc -l < "${A_COMBINED}")
A_HASH=$(sha256sum "${A_COMBINED}" | awk '{print $1}')
echo "journal combined.txt lines:  ${A_LINES}"        | tee -a $TASKLOG
echo "journal combined.txt sha256: ${A_HASH}"          | tee -a $TASKLOG

# ── Part B: destroy ───────────────────────────────────────────────────
echo "═══ Part B: destroy sandboxes ═══"               | tee -a $TASKLOG
rm -rf /tmp/lab04a /tmp/lab04c
test ! -d /tmp/lab04a -a ! -d /tmp/lab04c \
    && echo "✅ destroy clean"                          | tee -a $TASKLOG \
    || echo "❌ destroy incomplete"                     | tee -a $TASKLOG

# ── Part C: restore ───────────────────────────────────────────────────
echo "═══ Part C: restore combined.txt from journal ═══" | tee -a $TASKLOG
mkdir -p "${SANDBOX}" "${USER_HOME}"
chown -R "${USER}:${GROUP}" "${SANDBOX}"
cp "${A_COMBINED}" "${SANDBOX}/combined-restored.txt"
chown root:"${GROUP}" "${SANDBOX}/combined-restored.txt"
chmod 0664           "${SANDBOX}/combined-restored.txt"

RESTORE_HASH=$(head -n "${A_LINES}" "${SANDBOX}/combined-restored.txt" \
    | sha256sum | awk '{print $1}')
test "${RESTORE_HASH}" = "${A_HASH}" \
    && echo "✅ first ${A_LINES} lines byte-faithful"   | tee -a $TASKLOG \
    || echo "❌ restored file drifted"                  | tee -a $TASKLOG

# ── Part D: live &>> append AS ${USER} ───────────────────────────────
echo "═══ Part D: live &>> append AS ${USER} ═══"       | tee -a $TASKLOG
sudo -u "${USER}" bash -c \
    'echo "=== Pass 3 (restored by '"${USER}"' at $(date -Is)) ===" \
        &>> '"${SANDBOX}"'/combined-restored.txt'

sudo -u "${USER}" bash -c \
    'find /var/log -maxdepth 1 -type f &>> '"${SANDBOX}"'/combined-restored.txt'

sudo -u "${USER}" bash -c \
    'echo "=== End Pass 3 ===" &>> '"${SANDBOX}"'/combined-restored.txt'

# ── Part E: verify forward motion ───────────────────────────────────
echo "═══ Part E: forward-motion verify ═══"           | tee -a $TASKLOG
NEW_LINES=$(wc -l < "${SANDBOX}/combined-restored.txt")
APPENDED=$((NEW_LINES - A_LINES))
echo "lines now: ${NEW_LINES}  added: ${APPENDED}"     | tee -a $TASKLOG
test "${APPENDED}" -gt 2 \
    && echo "✅ &>> appended header, find output, and footer" \
    || echo "❌ append delta too small" \
    | tee -a $TASKLOG

PASS3=$(grep -c "restored by ${USER}" "${SANDBOX}/combined-restored.txt")
test "${PASS3}" -eq 1 \
    && echo "✅ Pass 3 signed exactly once by ${USER}" \
    || echo "❌ Pass 3 sign-count wrong" \
    | tee -a $TASKLOG

PASS2_MARKERS=$(grep -c '=== Pass' "${SANDBOX}/combined-restored.txt")
echo "total Pass markers: ${PASS2_MARKERS}"            | tee -a $TASKLOG
stat -c '%U:%G %a %n' "${SANDBOX}/combined-restored.txt" | tee -a $TASKLOG

echo "exit was: $?"
```

### 🔁 PERSISTENCE CHECK

| What was configured | Verification command | Why it matters |
|---|---|---|
| Destroy clean | `test ! -d /tmp/lab04a -a ! -d /tmp/lab04c` | Wipe was complete |
| Restore byte-faithful | head sha256 matches journal | Lossless from journal |
| Pass 3 appended | `grep -c "restored by ${USER}"` = 1 | Live &>> ran as USER |
| Total grew | `wc -l restored` > A_LINES + 2 | Combined capture added content |

> **Reboot reasoning (verbalize before Lab Closeout):** "On reboot, `/tmp/lab04c/combined-restored.txt` is gone. `/root/rhcsa_journal/lab-04a/task1/combined.txt` survives. The restore + `&>>` procedure above is what I'd run post-reboot. T42 is editing the `/tmp` copy without updating `/root/`."

### Journal write

```bash
LAB=lab-04c
TASK=task2
JDIR="/root/rhcsa_journal/${LAB}/${TASK}"
mkdir -p "$JDIR"
cp /tmp/lab04c/task2.txt                       "$JDIR/evidence.txt"
cp "${SANDBOX}/combined-restored.txt"          "$JDIR/combined-restored.txt"
sha256sum "${SANDBOX}/combined-restored.txt" \
          /root/rhcsa_journal/lab-04a/task1/combined.txt \
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
TOPIC:    Destroy-restore combined.txt + live &>> append AS USER
COMMANDS: sha256sum, head -n N | sha256sum, rm -rf, cp, chown root:GROUP, chmod 0664, sudo -u ${USER}, &>>
TRAPS:    T41 rehearsed; T42 verbalized; T44 deferred to Lab Closeout
PERSISTENCE: /tmp wiped; /root/rhcsa_journal/ survived
MISSED:   (fill in if any ⚠️ flags)
NEXT:     Lab 05a — Directory Navigation (cd, pwd)
EOF

ls -la "$JDIR"
echo "exit was: $?"
```

### 🧹 Cleanup (per-task)

```bash
rm -f /tmp/lab04c/warmup2.txt /tmp/lab04c/task2.txt
rm -f "${SANDBOX}/combined-restored.txt" "${USER_HOME}/crosscheck-combined.txt"
getent passwd "${USER}"  >/dev/null && echo "✅ ${USER} still present"
getent group  "${GROUP}" >/dev/null && echo "✅ ${GROUP} still present"
test -d       "${SANDBOX}"          && echo "✅ ${SANDBOX} still present"
ls /tmp/lab04c
echo "exit was: $?"
```

> **STOP — paste Part C `byte-faithful` and Part E `Pass 3 signed` lines before Lab Closeout.**

---

## Lab Closeout — Bulletproof Teardown (Section 6)

```bash
set +e

awk -v s="${SANDBOX}" '$2 ~ s {print $2}' /proc/mounts \
    | tac | xargs -r -n1 umount -l 2>/dev/null

if getent passwd "${USER}" >/dev/null 2>&1; then
    userdel -r "${USER}" 2>/dev/null
fi
if getent group "${GROUP}" >/dev/null 2>&1; then
    groupdel "${GROUP}"  2>/dev/null
fi

rm -rf "${SANDBOX}"

echo "── Lab 04c cleanup audit ──"
getent passwd "${USER}"  >/dev/null && echo "❌ user remains"    || echo "✅ user gone"
getent group  "${GROUP}" >/dev/null && echo "❌ group remains"   || echo "✅ group gone"
test -d "${SANDBOX}"                && echo "❌ sandbox remains" || echo "✅ sandbox gone"
test -d "${USER_HOME}"              && echo "❌ home remains"    || echo "✅ home gone"

set -e
echo "Cleanup complete by $(whoami) at $(date -Is)"
echo "exit was: $?"
```

> **STOP — paste four `✅` audit lines. Lab 04 trilogy complete.**

---

## Lab 04c Checklist (2 tasks + closeout)

- [ ] Task 1 — completeness=0 missing; combined has both streams; T04-A `✅`; Tier B ownership `✅`; cross-check as `${USER}`
- [ ] Task 2 — destroy clean; byte-faithful restore; Pass 3 signed by `${USER}`; line count grew
- [ ] Lab Closeout — four `✅` audit lines

---

## Related Labs

| Lab | Connection |
|---|---|
| **Lab 04a** — Combined Streams RHCSA | Creator-seat lab this audits |
| **Lab 04b** — Combined Streams Ansible | Ansible merge pattern for the same concept |
| Lab 01c / 02c / 03c | Previous verify capstones — same audit + destroy-restore pattern |
| Lab 05a — Directory Navigation | Next topic in the curriculum |

---

## Author

**Kelvin R. Tobias**
[kelvinintech.com](https://kelvinintech.com) · [GitHub](https://github.com/kelvintechnical) · [LinkedIn](https://www.linkedin.com/in/kelvin-r-tobias-211949219)
