# Lab 42c: Verifying SUID Executables — audit + destroy/restore

- **Series:** linux-ops-mastery — Privilege, Permissions, and Security Posture
- **Trilogy:** `42a` (RHCSA) -> `42b` (Ansible) -> `42c` (Verify — you are here)
- **Time Estimate:** 25-35 minutes
- **Tasks:** 2
- **Practice Directory (rotation slot 42):** `/boot`
- **Sandbox (Tier B):** `/tmp/lab42c` with `USER=labuser_42_suid`, `GROUP=labgrp_42_suid`
- **Traps rehearsed this lab:** **T42-A** · **T42-B** · **T41** · **T44**

> **This lab verifies** SUID state with `stat`, then forces a safe destroy-restore cycle that clears SUID (`0755`) and proves cleanup.

---

## LAB HEADER BLOCK

```bash
echo "🖥️  ENV:   ${ENV:-DECLARE_ME}"
echo "📦  OS:    $(cat /etc/redhat-release 2>/dev/null || grep PRETTY_NAME /etc/os-release)"
echo "🕒  TIME:  $(date -Is)"
echo "👤  USER:  $(whoami)@$(hostname)"
echo "📁  PRACTICE DIR: /boot"
echo "⚠️  TRAP REMINDERS THIS LAB: T42-A T42-B T41 T44"
ls -ld /boot
```

---

## Objective

1. Audit SUID mode, ownership, and execution semantics of lab artifacts using `stat`.
2. Perform destroy-restore drill: remove SUID (`chmod 0755`) and verify privileged behavior disappears.
3. End with mandatory cleanup of all copied SUID binaries.

---

## Lab-Wide Setup — Tier B Sandbox

```bash
sudo -i

export SANDBOX=/tmp/lab42c
export GROUP=labgrp_42_suid
export USER=labuser_42_suid
export USER_HOME=${SANDBOX}/home_${USER}

mkdir -p "${SANDBOX}" "${USER_HOME}" /root/rhcsa_journal/lab-42c/task1 /root/rhcsa_journal/lab-42c/task2
getent group "${GROUP}" >/dev/null || groupadd "${GROUP}"
getent passwd "${USER}" >/dev/null || useradd -d "${USER_HOME}" -M -s /bin/bash -g "${GROUP}" "${USER}"
chown -R "${USER}:${GROUP}" "${SANDBOX}"

# Build verify target
cp /usr/bin/cat /tmp/lab42c/labcat
chown root:root /tmp/lab42c/labcat
chmod 4755 /tmp/lab42c/labcat
```

---

## Task 1 — Audit SUID state via `stat`

### Purpose

Produce audit-grade evidence for mode, owner, and behavior before changes.

### Main command block

```bash
TASKLOG=/tmp/lab42c/task1.txt

echo "═══ baseline permission audit ═══"                   | tee "${TASKLOG}"
stat -c '%A %a %U:%G %n' /tmp/lab42c/labcat              | tee -a "${TASKLOG}"
ls -l /tmp/lab42c/labcat                                  | tee -a "${TASKLOG}"

echo "═══ global SUID discovery sample ═══"               | tee -a "${TASKLOG}"
find / -perm -4000 -type f 2>/dev/null | head -n 15      | tee -a "${TASKLOG}"

echo "═══ behavior proof as non-root ═══"                 | tee -a "${TASKLOG}"
sudo -u "${USER}" /tmp/lab42c/labcat /etc/shadow | head -n 2 | tee -a "${TASKLOG}"

echo "exit was: $?"                                       | tee -a "${TASKLOG}"
```

### Journal write

```bash
cp /tmp/lab42c/task1.txt /root/rhcsa_journal/lab-42c/task1/evidence.txt
```

---

## Task 2 — Destroy-restore drill (clear SUID to `0755`)

### Purpose

Rehearse T41-style verification discipline: change state, re-audit, and prove effect difference.

### Main command block

```bash
TASKLOG=/tmp/lab42c/task2.txt

echo "═══ DESTROY phase: clear SUID ═══"                  | tee "${TASKLOG}"
chmod 0755 /tmp/lab42c/labcat
stat -c '%A %a %U:%G %n' /tmp/lab42c/labcat              | tee -a "${TASKLOG}"
ls -l /tmp/lab42c/labcat                                  | tee -a "${TASKLOG}"

echo "═══ verify behavior changed ═══"                    | tee -a "${TASKLOG}"
sudo -u "${USER}" /tmp/lab42c/labcat /etc/shadow 2>&1 | head -n 3 | tee -a "${TASKLOG}" || true

echo "═══ RESTORE phase (controlled) ═══"                 | tee -a "${TASKLOG}"
chmod 4755 /tmp/lab42c/labcat
stat -c '%A %a %U:%G %n' /tmp/lab42c/labcat              | tee -a "${TASKLOG}"
sudo -u "${USER}" /tmp/lab42c/labcat /etc/shadow | head -n 2 | tee -a "${TASKLOG}"

echo "exit was: $?"                                       | tee -a "${TASKLOG}"
```

### Trap callout

- **T42-A:** uppercase `S` indicates broken execute path even if SUID bit is set.
- **T42-B:** script-based SUID "tests" are invalid; only binaries are meaningful.

### Journal write

```bash
cp /tmp/lab42c/task2.txt /root/rhcsa_journal/lab-42c/task2/evidence.txt
```

---

## Lab Closeout — Bulletproof Teardown (Section 6)

```bash
set +e

# Mandatory SUID cleanup first (security)
chmod 0755 /tmp/lab42c/labcat 2>/dev/null
rm -f /tmp/lab42c/labcat /tmp/lab42c/task1.txt /tmp/lab42c/task2.txt

if getent passwd "${USER}" >/dev/null 2>&1; then
  userdel -r "${USER}" 2>/dev/null
fi
if getent group "${GROUP}" >/dev/null 2>&1; then
  groupdel "${GROUP}" 2>/dev/null
fi

rm -rf "${SANDBOX}"

echo "── Lab 42c cleanup audit ──"
getent passwd "${USER}" >/dev/null && echo "❌ user remains" || echo "✅ user gone"
getent group "${GROUP}" >/dev/null && echo "❌ group remains" || echo "✅ group gone"
test -d "${SANDBOX}" && echo "❌ sandbox remains" || echo "✅ sandbox gone"
test -e /tmp/lab42c/labcat && echo "❌ suid labcat remains" || echo "✅ suid labcat gone"

set -e
```

---

## Lab 42c Checklist

- [ ] Task 1 completed (`stat` + `find / -perm -4000` audit evidence captured)
- [ ] Task 2 completed (destroy phase set `0755`; restore phase re-applied `4755`; behavior difference proven)
- [ ] All SUID copies removed from `/tmp/lab42c`
- [ ] Section 6 closeout ended with `✅` lines

---

## Author

**Kelvin R. Tobias**
[kelvinintech.com](https://kelvinintech.com) · [GitHub](https://github.com/kelvintechnical) · [LinkedIn](https://www.linkedin.com/in/kelvin-r-tobias-211949219)
