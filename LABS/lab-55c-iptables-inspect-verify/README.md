# Lab 55c: Inspecting iptables (Verify Capstone)

- **Series:** linux-ops-mastery
- **Trilogy:** `55a` (RHCSA) -> `55b` (Ansible) -> `55c` (Verify)
- **Practice Directory:** `/tmp`
- **Tier B Sandbox:** `/tmp/lab55c`
- **Lab User/Group:** `labuser_55_iptables` / `labgrp_55_iptables`
- **Traps rehearsed:** `T55-A`, `T55-B`, `T41`, `T44`

This lab's practice directory is: `/tmp`

> Read-only inspection only. Do **not** add, flush, or modify any firewall rules.

---

## LAB HEADER

```bash
echo "TIME: $(date -Is)"
echo "USER: $(whoami)@$(hostname)"
echo "PRACTICE DIR: /tmp"
echo "VERIFY TARGET: journal audit + destroy-restore evidence drill"
echo "TRAPS: T55-A T55-B T41 T44"
cat /etc/redhat-release 2>/dev/null || grep PRETTY_NAME /etc/os-release
echo "exit was: $?"
```

> STOP and confirm header output before continuing.

---

## Lab-Wide Tier B Setup (run before Task 1)

```bash
sudo -i
export LAB_NUM=55
export LAB_SLUG=iptables
export SANDBOX=/tmp/lab55c
export GROUP=labgrp_55_iptables
export USER=labuser_55_iptables
export USER_HOME=${SANDBOX}/home_${USER}

mkdir -p "${SANDBOX}" "${USER_HOME}" /root/rhcsa_journal/lab-55c/task1 /root/rhcsa_journal/lab-55c/task2
getent group "${GROUP}" >/dev/null || groupadd "${GROUP}"
getent passwd "${USER}" >/dev/null || useradd -d "${USER_HOME}" -M -s /bin/bash -g "${GROUP}" "${USER}"
chown -R "${USER}:${GROUP}" "${SANDBOX}"

id "${USER}"
ls -ld /tmp "${SANDBOX}" "${USER_HOME}"
echo "Sandbox built by $(whoami) at $(date -Is)"
echo "exit was: $?"
```

---

## Task 1 - Audit iptables/nft captures in the journal

Practice directory this task: `/tmp`

### Purpose

Audit lab evidence from `55a` and `55b` and confirm key strings exist for legacy and modern firewall inspection outputs.

### Main Block

```bash
export SANDBOX=/tmp/lab55c
export JROOT=/root/rhcsa_journal
export TASKLOG="${SANDBOX}/task1.txt"

{
  echo "=== LAB55 JOURNAL AUDIT ==="
  echo "--- done files ---"
  find "${JROOT}/lab-55a" "${JROOT}/lab-55b" -name done.txt -print 2>/dev/null | sort
  echo "--- evidence files ---"
  find "${JROOT}/lab-55a" "${JROOT}/lab-55b" -type f -name '*.txt' -print 2>/dev/null | sort
  echo "--- marker scan ---"
  rg -n "iptables -L -n -v|iptables-save|nft list ruleset|Chain INPUT|RHEL9|nftables" \
     "${JROOT}/lab-55a" "${JROOT}/lab-55b" 2>/dev/null || true
  echo "--- current host snapshot (read-only) ---"
  sudo iptables -L -n -v 2>&1 | head -n 25
  sudo nft list ruleset 2>&1 | head -n 40
} | tee "${TASKLOG}"

sudo -u "${USER}" bash -c 'echo "Task1 verify audit reviewed at $(date -Is)" >> /tmp/lab55c/task1-reviewed-by-user.txt'
stat -c '%U:%G %a %n' /tmp/lab55c/task1-reviewed-by-user.txt | tee -a "${TASKLOG}"
echo "exit was: $?"
```

### Trap focus

- `T41`: persistence and audit checks are mandatory; do not skip evidence validation.
- `T55-A`: if legacy output and nft output differ, document both instead of assuming one is wrong.

### Journal Write

```bash
LAB=lab-55c
TASK=task1
JDIR="/root/rhcsa_journal/${LAB}/${TASK}"
mkdir -p "${JDIR}"
cp /tmp/lab55c/task1.txt "${JDIR}/evidence.txt"
cat > "${JDIR}/done.txt" <<EOF
LAB: ${LAB}
TASK: ${TASK}
DATE: $(date -Is)
USER: $(whoami)@$(hostname)
STATUS: COMPLETE
EOF
```

---

## Task 2 - Destroy-restore drill for evidence artifacts (no rule changes)

Practice directory this task: `/tmp`

### Purpose

Practice operational recovery by deleting local capture copies and restoring them from journal artifacts, while leaving firewall rules untouched.

### Main Block

```bash
export SANDBOX=/tmp/lab55c
export TASKLOG="${SANDBOX}/task2.txt"
export RESTORE_SRC_A=/root/rhcsa_journal/lab-55a/task1/evidence.txt
export RESTORE_SRC_B=/root/rhcsa_journal/lab-55b/task2/apply.txt
export DEST_A="${SANDBOX}/restore-from-55a.txt"
export DEST_B="${SANDBOX}/restore-from-55b.txt"

echo "=== baseline read-only snapshots ===" | tee "${TASKLOG}"
sudo iptables -L -n -v 2>&1 | head -n 20 | tee -a "${TASKLOG}"
sudo nft list ruleset 2>&1 | head -n 30 | tee -a "${TASKLOG}"

echo "=== destroy local copies ===" | tee -a "${TASKLOG}"
cp "${RESTORE_SRC_A}" "${DEST_A}"
cp "${RESTORE_SRC_B}" "${DEST_B}"
rm -f "${DEST_A}" "${DEST_B}"
ls -l "${SANDBOX}"/restore-from-* 2>&1 | tee -a "${TASKLOG}" || true

echo "=== restore from journal ===" | tee -a "${TASKLOG}"
cp "${RESTORE_SRC_A}" "${DEST_A}"
cp "${RESTORE_SRC_B}" "${DEST_B}"
wc -l "${DEST_A}" "${DEST_B}" | tee -a "${TASKLOG}"
head -n 3 "${DEST_A}" | tee -a "${TASKLOG}"
head -n 3 "${DEST_B}" | tee -a "${TASKLOG}"

echo "=== post-drill read-only snapshots (must remain inspection only) ===" | tee -a "${TASKLOG}"
sudo iptables -L -n -v 2>&1 | head -n 20 | tee -a "${TASKLOG}"
sudo nft list ruleset 2>&1 | head -n 30 | tee -a "${TASKLOG}"

sudo -u "${USER}" bash -c 'echo "Task2 destroy-restore reviewed at $(date -Is)" >> /tmp/lab55c/task2-reviewed-by-user.txt'
stat -c '%U:%G %a %n' /tmp/lab55c/task2-reviewed-by-user.txt | tee -a "${TASKLOG}"
echo "exit was: $?"
```

### Trap focus

- `T44`: verify cleanup and restoration artifacts so no residue pollutes later labs.
- `T55-B`: keep numeric listing (`-n`) for stable, non-blocking output in repeated drills.

### Journal Write

```bash
LAB=lab-55c
TASK=task2
JDIR="/root/rhcsa_journal/${LAB}/${TASK}"
mkdir -p "${JDIR}"
cp /tmp/lab55c/task2.txt "${JDIR}/evidence.txt"
cat > "${JDIR}/done.txt" <<EOF
LAB: ${LAB}
TASK: ${TASK}
DATE: $(date -Is)
USER: $(whoami)@$(hostname)
STATUS: COMPLETE
EOF
cat > "${JDIR}/notes.txt" <<EOF
TOPIC: verify audit plus destroy-restore drill for inspection artifacts
COMMANDS: find, rg, iptables -L -n -v, nft list ruleset, cp, rm, wc -l
TRAPS: T41 and T44 rehearsed
NEXT: trilogy complete
EOF
```

---

## Section 6 Closeout (after Task 2)

```bash
set +e
export SANDBOX=/tmp/lab55c
export GROUP=labgrp_55_iptables
export USER=labuser_55_iptables
export USER_HOME=${SANDBOX}/home_${USER}

if getent passwd "${USER}" >/dev/null 2>&1; then userdel -r "${USER}" 2>/dev/null; fi
if getent group "${GROUP}" >/dev/null 2>&1; then groupdel "${GROUP}" 2>/dev/null; fi
rm -rf "${SANDBOX}"

echo "── cleanup audit ──"
getent passwd "${USER}" >/dev/null && echo "❌ user remains" || echo "✅ user gone"
getent group "${GROUP}" >/dev/null && echo "❌ group remains" || echo "✅ group gone"
test -d "${SANDBOX}" && echo "❌ sandbox remains" || echo "✅ sandbox gone"
test -d "${USER_HOME}" && echo "❌ home remains" || echo "✅ home gone"

set -e
echo "Cleanup complete by $(whoami) at $(date -Is)"
echo "exit was: $?"
```

---

## Author

Kelvin R. Tobias
