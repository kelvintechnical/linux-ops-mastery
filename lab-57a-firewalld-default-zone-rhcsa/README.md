# Lab 57a: Changing Default Firewall Zone (RHCSA) — `--set-default-zone`, `--change-interface`, `--reload`

- **Series:** linux-ops-mastery — Firewalld Zone Operations
- **Trilogy:** `57a` (RHCSA hand-typed) -> `57b` (Ansible mirror) -> `57c` (Verify capstone)
- **Time Estimate:** 25-35 minutes
- **Tasks:** 2
- **Practice Directory (rotation #57):** `/sbin` (command context)
- **Sandbox (Tier B):** `/tmp/lab57a` with `USER=labuser_57_fwdef`, `GROUP=labgrp_57_fwdef`
- **Traps rehearsed this lab:** **T57-A** (switching default zone can cut SSH) · **T57-B** (`--set-default-zone` is permanent immediately) · **T41** · **T44**

> **CRITICAL SAFETY:** Always capture the original default zone first and always restore it at the end. Use a safe target zone (`internal` or `dmz`) only when console access exists or an `at` rollback safeguard is armed.

---

## LAB HEADER BLOCK

```bash
echo "🕒  TIME: $(date -Is)"
echo "👤  USER: $(whoami)@$(hostname)"
echo "📁  PRACTICE DIR: /sbin"
echo "⚠️  TRAPS: T57-A T57-B T41 T44"
command -v firewall-cmd
firewall-cmd --state
firewall-cmd --get-default-zone
```

> **STOP — paste header output before setup.**

---

## Objective

1. Change default zone safely with `firewall-cmd --set-default-zone=...` and verify before/after state.
2. Rehearse interface reassignment with `--change-interface` using a disposable test NIC or documented skip.

---

## Lab-Wide Setup — Tier B Sandbox

```bash
sudo -i

export SANDBOX=/tmp/lab57a
export GROUP=labgrp_57_fwdef
export USER=labuser_57_fwdef
export USER_HOME=${SANDBOX}/home_${USER}

mkdir -p "${SANDBOX}" "${USER_HOME}" /root/rhcsa_journal/lab-57a/task1 /root/rhcsa_journal/lab-57a/task2
getent group "${GROUP}" >/dev/null || groupadd "${GROUP}"
getent passwd "${USER}" >/dev/null || useradd -d "${USER_HOME}" -M -s /bin/bash -g "${GROUP}" "${USER}"
chown -R "${USER}:${GROUP}" "${SANDBOX}"
```

---

## Task 1 — Safe default-zone switch with guaranteed restore

### Purpose

Build reflex timing for the exact RHCSA flow: record original zone, switch to safe target, verify, reload check, then restore in the same script.

### Main command block

```bash
TASKLOG=/var/tmp/lab57a-task1.txt

orig=$(firewall-cmd --get-default-zone)
target=internal
rollback_minutes=3

echo "original default zone: ${orig}"                     | tee "${TASKLOG}"
echo "target zone: ${target}"                             | tee -a "${TASKLOG}"
echo "${orig}" | tee /root/rhcsa_journal/lab-57a/original_default_zone.txt >/dev/null

# T57-A safety: schedule automatic rollback in case SSH drops.
echo "firewall-cmd --set-default-zone=${orig}" | at now + ${rollback_minutes} minutes

echo "before switch:"                                     | tee -a "${TASKLOG}"
firewall-cmd --get-default-zone                           | tee -a "${TASKLOG}"

firewall-cmd --set-default-zone="${target}"               | tee -a "${TASKLOG}"
echo "after switch:"                                      | tee -a "${TASKLOG}"
firewall-cmd --get-default-zone                           | tee -a "${TASKLOG}"

firewall-cmd --reload                                     | tee -a "${TASKLOG}"
firewall-cmd --get-default-zone                           | tee -a "${TASKLOG}"

# CRITICAL: restore original zone in same task script.
firewall-cmd --set-default-zone="${orig}"                 | tee -a "${TASKLOG}"
echo "after restore:"                                     | tee -a "${TASKLOG}"
firewall-cmd --get-default-zone                           | tee -a "${TASKLOG}"

atq | tail -n 1                                           | tee -a "${TASKLOG}" || true
echo "exit was: $?"                                       | tee -a "${TASKLOG}"
```

### Trap callout

- **T57-A:** if SSH is not allowed in the new zone, remote shell can die immediately.
- **T57-B:** do **not** add `--permanent`; `--set-default-zone` is already persistent.

### Journal write

```bash
cp /var/tmp/lab57a-task1.txt /root/rhcsa_journal/lab-57a/task1/evidence.txt
```

---

## Task 2 — `--change-interface` drill (test NIC or safe skip)

### Purpose

Practice the interface-zone move command without risking production NIC loss.

### Main command block

```bash
TASKLOG=/var/tmp/lab57a-task2.txt
orig=$(firewall-cmd --get-default-zone)
test_zone=dmz
test_if=dummy0

echo "original default zone: ${orig}"                     | tee "${TASKLOG}"
echo "test interface candidate: ${test_if}"               | tee -a "${TASKLOG}"

if ip link show "${test_if}" >/dev/null 2>&1; then
  firewall-cmd --zone="${test_zone}" --change-interface="${test_if}" 2>&1 | tee -a "${TASKLOG}"
  firewall-cmd --get-active-zones                         | tee -a "${TASKLOG}"
else
  echo "SKIP: ${test_if} not present. Documented command:" | tee -a "${TASKLOG}"
  echo "firewall-cmd --zone=${test_zone} --change-interface=${test_if}" | tee -a "${TASKLOG}"
fi

# Defensive restore pattern for default zone.
firewall-cmd --set-default-zone="${orig}"                 | tee -a "${TASKLOG}"
firewall-cmd --reload                                     | tee -a "${TASKLOG}"
firewall-cmd --get-default-zone                           | tee -a "${TASKLOG}"
echo "exit was: $?"                                       | tee -a "${TASKLOG}"
```

### Journal write

```bash
cp /var/tmp/lab57a-task2.txt /root/rhcsa_journal/lab-57a/task2/evidence.txt
```

---

## Lab Closeout — Bulletproof Teardown (Section 6)

```bash
set +e

orig_default_file=/root/rhcsa_journal/lab-57a/original_default_zone.txt
if [ -f "${orig_default_file}" ]; then
  orig="$(cat "${orig_default_file}")"
else
  orig="public"
fi

# CRITICAL SAFETY: always restore original default zone at closeout.
firewall-cmd --set-default-zone="${orig}" 2>/dev/null
firewall-cmd --reload 2>/dev/null

if getent passwd "${USER}" >/dev/null 2>&1; then
  userdel -r "${USER}" 2>/dev/null
fi
if getent group "${GROUP}" >/dev/null 2>&1; then
  groupdel "${GROUP}" 2>/dev/null
fi

rm -rf "${SANDBOX}"

echo "── Lab 57a cleanup audit ──"
firewall-cmd --get-default-zone
getent passwd "${USER}" >/dev/null && echo "❌ user remains" || echo "✅ user gone"
getent group "${GROUP}" >/dev/null && echo "❌ group remains" || echo "✅ group gone"
test -d "${SANDBOX}" && echo "❌ sandbox remains" || echo "✅ sandbox gone"
test -d "${USER_HOME}" && echo "❌ home remains" || echo "✅ home gone"

set -e
```

> Original zone file is written during Task 1 and consumed by Section 6 closeout restore logic.

---

## Lab 57a Checklist

- [ ] Task 1 completed (`orig` captured, `internal` switch verified, restore done in same script)
- [ ] Task 2 completed (`--change-interface` run on test NIC or safely documented as skip)
- [ ] T57-A and T57-B risks recorded with T41/T44 awareness
- [ ] Section 6 closeout restored original default zone and printed cleanup audit

---

## Author

**Kelvin R. Tobias**
[kelvinintech.com](https://kelvinintech.com) · [GitHub](https://github.com/kelvintechnical) · [LinkedIn](https://www.linkedin.com/in/kelvin-r-tobias-211949219)
