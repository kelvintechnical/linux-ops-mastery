# Lab 09a: Hard and Soft Links (RHCSA) — `ln`, `ln -s`

**Series:** linux-ops-mastery — Essential Tools & File Operations · **Lab 09a of the Novice → RHCA path**  
**Certifications covered:** RHCSA EX200 (creating hard and symbolic links), RHCE EX294 (the `file` link states underneath), SRE/DevOps (current→release symlink deploys)  
**Prerequisite:** [Lab 08c](../lab-08c-copying-files-verify/) completed  
**Time Estimate:** 25–35 minutes  
**Difficulty:** Beginner → Intermediate

---

## 🎯 Today's Focus Coverage

> Stay on-subject via the ANCHOR rows; expand vocabulary via the NEW rows. Every row is exercised by a STEP below.

**⚓ Anchor — already learned (on-topic reuse)**

| # | Command / switch | Covered by |
|---|---|---|
| A1 | `ln` | _Task 1 · Step 1_ |
| A2 | `stat -c` | _Task 1 · Step 2_ |

**🆕 NEW this lab — introduced for the first time** (minimum 3)

| # | Command / switch | First taught in | Covered by |
|---|---|---|---|
| N1 | `ln -s` (symbolic link) | Task 2 · Step 1 | _Task 2 · Step 1_ |
| N2 | `stat -c %h` / `%i` | Task 1 · Step 2 | _Task 1 · Step 2_ |
| N3 | `find -inum` | Task 1 · Step 2 | _Task 1 · Step 2_ |
| N4 | `readlink -f` / `test -L` vs `-e` | Task 2 · Step 2 | _Task 2 · Step 2_ |

---

## 🎯 Objective

Understand the two kinds of links by building both and reading the evidence. A **hard link** is a second name for the same inode (same data, same link count); a **symbolic link** is a tiny file that points at a path. You will create a hard link and prove it shares an inode with `stat -c %i` and `find -inum`, then create a symlink, resolve it with `readlink -f`, and feel the dangling-link trap with `test -L` versus `test -e`.

---

## 🧠 Concept

A file's real identity is its **inode** (a number on the filesystem holding the data and metadata). A directory entry is just a *name* pointing at an inode. `ln src name` makes a **hard link**: a second name for the *same* inode, so both names are equal and the data survives until the link count (`stat -c %h`) hits zero. `ln -s target name` makes a **symbolic link**: a separate inode whose content is the path string — delete the target and the symlink "dangles" (points at nothing). Hard links cannot cross filesystems or link directories; symlinks can do both but break if the target moves.

```
ln a b        → a and b share inode N, link count = 2
stat -c %i a b → N  N   (same inode)
ln -s a c     → c is its own inode, content = "a"
rm a          → b still works (hard), c now dangles (soft)
```

> **Why this matters:** Deployments use a `current → releases/v5` symlink to switch versions atomically. Backups rely on hard links to deduplicate. Confusing the two — or missing a dangling link — causes silent data and service failures.

---

## 📚 Command Reference

| Command | Purpose | Critical flags |
|---|---|---|
| `ln src name` | Create a hard link (same inode) | cannot cross filesystems or link dirs |
| `ln -s tgt name` | Create a symbolic link (points at a path) | `-f` replace, `-n` treat link-dir as file |
| `stat -c %i` / `%h` | Show inode number / hard-link count | proves shared identity |
| `find -inum N` | Find all names for an inode | lists every hard link |
| `readlink -f` | Resolve a symlink to its target | `test -L` is-symlink, `-e` exists |

---

## 🧰 LAB-WIDE SETUP

**In plain English:** Build a sandbox with one real file we can link to in both ways.

> Run this block **once** before Task 1. It defines a single sandbox root
> (`LAB_ROOT`) that every file in this lab lives under, so the Teardown
> section can wipe it in one safe command.

```bash
export LAB_ROOT=/tmp/lab-09
mkdir -p "$LAB_ROOT"
cd "$LAB_ROOT"
echo "shared data" > original.txt
stat -c '%i %h %n' original.txt
echo "exit was: $?"
```

**Expected output:**

```
1310721 1 original.txt
exit was: 0
```

---

## TASK 1 of 2 — Hard links share an inode

**In plain English:** We create a hard link and prove both names point at the same inode with a rising link count.

---

### Step 1 of 2 — Create a hard link with `ln`

**In plain English:** We make a second name for the original file and list both to see identical size.

```bash
cd "$LAB_ROOT"
ln original.txt hardlink.txt
ls -li original.txt hardlink.txt
echo "exit was: $?"
```

**Expected output:**

```
1310721 -rw-r--r--. 2 root root 12 ... original.txt
1310721 -rw-r--r--. 2 root root 12 ... hardlink.txt
exit was: 0
```

**Line-by-line breakdown:**

- `ln original.txt hardlink.txt` → Create a hard link; `hardlink.txt` is a new *name* for the same inode, not a copy.
- `ls -li ...` → `-i` shows the inode number (identical) and the link count column now reads `2`.

**New words in this step:**

- **inode** — the on-disk structure that *is* the file; names are just pointers to it.
- **hard link** — an additional directory name for an existing inode.

---

### Step 2 of 2 — Prove shared identity with `stat -c %h` and `find -inum`

**In plain English:** We read the link count and inode, then find every name that points at that inode.

```bash
cd "$LAB_ROOT"
stat -c 'inode=%i links=%h name=%n' original.txt
INUM=$(stat -c %i original.txt)
find "$LAB_ROOT" -inum "$INUM"
echo "exit was: $?"
```

**Expected output:**

```
inode=1310721 links=2 name=original.txt
/tmp/lab-09/original.txt
/tmp/lab-09/hardlink.txt
exit was: 0
```

**Line-by-line breakdown:**

- `stat -c 'inode=%i links=%h ...'` → `%i` is the inode, `%h` the hard-link count (now `2`).
- `INUM=$(stat -c %i original.txt)` → Capture the inode number.
- `find "$LAB_ROOT" -inum "$INUM"` → List every name pointing at that inode — both hard links appear.

**New words in this step:**

- **link count (`%h`)** — how many names point at an inode; data is freed only at zero.
- **`find -inum`** — locate all directory entries sharing an inode.

---

### Concept card (Task 1)

| Concept | What it does | Exam trap |
|---|---|---|
| `ln` (hard) | new name, same inode | cannot span filesystems or link dirs |
| `stat -c %h` | link count | deleting one name only decrements it |
| `find -inum` | find all hard links | needs the inode number, not the name |

---

### Troubleshoot (Task 1)

| Symptom | Likely cause | Fix |
|---|---|---|
| `Invalid cross-device link` | Source/dest on different filesystems | Use a symlink instead |
| `hard link not allowed for directory` | Tried to hard-link a dir | Symlink directories |

---

## TASK 2 of 2 — Symlinks point at a path

**In plain English:** We create a symbolic link, resolve it, then break it to feel the dangling-link trap.

---

### Step 1 of 2 — Create a symlink with `ln -s`

**In plain English:** We make a symbolic link to the original and confirm it has its own inode whose content is the target path.

```bash
cd "$LAB_ROOT"
ln -s original.txt softlink.txt
ls -li original.txt softlink.txt
cat softlink.txt
echo "exit was: $?"
```

**Expected output:**

```
1310721 -rw-r--r--. 2 root root 12 ... original.txt
1310733 lrwxrwxrwx. 1 root root 12 ... softlink.txt -> original.txt
shared data
exit was: 0
```

**Line-by-line breakdown:**

- `ln -s original.txt softlink.txt` → Create a symlink; `-s` makes it symbolic (a pointer file), not a hard link.
- `ls -li ...` → The symlink has a *different* inode and the `l` type and `->` arrow; reading through it still shows the data.

**New words in this step:**

- **symbolic link (symlink)** — a small file whose content is a path to another file.

---

### Step 2 of 2 — Resolve and break it: `readlink -f`, `test -L` vs `-e`

**In plain English:** We resolve the symlink's target, then delete the original and prove the link still *exists* as a link but no longer *resolves*.

```bash
cd "$LAB_ROOT"
readlink -f softlink.txt
rm -f original.txt hardlink.txt
test -L softlink.txt && echo "STILL A SYMLINK (-L true)" || echo "no link"
test -e softlink.txt && echo "target exists (-e true)" || echo "DANGLING (-e false)"
echo "exit was: $?"
```

**Expected output:**

```
/tmp/lab-09/original.txt
STILL A SYMLINK (-L true)
DANGLING (-e false)
exit was: 0
```

**Line-by-line breakdown:**

- `readlink -f softlink.txt` → Resolve the symlink to its canonical target path.
- `rm -f original.txt hardlink.txt` → Remove the real data (both hard-linked names) so the symlink target vanishes.
- `test -L softlink.txt` → `-L` is true: the symlink file itself still exists.
- `test -e softlink.txt` → `-e` follows the link and is *false* now, because the target is gone — a dangling link.

**New words in this step:**

- **dangling link** — a symlink whose target no longer exists (`-L` true, `-e` false).
- **`test -L` vs `-e`** — is-a-symlink versus does-the-target-exist.

---

### Concept card (Task 2)

| Concept | What it does | Exam trap |
|---|---|---|
| `ln -s` | path pointer | breaks if the target moves/deletes |
| `readlink -f` | resolve target | empty/error on a non-link |
| `-L` vs `-e` | link vs target existence | a dangling link is `-L` true, `-e` false |

---

### Troubleshoot (Task 2)

| Symptom | Likely cause | Fix |
|---|---|---|
| Symlink shows red / broken | Target deleted or moved | Recreate target or repoint the link |
| `ln -s` fails "File exists" | Link name already present | Use `ln -sf` to replace |

---

## ✅ Lab Checklist

- [ ] Task 1 · Step 1 — Create a hard link with `ln`
- [ ] Task 1 · Step 2 — Prove shared identity with `stat -c %h` and `find -inum`
- [ ] Task 2 · Step 1 — Create a symlink with `ln -s`
- [ ] Task 2 · Step 2 — Resolve and break it: `readlink -f`, `test -L` vs `-e`
- [ ] Every 🎯 Focus Coverage row (Anchor + NEW) mapped to a step
- [ ] 🧹 Teardown run — sandbox + any system state removed

---

## 🧹 Teardown

**In plain English:** Delete everything this lab created so the box is clean for the next run.

> Run this after you've verified the lab. `lab_teardown.sh` safely removes the single sandbox root — it refuses to touch `/`, `$HOME`, or any protected path. This lab changed **no** system state.

```bash
cd /tmp
bash lab_teardown.sh "$LAB_ROOT"     # = /tmp/lab-09
```

**Expected output:**

```
✅ Removed /tmp/lab-09 — lab workspace is clean.
```

---

## ⚠️ Common Pitfalls

| Mistake | Symptom | Fix |
|---|---|---|
| Hard-linking across filesystems | `Invalid cross-device link` | Use a symlink |
| Expecting a symlink to survive a moved target | Dangling link | Use a hard link or fix the path |
| Reading link count as "copies" | Misunderstands hard links | They are names, not copies |

---

## 📌 Exam Strategy

Link tasks ask you to "create a link from A to B" — clarify hard vs symbolic. Use `ln` for hard links within one filesystem, `ln -s` for symbolic links (and always for directories or cross-filesystem). Prove your work with `ls -li` (inode + count) and `readlink -f`.

- `ls -li` shows inode and link count in one shot — your go-to proof.
- Use `ln -sf` to safely repoint an existing symlink.
- Watch for dangling links: `-L` true but `-e` false.

---

## 🔗 Related Labs

- [Lab 09b — Hard and Soft Links (Ansible)](../lab-09b-hard-and-soft-links-ansible/) — `ansible.builtin.file` `state: link`/`hard`
- [Lab 09c — Hard and Soft Links (Verify)](../lab-09c-hard-and-soft-links-verify/) — prove inode sharing and resolution
- [Lab 05a — Directory Navigation (RHCSA)](../lab-05a-directory-navigation-rhcsa/) — the symlink path trap with `pwd -P`

---

## 👤 Author

**Kelvin R. Tobias**  
[kelvinintech.com](https://kelvinintech.com) · [GitHub](https://github.com/kelvintechnical) · [LinkedIn](https://www.linkedin.com/in/kelvin-r-tobias-211949219)
