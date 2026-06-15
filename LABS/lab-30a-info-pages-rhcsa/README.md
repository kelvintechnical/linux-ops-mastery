# Lab 30a: Navigating info Pages (RHCSA) — `info`, nodes, `n`/`p`/`u`

**Series:** linux-ops-mastery — Documentation · **Lab 30a of the Novice → RHCA path**  
**Certifications covered:** RHCSA EX200 (using the second documentation system), SRE/DevOps (deep GNU-tool reference)  
**Prerequisite:** [Lab 29c](../lab-29c-apropos-whatis-verify/) completed  
**Time Estimate:** 20–30 minutes  
**Difficulty:** Beginner

---

## 🎯 Today's Focus Coverage

> Stay on-subject via the ANCHOR rows; expand vocabulary via the NEW rows. Every row is exercised by a STEP below.

**⚓ Anchor — already learned (on-topic reuse)**

| # | Command / switch | Covered by |
|---|---|---|
| A1 | `man` as the other doc system | _Task 1 · Step 1_ |
| A2 | pager-style search (`/`) | _Task 2 · Step 1_ |

**🆕 NEW this lab — introduced for the first time** (minimum 3)

| # | Command / switch | First taught in | Covered by |
|---|---|---|---|
| N1 | `info COMMAND` + nodes | Task 1 · Step 1 | _Task 1 · Step 1_ |
| N2 | `n` / `p` / `u` navigation | Task 1 · Step 2 | _Task 1 · Step 2_ |
| N3 | menu items + `Enter` / `l` | Task 2 · Step 1 | _Task 2 · Step 1_ |
| N4 | `info --output` / `s` search | Task 2 · Step 2 | _Task 2 · Step 2_ |

---

## 🎯 Objective

Use `info`, the GNU documentation system that's often richer than `man` for GNU tools (coreutils, bash, gawk). You will open an info document, understand its tree of **nodes**, move between sibling nodes (`n`/`p`), go up to the parent (`u`), follow menu items into subtopics, and search. By the end you can read the long-form GNU manuals that `man` only summarizes.

> **Note:** `info` is interactive. Keys: `n` next, `p` previous, `u` up, `Enter` follow menu item, `l` back, `s` search, `q` quit.

---

## 🧠 Concept

Where `man` shows one flat page, `info` organizes documentation as a tree of **nodes** linked like a mini-website. The top node has a **menu** (`* Item::` lines); pressing `Enter` on a menu item descends into that node. Navigation keys: `n` (next sibling node), `p` (previous sibling), `u` (up to parent), `l` (last — go back where you came from), `Enter`/`m` (follow a menu item by selecting it). `s` searches the whole document; `q` quits. Many GNU tools ship a brief `man` page that says "the full documentation is in the info manual" — `info coreutils 'ls invocation'` jumps straight to that section. Think `man` = quick reference, `info` = the book.

```
info ls               → the ls info node (often via coreutils)
n / p                 → next / previous sibling node
u                     → up to the parent node
Enter (on * Item::)   → descend into that menu item
s pattern             → search the document
q                     → quit
```

> **Why this matters:** For GNU coreutils and bash, the `info` manual is the authoritative, complete reference. When a `man` page ends with "see the info manual," `info` is where the real answer lives.

---

## 📚 Command Reference

| Key / command | Purpose | Notes |
|---|---|---|
| `info NAME` | Open info doc | tree of nodes |
| `n` / `p` | Next / previous node | siblings |
| `u` | Up to parent | one level |
| `Enter` / `m` | Follow menu item | descend |
| `l` | Back (last node) | history |
| `s` | Search document | `q` to quit |

---

## 🧰 LAB-WIDE SETUP

**In plain English:** Make a sandbox for notes; info docs come from the system.

> Run this block **once** before Task 1. `LAB_ROOT` holds any notes you save.

```bash
export LAB_ROOT=/tmp/lab-30
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

## TASK 1 of 2 — Open and move between nodes

**In plain English:** We open an info document and navigate its nodes.

---

### Step 1 of 2 — Open an info document

**In plain English:** We open the coreutils info manual at the `ls` section.

```bash
info coreutils 'ls invocation'
# Inside info:
#   read the node; note the top line shows Next:, Prev:, Up:
#   q   → quit
echo "exit was: $?"
```

**Expected output (on screen):**

```
Next: dir invocation,  Prev: ...,  Up: Directory listing

10.1 'ls': List directory contents
==================================
... (full ls documentation) ...
```

**Line-by-line breakdown:**

- `info coreutils 'ls invocation'` → Open the coreutils manual directly at the `ls` node.
- the header `Next:/Prev:/Up:` → Shows the node's neighbors in the tree — your navigation map.

**New words in this step:**

- **node** — a single page in the info tree, linked to Next/Prev/Up neighbors.

---

### Step 2 of 2 — Move with `n`, `p`, `u`

**In plain English:** We step to the next node, back, and up to the parent.

```bash
info coreutils 'ls invocation'
# Inside info:
#   n   → jump to the Next node (e.g. "dir invocation")
#   p   → jump to the Previous node
#   u   → go Up to the parent (e.g. "Directory listing")
#   q   → quit
```

**Expected output (on screen):**

```
(after n) 10.2 'dir': ...
(after p) 10.1 'ls': ...
(after u) Directory listing  (the parent node with its menu)
```

**Line-by-line breakdown:**

- `n` / `p` → Move to the next / previous *sibling* node at the same level.
- `u` → Move *up* to the parent node, which usually shows a menu of its children.

**New words in this step:**

- **`n` / `p` / `u`** — next / previous sibling / up to parent navigation.

---

### Concept card (Task 1)

| Concept | What it does | Exam trap |
|---|---|---|
| node tree | linked pages | not one flat page |
| `n`/`p` | siblings | same level only |
| `u` | parent | shows the menu |

---

### Troubleshoot (Task 1)

| Symptom | Likely cause | Fix |
|---|---|---|
| `info ls` shows man text | No info manual for it | Try `info coreutils` |
| Lost in nodes | Forgot the map | Read the `Next/Prev/Up` header |

---

## TASK 2 of 2 — Menus and search

**In plain English:** We follow a menu item into a subtopic, then search the document.

---

### Step 1 of 2 — Follow a menu item

**In plain English:** We open the top of a manual and descend into a menu item with `Enter`.

```bash
info coreutils
# Inside info (top node shows a menu of "* Item::" lines):
#   move the cursor to a menu line like "* ls invocation::"
#   Enter   → descend into that node
#   l       → go back (last node)
#   q       → quit
```

**Expected output (on screen):**

```
* Menu:
* Common options::
* Output of entire files::    cat tac nl ...
* ls invocation::             ls
... (Enter on "* ls invocation::" opens that node) ...
```

**Line-by-line breakdown:**

- `info coreutils` → Open the manual's top node, which lists `* Item::` menu entries.
- `Enter` on a menu line → Descend into that subtopic node; `l` returns to where you were.

**New words in this step:**

- **menu item** — a `* Item::` link you follow with `Enter` to descend the tree.

---

### Step 2 of 2 — Search and export with `s` / `--output`

**In plain English:** We search inside a document, then dump a node to a file non-interactively.

```bash
cd "$LAB_ROOT"
# Interactive search:
info coreutils 'ls invocation'
#   s   → type "human-readable" then Enter to jump to that text; q to quit
# Non-interactive export of the node to a file:
info --output=ls-node.txt coreutils 'ls invocation'
head -5 ls-node.txt
echo "exit was: $?"
```

**Expected output:**

```
(interactive: s jumps to the --human-readable description)
10.1 'ls': List directory contents
==================================
... (first lines of the exported node) ...
exit was: 0
```

**Line-by-line breakdown:**

- `s` (inside info) → Search the whole document for text and jump to it.
- `info --output=ls-node.txt ...` → Write the node to a file non-interactively — handy for saving or grepping.

**New words in this step:**

- **`s`** — search within an info document.
- **`--output`** — dump an info node to a file without the interactive UI.

---

### Concept card (Task 2)

| Concept | What it does | Exam trap |
|---|---|---|
| `* Item::` | menu link | `Enter` to follow |
| `s` | doc search | different from man `/` |
| `--output` | export node | non-interactive |

---

### Troubleshoot (Task 2)

| Symptom | Likely cause | Fix |
|---|---|---|
| `Enter` does nothing | Cursor not on menu line | Move onto `* Item::` |
| Export empty | Wrong node name | Quote the exact node |

---

## ✅ Lab Checklist

- [ ] Task 1 · Step 1 — Open an info document
- [ ] Task 1 · Step 2 — Move with `n`, `p`, `u`
- [ ] Task 2 · Step 1 — Follow a menu item
- [ ] Task 2 · Step 2 — Search and export with `s` / `--output`
- [ ] Every 🎯 Focus Coverage row (Anchor + NEW) mapped to a step
- [ ] 🧹 Teardown run — sandbox + any system state removed

---

## 🧹 Teardown

**In plain English:** Delete everything this lab created so the box is clean for the next run.

> Run this after you've verified the lab. `lab_teardown.sh` safely removes the single sandbox root — it refuses to touch `/`, `$HOME`, or any protected path. This lab changed **no** system state.

```bash
cd /tmp
bash lab_teardown.sh "$LAB_ROOT"     # = /tmp/lab-30
```

**Expected output:**

```
✅ Removed /tmp/lab-30 — lab workspace is clean.
```

---

## ⚠️ Common Pitfalls

| Mistake | Symptom | Fix |
|---|---|---|
| Treating info like man | Confused by nodes | Learn `n`/`p`/`u` |
| Ignoring info for GNU tools | Missing full docs | `info coreutils` |
| Can't quit | In the reader | Press `q` |

---

## 📌 Exam Strategy

When a `man` page says "see the info manual," use `info`. Navigate with `n`/`p`/`u`, follow `* Item::` menus with `Enter`, and `s` to search. `info --output` lets you dump a node to grep it.

- `info coreutils 'X invocation'` jumps straight to a tool.
- `u` then read the menu to orient yourself.
- `--output` for non-interactive extraction.

---

## 🔗 Related Labs

- [Lab 30b — Navigating info Pages (Ansible)](../lab-30b-info-pages-ansible/) — extracting info content in a play
- [Lab 30c — Navigating info Pages (Verify)](../lab-30c-info-pages-verify/) — prove nodes exist and resolve
- [Lab 28a — Exploring Manual Pages (RHCSA)](../lab-28a-man-pages-rhcsa/) — the `man` system info complements

---

## 👤 Author

**Kelvin R. Tobias**  
[kelvinintech.com](https://kelvinintech.com) · [GitHub](https://github.com/kelvintechnical) · [LinkedIn](https://www.linkedin.com/in/kelvin-r-tobias-211949219)
