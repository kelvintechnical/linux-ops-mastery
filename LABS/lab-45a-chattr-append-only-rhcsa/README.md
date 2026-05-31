# Lab 45a: Append-Only File Attribute (RHCSA) — `chattr +a`, `chattr -a`, `lsattr`

- **Series:** linux-ops-mastery — File Attributes and Tamper Resistance
- **Trilogy:** `45a` (RHCSA hand-typed) -> `45b` (Ansible mirror) -> `45c` (Verify capstone)
- **Time Estimate:** 25-35 minutes
- **Tasks:** 2
- **Practice Directory (rotation slot 23):** `/var`
- **Sandbox (Tier B):** `/tmp/lab45a` with `USER=labuser_45_append`, `GROUP=labgrp_45_append`
- **Traps rehearsed this lab:** **T45-A** (`chattr +a` allows `>>` but blocks `>`) · **T45-B** (`chattr -a` required before rotation/removal) · **T41** · **T44**

> **This lab's topic:** use append-only mode to make log writes tamper-resistant while still allowing safe appends.

---

## LAB HEADER BLOCK

```bash
echo "🖥️  ENV:   ${ENV:-DECLARE_ME}"
echo "📦  OS:    $(cat /etc/redhat-release 2>/dev/null || grep PRETTY_NAME /etc/os-release)"
echo "🕒  TIME:  $(date -Is)"
echo "👤  USER:  $(whoami)@$(hostname)"
echo "📁  PRACTICE DIR: /var"
echo "⚠️  TRAP REMINDERS THIS LAB: T45-A T45-B T41 T44"
ls -ld /var
command -v chattr
command -v lsattr
```

> **STOP — paste header output before setup.**

---

## Objective

1. Apply append-only (`+a`) and prove `>>` works while `>` is blocked.
2. Practice safe teardown: remove append-only (`-a`) before `rm` and reapply protection.

---

## Lab-Wide Setup — Tier B Sandbox

```bash
sudo -i

export SANDBOX=/tmp/lab45a
export GROUP=labgrp_45_append
export USER=labuser_45_append
export USER_HOME=${SANDBOX}/home_${USER}

mkdir -p "${SANDBOX}" "${USER_HOME}" /root/rhcsa_journal/lab-45a/task1 /root/rhcsa_journal/lab-45a/task2
getent group "${GROUP}" >/dev/null || groupadd "${GROUP}"
getent passwd "${USER}" >/dev/null || useradd -d "${USER_HOME}" -M -s /bin/bash -g "${GROUP}" "${USER}"
chown -R "${USER}:${GROUP}" "${SANDBOX}"
mkdir -p /tmp/lab45a
touch /tmp/lab45a/audit.log
```

---

## Task 1 — Set append-only and demonstrate T45-A behavior

### Purpose

Build the exact exam reflex: append-only protects against clobber and delete, but still accepts appends.

### Main command block

```bash
TASKLOG=/var/tmp/lab45a-task1.txt

sudo chattr +a /tmp/lab45a/audit.log
lsattr /tmp/lab45a/audit.log                          2>&1 | tee "${TASKLOG}"

echo "line: append allowed $(date -Is)" >> /tmp/lab45a/audit.log
cat /tmp/lab45a/audit.log                             2>&1 | tee -a "${TASKLOG}"

echo "line: overwrite should fail" > /tmp/lab45a/audit.log 2>&1 | tee -a "${TASKLOG}" || true
rm -f /tmp/lab45a/audit.log                           2>&1 | tee -a "${TASKLOG}" || true

echo "exit was: $?"                                   | tee -a "${TASKLOG}"
```

### Trap callout

- **T45-A:** `>>` works with `+a`, but `>` fails by design.
- Delete is also blocked while `+a` is present.

### Journal write

```bash
cp /var/tmp/lab45a-task1.txt /root/rhcsa_journal/lab-45a/task1/evidence.txt
```

---

## Task 2 — Safe remove/recreate cycle (T45-B)

### Purpose

Rehearse the teardown rule you must not skip: **`chattr -a` before `rm`**.

### Main command block

```bash
TASKLOG=/var/tmp/lab45a-task2.txt

echo "═══ remove protection before removal ═══"       | tee "${TASKLOG}"
sudo chattr -a /tmp/lab45a/audit.log
lsattr /tmp/lab45a/audit.log                          2>&1 | tee -a "${TASKLOG}"

rm -f /tmp/lab45a/audit.log
test ! -e /tmp/lab45a/audit.log && echo "✅ removed"  | tee -a "${TASKLOG}"

touch /tmp/lab45a/audit.log
echo "line: recreated after cleanup" >> /tmp/lab45a/audit.log
sudo chattr +a /tmp/lab45a/audit.log
lsattr /tmp/lab45a/audit.log                          2>&1 | tee -a "${TASKLOG}"

echo "exit was: $?"                                   | tee -a "${TASKLOG}"
```

### Trap callout

- **T45-B:** file rotation/removal fails unless you clear append-only first.
- Treat this the same teardown hazard pattern as immutable (`+i`) labs.

### Journal write

```bash
cp /var/tmp/lab45a-task2.txt /root/rhcsa_journal/lab-45a/task2/evidence.txt
```

---

## Lab Closeout — Bulletproof Teardown (Section 6)

```bash
set +e

# CRITICAL: clear append-only before rm
if [ -e /tmp/lab45a/audit.log ]; then
  chattr -a /tmp/lab45a/audit.log 2>/dev/null
fi

rm -f /tmp/lab45a/audit.log

if getent passwd "${USER}" >/dev/null 2>&1; then
  userdel -r "${USER}" 2>/dev/null
fi
if getent group "${GROUP}" >/dev/null 2>&1; then
  groupdel "${GROUP}" 2>/dev/null
fi

rm -rf "${SANDBOX}" /tmp/lab45a

echo "── Lab 45a cleanup audit ──"
getent passwd "${USER}" >/dev/null && echo "❌ user remains" || echo "✅ user gone"
getent group "${GROUP}" >/dev/null && echo "❌ group remains" || echo "✅ group gone"
test -d "${SANDBOX}" && echo "❌ sandbox remains" || echo "✅ sandbox gone"
test -e /tmp/lab45a/audit.log && echo "❌ append file remains" || echo "✅ append file gone"

set -e
```

---

## Lab 45a Checklist

- [ ] Task 1 completed (`+a` set; `>>` succeeded; `>` and `rm` failed under protection)
- [ ] Task 2 completed (`-a` -> `rm` -> recreate -> `+a` restore)
- [ ] T45-A and T45-B notes captured with T41/T44 awareness
- [ ] Section 6 closeout audit shows teardown success

---

## Author

**Kelvin R. Tobias**
[kelvinintech.com](https://kelvinintech.com) · [GitHub](https://github.com/kelvintechnical) · [LinkedIn](https://www.linkedin.com/in/kelvin-r-tobias-211949219)
