# Lab 22c: Filtering with grep and Regex (Verify) — `grep -E`, `-c`, `-q`, `-o`

**Series:** linux-ops-mastery — Text Processing & Filters · **Lab 22c of the Novice → RHCA path**  
**Certifications covered:** RHCSA EX200 (proving regex matches), SRE (extraction validation), DevOps (config-rewrite verification)  
**Prerequisite:** [Lab 22a](../lab-22a-grep-regex-rhcsa/) and [Lab 22b](../lab-22b-grep-regex-ansible/) completed  
**Time Estimate:** 15–25 minutes  
**Difficulty:** Beginner → Intermediate

---

## 🎯 Today's Focus Coverage

> Stay on-subject via the ANCHOR rows; expand vocabulary via the NEW rows. Every row is exercised by a STEP below.

**⚓ Anchor — already learned (on-topic reuse)**

| # | Command / switch | Covered by |
|---|---|---|
| A1 | `grep -E` | _Task 1 · Step 1_ |
| A2 | `grep -o` extraction | _Task 1 · Step 2_ |

**🆕 NEW this lab — introduced for the first time** (minimum 3)

| # | Command / switch | First taught in | Covered by |
|---|---|---|---|
| N1 | `grep -Eq` boolean test | Task 1 · Step 1 | _Task 1 · Step 1_ |
| N2 | `grep -Eo | sort -u` extraction proof | Task 1 · Step 2 | _Task 1 · Step 2_ |
| N3 | `grep -Ec` count assertion | Task 2 · Step 1 | _Task 2 · Step 1_ |
| N4 | `grep -Ev` negative assertion | Task 2 · Step 2 | _Task 2 · Step 2_ |

---

## 🎯 Objective

Certify that a regex did exactly what was intended. You will test for presence with `grep -Eq` (quiet, exit-code only), prove an extraction returns the expected set with `grep -Eo | sort -u`, assert a match count with `grep -Ec`, and prove an unwanted pattern is *absent* with `grep -Ev`. Presence, set, count, and absence together fully describe a regex result.

---

## 🧠 Concept

Regex verification answers four questions. **Presence**: `grep -Eq PATTERN` is silent and just sets an exit code — perfect for `if`. **Set/extraction**: `grep -Eo PATTERN | sort -u` lists the distinct things matched, which you compare to the expected set. **Count**: `grep -Ec PATTERN` gives the number of matching lines for an exact assertion. **Absence**: proving something is *gone* needs `grep -Eq PATTERN` returning non-zero (or counting with `-c` and expecting 0). A config rewrite is verified when the new pattern is present once and the old pattern is absent.

```
grep -Eq '^Port 2222' f   → rc 0 means present
grep -Eo '[0-9.]+' f | sort -u → the distinct IPs matched
grep -Ec 'deadline' f → 2  → exactly two rewritten lines
grep -Eq 'timeout v' f || echo "old pattern gone"
```

> **Why this matters:** "It changed" isn't proof. You must show the new value is present, correct in count, and the old value is gone — exactly what verifies the Lab 22b rewrites.

---

## 📚 Command Reference

| Command | Purpose | Critical flags |
|---|---|---|
| `grep -Eq` | Presence test (silent) | exit code only |
| `grep -Eo | sort -u` | Distinct matches | extraction set |
| `grep -Ec` | Match-line count | for `-eq` assertions |
| `grep -Ev` | Non-matching lines | absence/inverse |
| `grep -En` | Match with line numbers | locate matches |

---

## 🧰 LAB-WIDE SETUP

**In plain English:** Recreate a rewritten config like the one Lab 22b produces.

> Run this block **once** before Task 1. It builds the clean, private workspace that both tasks depend on.

```bash
export LAB_ROOT=/tmp/lab-22
mkdir -p "$LAB_ROOT"
cd "$LAB_ROOT"
cat > sshd_demo.conf <<'EOF'
# demo config
Port 2222
LogLevel INFO
deadline v1 30
deadline v2 60
client 10.0.0.5
client 192.168.1.20
EOF
cat sshd_demo.conf
echo "exit was: $?"
```

**Expected output:**

```
# demo config
Port 2222
LogLevel INFO
deadline v1 30
deadline v2 60
client 10.0.0.5
client 192.168.1.20
exit was: 0
```

---

## TASK 1 of 2 — Prove presence and extraction

**In plain English:** We test that a directive exists, then prove the extracted IP set.

---

### Step 1 of 2 — Presence test with `grep -Eq`

**In plain English:** We silently test whether the canonical Port line exists.

```bash
cd "$LAB_ROOT"
grep -Eq '^Port 2222$' sshd_demo.conf && echo "PORT OK" || echo "PORT MISSING (FAIL)"
echo "exit was: $?"
```

**Expected output:**

```
PORT OK
exit was: 0
```

**Line-by-line breakdown:**

- `grep -Eq '^Port 2222$'` → `-q` suppresses output; the exit code alone says present (0) or absent (1).
- `&& ... || ...` → Branch on the exit code for a clean pass/fail message.

**New words in this step:**

- **`grep -Eq`** — quiet match used purely for its exit code in tests.

---

### Step 2 of 2 — Prove the extraction set

**In plain English:** We extract all IPv4 addresses and confirm the distinct set is exactly the two we expect.

```bash
cd "$LAB_ROOT"
grep -Eo '[0-9]{1,3}(\.[0-9]{1,3}){3}' sshd_demo.conf | sort -u > got.txt
printf '10.0.0.5\n192.168.1.20\n' | sort -u > want.txt
diff got.txt want.txt && echo "IP SET OK" || echo "IP SET WRONG (FAIL)"
```

**Expected output:**

```
IP SET OK
```

**Line-by-line breakdown:**

- `grep -Eo '...' | sort -u` → Extract every IPv4 match and reduce to the distinct set.
- `diff got.txt want.txt` → Empty output proves the extracted set equals the expected set.

**New words in this step:**

- **extraction set** — the distinct values a regex pulled, compared to expectation.

---

### Concept card (Task 1)

| Concept | What it does | Exam trap |
|---|---|---|
| `-q` | exit-code only | no stdout to parse |
| `-o | sort -u` | distinct matches | duplicates collapse |
| anchored test | exact line | `^...$` for whole line |

---

### Troubleshoot (Task 1)

| Symptom | Likely cause | Fix |
|---|---|---|
| `-q` prints nothing | That's correct | Read the exit code |
| IP set mismatch | Regex too loose/tight | Adjust octet pattern |

---

## TASK 2 of 2 — Prove count and absence

**In plain English:** We assert the rewritten line count and prove the old pattern is gone.

---

### Step 1 of 2 — Count with `grep -Ec`

**In plain English:** We confirm exactly two `deadline` lines exist after the rewrite.

```bash
cd "$LAB_ROOT"
C=$(grep -Ec '^deadline v[0-9]+' sshd_demo.conf)
echo "deadline lines: $C"
[ "$C" -eq 2 ] && echo "COUNT OK" || echo "WRONG COUNT (FAIL)"
```

**Expected output:**

```
deadline lines: 2
COUNT OK
```

**Line-by-line breakdown:**

- `grep -Ec '^deadline v[0-9]+'` → Count lines matching the rewritten form.
- `[ "$C" -eq 2 ]` → Assert both lines were rewritten.

**New words in this step:**

- **count assertion** — proving the exact number of matching lines.

---

### Step 2 of 2 — Prove absence with `grep -Eq`

**In plain English:** We confirm the old `timeout v` pattern no longer appears.

```bash
cd "$LAB_ROOT"
if grep -Eq 'timeout v[0-9]+' sshd_demo.conf; then
  echo "OLD PATTERN STILL PRESENT (FAIL)"
else
  echo "OLD PATTERN GONE (OK)"
fi
grep -Ev '^deadline' sshd_demo.conf | grep -Ec 'timeout' || true
```

**Expected output:**

```
OLD PATTERN GONE (OK)
0
```

**Line-by-line breakdown:**

- `if grep -Eq 'timeout v[0-9]+'` → Non-zero exit (no match) is the success branch — the old form is gone.
- `grep -Ev '^deadline' | grep -Ec 'timeout'` → Among non-deadline lines, count any leftover `timeout`; `0` confirms none.

**New words in this step:**

- **absence proof** — verifying a pattern does *not* occur (inverse assertion).

---

### Concept card (Task 2)

| Concept | What it does | Exam trap |
|---|---|---|
| `-Ec` | count lines | not occurrences |
| `-q` for absence | rc 1 = gone | invert the logic |
| `-v` | non-matching | useful for "everything but" |

---

### Troubleshoot (Task 2)

| Symptom | Likely cause | Fix |
|---|---|---|
| Old pattern lingers | Rewrite incomplete | Re-run the replace play |
| Count off | Anchor too strict/loose | Adjust the regex |

---

## ✅ Lab Checklist

- [ ] Task 1 · Step 1 — Presence test with `grep -Eq`
- [ ] Task 1 · Step 2 — Prove the extraction set
- [ ] Task 2 · Step 1 — Count with `grep -Ec`
- [ ] Task 2 · Step 2 — Prove absence with `grep -Eq`
- [ ] Every 🎯 Focus Coverage row (Anchor + NEW) mapped to a step
- [ ] 🧹 Teardown run — sandbox + any system state removed

---

## 🧹 Teardown

**In plain English:** Delete everything this lab created so the box is clean for the next run.

> Run this after you've verified the lab. `lab_teardown.sh` safely removes the single sandbox root — it refuses to touch `/`, `$HOME`, or any protected path. This verify lab changed **no** system state.

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
| Proving presence only | Old value left behind | Also prove absence |
| `-c` vs occurrences | Wrong count | `-c` counts lines |
| Loose extraction regex | Extra matches | Tighten the pattern |

---

## 📌 Exam Strategy

A regex change is verified by four checks: presence (`-q`), set (`-o | sort -u`), count (`-c`), and absence (`-q` inverted). Always prove the old value is gone, not just that the new one arrived.

- `-q` for boolean tests in `if`/`&&`.
- `-o | sort -u` certifies an extraction set.
- Absence proofs catch incomplete rewrites.

---

## 🔗 Related Labs

- [Lab 22a — Filtering with grep and Regex (RHCSA)](../lab-22a-grep-regex-rhcsa/) — the regex this audits
- [Lab 22b — Filtering with grep and Regex (Ansible)](../lab-22b-grep-regex-ansible/) — the rewrites you verify
- [Lab 23a — Comparing File Differences (RHCSA)](../lab-23a-diff-comparing-files-rhcsa/) — diff-based verification

---

## 👤 Author

**Kelvin R. Tobias**  
[kelvinintech.com](https://kelvinintech.com) · [GitHub](https://github.com/kelvintechnical) · [LinkedIn](https://www.linkedin.com/in/kelvin-r-tobias-211949219)
