# Lab 56a: Exploring firewalld Zones (RHCSA) - inspect default, active, and predefined zones

- **Series:** linux-ops-mastery - Security Administration (firewalld)
- **Trilogy:** `56a` (RHCSA hand-typed) -> [`56b`](../lab-56b-firewalld-zones-ansible/) (Ansible) -> [`56c`](../lab-56c-firewalld-zones-verify/) (Verify)
- **Time Estimate:** 20-30 minutes
- **Tasks:** 2
- **Practice Directory (objective context):** `/bin` (inspection context), `/tmp/lab56a` (write target)
- **Sandbox (Tier B):** `/tmp/lab56a` with `USER=labuser_56_fwzones`, `GROUP=labgrp_56_fwzones`
- **Traps rehearsed:** **T56-A** (firewalld must be running before zone inspection) · **T56-B** (`--list-all` without `--zone` only shows default zone) · **T41** (destroy-restore appears in 56c) · **T44** (cleanup audit)

> **Read-only scope:** this lab performs zone inspection only. No zone/service/port changes are made.

---

## LAB HEADER BLOCK

```bash
echo "📁 PRACTICE DIR: /bin (inspect), /tmp/lab56a (write)"
echo "👤 USER: $(whoami)@$(hostname)"
echo "🕒 TIME: $(date -Is)"
echo "⚠️ TRAPS: T56-A T56-B T41 T44"
command -v firewall-cmd
systemctl is-active firewalld
ls -ld /bin /tmp
```

> **STOP:** if `systemctl is-active firewalld` is not `active`, fix that first or every task result is invalid (T56-A).

---

## Objective

1. Inspect firewalld default and available zones with `firewall-cmd` safely.
2. Distinguish default-zone output from explicit zone output (`--zone=...`) to avoid T56-B.
3. Build evidence artifacts for journal review without changing firewall state.

---

## Predefined Zones to Know

`public`, `internal`, `dmz`, `drop`, `block`, `work`, `home`, `trusted`

---

## Lab-Wide Setup - Tier B Sandbox

```bash
sudo -i

export SANDBOX=/tmp/lab56a
export GROUP=labgrp_56_fwzones
export USER=labuser_56_fwzones
export USER_HOME=${SANDBOX}/home_${USER}

mkdir -p "${SANDBOX}" "${USER_HOME}"
mkdir -p /root/rhcsa_journal/lab-56a/task1
mkdir -p /root/rhcsa_journal/lab-56a/task2

getent group "${GROUP}" >/dev/null || groupadd "${GROUP}"
getent passwd "${USER}" >/dev/null || useradd -d "${USER_HOME}" -M -s /bin/bash -g "${GROUP}" "${USER}"
chown -R "${USER}:${GROUP}" "${SANDBOX}"
```

---

## Task 1 - Baseline zone discovery (default, all zones, list-all)

### Purpose

Run the exact baseline commands used in RHCSA troubleshooting to identify default zone context.

### Main command block

```bash
TASKLOG=/tmp/lab56a/task1.txt

echo "== T56-A precheck: firewalld must be active ==" | tee "${TASKLOG}"
systemctl is-active firewalld | tee -a "${TASKLOG}"

echo "== default zone ==" | tee -a "${TASKLOG}"
sudo firewall-cmd --get-default-zone | tee -a "${TASKLOG}"

echo "== all defined zones ==" | tee -a "${TASKLOG}"
sudo firewall-cmd --get-zones | tee -a "${TASKLOG}"

echo "== list-all (default zone only) ==" | tee -a "${TASKLOG}"
sudo firewall-cmd --list-all | tee -a "${TASKLOG}"

echo "exit was: $?"
```

### Trap callout

- **T56-A:** if firewalld is inactive, all further results are garbage. Always check service state first.
- **T56-B:** this `--list-all` output is only for the default zone.

### Journal write

```bash
cp /tmp/lab56a/task1.txt /root/rhcsa_journal/lab-56a/task1/evidence.txt
cat > /root/rhcsa_journal/lab-56a/task1/done.txt <<EOF
LAB: lab-56a
TASK: task1
DATE: $(date -Is)
STATUS: COMPLETE
EOF
```

---

## Task 2 - Active zones and explicit zone contrast (`public` vs `trusted`)

### Purpose

Show the difference between "what is active now" and "what is configured in a named zone."

### Main command block

```bash
TASKLOG=/tmp/lab56a/task2.txt

echo "== active zones ==" | tee "${TASKLOG}"
sudo firewall-cmd --get-active-zones | tee -a "${TASKLOG}"

echo "== public zone details (explicit) ==" | tee -a "${TASKLOG}"
sudo firewall-cmd --list-all --zone=public | tee -a "${TASKLOG}"

echo "== trusted zone details (explicit) ==" | tee -a "${TASKLOG}"
sudo firewall-cmd --list-all --zone=trusted | tee -a "${TASKLOG}"

echo "== all zones in one view ==" | tee -a "${TASKLOG}"
sudo firewall-cmd --list-all-zones | tee -a "${TASKLOG}"

echo "exit was: $?"
```

### Trap callout

- **T56-B:** never compare non-default zones with plain `--list-all`; always force `--zone=<name>`.

### Journal write

```bash
cp /tmp/lab56a/task2.txt /root/rhcsa_journal/lab-56a/task2/evidence.txt
cat > /root/rhcsa_journal/lab-56a/task2/done.txt <<EOF
LAB: lab-56a
TASK: task2
DATE: $(date -Is)
STATUS: COMPLETE
EOF
```

---

## Lab Closeout - Bulletproof Teardown (Section 6)

```bash
set +e
userdel -r "${USER}" 2>/dev/null
groupdel "${GROUP}" 2>/dev/null
rm -rf "${SANDBOX}"

echo "── Lab 56a cleanup audit ──"
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
