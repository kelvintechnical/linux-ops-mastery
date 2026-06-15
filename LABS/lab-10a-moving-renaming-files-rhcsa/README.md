# Lab 10a: Moving and Renaming Files (RHCSA) — `mv`, `mv -t`

**Series:** linux-ops-mastery — Essential Tools & File Operations · **Lab 10a of the Novice → RHCA path**  
**Certifications covered:** RHCSA EX200 (renaming/relocating files safely), RHCE EX294 (the guarded `command: mv` underneath), SRE/DevOps (atomic file swaps, log rotation)  
**Prerequisite:** [Lab 09c](../lab-09c-hard-and-soft-links-verify/) completed  
**Time Estimate:** 25–35 minutes  
**Difficulty:** Beginner → Intermediate

---

## 🎯 Today's Focus Coverage

> Stay on-subject via the ANCHOR rows; expand vocabulary via the NEW rows. Every row is exercised by a STEP below.

**⚓ Anchor — already learned (on-topic reuse)**

| # | Command / switch | Covered by |
|---|---|---|
| A1 | `mv` | _Task 1 · Step 1_ |
| A2 | `stat -c %i` | _Task 2 · Step 2_ |

**🆕 NEW this lab — introduced for the first time** (minimum 3)

| # | Command / switch | First taught in | Covered by |
|---|---|---|---|
| N1 | `mv -i` / `mv -n` | Task 1 · Step 1 | _Task 1 · Step 1_ |
| N2 | `mv -b` (backup) | Task 1 · Step 2 | _Task 1 · Step 2_ |
| N3 | `mv -t` (target dir) | Task 2 · Step 1 | _Task 2 · Step 1_ |
| N4 | atomic rename / inode survival | Task 2 · Step 2 | _Task 2 · Step 2_ |

---

## 🎯 Objective

Move and rename files without losing data. You will rename with `mv`, guard against clobbering with `-i`/`-n`, keep a safety copy with `-b`, batch-move into a directory with `-t`, and prove the key property that makes `mv` powerful: a rename *within one filesystem* is **atomic** and keeps the same inode (so hard links and open file handles survive), while a cross-filesystem move is really a copy-then-delete.

---

## 🧠 Concept

On a single filesystem, `mv` just rewrites a directory entry — the inode never changes, the operation is **atomic** (no half-moved state), and any hard link to that inode keeps working. Across filesystems there is no shared inode table, so `mv` falls back to **copy then remove**, which is not atomic and gets a brand-new inode. The safety flags decide what happens on a name collision: `-i` asks, `-n` refuses, `-b` renames the existing target to a backup first. `-t DIR` puts the destination directory first so you can move many files into it.

```
mv a b            (same FS)  → rename only; inode unchanged; atomic
mv a /other/fs/b  (cross FS) → copy + rm; new inode; not atomic
mv -n a b         → never overwrite b
mv -b a b         → back up old b as b~ before overwriting
mv -t DIR f1 f2   → move f1,f2 into DIR
```

> **Why this matters:** Atomic same-FS renames are how configs and logs are swapped without a reader ever seeing a partial file. Knowing `mv` is copy+rm across filesystems explains why a big cross-mount move is slow and interruptible.

---

## 📚 Command Reference

| Command | Purpose | Critical flags |
|---|---|---|
| `mv` | Rename or move | atomic within one filesystem |
| `mv -i` / `-n` | Prompt before / never overwrite | `-n` is the safe scripting default |
| `mv -b` | Back up an existing target first | makes `target~` before overwrite |
| `mv -t DIR` | Move into a directory | DIR first, then the files |
| `stat -c %i` | Inode number | proves same-FS rename keeps it |

---

## 🧰 LAB-WIDE SETUP

**In plain English:** Build a sandbox with a couple of files and a destination directory so we have things to rename and relocate.

> Run this block **once** before Task 1. It defines a single sandbox root
> (`LAB_ROOT`) that every file in this lab lives under, so the Teardown
> section can wipe it in one safe command.

```bash
export LAB_ROOT=/tmp/lab-10
mkdir -p "$LAB_ROOT/archive"
cd "$LAB_ROOT"
echo "report v1" > report.txt
echo "existing"  > taken.txt
ls -l
echo "exit was: $?"
```

**Expected output:**

```
drwxr-xr-x. 2 root root  6 ... archive
-rw-r--r--. 1 root root 10 ... report.txt
-rw-r--r--. 1 root root  9 ... taken.txt
exit was: 0
```

---

## TASK 1 of 2 — Rename safely with collision guards

**In plain English:** We rename a file, then protect against accidentally overwriting an existing one with `-n` and `-b`.

---

### Step 1 of 2 — Rename, then refuse to clobber with `-n`

**In plain English:** We rename a file, then try to move it onto an existing name with `-n` to prove the no-overwrite guard works.

```bash
cd "$LAB_ROOT"
mv report.txt report-final.txt
mv -n report-final.txt taken.txt
cat taken.txt
echo "exit was: $?"
```

**Expected output:**

```
existing
exit was: 0
```

**Line-by-line breakdown:**

- `mv report.txt report-final.txt` → Rename the file; same directory, so it is an atomic entry rewrite.
- `mv -n report-final.txt taken.txt` → `-n` (no-clobber) refuses to overwrite the existing `taken.txt`, so the move is skipped silently.
- `cat taken.txt` → Confirm the original `existing` content is intact — nothing was clobbered.

**New words in this step:**

- **clobber** — to overwrite an existing file; `-n` prevents it, `-i` prompts.

---

### Step 2 of 2 — Keep a safety copy with `-b`

**In plain English:** We deliberately overwrite a target but use `-b` so the old version is preserved as a backup.

```bash
cd "$LAB_ROOT"
mv -b report-final.txt taken.txt
ls -1 taken.txt*
cat taken.txt
echo "exit was: $?"
```

**Expected output:**

```
taken.txt
taken.txt~
report v1
exit was: 0
```

**Line-by-line breakdown:**

- `mv -b report-final.txt taken.txt` → Overwrite `taken.txt`, but first rename the old one to `taken.txt~`; `-b` is the backup flag.
- `ls -1 taken.txt*` → Show both the new file and the `~` backup.
- `cat taken.txt` → Confirm the new content (`report v1`) landed while the old survives in the backup.

**New words in this step:**

- **`mv -b`** — back up the existing target as `target~` before overwriting it.

---

### Concept card (Task 1)

| Concept | What it does | Exam trap |
|---|---|---|
| `mv -n` | never overwrite | silent skip — check the result |
| `mv -i` | prompt on overwrite | non-interactive scripts hang on it |
| `mv -b` | backup before overwrite | backup suffix is `~` by default |

---

### Troubleshoot (Task 1)

| Symptom | Likely cause | Fix |
|---|---|---|
| Overwrite happened anyway | Forgot `-n`/`-i` | Add the guard flag |
| No backup created | Forgot `-b` | Use `-b` (or `--backup=numbered`) |

---

## TASK 2 of 2 — Relocate and prove atomic rename

**In plain English:** We batch-move files into a directory with `-t`, then prove a same-filesystem rename keeps the inode.

---

### Step 1 of 2 — Batch-move into a directory with `-t`

**In plain English:** We move multiple files into the archive directory using the target-first form.

```bash
cd "$LAB_ROOT"
echo "a" > f1.log; echo "b" > f2.log
mv -t archive f1.log f2.log
ls archive
echo "exit was: $?"
```

**Expected output:**

```
f1.log
f2.log
exit was: 0
```

**Line-by-line breakdown:**

- `mv -t archive f1.log f2.log` → `-t` names the target directory first, so every following argument is a file to move into it — handy with `find ... | xargs mv -t`.
- `ls archive` → Confirm both files landed in the archive.

**New words in this step:**

- **`mv -t DIR`** — target-directory-first form for moving many files at once.

---

### Step 2 of 2 — Prove same-FS rename keeps the inode

**In plain English:** We record a file's inode, rename it within the same filesystem, and prove the inode is unchanged — the atomic-rename signature.

```bash
cd "$LAB_ROOT"
echo "atomic" > moveme.txt
BEFORE=$(stat -c %i moveme.txt)
mv moveme.txt moved.txt
AFTER=$(stat -c %i moved.txt)
echo "inode before=$BEFORE after=$AFTER"
[ "$BEFORE" -eq "$AFTER" ] && echo "SAME INODE (ATOMIC RENAME)" || echo "NEW INODE (cross-FS copy)"
```

**Expected output:**

```
inode before=1310955 after=1310955
SAME INODE (ATOMIC RENAME)
```

**Line-by-line breakdown:**

- `BEFORE=$(stat -c %i moveme.txt)` → Record the inode before the move.
- `mv moveme.txt moved.txt` → Rename within the same filesystem — just a directory-entry rewrite.
- `[ "$BEFORE" -eq "$AFTER" ]` → Equal inodes prove the rename was atomic and the file's identity (and any hard links) survived.

**New words in this step:**

- **atomic rename** — a same-filesystem move that swaps the name instantly with no intermediate state.

---

### Concept card (Task 2)

| Concept | What it does | Exam trap |
|---|---|---|
| `mv -t DIR` | move many into a dir | DIR must come first |
| same-FS `mv` | inode unchanged, atomic | cross-FS `mv` gets a NEW inode |
| inode survival | hard links keep working | a copy+rm would break them |

---

### Troubleshoot (Task 2)

| Symptom | Likely cause | Fix |
|---|---|---|
| New inode after move | Crossed a filesystem | Expected; it is copy+rm there |
| `mv -t` errors | Files listed before DIR | Put the directory first |

---

## ✅ Lab Checklist

- [ ] Task 1 · Step 1 — Rename, then refuse to clobber with `-n`
- [ ] Task 1 · Step 2 — Keep a safety copy with `-b`
- [ ] Task 2 · Step 1 — Batch-move into a directory with `-t`
- [ ] Task 2 · Step 2 — Prove same-FS rename keeps the inode
- [ ] Every 🎯 Focus Coverage row (Anchor + NEW) mapped to a step
- [ ] 🧹 Teardown run — sandbox + any system state removed

---

## 🧹 Teardown

**In plain English:** Delete everything this lab created so the box is clean for the next run.

> Run this after you've verified the lab. `lab_teardown.sh` safely removes the single sandbox root — it refuses to touch `/`, `$HOME`, or any protected path. This lab changed **no** system state.

```bash
cd /tmp
bash lab_teardown.sh "$LAB_ROOT"     # = /tmp/lab-10
```

**Expected output:**

```
✅ Removed /tmp/lab-10 — lab workspace is clean.
```

---

## ⚠️ Common Pitfalls

| Mistake | Symptom | Fix |
|---|---|---|
| `mv` without `-n` in a script | Silent overwrite | Use `-n` (or `-b` to keep a backup) |
| Expecting cross-FS move to be atomic | Partial state on interruption | Same-FS only is atomic |
| `mv -i` in automation | Script hangs on prompt | Use `-n`/`-b`, not `-i`, non-interactively |

---

## 📌 Exam Strategy

Renames look trivial until they overwrite something. Default to `-n` or `-b` when a collision is possible, and use `-t` for batch moves. Remember the atomic-rename rule: same filesystem keeps the inode and is instant; crossing a mount is a slow copy+delete.

- `mv -b` is the safe overwrite — old version becomes `~`.
- Same-FS renames are atomic; prove it with `stat -c %i`.
- `find ... | xargs mv -t DIR` is the batch-move idiom.

---

## 🔗 Related Labs

- [Lab 10b — Moving and Renaming Files (Ansible)](../lab-10b-moving-renaming-files-ansible/) — guarded `command: mv` with `creates:`/`removes:`
- [Lab 10c — Moving and Renaming Files (Verify)](../lab-10c-moving-renaming-files-verify/) — prove inode survival and no data loss
- [Lab 08a — Copying Files (RHCSA)](../lab-08a-copying-files-rhcsa/) — copy vs move, the metadata story

---

## 👤 Author

**Kelvin R. Tobias**  
[kelvinintech.com](https://kelvinintech.com) · [GitHub](https://github.com/kelvintechnical) · [LinkedIn](https://www.linkedin.com/in/kelvin-r-tobias-211949219)
