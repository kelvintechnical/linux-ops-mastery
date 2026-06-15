# Lab 28a: Exploring Manual Pages (RHCSA) — `man`, sections, `man -w`

**Series:** linux-ops-mastery — Documentation · **Lab 28a of the Novice → RHCA path**  
**Certifications covered:** RHCSA EX200 (using built-in documentation — the on-exam reference), SRE/DevOps (offline self-help)  
**Prerequisite:** [Lab 27c](../lab-27c-vipw-vigr-safe-editing-verify/) completed  
**Time Estimate:** 20–30 minutes  
**Difficulty:** Beginner

---

## 🎯 Today's Focus Coverage

> Stay on-subject via the ANCHOR rows; expand vocabulary via the NEW rows. Every row is exercised by a STEP below.

**⚓ Anchor — already learned (on-topic reuse)**

| # | Command / switch | Covered by |
|---|---|---|
| A1 | `less` navigation in pager | _Task 1 · Step 2_ |
| A2 | `man -w` (path) | _Task 2 · Step 2_ |

**🆕 NEW this lab — introduced for the first time** (minimum 3)

| # | Command / switch | First taught in | Covered by |
|---|---|---|---|
| N1 | `man COMMAND` + navigation | Task 1 · Step 1 | _Task 1 · Step 1_ |
| N2 | man sections (`man 5 passwd`) | Task 2 · Step 1 | _Task 2 · Step 1_ |
| N3 | `man -f` / `man -k` | Task 1 · Step 1 | _Task 1 · Step 1_ |
| N4 | `man -w` (page path) | Task 2 · Step 2 | _Task 2 · Step 2_ |

---

## 🎯 Objective

Use the manual — your only reference on the exam. You will open a man page and navigate it, understand the numbered sections (and why `passwd` has two pages), jump straight to a section (`man 5 passwd`), find the page file on disk (`man -w`), and use `man -f`/`man -k` for one-line summaries and keyword search. By the end you can answer almost any "how does this work?" without internet.

> **Note:** `man` opens an interactive pager (`less`). Use `/` to search, `n` for next, `q` to quit.

---

## 🧠 Concept

The manual is organized into numbered **sections**: 1 = user commands, 2 = system calls, 3 = library functions, 4 = devices, 5 = file formats/configs, 6 = games, 7 = misc/conventions, 8 = admin commands. A name can appear in several sections — `passwd` is both the command (`man 1 passwd`) and the file format (`man 5 passwd`); `man passwd` shows the lowest-numbered (the command) unless you specify. Inside `man` you're in `less`: `/pattern` searches, `n`/`N` repeat, `g`/`G` jump, `q` quits. `man -f name` (a.k.a. `whatis`) prints the one-line summary and section; `man -k keyword` (a.k.a. `apropos`) searches all summaries. `man -w name` prints the path to the page source.

```
man ls            → the ls(1) page in less
man 5 passwd      → the /etc/passwd FILE FORMAT page (section 5)
man -f passwd     → one-line summary + which sections exist
man -k network    → all pages whose summary mentions "network"
man -w ls         → /usr/share/man/man1/ls.1.gz  (the file)
```

> **Why this matters:** The exam allows `man` but not the internet. Knowing sections (especially 5 for config-file formats) and `-k`/`-f` to find the right page fast is genuinely worth exam points.

---

## 📚 Command Reference

| Command | Purpose | Notes |
|---|---|---|
| `man NAME` | Open a page | lowest section by default |
| `man N NAME` | Specific section | `man 5 passwd` |
| `man -f NAME` | One-line summary | = `whatis` |
| `man -k KEY` | Search summaries | = `apropos` |
| `man -w NAME` | Page file path | locate the source |
| `/` `n` `q` | Search / next / quit | inside the pager |

---

## 🧰 LAB-WIDE SETUP

**In plain English:** Make a sandbox to save notes; the man pages come from the system.

> Run this block **once** before Task 1. `LAB_ROOT` just holds any notes you save.

```bash
export LAB_ROOT=/tmp/lab-28
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

## TASK 1 of 2 — Open and search pages

**In plain English:** We find a page with a summary search, then open and navigate it.

---

### Step 1 of 2 — Summaries with `man -f` and `man -k`

**In plain English:** We get the one-line description of a command and search all summaries by keyword.

```bash
man -f ls
man -k "list directory contents" | head -3
echo "exit was: $?"
```

**Expected output:**

```
ls (1)               - list directory contents
ls (1)               - list directory contents
dir (1)              - list directory contents
vdir (1)             - list directory contents
exit was: 0
```

**Line-by-line breakdown:**

- `man -f ls` → One-line summary plus the section number `(1)` — same as `whatis ls`.
- `man -k "..."` → Search every page's summary for the phrase — same as `apropos`.

**New words in this step:**

- **`man -f`** — one-line summary (`whatis`).
- **`man -k`** — keyword search across summaries (`apropos`).

---

### Step 2 of 2 — Open and navigate a page

**In plain English:** We open the `ls` page and search inside it for an option.

```bash
man ls
# Inside the pager:
#   /human-readable   then Enter → jumps to the -h description
#   n                 → next match
#   q                 → quit
echo "exit was: $?"
```

**Expected output (on screen):**

```
LS(1)                          User Commands                         LS(1)

NAME
       ls - list directory contents
... (/human-readable jumps to the -h option description) ...
```

**Line-by-line breakdown:**

- `man ls` → Open `ls(1)` in the `less` pager.
- `/human-readable` → Search inside the page; `n` repeats, `q` quits — the same keys as Lab 20's `less`.

**New words in this step:**

- **man navigation** — `man` opens in `less`; `/`, `n`, `q` work as usual.

---

### Concept card (Task 1)

| Concept | What it does | Exam trap |
|---|---|---|
| `man -f` | summary | needs mandb cache |
| `man -k` | keyword search | quote multi-word |
| in-page `/` | search | `q` to quit |

---

### Troubleshoot (Task 1)

| Symptom | Likely cause | Fix |
|---|---|---|
| `-k`/`-f` empty | mandb not built | `sudo mandb` |
| Stuck in man | In the pager | Press `q` |

---

## TASK 2 of 2 — Sections and page paths

**In plain English:** We open a specific section, then find where the page lives.

---

### Step 1 of 2 — Jump to a section with `man N`

**In plain English:** We open the *file-format* page for `passwd` (section 5), not the command.

```bash
man -f passwd
man 5 passwd
# Inside the pager: read the /etc/passwd field description, then press q
echo "exit was: $?"
```

**Expected output:**

```
passwd (1)           - change user password
passwd (5)           - the password file
(then the section-5 page opens, describing the /etc/passwd fields)
exit was: 0
```

**Line-by-line breakdown:**

- `man -f passwd` → Shows `passwd` exists in *both* section 1 (command) and section 5 (file format).
- `man 5 passwd` → Open the section-5 page describing the `/etc/passwd` format — the one you want when editing the file.

**New words in this step:**

- **section** — numbered manual category; 5 is file formats/configs.

---

### Step 2 of 2 — Locate the page with `man -w`

**In plain English:** We print the path to the man page source file.

```bash
man -w ls
man -w 5 passwd
echo "exit was: $?"
```

**Expected output:**

```
/usr/share/man/man1/ls.1.gz
/usr/share/man/man5/passwd.5.gz
exit was: 0
```

**Line-by-line breakdown:**

- `man -w ls` → Path to the `ls(1)` page source (`man1/ls.1.gz`).
- `man -w 5 passwd` → Path to the section-5 page; the `man5` directory confirms the section.

**New words in this step:**

- **`man -w`** — print the filesystem path of the man page.

---

### Concept card (Task 2)

| Concept | What it does | Exam trap |
|---|---|---|
| `man N name` | specific section | default = lowest |
| section 5 | file formats | for config files |
| `man -w` | page path | shows `manN/` dir |

---

### Troubleshoot (Task 2)

| Symptom | Likely cause | Fix |
|---|---|---|
| Wrong page opens | Default lowest section | Specify the number |
| `-w` not found | Package not installed | Install the relevant package |

---

## ✅ Lab Checklist

- [ ] Task 1 · Step 1 — Summaries with `man -f` and `man -k`
- [ ] Task 1 · Step 2 — Open and navigate a page
- [ ] Task 2 · Step 1 — Jump to a section with `man N`
- [ ] Task 2 · Step 2 — Locate the page with `man -w`
- [ ] Every 🎯 Focus Coverage row (Anchor + NEW) mapped to a step
- [ ] 🧹 Teardown run — sandbox + any system state removed

---

## 🧹 Teardown

**In plain English:** Delete everything this lab created so the box is clean for the next run.

> Run this after you've verified the lab. `lab_teardown.sh` safely removes the single sandbox root — it refuses to touch `/`, `$HOME`, or any protected path. This lab changed **no** system state.

```bash
cd /tmp
bash lab_teardown.sh "$LAB_ROOT"     # = /tmp/lab-28
```

**Expected output:**

```
✅ Removed /tmp/lab-28 — lab workspace is clean.
```

---

## ⚠️ Common Pitfalls

| Mistake | Symptom | Fix |
|---|---|---|
| Ignoring sections | Read command page for a config | Use `man 5` for formats |
| Forgetting `-k`/`-f` | Can't find the right page | Search summaries first |
| Lost in the pager | Can't exit | Press `q` |

---

## 📌 Exam Strategy

`man` is your on-exam reference. Use `man -k`/`-f` to find the right page, `man N name` to hit the correct section (5 for config files), and `/` to search within. When editing a config, the section-5 page is gold.

- `man 5 <file>` for any config-file format.
- `man -k keyword` when you don't know the command name.
- `/` + `n` to find an option fast inside a page.

---

## 🔗 Related Labs

- [Lab 28b — Exploring Manual Pages (Ansible)](../lab-28b-man-pages-ansible/) — capturing man content in a play
- [Lab 28c — Exploring Manual Pages (Verify)](../lab-28c-man-pages-verify/) — prove pages exist and resolve
- [Lab 29a — Searching Manuals by Keyword (RHCSA)](../lab-29a-apropos-whatis-rhcsa/) — `whatis`/`apropos` deep dive

---

## 👤 Author

**Kelvin R. Tobias**  
[kelvinintech.com](https://kelvinintech.com) · [GitHub](https://github.com/kelvintechnical) · [LinkedIn](https://www.linkedin.com/in/kelvin-r-tobias-211949219)
