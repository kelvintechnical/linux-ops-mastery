# Lab 41b: Changing Ownership (Ansible) — `ansible.builtin.file` owner/group

- **Series:** linux-ops-mastery — Files, Permissions, and Identity
- **Trilogy:** [`41a`](../lab-41a-chown-chgrp-ownership-rhcsa/) (RHCSA) → **`41b`** (Ansible) → [`41c`](../lab-41c-chown-chgrp-ownership-verify/) (Verify)
- **Time Estimate:** 30-40 minutes
- **Tasks:** 2
- **Practice Directory (objective context):** `/etc` (inspection only)
- **Playbooks:** `/root/rhcsa_journal/lab-41b/playbooks`
- **Sandbox (Tier B):** `/tmp/lab41b` with `USER=labuser_41_chown`, `GROUP=labgrp_41_chown`
- **Traps rehearsed:** **T41-A** (prefer canonical owner/group expression, avoid legacy habits) · **T41-B** (recursive ownership and symlink behavior must be deliberate) · **T41** (destroy-restore drill validated in 41c) · **T44** (cleanup audit)

> **Variable warning:** `USER=labuser_41_chown` is a sandbox variable. In Ansible, ownership is declared with `owner:` and `group:` fields.

---

## LAB HEADER BLOCK

```bash
echo "📁 PRACTICE DIR: /etc (inspect), /tmp/lab41b (write)"
ansible --version
ansible localhost -m ping --connection=local -i 'localhost,'
id
echo "⚠️ TRAPS: T41-A T41-B T41 T44"
```

---

## Objective

Express ownership declaratively with Ansible and prove idempotent convergence:

1. Use `ansible.builtin.file` with `owner:` and `group:` to set file ownership.
2. Use `recurse: yes` on a directory tree.
3. Assert resulting owners with `stat` + `assert` so failures are explicit.

---

## Lab-Wide Setup

```bash
sudo -i

export SANDBOX=/tmp/lab41b
export GROUP=labgrp_41_chown
export USER=labuser_41_chown
export USER_HOME=${SANDBOX}/home_${USER}

mkdir -p "${SANDBOX}" "${USER_HOME}" "${SANDBOX}/task1" "${SANDBOX}/task2/tree/sub"
mkdir -p /root/rhcsa_journal/lab-41b/playbooks
mkdir -p /root/rhcsa_journal/lab-41b/task1
mkdir -p /root/rhcsa_journal/lab-41b/task2

getent group "${GROUP}" >/dev/null || groupadd "${GROUP}"
getent passwd "${USER}" >/dev/null || useradd -d "${USER_HOME}" -M -s /bin/bash -g "${GROUP}" "${USER}"

touch "${SANDBOX}/task1/a.txt" "${SANDBOX}/task1/b.txt"
touch "${SANDBOX}/task2/tree/root.txt" "${SANDBOX}/task2/tree/sub/leaf.txt"
chown -R root:root "${SANDBOX}"
```

---

## Task 1 — Declarative `owner:` / `group:` with `ansible.builtin.file`

### Main command block

```bash
PB=/root/rhcsa_journal/lab-41b/playbooks/task1.yml
TASKLOG=/tmp/lab41b/task1/task1.txt

cat > "${PB}" <<'PLAYBOOK'
---
- name: "Lab 41b Task 1 - declarative ownership"
  hosts: localhost
  connection: local
  gather_facts: false
  vars:
    target_user: labuser_41_chown
    target_group: labgrp_41_chown
  tasks:
    - name: Set ownership on files
      ansible.builtin.file:
        path: "{{ item }}"
        state: file
        owner: "{{ target_user }}"
        group: "{{ target_group }}"
      loop:
        - /tmp/lab41b/task1/a.txt
        - /tmp/lab41b/task1/b.txt

    - name: Collect ownership
      ansible.builtin.stat:
        path: "{{ item }}"
      loop:
        - /tmp/lab41b/task1/a.txt
        - /tmp/lab41b/task1/b.txt
      register: st

    - name: Assert ownership is correct
      ansible.builtin.assert:
        that:
          - item.stat.pw_name == target_user
          - item.stat.gr_name == target_group
      loop: "{{ st.results }}"
PLAYBOOK

ansible-playbook -i 'localhost,' "${PB}" 2>&1 | tee "${TASKLOG}"
echo "exit was: $?"
```

### Journal write

```bash
cp /tmp/lab41b/task1/task1.txt /root/rhcsa_journal/lab-41b/task1/evidence.txt
cat > /root/rhcsa_journal/lab-41b/task1/done.txt <<EOF
LAB: lab-41b
TASK: task1
DATE: $(date -Is)
STATUS: COMPLETE
EOF
```

---

## Task 2 — Recursive ownership with `recurse: yes` + asserts

### Main command block

```bash
PB=/root/rhcsa_journal/lab-41b/playbooks/task2.yml
TASKLOG=/tmp/lab41b/task2/task2.txt

cat > "${PB}" <<'PLAYBOOK'
---
- name: "Lab 41b Task 2 - recursive ownership"
  hosts: localhost
  connection: local
  gather_facts: false
  vars:
    target_user: labuser_41_chown
    target_group: labgrp_41_chown
    target_tree: /tmp/lab41b/task2/tree
  tasks:
    - name: Apply recursive ownership on subtree
      ansible.builtin.file:
        path: "{{ target_tree }}"
        owner: "{{ target_user }}"
        group: "{{ target_group }}"
        recurse: yes

    - name: Gather stats for subtree files
      ansible.builtin.stat:
        path: "{{ item }}"
      loop:
        - /tmp/lab41b/task2/tree/root.txt
        - /tmp/lab41b/task2/tree/sub/leaf.txt
      register: subtree_stats

    - name: Assert subtree ownership
      ansible.builtin.assert:
        that:
          - item.stat.pw_name == target_user
          - item.stat.gr_name == target_group
      loop: "{{ subtree_stats.results }}"
PLAYBOOK

ansible-playbook -i 'localhost,' "${PB}" 2>&1 | tee "${TASKLOG}"
stat -c '%U:%G %n' /tmp/lab41b/task2/tree/root.txt /tmp/lab41b/task2/tree/sub/leaf.txt | tee -a "${TASKLOG}"
echo "T41-B reminder: recurse behavior around symlinks must be intentional." | tee -a "${TASKLOG}"
echo "exit was: $?"
```

### Journal write

```bash
cp /tmp/lab41b/task2/task2.txt /root/rhcsa_journal/lab-41b/task2/evidence.txt
cat > /root/rhcsa_journal/lab-41b/task2/done.txt <<EOF
LAB: lab-41b
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

echo "── Lab 41b cleanup audit ──"
getent passwd "${USER}" >/dev/null && echo "❌ user remains" || echo "✅ user gone"
getent group "${GROUP}" >/dev/null && echo "❌ group remains" || echo "✅ group gone"
test -d "${SANDBOX}" && echo "❌ sandbox remains" || echo "✅ sandbox gone"
test -d "${USER_HOME}" && echo "❌ home remains" || echo "✅ home gone"
set -e
```

---

## Author

**Kelvin R. Tobias**
