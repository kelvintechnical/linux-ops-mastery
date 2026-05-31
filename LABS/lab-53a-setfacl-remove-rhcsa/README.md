# Lab 53a: Removing ACLs (RHCSA) — `setfacl -x`, `setfacl -b`, `setfacl -k`

- **Series:** linux-ops-mastery — Permissions, ACLs, and Ownership
- **Trilogy:** `53a` (RHCSA hand-typed) -> `53b` (Ansible) -> `53c` (Verify)
- **Topic:** Removing ACL entries safely without damaging base Unix permissions
- **Prerequisite:** Basic `chmod`/`chown`, and reading `getfacl` output
- **Time Estimate:** 25-35 minutes
- **Tasks:** 2 (ADHD format: Task 1 specific-entry removal, Task 2 full extended-ACL reset)
- **Practice Directory:** `/media`
- **Sandbox (Tier B):** `/tmp/lab53a`, `USER=labuser_53_aclrm`, `GROUP=labgrp_53_aclrm`
- **Traps rehearsed this lab:** **T53-A** (`-x` removes one ACL entry, but mask and other extended entries can remain) · **T41** (skipping destroy-restore) · **T44** (orphan user/group cleanup miss)

> This lab's practice directory is `/media`. We still stage user/group and transient files under `/tmp/lab53a` for safe teardown.

---

## LAB HEADER BLOCK

```bash
echo "ENV:   ${ENV:-DECLARE_ME}"
echo "OS:    $(cat /etc/redhat-release 2>/dev/null || grep PRETTY_NAME /etc/os-release)"
echo "TIME:  $(date -Is)"
echo "USER:  $(whoami)@$(hostname)"
echo "TRAPS: T53-A T41 T44"
echo "PRACTICE DIR: /media"
ls -ld /media
```

> STOP - paste header output before setup.

---

## Objective

Build a precise ACL-removal reflex:

1. Remove one targeted ACL entry with `setfacl -x`.
2. Recognize why `+` can still appear in `ls -l` after partial ACL cleanup.
3. Remove all extended ACLs with `setfacl -b` while preserving base owner/group/other mode bits.
4. Confirm final state with `getfacl` after each removal step.

---

## Concept: `-x` vs `-b` vs `-k`

- `setfacl -x u:user FILE` removes only the named ACL entry.
- `setfacl -b FILE` removes all extended ACL entries (named users, named groups, mask, and default ACLs), leaving base mode permissions.
- `setfacl -k DIR` removes only default ACL entries from a directory; explicit access ACL entries remain.

This distinction is the center of ACL cleanup work in RHCSA and production triage.

---

## Lab-Wide Setup (Tier B)

```bash
sudo -i

export LAB_NUM=53
export LAB_SLUG=aclrm
export SANDBOX=/tmp/lab53a
export GROUP=labgrp_53_aclrm
export USER=labuser_53_aclrm
export USER_HOME=${SANDBOX}/home_${USER}
export TARGET_FILE=${SANDBOX}/acl-remove.txt

mkdir -p "${SANDBOX}" "${USER_HOME}" /root/rhcsa_journal/lab-53a/task1 /root/rhcsa_journal/lab-53a/task2
getent group "${GROUP}" >/dev/null || groupadd "${GROUP}"
getent passwd "${USER}" >/dev/null || useradd -d "${USER_HOME}" -M -s /bin/bash -g "${GROUP}" "${USER}"
chown -R "${USER}:${GROUP}" "${SANDBOX}"

echo "acl baseline" > "${TARGET_FILE}"
chown "${USER}:${GROUP}" "${TARGET_FILE}"
chmod 640 "${TARGET_FILE}"

id "${USER}"
ls -ld "${SANDBOX}" "${USER_HOME}"
ls -l "${TARGET_FILE}"
```

> STOP - paste `id`, both `ls -ld` lines, and `ls -l` for `${TARGET_FILE}` before Task 1.

---

## Task 1 - Remove one ACL entry with `setfacl -x`

### Purpose

Practice targeted removal and verify that partial cleanup can still leave extended ACL markers in place.

### Main command block

```bash
TASKLOG=/tmp/lab53a/task1.txt

# Add two named user ACL entries exactly as requested
setfacl -m u:${USER}:rwx,u:other:rw "${TARGET_FILE}"

echo "== after setfacl -m ==" | tee "${TASKLOG}"
getfacl "${TARGET_FILE}" | tee -a "${TASKLOG}"
ls -l "${TARGET_FILE}" | tee -a "${TASKLOG}"

# Remove only one named entry
setfacl -x u:other "${TARGET_FILE}"

echo "== after setfacl -x u:other ==" | tee -a "${TASKLOG}"
getfacl "${TARGET_FILE}" | tee -a "${TASKLOG}"
ls -l "${TARGET_FILE}" | tee -a "${TASKLOG}"

echo "exit was: $?"
```

### Expected verification

- `getfacl` still shows the named entry for `${USER}`.
- `getfacl` no longer shows `user:other:rw`.
- `ls -l` still shows `+` on the file because extended ACL state can still exist after removing only one entry (**T53-A**).

### Journal write

```bash
JDIR=/root/rhcsa_journal/lab-53a/task1
mkdir -p "${JDIR}"
cp /tmp/lab53a/task1.txt "${JDIR}/evidence.txt"
cat > "${JDIR}/done.txt" <<EOF
LAB: lab-53a
TASK: task1
DATE: $(date -Is)
STATUS: COMPLETE
EOF
```

---

## Task 2 - Remove all extended ACLs with `setfacl -b`

### Purpose

Complete ACL cleanup and prove base permissions remain while extended ACL metadata disappears.

### Main command block

```bash
TASKLOG=/tmp/lab53a/task2.txt

echo "== before setfacl -b ==" | tee "${TASKLOG}"
getfacl "${TARGET_FILE}" | tee -a "${TASKLOG}"
ls -l "${TARGET_FILE}" | tee -a "${TASKLOG}"

setfacl -b "${TARGET_FILE}"

echo "== after setfacl -b ==" | tee -a "${TASKLOG}"
getfacl "${TARGET_FILE}" | tee -a "${TASKLOG}"
ls -l "${TARGET_FILE}" | tee -a "${TASKLOG}"
stat -c '%U:%G %a %n' "${TARGET_FILE}" | tee -a "${TASKLOG}"

echo "exit was: $?"
```

### Expected verification

- `getfacl` shows only base entries (`user::`, `group::`, `other::`).
- `ls -l` no longer shows `+`.
- Owner/group/mode remain intact (base perms preserved).

### Journal write

```bash
JDIR=/root/rhcsa_journal/lab-53a/task2
mkdir -p "${JDIR}"
cp /tmp/lab53a/task2.txt "${JDIR}/evidence.txt"
cat > "${JDIR}/done.txt" <<EOF
LAB: lab-53a
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

echo "-- lab-53a cleanup audit --"
getent passwd "${USER}" >/dev/null && echo "FAIL user remains" || echo "OK user gone"
getent group  "${GROUP}" >/dev/null && echo "FAIL group remains" || echo "OK group gone"
test -d "${SANDBOX}" && echo "FAIL sandbox remains" || echo "OK sandbox gone"

set -e
```

> T44 guard: do not mark complete until all three audit lines show `OK`.

---

## Checklist

- [ ] Task 1: `setfacl -x u:other` removed only that entry, `${USER}` ACL remained
- [ ] Task 1: `ls -l` still showed `+` after partial removal (T53-A)
- [ ] Task 2: `setfacl -b` removed all extended ACL entries
- [ ] Task 2: `getfacl` showed base perms only, and `ls -l` had no `+`
- [ ] Section 6 closeout audit returned all `OK`

---

## Author

**Kelvin R. Tobias**
