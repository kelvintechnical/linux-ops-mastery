# Lab 50c: Verifying ACL Deny Pattern (Capstone) — audit + destroy-restore

- **Series:** linux-ops-mastery — Permissions, Ownership, and ACL Control
- **Trilogy:** [`50a`](../lab-50a-setfacl-deny-rhcsa/) (RHCSA) → [`50b`](../lab-50b-setfacl-deny-ansible/) (Ansible) → `50c` (Verify capstone)
- **Time Estimate:** 25–35 minutes
- **Tasks:** 2 (Task 1 = ACL audit proof; Task 2 = destroy-restore with `setfacl -b` then re-apply)
- **Practice Directory (rotation #50):** `/proc` (inspection only; writes in `/tmp/lab50c`)
- **Sandbox (Tier B):** `/tmp/lab50c` with `USER=labuser_50_aclden`, `USER_B=labuser_50_aclden_b`, `GROUP=labgrp_50_aclden`
- **Traps rehearsed this lab:** **T50-A** (no true deny keyword; explicit zero pattern) · **T50-B** (explicit zero vs absent entry) · **T41** (destroy-restore discipline) · **T44** (closeout audit must show no residue)

> **This lab's practice directory is: `/proc`**. `/proc` is for read-only context; ACL state is exercised in `/tmp/lab50c`.

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
mount | grep " on /proc "
ls -ld /proc
```

---

## Objective

Audit and rebuild ACL deny behavior so you can prove ACL state, lose it safely, and restore it correctly:

1. Audit ACL entries and effective behavior for owner user vs denied user.
2. Run a destroy-restore drill: clear ACLs with `setfacl -b`, verify fallback, then re-apply explicit zero deny and verify denial returns.

---

## Lab-Wide Setup — Tier B Sandbox Stack (Section 1.5)

```bash
sudo -i

export LAB_NUM=50
export LAB_SLUG=aclden
export SANDBOX=/tmp/lab50c
export GROUP=labgrp_${LAB_NUM}_${LAB_SLUG}
export USER=labuser_${LAB_NUM}_${LAB_SLUG}
export USER_B=labuser_${LAB_NUM}_${LAB_SLUG}_b
export USER_HOME=${SANDBOX}/home_${USER}
export USER_B_HOME=${SANDBOX}/home_${USER_B}
export ACLFILE=${SANDBOX}/public.txt

mkdir -p "${SANDBOX}" "${USER_HOME}" "${USER_B_HOME}"
mkdir -p /root/rhcsa_journal/lab-50c/task1
mkdir -p /root/rhcsa_journal/lab-50c/task2

getent group "${GROUP}" >/dev/null || groupadd "${GROUP}"
getent passwd "${USER}" >/dev/null || useradd -d "${USER_HOME}" -M -s /bin/bash -g "${GROUP}" "${USER}"
getent passwd "${USER_B}" >/dev/null || useradd -d "${USER_B_HOME}" -M -s /bin/bash -g "${GROUP}" "${USER_B}"

sudo -u "${USER}" bash -c 'echo "lab50c verify artifact" > '"${ACLFILE}"
chmod 0644 "${ACLFILE}"
setfacl -m u:"${USER_B}":--- "${ACLFILE}"
```

> **STOP — confirm setup produced `public.txt` with mode `0644` and ACL entry `u:${USER_B}:---`.**

---

## Task 1 — Audit ACL entries and effective behavior

### Purpose

Prove, with evidence, that explicit zero ACL entry denies one named user while owner still reads normally.

### Main command block

```bash
TASKLOG=/tmp/lab50c/task1.txt

echo "═══ ACL entry audit ═══"                              | tee "${TASKLOG}"
stat -c '%U:%G %a %n' "${ACLFILE}"                         | tee -a "${TASKLOG}"
getfacl "${ACLFILE}"                                       | tee -a "${TASKLOG}"

echo "═══ owner can read ═══"                              | tee -a "${TASKLOG}"
sudo -u "${USER}" cat "${ACLFILE}"                         | tee -a "${TASKLOG}"

echo "═══ denied user should fail ═══"                     | tee -a "${TASKLOG}"
sudo -u "${USER_B}" cat "${ACLFILE}" 2>&1                  | tee -a "${TASKLOG}"
echo "exit was: $?"                                        | tee -a "${TASKLOG}"
```

### Expected signal

- `getfacl` includes `user:labuser_50_aclden_b:---`
- owner read succeeds
- denied user read fails

---

## Task 2 — Destroy-restore ACL drill (`setfacl -b` then re-apply)

### Purpose

Practice T41 for ACLs: remove ACL state, verify changed behavior, then restore desired state and verify behavior returns.

### Main command block

```bash
TASKLOG=/tmp/lab50c/task2.txt

echo "═══ destroy phase: clear ACLs ═══"                    | tee "${TASKLOG}"
setfacl -b "${ACLFILE}"
getfacl "${ACLFILE}"                                        | tee -a "${TASKLOG}"

echo "after setfacl -b, USER_B should fall through to 0644 other::r--" | tee -a "${TASKLOG}"
sudo -u "${USER_B}" cat "${ACLFILE}"                        | tee -a "${TASKLOG}"

echo "═══ restore phase: re-apply explicit zero deny ═══"   | tee -a "${TASKLOG}"
setfacl -m u:"${USER_B}":0 "${ACLFILE}"
getfacl "${ACLFILE}"                                        | tee -a "${TASKLOG}"
sudo -u "${USER_B}" cat "${ACLFILE}" 2>&1                   | tee -a "${TASKLOG}"
echo "exit was: $?"                                         | tee -a "${TASKLOG}"
```

### Contrast card

- `setfacl -b FILE` removes extended ACL entries; behavior falls back to base bits.
- `setfacl -m u:USER_B:0 FILE` reintroduces explicit zero entry and denial returns.
- `:---` and `:0` are equivalent intent for this lab's deny-by-explicit-zero pattern.
- Group trap variant (T50-B): `g:GROUP:---` explicitly blocks that group path; removing that group entry restores fallback behavior.

---

## Lab Closeout — Bulletproof Teardown (Section 6)

```bash
set +e

awk -v s="${SANDBOX}" '$2 ~ s {print $2}' /proc/mounts | tac | xargs -r -n1 umount -l 2>/dev/null

if getent passwd "${USER}" >/dev/null 2>&1; then userdel -r "${USER}" 2>/dev/null; fi
if getent passwd "${USER_B}" >/dev/null 2>&1; then userdel -r "${USER_B}" 2>/dev/null; fi
if getent group "${GROUP}" >/dev/null 2>&1; then groupdel "${GROUP}" 2>/dev/null; fi

rm -rf "${SANDBOX}"

echo "── Lab 50c cleanup audit ──"
getent passwd "${USER}"   >/dev/null && echo "❌ ${USER} remains"   || echo "✅ ${USER} gone"
getent passwd "${USER_B}" >/dev/null && echo "❌ ${USER_B} remains" || echo "✅ ${USER_B} gone"
getent group  "${GROUP}"  >/dev/null && echo "❌ ${GROUP} remains"  || echo "✅ ${GROUP} gone"
test -d "${SANDBOX}"                    && echo "❌ sandbox remains" || echo "✅ sandbox gone"

set -e
```

> **STOP — paste the four cleanup audit lines before declaring the 50 trilogy complete.**

---

## Lab 50c Checklist (2 tasks + closeout)

- [ ] Task 1 audited ACL entry + effective access outcomes
- [ ] Task 2 completed destroy-restore drill (`-b` then re-apply zero ACL)
- [ ] T50-A and T50-B were verbalized during verification
- [ ] Closeout removed both users, group, and sandbox with audit proof

---

## Related Labs

| Lab | Connection |
|---|---|
| **Lab 50a** — CLI deny pattern | Initial manual implementation |
| **Lab 50b** — Ansible deny pattern | Declarative implementation with `ansible.posix.acl` |

---

## Author

**Kelvin R. Tobias**  
[kelvinintech.com](https://kelvinintech.com) · [GitHub](https://github.com/kelvintechnical) · [LinkedIn](https://www.linkedin.com/in/kelvin-r-tobias-211949219)
