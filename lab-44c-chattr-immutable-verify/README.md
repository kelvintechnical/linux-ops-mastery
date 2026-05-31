# Lab 44c: Verifying Immutable Attribute — audit + destroy/restore

- **Series:** linux-ops-mastery — Filesystem Attributes and Protection
- **Trilogy:** `44a` (RHCSA) -> `44b` (Ansible boundary) -> `44c` (Verify — you are here)
- **Time Estimate:** 25-35 minutes
- **Tasks:** 2 (Task 1 = audit, Task 2 = destroy-restore drill)
- **Practice Directory (rotation slot 44):** `/root`
- **Sandbox (Tier B):** `/tmp/lab44c` with `USER=labuser_44_immutable`, `GROUP=labgrp_44_immutable`
- **Traps rehearsed this lab:** **T44-A** · **T44-B** · **T41** · **T44**

> **Verifier posture:** prove immutable state from `lsattr` evidence, then prove recovery sequence works only when `chattr -i` occurs before delete.

---

## LAB HEADER BLOCK

```bash
echo "🖥️  ENV:   ${ENV:-DECLARE_ME}"
echo "📦  OS:    $(cat /etc/redhat-release 2>/dev/null || grep PRETTY_NAME /etc/os-release)"
echo "🕒  TIME:  $(date -Is)"
echo "👤  USER:  $(whoami)@$(hostname)"
echo "📁  PRACTICE DIR: /root"
echo "⚠️  TRAP REMINDERS THIS LAB: T44-A T44-B T41 T44"
command -v chattr
command -v lsattr
```

> **STOP — paste header output before setup.**

---

## Objective

1. Audit immutable file state and archive `lsattr` output into journal evidence.
2. Run destroy-restore drill: unlock, remove, recreate, re-lock, and re-verify.

---

## Lab-Wide Setup — Tier B Sandbox

```bash
sudo -i

export SANDBOX=/tmp/lab44c
export GROUP=labgrp_44_immutable
export USER=labuser_44_immutable
export USER_HOME=${SANDBOX}/home_${USER}

mkdir -p "${SANDBOX}" "${USER_HOME}" /root/rhcsa_journal/lab-44c/task1 /root/rhcsa_journal/lab-44c/task2
getent group "${GROUP}" >/dev/null || groupadd "${GROUP}"
getent passwd "${USER}" >/dev/null || useradd -d "${USER_HOME}" -M -s /bin/bash -g "${GROUP}" "${USER}"
chown -R "${USER}:${GROUP}" "${SANDBOX}"
```

---

## Task 1 — Audit immutable state with `lsattr` journal proof

### Purpose

Capture auditor-grade immutable evidence before any mutation.

### Main command block

```bash
TASKLOG=/tmp/lab44c/task1.txt
cd /tmp/lab44c

touch protected.txt
sudo chattr +i protected.txt                                      2>&1 | tee "${TASKLOG}"
sudo lsattr protected.txt                                         2>&1 | tee -a "${TASKLOG}"
stat -c '%U:%G %a %n' protected.txt                               2>&1 | tee -a "${TASKLOG}"

echo "exit was: $?"                                               | tee -a "${TASKLOG}"
```

### Journal write

```bash
cp /tmp/lab44c/task1.txt /root/rhcsa_journal/lab-44c/task1/audit.txt
sudo lsattr /tmp/lab44c/protected.txt > /root/rhcsa_journal/lab-44c/task1/lsattr-audit.txt
```

---

## Task 2 — Destroy-restore drill (`-i` first, then remove, then restore `+i`)

### Purpose

Rehearse failure recovery sequence without breaking teardown.

### Main command block

```bash
TASKLOG=/tmp/lab44c/task2.txt
cd /tmp/lab44c

echo "phase A: destroy (unlock -> remove)"
sudo chattr -i protected.txt                                      2>&1 | tee "${TASKLOG}"
rm -f protected.txt                                               2>&1 | tee -a "${TASKLOG}"
test -e protected.txt && echo "❌ still present" || echo "✅ destroyed" | tee -a "${TASKLOG}"

echo "phase B: restore (recreate -> lock -> verify)"
touch protected.txt
echo "restored-content" > protected.txt
sudo chattr +i protected.txt                                      2>&1 | tee -a "${TASKLOG}"
sudo lsattr protected.txt                                         2>&1 | tee -a "${TASKLOG}"

echo "phase C: immutable check after restore"
mv protected.txt protected-renamed.txt                            2>&1 | tee -a "${TASKLOG}" || true
echo "mutate-again" >> protected.txt                              2>&1 | tee -a "${TASKLOG}" || true

echo "exit was: $?"                                               | tee -a "${TASKLOG}"
```

### Trap callout

- **T44-A:** every destroy/cleanup sequence starts with `sudo chattr -i` first.
- **T41:** destroy-restore is intentional resilience drill, not accidental damage.

### Journal write

```bash
cp /tmp/lab44c/task2.txt /root/rhcsa_journal/lab-44c/task2/destroy-restore.txt
```

---

## Lab Closeout — Bulletproof Teardown (Section 6)

```bash
set +e

# Immutable safety sweep before any remove.
if test -e /tmp/lab44c/protected.txt; then
  sudo chattr -i /tmp/lab44c/protected.txt 2>/dev/null
fi
if test -e /tmp/lab44c/protected-renamed.txt; then
  sudo chattr -i /tmp/lab44c/protected-renamed.txt 2>/dev/null
fi

if getent passwd "${USER}" >/dev/null 2>&1; then
  userdel -r "${USER}" 2>/dev/null
fi
if getent group "${GROUP}" >/dev/null 2>&1; then
  groupdel "${GROUP}" 2>/dev/null
fi

rm -rf "${SANDBOX}"

echo "── Lab 44c cleanup audit ──"
getent passwd "${USER}" >/dev/null && echo "❌ user remains" || echo "✅ user gone"
getent group "${GROUP}" >/dev/null && echo "❌ group remains" || echo "✅ group gone"
test -d "${SANDBOX}" && echo "❌ sandbox remains" || echo "✅ sandbox gone"
test -d "${USER_HOME}" && echo "❌ home remains" || echo "✅ home gone"

set -e
```

---

## Lab 44c Checklist

- [ ] Task 1 completed (`lsattr` immutable evidence captured in journal)
- [ ] Task 2 completed (destroy-restore sequence proved: `-i` -> `rm` -> recreate -> `+i`)
- [ ] T44-A, T44-B, T41, and T44 risks noted in evidence
- [ ] Section 6 closeout audit shows four `✅` lines

---

## Author

**Kelvin R. Tobias**
[kelvinintech.com](https://kelvinintech.com) · [GitHub](https://github.com/kelvintechnical) · [LinkedIn](https://www.linkedin.com/in/kelvin-r-tobias-211949219)
