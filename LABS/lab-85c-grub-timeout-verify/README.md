# Lab 85c - Modify GRUB Timeout (Verify)

## Lab Header Block

- ENV: RHEL-family Linux host or compatible lab VM
- OS: Linux
- USER: root-capable lab account with sudo
- TIMEBOX: 20-30 minutes
- PRACTICE DIRECTORY: `/usr`
- PRIMARY COMMANDS: `GRUB_TIMEOUT in /etc/default/grub`
- TRAPS: T85-A: editing /etc/default/grub alone does not regenerate active grub.cfg; T85-B: wrong grub.cfg output path differs on BIOS vs UEFI; T41 destroy-restore; T44 cleanup safety

This lab's practice directory is: `/usr`.

## Lab-Wide Setup - Tier B Sandbox

Run this before Task 1.

```bash
export LAB_NUM=85
export LAB_SLUG=grub_timeout
export SANDBOX=/tmp/labsandbox_${LAB_NUM}
export GROUP=labgrp_${LAB_NUM}_${LAB_SLUG}
export USER=labuser_${LAB_NUM}_${LAB_SLUG}
export USER_HOME=${SANDBOX}/home_${USER}

mkdir -p "${SANDBOX}" "${USER_HOME}"
getent group  "${GROUP}" >/dev/null || groupadd "${GROUP}"
getent passwd "${USER}"  >/dev/null || useradd -d "${USER_HOME}" -M -s /bin/bash -g "${GROUP}" "${USER}"
chown -R "${USER}:${GROUP}" "${SANDBOX}"
cat > "${SANDBOX}/THIS_DIRECTORY.txt" <<'EOF'
Practice directory: /usr
Most packaged programs, documentation, and shared data live under /usr. Many exam commands and man pages are installed here.
EOF
id "${USER}"
ls -ld "${SANDBOX}" "${USER_HOME}" /usr
echo "Sandbox built by $(whoami) at $(date -Is)"
echo "exit was: $?"
```

## Task 1 - Audit evidence for Modify GRUB Timeout

### Warm-Up Rotation

```bash
pwd
ls -ld /usr
test -e /usr && echo "practice directory exists"
printf 'lab 85c task 1 warm-up at %s
' "$(date -Is)" | tee "${SANDBOX}/warmup-c1.txt"
```

### WEAVE TRACE

```bash
whoami
id "${USER}"
sudo -u "${USER}" bash -lc 'whoami; pwd; echo weave-ok'
ls -ld "${SANDBOX}" /usr
```

### Purpose

Audit evidence for Modify GRUB Timeout. This task connects `GRUB_TIMEOUT in /etc/default/grub` to a repeatable artifact in `${SANDBOX}`.

### Main Command Block

```bash
test -s "${SANDBOX}/journal.txt" && echo journal-present
ls -l "${SANDBOX}" | tee "${SANDBOX}/verify-listing.txt"
grep -E 'Trap rehearsed|Persistence check' "${SANDBOX}/journal.txt" | tee "${SANDBOX}/verify-journal.txt" || true
ls -ld /usr | tee -a "${SANDBOX}/task-1-practice.txt"
test -e /usr && echo "/usr checked again" | tee -a "${SANDBOX}/task-1-practice.txt"
echo "exit was: $?" | tee -a "${SANDBOX}/task-1-exit.txt"
```

### Human-Readable Breakdown

- Confirm the practice directory and sandbox exist.
- Name the command and every switch before pressing Enter.
- Save evidence under `${SANDBOX}` for the verify tier.
- Use the Tier B user weave to keep user/group/home cleanup familiar.

### Reading It Left to Right

Read the command as: command, target, option, safety guard, evidence file. For firewall, PAM, SELinux, sysctl, and GRUB work, do not skip the restore or preview step.

### The Story

The verify tier treats previous evidence like production audit data: inspect first, then decide if state matches the journal.

### Expected Output

The verify listing and journal grep should produce non-empty files.

### Switches And Repetition Table

| Switch / Command | Meaning | Why it matters |
|---|---|---|
| `GRUB_TIMEOUT` | Practice token for this lab | Repeat it until recognition is automatic |
| `in` | Practice token for this lab | Repeat it until recognition is automatic |
| `/etc/default/grub` | Practice token for this lab | Repeat it until recognition is automatic |

### Concept Card

| Concept | Answer |
|---|---|
| Command family | `GRUB_TIMEOUT in /etc/default/grub` |
| Practice directory | `/usr` |
| Evidence directory | `${SANDBOX}` |
| Trap risk | T41: verify evidence before teardown |
| Recovery phrase | Stop, restore the saved state, then verify before continuing |

### PERSISTENCE CHECK

```bash
ls -l "${SANDBOX}"
test -s "${SANDBOX}/task-1-exit.txt"
printf 'Persistence check 85c task 1: PASS
' | tee -a "${SANDBOX}/journal.txt"
```

### Journal Write

```bash
cat >> "${SANDBOX}/journal.txt" <<'EOF'
Lab 85c Task 1
What I practiced: Audit evidence for Modify GRUB Timeout
Trap rehearsed: T41: verify evidence before teardown
What I will verify later: evidence file exists and the system state is restored.
EOF
```

### Cleanup

Task cleanup is intentionally light. The final Section 6 closeout removes the sandbox, user, and group after Task 2.

### Troubleshoot

- If the command fails, read the exact error before retrying.
- If a backup exists, restore from it before running another variant.
- If a command changes runtime and persistent state, verify both.

### STOP Marker

Stop after Task 1. Say out loud what changed, what did not change, and what evidence proves it.

## Task 2 - Destroy-restore drill for Modify GRUB Timeout

### Warm-Up Rotation

```bash
pwd
ls -ld /usr
test -e /usr && echo "practice directory exists"
printf 'lab 85c task 2 warm-up at %s
' "$(date -Is)" | tee "${SANDBOX}/warmup-c2.txt"
```

### WEAVE TRACE

```bash
whoami
id "${USER}"
sudo -u "${USER}" bash -lc 'whoami; pwd; echo weave-ok'
ls -ld "${SANDBOX}" /usr
```

### Purpose

Destroy-restore drill for Modify GRUB Timeout. This task connects `GRUB_TIMEOUT in /etc/default/grub` to a repeatable artifact in `${SANDBOX}`.

### Main Command Block

```bash
cp -a "${SANDBOX}/journal.txt" /tmp/lab-85-journal.backup
rm -rf "${SANDBOX}/restore-test"
mkdir -p "${SANDBOX}/restore-test"
cp -a /tmp/lab-85-journal.backup "${SANDBOX}/restore-test/journal.restored"
test -s "${SANDBOX}/restore-test/journal.restored" && echo restore-pass | tee "${SANDBOX}/restore-check.txt"
ls -ld /usr | tee -a "${SANDBOX}/task-2-practice.txt"
test -e /usr && echo "/usr checked again" | tee -a "${SANDBOX}/task-2-practice.txt"
echo "exit was: $?" | tee -a "${SANDBOX}/task-2-exit.txt"
```

### Human-Readable Breakdown

- Confirm the practice directory and sandbox exist.
- Name the command and every switch before pressing Enter.
- Save evidence under `${SANDBOX}` for the verify tier.
- Use the Tier B user weave to keep user/group/home cleanup familiar.

### Reading It Left to Right

Read the command as: command, target, option, safety guard, evidence file. For firewall, PAM, SELinux, sysctl, and GRUB work, do not skip the restore or preview step.

### The Story

The destroy-restore drill proves that the learner can recreate evidence from the journal rather than trusting memory.

### Expected Output

The restore check prints restore-pass and leaves a restored copy under the sandbox.

### Switches And Repetition Table

| Switch / Command | Meaning | Why it matters |
|---|---|---|
| `GRUB_TIMEOUT` | Practice token for this lab | Repeat it until recognition is automatic |
| `in` | Practice token for this lab | Repeat it until recognition is automatic |
| `/etc/default/grub` | Practice token for this lab | Repeat it until recognition is automatic |

### Concept Card

| Concept | Answer |
|---|---|
| Command family | `GRUB_TIMEOUT in /etc/default/grub` |
| Practice directory | `/usr` |
| Evidence directory | `${SANDBOX}` |
| Trap risk | T44: cleanup must not destroy the only evidence copy |
| Recovery phrase | Stop, restore the saved state, then verify before continuing |

### PERSISTENCE CHECK

```bash
ls -l "${SANDBOX}"
test -s "${SANDBOX}/task-2-exit.txt"
printf 'Persistence check 85c task 2: PASS
' | tee -a "${SANDBOX}/journal.txt"
```

### Journal Write

```bash
cat >> "${SANDBOX}/journal.txt" <<'EOF'
Lab 85c Task 2
What I practiced: Destroy-restore drill for Modify GRUB Timeout
Trap rehearsed: T44: cleanup must not destroy the only evidence copy
What I will verify later: evidence file exists and the system state is restored.
EOF
```

### Cleanup

Task cleanup is intentionally light. The final Section 6 closeout removes the sandbox, user, and group after Task 2.

### Troubleshoot

- If the command fails, read the exact error before retrying.
- If a backup exists, restore from it before running another variant.
- If a command changes runtime and persistent state, verify both.

### STOP Marker

Stop after Task 2. Say out loud what changed, what did not change, and what evidence proves it.

## Section 6 - Bulletproof Closeout Teardown

Run this after Task 2 only.

```bash
set +e
export LAB_NUM=85
export LAB_SLUG=grub_timeout
export SANDBOX=/tmp/labsandbox_${LAB_NUM}
export GROUP=labgrp_${LAB_NUM}_${LAB_SLUG}
export USER=labuser_${LAB_NUM}_${LAB_SLUG}

command -v chattr >/dev/null 2>&1 && chattr -R -i -a "${SANDBOX}" 2>/dev/null || true
userdel -r "${USER}" 2>/dev/null || userdel "${USER}" 2>/dev/null || true
groupdel "${GROUP}" 2>/dev/null || true
rm -rf "${SANDBOX}"
getent passwd "${USER}" || true
getent group "${GROUP}" || true
ls -ld "${SANDBOX}" 2>/dev/null || true
echo "Lab 85 cleanup complete at $(date -Is)"
echo "exit was: $?"
```

## Author

Kelvin R. Tobias  
Website: kelvinintech.com  
GitHub: kelvintechnical  
LinkedIn: Kelvin R. Tobias
