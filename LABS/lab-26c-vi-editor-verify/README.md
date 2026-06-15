# Lab 26c: Editing Files (Verify) — proving saved edits and managed blocks

**Series:** linux-ops-mastery — Text Editors · **Lab 26c of the Novice → RHCA path**  
**Certifications covered:** RHCSA EX200 (proving an edit was saved correctly), SRE (config-edit validation), DevOps (managed-block verification)  
**Prerequisite:** [Lab 26a](../lab-26a-vi-editor-rhcsa/) and [Lab 26b](../lab-26b-vi-editor-ansible/) completed  
**Time Estimate:** 15–25 minutes  
**Difficulty:** Beginner

---

## 🎯 Today's Focus Coverage

> Stay on-subject via the ANCHOR rows; expand vocabulary via the NEW rows. Every row is exercised by a STEP below.

**⚓ Anchor — already learned (on-topic reuse)**

| # | Command / switch | Covered by |
|---|---|---|
| A1 | `grep -q` presence | _Task 1 · Step 1_ |
| A2 | `sed -n` range print | _Task 2 · Step 1_ |

**🆕 NEW this lab — introduced for the first time** (minimum 3)

| # | Command / switch | First taught in | Covered by |
|---|---|---|---|
| N1 | edit-position proof (`grep -A`) | Task 1 · Step 1 | _Task 1 · Step 1_ |
| N2 | `vim -es` headless edit | Task 1 · Step 2 | _Task 1 · Step 2_ |
| N3 | managed-block extraction | Task 2 · Step 1 | _Task 2 · Step 1_ |
| N4 | marker-pair integrity | Task 2 · Step 2 | _Task 2 · Step 2_ |

---

## 🎯 Objective

Prove an edit landed where intended and that a managed block is well-formed. You will confirm an inserted line sits under the right header (`grep -A`), apply a non-interactive `vim -es` edit and verify it, extract a marker-delimited block, and confirm the BEGIN/END marker pair is balanced. These checks validate both hand edits and Ansible-managed regions.

---

## 🧠 Concept

Editing verification is about *position* and *integrity*, not just presence. A line can exist but be in the wrong place; `grep -A1 '^\[network\]'` proves the inserted line follows its header. `vim` can edit non-interactively with `-es` (ex-silent mode) fed a command script — useful for scripted edits and to prove vim commands do what you expect. For Ansible-managed blocks, the BEGIN/END `marker:` pair must be balanced (exactly one each) or the region is corrupt; `sed -n '/BEGIN/,/END/p'` extracts the block and `grep -c` confirms the markers are paired.

```
grep -A1 '^\[network\]' f → header then the inserted line
printf ':...\nx\n' | vim -es f → scripted non-interactive edit
sed -n '/BEGIN APP/,/END APP/p' f → extract the managed block
grep -c 'BEGIN APP' f == grep -c 'END APP' f == 1 → markers balanced
```

> **Why this matters:** A config line in the wrong section, or a block with a broken/duplicated marker, fails subtly. Position and marker-integrity checks catch what a simple `grep` for the value would miss.

---

## 📚 Command Reference

| Command | Purpose | Critical flags |
|---|---|---|
| `grep -A N` | Show lines after match | position proof |
| `vim -es` | Non-interactive ex edit | scripted commands |
| `sed -n '/B/,/E/p'` | Extract a block | range by marker |
| `grep -c` | Count markers | balance check |
| `diff` | Compare expected block | empty = match |

---

## 🧰 LAB-WIDE SETUP

**In plain English:** Recreate an edited config with an inserted line and a managed block.

> Run this block **once** before Task 1. It builds the clean, private workspace that both tasks depend on.

```bash
export LAB_ROOT=/tmp/lab-26
mkdir -p "$LAB_ROOT"
cd "$LAB_ROOT"
cat > app.conf <<'EOF'
[main]
name = demo
[network]
port = 8080
# BEGIN APP LIMITS
max_connections = 100
timeout = 30
retries = 3
# END APP LIMITS
EOF
cat app.conf
echo "exit was: $?"
```

**Expected output:**

```
[main]
name = demo
[network]
port = 8080
# BEGIN APP LIMITS
max_connections = 100
timeout = 30
retries = 3
# END APP LIMITS
exit was: 0
```

---

## TASK 1 of 2 — Prove the line edit

**In plain English:** We confirm the inserted line's position, then make and verify a headless edit.

---

### Step 1 of 2 — Prove the line position

**In plain English:** We confirm `port = 8080` appears immediately after the `[network]` header.

```bash
cd "$LAB_ROOT"
grep -A1 '^\[network\]' app.conf
grep -A1 '^\[network\]' app.conf | grep -q 'port = 8080' \
  && echo "POSITION OK" || echo "WRONG POSITION (FAIL)"
```

**Expected output:**

```
[network]
port = 8080
POSITION OK
```

**Line-by-line breakdown:**

- `grep -A1 '^\[network\]'` → Print the header line plus the one after it.
- `... | grep -q 'port = 8080'` → Confirm the inserted line is exactly that following line — position, not just presence.

**New words in this step:**

- **position proof** — verifying a line's location relative to an anchor, not just that it exists.

---

### Step 2 of 2 — Headless edit with `vim -es`

**In plain English:** We change a value using vim non-interactively and verify the result.

```bash
cd "$LAB_ROOT"
printf '%%s/timeout = 30/timeout = 45/\nwq\n' | vim -es app.conf
grep -q 'timeout = 45' app.conf && echo "HEADLESS EDIT OK" || echo "EDIT FAILED (FAIL)"
echo "exit was: $?"
```

**Expected output:**

```
HEADLESS EDIT OK
exit was: 0
```

**Line-by-line breakdown:**

- `printf '%%s/.../.../\nwq\n' | vim -es app.conf` → Feed ex commands (`:%s` then `:wq`) to vim in silent mode — a scripted, non-interactive edit.
- `grep -q 'timeout = 45'` → Confirm the value changed on disk.

**New words in this step:**

- **`vim -es`** — ex-silent mode; runs vim commands from a script with no UI.

---

### Concept card (Task 1)

| Concept | What it does | Exam trap |
|---|---|---|
| `grep -A1` | position check | header + next line |
| `vim -es` | scripted edit | feed ex commands |
| presence vs position | where, not just if | a line can be misplaced |

---

### Troubleshoot (Task 1)

| Symptom | Likely cause | Fix |
|---|---|---|
| Line present but misplaced | Wrong `insertafter` | Re-anchor and re-run |
| `vim -es` no change | Command syntax | Check the ex script |

---

## TASK 2 of 2 — Prove the managed block

**In plain English:** We extract the block and confirm its markers are balanced.

---

### Step 1 of 2 — Extract the managed block

**In plain English:** We print just the block between the BEGIN and END markers.

```bash
cd "$LAB_ROOT"
sed -n '/# BEGIN APP LIMITS/,/# END APP LIMITS/p' app.conf
echo "exit was: $?"
```

**Expected output:**

```
# BEGIN APP LIMITS
max_connections = 100
timeout = 45
retries = 3
# END APP LIMITS
exit was: 0
```

**Line-by-line breakdown:**

- `sed -n '/# BEGIN APP LIMITS/,/# END APP LIMITS/p'` → Range address from BEGIN marker to END marker; `-n p` prints only that region.

**New words in this step:**

- **block extraction** — printing only the marker-delimited managed region.

---

### Step 2 of 2 — Prove marker integrity

**In plain English:** We confirm there is exactly one BEGIN and one END marker.

```bash
cd "$LAB_ROOT"
B=$(grep -c '# BEGIN APP LIMITS' app.conf)
E=$(grep -c '# END APP LIMITS' app.conf)
echo "BEGIN: $B  END: $E"
[ "$B" -eq 1 ] && [ "$E" -eq 1 ] && echo "MARKERS BALANCED (OK)" || echo "MARKER ERROR (FAIL)"
```

**Expected output:**

```
BEGIN: 1  END: 1
MARKERS BALANCED (OK)
```

**Line-by-line breakdown:**

- `grep -c '# BEGIN ...'` / `grep -c '# END ...'` → Count each marker.
- `[ "$B" -eq 1 ] && [ "$E" -eq 1 ]` → Exactly one of each means the block is well-formed and re-manageable.

**New words in this step:**

- **marker integrity** — a balanced single BEGIN/END pair around a managed block.

---

### Concept card (Task 2)

| Concept | What it does | Exam trap |
|---|---|---|
| `sed` range | extract block | inclusive of markers |
| marker count | integrity | must be 1 each |
| balanced pair | re-manageable | dupes break idempotence |

---

### Troubleshoot (Task 2)

| Symptom | Likely cause | Fix |
|---|---|---|
| Two BEGIN markers | Marker reused elsewhere | Use unique markers |
| Empty extraction | Marker text mismatch | Match the exact marker |

---

## ✅ Lab Checklist

- [ ] Task 1 · Step 1 — Prove the line position
- [ ] Task 1 · Step 2 — Headless edit with `vim -es`
- [ ] Task 2 · Step 1 — Extract the managed block
- [ ] Task 2 · Step 2 — Prove marker integrity
- [ ] Every 🎯 Focus Coverage row (Anchor + NEW) mapped to a step
- [ ] 🧹 Teardown run — sandbox + any system state removed

---

## 🧹 Teardown

**In plain English:** Delete everything this lab created so the box is clean for the next run.

> Run this after you've verified the lab. `lab_teardown.sh` safely removes the single sandbox root — it refuses to touch `/`, `$HOME`, or any protected path. This verify lab changed **no** system state.

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
| Checking presence only | Misplaced line passes | Verify position with `-A` |
| Ignoring markers | Corrupt managed block | Count BEGIN/END |
| Manual block edits | Breaks idempotence | Let Ansible own the block |

---

## 📌 Exam Strategy

Verify edits by position (`grep -A`), not just presence, and verify managed blocks by extracting them and confirming a balanced marker pair. `vim -es` lets you script and test vim edits non-interactively.

- `grep -A1` proves a line followed its anchor.
- Balanced BEGIN/END markers keep a block re-manageable.
- `vim -es` is scriptable vim for verification.

---

## 🔗 Related Labs

- [Lab 26a — Command/Insert Mode in vi (RHCSA)](../lab-26a-vi-editor-rhcsa/) — the interactive editing this audits
- [Lab 26b — Editing Files (Ansible)](../lab-26b-vi-editor-ansible/) — the line/block edits you verify
- [Lab 27c — Safely Editing System Databases (Verify)](../lab-27c-vipw-vigr-safe-editing-verify/) — verifying locked-file edits

---

## 👤 Author

**Kelvin R. Tobias**  
[kelvinintech.com](https://kelvinintech.com) · [GitHub](https://github.com/kelvintechnical) · [LinkedIn](https://www.linkedin.com/in/kelvin-r-tobias-211949219)
