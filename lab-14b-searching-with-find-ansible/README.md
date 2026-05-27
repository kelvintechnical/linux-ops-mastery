# Lab 14b: Searching with `find` (Ansible) — `ansible.builtin.find`

- **Series:** linux-ops-mastery — File Operations & Shell Fundamentals
- **Trilogy:** `14a` (RHCSA) → `14b` (Ansible) → `14c` (Verify)
- **Prerequisite:** Lab 14a complete
- **Time Estimate:** 25–35 minutes
- **Tasks:** 2
- **Practice Directory (rotation #14):** `/etc`
- **Traps rehearsed:** **T14-A** (unquoted patterns in playbooks) · **T14-B** (looping over `find` results one-by-one vs batching)

> **This lab's practice directory is: `/etc`** — Task 2 targets `/etc` with the same predicates as Lab 14a Task 2.

---

## Objective

Replace imperative `find` one-liners with declarative `ansible.builtin.find` tasks. Register results, loop with `loop` / `loop_control`, and emit the same `/root/conf-list.txt` artifact Lab 14a produced.

---

## Reference

| Shell (14a) | Ansible (14b) |
|---|---|
| `find /path -name '*.conf'` | `find: path=/path patterns="*.conf"` |
| `-type f` | `file_type: file` |
| `-user root` | `get_matched: true` + filter `item.pw_name == 'root'` OR use `owner: root` (2.14+) |
| `-mtime -90` | `age: 90d` with `age_stamp: mtime` |
| `-size +100c` | `size: 100` + `size_unit: b` (check version) |
| `-print0` | `register: result` → `result.files` list |

> **Note:** `ansible.builtin.find` does not support every `find(1)` predicate. For exotic cases, use `ansible.builtin.command` with `find` and `changed_when: false`.

---

## Lab-Wide Setup

```bash
sudo -i
mkdir -p /root/rhcsa_journal/lab-14b/playbooks
cd /root/rhcsa_journal/lab-14b
ansible --version | head -n 1
echo "exit was: $?"
```

Copy playbooks from this repo folder `playbooks/` into `/root/rhcsa_journal/lab-14b/playbooks/` or paste from Task sections below.

---

## Task 1 — Discover files under a sandbox path with `ansible.builtin.find`

**Practice directory this task:** `/etc` (warm-up reads) · writes under `/tmp/find-ansible-lab`.

### Warm-Up

```bash
find /etc -maxdepth 1 -type f -name '*.conf' 2>/dev/null | wc -l
ansible localhost -m ansible.builtin.setup -a 'filter=ansible_distribution' 2>/dev/null | head -n 3
test -d /root/rhcsa_journal/lab-14b && echo "journal dir OK"
echo "Warm-up done by $(whoami) at $(date -Is)"
```

### Purpose

Build a sandbox tree, run `ansible.builtin.find` with `patterns` and `file_type`, register `found_files`, and write a manifest with `ansible.builtin.copy` + `content` from `query('ansible.builtin.json_query', ...)`.

### WEAVE TRACE

| Warm-up command | Role inside Task 1 |
|---|---|
| `find /etc ... \| wc -l` | Baseline count — compare to Ansible `found_files \| length` |
| `ansible ... setup` | Confirms Ansible can reach localhost |
| `test -d` journal | Guards playbook path |
| `2>&1 \| tee` | Evidence capture |
| `$(date -Is)` | Journal stamp |

### Playbook — `playbooks/task1.yml`

See `playbooks/task1.yml` in this lab folder.

### Run

```bash
mkdir -p /tmp/find-ansible-lab
ansible-playbook /root/rhcsa_journal/lab-14b/playbooks/task1.yml \
  2>&1 | tee /root/rhcsa_journal/lab-14b/task1/op.txt
echo "exit was: $?"
```

### Expected output (excerpt)

```text
TASK [Find all .log files under sandbox] *************************
ok: [localhost]

TASK [Show match count] ******************************************
ok: [localhost] => {
    "msg": "Matched 3 .log files"
}
```

### Journal write

```bash
LAB=lab-14b
TASK=task1
JDIR="/root/rhcsa_journal/${LAB}/${TASK}"
mkdir -p "$JDIR"
cp /root/rhcsa_journal/lab-14b/task1/op.txt "$JDIR/evidence.txt" 2>/dev/null || true

cat > "$JDIR/done.txt" <<EOF
LAB:    ${LAB}
TASK:   ${TASK}
DATE:   $(date -Is)
STATUS: COMPLETE
EOF

cat > "$JDIR/notes.txt" <<EOF
TOPIC:    ansible.builtin.find — patterns, file_type, register
COMMANDS: find module, debug, copy with json_query
NEXT:     task2 — /etc capstone via Ansible
EOF
```

> **STOP — paste play recap before Task 2.**

---

## Task 2 — `/etc` capstone: same predicates as Lab 14a Task 2

**Practice directory this task:** `/etc`

### Warm-Up

```bash
wc -l /root/conf-list.txt 2>/dev/null || echo "(14a list removed — will regenerate)"
find /etc -type f -name '*.conf' -user root -mtime -90 -size +100c 2>/dev/null | wc -l
echo "Warm-up done at $(date -Is)"
```

### Purpose

Use `ansible.builtin.find` on `/etc` with `patterns`, `file_type`, `age`, and `size` filters; write `/root/conf-list-ansible.txt`; compare line count to a fresh shell `find` (T14-B: one module call vs many shell loops).

### Playbook — `playbooks/task2.yml`

See `playbooks/task2.yml` in this lab folder.

### Run

```bash
ansible-playbook /root/rhcsa_journal/lab-14b/playbooks/task2.yml \
  2>&1 | tee /root/rhcsa_journal/lab-14b/task2/op.txt

wc -l /root/conf-list-ansible.txt
find /etc -type f -name '*.conf' -user root -mtime -90 -size +100c 2>/dev/null | wc -l
echo "exit was: $?"
```

### PERSISTENCE CHECK

| Artifact | Verification |
|---|---|
| Ansible list | `test -s /root/conf-list-ansible.txt` |
| Count parity | `wc -l` matches shell find count |

### Journal write

```bash
LAB=lab-14b
TASK=task2
JDIR="/root/rhcsa_journal/${LAB}/${TASK}"
mkdir -p "$JDIR"
cp /root/rhcsa_journal/lab-14b/task2/op.txt "$JDIR/evidence.txt" 2>/dev/null || true
cp /root/conf-list-ansible.txt "$JDIR/" 2>/dev/null || true

cat > "$JDIR/done.txt" <<EOF
LAB:    ${LAB}
TASK:   ${TASK}
DATE:   $(date -Is)
STATUS: COMPLETE
EOF
```

### Cleanup

```bash
rm -rf /tmp/find-ansible-lab
rm -f /root/conf-list-ansible.txt
```

> **STOP — proceed to Lab 14c.**

---

## Lab 14b Checklist

- [ ] Task 1 — `ansible.builtin.find` on sandbox + registered manifest
- [ ] Task 2 — `/etc` capstone list matches shell find count

---

## Author

**Kelvin R. Tobias** — [kelvinintech.com](https://kelvinintech.com)
