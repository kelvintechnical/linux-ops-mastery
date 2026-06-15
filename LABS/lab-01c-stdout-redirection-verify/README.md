# Lab 01c: Stdout Redirection Verify — `wc -l`, `diff`, `sha256sum`

**Series:** linux-ops-mastery — Shells, Terminals & Redirection · **Lab 01c of the Novice → RHCA path**  
**Certifications covered:** RHCSA EX200 (inspection commands graders run on your work), SRE (post-change verification), DevOps (artifact validation in CI)  
**Prerequisite:** [Lab 01a](../lab-01a-stdout-redirection-rhcsa/) and [Lab 01b](../lab-01b-stdout-redirection-ansible/) completed  
**Time Estimate:** 20–30 minutes  
**Difficulty:** Beginner

---

## 🎯 Objective

Take the auditor's seat: instead of *producing* redirected output, you *prove* it is correct with hard evidence. You will verify numerically that `>` truncates and `>>` preserves, compare a file byte-for-byte against an expected copy, and run a destroy-restore drill that shows volatile `/tmp` disappears while a durable fingerprint lets you rebuild and confirm an exact match.

---

## 🧠 Concept

Verification means running a command to *prove* a fact about the system instead of trusting your memory. For redirection, three tools do all the talking: `wc -l` turns "did the lines survive?" into a number, `diff` turns "does it match what I expected?" into a pass/fail, and `sha256sum` turns "is it byte-for-byte identical?" into a fingerprint that flips if even one character changes. The numbers and hashes are the verdict — not your recollection of having typed the right thing.

```
wc -l < notes.txt    →  3        (count is the verdict)
diff expected notes  →  (empty)  (no output = identical)
sha256sum notes.txt  →  9f3a…    (one fingerprint per exact byte sequence)
```

> **Why this matters:** On the exam and in production, "I'm pretty sure I saved it right" is worth zero points. A line count, a clean `diff`, and a matching hash are objective proof — the same evidence a grader script (or your future on-call self) uses to confirm the work without trusting you.

---

## 📚 Command Reference

| Command | Purpose | Critical flags |
|---|---|---|
| `wc -l` | Count lines as a bare number | `< file` keeps the filename out of the output |
| `cat -n` | Print file contents with line numbers | great for spotting missing/reordered lines |
| `diff -u` | Compare two files, show a unified diff | exit code `1` means "files differ" (not an error) |
| `sha256sum` | Produce a byte-exact fingerprint of a file | pipe through `awk '{print $1}'` to keep just the hash |

---

## 🧰 LAB-WIDE SETUP

**In plain English:** Build the sandbox and re-create the canonical three-line file from Lab 01a so there is something correct to audit, and confirm where it lives so we can reason about persistence later.

> Run this block **once** before Task 1. It builds the clean, private
> workspace that both tasks depend on.

```bash
export SANDBOX=/tmp/labsandbox_01
mkdir -p "${SANDBOX}"

echo "alpha"   >  "${SANDBOX}/notes.txt"
echo "bravo"   >> "${SANDBOX}/notes.txt"
echo "charlie" >> "${SANDBOX}/notes.txt"

ls -la "${SANDBOX}/notes.txt"
echo "Sandbox ready at $(date -Is)"
echo "exit was: $?"
```

**Expected output:**

```
-rw-r--r--. 1 root root 19 Jun 15 17:30 /tmp/labsandbox_01/notes.txt
Sandbox ready at 2026-06-15T17:30:02-04:00
exit was: 0
```

---

## TASK 1 of 2 — Audit: prove `>` truncates and `>>` preserves

**In plain English:** We tell the whole `>` vs `>>` story in numbers — count the good file, watch a single `>` drop the count, rebuild it correctly, then compare it byte-for-byte against an expected copy.

---

### Step 1 of 2 — Count, destroy, and rebuild — read the `wc -l` verdict each time

**In plain English:** We count the canonical file's lines, fire one `>` and re-count to watch two lines silently vanish, then rebuild the right way and re-count to prove `>>` brought them back.

```bash
wc -l < "${SANDBOX}/notes.txt"
echo "only newest" > "${SANDBOX}/notes.txt"
wc -l < "${SANDBOX}/notes.txt"
echo "alpha"   >  "${SANDBOX}/notes.txt"
echo "bravo"   >> "${SANDBOX}/notes.txt"
echo "charlie" >> "${SANDBOX}/notes.txt"
wc -l < "${SANDBOX}/notes.txt"
```

**Expected output:**

```
3
1
3
```

**Line-by-line breakdown:**

- `wc -l < "${SANDBOX}/notes.txt"` (first) → Baseline count; prints `3`, proving `>>` built the canonical file.
- `echo "only newest" > "${SANDBOX}/notes.txt"` → A single `>` truncates the file and writes one line — the silent destruction.
- `wc -l < ...` (second) → Re-count; prints `1`, proving two lines were lost with no warning.
- the three `echo` lines → Rebuild with `>` for line 1 (start fresh) then `>>` for the rest, and the final `wc -l` prints `3` again — proof `>>` preserves.

**New words in this step:**

- **audit** — running a command to prove a fact about the system instead of trusting your memory.

---

### Step 2 of 2 — Compare against expected with `diff`

**In plain English:** We write an expected copy of what the file *should* contain, then ask `diff` whether the real file matches it byte-for-byte — no output means a perfect match.

```bash
cat > /tmp/expected_notes.txt <<'EOF'
alpha
bravo
charlie
EOF
diff -u /tmp/expected_notes.txt "${SANDBOX}/notes.txt" && echo "MATCH (OK)"
echo "exit was: $?"
```

**Expected output:**

```
MATCH (OK)
exit was: 0
```

**Line-by-line breakdown:**

- `cat > /tmp/expected_notes.txt <<'EOF' ... EOF` → A heredoc writing the three expected lines into a reference file; the quoted `'EOF'` means "write the text exactly, no variable substitution."
- `diff -u /tmp/expected_notes.txt "${SANDBOX}/notes.txt"` → Compare expected vs actual; `-u` shows a unified diff. No differences means no output and exit code `0`, so `&& echo "MATCH (OK)"` fires.
- `echo "exit was: $?"` → Prints `0` when the files are identical; a `1` here would mean they differ.

**New words in this step:**

- **heredoc** — a block of text typed inline that gets fed into a command or file, ending at a marker word like `EOF`.

---

### Concept card (Task 1)

| Concept | What it does | Exam trap |
|---|---|---|
| `wc -l < f` | line count as a bare number | proves `>` vs `>>` numerically |
| `diff -u` | expected vs actual comparison | exit `1` means "differ," which is not an error |
| `>` then `>>` rebuild | restore to a known-good state | using `>>` first appends to stale data |

---

### Troubleshoot (Task 1)

| Symptom | Likely cause | Fix |
|---|---|---|
| `wc -l` stays `1` after rebuild | The rebuild used `>` on every line | Use `>` only for line 1, `>>` for the rest |
| `diff` shows `+`/`-` lines | Actual content differs from expected | Re-run the rebuild; check for stray spaces |

---

## TASK 2 of 2 — Destroy-restore drill with `sha256sum`

**In plain English:** We fingerprint the file, wipe the sandbox to simulate a reboot, rebuild it from muscle memory, and prove the new fingerprint matches the old one exactly.

---

### Step 1 of 2 — Fingerprint, then destroy

**In plain English:** We take a `sha256sum` of the file (a fingerprint that flips if any byte changes), save it, then delete the whole sandbox to mimic `/tmp` being cleared on reboot.

```bash
BEFORE_HASH=$(sha256sum "${SANDBOX}/notes.txt" | awk '{print $1}')
echo "BEFORE hash: ${BEFORE_HASH}"
rm -rf "${SANDBOX}"
test -d "${SANDBOX}" && echo "sandbox STILL exists (FAIL)" || echo "sandbox gone (OK)"
```

**Expected output:**

```
BEFORE hash: 9f3a1c2b... (64 hex chars)
sandbox gone (OK)
```

**Line-by-line breakdown:**

- `BEFORE_HASH=$(sha256sum ... | awk '{print $1}')` → Compute the fingerprint and store it; `sha256sum` prints `<hash> <filename>`, and `awk '{print $1}'` keeps only the hash.
- `echo "BEFORE hash: ${BEFORE_HASH}"` → Print the saved fingerprint so you can compare it later.
- `rm -rf "${SANDBOX}"` → Delete the sandbox tree, simulating `/tmp` being cleared on reboot.
- `test -d "${SANDBOX}" && ... || ...` → Confirm the folder is gone; we want `sandbox gone (OK)`.

**New words in this step:**

- **`sha256sum`** — a tool that produces a fixed fingerprint of a file's exact bytes; identical files share a hash, any change flips it.

---

### Step 2 of 2 — Rebuild and prove byte-identical

**In plain English:** We rebuild the file with the same `>`-then-`>>` idiom, fingerprint it again, and prove the new hash equals the saved one — a byte-for-byte restore.

```bash
mkdir -p "${SANDBOX}"
echo "alpha"   >  "${SANDBOX}/notes.txt"
echo "bravo"   >> "${SANDBOX}/notes.txt"
echo "charlie" >> "${SANDBOX}/notes.txt"
AFTER_HASH=$(sha256sum "${SANDBOX}/notes.txt" | awk '{print $1}')
test "${BEFORE_HASH}" = "${AFTER_HASH}" && echo "restore MATCH (OK)" || echo "restore MISMATCH (FAIL)"
echo "exit was: $?"
```

**Expected output:**

```
restore MATCH (OK)
exit was: 0
```

**Line-by-line breakdown:**

- `mkdir -p "${SANDBOX}"` → Recreate the sandbox folder we just deleted.
- the three `echo` lines → Rebuild the file exactly, `>` first then `>>`, reproducing the original byte sequence.
- `AFTER_HASH=$(sha256sum ... | awk '{print $1}')` → Fingerprint the rebuilt file.
- `test "${BEFORE_HASH}" = "${AFTER_HASH}" && ... || ...` → Compare the two fingerprints; `restore MATCH (OK)` proves the rebuild is byte-identical. A mismatch would mean a stray space or `>>`-vs-`>` slip changed the bytes.

**New words in this step:**

- **persistence** — whether a file survives a reboot (durable) or disappears (volatile, like `/tmp`).

---

### Concept card (Task 2)

| Concept | What it does | Exam trap |
|---|---|---|
| `sha256sum` | byte-exact file fingerprint | `cat` can miss trailing-newline differences a hash catches |
| `rm -rf ${SANDBOX}` | simulate `/tmp` volatility | the lab user account would survive — only files vanish |
| hash equality test | proves a lossless restore | a stray space flips the hash |

---

### Troubleshoot (Task 2)

| Symptom | Likely cause | Fix |
|---|---|---|
| `restore MISMATCH (FAIL)` | Extra space or line in the rebuild | Rebuild exactly; verify with `cat -A` to see hidden chars |
| `sha256sum: No such file` | Sandbox not recreated before fingerprinting | Run `mkdir -p "${SANDBOX}"` and rebuild first |

---

## ✅ Lab Checklist

- [ ] Task 1 · Step 1 — Count, destroy, and rebuild — read the `wc -l` verdict each time
- [ ] Task 1 · Step 2 — Compare against expected with `diff`
- [ ] Task 2 · Step 1 — Fingerprint, then destroy
- [ ] Task 2 · Step 2 — Rebuild and prove byte-identical

---

## ⚠️ Common Pitfalls

| Mistake | Symptom | Fix |
|---|---|---|
| Trusting `cat` instead of a hash | A trailing-newline difference goes unnoticed | Use `sha256sum` for byte-exact verification |
| Treating `diff` exit `1` as failure | You abort a script that was working | `1` just means "differ"; wrap in `\|\| true` if intentional |
| Forgetting `< file` with `wc -l` | Output includes the filename | Feed via `<` so only the number prints |

---

## 📌 Exam Strategy

Verification is what turns "I did the task" into "I can prove I did the task." After any redirection step, count the lines, compare against what you expected, and (for anything that must survive) confirm a fingerprint. Build the habit of auditing your own work before you move on — it catches the silent `>` slip before the grader does.

- `wc -l < file` is your fastest pass/fail; memorize the bare-number form.
- A clean `diff` (no output) is the strongest "it matches" signal — learn to read empty output as success.
- `sha256sum | awk '{print $1}'` is the production idiom for "give me just the hash" — use it for any before/after comparison.

---

## 🔗 Related Labs

- [Lab 01a — Stdout Redirection (RHCSA)](../lab-01a-stdout-redirection-rhcsa/) — the creator-seat lab this audits
- [Lab 01b — Stdout Redirection (Ansible)](../lab-01b-stdout-redirection-ansible/) — the playbook whose output you can verify the same way
- [Lab 02c — Stderr Redirection (Verify)](../lab-02c-stderr-redirection-verify/) — the stderr analog of this audit-and-restore pattern

---

## 👤 Author

**Kelvin R. Tobias**  
[kelvinintech.com](https://kelvinintech.com) · [GitHub](https://github.com/kelvintechnical) · [LinkedIn](https://www.linkedin.com/in/kelvin-r-tobias-211949219)
