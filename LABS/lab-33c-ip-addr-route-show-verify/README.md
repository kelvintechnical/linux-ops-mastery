# Lab 33c: Verifying IP and Routing Info - audit + destroy/restore

- **Series:** linux-ops-mastery - Documentation & Networking
- **Trilogy:** `33a` (RHCSA) -> `33b` (Ansible) -> `33c` (Verify - you are here)
- **Time Estimate:** 25-35 minutes
- **Tasks:** 2 (Task 1 = audit artifacts from 33a/33b, Task 2 = destroy-restore drill)
- **Practice Directory (rotation #33):** `/mnt`
- **Sandbox (Tier B):** `/tmp/lab33c` with `USER=labuser_33_ipshow`, `GROUP=labgrp_33_ipshow`
- **Traps rehearsed this lab:** **T33-A** · **T33-B** · **T41** · **T44**

> **This lab verifies** that interface/routing evidence from both command line and Ansible paths is complete, replayable, and recoverable under failure.

---

## LAB HEADER BLOCK

```bash
echo "🖥️  ENV:   ${ENV:-DECLARE_ME}"
echo "📦  OS:    $(cat /etc/redhat-release 2>/dev/null || grep PRETTY_NAME /etc/os-release)"
echo "🕒  TIME:  $(date -Is)"
echo "👤  USER:  $(whoami)@$(hostname)"
echo "📁  PRACTICE DIR: /mnt"
echo "⚠️  TRAP REMINDERS THIS LAB: T33-A T33-B T41 T44"
ip -br addr show
ip route show
```

> **STOP - paste header output before setup.**

---

## Objective

1. Audit `33a` and `33b` artifacts to confirm they show interface, IPv4 route, IPv6 route, and Ansible evidence with trap-awareness notes.
2. Perform a destroy-restore drill to prove routing/address inspection recovers cleanly after deleting evidence outputs.

---

## Lab-Wide Setup - Tier B Sandbox

```bash
sudo -i

export SANDBOX=/tmp/lab33c
export GROUP=labgrp_33_ipshow
export USER=labuser_33_ipshow
export USER_HOME=${SANDBOX}/home_${USER}

mkdir -p "${SANDBOX}" "${USER_HOME}" /root/rhcsa_journal/lab-33c/task1 /root/rhcsa_journal/lab-33c/task2
getent group "${GROUP}" >/dev/null || groupadd "${GROUP}"
getent passwd "${USER}" >/dev/null || useradd -d "${USER_HOME}" -M -s /bin/bash -g "${GROUP}" "${USER}"
chown -R "${USER}:${GROUP}" "${SANDBOX}"
```

---

## Task 1 - Audit `33a` / `33b` artifacts

### Purpose

Verify that both implementation paths produced valid evidence:

- `33a` should include `ip -br addr`, `ip addr show lo`, `ip route show`, `ip route show table all`, and `ip -6 route` captures.
- `33b` should include fact-gather output and guarded `ip addr` command capture with assert/failure logic.

### Main command block

```bash
TASKLOG=/tmp/lab33c/task1.txt

echo "=== audit 33a journal ==="                                      | tee "${TASKLOG}"
ls -la /root/rhcsa_journal/lab-33a/task1 /root/rhcsa_journal/lab-33a/task2 \
  2>&1 | tee -a "${TASKLOG}"

echo "=== audit 33b journal ==="                                      | tee -a "${TASKLOG}"
ls -la /root/rhcsa_journal/lab-33b/task1 /root/rhcsa_journal/lab-33b/task2 \
  2>&1 | tee -a "${TASKLOG}"

echo "=== key content checks ==="                                     | tee -a "${TASKLOG}"
grep -E "ip -br addr show|ip addr show lo|ip link" \
  /root/rhcsa_journal/lab-33a/task1/evidence.txt 2>&1 | tee -a "${TASKLOG}" || true
grep -E "ip route show table all|ip -6 route" \
  /root/rhcsa_journal/lab-33a/task2/evidence.txt 2>&1 | tee -a "${TASKLOG}" || true
grep -E "Gather network facts|Interfaces detected|PLAY RECAP" \
  /root/rhcsa_journal/lab-33b/task1/evidence.txt \
  /root/rhcsa_journal/lab-33b/task2/evidence.txt 2>&1 | tee -a "${TASKLOG}" || true

echo "exit was: $?"                                                   | tee -a "${TASKLOG}"
```

### Journal write

```bash
JDIR=/root/rhcsa_journal/lab-33c/task1
cp /tmp/lab33c/task1.txt "${JDIR}/audit.txt"
```

---

## Task 2 - Destroy-restore drill (T41 rehearsal)

### Purpose

Force a local evidence loss event, then rebuild inspection artifacts from live system state.

### Main command block

```bash
TASKLOG=/tmp/lab33c/task2.txt

echo "=== DESTROY phase ==="                                          | tee "${TASKLOG}"
rm -f /tmp/lab33c/rebuilt-ip.txt /tmp/lab33c/rebuilt-routes.txt /tmp/lab33c/rebuilt-ipv6-routes.txt
ls -l /tmp/lab33c/rebuilt-* 2>&1 | tee -a "${TASKLOG}" || true

echo "=== RESTORE phase ==="                                          | tee -a "${TASKLOG}"
ip -br addr show > /tmp/lab33c/rebuilt-ip.txt
ip route show table all > /tmp/lab33c/rebuilt-routes.txt
ip -6 route > /tmp/lab33c/rebuilt-ipv6-routes.txt

wc -l /tmp/lab33c/rebuilt-ip.txt /tmp/lab33c/rebuilt-routes.txt /tmp/lab33c/rebuilt-ipv6-routes.txt \
  | tee -a "${TASKLOG}"

echo "=== restore spot checks ==="                                    | tee -a "${TASKLOG}"
head -n 5 /tmp/lab33c/rebuilt-ip.txt                                  | tee -a "${TASKLOG}"
head -n 5 /tmp/lab33c/rebuilt-routes.txt                              | tee -a "${TASKLOG}"
head -n 5 /tmp/lab33c/rebuilt-ipv6-routes.txt                         | tee -a "${TASKLOG}" || true

echo "exit was: $?"                                                   | tee -a "${TASKLOG}"
```

### Trap callout

- **T41:** skipping destroy-restore leaves false confidence; recovery must be practiced while calm so failures are routine.

### Journal write

```bash
JDIR=/root/rhcsa_journal/lab-33c/task2
cp /tmp/lab33c/task2.txt "${JDIR}/destroy-restore.txt"
cp /tmp/lab33c/rebuilt-ip.txt "${JDIR}/rebuilt-ip.txt"
cp /tmp/lab33c/rebuilt-routes.txt "${JDIR}/rebuilt-routes.txt"
cp /tmp/lab33c/rebuilt-ipv6-routes.txt "${JDIR}/rebuilt-ipv6-routes.txt"
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

echo "── Lab 33c cleanup audit ──"
getent passwd "${USER}" >/dev/null && echo "❌ user remains" || echo "✅ user gone"
getent group "${GROUP}" >/dev/null && echo "❌ group remains" || echo "✅ group gone"
test -d "${SANDBOX}" && echo "❌ sandbox remains" || echo "✅ sandbox gone"
test -d "${USER_HOME}" && echo "❌ home remains" || echo "✅ home gone"

set -e
```

---

## Lab 33c Checklist

- [ ] Task 1 completed (`33a` and `33b` artifacts audited for required command/fact coverage)
- [ ] Task 2 completed (destroy-restore drill rebuilt IP and route evidence)
- [ ] T41 destroy-restore rehearsal documented in journal evidence
- [ ] Section 6 closeout audit shows four `✅` lines

---

## Author

**Kelvin R. Tobias**
[kelvinintech.com](https://kelvinintech.com) · [GitHub](https://github.com/kelvintechnical) · [LinkedIn](https://www.linkedin.com/in/kelvin-r-tobias-211949219)
