# Lab 27c: Safely Editing System Databases (Verify) - audit + destroy/restore

- **Series:** linux-ops-mastery - Text File Management
- **Trilogy:** `27a` (RHCSA) -> `27b` (Ansible) -> `27c` (Verify)
- **Prerequisite:** Labs 27a and 27b complete
- **Time Estimate:** 25-35 minutes
- **Tasks:** 2 (Task 1 = `getent` audit against expected state, Task 2 = destroy-restore drill from journal)
- **Practice Directory (rotation #27):** `/srv`
- **Sandbox (Tier B):** `/tmp/lab27c` with `USER=labuser_27_vipw`, `GROUP=labgrp_27_vipw`
- **Traps rehearsed this lab:** **T41** (skip restore drill) ; **T44** (leave orphaned user/group/home)

> **This lab's practice directory is: `/srv`**. Verification artifacts live in `/root/rhcsa_journal/lab-27c/`.

---

## Objective

Prove that account database state matches declarations from the trilogy, then prove you can recover cleanly after destructive removal by rebuilding from journaled expectations.

---

## Lab-Wide Setup - Tier B + journal anchors

```bash
sudo -i

export LAB_NUM=27
export LAB_SLUG=vipw
export SANDBOX=/tmp/lab27c
export GROUP=labgrp_${LAB_NUM}_${LAB_SLUG}
export USER=labuser_${LAB_NUM}_${LAB_SLUG}
export USER_HOME=${SANDBOX}/home_${USER}

mkdir -p "${SANDBOX}" "${USER_HOME}"
mkdir -p /root/rhcsa_journal/lab-27c/{task1,task2}
mkdir -p /root/rhcsa_journal/lab-27c/restore-plan
```

Create a small restore manifest once and reuse it in Task 2:

```bash
cat > /root/rhcsa_journal/lab-27c/restore-plan/expected.env <<'EOF'
GROUP=labgrp_27_vipw
USER=labuser_27_vipw
HOME=/tmp/lab27c/home_labuser_27_vipw
SHELL=/bin/bash
EOF
```

---

## Task 1 - Audit user/group state with `getent`

**Practice directory this task:** `/srv` (auditing account DB state only)

### Warm-Up

```bash
source /root/rhcsa_journal/lab-27c/restore-plan/expected.env
echo "Expect USER=${USER} GROUP=${GROUP}"
echo "Warm-up at $(date -Is)"
```

### Purpose

Validate that passwd/shadow and group/gshadow records all resolve and names match expected declarations.

### Main command block

```bash
set -o pipefail
source /root/rhcsa_journal/lab-27c/restore-plan/expected.env
TASKLOG=/root/rhcsa_journal/lab-27c/task1/op.txt

echo "== account state audit ==" | tee "${TASKLOG}"
getent passwd "${USER}"  | tee -a "${TASKLOG}"
getent shadow "${USER}"  | cut -d: -f1-2 | tee -a "${TASKLOG}"
getent group  "${GROUP}" | tee -a "${TASKLOG}"
getent gshadow "${GROUP}" | cut -d: -f1-2 | tee -a "${TASKLOG}"

pw_user=$(getent passwd "${USER}"  | cut -d: -f1)
sh_user=$(getent shadow "${USER}"  | cut -d: -f1)
gr_name=$(getent group  "${GROUP}" | cut -d: -f1)
gs_name=$(getent gshadow "${GROUP}" | cut -d: -f1)

test "${pw_user}" = "${sh_user}" && echo "PASS passwd-shadow aligned" | tee -a "${TASKLOG}"
test "${gr_name}" = "${gs_name}" && echo "PASS group-gshadow aligned" | tee -a "${TASKLOG}"

id "${USER}" | tee -a "${TASKLOG}"
echo "exit was: $?"
```

### PERSISTENCE CHECK

| What must exist | Verification |
|---|---|
| passwd entry | `getent passwd ${USER}` |
| shadow entry | `getent shadow ${USER}` |
| group entry | `getent group ${GROUP}` |
| gshadow entry | `getent gshadow ${GROUP}` |

### Journal write

```bash
LAB=lab-27c
TASK=task1
JDIR="/root/rhcsa_journal/${LAB}/${TASK}"
mkdir -p "${JDIR}"
cp /root/rhcsa_journal/lab-27c/task1/op.txt "${JDIR}/evidence.txt"

cat > "${JDIR}/done.txt" <<EOF
LAB:    ${LAB}
TASK:   ${TASK}
DATE:   $(date -Is)
STATUS: COMPLETE
EOF
```

---

## Task 2 - Destroy-restore drill (`userdel -r` then rebuild from journal)

**Practice directory this task:** `/srv` (restore actions update account DBs and sandbox home)

### Purpose

Rehearse incident recovery: intentionally remove the lab user and group, verify absence, then rebuild from recorded expectation data.

### Main command block

```bash
set -o pipefail
source /root/rhcsa_journal/lab-27c/restore-plan/expected.env
TASKLOG=/root/rhcsa_journal/lab-27c/task2/op.txt

echo "== destroy phase ==" | tee "${TASKLOG}"
getent passwd "${USER}" >/dev/null 2>&1 && userdel -r "${USER}" || true
getent group  "${GROUP}" >/dev/null 2>&1 && groupdel "${GROUP}" || true

getent passwd "${USER}" >/dev/null && echo "FAIL user still present" | tee -a "${TASKLOG}" || echo "PASS user removed" | tee -a "${TASKLOG}"
getent group  "${GROUP}" >/dev/null && echo "FAIL group still present" | tee -a "${TASKLOG}" || echo "PASS group removed" | tee -a "${TASKLOG}"

echo "== restore phase from journal ==" | tee -a "${TASKLOG}"
getent group "${GROUP}" >/dev/null || groupadd "${GROUP}"
getent passwd "${USER}" >/dev/null || useradd -d "${HOME}" -M -s "${SHELL}" -g "${GROUP}" "${USER}"
mkdir -p "${HOME}"
chown -R "${USER}:${GROUP}" "${HOME}"

getent passwd "${USER}"  | tee -a "${TASKLOG}"
getent shadow "${USER}"  | cut -d: -f1-2 | tee -a "${TASKLOG}"
getent group  "${GROUP}" | tee -a "${TASKLOG}"
getent gshadow "${GROUP}" | cut -d: -f1-2 | tee -a "${TASKLOG}"
id "${USER}" | tee -a "${TASKLOG}"
ls -ld "${HOME}" | tee -a "${TASKLOG}"

echo "exit was: $?"
```

### T41 Completion Gate

Do not mark Lab 27 complete without this destroy-restore drill. Passing Task 1 alone is incomplete verification.

### Journal write

```bash
LAB=lab-27c
TASK=task2
JDIR="/root/rhcsa_journal/${LAB}/${TASK}"
mkdir -p "${JDIR}"
cp /root/rhcsa_journal/lab-27c/task2/op.txt "${JDIR}/evidence.txt"
cp /root/rhcsa_journal/lab-27c/restore-plan/expected.env "${JDIR}/expected.env"

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
source /root/rhcsa_journal/lab-27c/restore-plan/expected.env

if getent passwd "${USER}" >/dev/null 2>&1; then
  userdel -r "${USER}" 2>/dev/null
fi
if getent group "${GROUP}" >/dev/null 2>&1; then
  groupdel "${GROUP}" 2>/dev/null
fi

rm -rf /tmp/lab27c

echo "-- Lab 27c cleanup audit --"
getent passwd "${USER}" >/dev/null && echo "FAIL user remains" || echo "PASS user gone"
getent group  "${GROUP}" >/dev/null && echo "FAIL group remains" || echo "PASS group gone"
test -d /tmp/lab27c && echo "FAIL sandbox remains" || echo "PASS sandbox gone"
test -d "${HOME}" && echo "FAIL home remains" || echo "PASS home gone"

set -e
echo "Cleanup complete at $(date -Is)"
```

---

## Lab 27c Checklist

- [ ] Task 1: full `getent` audit across passwd/shadow/group/gshadow
- [ ] Task 2: destroy (`userdel -r`) and restore from journal manifest
- [ ] Section 6 closeout: four PASS audit lines shown

---

## Related Labs

| Lab | Connection |
|---|---|
| Lab 27a | Lock contention and paired shadow edits |
| Lab 27b | Declarative user/group convergence with Ansible |

---

## Author

**Kelvin R. Tobias**
