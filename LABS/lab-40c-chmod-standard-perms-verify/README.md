# Lab 40c: Standard File Permissions (Verify) - audit modes + destroy/restore

- **Series:** linux-ops-mastery - Identity, Permissions, and Access
- **Trilogy:** [`40a`](../lab-40a-chmod-standard-perms-rhcsa/) (RHCSA) -> [`40b`](../lab-40b-chmod-standard-perms-ansible/) (Ansible) -> `40c` (Verify)
- **Time Estimate:** 25-35 minutes
- **Tasks:** 2 (Task 1 = permission audit against expected journal, Task 2 = destroy-restore drill)
- **Practice Directory (rotation #40):** `/usr`
- **Sandbox (Tier B):** `/tmp/lab40c` with `USER=labuser_40_chmod`, `GROUP=labgrp_40_chmod`, `USER_HOME=/tmp/lab40c/home_labuser_40_chmod`
- **Traps rehearsed this lab:** **T40-A** ; **T40-B** ; **T41** (do not skip restore drill) ; **T44** (no residue after teardown)

> **This lab's practice directory is: `/usr`**. Verification and drills are performed in `/tmp/lab40c` and journaled under `/root/rhcsa_journal/lab-40c/`.

---

## LAB HEADER BLOCK

```bash
echo "📦 OS: $(cat /etc/redhat-release 2>/dev/null || grep PRETTY_NAME /etc/os-release)"
echo "🕒 TIME: $(date -Is)"
echo "👤 USER: $(whoami)@$(hostname)"
echo "📁 PRACTICE DIR: /usr"
echo "⚠️ TRAPS: T40-A T40-B T41 T44"
umask
```

---

## Objective

Act as the verifier:

1. Audit permission mode bits and compare with expected values from a manifest.
2. Validate using both `ls -l` and `stat -c %a`.
3. Prove recovery skill by destroying and restoring test assets from journaled expectations.

---

## Lab-Wide Setup - Tier B Sandbox + restore manifest

```bash
sudo -i

export LAB_NUM=40
export LAB_SLUG=chmod
export SANDBOX=/tmp/lab40c
export GROUP=labgrp_${LAB_NUM}_${LAB_SLUG}
export USER=labuser_${LAB_NUM}_${LAB_SLUG}
export USER_HOME=${SANDBOX}/home_${USER}

mkdir -p "${SANDBOX}" "${USER_HOME}" /root/rhcsa_journal/lab-40c/{task1,task2,restore-plan}

getent group  "${GROUP}" >/dev/null || groupadd "${GROUP}"
getent passwd "${USER}"  >/dev/null || useradd -d "${USER_HOME}" -M -s /bin/bash -g "${GROUP}" "${USER}"
chown -R "${USER}:${GROUP}" "${SANDBOX}"

mkdir -p /tmp/lab40c/bin /tmp/lab40c/docs /tmp/lab40c/priv
touch /tmp/lab40c/bin/run.sh /tmp/lab40c/docs/readme.txt /tmp/lab40c/priv/secret.txt
chmod 755 /tmp/lab40c/bin/run.sh
chmod 644 /tmp/lab40c/docs/readme.txt
chmod 600 /tmp/lab40c/priv/secret.txt

cat > /root/rhcsa_journal/lab-40c/restore-plan/expected-modes.tsv <<'EOF'
755 /tmp/lab40c/bin/run.sh
644 /tmp/lab40c/docs/readme.txt
600 /tmp/lab40c/priv/secret.txt
700 /tmp/lab40c/priv
EOF
```

---

## Task 1 - Audit mode bits against expected journal manifest

### Purpose

Validate current permissions against expected values in a machine-checkable way.

### Main command block

```bash
set -o pipefail
TASKLOG=/root/rhcsa_journal/lab-40c/task1/audit.txt

echo "== manifest audit ==" | tee "${TASKLOG}"
while read -r expected path; do
  actual=$(stat -c '%a' "${path}")
  printf "expected=%s actual=%s path=%s\n" "${expected}" "${actual}" "${path}" | tee -a "${TASKLOG}"
  if [ "${actual}" = "${expected}" ]; then
    echo "PASS ${path}" | tee -a "${TASKLOG}"
  else
    echo "FAIL ${path}" | tee -a "${TASKLOG}"
  fi
done < /root/rhcsa_journal/lab-40c/restore-plan/expected-modes.tsv

ls -ld /tmp/lab40c/priv | tee -a "${TASKLOG}"
ls -l /tmp/lab40c/bin/run.sh /tmp/lab40c/docs/readme.txt /tmp/lab40c/priv/secret.txt | tee -a "${TASKLOG}"

echo "exit was: $?"
```

---

## Task 2 - Destroy-restore drill (T41 gate)

### Purpose

Practice incident-style recovery: remove files/directories, rebuild, and re-audit against the manifest.

### Main command block

```bash
set -o pipefail
TASKLOG=/root/rhcsa_journal/lab-40c/task2/drill.txt

echo "== destroy phase ==" | tee "${TASKLOG}"
rm -f /tmp/lab40c/bin/run.sh /tmp/lab40c/docs/readme.txt /tmp/lab40c/priv/secret.txt
rmdir /tmp/lab40c/priv 2>/dev/null || true
find /tmp/lab40c -maxdepth 2 -type f -o -type d | sort | tee -a "${TASKLOG}"

echo "== restore phase ==" | tee -a "${TASKLOG}"
mkdir -p /tmp/lab40c/bin /tmp/lab40c/docs /tmp/lab40c/priv
touch /tmp/lab40c/bin/run.sh /tmp/lab40c/docs/readme.txt /tmp/lab40c/priv/secret.txt
chmod 755 /tmp/lab40c/bin/run.sh
chmod 644 /tmp/lab40c/docs/readme.txt
chmod 600 /tmp/lab40c/priv/secret.txt
chmod 700 /tmp/lab40c/priv

echo "== re-audit ==" | tee -a "${TASKLOG}"
while read -r expected path; do
  actual=$(stat -c '%a' "${path}")
  printf "expected=%s actual=%s path=%s\n" "${expected}" "${actual}" "${path}" | tee -a "${TASKLOG}"
done < /root/rhcsa_journal/lab-40c/restore-plan/expected-modes.tsv

echo "exit was: $?"
```

> **T40-B reminder:** recursive mode changes must stay scoped (`/tmp/lab40c/...`), never `/` or `/usr`.

---

## Lab Closeout - Section 6 Bulletproof Teardown

```bash
set +e

if getent passwd "${USER}" >/dev/null 2>&1; then userdel -r "${USER}" 2>/dev/null; fi
if getent group  "${GROUP}" >/dev/null 2>&1; then groupdel "${GROUP}"  2>/dev/null; fi
rm -rf "${SANDBOX}"

echo "── Lab 40c cleanup audit ──"
getent passwd "${USER}" >/dev/null && echo "❌ user remains"    || echo "✅ user gone"
getent group  "${GROUP}" >/dev/null && echo "❌ group remains"   || echo "✅ group gone"
test -d "${SANDBOX}"               && echo "❌ sandbox remains" || echo "✅ sandbox gone"
test -d "${USER_HOME}"             && echo "❌ home remains"    || echo "✅ home gone"

set -e
```

---

## Lab 40c Checklist

- [ ] Task 1 audited mode bits from journal manifest (`expected-modes.tsv`)
- [ ] Used both `stat -c %a` and `ls -l` as proof outputs
- [ ] Task 2 completed full destroy-restore drill (T41)
- [ ] Re-audit after restore matched expected mode bits
- [ ] Section 6 closeout produced four `✅` lines (T44)

---

## Author

**Kelvin R. Tobias**  
[kelvinintech.com](https://kelvinintech.com) · [GitHub](https://github.com/kelvintechnical) · [LinkedIn](https://www.linkedin.com/in/kelvin-r-tobias-211949219)
