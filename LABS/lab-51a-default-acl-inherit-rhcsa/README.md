# Lab 51a: Default Directory ACL Inheritance (RHCSA) — `setfacl -d`, `getfacl`

- **Series:** linux-ops-mastery — ACLs and Permission Control
- **Trilogy:** **`51a`** (RHCSA hand-typed) -> [`51b`](../lab-51b-default-acl-inherit-ansible/) (Ansible) -> [`51c`](../lab-51c-default-acl-inherit-verify/) (Verify capstone)
- **Time Estimate:** 25-35 minutes
- **Tasks:** 2
- **Practice Directory (rotation #51):** `/sys` (inspection context), writes happen in sandbox
- **Sandbox (Tier B):** `/tmp/lab51a` with `USER=labuser_51_dacl`, `GROUP=labgrp_51_dacl`
- **Traps rehearsed this lab:** **T51-A** (default ACL applies only to NEW children) · **T51-B** (default ACL belongs on directories, not files) · **T41** · **T44**

> **Topic focus:** set default ACLs on a parent directory and prove `default:` entries are inherited only by files created after the default ACL is set.

---

## LAB HEADER BLOCK

```bash
echo "🕒  TIME:  $(date -Is)"
echo "👤  USER:  $(whoami)@$(hostname)"
echo "📁  PRACTICE DIR: /sys"
echo "⚠️  TRAP REMINDERS THIS LAB: T51-A T51-B T41 T44"
ls -ld /sys /tmp
command -v setfacl
command -v getfacl
```

---

## Objective

1. Apply default ACL entries on a directory using `setfacl -d -m`.
2. Verify `getfacl` shows `default:` entries and new files inherit them.
3. Prove existing files do not retroactively gain inherited ACL entries (**T51-A**).

---

## Lab-Wide Setup — Tier B Sandbox

```bash
sudo -i

export SANDBOX=/tmp/lab51a
export GROUP=labgrp_51_dacl
export USER=labuser_51_dacl
export USER_HOME=${SANDBOX}/home_${USER}

mkdir -p "${SANDBOX}" "${USER_HOME}" /root/rhcsa_journal/lab-51a/task1 /root/rhcsa_journal/lab-51a/task2
getent group "${GROUP}" >/dev/null || groupadd "${GROUP}"
getent passwd "${USER}" >/dev/null || useradd -d "${USER_HOME}" -M -s /bin/bash -g "${GROUP}" "${USER}"
chown -R "${USER}:${GROUP}" "${SANDBOX}"
```

---

## Task 1 — Apply default ACL and verify inheritance on new file

### Purpose

Build the default-ACL reflex: set on directory, then create child, then confirm inherited ACL entries with `getfacl`.

### Main command block

```bash
TASKLOG=/tmp/lab51a/task1.txt
cd /tmp/lab51a

mkdir -p parent
setfacl -d -m u:${USER}:rwx parent                                2>&1 | tee "${TASKLOG}"
setfacl -d -m g:${GROUP}:rx  parent                                2>&1 | tee -a "${TASKLOG}"

touch parent/newfile
getfacl parent                                                     2>&1 | tee -a "${TASKLOG}"
getfacl parent/newfile                                             2>&1 | tee -a "${TASKLOG}"

echo "exit was: $?"                                                | tee -a "${TASKLOG}"
```

### Expected signals

- `getfacl parent` shows lines starting with `default:user:...` and `default:group:...`.
- `getfacl parent/newfile` shows inherited ACL entries matching the parent defaults.

### Journal write

```bash
cp /tmp/lab51a/task1.txt /root/rhcsa_journal/lab-51a/task1/evidence.txt
```

---

## Task 2 — Prove existing file unchanged (T51-A) + T51-B reminder

### Purpose

Demonstrate the most common failure: admins expect old files to inherit default ACLs retroactively.

### Main command block

```bash
TASKLOG=/tmp/lab51a/task2.txt
cd /tmp/lab51a

mkdir -p parent_existing_demo
touch parent_existing_demo/preexisting
getfacl parent_existing_demo/preexisting                           2>&1 | tee "${TASKLOG}"

setfacl -d -m u:${USER}:rwx parent_existing_demo                  2>&1 | tee -a "${TASKLOG}"
setfacl -d -m g:${GROUP}:rx  parent_existing_demo                  2>&1 | tee -a "${TASKLOG}"

touch parent_existing_demo/new_after_default
echo "=== preexisting (should NOT gain inherited ACL retroactively) ===" | tee -a "${TASKLOG}"
getfacl parent_existing_demo/preexisting                           2>&1 | tee -a "${TASKLOG}"
echo "=== new_after_default (should inherit) ==="                  | tee -a "${TASKLOG}"
getfacl parent_existing_demo/new_after_default                     2>&1 | tee -a "${TASKLOG}"

echo "=== T51-B reminder: default ACL on regular file is invalid ===" | tee -a "${TASKLOG}"
setfacl -d -m u:${USER}:rwx parent_existing_demo/preexisting       2>&1 | tee -a "${TASKLOG}" || true

echo "exit was: $?"                                                | tee -a "${TASKLOG}"
```

### Trap callout

- **T51-A:** default ACL changes apply only to children created after the default ACL exists.
- **T51-B:** use `setfacl -d` on directories; default ACL on a regular file is not valid.

### Journal write

```bash
cp /tmp/lab51a/task2.txt /root/rhcsa_journal/lab-51a/task2/evidence.txt
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

echo "── Lab 51a cleanup audit ──"
getent passwd "${USER}" >/dev/null && echo "❌ user remains" || echo "✅ user gone"
getent group "${GROUP}" >/dev/null && echo "❌ group remains" || echo "✅ group gone"
test -d "${SANDBOX}" && echo "❌ sandbox remains" || echo "✅ sandbox gone"
test -d "${USER_HOME}" && echo "❌ home remains" || echo "✅ home gone"

set -e
```

---

## Lab 51a Checklist

- [ ] Task 1 completed (`setfacl -d -m` entries set on parent directory)
- [ ] Verified `getfacl` shows `default:` entries on parent
- [ ] Verified `newfile` inherited expected ACL entries
- [ ] Task 2 proved T51-A (existing file unchanged)
- [ ] Task 2 rehearsed T51-B (default ACL on file invalid)
- [ ] Section 6 closeout ended with four `✅` lines

---

## Author

**Kelvin R. Tobias**
[kelvinintech.com](https://kelvinintech.com) · [GitHub](https://github.com/kelvintechnical) · [LinkedIn](https://www.linkedin.com/in/kelvin-r-tobias-211949219)
