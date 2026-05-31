# Lab 21b: Monitoring Live Log Files — Ansible (`shell`, `register`, `lineinfile`, `failed_when`)

- **Series:** linux-ops-mastery — Logging, Troubleshooting, and Real-Time Observability
- **Trilogy:** [`21a`](../lab-21a-tail-f-live-logs-rhcsa/) (RHCSA hand-typed) → **`21b`** (Ansible automation) → [`21c`](../lab-21c-tail-f-live-logs-verify/) (Verify capstone)
- **Career arcs covered:** RHCE EX294 (safe shell tasks + explicit failure criteria), SRE (automated log-follow checks), DevOps (pipeline health probes in playbooks)
- **Prerequisite:** Lab 21a complete with journal artifacts in `/root/rhcsa_journal/lab-21a/`
- **Time Estimate:** 30–40 minutes
- **Tasks:** 2 (Task 1 = `timeout 5 tail -F` + register + `lineinfile`; Task 2 = failed_when trap for empty tail output)
- **Practice Directory (rotation #21):** `/boot` (context) with writes in `/tmp/lab21b`
- **Sandbox (Tier B):** `/tmp/lab21b` with `USER=labuser_21_livelog`, `GROUP=labgrp_21_livelog`, `USER_HOME=/tmp/lab21b/home_labuser_21_livelog`
- **Traps rehearsed this lab:** **T21-A** (must use `-F` for rotate-safe follow) · **T21-B** (avoid unbounded tails by forcing timeout) · **T41** (verify in 21c) · **T44** (closeout audit)

> **This lab's practice directory is: `/boot`** — operational context is read-only there while playbook artifacts live in `/tmp/lab21b` and `/root/rhcsa_journal/lab-21b/`.

---

## LAB HEADER BLOCK

```bash
echo "--- ansible controller ---"
ansible --version
ansible localhost -m ping --connection=local
echo ""
echo "--- /boot context ---"
ls -ld /boot
ls /boot 2>/dev/null | head -n 5
echo ""
echo "--- 21a prereq check ---"
ls /root/rhcsa_journal/lab-21a/task1/done.txt /root/rhcsa_journal/lab-21a/task2/done.txt 2>/dev/null \
  && echo "✅ 21a journal exists" || echo "❌ 21a journal missing"
echo "exit was: $?"
```

> **STOP — paste header output before setup.**

---

## Objective

Automate bounded live-log checks with explicit pass/fail logic:

1. Run `timeout 5 tail -F` safely in `ansible.builtin.shell`.
2. Capture tail output with `register` and persist evidence.
3. Use `lineinfile` to build a rotate fragment under `/tmp/lab21b`.
4. Guard against false-success when output is empty using `failed_when`.

---

## Lab-Wide Setup — Tier B Stack

```bash
sudo -i

export LAB_NUM=21
export LAB_SLUG=livelog
export SANDBOX=/tmp/lab21b
export GROUP=labgrp_${LAB_NUM}_${LAB_SLUG}
export USER=labuser_${LAB_NUM}_${LAB_SLUG}
export USER_HOME=${SANDBOX}/home_${USER}

mkdir -p "${SANDBOX}" "${USER_HOME}" /root/rhcsa_journal/lab-21b/playbooks /root/rhcsa_journal/lab-21b/task1 /root/rhcsa_journal/lab-21b/task2
getent group  "${GROUP}" >/dev/null || groupadd "${GROUP}"
getent passwd "${USER}"  >/dev/null || useradd -d "${USER_HOME}" -M -s /bin/bash -g "${GROUP}" "${USER}"
chown -R "${USER}:${GROUP}" "${SANDBOX}"

id "${USER}"
ls -ld "${SANDBOX}" "${USER_HOME}" /boot
getent group "${GROUP}"
getent passwd "${USER}"
echo "setup complete: $(date -Is)"
echo "exit was: $?"
```

---

## Task 1 — `timeout 5 tail -F` with `register` + `lineinfile`

**Practice directory this task:** `/boot` context, `/tmp/lab21b` for ansible artifacts.

### Warm-Up

```bash
mkdir -p /tmp/lab21b
echo "seed-1" > /tmp/lab21b/app.log
tail -n 1 /tmp/lab21b/app.log                       2>&1 | tee /tmp/lab21b/warmup.txt
echo "exit was: $?"
```

### Purpose

Run a rotate-safe follower for 5 seconds, collect output with `register`, and create a logrotate fragment file using `ansible.builtin.lineinfile`.

### Main command block

```bash
TASKLOG=/tmp/lab21b/task1.txt
PB=/root/rhcsa_journal/lab-21b/playbooks/task1.yml

cat > "${PB}" <<'PLAYBOOK'
---
- name: "Lab 21b Task 1 — timeout tail -F + lineinfile fragment"
  hosts: localhost
  connection: local
  gather_facts: false
  vars:
    live_log: /tmp/lab21b/app.log
    capture_file: /tmp/lab21b/tail-capture.txt
    rotate_fragment: /tmp/lab21b/logrotate-app.conf

  tasks:
    - name: Ensure practice directory exists
      ansible.builtin.file:
        path: /tmp/lab21b
        state: directory
        mode: '0755'

    - name: Seed log content
      ansible.builtin.shell: |
        echo "pre-1 $(date -Is)" >> "{{ live_log }}"
        echo "pre-2 $(date -Is)" >> "{{ live_log }}"
      changed_when: true

    - name: Generate live events in background
      ansible.builtin.shell: |
        (
          sleep 1; echo "ev-1 $(date -Is)" >> "{{ live_log }}"
          sleep 1; echo "ev-2 $(date -Is)" >> "{{ live_log }}"
          sleep 1; echo "ev-3 $(date -Is)" >> "{{ live_log }}"
        ) &
      changed_when: true

    - name: Capture bounded follower output (rotate-safe)
      ansible.builtin.shell: timeout 5 tail -n 0 -F "{{ live_log }}"
      register: tail_capture
      changed_when: false
      failed_when: false

    - name: Persist capture content
      ansible.builtin.copy:
        dest: "{{ capture_file }}"
        content: "{{ tail_capture.stdout }}"
        mode: '0644'

    - name: Build logrotate fragment header
      ansible.builtin.lineinfile:
        path: "{{ rotate_fragment }}"
        create: true
        line: "/tmp/lab21b/app.log {"

    - name: Add rotate directive
      ansible.builtin.lineinfile:
        path: "{{ rotate_fragment }}"
        insertafter: "^/tmp/lab21b/app.log \\{$"
        line: "    rotate 3"

    - name: Add size directive
      ansible.builtin.lineinfile:
        path: "{{ rotate_fragment }}"
        insertafter: "    rotate 3"
        line: "    size 5k"

    - name: Add closing brace
      ansible.builtin.lineinfile:
        path: "{{ rotate_fragment }}"
        insertafter: "    size 5k"
        line: "}"

    - name: Show captured summary
      ansible.builtin.debug:
        msg:
          - "rc={{ tail_capture.rc }}"
          - "stdout_lines={{ tail_capture.stdout_lines | length }}"
PLAYBOOK

ansible-playbook "${PB}" 2>&1 | tee "${TASKLOG}"
echo "═══ verify outputs ═══" | tee -a "${TASKLOG}"
wc -l /tmp/lab21b/tail-capture.txt | tee -a "${TASKLOG}"
cat /tmp/lab21b/logrotate-app.conf | tee -a "${TASKLOG}"
echo "exit was: $?"
```

### Journal write

```bash
LAB=lab-21b
TASK=task1
JDIR="/root/rhcsa_journal/${LAB}/${TASK}"
mkdir -p "$JDIR"
cp /tmp/lab21b/task1.txt             "$JDIR/evidence.txt"
cp /tmp/lab21b/tail-capture.txt      "$JDIR/tail-capture.txt"
cp /tmp/lab21b/logrotate-app.conf    "$JDIR/logrotate-app.conf"

cat > "$JDIR/done.txt" <<EOF
LAB:    ${LAB}
TASK:   ${TASK}
DATE:   $(date -Is)
USER:   $(whoami)@$(hostname)
STATUS: COMPLETE
EOF
```

---

## Task 2 — `failed_when` trap for empty capture

**Practice directory this task:** `/tmp/lab21b`

### Warm-Up

```bash
truncate -s 0 /tmp/lab21b/empty.log
ls -l /tmp/lab21b/empty.log                            2>&1 | tee /tmp/lab21b/warmup2.txt
echo "exit was: $?"
```

### Purpose

Prove that "command succeeded" is not the same as "useful data captured." Handle T21-B style silent-empty captures with explicit `failed_when`.

### Main command block

```bash
TASKLOG=/tmp/lab21b/task2.txt
PB=/root/rhcsa_journal/lab-21b/playbooks/task2.yml

cat > "${PB}" <<'PLAYBOOK'
---
- name: "Lab 21b Task 2 — failed_when on empty tail output"
  hosts: localhost
  connection: local
  gather_facts: false
  vars:
    test_log: /tmp/lab21b/empty.log

  tasks:
    - name: Reset log empty
      ansible.builtin.copy:
        dest: "{{ test_log }}"
        content: ""
        mode: '0644'

    - name: Trap demo (allows empty output)
      ansible.builtin.shell: timeout 3 tail -n 0 -F "{{ test_log }}"
      register: weak_capture
      changed_when: false
      failed_when: false

    - name: Correct gate (fail if empty)
      ansible.builtin.shell: timeout 3 tail -n 0 -F "{{ test_log }}"
      register: strict_capture
      changed_when: false
      failed_when: strict_capture.stdout | trim == ""
      ignore_errors: true

    - name: Emit strict gate status
      ansible.builtin.debug:
        msg:
          - "weak_rc={{ weak_capture.rc }} weak_len={{ weak_capture.stdout_lines | length }}"
          - "strict_failed={{ strict_capture is failed }}"
          - "strict_len={{ strict_capture.stdout_lines | length }}"
PLAYBOOK

ansible-playbook "${PB}" 2>&1 | tee "${TASKLOG}"
echo "exit was: $?"
```

### Trap callout

- **T21-B pattern:** without `failed_when`, empty output can look "green."
- **Fix:** explicit semantic gate: `failed_when: strict_capture.stdout | trim == ""`.
- **T21-A reinforcement:** use `-F` (not `-f`) whenever rotate resilience is required.

### Journal write

```bash
LAB=lab-21b
TASK=task2
JDIR="/root/rhcsa_journal/${LAB}/${TASK}"
mkdir -p "$JDIR"
cp /tmp/lab21b/task2.txt "$JDIR/evidence.txt"

cat > "$JDIR/done.txt" <<EOF
LAB:    ${LAB}
TASK:   ${TASK}
DATE:   $(date -Is)
USER:   $(whoami)@$(hostname)
STATUS: COMPLETE
EOF
```

---

## Lab Closeout — Bulletproof Teardown (Section 6)

```bash
set +e

awk -v s="${SANDBOX}" '$2 ~ s {print $2}' /proc/mounts | tac | xargs -r -n1 umount -l 2>/dev/null

if getent passwd "${USER}" >/dev/null 2>&1; then
  userdel -r "${USER}" 2>/dev/null
fi
if getent group "${GROUP}" >/dev/null 2>&1; then
  groupdel "${GROUP}" 2>/dev/null
fi

rm -rf "${SANDBOX}"

echo "── Lab 21b cleanup audit ──"
getent passwd "${USER}" >/dev/null && echo "❌ user remains" || echo "✅ user gone"
getent group  "${GROUP}" >/dev/null && echo "❌ group remains" || echo "✅ group gone"
test -d "${SANDBOX}" && echo "❌ sandbox remains" || echo "✅ sandbox gone"
test -d "${USER_HOME}" && echo "❌ home remains" || echo "✅ home gone"

set -e
echo "Cleanup complete at $(date -Is)"
echo "exit was: $?"
```

---

## Lab 21b Checklist (2 tasks + closeout)

- [ ] Task 1: `timeout 5 tail -F` registered; capture persisted; `/tmp/lab21b/logrotate-app.conf` created via `lineinfile`
- [ ] Task 2: strict `failed_when` detects empty capture and reports controlled failure path
- [ ] Journal: both `done.txt` files written under `/root/rhcsa_journal/lab-21b/`
- [ ] Closeout: four `✅` audit lines

---

## Author

**Kelvin R. Tobias**  
[kelvinintech.com](https://kelvinintech.com) · [GitHub](https://github.com/kelvintechnical) · [LinkedIn](https://www.linkedin.com/in/kelvin-r-tobias-211949219)
