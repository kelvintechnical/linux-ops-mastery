# Lab 51c: Verifying Default Directory ACL Inheritance (Capstone) — Audit + Destroy-Restore Drill

- **Series:** linux-ops-mastery — ACLs and Permission Control
- **Trilogy:** [`51a`](../lab-51a-default-acl-inherit-rhcsa/) (RHCSA) -> [`51b`](../lab-51b-default-acl-inherit-ansible/) (Ansible) -> **`51c`** (Verify capstone)
- **Time Estimate:** 25-35 minutes
- **Tasks:** 2
- **Practice Directory (rotation #51):** `/sys` (inspection context), writes happen in sandbox
- **Sandbox (Tier B):** `/tmp/lab51c` with `USER=labuser_51_dacl`, `GROUP=labgrp_51_dacl`
- **Traps rehearsed this lab:** **T51-A** · **T51-B** · **T41** · **T44**

> **Topic focus:** audit `default:` ACL evidence in journal artifacts, then run a destroy-restore drill for default ACL state.

---

## LAB HEADER BLOCK

```bash
echo "🕒  TIME:  $(date -Is)"
echo "👤  USER:  $(whoami)@$(hostname)"
echo "📁  PRACTICE DIR: /sys"
echo "⚠️  TRAP REMINDERS THIS LAB: T51-A T51-B T41 T44"
ls -ld /sys /tmp
ls -la /root/rhcsa_journal/lab-51a/task1 /root/rhcsa_journal/lab-51a/task2 2>/dev/null || true
ls -la /root/rhcsa_journal/lab-51b/task1 /root/rhcsa_journal/lab-51b/task2 2>/dev/null || true
```

---

## Objective

1. Audit journal and live ACL output for required `default:` entries and inheritance behavior.
2. Execute a destroy-restore drill for default ACL policy on a parent directory (**T41**).
3. Confirm cleanup leaves no sandbox identity residue (**T44**).

---

## Lab-Wide Setup — Tier B Sandbox

```bash
sudo -i

export SANDBOX=/tmp/lab51c
export GROUP=labgrp_51_dacl
export USER=labuser_51_dacl
export USER_HOME=${SANDBOX}/home_${USER}

mkdir -p "${SANDBOX}" "${USER_HOME}" /root/rhcsa_journal/lab-51c/task1 /root/rhcsa_journal/lab-51c/task2
getent group "${GROUP}" >/dev/null || groupadd "${GROUP}"
getent passwd "${USER}" >/dev/null || useradd -d "${USER_HOME}" -M -s /bin/bash -g "${GROUP}" "${USER}"
chown -R "${USER}:${GROUP}" "${SANDBOX}"
```

---

## Task 1 — Audit default ACL evidence in journal + live state

### Purpose

Prove previous labs captured the right ACL model: parent has `default:` entries, fresh child inherits, older file behavior is understood.

### Main command block

```bash
TASKLOG=/tmp/lab51c/task1.txt
PARENT=/tmp/lab51c/audit_parent
FRESH=${PARENT}/fresh_after_default
OLD=${PARENT}/old_before_default

mkdir -p "${PARENT}"
touch "${OLD}"
setfacl -d -m u:${USER}:rwx "${PARENT}"                            2>&1 | tee "${TASKLOG}"
setfacl -d -m g:${GROUP}:rx  "${PARENT}"                            2>&1 | tee -a "${TASKLOG}"
touch "${FRESH}"

echo "=== journal file presence checks ==="                         | tee -a "${TASKLOG}"
test -s /root/rhcsa_journal/lab-51a/task1/evidence.txt && echo "✅ 51a task1 evidence exists" | tee -a "${TASKLOG}"
test -s /root/rhcsa_journal/lab-51a/task2/evidence.txt && echo "✅ 51a task2 evidence exists" | tee -a "${TASKLOG}"
test -s /root/rhcsa_journal/lab-51b/task1/evidence.txt && echo "✅ 51b task1 evidence exists" | tee -a "${TASKLOG}"
test -s /root/rhcsa_journal/lab-51b/task2/evidence.txt && echo "✅ 51b task2 evidence exists" | tee -a "${TASKLOG}"

echo "=== parent default ACL entries ==="                           | tee -a "${TASKLOG}"
getfacl "${PARENT}"                                                 | tee -a "${TASKLOG}"
echo "=== old file (should not retro-inherit: T51-A) ==="           | tee -a "${TASKLOG}"
getfacl "${OLD}"                                                    | tee -a "${TASKLOG}"
echo "=== fresh file (should inherit) ==="                          | tee -a "${TASKLOG}"
getfacl "${FRESH}"                                                  | tee -a "${TASKLOG}"

echo "exit was: $?"                                                 | tee -a "${TASKLOG}"
```

---

## Task 2 — Destroy-restore drill for default ACL state (T41)

### Purpose

Rehearse full recovery: destroy the ACL-governed tree, rebuild it, re-apply defaults, and verify inheritance again.

### Main command block

```bash
TASKLOG=/tmp/lab51c/task2.txt
PARENT=/tmp/lab51c/drill_parent
RESTORED_CHILD=${PARENT}/restored_child

mkdir -p "${PARENT}"
setfacl -d -m u:${USER}:rwx "${PARENT}"                            2>&1 | tee "${TASKLOG}"
setfacl -d -m g:${GROUP}:rx  "${PARENT}"                            2>&1 | tee -a "${TASKLOG}"
getfacl "${PARENT}" > /root/rhcsa_journal/lab-51c/parent.before-destroy.getfacl

echo "=== destroy phase ==="                                        | tee -a "${TASKLOG}"
rm -rf "${PARENT}"
test -d "${PARENT}" && echo "❌ destroy failed" || echo "✅ parent removed" | tee -a "${TASKLOG}"

echo "=== restore phase ==="                                        | tee -a "${TASKLOG}"
mkdir -p "${PARENT}"
setfacl -d -m u:${USER}:rwx "${PARENT}"                            2>&1 | tee -a "${TASKLOG}"
setfacl -d -m g:${GROUP}:rx  "${PARENT}"                            2>&1 | tee -a "${TASKLOG}"
touch "${RESTORED_CHILD}"
getfacl "${PARENT}"                                                 | tee -a "${TASKLOG}"
getfacl "${RESTORED_CHILD}"                                         | tee -a "${TASKLOG}"

cp /tmp/lab51c/task1.txt /root/rhcsa_journal/lab-51c/task1/evidence.txt
cp /tmp/lab51c/task2.txt /root/rhcsa_journal/lab-51c/task2/evidence.txt

echo "exit was: $?"                                                 | tee -a "${TASKLOG}"
```

### Trap callout

- **T51-A:** verify inheritance on newly created children after restore.
- **T51-B:** default ACL remains a directory policy through the drill.
- **T41:** destroy-restore executed end-to-end instead of skipped.

---

## Lab Closeout — Section 6 Bulletproof Teardown

```bash
set +e

if getent passwd "${USER}" >/dev/null 2>&1; then
  userdel -r "${USER}" 2>/dev/null
fi
if getent group "${GROUP}" >/dev/null 2>&1; then
  groupdel "${GROUP}" 2>/dev/null
fi

rm -rf "${SANDBOX}"

echo "── Lab 51c cleanup audit ──"
getent passwd "${USER}" >/dev/null && echo "❌ user remains" || echo "✅ user gone"
getent group "${GROUP}" >/dev/null && echo "❌ group remains" || echo "✅ group gone"
test -d "${SANDBOX}" && echo "❌ sandbox remains" || echo "✅ sandbox gone"
test -d "${USER_HOME}" && echo "❌ home remains" || echo "✅ home gone"

set -e
```

---

## Lab 51c Checklist

- [ ] Task 1 audited journal evidence and live `default:` ACL entries
- [ ] Task 1 confirmed fresh child inherits while old file does not (T51-A)
- [ ] Task 2 completed destroy-restore drill for default ACL state (T41)
- [ ] Task 2 re-verified inherited ACL behavior after restore
- [ ] Section 6 closeout ended with four `✅` lines (T44)

---

## Author

**Kelvin R. Tobias**
[kelvinintech.com](https://kelvinintech.com) · [GitHub](https://github.com/kelvintechnical) · [LinkedIn](https://www.linkedin.com/in/kelvin-r-tobias-211949219)
