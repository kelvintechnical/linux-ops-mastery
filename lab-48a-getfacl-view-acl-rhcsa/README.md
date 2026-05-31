# Lab 48a: Viewing ACLs (RHCSA) — `getfacl`, `getfacl -R`, `getfacl --absolute-names`

- **Series:** linux-ops-mastery — Permissions, Special Bits, and ACLs
- **Trilogy:** `48a` (RHCSA hand-typed) → `48b` (Ansible) → `48c` (Verify)
- **Time Estimate:** 25-35 minutes
- **Tasks:** 2
- **Practice Directory (objective context):** `/srv` (inspection focus), `/tmp/lab48a` (safe write sandbox)
- **Sandbox (Tier B):** `/tmp/lab48a` with `USER=labuser_48_getfacl`, `GROUP=labgrp_48_getfacl`
- **Traps rehearsed:** **T48-A** (`ls -l` without `+` means no extended ACL, but base mode bits still govern access) · **T48-B** (`getfacl DIR` is single-level; use `-R` for recursive coverage) · **T41** (destroy-restore drill appears in 48c) · **T44** (cleanup audit)

---

## LAB HEADER BLOCK

```bash
echo "📁 PRACTICE DIR: /srv (read), /tmp/lab48a (write)"
echo "👤 USER: $(whoami)@$(hostname)"
echo "🕒 TIME: $(date -Is)"
echo "⚠️ TRAPS: T48-A T48-B T41 T44"
id
ls -ld /srv /tmp
```

> **STOP — paste output before setup.**

---

## Objective

Build exam-speed ACL inspection reflexes:

1. Identify ACL presence quickly from `ls -l` (`+` suffix on mode string).
2. Read exact ACL entries with `getfacl`.
3. Recursively audit ACLs with `getfacl -R`.
4. Preserve absolute paths in output using `getfacl --absolute-names`.
5. Recognize default ACL inheritance behavior (especially in skeleton-style template trees like `/etc/skel` patterns).

---

## Lab-Wide Setup — Tier B Sandbox

```bash
sudo -i

export LAB_NUM=48
export LAB_SLUG=getfacl
export SANDBOX=/tmp/lab48a
export GROUP=labgrp_48_getfacl
export USER=labuser_48_getfacl
export USER_HOME=${SANDBOX}/home_${USER}

mkdir -p "${SANDBOX}/task1" "${SANDBOX}/task2" "${USER_HOME}"
mkdir -p /root/rhcsa_journal/lab-48a/task1
mkdir -p /root/rhcsa_journal/lab-48a/task2

getent group "${GROUP}" >/dev/null || groupadd "${GROUP}"
getent passwd "${USER}" >/dev/null || useradd -d "${USER_HOME}" -M -s /bin/bash -g "${GROUP}" "${USER}"
chown -R "${USER}:${GROUP}" "${SANDBOX}"

id "${USER}"
stat -c '%U:%G %a %n' "${SANDBOX}" "${USER_HOME}"
```

---

## Task 1 — View a file ACL directly (`getfacl FILE`)

### Purpose

Create a file with a non-base ACL entry and inspect it with `getfacl`.

### Main command block

```bash
TASKLOG=/tmp/lab48a/task1/task1.txt

touch /tmp/lab48a/file
chown "${USER}:${GROUP}" /tmp/lab48a/file

# Required ACL seed for this lab: without this, there is no extra ACL to inspect.
setfacl -m u:${USER}:rw /tmp/lab48a/file

echo "== ls -l marker check ==" | tee "${TASKLOG}"
ls -l /tmp/lab48a/file | tee -a "${TASKLOG}"

echo "== ACL listing ==" | tee -a "${TASKLOG}"
getfacl /tmp/lab48a/file | tee -a "${TASKLOG}"

echo "== absolute names variant ==" | tee -a "${TASKLOG}"
getfacl --absolute-names /tmp/lab48a/file | tee -a "${TASKLOG}"
echo "exit was: $?"
```

### Expected checks

- `ls -l /tmp/lab48a/file` shows permission bits ending with `+`.
- `getfacl` output contains `user:${USER}:rw-`.
- `getfacl --absolute-names` keeps `/tmp/lab48a/file` in output path headers.

### Trap focus

- **T48-A:** if `+` is missing, no extended ACL exists on that inode; base owner/group/other bits still apply.

### Journal write

```bash
cp /tmp/lab48a/task1/task1.txt /root/rhcsa_journal/lab-48a/task1/evidence.txt
cat > /root/rhcsa_journal/lab-48a/task1/done.txt <<EOF
LAB: lab-48a
TASK: task1
DATE: $(date -Is)
STATUS: COMPLETE
EOF
```

---

## Task 2 — Recursive ACL view + inheritance observation

### Purpose

Show the difference between one-level and recursive ACL inspection, then observe default ACL inheritance behavior.

### Main command block

```bash
TASKLOG=/tmp/lab48a/task2/task2.txt

mkdir -p /tmp/lab48a/tree/sub
touch /tmp/lab48a/tree/root.txt /tmp/lab48a/tree/sub/leaf.txt

# Directory ACL for demo coverage
setfacl -m u:${USER}:r-x /tmp/lab48a/tree

# Default ACL to demonstrate inheritance
setfacl -m d:u:${USER}:rwX /tmp/lab48a/tree
touch /tmp/lab48a/tree/sub/inherited.txt

echo "== single-level getfacl (dir only) ==" | tee "${TASKLOG}"
getfacl /tmp/lab48a/tree | tee -a "${TASKLOG}"

echo "== recursive getfacl -R ==" | tee -a "${TASKLOG}"
getfacl -R /tmp/lab48a/tree | tee -a "${TASKLOG}"

echo "== ls -l plus markers ==" | tee -a "${TASKLOG}"
ls -l /tmp/lab48a/tree /tmp/lab48a/tree/sub | tee -a "${TASKLOG}"

echo "== /etc/skel comparison note ==" | tee -a "${TASKLOG}"
echo "Default ACLs on a template directory (same pattern as /etc/skel workflows) propagate to newly created children." | tee -a "${TASKLOG}"
echo "exit was: $?"
```

### Expected checks

- `getfacl /tmp/lab48a/tree` does not enumerate every child entry.
- `getfacl -R /tmp/lab48a/tree` includes `root.txt`, `leaf.txt`, and `inherited.txt`.
- `ls -l` on ACL-bearing entries displays `+`.

### Trap focus

- **T48-B:** `getfacl DIR` is not recursive; use `-R` when auditing trees.

### Journal write

```bash
cp /tmp/lab48a/task2/task2.txt /root/rhcsa_journal/lab-48a/task2/evidence.txt
cat > /root/rhcsa_journal/lab-48a/task2/done.txt <<EOF
LAB: lab-48a
TASK: task2
DATE: $(date -Is)
STATUS: COMPLETE
EOF
```

---

## Lab Closeout — Section 6 Teardown

```bash
set +e
userdel -r "${USER}" 2>/dev/null
groupdel "${GROUP}" 2>/dev/null
rm -rf "${SANDBOX}"

echo "── Lab 48a cleanup audit ──"
getent passwd "${USER}" >/dev/null && echo "❌ user remains" || echo "✅ user gone"
getent group "${GROUP}" >/dev/null && echo "❌ group remains" || echo "✅ group gone"
test -d "${SANDBOX}" && echo "❌ sandbox remains" || echo "✅ sandbox gone"
test -d "${USER_HOME}" && echo "❌ home remains" || echo "✅ home gone"
set -e
```

---

## Author

**Kelvin R. Tobias**
