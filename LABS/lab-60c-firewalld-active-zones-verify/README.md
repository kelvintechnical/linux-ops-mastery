# Lab 60c: Verify Active Firewall Zones — audit + destroy/restore drill

- **Series:** linux-ops-mastery — Network Security and Service Access
- **Trilogy:** [`60a`](../lab-60a-firewalld-active-zones-rhcsa/) (RHCSA) -> [`60b`](../lab-60b-firewalld-active-zones-ansible/) (Ansible) -> `60c` (Verify)
- **Topic:** Verifier workflow for active zones, default-zone alignment, and runtime/permanent audit evidence
- **Distinct from Lab 56:** This verify lab checks active-zone/interface truth and runtime/permanent deltas, not generic zone listing coverage.
- **Time Estimate:** 25-35 minutes
- **Tasks:** 2 (Task 1 audit, Task 2 destroy-restore drill)
- **Practice Directory:** `/usr` (inspection context)
- **Sandbox (Tier B):** `/tmp/lab60c`, `USER=labuser_60_fwactive`, `GROUP=labgrp_60_fwactive`
- **Traps rehearsed this lab:** **T60-A** · **T60-B** · **T41** · **T44**

> Read-only inspection only. Destroy-restore in this lab means evidence-file lifecycle only, never firewalld state mutation.

---

## LAB HEADER BLOCK

```bash
echo "OS:    $(cat /etc/redhat-release 2>/dev/null || grep PRETTY_NAME /etc/os-release)"
echo "TIME:  $(date -Is)"
echo "USER:  $(whoami)@$(hostname)"
echo "PRACTICE DIR: /usr"
echo "TRAPS: T60-A T60-B T41 T44"
systemctl is-active firewalld 2>/dev/null || echo "firewalld inactive"
firewall-cmd --state 2>/dev/null || true
ls -ld /usr
```

> STOP - paste header output before setup.

---

## Objective

1. Audit active-zone state and store traceable journal evidence.
2. Prove destroy-restore discipline (T41) without touching firewall configuration.
3. Confirm cleanup leaves no orphan sandbox/user/group state (T44).

---

## Lab-Wide Setup (Tier B)

```bash
sudo -i

export SANDBOX=/tmp/lab60c
export GROUP=labgrp_60_fwactive
export USER=labuser_60_fwactive
export USER_HOME=${SANDBOX}/home_${USER}

mkdir -p "${SANDBOX}" "${USER_HOME}" /root/rhcsa_journal/lab-60c/task1 /root/rhcsa_journal/lab-60c/task2
getent group "${GROUP}" >/dev/null || groupadd "${GROUP}"
getent passwd "${USER}" >/dev/null || useradd -d "${USER_HOME}" -M -s /bin/bash -g "${GROUP}" "${USER}"
chown -R "${USER}:${GROUP}" "${SANDBOX}"
```

---

## Task 1 - Audit active-zone state in journal

### Purpose

Collect a complete, replayable snapshot of active zones, default zone, and runtime/permanent compare output.

### Main command block

```bash
TASKLOG=/tmp/lab60c/task1.txt

echo "== active zones ==" | tee "${TASKLOG}"
sudo firewall-cmd --get-active-zones | tee -a "${TASKLOG}"

echo "== default zone ==" | tee -a "${TASKLOG}"
sudo firewall-cmd --get-default-zone | tee -a "${TASKLOG}"

echo "== runtime all (scoped head) ==" | tee -a "${TASKLOG}"
sudo firewall-cmd --list-all-zones | head -n 40 | tee -a "${TASKLOG}"

echo "== permanent all (scoped head) ==" | tee -a "${TASKLOG}"
sudo firewall-cmd --permanent --list-all-zones | head -n 40 | tee -a "${TASKLOG}"

echo "== public runtime/permanent compare ==" | tee -a "${TASKLOG}"
sudo firewall-cmd --info-zone=public | tee -a "${TASKLOG}"
sudo firewall-cmd --permanent --info-zone=public | tee -a "${TASKLOG}"

echo "exit was: $?"
```

### Journal write

```bash
cp /tmp/lab60c/task1.txt /root/rhcsa_journal/lab-60c/task1/audit.txt
cat > /root/rhcsa_journal/lab-60c/task1/done.txt <<EOF
LAB: lab-60c
TASK: task1
DATE: $(date -Is)
STATUS: COMPLETE
EOF
```

---

## Task 2 - Destroy-restore drill (read-only evidence lifecycle)

### Purpose

Rehearse T41 resilience flow by destroying and restoring **journal evidence copies only**, while preserving firewall read-only posture.

### Main command block

```bash
TASKLOG=/tmp/lab60c/task2.txt
SRC=/root/rhcsa_journal/lab-60c/task1/audit.txt
WORK=/tmp/lab60c/audit-copy.txt

echo "phase A: restore baseline copy from journal" | tee "${TASKLOG}"
cp "${SRC}" "${WORK}"
test -s "${WORK}" && echo "OK restored copy exists" | tee -a "${TASKLOG}"

echo "phase B: destroy working copy (no firewall changes)" | tee -a "${TASKLOG}"
rm -f "${WORK}"
test -e "${WORK}" && echo "FAIL copy still exists" | tee -a "${TASKLOG}" || echo "OK destroyed" | tee -a "${TASKLOG}"

echo "phase C: restore working copy again from source journal" | tee -a "${TASKLOG}"
cp "${SRC}" "${WORK}"
wc -l "${WORK}" | tee -a "${TASKLOG}"
sha256sum "${SRC}" "${WORK}" | tee -a "${TASKLOG}"

echo "phase D: confirm firewall remained untouched by drill" | tee -a "${TASKLOG}"
sudo firewall-cmd --get-active-zones | tee -a "${TASKLOG}"
sudo firewall-cmd --get-default-zone | tee -a "${TASKLOG}"

echo "exit was: $?"
```

### Trap callouts

- **T41:** Destroy-restore applies to artifacts/evidence too, not only service files.
- **T60-B:** Re-audit runtime/permanent snapshots after drills to ensure no accidental operational drift.

### Journal write

```bash
cp /tmp/lab60c/task2.txt /root/rhcsa_journal/lab-60c/task2/destroy-restore.txt
```

---

## Lab Closeout - Section 6 Teardown

```bash
set +e

if getent passwd "${USER}" >/dev/null 2>&1; then
  userdel -r "${USER}" 2>/dev/null
fi
if getent group "${GROUP}" >/dev/null 2>&1; then
  groupdel "${GROUP}" 2>/dev/null
fi
rm -rf "${SANDBOX}"

echo "-- lab-60c cleanup audit --"
getent passwd "${USER}" >/dev/null && echo "FAIL user remains" || echo "OK user gone"
getent group  "${GROUP}" >/dev/null && echo "FAIL group remains" || echo "OK group gone"
test -d "${SANDBOX}" && echo "FAIL sandbox remains" || echo "OK sandbox gone"
test -d "${USER_HOME}" && echo "FAIL home remains" || echo "OK home gone"

set -e
```

---

## Checklist

- [ ] Task 1 completed (active/default/runtime/permanent snapshots captured in journal)
- [ ] Task 2 completed (destroy-restore drill run on evidence copy; firewall remained read-only)
- [ ] T60-A, T60-B, T41, and T44 risks documented
- [ ] Section 6 closeout audit shows all `OK`

---

## Author

**Kelvin R. Tobias**
[kelvinintech.com](https://kelvinintech.com) · [GitHub](https://github.com/kelvintechnical) · [LinkedIn](https://www.linkedin.com/in/kelvin-r-tobias-211949219)
