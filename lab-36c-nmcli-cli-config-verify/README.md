# Lab 36c: Verifying `nmcli` CLI Config — audit + destroy/restore

- **Series:** linux-ops-mastery — Network Configuration and Verification
- **Trilogy:** `36a` (RHCSA) -> `36b` (Ansible) -> `36c` (Verify — you are here)
- **Time Estimate:** 25-35 minutes
- **Tasks:** 2 (Task 1 = audit, Task 2 = destroy-restore drill)
- **Practice Directory (rotation slot 1):** `/bin`
- **Sandbox (Tier B):** `/tmp/lab36c` with `USER=labuser_36_nmcli`, `GROUP=labgrp_36_nmcli`
- **Traps rehearsed this lab:** **T36-A** · **T36-B** · **T41** · **T44**

> **Safety rule (hard):** verify only the test profile `lab36test` on `dummy-lab36`. Never alter your live management profile.

---

## LAB HEADER BLOCK

```bash
echo "🖥️  ENV: ${ENV:-DECLARE_ME}"
echo "📦  OS:  $(cat /etc/redhat-release 2>/dev/null || grep PRETTY_NAME /etc/os-release)"
echo "🕒  TIME: $(date -Is)"
echo "👤  USER: $(whoami)@$(hostname)"
echo "📁  PRACTICE DIR: /bin"
echo "⚠️  TRAP REMINDERS THIS LAB: T36-A T36-B T41 T44"
nmcli --version
nmcli con show
nmcli dev status
```

---

## Objective

1. Audit a test connection for profile state, device state, and evidence quality.
2. Prove recovery using a destroy-restore drill with `nmcli` only.

---

## Lab-Wide Setup — Tier B Sandbox

```bash
sudo -i

export SANDBOX=/tmp/lab36c
export GROUP=labgrp_36_nmcli
export USER=labuser_36_nmcli
export USER_HOME=${SANDBOX}/home_${USER}

mkdir -p "${SANDBOX}" "${USER_HOME}" /root/rhcsa_journal/lab-36c/task1 /root/rhcsa_journal/lab-36c/task2
getent group "${GROUP}" >/dev/null || groupadd "${GROUP}"
getent passwd "${USER}" >/dev/null || useradd -d "${USER_HOME}" -M -s /bin/bash -g "${GROUP}" "${USER}"
chown -R "${USER}:${GROUP}" "${SANDBOX}"
```

---

## Task 1 — Audit `lab36test` profile and runtime state

### Purpose

Gather journal-grade evidence that both persistent config and live state are correct.

### Main command block

```bash
TASKLOG=/tmp/lab36c/task1.txt

# Recreate test profile if missing (safe, test-only)
nmcli con show lab36test >/dev/null 2>&1 || \
  nmcli con add type dummy ifname dummy-lab36 con-name lab36test                         2>&1 | tee "${TASKLOG}"
nmcli con mod lab36test ipv4.method manual ipv4.addresses 10.99.0.1/24                   2>&1 | tee -a "${TASKLOG}"
nmcli con up lab36test                                                                     2>&1 | tee -a "${TASKLOG}"

echo "═══ AUDIT: profile view ═══"                                                         | tee -a "${TASKLOG}"
nmcli con show lab36test                                                                   2>&1 | tee -a "${TASKLOG}"
echo "═══ AUDIT: active and device state ═══"                                              | tee -a "${TASKLOG}"
nmcli -f NAME,DEVICE,TYPE,STATE con show --active                                         2>&1 | tee -a "${TASKLOG}"
nmcli dev status                                                                           2>&1 | tee -a "${TASKLOG}"
nmcli -t -f GENERAL.STATE con show lab36test                                               2>&1 | tee -a "${TASKLOG}"

echo "exit was: $?"                                                                        | tee -a "${TASKLOG}"
```

### Trap callout

- **T36-A:** if `GENERAL.STATE` is not `activated`, your config may be stored but not in effect.
- **T36-B:** every command above targets `lab36test` only.

### Journal write

```bash
cp /tmp/lab36c/task1.txt /root/rhcsa_journal/lab-36c/task1/audit.txt
```

---

## Task 2 — Destroy-restore drill for `lab36test`

### Purpose

Exercise full lifecycle confidence: remove the profile, prove it is gone, recreate, and verify active state again.

### Main command block

```bash
TASKLOG=/tmp/lab36c/task2.txt

echo "═══ DESTROY phase ═══"                                              | tee "${TASKLOG}"
nmcli con show lab36test >/dev/null 2>&1 && nmcli con down lab36test     2>&1 | tee -a "${TASKLOG}" || true
nmcli con show lab36test >/dev/null 2>&1 && nmcli con delete lab36test   2>&1 | tee -a "${TASKLOG}" || true
nmcli con show lab36test                                                  2>&1 | tee -a "${TASKLOG}" || echo "✅ lab36test absent" | tee -a "${TASKLOG}"

echo "═══ RESTORE phase ═══"                                              | tee -a "${TASKLOG}"
nmcli con add type dummy ifname dummy-lab36 con-name lab36test            2>&1 | tee -a "${TASKLOG}"
nmcli con mod lab36test ipv4.method manual ipv4.addresses 10.99.0.1/24    2>&1 | tee -a "${TASKLOG}"
nmcli con up lab36test                                                     2>&1 | tee -a "${TASKLOG}"
nmcli -t -f GENERAL.STATE con show lab36test                               2>&1 | tee -a "${TASKLOG}"
nmcli dev status                                                            2>&1 | tee -a "${TASKLOG}"

echo "exit was: $?"                                                         | tee -a "${TASKLOG}"
```

### Journal write

```bash
cp /tmp/lab36c/task2.txt /root/rhcsa_journal/lab-36c/task2/destroy-restore.txt
```

---

## Lab Closeout — Bulletproof Teardown (Section 6)

```bash
set +e

nmcli con show lab36test >/dev/null 2>&1 && nmcli con down lab36test >/dev/null 2>&1
nmcli con show lab36test >/dev/null 2>&1 && nmcli con delete lab36test >/dev/null 2>&1

if getent passwd "${USER}" >/dev/null 2>&1; then
  userdel -r "${USER}" 2>/dev/null
fi
if getent group "${GROUP}" >/dev/null 2>&1; then
  groupdel "${GROUP}" 2>/dev/null
fi

rm -rf "${SANDBOX}"

echo "── Lab 36c cleanup audit ──"
getent passwd "${USER}" >/dev/null && echo "❌ user remains" || echo "✅ user gone"
getent group "${GROUP}" >/dev/null && echo "❌ group remains" || echo "✅ group gone"
test -d "${SANDBOX}" && echo "❌ sandbox remains" || echo "✅ sandbox gone"
test -d "${USER_HOME}" && echo "❌ home remains" || echo "✅ home gone"

set -e
```

---

## Lab 36c Checklist

- [ ] Task 1 completed (audit captures `nmcli con show`, active state, and `nmcli dev status`)
- [ ] Task 2 completed (destroy-restore drill successfully reactivated `lab36test`)
- [ ] T36-A and T36-B checks explicitly validated
- [ ] Section 6 closeout audit shows four `✅` lines

---

## Author

**Kelvin R. Tobias**
[kelvinintech.com](https://kelvinintech.com) · [GitHub](https://github.com/kelvintechnical) · [LinkedIn](https://www.linkedin.com/in/kelvin-r-tobias-211949219)
