# Lab 27a: Safely Editing System Databases (RHCSA) - `vipw`, `vipw -s`, `vigr`, `vigr -s`

- **Series:** linux-ops-mastery - Text File Management
- **Trilogy:** `27a` (RHCSA) -> `27b` (Ansible) -> `27c` (Verify)
- **Prerequisite:** Labs 26 and earlier complete
- **Time Estimate:** 35-45 minutes
- **Tasks:** 2 (Task 1 = prove `vipw` lock behavior with concurrent edit attempt, Task 2 = keep passwd/shadow + group/gshadow synchronized)
- **Practice Directory (rotation #27):** `/srv`
- **Sandbox (Tier B):** `/tmp/lab27a` with `USER=labuser_27_vipw`, `GROUP=labgrp_27_vipw`
- **Traps rehearsed this lab:** **T27-A** (editing `/etc/passwd` directly bypasses lock and risks concurrent corruption) ; **T27-B** (forgetting `-s` updates passwd/group but leaves shadow/gshadow out of sync) ; **T41** ; **T44**

> **This lab's practice directory is: `/srv`**. The sandbox for destructive practice remains under `/tmp/lab27a`.

---

## LAB HEADER BLOCK

```bash
echo "ENV:   ${ENV:-DECLARE_ME}"
echo "OS:    $(cat /etc/redhat-release 2>/dev/null || grep PRETTY_NAME /etc/os-release)"
echo "TIME:  $(date -Is)"
echo "USER:  $(whoami)@$(hostname)"
echo "TRAPS: T27-A T27-B T41 T44"
echo "DIR:   /srv"
ls -ld /srv
echo "exit was: $?"
```

> **STOP - paste header output before running setup.**

---

## Objective

Safely edit account databases with lock-aware tools. By the end of this lab you can prove `vipw`/`vigr` locking behavior under contention and you can update both public and shadow databases in matched pairs so account metadata stays consistent.

---

## Concept: Why `vipw`/`vigr` exist

Direct edits to `/etc/passwd`, `/etc/shadow`, `/etc/group`, and `/etc/gshadow` can race with other admin processes. `vipw` and `vigr` coordinate locking and atomic replacement so writes are serialized.

| Database | Public file | Protected file | Correct editor |
|---|---|---|---|
| Users | `/etc/passwd` | `/etc/shadow` | `vipw` + `vipw -s` |
| Groups | `/etc/group` | `/etc/gshadow` | `vigr` + `vigr -s` |

**Rule:** if you changed passwd/group identity data, validate shadow/gshadow alignment in the same change window.

---

## Lab-Wide Setup - Tier B Sandbox Stack

```bash
sudo -i

export LAB_NUM=27
export LAB_SLUG=vipw
export SANDBOX=/tmp/lab27a
export GROUP=labgrp_${LAB_NUM}_${LAB_SLUG}
export USER=labuser_${LAB_NUM}_${LAB_SLUG}
export USER_HOME=${SANDBOX}/home_${USER}

mkdir -p "${SANDBOX}" "${USER_HOME}"
mkdir -p /root/rhcsa_journal/lab-27a/task1
mkdir -p /root/rhcsa_journal/lab-27a/task2

getent group  "${GROUP}" >/dev/null || groupadd "${GROUP}"
getent passwd "${USER}"  >/dev/null || useradd -d "${USER_HOME}" -M -s /bin/bash -g "${GROUP}" "${USER}"
chown -R "${USER}:${GROUP}" "${SANDBOX}"

id "${USER}"
getent passwd "${USER}"
getent group "${GROUP}"
echo "exit was: $?"
```

---

## Task 1 - Prove `vipw` lock behavior with concurrent edit attempt

**Practice directory this task:** `/srv` (journal artifacts under `/root/rhcsa_journal/lab-27a/task1`)

### Warm-Up

```bash
command -v vipw vigr ed
ls -l /etc/passwd /etc/shadow /etc/group /etc/gshadow
echo "Warm-up at $(date -Is)"
```

### Purpose

Hold a `vipw` session open using `EDITOR=ed` and, while lock is held, attempt a second `vipw` invocation. Capture the refusal message to prove file locking is active.

### Main command block

```bash
set -o pipefail
TASKLOG=/root/rhcsa_journal/lab-27a/task1/op.txt
LOCK_HOLD=/tmp/lab27a/hold-vipw.ed
LOCK_TRY=/tmp/lab27a/try-vipw.ed

# Script 1: keep editor open briefly so lock remains held.
cat > "${LOCK_HOLD}" <<'EOF'
1p
,p
!sleep 12
q
EOF

# Script 2: minimal open/quit for second attempt.
cat > "${LOCK_TRY}" <<'EOF'
q
EOF

echo "== start first vipw (holds lock) ==" | tee "${TASKLOG}"
( EDITOR="ed -s ${LOCK_HOLD}" vipw ) >/tmp/lab27a/vipw-first.out 2>&1 &
PID1=$!
sleep 2

echo "== second vipw should fail/complain about lock ==" | tee -a "${TASKLOG}"
( EDITOR="ed -s ${LOCK_TRY}" vipw ) >/tmp/lab27a/vipw-second.out 2>&1 || true

wait "${PID1}" || true

echo "--- first output ---"  | tee -a "${TASKLOG}"
cat /tmp/lab27a/vipw-first.out  | tee -a "${TASKLOG}"
echo "--- second output ---" | tee -a "${TASKLOG}"
cat /tmp/lab27a/vipw-second.out | tee -a "${TASKLOG}"

echo "exit was: $?"
```

### Expected output (excerpt)

```text
== second vipw should fail/complain about lock ==
vipw: /etc/passwd is busy; try again later
```

Distribution phrasing differs, but the second invocation must not silently proceed while the first holds the lock.

### T27-A Proof

```bash
echo "NEVER do this in production:" | tee -a "${TASKLOG}"
echo "echo '#bad-edit' >> /etc/passwd" | tee -a "${TASKLOG}"
echo "Reason: bypasses vipw lock discipline and can race concurrent writes." | tee -a "${TASKLOG}"
```

### Journal write

```bash
LAB=lab-27a
TASK=task1
JDIR="/root/rhcsa_journal/${LAB}/${TASK}"
mkdir -p "${JDIR}"
cp "${TASKLOG}" "${JDIR}/evidence.txt"

cat > "${JDIR}/done.txt" <<EOF
LAB:    ${LAB}
TASK:   ${TASK}
DATE:   $(date -Is)
STATUS: COMPLETE
EOF
```

> **STOP - paste the second `vipw` output line proving lock contention before Task 2.**

---

## Task 2 - Use `vipw -s` and `vigr -s` to keep shadow files aligned

**Practice directory this task:** `/srv` (edits are made via lock-aware editors on system databases)

### Warm-Up

```bash
getent passwd "${USER}"
getent shadow "${USER}" | cut -d: -f1-2
getent group "${GROUP}"
getent gshadow "${GROUP}" | cut -d: -f1-2
echo "Warm-up at $(date -Is)"
```

### Purpose

Practice paired editing discipline: user metadata changes must be mirrored in shadow metadata, and group metadata changes must be mirrored in gshadow metadata. This drills out-of-sync prevention (T27-B).

### Main command block

```bash
set -o pipefail
TASKLOG=/root/rhcsa_journal/lab-27a/task2/op.txt

echo "== baseline snapshots ==" | tee "${TASKLOG}"
cp -a /etc/passwd  /tmp/lab27a/passwd.pre
cp -a /etc/shadow  /tmp/lab27a/shadow.pre
cp -a /etc/group   /tmp/lab27a/group.pre
cp -a /etc/gshadow /tmp/lab27a/gshadow.pre

echo "Open editors now (manual, lock-aware):" | tee -a "${TASKLOG}"
echo "1) vipw      # edit ${USER} passwd metadata only if required" | tee -a "${TASKLOG}"
echo "2) vipw -s   # validate/update ${USER} shadow row pairing" | tee -a "${TASKLOG}"
echo "3) vigr      # edit ${GROUP} group metadata only if required" | tee -a "${TASKLOG}"
echo "4) vigr -s   # validate/update ${GROUP} gshadow row pairing" | tee -a "${TASKLOG}"

echo "== post-edit alignment checks ==" | tee -a "${TASKLOG}"
getent passwd "${USER}"  | tee -a "${TASKLOG}"
getent shadow "${USER}"  | cut -d: -f1,3,4,5,6,7,8,9 | tee -a "${TASKLOG}"
getent group  "${GROUP}" | tee -a "${TASKLOG}"
getent gshadow "${GROUP}" | cut -d: -f1-3 | tee -a "${TASKLOG}"

pw_user=$(getent passwd "${USER}" | cut -d: -f1)
sh_user=$(getent shadow "${USER}" | cut -d: -f1)
gr_name=$(getent group "${GROUP}" | cut -d: -f1)
gs_name=$(getent gshadow "${GROUP}" | cut -d: -f1)

test "${pw_user}" = "${sh_user}" && echo "PASS: passwd/shadow name match" | tee -a "${TASKLOG}"
test "${gr_name}" = "${gs_name}" && echo "PASS: group/gshadow name match" | tee -a "${TASKLOG}"

echo "exit was: $?"
```

### T27-B Trap Reminder

If you edit only `/etc/passwd` or `/etc/group` and skip `-s`, shadow databases can drift. Always run the paired `-s` editor and re-check with `getent`.

### PERSISTENCE CHECK

| Check | Command |
|---|---|
| user row still resolves | `getent passwd ${USER}` |
| shadow row resolves | `getent shadow ${USER}` |
| group row resolves | `getent group ${GROUP}` |
| gshadow row resolves | `getent gshadow ${GROUP}` |

### Journal write

```bash
LAB=lab-27a
TASK=task2
JDIR="/root/rhcsa_journal/${LAB}/${TASK}"
mkdir -p "${JDIR}"
cp /root/rhcsa_journal/lab-27a/task2/op.txt "${JDIR}/evidence.txt"

cat > "${JDIR}/done.txt" <<EOF
LAB:    ${LAB}
TASK:   ${TASK}
DATE:   $(date -Is)
STATUS: COMPLETE
EOF
```

---

## Lab Closeout - Bulletproof Teardown (Section 6)

```bash
set +e

if getent passwd "${USER}" >/dev/null 2>&1; then
  userdel -r "${USER}" 2>/dev/null
fi
if getent group "${GROUP}" >/dev/null 2>&1; then
  groupdel "${GROUP}" 2>/dev/null
fi

rm -rf "${SANDBOX}"

echo "-- Lab 27a cleanup audit --"
getent passwd "${USER}" >/dev/null && echo "FAIL user remains" || echo "PASS user gone"
getent group  "${GROUP}" >/dev/null && echo "FAIL group remains" || echo "PASS group gone"
test -d "${SANDBOX}" && echo "FAIL sandbox remains" || echo "PASS sandbox gone"
test -d "${USER_HOME}" && echo "FAIL home remains" || echo "PASS home gone"

set -e
echo "Cleanup complete at $(date -Is)"
```

---

## Lab 27a Checklist

- [ ] Task 1 completed with concurrent `vipw` lock contention evidence
- [ ] Task 2 completed with passwd/shadow and group/gshadow alignment checks
- [ ] Section 6 closeout run with four PASS audit lines

---

## Related Labs

| Lab | Connection |
|---|---|
| Lab 27b | Converts this workflow to idempotent Ansible (`user`/`group`) |
| Lab 27c | Auditor seat + destroy/restore drill using journal |

---

## Author

**Kelvin R. Tobias**
