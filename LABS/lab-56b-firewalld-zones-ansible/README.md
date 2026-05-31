# Lab 56b: Exploring firewalld Zones with Ansible - read-only query and assertion

- **Series:** linux-ops-mastery - Security Administration (firewalld)
- **Trilogy:** [`56a`](../lab-56a-firewalld-zones-rhcsa/) (RHCSA) -> `56b` (Ansible) -> [`56c`](../lab-56c-firewalld-zones-verify/) (Verify)
- **Time Estimate:** 20-30 minutes
- **Tasks:** 2
- **Practice Directory (objective context):** `/bin` (inspection context), `/tmp/lab56b` (write target)
- **Sandbox (Tier B):** `/tmp/lab56b` with `USER=labuser_56_fwzones`, `GROUP=labgrp_56_fwzones`
- **Playbooks live at:** `/root/rhcsa_journal/lab-56b/playbooks/`
- **Traps rehearsed:** **T56-A** (firewalld must be active first) · **T56-B** (`--list-all` scope trap) · **T41** (destroy-restore appears in 56c) · **T44** (cleanup audit)

> **Read-only scope:** query and assert only. No firewalld modifications are allowed in this lab.

---

## LAB HEADER BLOCK

```bash
echo "📁 PRACTICE DIR: /bin (inspect), /tmp/lab56b (write)"
echo "👤 USER: $(whoami)@$(hostname)"
echo "🕒 TIME: $(date -Is)"
echo "⚠️ TRAPS: T56-A T56-B T41 T44"
ansible --version | head -n 2
ansible localhost -m ping
systemctl is-active firewalld
```

---

## Objective

1. Capture firewalld zone state with Ansible in read-only mode.
2. Assert the default zone equals `public` using automation guardrails.

---

## Lab-Wide Setup - Tier B Sandbox

```bash
sudo -i

export SANDBOX=/tmp/lab56b
export GROUP=labgrp_56_fwzones
export USER=labuser_56_fwzones
export USER_HOME=${SANDBOX}/home_${USER}

mkdir -p "${SANDBOX}" "${USER_HOME}" /root/rhcsa_journal/lab-56b/playbooks
mkdir -p /root/rhcsa_journal/lab-56b/task1 /root/rhcsa_journal/lab-56b/task2
getent group "${GROUP}" >/dev/null || groupadd "${GROUP}"
getent passwd "${USER}" >/dev/null || useradd -d "${USER_HOME}" -M -s /bin/bash -g "${GROUP}" "${USER}"
chown -R "${USER}:${GROUP}" "${SANDBOX}"
```

---

## Task 1 - Ansible read-only firewalld queries

### Purpose

Use Ansible to gather zone evidence without mutating runtime or permanent firewall config.

### Playbook (`/root/rhcsa_journal/lab-56b/playbooks/task1.yml`)

```yaml
---
- name: "Lab 56b Task 1 - firewalld read-only zone discovery"
  hosts: localhost
  connection: local
  gather_facts: false

  tasks:
    - name: "T56-A precheck - firewalld service is active"
      ansible.builtin.command: systemctl is-active firewalld
      register: fw_active
      changed_when: false
      failed_when: fw_active.stdout.strip() != "active"

    - name: "Query default zone"
      ansible.builtin.command: firewall-cmd --get-default-zone
      register: default_zone
      changed_when: false

    - name: "Query available zones"
      ansible.builtin.command: firewall-cmd --get-zones
      register: all_zones
      changed_when: false

    - name: "Query active zones"
      ansible.builtin.command: firewall-cmd --get-active-zones
      register: active_zones
      changed_when: false

    - name: "Read-only module query example (ssh enabled in public?)"
      ansible.posix.firewalld:
        zone: public
        service: ssh
        state: query
      register: public_ssh_query

    - name: "Capture evidence"
      ansible.builtin.copy:
        dest: /tmp/lab56b/task1.txt
        mode: "0644"
        content: |
          firewalld_active={{ fw_active.stdout.strip() }}
          default_zone={{ default_zone.stdout.strip() }}
          zones={{ all_zones.stdout.strip() }}
          active_zones={{ active_zones.stdout | trim }}
          public_ssh_enabled={{ public_ssh_query.enabled | default('unknown') }}
```

### Run and verify

```bash
ansible-playbook /root/rhcsa_journal/lab-56b/playbooks/task1.yml 2>&1 | tee /var/tmp/lab56b-task1-apply.txt
cat /tmp/lab56b/task1.txt
```

### Journal write

```bash
cp /var/tmp/lab56b-task1-apply.txt /root/rhcsa_journal/lab-56b/task1/evidence.txt
cp /tmp/lab56b/task1.txt /root/rhcsa_journal/lab-56b/task1/zone-snapshot.txt
```

---

## Task 2 - Assert default zone is `public`

### Purpose

Automate a safety check that fails fast when default zone drifts away from expected baseline.

### Playbook (`/root/rhcsa_journal/lab-56b/playbooks/task2.yml`)

```yaml
---
- name: "Lab 56b Task 2 - assert default zone is public"
  hosts: localhost
  connection: local
  gather_facts: false

  tasks:
    - name: "Read default zone"
      ansible.builtin.command: firewall-cmd --get-default-zone
      register: default_zone
      changed_when: false

    - name: "Assert default zone equals public"
      ansible.builtin.assert:
        that:
          - default_zone.stdout.strip() == "public"
        fail_msg: "Default zone is not public. Found: {{ default_zone.stdout.strip() }}"
        success_msg: "Default zone is public."

    - name: "Write assertion artifact"
      ansible.builtin.copy:
        dest: /tmp/lab56b/task2.txt
        mode: "0644"
        content: |
          asserted_default_zone={{ default_zone.stdout.strip() }}
          expected=public
```

### Run and inspect

```bash
ansible-playbook /root/rhcsa_journal/lab-56b/playbooks/task2.yml 2>&1 | tee /var/tmp/lab56b-task2-apply.txt
cat /tmp/lab56b/task2.txt
```

### Trap callout

- **T56-B:** if you later compare details, use `firewall-cmd --list-all --zone=<zone>` explicitly instead of plain `--list-all`.

### Journal write

```bash
cp /var/tmp/lab56b-task2-apply.txt /root/rhcsa_journal/lab-56b/task2/evidence.txt
cp /tmp/lab56b/task2.txt /root/rhcsa_journal/lab-56b/task2/assertion.txt
```

---

## Lab Closeout - Bulletproof Teardown (Section 6)

```bash
set +e
userdel -r "${USER}" 2>/dev/null
groupdel "${GROUP}" 2>/dev/null
rm -rf "${SANDBOX}"

echo "── Lab 56b cleanup audit ──"
getent passwd "${USER}" >/dev/null && echo "❌ user remains" || echo "✅ user gone"
getent group "${GROUP}" >/dev/null && echo "❌ group remains" || echo "✅ group gone"
test -d "${SANDBOX}" && echo "❌ sandbox remains" || echo "✅ sandbox gone"
test -d "${USER_HOME}" && echo "❌ home remains" || echo "✅ home gone"
set -e
```

---

## Author

**Kelvin R. Tobias**
[kelvinintech.com](https://kelvinintech.com) · [GitHub](https://github.com/kelvintechnical) · [LinkedIn](https://www.linkedin.com/in/kelvin-r-tobias-211949219)
