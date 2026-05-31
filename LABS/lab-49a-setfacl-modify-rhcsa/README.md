# Lab 49a: Modifying ACLs (RHCSA) — `setfacl -m`, recursive ACLs, mask control

- **Series:** linux-ops-mastery — Permissions, Special Bits & ACLs
- **Trilogy:** `49a` (RHCSA hand-typed) -> [`49b`](../lab-49b-setfacl-modify-ansible/) (Ansible) -> [`49c`](../lab-49c-setfacl-modify-verify/) (Verify)
- **Time Estimate:** 30-40 minutes
- **Tasks:** 2
- **Practice Directory (objective context):** `/dev` (inspection), `/tmp/lab49a` (write target)
- **Sandbox (Tier B):** `/tmp/lab49a` with `USER=labuser_49_setfacl`, `GROUP=labgrp_49_setfacl`
- **Traps rehearsed:** **T49-A** (mask caps effective perms) · **T49-B** (`setfacl -R` is for directory trees, not single-file intent) · **T41** (destroy-restore appears in 49c) · **T44** (cleanup audit)

> **Mask reality check:** you can set an entry like `u:${USER}:rwx`, but if mask is `rw-`, effective permission is `rw-`.

---

## LAB HEADER BLOCK

```bash
echo "📁 PRACTICE DIR: /dev (inspect), /tmp/lab49a (write)"
echo "👤 USER: $(whoami)@$(hostname)"
echo "🕒 TIME: $(date -Is)"
echo "⚠️ TRAPS: T49-A T49-B T41 T44"
id
setfacl --version
ls -ld /dev /tmp
```

---

## Objective

Build ACL modification reflexes used on RHCSA:

1. Grant per-user access with `setfacl -m u:user:rw`.
2. Grant group ACLs recursively with `setfacl -R -m g:group:rx`.
3. Prove effective rights with `getfacl` and runtime access checks.
4. Control effective permissions with ACL mask (`m::rwx`, capped variants).

---

## Lab-Wide Setup — Tier B Sandbox

```bash
sudo -i

export SANDBOX=/tmp/lab49a
export GROUP=labgrp_49_setfacl
export USER=labuser_49_setfacl
export USER_HOME=${SANDBOX}/home_${USER}

mkdir -p "${SANDBOX}/task1" "${SANDBOX}/task2/dir/sub" "${USER_HOME}"
mkdir -p /root/rhcsa_journal/lab-49a/task1
mkdir -p /root/rhcsa_journal/lab-49a/task2

getent group "${GROUP}" >/dev/null || groupadd "${GROUP}"
getent passwd "${USER}" >/dev/null || useradd -d "${USER_HOME}" -M -s /bin/bash -g "${GROUP}" "${USER}"

echo "root-only secret" > "${SANDBOX}/task1/file"
chmod 600 "${SANDBOX}/task1/file"
chown root:root "${SANDBOX}/task1/file"

touch "${SANDBOX}/task2/dir/root.txt" "${SANDBOX}/task2/dir/sub/leaf.txt"
chmod -R 640 "${SANDBOX}/task2/dir"
chown -R root:root "${SANDBOX}/task2/dir"
```

---

## Task 1 — Modify user ACL and verify effective access

### Purpose

Grant `${USER}` read/write via ACL on a file where base mode (`600 root:root`) blocks normal access.

### Main command block

```bash
TASKLOG=/tmp/lab49a/task1/task1.txt
TARGET=/tmp/lab49a/task1/file

echo "== baseline (expected deny for ${USER}) ==" | tee "${TASKLOG}"
sudo -u "${USER}" cat "${TARGET}" 2>&1 | tee -a "${TASKLOG}" || true
stat -c '%U:%G %a %n' "${TARGET}" | tee -a "${TASKLOG}"

echo "== grant ACL u:${USER}:rw ==" | tee -a "${TASKLOG}"
setfacl -m "u:${USER}:rw" "${TARGET}"
getfacl "${TARGET}" | tee -a "${TASKLOG}"

echo "== runtime proof (should now work) ==" | tee -a "${TASKLOG}"
sudo -u "${USER}" cat "${TARGET}" 2>&1 | tee -a "${TASKLOG}"
sudo -u "${USER}" bash -c "echo 'append-by-${USER}' >> '${TARGET}'"
tail -n 2 "${TARGET}" | tee -a "${TASKLOG}"
echo "exit was: $?"
```

### Trap callout

- **T49-A intro:** if mask is tightened (for example `m::rw-`), even `u:${USER}:rwx` becomes effectively `rw-`.

### Journal write

```bash
cp /tmp/lab49a/task1/task1.txt /root/rhcsa_journal/lab-49a/task1/evidence.txt
cat > /root/rhcsa_journal/lab-49a/task1/done.txt <<EOF
LAB: lab-49a
TASK: task1
DATE: $(date -Is)
STATUS: COMPLETE
EOF
```

---

## Task 2 — Recursive group ACL + mask interaction demo

### Purpose

Apply ACLs over a directory tree and prove mask-controlled effective permissions.

### Main command block

```bash
TASKLOG=/tmp/lab49a/task2/task2.txt
TREE=/tmp/lab49a/task2/dir

echo "== recursive group ACL: g:${GROUP}:rx ==" | tee "${TASKLOG}"
setfacl -R -m "g:${GROUP}:rx" "${TREE}"
getfacl -R "${TREE}" | tee -a "${TASKLOG}"

echo "== mask demo: set user ACL then cap with mask ==" | tee -a "${TASKLOG}"
setfacl -m "u:${USER}:rwx" "${TREE}/root.txt"
setfacl -m "m::rw-" "${TREE}/root.txt"
getfacl "${TREE}/root.txt" | tee -a "${TASKLOG}"

echo "== runtime check (execute bit masked away on file) ==" | tee -a "${TASKLOG}"
sudo -u "${USER}" test -r "${TREE}/root.txt" && echo "read: yes" | tee -a "${TASKLOG}"
sudo -u "${USER}" test -x "${TREE}/root.txt" && echo "exec: yes" | tee -a "${TASKLOG}" || echo "exec: no (masked)" | tee -a "${TASKLOG}"

echo "== T49-B reminder ==" | tee -a "${TASKLOG}"
echo "Use -R for directory trees. If your target is one file, use setfacl -m directly on that file." | tee -a "${TASKLOG}"
echo "exit was: $?"
```

### Journal write

```bash
cp /tmp/lab49a/task2/task2.txt /root/rhcsa_journal/lab-49a/task2/evidence.txt
cat > /root/rhcsa_journal/lab-49a/task2/done.txt <<EOF
LAB: lab-49a
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

echo "── Lab 49a cleanup audit ──"
getent passwd "${USER}" >/dev/null && echo "❌ user remains" || echo "✅ user gone"
getent group "${GROUP}" >/dev/null && echo "❌ group remains" || echo "✅ group gone"
test -d "${SANDBOX}" && echo "❌ sandbox remains" || echo "✅ sandbox gone"
test -d "${USER_HOME}" && echo "❌ home remains" || echo "✅ home gone"
set -e
```

---

## Author

**Kelvin R. Tobias**
