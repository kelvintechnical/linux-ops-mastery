# Lab 52a: ACL Masks (RHCSA) — `setfacl -m m::`, `getfacl`, effective permissions

- **Series:** linux-ops-mastery — Files, Permissions, and Identity
- **Trilogy:** `52a` (RHCSA hand-typed) → [`52b`](../lab-52b-acl-masks-ansible/) (Ansible) → [`52c`](../lab-52c-acl-masks-verify/) (Verify)
- **Time Estimate:** 30-40 minutes
- **Tasks:** 2
- **Practice Directory (objective context):** `/run` (inspection context), `/tmp/lab52a` (write target)
- **Sandbox (Tier B):** `/tmp/lab52a` with `USER=labuser_52_aclmask`, `GROUP=labgrp_52_aclmask`
- **Traps rehearsed:** **T52-A** (ACL mask auto-recalculates on each `setfacl` call unless `-n` is used) · **T52-B** (mask caps effective rights for named users/groups) · **T41** (destroy-restore drill appears in 52c) · **T44** (cleanup audit)

> **Mask rule:** `mask::` is the effective maximum for named user/group ACL entries. It does **not** cap file owner (`user::`) or other (`other::`).

---

## LAB HEADER BLOCK

```bash
echo "📁 PRACTICE DIR: /run (inspect), /tmp/lab52a (write)"
echo "👤 USER: $(whoami)@$(hostname)"
echo "🕒 TIME: $(date -Is)"
echo "⚠️ TRAPS: T52-A T52-B T41 T44"
id
ls -ld /run /tmp
```

> **STOP — paste output before setup.**

---

## Objective

Build ACL mask reflexes for exam-day troubleshooting:

1. Set named-user ACL permissions, then cap them with `mask::`.
2. Read `getfacl` output and interpret `#effective:` correctly.
3. Prove mask capping affects named users/groups, not owner/other.
4. Demonstrate mask recalculation behavior and `-n` preservation.

---

## Lab-Wide Setup — Tier B Sandbox

```bash
sudo -i

export SANDBOX=/tmp/lab52a
export GROUP=labgrp_52_aclmask
export USER=labuser_52_aclmask
export USER_HOME=${SANDBOX}/home_${USER}

mkdir -p "${SANDBOX}/task1" "${SANDBOX}/task2" "${USER_HOME}"
mkdir -p /root/rhcsa_journal/lab-52a/task1
mkdir -p /root/rhcsa_journal/lab-52a/task2

getent group "${GROUP}" >/dev/null || groupadd "${GROUP}"
getent passwd "${USER}" >/dev/null || useradd -d "${USER_HOME}" -M -s /bin/bash -g "${GROUP}" "${USER}"
chown -R root:root "${SANDBOX}"
chmod -R 0770 "${SANDBOX}"
```

---

## Task 1 — Mask caps effective permissions (T52-B)

### Purpose

Assign `rwx` to a named user, then apply a stricter mask and verify the named user is effectively capped.

### Main command block

```bash
TASKLOG=/tmp/lab52a/task1/task1.txt
DATA=/tmp/lab52a/task1/mask_demo.txt
EXEC=/tmp/lab52a/task1/mask_exec.sh

echo "seed" > "${DATA}"
cat > "${EXEC}" <<'EOF'
#!/usr/bin/env bash
echo "EXEC-RAN"
EOF

chmod 0700 "${EXEC}"
chown root:root "${DATA}" "${EXEC}"

# Named user gets rwx initially.
setfacl -m u:${USER}:rwx "${DATA}" "${EXEC}"

# Mask now caps named-user effective rights to rw.
setfacl -m m::rw "${DATA}" "${EXEC}"

echo "== getfacl after mask cap ==" | tee "${TASKLOG}"
getfacl "${DATA}" "${EXEC}" | tee -a "${TASKLOG}"

# Write should work (w is still effective through mask).
sudo -u "${USER}" bash -c 'echo "user-write-ok" >> /tmp/lab52a/task1/mask_demo.txt'
echo "write test exit: $?" | tee -a "${TASKLOG}"

# Execute should fail because mask removed x (effective rw-).
sudo -u "${USER}" /tmp/lab52a/task1/mask_exec.sh 2>&1 | tee -a "${TASKLOG}" || true
echo "execute attempt captured (expected failure under mask cap)" | tee -a "${TASKLOG}"
echo "exit was: $?"
```

### Journal write

```bash
cp /tmp/lab52a/task1/task1.txt /root/rhcsa_journal/lab-52a/task1/evidence.txt
cat > /root/rhcsa_journal/lab-52a/task1/done.txt <<EOF
LAB: lab-52a
TASK: task1
DATE: $(date -Is)
STATUS: COMPLETE
EOF
```

---

## Task 2 — Preserve mask with `-n` vs default recalculation (T52-A)

### Purpose

Prove that each `setfacl` call normally recalculates mask, and that `setfacl -n` preserves the current mask.

### Main command block

```bash
TASKLOG=/tmp/lab52a/task2/task2.txt
TARGET=/tmp/lab52a/task2/recalc_demo.txt

echo "acl-recalc-demo" > "${TARGET}"
setfacl -b "${TARGET}"

# Start with strict mask r--.
setfacl -m u:${USER}:rwx "${TARGET}"
setfacl -m m::r "${TARGET}"
echo "== baseline strict mask ==" | tee "${TASKLOG}"
getfacl "${TARGET}" | tee -a "${TASKLOG}"

# Preserve current mask while adding another named user ACL.
setfacl -n -m u:nobody:rwx "${TARGET}"
echo "== after setfacl -n (mask preserved) ==" | tee -a "${TASKLOG}"
getfacl "${TARGET}" | tee -a "${TASKLOG}"

# Default behavior: recalculates mask from ACL entries.
setfacl -m u:daemon:rwx "${TARGET}"
echo "== after default setfacl (mask recalculated) ==" | tee -a "${TASKLOG}"
getfacl "${TARGET}" | tee -a "${TASKLOG}"

echo "T52-A proof: compare mask:: line before/after -n and default call." | tee -a "${TASKLOG}"
echo "exit was: $?"
```

### Journal write

```bash
cp /tmp/lab52a/task2/task2.txt /root/rhcsa_journal/lab-52a/task2/evidence.txt
cat > /root/rhcsa_journal/lab-52a/task2/done.txt <<EOF
LAB: lab-52a
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

echo "── Lab 52a cleanup audit ──"
getent passwd "${USER}" >/dev/null && echo "❌ user remains" || echo "✅ user gone"
getent group "${GROUP}" >/dev/null && echo "❌ group remains" || echo "✅ group gone"
test -d "${SANDBOX}" && echo "❌ sandbox remains" || echo "✅ sandbox gone"
test -d "${USER_HOME}" && echo "❌ home remains" || echo "✅ home gone"
set -e
```

---

## Author

**Kelvin R. Tobias**
