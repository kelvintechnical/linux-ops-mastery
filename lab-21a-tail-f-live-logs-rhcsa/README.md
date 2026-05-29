# Lab 21a: Monitoring Live Log Files (RHCSA) — `tail -f`, `tail -F`, `tail -n`, `tail --pid`, `journalctl -f`, `less +F`

- **Series:** linux-ops-mastery — Logging, Troubleshooting, and Real-Time Observability
- **Trilogy:** `21a` (RHCSA hand-typed) → [`21b`](../lab-21b-tail-f-live-logs-ansible/) (Ansible automation) → `21c` (Verify capstone — audit + destroy-restore)
- **Career arcs covered:** RHCSA EX200 (follow logs while reproducing failures), RHCE EX294 (automation-safe tail capture), SRE (watch incidents live), DevOps (pipeline troubleshooting), AI/MLOps (follow worker logs during runs)
- **Prerequisite:** Labs 01a/01c (stdout + verify), Lab 03a/03c (pipes + pipefail + verify)
- **Time Estimate:** 30–40 minutes
- **Tasks:** 2 (Task 1 = controlled live follow with timeout and `--pid`; Task 2 = trap-proof `tail -f` vs `tail -F` during rotate)
- **Practice Directory (rotation #21):** `/boot` (read-only context target)
- **Sandbox (Tier B per Section 1.5):** `/tmp/lab21a` with `USER=labuser_21_livelog`, `GROUP=labgrp_21_livelog`, `USER_HOME=/tmp/lab21a/home_labuser_21_livelog`
- **Traps rehearsed this lab:** **T21-A** (`tail -f` sticks to old inode after rotate; `tail -F` tracks filename) · **T21-B** (forgetting `--pid` leaves orphan follower) · **T41** (destroy-restore drill deferred to 21c) · **T44** (closeout audit required)

> **This lab's practice directory is: `/boot`** — we inspect it for rotation-context discipline while all writes happen in `/tmp/lab21a` and `/root/rhcsa_journal/lab-21a/`.

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
echo "⚠️  TRAP REMINDERS THIS LAB: T21-A T21-B T41 T44"
echo "📁  PRACTICE DIR: /boot"
echo ""
echo "💡 /boot context (read-only rotation reference):"
ls -ld /boot
ls /boot 2>/dev/null | head -n 5
echo "Shell version: $BASH_VERSION"
```

> **STOP — paste header output before setup.**

---

## Objective

Build reflexes for following live logs safely and predictably:

1. Use bounded followers (`timeout`, `tail --pid`) so monitors self-stop.
2. Distinguish `tail -f` from `tail -F` under log rotation.
3. Capture deterministic evidence with `tail -n` + `journalctl -f`.
4. Recognize and avoid orphan-monitor and rotated-file traps.

---

## Concept: Follow by Inode vs Follow by Name

`tail -f FILE` follows the current file descriptor. If FILE is rotated (renamed) and a new file is created with the same name, `-f` keeps reading the old inode.

`tail -F FILE` is shorthand for `--follow=name --retry` and reopens by filename, so it survives rotate/create.

```text
rotate event:
  /tmp/lab21a/live.log  --mv-->  /tmp/lab21a/live.log.1
  new empty file created at /tmp/lab21a/live.log

tail -f old FD   -> still reading live.log.1
tail -F by name  -> switches to new live.log
```

`tail --pid PID -f FILE` exits when PID exits. This is the clean way to bind a log follower to the producer process and avoid T21-B.

---

## Reference Quick Card

| Command | What it does |
|---|---|
| `tail -n 20 FILE` | Print last 20 lines, then exit |
| `tail -f FILE` | Follow appended data on current file descriptor |
| `tail -F FILE` | Follow by filename; survive rename/recreate |
| `tail --pid=$PID -f FILE` | Follow until watched process exits |
| `timeout 5 tail -f FILE` | Hard-stop follower at 5 seconds |
| `journalctl -f` | Follow systemd journal in real time |
| `less +F FILE` | Follow mode in pager; Ctrl+C to stop follow, `q` to quit |

---

## Lab-Wide Setup — Tier B Sandbox Stack (Section 1.5)

```bash
sudo -i

export LAB_NUM=21
export LAB_SLUG=livelog
export SANDBOX=/tmp/lab21a
export GROUP=labgrp_${LAB_NUM}_${LAB_SLUG}
export USER=labuser_${LAB_NUM}_${LAB_SLUG}
export USER_HOME=${SANDBOX}/home_${USER}

mkdir -p "${SANDBOX}" "${USER_HOME}" /root/rhcsa_journal/lab-21a/task1 /root/rhcsa_journal/lab-21a/task2
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

> **STOP — paste `id`, `ls -ld`, and both `getent` lines before Task 1.**

---

## Task 1 — Live follow `/var/log/messages` with timeout + `--pid`

**Practice directory this task:** `/boot` (context) and `/tmp/lab21a` (capture files).

### Warm-Up

```bash
ls -ld /boot                                           2>&1 | tee /tmp/lab21a/warmup.txt
tail -n 3 /var/log/messages                            2>&1 | tee -a /tmp/lab21a/warmup.txt
logger "lab21a warmup logger line $(date -Is)"
journalctl -n 3 --no-pager                             2>&1 | tee -a /tmp/lab21a/warmup.txt
echo "Warm-up done by $(whoami) at $(date -Is)"
echo "exit was: $?"
```

### Purpose

Capture deterministic live evidence from `/var/log/messages` without leaving background followers behind. Rehearse both bounded strategies:

- `timeout 5 tail -f`
- `tail --pid=<producer_pid> -f`

### Main command block

```bash
TASKLOG=/tmp/lab21a/task1.txt
LIVE=/tmp/lab21a/messages-live-capture.txt

echo "═══ Part A: bounded capture with timeout 5s + logger events ═══" 2>&1 | tee "${TASKLOG}"
(
  sleep 1; logger "lab21a-task1 event-1 $(date -Is)"
  sleep 1; logger "lab21a-task1 event-2 $(date -Is)"
  sleep 1; logger "lab21a-task1 event-3 $(date -Is)"
) &
GEN_PID=$!

timeout 5 tail -n 0 -f /var/log/messages | tee "${LIVE}"
wait "${GEN_PID}"

echo "captured lines:" | tee -a "${TASKLOG}"
wc -l "${LIVE}" | tee -a "${TASKLOG}"
grep -c 'lab21a-task1 event-' "${LIVE}" | tee -a "${TASKLOG}"

echo "═══ Part B: --pid demo (auto-exit on producer end) ═══" | tee -a "${TASKLOG}"
sudo -u "${USER}" bash -c '
  LOG=/tmp/lab21a/home_labuser_21_livelog/user-producer.log
  (
    echo "start $(date -Is)" >> "$LOG"
    sleep 1
    echo "middle $(date -Is)" >> "$LOG"
    sleep 1
    echo "end $(date -Is)" >> "$LOG"
  ) &
  P=$!
  tail --pid="$P" -n 0 -f "$LOG" > /tmp/lab21a/home_labuser_21_livelog/user-producer-follow.txt
  wait "$P"
'

stat -c '%U:%G %a %n' "${USER_HOME}/user-producer.log" "${USER_HOME}/user-producer-follow.txt" | tee -a "${TASKLOG}"
wc -l "${USER_HOME}/user-producer-follow.txt" | tee -a "${TASKLOG}"

echo "═══ Part C: journalctl -f quick bounded run ═══" | tee -a "${TASKLOG}"
( sleep 1; logger "lab21a-task1 journal-follow $(date -Is)" ) &
timeout 4 journalctl -f -n 0 --no-pager | tee /tmp/lab21a/journal-follow.txt
grep -c 'lab21a-task1 journal-follow' /tmp/lab21a/journal-follow.txt | tee -a "${TASKLOG}"

echo "exit was: $?"
```

### Expected output

```text
captured lines:
3 /tmp/lab21a/messages-live-capture.txt
3
labuser_21_livelog:labgrp_21_livelog 644 /tmp/lab21a/home_labuser_21_livelog/user-producer.log
labuser_21_livelog:labgrp_21_livelog 644 /tmp/lab21a/home_labuser_21_livelog/user-producer-follow.txt
3 /tmp/lab21a/home_labuser_21_livelog/user-producer-follow.txt
1
```

### Journal write

```bash
LAB=lab-21a
TASK=task1
JDIR="/root/rhcsa_journal/${LAB}/${TASK}"
mkdir -p "$JDIR"
cp /tmp/lab21a/task1.txt                         "$JDIR/evidence.txt"
cp /tmp/lab21a/messages-live-capture.txt         "$JDIR/messages-live-capture.txt"
cp /tmp/lab21a/journal-follow.txt                "$JDIR/journal-follow.txt"
cp "${USER_HOME}/user-producer-follow.txt"       "$JDIR/user-producer-follow.txt"

cat > "$JDIR/done.txt" <<EOF
LAB:    ${LAB}
TASK:   ${TASK}
DATE:   $(date -Is)
USER:   $(whoami)@$(hostname)
STATUS: COMPLETE
EOF

echo "exit was: $?"
```

---

## Task 2 — `tail -f` vs `tail -F` after rotate (T21-A)

**Practice directory this task:** `/boot` (context) and `/tmp/lab21a` (rotation simulation).

### Warm-Up

```bash
ls -ld /boot                                         2>&1 | tee /tmp/lab21a/warmup2.txt
echo "seed0" > /tmp/lab21a/rotate.log
tail -n 1 /tmp/lab21a/rotate.log                     2>&1 | tee -a /tmp/lab21a/warmup2.txt
echo "exit was: $?"
```

### Purpose

Prove trap T21-A with an explicit rotate event (`mv` + create new file), then show `-F` is the correct operator for long-running filename-based log monitoring.

### Main command block

```bash
TASKLOG=/tmp/lab21a/task2.txt
ROT=/tmp/lab21a/rotate.log

echo "seed-before" > "${ROT}"

echo "═══ Part A: tail -f trap demo ═══" 2>&1 | tee "${TASKLOG}"
timeout 7 bash -c '
  tail -n 0 -f /tmp/lab21a/rotate.log > /tmp/lab21a/out-f.txt &
  TP=$!
  sleep 1
  echo "before-rotate-1" >> /tmp/lab21a/rotate.log
  sleep 1
  mv /tmp/lab21a/rotate.log /tmp/lab21a/rotate.log.1
  : > /tmp/lab21a/rotate.log
  echo "after-rotate-newfile-1" >> /tmp/lab21a/rotate.log
  sleep 2
  kill $TP 2>/dev/null || true
'

echo "tail -f output:" | tee -a "${TASKLOG}"
cat /tmp/lab21a/out-f.txt | tee -a "${TASKLOG}"
grep -c "after-rotate-newfile-1" /tmp/lab21a/out-f.txt | tee -a "${TASKLOG}"

echo "═══ Part B: tail -F correct behavior ═══" | tee -a "${TASKLOG}"
echo "seed2" > "${ROT}"
timeout 7 bash -c '
  tail -n 0 -F /tmp/lab21a/rotate.log > /tmp/lab21a/out-F.txt &
  TP=$!
  sleep 1
  echo "before-rotate-2" >> /tmp/lab21a/rotate.log
  sleep 1
  mv /tmp/lab21a/rotate.log /tmp/lab21a/rotate.log.1
  : > /tmp/lab21a/rotate.log
  echo "after-rotate-newfile-2" >> /tmp/lab21a/rotate.log
  sleep 2
  kill $TP 2>/dev/null || true
'

echo "tail -F output:" | tee -a "${TASKLOG}"
cat /tmp/lab21a/out-F.txt | tee -a "${TASKLOG}"
grep -c "after-rotate-newfile-2" /tmp/lab21a/out-F.txt | tee -a "${TASKLOG}"

echo "exit was: $?"
```

### Trap callout

- **T21-A hit:** `tail -f` often misses `after-rotate-newfile-*` because it stayed on old inode.
- **T21-A avoided:** `tail -F` includes post-rotate line from new file path.
- **T21-B avoided:** bounded monitoring used (`timeout`, explicit kill, and Task 1 `--pid`).

### Journal write

```bash
LAB=lab-21a
TASK=task2
JDIR="/root/rhcsa_journal/${LAB}/${TASK}"
mkdir -p "$JDIR"
cp /tmp/lab21a/task2.txt   "$JDIR/evidence.txt"
cp /tmp/lab21a/out-f.txt   "$JDIR/out-f.txt"
cp /tmp/lab21a/out-F.txt   "$JDIR/out-F.txt"

cat > "$JDIR/done.txt" <<EOF
LAB:    ${LAB}
TASK:   ${TASK}
DATE:   $(date -Is)
USER:   $(whoami)@$(hostname)
STATUS: COMPLETE
EOF

echo "exit was: $?"
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

echo "── Lab 21a cleanup audit ──"
getent passwd "${USER}" >/dev/null && echo "❌ user remains" || echo "✅ user gone"
getent group  "${GROUP}" >/dev/null && echo "❌ group remains" || echo "✅ group gone"
test -d "${SANDBOX}" && echo "❌ sandbox remains" || echo "✅ sandbox gone"
test -d "${USER_HOME}" && echo "❌ home remains" || echo "✅ home gone"

set -e
echo "Cleanup complete at $(date -Is)"
echo "exit was: $?"
```

---

## Lab 21a Checklist (2 tasks + closeout)

- [ ] Setup: Tier B sandbox + user/group created (`labuser_21_livelog`, `labgrp_21_livelog`)
- [ ] Task 1: `timeout 5 tail -n0 -f /var/log/messages` capture includes logger events; `tail --pid` demo exits automatically
- [ ] Task 2: `tail -f` vs `tail -F` rotate proof captured in `out-f.txt` and `out-F.txt`
- [ ] Closeout: four `✅` audit lines

---

## Related Labs

| Lab | Connection |
|---|---|
| **Lab 21b** — Live Logs with Ansible | Automates bounded followers and rotate-safe behavior |
| **Lab 21c** — Live Logs Verify | Audits captures, destroy-restore, and rerun under verify user |
| Lab 03a / 03c | Pipe and verify patterns reused for evidence capture |

---

## Author

**Kelvin R. Tobias**  
[kelvinintech.com](https://kelvinintech.com) · [GitHub](https://github.com/kelvintechnical) · [LinkedIn](https://www.linkedin.com/in/kelvin-r-tobias-211949219)
