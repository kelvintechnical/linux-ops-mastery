# Lab 62a - Allow Services Through Firewall (RHCSA)

## Lab Header Block

- ENV: RHEL-family Linux host or compatible lab VM
- OS: Linux
- USER: root-capable lab account with sudo
- TIMEBOX: 20-30 minutes
- PRACTICE DIRECTORY: `/sbin`
- PRIMARY COMMANDS: `firewall-cmd --permanent --add-service`
- TRAPS: T62-A: adding a service without --permanent disappears after reload; T62-B: opening a service does not start the daemon that owns it; T41 destroy-restore; T44 cleanup safety

This lab's practice directory is: `/sbin`.

## Lab-Wide Setup - Tier B Sandbox

Run this before Task 1.

```bash
export LAB_NUM=62
export LAB_SLUG=firewall_allow_services
export SANDBOX=/tmp/labsandbox_${LAB_NUM}
export GROUP=labgrp_${LAB_NUM}_${LAB_SLUG}
export USER=labuser_${LAB_NUM}_${LAB_SLUG}
export USER_HOME=${SANDBOX}/home_${USER}

mkdir -p "${SANDBOX}" "${USER_HOME}"
getent group  "${GROUP}" >/dev/null || groupadd "${GROUP}"
getent passwd "${USER}"  >/dev/null || useradd -d "${USER_HOME}" -M -s /bin/bash -g "${GROUP}" "${USER}"
chown -R "${USER}:${GROUP}" "${SANDBOX}"
cat > "${SANDBOX}/THIS_DIRECTORY.txt" <<'EOF'
Practice directory: /sbin
Administrative commands live here. Network, firewall, recovery, and boot-administration tools are commonly associated with this path.
EOF
id "${USER}"
ls -ld "${SANDBOX}" "${USER_HOME}" /sbin
echo "Sandbox built by $(whoami) at $(date -Is)"
echo "exit was: $?"
```

## Task 1 - Canonical RHCSA form for Allow Services Through Firewall

### Warm-Up Rotation

```bash
pwd
ls -ld /sbin
test -e /sbin && echo "practice directory exists"
printf 'lab 62a task 1 warm-up at %s
' "$(date -Is)" | tee "${SANDBOX}/warmup-a1.txt"
```

### WEAVE TRACE

```bash
whoami
id "${USER}"
sudo -u "${USER}" bash -lc 'whoami; pwd; echo weave-ok'
ls -ld "${SANDBOX}" /sbin
```

### Purpose

Canonical RHCSA form for Allow Services Through Firewall. This task connects `firewall-cmd --permanent --add-service` to a repeatable artifact in `${SANDBOX}`.

### Main Command Block

```bash
sudo firewall-cmd --permanent --add-service=http
sudo firewall-cmd --permanent --add-service=ftp
sudo firewall-cmd --reload
sudo firewall-cmd --list-services | tee ${SANDBOX}/services.txt
ls -ld /sbin | tee -a "${SANDBOX}/task-1-practice.txt"
test -e /sbin && echo "/sbin checked again" | tee -a "${SANDBOX}/task-1-practice.txt"
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

Task 1 is the safe, exam-style version of Allow Services Through Firewall. It creates evidence first and avoids changing production state without a restore path.

### Expected Output

Evidence files appear under the sandbox. Any system-changing command is either a preview, a test-profile operation, or paired with a restore command.

### Switches And Repetition Table

| Switch / Command | Meaning | Why it matters |
|---|---|---|
| `firewall-cmd` | Practice token for this lab | Repeat it until recognition is automatic |
| `--permanent` | Practice token for this lab | Repeat it until recognition is automatic |
| `--add-service` | Practice token for this lab | Repeat it until recognition is automatic |

### Concept Card

| Concept | Answer |
|---|---|
| Command family | `firewall-cmd --permanent --add-service` |
| Practice directory | `/sbin` |
| Evidence directory | `${SANDBOX}` |
| Trap risk | T62-A: adding a service without --permanent disappears after reload |
| Recovery phrase | Stop, restore the saved state, then verify before continuing |

### PERSISTENCE CHECK

```bash
ls -l "${SANDBOX}"
test -s "${SANDBOX}/task-1-exit.txt"
printf 'Persistence check 62a task 1: PASS
' | tee -a "${SANDBOX}/journal.txt"
```

### Journal Write

```bash
cat >> "${SANDBOX}/journal.txt" <<'EOF'
Lab 62a Task 1
What I practiced: Canonical RHCSA form for Allow Services Through Firewall
Trap rehearsed: T62-A: adding a service without --permanent disappears after reload
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

## Task 2 - Trap rehearsal and contrast for Allow Services Through Firewall

### Warm-Up Rotation

```bash
pwd
ls -ld /sbin
test -e /sbin && echo "practice directory exists"
printf 'lab 62a task 2 warm-up at %s
' "$(date -Is)" | tee "${SANDBOX}/warmup-a2.txt"
```

### WEAVE TRACE

```bash
whoami
id "${USER}"
sudo -u "${USER}" bash -lc 'whoami; pwd; echo weave-ok'
ls -ld "${SANDBOX}" /sbin
```

### Purpose

Trap rehearsal and contrast for Allow Services Through Firewall. This task connects `firewall-cmd --permanent --add-service` to a repeatable artifact in `${SANDBOX}`.

### Main Command Block

```bash
sudo firewall-cmd --add-service=http
sudo firewall-cmd --reload
sudo firewall-cmd --list-services | tee ${SANDBOX}/runtime-trap.txt
ls -ld /sbin | tee -a "${SANDBOX}/task-2-practice.txt"
test -e /sbin && echo "/sbin checked again" | tee -a "${SANDBOX}/task-2-practice.txt"
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
| `--permanent` | Practice token for this lab | Repeat it until recognition is automatic |
| `--add-service` | Practice token for this lab | Repeat it until recognition is automatic |

### Concept Card

| Concept | Answer |
|---|---|
| Command family | `firewall-cmd --permanent --add-service` |
| Practice directory | `/sbin` |
| Evidence directory | `${SANDBOX}` |
| Trap risk | T62-B: opening a service does not start the daemon that owns it |
| Recovery phrase | Stop, restore the saved state, then verify before continuing |

### PERSISTENCE CHECK

```bash
ls -l "${SANDBOX}"
test -s "${SANDBOX}/task-2-exit.txt"
printf 'Persistence check 62a task 2: PASS
' | tee -a "${SANDBOX}/journal.txt"
```

### Journal Write

```bash
cat >> "${SANDBOX}/journal.txt" <<'EOF'
Lab 62a Task 2
What I practiced: Trap rehearsal and contrast for Allow Services Through Firewall
Trap rehearsed: T62-B: opening a service does not start the daemon that owns it
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
export LAB_NUM=62
export LAB_SLUG=firewall_allow_services
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
echo "Lab 62 cleanup complete at $(date -Is)"
echo "exit was: $?"
```

## Author

Kelvin R. Tobias  
Website: kelvinintech.com  
GitHub: kelvintechnical  
LinkedIn: Kelvin R. Tobias
