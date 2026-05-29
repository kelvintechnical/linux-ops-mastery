# Lab 19c: Verifying File Concatenation (Audit + Restore)

- **Series:** linux-ops-mastery — Text Streams and File Composition
- **Trilogy:** `19a` (RHCSA) → `19b` (Ansible) → `19c` (Verify)
- **Time Estimate:** 25–35 minutes
- **Tasks:** 2
- **Practice Directory (rotation #19):** `/usr`
- **Sandbox (Tier B):** `/tmp/lab19c` with `USER=labuser_19_catjoin`, `GROUP=labgrp_19_catjoin`
- **Traps rehearsed this lab:** **T19-A** · **T19-B** · **T41** · **T44**

> **This lab's practice directory is: `/usr`** (read-only reference) while verification artifacts are in `/tmp/lab19c`.

---

## LAB HEADER BLOCK

```bash
echo "📦 OS: $(cat /etc/redhat-release 2>/dev/null || grep PRETTY_NAME /etc/os-release)"
echo "🕒 TIME: $(date -Is)"
echo "👤 USER: $(whoami)@$(hostname)"
echo "📁 PRACTICE DIR: /usr"
echo "⚠️ TRAPS: T19-A T19-B T41 T44"
ls -ld /usr
```

---

## Objective

Take the auditor seat for the concatenation trilogy:

1. Prove assembled output exists and line counts match source inputs.
2. Run a destroy-restore drill to validate recovery habits.

---

## Lab-Wide Setup — Tier B Sandbox

```bash
sudo -i

export SANDBOX=/tmp/lab19c
export GROUP=labgrp_19_catjoin
export USER=labuser_19_catjoin
export USER_HOME=${SANDBOX}/home_${USER}

mkdir -p "${SANDBOX}" "${USER_HOME}" /root/rhcsa_journal/lab-19c/task1 /root/rhcsa_journal/lab-19c/task2
getent group "${GROUP}" >/dev/null || groupadd "${GROUP}"
getent passwd "${USER}" >/dev/null || useradd -d "${USER_HOME}" -M -s /bin/bash -g "${GROUP}" "${USER}"
chown -R "${USER}:${GROUP}" "${SANDBOX}"
```

---

## Task 1 — Audit assembled output and line-count integrity

### Purpose

Validate that a merged output exists and its line count equals the sum of inputs.

### Main command block

```bash
TASKLOG=/tmp/lab19c/task1.txt
mkdir -p /tmp/lab19c/in

cat /etc/redhat-release > /tmp/lab19c/in/f1.txt
cat /etc/hostname > /tmp/lab19c/in/f2.txt
cat /etc/hosts > /tmp/lab19c/in/f3.txt

cat /tmp/lab19c/in/f1.txt /tmp/lab19c/in/f2.txt /tmp/lab19c/in/f3.txt > /tmp/lab19c/assembled.txt

test -f /tmp/lab19c/assembled.txt && echo "✅ assembled exists" | tee "$TASKLOG"

L1=$(wc -l < /tmp/lab19c/in/f1.txt)
L2=$(wc -l < /tmp/lab19c/in/f2.txt)
L3=$(wc -l < /tmp/lab19c/in/f3.txt)
LT=$((L1 + L2 + L3))
LA=$(wc -l < /tmp/lab19c/assembled.txt)

echo "source_total=${LT} assembled=${LA}" | tee -a "$TASKLOG"
test "${LT}" -eq "${LA}" && echo "✅ line count match" | tee -a "$TASKLOG" || echo "❌ line count mismatch" | tee -a "$TASKLOG"

cat -n /tmp/lab19c/assembled.txt | head -n 20 | tee -a "$TASKLOG"
cat -A /tmp/lab19c/assembled.txt | head -n 10 | tee -a "$TASKLOG"
echo "exit was: $?"
```

### Audit notes

- `wc -l < file` form is required for clean numeric arithmetic.
- `cat -A` catches hidden character surprises (T19-B).

### Journal write

```bash
JDIR=/root/rhcsa_journal/lab-19c/task1
cp /tmp/lab19c/task1.txt "$JDIR/evidence.txt"
cp /tmp/lab19c/assembled.txt "$JDIR/assembled.txt"
```

---

## Task 2 — Destroy-restore drill (T41)

### Purpose

Prove you can recover concatenation artifacts after intentional destruction.

### Main command block

```bash
TASKLOG=/tmp/lab19c/task2.txt
BACKUP=/root/rhcsa_journal/lab-19c/task2
mkdir -p "$BACKUP"

# Build baseline
cat /tmp/lab19c/in/f1.txt /tmp/lab19c/in/f2.txt /tmp/lab19c/in/f3.txt > /tmp/lab19c/assembled.txt
cp /tmp/lab19c/assembled.txt "$BACKUP/assembled.before-destroy.txt"

# Destroy
rm -f /tmp/lab19c/assembled.txt
test ! -f /tmp/lab19c/assembled.txt && echo "✅ destroyed target" | tee "$TASKLOG"

# Restore from source recomposition
cat /tmp/lab19c/in/f1.txt /tmp/lab19c/in/f2.txt /tmp/lab19c/in/f3.txt > /tmp/lab19c/assembled.txt
cp /tmp/lab19c/assembled.txt "$BACKUP/assembled.after-restore.txt"

diff -u "$BACKUP/assembled.before-destroy.txt" "$BACKUP/assembled.after-restore.txt" | tee -a "$TASKLOG"
echo "restore-status=$?" | tee -a "$TASKLOG"

wc -l /tmp/lab19c/assembled.txt | tee -a "$TASKLOG"
echo "exit was: $?"
```

### Expected outcome

- Destroy step proves target is absent.
- Restore step rebuilds exact output from source files.
- `diff -u` shows no differences.

### Journal write

```bash
cp /tmp/lab19c/task2.txt /root/rhcsa_journal/lab-19c/task2/evidence.txt
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

echo "── Lab 19c cleanup audit ──"
getent passwd "${USER}" >/dev/null && echo "❌ user remains" || echo "✅ user gone"
getent group "${GROUP}" >/dev/null && echo "❌ group remains" || echo "✅ group gone"
test -d "${SANDBOX}" && echo "❌ sandbox remains" || echo "✅ sandbox gone"
test -d "${USER_HOME}" && echo "❌ home remains" || echo "✅ home gone"

set -e
```

---

## Lab 19c Checklist

- [ ] Task 1 completed (assembled output exists + line count equals sum of inputs)
- [ ] Task 2 completed (destroy-restore drill and `diff -u` validation)
- [ ] Section 6 closeout audit shows four `✅` lines

---

## Author

**Kelvin R. Tobias**
[kelvinintech.com](https://kelvinintech.com) · [GitHub](https://github.com/kelvintechnical) · [LinkedIn](https://www.linkedin.com/in/kelvin-r-tobias-211949219)
