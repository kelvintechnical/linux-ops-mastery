# Lab 54c: Verifying NFSv4 ACL Workflow (Capstone) — Audit + Destroy/Restore

- **Series:** linux-ops-mastery — ACLs and Permissions
- **Trilogy:** [`54a`](../lab-54a-nfs4-acl-rhcsa/) (RHCSA) → [`54b`](../lab-54b-nfs4-acl-ansible/) (Ansible boundary) → **`54c` (Verify — you are here)**
- **Time Estimate:** 25–35 minutes
- **Tasks:** 2 (Task 1 = audit install + help evidence, Task 2 = destroy-restore drill)
- **Practice Directory (rotation #54):** `/mnt`
- **Sandbox (Tier B):** `/tmp/lab54c` with `USER=labuser_54_nfs4`, `GROUP=labgrp_54_nfs4`, `USER_HOME=/tmp/lab54c/home_labuser_54_nfs4`
- **Traps rehearsed this lab:** **T54-A** (tools + NFSv4 target required), **T54-B** (NFSv4 inheritance flags differ from POSIX ACL defaults), **T41** (destroy-restore drill), **T44** (cleanup audit completeness)

> **Verification scope:** this capstone validates tooling, syntax evidence, and recovery workflow even when no real NFSv4 mount exists locally.

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
echo "54a/54b journal paths:"
ls -la /root/rhcsa_journal/lab-54a /root/rhcsa_journal/lab-54b 2>/dev/null || true
findmnt -t nfs,nfs4 2>/dev/null || true
```

---

## Objective

1. Audit that `nfs4-acl-tools` is installed and both help outputs were captured in prior labs.
2. Re-collect command help evidence into 54c logs as independent proof.
3. Run the destroy-restore drill (T41): remove working artifacts, restore from journal, and prove recovered state.
4. Keep T54-A/T54-B explicit in notes so no one confuses syntax rehearsal with validated ACL mutation on non-NFSv4 filesystems.

---

## Lab-Wide Setup (Tier B Sandbox)

```bash
sudo -i

export LAB_NUM=54
export LAB_SLUG=nfs4
export SANDBOX=/tmp/lab54c
export GROUP=labgrp_${LAB_NUM}_${LAB_SLUG}
export USER=labuser_${LAB_NUM}_${LAB_SLUG}
export USER_HOME=${SANDBOX}/home_${USER}

mkdir -p "${SANDBOX}" "${USER_HOME}"
mkdir -p /root/rhcsa_journal/lab-54c/task1
mkdir -p /root/rhcsa_journal/lab-54c/task2

getent group  "${GROUP}" >/dev/null || groupadd "${GROUP}"
getent passwd "${USER}"  >/dev/null || useradd -d "${USER_HOME}" -M -s /bin/bash -g "${GROUP}" "${USER}"
chown -R "${USER}:${GROUP}" "${SANDBOX}"
```

---

## Task 1 — Audit tool install and help evidence

### Main command block

```bash
TASKLOG=/tmp/lab54c/task1.txt

echo "=== 54c Task 1: install/help audit ==="                    | tee "${TASKLOG}"
rpm -q nfs4-acl-tools                                           | tee -a "${TASKLOG}"
nfs4_getfacl --help                                             2>&1 | tee /tmp/lab54c/nfs4_getfacl-help.txt
nfs4_setfacl --help                                             2>&1 | tee /tmp/lab54c/nfs4_setfacl-help.txt

echo "--- prior journal checks ---"                             | tee -a "${TASKLOG}"
for f in \
  /root/rhcsa_journal/lab-54a/task1/nfs4_getfacl-help.txt \
  /root/rhcsa_journal/lab-54a/task2/evidence.txt \
  /root/rhcsa_journal/lab-54b/task1/nfs4_setfacl-help.txt \
  /root/rhcsa_journal/lab-54b/task2/evidence.txt
do
  if test -s "$f"; then
    echo "✅ present: $f"                                        | tee -a "${TASKLOG}"
  else
    echo "❌ missing/empty: $f"                                  | tee -a "${TASKLOG}"
  fi
done

echo "T54-A reminder: successful nfs4_setfacl write requires actual NFSv4 target." | tee -a "${TASKLOG}"
echo "T54-B reminder: inheritance relies on ACE flags d/f/i (not POSIX default ACL)." | tee -a "${TASKLOG}"
echo "exit was: $?"
```

### Journal write

```bash
JDIR=/root/rhcsa_journal/lab-54c/task1
mkdir -p "${JDIR}"
cp /tmp/lab54c/task1.txt "${JDIR}/evidence.txt"
cp /tmp/lab54c/nfs4_getfacl-help.txt "${JDIR}/nfs4_getfacl-help.txt"
cp /tmp/lab54c/nfs4_setfacl-help.txt "${JDIR}/nfs4_setfacl-help.txt"
```

---

## Task 2 — Destroy-Restore drill (T41)

### Main command block

```bash
TASKLOG=/tmp/lab54c/task2.txt
WORKDIR=/tmp/lab54c/recovery-demo
JDIR=/root/rhcsa_journal/lab-54c/task1
mkdir -p "${WORKDIR}"

echo "=== pre-destroy seed ==="                                  | tee "${TASKLOG}"
cp "${JDIR}/nfs4_getfacl-help.txt" "${WORKDIR}/seed-getfacl.txt"
cp "${JDIR}/nfs4_setfacl-help.txt" "${WORKDIR}/seed-setfacl.txt"
ls -la "${WORKDIR}"                                              | tee -a "${TASKLOG}"

echo "=== destroy ==="                                           | tee -a "${TASKLOG}"
rm -rf "${WORKDIR}"
test -d "${WORKDIR}" && echo "❌ destroy failed" || echo "✅ destroyed" | tee -a "${TASKLOG}"

echo "=== restore ==="                                           | tee -a "${TASKLOG}"
mkdir -p "${WORKDIR}"
cp "${JDIR}/nfs4_getfacl-help.txt" "${WORKDIR}/restored-getfacl.txt"
cp "${JDIR}/nfs4_setfacl-help.txt" "${WORKDIR}/restored-setfacl.txt"
ls -la "${WORKDIR}"                                              | tee -a "${TASKLOG}"
sha256sum "${WORKDIR}/restored-getfacl.txt" "${WORKDIR}/restored-setfacl.txt" | tee -a "${TASKLOG}"

echo "T41 complete: artifacts were destroyed and restored from journal." | tee -a "${TASKLOG}"
echo "exit was: $?"
```

### Journal write

```bash
JDIR2=/root/rhcsa_journal/lab-54c/task2
mkdir -p "${JDIR2}"
cp /tmp/lab54c/task2.txt "${JDIR2}/evidence.txt"
```

---

## Lab Closeout — Section 6 Teardown

```bash
set +e
userdel -r "${USER}" 2>/dev/null
groupdel "${GROUP}" 2>/dev/null
rm -rf "${SANDBOX}"

echo "── Lab 54c cleanup audit ──"
getent passwd "${USER}" >/dev/null && echo "❌ user remains" || echo "✅ user gone"
getent group  "${GROUP}" >/dev/null && echo "❌ group remains" || echo "✅ group gone"
test -d "${SANDBOX}" && echo "❌ sandbox remains" || echo "✅ sandbox gone"
test -d "${USER_HOME}" && echo "❌ home remains" || echo "✅ home gone"
set -e
```

---

## Checklist

- [ ] Task 1 audited package install and captured fresh `--help` evidence
- [ ] Task 1 confirmed expected 54a/54b journal artifacts exist
- [ ] Task 2 completed T41 destroy-restore drill and checksum proof
- [ ] T54-A and T54-B notes captured in verification evidence
- [ ] Section 6 closeout audit passed with four status lines

---

## Author

**Kelvin R. Tobias**  
[kelvinintech.com](https://kelvinintech.com) · [GitHub](https://github.com/kelvintechnical) · [LinkedIn](https://www.linkedin.com/in/kelvin-r-tobias-211949219)
