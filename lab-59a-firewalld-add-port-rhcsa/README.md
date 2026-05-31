# Lab 59a: Opening Custom Ports (RHCSA) — `firewall-cmd --add-port`, `--remove-port`, `--list-ports`

- **Series:** linux-ops-mastery — Networking, Services, and Access Control
- **Trilogy:** **`59a`** (RHCSA hand-typed) -> [`59b`](../lab-59b-firewalld-add-port-ansible/) (Ansible) -> [`59c`](../lab-59c-firewalld-add-port-verify/) (Verify)
- **Time Estimate:** 25-35 minutes
- **Tasks:** 2
- **Practice Directory (objective context):** `/lib64` (inspection), `/tmp/lab59a` (write/log target)
- **Sandbox (Tier B):** `/tmp/lab59a` with `USER=labuser_59_fwport`, `GROUP=labgrp_59_fwport`
- **Traps rehearsed:** **T59-A** (port without protocol fails: always use `/tcp` or `/udp`) · **T59-B** (range syntax is `8000-8100/tcp`, never `8000:8100`) · **T41** (destroy-restore discipline) · **T44** (cleanup audit)

> **Port reflex:** `firewall-cmd --add-port` always requires `PORT/PROTO` (example: `8080/tcp`). Missing protocol is a hard error.

---

## LAB HEADER BLOCK

```bash
echo "📁 PRACTICE DIR: /lib64 (inspect), /tmp/lab59a (write)"
echo "👤 USER: $(whoami)@$(hostname)"
echo "🕒 TIME: $(date -Is)"
echo "⚠️ TRAPS: T59-A T59-B T41 T44"
firewall-cmd --state
ls -ld /lib64 /tmp
```

> **STOP — paste output before setup.**

---

## Objective

Build exam reflex for custom firewalld ports:

1. Add persistent custom ports with valid protocol and valid range syntax.
2. Reload and verify exactly what ports are active.
3. Revert safely with `--remove-port` and prove T59-A failure mode.

---

## Lab-Wide Setup — Tier B Sandbox

```bash
sudo -i

export SANDBOX=/tmp/lab59a
export GROUP=labgrp_59_fwport
export USER=labuser_59_fwport
export USER_HOME=${SANDBOX}/home_${USER}
export ORIG_PORTS_FILE=${SANDBOX}/orig_ports.txt

mkdir -p "${SANDBOX}" "${USER_HOME}"
mkdir -p /root/rhcsa_journal/lab-59a/task1 /root/rhcsa_journal/lab-59a/task2

getent group "${GROUP}" >/dev/null || groupadd "${GROUP}"
getent passwd "${USER}" >/dev/null || useradd -d "${USER_HOME}" -M -s /bin/bash -g "${GROUP}" "${USER}"
chown -R "${USER}:${GROUP}" "${SANDBOX}"
```

---

## Task 1 — Add custom ports permanently, reload, verify

### Purpose

Capture original port state, add the required ports permanently, reload firewalld, and verify effective state.

### Main command block

```bash
TASKLOG=/tmp/lab59a/task1.txt

firewall-cmd --list-ports | tee "${ORIG_PORTS_FILE}" | tee "${TASKLOG}"
echo "saved original ports to ${ORIG_PORTS_FILE}" | tee -a "${TASKLOG}"

sudo firewall-cmd --permanent --add-port=8080/tcp --add-port=9090-9095/udp | tee -a "${TASKLOG}"
sudo firewall-cmd --reload | tee -a "${TASKLOG}"
sudo firewall-cmd --list-ports | tee -a "${TASKLOG}"

echo "T59-B range syntax reminder: 8000-8100/tcp is valid; 8000:8100 is invalid." | tee -a "${TASKLOG}"
echo "exit was: $?" | tee -a "${TASKLOG}"
```

### Journal write

```bash
cp /tmp/lab59a/task1.txt /root/rhcsa_journal/lab-59a/task1/evidence.txt
cp "${ORIG_PORTS_FILE}" /root/rhcsa_journal/lab-59a/task1/original-ports.txt
```

---

## Task 2 — Revert with `--remove-port` + T59-A trap demo

### Purpose

Practice clean rollback and demonstrate that omitting protocol fails immediately.

### Main command block

```bash
TASKLOG=/tmp/lab59a/task2.txt

sudo firewall-cmd --permanent --remove-port=8080/tcp | tee "${TASKLOG}"
sudo firewall-cmd --permanent --remove-port=9090-9095/udp | tee -a "${TASKLOG}"
sudo firewall-cmd --reload | tee -a "${TASKLOG}"
sudo firewall-cmd --list-ports | tee -a "${TASKLOG}"

echo "== T59-A demo: add-port without protocol must fail ==" | tee -a "${TASKLOG}"
sudo firewall-cmd --permanent --add-port=8080 2>&1 | tee -a "${TASKLOG}" || true
echo "Fix: use --add-port=8080/tcp (or /udp)." | tee -a "${TASKLOG}"

echo "exit was: $?" | tee -a "${TASKLOG}"
```

### Journal write

```bash
cp /tmp/lab59a/task2.txt /root/rhcsa_journal/lab-59a/task2/evidence.txt
```

---

## Lab Closeout — Section 6 Teardown (must restore original ports)

```bash
set +e

if test -f "${ORIG_PORTS_FILE}"; then
  # Remove all currently listed runtime ports from permanent config first.
  current_ports="$(firewall-cmd --list-ports)"
  for p in ${current_ports}; do
    firewall-cmd --permanent --remove-port="${p}" >/dev/null 2>&1
  done

  # Restore original list exactly as captured at setup.
  for p in $(cat "${ORIG_PORTS_FILE}"); do
    firewall-cmd --permanent --add-port="${p}" >/dev/null 2>&1
  done
  firewall-cmd --reload >/dev/null 2>&1
fi

if getent passwd "${USER}" >/dev/null 2>&1; then userdel -r "${USER}" 2>/dev/null; fi
if getent group "${GROUP}" >/dev/null 2>&1; then groupdel "${GROUP}" 2>/dev/null; fi
rm -rf "${SANDBOX}"

echo "── Lab 59a cleanup audit ──"
echo "original ports target: $(test -f "${ORIG_PORTS_FILE}" && cat "${ORIG_PORTS_FILE}" || echo '(file removed with sandbox)')"
echo "runtime ports now: $(firewall-cmd --list-ports)"
getent passwd "${USER}" >/dev/null && echo "❌ user remains" || echo "✅ user gone"
getent group "${GROUP}" >/dev/null && echo "❌ group remains" || echo "✅ group gone"
test -d "${SANDBOX}" && echo "❌ sandbox remains" || echo "✅ sandbox gone"

set -e
```

---

## Author

**Kelvin R. Tobias**
