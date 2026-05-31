# Lab 58c: Verifying firewalld Service Adds - audit + destroy/restore

- **Series:** linux-ops-mastery - Security Administration (firewalld)
- **Trilogy:** `58a` (RHCSA) -> `58b` (Ansible) -> `58c` (Verify - you are here)
- **Time Estimate:** 25-35 minutes
- **Tasks:** 2 (Task 1 = audit, Task 2 = destroy-restore drill)
- **Practice Directory (rotation slot 58):** `/lib`
- **Sandbox (Tier B):** `/tmp/lab58c` with `USER=labuser_58_fwsvc`, `GROUP=labgrp_58_fwsvc`
- **Traps rehearsed this lab:** **T58-A** · **T58-B** · **T41** · **T44**

> **Verification scope:** prove service state from command output and journal artifacts, then rehearse remove/restore safely.

---

## LAB HEADER BLOCK

```bash
echo "🖥️  ENV:   ${ENV:-DECLARE_ME}"
echo "🕒  TIME:  $(date -Is)"
echo "👤  USER:  $(whoami)@$(hostname)"
echo "📁  PRACTICE DIR: /lib"
echo "⚠️  TRAP REMINDERS THIS LAB: T58-A T58-B T41 T44"
command -v firewall-cmd
systemctl is-active firewalld
ls /usr/lib/firewalld/services | head -n 10
```

---

## Objective

1. Audit runtime/permanent service state and preserve evidence in journal.
2. Execute destroy-restore drill: remove `http`, reload, then restore original service list exactly.

---

## Lab-Wide Setup - Tier B Sandbox

```bash
sudo -i

export SANDBOX=/tmp/lab58c
export GROUP=labgrp_58_fwsvc
export USER=labuser_58_fwsvc
export USER_HOME=${SANDBOX}/home_${USER}
export ZONE=public

mkdir -p "${SANDBOX}" "${USER_HOME}" /root/rhcsa_journal/lab-58c/task1 /root/rhcsa_journal/lab-58c/task2
getent group "${GROUP}" >/dev/null || groupadd "${GROUP}"
getent passwd "${USER}" >/dev/null || useradd -d "${USER_HOME}" -M -s /bin/bash -g "${GROUP}" "${USER}"
chown -R "${USER}:${GROUP}" "${SANDBOX}"

sudo firewall-cmd --zone="${ZONE}" --list-services | xargs > "${SANDBOX}/original-services.txt"
cat "${SANDBOX}/original-services.txt"
```

---

## Task 1 - Audit service state in journal evidence

### Purpose

Collect auditor-grade snapshots of active service lists and service definition files.

### Main command block

```bash
TASKLOG=/tmp/lab58c/task1.txt

echo "═══ firewalld audit snapshot ═══"                            | tee "${TASKLOG}"
echo "zone=${ZONE}"                                               | tee -a "${TASKLOG}"
echo "runtime services:"                                          | tee -a "${TASKLOG}"
sudo firewall-cmd --zone="${ZONE}" --list-services               | tee -a "${TASKLOG}"
echo "permanent services:"                                        | tee -a "${TASKLOG}"
sudo firewall-cmd --permanent --zone="${ZONE}" --list-services   | tee -a "${TASKLOG}"
echo "http service definition file:"                              | tee -a "${TASKLOG}"
ls -l /usr/lib/firewalld/services/http.xml 2>&1                  | tee -a "${TASKLOG}"
echo "active zones:"                                              | tee -a "${TASKLOG}"
sudo firewall-cmd --get-active-zones                             | tee -a "${TASKLOG}"
echo "exit was: $?"                                               | tee -a "${TASKLOG}"
```

### Journal write

```bash
cp /tmp/lab58c/task1.txt /root/rhcsa_journal/lab-58c/task1/audit.txt
```

---

## Task 2 - Destroy-restore drill (remove `http`, restore original list)

### Purpose

Rehearse safe rollback and recovery so firewall service state is deterministic after remediation.

### Main command block

```bash
TASKLOG=/tmp/lab58c/task2.txt

echo "═══ DESTROY phase: remove http ═══"                          | tee "${TASKLOG}"
sudo firewall-cmd --permanent --zone="${ZONE}" --remove-service=http 2>&1 | tee -a "${TASKLOG}" || true
sudo firewall-cmd --zone="${ZONE}" --remove-service=http 2>&1      | tee -a "${TASKLOG}" || true
sudo firewall-cmd --reload                                          | tee -a "${TASKLOG}"
echo "services after destroy:"                                      | tee -a "${TASKLOG}"
sudo firewall-cmd --zone="${ZONE}" --list-services                  | tee -a "${TASKLOG}"

echo "═══ RESTORE phase: restore original services exactly ═══"     | tee -a "${TASKLOG}"
ORIG="$(cat "${SANDBOX}/original-services.txt")"
CURR="$(sudo firewall-cmd --permanent --zone="${ZONE}" --list-services)"

for svc in ${CURR}; do
  sudo firewall-cmd --permanent --zone="${ZONE}" --remove-service="${svc}" >/dev/null 2>&1 || true
done
for svc in ${ORIG}; do
  sudo firewall-cmd --permanent --zone="${ZONE}" --add-service="${svc}" >/dev/null 2>&1 || true
done
sudo firewall-cmd --reload | tee -a "${TASKLOG}"

echo "services after restore:"                                      | tee -a "${TASKLOG}"
sudo firewall-cmd --zone="${ZONE}" --list-services                  | tee -a "${TASKLOG}"
echo "original services baseline:"                                  | tee -a "${TASKLOG}"
cat "${SANDBOX}/original-services.txt"                              | tee -a "${TASKLOG}"
echo "exit was: $?"                                                 | tee -a "${TASKLOG}"
```

### Trap callout

- **T58-A:** runtime-only additions disappear on reload.
- **T58-B:** only permanent config survives reload; pair permanent edits with reload and verify.
- **T41:** verify labs must include destroy and restore, not inspection only.

### Journal write

```bash
cp /tmp/lab58c/task2.txt /root/rhcsa_journal/lab-58c/task2/destroy-restore.txt
```

---

## Lab Closeout - Bulletproof Teardown (Section 6 restore check required)

```bash
set +e

# Enforce final restore to original services before teardown.
ORIG="$(cat "${SANDBOX}/original-services.txt" 2>/dev/null)"
CURR="$(sudo firewall-cmd --permanent --zone="${ZONE}" --list-services 2>/dev/null)"
for svc in ${CURR}; do
  sudo firewall-cmd --permanent --zone="${ZONE}" --remove-service="${svc}" >/dev/null 2>&1 || true
done
for svc in ${ORIG}; do
  sudo firewall-cmd --permanent --zone="${ZONE}" --add-service="${svc}" >/dev/null 2>&1 || true
done
sudo firewall-cmd --reload >/dev/null 2>&1 || true

if getent passwd "${USER}" >/dev/null 2>&1; then
  userdel -r "${USER}" 2>/dev/null
fi
if getent group "${GROUP}" >/dev/null 2>&1; then
  groupdel "${GROUP}" 2>/dev/null
fi

rm -rf "${SANDBOX}"

echo "── Lab 58c cleanup audit ──"
getent passwd "${USER}" >/dev/null && echo "❌ user remains" || echo "✅ user gone"
getent group "${GROUP}" >/dev/null && echo "❌ group remains" || echo "✅ group gone"
test -d "${SANDBOX}" && echo "❌ sandbox remains" || echo "✅ sandbox gone"
test -e /tmp/lab58c/original-services.txt && echo "❌ baseline file remains" || echo "✅ baseline file gone"
echo "firewalld ${ZONE} services after final restore:"
sudo firewall-cmd --zone="${ZONE}" --list-services

set -e
```

---

## Author

**Kelvin R. Tobias**
[kelvinintech.com](https://kelvinintech.com) · [GitHub](https://github.com/kelvintechnical) · [LinkedIn](https://www.linkedin.com/in/kelvin-r-tobias-211949219)
