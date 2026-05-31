# Lab 44b: Immutable File Attribute with Ansible (Section 18 Boundary)

- **Series:** linux-ops-mastery — Filesystem Attributes and Protection
- **Trilogy:** `44a` (RHCSA) -> `44b` (Ansible boundary) -> `44c` (Verify)
- **Time Estimate:** 25-35 minutes
- **Tasks:** 2
- **Practice Directory (rotation slot 44):** `/root`
- **Sandbox (Tier B):** `/tmp/lab44b` with `USER=labuser_44_immutable`, `GROUP=labgrp_44_immutable`
- **Playbooks live at:** `/root/rhcsa_journal/lab-44b/playbooks/`
- **Traps rehearsed this lab:** **T44-A** · **T44-B** · **T41** · **T44**

> **Section 18 boundary (explicit):** there is no dedicated Ansible module for immutable file attribute toggling. Use `ansible.builtin.command` with `chattr` and guard execution with `creates:` where appropriate.

---

## LAB HEADER BLOCK

```bash
echo "📦 OS: $(cat /etc/redhat-release 2>/dev/null || grep PRETTY_NAME /etc/os-release)"
echo "🕒 TIME: $(date -Is)"
echo "👤 USER: $(whoami)@$(hostname)"
echo "📁 PRACTICE DIR: /root"
echo "⚠️ TRAPS: T44-A T44-B T41 T44"
ansible --version | head -n 2
command -v chattr
command -v lsattr
```

---

## Objective

1. Automate immutable protection with `ansible.builtin.command: chattr +i` and a state guard.
2. Build fail-safe teardown flow where `chattr -i` always runs before delete.
3. Preserve boundary honesty: command module for `chattr`, not a non-existent dedicated module.

---

## Lab-Wide Setup — Tier B Sandbox

```bash
sudo -i

export SANDBOX=/tmp/lab44b
export GROUP=labgrp_44_immutable
export USER=labuser_44_immutable
export USER_HOME=${SANDBOX}/home_${USER}

mkdir -p "${SANDBOX}" "${USER_HOME}" /root/rhcsa_journal/lab-44b/playbooks
getent group "${GROUP}" >/dev/null || groupadd "${GROUP}"
getent passwd "${USER}" >/dev/null || useradd -d "${USER_HOME}" -M -s /bin/bash -g "${GROUP}" "${USER}"
chown -R "${USER}:${GROUP}" "${SANDBOX}"
```

---

## Task 1 — Boundary-safe immutable apply with `ansible.builtin.command`

### Purpose

Apply immutable state using command module while still being idempotence-aware through a creation guard.

### Playbook (`/root/rhcsa_journal/lab-44b/playbooks/task1.yml`)

```yaml
---
- name: "Lab 44b Task 1 - apply immutable with command boundary"
  hosts: localhost
  connection: local
  gather_facts: false

  vars:
    target_dir: /tmp/lab44b
    target_file: /tmp/lab44b/protected.txt
    guard_file: /tmp/lab44b/.immutable_applied

  tasks:
    - name: "Ensure target directory exists"
      ansible.builtin.file:
        path: "{{ target_dir }}"
        state: directory
        mode: "0755"

    - name: "Create target file once (state guard)"
      ansible.builtin.command:
        cmd: touch {{ target_file }}
        creates: "{{ target_file }}"

    - name: "Apply immutable attribute (+i) using command boundary"
      ansible.builtin.command:
        cmd: /bin/bash -c 'chattr +i {{ target_file }} && touch {{ guard_file }}'
        creates: "{{ guard_file }}"
      become: true

    - name: "Audit immutable flag"
      ansible.builtin.command:
        cmd: lsattr {{ target_file }}
      become: true
      register: attr_state
      changed_when: false

    - name: "Assert immutable flag present"
      ansible.builtin.assert:
        that:
          - "' i ' in attr_state.stdout or attr_state.stdout.split()[0].endswith('i')"
        fail_msg: "Immutable flag not detected on protected.txt"
        success_msg: "Immutable flag confirmed"
```

### Run and verify

```bash
ansible-playbook /root/rhcsa_journal/lab-44b/playbooks/task1.yml 2>&1 | tee /tmp/lab44b/task1-apply-1.txt
ansible-playbook /root/rhcsa_journal/lab-44b/playbooks/task1.yml 2>&1 | tee /tmp/lab44b/task1-apply-2.txt
sudo lsattr /tmp/lab44b/protected.txt                             2>&1 | tee -a /tmp/lab44b/task1-apply-2.txt
```

### Trap callout

- **T44-B:** immutable apply requires elevated privilege path; use `become: true`.

### Journal write

```bash
mkdir -p /root/rhcsa_journal/lab-44b/task1
cp /tmp/lab44b/task1-apply-1.txt /root/rhcsa_journal/lab-44b/task1/apply-1.txt
cp /tmp/lab44b/task1-apply-2.txt /root/rhcsa_journal/lab-44b/task1/apply-2.txt
```

---

## Task 2 — Trap T44-A fail-safe delete flow (pre-delete unlock)

### Purpose

Guarantee cleanup order: unlock immutable first, then delete.

### Playbook (`/root/rhcsa_journal/lab-44b/playbooks/task2.yml`)

```yaml
---
- name: "Lab 44b Task 2 - fail-safe cleanup ordering"
  hosts: localhost
  connection: local
  gather_facts: false

  vars:
    target_file: /tmp/lab44b/protected.txt

  handlers:
    - name: "pre-delete unlock immutable"
      ansible.builtin.command:
        cmd: chattr -i {{ target_file }}
      become: true
      when: file_stat.stat.exists

  tasks:
    - name: "Check target file state"
      ansible.builtin.stat:
        path: "{{ target_file }}"
      register: file_stat

    - name: "Queue pre-delete unlock handler (T44-A guard)"
      ansible.builtin.debug:
        msg: "Queue unlock before delete"
      changed_when: true
      notify: "pre-delete unlock immutable"
      when: file_stat.stat.exists

    - name: "Run queued unlock handler now"
      ansible.builtin.meta: flush_handlers
      when: file_stat.stat.exists

    - name: "Delete file only after unlock"
      ansible.builtin.file:
        path: "{{ target_file }}"
        state: absent

    - name: "Assert file removed"
      ansible.builtin.stat:
        path: "{{ target_file }}"
      register: after_delete

    - name: "Guard result"
      ansible.builtin.assert:
        that:
          - not after_delete.stat.exists
        fail_msg: "T44-A: protected file still exists; check unlock order"
        success_msg: "Cleanup order valid: unlock then delete"
```

### Run and inspect

```bash
ansible-playbook /root/rhcsa_journal/lab-44b/playbooks/task2.yml 2>&1 | tee /tmp/lab44b/task2-apply.txt
ls -l /tmp/lab44b/protected.txt                                   2>&1 | tee -a /tmp/lab44b/task2-apply.txt || echo "✅ protected.txt absent" | tee -a /tmp/lab44b/task2-apply.txt
```

### Trap callout

- **T44-A (critical):** cleanup fails if immutable unlock is skipped before delete.

### Journal write

```bash
mkdir -p /root/rhcsa_journal/lab-44b/task2
cp /tmp/lab44b/task2-apply.txt /root/rhcsa_journal/lab-44b/task2/evidence.txt
```

---

## Lab Closeout — Bulletproof Teardown (Section 6)

```bash
set +e

# Immutable safety first: unlock before any delete.
if test -e /tmp/lab44b/protected.txt; then
  sudo chattr -i /tmp/lab44b/protected.txt 2>/dev/null
fi

if getent passwd "${USER}" >/dev/null 2>&1; then
  userdel -r "${USER}" 2>/dev/null
fi
if getent group "${GROUP}" >/dev/null 2>&1; then
  groupdel "${GROUP}" 2>/dev/null
fi

rm -rf "${SANDBOX}"

echo "── Lab 44b cleanup audit ──"
getent passwd "${USER}" >/dev/null && echo "❌ user remains" || echo "✅ user gone"
getent group "${GROUP}" >/dev/null && echo "❌ group remains" || echo "✅ group gone"
test -d "${SANDBOX}" && echo "❌ sandbox remains" || echo "✅ sandbox gone"
test -d "${USER_HOME}" && echo "❌ home remains" || echo "✅ home gone"

set -e
```

---

## Lab 44b Checklist

- [ ] Task 1 completed (Section 18 boundary honored: `ansible.builtin.command` for `chattr +i`; `lsattr` proves immutable)
- [ ] Task 2 completed (fail-safe cleanup ordering enforces `chattr -i` before delete)
- [ ] T44-A and T44-B documented in evidence
- [ ] Section 6 closeout audit shows four `✅` lines

---

## Author

**Kelvin R. Tobias**
[kelvinintech.com](https://kelvinintech.com) · [GitHub](https://github.com/kelvintechnical) · [LinkedIn](https://www.linkedin.com/in/kelvin-r-tobias-211949219)
