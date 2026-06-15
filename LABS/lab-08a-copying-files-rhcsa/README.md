# Lab 08a: Copying Files and Directories (RHCSA) — `cp -a`, `cp --preserve`

**Series:** linux-ops-mastery — Essential Tools & File Operations · **Lab 08a of the Novice → RHCA path**  
**Certifications covered:** RHCSA EX200 (copying while preserving permissions/SELinux context), RHCE EX294 (the `copy` module behavior underneath), SRE/DevOps (faithful backups and deployments)  
**Prerequisite:** [Lab 07c](../lab-07c-touch-timestamps-verify/) completed  
**Time Estimate:** 25–35 minutes  
**Difficulty:** Beginner → Intermediate

---

## 🎯 Today's Focus Coverage

> Stay on-subject via the ANCHOR rows; expand vocabulary via the NEW rows. Every row is exercised by a STEP below.

**⚓ Anchor — already learned (on-topic reuse)**

| # | Command / switch | Covered by |
|---|---|---|
| A1 | `cp` | _Task 1 · Step 1_ |
| A2 | `stat` | _Task 1 · Step 2_ |

**🆕 NEW this lab — introduced for the first time** (minimum 3)

| # | Command / switch | First taught in | Covered by |
|---|---|---|---|
| N1 | `cp -R` | Task 1 · Step 1 | _Task 1 · Step 1_ |
| N2 | `cp -a` (archive) | Task 1 · Step 2 | _Task 1 · Step 2_ |
| N3 | `cp --preserve=mode,timestamps,context` | Task 2 · Step 1 | _Task 2 · Step 1_ |
| N4 | `cp --no-preserve=ownership` | Task 2 · Step 2 | _Task 2 · Step 2_ |

---

## 🎯 Objective

Copy files and whole directory trees the way the exam demands: faithfully. You will recurse a tree with `cp -R`, make a byte-and-metadata-perfect clone with `cp -a`, then dial preservation precisely with `--preserve=mode,timestamps,context` and `--no-preserve=ownership`. By the end you can reproduce `/etc/skel`-style copies that keep permissions and SELinux labels intact — the difference between a working deployment and a "permission denied" mystery.

---

## 🧠 Concept

`cp` defaults to a *shallow* copy that drops most metadata and resets timestamps and ownership to the copier. `-R` recurses into directories. `-a` ("archive") is the faithful clone: it implies `-R`, preserves mode, ownership, timestamps, symlinks, and SELinux context. When you need finer control, `--preserve=LIST` keeps exactly the attributes you name and `--no-preserve=LIST` drops some. On SELinux systems, forgetting `context` is the classic reason a copied config stops working.

```
cp file copy                 → new mtime, copier owns it, default context
cp -R dir/ dest/             → recurse, but still resets metadata
cp -a dir/ dest/             → faithful: mode+owner+time+symlink+context
cp --preserve=mode,timestamps,context src dst   → keep those three only
cp --no-preserve=ownership ... → keep most, but reset owner to you
```

> **Why this matters:** A copied web file with the wrong SELinux context is served as a 403. `cp -a` (or `--preserve=context`) is how you keep the label so the service still works after a copy.

---

## 📚 Command Reference

| Command | Purpose | Critical flags |
|---|---|---|
| `cp` | Copy files | shallow by default — drops metadata |
| `cp -R` | Recurse into directories | needed for any directory copy |
| `cp -a` | Archive: faithful recursive copy | = `-dR --preserve=all` |
| `cp --preserve=LIST` | Keep named attributes | `mode,ownership,timestamps,context,all` |
| `cp --no-preserve=LIST` | Drop named attributes | combine with `-a` to keep all-but-one |

---

## 🧰 LAB-WIDE SETUP

**In plain English:** Build a sandbox with a small source tree whose files have non-default permissions and times, so copies have something meaningful to preserve.

> Run this block **once** before Task 1. It defines a single sandbox root
> (`LAB_ROOT`) that every file in this lab lives under, so the Teardown
> section can wipe it in one safe command.

```bash
export LAB_ROOT=/tmp/lab-08
mkdir -p "$LAB_ROOT/src/conf"
cd "$LAB_ROOT"
echo "key=value" > src/conf/app.conf
chmod 640 src/conf/app.conf
touch -t 202601010000 src/conf/app.conf
ls -l src/conf
echo "exit was: $?"
```

**Expected output:**

```
-rw-r-----. 1 root root 10 2026-01-01 00:00 app.conf
exit was: 0
```

---

## TASK 1 of 2 — Recursive and archive copies

**In plain English:** We copy a tree with `cp -R`, then a faithful clone with `cp -a`, and compare what each preserved.

---

### Step 1 of 2 — Recurse a tree with `cp -R`

**In plain English:** We copy the whole source directory into a new destination and confirm the structure came across.

```bash
cd "$LAB_ROOT"
cp -R src dest_R
ls -l dest_R/conf/app.conf
echo "exit was: $?"
```

**Expected output:**

```
-rw-r-----. 1 root root 10 2026-01-01 00:00 app.conf
exit was: 0
```

**Line-by-line breakdown:**

- `cp -R src dest_R` → Recursively copy the `src` tree to `dest_R`; `-R` is required for directories.
- `ls -l dest_R/conf/app.conf` → On modern GNU `cp`, `-R` keeps mode; note ownership/time behavior varies — `-a` is the guaranteed faithful option (next step).

**New words in this step:**

- **recursive copy** — copying a directory and everything inside it, not just one file.

---

### Step 2 of 2 — Faithful clone with `cp -a`

**In plain English:** We make an archive copy that preserves mode, timestamps, and SELinux context exactly, then read the metadata to confirm.

```bash
cd "$LAB_ROOT"
cp -a src dest_a
stat -c '%a %y %C %n' src/conf/app.conf dest_a/conf/app.conf
echo "exit was: $?"
```

**Expected output:**

```
640 2026-01-01 00:00:00.000000000 -0500 unconfined_u:object_r:user_tmp_t:s0 src/conf/app.conf
640 2026-01-01 00:00:00.000000000 -0500 unconfined_u:object_r:user_tmp_t:s0 dest_a/conf/app.conf
exit was: 0
```

**Line-by-line breakdown:**

- `cp -a src dest_a` → Archive copy: implies `-R` and `--preserve=all`, so mode, owner, mtime, symlinks, and context all carry over.
- `stat -c '%a %y %C %n' ...` → Compare mode (`%a`), mtime (`%y`), context (`%C`), and name; source and copy match exactly.

**New words in this step:**

- **`cp -a` (archive)** — the faithful copy that preserves all metadata, the go-to for backups.

---

### Concept card (Task 1)

| Concept | What it does | Exam trap |
|---|---|---|
| `cp -R` | recurse directories | may reset times/owner depending on flags |
| `cp -a` | faithful clone | the safe default for "copy and keep everything" |
| SELinux context | `%C` field | a plain `cp` can drop it, breaking services |

---

### Troubleshoot (Task 1)

| Symptom | Likely cause | Fix |
|---|---|---|
| `omitting directory` | Copied a dir without `-R`/`-a` | Add `-R` or `-a` |
| Copy has wrong context | Plain `cp` reset it | Use `cp -a` or `--preserve=context` |

---

## TASK 2 of 2 — Precise preservation control

**In plain English:** We keep exactly the attributes we name with `--preserve`, then deliberately drop ownership with `--no-preserve`.

---

### Step 1 of 2 — Keep specific attributes with `--preserve`

**In plain English:** We copy a file keeping only mode, timestamps, and SELinux context, and confirm those three carried over.

```bash
cd "$LAB_ROOT"
cp --preserve=mode,timestamps,context src/conf/app.conf preserved.conf
stat -c '%a %y %C %n' src/conf/app.conf preserved.conf
echo "exit was: $?"
```

**Expected output:**

```
640 2026-01-01 00:00:00.000000000 -0500 unconfined_u:object_r:user_tmp_t:s0 src/conf/app.conf
640 2026-01-01 00:00:00.000000000 -0500 unconfined_u:object_r:user_tmp_t:s0 preserved.conf
exit was: 0
```

**Line-by-line breakdown:**

- `cp --preserve=mode,timestamps,context ...` → Keep exactly those three attributes; everything else (like ownership) resets to default.
- `stat -c '%a %y %C %n' ...` → Confirm mode, mtime, and context match the source.

**New words in this step:**

- **`--preserve=LIST`** — keep only the named attributes during a copy.

---

### Step 2 of 2 — Drop ownership with `--no-preserve`

**In plain English:** We make an otherwise-faithful copy but explicitly reset ownership, simulating handing a file to a different account.

```bash
cd "$LAB_ROOT"
cp -a --no-preserve=ownership src/conf/app.conf reowned.conf
stat -c '%U:%G %a %n' src/conf/app.conf reowned.conf
echo "exit was: $?"
```

**Expected output:**

```
root:root 640 src/conf/app.conf
root:root 640 reowned.conf
exit was: 0
```

**Line-by-line breakdown:**

- `cp -a --no-preserve=ownership ...` → Start from a faithful `-a` copy but drop ownership preservation, so the copy is owned by the copier.
- `stat -c '%U:%G %a %n' ...` → Compare owner:group and mode; mode is preserved while ownership is reset (both show root here since root ran it).

**New words in this step:**

- **`--no-preserve=LIST`** — drop the named attributes even when `-a` would otherwise keep them.

---

### Concept card (Task 2)

| Concept | What it does | Exam trap |
|---|---|---|
| `--preserve=context` | keeps SELinux label | omit it and services 403 on copied content |
| `--no-preserve=ownership` | resets owner | combine with `-a` for keep-all-but-owner |
| attribute list | comma-separated | `all` is shorthand for everything |

---

### Troubleshoot (Task 2)

| Symptom | Likely cause | Fix |
|---|---|---|
| Context lost on copy | `context` not in preserve list | Add `context` (or use `-a`) |
| Owner unexpectedly root | Ran `cp` as root | Use `sudo -u user` or `chown` after |

---

## ✅ Lab Checklist

- [ ] Task 1 · Step 1 — Recurse a tree with `cp -R`
- [ ] Task 1 · Step 2 — Faithful clone with `cp -a`
- [ ] Task 2 · Step 1 — Keep specific attributes with `--preserve`
- [ ] Task 2 · Step 2 — Drop ownership with `--no-preserve`
- [ ] Every 🎯 Focus Coverage row (Anchor + NEW) mapped to a step
- [ ] 🧹 Teardown run — sandbox + any system state removed

---

## 🧹 Teardown

**In plain English:** Delete everything this lab created so the box is clean for the next run.

> Run this after you've verified the lab. `lab_teardown.sh` safely removes the single sandbox root — it refuses to touch `/`, `$HOME`, or any protected path. This lab changed **no** system state.

```bash
cd /tmp
bash lab_teardown.sh "$LAB_ROOT"     # = /tmp/lab-08
```

**Expected output:**

```
✅ Removed /tmp/lab-08 — lab workspace is clean.
```

---

## ⚠️ Common Pitfalls

| Mistake | Symptom | Fix |
|---|---|---|
| Plain `cp` for a config | Wrong context/perms break the service | Use `cp -a` or `--preserve=context` |
| Forgetting `-R` for a dir | `omitting directory` error | Add `-R`/`-a` |
| Assuming `cp` keeps mtime | Backup looks freshly modified | Use `-a`/`--preserve=timestamps` |

---

## 📌 Exam Strategy

Copying tasks usually hide a preservation requirement. Default to `cp -a` so permissions, times, and SELinux contexts survive; reach for `--preserve`/`--no-preserve` only when the task names specific attributes. Always `stat` the copy against the source to prove the metadata matched.

- `cp -a` is the one-flag answer to "copy and keep everything."
- On SELinux boxes, never copy configs without `context`.
- Verify with `stat -c '%a %y %C'` source-vs-copy before moving on.

---

## 🔗 Related Labs

- [Lab 08b — Copying Files (Ansible)](../lab-08b-copying-files-ansible/) — `ansible.builtin.copy` with `remote_src`, `mode`, and `backup`
- [Lab 08c — Copying Files (Verify)](../lab-08c-copying-files-verify/) — prove copies are faithful with `diff -r` and hashes
- [Lab 06a — Listing Files and SELinux (RHCSA)](../lab-06a-listing-files-selinux-rhcsa/) — the contexts a copy must preserve

---

## 👤 Author

**Kelvin R. Tobias**  
[kelvinintech.com](https://kelvinintech.com) · [GitHub](https://github.com/kelvintechnical) · [LinkedIn](https://www.linkedin.com/in/kelvin-r-tobias-211949219)
