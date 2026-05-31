# Lab 53c: Verifying ACL Removal — audit + destroy-restore

- **Series:** linux-ops-mastery — Permissions, ACLs, and Ownership
- **Trilogy:** `53a` (RHCSA) -> `53b` (Ansible) -> `53c` (Verify)
- **Topic:** Validate ACL removal with pre/post evidence and recovery drill
- **Prerequisite:** Labs 53a and 53b complete
- **Time Estimate:** 20-30 minutes
- **Tasks:** 2 (Task 1 audit pre/post ACL states, Task 2 destroy-restore drill)
- **Practice Directory:** `/media`
- **Sandbox (Tier B):** `/tmp/lab53c`, `USER=labuser_53_aclrm`, `GROUP=labgrp_53_aclrm`
- **Traps rehearsed this lab:** **T53-A** · **T53-B** · **T41** (destroy-restore required) · **T44** (orphan cleanup proof)

> Verification lab rule: trust neither shell output nor Ansible recap until `getfacl` evidence is captured and compared.

---

## LAB HEADER BLOCK

```bash
echo "ENV:   ${ENV:-DECLARE_ME}"
echo "OS:    $(cat /etc/redhat-release 2>/dev/null || grep PRETTY_NAME /etc/os-release)"
echo "TIME:  $(date -Is)"
echo "USER:  $(whoami)@$(hostname)"
echo "TRAPS: T53-A T53-B T41 T44"
echo "PRACTICE DIR: /media"
test -f /root/rhcsa_journal/lab-53a/task2/done.txt && echo "OK lab-53a evidence present"
test -f /root/rhcsa_journal/lab-53b/task2/done.txt && echo "OK lab-53b evidence present"
```

---

## Objective

Work from the auditor seat:

1. Capture ACL state before and after removals and store it in journal evidence.
2. Prove the ACL cleanup process is repeatable through a destroy-restore drill.

---

## Lab-Wide Setup (Tier B)

```bash
sudo -i

export SANDBOX=/tmp/lab53c
export GROUP=labgrp_53_aclrm
export USER=labuser_53_aclrm
export USER_HOME=${SANDBOX}/home_${USER}
export TARGET_FILE=${SANDBOX}/verify-acl.txt
export TARGET_DIR=${SANDBOX}/verify-dir
export JDIR=/root/rhcsa_journal/lab-53c

mkdir -p "${SANDBOX}" "${USER_HOME}" "${TARGET_DIR}" "${JDIR}/task1" "${JDIR}/task2"
getent group "${GROUP}" >/dev/null || groupadd "${GROUP}"
getent passwd "${USER}" >/dev/null || useradd -d "${USER_HOME}" -M -s /bin/bash -g "${GROUP}" "${USER}"
chown -R "${USER}:${GROUP}" "${SANDBOX}"

echo "verify fixture" > "${TARGET_FILE}"
chown "${USER}:${GROUP}" "${TARGET_FILE}"
chmod 640 "${TARGET_FILE}"

# Seed ACLs for audit and removal checks
setfacl -m u:${USER}:rwx,u:other:rw "${TARGET_FILE}"
setfacl -m u:${USER}:rwx "${TARGET_DIR}"
setfacl -m d:u:${USER}:rwx "${TARGET_DIR}"

getfacl "${TARGET_FILE}"
getfacl "${TARGET_DIR}"
```

---

## Task 1 - Audit pre/post ACL state in journal

### Purpose

Capture reproducible ACL evidence and prove exactly what changed.

### Main command block

```bash
TASKLOG=/tmp/lab53c/task1.txt

echo "== PRE-REMOVAL ACL ==" | tee "${TASKLOG}"
getfacl "${TARGET_FILE}" | tee -a "${TASKLOG}"
getfacl "${TARGET_DIR}"  | tee -a "${TASKLOG}"
getfacl "${TARGET_FILE}" > /tmp/lab53c/pre-file.acl
getfacl "${TARGET_DIR}"  > /tmp/lab53c/pre-dir.acl

# Removal actions under verification
setfacl -x u:other "${TARGET_FILE}"
setfacl -b "${TARGET_FILE}"
setfacl -k "${TARGET_DIR}"

echo "== POST-REMOVAL ACL ==" | tee -a "${TASKLOG}"
getfacl "${TARGET_FILE}" | tee -a "${TASKLOG}"
getfacl "${TARGET_DIR}"  | tee -a "${TASKLOG}"
getfacl "${TARGET_FILE}" > /tmp/lab53c/post-file.acl
getfacl "${TARGET_DIR}"  > /tmp/lab53c/post-dir.acl

echo "== DIFFS ==" | tee -a "${TASKLOG}"
diff -u /tmp/lab53c/pre-file.acl /tmp/lab53c/post-file.acl | tee -a "${TASKLOG}" || true
diff -u /tmp/lab53c/pre-dir.acl  /tmp/lab53c/post-dir.acl  | tee -a "${TASKLOG}" || true

echo "exit was: $?"
```

### Journal write

```bash
cp /tmp/lab53c/task1.txt      "${JDIR}/task1/evidence.txt"
cp /tmp/lab53c/pre-file.acl   "${JDIR}/task1/pre-file.acl"
cp /tmp/lab53c/post-file.acl  "${JDIR}/task1/post-file.acl"
cp /tmp/lab53c/pre-dir.acl    "${JDIR}/task1/pre-dir.acl"
cp /tmp/lab53c/post-dir.acl   "${JDIR}/task1/post-dir.acl"
cat > "${JDIR}/task1/done.txt" <<EOF
LAB: lab-53c
TASK: task1
DATE: $(date -Is)
STATUS: COMPLETE
EOF
```

---

## Task 2 - Destroy-restore drill (T41)

### Purpose

Prove you can tear down and recreate the ACL scenario from scratch, then verify cleanup consistency.

### Main command block

```bash
TASKLOG=/tmp/lab53c/task2.txt

echo "== DESTROY phase ==" | tee "${TASKLOG}"
rm -f "${TARGET_FILE}" | tee -a "${TASKLOG}"
rm -rf "${TARGET_DIR}" | tee -a "${TASKLOG}"
ls -la "${SANDBOX}" | tee -a "${TASKLOG}"

echo "== RESTORE phase ==" | tee -a "${TASKLOG}"
echo "restored fixture" > "${TARGET_FILE}"
mkdir -p "${TARGET_DIR}"
chown "${USER}:${GROUP}" "${TARGET_FILE}" "${TARGET_DIR}"
chmod 640 "${TARGET_FILE}"
setfacl -m u:${USER}:rwx,u:other:rw "${TARGET_FILE}"
setfacl -m u:${USER}:rwx "${TARGET_DIR}"
setfacl -m d:u:${USER}:rwx "${TARGET_DIR}"
getfacl "${TARGET_FILE}" | tee -a "${TASKLOG}"
getfacl "${TARGET_DIR}"  | tee -a "${TASKLOG}"

echo "== cleanup proof pass ==" | tee -a "${TASKLOG}"
setfacl -b "${TARGET_FILE}"
setfacl -k "${TARGET_DIR}"
getfacl "${TARGET_FILE}" | tee -a "${TASKLOG}"
getfacl "${TARGET_DIR}"  | tee -a "${TASKLOG}"

echo "exit was: $?"
```

### Journal write

```bash
cp /tmp/lab53c/task2.txt "${JDIR}/task2/evidence.txt"
cat > "${JDIR}/task2/done.txt" <<EOF
LAB: lab-53c
TASK: task2
DATE: $(date -Is)
STATUS: COMPLETE
EOF
```

---

## Lab Closeout - Section 6 Teardown

```bash
set +e

if getent passwd "${USER}" >/dev/null 2>&1; then
  userdel -r "${USER}" 2>/dev/null
fi
if getent group "${GROUP}" >/dev/null 2>&1; then
  groupdel "${GROUP}" 2>/dev/null
fi
rm -rf "${SANDBOX}"

echo "-- lab-53c cleanup audit --"
getent passwd "${USER}" >/dev/null && echo "FAIL user remains" || echo "OK user gone"
getent group  "${GROUP}" >/dev/null && echo "FAIL group remains" || echo "OK group gone"
test -d "${SANDBOX}" && echo "FAIL sandbox remains" || echo "OK sandbox gone"

set -e
```

> T44 pass condition: all closeout lines must show `OK`.

---

## Checklist

- [ ] Task 1 stored pre/post ACL snapshots and diffs in journal
- [ ] Task 1 verified `setfacl -x`, `-b`, and `-k` effects with `getfacl`
- [ ] Task 2 completed destroy-restore drill (T41)
- [ ] Section 6 closeout audit returned all `OK` (T44)

---

## Author

**Kelvin R. Tobias**
