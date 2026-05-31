# Lab 44a: Immutable File Attribute with `chattr` (RHCSA) — `+i`, `-i`, `lsattr`

- **Series:** linux-ops-mastery — Filesystem Attributes and Protection
- **Trilogy:** `44a` (RHCSA hand-typed) -> `44b` (Ansible boundary) -> `44c` (Verify capstone)
- **Time Estimate:** 25-35 minutes
- **Tasks:** 2
- **Practice Directory (rotation slot 44):** `/root`
- **Sandbox (Tier B):** `/tmp/lab44a` with `USER=labuser_44_immutable`, `GROUP=labgrp_44_immutable`
- **Traps rehearsed this lab:** **T44-A** (forgetting `chattr -i` before cleanup) · **T44-B** (`chattr +i` requires elevated privilege / CAP_LINUX_IMMUTABLE path) · **T41** · **T44**

> **Immutable rule:** a file with `i` attribute cannot be removed, renamed, or edited, even by root, until `chattr -i` is applied first.

---

## LAB HEADER BLOCK

```bash
echo "🖥️  ENV:   ${ENV:-DECLARE_ME}"
echo "📦  OS:    $(cat /etc/redhat-release 2>/dev/null || grep PRETTY_NAME /etc/os-release)"
echo "🕒  TIME:  $(date -Is)"
echo "👤  USER:  $(whoami)@$(hostname)"
echo "📁  PRACTICE DIR: /root"
echo "⚠️  TRAP REMINDERS THIS LAB: T44-A T44-B T41 T44"
ls -ld /root
command -v chattr
command -v lsattr
```

> **STOP — paste header output before setup.**

---

## Objective

1. Apply immutable protection with `sudo chattr +i` and verify with `lsattr`.
2. Prove immutable behavior blocks delete and edit operations.
3. Remove immutable safely with `sudo chattr -i` before cleanup.

---

## Lab-Wide Setup — Tier B Sandbox

```bash
sudo -i

export SANDBOX=/tmp/lab44a
export GROUP=labgrp_44_immutable
export USER=labuser_44_immutable
export USER_HOME=${SANDBOX}/home_${USER}

mkdir -p "${SANDBOX}" "${USER_HOME}" /root/rhcsa_journal/lab-44a/task1 /root/rhcsa_journal/lab-44a/task2
getent group "${GROUP}" >/dev/null || groupadd "${GROUP}"
getent passwd "${USER}" >/dev/null || useradd -d "${USER_HOME}" -M -s /bin/bash -g "${GROUP}" "${USER}"
chown -R "${USER}:${GROUP}" "${SANDBOX}"

id "${USER}"
ls -ld "${SANDBOX}" "${USER_HOME}"
```

---

## Task 1 — Protect file with `+i` and prove deny behavior

### Purpose

Create immutable protection and observe expected `Operation not permitted` failures.

### Main command block

```bash
TASKLOG=/tmp/lab44a/task1.txt
cd /tmp/lab44a

touch protected.txt
sudo chattr +i protected.txt                                      2>&1 | tee "${TASKLOG}"
sudo lsattr protected.txt                                         2>&1 | tee -a "${TASKLOG}"

echo "try remove (expect EPERM)"
rm -f protected.txt                                               2>&1 | tee -a "${TASKLOG}" || true

echo "try edit (expect EPERM)"
echo "mutate" >> protected.txt                                    2>&1 | tee -a "${TASKLOG}" || true

ls -l protected.txt                                               2>&1 | tee -a "${TASKLOG}"
echo "exit was: $?"                                               | tee -a "${TASKLOG}"
```

### Trap callout

- **T44-B:** run `chattr +i` with `sudo`; ownership alone is not enough in this workflow.
- **Immutable behavior:** delete/rename/edit fails until `-i` is applied.

### Journal write

```bash
cp /tmp/lab44a/task1.txt /root/rhcsa_journal/lab-44a/task1/evidence.txt
sudo lsattr /tmp/lab44a/protected.txt > /root/rhcsa_journal/lab-44a/task1/lsattr.txt
```

---

## Task 2 — Remove immutable, cleanup, and trap rehearsal

### Purpose

Build teardown reflex: always `chattr -i` before any remove.

### Main command block

```bash
TASKLOG=/tmp/lab44a/task2.txt
cd /tmp/lab44a

echo "phase A: unlock then remove"
sudo chattr -i protected.txt                                      2>&1 | tee "${TASKLOG}"
sudo lsattr protected.txt                                         2>&1 | tee -a "${TASKLOG}"
rm -f protected.txt                                               2>&1 | tee -a "${TASKLOG}"
test -e protected.txt && echo "❌ still present" || echo "✅ removed" | tee -a "${TASKLOG}"

echo "phase B: rebuild and rehearse trap T44-A"
touch protected.txt
sudo chattr +i protected.txt                                      2>&1 | tee -a "${TASKLOG}"
rm -f protected.txt                                               2>&1 | tee -a "${TASKLOG}" || true
sudo chattr -i protected.txt                                      2>&1 | tee -a "${TASKLOG}"
rm -f protected.txt                                               2>&1 | tee -a "${TASKLOG}"
test -e protected.txt && echo "❌ rehearsal failed" || echo "✅ rehearsal complete" | tee -a "${TASKLOG}"

echo "exit was: $?"                                               | tee -a "${TASKLOG}"
```

### Trap callout

- **T44-A (critical):** never run cleanup `rm` on immutable files without `sudo chattr -i` first.

### Journal write

```bash
cp /tmp/lab44a/task2.txt /root/rhcsa_journal/lab-44a/task2/evidence.txt
```

---

## Lab Closeout — Bulletproof Teardown (Section 6)

```bash
set +e

# Immutable safety sweep: unlock before any delete attempt.
if test -e /tmp/lab44a/protected.txt; then
  sudo chattr -i /tmp/lab44a/protected.txt 2>/dev/null
fi

if getent passwd "${USER}" >/dev/null 2>&1; then
  userdel -r "${USER}" 2>/dev/null
fi
if getent group "${GROUP}" >/dev/null 2>&1; then
  groupdel "${GROUP}" 2>/dev/null
fi

rm -rf "${SANDBOX}"

echo "── Lab 44a cleanup audit ──"
getent passwd "${USER}" >/dev/null && echo "❌ user remains" || echo "✅ user gone"
getent group "${GROUP}" >/dev/null && echo "❌ group remains" || echo "✅ group gone"
test -d "${SANDBOX}" && echo "❌ sandbox remains" || echo "✅ sandbox gone"
test -d "${USER_HOME}" && echo "❌ home remains" || echo "✅ home gone"

set -e
```

---

## Lab 44a Checklist

- [ ] Task 1 completed (`touch` + `sudo chattr +i` + `sudo lsattr`; delete/edit attempts denied)
- [ ] Task 2 completed (`sudo chattr -i` then remove; trap rehearsal proved failure-before-unlock)
- [ ] T44-A and T44-B documented in evidence
- [ ] Section 6 closeout audit shows four `✅` lines

---

## Author

**Kelvin R. Tobias**
[kelvinintech.com](https://kelvinintech.com) · [GitHub](https://github.com/kelvintechnical) · [LinkedIn](https://www.linkedin.com/in/kelvin-r-tobias-211949219)
