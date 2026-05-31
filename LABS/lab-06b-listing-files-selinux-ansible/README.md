# Lab 06b: Listing Files and SELinux (Ansible) — `community.general.sefcontext`

- **Series:** linux-ops-mastery — Essential Tools & File Operations
- **Trilogy:** [`06a`](../lab-06a-listing-files-selinux-rhcsa/) (RHCSA hand-typed) → **`06b`** (Ansible — you are here) → [`06c`](../lab-06c-listing-files-selinux-verify/) (Verify capstone)
- **Career arcs covered:** RHCE EX294 (`community.general.sefcontext` is the declarative `semanage fcontext`)
- **Prerequisite:** [`Lab 06a`](../lab-06a-listing-files-selinux-rhcsa/) and [`Lab 00b`](../lab-00b-ansible-control-node-setup-ansible/) completed
- **Time Estimate:** 25–35 minutes
- **Tasks:** 2 (Task 1 = sefcontext rule + restorecon via Ansible · Task 2 = idempotence + drift correction)
- **Practice Directory:** `/tmp/lab06b/web` (mock webroot)
- **Playbooks:** `/root/rhcsa_journal/lab-06b/playbooks/`
- **Traps rehearsed:** **T02** (sefcontext alone doesn't relabel — must call `command: restorecon` after) · **T02-X** (using `ansible.builtin.command: chcon` instead of sefcontext — temporary label, no persistence)

---

## LAB HEADER BLOCK

```bash
ansible --version | head -n 3
ansible-galaxy collection list | grep community.general
echo ""
echo "--- 06a prereq ---"
ls /root/rhcsa_journal/lab-06a/task2/done.txt 2>/dev/null \
    && echo "✅ 06a journal present" \
    || echo "❌ 06a journal missing — complete Lab 06a first"
echo "exit was: $?"
```

> **STOP — paste header.**

---

## Lab-Wide Setup

```bash
sudo -i

mkdir -p /tmp/lab06b/web
echo "<h1>Lab 06b</h1>" > /tmp/lab06b/web/index.html
mkdir -p /root/rhcsa_journal/lab-06b/playbooks
mkdir -p /root/rhcsa_journal/lab-06b/task1 /root/rhcsa_journal/lab-06b/task2

ls -ldZ /tmp/lab06b/web
echo "Setup complete at $(date -Is)"
echo "exit was: $?"
```

---

## Task 1 — sefcontext rule + restorecon via Ansible

### 🔁 Warm-Up

```bash
ls -lZ /tmp/lab06b/web/index.html
matchpathcon /tmp/lab06b/web/index.html
ansible-doc community.general.sefcontext | head -n 20
echo "Warm-up done by $(whoami) at $(date -Is)"
echo "exit was: $?"
```

### Main command block

```bash
TASKLOG=/tmp/lab06b/task1.txt
PB=/root/rhcsa_journal/lab-06b/playbooks/task1.yml

cat > "${PB}" << 'PLAYBOOK'
---
- name: "Lab 06b Task 1 — declarative SELinux fcontext"
  hosts: localhost
  connection: local
  gather_facts: false

  tasks:
    - name: "Add fcontext rule for the lab webroot"
      community.general.sefcontext:
        target: '/tmp/lab06b/web(/.*)?'
        setype: httpd_sys_content_t
        state: present
      register: fc_result

    - name: "Apply contexts on the filesystem (sefcontext does NOT do this)"
      ansible.builtin.command: restorecon -Rv /tmp/lab06b/web
      register: rc_result
      changed_when: rc_result.stdout | length > 0

    - name: "Show results"
      ansible.builtin.debug:
        msg:
          - "fcontext changed: {{ fc_result.changed }}"
          - "restorecon changed: {{ rc_result.changed }}"
          - "restorecon stdout: {{ rc_result.stdout_lines | default([]) }}"
PLAYBOOK

echo "═══ Part A: --check --diff ═══"                    2>&1 | tee $TASKLOG
ansible-playbook --check --diff "${PB}"                  2>&1 | tee -a $TASKLOG

echo "═══ Part B: apply ═══"                              | tee -a $TASKLOG
ansible-playbook "${PB}"                                  2>&1 | tee -a $TASKLOG

echo "═══ Part C: verify on disk ═══"                     | tee -a $TASKLOG
ls -lZ /tmp/lab06b/web/index.html                        | tee -a $TASKLOG
semanage fcontext -l | grep '/tmp/lab06b/web'            | tee -a $TASKLOG
echo "exit was: $?"
```

### Expected output

```text
═══ Part A: --check --diff ═══
TASK [Add fcontext rule for the lab webroot]
changed: [localhost]
TASK [Apply contexts on the filesystem (sefcontext does NOT do this)]
skipping (check mode)
═══ Part B: apply ═══
TASK [Add fcontext rule for the lab webroot]
changed: [localhost]
TASK [Apply contexts on the filesystem (sefcontext does NOT do this)]
changed: [localhost]
═══ Part C: verify on disk ═══
-rw-r--r--. ... httpd_sys_content_t ... index.html
/tmp/lab06b/web(/.*)? all files system_u:object_r:httpd_sys_content_t:s0
```

### 🧠 Concept Card

| Concept | What it does |
|---|---|
| `community.general.sefcontext` | Declarative `semanage fcontext -a/-d` |
| `state: present`/`absent` | Add or remove the rule |
| **🪤 Trap Risk T02** | sefcontext alone records the rule but does NOT relabel — you must follow with `restorecon`. **Fix:** combine the two tasks. |

### Journal write

```bash
LAB=lab-06b
TASK=task1
JDIR="/root/rhcsa_journal/${LAB}/${TASK}"
mkdir -p "$JDIR"
cp /tmp/lab06b/task1.txt "$JDIR/evidence.txt"
cp "${PB}" "$JDIR/task1.yml"
ls -lZ /tmp/lab06b/web/index.html > "$JDIR/lsZ.txt"

cat > "$JDIR/done.txt" <<EOF
LAB:    ${LAB}
TASK:   ${TASK}
DATE:   $(date -Is)
USER:   $(whoami)@$(hostname)
STATUS: COMPLETE
EOF

cat > "$JDIR/notes.txt" <<EOF
TOPIC:    community.general.sefcontext + ansible.builtin.command restorecon
COMMANDS: ansible-playbook --check --diff, sefcontext target/setype/state
TRAPS:    T02 rehearsed
NEXT:     task2 — idempotence + drift correction
EOF

ls -la "$JDIR"
echo "exit was: $?"
```

### 🧹 Cleanup

```bash
rm -f /tmp/lab06b/task1.txt
ls /tmp/lab06b
echo "exit was: $?"
```

> **STOP — paste the apply PLAY RECAP and the `httpd_sys_content_t` line before Task 2.**

---

## Task 2 — Idempotence + drift correction

### 🔁 Warm-Up

```bash
ls -lZ /tmp/lab06b/web/index.html
ansible-playbook --syntax-check /root/rhcsa_journal/lab-06b/playbooks/task1.yml
echo "Warm-up done by $(whoami) at $(date -Is)"
echo "exit was: $?"
```

### Main command block

```bash
TASKLOG=/tmp/lab06b/task2.txt
PB=/root/rhcsa_journal/lab-06b/playbooks/task1.yml

echo "═══ Part A: re-apply (idempotence) ═══"             2>&1 | tee $TASKLOG
ansible-playbook "${PB}"                                  2>&1 | tee -a $TASKLOG
CHG_A=$(grep -oP 'changed=\K[0-9]+' "$TASKLOG" | tail -n 1)
echo "Pass A changed=${CHG_A}"                            | tee -a $TASKLOG

echo "═══ Part B: introduce drift via chcon ═══"          | tee -a $TASKLOG
chcon -R -t user_tmp_t /tmp/lab06b/web
ls -lZ /tmp/lab06b/web/index.html                         | tee -a $TASKLOG

echo "═══ Part C: re-apply — drift corrected ═══"          | tee -a $TASKLOG
ansible-playbook "${PB}"                                  2>&1 | tee -a $TASKLOG
ls -lZ /tmp/lab06b/web/index.html                         | tee -a $TASKLOG

echo "═══ Part D: re-apply (idempotent again) ═══"         | tee -a $TASKLOG
ansible-playbook "${PB}"                                  2>&1 | tee -a $TASKLOG
CHG_D=$(grep -oP 'changed=\K[0-9]+' "$TASKLOG" | tail -n 1)
echo "Pass D changed=${CHG_D}"                            | tee -a $TASKLOG

CTX=$(stat -c '%C' /tmp/lab06b/web/index.html)
echo "${CTX}" | grep -q 'httpd_sys_content_t' \
    && echo "✅ drift corrected; context restored" \
    || echo "❌ drift not corrected" \
    | tee -a $TASKLOG

echo "exit was: $?"
```

### Journal write

```bash
LAB=lab-06b
TASK=task2
JDIR="/root/rhcsa_journal/${LAB}/${TASK}"
mkdir -p "$JDIR"
cp /tmp/lab06b/task2.txt "$JDIR/evidence.txt"

cat > "$JDIR/done.txt" <<EOF
LAB:    ${LAB}
TASK:   ${TASK}
DATE:   $(date -Is)
USER:   $(whoami)@$(hostname)
STATUS: COMPLETE
EOF

cat > "$JDIR/notes.txt" <<EOF
TOPIC:    Idempotence proof; drift via chcon corrected by re-apply
COMMANDS: ansible-playbook re-apply, chcon (drift), restorecon (correction via apply)
TRAPS:    T02 rehearsed again
NEXT:     lab-06c — verify capstone
EOF

ls -la "$JDIR"
echo "exit was: $?"
```

### 🧹 Cleanup (per-task — keep webroot + rule for 06c)

```bash
rm -f /tmp/lab06b/task2.txt
ls /tmp/lab06b
echo "exit was: $?"
```

> **STOP — paste both `Pass A changed=` and `Pass D changed=` lines before moving to Lab 06c.**

---

## Lab 06b Checklist

- [ ] Task 1 — `--check --diff` previewed; apply added rule + relabeled; on-disk shows `httpd_sys_content_t`
- [ ] Task 2 — Pass A changed=0; chcon-induced drift corrected on next apply; Pass D changed=0

---

## Author

**Kelvin R. Tobias**
[kelvinintech.com](https://kelvinintech.com) · [GitHub](https://github.com/kelvintechnical) · [LinkedIn](https://www.linkedin.com/in/kelvin-r-tobias-211949219)
