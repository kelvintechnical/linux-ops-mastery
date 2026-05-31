# Lab 04c: Verifying Capture Both Output and Error (Capstone) — Audit + Persistence Drill

- **Series:** linux-ops-mastery — Shells, Terminals & Redirection
- **Trilogy:** [`04a`](../lab-04a-capture-both-output-error-rhcsa/) → [`04b`](../lab-04b-capture-both-output-error-ansible/) → **`04c`** (verify capstone)
- **Career arcs covered:** RHCSA EX200, SRE incident forensics, DevOps CI log auditing
- **Prerequisite:** 04a journal populated at `/root/rhcsa_journal/lab-04a/` (optional: reference 04b evidence for comparison)
- **Time Estimate:** 25–35 minutes
- **Tasks:** **2 exactly** (Task 1 audit matrix · Task 2 destroy-restore drill)
- **Practice Directory (same as 04a):** `/lib64`
- **Tier B Sandbox:** `/tmp/lab04c`, `USER=labuser_04_verify`, `GROUP=labgrp_04_verify`, `USER_HOME=/tmp/lab04c/home_labuser_04_verify`
- **Traps rehearsed:** **T04-A**, **T41**, **T42**, **T44**

> This lab follows the same verify flow as 02c: audit evidence first, then persistence drill.

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
echo "📁  PRACTICE DIR: /lib64"
echo ""
echo "💡 /lib64 context:"
ls -ld /lib64
ls /lib64 | head -n 5
echo ""
echo "📓 04a journal precheck:"
ls -la /root/rhcsa_journal/lab-04a/task1/ /root/rhcsa_journal/lab-04a/task2/
echo "Shell version: $BASH_VERSION"
```

> **STOP:** paste header output before setup.

---

## Objective

1. Audit 04a artifacts under `/root/rhcsa_journal/lab-04a/`.
2. Prove T04-A: wrong-order file lacks in-file stderr evidence, correct-order file contains `cannot access`.
3. Use `grep -c`, `wc -l`, `stat`, and `diff -u` for assertions.
4. Run T41 destroy-restore, then re-verify live combined capture as `labuser_04_verify`.

---

## Concept: Four-Way Assertion Matrix (02c style)

```
   ┌───────────────────────────────────────────────────────────────────┐
   │  04a artifact                      │  04c assertion               │
   ├───────────────────────────────────────────────────────────────────┤
   │  posix-combined.txt               │  has "cannot access"         │
   │  ampersand-combined.txt           │  has "cannot access"         │
   │  right.log (correct order)        │  has "cannot access"         │
   │  wrong.log (wrong order)          │  0 "cannot access" in-file   │
   └───────────────────────────────────────────────────────────────────┘
```

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

id "${USER}"
ls -ld "${SANDBOX}" "${USER_HOME}"
getent group "${GROUP}"
getent passwd "${USER}"
echo "Sandbox built by $(whoami) at $(date -Is)"
echo "exit was: $?"
```

> **STOP:** paste `id`, `ls -ld`, and `getent` lines before Task 1.

---

## Task 1 — Audit 04a Evidence

**Practice directory this task:** write to `/tmp/lab04c`, read from `/root/rhcsa_journal/lab-04a`.

### Warm-Up

```bash
ls -la /root/rhcsa_journal/lab-04a/                     2>&1 | tee /tmp/lab04c/warmup.txt
find /root/rhcsa_journal/lab-04a -type f | sort
wc -l /root/rhcsa_journal/lab-04a/task1/*.txt /root/rhcsa_journal/lab-04a/task2/*.log 2>/dev/null
stat -c '%U:%G %a %n' /root/rhcsa_journal/lab-04a/task2/cum-combined-asuser.txt 2>/dev/null
set -o pipefail
echo "Warm-up done by $(whoami) at $(date -Is)"
echo "exit was: $?"
```

### Main command block

```bash
TASKLOG=/tmp/lab04c/task1.txt
A_JDIR=/root/rhcsa_journal/lab-04a

echo "═══ Part A: completeness audit ═══"                 2>&1 | tee "$TASKLOG"
EXPECTED=(
  "${A_JDIR}/task1/posix-combined.txt"
  "${A_JDIR}/task1/ampersand-combined.txt"
  "${A_JDIR}/task2/right.log"
  "${A_JDIR}/task2/wrong.log"
  "${A_JDIR}/task2/cum-combined-asuser.txt"
)
MISSING=0
for f in "${EXPECTED[@]}"; do
  if test -s "$f"; then
    echo "✅ $f ($(wc -l < "$f") lines)"
  else
    echo "❌ $f MISSING OR EMPTY"
    MISSING=$((MISSING + 1))
  fi
done                                                     2>&1 | tee -a "$TASKLOG"
echo "missing-or-empty files: ${MISSING}"               | tee -a "$TASKLOG"

echo "═══ Part B: grep -c + wc -l assertions ═══"       | tee -a "$TASKLOG"
P_CA=$(grep -c 'cannot access' "${A_JDIR}/task1/posix-combined.txt" 2>/dev/null || echo 0)
A_CA=$(grep -c 'cannot access' "${A_JDIR}/task1/ampersand-combined.txt" 2>/dev/null || echo 0)
R_CA=$(grep -c 'cannot access' "${A_JDIR}/task2/right.log" 2>/dev/null || echo 0)
W_CA=$(grep -c 'cannot access' "${A_JDIR}/task2/wrong.log" 2>/dev/null || echo 0)
R_LN=$(wc -l < "${A_JDIR}/task2/right.log")
W_LN=$(wc -l < "${A_JDIR}/task2/wrong.log")
echo "posix cannot-access=${P_CA}"                      | tee -a "$TASKLOG"
echo "ampersand cannot-access=${A_CA}"                  | tee -a "$TASKLOG"
echo "right.log cannot-access=${R_CA} lines=${R_LN}"    | tee -a "$TASKLOG"
echo "wrong.log cannot-access=${W_CA} lines=${W_LN}"    | tee -a "$TASKLOG"

test "${R_CA}" -gt 0 -a "${W_CA}" -eq 0 \
  && echo "✅ T04-A proven: correct-order file captured stderr, wrong-order file did not" \
  || echo "❌ T04-A not proven — recheck 04a order demonstration" \
  | tee -a "$TASKLOG"

echo "═══ Part C: stat ownership check ═══"              | tee -a "$TASKLOG"
stat -c '%U:%G %a %n' "${A_JDIR}/task2/cum-combined-asuser.txt" | tee -a "$TASKLOG"
C_OWNER=$(stat -c '%U' "${A_JDIR}/task2/cum-combined-asuser.txt")
C_LINES=$(wc -l < "${A_JDIR}/task2/cum-combined-asuser.txt")
echo "cum owner=${C_OWNER} lines=${C_LINES}"            | tee -a "$TASKLOG"

echo "═══ Part D: diff -u comparisons ═══"               | tee -a "$TASKLOG"
echo "-- right vs wrong (cannot-access lines) --"       | tee -a "$TASKLOG"
diff -u \
  <(grep 'cannot access' "${A_JDIR}/task2/right.log" | sort) \
  <(grep 'cannot access' "${A_JDIR}/task2/wrong.log" | sort) \
  | tee -a "$TASKLOG" || true
echo "-- posix vs ampersand (cannot-access lines) --"   | tee -a "$TASKLOG"
diff -u \
  <(grep 'cannot access' "${A_JDIR}/task1/posix-combined.txt" | sort) \
  <(grep 'cannot access' "${A_JDIR}/task1/ampersand-combined.txt" | sort) \
  | tee -a "$TASKLOG" || true

echo "exit was: $?"
```

### Journal write

```bash
LAB=lab-04c
TASK=task1
JDIR="/root/rhcsa_journal/${LAB}/${TASK}"
mkdir -p "$JDIR"
cp /tmp/lab04c/task1.txt "$JDIR/evidence.txt"

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
TOPIC:    Audit 04a combined-capture evidence and prove T04-A
COMMANDS: grep -c, wc -l, stat -c, diff -u
TRAPS:    T04-A audited; T44 deferred to Lab Closeout
NEXT:     task2 destroy-restore drill (T41) + live recapture
EOF

ls -la "$JDIR"
echo "exit was: $?"
```

> **STOP:** paste key `✅` lines before Task 2.

---

## Task 2 — Destroy-Restore Drill (T41) + Live Re-Verify

**Practice directory this task:** `/tmp/lab04c` (destroy/rebuild) with journal source from 04a.

### Warm-Up

```bash
ls -la /tmp/lab04a /tmp/lab04c 2>/dev/null             2>&1 | tee /tmp/lab04c/warmup2.txt
df -h /tmp | tail -1
findmnt /tmp 2>/dev/null || echo "/tmp not separately mounted"
sha256sum /root/rhcsa_journal/lab-04a/task2/cum-combined-asuser.txt
set -o pipefail
echo "Warm-up done by $(whoami) at $(date -Is)"
echo "exit was: $?"
```

### Main command block

```bash
TASKLOG=/tmp/lab04c/task2.txt
SRC=/root/rhcsa_journal/lab-04a/task2/cum-combined-asuser.txt

echo "═══ Part A: snapshot source ═══"                    2>&1 | tee "$TASKLOG"
SRC_LINES=$(wc -l < "$SRC")
SRC_HASH=$(sha256sum "$SRC" | awk '{print $1}')
echo "source lines=${SRC_LINES}"                          | tee -a "$TASKLOG"
echo "source sha256=${SRC_HASH}"                          | tee -a "$TASKLOG"

echo "═══ Part B: destroy sandboxes ═══"                  | tee -a "$TASKLOG"
rm -rf /tmp/lab04a /tmp/lab04c
if test ! -d /tmp/lab04a -a ! -d /tmp/lab04c; then
  echo "✅ destroy clean (both directories gone)"         | tee -a "$TASKLOG"
else
  echo "❌ destroy incomplete"                            | tee -a "$TASKLOG"
fi

echo "═══ Part C: restore combined log ═══"               | tee -a "$TASKLOG"
mkdir -p "${SANDBOX}" "${USER_HOME}"
chown -R "${USER}:${GROUP}" "${SANDBOX}"
cp "$SRC" "${USER_HOME}/cum-combined-restored.txt"
chown "${USER}:${GROUP}" "${USER_HOME}/cum-combined-restored.txt"
chmod 0664 "${USER_HOME}/cum-combined-restored.txt"
REST_HASH=$(sha256sum "${USER_HOME}/cum-combined-restored.txt" | awk '{print $1}')
echo "restored sha256=${REST_HASH}"                       | tee -a "$TASKLOG"
test "${REST_HASH}" = "${SRC_HASH}" \
  && echo "✅ restore hash matches source" \
  || echo "❌ restore hash mismatch" \
  | tee -a "$TASKLOG"

echo "═══ Part D: live verify capture as ${USER} ═══"     | tee -a "$TASKLOG"
sudo -u "${USER}" bash -c \
  'ls /lib64 /nonexistent > '"${USER_HOME}"'/live-verify.txt 2>&1'
LIVE_CA=$(grep -c 'cannot access' "${USER_HOME}/live-verify.txt" 2>/dev/null || echo 0)
LIVE_LN=$(wc -l < "${USER_HOME}/live-verify.txt")
echo "live lines=${LIVE_LN} cannot-access=${LIVE_CA}"     | tee -a "$TASKLOG"
test "${LIVE_CA}" -gt 0 \
  && echo "✅ live capture still works with > file 2>&1 under sudo -u" \
  || echo "❌ live capture missing stderr evidence" \
  | tee -a "$TASKLOG"

echo "═══ Part E: restored + live proof ═══"              | tee -a "$TASKLOG"
REST_LN=$(wc -l < "${USER_HOME}/cum-combined-restored.txt")
stat -c '%U:%G %a %n' "${USER_HOME}/cum-combined-restored.txt" | tee -a "$TASKLOG"
stat -c '%U:%G %a %n' "${USER_HOME}/live-verify.txt"           | tee -a "$TASKLOG"
echo "restored lines=${REST_LN}"                          | tee -a "$TASKLOG"
test "${REST_LN}" -gt 0 -a "${LIVE_LN}" -gt 0 \
  && echo "✅ restored artifact and live capture both verified post-wipe" \
  || echo "❌ restored/live verification incomplete" \
  | tee -a "$TASKLOG"

echo "exit was: $?"
```

### Journal write

```bash
LAB=lab-04c
TASK=task2
JDIR="/root/rhcsa_journal/${LAB}/${TASK}"
mkdir -p "$JDIR"
cp /tmp/lab04c/task2.txt "$JDIR/evidence.txt"
cp "${USER_HOME}/cum-combined-restored.txt" "$JDIR/cum-combined-restored.txt"
cp "${USER_HOME}/live-verify.txt" "$JDIR/live-verify.txt"
sha256sum "${USER_HOME}/cum-combined-restored.txt" "$SRC" > "$JDIR/sha256sums.txt"

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
TOPIC:    T41 destroy-restore + live recapture as verify user
COMMANDS: rm -rf, cp, sha256sum, wc -l, stat -c, sudo -u ${USER} bash -c 'ls /lib64 /nonexistent > file 2>&1'
TRAPS:    T41 rehearsed; T42 verbalize reboot reasoning before closeout
NEXT:     Lab Closeout Section 6
EOF

ls -la "$JDIR"
echo "exit was: $?"
```

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
    groupdel "${GROUP}" 2>/dev/null
fi

rm -rf "${SANDBOX}"

echo "── Lab 04c cleanup audit ──"
getent passwd "${USER}" >/dev/null && echo "❌ user remains" || echo "✅ user gone"
getent group  "${GROUP}" >/dev/null && echo "❌ group remains" || echo "✅ group gone"
test -d "${SANDBOX}" && echo "❌ sandbox remains" || echo "✅ sandbox gone"
test -d "${USER_HOME}" && echo "❌ home remains" || echo "✅ home gone"

set -e
echo "Cleanup complete by $(whoami) at $(date -Is)"
echo "exit was: $?"
```

---

## Lab 04c Checklist (2 tasks + closeout)

- [ ] Lab-Wide Setup complete (`labuser_04_verify` / `labgrp_04_verify`)
- [ ] Task 1 complete (four-way matrix + `grep -c`/`wc -l`/`stat`/`diff -u` evidence)
- [ ] Task 2 complete (destroy clean, restore hash match, live `sudo -u` combined capture proof)
- [ ] Lab Closeout complete (four cleanup `✅` lines)

---

## Related Labs

| Lab | Connection |
|---|---|
| **Lab 04a** — RHCSA combined capture | Source artifacts audited here |
| **Lab 04b** — Ansible combined capture | Optional evidence comparison |
| **Lab 02c** — stderr verify capstone | Structural pattern mirrored by this lab |

---

## Author

**Kelvin R. Tobias**  
[kelvinintech.com](https://kelvinintech.com) · [GitHub](https://github.com/kelvintechnical) · [LinkedIn](https://www.linkedin.com/in/kelvin-r-tobias-211949219)
