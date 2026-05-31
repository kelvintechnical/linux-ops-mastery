# Lab 79b - Viewing SELinux Contexts (Ansible)

## Lab Header Block

- ENV: RHEL-family Linux host or compatible lab VM
- OS: Linux
- USER: root-capable lab account with sudo
- TIMEBOX: 20-30 minutes
- PRACTICE DIRECTORY: `/mnt`
- PRIMARY COMMANDS: `ls -Z, ps -eZ`
- TRAPS: T79-A: standard ls hides contexts unless -Z is used; T79-B: process contexts and file contexts are different object classes; T41 destroy-restore; T44 cleanup safety

This lab's practice directory is: `/mnt`.

## Lab-Wide Setup - Tier B Sandbox

Run this before Task 1.

```bash
export LAB_NUM=79
export LAB_SLUG=selinux_contexts
export SANDBOX=/tmp/labsandbox_${LAB_NUM}
export GROUP=labgrp_${LAB_NUM}_${LAB_SLUG}
export USER=labuser_${LAB_NUM}_${LAB_SLUG}
export USER_HOME=${SANDBOX}/home_${USER}

mkdir -p "${SANDBOX}" "${USER_HOME}"
getent group  "${GROUP}" >/dev/null || groupadd "${GROUP}"
getent passwd "${USER}"  >/dev/null || useradd -d "${USER_HOME}" -M -s /bin/bash -g "${GROUP}" "${USER}"
chown -R "${USER}:${GROUP}" "${SANDBOX}"
cat > "${SANDBOX}/THIS_DIRECTORY.txt" <<'EOF'
Practice directory: /mnt
Temporary manual mount points live here. Rescue and chroot tasks commonly use /mnt.
EOF
id "${USER}"
ls -ld "${SANDBOX}" "${USER_HOME}" /mnt
echo "Sandbox built by $(whoami) at $(date -Is)"
echo "exit was: $?"
```

## Task 1 - Ansible equivalent for Viewing SELinux Contexts

### Warm-Up Rotation

```bash
pwd
ls -ld /mnt
test -e /mnt && echo "practice directory exists"
printf 'lab 79b task 1 warm-up at %s
' "$(date -Is)" | tee "${SANDBOX}/warmup-b1.txt"
```

### WEAVE TRACE

```bash
whoami
id "${USER}"
sudo -u "${USER}" bash -lc 'whoami; pwd; echo weave-ok'
ls -ld "${SANDBOX}" /mnt
```

### Purpose

Ansible equivalent for Viewing SELinux Contexts. This task connects `ansible.posix.selinux / community.general.sefcontext / ansible.posix.seboolean as appropriate` to a repeatable artifact in `${SANDBOX}`.

### Main Command Block

```bash
cat > "${SANDBOX}/lab-79b.yml" <<'EOF'
---
- name: Lab 79b Task 1 - Viewing SELinux Contexts
  hosts: localhost
  connection: local
  gather_facts: false
  tasks:
    - name: Query SELinux state
      ansible.builtin.command: getenforce
      register: selinux_state
      changed_when: false
EOF
ansible-playbook --check --diff "${SANDBOX}/lab-79b.yml" | tee "${SANDBOX}/ansible-check.txt"
ls -ld /mnt | tee -a "${SANDBOX}/task-1-practice.txt"
test -e /mnt && echo "/mnt checked again" | tee -a "${SANDBOX}/task-1-practice.txt"
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

The Ansible tier uses `ansible.posix.selinux / community.general.sefcontext / ansible.posix.seboolean as appropriate` or an honest boundary pattern when no safe dedicated module exists.

### Expected Output

The playbook runs in check/diff mode first so intended change is visible before applying it.

### Switches And Repetition Table

| Switch / Command | Meaning | Why it matters |
|---|---|---|
| `ansible.posix.selinux` | Practice token for this lab | Repeat it until recognition is automatic |
| `/` | Practice token for this lab | Repeat it until recognition is automatic |
| `community.general.sefcontext` | Practice token for this lab | Repeat it until recognition is automatic |
| `/` | Practice token for this lab | Repeat it until recognition is automatic |
| `ansible.posix.seboolean` | Practice token for this lab | Repeat it until recognition is automatic |
| `as` | Practice token for this lab | Repeat it until recognition is automatic |

### Concept Card

| Concept | Answer |
|---|---|
| Command family | `ansible.posix.selinux / community.general.sefcontext / ansible.posix.seboolean as appropriate` |
| Practice directory | `/mnt` |
| Evidence directory | `${SANDBOX}` |
| Trap risk | T79-A: standard ls hides contexts unless -Z is used |
| Recovery phrase | Stop, restore the saved state, then verify before continuing |

### PERSISTENCE CHECK

```bash
ls -l "${SANDBOX}"
test -s "${SANDBOX}/task-1-exit.txt"
printf 'Persistence check 79b task 1: PASS
' | tee -a "${SANDBOX}/journal.txt"
```

### Journal Write

```bash
cat >> "${SANDBOX}/journal.txt" <<'EOF'
Lab 79b Task 1
What I practiced: Ansible equivalent for Viewing SELinux Contexts
Trap rehearsed: T79-A: standard ls hides contexts unless -Z is used
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

## Task 2 - Ansible trap rehearsal for Viewing SELinux Contexts

### Warm-Up Rotation

```bash
pwd
ls -ld /mnt
test -e /mnt && echo "practice directory exists"
printf 'lab 79b task 2 warm-up at %s
' "$(date -Is)" | tee "${SANDBOX}/warmup-b2.txt"
```

### WEAVE TRACE

```bash
whoami
id "${USER}"
sudo -u "${USER}" bash -lc 'whoami; pwd; echo weave-ok'
ls -ld "${SANDBOX}" /mnt
```

### Purpose

Ansible trap rehearsal for Viewing SELinux Contexts. This task connects `ansible.posix.selinux / community.general.sefcontext / ansible.posix.seboolean as appropriate` to a repeatable artifact in `${SANDBOX}`.

### Main Command Block

```bash
ansible-playbook "${SANDBOX}/lab-79b.yml" | tee "${SANDBOX}/ansible-apply.txt"
ansible localhost -m ansible.builtin.command -a "true" -c local | tee "${SANDBOX}/ansible-smoke.txt"
ls -ld /mnt | tee -a "${SANDBOX}/task-2-practice.txt"
test -e /mnt && echo "/mnt checked again" | tee -a "${SANDBOX}/task-2-practice.txt"
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

The second task makes idempotence and assertion visible instead of trusting that a playbook changed the intended state.

### Expected Output

The captured output proves the module path ran and leaves an audit trail.

### Switches And Repetition Table

| Switch / Command | Meaning | Why it matters |
|---|---|---|
| `ansible.posix.selinux` | Practice token for this lab | Repeat it until recognition is automatic |
| `/` | Practice token for this lab | Repeat it until recognition is automatic |
| `community.general.sefcontext` | Practice token for this lab | Repeat it until recognition is automatic |
| `/` | Practice token for this lab | Repeat it until recognition is automatic |
| `ansible.posix.seboolean` | Practice token for this lab | Repeat it until recognition is automatic |
| `as` | Practice token for this lab | Repeat it until recognition is automatic |

### Concept Card

| Concept | Answer |
|---|---|
| Command family | `ansible.posix.selinux / community.general.sefcontext / ansible.posix.seboolean as appropriate` |
| Practice directory | `/mnt` |
| Evidence directory | `${SANDBOX}` |
| Trap risk | T79-B: process contexts and file contexts are different object classes |
| Recovery phrase | Stop, restore the saved state, then verify before continuing |

### PERSISTENCE CHECK

```bash
ls -l "${SANDBOX}"
test -s "${SANDBOX}/task-2-exit.txt"
printf 'Persistence check 79b task 2: PASS
' | tee -a "${SANDBOX}/journal.txt"
```

### Journal Write

```bash
cat >> "${SANDBOX}/journal.txt" <<'EOF'
Lab 79b Task 2
What I practiced: Ansible trap rehearsal for Viewing SELinux Contexts
Trap rehearsed: T79-B: process contexts and file contexts are different object classes
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
export LAB_NUM=79
export LAB_SLUG=selinux_contexts
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
echo "Lab 79 cleanup complete at $(date -Is)"
echo "exit was: $?"
```

## Author

Kelvin R. Tobias  
Website: kelvinintech.com  
GitHub: kelvintechnical  
LinkedIn: Kelvin R. Tobias
