# Lab 50a: Denying Access via ACLs (RHCSA) — `setfacl -m u:user:---`

- **Series:** linux-ops-mastery — Permissions, Ownership, and ACL Control
- **Trilogy:** `50a` (RHCSA hand-typed) → [`50b`](../lab-50b-setfacl-deny-ansible/) (Ansible) → [`50c`](../lab-50c-setfacl-deny-verify/) (Verify)
- **Time Estimate:** 25–35 minutes
- **Tasks:** 2 (Task 1 = explicit zero-permission ACL deny pattern; Task 2 = remove ACL entry and contrast with fallback)
- **Practice Directory (rotation #50):** `/proc` (read-only mount for inspection only)
- **Sandbox (Tier B):** `/tmp/lab50a` with `USER=labuser_50_aclden`, `USER_B=labuser_50_aclden_b`, `GROUP=labgrp_50_aclden`
- **Traps rehearsed this lab:** **T50-A** (Linux POSIX ACLs do not have true deny entries; zero-perm ACL is a simulation pattern) · **T50-B** (absent ACL entry is not the same as explicit `---`) · **T41** (destroy-restore habit deferred to 50c) · **T44** (closeout must prove no identity residue)

> **This lab's practice directory is: `/proc`**. Because `/proc` is read-only and kernel-managed, we do all writes in `/tmp/lab50a` while using `/proc` for context checks.

---

## LAB HEADER BLOCK

```bash
echo "🖥️  ENV:   ${ENV:-DECLARE_ME}"
echo "📦  OS:    $(cat /etc/redhat-release 2>/dev/null || grep PRETTY_NAME /etc/os-release)"
echo "🕒  TIME:  $(date -Is)"
echo "👤  USER:  $(whoami)@$(hostname)"
echo "⚠️  TRAP REMINDERS THIS LAB: T50-A T50-B T41 T44"
echo "📁  PRACTICE DIR: /proc"
echo ""
echo "💡 /proc context (read-only check):"
mount | grep " on /proc "
ls -ld /proc
```

> **STOP — paste header output before setup.**

---

## Objective

Practice the Linux POSIX ACL "deny-by-explicit-zero" pattern so it becomes exam reflex:

1. Set a file to base mode `0644` (world-readable).
2. Add an ACL entry with no permissions for one specific user: `setfacl -m u:USER_B:--- FILE`.
3. Prove that user is denied even though base mode still grants world read.
4. Remove the explicit entry and prove access falls back to normal mode evaluation.

---

## Concept: Linux POSIX ACL Has No True Deny Keyword

Linux POSIX ACLs do not implement NFSv4-style deny entries. The practical workaround is:

- add a named-user ACL entry with zero permissions (`---` or `0`)
- this explicit entry is evaluated before fallback to group/other bits
- removing the entry (`setfacl -x`) restores normal fallback behavior

T50-B group form of the same rule:

- `setfacl -m g:GROUP:--- FILE` explicitly denies that named group entry
- if that group ACL entry is absent, evaluation can fall through to `other::` bits

That contrast (explicit zero vs absent entry) is the core skill in this trilogy.

---

## Lab-Wide Setup — Tier B Sandbox Stack (Section 1.5)

```bash
sudo -i

export LAB_NUM=50
export LAB_SLUG=aclden
export SANDBOX=/tmp/lab50a
export GROUP=labgrp_${LAB_NUM}_${LAB_SLUG}
export USER=labuser_${LAB_NUM}_${LAB_SLUG}
export USER_B=labuser_${LAB_NUM}_${LAB_SLUG}_b
export USER_HOME=${SANDBOX}/home_${USER}
export USER_B_HOME=${SANDBOX}/home_${USER_B}

mkdir -p "${SANDBOX}" "${USER_HOME}" "${USER_B_HOME}"
mkdir -p /root/rhcsa_journal/lab-50a/task1
mkdir -p /root/rhcsa_journal/lab-50a/task2

getent group "${GROUP}" >/dev/null || groupadd "${GROUP}"
getent passwd "${USER}" >/dev/null || useradd -d "${USER_HOME}" -M -s /bin/bash -g "${GROUP}" "${USER}"
getent passwd "${USER_B}" >/dev/null || useradd -d "${USER_B_HOME}" -M -s /bin/bash -g "${GROUP}" "${USER_B}"

chown -R "${USER}:${GROUP}" "${USER_HOME}"
chown -R "${USER_B}:${GROUP}" "${USER_B_HOME}"
chown root:root "${SANDBOX}"
chmod 0755 "${SANDBOX}"

id "${USER}"
id "${USER_B}"
getent group "${GROUP}"
ls -ld "${SANDBOX}" "${USER_HOME}" "${USER_B_HOME}"
```

> **STOP — paste both `id` lines, `getent group`, and the three `ls -ld` lines before Task 1.**

---

## Task 1 — Deny one user with explicit zero ACL entry

### Purpose

Demonstrate that ACL entries can override permissive base bits for a specific named user.

### Main command block

```bash
TASKLOG=/tmp/lab50a/task1.txt
ACLFILE=/tmp/lab50a/public.txt

# Create as ${USER}, world-readable base mode
sudo -u "${USER}" bash -c 'echo "lab50a ACL deny demo" > '"${ACLFILE}"
chmod 0644 "${ACLFILE}"
stat -c '%U:%G %a %n' "${ACLFILE}"                           | tee "${TASKLOG}"

# Baseline: USER_B can read before ACL deny (because mode is 0644)
sudo -u "${USER_B}" cat "${ACLFILE}"                         | tee -a "${TASKLOG}"

# Explicit deny-by-zero ACL entry
setfacl -m u:"${USER_B}":--- "${ACLFILE}"
getfacl "${ACLFILE}"                                          | tee -a "${TASKLOG}"

# Access attempt should now fail for USER_B despite world-readable base perms
sudo -u "${USER_B}" cat "${ACLFILE}" 2>&1                     | tee -a "${TASKLOG}"
echo "exit was: $?"                                           | tee -a "${TASKLOG}"
```

### Expected signal

- `stat` shows mode `644`
- `getfacl` contains `user:labuser_50_aclden_b:---`
- `sudo -u "${USER_B}" cat` returns permission denied

### Trap callout (T50-B)

`other::r--` is still present in mode `0644`, but named-user ACL `---` for `USER_B` wins for that user. This is exactly why explicit zero differs from no ACL entry.

---

## Task 2 — Remove explicit entry and contrast with absent ACL

### Purpose

Prove that deleting the named-user ACL entry restores fallback to standard mode bits.

### Main command block

```bash
TASKLOG=/tmp/lab50a/task2.txt
ACLFILE=/tmp/lab50a/public.txt

# Remove deny ACL entry
setfacl -x u:"${USER_B}" "${ACLFILE}"
getfacl "${ACLFILE}"                                          | tee "${TASKLOG}"

# USER_B should read again via fallback to other::r--
sudo -u "${USER_B}" cat "${ACLFILE}"                          | tee -a "${TASKLOG}"
echo "exit was: $?"                                           | tee -a "${TASKLOG}"
```

### Contrast card

- **Explicit zero entry exists (`u:USER_B:---`)** → access denied for `USER_B`
- **Entry absent (`setfacl -x u:USER_B`)** → permission fallback applies (`other::r--` from mode `0644`)
- **Group explicit zero (`g:GROUP:---`)** → that group path is blocked explicitly
- **Group entry absent** → group path may fall through and `other::` can still permit read

---

## Lab Closeout — Bulletproof Teardown (Section 6)

```bash
set +e

# 1) Unmount anything nested under sandbox (normally no-op)
awk -v s="${SANDBOX}" '$2 ~ s {print $2}' /proc/mounts | tac | xargs -r -n1 umount -l 2>/dev/null

# 2) Remove users first (both USER and USER_B), then group
if getent passwd "${USER}" >/dev/null 2>&1; then userdel -r "${USER}" 2>/dev/null; fi
if getent passwd "${USER_B}" >/dev/null 2>&1; then userdel -r "${USER_B}" 2>/dev/null; fi
if getent group "${GROUP}" >/dev/null 2>&1; then groupdel "${GROUP}" 2>/dev/null; fi

# 3) Remove sandbox
rm -rf "${SANDBOX}"

# 4) Audit
echo "── Lab 50a cleanup audit ──"
getent passwd "${USER}"   >/dev/null && echo "❌ ${USER} remains"   || echo "✅ ${USER} gone"
getent passwd "${USER_B}" >/dev/null && echo "❌ ${USER_B} remains" || echo "✅ ${USER_B} gone"
getent group  "${GROUP}"  >/dev/null && echo "❌ ${GROUP} remains"  || echo "✅ ${GROUP} gone"
test -d "${SANDBOX}"                    && echo "❌ sandbox remains" || echo "✅ sandbox gone"

set -e
```

> **STOP — paste the four cleanup audit lines before marking Lab 50a complete.**

---

## Lab 50a Checklist (2 tasks + closeout)

- [ ] Setup created `${USER}`, `${USER_B}`, `${GROUP}`, and `/tmp/lab50a`
- [ ] Task 1 proved explicit zero ACL deny on a mode `0644` file
- [ ] Task 2 removed entry and proved access restored via fallback
- [ ] Closeout removed both users, group, and sandbox with audit proof

---

## Related Labs

| Lab | Connection |
|---|---|
| **Lab 50b** — Ansible ACL deny pattern | Same deny-by-zero behavior using `ansible.posix.acl` |
| **Lab 50c** — Verify ACL deny pattern | Auditor seat: inspect ACL entries + destroy-restore drill |

---

## Author

**Kelvin R. Tobias**  
[kelvinintech.com](https://kelvinintech.com) · [GitHub](https://github.com/kelvintechnical) · [LinkedIn](https://www.linkedin.com/in/kelvin-r-tobias-211949219)
