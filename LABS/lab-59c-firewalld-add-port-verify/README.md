# Lab 59c: Verifying Custom Port State — audit + destroy/restore drill

- **Series:** linux-ops-mastery — Networking, Services, and Access Control
- **Trilogy:** [`59a`](../lab-59a-firewalld-add-port-rhcsa/) (RHCSA) -> [`59b`](../lab-59b-firewalld-add-port-ansible/) (Ansible) -> **`59c`** (Verify)
- **Time Estimate:** 25-35 minutes
- **Tasks:** 2 (Task 1 = audit state in journal, Task 2 = destroy-restore port drill)
- **Practice Directory (objective context):** `/lib64` (inspection), `/tmp/lab59c` (write/log target)
- **Sandbox (Tier B):** `/tmp/lab59c` with `USER=labuser_59_fwport`, `GROUP=labgrp_59_fwport`
- **Traps rehearsed:** **T59-A** (must include protocol), **T59-B** (range uses hyphen), **T41** (destroy-restore), **T44** (cleanup audit)

> **Verifier posture:** record exactly what firewalld reports (`--list-ports`, zone context, journal evidence), then prove you can remove and restore without drift.

---

## LAB HEADER BLOCK

```bash
echo "🖥️ ENV: ${ENV:-DECLARE_ME}"
echo "📦 OS: $(cat /etc/redhat-release 2>/dev/null || grep PRETTY_NAME /etc/os-release)"
echo "🕒 TIME: $(date -Is)"
echo "👤 USER: $(whoami)@$(hostname)"
echo "📁 PRACTICE DIR: /lib64 (inspect), /tmp/lab59c (write)"
echo "⚠️ TRAPS: T59-A T59-B T41 T44"
firewall-cmd --state
firewall-cmd --get-default-zone
```

> **STOP — paste header output before setup.**

---

## Objective

1. Audit active custom-port state and capture journal-grade evidence.
2. Run destroy-restore drill: remove known custom ports, verify removal, restore baseline exactly.

---

## Lab-Wide Setup — Tier B Sandbox

```bash
sudo -i

export SANDBOX=/tmp/lab59c
export GROUP=labgrp_59_fwport
export USER=labuser_59_fwport
export USER_HOME=${SANDBOX}/home_${USER}
export ORIG_PORTS_FILE=${SANDBOX}/orig_ports.txt

mkdir -p "${SANDBOX}" "${USER_HOME}"
mkdir -p /root/rhcsa_journal/lab-59c/task1 /root/rhcsa_journal/lab-59c/task2

getent group "${GROUP}" >/dev/null || groupadd "${GROUP}"
getent passwd "${USER}" >/dev/null || useradd -d "${USER_HOME}" -M -s /bin/bash -g "${GROUP}" "${USER}"
chown -R "${USER}:${GROUP}" "${SANDBOX}"

firewall-cmd --list-ports > "${ORIG_PORTS_FILE}"
```

---

## Task 1 — Audit port state in journal evidence

### Purpose

Collect auditable runtime + permanent firewalld evidence for custom ports.

### Main command block

```bash
TASKLOG=/tmp/lab59c/task1.txt

echo "== default zone ==" | tee "${TASKLOG}"
firewall-cmd --get-default-zone | tee -a "${TASKLOG}"

echo "== runtime ports ==" | tee -a "${TASKLOG}"
firewall-cmd --list-ports | tee -a "${TASKLOG}"

echo "== permanent ports (zone scoped) ==" | tee -a "${TASKLOG}"
zone="$(firewall-cmd --get-default-zone)"
firewall-cmd --permanent --zone="${zone}" --list-ports | tee -a "${TASKLOG}"

echo "== recent firewalld journal ==" | tee -a "${TASKLOG}"
journalctl -u firewalld -n 40 --no-pager | tee -a "${TASKLOG}"

echo "trap reminders: T59-A use 8080/tcp; T59-B use 8000-8100/tcp." | tee -a "${TASKLOG}"
echo "exit was: $?" | tee -a "${TASKLOG}"
```

### Journal write

```bash
cp /tmp/lab59c/task1.txt /root/rhcsa_journal/lab-59c/task1/audit.txt
cp "${ORIG_PORTS_FILE}" /root/rhcsa_journal/lab-59c/task1/original-ports.txt
```

---

## Task 2 — Destroy-restore drill (remove and restore original list)

### Purpose

Exercise T41 safely: remove target custom ports, verify disappearance, then restore captured baseline.

### Main command block

```bash
TASKLOG=/tmp/lab59c/task2.txt

echo "phase A: destroy known custom tokens" | tee "${TASKLOG}"
firewall-cmd --permanent --remove-port=8080/tcp | tee -a "${TASKLOG}" || true
firewall-cmd --permanent --remove-port=9090-9095/udp | tee -a "${TASKLOG}" || true
firewall-cmd --permanent --remove-port=8000-8100/tcp | tee -a "${TASKLOG}" || true
firewall-cmd --reload | tee -a "${TASKLOG}"
firewall-cmd --list-ports | tee -a "${TASKLOG}"

echo "phase B: restore exactly from original capture" | tee -a "${TASKLOG}"
current_ports="$(firewall-cmd --list-ports)"
for p in ${current_ports}; do
  firewall-cmd --permanent --remove-port="${p}" >/dev/null 2>&1
done
for p in $(cat "${ORIG_PORTS_FILE}"); do
  firewall-cmd --permanent --add-port="${p}" >/dev/null 2>&1
done
firewall-cmd --reload | tee -a "${TASKLOG}"
firewall-cmd --list-ports | tee -a "${TASKLOG}"

echo "destroy-restore complete; compare final list with ${ORIG_PORTS_FILE}" | tee -a "${TASKLOG}"
echo "exit was: $?" | tee -a "${TASKLOG}"
```

### Journal write

```bash
cp /tmp/lab59c/task2.txt /root/rhcsa_journal/lab-59c/task2/destroy-restore.txt
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

echo "── Lab 59c cleanup audit ──"
echo "runtime ports now: $(firewall-cmd --list-ports)"
getent passwd "${USER}" >/dev/null && echo "❌ user remains" || echo "✅ user gone"
getent group "${GROUP}" >/dev/null && echo "❌ group remains" || echo "✅ group gone"
test -d "${SANDBOX}" && echo "❌ sandbox remains" || echo "✅ sandbox gone"

set -e
```

---

## Author

**Kelvin R. Tobias**
