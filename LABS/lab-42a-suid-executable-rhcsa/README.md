# Lab 42a: SUID Executables (RHCSA) — `chmod u+s`, `chmod 4755`, `ls -l`

- **Series:** linux-ops-mastery — Privilege, Permissions, and Security Posture
- **Trilogy:** `42a` (RHCSA hand-typed) -> `42b` (Ansible mirror) -> `42c` (Verify capstone)
- **Time Estimate:** 25-35 minutes
- **Tasks:** 2
- **Practice Directory (rotation slot 42):** `/boot`
- **Sandbox (Tier B):** `/tmp/lab42a` with `USER=labuser_42_suid`, `GROUP=labgrp_42_suid`
- **Traps rehearsed this lab:** **T42-A** (lowercase `s` vs uppercase `S`) · **T42-B** (SUID on shell scripts ignored by Linux kernel) · **T41** · **T44**

> **This lab's topic:** set, inspect, and reason about SUID executables safely; prove why stale SUID copies must be removed immediately.

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
id
```

> **STOP — paste header output before setup.**

---

## Objective

1. Build a local SUID test binary from `/usr/bin/cat` and verify effective privilege behavior.
2. Contrast `chmod u+s` vs `chmod u+S` using `ls -l` (`s` means executable+SUID, `S` means missing execute bit).
3. Prove trap T42-B: SUID on shell scripts does not grant elevation on Linux.

---

## Core Reference

| Command | Meaning |
|---|---|
| `chmod u+s FILE` | Set SUID bit symbolically |
| `chmod 4755 FILE` | Set mode with SUID + rwx/rx/rx |
| `ls -l FILE` | View mode string (`rws` vs `rwS`) |
| `find / -perm -4000 -type f` | Discover SUID binaries |
| `stat -c '%A %a %U:%G %n' FILE` | Machine-friendly permission/owner audit |

---

## Lab-Wide Setup — Tier B Sandbox

```bash
sudo -i

export SANDBOX=/tmp/lab42a
export GROUP=labgrp_42_suid
export USER=labuser_42_suid
export USER_HOME=${SANDBOX}/home_${USER}

mkdir -p "${SANDBOX}" "${USER_HOME}" /root/rhcsa_journal/lab-42a/task1 /root/rhcsa_journal/lab-42a/task2
getent group "${GROUP}" >/dev/null || groupadd "${GROUP}"
getent passwd "${USER}" >/dev/null || useradd -d "${USER_HOME}" -M -s /bin/bash -g "${GROUP}" "${USER}"
chown -R "${USER}:${GROUP}" "${SANDBOX}"

id "${USER}"
ls -ld "${SANDBOX}" "${USER_HOME}"
```

---

## Task 1 — Build a SUID copy of `cat` and prove behavior

### Purpose

Create an intentionally risky SUID binary in the lab sandbox, verify behavior as non-root, then clean it immediately.

### Main command block

```bash
TASKLOG=/tmp/lab42a/task1.txt

mkdir -p /tmp/lab42a
cp /usr/bin/cat /tmp/lab42a/labcat
chown root:root /tmp/lab42a/labcat
chmod 4755 /tmp/lab42a/labcat

echo "═══ SUID mode proof ═══" | tee "${TASKLOG}"
ls -l /tmp/lab42a/labcat     | tee -a "${TASKLOG}"
stat -c '%A %a %U:%G %n' /tmp/lab42a/labcat | tee -a "${TASKLOG}"

echo "═══ non-root read of /etc/shadow via SUID labcat ═══" | tee -a "${TASKLOG}"
sudo -u "${USER}" /tmp/lab42a/labcat /etc/shadow | head -n 3 | tee -a "${TASKLOG}"

echo "exit was: $?" | tee -a "${TASKLOG}"
```

### Security note

- This proves why SUID binaries are dangerous if left behind.
- **Always remove `/tmp/lab42a/labcat` after evidence capture.**

### Journal write

```bash
JDIR=/root/rhcsa_journal/lab-42a/task1
cp /tmp/lab42a/task1.txt "${JDIR}/evidence.txt"
```

---

## Task 2 — `u+s` vs `u+S`, and shell-script SUID trap (T42-B)

### Purpose

Demonstrate both failure modes:

- **T42-A:** `S` means SUID set but execute bit absent (non-functional execution path).
- **T42-B:** kernel ignores SUID bit on interpreted scripts.

### Main command block

```bash
TASKLOG=/tmp/lab42a/task2.txt

# A) symbolic vs uppercase-S contrast
cp /usr/bin/cat /tmp/lab42a/labcat-symbolic
chown root:root /tmp/lab42a/labcat-symbolic
chmod u+s /tmp/lab42a/labcat-symbolic
ls -l /tmp/lab42a/labcat-symbolic | tee "${TASKLOG}"

chmod u-x /tmp/lab42a/labcat-symbolic
ls -l /tmp/lab42a/labcat-symbolic | tee -a "${TASKLOG}"   # expect rwSr-xr-x

# B) T42-B: SUID on shell script ignored
cat > /tmp/lab42a/suid-script.sh <<'EOF'
#!/bin/bash
id
cat /etc/shadow | head -n 1
EOF
chmod 755 /tmp/lab42a/suid-script.sh
chown root:root /tmp/lab42a/suid-script.sh
chmod u+s /tmp/lab42a/suid-script.sh

ls -l /tmp/lab42a/suid-script.sh        | tee -a "${TASKLOG}"
sudo -u "${USER}" /tmp/lab42a/suid-script.sh 2>&1 | tee -a "${TASKLOG}" || true

echo "exit was: $?" | tee -a "${TASKLOG}"
```

### Expected interpretation

- Script run still shows `uid=<lab user>` behavior, not privileged root effect.
- If `/etc/shadow` read fails in script context, that is expected and proves T42-B.

### Journal write

```bash
JDIR=/root/rhcsa_journal/lab-42a/task2
cp /tmp/lab42a/task2.txt "${JDIR}/evidence.txt"
```

---

## Lab Closeout — Bulletproof Teardown (Section 6)

```bash
set +e

# Mandatory SUID cleanup first (security)
rm -f /tmp/lab42a/labcat /tmp/lab42a/labcat-symbolic /tmp/lab42a/suid-script.sh

if getent passwd "${USER}" >/dev/null 2>&1; then
  userdel -r "${USER}" 2>/dev/null
fi
if getent group "${GROUP}" >/dev/null 2>&1; then
  groupdel "${GROUP}" 2>/dev/null
fi

rm -rf "${SANDBOX}"

echo "── Lab 42a cleanup audit ──"
getent passwd "${USER}" >/dev/null && echo "❌ user remains" || echo "✅ user gone"
getent group "${GROUP}" >/dev/null && echo "❌ group remains" || echo "✅ group gone"
test -d "${SANDBOX}" && echo "❌ sandbox remains" || echo "✅ sandbox gone"
test -e /tmp/lab42a/labcat && echo "❌ suid labcat remains" || echo "✅ suid labcat gone"

set -e
```

---

## Lab 42a Checklist

- [ ] Task 1 completed (`labcat` created with mode `4755`, non-root `/etc/shadow` read demonstrated)
- [ ] Task 2 completed (`s` vs `S` contrast captured; shell-script SUID trap demonstrated)
- [ ] All SUID test artifacts removed from `/tmp/lab42a`
- [ ] Section 6 closeout audit ended with `✅` lines

---

## Author

**Kelvin R. Tobias**
[kelvinintech.com](https://kelvinintech.com) · [GitHub](https://github.com/kelvintechnical) · [LinkedIn](https://www.linkedin.com/in/kelvin-r-tobias-211949219)
