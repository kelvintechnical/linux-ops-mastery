# Lab 30c: Navigating info Pages (Verify) — `info --output`, node checks

**Series:** linux-ops-mastery — Documentation · **Lab 30c of the Novice → RHCA path**  
**Certifications covered:** RHCSA EX200 (proving info docs resolve), SRE (doc-availability checks), DevOps (artifact validation)  
**Prerequisite:** [Lab 30a](../lab-30a-info-pages-rhcsa/) and [Lab 30b](../lab-30b-info-pages-ansible/) completed  
**Time Estimate:** 15–25 minutes  
**Difficulty:** Beginner

---

## 🎯 Today's Focus Coverage

> Stay on-subject via the ANCHOR rows; expand vocabulary via the NEW rows. Every row is exercised by a STEP below.

**⚓ Anchor — already learned (on-topic reuse)**

| # | Command / switch | Covered by |
|---|---|---|
| A1 | `info --output` | _Task 1 · Step 1_ |
| A2 | `grep -q` / `wc -l` | _Task 1 · Step 2_ |

**🆕 NEW this lab — introduced for the first time** (minimum 3)

| # | Command / switch | First taught in | Covered by |
|---|---|---|---|
| N1 | node-resolves rc check | Task 1 · Step 1 | _Task 1 · Step 1_ |
| N2 | non-empty render proof | Task 1 · Step 2 | _Task 1 · Step 2_ |
| N3 | content presence in node | Task 2 · Step 1 | _Task 2 · Step 1_ |
| N4 | `install-info` / dir file check | Task 2 · Step 2 | _Task 2 · Step 2_ |

---

## 🎯 Objective

Prove an info node resolves and carries the content you expect. You will confirm a node renders (exit code), check the render is non-empty and substantial, verify it documents a specific option, and confirm the info directory (`dir`) registers the manual. These checks certify that the long-form GNU documentation you depend on is actually installed and findable.

---

## 🧠 Concept

Info verification has the same shape as man verification but targets nodes. `info --output=- NODE` exits 0 and emits text when the node resolves, non-zero when it doesn't — a boolean for "does this node exist?" A render that's suspiciously short may indicate a missing manual, so check the line count is substantial. Content checks (`grep -q OPTION`) confirm the node documents what you need. Finally, the info **dir** file (`/usr/share/info/dir`) is the top-level menu that `install-info` maintains; a manual listed there is properly registered and discoverable by `info NAME` without a full path.

```
info --output=- coreutils 'ls invocation'; echo $? → 0 = resolves
... | wc -l  (substantial, not ~0)              → real content
... | grep -q -- --human-readable               → documents the option
grep -q coreutils /usr/share/info/dir           → manual registered
```

> **Why this matters:** A role that points users to `info coreutils` assumes the manual is installed and registered. Proving the node resolves, has content, and is in the `dir` index is what backs that assumption.

---

## 📚 Command Reference

| Command | Purpose | Critical flags |
|---|---|---|
| `info --output=-` | Render to stdout | rc 0 = resolves |
| `wc -l` | Render size | substantial check |
| `grep -q` | Content presence | exit-code only |
| `/usr/share/info/dir` | Top-level index | registration |
| `install-info` | Manage `dir` | registers manuals |

---

## 🧰 LAB-WIDE SETUP

**In plain English:** Make a sandbox for saved renders; info docs come from the system.

> Run this block **once** before Task 1. `LAB_ROOT` holds rendered nodes.

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

## TASK 1 of 2 — Prove the node resolves

**In plain English:** We confirm the node renders and produces real content.

---

### Step 1 of 2 — Resolve check via exit code

**In plain English:** We confirm the `ls` node renders successfully and a bogus node fails.

```bash
cd "$LAB_ROOT"
info --output=- coreutils 'ls invocation' >/dev/null 2>&1 && echo "NODE OK" || echo "NODE MISSING (FAIL)"
info --output=- coreutils 'no such node xyz' >/dev/null 2>&1 && echo "unexpected" || echo "BOGUS DETECTED (OK)"
```

**Expected output:**

```
NODE OK
BOGUS DETECTED (OK)
```

**Line-by-line breakdown:**

- `info --output=- coreutils 'ls invocation' >/dev/null 2>&1 && ...` → Exit 0 means the node resolved; output discarded.
- the bogus node → Non-zero exit confirms the failure path works.

**New words in this step:**

- **node resolves** — `info --output` exit code as a node-exists boolean.

---

### Step 2 of 2 — Prove the render is substantial

**In plain English:** We confirm the rendered node has real content, not a stub.

```bash
cd "$LAB_ROOT"
info --output=- coreutils 'ls invocation' > ls-node.txt
N=$(wc -l < ls-node.txt)
echo "node lines: $N"
[ "$N" -gt 20 ] && echo "SUBSTANTIAL (OK)" || echo "TOO SHORT (FAIL)"
```

**Expected output:**

```
node lines: 200
SUBSTANTIAL (OK)
```

**Line-by-line breakdown:**

- `info --output=- ... > ls-node.txt` → Save the rendered node.
- `wc -l < ls-node.txt` → Count its lines.
- `[ "$N" -gt 20 ]` → A real node has many lines; a tiny render hints at a missing manual.

**New words in this step:**

- **substantial render** — a node with real content, not a near-empty stub.

---

### Concept card (Task 1)

| Concept | What it does | Exam trap |
|---|---|---|
| `--output` rc | resolves | 0 found |
| line count | content | tiny = suspect |
| bogus node | failure path | non-zero rc |

---

### Troubleshoot (Task 1)

| Symptom | Likely cause | Fix |
|---|---|---|
| Node fails | Manual not installed | Install the package |
| Render too short | Wrong/empty node | Check node name |

---

## TASK 2 of 2 — Prove content and registration

**In plain English:** We confirm the node documents an option and the manual is registered.

---

### Step 1 of 2 — Content presence in the node

**In plain English:** We confirm the rendered node documents the `--human-readable` option.

```bash
cd "$LAB_ROOT"
grep -q -- '--human-readable' ls-node.txt && echo "OPTION DOCUMENTED (OK)" || echo "MISSING (FAIL)"
grep -c -- '-l' ls-node.txt
```

**Expected output:**

```
OPTION DOCUMENTED (OK)
12
```

**Line-by-line breakdown:**

- `grep -q -- '--human-readable' ls-node.txt` → `--` stops option parsing; rc 0 means the option is documented in the node.
- `grep -c -- '-l'` → Count references to the `-l` option as a sanity signal.

**New words in this step:**

- **node content check** — confirming a rendered node documents a needed feature.

---

### Step 2 of 2 — Manual registration in `dir`

**In plain English:** We confirm the coreutils manual is listed in the info directory index.

```bash
grep -qi coreutils /usr/share/info/dir 2>/dev/null && echo "REGISTERED (OK)" || echo "NOT IN DIR (info)"
ls /usr/share/info/coreutils* >/dev/null 2>&1 && echo "INFO FILE PRESENT (OK)" || echo "NO INFO FILE (FAIL)"
echo "exit was: $?"
```

**Expected output:**

```
REGISTERED (OK)
INFO FILE PRESENT (OK)
exit was: 0
```

**Line-by-line breakdown:**

- `grep -qi coreutils /usr/share/info/dir` → The `dir` file is info's top-level menu; a match means `info coreutils` resolves without a path.
- `ls /usr/share/info/coreutils*` → Confirm the actual info source file is installed.

**New words in this step:**

- **`dir` registration** — a manual listed in info's top-level index, kept by `install-info`.

---

### Concept card (Task 2)

| Concept | What it does | Exam trap |
|---|---|---|
| `grep -q --` | option present | `--` ends options |
| `dir` file | top index | registration |
| info file | the manual | path varies |

---

### Troubleshoot (Task 2)

| Symptom | Likely cause | Fix |
|---|---|---|
| Not in `dir` | `install-info` not run | Reinstall/register |
| No info file | Package missing | Install the package |

---

## ✅ Lab Checklist

- [ ] Task 1 · Step 1 — Resolve check via exit code
- [ ] Task 1 · Step 2 — Prove the render is substantial
- [ ] Task 2 · Step 1 — Content presence in the node
- [ ] Task 2 · Step 2 — Manual registration in `dir`
- [ ] Every 🎯 Focus Coverage row (Anchor + NEW) mapped to a step
- [ ] 🧹 Teardown run — sandbox + any system state removed

---

## 🧹 Teardown

**In plain English:** Delete everything this lab created so the box is clean for the next run.

> Run this after you've verified the lab. `lab_teardown.sh` safely removes the single sandbox root — it refuses to touch `/`, `$HOME`, or any protected path. This verify lab changed **no** system state.

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
| Assuming node exists | Runbook breaks | Test with `--output` rc |
| Trusting tiny render | Missing manual | Check line count |
| `grep` eats `--opt` | Error | Use `grep -q --` |

---

## 📌 Exam Strategy

Certify info docs by node resolution (`--output` rc), substantial content (line count), option presence (`grep -q --`), and `dir` registration. If `info NAME` should work and doesn't, confirm the manual is installed and registered.

- `info --output=-` rc is your node-exists boolean.
- A real node is many lines, not a stub.
- The `dir` file proves `info NAME` will resolve.

---

## 🔗 Related Labs

- [Lab 30a — Navigating info Pages (RHCSA)](../lab-30a-info-pages-rhcsa/) — the `info` reader this audits
- [Lab 30b — Navigating info Pages (Ansible)](../lab-30b-info-pages-ansible/) — the node-capture plays you verify
- [Lab 28c — Exploring Manual Pages (Verify)](../lab-28c-man-pages-verify/) — the parallel man-page checks

---

## 👤 Author

**Kelvin R. Tobias**  
[kelvinintech.com](https://kelvinintech.com) · [GitHub](https://github.com/kelvintechnical) · [LinkedIn](https://www.linkedin.com/in/kelvin-r-tobias-211949219)
