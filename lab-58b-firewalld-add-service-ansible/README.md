# Lab 58b: Adding Services to firewalld Zones (Ansible) - `ansible.posix.firewalld`

- **Series:** linux-ops-mastery - Security Administration (firewalld)
- **Trilogy:** [`58a`](../lab-58a-firewalld-add-service-rhcsa/) (RHCSA) -> **`58b`** (Ansible) -> [`58c`](../lab-58c-firewalld-add-service-verify/) (Verify)
- **Time Estimate:** 25-35 minutes
- **Tasks:** 2
- **Practice Directory (objective context):** `/lib` (inspection context), `/tmp/lab58b` (write target)
- **Playbooks:** `/root/rhcsa_journal/lab-58b/playbooks`
- **Sandbox (Tier B):** `/tmp/lab58b` with `USER=labuser_58_fwsvc`, `GROUP=labgrp_58_fwsvc`
- **Traps rehearsed:** **T58-A** (runtime-only changes vanish on reload) · **T58-B** (`--reload` restores runtime from permanent) · **T41** (destroy-restore belongs in verify) · **T44** (cleanup audit)

> **Service source reminder:** predefined service profiles are in `/usr/lib/firewalld/services/`.

---

## LAB HEADER BLOCK

```bash
echo "📁 PRACTICE DIR: /lib (inspect), /tmp/lab58b (write)"
ansible --version
ansible localhost -m ping --connection=local -i 'localhost,'
echo "👤 USER: $(whoami)@$(hostname)"
echo "⚠️ TRAPS: T58-A T58-B T41 T44"
systemctl is-active firewalld
ls /usr/lib/firewalld/services | head -n 10
```

---

## Objective

1. Add `http` service declaratively with `ansible.posix.firewalld`.
2. Ensure immediate runtime effect and permanent persistence in one task.
3. Verify persistence after explicit reload to avoid T58-A.

---

## Lab-Wide Setup

```bash
sudo -i

export SANDBOX=/tmp/lab58b
export GROUP=labgrp_58_fwsvc
export USER=labuser_58_fwsvc
export USER_HOME=${SANDBOX}/home_${USER}
export ZONE=public

mkdir -p "${SANDBOX}" "${USER_HOME}"
mkdir -p /root/rhcsa_journal/lab-58b/playbooks
mkdir -p /root/rhcsa_journal/lab-58b/task1
mkdir -p /root/rhcsa_journal/lab-58b/task2

getent group "${GROUP}" >/dev/null || groupadd "${GROUP}"
getent passwd "${USER}" >/dev/null || useradd -d "${USER_HOME}" -M -s /bin/bash -g "${GROUP}" "${USER}"
chown -R "${USER}:${GROUP}" "${SANDBOX}"

sudo firewall-cmd --zone="${ZONE}" --list-services | xargs > "${SANDBOX}/original-services.txt"
cat "${SANDBOX}/original-services.txt"
```

---

## Task 1 - Add `http` with `ansible.posix.firewalld` (permanent + immediate)

### Purpose

Use the exact module fields that prevent runtime/permanent drift.

### Main command block

```bash
PB=/root/rhcsa_journal/lab-58b/playbooks/task1.yml
TASKLOG=/tmp/lab58b/task1.txt

cat > "${PB}" <<'PLAYBOOK'
---
- name: "Lab 58b Task 1 - add http service correctly"
  hosts: localhost
  connection: local
  gather_facts: false
  tasks:
    - name: Enable http service in public zone (immediate + permanent)
      ansible.posix.firewalld:
        zone: public
        service: http
        state: enabled
        permanent: yes
        immediate: yes
PLAYBOOK

ansible-playbook -i 'localhost,' "${PB}" 2>&1 | tee "${TASKLOG}"
sudo firewall-cmd --zone=public --list-services | tee -a "${TASKLOG}"
echo "exit was: $?"
```

### Journal write

```bash
cp /tmp/lab58b/task1.txt /root/rhcsa_journal/lab-58b/task1/evidence.txt
cat > /root/rhcsa_journal/lab-58b/task1/done.txt <<EOF
LAB: lab-58b
TASK: task1
DATE: $(date -Is)
STATUS: COMPLETE
EOF
```

---

## Task 2 - T58-A guard: assert service remains after reload

### Purpose

Prove the service survives reload, which confirms permanent config is correct.

### Main command block

```bash
PB=/root/rhcsa_journal/lab-58b/playbooks/task2.yml
TASKLOG=/tmp/lab58b/task2.txt

cat > "${PB}" <<'PLAYBOOK'
---
- name: "Lab 58b Task 2 - reload and persistence assert"
  hosts: localhost
  connection: local
  gather_facts: false
  tasks:
    - name: Reload firewalld (runtime <- permanent)
      ansible.builtin.command: firewall-cmd --reload
      changed_when: true

    - name: Read current services in public zone
      ansible.builtin.command: firewall-cmd --zone=public --list-services
      register: svc
      changed_when: false

    - name: Assert http still present after reload
      ansible.builtin.assert:
        that:
          - "'http' in svc.stdout.split()"
        fail_msg: "T58-A hit: http missing after reload (likely runtime-only change)."
        success_msg: "http persisted through reload (permanent+reload flow is correct)."
PLAYBOOK

ansible-playbook -i 'localhost,' "${PB}" 2>&1 | tee "${TASKLOG}"
sudo firewall-cmd --zone=public --list-services | tee -a "${TASKLOG}"
echo "exit was: $?"
```

### Trap callout

- **T58-A:** runtime-only add is lost on reload.
- **T58-B:** `--reload` is the truth-sync checkpoint; always validate after it.

### Journal write

```bash
cp /tmp/lab58b/task2.txt /root/rhcsa_journal/lab-58b/task2/evidence.txt
cat > /root/rhcsa_journal/lab-58b/task2/done.txt <<EOF
LAB: lab-58b
TASK: task2
DATE: $(date -Is)
STATUS: COMPLETE
EOF
```

---

## Lab Closeout - Section 6 Teardown (restore original services first)

```bash
set +e

ORIG="$(cat "${SANDBOX}/original-services.txt" 2>/dev/null)"
CURR="$(sudo firewall-cmd --permanent --zone="${ZONE}" --list-services 2>/dev/null)"

for svc in ${CURR}; do
  sudo firewall-cmd --permanent --zone="${ZONE}" --remove-service="${svc}" >/dev/null 2>&1 || true
done
for svc in ${ORIG}; do
  sudo firewall-cmd --permanent --zone="${ZONE}" --add-service="${svc}" >/dev/null 2>&1 || true
done
sudo firewall-cmd --reload >/dev/null 2>&1 || true

userdel -r "${USER}" 2>/dev/null
groupdel "${GROUP}" 2>/dev/null
rm -rf "${SANDBOX}"

echo "── Lab 58b cleanup audit ──"
getent passwd "${USER}" >/dev/null && echo "❌ user remains" || echo "✅ user gone"
getent group "${GROUP}" >/dev/null && echo "❌ group remains" || echo "✅ group gone"
test -d "${SANDBOX}" && echo "❌ sandbox remains" || echo "✅ sandbox gone"
test -d "${USER_HOME}" && echo "❌ home remains" || echo "✅ home gone"
echo "firewalld ${ZONE} services after restore:"
sudo firewall-cmd --zone="${ZONE}" --list-services

set -e
```

---

## Author

**Kelvin R. Tobias**
[kelvinintech.com](https://kelvinintech.com) · [GitHub](https://github.com/kelvintechnical) · [LinkedIn](https://www.linkedin.com/in/kelvin-r-tobias-211949219)
