# Lab 53b: Removing ACLs via Ansible — `ansible.posix.acl` `state: absent`

- **Series:** linux-ops-mastery — Permissions, ACLs, and Ownership
- **Trilogy:** `53a` (RHCSA) -> `53b` (Ansible) -> `53c` (Verify)
- **Topic:** Declarative ACL removal and post-task assertions
- **Prerequisite:** Lab 53a completed, Lab 00 (Ansible control-node setup)
- **Time Estimate:** 25-35 minutes
- **Tasks:** 2 (Task 1 remove ACL entries declaratively, Task 2 trap-proof assertions)
- **Practice Directory:** `/media`
- **Sandbox (Tier B):** `/tmp/lab53b`, `USER=labuser_53_aclrm`, `GROUP=labgrp_53_aclrm`
- **Playbooks path:** `/root/rhcsa_journal/lab-53b/playbooks`
- **Traps rehearsed this lab:** **T53-A** (specific removal != full ACL cleanup) · **T53-B** (`-k`-style default removal does not erase explicit ACLs) · **T41** · **T44**

> This lab's practice directory is `/media`, while playbook fixtures and cleanup drills run in `/tmp/lab53b`.

---

## LAB HEADER BLOCK

```bash
echo "ENV:   ${ENV:-DECLARE_ME}"
echo "OS:    $(cat /etc/redhat-release 2>/dev/null || grep PRETTY_NAME /etc/os-release)"
echo "TIME:  $(date -Is)"
echo "USER:  $(whoami)@$(hostname)"
echo "TRAPS: T53-A T53-B T41 T44"
echo "PRACTICE DIR: /media"
ansible --version | head -n 2
ansible-galaxy collection list | grep -E '^ansible\.posix' || true
```

> STOP - if Ansible is missing, return to Lab 00 before Task 1.

---

## Objective

Use Ansible to remove ACL entries with the same precision as hand-typed `setfacl`, then prove the end state with machine-checkable assertions.

---

## Concept: Declarative ACL cleanup

`ansible.posix.acl` with `state: absent` declares what ACL entries should not exist.  
Your verification still matters: removing one entry is not the same as removing all extended ACL metadata.

---

## Lab-Wide Setup (Tier B)

```bash
sudo -i

export SANDBOX=/tmp/lab53b
export GROUP=labgrp_53_aclrm
export USER=labuser_53_aclrm
export USER_HOME=${SANDBOX}/home_${USER}
export TARGET_FILE=${SANDBOX}/acl-remove.txt
export TARGET_DIR=${SANDBOX}/acl-dir

mkdir -p "${SANDBOX}" "${USER_HOME}" "${TARGET_DIR}" /root/rhcsa_journal/lab-53b/playbooks /root/rhcsa_journal/lab-53b/task1 /root/rhcsa_journal/lab-53b/task2
getent group "${GROUP}" >/dev/null || groupadd "${GROUP}"
getent passwd "${USER}" >/dev/null || useradd -d "${USER_HOME}" -M -s /bin/bash -g "${GROUP}" "${USER}"
chown -R "${USER}:${GROUP}" "${SANDBOX}"

echo "acl ansible fixture" > "${TARGET_FILE}"
chown "${USER}:${GROUP}" "${TARGET_FILE}"
chmod 640 "${TARGET_FILE}"

# Seed explicit and default ACLs so removal task has real work
setfacl -m u:${USER}:rwx,u:other:rw "${TARGET_FILE}"
setfacl -m d:u:${USER}:rwx "${TARGET_DIR}"
setfacl -m u:${USER}:rwx "${TARGET_DIR}"

getfacl "${TARGET_FILE}"
getfacl "${TARGET_DIR}"
```

---

## Task 1 - Remove ACL entries declaratively (`state: absent`)

### Purpose

Use `ansible.posix.acl` to remove:
- the specific named ACL on `${TARGET_FILE}` (`user:other`)
- the default ACL on `${TARGET_DIR}` (default named user)

### Playbook (`/root/rhcsa_journal/lab-53b/playbooks/task1.yml`)

```yaml
---
- name: "Lab 53b Task 1 - declarative ACL removal"
  hosts: localhost
  connection: local
  gather_facts: false

  vars:
    target_file: /tmp/lab53b/acl-remove.txt
    target_dir: /tmp/lab53b/acl-dir

  tasks:
    - name: "Remove specific named ACL user entry (user:other) from file"
      ansible.posix.acl:
        path: "{{ target_file }}"
        etype: user
        entity: other
        state: absent

    - name: "Remove default ACL entry from directory only"
      ansible.posix.acl:
        path: "{{ target_dir }}"
        etype: user
        entity: labuser_53_aclrm
        default: true
        state: absent
```

### Main command block

```bash
TASKLOG=/tmp/lab53b/task1.txt

ansible-playbook /root/rhcsa_journal/lab-53b/playbooks/task1.yml 2>&1 | tee "${TASKLOG}"
echo "== post-task getfacl file ==" | tee -a "${TASKLOG}"
getfacl "${TARGET_FILE}" | tee -a "${TASKLOG}"
echo "== post-task getfacl dir ==" | tee -a "${TASKLOG}"
getfacl "${TARGET_DIR}" | tee -a "${TASKLOG}"
echo "exit was: $?"
```

### Expected verification

- `${TARGET_FILE}` no longer contains `user:other`.
- `${TARGET_DIR}` no longer contains the corresponding `default:` entry.
- Explicit ACL entries on `${TARGET_DIR}` can still remain (this is the `-k`/T53-B concept).

---

## Task 2 - Trap-proof assertion checks

### Purpose

Fail fast if ACL state is wrong:

1. Confirm targeted entries are absent.
2. Confirm explicit ACLs were not unintentionally removed when only default ACL cleanup was requested.

### Main command block

```bash
TASKLOG=/tmp/lab53b/task2.txt

echo "== assertion checks ==" | tee "${TASKLOG}"

# Assertion A: file-specific named user removed
if getfacl "${TARGET_FILE}" | grep -q '^user:other:'; then
  echo "FAIL: user:other still present on file" | tee -a "${TASKLOG}"
  exit 1
else
  echo "OK: user:other removed from file" | tee -a "${TASKLOG}"
fi

# Assertion B: default ACL removed from dir
if getfacl "${TARGET_DIR}" | grep -q '^default:user:labuser_53_aclrm:'; then
  echo "FAIL: default ACL still present on dir" | tee -a "${TASKLOG}"
  exit 1
else
  echo "OK: default ACL removed from dir" | tee -a "${TASKLOG}"
fi

# Assertion C: explicit ACL remains (T53-B distinction)
if getfacl "${TARGET_DIR}" | grep -q '^user:labuser_53_aclrm:'; then
  echo "OK: explicit ACL remains (default-only removal behavior confirmed)" | tee -a "${TASKLOG}"
else
  echo "FAIL: explicit ACL unexpectedly removed" | tee -a "${TASKLOG}"
  exit 1
fi

echo "exit was: $?"
```

### Journal write

```bash
mkdir -p /root/rhcsa_journal/lab-53b/task1 /root/rhcsa_journal/lab-53b/task2
cp /tmp/lab53b/task1.txt /root/rhcsa_journal/lab-53b/task1/evidence.txt
cp /tmp/lab53b/task2.txt /root/rhcsa_journal/lab-53b/task2/evidence.txt
cat > /root/rhcsa_journal/lab-53b/task2/done.txt <<EOF
LAB: lab-53b
TASK: task2
DATE: $(date -Is)
STATUS: COMPLETE
EOF
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

echo "-- lab-53b cleanup audit --"
getent passwd "${USER}" >/dev/null && echo "FAIL user remains" || echo "OK user gone"
getent group  "${GROUP}" >/dev/null && echo "FAIL group remains" || echo "OK group gone"
test -d "${SANDBOX}" && echo "FAIL sandbox remains" || echo "OK sandbox gone"

set -e
```

---

## Checklist

- [ ] Task 1 used `ansible.posix.acl` with `state: absent`
- [ ] Task 2 assertions proved targeted entries were removed
- [ ] Task 2 confirmed default-only removal does not erase explicit ACLs (T53-B)
- [ ] Section 6 closeout audit returned all `OK`

---

## Author

**Kelvin R. Tobias**
