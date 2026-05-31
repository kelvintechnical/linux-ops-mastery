# Lab 46c: Identifying File Attributes (Verify) — Audit + Destroy/Restore

- **Series:** linux-ops-mastery — Attribute Verification and Recovery
- **Trilogy:** [`46a`](../lab-46a-lsattr-extended-attrs-rhcsa/) (RHCSA) → [`46b`](../lab-46b-lsattr-extended-attrs-ansible/) (Ansible) → **`46c`** (Verify)
- **Tasks:** 2 (Task 1 = audit prior `lsattr` evidence in journal; Task 2 = destroy `/tmp` artifacts, restore from journal, and re-verify)
- **Practice Directory:** `/tmp`
- **Sandbox (Tier B):** `/tmp/lab46c`, `USER=labuser_46_lsattr`, `GROUP=labgrp_46_lsattr`
- **Traps rehearsed:** `T46-A` · `T46-B` · `T41` · `T44`

> **This verify lab proves evidence quality, not just command recall.**

---

## LAB HEADER BLOCK

```bash
echo "🖥️  ENV:   ${ENV:-DECLARE_ME}"
echo "💿  DISK:  $(lsblk 2>/dev/null | awk '$NF=="disk"{print "/dev/"$1}' | paste -sd, -)"
echo "🌐  NIC:   $(ip -o addr show 2>/dev/null | awk '$2!="lo"{print $2}' | sort -u | paste -sd, -)"
echo "🔐  SE:    $(getenforce 2>/dev/null || echo n/a)"
echo "📦  OS:    $(cat /etc/redhat-release 2>/dev/null || grep PRETTY_NAME /etc/os-release)"
echo "🕒  TIME:  $(date -Is)"
echo "👤  USER:  $(whoami)@$(hostname)"
echo "⚠️  TRAP REMINDERS THIS LAB: T46-A T46-B T41 T44"
echo "📁  PRACTICE DIR: /tmp"
```

---

## Lab-Wide Setup — Tier B Sandbox Stack

```bash
sudo -i

export LAB_NUM=46
export LAB_SLUG=lsattr
export SANDBOX=/tmp/lab46c
export GROUP=labgrp_46_lsattr
export USER=labuser_46_lsattr
export USER_HOME=${SANDBOX}/home_${USER}

mkdir -p "${SANDBOX}" "${USER_HOME}"
mkdir -p /root/rhcsa_journal/lab-46c/task1
mkdir -p /root/rhcsa_journal/lab-46c/task2

getent group  "${GROUP}" >/dev/null || groupadd "${GROUP}"
getent passwd "${USER}"  >/dev/null || useradd -d "${USER_HOME}" -M -s /bin/bash -g "${GROUP}" "${USER}"
chown -R "${USER}:${GROUP}" "${SANDBOX}"

id "${USER}"
ls -ld /tmp "${SANDBOX}" "${USER_HOME}"
echo "Setup complete at $(date -Is)"
echo "exit was: $?"
```

---

## Task 1 — Audit `lsattr` captures from journal

**Practice directory this task:** `/tmp`

### Purpose

Validate that lab 46a/46b stored usable evidence and that attribute lines can still be interpreted.

### Main Command Block

```bash
TASKLOG=/tmp/lab46c/task1.txt
E46A1=/root/rhcsa_journal/lab-46a/task1/evidence.txt
E46A2=/root/rhcsa_journal/lab-46a/task2/evidence.txt
E46B1=/root/rhcsa_journal/lab-46b/task1/lsattr-r.txt

test -s "${E46A1}" || { echo "missing ${E46A1}" | tee "${TASKLOG}"; false; }
test -s "${E46A2}" || { echo "missing ${E46A2}" | tee -a "${TASKLOG}"; false; }

ls -l "${E46A1}" "${E46A2}" "${E46B1}"                    2>&1 | tee "${TASKLOG}" || true
grep -E "lsattr /etc/passwd|lsattr -d /tmp|lsattr -R" "${E46A1}" 2>&1 | tee -a "${TASKLOG}" || true
grep -E "noatime.txt|sync.txt|A|S" "${E46A2}"             2>&1 | tee -a "${TASKLOG}" || true
head -20 "${E46B1}"                                        2>&1 | tee -a "${TASKLOG}" || true

# Tier B verify write
sudo -u "${USER}" bash -c 'echo "verify-audit-line $(date -Is)" > '"${USER_HOME}"'/verify-audit.txt'
stat -c '%U:%G %a %n' "${USER_HOME}/verify-audit.txt"      2>&1 | tee -a "${TASKLOG}"

echo "exit was: $?"
```

### Journal Write

```bash
LAB=lab-46c
TASK=task1
JDIR="/root/rhcsa_journal/${LAB}/${TASK}"
mkdir -p "$JDIR"
cp /tmp/lab46c/task1.txt "$JDIR/evidence.txt"
```

> **STOP — paste journal audit evidence before Task 2.**

---

## Task 2 — Destroy/Restore drill (`T41`) and re-verify

**Practice directory this task:** `/tmp`

### Purpose

Simulate `/tmp` loss, restore from persistent journal, and prove attributes can be inspected again after recovery.

### Main Command Block

```bash
TASKLOG=/tmp/lab46c/task2.txt
RESTORE=/tmp/lab46c/restore
SRC=/root/rhcsa_journal/lab-46a/task2/evidence.txt

test -s "${SRC}" || { echo "missing ${SRC}" | tee "${TASKLOG}"; false; }

# Destroy phase
rm -rf /tmp/lab46c/restore /tmp/lab46c/rebuilt.txt /tmp/lab46c/rebuilt-sync.txt
mkdir -p "${RESTORE}"

# Restore phase
cp "${SRC}" "${RESTORE}/lab46a-task2-evidence.txt"
touch /tmp/lab46c/rebuilt.txt /tmp/lab46c/rebuilt-sync.txt
chattr +A /tmp/lab46c/rebuilt.txt        2>&1 | tee "${TASKLOG}" || true
chattr +S /tmp/lab46c/rebuilt-sync.txt   2>&1 | tee -a "${TASKLOG}" || true

lsattr /tmp/lab46c/rebuilt.txt           2>&1 | tee -a "${TASKLOG}"
lsattr /tmp/lab46c/rebuilt-sync.txt      2>&1 | tee -a "${TASKLOG}"
ls -l "${RESTORE}/lab46a-task2-evidence.txt" 2>&1 | tee -a "${TASKLOG}"

# Non-root replay check
sudo -u "${USER}" bash -c 'lsattr /tmp/lab46c/rebuilt.txt' 2>&1 | tee -a "${TASKLOG}" || true

echo "exit was: $?"
```

### PERSISTENCE CHECK

| What was configured | Verification command | Why it matters |
|---|---|---|
| Journal artifact restored | `test -s /tmp/lab46c/restore/lab46a-task2-evidence.txt` | Proves recovery path works |
| Rebuilt files inspected | `lsattr /tmp/lab46c/rebuilt.txt /tmp/lab46c/rebuilt-sync.txt` | Confirms post-restore attr workflow |
| Tier B replay done | `stat -c '%U:%G' "${USER_HOME}/verify-audit.txt"` | Keeps user/group reflex active |

### Journal Write

```bash
LAB=lab-46c
TASK=task2
JDIR="/root/rhcsa_journal/${LAB}/${TASK}"
mkdir -p "$JDIR"
cp /tmp/lab46c/task2.txt "$JDIR/evidence.txt"
cp /tmp/lab46c/restore/lab46a-task2-evidence.txt "$JDIR/restored-evidence.txt"
```

---

## Lab Closeout — Section 6 Teardown

```bash
set +e

if getent passwd "${USER}" >/dev/null 2>&1; then
    userdel -r "${USER}" 2>/dev/null
fi
if getent group "${GROUP}" >/dev/null 2>&1; then
    groupdel "${GROUP}" 2>/dev/null
fi

rm -rf "${SANDBOX}"

echo "── Lab 46c cleanup audit ──"
getent passwd "${USER}" >/dev/null && echo "❌ user remains" || echo "✅ user gone"
getent group  "${GROUP}" >/dev/null && echo "❌ group remains" || echo "✅ group gone"
test -d "${SANDBOX}" && echo "❌ sandbox remains" || echo "✅ sandbox gone"
test -d "${USER_HOME}" && echo "❌ home remains" || echo "✅ home gone"

set -e
echo "Cleanup complete at $(date -Is)"
echo "exit was: $?"
```

---

## Author

**Kelvin R. Tobias**
