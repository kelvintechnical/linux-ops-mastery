# Lab 45b: Append-Only Attribute with Ansible (Section 18 Boundary)

- **Series:** linux-ops-mastery — File Attributes and Tamper Resistance
- **Trilogy:** `45a` (RHCSA) -> `45b` (Ansible) -> `45c` (Verify)
- **Time Estimate:** 25-35 minutes
- **Tasks:** 2
- **Practice Directory (rotation slot 23):** `/var`
- **Sandbox (Tier B):** `/tmp/lab45b` with `USER=labuser_45_append`, `GROUP=labgrp_45_append`
- **Playbooks live at:** `/root/rhcsa_journal/lab-45b/playbooks/`
- **Traps rehearsed this lab:** **T45-A** · **T45-B** · **T41** · **T44**

> **Section 18 boundary note:** there is no first-class append-only module for `chattr` flags, so this lab uses `ansible.builtin.command` for attribute toggles with explicit guards.

---

## LAB HEADER BLOCK

```bash
echo "📦 OS: $(cat /etc/redhat-release 2>/dev/null || grep PRETTY_NAME /etc/os-release)"
echo "🕒 TIME: $(date -Is)"
echo "👤 USER: $(whoami)@$(hostname)"
echo "📁 PRACTICE DIR: /var"
echo "⚠️ TRAPS: T45-A T45-B T41 T44"
ansible --version | head -n 2
ansible -m ping localhost | tail -n 4
command -v chattr
command -v lsattr
```

---

## Objective

1. Use `ansible.builtin.command` to set append-only (`+a`) and verify behavior.
2. Implement guarded teardown that clears append-only before remove (handler trap protection).

---

## Lab-Wide Setup — Tier B Sandbox

```bash
sudo -i

export SANDBOX=/tmp/lab45b
export GROUP=labgrp_45_append
export USER=labuser_45_append
export USER_HOME=${SANDBOX}/home_${USER}

mkdir -p "${SANDBOX}" "${USER_HOME}" /root/rhcsa_journal/lab-45b/playbooks
getent group "${GROUP}" >/dev/null || groupadd "${GROUP}"
getent passwd "${USER}" >/dev/null || useradd -d "${USER_HOME}" -M -s /bin/bash -g "${GROUP}" "${USER}"
chown -R "${USER}:${GROUP}" "${SANDBOX}"
mkdir -p /tmp/lab45b
touch /tmp/lab45b/audit.log
```

---

## Task 1 — Apply `+a` via Ansible command (Section 18 boundary-safe)

### Purpose

Use command-based attribute control with idempotent pre-checks so reruns stay predictable.

### Playbook (`/root/rhcsa_journal/lab-45b/playbooks/task1.yml`)

```yaml
---
- name: "Lab 45b Task 1 - set append-only and verify"
  hosts: localhost
  connection: local
  gather_facts: false

  vars:
    target_file: /tmp/lab45b/audit.log

  tasks:
    - name: "Ensure target file exists (creates pre-check)"
      ansible.builtin.command:
        cmd: "touch {{ target_file }}"
        creates: "{{ target_file }}"

    - name: "Set append-only attribute (Section 18 boundary)"
      ansible.builtin.command: "chattr +a {{ target_file }}"
      changed_when: true

    - name: "Read attribute state"
      ansible.builtin.command: "lsattr {{ target_file }}"
      register: attr_state
      changed_when: false

    - name: "Assert append-only flag is present"
      ansible.builtin.assert:
        that:
          - "' a ' in (' ' ~ attr_state.stdout ~ ' ') or attr_state.stdout is search('a.*audit\\.log')"
        fail_msg: "append-only flag missing on {{ target_file }}"
        success_msg: "append-only flag detected on {{ target_file }}"

    - name: "Demonstrate append allowed"
      ansible.builtin.shell: "echo 'line from ansible $(date -Is)' >> {{ target_file }}"
      changed_when: true
```

### Run and verify

```bash
ansible-playbook /root/rhcsa_journal/lab-45b/playbooks/task1.yml 2>&1 | tee /var/tmp/lab45b-task1-apply.txt
echo "blocked overwrite demo" > /tmp/lab45b/audit.log 2>&1 | tee -a /var/tmp/lab45b-task1-apply.txt || true
rm -f /tmp/lab45b/audit.log 2>&1 | tee -a /var/tmp/lab45b-task1-apply.txt || true
```

### Journal write

```bash
mkdir -p /root/rhcsa_journal/lab-45b/task1
cp /var/tmp/lab45b-task1-apply.txt /root/rhcsa_journal/lab-45b/task1/evidence.txt
```

---

## Task 2 — Guarded teardown handler (`-a` before `rm`)

### Purpose

Encode the trap-proof order in automation so cleanup never gets stuck on append-only protection.

### Playbook (`/root/rhcsa_journal/lab-45b/playbooks/task2.yml`)

```yaml
---
- name: "Lab 45b Task 2 - guarded append-only teardown"
  hosts: localhost
  connection: local
  gather_facts: false

  vars:
    target_file: /tmp/lab45b/audit.log

  tasks:
    - name: "Request teardown"
      ansible.builtin.debug:
        msg: "Trigger teardown handler for {{ target_file }}"
      notify: "guarded remove append-only file"
      changed_when: true

    - name: "Flush handlers now"
      ansible.builtin.meta: flush_handlers

    - name: "Recreate and restore append-only"
      ansible.builtin.file:
        path: "{{ target_file }}"
        state: touch

    - name: "Restore append-only after recreate"
      ansible.builtin.command: "chattr +a {{ target_file }}"
      changed_when: true

  handlers:
    - name: "guarded remove append-only file"
      block:
        - name: "CRITICAL: clear append-only before rm (T45-B guard)"
          ansible.builtin.command: "chattr -a {{ target_file }}"
          failed_when: false
          changed_when: true

        - name: "Remove file after attribute clear"
          ansible.builtin.file:
            path: "{{ target_file }}"
            state: absent
```

### Run and inspect

```bash
ansible-playbook /root/rhcsa_journal/lab-45b/playbooks/task2.yml 2>&1 | tee /var/tmp/lab45b-task2-apply.txt
lsattr /tmp/lab45b/audit.log 2>&1 | tee -a /var/tmp/lab45b-task2-apply.txt
```

### Journal write

```bash
mkdir -p /root/rhcsa_journal/lab-45b/task2
cp /var/tmp/lab45b-task2-apply.txt /root/rhcsa_journal/lab-45b/task2/evidence.txt
```

---

## Lab Closeout — Bulletproof Teardown (Section 6)

```bash
set +e

# CRITICAL: cleanup MUST clear append-only before rm
if [ -e /tmp/lab45b/audit.log ]; then
  chattr -a /tmp/lab45b/audit.log 2>/dev/null
fi

rm -f /tmp/lab45b/audit.log

if getent passwd "${USER}" >/dev/null 2>&1; then
  userdel -r "${USER}" 2>/dev/null
fi
if getent group "${GROUP}" >/dev/null 2>&1; then
  groupdel "${GROUP}" 2>/dev/null
fi

rm -rf "${SANDBOX}" /tmp/lab45b

echo "── Lab 45b cleanup audit ──"
getent passwd "${USER}" >/dev/null && echo "❌ user remains" || echo "✅ user gone"
getent group "${GROUP}" >/dev/null && echo "❌ group remains" || echo "✅ group gone"
test -d "${SANDBOX}" && echo "❌ sandbox remains" || echo "✅ sandbox gone"
test -e /tmp/lab45b/audit.log && echo "❌ append file remains" || echo "✅ append file gone"

set -e
```

---

## Lab 45b Checklist

- [ ] Task 1 completed (`ansible.builtin.command` set `+a`; append works; overwrite/remove blocked)
- [ ] Task 2 completed (handler executes `chattr -a` before file removal, then restore drill runs)
- [ ] Section 18 boundary documented and respected
- [ ] Section 6 closeout audit shows teardown success

---

## Author

**Kelvin R. Tobias**
[kelvinintech.com](https://kelvinintech.com) · [GitHub](https://github.com/kelvintechnical) · [LinkedIn](https://www.linkedin.com/in/kelvin-r-tobias-211949219)
