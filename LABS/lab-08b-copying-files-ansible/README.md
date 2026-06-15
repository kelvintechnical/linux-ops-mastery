# Lab 08b: Copying Files and Directories (Ansible) — `ansible.builtin.copy` (`remote_src`, `backup`)

**Series:** linux-ops-mastery — Essential Tools & File Operations · **Lab 08b of the Novice → RHCA path**  
**Certifications covered:** RHCE EX294 (idempotent file copies with mode/owner/backup), RHCSA EX200 (the `cp` behavior underneath), DevOps (safe config rollout with backups)  
**Prerequisite:** [Lab 08a](../lab-08a-copying-files-rhcsa/) completed and a working control node  
**Time Estimate:** 25–35 minutes  
**Difficulty:** Beginner → Intermediate

---

## 🎯 Today's Focus Coverage

> Stay on-subject via the ANCHOR rows; expand vocabulary via the NEW rows. Every row is exercised by a STEP below.

**⚓ Anchor — already learned (on-topic reuse)**

| # | Command / switch | Covered by |
|---|---|---|
| A1 | `ansible.builtin.copy` | _Task 1 · Step 1_ |
| A2 | `mode:` | _Task 1 · Step 1_ |

**🆕 NEW this lab — introduced for the first time** (minimum 3)

| # | Command / switch | First taught in | Covered by |
|---|---|---|---|
| N1 | `remote_src: true` | Task 1 · Step 1 | _Task 1 · Step 1_ |
| N2 | `backup: true` | Task 2 · Step 1 | _Task 2 · Step 1_ |
| N3 | `owner:` / `group:` | Task 1 · Step 1 | _Task 1 · Step 1_ |
| N4 | `backup_file` return value | Task 2 · Step 2 | _Task 2 · Step 2_ |

---

## 🎯 Objective

Reproduce Lab 08a's faithful copies in Ansible. You will copy a file *already on the target* with `remote_src: true` (the `cp` equivalent, versus pushing from the control node), set `mode`/`owner`/`group` declaratively, and turn on `backup: true` so any overwrite saves a timestamped copy first. Run twice to prove `changed=0`, and inspect the `backup_file` return so a rollback is always one path away.

---

## 🧠 Concept

`ansible.builtin.copy` has two source modes. By default `src:` is a file on the **control node** that gets pushed out. With `remote_src: true`, `src:` is a path already on the **target** — exactly what `cp` does locally. Either way the module is idempotent: it hashes source and destination and only writes on difference. `mode`/`owner`/`group` set metadata declaratively (the `--preserve` story, but explicit). `backup: true` makes the module copy the old destination to a `dest.TIMESTAMP~` file before overwriting, and returns that path in `backup_file` for easy rollback.

```
SHELL (08a)                          ANSIBLE (08b)
─────────────────────────────       ──────────────────────────────────────
cp -a src dst                        copy: src=src dest=dst remote_src=true mode=...
cp dst dst.bak ; cp new dst          copy: ... backup=true   → backup_file returned
```

> **Why this matters:** Overwriting a config without a backup is how outages become unrecoverable. `backup: true` plus the returned `backup_file` is the exam-safe, production-safe way to replace files.

---

## 📚 Command Reference

| Command | Purpose | Critical flags |
|---|---|---|
| `ansible.builtin.copy` | Copy a file idempotently | hashes src vs dest; writes only on change |
| `remote_src: true` | Source is on the target, not control node | the `cp` equivalent |
| `mode` / `owner` / `group` | Set metadata declaratively | `mode: '0640'` etc. |
| `backup: true` | Save the old dest before overwrite | returns `backup_file` |
| `register:` + `debug:` | Read `changed` / `backup_file` | rollback path lives here |

---

## 🧰 LAB-WIDE SETUP

**In plain English:** Build the sandbox and durable playbook folder, and seed a source file already on this host so `remote_src` has something to copy.

> Run this block **once** before Task 1. It builds the clean, private workspace that both tasks depend on.

```bash
export LAB_ROOT=/tmp/lab-08
mkdir -p "$LAB_ROOT/src"
mkdir -p /root/rhcsa_journal/lab-08b/playbooks
echo "key=value" > "$LAB_ROOT/src/app.conf"
ls -l "$LAB_ROOT/src"
echo "exit was: $?"
```

**Expected output:**

```
-rw-r--r--. 1 root root 10 Jun 15 18:45 app.conf
exit was: 0
```

---

## TASK 1 of 2 — Local copy with `remote_src` and metadata

**In plain English:** We write a play that copies a file already on the target, setting mode and owner, and prove it converges to `changed=0`.

---

### Step 1 of 2 — Write the `remote_src` copy playbook

**In plain English:** We create `task1.yml`, which copies the sandbox source file to a destination on the same host with explicit mode and owner.

```yaml
---
- name: "Lab 08b Task 1 — local copy with metadata"
  hosts: localhost
  connection: local
  gather_facts: false
  become: true
  vars:
    src_file: /tmp/lab-08/src/app.conf
    dst_file: /tmp/lab-08/deployed.conf
  tasks:
    - name: "Copy a file already on the target (remote_src)"
      ansible.builtin.copy:
        src: "{{ src_file }}"
        dest: "{{ dst_file }}"
        remote_src: true
        mode: '0640'
        owner: root
        group: root
      register: copy_result

    - name: "Show whether the copy changed anything"
      ansible.builtin.debug:
        msg: "changed: {{ copy_result.changed }}"
```

**Expected output:**

```
(this is the saved playbook file — no output until you run it in Step 2)
```

**Line-by-line breakdown:**

- `remote_src: true` → Treat `src:` as a path on the target, not on the control node — the `cp` equivalent.
- `mode/owner/group` → Set the destination's metadata declaratively, the explicit version of `--preserve`.
- `register:` + `debug:` → Capture and print the `changed` flag.

**New words in this step:**

- **`remote_src: true`** — copy from a source that lives on the managed host itself.

---

### Step 2 of 2 — Run it twice and watch `changed=0` on the re-run

**In plain English:** We run the play twice; the first creates the copy, and the second sees identical content and metadata, reporting `changed=0`.

```bash
ansible-playbook /root/rhcsa_journal/lab-08b/playbooks/task1.yml
ansible-playbook /root/rhcsa_journal/lab-08b/playbooks/task1.yml
stat -c '%U:%G %a %n' /tmp/lab-08/deployed.conf
echo "exit was: $?"
```

**Expected output:**

```
PLAY RECAP ********************************************************************
localhost                  : ok=2    changed=1    unreachable=0    failed=0
PLAY RECAP ********************************************************************
localhost                  : ok=2    changed=0    unreachable=0    failed=0
root:root 640 /tmp/lab-08/deployed.conf
exit was: 0
```

**Line-by-line breakdown:**

- first run → Creates `deployed.conf` with the requested mode/owner; `changed=1`.
- second run → Content and metadata already match; `changed=0` — the idempotence proof.
- `stat -c '%U:%G %a %n' ...` → Confirm the destination has mode 640 and root ownership.

**New words in this step:**

- **content hash** — Ansible compares source/dest hashes to decide whether to write.

---

### Concept card (Task 1)

| Concept | What it does | Exam trap |
|---|---|---|
| `remote_src: true` | source on the target | omit it and Ansible looks on the control node |
| `mode/owner/group` | declarative metadata | strings like `'0640'` keep the leading zero |
| idempotent copy | writes only on drift | re-run must be `changed=0` |

---

### Troubleshoot (Task 1)

| Symptom | Likely cause | Fix |
|---|---|---|
| `Could not find src` | Missing `remote_src: true` | Add it for on-target sources |
| Mode shows `0750` not `0640` | Quotes dropped on mode | Quote it: `mode: '0640'` |

---

## TASK 2 of 2 — Safe overwrite with `backup: true`

**In plain English:** We change the source, copy again with `backup: true`, and read the returned `backup_file` so the old version is recoverable.

---

### Step 1 of 2 — Write the backup-on-overwrite playbook

**In plain English:** We create `task2.yml`, which copies a (possibly changed) source over the destination and keeps a timestamped backup of whatever was there.

```yaml
---
- name: "Lab 08b Task 2 — overwrite with a backup"
  hosts: localhost
  connection: local
  gather_facts: false
  become: true
  vars:
    src_file: /tmp/lab-08/src/app.conf
    dst_file: /tmp/lab-08/deployed.conf
  tasks:
    - name: "Mutate the source so the next copy differs"
      ansible.builtin.copy:
        dest: "{{ src_file }}"
        content: "key=value\nupdated=true\n"
        mode: '0644'

    - name: "Copy over the destination, backing up the old version"
      ansible.builtin.copy:
        src: "{{ src_file }}"
        dest: "{{ dst_file }}"
        remote_src: true
        mode: '0640'
        backup: true
      register: copy_result

    - name: "Show the backup path (rollback target)"
      ansible.builtin.debug:
        msg: "backup_file: {{ copy_result.backup_file | default('none — no overwrite needed') }}"
```

**Expected output:**

```
(this is the saved playbook file — no output until you run it in Step 2)
```

**Line-by-line breakdown:**

- first `copy:` (content) → Change the source so the destination is genuinely out of date.
- second `copy:` with `backup: true` → Overwrite the destination, but first save the old one as `deployed.conf.TIMESTAMP~`.
- `debug: backup_file` → Print the saved path so you know exactly how to roll back.

**New words in this step:**

- **`backup: true`** — save the prior destination before overwriting.
- **`backup_file`** — the return value holding the saved backup's path.

---

### Step 2 of 2 — Run it and confirm the backup exists

**In plain English:** We run the play once and confirm a timestamped backup of the old file was created.

```bash
ansible-playbook /root/rhcsa_journal/lab-08b/playbooks/task2.yml
ls -1 /tmp/lab-08/deployed.conf*
echo "exit was: $?"
```

**Expected output:**

```
TASK [Show the backup path (rollback target)] ******************************
ok: [localhost] => {
    "msg": "backup_file: /tmp/lab-08/deployed.conf.18-45-10.2026-06-15@...~"
}
/tmp/lab-08/deployed.conf
/tmp/lab-08/deployed.conf.18-45-10.2026-06-15@...~
exit was: 0
```

**Line-by-line breakdown:**

- `ansible-playbook ...task2.yml` → Mutate the source, copy with backup; the debug line prints the backup path.
- `ls -1 /tmp/lab-08/deployed.conf*` → List the live file and its timestamped backup, proving the safety net.

**New words in this step:**

- **rollback** — restoring the previous version by copying the backup file back over the destination.

---

### Concept card (Task 2)

| Concept | What it does | Exam trap |
|---|---|---|
| `backup: true` | timestamped safety copy | only created when an overwrite happens |
| `backup_file` | rollback path | empty when no change occurred |
| content `copy:` | mutate then re-copy | drives the overwrite that triggers backup |

---

### Troubleshoot (Task 2)

| Symptom | Likely cause | Fix |
|---|---|---|
| No backup created | Destination already matched | Backups only happen on overwrite |
| `backup_file` is empty | `changed=false` this run | Change the source first |

---

## ✅ Lab Checklist

- [ ] Task 1 · Step 1 — Write the `remote_src` copy playbook
- [ ] Task 1 · Step 2 — Run it twice and watch `changed=0` on the re-run
- [ ] Task 2 · Step 1 — Write the backup-on-overwrite playbook
- [ ] Task 2 · Step 2 — Run it and confirm the backup exists
- [ ] Every 🎯 Focus Coverage row (Anchor + NEW) mapped to a step
- [ ] 🧹 Teardown run — sandbox + any system state removed

---

## 🧹 Teardown

**In plain English:** Delete everything this lab created so the box is clean for the next run.

> Run this after you've verified the lab. `lab_teardown.sh` safely removes the single sandbox root — it refuses to touch `/`, `$HOME`, or any protected path. This lab changed **no** system state.

```bash
bash lab_teardown.sh "$LAB_ROOT"     # = /tmp/lab-08
rm -rf /root/rhcsa_journal/lab-08b
```

**Expected output:**

```
✅ Removed /tmp/lab-08 — lab workspace is clean.
```

---

## ⚠️ Common Pitfalls

| Mistake | Symptom | Fix |
|---|---|---|
| Forgetting `remote_src: true` | Ansible looks on control node | Add it for on-target copies |
| Overwriting without `backup` | No way to roll back | Set `backup: true` for config replacements |
| Unquoted `mode` | Octal misread | Quote: `mode: '0640'` |

---

## 📌 Exam Strategy

Use `ansible.builtin.copy` for files; add `remote_src: true` when the source is already on the host, set `mode`/`owner`/`group` explicitly, and always `backup: true` when replacing something important. Read `backup_file` so a rollback is trivial.

- `backup: true` is cheap insurance — use it on every config overwrite.
- Set metadata in the module; do not rely on default umask.
- Re-run to confirm `changed=0` before moving on.

---

## 🔗 Related Labs

- [Lab 08a — Copying Files (RHCSA)](../lab-08a-copying-files-rhcsa/) — the `cp -a`/`--preserve` this play mirrors
- [Lab 08c — Copying Files (Verify)](../lab-08c-copying-files-verify/) — prove copies are faithful with `diff -r` and hashes
- [Lab 10b — Moving and Renaming Files (Ansible)](../lab-10b-moving-renaming-files-ansible/) — the move counterpart with `command: mv`

---

## 👤 Author

**Kelvin R. Tobias**  
[kelvinintech.com](https://kelvinintech.com) · [GitHub](https://github.com/kelvintechnical) · [LinkedIn](https://www.linkedin.com/in/kelvin-r-tobias-211949219)
