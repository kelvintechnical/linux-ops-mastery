# Lab 28c: Exploring Manual Pages (Verify) — `man -w`, `man -f`, sections

**Series:** linux-ops-mastery — Documentation · **Lab 28c of the Novice → RHCA path**  
**Certifications covered:** RHCSA EX200 (proving documentation resolves), SRE (tooling-presence checks), DevOps (node doc validation)  
**Prerequisite:** [Lab 28a](../lab-28a-man-pages-rhcsa/) and [Lab 28b](../lab-28b-man-pages-ansible/) completed  
**Time Estimate:** 15–25 minutes  
**Difficulty:** Beginner

---

## 🎯 Today's Focus Coverage

> Stay on-subject via the ANCHOR rows; expand vocabulary via the NEW rows. Every row is exercised by a STEP below.

**⚓ Anchor — already learned (on-topic reuse)**

| # | Command / switch | Covered by |
|---|---|---|
| A1 | `man -w` | _Task 1 · Step 1_ |
| A2 | `man -f` | _Task 1 · Step 2_ |

**🆕 NEW this lab — introduced for the first time** (minimum 3)

| # | Command / switch | First taught in | Covered by |
|---|---|---|---|
| N1 | `man -w` rc as existence test | Task 1 · Step 1 | _Task 1 · Step 1_ |
| N2 | section-number assertion | Task 1 · Step 2 | _Task 1 · Step 2_ |
| N3 | multi-section detection | Task 2 · Step 1 | _Task 2 · Step 1_ |
| N4 | `man -P cat | grep` content proof | Task 2 · Step 2 | _Task 2 · Step 2_ |

---

## 🎯 Objective

Prove documentation is actually available and correct. You will use `man -w`'s exit code as an existence test, assert a page lives in the expected section, detect when a name has *multiple* section pages (like `passwd`), and confirm a page's body contains an expected option by piping `man -P cat` to `grep`. These checks certify that the help you'll rely on is really there.

---

## 🧠 Concept

Documentation verification is existence plus correctness. `man -w name` exits 0 and prints a path when the page exists, non-zero when it doesn't — a clean boolean. The path encodes the section (`man1/`, `man5/`), so you can assert the right *kind* of page. Some names resolve in multiple sections; `man -f name` lists them all, and counting the lines tells you a config name like `passwd` has both a command (1) and a format (5) page. Finally, body content matters: `man -P cat name | grep -q OPTION` proves a specific flag is documented — useful when validating tool versions.

```
man -w ls; echo $?           → 0 + path = exists
man -w ls | grep -q man1     → it's a section-1 page
man -f passwd | wc -l → 2    → command + file-format pages
man -P cat ls | grep -q -- -l → the -l option is documented
```

> **Why this matters:** Before you depend on `man 5 <file>` during an exam or `man <tool>` in a runbook, confirming the page exists, is in the right section, and documents the option you need prevents nasty surprises.

---

## 📚 Command Reference

| Command | Purpose | Critical flags |
|---|---|---|
| `man -w` | Existence + path | rc 0 = present |
| `man -f` | List sections | count = how many |
| `wc -l` | Count section pages | multi-section detect |
| `man -P cat` | Non-interactive body | pipe to `grep` |
| `grep -q` | Content presence | exit-code only |

---

## 🧰 LAB-WIDE SETUP

**In plain English:** Make a sandbox for any saved checks; pages come from the system.

> Run this block **once** before Task 1. `LAB_ROOT` just holds notes.

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

## TASK 1 of 2 — Prove existence and section

**In plain English:** We confirm a page exists and lives in the expected section.

---

### Step 1 of 2 — Existence via `man -w` rc

**In plain English:** We test that the `ls` page resolves using the exit code.

```bash
man -w ls >/dev/null 2>&1 && echo "LS PAGE OK" || echo "LS PAGE MISSING (FAIL)"
man -w definitely-not-a-command >/dev/null 2>&1 && echo "unexpected" || echo "MISSING DETECTED (OK)"
```

**Expected output:**

```
LS PAGE OK
MISSING DETECTED (OK)
```

**Line-by-line breakdown:**

- `man -w ls >/dev/null 2>&1 && ...` → Exit 0 means the page exists; output discarded.
- `man -w definitely-not-a-command ...` → Non-zero exit proves the absence check works.

**New words in this step:**

- **existence test** — using `man -w`'s exit code as a boolean.

---

### Step 2 of 2 — Assert the section

**In plain English:** We confirm the `ls` page is in section 1.

```bash
P=$(man -w ls)
echo "$P"
echo "$P" | grep -q '/man1/' && echo "SECTION 1 (OK)" || echo "WRONG SECTION (FAIL)"
```

**Expected output:**

```
/usr/share/man/man1/ls.1.gz
SECTION 1 (OK)
```

**Line-by-line breakdown:**

- `P=$(man -w ls)` → Capture the page path.
- `echo "$P" | grep -q '/man1/'` → The `man1` directory in the path confirms section 1.

**New words in this step:**

- **section assertion** — verifying the page's section from its path.

---

### Concept card (Task 1)

| Concept | What it does | Exam trap |
|---|---|---|
| `man -w` rc | existence | 0 found |
| `manN/` in path | section | encodes the number |
| absence check | rc non-zero | confirms "not found" |

---

### Troubleshoot (Task 1)

| Symptom | Likely cause | Fix |
|---|---|---|
| Page missing | Package absent | Install it |
| Wrong section | Default lowest | Query with `man -w N` |

---

## TASK 2 of 2 — Multi-section and content

**In plain English:** We detect a name with multiple pages and prove an option is documented.

---

### Step 1 of 2 — Detect multiple sections

**In plain English:** We confirm `passwd` resolves in more than one section.

```bash
man -f passwd
N=$(man -f passwd | wc -l)
echo "passwd pages: $N"
[ "$N" -ge 2 ] && echo "MULTI-SECTION (OK)" || echo "ONLY ONE (info)"
```

**Expected output:**

```
passwd (1)           - change user password
passwd (5)           - the password file
passwd pages: 2
MULTI-SECTION (OK)
```

**Line-by-line breakdown:**

- `man -f passwd` → Lists every section `passwd` appears in.
- `man -f passwd | wc -l` → Counting the lines (≥2) proves it's documented as both a command and a file format.

**New words in this step:**

- **multi-section name** — a name with man pages in more than one section.

---

### Step 2 of 2 — Prove an option is documented

**In plain English:** We confirm the `ls` page documents the `-l` option.

```bash
man -P cat ls | grep -q -- '-l' && echo "OPTION -l DOCUMENTED (OK)" || echo "NOT FOUND (FAIL)"
echo "exit was: $?"
```

**Expected output:**

```
OPTION -l DOCUMENTED (OK)
exit was: 0
```

**Line-by-line breakdown:**

- `man -P cat ls` → Render the full page non-interactively (pager = `cat`).
- `grep -q -- '-l'` → `--` stops option parsing so `-l` is treated as a search string; rc 0 means it's documented.

**New words in this step:**

- **content proof** — confirming a specific option/flag appears in a page's body.

---

### Concept card (Task 2)

| Concept | What it does | Exam trap |
|---|---|---|
| `man -f | wc -l` | section count | ≥2 = multi |
| `man -P cat` | full body | pipe-friendly |
| `grep -q --` | literal flag search | `--` ends options |

---

### Troubleshoot (Task 2)

| Symptom | Likely cause | Fix |
|---|---|---|
| `grep` eats `-l` | No `--` | Add `--` before pattern |
| One section only | Name truly single | That's fine |

---

## ✅ Lab Checklist

- [ ] Task 1 · Step 1 — Existence via `man -w` rc
- [ ] Task 1 · Step 2 — Assert the section
- [ ] Task 2 · Step 1 — Detect multiple sections
- [ ] Task 2 · Step 2 — Prove an option is documented
- [ ] Every 🎯 Focus Coverage row (Anchor + NEW) mapped to a step
- [ ] 🧹 Teardown run — sandbox + any system state removed

---

## 🧹 Teardown

**In plain English:** Delete everything this lab created so the box is clean for the next run.

> Run this after you've verified the lab. `lab_teardown.sh` safely removes the single sandbox root — it refuses to touch `/`, `$HOME`, or any protected path. This verify lab changed **no** system state.

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
| Assuming a page exists | Runbook breaks | Test with `man -w` |
| Reading wrong section | Misleading info | Check the `manN/` path |
| `grep` treats flag as option | Error | Use `grep -q --` |

---

## 📌 Exam Strategy

Certify docs with `man -w` (existence + section), `man -f | wc -l` (multi-section names), and `man -P cat | grep` (option present). Knowing a config name has a section-5 page is often the key to an exam config task.

- `man -w` rc is your existence boolean.
- The `manN/` path tells you the section.
- `man -P cat` makes pages grep-able.

---

## 🔗 Related Labs

- [Lab 28a — Exploring Manual Pages (RHCSA)](../lab-28a-man-pages-rhcsa/) — the `man` this audits
- [Lab 28b — Exploring Manual Pages (Ansible)](../lab-28b-man-pages-ansible/) — the doc-capture plays you verify
- [Lab 29c — Searching Manuals by Keyword (Verify)](../lab-29c-apropos-whatis-verify/) — verifying keyword search

---

## 👤 Author

**Kelvin R. Tobias**  
[kelvinintech.com](https://kelvinintech.com) · [GitHub](https://github.com/kelvintechnical) · [LinkedIn](https://www.linkedin.com/in/kelvin-r-tobias-211949219)
