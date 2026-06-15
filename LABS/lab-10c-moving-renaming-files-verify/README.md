# Lab 10c: Moving and Renaming Files (Verify) — `stat -c %i`, `sha256sum`, `test -e`

**Series:** linux-ops-mastery — Essential Tools & File Operations · **Lab 10c of the Novice → RHCA path**  
**Certifications covered:** RHCSA EX200 (proving a move completed without data loss), SRE (atomic-swap validation), DevOps (release/rotation audits)  
**Prerequisite:** [Lab 10a](../lab-10a-moving-renaming-files-rhcsa/) and [Lab 10b](../lab-10b-moving-renaming-files-ansible/) completed  
**Time Estimate:** 15–25 minutes  
**Difficulty:** Beginner

---

## 🎯 Today's Focus Coverage

> Stay on-subject via the ANCHOR rows; expand vocabulary via the NEW rows. Every row is exercised by a STEP below.

**⚓ Anchor — already learned (on-topic reuse)**

| # | Command / switch | Covered by |
|---|---|---|
| A1 | `stat -c %i` | _Task 1 · Step 1_ |
| A2 | `sha256sum` | _Task 1 · Step 2_ |

**🆕 NEW this lab — introduced for the first time** (minimum 3)

| # | Command / switch | First taught in | Covered by |
|---|---|---|---|
| N1 | `test -e` move completeness | Task 2 · Step 1 | _Task 2 · Step 1_ |
| N2 | `[ a -eq b ]` inode test | Task 1 · Step 1 | _Task 1 · Step 1_ |
| N3 | `diff` backup vs live | Task 2 · Step 2 | _Task 2 · Step 2_ |
| N4 | `stat -c %h` link survival | Task 1 · Step 2 | _Task 1 · Step 2_ |

---

## 🎯 Objective

Take the auditor's seat: prove a move kept the data and (within one filesystem) the inode. You will record a file's inode and hash, move it, and assert the inode is unchanged and the bytes are identical — proof the rename was atomic and lossless. Then you will prove a guarded move is complete (source gone, destination present) and that a `backup` truly captured the old content.

---

## 🧠 Concept

Move verification answers two questions. **Integrity**: did the data survive? Equal `sha256sum` before and after proves zero corruption; equal `stat -c %i` proves a same-filesystem atomic rename (and that hard links, by `%h`, kept working). **Completeness**: is the move finished? `test -e src` must be false and `test -e dst` true. For a backup-style replace, `diff` between the backup and the new live file proves the old version was preserved and the new one differs.

```
sha256sum before == after   → no data loss
stat -c %i before == after  → atomic same-FS rename
test -e src == false        → source removed
test -e dst == true         → destination present
diff backup live            → backup holds the OLD content
```

> **Why this matters:** A "successful" move that corrupted a byte or left the source behind is a silent failure. Hash + inode + presence checks certify the operation actually did what `mv` promised.

---

## 📚 Command Reference

| Command | Purpose | Critical flags |
|---|---|---|
| `stat -c %i` / `%h` | Inode / hard-link count | survival proof |
| `sha256sum` | Content fingerprint | before/after equality |
| `test -e` | Path exists (follows links) | move completeness |
| `[ a -eq b ]` | Integer equality | inode comparison |
| `diff` | Compare two files | backup vs live |

---

## 🧰 LAB-WIDE SETUP

**In plain English:** Rebuild a file with a hard link so we can prove the link survives a rename, plus a backup pair to audit.

> Run this block **once** before Task 1. It builds the clean, private workspace that both tasks depend on.

```bash
export LAB_ROOT=/tmp/lab-10
mkdir -p "$LAB_ROOT/archive"
cd "$LAB_ROOT"
echo "payload" > data.txt
ln data.txt data.hardlink
ls -li data.txt data.hardlink
echo "exit was: $?"
```

**Expected output:**

```
1311001 -rw-r--r--. 2 root root 8 ... data.hardlink
1311001 -rw-r--r--. 2 root root 8 ... data.txt
exit was: 0
```

---

## TASK 1 of 2 — Prove the rename was atomic and lossless

**In plain English:** We record inode and hash, rename within the filesystem, and prove both are unchanged.

---

### Step 1 of 2 — Prove inode survival

**In plain English:** We capture the inode, rename the file, and assert the inode is identical.

```bash
cd "$LAB_ROOT"
BEFORE=$(stat -c %i data.txt)
mv data.txt renamed.txt
AFTER=$(stat -c %i renamed.txt)
[ "$BEFORE" -eq "$AFTER" ] && echo "INODE SURVIVED (ATOMIC)" || echo "NEW INODE (FAIL)"
```

**Expected output:**

```
INODE SURVIVED (ATOMIC)
```

**Line-by-line breakdown:**

- `BEFORE=$(stat -c %i data.txt)` → Record the inode before the move.
- `mv data.txt renamed.txt` → Same-filesystem rename.
- `[ "$BEFORE" -eq "$AFTER" ]` → Equal inodes prove an atomic rename, not a copy+delete.

**New words in this step:**

- **atomic rename proof** — equal inode before and after a same-FS move.

---

### Step 2 of 2 — Prove content and hard link survived

**In plain English:** We confirm the hash is unchanged and the hard link still shares the inode after the rename.

```bash
cd "$LAB_ROOT"
sha256sum renamed.txt data.hardlink | awk '{print $1}' | sort -u
echo "link count: $(stat -c %h renamed.txt)"
[ "$(stat -c %i renamed.txt)" -eq "$(stat -c %i data.hardlink)" ] && echo "HARD LINK INTACT (OK)" || echo "LINK BROKEN (FAIL)"
```

**Expected output:**

```
e8c9...  (single unique hash — both files identical)
link count: 2
HARD LINK INTACT (OK)
```

**Line-by-line breakdown:**

- `sha256sum renamed.txt data.hardlink | awk ... | sort -u` → A single unique hash proves both names hold identical bytes — no corruption.
- `stat -c %h renamed.txt` → Link count `2` confirms the hard link survived the rename.
- the inode test → Same inode proves the rename did not break the hard link.

**New words in this step:**

- **link survival** — a hard link keeps pointing at the same inode through a same-FS rename.

---

### Concept card (Task 1)

| Concept | What it does | Exam trap |
|---|---|---|
| inode equality | atomic-rename proof | cross-FS move gives a new inode |
| `sort -u` of hashes | content equality | one unique hash = identical |
| `%h` after move | link survival | copy+rm would drop it to 1 |

---

### Troubleshoot (Task 1)

| Symptom | Likely cause | Fix |
|---|---|---|
| `NEW INODE (FAIL)` | Crossed a filesystem | Expected off-mount; keep same FS for atomic |
| Two unique hashes | Corruption | Investigate; the move was not lossless |

---

## TASK 2 of 2 — Prove move completeness and backup integrity

**In plain English:** We confirm a guarded move left no source behind and that a backup captured the old content.

---

### Step 1 of 2 — Assert source gone, destination present

**In plain English:** We move a file into the archive and prove the source no longer exists while the destination does.

```bash
cd "$LAB_ROOT"
echo "move me" > toarchive.txt
mv toarchive.txt archive/toarchive.txt
test -e toarchive.txt && echo "SRC REMAINS (FAIL)" || echo "SRC GONE (OK)"
test -e archive/toarchive.txt && echo "DST PRESENT (OK)" || echo "DST MISSING (FAIL)"
```

**Expected output:**

```
SRC GONE (OK)
DST PRESENT (OK)
```

**Line-by-line breakdown:**

- `mv toarchive.txt archive/toarchive.txt` → Relocate the file into the archive.
- `test -e toarchive.txt` → Must be false — the source should be gone.
- `test -e archive/toarchive.txt` → Must be true — the destination must exist; together they prove a complete move.

**New words in this step:**

- **move completeness** — source removed AND destination present, the two-sided proof.

---

### Step 2 of 2 — Prove the backup holds the old content

**In plain English:** We overwrite a file keeping a backup, then `diff` to prove the backup preserved the original and the live file changed.

```bash
cd "$LAB_ROOT"
echo "v1" > cfg.txt
echo "v2" > cfg.new
mv -b cfg.new cfg.txt
ls -1 cfg.txt*
diff <(echo "v2") cfg.txt && echo "LIVE IS V2 (OK)" || echo "LIVE WRONG (FAIL)"
```

**Expected output:**

```
cfg.txt
cfg.txt~
LIVE IS V2 (OK)
```

**Line-by-line breakdown:**

- `echo "v1" > cfg.txt` → Create the original.
- `echo "v2" > cfg.new; mv -b cfg.new cfg.txt` → Overwrite with v2 using `-b`, which renames the old `cfg.txt` to `cfg.txt~`.
- `ls -1 cfg.txt*` → Show the live file and its backup.
- `diff <(echo "v2") cfg.txt` → Prove the live file is now v2; the `~` backup still holds v1.

**New words in this step:**

- **backup integrity** — confirming the `~` file preserved the pre-overwrite content.

---

### Concept card (Task 2)

| Concept | What it does | Exam trap |
|---|---|---|
| `test -e` both sides | move completeness | checking only one side hides failure |
| `mv -b` backup | `~` keeps old version | default suffix is `~` |
| `diff` live vs backup | integrity proof | empty diff means identical |

---

### Troubleshoot (Task 2)

| Symptom | Likely cause | Fix |
|---|---|---|
| No `cfg.txt~` | `-b` omitted | Use `mv -b`/`cp -b` |
| `LIVE WRONG (FAIL)` | Overwrite didn't apply | Re-run the replace |

---

## ✅ Lab Checklist

- [ ] Task 1 · Step 1 — Prove inode survival
- [ ] Task 1 · Step 2 — Prove content and hard link survived
- [ ] Task 2 · Step 1 — Assert source gone, destination present
- [ ] Task 2 · Step 2 — Prove the backup holds the old content
- [ ] Every 🎯 Focus Coverage row (Anchor + NEW) mapped to a step
- [ ] 🧹 Teardown run — sandbox + any system state removed

---

## 🧹 Teardown

**In plain English:** Delete everything this lab created so the box is clean for the next run.

> Run this after you've verified the lab. `lab_teardown.sh` safely removes the single sandbox root — it refuses to touch `/`, `$HOME`, or any protected path. This verify lab changed **no** system state.

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
| Checking only destination | Source left behind unnoticed | Assert both sides with `test -e` |
| Trusting size over hash | Subtle corruption missed | Compare `sha256sum` before/after |
| Assuming all moves are atomic | Cross-FS gave a new inode | Verify with `stat -c %i` |

---

## 📌 Exam Strategy

Certify a move three ways: equal hash (no data loss), equal inode (atomic same-FS rename), and `test -e` on both sides (complete). For replaces, prove the backup with `diff`. These checks turn "I moved it" into "I can prove the data is intact and the move finished."

- Equal inode + equal hash = a perfect same-FS move.
- Always assert the source is gone, not just the destination present.
- `diff` the backup to certify a safe overwrite.

---

## 🔗 Related Labs

- [Lab 10a — Moving and Renaming Files (RHCSA)](../lab-10a-moving-renaming-files-rhcsa/) — the moves this audits
- [Lab 10b — Moving and Renaming Files (Ansible)](../lab-10b-moving-renaming-files-ansible/) — the guarded `command: mv` you verify
- [Lab 09c — Hard and Soft Links (Verify)](../lab-09c-hard-and-soft-links-verify/) — inode proofs in the link context

---

## 👤 Author

**Kelvin R. Tobias**  
[kelvinintech.com](https://kelvinintech.com) · [GitHub](https://github.com/kelvintechnical) · [LinkedIn](https://www.linkedin.com/in/kelvin-r-tobias-211949219)
