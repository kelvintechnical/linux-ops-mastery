# Lab 45c: Verifying Append-Only Controls — audit + destroy/restore

- **Series:** linux-ops-mastery — File Attributes and Tamper Resistance
- **Trilogy:** `45a` (RHCSA) -> `45b` (Ansible) -> `45c` (Verify — you are here)
- **Time Estimate:** 25-35 minutes
- **Tasks:** 2 (Task 1 = audit, Task 2 = destroy-restore drill)
- **Practice Directory (rotation slot 23):** `/var`
- **Sandbox (Tier B):** `/tmp/lab45c` with `USER=labuser_45_append`, `GROUP=labgrp_45_append`
- **Traps rehearsed this lab:** **T45-A** · **T45-B** · **T41** · **T44**

> **This lab verifies** append-only behavior is observable, repeatable, and recoverable under teardown pressure.

---

## LAB HEADER BLOCK

```bash
echo "🖥️  ENV:   ${ENV:-DECLARE_ME}"
echo "📦  OS:    $(cat /etc/redhat-release 2>/dev/null || grep PRETTY_NAME /etc/os-release)"
echo "🕒  TIME:  $(date -Is)"
echo "👤  USER:  $(whoami)@$(hostname)"
echo "📁  PRACTICE DIR: /var"
echo "⚠️  TRAP REMINDERS THIS LAB: T45-A T45-B T41 T44"
command -v chattr
command -v lsattr
```

> **STOP — paste header output before setup.**

---

## Objective

1. Audit append-only state and prove `lsattr` evidence includes the `a` flag in the journal.
2. Run destroy-restore drill: `chattr -a` -> `rm` -> recreate -> `chattr +a`.

---

## Lab-Wide Setup — Tier B Sandbox

```bash
sudo -i

export SANDBOX=/tmp/lab45c
export GROUP=labgrp_45_append
export USER=labuser_45_append
export USER_HOME=${SANDBOX}/home_${USER}

mkdir -p "${SANDBOX}" "${USER_HOME}" /root/rhcsa_journal/lab-45c/task1 /root/rhcsa_journal/lab-45c/task2
getent group "${GROUP}" >/dev/null || groupadd "${GROUP}"
getent passwd "${USER}" >/dev/null || useradd -d "${USER_HOME}" -M -s /bin/bash -g "${GROUP}" "${USER}"
chown -R "${USER}:${GROUP}" "${SANDBOX}"
mkdir -p /tmp/lab45c
touch /tmp/lab45c/audit.log
chattr +a /tmp/lab45c/audit.log
```

---

## Task 1 — Audit append-only evidence with `lsattr`

### Purpose

Produce auditor-grade proof that the append-only bit is set and logged.

### Main command block

```bash
TASKLOG=/var/tmp/lab45c-task1.txt

echo "═══ append-only audit snapshot ═══"           | tee "${TASKLOG}"
lsattr /tmp/lab45c/audit.log                       2>&1 | tee -a "${TASKLOG}"
echo "audit line $(date -Is)" >> /tmp/lab45c/audit.log
cat /tmp/lab45c/audit.log                          2>&1 | tee -a "${TASKLOG}"

echo "overwrite trap demo (expected fail)"         | tee -a "${TASKLOG}"
echo "blocked" > /tmp/lab45c/audit.log             2>&1 | tee -a "${TASKLOG}" || true

echo "exit was: $?"                                | tee -a "${TASKLOG}"
```

### Journal write

```bash
cp /var/tmp/lab45c-task1.txt /root/rhcsa_journal/lab-45c/task1/audit.txt
```

---

## Task 2 — Destroy-restore drill (T41 + T45-B)

### Purpose

Prove recovery discipline: remove protection first, remove file, recreate artifact, then restore append-only.

### Main command block

```bash
TASKLOG=/var/tmp/lab45c-task2.txt

echo "═══ DESTROY phase ═══"                         | tee "${TASKLOG}"
chattr -a /tmp/lab45c/audit.log
rm -f /tmp/lab45c/audit.log
test ! -e /tmp/lab45c/audit.log && echo "✅ destroyed" | tee -a "${TASKLOG}"

echo "═══ RESTORE phase ═══"                         | tee -a "${TASKLOG}"
touch /tmp/lab45c/audit.log
echo "recreated $(date -Is)" >> /tmp/lab45c/audit.log
chattr +a /tmp/lab45c/audit.log
lsattr /tmp/lab45c/audit.log                         2>&1 | tee -a "${TASKLOG}"

echo "exit was: $?"                                  | tee -a "${TASKLOG}"
```

### Trap callout

- **T45-B:** forgetting `chattr -a` before `rm` causes failed cleanup/rotation.
- **T41:** verify-mode means you must rehearse destroy and restore, not just inspect.

### Journal write

```bash
cp /var/tmp/lab45c-task2.txt /root/rhcsa_journal/lab-45c/task2/destroy-restore.txt
```

---

## Lab Closeout — Bulletproof Teardown (Section 6)

```bash
set +e

# CRITICAL: cleanup MUST clear append-only before rm
if [ -e /tmp/lab45c/audit.log ]; then
  chattr -a /tmp/lab45c/audit.log 2>/dev/null
fi

rm -f /tmp/lab45c/audit.log

if getent passwd "${USER}" >/dev/null 2>&1; then
  userdel -r "${USER}" 2>/dev/null
fi
if getent group "${GROUP}" >/dev/null 2>&1; then
  groupdel "${GROUP}" 2>/dev/null
fi

rm -rf "${SANDBOX}" /tmp/lab45c

echo "── Lab 45c cleanup audit ──"
getent passwd "${USER}" >/dev/null && echo "❌ user remains" || echo "✅ user gone"
getent group "${GROUP}" >/dev/null && echo "❌ group remains" || echo "✅ group gone"
test -d "${SANDBOX}" && echo "❌ sandbox remains" || echo "✅ sandbox gone"
test -e /tmp/lab45c/audit.log && echo "❌ append file remains" || echo "✅ append file gone"

set -e
```

---

## Lab 45c Checklist

- [ ] Task 1 completed (`lsattr` evidence shows append-only state with `a` in journal capture)
- [ ] Task 2 completed (destroy-restore drill: `-a` -> remove -> recreate -> `+a`)
- [ ] T45-A/T45-B plus T41/T44 risk notes documented in evidence
- [ ] Section 6 closeout audit shows teardown success

---

## Author

**Kelvin R. Tobias**
[kelvinintech.com](https://kelvinintech.com) · [GitHub](https://github.com/kelvintechnical) · [LinkedIn](https://www.linkedin.com/in/kelvin-r-tobias-211949219)
