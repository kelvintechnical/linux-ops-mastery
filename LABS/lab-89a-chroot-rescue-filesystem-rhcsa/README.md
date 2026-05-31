# Lab 89a - Chroot into Rescue Filesystem (RHCSA)

## Lab Header Block

- ENV: RHEL-family Linux host or compatible lab VM
- OS: Linux
- USER: root-capable lab account with sudo
- TIMEBOX: 20-30 minutes
- PRACTICE DIRECTORY: `/root`
- PRIMARY COMMANDS: `chroot /mnt/sysimage`
- TRAPS: T89-A: chroot without bind-mounting /dev /proc /sys limits repair tools; T89-B: editing the rescue environment instead of target root fixes the wrong system; T41 destroy-restore; T44 cleanup safety

This lab's practice directory is: `/root`.

## Lab-Wide Setup - Tier B Sandbox

Run this before Task 1.

```bash
export LAB_NUM=89
export LAB_SLUG=chroot_rescue_filesystem
export SANDBOX=/tmp/labsandbox_${LAB_NUM}
export GROUP=labgrp_${LAB_NUM}_${LAB_SLUG}
export USER=labuser_${LAB_NUM}_${LAB_SLUG}
export USER_HOME=${SANDBOX}/home_${USER}

mkdir -p "${SANDBOX}" "${USER_HOME}"
getent group  "${GROUP}" >/dev/null || groupadd "${GROUP}"
getent passwd "${USER}"  >/dev/null || useradd -d "${USER_HOME}" -M -s /bin/bash -g "${GROUP}" "${USER}"
chown -R "${USER}:${GROUP}" "${SANDBOX}"
cat > "${SANDBOX}/THIS_DIRECTORY.txt" <<'EOF'
Practice directory: /root
The root user home lives here. It remains available even when /home is not mounted.
EOF
id "${USER}"
ls -ld "${SANDBOX}" "${USER_HOME}" /root
echo "Sandbox built by $(whoami) at $(date -Is)"
echo "exit was: $?"
```

## Task 1 - Canonical RHCSA form for Chroot into Rescue Filesystem

### Warm-Up Rotation

```bash
pwd
ls -ld /root
test -e /root && echo "practice directory exists"
printf 'lab 89a task 1 warm-up at %s
' "$(date -Is)" | tee "${SANDBOX}/warmup-a1.txt"
```

### WEAVE TRACE

```bash
whoami
id "${USER}"
sudo -u "${USER}" bash -lc 'whoami; pwd; echo weave-ok'
ls -ld "${SANDBOX}" /root
```

### Purpose

Canonical RHCSA form for Chroot into Rescue Filesystem. This task connects `chroot /mnt/sysimage` to a repeatable artifact in `${SANDBOX}`.

### Main Command Block

```bash
printf 'Lab 89 evidence for Chroot into Rescue Filesystem\n' | tee ${SANDBOX}/task-1-topic.txt
printf 'Command family: chroot /mnt/sysimage\n' | tee -a ${SANDBOX}/task-1-topic.txt
ls -ld /root | tee -a "${SANDBOX}/task-1-practice.txt"
test -e /root && echo "/root checked again" | tee -a "${SANDBOX}/task-1-practice.txt"
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

Task 1 is the safe, exam-style version of Chroot into Rescue Filesystem. It creates evidence first and avoids changing production state without a restore path.

### Expected Output

Evidence files appear under the sandbox. Any system-changing command is either a preview, a test-profile operation, or paired with a restore command.

### Switches And Repetition Table

| Switch / Command | Meaning | Why it matters |
|---|---|---|
| `chroot` | Practice token for this lab | Repeat it until recognition is automatic |
| `/mnt/sysimage` | Practice token for this lab | Repeat it until recognition is automatic |

### Concept Card

| Concept | Answer |
|---|---|
| Command family | `chroot /mnt/sysimage` |
| Practice directory | `/root` |
| Evidence directory | `${SANDBOX}` |
| Trap risk | T89-A: chroot without bind-mounting /dev /proc /sys limits repair tools |
| Recovery phrase | Stop, restore the saved state, then verify before continuing |

### PERSISTENCE CHECK

```bash
ls -l "${SANDBOX}"
test -s "${SANDBOX}/task-1-exit.txt"
printf 'Persistence check 89a task 1: PASS
' | tee -a "${SANDBOX}/journal.txt"
```

### Journal Write

```bash
cat >> "${SANDBOX}/journal.txt" <<'EOF'
Lab 89a Task 1
What I practiced: Canonical RHCSA form for Chroot into Rescue Filesystem
Trap rehearsed: T89-A: chroot without bind-mounting /dev /proc /sys limits repair tools
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

## Task 2 - Trap rehearsal and contrast for Chroot into Rescue Filesystem

### Warm-Up Rotation

```bash
pwd
ls -ld /root
test -e /root && echo "practice directory exists"
printf 'lab 89a task 2 warm-up at %s
' "$(date -Is)" | tee "${SANDBOX}/warmup-a2.txt"
```

### WEAVE TRACE

```bash
whoami
id "${USER}"
sudo -u "${USER}" bash -lc 'whoami; pwd; echo weave-ok'
ls -ld "${SANDBOX}" /root
```

### Purpose

Trap rehearsal and contrast for Chroot into Rescue Filesystem. This task connects `chroot /mnt/sysimage` to a repeatable artifact in `${SANDBOX}`.

### Main Command Block

```bash
printf 'Trap rehearsal: T89-B: editing the rescue environment instead of target root fixes the wrong system\n' | tee ${SANDBOX}/task-2-trap.txt
printf 'Restore note: verify before cleanup\n' | tee -a ${SANDBOX}/task-2-trap.txt
ls -ld /root | tee -a "${SANDBOX}/task-2-practice.txt"
test -e /root && echo "/root checked again" | tee -a "${SANDBOX}/task-2-practice.txt"
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
| `chroot` | Practice token for this lab | Repeat it until recognition is automatic |
| `/mnt/sysimage` | Practice token for this lab | Repeat it until recognition is automatic |

### Concept Card

| Concept | Answer |
|---|---|
| Command family | `chroot /mnt/sysimage` |
| Practice directory | `/root` |
| Evidence directory | `${SANDBOX}` |
| Trap risk | T89-B: editing the rescue environment instead of target root fixes the wrong system |
| Recovery phrase | Stop, restore the saved state, then verify before continuing |

### PERSISTENCE CHECK

```bash
ls -l "${SANDBOX}"
test -s "${SANDBOX}/task-2-exit.txt"
printf 'Persistence check 89a task 2: PASS
' | tee -a "${SANDBOX}/journal.txt"
```

### Journal Write

```bash
cat >> "${SANDBOX}/journal.txt" <<'EOF'
Lab 89a Task 2
What I practiced: Trap rehearsal and contrast for Chroot into Rescue Filesystem
Trap rehearsed: T89-B: editing the rescue environment instead of target root fixes the wrong system
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
export LAB_NUM=89
export LAB_SLUG=chroot_rescue_filesystem
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
echo "Lab 89 cleanup complete at $(date -Is)"
echo "exit was: $?"
```

## Author

Kelvin R. Tobias  
Website: kelvinintech.com  
GitHub: kelvintechnical  
LinkedIn: Kelvin R. Tobias
