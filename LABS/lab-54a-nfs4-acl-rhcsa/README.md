# Lab 54a: NFSv4 ACL Basics (RHCSA) — `nfs4_getfacl`, `nfs4_setfacl`

- **Series:** linux-ops-mastery — ACLs and Permissions
- **Trilogy:** **`54a` (RHCSA — you are here)** → [`54b`](../lab-54b-nfs4-acl-ansible/) (Ansible boundary) → [`54c`](../lab-54c-nfs4-acl-verify/) (Verify capstone)
- **Time Estimate:** 25–35 minutes
- **Tasks:** 2 (Task 1 = install + inspect tools, Task 2 = `nfs4_setfacl` syntax walkthrough with graceful fallback)
- **Practice Directory (rotation #54):** `/mnt`
- **Sandbox (Tier B):** `/tmp/lab54a` with `USER=labuser_54_nfs4`, `GROUP=labgrp_54_nfs4`, `USER_HOME=/tmp/lab54a/home_labuser_54_nfs4`
- **Traps rehearsed this lab:** **T54-A** (NFSv4 ACL tools require package + NFSv4 filesystem; local ext4/xfs targets will fail) · **T54-B** (NFSv4 inheritance flags `d/f/i` are not POSIX default ACL behavior) · **T41** (destroy-restore drill reserved for verify) · **T44** (closeout audit must show complete cleanup)

> **Critical reality for this lab:** many local VMs do not expose an actual NFSv4 mount. This lab still delivers value by proving tool install, documenting command syntax, capturing help/man evidence, and handling no-mount situations cleanly.

---

## LAB HEADER BLOCK

```bash
echo "🖥️  ENV:   ${ENV:-DECLARE_ME}"
echo "📦  OS:    $(cat /etc/redhat-release 2>/dev/null || grep PRETTY_NAME /etc/os-release)"
echo "🕒  TIME:  $(date -Is)"
echo "👤  USER:  $(whoami)@$(hostname)"
echo "⚠️  TRAP REMINDERS THIS LAB: T54-A T54-B T41 T44"
echo "📁  PRACTICE DIR: /mnt"
echo ""
echo "Potential NFS mounts:"
findmnt -t nfs,nfs4 2>/dev/null || true
mount | grep -E ' type nfs| type nfs4' || true
echo "Shell version: $BASH_VERSION"
```

> **STOP — paste header output before setup.**

---

## Objective

Build exam-ready reflexes for NFSv4 ACL tooling without pretending local filesystems support it:

1. Install and verify `nfs4-acl-tools` (`nfs4_getfacl`, `nfs4_setfacl` binaries).
2. Capture authoritative command help into journal evidence.
3. Practice NFSv4 ACL entry grammar (`A` Allow, `D` Deny) and inheritance flags (`d`, `f`, `i`).
4. Execute against a hypothetical `/mnt/nfs/...` target with a fallback path that records why a real ACL mutation cannot be validated locally.

---

## Quick Concept Card

| Concept | Meaning |
|---|---|
| `nfs4_getfacl PATH` | Read NFSv4 ACL from file/dir (works only on NFSv4 object) |
| `nfs4_setfacl -a ACE PATH` | Add an ACE entry |
| `nfs4_setfacl -x ACE PATH` | Remove matching ACE entry |
| ACE type `A` | Allow |
| ACE type `D` | Deny |
| Flags `d/f/i` | dir-inherit / file-inherit / inherit-only |
| **🪤 T54-A** | Local ext4/xfs target is not NFSv4 ACL-capable for these tools |
| **🪤 T54-B** | NFSv4 inheritance is ACE-flag driven, unlike POSIX default ACL model |

---

## Lab-Wide Setup (Tier B Sandbox)

```bash
sudo -i

export LAB_NUM=54
export LAB_SLUG=nfs4
export SANDBOX=/tmp/lab54a
export GROUP=labgrp_${LAB_NUM}_${LAB_SLUG}
export USER=labuser_${LAB_NUM}_${LAB_SLUG}
export USER_HOME=${SANDBOX}/home_${USER}

mkdir -p "${SANDBOX}" "${USER_HOME}"
mkdir -p /root/rhcsa_journal/lab-54a/task1
mkdir -p /root/rhcsa_journal/lab-54a/task2

getent group  "${GROUP}" >/dev/null || groupadd "${GROUP}"
getent passwd "${USER}"  >/dev/null || useradd -d "${USER_HOME}" -M -s /bin/bash -g "${GROUP}" "${USER}"
chown -R "${USER}:${GROUP}" "${SANDBOX}"

id "${USER}"
ls -ld "${SANDBOX}" "${USER_HOME}"
```

---

## Task 1 — Install tools and capture proof

**Practice directory this task:** `/mnt` (operational context) and `/tmp/lab54a` (safe artifacts + logs)

### Main command block

```bash
TASKLOG=/tmp/lab54a/task1.txt

dnf install -y nfs4-acl-tools                              2>&1 | tee "${TASKLOG}"
nfs4_getfacl --help                                         2>&1 | tee /tmp/lab54a/nfs4_getfacl-help.txt
rpm -ql nfs4-acl-tools                                      2>&1 | tee /tmp/lab54a/nfs4-acl-tools-files.txt

# Optional: confirm command paths
command -v nfs4_getfacl                                     2>&1 | tee -a "${TASKLOG}"
command -v nfs4_setfacl                                     2>&1 | tee -a "${TASKLOG}"

echo "exit was: $?"
```

### Expected outcome

- Package installs successfully.
- `nfs4_getfacl --help` prints syntax and options.
- `rpm -ql nfs4-acl-tools` lists binaries/docs owned by the package.

### Journal write

```bash
JDIR=/root/rhcsa_journal/lab-54a/task1
mkdir -p "${JDIR}"
cp /tmp/lab54a/task1.txt               "${JDIR}/evidence.txt"
cp /tmp/lab54a/nfs4_getfacl-help.txt   "${JDIR}/nfs4_getfacl-help.txt"
cp /tmp/lab54a/nfs4-acl-tools-files.txt "${JDIR}/package-filelist.txt"
```

---

## Task 2 — `nfs4_setfacl` syntax walkthrough and graceful fallback

**Practice directory this task:** `/mnt` (hypothetical NFSv4 target path)

### Main command block

```bash
TASKLOG=/tmp/lab54a/task2.txt
TARGET=/mnt/nfs/lab54-demo.txt
FALLBACK=/tmp/lab54a/fake-target.txt
mkdir -p /mnt /tmp/lab54a
touch "${FALLBACK}"

echo "=== nfs4_setfacl syntax drill ==="                   | tee "${TASKLOG}"
echo "Allow entry example: A::${USER}@::rwatTnNcCy"        | tee -a "${TASKLOG}"
echo "Deny entry example:  D::EVERYONE@:w"                 | tee -a "${TASKLOG}"
echo "Inheritance flags: d=dir-inherit f=file-inherit i=inherit-only" | tee -a "${TASKLOG}"
echo "Directory inherit ACE example:"                      | tee -a "${TASKLOG}"
echo "A:fd:${USER}@::rxtncy"                               | tee -a "${TASKLOG}"
echo "Inherit-only deny example:"                          | tee -a "${TASKLOG}"
echo "D:fi:${USER}@::w"                                    | tee -a "${TASKLOG}"

if findmnt -n -o FSTYPE /mnt 2>/dev/null | grep -q '^nfs4$'; then
  echo "Detected nfs4 mount at /mnt; running live examples."           | tee -a "${TASKLOG}"
  touch "${TARGET}"
  nfs4_getfacl "${TARGET}"                                   2>&1 | tee -a "${TASKLOG}" || true
  nfs4_setfacl -a "A::${USER}@::rxtncy" "${TARGET}"          2>&1 | tee -a "${TASKLOG}" || true
  nfs4_getfacl "${TARGET}"                                   2>&1 | tee -a "${TASKLOG}" || true
else
  echo "T54-A path: /mnt is not nfs4 on this host; capturing help/doc fallback." | tee -a "${TASKLOG}"
  nfs4_setfacl --help                                        2>&1 | tee /tmp/lab54a/nfs4_setfacl-help.txt
  nfs4_getfacl --help                                        2>&1 | tee -a "${TASKLOG}"
  echo "Tried fake file ${FALLBACK}; expected incompatibility on non-NFSv4 filesystems." | tee -a "${TASKLOG}"
  nfs4_getfacl "${FALLBACK}"                                 2>&1 | tee -a "${TASKLOG}" || true
fi

echo "exit was: $?"
```

### Journal write

```bash
JDIR=/root/rhcsa_journal/lab-54a/task2
mkdir -p "${JDIR}"
cp /tmp/lab54a/task2.txt "${JDIR}/evidence.txt"
test -f /tmp/lab54a/nfs4_setfacl-help.txt && cp /tmp/lab54a/nfs4_setfacl-help.txt "${JDIR}/nfs4_setfacl-help.txt"
```

---

## Lab Closeout — Section 6 Teardown

```bash
set +e

userdel -r "${USER}" 2>/dev/null
groupdel "${GROUP}" 2>/dev/null
rm -rf "${SANDBOX}"

echo "── Lab 54a cleanup audit ──"
getent passwd "${USER}" >/dev/null && echo "❌ user remains" || echo "✅ user gone"
getent group  "${GROUP}" >/dev/null && echo "❌ group remains" || echo "✅ group gone"
test -d "${SANDBOX}" && echo "❌ sandbox remains" || echo "✅ sandbox gone"
test -d "${USER_HOME}" && echo "❌ home remains" || echo "✅ home gone"

set -e
```

---

## Checklist

- [ ] Task 1 completed: `dnf install -y nfs4-acl-tools`, help captured, package file list captured
- [ ] Task 2 completed: syntax walkthrough logged, live run only if `/mnt` is `nfs4`, otherwise fallback evidence captured
- [ ] T54-A and T54-B explicitly recorded in notes
- [ ] Section 6 closeout completed with four audit lines

---

## Author

**Kelvin R. Tobias**  
[kelvinintech.com](https://kelvinintech.com) · [GitHub](https://github.com/kelvintechnical) · [LinkedIn](https://www.linkedin.com/in/kelvin-r-tobias-211949219)
