# Lab 49c: Verifying ACL Modifications — audit + destroy/restore

- **Series:** linux-ops-mastery — Permissions, Special Bits & ACLs
- **Trilogy:** [`49a`](../lab-49a-setfacl-modify-rhcsa/) (RHCSA) -> [`49b`](../lab-49b-setfacl-modify-ansible/) (Ansible) -> **`49c`** (Verify)
- **Time Estimate:** 25-35 minutes
- **Tasks:** 2 (Task 1 = ACL audit, Task 2 = destroy-restore drill)
- **Practice Directory (rotation slot 1):** `/dev` (inspection), `/tmp/lab49c` (write target)
- **Sandbox (Tier B):** `/tmp/lab49c` with `USER=labuser_49_setfacl`, `GROUP=labgrp_49_setfacl`
- **Traps rehearsed this lab:** **T49-A** · **T49-B** · **T41** · **T44**

> **Verify role:** you are the auditor. Prove ACL state, prove effective permissions, then prove recovery.

---

## LAB HEADER BLOCK

```bash
echo "🖥️  ENV: ${ENV:-DECLARE_ME}"
echo "🕒  TIME: $(date -Is)"
echo "👤  USER: $(whoami)@$(hostname)"
echo "📁  PRACTICE DIR: /dev (inspect), /tmp/lab49c (write)"
echo "⚠️  TRAP REMINDERS THIS LAB: T49-A T49-B T41 T44"
getfacl --version
id
```

---

## Objective

1. Audit ACL state and evidence quality in the journal.
2. Prove recovery using destroy-restore: clear ACLs with `setfacl -b`, then re-apply from playbook.

---

## Lab-Wide Setup — Tier B Sandbox

```bash
sudo -i

export SANDBOX=/tmp/lab49c
export GROUP=labgrp_49_setfacl
export USER=labuser_49_setfacl
export USER_HOME=${SANDBOX}/home_${USER}

mkdir -p "${SANDBOX}/task1" "${SANDBOX}/task2/tree/sub" "${USER_HOME}"
mkdir -p /root/rhcsa_journal/lab-49c/task1 /root/rhcsa_journal/lab-49c/task2
mkdir -p /root/rhcsa_journal/lab-49c/playbooks

getent group "${GROUP}" >/dev/null || groupadd "${GROUP}"
getent passwd "${USER}" >/dev/null || useradd -d "${USER_HOME}" -M -s /bin/bash -g "${GROUP}" "${USER}"

echo "verify me" > "${SANDBOX}/task1/file"
chmod 600 "${SANDBOX}/task1/file"
chown root:root "${SANDBOX}/task1/file"
touch "${SANDBOX}/task2/tree/root.txt" "${SANDBOX}/task2/tree/sub/leaf.txt"
chmod -R 640 "${SANDBOX}/task2/tree"
chown -R root:root "${SANDBOX}/task2/tree"

# Seed ACL state that Task 1 audits
setfacl -m "u:${USER}:rw" "${SANDBOX}/task1/file"
setfacl -R -m "g:${GROUP}:rx" "${SANDBOX}/task2/tree"
setfacl -m "u:${USER}:rwx" "${SANDBOX}/task2/tree/root.txt"
setfacl -m "m::rw-" "${SANDBOX}/task2/tree/root.txt"
```

---

## Task 1 — Audit ACLs and write journal evidence

### Purpose

Capture journal-grade evidence for ACL entries, effective rights, and runtime access behavior.

### Main command block

```bash
TASKLOG=/tmp/lab49c/task1/task1.txt

echo "== audit target file ACL ==" | tee "${TASKLOG}"
getfacl /tmp/lab49c/task1/file | tee -a "${TASKLOG}"

echo "== audit tree ACLs ==" | tee -a "${TASKLOG}"
getfacl -R /tmp/lab49c/task2/tree | tee -a "${TASKLOG}"

echo "== runtime checks ==" | tee -a "${TASKLOG}"
sudo -u "${USER}" cat /tmp/lab49c/task1/file 2>&1 | tee -a "${TASKLOG}"
sudo -u "${USER}" test -x /tmp/lab49c/task2/tree/root.txt && echo "exec: yes" | tee -a "${TASKLOG}" || echo "exec: no (mask capped)" | tee -a "${TASKLOG}"

echo "== trap notes ==" | tee -a "${TASKLOG}"
echo "T49-A: mask may cap effective permission below requested ACL bits." | tee -a "${TASKLOG}"
echo "T49-B: recursive ACL operations should target directory trees." | tee -a "${TASKLOG}"
echo "exit was: $?"
```

### Journal write

```bash
cp /tmp/lab49c/task1/task1.txt /root/rhcsa_journal/lab-49c/task1/audit-acl.txt
```

---

## Task 2 — Destroy-restore drill (`setfacl -b` then re-apply playbook)

### Purpose

Practice full lifecycle confidence: remove ACLs, prove absence, re-apply declarative ACL state.

### Main command block

```bash
PB=/root/rhcsa_journal/lab-49c/playbooks/restore.yml
TASKLOG=/tmp/lab49c/task2/task2.txt

cat > "${PB}" <<'PLAYBOOK'
---
- name: "Lab 49c Task 2 - restore ACL state"
  hosts: localhost
  connection: local
  gather_facts: false
  vars:
    target_user: labuser_49_setfacl
    target_group: labgrp_49_setfacl
  tasks:
    - name: Restore user ACL on task1 file
      ansible.posix.acl:
        path: /tmp/lab49c/task1/file
        entity: "{{ target_user }}"
        etype: user
        permissions: rw
        state: present

    - name: Restore recursive group ACL on tree
      ansible.posix.acl:
        path: /tmp/lab49c/task2/tree
        entity: "{{ target_group }}"
        etype: group
        permissions: rx
        recursive: true
        state: present

    - name: Restore user ACL on root.txt
      ansible.posix.acl:
        path: /tmp/lab49c/task2/tree/root.txt
        entity: "{{ target_user }}"
        etype: user
        permissions: rwx
        state: present

    - name: Restore mask cap
      ansible.posix.acl:
        path: /tmp/lab49c/task2/tree/root.txt
        etype: mask
        permissions: rw
        state: present
PLAYBOOK

echo "== destroy phase ==" | tee "${TASKLOG}"
setfacl -b /tmp/lab49c/task1/file
setfacl -R -b /tmp/lab49c/task2/tree
getfacl /tmp/lab49c/task1/file | tee -a "${TASKLOG}"
getfacl -R /tmp/lab49c/task2/tree | tee -a "${TASKLOG}"

echo "== restore phase ==" | tee -a "${TASKLOG}"
ansible-playbook -i 'localhost,' "${PB}" 2>&1 | tee -a "${TASKLOG}"
getfacl /tmp/lab49c/task1/file | tee -a "${TASKLOG}"
getfacl -R /tmp/lab49c/task2/tree | tee -a "${TASKLOG}"
echo "exit was: $?"
```

### Journal write

```bash
cp /tmp/lab49c/task2/task2.txt /root/rhcsa_journal/lab-49c/task2/destroy-restore.txt
```

---

## Lab Closeout — Bulletproof Teardown (Section 6)

```bash
set +e
userdel -r "${USER}" 2>/dev/null
groupdel "${GROUP}" 2>/dev/null
rm -rf "${SANDBOX}"

echo "── Lab 49c cleanup audit ──"
getent passwd "${USER}" >/dev/null && echo "❌ user remains" || echo "✅ user gone"
getent group "${GROUP}" >/dev/null && echo "❌ group remains" || echo "✅ group gone"
test -d "${SANDBOX}" && echo "❌ sandbox remains" || echo "✅ sandbox gone"
test -d "${USER_HOME}" && echo "❌ home remains" || echo "✅ home gone"

set -e
```

---

## Author

**Kelvin R. Tobias**
