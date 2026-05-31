# Lab 59b: Opening Custom Ports (Ansible) — `ansible.posix.firewalld` port state

- **Series:** linux-ops-mastery — Networking, Services, and Access Control
- **Trilogy:** [`59a`](../lab-59a-firewalld-add-port-rhcsa/) (RHCSA) -> **`59b`** (Ansible) -> [`59c`](../lab-59c-firewalld-add-port-verify/) (Verify)
- **Time Estimate:** 25-35 minutes
- **Tasks:** 2
- **Practice Directory (objective context):** `/lib64` (inspection), `/tmp/lab59b` (write/log target)
- **Playbooks:** `/root/rhcsa_journal/lab-59b/playbooks`
- **Sandbox (Tier B):** `/tmp/lab59b` with `USER=labuser_59_fwport`, `GROUP=labgrp_59_fwport`
- **Traps rehearsed:** **T59-A** (always include protocol in port spec) · **T59-B** (range syntax is `8000-8100/tcp`) · **T41** (destroy-restore discipline) · **T44** (cleanup audit)

> **Ansible reflex:** for single custom port exposure, declare `port: 8080/tcp`, `state: enabled`, `permanent: yes`.

---

## LAB HEADER BLOCK

```bash
echo "📁 PRACTICE DIR: /lib64 (inspect), /tmp/lab59b (write)"
ansible --version
ansible localhost -m ping --connection=local -i 'localhost,'
echo "👤 USER: $(whoami)@$(hostname)"
echo "⚠️ TRAPS: T59-A T59-B T41 T44"
firewall-cmd --state
```

---

## Objective

Apply firewalld custom-port state declaratively:

1. Use `ansible.posix.firewalld` to enable `8080/tcp` permanently.
2. Reload and assert the port is present in `firewall-cmd --list-ports`.

---

## Lab-Wide Setup

```bash
sudo -i

export SANDBOX=/tmp/lab59b
export GROUP=labgrp_59_fwport
export USER=labuser_59_fwport
export USER_HOME=${SANDBOX}/home_${USER}
export ORIG_PORTS_FILE=${SANDBOX}/orig_ports.txt

mkdir -p "${SANDBOX}" "${USER_HOME}"
mkdir -p /root/rhcsa_journal/lab-59b/playbooks
mkdir -p /root/rhcsa_journal/lab-59b/task1 /root/rhcsa_journal/lab-59b/task2

getent group "${GROUP}" >/dev/null || groupadd "${GROUP}"
getent passwd "${USER}" >/dev/null || useradd -d "${USER_HOME}" -M -s /bin/bash -g "${GROUP}" "${USER}"
chown -R "${USER}:${GROUP}" "${SANDBOX}"

firewall-cmd --list-ports > "${ORIG_PORTS_FILE}"
```

---

## Task 1 — Enable `8080/tcp` permanently with Ansible

### Purpose

Use the module declaration exactly as exam guidance: `port`, `state`, `permanent`.

### Main command block

```bash
PB=/root/rhcsa_journal/lab-59b/playbooks/task1.yml
TASKLOG=/tmp/lab59b/task1.txt

cat > "${PB}" <<'PLAYBOOK'
---
- name: "Lab 59b Task 1 - enable custom firewalld port"
  hosts: localhost
  connection: local
  gather_facts: false
  tasks:
    - name: Enable 8080/tcp permanently
      ansible.posix.firewalld:
        port: 8080/tcp
        state: enabled
        permanent: yes
PLAYBOOK

ansible-playbook -i 'localhost,' "${PB}" 2>&1 | tee "${TASKLOG}"
firewall-cmd --reload 2>&1 | tee -a "${TASKLOG}"
firewall-cmd --list-ports 2>&1 | tee -a "${TASKLOG}"
echo "exit was: $?" | tee -a "${TASKLOG}"
```

### Journal write

```bash
cp /tmp/lab59b/task1.txt /root/rhcsa_journal/lab-59b/task1/evidence.txt
cp "${PB}" /root/rhcsa_journal/lab-59b/task1/task1.yml
```

---

## Task 2 — Trap-proof assert after reload (T59-A, T59-B awareness)

### Purpose

Validate that runtime state really reflects permanent changes after a reload.

### Main command block

```bash
PB=/root/rhcsa_journal/lab-59b/playbooks/task2.yml
TASKLOG=/tmp/lab59b/task2.txt

cat > "${PB}" <<'PLAYBOOK'
---
- name: "Lab 59b Task 2 - assert 8080/tcp is active after reload"
  hosts: localhost
  connection: local
  gather_facts: false
  tasks:
    - name: Reload firewalld runtime from permanent config
      ansible.builtin.command: firewall-cmd --reload
      changed_when: true

    - name: Read runtime port list
      ansible.builtin.command: firewall-cmd --list-ports
      register: fw_ports
      changed_when: false

    - name: Assert required custom port exists
      ansible.builtin.assert:
        that:
          - "'8080/tcp' in fw_ports.stdout.split()"
        fail_msg: "T59-A/T59-B check failed: expected exact token 8080/tcp in runtime list."
PLAYBOOK

ansible-playbook -i 'localhost,' "${PB}" 2>&1 | tee "${TASKLOG}"
echo "T59-B reminder: valid range token is 8000-8100/tcp (hyphen, not colon)." | tee -a "${TASKLOG}"
echo "exit was: $?" | tee -a "${TASKLOG}"
```

### Journal write

```bash
cp /tmp/lab59b/task2.txt /root/rhcsa_journal/lab-59b/task2/evidence.txt
cp "${PB}" /root/rhcsa_journal/lab-59b/task2/task2.yml
```

---

## Lab Closeout — Section 6 Teardown (must restore original ports)

```bash
set +e

if test -f "${ORIG_PORTS_FILE}"; then
  current_ports="$(firewall-cmd --list-ports)"
  for p in ${current_ports}; do
    firewall-cmd --permanent --remove-port="${p}" >/dev/null 2>&1
  done
  for p in $(cat "${ORIG_PORTS_FILE}"); do
    firewall-cmd --permanent --add-port="${p}" >/dev/null 2>&1
  done
  firewall-cmd --reload >/dev/null 2>&1
fi

if getent passwd "${USER}" >/dev/null 2>&1; then userdel -r "${USER}" 2>/dev/null; fi
if getent group "${GROUP}" >/dev/null 2>&1; then groupdel "${GROUP}" 2>/dev/null; fi
rm -rf "${SANDBOX}"

echo "── Lab 59b cleanup audit ──"
echo "runtime ports now: $(firewall-cmd --list-ports)"
getent passwd "${USER}" >/dev/null && echo "❌ user remains" || echo "✅ user gone"
getent group "${GROUP}" >/dev/null && echo "❌ group remains" || echo "✅ group gone"
test -d "${SANDBOX}" && echo "❌ sandbox remains" || echo "✅ sandbox gone"

set -e
```

---

## Author

**Kelvin R. Tobias**
