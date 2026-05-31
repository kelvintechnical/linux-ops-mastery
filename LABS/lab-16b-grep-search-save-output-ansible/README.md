# Lab 16b: Search for a String and Save Output (Ansible) — `ansible.builtin.shell`, `register`, `failed_when`

- **Series:** linux-ops-mastery — Search and Capture
- **Trilogy:** [`16a`](../lab-16a-grep-search-save-output-rhcsa/) (RHCSA) → **`16b`** (Ansible) → [`16c`](../lab-16c-grep-search-save-output-verify/) (Verify)
- **Tasks:** 2 (Task 1 = `ansible.builtin.shell: "grep ... | tee ..."` with `register` + `changed_when: false`; Task 2 = fail on empty stdout with `failed_when`)
- **Practice Directory:** `/sbin`
- **Sandbox (Tier B):** `/tmp/lab16b`, `USER=labuser_16_grepsave`, `GROUP=labgrp_16_grepsave`
- **Traps rehearsed:** `T16-A` · `T16-B` · `T41` · `T44`

> **This lab's practice directory is: `/sbin`** — Ansible shell tasks read command names from `/sbin` while journal and task artifacts land in `/tmp/lab16b` and `/root/rhcsa_journal/lab-16b/`.

---

## LAB HEADER BLOCK

```bash
echo "🖥️  ENV:   ${ENV:-DECLARE_ME}"
echo "💿  DISK:  $(lsblk 2>/dev/null | awk '$NF=="disk"{print "/dev/"$1}' | paste -sd, -)"
echo "🌐  NIC:   $(ip -o addr show 2>/dev/null | awk '$2!="lo"{print $2}' | sort -u | paste -sd, -)"
echo "🔐  SE:    $(getenforce 2>/dev/null || echo n/a)"
echo "📦  OS:    $(cat /etc/redhat-release 2>/dev/null || grep PRETTY_NAME /etc/os-release)"
echo "🕒  TIME:  $(date -Is)"
echo "👤  USER:  $(whoami)@$(hostname)"
echo "⚠️  TRAP REMINDERS THIS LAB: T16-A T16-B T41 T44"
echo "📁  PRACTICE DIR: /sbin"
ansible --version
ansible localhost -m ping --connection=local
```

> **STOP — paste output before setup.**

---

## Lab-Wide Setup — Tier B Sandbox Stack

```bash
sudo -i

export LAB_NUM=16
export LAB_SLUG=grepsave
export SANDBOX=/tmp/lab16b
export GROUP=labgrp_16_grepsave
export USER=labuser_16_grepsave
export USER_HOME=${SANDBOX}/home_${USER}

mkdir -p "${SANDBOX}" "${USER_HOME}"
mkdir -p /root/rhcsa_journal/lab-16b/playbooks
mkdir -p /root/rhcsa_journal/lab-16b/task1
mkdir -p /root/rhcsa_journal/lab-16b/task2

getent group  "${GROUP}" >/dev/null || groupadd "${GROUP}"
getent passwd "${USER}"  >/dev/null || useradd -d "${USER_HOME}" -M -s /bin/bash -g "${GROUP}" "${USER}"
chown -R "${USER}:${GROUP}" "${SANDBOX}"

cat > "${SANDBOX}/THIS_DIRECTORY.txt" <<'EOF'
/sbin is the admin command path used for this rotation.
This lab reads /sbin names via ansible.builtin.shell and persists outputs in /tmp and /root journal.
EOF

id "${USER}"
ls -ld /sbin "${SANDBOX}" "${USER_HOME}"
echo "Setup complete at $(date -Is)"
echo "exit was: $?"
```

> **STOP — paste setup proof before Task 1.**

---

## Task 1 — Ansible shell grep pipeline with `register:` and `changed_when: false`

**Practice directory this task:** `/sbin` — shell pipeline searches `/sbin` command names and saves to `/tmp/lab16b/result.txt`.

### Warm-Up

```bash
ls -ld /sbin
ls -1 /sbin 2>/dev/null | head -10
grep -E 'sh$|ctl$' /tmp/lab16b/THIS_DIRECTORY.txt || true
echo "Warm-up done by $(whoami) at $(date -Is)"
echo "exit was: $?"
```

### Purpose

Run a grep-and-tee pipeline via `ansible.builtin.shell`, capture output with `register: result`, keep task read-only with `changed_when: false`, and copy stdout to journal evidence.

### WEAVE TRACE

| Warm-up / setup command | Role inside Task 1 |
|---|---|
| `ls -ld /sbin` | Confirms search root before playbook |
| `ls -1 /sbin` | Mirrors command used inside shell task |
| `grep -E` | Reused in pipeline filter criteria |
| `id "${USER}"` | Tier B identity audit in post-check |

### Main Command Block

```bash
TASKLOG=/tmp/lab16b/task1.txt
PB=/root/rhcsa_journal/lab-16b/playbooks/task1.yml

cat > "${PB}" <<'PLAYBOOK'
---
- name: Lab 16b Task 1 grep tee capture
  hosts: localhost
  connection: local
  gather_facts: false
  tasks:
    - name: Search /sbin names and save through tee
      ansible.builtin.shell: "ls -1 /sbin 2>/dev/null | grep -E 'sh$|ctl$' | tee /tmp/lab16b/result.txt"
      register: result
      changed_when: false
      failed_when: false

    - name: Show result lengths
      ansible.builtin.debug:
        msg:
          - "rc={{ result.rc }}"
          - "stdout_lines={{ result.stdout_lines | length }}"
          - "stderr_lines={{ result.stderr_lines | length }}"

    - name: Copy stdout into journal evidence
      ansible.builtin.copy:
        dest: /root/rhcsa_journal/lab-16b/task1/result-stdout.txt
        content: "{{ result.stdout }}\n"
        mode: '0644'
PLAYBOOK

ansible-playbook "${PB}" 2>&1 | tee "${TASKLOG}"
echo "play exit was: $?" | tee -a "${TASKLOG}"
wc -l /tmp/lab16b/result.txt | tee -a "${TASKLOG}"
echo "exit was: $?"
```

### Human-Readable Breakdown

- `ansible.builtin.shell` runs the exact shell pipeline with `grep ... | tee`.
- `register: result` stores `rc`, `stdout`, `stdout_lines`, `stderr_lines`.
- `changed_when: false` keeps read-only search tasks idempotent in recap.
- `copy` writes captured stdout into persistent journal location.

### Reading It Left to Right

```text
ansible.builtin.shell: "ls -1 /sbin | grep -E 'sh$|ctl$' | tee /tmp/lab16b/result.txt"
│                      │             │                   │
│                      │             │                   └─ persist and display matches
│                      │             └─ regex filter
│                      └─ enumerate commands in /sbin
└─ execute literal shell pipeline
```

### The Story

Ansible does not replace shell literacy; it operationalizes it. When you do need shell, make state reporting honest (`changed_when: false`) and capture outputs intentionally (`register` + journal copy). That is the RHCE habit this task drills.

### Expected Output

```text
TASK [Show result lengths] ...
rc=0
stdout_lines=<n>
stderr_lines=0
```

### Switches

| Token | Meaning |
|---|---|
| `ansible.builtin.shell` | Run shell command |
| `register: result` | Capture command output data |
| `changed_when: false` | Prevent false-positive change |
| `failed_when: false` | Continue for evidence collection |
| `grep -E` | Extended regex matching |

### Concept Card

| ✅ | Concept | What it does |
|---|---|---|
| ✅ | Shell pipeline in Ansible | Preserves familiar grep/tee behavior |
| ✅ | `register` output object | Gives structured stdout/stderr access |
| ✅ | `changed_when: false` | Keeps read-only tasks truly idempotent |
| ✅ | Journal copy | Makes evidence persistent beyond `/tmp` |
| 🪤 Trap Risk | What goes wrong | How to avoid |
| ⚠️ `T16-A` | Greedy regex captures unintended command names | Use end anchors and explicit alternatives |

### 🔁 PERSISTENCE CHECK

| What was configured | Verification command | Why it matters |
|---|---|---|
| Result file exists | `test -s /tmp/lab16b/result.txt && wc -l /tmp/lab16b/result.txt` | Confirms pipeline output saved |
| Journal evidence exists | `test -s /root/rhcsa_journal/lab-16b/task1/result-stdout.txt` | Confirms persistent capture |
| Idempotent reporting | `grep -c "changed=0" /tmp/lab16b/task1.txt` | Ensures read-only task not marked changed |

### Journal Write

```bash
LAB=lab-16b
TASK=task1
JDIR="/root/rhcsa_journal/${LAB}/${TASK}"
mkdir -p "$JDIR"

cp /tmp/lab16b/task1.txt "$JDIR/evidence.txt"
cp /tmp/lab16b/result.txt "$JDIR/result.txt"

cat > "$JDIR/done.txt" <<EOF
LAB:    ${LAB}
TASK:   ${TASK}
DATE:   $(date -Is)
USER:   $(whoami)@$(hostname)
STATUS: COMPLETE
EOF

cat > "$JDIR/notes.txt" <<EOF
TOPIC:    ansible shell grep|tee with register and changed_when false
COMMANDS: ansible.builtin.shell, register, changed_when:false, grep -E, tee
TRAPS:    T16-A rehearsed
NEXT:     task2 failed_when on empty stdout
EOF

echo "Journal written: $(ls -la "$JDIR")"
echo "exit was: $?"
```

### Cleanup

```bash
rm -f /tmp/lab16b/task1.txt /tmp/lab16b/result.txt
echo "exit was: $?"
```

### Troubleshoot

| Symptom | Fix |
|---|---|
| `stdout_lines` is zero | Recheck regex and source list from `/sbin` |
| Play shows changed=1 | Confirm `changed_when: false` present |
| Result file missing | Ensure `tee /tmp/lab16b/result.txt` is in shell string |

> **STOP — paste play recap and result count before Task 2.**

---

## Task 2 — `failed_when: result.stdout|length == 0` trap guard

**Practice directory this task:** `/sbin` — search remains anchored to `/sbin` so empty-result detection is meaningful.

### Warm-Up

```bash
ls -ld /sbin
ls -1 /sbin 2>/dev/null | grep -E 'sh$|ctl$' | head -5
echo "Warm-up done by $(whoami) at $(date -Is)"
echo "exit was: $?"
```

### Purpose

Prevent silent success when grep returns no matches by failing explicitly on empty stdout (`failed_when: result.stdout|length == 0`), then record both pass and fail behavior.

### WEAVE TRACE

| Warm-up / setup command | Role inside Task 2 |
|---|---|
| `ls -ld /sbin` | Confirms expected search source |
| `grep -E ...` | Validates known-good matching baseline |
| Prior `register` habit | Reused for stdout-length guard |

### Main Command Block

```bash
TASKLOG=/tmp/lab16b/task2.txt
PB=/root/rhcsa_journal/lab-16b/playbooks/task2.yml

cat > "${PB}" <<'PLAYBOOK'
---
- name: Lab 16b Task 2 empty-stdout failed_when
  hosts: localhost
  connection: local
  gather_facts: false
  tasks:
    - name: Good search expected to match
      ansible.builtin.shell: "ls -1 /sbin 2>/dev/null | grep -E 'sh$|ctl$' | tee /tmp/lab16b/good.txt"
      register: result
      changed_when: false
      failed_when: result.stdout | length == 0

    - name: Bad search intentionally empty (trap demo)
      ansible.builtin.shell: "ls -1 /sbin 2>/dev/null | grep -E 'ZZZ_NO_MATCH_PATTERN' | tee /tmp/lab16b/empty.txt"
      register: empty_result
      changed_when: false
      failed_when: empty_result.stdout | length == 0
      ignore_errors: true

    - name: Show guard behavior
      ansible.builtin.debug:
        msg:
          - "good_len={{ result.stdout | length }}"
          - "empty_len={{ empty_result.stdout | length }}"
          - "empty_guard_triggered={{ empty_result.failed | default(false) }}"

    - name: Copy task2 summary to journal
      ansible.builtin.copy:
        dest: /root/rhcsa_journal/lab-16b/task2/guard-summary.txt
        content: |
          good_len={{ result.stdout | length }}
          empty_len={{ empty_result.stdout | length }}
          empty_guard_triggered={{ empty_result.failed | default(false) }}
        mode: '0644'
PLAYBOOK

ansible-playbook "${PB}" 2>&1 | tee "${TASKLOG}"
echo "play exit was: $?" | tee -a "${TASKLOG}"
grep -E "good_len|empty_len" "${TASKLOG}" | tee -a "${TASKLOG}"
echo "exit was: $?"
```

### Human-Readable Breakdown

- First task proves normal successful non-empty search.
- Second task intentionally creates empty stdout to trigger guard.
- `failed_when: ... == 0` turns silent empty output into explicit failure signal.
- `ignore_errors: true` keeps play running so you can inspect trap behavior.

### Reading It Left to Right

```text
failed_when: empty_result.stdout | length == 0
│            │                   │          │
│            │                   │          └─ fail when no output bytes
│            │                   └─ Jinja length filter
│            └─ captured stdout from grep pipeline
└─ custom task failure rule
```

### The Story

Grep returning nothing is not always an error code problem; it is frequently a verification problem. In automation, "no data" can silently pass unless you assert expectations. This guard converts silent emptiness into auditable behavior.

### Expected Output

```text
good_len=<nonzero>
empty_len=0
empty_guard_triggered=True
```

### Switches

| Token | Meaning |
|---|---|
| `failed_when:` | Custom failure condition |
| `result.stdout | length` | Output-byte/char length check |
| `ignore_errors: true` | Continue to inspect intentional failure |
| `grep -E` | Regex search mode |

### Concept Card

| ✅ | Concept | What it does |
|---|---|---|
| ✅ | Empty-stdout guard | Fails task when expected matches are absent |
| ✅ | Trap rehearsal | Demonstrates silent pass risk without guard |
| ✅ | Journalized summary | Persists lengths and failure state |
| ✅ | `/sbin` search source | Keeps pattern tied to real admin commands |
| 🪤 Trap Risk | What goes wrong | How to avoid |
| ⚠️ `T16-B` | Assuming sudo prefix fixes redirect/file privilege in shell snippets | Use `tee` with proper privilege context; verify outputs/ownership |

### 🔁 PERSISTENCE CHECK

| What was configured | Verification command | Why it matters |
|---|---|---|
| Guard summary persisted | `test -s /root/rhcsa_journal/lab-16b/task2/guard-summary.txt` | Confirms recorded automation behavior |
| Good capture exists | `test -s /tmp/lab16b/good.txt` | Confirms positive path |
| Empty trap detected | `grep -q "empty_len=0" /root/rhcsa_journal/lab-16b/task2/guard-summary.txt` | Confirms failure condition rehearsal |

### Journal Write

```bash
LAB=lab-16b
TASK=task2
JDIR="/root/rhcsa_journal/${LAB}/${TASK}"
mkdir -p "$JDIR"

cp /tmp/lab16b/task2.txt "$JDIR/evidence.txt"

cat > "$JDIR/done.txt" <<EOF
LAB:    ${LAB}
TASK:   ${TASK}
DATE:   $(date -Is)
USER:   $(whoami)@$(hostname)
STATUS: COMPLETE
EOF

cat > "$JDIR/notes.txt" <<EOF
TOPIC:    failed_when guard for empty grep stdout
COMMANDS: failed_when, register, grep -E, tee
TRAPS:    empty-match silent pass prevented via stdout length assert
NEXT:     lab-16c verify audit + destroy-restore
EOF

echo "Journal written: $(ls -la "$JDIR")"
echo "exit was: $?"
```

### Cleanup

```bash
rm -f /tmp/lab16b/task2.txt /tmp/lab16b/good.txt /tmp/lab16b/empty.txt
echo "exit was: $?"
```

### Troubleshoot

| Symptom | Fix |
|---|---|
| Guard never triggers | Ensure bad regex truly has zero matches |
| Play aborts too early | Add `ignore_errors: true` on intentional-failure task |
| Journal summary missing | Verify copy/debug task path under `/root/rhcsa_journal/lab-16b/task2/` |

> **STOP — paste guard summary before Lab Closeout.**

---

## Lab Closeout — Section 6 Bulletproof Teardown

```bash
set +e

podman ps -aq --filter "name=^${CTR}$" 2>/dev/null | xargs -r podman rm -f >/dev/null 2>&1
awk -v s="${SANDBOX}" '$2 ~ s {print $2}' /proc/mounts | tac | xargs -r -n1 umount -l 2>/dev/null
if vgs "${VG}" >/dev/null 2>&1; then
    lvremove -fy "${VG}" 2>/dev/null
    vgremove -fy "${VG}" 2>/dev/null
    pvremove -ffy /dev/loop* 2>/dev/null
fi
losetup -j "${SANDBOX}/disk.img" 2>/dev/null | cut -d: -f1 | xargs -r losetup -d 2>/dev/null

if getent passwd "${USER}" >/dev/null 2>&1; then userdel -r "${USER}" 2>/dev/null; fi
if getent group "${GROUP}" >/dev/null 2>&1; then groupdel "${GROUP}" 2>/dev/null; fi
rm -rf "${SANDBOX}"

echo "── cleanup audit ──"
getent passwd "${USER}" && echo "❌ user remains" || echo "✅ user gone"
getent group "${GROUP}" && echo "❌ group remains" || echo "✅ group gone"
vgs "${VG}" 2>/dev/null && echo "❌ VG remains" || echo "✅ vg gone"
losetup -l | grep -q "${SANDBOX}" && echo "❌ loop remains" || echo "✅ loop gone"
podman ps -a --filter "name=^${CTR}$" --format '{{.Names}}' | grep -q . && echo "❌ ctr remains" || echo "✅ ctr gone"
test -d "${SANDBOX}" && echo "❌ sandbox remains" || echo "✅ sandbox gone"

set -e
echo "Cleanup complete by $(whoami) at $(date -Is)"
echo "exit was: $?"
```

> **STOP — paste cleanup audit lines.**

---

## Author

**Kelvin R. Tobias**  
[kelvinintech.com](https://kelvinintech.com) · [GitHub](https://github.com/kelvintechnical) · [LinkedIn](https://www.linkedin.com/in/kelvin-r-tobias-211949219)
