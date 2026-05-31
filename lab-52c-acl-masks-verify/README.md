# Lab 52c: Verifying ACL Masks (Capstone) — Audit + Destroy-Restore

- **Series:** linux-ops-mastery — Files, Permissions, and Identity
- **Trilogy:** [`52a`](../lab-52a-acl-masks-rhcsa/) (RHCSA) → [`52b`](../lab-52b-acl-masks-ansible/) (Ansible) → **`52c`** (Verify)
- **Time Estimate:** 25-35 minutes
- **Tasks:** 2
- **Practice Directory (objective context):** `/run` (inspection context), `/tmp/lab52c` (verification sandbox)
- **Sandbox (Tier B):** `/tmp/lab52c` with `USER=labuser_52_aclmask`, `GROUP=labgrp_52_aclmask`
- **Traps rehearsed:** **T52-A** (mask recalc behavior) · **T52-B** (effective mask cap) · **T41** (destroy-restore drill) · **T44** (cleanup audit)

> **Auditor stance:** verify prior labs by reading journal evidence first, then rebuild state from known-good steps.

---

## LAB HEADER BLOCK

```bash
echo "📁 PRACTICE DIR: /run (inspect), /tmp/lab52c (verify sandbox)"
echo "🕒 TIME: $(date -Is)"
echo "👤 USER: $(whoami)@$(hostname)"
echo "⚠️ TRAPS: T52-A T52-B T41 T44"
ls -la /root/rhcsa_journal/lab-52a /root/rhcsa_journal/lab-52b 2>/dev/null
```

---

## Objective

Operate from the verification seat:

1. Audit journal evidence and confirm `mask::` plus `#effective:` lines are present.
2. Perform a destroy-restore ACL drill and prove behavior is reproducible.

---

## Lab-Wide Setup

```bash
sudo -i

export SANDBOX=/tmp/lab52c
export GROUP=labgrp_52_aclmask
export USER=labuser_52_aclmask
export USER_HOME=${SANDBOX}/home_${USER}

mkdir -p "${SANDBOX}/task1" "${SANDBOX}/task2" "${USER_HOME}"
mkdir -p /root/rhcsa_journal/lab-52c/task1
mkdir -p /root/rhcsa_journal/lab-52c/task2

getent group "${GROUP}" >/dev/null || groupadd "${GROUP}"
getent passwd "${USER}" >/dev/null || useradd -d "${USER_HOME}" -M -s /bin/bash -g "${GROUP}" "${USER}"
chown -R "${USER}:${GROUP}" "${SANDBOX}"
```

---

## Task 1 — Audit mask evidence in journal output

### Purpose

Verify prior labs captured ACL mask lines and effective-permission evidence.

### Main command block

```bash
TASKLOG=/tmp/lab52c/task1/task1.txt

echo "== lab-52a evidence audit ==" | tee "${TASKLOG}"
test -s /root/rhcsa_journal/lab-52a/task1/evidence.txt && echo "✅ 52a task1 evidence present" | tee -a "${TASKLOG}"
test -s /root/rhcsa_journal/lab-52a/task2/evidence.txt && echo "✅ 52a task2 evidence present" | tee -a "${TASKLOG}"
rg "mask::|#effective:" /root/rhcsa_journal/lab-52a/task1/evidence.txt /root/rhcsa_journal/lab-52a/task2/evidence.txt | tee -a "${TASKLOG}" || true

echo "== lab-52b evidence audit ==" | tee -a "${TASKLOG}"
test -s /root/rhcsa_journal/lab-52b/task1/evidence.txt && echo "✅ 52b task1 evidence present" | tee -a "${TASKLOG}"
test -s /root/rhcsa_journal/lab-52b/task2/evidence.txt && echo "✅ 52b task2 evidence present" | tee -a "${TASKLOG}"
rg "mask::|#effective:|T52-B passed" /root/rhcsa_journal/lab-52b/task1/evidence.txt /root/rhcsa_journal/lab-52b/task2/evidence.txt | tee -a "${TASKLOG}" || true

echo "Audit complete: mask line and effective cap evidence reviewed." | tee -a "${TASKLOG}"
echo "exit was: $?"
```

### Journal write

```bash
cp /tmp/lab52c/task1/task1.txt /root/rhcsa_journal/lab-52c/task1/evidence.txt
cat > /root/rhcsa_journal/lab-52c/task1/done.txt <<EOF
LAB: lab-52c
TASK: task1
DATE: $(date -Is)
STATUS: COMPLETE
EOF
```

---

## Task 2 — Destroy-restore ACL mask drill (T41 applied to ACL state)

### Purpose

Destroy ACL state, restore it from a known-good sequence, and verify `mask::` and `#effective:` are back exactly as expected.

### Main command block

```bash
TASKLOG=/tmp/lab52c/task2/task2.txt
TARGET=/tmp/lab52c/task2/drill_mask.txt

echo "seed" > "${TARGET}"
setfacl -b "${TARGET}"

# Build baseline ACL state.
setfacl -m u:${USER}:rwx "${TARGET}"
setfacl -m m::r "${TARGET}"
echo "== baseline ==" | tee "${TASKLOG}"
getfacl "${TARGET}" | tee -a "${TASKLOG}"

# Destroy phase: wipe ACL + file.
setfacl -b "${TARGET}"
rm -f "${TARGET}"
echo "destroy complete" | tee -a "${TASKLOG}"

# Restore phase: recreate and reapply known-good ACL sequence.
echo "seed-restore" > "${TARGET}"
setfacl -m u:${USER}:rwx "${TARGET}"
setfacl -m m::r "${TARGET}"

echo "== restored ==" | tee -a "${TASKLOG}"
getfacl "${TARGET}" | tee -a "${TASKLOG}"
sudo -u "${USER}" bash -c 'echo "user-write-ok" >> /tmp/lab52c/task2/drill_mask.txt' 2>&1 | tee -a "${TASKLOG}" || true
echo "✅ destroy-restore ACL drill complete (T41 applied)" | tee -a "${TASKLOG}"
echo "exit was: $?"
```

### Journal write

```bash
cp /tmp/lab52c/task2/task2.txt /root/rhcsa_journal/lab-52c/task2/evidence.txt
cat > /root/rhcsa_journal/lab-52c/task2/done.txt <<EOF
LAB: lab-52c
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

echo "── Lab 52c cleanup audit ──"
getent passwd "${USER}" >/dev/null && echo "❌ user remains" || echo "✅ user gone"
getent group "${GROUP}" >/dev/null && echo "❌ group remains" || echo "✅ group gone"
test -d "${SANDBOX}" && echo "❌ sandbox remains" || echo "✅ sandbox gone"
test -d "${USER_HOME}" && echo "❌ home remains" || echo "✅ home gone"
set -e
```

---

## Author

**Kelvin R. Tobias**
