# Lab 09b: Hard and Soft Links (Ansible) — `ansible.builtin.file` (`state: link`, `state: hard`)

**Series:** linux-ops-mastery — Essential Tools & File Operations · **Lab 09b of the Novice → RHCA path**  
**Certifications covered:** RHCE EX294 (idempotent link management, `force:` semantics), RHCSA EX200 (the `ln` behavior underneath), DevOps (atomic release symlinks)  
**Prerequisite:** [Lab 09a](../lab-09a-hard-and-soft-links-rhcsa/) completed and a working control node  
**Time Estimate:** 25–35 minutes  
**Difficulty:** Beginner → Intermediate

---

## 🎯 Today's Focus Coverage

> Stay on-subject via the ANCHOR rows; expand vocabulary via the NEW rows. Every row is exercised by a STEP below.

**⚓ Anchor — already learned (on-topic reuse)**

| # | Command / switch | Covered by |
|---|---|---|
| A1 | `ansible.builtin.file` | _Task 1 · Step 1_ |
| A2 | `stat` (inode/link count) | _Task 1 · Step 2_ |

**🆕 NEW this lab — introduced for the first time** (minimum 3)

| # | Command / switch | First taught in | Covered by |
|---|---|---|---|
| N1 | `state: hard` | Task 1 · Step 1 | _Task 1 · Step 1_ |
| N2 | `state: link` | Task 2 · Step 1 | _Task 2 · Step 1_ |
| N3 | `force: true` (repoint) | Task 2 · Step 1 | _Task 2 · Step 1_ |
| N4 | `ansible.builtin.stat` module | Task 1 · Step 2 | _Task 1 · Step 2_ |

---

## 🎯 Objective

Reproduce Lab 09a's links as idempotent automation. `ansible.builtin.file` makes a hard link with `state: hard` and a symlink with `state: link`; both are state-aware, so a re-run reports `changed=0`. You will also meet `force: true`, which lets a symlink be repointed (or replace an existing file) — the mechanism behind atomic `current → release` deploys — and read link facts with the `ansible.builtin.stat` module.

---

## 🧠 Concept

The `file` module unifies links under `state:`. `state: hard` with `src:`/`path:` adds a second name for an inode; `state: link` makes a symbolic link to a path. Idempotence is automatic: if the link already points where you asked, `changed=0`. The catch is replacement — by default `file` will not clobber an existing path, so repointing a symlink (the deploy pattern) needs `force: true`. To verify, the `ansible.builtin.stat` module returns rich facts (`islnk`, `inode`, `nlink`, `lnk_target`) you can assert on.

```
SHELL (09a)                          ANSIBLE (09b)
─────────────────────────────       ──────────────────────────────────────
ln a b                               file: src=a path=b state=hard
ln -sf releases/v5 current           file: src=releases/v5 path=current state=link force=true
```

> **Why this matters:** A release switch is a one-line `force: true` symlink repoint. Knowing `state: link` + `force:` is exactly how RHCE/DevOps tasks express atomic version cutovers.

---

## 📚 Command Reference

| Command | Purpose | Critical flags |
|---|---|---|
| `ansible.builtin.file` `state: hard` | Create a hard link | `src:` (target) + `path:` (link name) |
| `ansible.builtin.file` `state: link` | Create a symbolic link | `src:` may be relative or absolute |
| `force: true` | Replace/repoint an existing path | required to move a symlink |
| `ansible.builtin.stat` | Return file facts | `islnk`, `inode`, `nlink`, `lnk_target` |
| `register:` + `debug:` | Read the link facts | assert on them |

---

## 🧰 LAB-WIDE SETUP

**In plain English:** Build the sandbox and playbook folder, a source file to hard-link, and two release directories to symlink between.

> Run this block **once** before Task 1. It builds the clean, private workspace that both tasks depend on.

```bash
export LAB_ROOT=/tmp/lab-09
mkdir -p "$LAB_ROOT/releases/v4" "$LAB_ROOT/releases/v5"
mkdir -p /root/rhcsa_journal/lab-09b/playbooks
echo "shared data" > "$LAB_ROOT/original.txt"
ls -l "$LAB_ROOT"
echo "exit was: $?"
```

**Expected output:**

```
-rw-r--r--. 1 root root 12 ... original.txt
drwxr-xr-x. 4 root root 30 ... releases
exit was: 0
```

---

## TASK 1 of 2 — Idempotent hard link with `state: hard`

**In plain English:** We write a play that hard-links a file and verifies the shared inode with the `stat` module.

---

### Step 1 of 2 — Write the hard-link playbook

**In plain English:** We create `task1.yml`, which makes a hard link and then reads its facts.

```yaml
---
- name: "Lab 09b Task 1 — idempotent hard link"
  hosts: localhost
  connection: local
  gather_facts: false
  vars:
    target: /tmp/lab-09/original.txt
    link: /tmp/lab-09/hardlink.txt
  tasks:
    - name: "Create a hard link (same inode)"
      ansible.builtin.file:
        src: "{{ target }}"
        path: "{{ link }}"
        state: hard
      register: link_result

    - name: "Read the link facts"
      ansible.builtin.stat:
        path: "{{ link }}"
      register: link_stat

    - name: "Show inode and link count"
      ansible.builtin.debug:
        msg:
          - "changed: {{ link_result.changed }}"
          - "inode: {{ link_stat.stat.inode }}"
          - "nlink: {{ link_stat.stat.nlink }}"
```

**Expected output:**

```
(this is the saved playbook file — no output until you run it in Step 2)
```

**Line-by-line breakdown:**

- `state: hard` with `src:`/`path:` → Make `path` a hard link to `src` (the same inode).
- `ansible.builtin.stat:` → Gather facts about the link, including `inode` and `nlink`.
- `debug:` → Print `changed`, the inode, and the link count.

**New words in this step:**

- **`state: hard`** — the `file` mode that creates a hard link.
- **`ansible.builtin.stat`** — the module that returns rich file metadata as facts.

---

### Step 2 of 2 — Run it twice and watch `changed=0`

**In plain English:** We run the play twice; the first creates the link (`changed=1`), and the second sees it already exists, reporting `changed=0` with `nlink: 2`.

```bash
ansible-playbook /root/rhcsa_journal/lab-09b/playbooks/task1.yml
ansible-playbook /root/rhcsa_journal/lab-09b/playbooks/task1.yml
stat -c '%i %h %n' /tmp/lab-09/original.txt /tmp/lab-09/hardlink.txt
echo "exit was: $?"
```

**Expected output:**

```
PLAY RECAP ********************************************************************
localhost                  : ok=3    changed=1    unreachable=0    failed=0
PLAY RECAP ********************************************************************
localhost                  : ok=3    changed=0    unreachable=0    failed=0
1310721 2 /tmp/lab-09/original.txt
1310721 2 /tmp/lab-09/hardlink.txt
exit was: 0
```

**Line-by-line breakdown:**

- two runs → `changed=1` then `changed=0`, proving `state: hard` is idempotent.
- `stat -c '%i %h %n' ...` → Both names share the inode and show `nlink=2`.

**New words in this step:**

- **`nlink`** — the hard-link count fact, the module's view of `stat -c %h`.

---

### Concept card (Task 1)

| Concept | What it does | Exam trap |
|---|---|---|
| `state: hard` | hard link via module | `src` must exist and be on same FS |
| `stat` module | link facts | use `.stat.inode`, `.stat.nlink` |
| idempotent link | re-run `changed=0` | recreating an identical link is a no-op |

---

### Troubleshoot (Task 1)

| Symptom | Likely cause | Fix |
|---|---|---|
| `cross-device` error | `src`/`path` on different FS | Use `state: link` instead |
| `src is required` | Missing `src:` | Provide both `src:` and `path:` |

---

## TASK 2 of 2 — Symlink repoint with `force: true`

**In plain English:** We write a play that points `current` at v4, then repoints it to v5 with `force: true` — the atomic deploy pattern.

---

### Step 1 of 2 — Write the symlink-repoint playbook

**In plain English:** We create `task2.yml`, which makes `current` a symlink and uses `force: true` so it can be moved from one release to another.

```yaml
---
- name: "Lab 09b Task 2 — atomic symlink repoint"
  hosts: localhost
  connection: local
  gather_facts: false
  vars:
    release: /tmp/lab-09/releases/v5
    current: /tmp/lab-09/current
  tasks:
    - name: "Point current at the chosen release (repointable)"
      ansible.builtin.file:
        src: "{{ release }}"
        path: "{{ current }}"
        state: link
        force: true
      register: link_result

    - name: "Show where current points"
      ansible.builtin.stat:
        path: "{{ current }}"
      register: cur_stat

    - name: "Report the symlink target"
      ansible.builtin.debug:
        msg:
          - "changed: {{ link_result.changed }}"
          - "is link: {{ cur_stat.stat.islnk }}"
          - "target: {{ cur_stat.stat.lnk_target }}"
```

**Expected output:**

```
(this is the saved playbook file — no output until you run it in Step 2)
```

**Line-by-line breakdown:**

- `state: link` + `force: true` → Make `current` a symlink; `force:` lets it replace an existing symlink/file, enabling a repoint.
- `ansible.builtin.stat:` → Read `islnk` and `lnk_target` to confirm where it points.

**New words in this step:**

- **`state: link`** — the `file` mode for symbolic links.
- **`force: true`** — allow `file` to overwrite/repoint an existing path.

---

### Step 2 of 2 — Run it, then prove a repoint with `force`

**In plain English:** We run the play (points at v5), then re-run with the variable flipped to v4 to prove `force: true` moves the symlink cleanly.

```bash
ansible-playbook /root/rhcsa_journal/lab-09b/playbooks/task2.yml
ansible-playbook -e release=/tmp/lab-09/releases/v4 /root/rhcsa_journal/lab-09b/playbooks/task2.yml
readlink /tmp/lab-09/current
echo "exit was: $?"
```

**Expected output:**

```
PLAY RECAP ********************************************************************
localhost                  : ok=3    changed=1    unreachable=0    failed=0
PLAY RECAP ********************************************************************
localhost                  : ok=3    changed=1    unreachable=0    failed=0
/tmp/lab-09/releases/v4
exit was: 0
```

**Line-by-line breakdown:**

- first run → Creates `current -> releases/v5`; `changed=1`.
- second run with `-e release=...v4` → `force: true` repoints `current` to v4; `changed=1` because the target differs.
- `readlink /tmp/lab-09/current` → Confirm the symlink now points at v4 — the atomic cutover.

**New words in this step:**

- **`-e var=value`** — pass an extra variable on the command line, overriding the default.

---

### Concept card (Task 2)

| Concept | What it does | Exam trap |
|---|---|---|
| `state: link` | symbolic link | without `force:`, won't replace existing |
| `force: true` | repoint/overwrite | needed for `current → release` swaps |
| `-e var=` | override at runtime | useful for parameterized deploys |

---

### Troubleshoot (Task 2)

| Symptom | Likely cause | Fix |
|---|---|---|
| `refusing to convert` error | Existing path, no `force:` | Add `force: true` |
| Re-run always `changed=1` | Target keeps changing | Expected when repointing to a new release |

---

## ✅ Lab Checklist

- [ ] Task 1 · Step 1 — Write the hard-link playbook
- [ ] Task 1 · Step 2 — Run it twice and watch `changed=0`
- [ ] Task 2 · Step 1 — Write the symlink-repoint playbook
- [ ] Task 2 · Step 2 — Run it, then prove a repoint with `force`
- [ ] Every 🎯 Focus Coverage row (Anchor + NEW) mapped to a step
- [ ] 🧹 Teardown run — sandbox + any system state removed

---

## 🧹 Teardown

**In plain English:** Delete everything this lab created so the box is clean for the next run.

> Run this after you've verified the lab. `lab_teardown.sh` safely removes the single sandbox root — it refuses to touch `/`, `$HOME`, or any protected path. This lab changed **no** system state.

```bash
bash lab_teardown.sh "$LAB_ROOT"     # = /tmp/lab-09
rm -rf /root/rhcsa_journal/lab-09b
```

**Expected output:**

```
✅ Removed /tmp/lab-09 — lab workspace is clean.
```

---

## ⚠️ Common Pitfalls

| Mistake | Symptom | Fix |
|---|---|---|
| Repoint without `force:` | Task fails on existing link | Add `force: true` |
| `state: hard` across filesystems | Cross-device error | Use `state: link` |
| Asserting on wrong stat field | Wrong verdict | Use `islnk`/`lnk_target`/`nlink` |

---

## 📌 Exam Strategy

Use `ansible.builtin.file` for links: `state: hard` or `state: link`, with `force: true` whenever you must replace or repoint. Verify with the `stat` module's `islnk`/`lnk_target`/`nlink`, and re-run to confirm idempotence (a stable link is `changed=0`).

- `force: true` is the deploy-cutover switch — memorize it.
- The `stat` module beats parsing `ls` for link facts.
- A re-run that stays `changed=0` proves a stable link.

---

## 🔗 Related Labs

- [Lab 09a — Hard and Soft Links (RHCSA)](../lab-09a-hard-and-soft-links-rhcsa/) — the `ln`/`ln -s` this play mirrors
- [Lab 09c — Hard and Soft Links (Verify)](../lab-09c-hard-and-soft-links-verify/) — prove inode sharing and resolution
- [Lab 08b — Copying Files (Ansible)](../lab-08b-copying-files-ansible/) — copy vs link, the deployment toolkit

---

## 👤 Author

**Kelvin R. Tobias**  
[kelvinintech.com](https://kelvinintech.com) · [GitHub](https://github.com/kelvintechnical) · [LinkedIn](https://www.linkedin.com/in/kelvin-r-tobias-211949219)
