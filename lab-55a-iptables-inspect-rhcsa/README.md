# Lab 55a: Inspecting iptables (RHCSA) - `iptables -L`, `iptables-save`, `nft list ruleset`

- **Series:** linux-ops-mastery
- **Trilogy:** `55a` (RHCSA) -> `55b` (Ansible) -> `55c` (Verify)
- **Practice Directory:** `/tmp`
- **Tier B Sandbox:** `/tmp/lab55a`
- **Lab User/Group:** `labuser_55_iptables` / `labgrp_55_iptables`
- **Traps rehearsed:** `T55-A`, `T55-B`, `T41`, `T44`

This lab's practice directory is: `/tmp`

> Read-only inspection only. Do **not** add, flush, or modify any firewall rules.

---

## LAB HEADER

```bash
echo "TIME: $(date -Is)"
echo "USER: $(whoami)@$(hostname)"
echo "PRACTICE DIR: /tmp"
echo "FOCUS: iptables legacy view vs nftables backend"
echo "TRAPS: T55-A T55-B T41 T44"
cat /etc/redhat-release 2>/dev/null || grep PRETTY_NAME /etc/os-release
iptables --version
nft --version
echo "exit was: $?"
```

> STOP and confirm header output before continuing.

---

## Lab-Wide Tier B Setup (run before Task 1)

```bash
sudo -i
export LAB_NUM=55
export LAB_SLUG=iptables
export SANDBOX=/tmp/lab55a
export GROUP=labgrp_55_iptables
export USER=labuser_55_iptables
export USER_HOME=${SANDBOX}/home_${USER}

mkdir -p "${SANDBOX}" "${USER_HOME}" /root/rhcsa_journal/lab-55a/task1 /root/rhcsa_journal/lab-55a/task2
getent group "${GROUP}" >/dev/null || groupadd "${GROUP}"
getent passwd "${USER}" >/dev/null || useradd -d "${USER_HOME}" -M -s /bin/bash -g "${GROUP}" "${USER}"
chown -R "${USER}:${GROUP}" "${SANDBOX}"

id "${USER}"
ls -ld /tmp "${SANDBOX}" "${USER_HOME}"
echo "Sandbox built by $(whoami) at $(date -Is)"
echo "exit was: $?"
```

---

## Task 1 - Capture iptables and nft read-only snapshots

Practice directory this task: `/tmp`

### Purpose

Capture three views of firewall state without mutation: legacy `iptables` table listing, saved iptables format, and nftables ruleset snapshot.

### Main Block

```bash
export SANDBOX=/tmp/lab55a
export TASKLOG="${SANDBOX}/task1.txt"

echo "=== iptables -L -n -v ===" | tee "${TASKLOG}"
sudo iptables -L -n -v 2>&1 | tee -a "${TASKLOG}"

echo "=== iptables-save | head ===" | tee -a "${TASKLOG}"
sudo iptables-save 2>&1 | head -n 40 | tee -a "${TASKLOG}"

echo "=== nft list ruleset | head ===" | tee -a "${TASKLOG}"
sudo nft list ruleset 2>&1 | head -n 60 | tee -a "${TASKLOG}"

sudo -u "${USER}" bash -c 'echo "Task1 capture reviewed at $(date -Is)" >> /tmp/lab55a/task1-reviewed-by-user.txt'
stat -c '%U:%G %a %n' /tmp/lab55a/task1-reviewed-by-user.txt | tee -a "${TASKLOG}"
echo "exit was: $?"
```

### Trap focus

- `T55-B`: avoid `iptables -L` without `-n` on offline systems, because reverse DNS lookup can stall output.
- `T55-A`: RHEL 9 uses nftables backend by default, so `iptables -L` may not reflect full nft ruleset view.

### Journal Write

```bash
LAB=lab-55a
TASK=task1
JDIR="/root/rhcsa_journal/${LAB}/${TASK}"
mkdir -p "${JDIR}"
cp /tmp/lab55a/task1.txt "${JDIR}/evidence.txt"
cat > "${JDIR}/done.txt" <<EOF
LAB: ${LAB}
TASK: ${TASK}
DATE: $(date -Is)
USER: $(whoami)@$(hostname)
STATUS: COMPLETE
EOF
```

---

## Task 2 - Contrast legacy and modern views on RHEL 9

Practice directory this task: `/tmp`

### Purpose

Document how `iptables` output compares to `nft list ruleset` and record the RHEL 9 backend reality for exam troubleshooting.

### Main Block

```bash
export SANDBOX=/tmp/lab55a
export TASKLOG="${SANDBOX}/task2.txt"

{
  echo "=== RHEL9 backend context ==="
  cat /etc/redhat-release 2>/dev/null || grep PRETTY_NAME /etc/os-release
  echo
  echo "=== legacy view: iptables -L (name lookup enabled; may stall offline) ==="
  sudo iptables -L 2>&1 | head -n 40
  echo
  echo "=== safer legacy inspect: iptables -L -n -v ==="
  sudo iptables -L -n -v 2>&1 | head -n 40
  echo
  echo "=== modern backend view: nft list ruleset ==="
  sudo nft list ruleset 2>&1 | head -n 80
  echo
  echo "=== operator note ==="
  echo "On RHEL9, iptables is a compatibility wrapper over nftables by default."
  echo "If iptables output looks empty but nft has policy objects/chains, trust nft as source of truth."
} | tee "${TASKLOG}"

sudo -u "${USER}" bash -c 'echo "Task2 contrast reviewed at $(date -Is)" >> /tmp/lab55a/task2-reviewed-by-user.txt'
stat -c '%U:%G %a %n' /tmp/lab55a/task2-reviewed-by-user.txt | tee -a "${TASKLOG}"
echo "exit was: $?"
```

### Journal Write

```bash
LAB=lab-55a
TASK=task2
JDIR="/root/rhcsa_journal/${LAB}/${TASK}"
mkdir -p "${JDIR}"
cp /tmp/lab55a/task2.txt "${JDIR}/evidence.txt"
cat > "${JDIR}/done.txt" <<EOF
LAB: ${LAB}
TASK: ${TASK}
DATE: $(date -Is)
USER: $(whoami)@$(hostname)
STATUS: COMPLETE
EOF
cat > "${JDIR}/notes.txt" <<EOF
TOPIC: inspect iptables legacy output and nftables backend view
COMMANDS: iptables -L, iptables -L -n -v, iptables-save, nft list ruleset
TRAPS: T55-A and T55-B rehearsed
NEXT: lab-55b ansible read-only inspection
EOF
```

---

## Section 6 Closeout (after Task 2)

```bash
set +e
export SANDBOX=/tmp/lab55a
export GROUP=labgrp_55_iptables
export USER=labuser_55_iptables
export USER_HOME=${SANDBOX}/home_${USER}

if getent passwd "${USER}" >/dev/null 2>&1; then userdel -r "${USER}" 2>/dev/null; fi
if getent group "${GROUP}" >/dev/null 2>&1; then groupdel "${GROUP}" 2>/dev/null; fi
rm -rf "${SANDBOX}"

echo "── cleanup audit ──"
getent passwd "${USER}" >/dev/null && echo "❌ user remains" || echo "✅ user gone"
getent group "${GROUP}" >/dev/null && echo "❌ group remains" || echo "✅ group gone"
test -d "${SANDBOX}" && echo "❌ sandbox remains" || echo "✅ sandbox gone"
test -d "${USER_HOME}" && echo "❌ home remains" || echo "✅ home gone"

set -e
echo "Cleanup complete by $(whoami) at $(date -Is)"
echo "exit was: $?"
```

---

## Author

Kelvin R. Tobias
