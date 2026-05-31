# Lab 43b: SGID and Sticky Bit with Ansible - `ansible.builtin.file` modes `2770` and `1777`

- **Series:** linux-ops-mastery - Permissions, Ownership, and Collaboration Controls
- **Trilogy:** `43a` (RHCSA) -> `43b` (Ansible) -> `43c` (Verify)
- **Time Estimate:** 25-35 minutes
- **Tasks:** 2 (Task 1 declarative permissions, Task 2 exact-mode trap assertions)
- **Practice Directory (rotation #43):** `/home`
- **Sandbox (Tier B):** `/tmp/lab43b` with `USER=labuser_43_sgid`, `GROUP=labgrp_43_sgid`
- **Traps rehearsed this lab:** **T43-A** · **T43-B** · **T41** · **T44**

> This lab maps the manual `chmod` reflex from 43a to declarative idempotent Ansible.

---

## LAB HEADER BLOCK

```bash
echo "ENV:   ${ENV:-DECLARE_ME}"
echo "TIME:  $(date -Is)"
echo "USER:  $(whoami)@$(hostname)"
echo "TRAPS: T43-A T43-B T41 T44"
echo "PRACTICE DIR: /home"
ansible --version | head -n 1
```

---

## Objective

Use Ansible to enforce SGID and sticky bit modes exactly:

1. `mode: '2770'` for SGID collaboration directory.
2. `mode: '1777'` for sticky shared drop directory.
3. Validate with `stat` so drift is visible and fail-fast.

---

## Lab-Wide Setup (Tier B)

```bash
sudo -i

export SANDBOX=/tmp/lab43b
export GROUP=labgrp_43_sgid
export USER=labuser_43_sgid
export USER_HOME=${SANDBOX}/home_${USER}

mkdir -p "${SANDBOX}" /root/rhcsa_journal/lab-43b/task1 /root/rhcsa_journal/lab-43b/task2
getent group "${GROUP}" >/dev/null || groupadd "${GROUP}"
getent passwd "${USER}"  >/dev/null || useradd -d "${USER_HOME}" -M -s /bin/bash -g "${GROUP}" "${USER}"
mkdir -p "${USER_HOME}"
chown -R "${USER}:${GROUP}" "${SANDBOX}"
```

---

## Task 1 - Declarative SGID and Sticky Directories

### Purpose

Create both directories with exact modes using `ansible.builtin.file`.

### Playbook

Create `/tmp/lab43b/task1.yml`:

```yaml
---
- name: Lab 43b Task 1
  hosts: localhost
  connection: local
  become: true
  gather_facts: false
  vars:
    sandbox: /tmp/lab43b
    group_name: labgrp_43_sgid
  tasks:
    - name: Ensure SGID team directory exists
      ansible.builtin.file:
        path: "{{ sandbox }}/groupdir"
        state: directory
        owner: root
        group: "{{ group_name }}"
        mode: '2770'

    - name: Ensure sticky shared directory exists
      ansible.builtin.file:
        path: "{{ sandbox }}/shared"
        state: directory
        owner: root
        group: root
        mode: '1777'
```

### Run + verify

```bash
ansible-playbook /tmp/lab43b/task1.yml
stat -c '%A %a %U:%G %n' /tmp/lab43b/groupdir
stat -c '%A %a %U:%G %n' /tmp/lab43b/shared
```

### Expected

- `/tmp/lab43b/groupdir` mode is exactly `2770`.
- `/tmp/lab43b/shared` mode is exactly `1777`.

---

## Task 2 - Trap-Proof Exact Mode Assertions

### Purpose

Fail the run when effective mode bits are not exactly what the lab requires.

### Playbook

Create `/tmp/lab43b/task2.yml`:

```yaml
---
- name: Lab 43b Task 2
  hosts: localhost
  connection: local
  become: true
  gather_facts: false
  vars:
    sgid_dir: /tmp/lab43b/groupdir
    sticky_dir: /tmp/lab43b/shared
  tasks:
    - name: Read SGID directory mode
      ansible.builtin.stat:
        path: "{{ sgid_dir }}"
      register: sgid_stat

    - name: Read sticky directory mode
      ansible.builtin.stat:
        path: "{{ sticky_dir }}"
      register: sticky_stat

    - name: Assert SGID dir exact mode
      ansible.builtin.assert:
        that:
          - sgid_stat.stat.mode == "2770"
        fail_msg: "T43-A risk: SGID directory mode drifted from 2770"
        success_msg: "SGID directory mode exact match (2770)"

    - name: Assert sticky dir exact mode
      ansible.builtin.assert:
        that:
          - sticky_stat.stat.mode == "1777"
        fail_msg: "T43-B risk: sticky directory mode drifted from 1777"
        success_msg: "Sticky directory mode exact match (1777)"
```

### Run + verify

```bash
ansible-playbook /tmp/lab43b/task2.yml
```

### Trap reminders

- **T43-A:** Do not confuse SGID directory behavior with SGID file behavior.
- **T43-B:** Sticky expectations apply to directory delete semantics.

---

## Lab Closeout (Section 6) - Destroy/Restore Drill

```bash
set +e
rm -rf /tmp/lab43b

if getent passwd "${USER}" >/dev/null 2>&1; then
    userdel -r "${USER}" 2>/dev/null
fi
if getent group "${GROUP}" >/dev/null 2>&1; then
    groupdel "${GROUP}" 2>/dev/null
fi

echo "-- Lab 43b cleanup audit --"
getent passwd "${USER}" >/dev/null && echo "FAIL user remains" || echo "OK user gone"
getent group "${GROUP}" >/dev/null && echo "FAIL group remains" || echo "OK group gone"
test -d /tmp/lab43b && echo "FAIL sandbox remains" || echo "OK sandbox gone"
set -e
```

---

## Checklist

- [ ] Task 1: `ansible.builtin.file` set modes `'2770'` and `'1777'`
- [ ] Task 2: `ansible.builtin.assert` proved exact mode bits
- [ ] T43-A and T43-B reviewed with mode-drift guardrails
- [ ] T41/T44 handled via closeout and audit block

---

## Author

**Kelvin R. Tobias**
