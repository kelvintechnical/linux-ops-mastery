# Lab 47a: Checking ACL Support (RHCSA) — `findmnt`, `mount`, `tune2fs`

- **Series:** linux-ops-mastery — Filesystems, Mount Options, and ACL Readiness
- **Trilogy:** `47a` (RHCSA hand-typed) -> [`47b`](../lab-47b-acl-mount-option-ansible/) (Ansible) -> [`47c`](../lab-47c-acl-mount-option-verify/) (Verify)
- **Time Estimate:** 25-35 minutes
- **Tasks:** 2
- **Practice Directory (objective context):** `/opt` (read-only inspection only)
- **Sandbox (Tier B):** `/tmp/lab47a` with `USER=labuser_47_aclmount`, `GROUP=labgrp_47_aclmount`
- **Traps rehearsed this lab:** **T47-A** (XFS always supports ACL; `acl` option may be ignored while ACL still works; ext4 historically needed explicit `acl`) · **T47-B** (`defaults` on modern RHEL often includes ACL behavior; verify runtime with `findmnt`, not only `/etc/fstab`) · **T41** · **T44**

> **Safety boundary:** read-only inspection lab. **Do not edit `/etc/fstab`** in this trilogy.

---

## LAB HEADER BLOCK

```bash
echo "📁 PRACTICE DIR: /opt (read-only), /tmp/lab47a (write target)"
echo "👤 USER: $(whoami)@$(hostname)"
echo "🕒 TIME: $(date -Is)"
echo "⚠️ TRAPS: T47-A T47-B T41 T44"
findmnt -o TARGET,FSTYPE,OPTIONS /
ls -ld /opt /tmp
```

> **STOP — paste header output before setup.**

---

## Objective

1. Inspect live root mount options with `findmnt` and `mount`.
2. Compare filesystem behavior between `ext4` and `xfs` for ACL support.
3. On `ext4`, inspect default mount options via `tune2fs -l`.
4. Validate ACL readiness from runtime state first, then cross-check `/etc/fstab` as read-only reference.

---

## Lab-Wide Setup — Tier B Sandbox

```bash
sudo -i

export SANDBOX=/tmp/lab47a
export GROUP=labgrp_47_aclmount
export USER=labuser_47_aclmount
export USER_HOME=${SANDBOX}/home_${USER}

mkdir -p "${SANDBOX}" "${USER_HOME}" /root/rhcsa_journal/lab-47a/task1 /root/rhcsa_journal/lab-47a/task2
getent group "${GROUP}" >/dev/null || groupadd "${GROUP}"
getent passwd "${USER}" >/dev/null || useradd -d "${USER_HOME}" -M -s /bin/bash -g "${GROUP}" "${USER}"
chown -R "${USER}:${GROUP}" "${SANDBOX}"

id "${USER}"
ls -ld "${SANDBOX}" "${USER_HOME}"
```

---

## Task 1 — Runtime ACL support inspection (`findmnt` + `mount`)

### Purpose

Build the first-pass ACL check you should trust most: current runtime mount options.

### Main command block

```bash
TASKLOG=/opt/lab47a-task1.txt

echo "═══ root runtime mount options (findmnt) ═══"      | tee "${TASKLOG}"
findmnt -o TARGET,FSTYPE,OPTIONS /                      | tee -a "${TASKLOG}"

echo "═══ mount view filter (acl/ext4/xfs) ═══"         | tee -a "${TASKLOG}"
mount | grep -E 'acl|ext4|xfs'                          | tee -a "${TASKLOG}" || true

echo "═══ read-only /etc/fstab root entry check ═══"    | tee -a "${TASKLOG}"
awk '$1 !~ /^#/ && $2=="/" {print}' /etc/fstab          | tee -a "${TASKLOG}" || true

echo "exit was: $?"                                     | tee -a "${TASKLOG}"
```

### Trap callout

- **T47-B:** seeing `defaults` (or no explicit `acl`) in `/etc/fstab` does not prove ACL is off. Trust live output from `findmnt` first.

### Journal write

```bash
JDIR=/root/rhcsa_journal/lab-47a/task1
cp /opt/lab47a-task1.txt "${JDIR}/evidence.txt"
```

---

## Task 2 — `tune2fs` ext4 defaults vs XFS ACL behavior

### Purpose

Demonstrate the filesystem-specific ACL interpretation:

- `ext4`: inspect default mount options from superblock metadata.
- `xfs`: ACL support is built in; explicit `acl` option can be ignored while ACL still works.

### Main command block

```bash
TASKLOG=/opt/lab47a-task2.txt

ROOT_SRC=$(findmnt -n -o SOURCE /)
ROOT_FSTYPE=$(findmnt -n -o FSTYPE /)
ROOT_OPTS=$(findmnt -n -o OPTIONS /)

echo "root source=${ROOT_SRC}"                          | tee "${TASKLOG}"
echo "root fstype=${ROOT_FSTYPE}"                       | tee -a "${TASKLOG}"
echo "root options=${ROOT_OPTS}"                        | tee -a "${TASKLOG}"

if [ "${ROOT_FSTYPE}" = "ext4" ]; then
  echo "═══ ext4 default mount options (tune2fs) ═══"   | tee -a "${TASKLOG}"
  tune2fs -l "${ROOT_SRC}" | grep -i 'Default mount options' | tee -a "${TASKLOG}"
  echo "RHEL9 note: ext4 ACL is enabled by default on modern builds; verify with findmnt runtime output." | tee -a "${TASKLOG}"
else
  echo "═══ xfs note ═══"                               | tee -a "${TASKLOG}"
  echo "XFS has ACL support by default; explicit acl/noacl in fstab may be ignored depending on kernel/fs behavior." | tee -a "${TASKLOG}"
fi

echo "exit was: $?"                                     | tee -a "${TASKLOG}"
```

### Trap callout

- **T47-A:** do not conclude "ACL disabled" just because `acl` is absent in `/etc/fstab`; interpretation depends on filesystem and runtime mount behavior.

### Journal write

```bash
JDIR=/root/rhcsa_journal/lab-47a/task2
cp /opt/lab47a-task2.txt "${JDIR}/evidence.txt"
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

echo "── Lab 47a cleanup audit ──"
getent passwd "${USER}" >/dev/null && echo "❌ user remains" || echo "✅ user gone"
getent group "${GROUP}" >/dev/null && echo "❌ group remains" || echo "✅ group gone"
test -d "${SANDBOX}" && echo "❌ sandbox remains" || echo "✅ sandbox gone"
test -d "${USER_HOME}" && echo "❌ home remains" || echo "✅ home gone"

set -e
```

---

## Lab 47a Checklist

- [ ] Task 1 completed (`findmnt -o TARGET,FSTYPE,OPTIONS /` and `mount | grep -E 'acl|ext4|xfs'` captured)
- [ ] Task 2 completed (`tune2fs -l` defaults checked for `ext4`, or XFS default ACL note documented)
- [ ] Read-only `/etc/fstab` check recorded (no edits made)
- [ ] T47-A/T47-B plus T41/T44 notes captured in evidence
- [ ] Section 6 closeout audit shows four `✅` lines

---

## Author

**Kelvin R. Tobias**
[kelvinintech.com](https://kelvinintech.com) · [GitHub](https://github.com/kelvintechnical) · [LinkedIn](https://www.linkedin.com/in/kelvin-r-tobias-211949219)
