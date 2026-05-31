# Lab 37a: Configuring Local Host Resolution (RHCSA) — `/etc/hosts`, `getent hosts`, `nsswitch.conf`

- **Series:** linux-ops-mastery — Networking Name Resolution Fundamentals
- **Trilogy:** **`37a`** (RHCSA hand-typed) → [`37b`](../lab-37b-etc-hosts-resolution-ansible/) (Ansible) → [`37c`](../lab-37c-etc-hosts-resolution-verify/) (Verify capstone)
- **Time Estimate:** 25–35 minutes
- **Tasks:** 2 (Task 1 = safe edit + verify lookup path, Task 2 = restore + cleanup proof)
- **Practice Directory (rotation #37):** `/sbin`
- **Sandbox (Tier B):** `/tmp/lab37a` with `USER=labuser_37_hosts`, `GROUP=labgrp_37_hosts`, `USER_HOME=/tmp/lab37a/home_labuser_37_hosts`
- **Traps rehearsed this lab:** **T37-A** (editing `/etc/hosts` without a backup) · **T37-B** (`hosts:` order in `/etc/nsswitch.conf` changes priority) · **T41** (skip destroy-restore drill) · **T44** (cleanup leaves residue)

> **This lab's practice directory is: `/sbin`** — we keep command-path awareness while performing system-safe host resolution changes under `/etc`.

---

## LAB HEADER BLOCK

```bash
echo "🖥️  ENV:   ${ENV:-DECLARE_ME}"
echo "📦  OS:    $(cat /etc/redhat-release 2>/dev/null || grep PRETTY_NAME /etc/os-release)"
echo "🕒  TIME:  $(date -Is)"
echo "👤  USER:  $(whoami)@$(hostname)"
echo "⚠️  TRAP REMINDERS THIS LAB: T37-A T37-B T41 T44"
echo "📁  PRACTICE DIR: /sbin"
echo "PATH: $PATH"
ls -ld /sbin /etc/hosts /etc/nsswitch.conf
```

---

## Objective

Build an exam-safe reflex for local hostname mapping:

1. Always back up `/etc/hosts` before any edit (**T37-A** defense).
2. Add and validate a local hostname mapping with `getent hosts`.
3. Understand `hosts:` lookup order in `/etc/nsswitch.conf` (`files dns` vs `dns files`) and why it changes resolution priority (**T37-B**).
4. Restore clean state and prove cleanup.

---

## Lab-Wide Setup — Tier B Sandbox

```bash
sudo -i

export LAB_NUM=37
export LAB_SLUG=hosts
export SANDBOX=/tmp/lab37a
export GROUP=labgrp_${LAB_NUM}_${LAB_SLUG}
export USER=labuser_${LAB_NUM}_${LAB_SLUG}
export USER_HOME=${SANDBOX}/home_${USER}

mkdir -p "${SANDBOX}" "${USER_HOME}"
mkdir -p /root/rhcsa_journal/lab-37a/task1
mkdir -p /root/rhcsa_journal/lab-37a/task2

getent group  "${GROUP}" >/dev/null || groupadd "${GROUP}"
getent passwd "${USER}"  >/dev/null || useradd -d "${USER_HOME}" -M -s /bin/bash -g "${GROUP}" "${USER}"
chown -R "${USER}:${GROUP}" "${SANDBOX}"

id "${USER}"
getent group "${GROUP}"
getent passwd "${USER}"
```

---

## Task 1 — Backup, edit `/etc/hosts`, and validate with `getent`

### Purpose

Perform the exact safe workflow for host-file edits and confirm name resolution behavior.

### Main command block

```bash
TASKLOG=/tmp/lab37a/task1.txt

# Required safety step (T37-A defense)
cp /etc/hosts /tmp/lab37a/hosts.bak
ls -l /tmp/lab37a/hosts.bak | tee "$TASKLOG"

# Required exercise mapping
echo '10.99.99.99 lab37test.local' | sudo tee -a /etc/hosts

# Validate local resolution now works
getent hosts lab37test.local | tee -a "$TASKLOG"

# Show current hosts lookup policy (T37-B context)
grep '^hosts:' /etc/nsswitch.conf | tee -a "$TASKLOG"

echo "exit was: $?"
```

### Expected result

- `getent hosts lab37test.local` returns `10.99.99.99 lab37test.local`
- `hosts:` line is visible (commonly `hosts: files dns`)

---

## Task 2 — Restore backup and prove cleanup

### Purpose

Return the system to pre-lab state and prove no stale mapping remains.

### Main command block

```bash
TASKLOG=/tmp/lab37a/task2.txt

# Restore exact original file
cp /tmp/lab37a/hosts.bak /etc/hosts

# Verify restored file equals backup
diff -u /tmp/lab37a/hosts.bak /etc/hosts | tee "$TASKLOG"

# Verify cleanup of test name
getent hosts lab37test.local | tee -a "$TASKLOG" || true

# Journal copy
cp /tmp/lab37a/task1.txt /root/rhcsa_journal/lab-37a/task1/evidence.txt
cp /tmp/lab37a/task2.txt /root/rhcsa_journal/lab-37a/task2/evidence.txt

echo "exit was: $?"
```

### Expected result

- `diff -u` is empty output
- `getent hosts lab37test.local` returns no mapping after restore

---

## Lab Closeout — Section 6 Bulletproof Teardown

```bash
set +e

awk -v s="${SANDBOX}" '$2 ~ s {print $2}' /proc/mounts | tac | xargs -r -n1 umount -l 2>/dev/null

if getent passwd "${USER}" >/dev/null 2>&1; then userdel -r "${USER}" 2>/dev/null; fi
if getent group  "${GROUP}" >/dev/null 2>&1; then groupdel "${GROUP}"  2>/dev/null; fi
rm -rf "${SANDBOX}"

echo "── Lab 37a cleanup audit ──"
getent passwd "${USER}" >/dev/null && echo "❌ user remains"    || echo "✅ user gone"
getent group  "${GROUP}" >/dev/null && echo "❌ group remains"   || echo "✅ group gone"
test -d "${SANDBOX}"               && echo "❌ sandbox remains" || echo "✅ sandbox gone"
test -d "${USER_HOME}"             && echo "❌ home remains"    || echo "✅ home gone"

set -e
```

---

## Lab 37a Checklist

- [ ] Backed up `/etc/hosts` before editing (**T37-A**)
- [ ] Added `10.99.99.99 lab37test.local` and verified with `getent hosts`
- [ ] Reviewed `hosts:` order in `/etc/nsswitch.conf` (**T37-B**)
- [ ] Restored `/etc/hosts` from backup and proved cleanup
- [ ] Ran Section 6 closeout audit with four `✅` lines (**T44**)

---

## Author

**Kelvin R. Tobias**  
[kelvinintech.com](https://kelvinintech.com) · [GitHub](https://github.com/kelvintechnical) · [LinkedIn](https://www.linkedin.com/in/kelvin-r-tobias-211949219)
