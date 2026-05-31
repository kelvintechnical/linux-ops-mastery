# Lab 34c: Verifying Listening Sockets — audit + destroy/restore

- **Series:** linux-ops-mastery — Network Inspection and Service Diagnostics
- **Trilogy:** `34a` (RHCSA) -> `34b` (Ansible) -> `34c` (Verify — you are here)
- **Time Estimate:** 25-35 minutes
- **Tasks:** 2 (Task 1 = audit, Task 2 = destroy-restore drill)
- **Practice Directory (rotation slot 20):** `/var/tmp`
- **Sandbox (Tier B):** `/tmp/lab34c` with `USER=labuser_34_ss`, `GROUP=labgrp_34_ss`
- **Traps rehearsed this lab:** **T34-A** · **T34-B** · **T41** · **T44**

> **This lab verifies** that listening-socket inspection is repeatable under failure and recovery conditions.

---

## LAB HEADER BLOCK

```bash
echo "🖥️  ENV:   ${ENV:-DECLARE_ME}"
echo "📦  OS:    $(cat /etc/redhat-release 2>/dev/null || grep PRETTY_NAME /etc/os-release)"
echo "🕒  TIME:  $(date -Is)"
echo "👤  USER:  $(whoami)@$(hostname)"
echo "📁  PRACTICE DIR: /var/tmp"
echo "⚠️  TRAP REMINDERS THIS LAB: T34-A T34-B T41 T44"
ss -tlnp4 2>/dev/null | head -n 5 || true
```

> **STOP — paste header output before setup.**

---

## Objective

1. Audit current listener inventory and ownership evidence with `ss`, `lsof`, and legacy `netstat`.
2. Run a destroy-restore drill for SSH listening state and verify port 22 returns.

---

## Lab-Wide Setup — Tier B Sandbox

```bash
sudo -i

export SANDBOX=/tmp/lab34c
export GROUP=labgrp_34_ss
export USER=labuser_34_ss
export USER_HOME=${SANDBOX}/home_${USER}

mkdir -p "${SANDBOX}" "${USER_HOME}" /root/rhcsa_journal/lab-34c/task1 /root/rhcsa_journal/lab-34c/task2
getent group "${GROUP}" >/dev/null || groupadd "${GROUP}"
getent passwd "${USER}" >/dev/null || useradd -d "${USER_HOME}" -M -s /bin/bash -g "${GROUP}" "${USER}"
chown -R "${USER}:${GROUP}" "${SANDBOX}"
```

---

## Task 1 — Audit listening sockets and evidence quality

### Purpose

Collect an auditor-grade snapshot without assuming previous runs are still valid.

### Main command block

```bash
TASKLOG=/var/tmp/lab34c-task1.txt

echo "═══ ss broad view (numeric) ═══"          | tee "${TASKLOG}"
ss -tuna4                                      2>&1 | tee -a "${TASKLOG}"

echo "═══ ss listening + process map ═══"       | tee -a "${TASKLOG}"
ss -tlnp4                                      2>&1 | tee -a "${TASKLOG}"

echo "═══ socket summary counters ═══"          | tee -a "${TASKLOG}"
ss -s                                          2>&1 | tee -a "${TASKLOG}"

echo "═══ ssh ownership contrast (lsof) ═══"    | tee -a "${TASKLOG}"
lsof -i :22                                    2>&1 | tee -a "${TASKLOG}" || true

echo "═══ legacy comparison (netstat) ═══"      | tee -a "${TASKLOG}"
netstat -tlnp                                  2>&1 | tee -a "${TASKLOG}" || true

echo "exit was: $?"                            | tee -a "${TASKLOG}"
```

### Trap callout

- **T34-A:** if you forget `-n`, name lookup can delay output.
- **T34-B:** process columns from `ss -p` are privileged data; run as root for complete mapping.

### Journal write

```bash
JDIR=/root/rhcsa_journal/lab-34c/task1
cp /var/tmp/lab34c-task1.txt "${JDIR}/audit.txt"
```

---

## Task 2 — Destroy-restore drill for SSH listener (T41 resilience)

### Purpose

Simulate listener loss, then recover and re-verify:

1. Destroy: stop SSH service and confirm port 22 disappears.
2. Restore: start SSH service and confirm port 22 returns.

### Main command block

```bash
TASKLOG=/var/tmp/lab34c-task2.txt

echo "═══ DESTROY phase (stop sshd) ═══"        | tee "${TASKLOG}"
systemctl stop sshd                             2>&1 | tee -a "${TASKLOG}" || true
ss -tlnp4 | grep -E ':22(\s|$)'                 2>&1 | tee -a "${TASKLOG}" || echo "✅ port 22 absent after stop" | tee -a "${TASKLOG}"

echo "═══ RESTORE phase (start sshd) ═══"       | tee -a "${TASKLOG}"
systemctl start sshd                            2>&1 | tee -a "${TASKLOG}"
ss -tlnp4 | grep -E ':22(\s|$)'                 2>&1 | tee -a "${TASKLOG}"
lsof -i :22                                     2>&1 | tee -a "${TASKLOG}" || true

echo "exit was: $?"                             | tee -a "${TASKLOG}"
```

### Journal write

```bash
JDIR=/root/rhcsa_journal/lab-34c/task2
cp /var/tmp/lab34c-task2.txt "${JDIR}/destroy-restore.txt"
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

echo "── Lab 34c cleanup audit ──"
getent passwd "${USER}" >/dev/null && echo "❌ user remains" || echo "✅ user gone"
getent group "${GROUP}" >/dev/null && echo "❌ group remains" || echo "✅ group gone"
test -d "${SANDBOX}" && echo "❌ sandbox remains" || echo "✅ sandbox gone"
test -d "${USER_HOME}" && echo "❌ home remains" || echo "✅ home gone"

set -e
```

---

## Lab 34c Checklist

- [ ] Task 1 completed (audit captured: `ss -tuna4`, `ss -tlnp4`, `ss -s`, `lsof -i :22`, `netstat -tlnp`)
- [ ] Task 2 completed (destroy-restore drill proved port 22 disappearance and return)
- [ ] T34-A/T34-B plus T41/T44 risk notes documented in evidence
- [ ] Section 6 closeout audit shows four `✅` lines

---

## Author

**Kelvin R. Tobias**
[kelvinintech.com](https://kelvinintech.com) · [GitHub](https://github.com/kelvintechnical) · [LinkedIn](https://www.linkedin.com/in/kelvin-r-tobias-211949219)
