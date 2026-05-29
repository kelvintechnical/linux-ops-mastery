# Lab 17b: Find and Save Config Files (Ansible) — `ansible.builtin.find`

- **Series:** linux-ops-mastery — RHCE-aligned file discovery
- **Trilogy:** [`17a`](../lab-17a-find-save-config-files-rhcsa/) (RHCSA) → `17b` (Ansible FQCN) → [`17c`](../lab-17c-find-save-config-files-verify/) (Verify capstone)
- **Time Estimate:** 30–45 minutes
- **Tasks:** 2 (Task 1 find+register+write list · Task 2 idempotence plus copy/synchronize workflow)
- **Practice Directory (rotation #03):** `/lib`
- **Sandbox (Tier B):** `/tmp/lab17b`, `USER=labuser_17_findsave`, `GROUP=labgrp_17_findsave`, `USER_HOME=/tmp/lab17b/home_labuser_17_findsave`
- **Traps rehearsed:** **T14-A**, **T14-B**, **T41**, **T44**

> **This lab's practice directory is: `/lib`**. We keep `/lib` in every task while using Ansible to discover and persist config-file inventories.

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
echo "⚠️  TRAP REMINDERS THIS LAB: T14-A T14-B T41 T44"
echo "📁  PRACTICE DIR: /lib"
ls -ld /lib
ansible --version | head -n 2
```

> **STOP — paste header output before setup.**

---

## Objective

Translate the RHCSA `find` reflex into RHCE-style playbooks:

1. Use `ansible.builtin.find` with `paths`, `patterns`, and `file_type`.
2. Register findings and write deterministic inventory files.
3. Prove idempotence (`changed=0` on second run).
4. Handle no-match conditions without false failure.

---

## Lab-Wide Setup — Tier B Sandbox Stack

```bash
sudo -i

export LAB_NUM=17
export LAB_SLUG=findsave
export SANDBOX=/tmp/lab17b
export GROUP=labgrp_17_findsave
export USER=labuser_17_findsave
export USER_HOME=${SANDBOX}/home_${USER}

mkdir -p "${SANDBOX}" "${USER_HOME}" /root/rhcsa_journal/lab-17b/playbooks
getent group  "${GROUP}" >/dev/null || groupadd "${GROUP}"
getent passwd "${USER}"  >/dev/null || useradd -d "${USER_HOME}" -M -s /bin/bash -g "${GROUP}" "${USER}"
chown -R "${USER}:${GROUP}" "${SANDBOX}"

cat > "${SANDBOX}/THIS_DIRECTORY.txt" <<'EOF'
/lib contains critical shared objects loaded by executable binaries.
This directory matters because command execution depends on these libraries.
Even when our target search paths are /etc or /, we keep /lib in rotation.
EOF

id "${USER}"
ls -ld "${SANDBOX}" "${USER_HOME}" /lib
echo "Sandbox built by $(whoami) at $(date -Is)"
echo "exit was: $?"
```

---

## Task 1 — `ansible.builtin.find` + `register` + saved list

**Practice directory this task:** `/lib` — referenced in warm-up and validation.

### Warm-Up

```bash
ls -ld /lib
find /lib -maxdepth 1 -type f 2>/dev/null | head -n 3
echo "ansible warmup $(date -Is)" | tee /tmp/lab17b/warmup1.txt
echo "Warm-up done by $(whoami) at $(date -Is)"
echo "exit was: $?"
```

### Purpose

Build a playbook that finds `*.conf` files in `/etc`, registers results, and writes a sorted list to disk using a real module workflow (no shell-wrapper shortcut for the main operation).

### WEAVE TRACE

| Warm-up / setup command | Role inside Task 1 |
|---|---|
| `find /lib ...` | Rehearses filtering mindset before module call |
| `tee` | Keeps a visible transcript while writing evidence |
| `ls -ld /lib` | Maintains rotation discipline |
| Tier B user/group | Ownership checks on generated inventory file |

### Main command block

```bash
cat > /root/rhcsa_journal/lab-17b/playbooks/task1.yml <<'EOF'
---
- name: Lab 17b task1 find and save
  hosts: localhost
  connection: local
  gather_facts: false
  vars:
    out_file: /tmp/lab17b/etc-conf-list-ansible.txt
  tasks:
    - name: Find .conf files under /etc
      ansible.builtin.find:
        paths: /etc
        patterns: "*.conf"
        file_type: file
      register: conf_find

    - name: Show result summary
      ansible.builtin.debug:
        msg: "matched={{ conf_find.matched }} examined={{ conf_find.examined }}"

    - name: Write sorted path list
      ansible.builtin.copy:
        dest: "{{ out_file }}"
        content: |
          {% for f in conf_find.files | map(attribute='path') | list | sort %}
          {{ f }}
          {% endfor %}
        mode: "0644"
EOF

ansible-playbook --check --diff /root/rhcsa_journal/lab-17b/playbooks/task1.yml 2>&1 | tee /tmp/lab17b/task1-check.log
ansible-playbook /root/rhcsa_journal/lab-17b/playbooks/task1.yml 2>&1 | tee /tmp/lab17b/task1-apply.log

wc -l /tmp/lab17b/etc-conf-list-ansible.txt     | tee /tmp/lab17b/task1.log
head -n 10 /tmp/lab17b/etc-conf-list-ansible.txt | tee -a /tmp/lab17b/task1.log
stat -c '%U:%G %a %n' /tmp/lab17b/etc-conf-list-ansible.txt | tee -a /tmp/lab17b/task1.log
ls -ld /lib | tee -a /tmp/lab17b/task1.log
echo "exit was: $?"
```

### Human-Readable Breakdown

- `ansible.builtin.find` performs structured discovery like CLI `find`.
- `register: conf_find` stores matches for later tasks in the same play.
- `ansible.builtin.copy` writes deterministic content from registered paths.
- `--check --diff` previews changes; apply run makes the file real.

### Reading it left to right

```text
ansible.builtin.find: paths=/etc patterns="*.conf" file_type=file
│                    │          │                 └─ only regular files
│                    │          └─ glob match
│                    └─ search root
└─ module (FQCN)
```

### The story

RHCE grading expects declarative modules and inspectable state, not ad-hoc shell pipelines. `register` plus deterministic writes produce artifacts that can be audited and re-run safely.

### Expected output

```text
TASK [Find .conf files under /etc] ...
ok: [localhost]
TASK [Write sorted path list] ...
changed: [localhost]
N /tmp/lab17b/etc-conf-list-ansible.txt
```

### Switches

| Token | Meaning |
|---|---|
| `--check --diff` | Preview mode with change diff |
| `paths` | Root location to search |
| `patterns` | Glob filter in module |
| `file_type: file` | Restrict to regular files |
| `register` | Save task output to variable |

### Concept Card

| ✅ | Concept | What it does |
|---|---|---|
| ✅ | `ansible.builtin.find` | Structured file discovery |
| ✅ | `register` | Captures module output for reuse |
| ✅ | `ansible.builtin.copy` content | Persists results as text |
| ✅ | Check-before-apply | Safer operator workflow |
| 🪤 Trap Risk | Wrapping `find` in `shell:` for no reason | Use module first; shell only if no module can express task |

### 🔁 PERSISTENCE CHECK

| What was configured | Verification command | Why it matters |
|---|---|---|
| Playbook exists | `test -f /root/rhcsa_journal/lab-17b/playbooks/task1.yml` | Persistent artifact for resume |
| Output list saved | `test -s /tmp/lab17b/etc-conf-list-ansible.txt` | Confirms module output persisted |
| Register used | `rg "register: conf_find" /root/rhcsa_journal/lab-17b/playbooks/task1.yml` | Verifies RHCE habit |

### Journal write

```bash
mkdir -p /root/rhcsa_journal/lab-17b/task1
cp /tmp/lab17b/task1.log /root/rhcsa_journal/lab-17b/task1/evidence.txt
echo "LAB: lab-17b TASK: task1 DATE: $(date -Is) STATUS: COMPLETE" > /root/rhcsa_journal/lab-17b/task1/done.txt
echo "TOPIC: ansible.builtin.find + register + copy list output" > /root/rhcsa_journal/lab-17b/task1/notes.txt
```

### 🧹 Cleanup

```bash
rm -f /tmp/lab17b/warmup1.txt
echo "exit was: $?"
```

### Troubleshoot

| Symptom | Fix |
|---|---|
| `matched=0` unexpectedly | Validate `paths` and `patterns` |
| Playbook reports changed every run | Ensure generated content is deterministic/sorted |
| Missing output file | Verify `dest` path in `copy` task |

> **STOP — paste check/apply summary and `wc -l` before Task 2.**

---

## Task 2 — Idempotence + copy/synchronize with no-match trap handling

**Practice directory this task:** `/lib`.

### Warm-Up

```bash
ls -ld /lib
find /lib -maxdepth 2 -type f -name '*.so*' 2>/dev/null | head -n 5
echo "task2 warmup $(date -Is)" | tee /tmp/lab17b/warmup2.txt
echo "Warm-up done by $(whoami) at $(date -Is)"
echo "exit was: $?"
```

### Purpose

Prove idempotence (second apply run `changed=0`) and stage found files into a backup tree using module-driven flow while guarding no-match conditions so the play does not fail incorrectly.

### WEAVE TRACE

| Warm-up / setup command | Role inside Task 2 |
|---|---|
| `head`/`find` | Sample matches before copy loop |
| `tee` | Captures run output for changed/ok proof |
| `/lib` references | Preserves directory rotation requirement |
| Tier B user/group | Ownership checks on backup tree |

### Main command block

```bash
cat > /root/rhcsa_journal/lab-17b/playbooks/task2.yml <<'EOF'
---
- name: Lab 17b task2 idempotence and backup
  hosts: localhost
  connection: local
  gather_facts: false
  vars:
    backup_dir: /tmp/lab17b/backup_conf
  tasks:
    - name: Find conf files in /etc
      ansible.builtin.find:
        paths: /etc
        patterns: "*.conf"
        file_type: file
      register: conf_find

    - name: Ensure backup directory exists
      ansible.builtin.file:
        path: "{{ backup_dir }}"
        state: directory
        mode: "0755"

    - name: Copy first 20 found files into backup tree
      ansible.builtin.copy:
        src: "{{ item.path }}"
        dest: "{{ backup_dir }}/{{ item.path | basename }}"
        remote_src: true
        mode: "0644"
      loop: "{{ conf_find.files[:20] }}"
      when: conf_find.matched | int > 0

    - name: No-match trap guard
      ansible.builtin.debug:
        msg: "No files matched; copy loop skipped safely."
      when: conf_find.matched | int == 0
      failed_when: false
EOF

ansible-playbook /root/rhcsa_journal/lab-17b/playbooks/task2.yml 2>&1 | tee /tmp/lab17b/task2-run1.log
ansible-playbook /root/rhcsa_journal/lab-17b/playbooks/task2.yml 2>&1 | tee /tmp/lab17b/task2-run2.log

ls -l /tmp/lab17b/backup_conf | head -n 20        | tee /tmp/lab17b/task2.log
rg "changed=0" /tmp/lab17b/task2-run2.log         | tee -a /tmp/lab17b/task2.log
stat -c '%U:%G %a %n' /tmp/lab17b/backup_conf     | tee -a /tmp/lab17b/task2.log
ls -ld /lib                                        | tee -a /tmp/lab17b/task2.log
echo "exit was: $?"
```

### Human-Readable Breakdown

- First run creates/updates backup files.
- Second run should report `changed=0` when idempotent.
- `when: matched > 0` and `failed_when: false` avoid false failures on empty matches.
- `remote_src: true` copies files already on localhost target.

### Reading it left to right

```text
loop: "{{ conf_find.files[:20] }}"  when: conf_find.matched | int > 0
│                                   └─ run copy only if matches exist
└─ iterate over discovered file objects
```

### The story

Idempotence is the core contract in automation. If a rerun keeps changing state, operators lose trust and CI drifts. This task drills the "run twice, second run clean" reflex and no-match resilience.

### Expected output

```text
PLAY RECAP ... changed=N
PLAY RECAP ... changed=0
... /tmp/lab17b/backup_conf/...
```

### Switches

| Token | Meaning |
|---|---|
| `remote_src: true` | Source path exists on managed host |
| `when:` | Conditional task execution |
| `failed_when: false` | Suppress failure for intentional branch |
| `loop` | Iterate over found files |
| `changed=0` check | Idempotence proof |

### Concept Card

| ✅ | Concept | What it does |
|---|---|---|
| ✅ | Idempotence | Same playbook rerun should stabilize state |
| ✅ | Guarded loop | Avoid copy errors on zero matches |
| ✅ | Module-first backup | Use declarative file module operations |
| ✅ | Evidence logs | Capture recap lines for audit |
| 🪤 Trap Risk | Treating no-match as fatal | Guard with `when` + `failed_when: false` |

### 🔁 PERSISTENCE CHECK

| What was configured | Verification command | Why it matters |
|---|---|---|
| Task2 playbook saved | `test -f /root/rhcsa_journal/lab-17b/playbooks/task2.yml` | Resume-safe artifact |
| Backup directory exists | `test -d /tmp/lab17b/backup_conf` | Confirms copy stage executed |
| Idempotence achieved | `rg "changed=0" /tmp/lab17b/task2-run2.log` | Confirms stable rerun |

### Journal write

```bash
mkdir -p /root/rhcsa_journal/lab-17b/task2
cp /tmp/lab17b/task2.log /root/rhcsa_journal/lab-17b/task2/evidence.txt
echo "LAB: lab-17b TASK: task2 DATE: $(date -Is) STATUS: COMPLETE" > /root/rhcsa_journal/lab-17b/task2/done.txt
echo "TOPIC: idempotent backup copy from ansible.builtin.find results with no-match guard" > /root/rhcsa_journal/lab-17b/task2/notes.txt
```

### 🧹 Cleanup (per-task; closeout after Task 2)

```bash
rm -f /tmp/lab17b/warmup2.txt
echo "exit was: $?"
```

### Troubleshoot

| Symptom | Fix |
|---|---|
| Second run still changed | Check unstable ordering/content in copy stage |
| Copy task fails on zero matches | Add `when: matched > 0` and safe no-match branch |
| Duplicate filenames in backup | Use unique destination strategy if needed |

> **STOP — paste both play recap lines and `changed=0` proof before closeout.**

---

## Section 6 Closeout — Bulletproof Teardown Audit

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

---

## Lab 17b Checklist

- [ ] Tier B setup complete with `/tmp/lab17b/THIS_DIRECTORY.txt`
- [ ] Task 1 used `ansible.builtin.find` + `register` + saved list
- [ ] Task 2 proved idempotence and handled no-match trap safely
- [ ] Section 6 closeout completed with all ✅ audit lines

---

## Author

**Kelvin R. Tobias**
