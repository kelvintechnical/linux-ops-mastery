# Lab 27a: Safely Editing System Databases (RHCSA) — `vipw`, `vigr`, locking

**Series:** linux-ops-mastery — Users & Groups · **Lab 27a of the Novice → RHCA path**  
**Certifications covered:** RHCSA EX200 (safely editing the account databases), SRE/DevOps (avoiding corrupt `/etc/passwd` during concurrent edits)  
**Prerequisite:** [Lab 26c](../lab-26c-vi-editor-verify/) completed · **root/sudo required**  
**Time Estimate:** 25–35 minutes  
**Difficulty:** Intermediate

---

## 🎯 Today's Focus Coverage

> Stay on-subject via the ANCHOR rows; expand vocabulary via the NEW rows. Every row is exercised by a STEP below.

**⚓ Anchor — already learned (on-topic reuse)**

| # | Command / switch | Covered by |
|---|---|---|
| A1 | `EDITOR=` environment | _Task 1 · Step 1_ |
| A2 | `getent` lookups | _Task 2 · Step 2_ |

**🆕 NEW this lab — introduced for the first time** (minimum 3)

| # | Command / switch | First taught in | Covered by |
|---|---|---|---|
| N1 | `vipw` (locked passwd edit) | Task 1 · Step 1 | _Task 1 · Step 1_ |
| N2 | `vipw -s` (shadow) | Task 1 · Step 2 | _Task 1 · Step 2_ |
| N3 | `vigr` / `vigr -s` (group/gshadow) | Task 2 · Step 1 | _Task 2 · Step 1_ |
| N4 | `pwck` / `grpck` consistency | Task 2 · Step 2 | _Task 2 · Step 2_ |

---

## 🎯 Objective

Edit the account databases the *safe* way. You will open `/etc/passwd` under a lock with `vipw`, edit the shadow file with `vipw -s`, add a group with `vigr`, and verify database consistency with `pwck`/`grpck`. The point is the lock: `vipw`/`vigr` serialize edits so a second editor (or `useradd` running concurrently) can't corrupt the file.

> **⚠️ System-state lab.** This lab touches real account databases. It only *reads* `/etc/passwd`/`/etc/shadow` and adds **one clearly-named test group** (`labtest99`) that the Teardown removes. Do this on a practice VM.

---

## 🧠 Concept

`/etc/passwd`, `/etc/shadow`, `/etc/group`, and `/etc/gshadow` are edited constantly by tools like `useradd`. Editing them by hand with plain `vi` risks a race: if `useradd` writes while you're saving, one set of changes is lost and the file can corrupt. `vipw` solves this by taking the same lock those tools use (`/etc/.pwd.lock`) before opening the file in your `$EDITOR`, releasing it on save. `vipw` edits `/etc/passwd`; `vipw -s` edits `/etc/shadow`; `vigr` edits `/etc/group`; `vigr -s` edits `/etc/gshadow`. After editing passwd it offers to run `vipw -s` to keep shadow in sync. `pwck`/`grpck` then check the databases for consistency (missing fields, bad UIDs, orphaned shadow entries).

```
vipw            → lock + edit /etc/passwd in $EDITOR
vipw -s         → edit /etc/shadow (passwords)
vigr            → lock + edit /etc/group
vigr -s         → edit /etc/gshadow
pwck / grpck    → verify passwd / group consistency
```

> **Why this matters:** Hand-editing account files without a lock is how production boxes end up with a broken `/etc/passwd` and locked-out root. `vipw`/`vigr` are the disciplined way, and the exam expects you to know them.

---

## 📚 Command Reference

| Command | Purpose | Notes |
|---|---|---|
| `vipw` | Edit `/etc/passwd` locked | uses `$EDITOR` |
| `vipw -s` | Edit `/etc/shadow` locked | passwords |
| `vigr` | Edit `/etc/group` locked | groups |
| `vigr -s` | Edit `/etc/gshadow` locked | group passwords |
| `pwck` | Check passwd/shadow | consistency |
| `grpck` | Check group/gshadow | consistency |
| `getent` | Query a database | NSS-aware |

---

## 🧰 LAB-WIDE SETUP

**In plain English:** Build a sandbox for editor scripts; the databases themselves live in `/etc`.

> Run this block **once** before Task 1. `LAB_ROOT` holds only the helper editor scripts; the system databases are edited in place (and reverted in Teardown).

```bash
export LAB_ROOT=/tmp/lab-27
mkdir -p "$LAB_ROOT"
cd "$LAB_ROOT"
# A non-interactive "editor" that appends one test group line, then exits.
cat > add_group_editor.sh <<'EOF'
#!/bin/bash
grep -q '^labtest99:' "$1" || echo 'labtest99:x:6999:' >> "$1"
EOF
chmod +x add_group_editor.sh
echo "setup done"
echo "exit was: $?"
```

**Expected output:**

```
setup done
exit was: 0
```

---

## TASK 1 of 2 — Locked reads of passwd and shadow

**In plain English:** We open the account files under their lock without changing them.

---

### Step 1 of 2 — Open `/etc/passwd` under lock with `vipw`

**In plain English:** We use a read-only "editor" (`cat`) so `vipw` takes the lock and shows the file without modifying it.

```bash
sudo EDITOR=/bin/cat vipw
echo "exit was: $?"
```

**Expected output:**

```
root:x:0:0:root:/root:/bin/bash
bin:x:1:1:bin:/bin:/sbin/nologin
... (full /etc/passwd printed by cat) ...
You have modified /etc/passwd.
You may need to modify /etc/shadow for consistency.
Please use the command 'vipw -s' to do so.
exit was: 0
```

**Line-by-line breakdown:**

- `sudo EDITOR=/bin/cat vipw` → `vipw` takes the passwd lock, then runs our "editor" (`cat`), which just prints the file — a safe, no-change demonstration of the locked workflow.
- the reminder about `vipw -s` → `vipw` always nudges you to keep shadow in sync after a passwd edit.

**New words in this step:**

- **`vipw`** — edit `/etc/passwd` while holding the account lock.
- **lock** — the `/etc/.pwd.lock` serialization that prevents concurrent corruption.

---

### Step 2 of 2 — Open `/etc/shadow` with `vipw -s`

**In plain English:** We read the shadow file under lock, again with a non-editing editor.

```bash
sudo EDITOR=/bin/cat vipw -s
echo "exit was: $?"
```

**Expected output:**

```
root:$6$...:19000:0:99999:7:::
bin:*:19000:0:99999:7:::
... (full /etc/shadow printed by cat) ...
exit was: 0
```

**Line-by-line breakdown:**

- `sudo EDITOR=/bin/cat vipw -s` → `-s` targets `/etc/shadow`; the same locking applies to the password hashes.

**New words in this step:**

- **`vipw -s`** — edit the shadow password file under lock.

---

### Concept card (Task 1)

| Concept | What it does | Exam trap |
|---|---|---|
| `vipw` | locked passwd edit | not plain `vi /etc/passwd` |
| `-s` | shadow variant | keep in sync with passwd |
| `$EDITOR` | which editor opens | set it to control behavior |

---

### Troubleshoot (Task 1)

| Symptom | Likely cause | Fix |
|---|---|---|
| "Cannot lock" | Another edit in progress | Wait/close the other editor |
| Opens unexpected editor | `$EDITOR` unset | Export `EDITOR` first |

---

## TASK 2 of 2 — Add a group with vigr and verify

**In plain English:** We add a clearly-named test group under lock, then check consistency.

---

### Step 1 of 2 — Add a test group with `vigr`

**In plain English:** We point `vigr` at a scripted editor that appends one test group, demonstrating a locked group edit.

```bash
cd "$LAB_ROOT"
sudo EDITOR="$LAB_ROOT/add_group_editor.sh" vigr
getent group labtest99
echo "exit was: $?"
```

**Expected output:**

```
labtest99:x:6999:
exit was: 0
```

**Line-by-line breakdown:**

- `sudo EDITOR=.../add_group_editor.sh vigr` → `vigr` locks `/etc/group`, then runs our script which appends `labtest99:x:6999:` (idempotently — it checks first).
- `getent group labtest99` → Confirms the group now exists in the database.

**New words in this step:**

- **`vigr`** — edit `/etc/group` while holding the group lock.

---

### Step 2 of 2 — Check consistency with `grpck` and `pwck`

**In plain English:** We verify the group and passwd databases are internally consistent.

```bash
sudo grpck -r; echo "grpck rc: $?"
sudo pwck -r; echo "pwck rc: $?"
```

**Expected output:**

```
grpck rc: 0
pwck rc: 0
```

**Line-by-line breakdown:**

- `sudo grpck -r` → Read-only (`-r`) consistency check of `/etc/group`/`/etc/gshadow`; rc 0 means no problems.
- `sudo pwck -r` → Same for `/etc/passwd`/`/etc/shadow`.

**New words in this step:**

- **`grpck` / `pwck`** — consistency checkers for the group and password databases.

---

### Concept card (Task 2)

| Concept | What it does | Exam trap |
|---|---|---|
| `vigr` | locked group edit | `-s` for gshadow |
| `grpck -r` | read-only check | `-r` avoids prompts |
| `pwck -r` | read-only check | catches orphans |

---

### Troubleshoot (Task 2)

| Symptom | Likely cause | Fix |
|---|---|---|
| Duplicate group | Edited twice | Script checks first; remove dup |
| `pwck` reports orphan | shadow/passwd mismatch | Sync with `vipw -s` |

---

## ✅ Lab Checklist

- [ ] Task 1 · Step 1 — Open `/etc/passwd` under lock with `vipw`
- [ ] Task 1 · Step 2 — Open `/etc/shadow` with `vipw -s`
- [ ] Task 2 · Step 1 — Add a test group with `vigr`
- [ ] Task 2 · Step 2 — Check consistency with `grpck` and `pwck`
- [ ] Every 🎯 Focus Coverage row (Anchor + NEW) mapped to a step
- [ ] 🧹 Teardown run — sandbox + **test group removed**

---

## 🧹 Teardown

**In plain English:** Remove the test group from the real database and delete the sandbox.

> This lab changed system state (added `labtest99`). The first command **reverses** that change; then `lab_teardown.sh` removes the helper-script sandbox.

```bash
sudo groupdel labtest99 2>/dev/null || true
getent group labtest99 || echo "labtest99 removed"
cd /tmp
bash lab_teardown.sh "$LAB_ROOT"     # = /tmp/lab-27
```

**Expected output:**

```
labtest99 removed
✅ Removed /tmp/lab-27 — lab workspace is clean.
```

---

## ⚠️ Common Pitfalls

| Mistake | Symptom | Fix |
|---|---|---|
| `vi /etc/passwd` directly | Race/corruption risk | Use `vipw` for the lock |
| Editing passwd, not shadow | Account inconsistency | Run `vipw -s` too |
| Skipping `pwck`/`grpck` | Latent corruption | Check after edits |

---

## 📌 Exam Strategy

Never hand-edit account files with plain `vi` — use `vipw`/`vigr` so the lock protects you, keep `/etc/shadow` in sync with `vipw -s`, and validate with `pwck`/`grpck`. In real automation you'd use the `user`/`group` modules (Lab 27b), which handle the locking for you.

- `vipw` over `vi /etc/passwd`, always.
- Edit shadow with `vipw -s` to stay consistent.
- `pwck -r`/`grpck -r` are safe read-only checks.

---

## 🔗 Related Labs

- [Lab 27b — Safely Editing System Databases (Ansible)](../lab-27b-vipw-vigr-safe-editing-ansible/) — `user`/`group` modules do the locking
- [Lab 27c — Safely Editing System Databases (Verify)](../lab-27c-vipw-vigr-safe-editing-verify/) — prove consistency and cleanup
- [Lab 26a — Command/Insert Mode in vi (RHCSA)](../lab-26a-vi-editor-rhcsa/) — the editor `vipw` invokes

---

## 👤 Author

**Kelvin R. Tobias**  
[kelvinintech.com](https://kelvinintech.com) · [GitHub](https://github.com/kelvintechnical) · [LinkedIn](https://www.linkedin.com/in/kelvin-r-tobias-211949219)
