# Lab 28b: Exploring Manual Pages (Ansible) — Boundary Artifact for Trap Practice

- **Series:** linux-ops-mastery — Documentation & Networking
- **Trilogy:** [`28a`](../lab-28a-man-pages-rhcsa/) → **`28b`** (Ansible — you are here) → [`28c`](../lab-28c-man-pages-verify/)
- **Career arcs covered:** RHCE EX294 (declarative package state + assertions), SRE (baseline host documentation availability checks)
- **Time Estimate:** 25–35 minutes
- **Tasks:** 2 (Task 1 = declarative install of man tooling; Task 2 = assertions that `/usr/share/man` content exists)
- **Practice Directory (rotation slot):** `/dev` (read-only context checks)
- **Playbooks:** `/root/rhcsa_journal/lab-28b/playbooks/`
- **Sandbox (Tier B):** `/tmp/lab28b` with `USER=labuser_28_man`, `GROUP=labgrp_28_man`
- **Traps rehearsed:** **T28-B** (missing man pages on minimal images) · **T41** (can you rebuild after wipe?) · **T44** (closeout discipline)

> **Section 18 boundary note:** manual-page navigation itself is a shell/pager skill. This b-lab is intentionally kept as a trap-rehearsal artifact to practice declarative remediation (`ansible.builtin.dnf`) and validation, not to replace interactive `man` usage.

---

## LAB HEADER BLOCK

```bash
ansible --version | head -n 3
ansible localhost -m ping --connection=local
ls -ld /dev
echo "exit was: $?"
```

---

## Lab-Wide Setup (Tier B)

```bash
sudo -i

export LAB_NUM=28
export LAB_SLUG=man
export SANDBOX=/tmp/lab28b
export GROUP=labgrp_${LAB_NUM}_${LAB_SLUG}
export USER=labuser_${LAB_NUM}_${LAB_SLUG}
export USER_HOME=${SANDBOX}/home_${USER}

mkdir -p "${SANDBOX}" "${USER_HOME}"
mkdir -p /root/rhcsa_journal/lab-28b/task1 /root/rhcsa_journal/lab-28b/task2
mkdir -p /root/rhcsa_journal/lab-28b/playbooks

getent group  "${GROUP}" >/dev/null || groupadd "${GROUP}"
getent passwd "${USER}"  >/dev/null || useradd -d "${USER_HOME}" -M -s /bin/bash -g "${GROUP}" "${USER}"
chown -R "${USER}:${GROUP}" "${SANDBOX}"
echo "exit was: $?"
```

---

## Task 1 — Declarative man environment via `ansible.builtin.dnf`

### Main command block

```bash
TASKLOG=/tmp/lab28b/task1.txt
PB=/root/rhcsa_journal/lab-28b/playbooks/task1.yml

cat > "${PB}" << 'PLAYBOOK'
---
- name: "Lab 28b Task 1 — Ensure man infrastructure exists"
  hosts: localhost
  connection: local
  gather_facts: false

  tasks:
    - name: "Ensure man packages present (T28-B prevention)"
      ansible.builtin.dnf:
        name:
          - man-db
          - man-pages
          - man-pages-extra
        state: present
      register: dnf_result

    - name: "Show package task result"
      ansible.builtin.debug:
        msg:
          - "changed={{ dnf_result.changed }}"
          - "results={{ dnf_result.results | default([]) }}"

    - name: "Check /dev still accessible (rotation slot context)"
      ansible.builtin.shell: "ls -ld /dev"
      register: dev_result
      changed_when: false

    - name: "Display /dev check"
      ansible.builtin.debug:
        msg: "{{ dev_result.stdout }}"
PLAYBOOK

echo "═══ check/diff ═══"                                  2>&1 | tee "${TASKLOG}"
ansible-playbook --check --diff "${PB}"                   2>&1 | tee -a "${TASKLOG}"
echo "═══ apply ═══"                                      | tee -a "${TASKLOG}"
ansible-playbook "${PB}"                                  2>&1 | tee -a "${TASKLOG}"
echo "═══ re-apply (idempotence) ═══"                     | tee -a "${TASKLOG}"
ansible-playbook "${PB}"                                  2>&1 | tee -a "${TASKLOG}"

echo "exit was: $?"
```

### Journal write

```bash
LAB=lab-28b
TASK=task1
JDIR="/root/rhcsa_journal/${LAB}/${TASK}"
mkdir -p "${JDIR}"
cp /tmp/lab28b/task1.txt "${JDIR}/evidence.txt"
cp "${PB}" "${JDIR}/task1.yml"
echo "exit was: $?"
```

---

## Task 2 — Assert man path content exists (`/usr/share/man`)

### Main command block

```bash
TASKLOG=/tmp/lab28b/task2.txt
PB=/root/rhcsa_journal/lab-28b/playbooks/task2.yml

cat > "${PB}" << 'PLAYBOOK'
---
- name: "Lab 28b Task 2 — Validate man content paths"
  hosts: localhost
  connection: local
  gather_facts: false

  tasks:
    - name: "Stat core man directories"
      ansible.builtin.stat:
        path: "{{ item }}"
      loop:
        - /usr/share/man
        - /usr/share/man/man1
        - /usr/share/man/man5
      register: man_stats

    - name: "Assert all core man paths exist"
      ansible.builtin.assert:
        that:
          - item.stat.exists
          - item.stat.isdir
        fail_msg: "T28-B hit: missing man content path {{ item.stat.path | default('unknown') }}"
        success_msg: "Path present: {{ item.stat.path }}"
      loop: "{{ man_stats.results }}"

    - name: "Count pages in man1 and man5"
      ansible.builtin.shell: |
        echo "man1_count=$(ls /usr/share/man/man1 2>/dev/null | wc -l)"
        echo "man5_count=$(ls /usr/share/man/man5 2>/dev/null | wc -l)"
        echo "manpath=$(man --path 2>/dev/null || true)"
      register: count_result
      changed_when: false

    - name: "Assert non-zero content present"
      ansible.builtin.assert:
        that:
          - "(count_result.stdout | regex_search('man1_count=([0-9]+)', '\\1') | first | int) > 0"
          - "(count_result.stdout | regex_search('man5_count=([0-9]+)', '\\1') | first | int) > 0"
        fail_msg: "T28-B hit: man section content not populated"
        success_msg: "man1/man5 both have page files"

    - name: "Show counters"
      ansible.builtin.debug:
        msg: "{{ count_result.stdout_lines }}"
PLAYBOOK

echo "═══ apply assertions ═══"                            2>&1 | tee "${TASKLOG}"
ansible-playbook "${PB}"                                   2>&1 | tee -a "${TASKLOG}"

echo "exit was: $?"
```

### Journal write

```bash
LAB=lab-28b
TASK=task2
JDIR="/root/rhcsa_journal/${LAB}/${TASK}"
mkdir -p "${JDIR}"
cp /tmp/lab28b/task2.txt "${JDIR}/evidence.txt"
cp "${PB}" "${JDIR}/task2.yml"
echo "exit was: $?"
```

---

## Lab Closeout (Section 6)

```bash
set +e
if getent passwd "${USER}" >/dev/null 2>&1; then userdel -r "${USER}" 2>/dev/null; fi
if getent group "${GROUP}" >/dev/null 2>&1; then groupdel "${GROUP}" 2>/dev/null; fi
rm -rf "${SANDBOX}" /tmp/lab28b

echo "── Lab 28b cleanup audit ──"
getent passwd "${USER}" >/dev/null && echo "❌ user remains"   || echo "✅ user gone"
getent group  "${GROUP}" >/dev/null && echo "❌ group remains"  || echo "✅ group gone"
test -d "${SANDBOX}"              && echo "❌ sandbox remains" || echo "✅ sandbox gone"
test -d /tmp/lab28b               && echo "❌ /tmp/lab28b remains" || echo "✅ /tmp/lab28b gone"
set -e
```

> **T44 check:** end closeout only after four `✅` audit lines.

---

## Author

**Kelvin R. Tobias**  
[kelvinintech.com](https://kelvinintech.com) · [GitHub](https://github.com/kelvintechnical) · [LinkedIn](https://www.linkedin.com/in/kelvin-r-tobias-211949219)
