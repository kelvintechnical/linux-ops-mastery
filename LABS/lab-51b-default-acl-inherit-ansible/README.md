# Lab 51b: Default Directory ACL Inheritance (Ansible) — `ansible.posix.acl` `default: yes`

- **Series:** linux-ops-mastery — ACLs and Permission Control
- **Trilogy:** [`51a`](../lab-51a-default-acl-inherit-rhcsa/) (RHCSA) -> **`51b`** (Ansible) -> [`51c`](../lab-51c-default-acl-inherit-verify/) (Verify capstone)
- **Time Estimate:** 25-35 minutes
- **Tasks:** 2
- **Practice Directory (rotation #51):** `/sys` (inspection context), writes happen in sandbox
- **Sandbox (Tier B):** `/tmp/lab51b` with `USER=labuser_51_dacl`, `GROUP=labgrp_51_dacl`
- **Playbooks live at:** `/root/rhcsa_journal/lab-51b/playbooks`
- **Traps rehearsed this lab:** **T51-A** · **T51-B** · **T41** · **T44**

> **Topic focus:** declare default directory ACL entries with `ansible.posix.acl` and prove inheritance on newly created child files.

---

## LAB HEADER BLOCK

```bash
echo "🕒  TIME:  $(date -Is)"
echo "👤  USER:  $(whoami)@$(hostname)"
echo "📁  PRACTICE DIR: /sys"
echo "⚠️  TRAP REMINDERS THIS LAB: T51-A T51-B T41 T44"
ls -ld /sys /tmp
ansible --version | head -n 2
ansible-galaxy collection list | rg '^ansible.posix'
```

---

## Objective

1. Use `ansible.posix.acl` with `default: yes` to declare directory default ACL state.
2. Create a fresh child file and assert inherited ACL entries are present.
3. Keep T51-A/T51-B behavior explicit in evidence.

---

## Lab-Wide Setup — Tier B Sandbox

```bash
sudo -i

export SANDBOX=/tmp/lab51b
export GROUP=labgrp_51_dacl
export USER=labuser_51_dacl
export USER_HOME=${SANDBOX}/home_${USER}

mkdir -p "${SANDBOX}" "${USER_HOME}" /root/rhcsa_journal/lab-51b/playbooks /root/rhcsa_journal/lab-51b/task1 /root/rhcsa_journal/lab-51b/task2
getent group "${GROUP}" >/dev/null || groupadd "${GROUP}"
getent passwd "${USER}" >/dev/null || useradd -d "${USER_HOME}" -M -s /bin/bash -g "${GROUP}" "${USER}"
chown -R "${USER}:${GROUP}" "${SANDBOX}"
```

---

## Task 1 — Declarative default ACL with `ansible.posix.acl`

### Purpose

Express default ACL inheritance policy as code (`default: yes`) on a target parent directory.

### Main command block

```bash
PB=/root/rhcsa_journal/lab-51b/playbooks/task1.yml
TASKLOG=/tmp/lab51b/task1.txt

cat > "${PB}" <<'PLAYBOOK'
---
- name: "Lab 51b Task 1 - default ACL declaration"
  hosts: localhost
  connection: local
  gather_facts: false
  vars:
    target_dir: /tmp/lab51b/parent
    target_user: labuser_51_dacl
    target_group: labgrp_51_dacl

  tasks:
    - name: Ensure parent directory exists
      ansible.builtin.file:
        path: "{{ target_dir }}"
        state: directory
        mode: "0770"

    - name: Declare default ACL for user
      ansible.posix.acl:
        path: "{{ target_dir }}"
        etype: user
        entity: "{{ target_user }}"
        permissions: rwx
        state: present
        default: true

    - name: Declare default ACL for group
      ansible.posix.acl:
        path: "{{ target_dir }}"
        etype: group
        entity: "{{ target_group }}"
        permissions: rx
        state: present
        default: true

    - name: Show parent ACL state
      ansible.builtin.command:
        cmd: getfacl {{ target_dir }}
      changed_when: false
      register: parent_acl

    - name: Print ACL evidence
      ansible.builtin.debug:
        var: parent_acl.stdout_lines
PLAYBOOK

ansible-playbook -i 'localhost,' "${PB}" 2>&1 | tee "${TASKLOG}"
echo "exit was: $?" | tee -a "${TASKLOG}"
```

### Journal write

```bash
cp /tmp/lab51b/task1.txt /root/rhcsa_journal/lab-51b/task1/evidence.txt
cp /root/rhcsa_journal/lab-51b/playbooks/task1.yml /root/rhcsa_journal/lab-51b/task1/task1.yml
```

---

## Task 2 — Trap proof: assert inheritance on fresh child file

### Purpose

Catch T51-A proactively by asserting inherited ACL entries on a freshly created child file, not an older file.

### Main command block

```bash
PB=/root/rhcsa_journal/lab-51b/playbooks/task2.yml
TASKLOG=/tmp/lab51b/task2.txt

cat > "${PB}" <<'PLAYBOOK'
---
- name: "Lab 51b Task 2 - assert inherited ACL on fresh file"
  hosts: localhost
  connection: local
  gather_facts: false
  vars:
    target_dir: /tmp/lab51b/parent
    fresh_file: /tmp/lab51b/parent/fresh_child.txt
    target_user: labuser_51_dacl
    target_group: labgrp_51_dacl

  tasks:
    - name: Remove any stale child first
      ansible.builtin.file:
        path: "{{ fresh_file }}"
        state: absent

    - name: Create fresh child file
      ansible.builtin.file:
        path: "{{ fresh_file }}"
        state: touch

    - name: Capture ACL on fresh child
      ansible.builtin.command:
        cmd: getfacl {{ fresh_file }}
      changed_when: false
      register: child_acl

    - name: Assert inherited ACL entries exist (T51-A guardrail)
      ansible.builtin.assert:
        that:
          - "'user:' ~ target_user ~ ':rwx' in child_acl.stdout"
          - "'group:' ~ target_group ~ ':r-x' in child_acl.stdout"
        fail_msg: "Fresh child file missing expected inherited ACL entries."
        success_msg: "Fresh child inherited expected ACL entries."

    - name: T51-B reminder (default ACL belongs on directories)
      ansible.builtin.debug:
        msg: "Do not use default ACL on regular files; apply default ACL to directories only."
PLAYBOOK

ansible-playbook -i 'localhost,' "${PB}" 2>&1 | tee "${TASKLOG}"
echo "exit was: $?" | tee -a "${TASKLOG}"
```

### Trap callout

- **T51-A:** assert inheritance on a newly created file to avoid false confidence.
- **T51-B:** `default: true` is directory policy; it is not a valid regular-file target model.

### Journal write

```bash
cp /tmp/lab51b/task2.txt /root/rhcsa_journal/lab-51b/task2/evidence.txt
cp /root/rhcsa_journal/lab-51b/playbooks/task2.yml /root/rhcsa_journal/lab-51b/task2/task2.yml
```

---

## Lab Closeout — Bulletproof Teardown (Section 6)

```bash
set +e

if getent passwd "${USER}" >/dev/null 2>&1; then
  userdel -r "${USER}" 2>/dev/null
fi
if getent group "${GROUP}" >/dev/null 2>&1; then
  groupdel "${GROUP}" 2>/dev/null
fi

rm -rf "${SANDBOX}"

echo "── Lab 51b cleanup audit ──"
getent passwd "${USER}" >/dev/null && echo "❌ user remains" || echo "✅ user gone"
getent group "${GROUP}" >/dev/null && echo "❌ group remains" || echo "✅ group gone"
test -d "${SANDBOX}" && echo "❌ sandbox remains" || echo "✅ sandbox gone"
test -d "${USER_HOME}" && echo "❌ home remains" || echo "✅ home gone"

set -e
```

---

## Lab 51b Checklist

- [ ] Task 1 completed (`ansible.posix.acl` used with `default: true`)
- [ ] Parent directory `getfacl` output contains `default:` entries
- [ ] Task 2 creates fresh child and asserts inherited ACL entries
- [ ] T51-A and T51-B captured in evidence notes
- [ ] Section 6 closeout ended with four `✅` lines

---

## Author

**Kelvin R. Tobias**
[kelvinintech.com](https://kelvinintech.com) · [GitHub](https://github.com/kelvintechnical) · [LinkedIn](https://www.linkedin.com/in/kelvin-r-tobias-211949219)
