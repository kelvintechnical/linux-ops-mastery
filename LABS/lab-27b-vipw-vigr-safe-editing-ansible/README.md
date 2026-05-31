# Lab 27b: Safely Editing System Databases (Ansible) - `ansible.builtin.user`, `ansible.builtin.group`

- **Series:** linux-ops-mastery - Text File Management
- **Trilogy:** `27a` (RHCSA) -> `27b` (Ansible) -> `27c` (Verify)
- **Prerequisite:** Lab 27a complete
- **Time Estimate:** 30-40 minutes
- **Tasks:** 2 (Task 1 = declarative user/group management with check+diff, Task 2 = trap proof that `lineinfile` on `/etc/passwd` is wrong)
- **Practice Directory (rotation #27):** `/srv`
- **Sandbox (Tier B):** `/tmp/lab27b` with `USER=labuser_27_vipw`, `GROUP=labgrp_27_vipw`
- **Traps rehearsed this lab:** **T27-B** (editing passwd/group without shadow parity) ; **T41** ; **T44**

> **This lab's practice directory is: `/srv`**. Ansible artifacts are staged under `/root/rhcsa_journal/lab-27b/`.

---

## Objective

Use Ansible as the idempotent, lock-safe equivalent of `vipw`/`vigr`. You will declare user/group state with dedicated modules, validate behavior in `--check --diff`, then prove why direct text edits (`lineinfile` on `/etc/passwd`) are unsafe and non-portable.

---

## Reference Mapping

| RHCSA edit path | Ansible-safe path |
|---|---|
| `vipw` + `vipw -s` | `ansible.builtin.user` |
| `vigr` + `vigr -s` | `ansible.builtin.group` |
| direct file hacks | avoid; use modules that respect account semantics |

---

## Lab-Wide Setup - Tier B + playbook workspace

```bash
sudo -i

export LAB_NUM=27
export LAB_SLUG=vipw
export SANDBOX=/tmp/lab27b
export GROUP=labgrp_${LAB_NUM}_${LAB_SLUG}
export USER=labuser_${LAB_NUM}_${LAB_SLUG}
export USER_HOME=${SANDBOX}/home_${USER}

mkdir -p "${SANDBOX}" "${USER_HOME}"
mkdir -p /root/rhcsa_journal/lab-27b/{task1,task2,playbooks}
cd /root/rhcsa_journal/lab-27b

ansible --version | head -n 1
echo "exit was: $?"
```

---

## Task 1 - Idempotent user/group declaration (`--check --diff`)

**Practice directory this task:** `/srv` (state declaration targets account DBs)

### Warm-Up

```bash
ansible localhost -m ansible.builtin.ping
getent passwd "${USER}" || true
getent group "${GROUP}" || true
echo "Warm-up at $(date -Is)"
```

### Purpose

Create a playbook that manages group then user declaratively, run in dry-run mode first, then apply for real, then re-run to prove idempotence.

### Playbook - `/root/rhcsa_journal/lab-27b/playbooks/task1.yml`

```yaml
---
- name: Lab 27b Task 1 - declarative account state
  hosts: localhost
  become: true
  gather_facts: false
  vars:
    lab_group: "labgrp_27_vipw"
    lab_user: "labuser_27_vipw"
    sandbox: "/tmp/lab27b"
    lab_home: "/tmp/lab27b/home_labuser_27_vipw"
  tasks:
    - name: Ensure sandbox exists
      ansible.builtin.file:
        path: "{{ sandbox }}"
        state: directory
        mode: "0755"

    - name: Ensure lab group exists
      ansible.builtin.group:
        name: "{{ lab_group }}"
        state: present

    - name: Ensure lab user exists
      ansible.builtin.user:
        name: "{{ lab_user }}"
        group: "{{ lab_group }}"
        home: "{{ lab_home }}"
        create_home: false
        shell: /bin/bash
        state: present

    - name: Ensure user home path exists under sandbox
      ansible.builtin.file:
        path: "{{ lab_home }}"
        state: directory
        owner: "{{ lab_user }}"
        group: "{{ lab_group }}"
        mode: "0755"
```

### Run sequence

```bash
set -o pipefail

ansible-playbook /root/rhcsa_journal/lab-27b/playbooks/task1.yml \
  --check --diff 2>&1 | tee /root/rhcsa_journal/lab-27b/task1/check-diff.txt

ansible-playbook /root/rhcsa_journal/lab-27b/playbooks/task1.yml \
  2>&1 | tee /root/rhcsa_journal/lab-27b/task1/apply.txt

ansible-playbook /root/rhcsa_journal/lab-27b/playbooks/task1.yml \
  2>&1 | tee /root/rhcsa_journal/lab-27b/task1/idempotent.txt

getent passwd "${USER}" | tee /root/rhcsa_journal/lab-27b/task1/getent-passwd.txt
getent group  "${GROUP}" | tee /root/rhcsa_journal/lab-27b/task1/getent-group.txt
getent shadow "${USER}"  | cut -d: -f1-2 | tee /root/rhcsa_journal/lab-27b/task1/getent-shadow.txt
getent gshadow "${GROUP}" | cut -d: -f1-2 | tee /root/rhcsa_journal/lab-27b/task1/getent-gshadow.txt
```

### Expected outcome

- first `--check --diff` predicts create/change actions
- first apply performs changes
- second apply reports `changed=0` (idempotent steady state)

### Journal write

```bash
LAB=lab-27b
TASK=task1
JDIR="/root/rhcsa_journal/${LAB}/${TASK}"
mkdir -p "${JDIR}"
cp /root/rhcsa_journal/lab-27b/task1/*.txt "${JDIR}/" 2>/dev/null || true

cat > "${JDIR}/done.txt" <<EOF
LAB:    ${LAB}
TASK:   ${TASK}
DATE:   $(date -Is)
STATUS: COMPLETE
EOF
```

---

## Task 2 - Trap T27-B: `lineinfile` on `/etc/passwd` is wrong

**Practice directory this task:** `/srv` (demonstration and corrected pattern)

### Warm-Up

```bash
ansible-doc ansible.builtin.user | head -n 20
ansible-doc ansible.builtin.lineinfile | head -n 20
echo "Warm-up at $(date -Is)"
```

### Purpose

Demonstrate policy: account DBs are not ordinary line-oriented text assets. Editing `/etc/passwd` with `lineinfile` can break field integrity and does not manage corresponding shadow state. Use `ansible.builtin.user` instead.

### Bad example (do not run against `/etc/passwd`)

```yaml
---
- name: WRONG pattern for account databases
  hosts: localhost
  become: true
  gather_facts: false
  tasks:
    - name: WRONG - lineinfile against /etc/passwd
      ansible.builtin.lineinfile:
        path: /etc/passwd
        line: "baduser:x:9999:9999::/tmp:/bin/bash"
```

### Correct replacement playbook - `/root/rhcsa_journal/lab-27b/playbooks/task2.yml`

```yaml
---
- name: Lab 27b Task 2 - safe corrective pattern
  hosts: localhost
  become: true
  gather_facts: false
  vars:
    lab_group: "labgrp_27_vipw"
    lab_user: "labuser_27_vipw"
    lab_home: "/tmp/lab27b/home_labuser_27_vipw"
  tasks:
    - name: Ensure group exists safely
      ansible.builtin.group:
        name: "{{ lab_group }}"
        state: present

    - name: Ensure user exists safely (handles shadow semantics)
      ansible.builtin.user:
        name: "{{ lab_user }}"
        group: "{{ lab_group }}"
        home: "{{ lab_home }}"
        create_home: false
        shell: /bin/bash
        state: present
```

### Run sequence

```bash
set -o pipefail

echo "Documenting trap T27-B; no direct passwd edits performed." \
  | tee /root/rhcsa_journal/lab-27b/task2/trap-note.txt

ansible-playbook /root/rhcsa_journal/lab-27b/playbooks/task2.yml \
  --check --diff 2>&1 | tee /root/rhcsa_journal/lab-27b/task2/check-diff.txt

ansible-playbook /root/rhcsa_journal/lab-27b/playbooks/task2.yml \
  2>&1 | tee /root/rhcsa_journal/lab-27b/task2/apply.txt

getent passwd "${USER}"  | tee /root/rhcsa_journal/lab-27b/task2/getent-passwd.txt
getent shadow "${USER}"  | cut -d: -f1-2 | tee /root/rhcsa_journal/lab-27b/task2/getent-shadow.txt
getent group  "${GROUP}" | tee /root/rhcsa_journal/lab-27b/task2/getent-group.txt
getent gshadow "${GROUP}" | cut -d: -f1-2 | tee /root/rhcsa_journal/lab-27b/task2/getent-gshadow.txt
```

### PERSISTENCE CHECK

| Check | Command |
|---|---|
| user resolves via NSS | `getent passwd ${USER}` |
| shadow entry exists | `getent shadow ${USER}` |
| group resolves | `getent group ${GROUP}` |
| gshadow entry exists | `getent gshadow ${GROUP}` |

### Journal write

```bash
LAB=lab-27b
TASK=task2
JDIR="/root/rhcsa_journal/${LAB}/${TASK}"
mkdir -p "${JDIR}"
cp /root/rhcsa_journal/lab-27b/task2/*.txt "${JDIR}/" 2>/dev/null || true

cat > "${JDIR}/done.txt" <<EOF
LAB:    ${LAB}
TASK:   ${TASK}
DATE:   $(date -Is)
STATUS: COMPLETE
EOF
```

---

## Lab Closeout - Bulletproof Teardown (Section 6)

```bash
set +e

if getent passwd "${USER}" >/dev/null 2>&1; then
  userdel -r "${USER}" 2>/dev/null
fi
if getent group "${GROUP}" >/dev/null 2>&1; then
  groupdel "${GROUP}" 2>/dev/null
fi

rm -rf "${SANDBOX}"

echo "-- Lab 27b cleanup audit --"
getent passwd "${USER}" >/dev/null && echo "FAIL user remains" || echo "PASS user gone"
getent group  "${GROUP}" >/dev/null && echo "FAIL group remains" || echo "PASS group gone"
test -d "${SANDBOX}" && echo "FAIL sandbox remains" || echo "PASS sandbox gone"
test -d "${USER_HOME}" && echo "FAIL home remains" || echo "PASS home gone"

set -e
echo "Cleanup complete at $(date -Is)"
```

---

## Lab 27b Checklist

- [ ] Task 1 playbook run with `--check --diff` and idempotent second apply
- [ ] Task 2 trap documented and corrected with `ansible.builtin.user` / `ansible.builtin.group`
- [ ] Section 6 closeout run with four PASS audit lines

---

## Related Labs

| Lab | Connection |
|---|---|
| Lab 27a | Imperative lock-aware editing with `vipw`/`vigr` |
| Lab 27c | State audit and destroy/restore validation |

---

## Author

**Kelvin R. Tobias**
