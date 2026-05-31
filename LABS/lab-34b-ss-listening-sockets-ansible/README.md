# Lab 34b: Inspecting Listening Sockets with Ansible (Module-First)

- **Series:** linux-ops-mastery — Network Inspection and Service Diagnostics
- **Trilogy:** `34a` (RHCSA) -> `34b` (Ansible) -> `34c` (Verify)
- **Time Estimate:** 25-35 minutes
- **Tasks:** 2
- **Practice Directory (rotation slot 20):** `/var/tmp`
- **Sandbox (Tier B):** `/tmp/lab34b` with `USER=labuser_34_ss`, `GROUP=labgrp_34_ss`
- **Playbooks live at:** `/root/rhcsa_journal/lab-34b/playbooks/`
- **Traps rehearsed this lab:** **T34-A** · **T34-B** · **T41** · **T44**

> **Not a boundary lab:** `community.general.listen_ports_facts` is a real module, so this b-lab stays fully module-honest.

---

## LAB HEADER BLOCK

```bash
echo "📦 OS: $(cat /etc/redhat-release 2>/dev/null || grep PRETTY_NAME /etc/os-release)"
echo "🕒 TIME: $(date -Is)"
echo "👤 USER: $(whoami)@$(hostname)"
echo "📁 PRACTICE DIR: /var/tmp"
echo "⚠️ TRAPS: T34-A T34-B T41 T44"
ansible --version | head -n 2
ansible -m ping localhost | tail -n 4
ansible-galaxy collection list | grep -E '^community\.general' || echo "community.general missing"
```

---

## Objective

1. Run `ss -tlnp4` through `ansible.builtin.shell`, capture with `register`, and assert non-empty output.
2. Gather listening-port facts through `community.general.listen_ports_facts` (FQCN).
3. Enforce trap guard with `failed_when` when port 22 is not present.

---

## Lab-Wide Setup — Tier B Sandbox

```bash
sudo -i

export SANDBOX=/tmp/lab34b
export GROUP=labgrp_34_ss
export USER=labuser_34_ss
export USER_HOME=${SANDBOX}/home_${USER}

mkdir -p "${SANDBOX}" "${USER_HOME}" /root/rhcsa_journal/lab-34b/playbooks
getent group "${GROUP}" >/dev/null || groupadd "${GROUP}"
getent passwd "${USER}" >/dev/null || useradd -d "${USER_HOME}" -M -s /bin/bash -g "${GROUP}" "${USER}"
chown -R "${USER}:${GROUP}" "${SANDBOX}"
```

---

## Task 1 — Register `ss -tlnp4` output + collect `listen_ports_facts`

### Purpose

Use both command-capture and facts-driven collection in the same run:

- `ansible.builtin.shell: ss -tlnp4` with `register`
- `community.general.listen_ports_facts` with FQCN

### Playbook (`/root/rhcsa_journal/lab-34b/playbooks/task1.yml`)

```yaml
---
- name: "Lab 34b Task 1 - collect listening sockets"
  hosts: localhost
  connection: local
  gather_facts: false

  tasks:
    - name: "Capture listening sockets via ss -tlnp4"
      ansible.builtin.shell: ss -tlnp4
      register: ss_tlnp4
      changed_when: false

    - name: "Assert ss output is not empty"
      ansible.builtin.assert:
        that:
          - ss_tlnp4.stdout | length > 0
        fail_msg: "ss -tlnp4 produced no output"
        success_msg: "ss -tlnp4 output captured"

    - name: "Gather listening ports using module facts"
      community.general.listen_ports_facts:

    - name: "Show quick facts summary"
      ansible.builtin.debug:
        msg:
          - "tcp_listen_count={{ (ansible_facts.tcp_listen | default([])) | length }}"
          - "udp_listen_count={{ (ansible_facts.udp_listen | default([])) | length }}"
```

### Run and verify

```bash
ansible-playbook /root/rhcsa_journal/lab-34b/playbooks/task1.yml 2>&1 | tee /var/tmp/lab34b-task1-apply-1.txt
ansible-playbook /root/rhcsa_journal/lab-34b/playbooks/task1.yml 2>&1 | tee /var/tmp/lab34b-task1-apply-2.txt
```

### Journal write

```bash
mkdir -p /root/rhcsa_journal/lab-34b/task1
cp /var/tmp/lab34b-task1-apply-1.txt /root/rhcsa_journal/lab-34b/task1/apply-1.txt
cp /var/tmp/lab34b-task1-apply-2.txt /root/rhcsa_journal/lab-34b/task1/apply-2.txt
```

---

## Task 2 — Trap guard with `failed_when` if port 22 missing

### Purpose

Make socket verification fail loudly when SSH listener is absent.

### Playbook (`/root/rhcsa_journal/lab-34b/playbooks/task2.yml`)

```yaml
---
- name: "Lab 34b Task 2 - fail when SSH listener absent"
  hosts: localhost
  connection: local
  gather_facts: false

  tasks:
    - name: "Capture listening sockets for trap guard"
      ansible.builtin.shell: ss -tlnp4
      register: ss_tlnp4
      changed_when: false
      failed_when: "':22 ' not in ss_tlnp4.stdout and ':22\\n' not in ss_tlnp4.stdout"

    - name: "Explain trap status"
      ansible.builtin.debug:
        msg:
          - "T34 guard passed: TCP port 22 listener found"
          - "If this task failed, investigate sshd/socket activation before continuing"
```

### Run and inspect

```bash
ansible-playbook /root/rhcsa_journal/lab-34b/playbooks/task2.yml 2>&1 | tee /var/tmp/lab34b-task2-apply.txt
grep -E "FAILED|T34 guard|PLAY RECAP" /var/tmp/lab34b-task2-apply.txt || true
```

### Trap callout

- **T34-A:** use `-n` in the command to avoid lookup delays.
- **T34-B:** process owner mapping in `ss -p` is root-sensitive; incomplete output as non-root is expected.

### Journal write

```bash
mkdir -p /root/rhcsa_journal/lab-34b/task2
cp /var/tmp/lab34b-task2-apply.txt /root/rhcsa_journal/lab-34b/task2/evidence.txt
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

echo "── Lab 34b cleanup audit ──"
getent passwd "${USER}" >/dev/null && echo "❌ user remains" || echo "✅ user gone"
getent group "${GROUP}" >/dev/null && echo "❌ group remains" || echo "✅ group gone"
test -d "${SANDBOX}" && echo "❌ sandbox remains" || echo "✅ sandbox gone"
test -d "${USER_HOME}" && echo "❌ home remains" || echo "✅ home gone"

set -e
```

---

## Lab 34b Checklist

- [ ] Task 1 completed (`ansible.builtin.shell: ss -tlnp4` captured with `register`; `community.general.listen_ports_facts` executed)
- [ ] Task 2 completed (`failed_when` guard enforces port 22 presence)
- [ ] T34-A and T34-B trap notes recorded in evidence
- [ ] Section 6 closeout audit shows four `✅` lines

---

## Author

**Kelvin R. Tobias**
[kelvinintech.com](https://kelvinintech.com) · [GitHub](https://github.com/kelvintechnical) · [LinkedIn](https://www.linkedin.com/in/kelvin-r-tobias-211949219)
