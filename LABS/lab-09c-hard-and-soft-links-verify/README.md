# Lab 09c: Hard and Soft Links (Verify) — `stat -c %i`, `find -inum`, `readlink`

**Series:** linux-ops-mastery — Essential Tools & File Operations · **Lab 09c of the Novice → RHCA path**  
**Certifications covered:** RHCSA EX200 (proving a link is the right kind and resolves), SRE (deploy symlink validation), DevOps (dedup/backup integrity)  
**Prerequisite:** [Lab 09a](../lab-09a-hard-and-soft-links-rhcsa/) and [Lab 09b](../lab-09b-hard-and-soft-links-ansible/) completed  
**Time Estimate:** 15–25 minutes  
**Difficulty:** Beginner

---

## 🎯 Today's Focus Coverage

> Stay on-subject via the ANCHOR rows; expand vocabulary via the NEW rows. Every row is exercised by a STEP below.

**⚓ Anchor — already learned (on-topic reuse)**

| # | Command / switch | Covered by |
|---|---|---|
| A1 | `stat -c %i` | _Task 1 · Step 1_ |
| A2 | `readlink` | _Task 2 · Step 1_ |

**🆕 NEW this lab — introduced for the first time** (minimum 3)

| # | Command / switch | First taught in | Covered by |
|---|---|---|---|
| N1 | `find -samefile` | Task 1 · Step 2 | _Task 1 · Step 2_ |
| N2 | `[ a -eq b ]` inode test | Task 1 · Step 1 | _Task 1 · Step 1_ |
| N3 | `readlink -f` vs `readlink` | Task 2 · Step 1 | _Task 2 · Step 1_ |
| N4 | `test -e` resolution check | Task 2 · Step 2 | _Task 2 · Step 2_ |

---

## 🎯 Objective

Take the auditor's seat: prove a hard link truly shares an inode and a symlink truly resolves. You will compare inode numbers numerically, enumerate every name for an inode with `find -samefile`, resolve a symlink's target with `readlink`, and assert it actually points at something with `test -e`. These checks distinguish a real link from a coincidental copy.

---

## 🧠 Concept

Link verification is about identity and resolution. **Identity** (hard links): two names are the same file only if their inode numbers (`stat -c %i`) are equal — `find -samefile`/`-inum` enumerates the full set. **Resolution** (symlinks): `readlink` shows the stored target string, `readlink -f` resolves the whole chain to a canonical path, and `test -e` proves the target actually exists (catching dangling links). A copy has a *different* inode; a real hard link does not.

```
stat -c %i a b   → 1310721 1310721   → [ eq ] = same file
find -samefile a → a, b              → full hard-link set
readlink current → releases/v5       → stored target
readlink -f cur  → /tmp/lab-09/releases/v5  (canonical)
test -e current  → exists (not dangling)
```

> **Why this matters:** "I made a link" is easy to fake with a copy. Proving a shared inode (hard) or a resolving target (soft) is the only way to certify the link actually exists.

---

## 📚 Command Reference

| Command | Purpose | Critical flags |
|---|---|---|
| `stat -c %i` | Inode number | equal inodes = same file |
| `find -samefile F` | All names sharing F's inode | cleaner than `-inum` |
| `readlink` | Stored symlink target | one hop, as written |
| `readlink -f` | Canonical resolved path | follows the whole chain |
| `test -e` | Target exists (follows links) | false on a dangling link |

---

## 🧰 LAB-WIDE SETUP

**In plain English:** Rebuild a file with a hard link and a symlink so there is a known link set to audit.

> Run this block **once** before Task 1. It builds the clean, private workspace that both tasks depend on.

```bash
export LAB_ROOT=/tmp/lab-09
mkdir -p "$LAB_ROOT/releases/v5"
cd "$LAB_ROOT"
echo "shared data" > original.txt
ln original.txt hardlink.txt
ln -sfn releases/v5 current
ls -li
echo "exit was: $?"
```

**Expected output:**

```
1310721 -rw-r--r--. 2 root root 12 ... hardlink.txt
1310721 -rw-r--r--. 2 root root 12 ... original.txt
1310740 lrwxrwxrwx. 1 root root 12 ... current -> releases/v5
exit was: 0
```

---

## TASK 1 of 2 — Prove the hard link shares an inode

**In plain English:** We compare inode numbers numerically and enumerate every name pointing at that inode.

---

### Step 1 of 2 — Compare inodes with a numeric test

**In plain English:** We capture both files' inode numbers and assert they are equal.

```bash
cd "$LAB_ROOT"
A=$(stat -c %i original.txt)
B=$(stat -c %i hardlink.txt)
echo "inodes: $A vs $B"
[ "$A" -eq "$B" ] && echo "SAME INODE (HARD LINK OK)" || echo "DIFFERENT (FAIL)"
```

**Expected output:**

```
inodes: 1310721 vs 1310721
SAME INODE (HARD LINK OK)
```

**Line-by-line breakdown:**

- `A=$(stat -c %i original.txt)` / `B=$(stat -c %i hardlink.txt)` → Capture both inode numbers.
- `[ "$A" -eq "$B" ]` → Numeric equality proves they are the same file, not a copy.

**New words in this step:**

- **inode equality** — the definitive test that two names are the same hard-linked file.

---

### Step 2 of 2 — Enumerate the link set with `find -samefile`

**In plain English:** We list every directory entry that shares the original's inode.

```bash
cd "$LAB_ROOT"
find "$LAB_ROOT" -samefile original.txt
COUNT=$(find "$LAB_ROOT" -samefile original.txt | wc -l)
[ "$COUNT" -eq 2 ] && echo "TWO HARD LINKS (OK)" || echo "UNEXPECTED COUNT (FAIL)"
```

**Expected output:**

```
/tmp/lab-09/original.txt
/tmp/lab-09/hardlink.txt
TWO HARD LINKS (OK)
```

**Line-by-line breakdown:**

- `find "$LAB_ROOT" -samefile original.txt` → List all names sharing the inode; both hard links appear.
- `[ "$COUNT" -eq 2 ]` → Assert exactly two names — matching the link count.

**New words in this step:**

- **`find -samefile`** — enumerate every path sharing a given file's inode (friendlier than `-inum`).

---

### Concept card (Task 1)

| Concept | What it does | Exam trap |
|---|---|---|
| `stat -c %i` | inode identity | a copy has a different inode |
| `find -samefile` | full link set | counts match the link count |
| `[ -eq ]` | numeric verdict | use `-eq`, not `=`, for numbers |

---

### Troubleshoot (Task 1)

| Symptom | Likely cause | Fix |
|---|---|---|
| `DIFFERENT (FAIL)` | It is a copy, not a link | Recreate with `ln` |
| Count is 1 | Link not created | Re-run SETUP |

---

## TASK 2 of 2 — Prove the symlink resolves

**In plain English:** We read the symlink's target and assert it actually exists.

---

### Step 1 of 2 — Resolve with `readlink` and `readlink -f`

**In plain English:** We show both the stored target and the fully resolved canonical path.

```bash
cd "$LAB_ROOT"
echo "stored:    $(readlink current)"
echo "canonical: $(readlink -f current)"
readlink -f current | grep -q '/releases/v5$' && echo "TARGET OK" || echo "TARGET WRONG (FAIL)"
```

**Expected output:**

```
stored:    releases/v5
canonical: /tmp/lab-09/releases/v5
TARGET OK
```

**Line-by-line breakdown:**

- `readlink current` → Print the stored target string exactly as written (relative).
- `readlink -f current` → Resolve to the canonical absolute path.
- `... | grep -q '/releases/v5$'` → Assert it resolves to the expected release.

**New words in this step:**

- **stored vs canonical target** — the raw link string versus the fully-resolved path.

---

### Step 2 of 2 — Prove it is not dangling with `test -e`

**In plain English:** We confirm the symlink both is a link and points at something that exists.

```bash
cd "$LAB_ROOT"
test -L current && echo "IS A SYMLINK (-L)" || echo "not a link (FAIL)"
test -e current && echo "TARGET EXISTS (-e OK)" || echo "DANGLING (FAIL)"
echo "exit was: $?"
```

**Expected output:**

```
IS A SYMLINK (-L)
TARGET EXISTS (-e OK)
exit was: 0
```

**Line-by-line breakdown:**

- `test -L current` → Confirm `current` is a symlink (the link file itself exists).
- `test -e current` → Follow the link and confirm the target exists — not dangling.

**New words in this step:**

- **resolution check** — using `test -e` to prove a symlink actually points at a real target.

---

### Concept card (Task 2)

| Concept | What it does | Exam trap |
|---|---|---|
| `readlink` | stored target | relative target depends on link's dir |
| `readlink -f` | canonical path | resolves the entire chain |
| `-L` + `-e` | link + resolves | dangling = `-L` true, `-e` false |

---

### Troubleshoot (Task 2)

| Symptom | Likely cause | Fix |
|---|---|---|
| `DANGLING (FAIL)` | Target missing | Recreate the release dir |
| `readlink` empty | Not a symlink | Point it at the link, not a regular file |

---

## ✅ Lab Checklist

- [ ] Task 1 · Step 1 — Compare inodes with a numeric test
- [ ] Task 1 · Step 2 — Enumerate the link set with `find -samefile`
- [ ] Task 2 · Step 1 — Resolve with `readlink` and `readlink -f`
- [ ] Task 2 · Step 2 — Prove it is not dangling with `test -e`
- [ ] Every 🎯 Focus Coverage row (Anchor + NEW) mapped to a step
- [ ] 🧹 Teardown run — sandbox + any system state removed

---

## 🧹 Teardown

**In plain English:** Delete everything this lab created so the box is clean for the next run.

> Run this after you've verified the lab. `lab_teardown.sh` safely removes the single sandbox root — it refuses to touch `/`, `$HOME`, or any protected path. This verify lab changed **no** system state.

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
| Treating a copy as a link | Inodes differ | Verify with `stat -c %i` |
| Trusting `readlink` for existence | Dangling link unnoticed | Also run `test -e` |
| Comparing inodes with `=` | String compare bug | Use `-eq` |

---

## 📌 Exam Strategy

Certify links by identity and resolution: equal inodes (`stat -c %i`, `find -samefile`) for hard links, and a resolving target (`readlink -f`, `test -e`) for symlinks. These prove you created the right kind of link, not a lookalike copy.

- Equal inodes are the only proof of a hard link.
- `test -e` catches dangling symlinks that `readlink` alone misses.
- `find -samefile` is the cleanest hard-link enumerator.

---

## 🔗 Related Labs

- [Lab 09a — Hard and Soft Links (RHCSA)](../lab-09a-hard-and-soft-links-rhcsa/) — the links this audits
- [Lab 09b — Hard and Soft Links (Ansible)](../lab-09b-hard-and-soft-links-ansible/) — the playbook whose links you verify
- [Lab 05c — Directory Navigation (Verify)](../lab-05c-directory-navigation-verify/) — canonical-path proofs with `readlink`

---

## 👤 Author

**Kelvin R. Tobias**  
[kelvinintech.com](https://kelvinintech.com) · [GitHub](https://github.com/kelvintechnical) · [LinkedIn](https://www.linkedin.com/in/kelvin-r-tobias-211949219)
