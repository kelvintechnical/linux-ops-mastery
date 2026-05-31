# Lab 47c: Verifying ACL Mount Support — audit + destroy/restore

- **Series:** linux-ops-mastery — Filesystems, Mount Options, and ACL Readiness
- **Trilogy:** [`47a`](../lab-47a-acl-mount-option-rhcsa/) (RHCSA) -> [`47b`](../lab-47b-acl-mount-option-ansible/) (Ansible) -> `47c` (Verify — you are here)
- **Time Estimate:** 25-35 minutes
- **Tasks:** 2 (Task 1 = audit journal evidence, Task 2 = destroy-restore drill)
- **Practice Directory (objective context):** `/opt` (read-only inspection only)
- **Sandbox (Tier B):** `/tmp/lab47c` with `USER=labuser_47_aclmount`, `GROUP=labgrp_47_aclmount`
- **Traps rehearsed this lab:** **T47-A** · **T47-B** · **T41** · **T44**

> **Safety boundary:** read-only inspection lab. **Do not edit `/etc/fstab`** in this trilogy.

---

## LAB HEADER BLOCK

```bash
echo "📁 PRACTICE DIR: /opt (read-only), /tmp/lab47c (write target)"
echo "👤 USER: $(whoami)@$(hostname)"
echo "🕒 TIME: $(date -Is)"
echo "⚠️ TRAPS: T47-A T47-B T41 T44"
findmnt -o TARGET,FSTYPE,OPTIONS /
```

> **STOP — paste header output before setup.**

---

## Objective

1. Produce auditor-grade runtime evidence for ACL support from `findmnt`, `mount`, and (if ext4) `tune2fs`.
2. Execute a destroy-restore verification drill that catches false conclusions from `/etc/fstab`-only checks.

---

## Lab-Wide Setup — Tier B Sandbox

```bash
sudo -i

export SANDBOX=/tmp/lab47c
export GROUP=labgrp_47_aclmount
export USER=labuser_47_aclmount
export USER_HOME=${SANDBOX}/home_${USER}

mkdir -p "${SANDBOX}" "${USER_HOME}" /root/rhcsa_journal/lab-47c/task1 /root/rhcsa_journal/lab-47c/task2
getent group "${GROUP}" >/dev/null || groupadd "${GROUP}"
getent passwd "${USER}" >/dev/null || useradd -d "${USER_HOME}" -M -s /bin/bash -g "${GROUP}" "${USER}"
chown -R "${USER}:${GROUP}" "${SANDBOX}"
```

---

## Task 1 — Audit runtime ACL support into journal

### Purpose

Collect an evidence set that can survive review:

- Runtime mount truth (`findmnt`, `mount`)
- Filesystem type context (`ext4` vs `xfs`)
- Read-only `/etc/fstab` reference line

### Main command block

```bash
TASKLOG=/opt/lab47c-task1-audit.txt

ROOT_SRC=$(findmnt -n -o SOURCE /)
ROOT_FSTYPE=$(findmnt -n -o FSTYPE /)

echo "═══ runtime root options (findmnt) ═══"            | tee "${TASKLOG}"
findmnt -o TARGET,FSTYPE,OPTIONS /                      | tee -a "${TASKLOG}"

echo "═══ mount filter (acl/ext4/xfs) ═══"              | tee -a "${TASKLOG}"
mount | grep -E 'acl|ext4|xfs'                          | tee -a "${TASKLOG}" || true

if [ "${ROOT_FSTYPE}" = "ext4" ]; then
  echo "═══ ext4 defaults (tune2fs) ═══"                 | tee -a "${TASKLOG}"
  tune2fs -l "${ROOT_SRC}" | grep -i 'Default mount options' | tee -a "${TASKLOG}"
else
  echo "═══ xfs default ACL note ═══"                    | tee -a "${TASKLOG}"
  echo "xfs ACL support is built in by default."         | tee -a "${TASKLOG}"
fi

echo "═══ read-only /etc/fstab root line ═══"            | tee -a "${TASKLOG}"
awk '$1 !~ /^#/ && $2=="/" {print}' /etc/fstab          | tee -a "${TASKLOG}" || true

echo "exit was: $?"                                      | tee -a "${TASKLOG}"
```

### Journal write

```bash
JDIR=/root/rhcsa_journal/lab-47c/task1
cp /opt/lab47c-task1-audit.txt "${JDIR}/audit.txt"
```

---

## Task 2 — Destroy-restore drill (T41 resilience applied to ACL verification)

### Purpose

Simulate a bad verification method, then restore to a correct method:

1. **Destroy:** create an incorrect ACL conclusion from `/etc/fstab`-only interpretation.
2. **Restore:** re-check with runtime `findmnt` and correct the verdict.

### Main command block

```bash
TASKLOG=/opt/lab47c-task2-drill.txt

echo "═══ DESTROY phase: fstab-only conclusion (intentionally weak) ═══" | tee "${TASKLOG}"
FSTAB_ROOT_LINE=$(awk '$1 !~ /^#/ && $2=="/" {print}' /etc/fstab)
echo "fstab_root_line=${FSTAB_ROOT_LINE:-<none>}"                         | tee -a "${TASKLOG}"
echo "verdict_destroy=UNTRUSTED (T47-B risk: fstab-only check)"           | tee -a "${TASKLOG}"

echo "═══ RESTORE phase: runtime truth with findmnt ═══"                  | tee -a "${TASKLOG}"
ROOT_FSTYPE=$(findmnt -n -o FSTYPE /)
ROOT_OPTS=$(findmnt -n -o OPTIONS /)
echo "runtime_fstype=${ROOT_FSTYPE}"                                       | tee -a "${TASKLOG}"
echo "runtime_opts=${ROOT_OPTS}"                                           | tee -a "${TASKLOG}"

if [ "${ROOT_FSTYPE}" = "xfs" ] || echo "${ROOT_OPTS}" | grep -qw acl; then
  echo "verdict_restore=ACL_READY"                                          | tee -a "${TASKLOG}"
else
  echo "verdict_restore=CHECK_REQUIRED (non-xfs without explicit acl)"      | tee -a "${TASKLOG}"
fi

echo "trap_notes=T47-A T47-B T41 T44"                                       | tee -a "${TASKLOG}"
echo "exit was: $?"                                                          | tee -a "${TASKLOG}"
```

### Journal write

```bash
JDIR=/root/rhcsa_journal/lab-47c/task2
cp /opt/lab47c-task2-drill.txt "${JDIR}/destroy-restore.txt"
```

---

## Lab Closeout — Bulletproof Teardown (Section 6)

```bash
set +e

if getent passwd "${USER}" >/dev/null 2>&1; then
  userdel -r "${USER}" 2>/dev/null
fi
if getent group "${GROUP}" >/dev/null 2>&1; then
  groupdel "${GROUP}" 2>/dev/null
fi

rm -rf "${SANDBOX}"

echo "── Lab 47c cleanup audit ──"
getent passwd "${USER}" >/dev/null && echo "❌ user remains" || echo "✅ user gone"
getent group "${GROUP}" >/dev/null && echo "❌ group remains" || echo "✅ group gone"
test -d "${SANDBOX}" && echo "❌ sandbox remains" || echo "✅ sandbox gone"
test -d "${USER_HOME}" && echo "❌ home remains" || echo "✅ home gone"

set -e
```

---

## Lab 47c Checklist

- [ ] Task 1 completed (runtime audit captured with `findmnt`, `mount`, and ext4/XFS context)
- [ ] Task 2 completed (destroy-restore drill corrected fstab-only assumption using runtime evidence)
- [ ] Read-only `/etc/fstab` cross-check recorded (no edits made)
- [ ] T47-A/T47-B plus T41/T44 notes captured in evidence
- [ ] Section 6 closeout audit shows four `✅` lines

---

## Author

**Kelvin R. Tobias**
[kelvinintech.com](https://kelvinintech.com) · [GitHub](https://github.com/kelvintechnical) · [LinkedIn](https://www.linkedin.com/in/kelvin-r-tobias-211949219)
