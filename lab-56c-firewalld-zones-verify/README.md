# Lab 56c: Verifying firewalld Zone Visibility - audit + destroy/restore evidence

- **Series:** linux-ops-mastery - Security Administration (firewalld)
- **Trilogy:** [`56a`](../lab-56a-firewalld-zones-rhcsa/) (RHCSA) -> [`56b`](../lab-56b-firewalld-zones-ansible/) (Ansible) -> `56c` (Verify - you are here)
- **Time Estimate:** 20-30 minutes
- **Tasks:** 2 (Task 1 = audit, Task 2 = destroy-restore drill)
- **Practice Directory (objective context):** `/bin` (inspection context), `/tmp/lab56c` (write target)
- **Sandbox (Tier B):** `/tmp/lab56c` with `USER=labuser_56_fwzones`, `GROUP=labgrp_56_fwzones`
- **Traps rehearsed:** **T56-A** (service state precheck) · **T56-B** (default-zone-only confusion) · **T41** (destroy-restore required) · **T44** (closeout audit)

> **Read-only scope:** verify and restore evidence only. No firewalld zone/service/port changes.

---

## LAB HEADER BLOCK

```bash
echo "📁 PRACTICE DIR: /bin (inspect), /tmp/lab56c (write)"
echo "👤 USER: $(whoami)@$(hostname)"
echo "🕒 TIME: $(date -Is)"
echo "⚠️ TRAPS: T56-A T56-B T41 T44"
systemctl is-active firewalld
ls -la /root/rhcsa_journal/lab-56a /root/rhcsa_journal/lab-56b 2>/dev/null || true
```

---

## Objective

1. Audit zone-state evidence from 56a/56b and refresh it with current read-only snapshots.
2. Rehearse destroy-restore of verification artifacts (T41) without any firewall mutation.

---

## Lab-Wide Setup - Tier B Sandbox

```bash
sudo -i

export SANDBOX=/tmp/lab56c
export GROUP=labgrp_56_fwzones
export USER=labuser_56_fwzones
export USER_HOME=${SANDBOX}/home_${USER}

mkdir -p "${SANDBOX}" "${USER_HOME}" /root/rhcsa_journal/lab-56c/task1 /root/rhcsa_journal/lab-56c/task2
getent group "${GROUP}" >/dev/null || groupadd "${GROUP}"
getent passwd "${USER}" >/dev/null || useradd -d "${USER_HOME}" -M -s /bin/bash -g "${GROUP}" "${USER}"
chown -R "${USER}:${GROUP}" "${SANDBOX}"
```

---

## Task 1 - Audit firewalld zone state in journal artifacts

### Purpose

Collect auditor-grade evidence showing current zone view and prior trilogy outputs in one place.

### Main command block

```bash
TASKLOG=/tmp/lab56c/task1.txt

echo "═══ service status (T56-A) ═══" | tee "${TASKLOG}"
systemctl is-active firewalld | tee -a "${TASKLOG}"

echo "═══ current runtime zone view ═══" | tee -a "${TASKLOG}"
firewall-cmd --get-default-zone | tee -a "${TASKLOG}"
firewall-cmd --get-zones | tee -a "${TASKLOG}"
firewall-cmd --get-active-zones | tee -a "${TASKLOG}"
firewall-cmd --list-all | tee -a "${TASKLOG}"
firewall-cmd --list-all --zone=public | tee -a "${TASKLOG}"
firewall-cmd --list-all --zone=trusted | tee -a "${TASKLOG}"

echo "═══ prior evidence inventory ═══" | tee -a "${TASKLOG}"
ls -la /root/rhcsa_journal/lab-56a/task1 /root/rhcsa_journal/lab-56a/task2 2>&1 | tee -a "${TASKLOG}"
ls -la /root/rhcsa_journal/lab-56b/task1 /root/rhcsa_journal/lab-56b/task2 2>&1 | tee -a "${TASKLOG}"

echo "exit was: $?" | tee -a "${TASKLOG}"
```

### Trap callout

- **T56-B:** this task intentionally captures both plain `--list-all` and explicit `--zone=...` outputs so auditors can spot scope mistakes quickly.

### Journal write

```bash
cp /tmp/lab56c/task1.txt /root/rhcsa_journal/lab-56c/task1/audit.txt
```

---

## Task 2 - Destroy-restore drill for verification evidence (T41)

### Purpose

Destroy local verify artifacts and restore them from journal snapshots to prove recoverability.

### Main command block

```bash
TASKLOG=/tmp/lab56c/task2.txt

echo "═══ destroy phase ═══" | tee "${TASKLOG}"
cp /tmp/lab56c/task1.txt /tmp/lab56c/task1.pre-destroy.txt
sha256sum /tmp/lab56c/task1.pre-destroy.txt | tee -a "${TASKLOG}"
rm -f /tmp/lab56c/task1.txt
test ! -f /tmp/lab56c/task1.txt && echo "✅ local verify copy destroyed" | tee -a "${TASKLOG}"

echo "═══ restore phase (read-only source: journal) ═══" | tee -a "${TASKLOG}"
cp /root/rhcsa_journal/lab-56c/task1/audit.txt /tmp/lab56c/task1.txt
sha256sum /tmp/lab56c/task1.txt /root/rhcsa_journal/lab-56c/task1/audit.txt | tee -a "${TASKLOG}"
diff -u /tmp/lab56c/task1.txt /root/rhcsa_journal/lab-56c/task1/audit.txt | tee -a "${TASKLOG}"
echo "✅ restore completed from journal without firewall changes" | tee -a "${TASKLOG}"

echo "exit was: $?" | tee -a "${TASKLOG}"
```

### Trap callout

- **T41:** verify labs must include destroy-restore practice, not just passive inspection.

### Journal write

```bash
cp /tmp/lab56c/task2.txt /root/rhcsa_journal/lab-56c/task2/destroy-restore.txt
```

---

## Lab Closeout - Bulletproof Teardown (Section 6)

```bash
set +e
userdel -r "${USER}" 2>/dev/null
groupdel "${GROUP}" 2>/dev/null
rm -rf "${SANDBOX}"

echo "── Lab 56c cleanup audit ──"
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
