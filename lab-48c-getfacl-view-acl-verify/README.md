# Lab 48c: Verifying ACL Views — audit + destroy/restore

- **Series:** linux-ops-mastery — Permissions, Special Bits, and ACLs
- **Trilogy:** `48a` (RHCSA) → `48b` (Ansible) → **`48c` (Verify — you are here)**
- **Time Estimate:** 20-30 minutes
- **Tasks:** 2
- **Practice Directory (objective context):** `/srv` (audit context), `/tmp/lab48c` (verify sandbox)
- **Sandbox (Tier B):** `/tmp/lab48c` with `USER=labuser_48_getfacl`, `GROUP=labgrp_48_getfacl`
- **Traps rehearsed:** **T48-A** (`ls -l` `+` marker interpretation) · **T48-B** (single-level vs recursive ACL query) · **T41** (destroy-restore drill is mandatory here) · **T44** (cleanup audit)

---

## LAB HEADER BLOCK

```bash
echo "📁 PRACTICE DIR: /srv (read), /tmp/lab48c (write)"
echo "👤 USER: $(whoami)@$(hostname)"
echo "🕒 TIME: $(date -Is)"
echo "⚠️ TRAPS: T48-A T48-B T41 T44"
test -f /root/rhcsa_journal/lab-48a/task2/done.txt && echo "lab-48a done"
test -f /root/rhcsa_journal/lab-48b/task2/done.txt && echo "lab-48b done"
```

> **STOP — if prior trilogy parts are missing, finish them first.**

---

## Objective

Verify ACL state as an auditor:

1. Capture `getfacl` evidence into journal artifacts.
2. Rehearse the destroy-restore ACL drill (`setfacl -b` then restore by playbook).
3. Prove restored ACL entries match expected output.

---

## Lab-Wide Setup — Tier B Sandbox

```bash
sudo -i

export LAB_NUM=48
export LAB_SLUG=getfacl
export SANDBOX=/tmp/lab48c
export GROUP=labgrp_48_getfacl
export USER=labuser_48_getfacl
export USER_HOME=${SANDBOX}/home_${USER}

mkdir -p "${SANDBOX}/task1" "${SANDBOX}/task2" "${USER_HOME}"
mkdir -p /root/rhcsa_journal/lab-48c/task1
mkdir -p /root/rhcsa_journal/lab-48c/task2
mkdir -p /root/rhcsa_journal/lab-48c/playbooks

getent group "${GROUP}" >/dev/null || groupadd "${GROUP}"
getent passwd "${USER}" >/dev/null || useradd -d "${USER_HOME}" -M -s /bin/bash -g "${GROUP}" "${USER}"
chown -R "${USER}:${GROUP}" "${SANDBOX}"

touch /tmp/lab48c/verify-file
setfacl -m u:${USER}:rw /tmp/lab48c/verify-file
```

---

## Task 1 — Audit ACL output and persist in journal

### Purpose

Capture human- and machine-readable ACL evidence for later comparison.

### Main command block

```bash
TASKLOG=/tmp/lab48c/task1/task1.txt

echo "== single target ACL ==" | tee "${TASKLOG}"
getfacl --absolute-names /tmp/lab48c/verify-file | tee -a "${TASKLOG}"

echo "== recursive ACL audit ==" | tee -a "${TASKLOG}"
getfacl -R /tmp/lab48c | tee -a "${TASKLOG}"

echo "== ls marker audit ==" | tee -a "${TASKLOG}"
ls -l /tmp/lab48c /tmp/lab48c/verify-file | tee -a "${TASKLOG}"
echo "exit was: $?"
```

### Expected checks

- Output contains `user:${USER}:rw-` line.
- Recursive output includes both directory and file ACL blocks.
- `ls -l` shows `+` marker on ACL-bearing inode(s).

### Journal write

```bash
cp /tmp/lab48c/task1/task1.txt /root/rhcsa_journal/lab-48c/task1/evidence.txt
cat > /root/rhcsa_journal/lab-48c/task1/done.txt <<EOF
LAB: lab-48c
TASK: task1
DATE: $(date -Is)
STATUS: COMPLETE
EOF
```

---

## Task 2 — Destroy-restore drill (`setfacl -b` then restore playbook)

### Purpose

Practice the required T41-style recovery flow: intentionally clear ACLs, then restore and verify.

### Main command block

```bash
TASKLOG=/tmp/lab48c/task2/task2.txt
PLAY=/root/rhcsa_journal/lab-48c/playbooks/task2-restore.yml

echo "== pre-destroy ACL ==" | tee "${TASKLOG}"
getfacl /tmp/lab48c/verify-file | tee -a "${TASKLOG}"

echo "== destroy ACL with setfacl -b ==" | tee -a "${TASKLOG}"
setfacl -b /tmp/lab48c/verify-file
getfacl /tmp/lab48c/verify-file | tee -a "${TASKLOG}"
ls -l /tmp/lab48c/verify-file | tee -a "${TASKLOG}"

cat > "${PLAY}" <<'EOF'
---
- name: Lab 48c Task 2 - restore ACL after destroy drill
  hosts: localhost
  connection: local
  gather_facts: false
  vars:
    acl_path: /tmp/lab48c/verify-file
    acl_user: labuser_48_getfacl
  tasks:
    - name: Restore user ACL entry
      ansible.posix.acl:
        path: "{{ acl_path }}"
        etype: user
        entity: "{{ acl_user }}"
        permissions: rw
        state: present

    - name: Verify restored ACL text
      ansible.builtin.shell: getfacl --absolute-names {{ acl_path }}
      register: acl_after
      changed_when: false

    - name: Assert restored ACL entry exists
      ansible.builtin.assert:
        that:
          - "'user:' ~ acl_user ~ ':rw-' in acl_after.stdout"
EOF

echo "== restore via playbook ==" | tee -a "${TASKLOG}"
ansible-playbook "${PLAY}" 2>&1 | tee -a "${TASKLOG}"

echo "== post-restore ACL ==" | tee -a "${TASKLOG}"
getfacl /tmp/lab48c/verify-file | tee -a "${TASKLOG}"
ls -l /tmp/lab48c/verify-file | tee -a "${TASKLOG}"
echo "exit was: $?"
```

### Expected checks

- After `setfacl -b`, `user:${USER}` entry is absent and `+` marker may disappear.
- After restore playbook, `user:${USER}:rw-` returns and `+` marker returns.

### Journal write

```bash
cp /tmp/lab48c/task2/task2.txt /root/rhcsa_journal/lab-48c/task2/evidence.txt
cat > /root/rhcsa_journal/lab-48c/task2/done.txt <<EOF
LAB: lab-48c
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

echo "── Lab 48c cleanup audit ──"
getent passwd "${USER}" >/dev/null && echo "❌ user remains" || echo "✅ user gone"
getent group "${GROUP}" >/dev/null && echo "❌ group remains" || echo "✅ group gone"
test -d "${SANDBOX}" && echo "❌ sandbox remains" || echo "✅ sandbox gone"
test -d "${USER_HOME}" && echo "❌ home remains" || echo "✅ home gone"
set -e
```

---

## Author

**Kelvin R. Tobias**
