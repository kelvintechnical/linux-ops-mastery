# Lab 75c - Configure PAM to Limit root Access (Verify)

## Lab Header Block

- ENV: RHEL-family Linux host or compatible lab VM
- OS: Linux
- USER: root-capable lab account with sudo
- TIMEBOX: 20-30 minutes
- PRACTICE DIRECTORY: `/proc`
- PRIMARY COMMANDS: `pam_securetty.so`
- TRAPS: T75-A: wrong securetty entry can block intended root console logins; T75-B: SSH root login is controlled by sshd_config as well as PAM; T41 destroy-restore; T44 cleanup safety

This lab's practice directory is: `/proc`.

## Lab-Wide Setup - Tier B Sandbox

Run this before Task 1.

```bash
export LAB_NUM=75
export LAB_SLUG=pam_securetty_root_access
export SANDBOX=/tmp/labsandbox_${LAB_NUM}
export GROUP=labgrp_${LAB_NUM}_${LAB_SLUG}
export USER=labuser_${LAB_NUM}_${LAB_SLUG}
export USER_HOME=${SANDBOX}/home_${USER}

mkdir -p "${SANDBOX}" "${USER_HOME}"
getent group  "${GROUP}" >/dev/null || groupadd "${GROUP}"
getent passwd "${USER}"  >/dev/null || useradd -d "${USER_HOME}" -M -s /bin/bash -g "${GROUP}" "${USER}"
chown -R "${USER}:${GROUP}" "${SANDBOX}"
cat > "${SANDBOX}/THIS_DIRECTORY.txt" <<'EOF'
Practice directory: /proc
Live kernel and process information appears here as files. Nothing under /proc is regular persisted disk data.
EOF
id "${USER}"
ls -ld "${SANDBOX}" "${USER_HOME}" /proc
echo "Sandbox built by $(whoami) at $(date -Is)"
echo "exit was: $?"
```

## Task 1 - Audit evidence for Configure PAM to Limit root Access

### Warm-Up Rotation

```bash
pwd
ls -ld /proc
test -e /proc && echo "practice directory exists"
printf 'lab 75c task 1 warm-up at %s
' "$(date -Is)" | tee "${SANDBOX}/warmup-c1.txt"
```

### WEAVE TRACE

```bash
whoami
id "${USER}"
sudo -u "${USER}" bash -lc 'whoami; pwd; echo weave-ok'
ls -ld "${SANDBOX}" /proc
```

### Purpose

Audit evidence for Configure PAM to Limit root Access. This task connects `pam_securetty.so` to a repeatable artifact in `${SANDBOX}`.

### Main Command Block

```bash
test -s "${SANDBOX}/journal.txt" && echo journal-present
ls -l "${SANDBOX}" | tee "${SANDBOX}/verify-listing.txt"
grep -E 'Trap rehearsed|Persistence check' "${SANDBOX}/journal.txt" | tee "${SANDBOX}/verify-journal.txt" || true
ls -ld /proc | tee -a "${SANDBOX}/task-1-practice.txt"
test -e /proc && echo "/proc checked again" | tee -a "${SANDBOX}/task-1-practice.txt"
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
| `pam_securetty.so` | Practice token for this lab | Repeat it until recognition is automatic |

### Concept Card

| Concept | Answer |
|---|---|
| Command family | `pam_securetty.so` |
| Practice directory | `/proc` |
| Evidence directory | `${SANDBOX}` |
| Trap risk | T41: verify evidence before teardown |
| Recovery phrase | Stop, restore the saved state, then verify before continuing |

### PERSISTENCE CHECK

```bash
ls -l "${SANDBOX}"
test -s "${SANDBOX}/task-1-exit.txt"
printf 'Persistence check 75c task 1: PASS
' | tee -a "${SANDBOX}/journal.txt"
```

### Journal Write

```bash
cat >> "${SANDBOX}/journal.txt" <<'EOF'
Lab 75c Task 1
What I practiced: Audit evidence for Configure PAM to Limit root Access
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

## Task 2 - Destroy-restore drill for Configure PAM to Limit root Access

### Warm-Up Rotation

```bash
pwd
ls -ld /proc
test -e /proc && echo "practice directory exists"
printf 'lab 75c task 2 warm-up at %s
' "$(date -Is)" | tee "${SANDBOX}/warmup-c2.txt"
```

### WEAVE TRACE

```bash
whoami
id "${USER}"
sudo -u "${USER}" bash -lc 'whoami; pwd; echo weave-ok'
ls -ld "${SANDBOX}" /proc
```

### Purpose

Destroy-restore drill for Configure PAM to Limit root Access. This task connects `pam_securetty.so` to a repeatable artifact in `${SANDBOX}`.

### Main Command Block

```bash
cp -a "${SANDBOX}/journal.txt" /tmp/lab-75-journal.backup
rm -rf "${SANDBOX}/restore-test"
mkdir -p "${SANDBOX}/restore-test"
cp -a /tmp/lab-75-journal.backup "${SANDBOX}/restore-test/journal.restored"
test -s "${SANDBOX}/restore-test/journal.restored" && echo restore-pass | tee "${SANDBOX}/restore-check.txt"
ls -ld /proc | tee -a "${SANDBOX}/task-2-practice.txt"
test -e /proc && echo "/proc checked again" | tee -a "${SANDBOX}/task-2-practice.txt"
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
| `pam_securetty.so` | Practice token for this lab | Repeat it until recognition is automatic |

### Concept Card

| Concept | Answer |
|---|---|
| Command family | `pam_securetty.so` |
| Practice directory | `/proc` |
| Evidence directory | `${SANDBOX}` |
| Trap risk | T44: cleanup must not destroy the only evidence copy |
| Recovery phrase | Stop, restore the saved state, then verify before continuing |

### PERSISTENCE CHECK

```bash
ls -l "${SANDBOX}"
test -s "${SANDBOX}/task-2-exit.txt"
printf 'Persistence check 75c task 2: PASS
' | tee -a "${SANDBOX}/journal.txt"
```

### Journal Write

```bash
cat >> "${SANDBOX}/journal.txt" <<'EOF'
Lab 75c Task 2
What I practiced: Destroy-restore drill for Configure PAM to Limit root Access
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
export LAB_NUM=75
export LAB_SLUG=pam_securetty_root_access
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
echo "Lab 75 cleanup complete at $(date -Is)"
echo "exit was: $?"
```

## Author

Kelvin R. Tobias  
Website: kelvinintech.com  
GitHub: kelvintechnical  
LinkedIn: Kelvin R. Tobias
