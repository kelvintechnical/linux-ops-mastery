# Lab 73b - Read PAM Module Documentation (Ansible)

## Lab Header Block

- ENV: RHEL-family Linux host or compatible lab VM
- OS: Linux
- USER: root-capable lab account with sudo
- TIMEBOX: 20-30 minutes
- PRACTICE DIRECTORY: `/srv`
- PRIMARY COMMANDS: `/usr/share/doc/pam-*/txts/`
- TRAPS: T73-A: minimal installs may not include PAM docs until packages are installed; T73-B: module names and config file names are easy to confuse; T41 destroy-restore; T44 cleanup safety

This lab's practice directory is: `/srv`.

## Lab-Wide Setup - Tier B Sandbox

Run this before Task 1.

```bash
export LAB_NUM=73
export LAB_SLUG=pam_module_docs
export SANDBOX=/tmp/labsandbox_${LAB_NUM}
export GROUP=labgrp_${LAB_NUM}_${LAB_SLUG}
export USER=labuser_${LAB_NUM}_${LAB_SLUG}
export USER_HOME=${SANDBOX}/home_${USER}

mkdir -p "${SANDBOX}" "${USER_HOME}"
getent group  "${GROUP}" >/dev/null || groupadd "${GROUP}"
getent passwd "${USER}"  >/dev/null || useradd -d "${USER_HOME}" -M -s /bin/bash -g "${GROUP}" "${USER}"
chown -R "${USER}:${GROUP}" "${SANDBOX}"
cat > "${SANDBOX}/THIS_DIRECTORY.txt" <<'EOF'
Practice directory: /srv
Data served by network services belongs here by convention, including web, FTP, and git service data.
EOF
id "${USER}"
ls -ld "${SANDBOX}" "${USER_HOME}" /srv
echo "Sandbox built by $(whoami) at $(date -Is)"
echo "exit was: $?"
```

## Task 1 - Ansible equivalent for Read PAM Module Documentation

### Warm-Up Rotation

```bash
pwd
ls -ld /srv
test -e /srv && echo "practice directory exists"
printf 'lab 73b task 1 warm-up at %s
' "$(date -Is)" | tee "${SANDBOX}/warmup-b1.txt"
```

### WEAVE TRACE

```bash
whoami
id "${USER}"
sudo -u "${USER}" bash -lc 'whoami; pwd; echo weave-ok'
ls -ld "${SANDBOX}" /srv
```

### Purpose

Ansible equivalent for Read PAM Module Documentation. This task connects `ansible.builtin.copy / ansible.builtin.lineinfile boundary pattern` to a repeatable artifact in `${SANDBOX}`.

### Main Command Block

```bash
cat > "${SANDBOX}/lab-73b.yml" <<'EOF'
---
- name: Lab 73b Task 1 - Read PAM Module Documentation
  hosts: localhost
  connection: local
  gather_facts: false
  tasks:
    - name: Stage PAM example safely
      ansible.builtin.copy:
        dest: /tmp/lab-pam-example.conf
        content: '# Review before installing into /etc/pam.d\n'
        mode: '0644'
EOF
ansible-playbook --check --diff "${SANDBOX}/lab-73b.yml" | tee "${SANDBOX}/ansible-check.txt"
ls -ld /srv | tee -a "${SANDBOX}/task-1-practice.txt"
test -e /srv && echo "/srv checked again" | tee -a "${SANDBOX}/task-1-practice.txt"
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

The Ansible tier uses `ansible.builtin.copy / ansible.builtin.lineinfile boundary pattern` or an honest boundary pattern when no safe dedicated module exists.

### Expected Output

The playbook runs in check/diff mode first so intended change is visible before applying it.

### Switches And Repetition Table

| Switch / Command | Meaning | Why it matters |
|---|---|---|
| `ansible.builtin.copy` | Practice token for this lab | Repeat it until recognition is automatic |
| `/` | Practice token for this lab | Repeat it until recognition is automatic |
| `ansible.builtin.lineinfile` | Practice token for this lab | Repeat it until recognition is automatic |
| `boundary` | Practice token for this lab | Repeat it until recognition is automatic |
| `pattern` | Practice token for this lab | Repeat it until recognition is automatic |

### Concept Card

| Concept | Answer |
|---|---|
| Command family | `ansible.builtin.copy / ansible.builtin.lineinfile boundary pattern` |
| Practice directory | `/srv` |
| Evidence directory | `${SANDBOX}` |
| Trap risk | T73-A: minimal installs may not include PAM docs until packages are installed |
| Recovery phrase | Stop, restore the saved state, then verify before continuing |

### PERSISTENCE CHECK

```bash
ls -l "${SANDBOX}"
test -s "${SANDBOX}/task-1-exit.txt"
printf 'Persistence check 73b task 1: PASS
' | tee -a "${SANDBOX}/journal.txt"
```

### Journal Write

```bash
cat >> "${SANDBOX}/journal.txt" <<'EOF'
Lab 73b Task 1
What I practiced: Ansible equivalent for Read PAM Module Documentation
Trap rehearsed: T73-A: minimal installs may not include PAM docs until packages are installed
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

## Task 2 - Ansible trap rehearsal for Read PAM Module Documentation

### Warm-Up Rotation

```bash
pwd
ls -ld /srv
test -e /srv && echo "practice directory exists"
printf 'lab 73b task 2 warm-up at %s
' "$(date -Is)" | tee "${SANDBOX}/warmup-b2.txt"
```

### WEAVE TRACE

```bash
whoami
id "${USER}"
sudo -u "${USER}" bash -lc 'whoami; pwd; echo weave-ok'
ls -ld "${SANDBOX}" /srv
```

### Purpose

Ansible trap rehearsal for Read PAM Module Documentation. This task connects `ansible.builtin.copy / ansible.builtin.lineinfile boundary pattern` to a repeatable artifact in `${SANDBOX}`.

### Main Command Block

```bash
ansible-playbook "${SANDBOX}/lab-73b.yml" | tee "${SANDBOX}/ansible-apply.txt"
ansible localhost -m ansible.builtin.command -a "true" -c local | tee "${SANDBOX}/ansible-smoke.txt"
ls -ld /srv | tee -a "${SANDBOX}/task-2-practice.txt"
test -e /srv && echo "/srv checked again" | tee -a "${SANDBOX}/task-2-practice.txt"
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
| `ansible.builtin.copy` | Practice token for this lab | Repeat it until recognition is automatic |
| `/` | Practice token for this lab | Repeat it until recognition is automatic |
| `ansible.builtin.lineinfile` | Practice token for this lab | Repeat it until recognition is automatic |
| `boundary` | Practice token for this lab | Repeat it until recognition is automatic |
| `pattern` | Practice token for this lab | Repeat it until recognition is automatic |

### Concept Card

| Concept | Answer |
|---|---|
| Command family | `ansible.builtin.copy / ansible.builtin.lineinfile boundary pattern` |
| Practice directory | `/srv` |
| Evidence directory | `${SANDBOX}` |
| Trap risk | T73-B: module names and config file names are easy to confuse |
| Recovery phrase | Stop, restore the saved state, then verify before continuing |

### PERSISTENCE CHECK

```bash
ls -l "${SANDBOX}"
test -s "${SANDBOX}/task-2-exit.txt"
printf 'Persistence check 73b task 2: PASS
' | tee -a "${SANDBOX}/journal.txt"
```

### Journal Write

```bash
cat >> "${SANDBOX}/journal.txt" <<'EOF'
Lab 73b Task 2
What I practiced: Ansible trap rehearsal for Read PAM Module Documentation
Trap rehearsed: T73-B: module names and config file names are easy to confuse
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
export LAB_NUM=73
export LAB_SLUG=pam_module_docs
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
echo "Lab 73 cleanup complete at $(date -Is)"
echo "exit was: $?"
```

## Author

Kelvin R. Tobias  
Website: kelvinintech.com  
GitHub: kelvintechnical  
LinkedIn: Kelvin R. Tobias
