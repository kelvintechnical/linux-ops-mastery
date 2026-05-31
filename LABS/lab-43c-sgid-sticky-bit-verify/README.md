# Lab 43c: SGID and Sticky Bit Verify Capstone - Audit + Destroy/Restore

- **Series:** linux-ops-mastery - Permissions, Ownership, and Collaboration Controls
- **Trilogy:** `43a` (RHCSA) -> `43b` (Ansible) -> `43c` (Verify)
- **Time Estimate:** 25-35 minutes
- **Tasks:** 2 (Task 1 audit behavior evidence, Task 2 destroy-restore drill)
- **Practice Directory (rotation #43):** `/home`
- **Sandbox (Tier B):** `/tmp/lab43c` with `USER=labuser_43_sgid`, `GROUP=labgrp_43_sgid`
- **Traps rehearsed this lab:** **T43-A** · **T43-B** · **T41** · **T44**

> This lab is the auditor seat: prove behavior with evidence, then prove clean teardown and rebuild discipline.

---

## LAB HEADER BLOCK

```bash
echo "ENV:   ${ENV:-DECLARE_ME}"
echo "TIME:  $(date -Is)"
echo "USER:  $(whoami)@$(hostname)"
echo "TRAPS: T43-A T43-B T41 T44"
echo "PRACTICE DIR: /home"
```

---

## Objective

Validate SGID/sticky behavior with hard evidence and write journal artifacts that survive cleanup:

1. SGID directory auto-group inheritance is visible in file metadata.
2. Sticky directory blocks cross-user deletion.
3. Destroy-restore cycle is complete and audited.

---

## Lab-Wide Setup (Tier B)

```bash
sudo -i

export SANDBOX=/tmp/lab43c
export GROUP=labgrp_43_sgid
export USER=labuser_43_sgid
export USER_HOME=${SANDBOX}/home_${USER}
export JDIR=/root/rhcsa_journal/lab-43c

mkdir -p "${SANDBOX}" "${USER_HOME}" "${JDIR}/task1" "${JDIR}/task2"
getent group "${GROUP}" >/dev/null || groupadd "${GROUP}"
getent passwd "${USER}"  >/dev/null || useradd -d "${USER_HOME}" -M -s /bin/bash -g "${GROUP}" "${USER}"
getent passwd alice >/dev/null || useradd -M -s /bin/bash alice
getent passwd bob   >/dev/null || useradd -M -s /bin/bash bob
chown -R "${USER}:${GROUP}" "${SANDBOX}"
```

---

## Task 1 - Audit SGID + Sticky Behavior into Journal

### Purpose

Generate durable evidence for both controls and store it under `/root/rhcsa_journal/lab-43c/task1`.

### Main command block

```bash
cd /tmp/lab43c
mkdir -p groupdir shared

# SGID directory behavior
chgrp "${GROUP}" groupdir
chmod 2770 groupdir
sudo -u "${USER}" touch groupdir/proof.txt

# Sticky directory behavior
chmod 1777 shared
sudo -u alice touch shared/alice.txt
sudo -u bob rm shared/alice.txt 2> /tmp/lab43c/sticky-deny.log || true

# Combined mode example
chmod 3770 groupdir

# Journal capture
{
  echo "=== SGID directory state ==="
  stat -c '%A %a %U:%G %n' /tmp/lab43c/groupdir
  stat -c '%A %a %U:%G %n' /tmp/lab43c/groupdir/proof.txt
  echo "=== Sticky directory state ==="
  stat -c '%A %a %U:%G %n' /tmp/lab43c/shared
  ls -l /tmp/lab43c/shared
  echo "=== Sticky denial message ==="
  cat /tmp/lab43c/sticky-deny.log
} | tee /root/rhcsa_journal/lab-43c/task1/evidence.txt

cat > /root/rhcsa_journal/lab-43c/task1/notes.txt <<EOF
TOPIC: SGID group inheritance + sticky delete protection
TRAPS: T43-A (dir vs file SGID), T43-B (sticky semantics on directories), T41, T44
RESULT: proof.txt inherited group ${GROUP}; bob delete of alice.txt was denied
EOF
```

### Expected audit outcomes

- `groupdir/proof.txt` group is `${GROUP}`.
- `shared/alice.txt` still exists after Bob delete attempt.
- Denial message captured in `sticky-deny.log` and journal evidence.

---

## Task 2 - Destroy-Restore Drill (T41 Guard)

### Purpose

Practice full teardown, verify no residue, then restore the minimal stack.

### Main command block

```bash
set +e

# Destroy
rm -rf /tmp/lab43c
if getent passwd "${USER}" >/dev/null 2>&1; then
    userdel -r "${USER}" 2>/dev/null
fi
if getent group "${GROUP}" >/dev/null 2>&1; then
    groupdel "${GROUP}" 2>/dev/null
fi

# Audit destroy (T44 guard)
{
  echo "=== destroy audit ==="
  getent passwd "${USER}" >/dev/null && echo "FAIL user remains" || echo "OK user gone"
  getent group "${GROUP}" >/dev/null && echo "FAIL group remains" || echo "OK group gone"
  test -d /tmp/lab43c && echo "FAIL sandbox remains" || echo "OK sandbox gone"
} | tee /root/rhcsa_journal/lab-43c/task2/destroy-audit.txt

# Restore minimal stack
mkdir -p /tmp/lab43c
getent group "${GROUP}" >/dev/null || groupadd "${GROUP}"
getent passwd "${USER}"  >/dev/null || useradd -d "/tmp/lab43c/home_${USER}" -M -s /bin/bash -g "${GROUP}" "${USER}"
mkdir -p "/tmp/lab43c/home_${USER}"
chown -R "${USER}:${GROUP}" /tmp/lab43c

{
  echo "=== restore audit ==="
  id "${USER}"
  getent group "${GROUP}"
  ls -ld /tmp/lab43c "/tmp/lab43c/home_${USER}"
} | tee /root/rhcsa_journal/lab-43c/task2/restore-audit.txt

set -e
```

### Expected outcomes

- Destroy audit prints only `OK` lines.
- Restore audit confirms user/group/sandbox were recreated.

---

## Section 6 Closeout

Run once more at lab completion to leave no residue:

```bash
set +e
rm -rf /tmp/lab43c
if getent passwd "${USER}" >/dev/null 2>&1; then userdel -r "${USER}" 2>/dev/null; fi
if getent group "${GROUP}" >/dev/null 2>&1; then groupdel "${GROUP}" 2>/dev/null; fi
echo "-- final audit --"
getent passwd "${USER}" >/dev/null && echo "FAIL user remains" || echo "OK user gone"
getent group "${GROUP}" >/dev/null && echo "FAIL group remains" || echo "OK group gone"
test -d /tmp/lab43c && echo "FAIL sandbox remains" || echo "OK sandbox gone"
set -e
```

---

## Checklist

- [ ] Task 1 evidence captured in journal for SGID and sticky behavior
- [ ] Task 2 destroy audit showed no residue and restore audit succeeded
- [ ] T43-A/T43-B verified with observable metadata and delete-denial output
- [ ] T41/T44 guarded by mandatory destroy-restore + cleanup audits

---

## Author

**Kelvin R. Tobias**
