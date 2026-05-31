# Lab 33b: Display IP and Routing Info with Ansible (Module-First)

- **Series:** linux-ops-mastery - Documentation & Networking
- **Trilogy:** `33a` (RHCSA) -> `33b` (Ansible mirror) -> `33c` (Verify)
- **Time Estimate:** 25-35 minutes
- **Tasks:** 2
- **Practice Directory (rotation #33):** `/mnt`
- **Sandbox (Tier B):** `/tmp/lab33b` with `USER=labuser_33_ipshow`, `GROUP=labgrp_33_ipshow`
- **Playbooks live at:** `/root/rhcsa_journal/lab-33b/playbooks/`
- **Traps rehearsed this lab:** **T33-A** · **T33-B** · **T41** · **T44**

> **Section 18 boundary note (explicit):** read-only network inspection has no dedicated Ansible module for every `ip` subcommand shape. The honest module-first path is `ansible.builtin.setup` for gathered facts, then controlled `ansible.builtin.shell` for command-level inspection evidence.

---

## LAB HEADER BLOCK

```bash
echo "📦 OS: $(cat /etc/redhat-release 2>/dev/null || grep PRETTY_NAME /etc/os-release)"
echo "🕒 TIME: $(date -Is)"
echo "👤 USER: $(whoami)@$(hostname)"
echo "📁 PRACTICE DIR: /mnt"
echo "⚠️ TRAPS: T33-A T33-B T41 T44"
ansible --version | head -n 2
ansible -m ping localhost | tail -n 4
ip -br addr show
```

---

## Objective

Translate network-inspection habits into Ansible evidence patterns:

1. Gather network facts with `ansible.builtin.setup` and filter down to `ansible_default_ipv4` and interface facts.
2. Run `ip addr` through `ansible.builtin.shell` + `tee` with `register`, `assert`, and `failed_when` safeguards so empty interface output cannot silently pass.

---

## Lab-Wide Setup - Tier B Sandbox

```bash
sudo -i

export SANDBOX=/tmp/lab33b
export GROUP=labgrp_33_ipshow
export USER=labuser_33_ipshow
export USER_HOME=${SANDBOX}/home_${USER}

mkdir -p "${SANDBOX}" "${USER_HOME}" /root/rhcsa_journal/lab-33b/playbooks
getent group "${GROUP}" >/dev/null || groupadd "${GROUP}"
getent passwd "${USER}" >/dev/null || useradd -d "${USER_HOME}" -M -s /bin/bash -g "${GROUP}" "${USER}"
chown -R "${USER}:${GROUP}" "${SANDBOX}"
```

---

## Task 1 - Gather network facts (`setup` with filters)

### Purpose

Use the supported fact pipeline for read-only interface/routing context:

- `ansible.builtin.setup` gathers network facts.
- Filter to the target keys: `ansible_default_ipv4`, `ansible_facts.interfaces`.
- Write run output for replay in the journal.

### Playbook (`/root/rhcsa_journal/lab-33b/playbooks/task1.yml`)

```yaml
---
- name: "Lab 33b Task 1 - gather network facts"
  hosts: localhost
  connection: local
  gather_facts: false

  tasks:
    - name: "Gather network facts only (Section 18 boundary path)"
      ansible.builtin.setup:
        gather_subset:
          - network
        filter:
          - ansible_default_ipv4
          - ansible_facts.interfaces
      register: network_setup

    - name: "Show default IPv4 and interface list"
      ansible.builtin.debug:
        msg:
          - "default_ipv4={{ network_setup.ansible_facts.ansible_default_ipv4 | default({}) }}"
          - "interfaces={{ network_setup.ansible_facts.ansible_interfaces | default([]) }}"
```

### Run and verify

```bash
ansible-playbook /root/rhcsa_journal/lab-33b/playbooks/task1.yml 2>&1 | tee /tmp/lab33b/task1-apply.txt
```

### Journal write

```bash
mkdir -p /root/rhcsa_journal/lab-33b/task1
cp /tmp/lab33b/task1-apply.txt /root/rhcsa_journal/lab-33b/task1/evidence.txt
```

---

## Task 2 - Run `ip addr` with shell + tee, register, assert, failed_when

### Purpose

Capture command-level interface output and fail fast when no interfaces are detected.

### Playbook (`/root/rhcsa_journal/lab-33b/playbooks/task2.yml`)

```yaml
---
- name: "Lab 33b Task 2 - ip addr inspection with guardrails"
  hosts: localhost
  connection: local
  gather_facts: false

  tasks:
    - name: "Run ip addr and tee to artifact"
      ansible.builtin.shell: "ip addr | tee /tmp/lab33b/ip-addr-live.txt"
      register: ip_addr_capture
      changed_when: false
      failed_when: >
        (ip_addr_capture.rc | int) != 0 or
        ('state ' not in (ip_addr_capture.stdout | lower))

    - name: "Assert at least one interface marker exists"
      ansible.builtin.assert:
        that:
          - ip_addr_capture.stdout is search('^[0-9]+:\\s', multiline=True)
        fail_msg: "No interfaces found in ip addr output."
        success_msg: "Interfaces detected from ip addr output."

    - name: "Summarize line count for evidence"
      ansible.builtin.shell: "wc -l /tmp/lab33b/ip-addr-live.txt"
      register: ip_addr_wc
      changed_when: false

    - name: "Display summary"
      ansible.builtin.debug:
        msg:
          - "ip_addr_lines={{ ip_addr_wc.stdout | trim }}"
```

### Run and inspect

```bash
ansible-playbook /root/rhcsa_journal/lab-33b/playbooks/task2.yml 2>&1 | tee /tmp/lab33b/task2-apply.txt
grep -E "FAILED|Interfaces detected|PLAY RECAP" /tmp/lab33b/task2-apply.txt || true
```

### Journal write

```bash
mkdir -p /root/rhcsa_journal/lab-33b/task2
cp /tmp/lab33b/task2-apply.txt /root/rhcsa_journal/lab-33b/task2/evidence.txt
cp /tmp/lab33b/ip-addr-live.txt /root/rhcsa_journal/lab-33b/task2/ip-addr-live.txt
```

---

## Lab Closeout - Bulletproof Teardown (Section 6)

```bash
set +e

if getent passwd "${USER}" >/dev/null 2>&1; then
  userdel -r "${USER}" 2>/dev/null
fi
if getent group "${GROUP}" >/dev/null 2>&1; then
  groupdel "${GROUP}" 2>/dev/null
fi

rm -rf "${SANDBOX}"

echo "── Lab 33b cleanup audit ──"
getent passwd "${USER}" >/dev/null && echo "❌ user remains" || echo "✅ user gone"
getent group "${GROUP}" >/dev/null && echo "❌ group remains" || echo "✅ group gone"
test -d "${SANDBOX}" && echo "❌ sandbox remains" || echo "✅ sandbox gone"
test -d "${USER_HOME}" && echo "❌ home remains" || echo "✅ home gone"

set -e
```

---

## Lab 33b Checklist

- [ ] Task 1 completed (`ansible.builtin.setup` gathered network facts with filters)
- [ ] Task 2 completed (`ansible.builtin.shell` captured `ip addr` with `register`, `assert`, and `failed_when`)
- [ ] Section 18 boundary note explicitly documented (no dedicated module beyond `setup` for this read-only command shape)
- [ ] Section 6 closeout audit shows four `✅` lines

---

## Author

**Kelvin R. Tobias**
[kelvinintech.com](https://kelvinintech.com) · [GitHub](https://github.com/kelvintechnical) · [LinkedIn](https://www.linkedin.com/in/kelvin-r-tobias-211949219)
