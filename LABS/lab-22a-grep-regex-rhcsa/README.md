# Lab 22a: Filtering Text with grep and Regex (RHCSA) — `grep -E`, anchors, classes

**Series:** linux-ops-mastery — Text Processing & Filters · **Lab 22a of the Novice → RHCA path**  
**Certifications covered:** RHCSA EX200 (regular-expression filtering), RHCE EX294 (regex in `lineinfile`/`replace`), SRE/DevOps (log mining)  
**Prerequisite:** [Lab 21c](../lab-21c-tail-f-live-logs-verify/) completed  
**Time Estimate:** 25–35 minutes  
**Difficulty:** Beginner → Intermediate

---

## 🎯 Today's Focus Coverage

> Stay on-subject via the ANCHOR rows; expand vocabulary via the NEW rows. Every row is exercised by a STEP below.

**⚓ Anchor — already learned (on-topic reuse)**

| # | Command / switch | Covered by |
|---|---|---|
| A1 | `grep` basic match | _Task 1 · Step 1_ |
| A2 | `grep -o` / `-w` | _Task 2 · Step 2_ |

**🆕 NEW this lab — introduced for the first time** (minimum 3)

| # | Command / switch | First taught in | Covered by |
|---|---|---|---|
| N1 | `grep -E` (extended regex) | Task 1 · Step 1 | _Task 1 · Step 1_ |
| N2 | anchors `^` `$` | Task 1 · Step 2 | _Task 1 · Step 2_ |
| N3 | character classes `[[:digit:]]` | Task 2 · Step 1 | _Task 2 · Step 1_ |
| N4 | alternation `a|b` + quantifiers `+ ?` | Task 2 · Step 2 | _Task 2 · Step 2_ |

---

## 🎯 Objective

Move from "find this word" to "find this *pattern*." You will use extended regex (`grep -E`), anchor matches to line start/end (`^`/`$`), match character classes (`[[:digit:]]`, `[A-Z]`), and combine alternation and quantifiers (`(warn|error)`, `+`, `?`). By the end you can extract IPs, codes, and structured fields out of messy logs with a single expression.

---

## 🧠 Concept

A **regular expression** describes a *set* of strings, not one literal. Basic grep (BRE) treats `+ ? ( ) |` literally and needs backslashes; `grep -E` (ERE) makes them operators, which is far more readable. **Anchors** pin position: `^` = line start, `$` = line end. **Character classes** match one-of: `[0-9]`, the POSIX `[[:digit:]]`, `[A-Za-z]`. **Quantifiers** repeat: `*` (0+), `+` (1+), `?` (0/1), `{n,m}` (range). **Alternation** `a|b` matches either. Combine them: `^(WARN|ERROR):` matches lines starting with either label.

```
grep -E 'ERROR|WARN' f      → lines with either word
grep -E '^[0-9]+ ' f        → lines starting with a number
grep -Eo '[0-9]{1,3}(\.[0-9]{1,3}){3}' f → extract IPv4 addresses
grep -E 'colou?r' f         → match "color" or "colour"
```

> **Why this matters:** Logs are semi-structured. Regex turns "I think the IP is in there somewhere" into a precise extraction, and `-E` keeps the expression legible instead of backslash soup.

---

## 📚 Command Reference

| Command | Purpose | Critical flags |
|---|---|---|
| `grep -E` | Extended regex | `+ ? ( ) |` are operators |
| `^` / `$` | Anchor start / end | match position |
| `[[:digit:]]` / `[A-Z]` | Character classes | one char from the set |
| `*` `+` `?` `{n,m}` | Quantifiers | repetition counts |
| `a|b` | Alternation | either side |
| `grep -Eo` | Print only the match | extraction |

---

## 🧰 LAB-WIDE SETUP

**In plain English:** Build a sandbox with a structured log to mine.

> Run this block **once** before Task 1. It defines a single sandbox root
> (`LAB_ROOT`) that every file in this lab lives under, so the Teardown
> section can wipe it in one safe command.

```bash
export LAB_ROOT=/tmp/lab-22
mkdir -p "$LAB_ROOT"
cd "$LAB_ROOT"
cat > app.log <<'EOF'
INFO  2024-01-01 user alice from 10.0.0.5 ok
WARN  2024-01-01 slow query 1200ms
ERROR 2024-01-02 user bob from 192.168.1.20 failed
INFO  2024-01-02 colour profile loaded
DEBUG 2024-01-03 retry count 3
EOF
wc -l app.log
echo "exit was: $?"
```

**Expected output:**

```
5 app.log
exit was: 0
```

---

## TASK 1 of 2 — Alternation and anchors

**In plain English:** We match either of two labels, then pin matches to line position.

---

### Step 1 of 2 — Match alternatives with `grep -E`

**In plain English:** We find lines that are either WARN or ERROR using extended regex.

```bash
cd "$LAB_ROOT"
grep -E 'WARN|ERROR' app.log
echo "exit was: $?"
```

**Expected output:**

```
WARN  2024-01-01 slow query 1200ms
ERROR 2024-01-02 user bob from 192.168.1.20 failed
exit was: 0
```

**Line-by-line breakdown:**

- `grep -E 'WARN|ERROR'` → ERE alternation: match a line containing *either* word. In BRE you'd need `\|`.

**New words in this step:**

- **`grep -E`** — extended regex mode where `| + ? ( )` are operators.
- **alternation** — `a|b` matches either pattern.

---

### Step 2 of 2 — Anchor with `^` and `$`

**In plain English:** We match lines that start with ERROR and lines that end in a millisecond figure.

```bash
cd "$LAB_ROOT"
grep -E '^ERROR' app.log
grep -E 'ms$' app.log
echo "exit was: $?"
```

**Expected output:**

```
ERROR 2024-01-02 user bob from 192.168.1.20 failed
WARN  2024-01-01 slow query 1200ms
exit was: 0
```

**Line-by-line breakdown:**

- `grep -E '^ERROR'` → `^` anchors to line start: only lines *beginning* with ERROR.
- `grep -E 'ms$'` → `$` anchors to line end: only lines *ending* in `ms`.

**New words in this step:**

- **anchors** — `^` (start) and `$` (end) pin a match to a line position.

---

### Concept card (Task 1)

| Concept | What it does | Exam trap |
|---|---|---|
| `-E` ERE | operators active | BRE needs `\|`, `\+` |
| `^` / `$` | position anchors | `$` before newline |
| alternation | either branch | group with `()` for scope |

---

### Troubleshoot (Task 1)

| Symptom | Likely cause | Fix |
|---|---|---|
| `|` matched literally | BRE mode | Use `-E` (or `\|`) |
| `^ERROR` misses lines | Leading spaces | Anchor `^[[:space:]]*ERROR` |

---

## TASK 2 of 2 — Classes, quantifiers, extraction

**In plain English:** We match digit classes, then extract IPs and optional spellings.

---

### Step 1 of 2 — Match character classes

**In plain English:** We find lines containing a digit using a POSIX class.

```bash
cd "$LAB_ROOT"
grep -E '[[:digit:]]' app.log | head -2
grep -E 'count [[:digit:]]+' app.log
echo "exit was: $?"
```

**Expected output:**

```
INFO  2024-01-01 user alice from 10.0.0.5 ok
WARN  2024-01-01 slow query 1200ms
DEBUG 2024-01-03 retry count 3
exit was: 0
```

**Line-by-line breakdown:**

- `grep -E '[[:digit:]]'` → Match any line with at least one digit.
- `grep -E 'count [[:digit:]]+'` → `[[:digit:]]+` matches one or more digits after "count ".

**New words in this step:**

- **character class** — `[[:digit:]]`, `[A-Z]`, `[0-9]`: match one character from a set.

---

### Step 2 of 2 — Quantifiers and extraction with `-Eo`

**In plain English:** We extract IPv4 addresses and match an optional letter.

```bash
cd "$LAB_ROOT"
grep -Eo '[0-9]{1,3}(\.[0-9]{1,3}){3}' app.log
grep -E 'colou?r' app.log
echo "exit was: $?"
```

**Expected output:**

```
10.0.0.5
192.168.1.20
INFO  2024-01-02 colour profile loaded
exit was: 0
```

**Line-by-line breakdown:**

- `grep -Eo '[0-9]{1,3}(\.[0-9]{1,3}){3}'` → `{1,3}` is 1–3 digits; the group repeated `{3}` matches the three dotted octets; `-o` prints only the matched IP.
- `grep -E 'colou?r'` → `u?` makes the `u` optional, matching both "color" and "colour".

**New words in this step:**

- **quantifiers** — `+` (1+), `?` (0/1), `{n,m}` (range) repetition.
- **`-Eo`** — print only the matched substring (extraction).

---

### Concept card (Task 2)

| Concept | What it does | Exam trap |
|---|---|---|
| `[[:digit:]]+` | 1+ digits | bare `+` needs `-E` |
| `{n,m}` | range repeat | inclusive bounds |
| `-o` | print match only | one match per line region |

---

### Troubleshoot (Task 2)

| Symptom | Likely cause | Fix |
|---|---|---|
| `+`/`?` literal | BRE mode | Use `-E` |
| IP regex misses | Dots not escaped | `\.` for literal dot |

---

## ✅ Lab Checklist

- [ ] Task 1 · Step 1 — Match alternatives with `grep -E`
- [ ] Task 1 · Step 2 — Anchor with `^` and `$`
- [ ] Task 2 · Step 1 — Match character classes
- [ ] Task 2 · Step 2 — Quantifiers and extraction with `-Eo`
- [ ] Every 🎯 Focus Coverage row (Anchor + NEW) mapped to a step
- [ ] 🧹 Teardown run — sandbox + any system state removed

---

## 🧹 Teardown

**In plain English:** Delete everything this lab created so the box is clean for the next run.

> Run this after you've verified the lab. `lab_teardown.sh` safely removes the single sandbox root — it refuses to touch `/`, `$HOME`, or any protected path. This lab changed **no** system state.

```bash
cd /tmp
bash lab_teardown.sh "$LAB_ROOT"     # = /tmp/lab-22
```

**Expected output:**

```
✅ Removed /tmp/lab-22 — lab workspace is clean.
```

---

## ⚠️ Common Pitfalls

| Mistake | Symptom | Fix |
|---|---|---|
| Forgetting `-E` | `+ ? ( ) |` literal | Add `-E` |
| Unescaped `.` | Matches any char | `\.` for literal dot |
| Greedy assumptions | Over-matching | grep is line-based, not greedy across lines |

---

## 📌 Exam Strategy

Use `grep -E` for readable regex, anchor with `^`/`$` to be precise, lean on POSIX classes for portability, and `-o` to extract just the field you need. Practice the IPv4 pattern — it shows up constantly.

- `-E` keeps regex free of backslash clutter.
- `[[:digit:]]` is portable across locales.
- `-o` turns grep into a field extractor.

---

## 🔗 Related Labs

- [Lab 22b — Filtering with grep and Regex (Ansible)](../lab-22b-grep-regex-ansible/) — regex in `replace`/`lineinfile`
- [Lab 22c — Filtering with grep and Regex (Verify)](../lab-22c-grep-regex-verify/) — prove matches and extractions
- [Lab 16a — Search and Save Output (RHCSA)](../lab-16a-grep-search-save-output-rhcsa/) — grep basics and saving results

---

## 👤 Author

**Kelvin R. Tobias**  
[kelvinintech.com](https://kelvinintech.com) · [GitHub](https://github.com/kelvintechnical) · [LinkedIn](https://www.linkedin.com/in/kelvin-r-tobias-211949219)
