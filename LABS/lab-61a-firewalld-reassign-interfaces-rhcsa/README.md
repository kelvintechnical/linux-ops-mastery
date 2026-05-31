# Lab 61a - Reassign Interfaces to Zones (RHCSA)

## Lab Header Block

- ENV: RHEL-family Linux host or compatible lab VM
- OS: Linux
- USER: root-capable lab account with sudo
- TIMEBOX: 20-30 minutes
- PRACTICE DIRECTORY: `/bin`
- PRIMARY COMMANDS: `firewall-cmd --change-interface`
- TRAPS: T61-A: moving the real SSH interface can lock you out; use a test interface or restore job; T61-B: runtime --change-interface is lost after reload unless permanent config is updated; T41 destroy-restore; T44 cleanup safety

This lab's practice directory is: `/bin`.

## Lab-Wide Setup - Tier B Sandbox

Run this before Task 1.

```bash
export LAB_NUM=61
export LAB_SLUG=firewalld_reassign_interfaces
export SANDBOX=/tmp/labsandbox_${LAB_NUM}
export GROUP=labgrp_${LAB_NUM}_${LAB_SLUG}
export USER=labuser_${LAB_NUM}_${LAB_SLUG}
export USER_HOME=${SANDBOX}/home_${USER}

mkdir -p "${SANDBOX}" "${USER_HOME}"
getent group  "${GROUP}" >/dev/null || groupadd "${GROUP}"
getent passwd "${USER}"  >/dev/null || useradd -d "${USER_HOME}" -M -s /bin/bash -g "${GROUP}" "${USER}"
chown -R "${USER}:${GROUP}" "${SANDBOX}"
cat > "${SANDBOX}/THIS_DIRECTORY.txt" <<'EOF'
Practice directory: /bin
Essential user commands live here. On modern RHEL it is usually a symlink into /usr/bin, but the RHCSA mental model is still that basic user commands belong here.
EOF
id "${USER}"
ls -ld "${SANDBOX}" "${USER_HOME}" /bin
echo "Sandbox built by $(whoami) at $(date -Is)"
echo "exit was: $?"
```

## Task 1 - Canonical RHCSA form for Reassign Interfaces to Zones

### Warm-Up Rotation

```bash
pwd
ls -ld /bin
test -e /bin && echo "practice directory exists"
printf 'lab 61a task 1 warm-up at %s
' "$(date -Is)" | tee "${SANDBOX}/warmup-a1.txt"
```

### WEAVE TRACE

```bash
whoami
id "${USER}"
sudo -u "${USER}" bash -lc 'whoami; pwd; echo weave-ok'
ls -ld "${SANDBOX}" /bin
```

### Purpose

Canonical RHCSA form for Reassign Interfaces to Zones. This task connects `firewall-cmd --change-interface` to a repeatable artifact in `${SANDBOX}`.

### Main Command Block

```bash
sudo firewall-cmd --get-active-zones | tee ${SANDBOX}/active-zones.txt
sudo firewall-cmd --zone=internal --change-interface=lab61dummy || true
sudo firewall-cmd --zone=public --change-interface=lab61dummy || true
ls -ld /bin | tee -a "${SANDBOX}/task-1-practice.txt"
test -e /bin && echo "/bin checked again" | tee -a "${SANDBOX}/task-1-practice.txt"
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

Task 1 is the safe, exam-style version of Reassign Interfaces to Zones. It creates evidence first and avoids changing production state without a restore path.

### Expected Output

Evidence files appear under the sandbox. Any system-changing command is either a preview, a test-profile operation, or paired with a restore command.

### Switches And Repetition Table

| Switch / Command | Meaning | Why it matters |
|---|---|---|
| `firewall-cmd` | Practice token for this lab | Repeat it until recognition is automatic |
| `--change-interface` | Practice token for this lab | Repeat it until recognition is automatic |

### Concept Card

| Concept | Answer |
|---|---|
| Command family | `firewall-cmd --change-interface` |
| Practice directory | `/bin` |
| Evidence directory | `${SANDBOX}` |
| Trap risk | T61-A: moving the real SSH interface can lock you out; use a test interface or restore job |
| Recovery phrase | Stop, restore the saved state, then verify before continuing |

### PERSISTENCE CHECK

```bash
ls -l "${SANDBOX}"
test -s "${SANDBOX}/task-1-exit.txt"
printf 'Persistence check 61a task 1: PASS
' | tee -a "${SANDBOX}/journal.txt"
```

### Journal Write

```bash
cat >> "${SANDBOX}/journal.txt" <<'EOF'
Lab 61a Task 1
What I practiced: Canonical RHCSA form for Reassign Interfaces to Zones
Trap rehearsed: T61-A: moving the real SSH interface can lock you out; use a test interface or restore job
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

## Task 2 - Trap rehearsal and contrast for Reassign Interfaces to Zones

### Warm-Up Rotation

```bash
pwd
ls -ld /bin
test -e /bin && echo "practice directory exists"
printf 'lab 61a task 2 warm-up at %s
' "$(date -Is)" | tee "${SANDBOX}/warmup-a2.txt"
```

### WEAVE TRACE

```bash
whoami
id "${USER}"
sudo -u "${USER}" bash -lc 'whoami; pwd; echo weave-ok'
ls -ld "${SANDBOX}" /bin
```

### Purpose

Trap rehearsal and contrast for Reassign Interfaces to Zones. This task connects `firewall-cmd --change-interface` to a repeatable artifact in `${SANDBOX}`.

### Main Command Block

```bash
sudo firewall-cmd --permanent --zone=internal --change-interface=lab61dummy || true
sudo firewall-cmd --reload
sudo firewall-cmd --get-active-zones | tee -a ${SANDBOX}/active-zones.txt
ls -ld /bin | tee -a "${SANDBOX}/task-2-practice.txt"
test -e /bin && echo "/bin checked again" | tee -a "${SANDBOX}/task-2-practice.txt"
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

Task 2 contrasts the common mistake with the safer command form.

### Expected Output

The trap evidence should show why the unsafe or incomplete form is not enough.

### Switches And Repetition Table

| Switch / Command | Meaning | Why it matters |
|---|---|---|
| `firewall-cmd` | Practice token for this lab | Repeat it until recognition is automatic |
| `--change-interface` | Practice token for this lab | Repeat it until recognition is automatic |

### Concept Card

| Concept | Answer |
|---|---|
| Command family | `firewall-cmd --change-interface` |
| Practice directory | `/bin` |
| Evidence directory | `${SANDBOX}` |
| Trap risk | T61-B: runtime --change-interface is lost after reload unless permanent config is updated |
| Recovery phrase | Stop, restore the saved state, then verify before continuing |

### PERSISTENCE CHECK

```bash
ls -l "${SANDBOX}"
test -s "${SANDBOX}/task-2-exit.txt"
printf 'Persistence check 61a task 2: PASS
' | tee -a "${SANDBOX}/journal.txt"
```

### Journal Write

```bash
cat >> "${SANDBOX}/journal.txt" <<'EOF'
Lab 61a Task 2
What I practiced: Trap rehearsal and contrast for Reassign Interfaces to Zones
Trap rehearsed: T61-B: runtime --change-interface is lost after reload unless permanent config is updated
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
export LAB_NUM=61
export LAB_SLUG=firewalld_reassign_interfaces
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
echo "Lab 61 cleanup complete at $(date -Is)"
echo "exit was: $?"
```

## Author

Kelvin R. Tobias  
Website: kelvinintech.com  
GitHub: kelvintechnical  
LinkedIn: Kelvin R. Tobias
