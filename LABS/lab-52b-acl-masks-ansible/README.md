# Lab 52b: ACL Masks (Ansible) — `ansible.posix.acl` with `etype: mask`

- **Series:** linux-ops-mastery — Files, Permissions, and Identity
- **Trilogy:** [`52a`](../lab-52a-acl-masks-rhcsa/) (RHCSA) → **`52b`** (Ansible) → [`52c`](../lab-52c-acl-masks-verify/) (Verify)
- **Time Estimate:** 30-40 minutes
- **Tasks:** 2
- **Practice Directory (objective context):** `/run` (inspection context), `/tmp/lab52b` (write target)
- **Playbooks:** `/root/rhcsa_journal/lab-52b/playbooks`
- **Sandbox (Tier B):** `/tmp/lab52b` with `USER=labuser_52_aclmask`, `GROUP=labgrp_52_aclmask`
- **Traps rehearsed:** **T52-A** (mask auto-recalc unless intentionally preserved) · **T52-B** (effective ACL rights capped by mask) · **T41** (destroy-restore drill in 52c) · **T44** (cleanup audit)

> **Module focus:** this lab uses `ansible.posix.acl` to make mask management declarative and auditable.

---

## LAB HEADER BLOCK

```bash
echo "📁 PRACTICE DIR: /run (inspect), /tmp/lab52b (write)"
ansible --version
ansible localhost -m ping --connection=local -i 'localhost,'
echo "🕒 TIME: $(date -Is)"
echo "⚠️ TRAPS: T52-A T52-B T41 T44"
id
```

---

## Objective

Use Ansible to enforce ACL mask behavior reliably:

1. Apply named-user ACL entries and a mask entry via `ansible.posix.acl`.
2. Assert `getfacl` output proves effective permissions are capped by mask.
3. Keep trap checks explicit so CI/test output catches ACL drift.

---

## Lab-Wide Setup

```bash
sudo -i

export SANDBOX=/tmp/lab52b
export GROUP=labgrp_52_aclmask
export USER=labuser_52_aclmask
export USER_HOME=${SANDBOX}/home_${USER}

mkdir -p "${SANDBOX}/task1" "${SANDBOX}/task2" "${USER_HOME}"
mkdir -p /root/rhcsa_journal/lab-52b/playbooks
mkdir -p /root/rhcsa_journal/lab-52b/task1
mkdir -p /root/rhcsa_journal/lab-52b/task2

getent group "${GROUP}" >/dev/null || groupadd "${GROUP}"
getent passwd "${USER}" >/dev/null || useradd -d "${USER_HOME}" -M -s /bin/bash -g "${GROUP}" "${USER}"

touch "${SANDBOX}/task1/mask_ansible.txt" "${SANDBOX}/task2/mask_assert.txt"
chown root:root "${SANDBOX}/task1/mask_ansible.txt" "${SANDBOX}/task2/mask_assert.txt"
chmod 0640 "${SANDBOX}/task1/mask_ansible.txt" "${SANDBOX}/task2/mask_assert.txt"
```

---

## Task 1 — Apply ACL mask declaratively (`etype: mask`)

### Purpose

Set a named-user ACL and then set the ACL mask to `rw` using `ansible.posix.acl`.

### Main command block

```bash
PB=/root/rhcsa_journal/lab-52b/playbooks/task1.yml
TASKLOG=/tmp/lab52b/task1/task1.txt

cat > "${PB}" <<'PLAYBOOK'
---
- name: "Lab 52b Task 1 - apply ACL mask"
  hosts: localhost
  connection: local
  gather_facts: false
  vars:
    target_file: /tmp/lab52b/task1/mask_ansible.txt
    target_user: labuser_52_aclmask
  tasks:
    - name: Ensure named user ACL requests rwx
      ansible.posix.acl:
        path: "{{ target_file }}"
        etype: user
        entity: "{{ target_user }}"
        permissions: rwx
        state: present

    - name: Set ACL mask to rw (effective maximum)
      ansible.posix.acl:
        path: "{{ target_file }}"
        etype: mask
        permissions: rw
        state: present

    - name: Capture ACL output
      ansible.builtin.command: "getfacl {{ target_file }}"
      register: facl_out
      changed_when: false

    - name: Print ACL output
      ansible.builtin.debug:
        var: facl_out.stdout_lines
PLAYBOOK

ansible-playbook -i 'localhost,' "${PB}" 2>&1 | tee "${TASKLOG}"
echo "exit was: $?"
```

### Journal write

```bash
cp /tmp/lab52b/task1/task1.txt /root/rhcsa_journal/lab-52b/task1/evidence.txt
cat > /root/rhcsa_journal/lab-52b/task1/done.txt <<EOF
LAB: lab-52b
TASK: task1
DATE: $(date -Is)
STATUS: COMPLETE
EOF
```

---

## Task 2 — Trap assertion: effective rights reflect mask cap (T52-A/T52-B)

### Purpose

Assert that a named user requesting `rwx` is effectively capped to `rw-` when mask is `rw`.

### Main command block

```bash
PB=/root/rhcsa_journal/lab-52b/playbooks/task2.yml
TASKLOG=/tmp/lab52b/task2/task2.txt

cat > "${PB}" <<'PLAYBOOK'
---
- name: "Lab 52b Task 2 - assert effective mask cap"
  hosts: localhost
  connection: local
  gather_facts: false
  vars:
    target_file: /tmp/lab52b/task2/mask_assert.txt
    target_user: labuser_52_aclmask
  tasks:
    - name: Reset ACL baseline
      ansible.builtin.command: "setfacl -b {{ target_file }}"
      changed_when: false

    - name: Set named user ACL to rwx
      ansible.posix.acl:
        path: "{{ target_file }}"
        etype: user
        entity: "{{ target_user }}"
        permissions: rwx
        state: present

    - name: Cap mask to rw
      ansible.posix.acl:
        path: "{{ target_file }}"
        etype: mask
        permissions: rw
        state: present

    - name: Read ACL text
      ansible.builtin.command: "getfacl {{ target_file }}"
      register: facl_read
      changed_when: false

    - name: Assert mask line exists and effective cap is visible
      ansible.builtin.assert:
        that:
          - "'mask::rw-' in facl_read.stdout"
          - "'#effective:rw-' in facl_read.stdout"
        fail_msg: "T52-B failed: named entry was not effectively capped by mask."
        success_msg: "T52-B passed: effective rights are capped by mask."

    - name: Print trap reminder
      ansible.builtin.debug:
        msg: "T52-A reminder: each ACL change can recalculate mask unless preservation is intentional."
PLAYBOOK

ansible-playbook -i 'localhost,' "${PB}" 2>&1 | tee "${TASKLOG}"
echo "exit was: $?"
```

### Journal write

```bash
cp /tmp/lab52b/task2/task2.txt /root/rhcsa_journal/lab-52b/task2/evidence.txt
cat > /root/rhcsa_journal/lab-52b/task2/done.txt <<EOF
LAB: lab-52b
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

echo "── Lab 52b cleanup audit ──"
getent passwd "${USER}" >/dev/null && echo "❌ user remains" || echo "✅ user gone"
getent group "${GROUP}" >/dev/null && echo "❌ group remains" || echo "✅ group gone"
test -d "${SANDBOX}" && echo "❌ sandbox remains" || echo "✅ sandbox gone"
test -d "${USER_HOME}" && echo "❌ home remains" || echo "✅ home gone"
set -e
```

---

## Author

**Kelvin R. Tobias**
