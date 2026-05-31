# Lab 21c: Verifying Live Log Monitoring (Capstone) — Audit + Destroy-Restore

- **Series:** linux-ops-mastery — Logging, Troubleshooting, and Real-Time Observability
- **Trilogy:** [`21a`](../lab-21a-tail-f-live-logs-rhcsa/) (RHCSA hand-typed) → [`21b`](../lab-21b-tail-f-live-logs-ansible/) (Ansible automation) → **`21c`** (Verify capstone)
- **Career arcs covered:** RHCSA exam verification discipline, SRE evidence audits, incident replay reliability
- **Prerequisite:** Lab 21a complete with `/root/rhcsa_journal/lab-21a/task1/` and `task2/`
- **Time Estimate:** 25–35 minutes
- **Tasks:** 2 (Task 1 = audit 21a evidence set; Task 2 = destroy-restore + re-run bounded follower as verify user)
- **Practice Directory (rotation #21):** `/boot` (context), writes in `/tmp/lab21c`
- **Sandbox (Tier B):** `/tmp/lab21c` with `USER=labuser_21_livelog`, `GROUP=labgrp_21_livelog`, `USER_HOME=/tmp/lab21c/home_labuser_21_livelog`
- **Traps rehearsed this lab:** **T21-A** (verify rotate-safe capture exists) · **T21-B** (verify bounded tails) · **T41** (mandatory destroy-restore) · **T44** (closeout audit must end with four `✅`)

> **This lab's practice directory is: `/boot`** — audit references this context while all verification artifacts are produced under `/tmp/lab21c` and `/root/rhcsa_journal/lab-21c/`.

---

## LAB HEADER BLOCK

```bash
echo "🖥️  ENV:   ${ENV:-DECLARE_ME}"
echo "📁  PRACTICE DIR: /boot"
ls -ld /boot
echo ""
echo "📓 21a journal presence check:"
ls -la /root/rhcsa_journal/lab-21a/task1 /root/rhcsa_journal/lab-21a/task2
echo "🕒  TIME:  $(date -Is)"
echo "👤  USER:  $(whoami)@$(hostname)"
echo "⚠️  TRAP REMINDERS THIS LAB: T21-A T21-B T41 T44"
echo "exit was: $?"
```

---

## Objective

Audit whether 21a produced correct and persistent evidence, then prove the workflow survives loss of `/tmp` artifacts:

1. Confirm required journal captures exist and are non-empty.
2. Validate key markers from Task 1 and Task 2 evidence.
3. Destroy ephemeral copies and restore from journal.
4. Re-run bounded follower as verify user and confirm ownership.

---

## Lab-Wide Setup — Tier B Stack

```bash
sudo -i

export LAB_NUM=21
export LAB_SLUG=livelog
export SANDBOX=/tmp/lab21c
export GROUP=labgrp_${LAB_NUM}_${LAB_SLUG}
export USER=labuser_${LAB_NUM}_${LAB_SLUG}
export USER_HOME=${SANDBOX}/home_${USER}

mkdir -p "${SANDBOX}" "${USER_HOME}" /root/rhcsa_journal/lab-21c/task1 /root/rhcsa_journal/lab-21c/task2
getent group  "${GROUP}" >/dev/null || groupadd "${GROUP}"
getent passwd "${USER}"  >/dev/null || useradd -d "${USER_HOME}" -M -s /bin/bash -g "${GROUP}" "${USER}"
chown -R "${USER}:${GROUP}" "${SANDBOX}"

id "${USER}"
ls -ld "${SANDBOX}" "${USER_HOME}" /boot
getent group "${GROUP}"
getent passwd "${USER}"
echo "setup complete: $(date -Is)"
echo "exit was: $?"
```

---

## Task 1 — Audit Lab 21a captures in journal

**Practice directory this task:** `/boot` context + `/root/rhcsa_journal/lab-21a/` audit source.

### Warm-Up

```bash
ls -la /root/rhcsa_journal/lab-21a/task1                 2>&1 | tee /tmp/lab21c/warmup.txt
ls -la /root/rhcsa_journal/lab-21a/task2                 2>&1 | tee -a /tmp/lab21c/warmup.txt
find /root/rhcsa_journal/lab-21a -type f | sort          2>&1 | tee -a /tmp/lab21c/warmup.txt
echo "exit was: $?"
```

### Purpose

Verify the complete evidence chain from 21a:

- Task 1 bounded follow captures exist.
- Task 2 rotate comparison outputs exist (`out-f.txt`, `out-F.txt`).
- Rotate-safe marker appears in `out-F.txt`.

### Main command block

```bash
TASKLOG=/tmp/lab21c/task1.txt
A=/root/rhcsa_journal/lab-21a

echo "═══ Part A: required files presence and size ═══" 2>&1 | tee "${TASKLOG}"
REQ=(
  "${A}/task1/evidence.txt"
  "${A}/task1/messages-live-capture.txt"
  "${A}/task1/journal-follow.txt"
  "${A}/task1/user-producer-follow.txt"
  "${A}/task2/evidence.txt"
  "${A}/task2/out-f.txt"
  "${A}/task2/out-F.txt"
)
MISS=0
for f in "${REQ[@]}"; do
  if test -s "$f"; then
    echo "✅ $f ($(wc -l < "$f") lines)" | tee -a "${TASKLOG}"
  else
    echo "❌ $f missing-or-empty" | tee -a "${TASKLOG}"
    MISS=$((MISS+1))
  fi
done
echo "missing count: ${MISS}" | tee -a "${TASKLOG}"

echo "═══ Part B: semantic checks for T21-A/T21-B evidence ═══" | tee -a "${TASKLOG}"
grep -c "after-rotate-newfile-2" "${A}/task2/out-F.txt" | tee -a "${TASKLOG}"
grep -c "after-rotate-newfile-1" "${A}/task2/out-f.txt" | tee -a "${TASKLOG}"
grep -c "lab21a-task1 event-" "${A}/task1/messages-live-capture.txt" | tee -a "${TASKLOG}"

if grep -q "after-rotate-newfile-2" "${A}/task2/out-F.txt"; then
  echo "✅ T21-A avoided path proven in out-F.txt" | tee -a "${TASKLOG}"
else
  echo "❌ missing rotate-safe marker in out-F.txt" | tee -a "${TASKLOG}"
fi

echo "exit was: $?"
```

### Journal write

```bash
LAB=lab-21c
TASK=task1
JDIR="/root/rhcsa_journal/${LAB}/${TASK}"
mkdir -p "$JDIR"
cp /tmp/lab21c/task1.txt "$JDIR/evidence.txt"

cat > "$JDIR/done.txt" <<EOF
LAB:    ${LAB}
TASK:   ${TASK}
DATE:   $(date -Is)
USER:   $(whoami)@$(hostname)
STATUS: COMPLETE
EOF
```

---

## Task 2 — Destroy-Restore + re-run tail with timeout as verify user

**Practice directory this task:** `/tmp/lab21c` with `/boot` context.

### Warm-Up

```bash
df -h /tmp | tail -n 1                                 2>&1 | tee /tmp/lab21c/warmup2.txt
findmnt /tmp 2>/dev/null || echo "/tmp not separately mounted" | tee -a /tmp/lab21c/warmup2.txt
echo "exit was: $?"
```

### Purpose

Run the T41 destroy-restore drill, then prove a fresh bounded tail capture still works as the verify user.

### Main command block

```bash
TASKLOG=/tmp/lab21c/task2.txt
A=/root/rhcsa_journal/lab-21a

echo "═══ Part A: snapshot journal source hashes ═══" 2>&1 | tee "${TASKLOG}"
sha256sum "${A}/task2/out-F.txt" | tee -a "${TASKLOG}"
sha256sum "${A}/task1/messages-live-capture.txt" | tee -a "${TASKLOG}"

echo "═══ Part B: destroy ephemeral tree (T41) ═══" | tee -a "${TASKLOG}"
rm -rf /tmp/lab21a /tmp/lab21c
if test ! -d /tmp/lab21a -a ! -d /tmp/lab21c; then
  echo "✅ destroy clean" | tee -a "${TASKLOG}"
else
  echo "❌ destroy incomplete" | tee -a "${TASKLOG}"
fi

echo "═══ Part C: restore into verify sandbox ═══" | tee -a "${TASKLOG}"
mkdir -p "${SANDBOX}" "${USER_HOME}" "${SANDBOX}/restore"
chown -R "${USER}:${GROUP}" "${SANDBOX}"
cp "${A}/task2/out-F.txt" "${SANDBOX}/restore/out-F-restored.txt"
cp "${A}/task1/messages-live-capture.txt" "${SANDBOX}/restore/messages-restored.txt"
sha256sum "${SANDBOX}/restore/out-F-restored.txt" | tee -a "${TASKLOG}"
sha256sum "${SANDBOX}/restore/messages-restored.txt" | tee -a "${TASKLOG}"

echo "═══ Part D: re-run bounded tail as verify user ═══" | tee -a "${TASKLOG}"
sudo -u "${USER}" bash -c '
  LOG=/tmp/lab21c/home_labuser_21_livelog/verify.log
  (
    sleep 1; echo "verify-ev-1 $(date -Is)" >> "$LOG"
    sleep 1; echo "verify-ev-2 $(date -Is)" >> "$LOG"
  ) &
  timeout 5 tail -n 0 -F "$LOG" > /tmp/lab21c/home_labuser_21_livelog/verify-follow.txt
'

wc -l "${USER_HOME}/verify-follow.txt" | tee -a "${TASKLOG}"
grep -c "verify-ev-" "${USER_HOME}/verify-follow.txt" | tee -a "${TASKLOG}"
stat -c '%U:%G %a %n' "${USER_HOME}/verify.log" "${USER_HOME}/verify-follow.txt" | tee -a "${TASKLOG}"

echo "exit was: $?"
```

### Trap callout

- **T41 rehearsed:** ephemeral `/tmp` artifacts destroyed and restored from journal.
- **T21-B avoided:** re-run uses bounded `timeout 5`.
- **Tier B proven:** verify artifacts are owned by `labuser_21_livelog:labgrp_21_livelog`.

### Journal write

```bash
LAB=lab-21c
TASK=task2
JDIR="/root/rhcsa_journal/${LAB}/${TASK}"
mkdir -p "$JDIR"
cp /tmp/lab21c/task2.txt                       "$JDIR/evidence.txt"
cp "${USER_HOME}/verify-follow.txt"            "$JDIR/verify-follow.txt"
cp "${SANDBOX}/restore/out-F-restored.txt"     "$JDIR/out-F-restored.txt"

cat > "$JDIR/done.txt" <<EOF
LAB:    ${LAB}
TASK:   ${TASK}
DATE:   $(date -Is)
USER:   $(whoami)@$(hostname)
STATUS: COMPLETE
EOF
```

---

## Lab Closeout — Bulletproof Teardown (Section 6)

```bash
set +e

awk -v s="${SANDBOX}" '$2 ~ s {print $2}' /proc/mounts | tac | xargs -r -n1 umount -l 2>/dev/null

if getent passwd "${USER}" >/dev/null 2>&1; then
  userdel -r "${USER}" 2>/dev/null
fi
if getent group "${GROUP}" >/dev/null 2>&1; then
  groupdel "${GROUP}" 2>/dev/null
fi

rm -rf "${SANDBOX}"

echo "── Lab 21c cleanup audit ──"
getent passwd "${USER}" >/dev/null && echo "❌ user remains" || echo "✅ user gone"
getent group  "${GROUP}" >/dev/null && echo "❌ group remains" || echo "✅ group gone"
test -d "${SANDBOX}" && echo "❌ sandbox remains" || echo "✅ sandbox gone"
test -d "${USER_HOME}" && echo "❌ home remains" || echo "✅ home gone"

set -e
echo "Cleanup complete at $(date -Is)"
echo "exit was: $?"
```

---

## Lab 21c Checklist (2 tasks + closeout)

- [ ] Task 1 audit: required 21a evidence files all present and non-empty
- [ ] Task 1 semantic checks: rotate-safe marker appears in `out-F.txt`
- [ ] Task 2: destroy-restore complete; re-run bounded follow as verify user succeeds
- [ ] Closeout: four `✅` audit lines

---

## Author

**Kelvin R. Tobias**  
[kelvinintech.com](https://kelvinintech.com) · [GitHub](https://github.com/kelvintechnical) · [LinkedIn](https://www.linkedin.com/in/kelvin-r-tobias-211949219)
