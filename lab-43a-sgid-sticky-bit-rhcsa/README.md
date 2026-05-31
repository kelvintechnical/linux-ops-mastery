# Lab 43a: SGID and Sticky Bit (RHCSA) - `chmod g+s`, `chmod +t`, `2770`, `1777`, `3770`

- **Series:** linux-ops-mastery - Permissions, Ownership, and Collaboration Controls
- **Trilogy:** `43a` (RHCSA hand-typed) -> `43b` (Ansible declarative) -> `43c` (Verify capstone)
- **Time Estimate:** 30-40 minutes
- **Tasks:** 2 (Task 1 SGID group-inherit proof, Task 2 sticky-delete protection proof)
- **Practice Directory (rotation #43):** `/home`
- **Sandbox (Tier B):** `/tmp/lab43a` with `USER=labuser_43_sgid`, `GROUP=labgrp_43_sgid`
- **Traps rehearsed this lab:** **T43-A** (SGID on file vs directory behavior) · **T43-B** (sticky on file is historical/ignored; meaningful on directories) · **T41** (skip destroy-restore drill) · **T44** (cleanup-left-orphan-user/group)

> **This lab's practice directory is `/home`**, but all destructive training commands run in `/tmp/lab43a` to stay safe.

---

## LAB HEADER BLOCK

```bash
echo "ENV:   ${ENV:-DECLARE_ME}"
echo "OS:    $(cat /etc/redhat-release 2>/dev/null || grep PRETTY_NAME /etc/os-release)"
echo "TIME:  $(date -Is)"
echo "USER:  $(whoami)@$(hostname)"
echo "TRAPS: T43-A T43-B T41 T44"
echo "PRACTICE DIR: /home"
ls -ld /home /tmp
```

> **STOP - paste header output before setup.**

---

## Objective

Build correct reflexes for SGID and sticky directories:

1. `chmod 2770 DIR` (`g+s` on directory) forces new files to inherit the directory group.
2. `chmod 1777 DIR` (`+t` sticky) allows shared writes but only file owner/root can delete.
3. `chmod 3770 DIR` combines both SGID and sticky for controlled team collaboration.
4. Avoid trap confusion about SGID/sticky on regular files (T43-A, T43-B).

---

## Concept Card

| Mode | Meaning | Practical effect |
|---|---|---|
| `chmod g+s DIR` | SGID on directory | New entries inherit directory group |
| `chmod 2770 DIR` | rwx for owner+group, no access others, SGID set | Team-private shared directory with group inheritance |
| `chmod +t DIR` | Sticky bit on directory | Only owner/root can delete or rename entries |
| `chmod 1777 DIR` | world-writable + sticky (like `/tmp`) | Everyone can create, only owners can remove own files |
| `chmod 3770 DIR` | SGID + sticky + 770 perms | Team-private shared dir with protected deletes |

> Trap reminder: SGID and sticky are directory semantics in modern admin practice.

---

## Lab-Wide Setup (Tier B Sandbox Stack)

```bash
sudo -i

export LAB_NUM=43
export LAB_SLUG=sgid
export SANDBOX=/tmp/lab43a
export GROUP=labgrp_43_sgid
export USER=labuser_43_sgid
export USER_HOME=${SANDBOX}/home_${USER}

mkdir -p "${SANDBOX}" "${USER_HOME}" /root/rhcsa_journal/lab-43a/task1 /root/rhcsa_journal/lab-43a/task2
mkdir -p /tmp/lab43a/groupdir /tmp/lab43a/shared

getent group "${GROUP}" >/dev/null || groupadd "${GROUP}"
getent passwd "${USER}"  >/dev/null || useradd -d "${USER_HOME}" -M -s /bin/bash -g "${GROUP}" "${USER}"

# Task 2 actors for sticky-bit behavior proof
getent passwd alice >/dev/null || useradd -M -s /bin/bash alice
getent passwd bob   >/dev/null || useradd -M -s /bin/bash bob

chown -R "${USER}:${GROUP}" "${SANDBOX}"
id "${USER}"
getent group "${GROUP}"
```

---

## Task 1 - SGID Directory Group Inheritance (`2770`)

### Purpose

Prove that SGID on a directory applies group inheritance to **new files** created inside that directory.

### Main command block

```bash
cd /tmp/lab43a
TASKLOG=/tmp/lab43a/task1.log

mkdir -p /tmp/lab43a/groupdir
chgrp "${GROUP}" /tmp/lab43a/groupdir
chmod 2770 /tmp/lab43a/groupdir

stat -c '%A %a %U:%G %n' /tmp/lab43a/groupdir | tee "${TASKLOG}"

sudo -u "${USER}" touch /tmp/lab43a/groupdir/file
stat -c '%A %a %U:%G %n' /tmp/lab43a/groupdir/file | tee -a "${TASKLOG}"

# Combined mode example requested in this trilogy
chmod 3770 /tmp/lab43a/groupdir
stat -c '%A %a %U:%G %n' /tmp/lab43a/groupdir | tee -a "${TASKLOG}"

echo "exit was: $?"
```

### Expected proof

- `groupdir` should show `2770` first, then `3770`.
- `/tmp/lab43a/groupdir/file` should show group `${GROUP}` automatically.

### Trap focus (T43-A)

- SGID on a **directory** = group inheritance for new entries.
- SGID on a **regular file** does **not** create group inheritance behavior.

---

## Task 2 - Sticky Directory Delete Protection (`1777`)

### Purpose

Prove that in a sticky directory, write is shared but delete is owner-protected.

### Main command block

```bash
cd /tmp/lab43a
TASKLOG=/tmp/lab43a/task2.log

mkdir -p /tmp/lab43a/shared
chmod 1777 /tmp/lab43a/shared
stat -c '%A %a %U:%G %n' /tmp/lab43a/shared | tee "${TASKLOG}"

sudo -u alice touch /tmp/lab43a/shared/alice.txt
ls -l /tmp/lab43a/shared/alice.txt | tee -a "${TASKLOG}"

# Sticky should block this delete attempt
sudo -u bob rm /tmp/lab43a/shared/alice.txt 2>&1 | tee -a "${TASKLOG}" || true
ls -l /tmp/lab43a/shared | tee -a "${TASKLOG}"

echo "exit was: $?"
```

### Expected proof

- `rm` by `bob` fails with `Operation not permitted` (or equivalent permission denial).
- `alice.txt` remains present after Bob's delete attempt.

### Trap focus (T43-B)

- Sticky bit on a **file** is not the operational control admins rely on.
- Sticky bit is meaningful on **directories** for delete/rename protection.

---

## Lab Closeout (Section 6) - Destroy and Audit

```bash
set +e

# Remove sandbox artifacts
rm -rf /tmp/lab43a

# Remove lab principal/group
if getent passwd "${USER}" >/dev/null 2>&1; then
    userdel -r "${USER}" 2>/dev/null
fi
if getent group "${GROUP}" >/dev/null 2>&1; then
    groupdel "${GROUP}" 2>/dev/null
fi

# Optional: keep alice/bob if your environment uses them globally.
# Uncomment only if they were created solely for this lab.
# userdel alice 2>/dev/null
# userdel bob 2>/dev/null

echo "-- Lab 43a cleanup audit --"
getent passwd "${USER}" >/dev/null && echo "FAIL user remains" || echo "OK user gone"
getent group "${GROUP}" >/dev/null && echo "FAIL group remains" || echo "OK group gone"
test -d /tmp/lab43a && echo "FAIL sandbox remains" || echo "OK sandbox gone"

set -e
echo "Cleanup complete at $(date -Is)"
```

---

## Checklist

- [ ] Task 1: `chmod 2770` SGID directory created and file inherited `${GROUP}`
- [ ] Task 2: `chmod 1777` sticky behavior blocked cross-user delete
- [ ] Trap T43-A reviewed (SGID dir vs file)
- [ ] Trap T43-B reviewed (sticky meaningful on dirs)
- [ ] Section 6 closeout completed with audit checks

---

## Author

**Kelvin R. Tobias**
