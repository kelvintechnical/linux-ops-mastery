# Lab 25a: Extracting Columns with awk (RHCSA) — `awk '{print $N}'`, `-F`, patterns

**Series:** linux-ops-mastery — Text Processing & Filters · **Lab 25a of the Novice → RHCA path**  
**Certifications covered:** RHCSA EX200 (field extraction from text), RHCE EX294 (parsing command output in plays), SRE/DevOps (log/CSV mining)  
**Prerequisite:** [Lab 24c](../lab-24c-sed-stream-editor-verify/) completed  
**Time Estimate:** 25–35 minutes  
**Difficulty:** Beginner → Intermediate

---

## 🎯 Today's Focus Coverage

> Stay on-subject via the ANCHOR rows; expand vocabulary via the NEW rows. Every row is exercised by a STEP below.

**⚓ Anchor — already learned (on-topic reuse)**

| # | Command / switch | Covered by |
|---|---|---|
| A1 | regex patterns | _Task 2 · Step 1_ |
| A2 | piping output | _Task 1 · Step 1_ |

**🆕 NEW this lab — introduced for the first time** (minimum 3)

| # | Command / switch | First taught in | Covered by |
|---|---|---|---|
| N1 | `awk '{print $N}'` fields | Task 1 · Step 1 | _Task 1 · Step 1_ |
| N2 | `awk -F` field separator | Task 1 · Step 2 | _Task 1 · Step 2_ |
| N3 | `awk '/re/{...}'` pattern-action | Task 2 · Step 1 | _Task 2 · Step 1_ |
| N4 | `awk` `NR`/`NF`/`END` + sum | Task 2 · Step 2 | _Task 2 · Step 2_ |

---

## 🎯 Objective

Pull fields out of structured text. You will print specific columns with `$1`, `$3`, `$NF`, change the delimiter with `-F` (for `/etc/passwd`, CSVs), select rows with patterns, and use built-in variables (`NR`, `NF`) plus `END` to count and sum. By the end you can turn whitespace- or comma-separated data into exactly the columns and aggregates you need.

---

## 🧠 Concept

`awk` splits each line into **fields** (`$1`, `$2`, …; `$0` is the whole line; `$NF` is the last field) and runs a **pattern { action }** for every line. With no pattern, the action runs on all lines; with a pattern like `/error/` or `$3 > 100`, only matching lines. The **field separator** defaults to runs of whitespace; `-F:` switches it to colon for `/etc/passwd`, `-F,` for CSV. Built-in variables: `NR` (current line number), `NF` (number of fields), and the special `END { }` block runs once after all input — perfect for totals. `awk` is a tiny language: it does selection, projection, and aggregation in one pass.

```
awk '{print $1}' f         → first column
awk '{print $NF}' f        → last column
awk -F: '{print $1}' /etc/passwd → usernames
awk '$3 > 100 {print $1}' f → rows where field 3 > 100
awk 'END{print NR}' f      → line count
awk '{sum+=$2} END{print sum}' f → total of column 2
```

> **Why this matters:** Command output is columns. `awk` extracts the one field you need (a PID, a username, a size) and aggregates it — the glue of shell scripting and the parser behind countless playbook `command:` results.

---

## 📚 Command Reference

| Command | Purpose | Critical flags |
|---|---|---|
| `awk '{print $N}'` | Print field N | `$0` whole, `$NF` last |
| `awk -F C` | Set field separator | `:`, `,`, etc. |
| `awk '/re/{...}'` | Pattern-action | selection |
| `awk '$N op V'` | Field comparison | numeric/string |
| `NR` / `NF` | Line / field counts | built-ins |
| `END { }` | After all input | totals/summaries |

---

## 🧰 LAB-WIDE SETUP

**In plain English:** Build a sandbox with whitespace and colon/CSV data to parse.

> Run this block **once** before Task 1. It defines a single sandbox root
> (`LAB_ROOT`) that every file in this lab lives under, so the Teardown
> section can wipe it in one safe command.

```bash
export LAB_ROOT=/tmp/lab-25
mkdir -p "$LAB_ROOT"
cd "$LAB_ROOT"
cat > sales.txt <<'EOF'
alice east 120
bob west 90
carol east 200
dave west 60
EOF
cat > users.csv <<'EOF'
name,role,uid
alice,admin,1001
bob,dev,1002
EOF
ls
echo "exit was: $?"
```

**Expected output:**

```
sales.txt
users.csv
exit was: 0
```

---

## TASK 1 of 2 — Print fields and set separators

**In plain English:** We extract columns from whitespace data, then from a CSV.

---

### Step 1 of 2 — Print specific fields

**In plain English:** We print the name and amount columns, and the last field.

```bash
cd "$LAB_ROOT"
awk '{print $1, $3}' sales.txt
echo "---"
awk '{print $NF}' sales.txt
echo "exit was: $?"
```

**Expected output:**

```
alice 120
bob 90
carol 200
dave 60
---
120
90
200
60
exit was: 0
```

**Line-by-line breakdown:**

- `awk '{print $1, $3}'` → Print fields 1 and 3; the comma inserts the output field separator (a space).
- `awk '{print $NF}'` → `$NF` is the last field regardless of how many there are.

**New words in this step:**

- **field** — `$1`, `$2`, …; `$0` is the whole line, `$NF` the last field.

---

### Step 2 of 2 — Change the separator with `-F`

**In plain English:** We parse a CSV by setting the field separator to a comma, skipping the header.

```bash
cd "$LAB_ROOT"
awk -F, 'NR>1 {print $1, $3}' users.csv
echo "---"
awk -F: '{print $1}' /etc/passwd | head -3
echo "exit was: $?"
```

**Expected output:**

```
alice 1001
bob 1002
---
root
bin
daemon
exit was: 0
```

**Line-by-line breakdown:**

- `awk -F, 'NR>1 {print $1, $3}'` → `-F,` splits on commas; `NR>1` skips the header line.
- `awk -F: '{print $1}' /etc/passwd` → `-F:` parses colon-separated `/etc/passwd`; `$1` is the username.

**New words in this step:**

- **`-F`** — set the field separator (comma, colon, etc.).
- **`NR`** — current record (line) number.

---

### Concept card (Task 1)

| Concept | What it does | Exam trap |
|---|---|---|
| `$N` | field N | `$0` is whole line |
| `$NF` | last field | varies per line |
| `-F` | separator | default is whitespace |

---

### Troubleshoot (Task 1)

| Symptom | Likely cause | Fix |
|---|---|---|
| Wrong columns | Default separator | Set `-F` |
| Header included | No row filter | Add `NR>1` |

---

## TASK 2 of 2 — Select rows and aggregate

**In plain English:** We filter rows by pattern and field, then count and sum.

---

### Step 1 of 2 — Select rows by pattern and field

**In plain English:** We print east-region rows, then rows where the amount exceeds 100.

```bash
cd "$LAB_ROOT"
awk '/east/ {print $1, $3}' sales.txt
echo "---"
awk '$3 > 100 {print $1, $3}' sales.txt
echo "exit was: $?"
```

**Expected output:**

```
alice 120
carol 200
---
alice 120
carol 200
exit was: 0
```

**Line-by-line breakdown:**

- `awk '/east/ {print $1, $3}'` → Regex pattern selects lines containing "east".
- `awk '$3 > 100 {print ...}'` → Numeric field comparison selects rows where column 3 > 100.

**New words in this step:**

- **pattern-action** — `pattern { action }`; the action runs only on matching lines.

---

### Step 2 of 2 — Count and sum with `END`

**In plain English:** We count the rows and total the amount column.

```bash
cd "$LAB_ROOT"
awk 'END {print "rows:", NR}' sales.txt
awk '{sum += $3} END {print "total:", sum}' sales.txt
awk '{sum += $3} END {print "avg:", sum/NR}' sales.txt
echo "exit was: $?"
```

**Expected output:**

```
rows: 4
total: 470
avg: 117.5
exit was: 0
```

**Line-by-line breakdown:**

- `awk 'END {print "rows:", NR}'` → After all lines, `NR` holds the total count.
- `awk '{sum += $3} END {print "total:", sum}'` → Accumulate column 3 per line, print the total at the `END`.
- `... sum/NR` → Compute the average using the accumulated sum and line count.

**New words in this step:**

- **`END { }`** — block that runs once after all input, used for totals.
- **`NF`** — number of fields on the current line (built-in).

---

### Concept card (Task 2)

| Concept | What it does | Exam trap |
|---|---|---|
| `/re/{}` | regex select | matches `$0` |
| `$N op V` | field test | numeric vs string |
| `END` sum | aggregate | initialize implicitly 0 |

---

### Troubleshoot (Task 2)

| Symptom | Likely cause | Fix |
|---|---|---|
| Sum is 0 | Wrong field/separator | Check `-F` and `$N` |
| String compare surprise | Quoted numbers | awk auto-detects; force with `+0` |

---

## ✅ Lab Checklist

- [ ] Task 1 · Step 1 — Print specific fields
- [ ] Task 1 · Step 2 — Change the separator with `-F`
- [ ] Task 2 · Step 1 — Select rows by pattern and field
- [ ] Task 2 · Step 2 — Count and sum with `END`
- [ ] Every 🎯 Focus Coverage row (Anchor + NEW) mapped to a step
- [ ] 🧹 Teardown run — sandbox + any system state removed

---

## 🧹 Teardown

**In plain English:** Delete everything this lab created so the box is clean for the next run.

> Run this after you've verified the lab. `lab_teardown.sh` safely removes the single sandbox root — it refuses to touch `/`, `$HOME`, or any protected path. This lab changed **no** system state.

```bash
cd /tmp
bash lab_teardown.sh "$LAB_ROOT"     # = /tmp/lab-25
```

**Expected output:**

```
✅ Removed /tmp/lab-25 — lab workspace is clean.
```

---

## ⚠️ Common Pitfalls

| Mistake | Symptom | Fix |
|---|---|---|
| Wrong separator | Fields misaligned | Set `-F` |
| Forgetting `END` | No totals printed | Aggregate in `END` |
| Counting header | Off-by-one | Filter with `NR>1` |

---

## 📌 Exam Strategy

`awk` selects rows (patterns), projects columns (`$N`), and aggregates (`END`) in one pass. Master `-F` for `/etc/passwd` and CSVs, `$NF` for the last field, and `sum += $N; END{print sum}` for totals.

- `$NF` grabs the last field no matter the width.
- `-F:` / `-F,` for colon and comma data.
- `END { }` is where counts and sums belong.

---

## 🔗 Related Labs

- [Lab 25b — Extracting Columns with awk (Ansible)](../lab-25b-awk-columns-ansible/) — parsing command output in plays
- [Lab 25c — Extracting Columns with awk (Verify)](../lab-25c-awk-columns-verify/) — prove extractions and totals
- [Lab 22a — Filtering with grep and Regex (RHCSA)](../lab-22a-grep-regex-rhcsa/) — pattern matching that pairs with awk

---

## 👤 Author

**Kelvin R. Tobias**  
[kelvinintech.com](https://kelvinintech.com) · [GitHub](https://github.com/kelvintechnical) · [LinkedIn](https://www.linkedin.com/in/kelvin-r-tobias-211949219)
