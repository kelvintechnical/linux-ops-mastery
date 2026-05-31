# Lab 57b: Changing Default Firewall Zone with Ansible — `ansible.posix.firewalld`

- **Series:** linux-ops-mastery — Firewalld Zone Operations
- **Trilogy:** `57a` (RHCSA) -> `57b` (Ansible) -> `57c` (Verify)
- **Time Estimate:** 25-35 minutes
- **Tasks:** 2
- **Practice Directory (rotation #57):** `/sbin` (command context)
- **Sandbox (Tier B):** `/tmp/lab57b` with `USER=labuser_57_fwdef`, `GROUP=labgrp_57_fwdef`
- **Playbooks live at:** `/root/rhcsa_journal/lab-57b/playbooks/`
- **Traps rehearsed this lab:** **T57-A** · **T57-B** · **T41** · **T44**

> **CRITICAL SAFETY:** Do not switch default zones remotely unless SSH is allowed in the target zone or an automatic rollback is pre-armed.

---

## LAB HEADER BLOCK

```bash
echo "🕒  TIME: $(date -Is)"
echo "👤  USER: $(whoami)@$(hostname)"
echo "📁  PRACTICE DIR: /sbin"
echo "⚠️  TRAPS: T57-A T57-B T41 T44"
ansible --version | head -n 2
ansible -m ping localhost | tail -n 4
firewall-cmd --get-default-zone
```

---

## Objective

1. Use `ansible.posix.firewalld` to set default zone with persistent state intent.
2. Add T57-A preflight guard: verify `ssh` service exists in target zone before any zone switch.

---

## Lab-Wide Setup — Tier B Sandbox

```bash
sudo -i

export SANDBOX=/tmp/lab57b
export GROUP=labgrp_57_fwdef
export USER=labuser_57_fwdef
export USER_HOME=${SANDBOX}/home_${USER}

mkdir -p "${SANDBOX}" "${USER_HOME}" /root/rhcsa_journal/lab-57b/playbooks /root/rhcsa_journal/lab-57b/task1 /root/rhcsa_journal/lab-57b/task2
getent group "${GROUP}" >/dev/null || groupadd "${GROUP}"
getent passwd "${USER}" >/dev/null || useradd -d "${USER_HOME}" -M -s /bin/bash -g "${GROUP}" "${USER}"
chown -R "${USER}:${GROUP}" "${SANDBOX}"
```

---

## Task 1 — Set default zone with `ansible.posix.firewalld`

### Purpose

Mirror the RHCSA default-zone transition using idempotent automation.

### Playbook (`/root/rhcsa_journal/lab-57b/playbooks/task1.yml`)

```yaml
---
- name: "Lab 57b Task 1 - set firewalld default zone"
  hosts: localhost
  connection: local
  gather_facts: false

  vars:
    target_zone: internal

  tasks:
    - name: "Capture current default zone"
      ansible.builtin.command: firewall-cmd --get-default-zone
      register: before_zone
      changed_when: false

    - name: "Persist original default zone for closeout restore"
      ansible.builtin.copy:
        dest: /root/rhcsa_journal/lab-57b/original_default_zone.txt
        content: "{{ before_zone.stdout }}\n"
        mode: "0600"

    - name: "Ensure target zone exists permanently (zone + state + permanent)"
      ansible.posix.firewalld:
        zone: "{{ target_zone }}"
        state: present
        permanent: true

    - name: "Switch default zone (T57-B: already persistent)"
      ansible.builtin.command: "firewall-cmd --set-default-zone={{ target_zone }}"
      changed_when: true

    - name: "Reload firewalld"
      ansible.builtin.command: firewall-cmd --reload
      changed_when: false

    - name: "Show default zone after switch"
      ansible.builtin.command: firewall-cmd --get-default-zone
      register: after_zone
      changed_when: false

    - name: "Assert switch happened"
      ansible.builtin.assert:
        that:
          - after_zone.stdout == target_zone

    - name: "Restore original default zone for safety"
      ansible.builtin.command: "firewall-cmd --set-default-zone={{ before_zone.stdout }}"
      changed_when: true

    - name: "Reload after restore"
      ansible.builtin.command: firewall-cmd --reload
      changed_when: false
```

### Run

```bash
ansible-playbook /root/rhcsa_journal/lab-57b/playbooks/task1.yml 2>&1 | tee /var/tmp/lab57b-task1.txt
```

### Journal write

```bash
cp /var/tmp/lab57b-task1.txt /root/rhcsa_journal/lab-57b/task1/evidence.txt
```

---

## Task 2 — T57-A preflight: ensure SSH exists in target zone before switch

### Purpose

Prevent remote lockout by failing early when target zone does not include `ssh`.

### Playbook (`/root/rhcsa_journal/lab-57b/playbooks/task2.yml`)

```yaml
---
- name: "Lab 57b Task 2 - preflight ssh service in target zone"
  hosts: localhost
  connection: local
  gather_facts: false

  vars:
    target_zone: internal

  tasks:
    - name: "List services in target zone (permanent)"
      ansible.builtin.command: "firewall-cmd --zone={{ target_zone }} --list-services --permanent"
      register: zone_services
      changed_when: false

    - name: "Guard against SSH-cutoff trap T57-A"
      ansible.builtin.assert:
        that:
          - "'ssh' in zone_services.stdout.split()"
        fail_msg: "T57-A risk: ssh not present in {{ target_zone }}. Add ssh before switch."
        success_msg: "Preflight passed: ssh present in {{ target_zone }}."

    - name: "Optional documented command to add ssh safely"
      ansible.builtin.debug:
        msg: "If needed: firewall-cmd --zone={{ target_zone }} --add-service=ssh --permanent && firewall-cmd --reload"
```

### Run

```bash
ansible-playbook /root/rhcsa_journal/lab-57b/playbooks/task2.yml 2>&1 | tee /var/tmp/lab57b-task2.txt
```

### Trap callout

- **T57-A:** Never switch default zone until `ssh` is present in the target zone.
- **T57-B:** `--set-default-zone` is already persistent; avoid mixed assumptions in rollback plans.

### Journal write

```bash
cp /var/tmp/lab57b-task2.txt /root/rhcsa_journal/lab-57b/task2/evidence.txt
```

---

## Lab Closeout — Bulletproof Teardown (Section 6)

```bash
set +e

orig_default_file=/root/rhcsa_journal/lab-57b/original_default_zone.txt
if [ -f "${orig_default_file}" ]; then
  orig="$(cat "${orig_default_file}")"
else
  orig="public"
fi

# CRITICAL SAFETY: restore original default zone before teardown.
firewall-cmd --set-default-zone="${orig}" 2>/dev/null
firewall-cmd --reload 2>/dev/null

if getent passwd "${USER}" >/dev/null 2>&1; then
  userdel -r "${USER}" 2>/dev/null
fi
if getent group "${GROUP}" >/dev/null 2>&1; then
  groupdel "${GROUP}" 2>/dev/null
fi

rm -rf "${SANDBOX}"

echo "── Lab 57b cleanup audit ──"
firewall-cmd --get-default-zone
getent passwd "${USER}" >/dev/null && echo "❌ user remains" || echo "✅ user gone"
getent group "${GROUP}" >/dev/null && echo "❌ group remains" || echo "✅ group gone"
test -d "${SANDBOX}" && echo "❌ sandbox remains" || echo "✅ sandbox gone"
test -d "${USER_HOME}" && echo "❌ home remains" || echo "✅ home gone"

set -e
```

---

## Lab 57b Checklist

- [ ] Task 1 completed (`ansible.posix.firewalld` ensured zone state/permanence, switched default zone, then restored original)
- [ ] Task 2 completed (T57-A preflight confirms `ssh` in target zone before switch)
- [ ] T57-B persistence behavior documented
- [ ] Section 6 closeout restored original default zone and printed cleanup audit

---

## Author

**Kelvin R. Tobias**
[kelvinintech.com](https://kelvinintech.com) · [GitHub](https://github.com/kelvintechnical) · [LinkedIn](https://www.linkedin.com/in/kelvin-r-tobias-211949219)
