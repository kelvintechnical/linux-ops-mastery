# Lab 26a: Command and Insert Mode in vi (RHCSA) — `vi`, modes, `:wq`

**Series:** linux-ops-mastery — Text Editors · **Lab 26a of the Novice → RHCA path**  
**Certifications covered:** RHCSA EX200 (editing files with vi/vim — the only guaranteed editor), SRE/DevOps (editing on minimal/remote systems)  
**Prerequisite:** [Lab 25c](../lab-25c-awk-columns-verify/) completed  
**Time Estimate:** 25–35 minutes  
**Difficulty:** Beginner

---

## 🎯 Today's Focus Coverage

> Stay on-subject via the ANCHOR rows; expand vocabulary via the NEW rows. Every row is exercised by a STEP below.

**⚓ Anchor — already learned (on-topic reuse)**

| # | Command / switch | Covered by |
|---|---|---|
| A1 | creating files | _Task 1 · Step 1_ |
| A2 | `cat` to inspect | _Task 1 · Step 2_ |

**🆕 NEW this lab — introduced for the first time** (minimum 3)

| # | Command / switch | First taught in | Covered by |
|---|---|---|---|
| N1 | vi modes (normal/insert/command) | Task 1 · Step 1 | _Task 1 · Step 1_ |
| N2 | `i` `a` `o` insert, `Esc`, `:wq` | Task 1 · Step 1 | _Task 1 · Step 1_ |
| N3 | `dd` `x` `yy` `p` editing | Task 2 · Step 1 | _Task 2 · Step 1_ |
| N4 | `/search`, `:%s///g`, `:q!` | Task 2 · Step 2 | _Task 2 · Step 2_ |

---

## 🎯 Objective

Become competent in `vi`/`vim` — the editor guaranteed to exist on every Red Hat system, even rescue mode. You will learn the three modes and how to move between them, insert text (`i`/`a`/`o`), save and quit (`:wq`, `:q!`), edit with `dd`/`x`/`yy`/`p`, and search-and-replace (`/`, `:%s///g`). By the end you can confidently edit any config file when `vi` is the only tool available.

> **Note:** `vi` is interactive. Run `vi FILE`, type the listed keystrokes, and watch the result. The "expected output" shows the file/screen state. If you get lost, press `Esc` then `:q!` Enter to quit without saving.

---

## 🧠 Concept

`vi` has three **modes**. **Normal** (the default, where you land) is for navigation and commands — letters move and edit, they don't type. **Insert** mode (entered with `i`, `a`, `o`, …) is where typing inserts text; `Esc` returns to normal. **Command-line** mode (entered with `:` from normal) runs ex commands like `:w` (write), `:q` (quit), `:wq` (both), `:q!` (quit discarding changes). The classic beginner trap is typing in normal mode and seeing letters trigger commands — always know which mode you're in (vim shows `-- INSERT --` at the bottom). Editing verbs in normal mode: `x` deletes a char, `dd` a line, `yy` yanks (copies) a line, `p` pastes; `/text` searches; `:%s/old/new/g` replaces globally.

```
vi file        → opens in NORMAL mode
i / a / o      → enter INSERT (before / after cursor / new line)
Esc            → back to NORMAL
:w  :q  :wq    → write / quit / write+quit (COMMAND-line)
:q!            → quit, discard changes
dd  x  yy  p   → delete line / char, yank line, paste
/foo  :%s/a/b/g → search / global replace
```

> **Why this matters:** The exam has no GUI and may drop you in an environment with only `vi`. Mode awareness and `:wq`/`:q!` are survival skills; the editing verbs make you fast.

---

## 📚 Command Reference

| Key / command | Purpose | Mode |
|---|---|---|
| `i` `a` `o` | Insert before/after/new line | normal → insert |
| `Esc` | Return to normal | insert → normal |
| `:w` `:q` `:wq` `:q!` | Write / quit / both / force-quit | command-line |
| `x` `dd` | Delete char / line | normal |
| `yy` `p` | Yank / paste line | normal |
| `/text` `n` | Search / next | normal |
| `:%s/old/new/g` | Global replace | command-line |

---

## 🧰 LAB-WIDE SETUP

**In plain English:** Build a sandbox to practice editing in.

> Run this block **once** before Task 1. It defines a single sandbox root
> (`LAB_ROOT`) that every file in this lab lives under, so the Teardown
> section can wipe it in one safe command.

```bash
export LAB_ROOT=/tmp/lab-26
mkdir -p "$LAB_ROOT"
cd "$LAB_ROOT"
printf 'line one\nline two\nline three\n' > notes.txt
cat notes.txt
echo "exit was: $?"
```

**Expected output:**

```
line one
line two
line three
exit was: 0
```

---

## TASK 1 of 2 — Modes, insert, save

**In plain English:** We open a file, insert text, and save it.

---

### Step 1 of 2 — Insert text and save with `:wq`

**In plain English:** We open the file, add a line in insert mode, and write+quit.

```bash
cd "$LAB_ROOT"
vi notes.txt
# Keystrokes:
#   o            → open a new line below and enter INSERT mode
#   line four    → type the text
#   Esc          → return to NORMAL mode
#   :wq          → write and quit  (then Enter)
```

**Expected file state after (verify with cat):**

```
line one
line two
line three
line four
```

**Line-by-line breakdown:**

- `o` → Open a new line *below* the cursor and switch to insert mode.
- `Esc` → Leave insert mode for normal mode (this is the step beginners forget).
- `:wq` → Write the file and quit.

**New words in this step:**

- **modes** — normal (commands), insert (typing), command-line (`:` commands).
- **`:wq`** — write the file and quit.

---

### Step 2 of 2 — Confirm the save

**In plain English:** We verify the new line was actually written to disk.

```bash
cd "$LAB_ROOT"
cat notes.txt
wc -l notes.txt
echo "exit was: $?"
```

**Expected output:**

```
line one
line two
line three
line four
4 notes.txt
exit was: 0
```

**Line-by-line breakdown:**

- `cat notes.txt` → The file now has the inserted line, proving `:wq` saved it.
- `wc -l notes.txt` → Four lines confirm the insert.

**New words in this step:**

- **write** — saving the in-memory buffer to disk with `:w`.

---

### Concept card (Task 1)

| Concept | What it does | Exam trap |
|---|---|---|
| `i`/`a`/`o` | enter insert | `o` makes a new line |
| `Esc` | back to normal | forgetting it = chaos |
| `:wq` | save + quit | `:q` alone fails if dirty |

---

### Troubleshoot (Task 1)

| Symptom | Likely cause | Fix |
|---|---|---|
| Letters trigger commands | In normal mode | Press `i` to insert |
| `:q` refuses to quit | Unsaved changes | `:wq` to save or `:q!` to discard |
| Stuck, beeping | Unknown state | `Esc` repeatedly, then `:q!` |

---

## TASK 2 of 2 — Edit, search, replace

**In plain English:** We delete and copy lines, then search-and-replace.

---

### Step 1 of 2 — Delete, yank, paste

**In plain English:** We delete a line, then copy a line and paste it.

```bash
cd "$LAB_ROOT"
vi notes.txt
# Keystrokes (all in NORMAL mode):
#   gg           → go to the first line
#   dd           → delete the current line ("line one")
#   yy           → yank (copy) the current line ("line two")
#   p            → paste it below
#   :wq          → save and quit
```

**Expected file state after (verify with cat):**

```
line two
line two
line three
line four
```

**Line-by-line breakdown:**

- `dd` → Delete the whole current line.
- `yy` then `p` → Yank (copy) the current line and paste a copy below it.

**New words in this step:**

- **`dd` / `yy` / `p`** — delete line / yank line / paste.

---

### Step 2 of 2 — Search and global replace

**In plain English:** We search for a word, then replace all occurrences, and practice quitting without saving.

```bash
cd "$LAB_ROOT"
vi notes.txt
# Keystrokes:
#   /three       → search for "three" (then Enter); n = next match
#   :%s/line/row/g   → replace every "line" with "row" on all lines (Enter)
#   :q!          → quit WITHOUT saving (discard the replace) — practice the escape hatch
```

**Expected file state after (unchanged, because we used :q!):**

```
line two
line two
line three
line four
```

**Line-by-line breakdown:**

- `/three` → Search forward for "three"; `n` jumps to the next match.
- `:%s/line/row/g` → On every line (`%`), substitute all (`g`) "line" with "row".
- `:q!` → Quit discarding changes — so the file stays as it was, demonstrating the safe abort.

**New words in this step:**

- **`:%s/old/new/g`** — global search-and-replace across the whole file.
- **`:q!`** — quit without saving (discard changes).

---

### Concept card (Task 2)

| Concept | What it does | Exam trap |
|---|---|---|
| `/text` | search | `n`/`N` repeat |
| `:%s///g` | global replace | `%` = all lines |
| `:q!` | discard + quit | your escape hatch |

---

### Troubleshoot (Task 2)

| Symptom | Likely cause | Fix |
|---|---|---|
| Replace hit one line | Missing `%` | Use `:%s` for all lines |
| Replace hit first only | Missing `g` | Add `g` flag |
| Accidentally edited | Wrong mode | `:q!` then reopen |

---

## ✅ Lab Checklist

- [ ] Task 1 · Step 1 — Insert text and save with `:wq`
- [ ] Task 1 · Step 2 — Confirm the save
- [ ] Task 2 · Step 1 — Delete, yank, paste
- [ ] Task 2 · Step 2 — Search and global replace
- [ ] Every 🎯 Focus Coverage row (Anchor + NEW) mapped to a step
- [ ] 🧹 Teardown run — sandbox + any system state removed

---

## 🧹 Teardown

**In plain English:** Delete everything this lab created so the box is clean for the next run.

> Run this after you've verified the lab. `lab_teardown.sh` safely removes the single sandbox root — it refuses to touch `/`, `$HOME`, or any protected path. This lab changed **no** system state.

```bash
cd /tmp
bash lab_teardown.sh "$LAB_ROOT"     # = /tmp/lab-26
```

**Expected output:**

```
✅ Removed /tmp/lab-26 — lab workspace is clean.
```

---

## ⚠️ Common Pitfalls

| Mistake | Symptom | Fix |
|---|---|---|
| Typing in normal mode | Letters run commands | Press `i` first |
| Can't quit | Unsaved changes block `:q` | `:wq` or `:q!` |
| Replace too narrow | Only one line/match | `:%s/.../.../g` |

---

## 📌 Exam Strategy

`vi` is the editor you can always count on. Internalize the mode cycle (`i` to insert, `Esc` to normal, `:` for commands) and the four exits (`:w`, `:q`, `:wq`, `:q!`). Add `dd`/`yy`/`p` and `:%s///g` for speed.

- When confused, `Esc` then decide: `:wq` to save or `:q!` to bail.
- `:%s/old/new/g` is the fast global edit.
- vim shows `-- INSERT --` at the bottom — read it to know your mode.

---

## 🔗 Related Labs

- [Lab 26b — Command/Insert Mode in vi (Ansible)](../lab-26b-vi-editor-ansible/) — declarative edits instead of interactive vi
- [Lab 26c — Command/Insert Mode in vi (Verify)](../lab-26c-vi-editor-verify/) — prove the edits saved
- [Lab 27a — Safely Editing System Databases (RHCSA)](../lab-27a-vipw-vigr-safe-editing-rhcsa/) — `vipw`/`vigr` locked editing

---

## 👤 Author

**Kelvin R. Tobias**  
[kelvinintech.com](https://kelvinintech.com) · [GitHub](https://github.com/kelvintechnical) · [LinkedIn](https://www.linkedin.com/in/kelvin-r-tobias-211949219)
