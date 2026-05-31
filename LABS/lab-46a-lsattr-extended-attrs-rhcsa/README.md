# Lab 46a: Identifying File Attributes (RHCSA) — `lsattr`, `lsattr -d`, `lsattr -R`, `chattr +A`, `chattr +S`

- **Series:** linux-ops-mastery — Permissions, Attributes, and Audit Reflex
- **Trilogy:** **`46a`** (RHCSA hand-typed) → [`46b`](../lab-46b-lsattr-extended-attrs-ansible/) (Ansible boundary) → [`46c`](../lab-46c-lsattr-extended-attrs-verify/) (Verify and restore)
- **Tasks:** 2 (Task 1 = identify attributes with `lsattr`, `-d`, and `-R`; Task 2 = apply `+A`, contrast with `+S`, and verify)
- **Practice Directory:** `/tmp`
- **Sandbox (Tier B):** `/tmp/lab46a`, `USER=labuser_46_lsattr`, `GROUP=labgrp_46_lsattr`
- **Traps rehearsed this lab:** `T46-A` (XFS shows fewer attrs than ext4) · `T46-B` (special/sparse paths can error in `lsattr`) · `T41` · `T44`

> **This lab's practice directory is: `/tmp`** — fast scratch space for attribute inspection drills.

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

> **STOP — paste header output before setup.**

---

## Lab-Wide Setup — Tier B Sandbox Stack

```bash
sudo -i

export LAB_NUM=46
export LAB_SLUG=lsattr
export SANDBOX=/tmp/lab46a
export GROUP=labgrp_46_lsattr
export USER=labuser_46_lsattr
export USER_HOME=${SANDBOX}/home_${USER}

mkdir -p "${SANDBOX}" "${USER_HOME}"
mkdir -p /root/rhcsa_journal/lab-46a/task1
mkdir -p /root/rhcsa_journal/lab-46a/task2

getent group  "${GROUP}" >/dev/null || groupadd "${GROUP}"
getent passwd "${USER}"  >/dev/null || useradd -d "${USER_HOME}" -M -s /bin/bash -g "${GROUP}" "${USER}"
chown -R "${USER}:${GROUP}" "${SANDBOX}"

id "${USER}"
ls -ld /tmp "${SANDBOX}" "${USER_HOME}"
echo "Setup complete at $(date -Is)"
echo "exit was: $?"
```

> **STOP — paste setup proof before Task 1.**

---

## Task 1 — Identify attributes with `lsattr`, `lsattr -d`, and `lsattr -R`

**Practice directory this task:** `/tmp`

### Warm-Up

```bash
ls -ld /tmp
mount | grep -E ' /tmp | on / '
touch /tmp/lab46a/warmup.txt
ls -l /tmp/lab46a/warmup.txt
echo "Warm-up done by $(whoami) at $(date -Is)"
echo "exit was: $?"
```

### Purpose

Build reflexes for reading file and directory attribute bits quickly, including recursive scans and the `-d` directory-self view.

### Main Command Block

```bash
TASKLOG=/tmp/lab46a/task1.txt

lsattr /etc/passwd                                        2>&1 | tee "${TASKLOG}"
lsattr -d /tmp                                            2>&1 | tee -a "${TASKLOG}"
mkdir -p /tmp/lab46a/tree/{a,b}
touch /tmp/lab46a/tree/a/file1 /tmp/lab46a/tree/b/file2
lsattr -R /tmp/lab46a                                     2>&1 | tee -a "${TASKLOG}"

# Tier B weave: user-owned file for ownership + attr visibility
sudo -u "${USER}" bash -c 'touch '"${USER_HOME}"'/user-owned.txt'
lsattr "${USER_HOME}/user-owned.txt"                      2>&1 | tee -a "${TASKLOG}"
stat -c '%U:%G %a %n' "${USER_HOME}/user-owned.txt"      2>&1 | tee -a "${TASKLOG}"

echo "exit was: $?"
```

### Attribute letters to recognize

| Letter | Meaning (short) | Exam relevance |
|---|---|---|
| `a` | Append-only | Logs that should not be truncated |
| `i` | Immutable | File cannot be changed/deleted |
| `A` | No atime updates | Reduce metadata writes on reads |
| `S` | Synchronous updates | Data+metadata sync aggressively |
| `c` | Compressed | Filesystem-dependent, often absent |
| `e` | Extents format | Common on ext4 |
| `d` | No dump utility | Backup/maintenance behavior |

### Concept Card

| ✅ | Concept | What it does |
|---|---|---|
| ✅ | `lsattr FILE` | Prints attribute flags for that file |
| ✅ | `lsattr -d DIR` | Shows the directory object's flags, not its contents |
| ✅ | `lsattr -R PATH` | Recursively prints attrs for tree |
| 🪤 `T46-A` | XFS may show only a subset vs ext4 | Do not expect every ext4 letter on XFS |
| 🪤 `T46-B` | Some sparse/special files can throw errors | Capture stderr and continue with evidence |

### Journal Write

```bash
LAB=lab-46a
TASK=task1
JDIR="/root/rhcsa_journal/${LAB}/${TASK}"
mkdir -p "$JDIR"
cp /tmp/lab46a/task1.txt "$JDIR/evidence.txt"

cat > "$JDIR/notes.txt" <<EOF
TOPIC:    lsattr baseline, -d directory attrs, -R recursive attrs
COMMANDS: lsattr /etc/passwd, lsattr -d /tmp, lsattr -R /tmp/lab46a
TRAPS:    T46-A filesystem differences, T46-B special-path errors
EOF
```

> **STOP — paste `lsattr /etc/passwd`, `lsattr -d /tmp`, and one recursive sample line before Task 2.**

---

## Task 2 — Apply `chattr +A`, verify with `lsattr`, contrast with `chattr +S`

**Practice directory this task:** `/tmp`

### Warm-Up

```bash
touch /tmp/lab46a/noatime.txt /tmp/lab46a/sync.txt
ls -l /tmp/lab46a/noatime.txt /tmp/lab46a/sync.txt
echo "Warm-up done by $(whoami) at $(date -Is)"
echo "exit was: $?"
```

### Purpose

Practice setting and reading two important bits: `A` (no atime updates) and `S` (sync writes), and compare behavior expectations.

### Main Command Block

```bash
TASKLOG=/tmp/lab46a/task2.txt

touch /tmp/lab46a/noatime.txt /tmp/lab46a/sync.txt

# Apply +A and verify
chattr +A /tmp/lab46a/noatime.txt                         2>&1 | tee "${TASKLOG}" || true
lsattr /tmp/lab46a/noatime.txt                            2>&1 | tee -a "${TASKLOG}"

# Contrast with +S
chattr +S /tmp/lab46a/sync.txt                            2>&1 | tee -a "${TASKLOG}" || true
lsattr /tmp/lab46a/sync.txt                               2>&1 | tee -a "${TASKLOG}"

# T46-B demo: sparse/special path may error depending on FS/implementation
truncate -s 1G /tmp/lab46a/sparse.img
lsattr /tmp/lab46a/sparse.img                             2>&1 | tee -a "${TASKLOG}" || true
lsattr /proc/kcore                                        2>&1 | tee -a "${TASKLOG}" || true

echo "exit was: $?"
```

### Human-Readable Contrast

- `+A` reduces atime metadata churn on reads.
- `+S` requests synchronous update semantics, trading speed for durability behavior.
- Filesystem support varies; record real output, do not force expected letters.

### PERSISTENCE CHECK

| What was configured | Verification command | Why it matters |
|---|---|---|
| `+A` attempted and captured | `grep -E 'noatime.txt|A' /tmp/lab46a/task2.txt` | Evidence of no-atime exercise |
| `+S` attempted and captured | `grep -E 'sync.txt|S' /tmp/lab46a/task2.txt` | Evidence of sync-flag contrast |
| Error handling rehearsed | `grep -E 'Inappropriate ioctl|Operation not supported|No such file' /tmp/lab46a/task2.txt` | Validates T46-B reflex |

### Journal Write

```bash
LAB=lab-46a
TASK=task2
JDIR="/root/rhcsa_journal/${LAB}/${TASK}"
mkdir -p "$JDIR"
cp /tmp/lab46a/task2.txt "$JDIR/evidence.txt"

cat > "$JDIR/notes.txt" <<EOF
TOPIC:    chattr +A and +S verification with lsattr
COMMANDS: chattr +A, chattr +S, lsattr, truncate
TRAPS:    T46-A, T46-B
NEXT:     lab-46b ansible shell/register boundary
EOF
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

echo "── Lab 46a cleanup audit ──"
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
