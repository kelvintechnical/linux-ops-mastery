# Lab 29a: Searching Manuals by Keyword (RHCSA) — `whatis`, `apropos`, `mandb`

**Series:** linux-ops-mastery — Documentation · **Lab 29a of the Novice → RHCA path**  
**Certifications covered:** RHCSA EX200 (finding the right command when you don't know its name), SRE/DevOps (offline discovery)  
**Prerequisite:** [Lab 28c](../lab-28c-man-pages-verify/) completed  
**Time Estimate:** 20–30 minutes  
**Difficulty:** Beginner

---

## 🎯 Today's Focus Coverage

> Stay on-subject via the ANCHOR rows; expand vocabulary via the NEW rows. Every row is exercised by a STEP below.

**⚓ Anchor — already learned (on-topic reuse)**

| # | Command / switch | Covered by |
|---|---|---|
| A1 | `man -f` / `man -k` | _Task 1 · Step 1_ |
| A2 | `grep` to filter | _Task 2 · Step 1_ |

**🆕 NEW this lab — introduced for the first time** (minimum 3)

| # | Command / switch | First taught in | Covered by |
|---|---|---|---|
| N1 | `whatis` | Task 1 · Step 1 | _Task 1 · Step 1_ |
| N2 | `apropos` | Task 1 · Step 2 | _Task 1 · Step 2_ |
| N3 | `apropos -s` section filter | Task 2 · Step 1 | _Task 2 · Step 1_ |
| N4 | `mandb` (rebuild index) | Task 2 · Step 2 | _Task 2 · Step 2_ |

---

## 🎯 Objective

Find the command you need when you only know *what it does*. You will get exact one-line descriptions with `whatis`, search all summaries by keyword with `apropos`, narrow results to a section (`apropos -s`), and rebuild the search index with `mandb` when results look stale. By the end, "I need something that does X" becomes a quick, offline lookup.

---

## 🧠 Concept

`whatis NAME` prints the exact one-line summary of a command (it matches the *name*) — `whatis` is literally `man -f`. `apropos KEYWORD` searches the *descriptions* of all man pages for the keyword — it's `man -k` — and is what you use when you don't know the command's name ("apropos compression"). Both read a pre-built index (the `whatis` database) maintained by `mandb`; if you just installed software and `apropos` finds nothing, run `sudo mandb` to refresh the index. `apropos -s 1` (or `-s 8`) restricts results to a section, cutting noise. The mental model: `whatis` = exact name lookup, `apropos` = fuzzy "what does X" search.

```
whatis ls          → ls (1) - list directory contents
apropos password   → every page whose summary mentions "password"
apropos -s 1 copy  → only section-1 (command) pages about copying
sudo mandb         → rebuild the whatis index after installs
```

> **Why this matters:** On the exam you can't Google "command to change file ownership." `apropos ownership` finds `chown` in seconds. `whatis` confirms you've got the right one.

---

## 📚 Command Reference

| Command | Purpose | Notes |
|---|---|---|
| `whatis NAME` | Exact one-line summary | = `man -f` |
| `apropos KEY` | Search descriptions | = `man -k` |
| `apropos -s N` | Restrict to section | cut noise |
| `apropos -a a b` | Match all keywords | AND search |
| `mandb` | Rebuild index | after installs |

---

## 🧰 LAB-WIDE SETUP

**In plain English:** Make a sandbox for saved searches; data comes from the man index.

> Run this block **once** before Task 1. `LAB_ROOT` holds any notes you save.

```bash
export LAB_ROOT=/tmp/lab-29
mkdir -p "$LAB_ROOT"
cd "$LAB_ROOT"
echo "ready"
echo "exit was: $?"
```

**Expected output:**

```
ready
exit was: 0
```

---

## TASK 1 of 2 — Exact and keyword lookups

**In plain English:** We get an exact summary, then search by what a tool does.

---

### Step 1 of 2 — Exact summary with `whatis`

**In plain English:** We look up the precise one-line description of a couple of commands.

```bash
whatis chmod
whatis chown grep
echo "exit was: $?"
```

**Expected output:**

```
chmod (1)            - change file mode bits
chown (1)            - change file owner and group
grep (1)             - print lines that match patterns
exit was: 0
```

**Line-by-line breakdown:**

- `whatis chmod` → Exact-name lookup of the one-line summary and section.
- `whatis chown grep` → `whatis` accepts multiple names at once.

**New words in this step:**

- **`whatis`** — exact one-line summary by command name (same as `man -f`).

---

### Step 2 of 2 — Keyword search with `apropos`

**In plain English:** We find commands related to a concept without knowing their names.

```bash
apropos "owner" | head -5
echo "---"
apropos compression | head -5
echo "exit was: $?"
```

**Expected output:**

```
chown (1)            - change file owner and group
chgrp (1)            - change group ownership
...
gzip (1)             - compress or expand files
bzip2 (1)            - a block-sorting file compressor
...
exit was: 0
```

**Line-by-line breakdown:**

- `apropos "owner"` → Search all summaries for "owner" — finds `chown`, `chgrp`, etc., even though you didn't know the names.
- `apropos compression` → Discover compression tools the same way.

**New words in this step:**

- **`apropos`** — keyword search across all man-page descriptions (same as `man -k`).

---

### Concept card (Task 1)

| Concept | What it does | Exam trap |
|---|---|---|
| `whatis` | exact name | not a keyword search |
| `apropos` | description search | needs the index |
| both = `man -f`/`-k` | aliases | same data |

---

### Troubleshoot (Task 1)

| Symptom | Likely cause | Fix |
|---|---|---|
| `whatis` "nothing appropriate" | Wrong name / no index | Check spelling; `mandb` |
| `apropos` empty | Stale index | Run `sudo mandb` |

---

## TASK 2 of 2 — Narrowing and indexing

**In plain English:** We restrict searches to a section, then rebuild the index.

---

### Step 1 of 2 — Restrict to a section with `-s`

**In plain English:** We search only command (section 1) pages, then only config-file (section 5) pages.

```bash
apropos -s 1 "directory" | head -3
echo "---"
apropos -s 5 "password" | head -3
echo "exit was: $?"
```

**Expected output:**

```
ls (1)               - list directory contents
mkdir (1)            - make directories
rmdir (1)            - remove empty directories
---
passwd (5)           - the password file
shadow (5)           - shadowed password file
...
exit was: 0
```

**Line-by-line breakdown:**

- `apropos -s 1 "directory"` → Restrict to section 1 (commands) — no config-file or syscall noise.
- `apropos -s 5 "password"` → Restrict to section 5 — finds the config-file formats `passwd(5)`, `shadow(5)`.

**New words in this step:**

- **`apropos -s N`** — restrict keyword results to a manual section.

---

### Step 2 of 2 — Rebuild the index with `mandb`

**In plain English:** We refresh the whatis database so searches reflect installed packages.

```bash
sudo mandb 2>&1 | tail -3
whatis ls
echo "exit was: $?"
```

**Expected output:**

```
... manual page(s) added ...
... whatis entries updated ...
ls (1)               - list directory contents
exit was: 0
```

**Line-by-line breakdown:**

- `sudo mandb` → Rebuild the whatis/apropos index from the installed man pages.
- `whatis ls` → Confirms lookups work after the rebuild.

**New words in this step:**

- **`mandb`** — rebuilds the index that `whatis`/`apropos` read.

---

### Concept card (Task 2)

| Concept | What it does | Exam trap |
|---|---|---|
| `-s 1` / `-s 5` | section filter | cuts noise |
| `mandb` | rebuild index | needed after installs |
| index-backed | not live scan | stale until rebuilt |

---

### Troubleshoot (Task 2)

| Symptom | Likely cause | Fix |
|---|---|---|
| New tool not found | Index stale | `sudo mandb` |
| Too many results | No section filter | Add `-s N` |

---

## ✅ Lab Checklist

- [ ] Task 1 · Step 1 — Exact summary with `whatis`
- [ ] Task 1 · Step 2 — Keyword search with `apropos`
- [ ] Task 2 · Step 1 — Restrict to a section with `-s`
- [ ] Task 2 · Step 2 — Rebuild the index with `mandb`
- [ ] Every 🎯 Focus Coverage row (Anchor + NEW) mapped to a step
- [ ] 🧹 Teardown run — sandbox + any system state removed

---

## 🧹 Teardown

**In plain English:** Delete everything this lab created so the box is clean for the next run.

> Run this after you've verified the lab. `lab_teardown.sh` safely removes the single sandbox root — it refuses to touch `/`, `$HOME`, or any protected path. This lab only rebuilt the man index (harmless) and changed **no** other system state.

```bash
cd /tmp
bash lab_teardown.sh "$LAB_ROOT"     # = /tmp/lab-29
```

**Expected output:**

```
✅ Removed /tmp/lab-29 — lab workspace is clean.
```

---

## ⚠️ Common Pitfalls

| Mistake | Symptom | Fix |
|---|---|---|
| Using `whatis` as search | "nothing appropriate" | Use `apropos` for keywords |
| Stale index | New tools missing | `sudo mandb` |
| Result overload | Too broad | Filter with `-s` |

---

## 📌 Exam Strategy

When you don't know the command, `apropos KEYWORD` finds it; `whatis NAME` confirms it. Filter with `-s` to cut noise, and remember `mandb` if a freshly installed tool isn't showing up.

- `apropos` for "what does X" discovery.
- `whatis` to verify the exact command.
- `-s 5` finds config-file formats fast.

---

## 🔗 Related Labs

- [Lab 29b — Searching Manuals by Keyword (Ansible)](../lab-29b-apropos-whatis-ansible/) — keyword discovery in a play
- [Lab 29c — Searching Manuals by Keyword (Verify)](../lab-29c-apropos-whatis-verify/) — prove searches return the right tools
- [Lab 28a — Exploring Manual Pages (RHCSA)](../lab-28a-man-pages-rhcsa/) — reading the pages you discover

---

## 👤 Author

**Kelvin R. Tobias**  
[kelvinintech.com](https://kelvinintech.com) · [GitHub](https://github.com/kelvintechnical) · [LinkedIn](https://www.linkedin.com/in/kelvin-r-tobias-211949219)
