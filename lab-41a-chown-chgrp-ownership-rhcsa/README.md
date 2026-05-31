# Lab 41a: Changing Ownership (RHCSA) — `chown`, `chgrp`, `stat -c '%U:%G'`

- **Series:** linux-ops-mastery — Files, Permissions, and Identity
- **Trilogy:** `41a` (RHCSA hand-typed) → [`41b`](../lab-41b-chown-chgrp-ownership-ansible/) (Ansible) → [`41c`](../lab-41c-chown-chgrp-ownership-verify/) (Verify)
- **Time Estimate:** 30-40 minutes
- **Tasks:** 2
- **Practice Directory (objective context):** `/etc` (read-only inspection only)
- **Sandbox (Tier B):** `/tmp/lab41a` with `USER=labuser_41_chown`, `GROUP=labgrp_41_chown`
- **Traps rehearsed:** **T41-A** (`user.group` dot syntax is legacy; `user:group` is canonical) · **T41-B** (`chown -R` and symlinks: use `-h` / `--no-dereference` when needed) · **T41** (destroy-restore drill appears in 41c) · **T44** (cleanup audit)

> **Variable warning:** this lab exports `USER=labuser_41_chown` for the sandbox. Do not confuse this shell variable with the literal user field in `chown` syntax.

---

## LAB HEADER BLOCK

```bash
echo "📁 PRACTICE DIR: /etc (read-only), /tmp/lab41a (write target)"
echo "👤 USER: $(whoami)@$(hostname)"
echo "🕒 TIME: $(date -Is)"
echo "⚠️ TRAPS: T41-A T41-B T41 T44"
id
ls -ld /etc /tmp
```

> **STOP — paste output before setup.**

---

## Objective

Build ownership reflexes you use on every RHCSA storage and config task:

1. Set owner and group together with `chown user:group`.
2. Set only group with `chown :group` and compare with `chgrp`.
3. Apply ownership recursively with `chown -R`.
4. Copy ownership from a known-good file with `chown --reference`.
5. Verify every change with `stat -c '%U:%G %a %n'` and `ls -l`.

---

## Lab-Wide Setup — Tier B Sandbox

```bash
sudo -i

export LAB_NUM=41
export LAB_SLUG=chown
export SANDBOX=/tmp/lab41a
export GROUP=labgrp_41_chown
export USER=labuser_41_chown
export USER_HOME=${SANDBOX}/home_${USER}

mkdir -p "${SANDBOX}/task1" "${SANDBOX}/task2" "${USER_HOME}"
mkdir -p /root/rhcsa_journal/lab-41a/task1
mkdir -p /root/rhcsa_journal/lab-41a/task2

getent group "${GROUP}" >/dev/null || groupadd "${GROUP}"
getent passwd "${USER}" >/dev/null || useradd -d "${USER_HOME}" -M -s /bin/bash -g "${GROUP}" "${USER}"
chown -R "${USER}:${GROUP}" "${SANDBOX}"

id "${USER}"
stat -c '%U:%G %a %n' "${SANDBOX}" "${USER_HOME}"
```

---

## Task 1 — Direct ownership changes (`chown user:group`, `chown :group`)

### Purpose

Practice the two most-tested ownership patterns: set both owner+group, then set group-only.

### Main command block

```bash
TASKLOG=/tmp/lab41a/task1/task1.txt

touch /tmp/lab41a/task1/file1 /tmp/lab41a/task1/file2
chown "${USER}:${GROUP}" /tmp/lab41a/task1/file1 /tmp/lab41a/task1/file2

# Group-only change (owner unchanged)
chown :nobody /tmp/lab41a/task1/file2

# Legacy dot syntax still works but is non-canonical:
# chown "${USER}.${GROUP}" /tmp/lab41a/task1/file1

ls -l /tmp/lab41a/task1 | tee "${TASKLOG}"
stat -c '%U:%G %n' /tmp/lab41a/task1/file1 /tmp/lab41a/task1/file2 | tee -a "${TASKLOG}"
id "${USER}" | tee -a "${TASKLOG}"
echo "exit was: $?"
```

### Expected checks

- `file1` should be `${USER}:${GROUP}`
- `file2` owner should stay `${USER}` while group becomes `nobody`

### Journal write

```bash
cp /tmp/lab41a/task1/task1.txt /root/rhcsa_journal/lab-41a/task1/evidence.txt
cat > /root/rhcsa_journal/lab-41a/task1/done.txt <<EOF
LAB: lab-41a
TASK: task1
DATE: $(date -Is)
STATUS: COMPLETE
EOF
```

---

## Task 2 — Recursive and reference ownership (`chown -R`, `--reference`)

### Purpose

Apply ownership through a subtree, then clone ownership from a template file exactly.

### Main command block

```bash
TASKLOG=/tmp/lab41a/task2/task2.txt

mkdir -p /tmp/lab41a/task2/tree/sub
touch /tmp/lab41a/task2/tree/root.txt /tmp/lab41a/task2/tree/sub/leaf.txt
touch /tmp/lab41a/task2/template.ref /tmp/lab41a/task2/copy.ref

# Seed template with a distinct owner/group first
chown root:root /tmp/lab41a/task2/template.ref
chown "${USER}:${GROUP}" /tmp/lab41a/task2/copy.ref

# Recursive apply
chown -R "${USER}:${GROUP}" /tmp/lab41a/task2/tree

# Copy ownership from reference file
chown --reference=/tmp/lab41a/task2/template.ref /tmp/lab41a/task2/copy.ref

stat -c '%U:%G %n' \
  /tmp/lab41a/task2/tree/root.txt \
  /tmp/lab41a/task2/tree/sub/leaf.txt \
  /tmp/lab41a/task2/template.ref \
  /tmp/lab41a/task2/copy.ref | tee "${TASKLOG}"

# Symlink trap demo reminder (T41-B): consider -h/--no-dereference when needed
echo "T41-B reminder: chown -R may dereference symlink targets; use -h/--no-dereference intentionally." | tee -a "${TASKLOG}"
echo "exit was: $?"
```

### Journal write

```bash
cp /tmp/lab41a/task2/task2.txt /root/rhcsa_journal/lab-41a/task2/evidence.txt
cat > /root/rhcsa_journal/lab-41a/task2/done.txt <<EOF
LAB: lab-41a
TASK: task2
DATE: $(date -Is)
STATUS: COMPLETE
EOF
```

---

## Lab Closeout — Section 6 Teardown

```bash
set +e
userdel -r "${USER}" 2>/dev/null
groupdel "${GROUP}" 2>/dev/null
rm -rf "${SANDBOX}"

echo "── Lab 41a cleanup audit ──"
getent passwd "${USER}" >/dev/null && echo "❌ user remains" || echo "✅ user gone"
getent group "${GROUP}" >/dev/null && echo "❌ group remains" || echo "✅ group gone"
test -d "${SANDBOX}" && echo "❌ sandbox remains" || echo "✅ sandbox gone"
test -d "${USER_HOME}" && echo "❌ home remains" || echo "✅ home gone"
set -e
```

---

## Author

**Kelvin R. Tobias**
