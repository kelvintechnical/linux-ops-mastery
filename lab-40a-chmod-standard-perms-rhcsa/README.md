# Lab 40a: Standard File Permissions (RHCSA) - `chmod`, symbolic and octal modes

- **Series:** linux-ops-mastery - Identity, Permissions, and Access
- **Trilogy:** `40a` (RHCSA hand-typed) -> [`40b`](../lab-40b-chmod-standard-perms-ansible/) (Ansible) -> [`40c`](../lab-40c-chmod-standard-perms-verify/) (Verify)
- **Time Estimate:** 25-35 minutes
- **Tasks:** 2 (Task 1 = octal permissions + verification, Task 2 = symbolic changes + setuid and `+X` behavior)
- **Practice Directory (rotation #40):** `/usr`
- **Sandbox (Tier B):** `/tmp/lab40a` with `USER=labuser_40_chmod`, `GROUP=labgrp_40_chmod`, `USER_HOME=/tmp/lab40a/home_labuser_40_chmod`
- **Traps rehearsed this lab:** **T40-A** (`644` vs `0644` confusion, accidental 4-digit setuid mode) ; **T40-B** (never run `chmod -R` on `/` or system dirs) ; **T41** ; **T44**

> **This lab's practice directory is: `/usr`**. All chmod practice happens in the Tier B sandbox under `/tmp/lab40a`.

---

## LAB HEADER BLOCK

```bash
echo "📦 OS: $(cat /etc/redhat-release 2>/dev/null || grep PRETTY_NAME /etc/os-release)"
echo "🕒 TIME: $(date -Is)"
echo "👤 USER: $(whoami)@$(hostname)"
echo "📁 PRACTICE DIR: /usr"
echo "⚠️ TRAPS: T40-A T40-B T41 T44"
ls -ld /usr
umask
```

---

## Objective

Build exam-safe reflexes for standard mode bits:

1. Apply and read octal modes (`755`, `644`, `600`, `700`).
2. Apply symbolic changes (`u+r`, `g-w`, `o+x`) and understand combined symbolic expressions.
3. Verify mode state from two angles: `ls -l` (human) and `stat -c %a` (machine-safe).
4. Avoid dangerous permission mistakes under pressure.

---

## Lab-Wide Setup - Tier B Sandbox

```bash
sudo -i

export LAB_NUM=40
export LAB_SLUG=chmod
export SANDBOX=/tmp/lab40a
export GROUP=labgrp_${LAB_NUM}_${LAB_SLUG}
export USER=labuser_${LAB_NUM}_${LAB_SLUG}
export USER_HOME=${SANDBOX}/home_${USER}

mkdir -p "${SANDBOX}" "${USER_HOME}" /root/rhcsa_journal/lab-40a/{task1,task2}

getent group  "${GROUP}" >/dev/null || groupadd "${GROUP}"
getent passwd "${USER}"  >/dev/null || useradd -d "${USER_HOME}" -M -s /bin/bash -g "${GROUP}" "${USER}"
chown -R "${USER}:${GROUP}" "${SANDBOX}"

id "${USER}"
ls -ld "${SANDBOX}" "${USER_HOME}"
```

---

## Task 1 - Apply octal permissions and verify (`755`, `644`, `600`)

### Purpose

Apply core RHCSA permission targets with octal syntax and confirm each result with both `ls -l` and `stat -c %a`.

### Main command block

```bash
set -o pipefail
TASKLOG=/tmp/lab40a/task1.txt

mkdir -p /tmp/lab40a/bin /tmp/lab40a/docs
touch /tmp/lab40a/bin/run.sh /tmp/lab40a/docs/readme.txt /tmp/lab40a/secret.txt

chmod 755 /tmp/lab40a/bin/run.sh
chmod 644 /tmp/lab40a/docs/readme.txt
chmod 600 /tmp/lab40a/secret.txt

ls -l /tmp/lab40a/bin/run.sh /tmp/lab40a/docs/readme.txt /tmp/lab40a/secret.txt | tee "${TASKLOG}"
stat -c '%a %n' /tmp/lab40a/bin/run.sh /tmp/lab40a/docs/readme.txt /tmp/lab40a/secret.txt | tee -a "${TASKLOG}"

echo "exit was: $?"
```

### Trap guard (T40-A)

```bash
# These are equivalent for chmod:
chmod 644 /tmp/lab40a/docs/readme.txt
chmod 0644 /tmp/lab40a/docs/readme.txt

# This is different and dangerous if accidental:
chmod 4644 /tmp/lab40a/docs/readme.txt
stat -c '%a %A %n' /tmp/lab40a/docs/readme.txt

# Restore expected mode:
chmod 644 /tmp/lab40a/docs/readme.txt
```

> `644` and `0644` are the same permission target in `chmod`; accidental **four-digit** values like `4644` add special bits (`setuid`) and change behavior.

---

## Task 2 - Symbolic chmod, setuid contrast, and `+X` on directories

### Purpose

Use symbolic syntax for targeted edits and understand where symbolic mode is clearer than octal, especially for mixed delta operations.

### Main command block

```bash
set -o pipefail
TASKLOG=/tmp/lab40a/task2.txt

mkdir -p /tmp/lab40a/tree/dirA /tmp/lab40a/tree/dirB
touch /tmp/lab40a/tree/dirA/a.txt /tmp/lab40a/tree/dirB/b.txt
chmod 644 /tmp/lab40a/tree/dirA/a.txt /tmp/lab40a/tree/dirB/b.txt
chmod 644 /tmp/lab40a/tree/dirA /tmp/lab40a/tree/dirB

# Symbolic contrast block
chmod u+s /tmp/lab40a/bin/run.sh
chmod g-w /tmp/lab40a/docs/readme.txt
chmod o-r /tmp/lab40a/docs/readme.txt

# Capital X: add execute only to directories (and already executable files)
chmod -R a+X /tmp/lab40a/tree

ls -ld /tmp/lab40a/tree /tmp/lab40a/tree/dirA /tmp/lab40a/tree/dirB | tee "${TASKLOG}"
ls -l /tmp/lab40a/bin/run.sh /tmp/lab40a/docs/readme.txt /tmp/lab40a/tree/dirA/a.txt /tmp/lab40a/tree/dirB/b.txt | tee -a "${TASKLOG}"
stat -c '%a %A %n' /tmp/lab40a/bin/run.sh /tmp/lab40a/docs/readme.txt /tmp/lab40a/tree/dirA /tmp/lab40a/tree/dirA/a.txt | tee -a "${TASKLOG}"

echo "exit was: $?"
```

### Trap guard (T40-B)

```bash
echo "NEVER run chmod -R on / or /usr in production."
echo "Safe pattern: scope recursion to explicit sandbox paths only."
echo "Example safe command used in this lab: chmod -R a+X /tmp/lab40a/tree"
```

---

## Lab Closeout - Section 6 Bulletproof Teardown

```bash
set +e

awk -v s="${SANDBOX}" '$2 ~ s {print $2}' /proc/mounts | tac | xargs -r -n1 umount -l 2>/dev/null

if getent passwd "${USER}" >/dev/null 2>&1; then userdel -r "${USER}" 2>/dev/null; fi
if getent group  "${GROUP}" >/dev/null 2>&1; then groupdel "${GROUP}"  2>/dev/null; fi
rm -rf "${SANDBOX}"

echo "── Lab 40a cleanup audit ──"
getent passwd "${USER}" >/dev/null && echo "❌ user remains"    || echo "✅ user gone"
getent group  "${GROUP}" >/dev/null && echo "❌ group remains"   || echo "✅ group gone"
test -d "${SANDBOX}"               && echo "❌ sandbox remains" || echo "✅ sandbox gone"
test -d "${USER_HOME}"             && echo "❌ home remains"    || echo "✅ home gone"

set -e
```

---

## Lab 40a Checklist

- [ ] Task 1 completed with `chmod 755`, `chmod 644`, `chmod 600`
- [ ] Verified with both `ls -l` and `stat -c %a`
- [ ] Task 2 completed with symbolic edits (`u+s`, `g-w`, `o-r`) and `a+X`
- [ ] T40-A and T40-B trap guards reviewed
- [ ] Section 6 closeout produced four `✅` lines

---

## Author

**Kelvin R. Tobias**  
[kelvinintech.com](https://kelvinintech.com) · [GitHub](https://github.com/kelvintechnical) · [LinkedIn](https://www.linkedin.com/in/kelvin-r-tobias-211949219)
