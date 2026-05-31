# Lab 41c: Verifying Ownership Changes (Capstone) — Audit + Destroy-Restore

- **Series:** linux-ops-mastery — Files, Permissions, and Identity
- **Trilogy:** [`41a`](../lab-41a-chown-chgrp-ownership-rhcsa/) (RHCSA) → [`41b`](../lab-41b-chown-chgrp-ownership-ansible/) (Ansible) → **`41c`** (Verify)
- **Time Estimate:** 25-35 minutes
- **Tasks:** 2
- **Practice Directory (objective context):** `/etc` (inspection only)
- **Sandbox (Tier B):** `/tmp/lab41c` with `USER=labuser_41_chown`, `GROUP=labgrp_41_chown`
- **Traps rehearsed:** **T41-A** (canon syntax memory check) · **T41-B** (recursive ownership + symlink caution) · **T41** (destroy-restore drill) · **T44** (cleanup audit)

> **Variable warning:** `USER=labuser_41_chown` is the sandbox identity; it is not shorthand for omitting explicit ownership checks.

---

## LAB HEADER BLOCK

```bash
echo "📁 PRACTICE DIR: /etc (inspect), /tmp/lab41c (verify sandbox)"
echo "🕒 TIME: $(date -Is)"
echo "👤 USER: $(whoami)@$(hostname)"
echo "⚠️ TRAPS: T41-A T41-B T41 T44"
ls -la /root/rhcsa_journal/lab-41a /root/rhcsa_journal/lab-41b 2>/dev/null
```

---

## Objective

Operate from the auditor seat:

1. Validate ownership outcomes from 41a/41b journals against expected owner:group tuples.
2. Re-run a destroy-restore drill so ownership state can be rebuilt from journal evidence.

---

## Lab-Wide Setup

```bash
sudo -i

export SANDBOX=/tmp/lab41c
export GROUP=labgrp_41_chown
export USER=labuser_41_chown
export USER_HOME=${SANDBOX}/home_${USER}

mkdir -p "${SANDBOX}" "${USER_HOME}" "${SANDBOX}/task1" "${SANDBOX}/task2"
mkdir -p /root/rhcsa_journal/lab-41c/task1
mkdir -p /root/rhcsa_journal/lab-41c/task2

getent group "${GROUP}" >/dev/null || groupadd "${GROUP}"
getent passwd "${USER}" >/dev/null || useradd -d "${USER_HOME}" -M -s /bin/bash -g "${GROUP}" "${USER}"
chown -R "${USER}:${GROUP}" "${SANDBOX}"
```

---

## Task 1 — Audit ownership matches journal expectations

### Purpose

Read prior lab evidence and confirm expected ownership decisions are visible in output.

### Main command block

```bash
TASKLOG=/tmp/lab41c/task1/task1.txt

echo "== Audit 41a task1 evidence ==" | tee "${TASKLOG}"
test -s /root/rhcsa_journal/lab-41a/task1/evidence.txt && echo "✅ 41a task1 evidence present" | tee -a "${TASKLOG}"
rg "labuser_41_chown:labgrp_41_chown|labuser_41_chown:nobody" /root/rhcsa_journal/lab-41a/task1/evidence.txt | tee -a "${TASKLOG}"

echo "== Audit 41a task2 evidence ==" | tee -a "${TASKLOG}"
test -s /root/rhcsa_journal/lab-41a/task2/evidence.txt && echo "✅ 41a task2 evidence present" | tee -a "${TASKLOG}"
rg "root:root /tmp/lab41a/task2/template.ref|root:root /tmp/lab41a/task2/copy.ref|labuser_41_chown:labgrp_41_chown /tmp/lab41a/task2/tree" /root/rhcsa_journal/lab-41a/task2/evidence.txt | tee -a "${TASKLOG}" || true

echo "== Audit 41b evidence ==" | tee -a "${TASKLOG}"
test -s /root/rhcsa_journal/lab-41b/task1/evidence.txt && echo "✅ 41b task1 evidence present" | tee -a "${TASKLOG}"
test -s /root/rhcsa_journal/lab-41b/task2/evidence.txt && echo "✅ 41b task2 evidence present" | tee -a "${TASKLOG}"

echo "Canonical check reminder: prefer user:group (T41-A)." | tee -a "${TASKLOG}"
echo "Recursive/symlink check reminder: verify dereference intent (T41-B)." | tee -a "${TASKLOG}"
echo "exit was: $?"
```

### Journal write

```bash
cp /tmp/lab41c/task1/task1.txt /root/rhcsa_journal/lab-41c/task1/evidence.txt
cat > /root/rhcsa_journal/lab-41c/task1/done.txt <<EOF
LAB: lab-41c
TASK: task1
DATE: $(date -Is)
STATUS: COMPLETE
EOF
```

---

## Task 2 — Destroy-restore drill (T41)

### Purpose

Delete working ownership artifacts, then restore and re-verify from the journal pattern.

### Main command block

```bash
TASKLOG=/tmp/lab41c/task2/task2.txt

mkdir -p /tmp/lab41c/task2/restore/sub
touch /tmp/lab41c/task2/restore/sub/file.txt /tmp/lab41c/task2/reference.txt /tmp/lab41c/task2/target.txt
chown root:root /tmp/lab41c/task2/reference.txt /tmp/lab41c/task2/target.txt

echo "pre-destroy snapshot" | tee "${TASKLOG}"
stat -c '%U:%G %n' /tmp/lab41c/task2/reference.txt /tmp/lab41c/task2/target.txt /tmp/lab41c/task2/restore/sub/file.txt | tee -a "${TASKLOG}"

# Destroy phase
rm -rf /tmp/lab41c/task2/restore
echo "destroy complete" | tee -a "${TASKLOG}"

# Restore phase
mkdir -p /tmp/lab41c/task2/restore/sub
touch /tmp/lab41c/task2/restore/sub/file.txt
chown -R "${USER}:${GROUP}" /tmp/lab41c/task2/restore
chown --reference=/tmp/lab41c/task2/reference.txt /tmp/lab41c/task2/target.txt

echo "post-restore snapshot" | tee -a "${TASKLOG}"
stat -c '%U:%G %n' /tmp/lab41c/task2/reference.txt /tmp/lab41c/task2/target.txt /tmp/lab41c/task2/restore/sub/file.txt | tee -a "${TASKLOG}"
echo "✅ destroy-restore ownership drill complete (T41)" | tee -a "${TASKLOG}"
echo "exit was: $?"
```

### Journal write

```bash
cp /tmp/lab41c/task2/task2.txt /root/rhcsa_journal/lab-41c/task2/evidence.txt
cat > /root/rhcsa_journal/lab-41c/task2/done.txt <<EOF
LAB: lab-41c
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

echo "── Lab 41c cleanup audit ──"
getent passwd "${USER}" >/dev/null && echo "❌ user remains" || echo "✅ user gone"
getent group "${GROUP}" >/dev/null && echo "❌ group remains" || echo "✅ group gone"
test -d "${SANDBOX}" && echo "❌ sandbox remains" || echo "✅ sandbox gone"
test -d "${USER_HOME}" && echo "❌ home remains" || echo "✅ home gone"
set -e
```

---

## Author

**Kelvin R. Tobias**
