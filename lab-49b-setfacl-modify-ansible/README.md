# Lab 49b: Modifying ACLs (Ansible) — `ansible.posix.acl` declarative ACL control

- **Series:** linux-ops-mastery — Permissions, Special Bits & ACLs
- **Trilogy:** [`49a`](../lab-49a-setfacl-modify-rhcsa/) (RHCSA) -> **`49b`** (Ansible) -> [`49c`](../lab-49c-setfacl-modify-verify/) (Verify)
- **Time Estimate:** 30-40 minutes
- **Tasks:** 2
- **Practice Directory (objective context):** `/dev` (inspection), `/tmp/lab49b` (write target)
- **Playbooks:** `/root/rhcsa_journal/lab-49b/playbooks`
- **Sandbox (Tier B):** `/tmp/lab49b` with `USER=labuser_49_setfacl`, `GROUP=labgrp_49_setfacl`
- **Traps rehearsed:** **T49-A** (mask caps effective perms) · **T49-B** (recursive ACL intent belongs on directories) · **T41** (destroy-restore validated in 49c) · **T44** (cleanup audit)

> **Ansible note:** use `ansible.posix.acl` with `entity:`, `etype:`, and `permissions:` for declarative ACL state.

---

## LAB HEADER BLOCK

```bash
echo "📁 PRACTICE DIR: /dev (inspect), /tmp/lab49b (write)"
ansible --version
ansible localhost -m ping --connection=local -i 'localhost,'
echo "👤 USER: $(whoami)@$(hostname)"
echo "⚠️ TRAPS: T49-A T49-B T41 T44"
```

---

## Objective

Use Ansible to manage ACLs predictably:

1. Set user/group ACL entries declaratively with `ansible.posix.acl`.
2. Apply recursive ACL policy on a directory tree.
3. Assert effective permissions after mask changes.

---

## Lab-Wide Setup

```bash
sudo -i

export SANDBOX=/tmp/lab49b
export GROUP=labgrp_49_setfacl
export USER=labuser_49_setfacl
export USER_HOME=${SANDBOX}/home_${USER}

mkdir -p "${SANDBOX}/task1" "${SANDBOX}/task2/tree/sub" "${USER_HOME}"
mkdir -p /root/rhcsa_journal/lab-49b/playbooks
mkdir -p /root/rhcsa_journal/lab-49b/task1
mkdir -p /root/rhcsa_journal/lab-49b/task2

getent group "${GROUP}" >/dev/null || groupadd "${GROUP}"
getent passwd "${USER}" >/dev/null || useradd -d "${USER_HOME}" -M -s /bin/bash -g "${GROUP}" "${USER}"

echo "acl baseline" > "${SANDBOX}/task1/file"
chmod 600 "${SANDBOX}/task1/file"
chown root:root "${SANDBOX}/task1/file"

touch "${SANDBOX}/task2/tree/root.txt" "${SANDBOX}/task2/tree/sub/leaf.txt"
chmod -R 640 "${SANDBOX}/task2/tree"
chown -R root:root "${SANDBOX}/task2/tree"
```

---

## Task 1 — Declarative ACL set with `ansible.posix.acl`

### Purpose

Set user and group ACL entries with module fields `entity`, `etype`, and `permissions`.

### Main command block

```bash
PB=/root/rhcsa_journal/lab-49b/playbooks/task1.yml
TASKLOG=/tmp/lab49b/task1/task1.txt

cat > "${PB}" <<'PLAYBOOK'
---
- name: "Lab 49b Task 1 - declarative ACL set"
  hosts: localhost
  connection: local
  gather_facts: false
  vars:
    target_user: labuser_49_setfacl
    target_group: labgrp_49_setfacl
    target_file: /tmp/lab49b/task1/file
  tasks:
    - name: Set user ACL to rw
      ansible.posix.acl:
        path: "{{ target_file }}"
        entity: "{{ target_user }}"
        etype: user
        permissions: rw
        state: present

    - name: Set group ACL to rx
      ansible.posix.acl:
        path: "{{ target_file }}"
        entity: "{{ target_group }}"
        etype: group
        permissions: rx
        state: present

    - name: Ensure ACL mask allows rwx max
      ansible.posix.acl:
        path: "{{ target_file }}"
        etype: mask
        permissions: rwx
        state: present
PLAYBOOK

ansible-playbook -i 'localhost,' "${PB}" 2>&1 | tee "${TASKLOG}"
getfacl /tmp/lab49b/task1/file | tee -a "${TASKLOG}"
sudo -u "${USER}" cat /tmp/lab49b/task1/file 2>&1 | tee -a "${TASKLOG}"
echo "exit was: $?"
```

### Journal write

```bash
cp /tmp/lab49b/task1/task1.txt /root/rhcsa_journal/lab-49b/task1/evidence.txt
cat > /root/rhcsa_journal/lab-49b/task1/done.txt <<EOF
LAB: lab-49b
TASK: task1
DATE: $(date -Is)
STATUS: COMPLETE
EOF
```

---

## Task 2 — Recursive ACL policy + post-mask effective permission assert

### Purpose

Apply ACLs recursively and assert effective permissions match mask-capped expectation.

### Main command block

```bash
PB=/root/rhcsa_journal/lab-49b/playbooks/task2.yml
TASKLOG=/tmp/lab49b/task2/task2.txt

cat > "${PB}" <<'PLAYBOOK'
---
- name: "Lab 49b Task 2 - recursive ACL and mask assert"
  hosts: localhost
  connection: local
  gather_facts: false
  vars:
    target_user: labuser_49_setfacl
    target_group: labgrp_49_setfacl
    target_tree: /tmp/lab49b/task2/tree
    target_file: /tmp/lab49b/task2/tree/root.txt
  tasks:
    - name: Recursive group ACL on tree
      ansible.posix.acl:
        path: "{{ target_tree }}"
        entity: "{{ target_group }}"
        etype: group
        permissions: rx
        recursive: true
        state: present

    - name: Set user ACL to rwx (requested)
      ansible.posix.acl:
        path: "{{ target_file }}"
        entity: "{{ target_user }}"
        etype: user
        permissions: rwx
        state: present

    - name: Cap mask to rw (T49-A)
      ansible.posix.acl:
        path: "{{ target_file }}"
        etype: mask
        permissions: rw
        state: present

    - name: Read ACL text for assertions
      ansible.builtin.command: "getfacl -p {{ target_file }}"
      register: facl
      changed_when: false

    - name: Assert effective permission is mask-capped
      ansible.builtin.assert:
        that:
          - "'mask::rw-' in facl.stdout"
          - "'user:' ~ target_user ~ ':rwx\\t#effective:rw-' in facl.stdout or 'user:' ~ target_user ~ ':rwx #effective:rw-' in facl.stdout"
PLAYBOOK

ansible-playbook -i 'localhost,' "${PB}" 2>&1 | tee "${TASKLOG}"
getfacl -R /tmp/lab49b/task2/tree | tee -a "${TASKLOG}"
echo "T49-B reminder: recursive ACL operations are intended for directory trees." | tee -a "${TASKLOG}"
echo "exit was: $?"
```

### Journal write

```bash
cp /tmp/lab49b/task2/task2.txt /root/rhcsa_journal/lab-49b/task2/evidence.txt
cat > /root/rhcsa_journal/lab-49b/task2/done.txt <<EOF
LAB: lab-49b
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

echo "── Lab 49b cleanup audit ──"
getent passwd "${USER}" >/dev/null && echo "❌ user remains" || echo "✅ user gone"
getent group "${GROUP}" >/dev/null && echo "❌ group remains" || echo "✅ group gone"
test -d "${SANDBOX}" && echo "❌ sandbox remains" || echo "✅ sandbox gone"
test -d "${USER_HOME}" && echo "❌ home remains" || echo "✅ home gone"
set -e
```

---

## Author

**Kelvin R. Tobias**
