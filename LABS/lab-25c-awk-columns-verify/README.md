# Lab 25c: Extracting Columns with awk (Verify) — cross-checking fields and totals

**Series:** linux-ops-mastery — Text Processing & Filters · **Lab 25c of the Novice → RHCA path**  
**Certifications covered:** RHCSA EX200 (proving field extractions and aggregates), SRE (data-pipeline validation), DevOps (report verification)  
**Prerequisite:** [Lab 25a](../lab-25a-awk-columns-rhcsa/) and [Lab 25b](../lab-25b-awk-columns-ansible/) completed  
**Time Estimate:** 15–25 minutes  
**Difficulty:** Beginner → Intermediate

---

## 🎯 Today's Focus Coverage

> Stay on-subject via the ANCHOR rows; expand vocabulary via the NEW rows. Every row is exercised by a STEP below.

**⚓ Anchor — already learned (on-topic reuse)**

| # | Command / switch | Covered by |
|---|---|---|
| A1 | `awk` totals | _Task 2 · Step 1_ |
| A2 | `cut` field extraction | _Task 1 · Step 1_ |

**🆕 NEW this lab — introduced for the first time** (minimum 3)

| # | Command / switch | First taught in | Covered by |
|---|---|---|---|
| N1 | `awk` vs `cut` cross-check | Task 1 · Step 1 | _Task 1 · Step 1_ |
| N2 | `awk NF` field-count proof | Task 1 · Step 2 | _Task 1 · Step 2_ |
| N3 | `awk` sum vs `paste`/`bc` | Task 2 · Step 1 | _Task 2 · Step 1_ |
| N4 | per-group totals proof | Task 2 · Step 2 | _Task 2 · Step 2_ |

---

## 🎯 Objective

Prove an `awk` extraction or aggregate is correct by computing it a *second*, independent way. You will cross-check a column extraction (`awk` vs `cut`), confirm every row has the expected field count, verify a total with an independent sum, and prove per-group subtotals add up to the grand total. Two methods agreeing is the cheapest reliable proof that your parse is right.

---

## 🧠 Concept

Parsing bugs hide in plain sight — a wrong field index or separator yields output that *looks* plausible. The fix is independent confirmation. For a column, `awk '{print $1}'` and `cut -d' ' -f1` should produce the same list. For structure, `awk '{print NF}' | sort -u` should show a single field count if the data is well-formed. For a total, `awk '{s+=$3}END{print s}'` should match a sum computed by another path (`cut | paste -sd+ | bc`). And per-group subtotals (`awk` grouping) must add up to the grand total — an internal consistency check.

```
awk '{print $1}' f == cut -d' ' -f1 f   → extraction agrees
awk '{print NF}' f | sort -u → 3        → every row has 3 fields
awk '{s+=$3}END{print s}' f == cut -d' ' -f3 | paste -sd+ | bc → total agrees
sum(group subtotals) == grand total     → internal consistency
```

> **Why this matters:** A report built on a mis-parsed column is worse than no report. Cross-checking with a second tool catches off-by-one fields and separator mistakes before they reach a decision.

---

## 📚 Command Reference

| Command | Purpose | Critical flags |
|---|---|---|
| `awk '{print $N}'` | Extract column | cross-check with `cut` |
| `cut -d -f` | Independent extract | delimiter + field |
| `awk '{print NF}'` | Field count | `sort -u` for uniformity |
| `paste -sd+ | bc` | Independent sum | arithmetic |
| `awk` grouping | Per-group totals | array by key |

---

## 🧰 LAB-WIDE SETUP

**In plain English:** Recreate the columnar data to audit.

> Run this block **once** before Task 1. It builds the clean, private workspace that both tasks depend on.

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
cat sales.txt
echo "exit was: $?"
```

**Expected output:**

```
alice east 120
bob west 90
carol east 200
dave west 60
exit was: 0
```

---

## TASK 1 of 2 — Prove the extraction

**In plain English:** We cross-check a column with two tools and confirm field counts.

---

### Step 1 of 2 — `awk` vs `cut`

**In plain English:** We extract the first column two ways and confirm they match.

```bash
cd "$LAB_ROOT"
awk '{print $1}' sales.txt > a.txt
cut -d' ' -f1 sales.txt > c.txt
diff a.txt c.txt && echo "EXTRACTION OK" || echo "MISMATCH (FAIL)"
```

**Expected output:**

```
EXTRACTION OK
```

**Line-by-line breakdown:**

- `awk '{print $1}'` / `cut -d' ' -f1` → Two independent extractions of column 1.
- `diff a.txt c.txt` → Empty output proves the two tools agree.

**New words in this step:**

- **cross-check** — confirming a result with a second, independent tool.

---

### Step 2 of 2 — Prove field counts with `NF`

**In plain English:** We confirm every row has exactly three fields.

```bash
cd "$LAB_ROOT"
awk '{print NF}' sales.txt | sort -u
U=$(awk '{print NF}' sales.txt | sort -u | wc -l)
[ "$U" -eq 1 ] && echo "UNIFORM FIELDS (OK)" || echo "RAGGED ROWS (FAIL)"
```

**Expected output:**

```
3
UNIFORM FIELDS (OK)
```

**Line-by-line breakdown:**

- `awk '{print NF}' | sort -u` → Print each row's field count, deduplicate; a single value `3` means uniform.
- `[ "$U" -eq 1 ]` → Exactly one distinct field count proves no ragged rows.

**New words in this step:**

- **`NF` uniformity** — every row having the same number of fields.

---

### Concept card (Task 1)

| Concept | What it does | Exam trap |
|---|---|---|
| `awk` vs `cut` | extraction proof | same delimiter |
| `NF` | field count | catches ragged rows |
| `sort -u` | distinct values | one = uniform |

---

### Troubleshoot (Task 1)

| Symptom | Likely cause | Fix |
|---|---|---|
| Extraction mismatch | Different separators | Align `cut -d` with awk FS |
| Multiple field counts | Ragged data | Inspect offending rows |

---

## TASK 2 of 2 — Prove the totals

**In plain English:** We verify the grand total and that group subtotals add up.

---

### Step 1 of 2 — Grand total two ways

**In plain English:** We total column 3 with `awk` and with `paste`/`bc` and confirm they match.

```bash
cd "$LAB_ROOT"
T1=$(awk '{s+=$3} END{print s}' sales.txt)
T2=$(cut -d' ' -f3 sales.txt | paste -sd+ | bc)
echo "awk: $T1  bc: $T2"
[ "$T1" -eq "$T2" ] && echo "TOTAL OK" || echo "TOTAL MISMATCH (FAIL)"
```

**Expected output:**

```
awk: 470  bc: 470
TOTAL OK
```

**Line-by-line breakdown:**

- `awk '{s+=$3} END{print s}'` → Total column 3 with awk.
- `cut -d' ' -f3 | paste -sd+ | bc` → Independent total: extract the column, join with `+`, evaluate with `bc`.
- `[ "$T1" -eq "$T2" ]` → Agreement proves the total.

**New words in this step:**

- **independent sum** — totaling a column via a different toolchain to confirm awk.

---

### Step 2 of 2 — Group subtotals add to the total

**In plain English:** We compute per-region subtotals and confirm they sum to the grand total.

```bash
cd "$LAB_ROOT"
awk '{g[$2]+=$3} END{for (k in g) print k, g[k]}' sales.txt | sort
SUB=$(awk '{g[$2]+=$3} END{for (k in g) s+=g[k]; print s}' sales.txt)
GRAND=$(awk '{s+=$3} END{print s}' sales.txt)
[ "$SUB" -eq "$GRAND" ] && echo "SUBTOTALS CONSISTENT (OK)" || echo "INCONSISTENT (FAIL)"
```

**Expected output:**

```
east 320
west 150
SUBTOTALS CONSISTENT (OK)
```

**Line-by-line breakdown:**

- `awk '{g[$2]+=$3} END{for (k in g) print k, g[k]}'` → Accumulate column 3 into an array keyed by region, print each subtotal.
- `SUB=...` and `GRAND=...` → Sum the subtotals and compute the grand total independently.
- `[ "$SUB" -eq "$GRAND" ]` → Subtotals summing to the grand total proves internal consistency.

**New words in this step:**

- **per-group total** — `awk` array aggregation keyed by a field.

---

### Concept card (Task 2)

| Concept | What it does | Exam trap |
|---|---|---|
| `paste -sd+ | bc` | independent sum | join then evaluate |
| `g[key]+=val` | grouped total | awk associative array |
| consistency | parts == whole | catches drops |

---

### Troubleshoot (Task 2)

| Symptom | Likely cause | Fix |
|---|---|---|
| Totals differ | Wrong field/separator | Align `cut`/`awk` field |
| Subtotals ≠ grand | Rows dropped | Check the group key |

---

## ✅ Lab Checklist

- [ ] Task 1 · Step 1 — `awk` vs `cut`
- [ ] Task 1 · Step 2 — Prove field counts with `NF`
- [ ] Task 2 · Step 1 — Grand total two ways
- [ ] Task 2 · Step 2 — Group subtotals add to the total
- [ ] Every 🎯 Focus Coverage row (Anchor + NEW) mapped to a step
- [ ] 🧹 Teardown run — sandbox + any system state removed

---

## 🧹 Teardown

**In plain English:** Delete everything this lab created so the box is clean for the next run.

> Run this after you've verified the lab. `lab_teardown.sh` safely removes the single sandbox root — it refuses to touch `/`, `$HOME`, or any protected path. This verify lab changed **no** system state.

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
| Trusting one parse | Hidden field bug | Cross-check with `cut`/`bc` |
| Ignoring ragged rows | Wrong totals | Check `NF` uniformity |
| Subtotals not reconciled | Silent drops | Sum groups vs grand total |

---

## 📌 Exam Strategy

Validate every parse with a second method: `awk` vs `cut` for columns, `awk` vs `paste|bc` for totals, `NF` for structure, and subtotal-vs-grand-total for consistency. Independent agreement is the proof that your extraction logic is correct.

- Cross-check columns with `cut`.
- Confirm totals with `paste -sd+ | bc`.
- `NF | sort -u` catches ragged data instantly.

---

## 🔗 Related Labs

- [Lab 25a — Extracting Columns with awk (RHCSA)](../lab-25a-awk-columns-rhcsa/) — the `awk` this audits
- [Lab 25b — Extracting Columns with awk (Ansible)](../lab-25b-awk-columns-ansible/) — the parsing plays you verify
- [Lab 23c — Comparing File Differences (Verify)](../lab-23c-diff-comparing-files-verify/) — diff-based cross-checks

---

## 👤 Author

**Kelvin R. Tobias**  
[kelvinintech.com](https://kelvinintech.com) · [GitHub](https://github.com/kelvintechnical) · [LinkedIn](https://www.linkedin.com/in/kelvin-r-tobias-211949219)
