# Lab 28c: Verifying Manual Page Workflow (Capstone) — Audit + Destroy-Restore

- **Series:** linux-ops-mastery — Documentation & Networking
- **Trilogy:** [`28a`](../lab-28a-man-pages-rhcsa/) → [`28b`](../lab-28b-man-pages-ansible/) → **`28c`**
- **Time Estimate:** 25–35 minutes
- **Tasks:** 2 (Task 1 = audit man tooling/state + section evidence; Task 2 = destroy-restore by uninstall/reinstall using journal playbooks)
- **Practice Directory (rotation slot):** `/dev` (read-only checks)
- **Sandbox (Tier B):** `/tmp/lab28c` with `USER=labuser_28_man`, `GROUP=labgrp_28_man`
- **Traps rehearsed:** **T28-A** (section confusion) · **T28-B** (missing man packages) · **T41** (destroy-restore discipline) · **T44** (closeout audit discipline)

---

## LAB HEADER BLOCK

```bash
ls -la /root/rhcsa_journal/lab-28a/ /root/rhcsa_journal/lab-28b/
ls -ld /dev
man --path 2>/dev/null || true
echo "exit was: $?"
```

---

## Lab-Wide Setup (Tier B)

```bash
sudo -i

export LAB_NUM=28
export LAB_SLUG=man
export SANDBOX=/tmp/lab28c
export GROUP=labgrp_${LAB_NUM}_${LAB_SLUG}
export USER=labuser_${LAB_NUM}_${LAB_SLUG}
export USER_HOME=${SANDBOX}/home_${USER}

mkdir -p "${SANDBOX}" "${USER_HOME}"
mkdir -p /root/rhcsa_journal/lab-28c/task1 /root/rhcsa_journal/lab-28c/task2

getent group  "${GROUP}" >/dev/null || groupadd "${GROUP}"
getent passwd "${USER}"  >/dev/null || useradd -d "${USER_HOME}" -M -s /bin/bash -g "${GROUP}" "${USER}"
chown -R "${USER}:${GROUP}" "${SANDBOX}"
echo "exit was: $?"
```

---

## Task 1 — Audit man pages, sections, and journal artifacts

### Main command block

```bash
TASKLOG=/tmp/lab28c/task1.txt

echo "═══ Part A: completeness audit ═══"                       2>&1 | tee "${TASKLOG}"
EXPECTED=(
  /root/rhcsa_journal/lab-28a/task1/evidence.txt
  /root/rhcsa_journal/lab-28a/task2/evidence.txt
  /root/rhcsa_journal/lab-28b/task1/task1.yml
  /root/rhcsa_journal/lab-28b/task2/task2.yml
)
M=0
for f in "${EXPECTED[@]}"; do
  test -s "$f" && echo "✅ $f" || { echo "❌ $f"; M=$((M+1)); }
done                                                           | tee -a "${TASKLOG}"
echo "missing=${M}"                                            | tee -a "${TASKLOG}"

echo "═══ Part B: package and file evidence ═══"               | tee -a "${TASKLOG}"
rpm -q man-db man-pages man-pages-extra                        | tee -a "${TASKLOG}" || true
rpm -ql man-pages | head -n 30                                 | tee -a "${TASKLOG}" || true
rpm -ql man-pages | rg '/man[1-9]/' -n | head -n 20            | tee -a "${TASKLOG}" || true

echo "═══ Part C: section checks (T28-A) ═══"                  | tee -a "${TASKLOG}"
man -P cat 1 passwd | head -n 10                               | tee -a "${TASKLOG}"
man -P cat 5 passwd | head -n 10                               | tee -a "${TASKLOG}"
man -P cat 8 useradd | head -n 10                              | tee -a "${TASKLOG}" || true

echo "═══ Part D: path checks (T28-B prevention) ═══"          | tee -a "${TASKLOG}"
man --path                                                     | tee -a "${TASKLOG}" || true
ls -ld /usr/share/man /usr/share/man/man1 /usr/share/man/man5  | tee -a "${TASKLOG}"
ls -ld /dev                                                    | tee -a "${TASKLOG}"

echo "exit was: $?"
```

### Journal write

```bash
LAB=lab-28c
TASK=task1
JDIR="/root/rhcsa_journal/${LAB}/${TASK}"
mkdir -p "${JDIR}"
cp /tmp/lab28c/task1.txt "${JDIR}/evidence.txt"
echo "exit was: $?"
```

---

## Task 2 — Destroy-restore drill (T41): uninstall + reinstall from journal playbook

### Main command block

```bash
TASKLOG=/tmp/lab28c/task2.txt
PB=/root/rhcsa_journal/lab-28c/task2/restore-man.yml

echo "═══ Part A: snapshot ═══"                                2>&1 | tee "${TASKLOG}"
rpm -q man-db man-pages man-pages-extra                        | tee -a "${TASKLOG}" || true
man --path                                                     | tee -a "${TASKLOG}" || true

echo "═══ Part B: destroy (remove packages) ═══"               | tee -a "${TASKLOG}"
dnf remove -y man-pages-extra man-pages man-db                 | tee -a "${TASKLOG}" || true
command -v man >/dev/null && echo "man command still present"  | tee -a "${TASKLOG}" || true

echo "═══ Part C: restore playbook from journal ═══"           | tee -a "${TASKLOG}"
cat > "${PB}" << 'PLAYBOOK'
---
- name: "Lab 28c Task 2 — Restore manual page tooling"
  hosts: localhost
  connection: local
  gather_facts: false

  tasks:
    - name: "Restore man packages"
      ansible.builtin.dnf:
        name:
          - man-db
          - man-pages
          - man-pages-extra
        state: present

    - name: "Verify core man paths exist"
      ansible.builtin.stat:
        path: "{{ item }}"
      loop:
        - /usr/share/man
        - /usr/share/man/man1
        - /usr/share/man/man5
      register: st

    - name: "Assert restored paths"
      ansible.builtin.assert:
        that:
          - item.stat.exists
          - item.stat.isdir
      loop: "{{ st.results }}"
PLAYBOOK

ansible-playbook "${PB}"                                        | tee -a "${TASKLOG}"

echo "═══ Part D: post-restore verify ═══"                      | tee -a "${TASKLOG}"
rpm -q man-db man-pages man-pages-extra                         | tee -a "${TASKLOG}"
man --path                                                      | tee -a "${TASKLOG}"
man -P cat 5 passwd | head -n 8                                | tee -a "${TASKLOG}"
echo "✅ T41 destroy-restore complete for man environment"      | tee -a "${TASKLOG}"

echo "exit was: $?"
```

### Journal write

```bash
LAB=lab-28c
TASK=task2
JDIR="/root/rhcsa_journal/${LAB}/${TASK}"
mkdir -p "${JDIR}"
cp /tmp/lab28c/task2.txt "${JDIR}/evidence.txt"
cp "${PB}" "${JDIR}/restore-man.yml"
echo "exit was: $?"
```

---

## Lab Closeout (Section 6)

```bash
set +e
if getent passwd "${USER}" >/dev/null 2>&1; then userdel -r "${USER}" 2>/dev/null; fi
if getent group "${GROUP}" >/dev/null 2>&1; then groupdel "${GROUP}" 2>/dev/null; fi
rm -rf "${SANDBOX}" /tmp/lab28c

echo "── Lab 28c cleanup audit ──"
getent passwd "${USER}" >/dev/null && echo "❌ user remains"   || echo "✅ user gone"
getent group  "${GROUP}" >/dev/null && echo "❌ group remains"  || echo "✅ group gone"
test -d "${SANDBOX}"              && echo "❌ sandbox remains" || echo "✅ sandbox gone"
test -d /tmp/lab28c               && echo "❌ /tmp/lab28c remains" || echo "✅ /tmp/lab28c gone"
set -e
```

> **T44 check:** closeout passes only when all four audit lines are `✅`.

---

## Author

**Kelvin R. Tobias**  
[kelvinintech.com](https://kelvinintech.com) · [GitHub](https://github.com/kelvintechnical) · [LinkedIn](https://www.linkedin.com/in/kelvin-r-tobias-211949219)
