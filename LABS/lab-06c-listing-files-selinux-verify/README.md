# Lab 06c: Listing Files and SELinux (Verify) — `ls -Z`, `matchpathcon`, `semanage fcontext -l`

**Series:** linux-ops-mastery — Essential Tools & File Operations · **Lab 06c of the Novice → RHCA path**  
**Certifications covered:** RHCSA EX200 (proving a context is persistent and correct), SRE (verifying security labels before go-live), DevOps (policy compliance checks)  
**Prerequisite:** [Lab 06a](../lab-06a-listing-files-selinux-rhcsa/) and [Lab 06b](../lab-06b-listing-files-selinux-ansible/) completed  
**Time Estimate:** 15–25 minutes  
**Difficulty:** Beginner → Intermediate

---

## 🎯 Today's Focus Coverage

> Stay on-subject via the ANCHOR rows; expand vocabulary via the NEW rows. Every row is exercised by a STEP below.

**⚓ Anchor — already learned (on-topic reuse)**

| # | Command / switch | Covered by |
|---|---|---|
| A1 | `ls -Z` | _Task 1 · Step 1_ |
| A2 | `matchpathcon` | _Task 1 · Step 2_ |

**🆕 NEW this lab — introduced for the first time** (minimum 3)

| # | Command / switch | First taught in | Covered by |
|---|---|---|---|
| N1 | `semanage fcontext -l` | Task 2 · Step 1 | _Task 2 · Step 1_ |
| N2 | `matchpathcon -V` (verify) | Task 1 · Step 2 | _Task 1 · Step 2_ |
| N3 | `stat -c %C` | Task 1 · Step 1 | _Task 1 · Step 1_ |
| N4 | `restorecon -n` (dry-run) | Task 2 · Step 2 | _Task 2 · Step 2_ |

---

## 🎯 Objective

Take the auditor's seat: prove the SELinux label from 06a/06b is both *correct* and *persistent*. You will read the live context with `stat -c %C`, confirm it matches policy with `matchpathcon -V`, prove the rule is recorded with `semanage fcontext -l`, and show a dry-run `restorecon -n` finds nothing to fix — the definitive "already converged" evidence.

---

## 🧠 Concept

A context is verified along two axes. **Live vs expected**: `stat -c %C` (or `ls -Z`) shows the actual label, and `matchpathcon -V` compares it against what policy expects, printing `verified` when they match. **Recorded rule**: `semanage fcontext -l` proves the persistent rule exists, so a relabel or reboot will restore it. The decisive proof of persistence is `restorecon -n` (dry-run): if it would change nothing, the on-disk label already equals the policy rule.

```
stat -c %C index.html        → ...:httpd_sys_content_t:s0   (live label)
matchpathcon -V index.html   → verified                     (matches policy)
semanage fcontext -l | grep  → /tmp/lab-06/webroot(/.*)?     (rule recorded)
restorecon -n -Rv webroot    → (no output)                   (nothing to fix)
```

> **Why this matters:** "It has the right label now" is weaker than "it is recorded so it stays right." Proving both is the difference between a fix that survives a reboot and one that silently reverts.

---

## 📚 Command Reference

| Command | Purpose | Critical flags |
|---|---|---|
| `stat -c %C` | Print just the SELinux context | scriptable; cleaner than parsing `ls -Z` |
| `matchpathcon -V` | Verify actual vs expected context | prints `verified` or the mismatch |
| `semanage fcontext -l` | List recorded fcontext rules | grep for your path to confirm the rule |
| `restorecon -n -Rv` | Dry-run relabel (no changes) | `-n` shows what *would* change |
| `getenforce` | Show SELinux mode | `Enforcing`/`Permissive`/`Disabled` |

---

## 🧰 LAB-WIDE SETUP

**In plain English:** Rebuild the labeled webroot so there is a known-good context to audit (re-using the rule from 06a/06b if present).

> Run this block **once** before Task 1. It builds the clean, private workspace that both tasks depend on.

```bash
export LAB_ROOT=/tmp/lab-06
mkdir -p "$LAB_ROOT/webroot"
echo "<h1>lab 06</h1>" > "$LAB_ROOT/webroot/index.html"
sudo semanage fcontext -a -t httpd_sys_content_t "${LAB_ROOT}/webroot(/.*)?" 2>/dev/null || true
sudo restorecon -Rv "${LAB_ROOT}/webroot"
echo "exit was: $?"
```

**Expected output:**

```
Relabeled /tmp/lab-06/webroot/index.html from ... to system_u:object_r:httpd_sys_content_t:s0
exit was: 0
```

---

## TASK 1 of 2 — Verify the live label matches policy

**In plain English:** We read the actual context and prove it equals what policy expects.

---

### Step 1 of 2 — Read the live context with `stat -c %C`

**In plain English:** We print just the context type of the file to confirm it is web content.

```bash
stat -c '%C %n' "${LAB_ROOT}/webroot/index.html"
stat -c '%C' "${LAB_ROOT}/webroot/index.html" | grep -q 'httpd_sys_content_t' && echo "TYPE OK" || echo "TYPE WRONG (FAIL)"
```

**Expected output:**

```
system_u:object_r:httpd_sys_content_t:s0 /tmp/lab-06/webroot/index.html
TYPE OK
```

**Line-by-line breakdown:**

- `stat -c '%C %n' ...` → Print the context (`%C`) and name (`%n`); cleaner than slicing `ls -Z`.
- `stat -c '%C' ... | grep -q 'httpd_sys_content_t'` → Assert the type is web content, turning the read into a verdict.

**New words in this step:**

- **`stat -c %C`** — emit only the SELinux context field of a file's metadata.

---

### Step 2 of 2 — Confirm policy agreement with `matchpathcon -V`

**In plain English:** We ask SELinux whether the live label matches the expected one and read its `verified` verdict.

```bash
matchpathcon -V "${LAB_ROOT}/webroot/index.html"
echo "exit was: $?"
```

**Expected output:**

```
/tmp/lab-06/webroot/index.html verified.
exit was: 0
```

**Line-by-line breakdown:**

- `matchpathcon -V ...` → `-V` verifies the file's current context against policy; `verified` means actual equals expected. A mismatch would print both contexts and exit non-zero.

**New words in this step:**

- **`matchpathcon -V`** — verify mode; reports `verified` or shows the actual-vs-expected mismatch.

---

### Concept card (Task 1)

| Concept | What it does | Exam trap |
|---|---|---|
| `stat -c %C` | live context | shows current label, not policy expectation |
| `matchpathcon -V` | actual vs expected | `verified` is the only passing output |
| context type | the access-deciding field | user/role rarely matter for file access |

---

### Troubleshoot (Task 1)

| Symptom | Likely cause | Fix |
|---|---|---|
| `matchpathcon` shows mismatch | File not relabeled | Run `restorecon -Rv` then re-verify |
| `%C` shows `?` | SELinux disabled | Check `getenforce` |

---

## TASK 2 of 2 — Prove the rule is recorded and persistent

**In plain English:** We confirm the persistent rule exists and that a dry-run relabel finds nothing to fix.

---

### Step 1 of 2 — Confirm the recorded rule with `semanage fcontext -l`

**In plain English:** We list the local fcontext rules and prove ours is present, which is what makes the label survive a relabel or reboot.

```bash
sudo semanage fcontext -l | grep "${LAB_ROOT}/webroot"
sudo semanage fcontext -l | grep -q "${LAB_ROOT}/webroot" && echo "RULE RECORDED (OK)" || echo "NO RULE (FAIL)"
```

**Expected output:**

```
/tmp/lab-06/webroot(/.*)?    all files    system_u:object_r:httpd_sys_content_t:s0
RULE RECORDED (OK)
```

**Line-by-line breakdown:**

- `semanage fcontext -l | grep ...` → List the rules and show ours, proving the policy entry exists.
- `... | grep -q ... && echo OK || echo FAIL` → Turn "is the rule recorded?" into a pass/fail.

**New words in this step:**

- **`semanage fcontext -l`** — lists all file-context rules, local and built-in.

---

### Step 2 of 2 — Prove convergence with a dry-run `restorecon -n`

**In plain English:** We run `restorecon` in no-change mode; empty output proves the on-disk labels already match the rule.

```bash
sudo restorecon -n -Rv "${LAB_ROOT}/webroot"
echo "restorecon dry-run rc: $?"
echo "(no 'would relabel' lines above means already converged)"
```

**Expected output:**

```
restorecon dry-run rc: 0
(no 'would relabel' lines above means already converged)
```

**Line-by-line breakdown:**

- `restorecon -n -Rv ...` → `-n` makes it a dry-run; with no lines printed, nothing would change — proof the labels already equal the policy.
- `echo "...rc: $?"` → A clean exit confirms the scan ran without error.

**New words in this step:**

- **`restorecon -n`** — dry-run mode that reports what it *would* relabel without doing it.

---

### Concept card (Task 2)

| Concept | What it does | Exam trap |
|---|---|---|
| `semanage fcontext -l` | proves rule persistence | `chcon` leaves NO rule here |
| `restorecon -n` | dry-run audit | output means drift; silence means converged |
| persistence | survives relabel/reboot | only `semanage` rules persist |

---

### Troubleshoot (Task 2)

| Symptom | Likely cause | Fix |
|---|---|---|
| No rule listed | Used `chcon` not `semanage` | Add a rule with `semanage fcontext -a` |
| Dry-run lists relabels | Labels drifted | Run `restorecon -Rv` to converge |

---

## ✅ Lab Checklist

- [ ] Task 1 · Step 1 — Read the live context with `stat -c %C`
- [ ] Task 1 · Step 2 — Confirm policy agreement with `matchpathcon -V`
- [ ] Task 2 · Step 1 — Confirm the recorded rule with `semanage fcontext -l`
- [ ] Task 2 · Step 2 — Prove convergence with a dry-run `restorecon -n`
- [ ] Every 🎯 Focus Coverage row (Anchor + NEW) mapped to a step
- [ ] 🧹 Teardown run — sandbox + any system state removed

---

## 🧹 Teardown

**In plain English:** Delete everything this lab created so the box is clean for the next run.

> Run this after you've verified the lab. `lab_teardown.sh` safely removes the single sandbox root — it refuses to touch `/`, `$HOME`, or any protected path.

```bash
bash lab_teardown.sh "$LAB_ROOT"     # = /tmp/lab-06
```

**This lab (with 06a/06b) created SYSTEM state (an SELinux fcontext rule) — reverse it explicitly:**

```bash
sudo semanage fcontext -d "/tmp/lab-06/webroot(/.*)?"
```

**Expected output:**

```
✅ Removed /tmp/lab-06 — lab workspace is clean.
```

---

## ⚠️ Common Pitfalls

| Mistake | Symptom | Fix |
|---|---|---|
| Verifying live label only | A reboot reverts it | Also prove the `semanage` rule exists |
| Ignoring `restorecon -n` output | Hidden drift ships | Treat any dry-run line as a failure |
| Forgetting to remove the rule | Policy DB clutter | `semanage fcontext -d` in teardown |

---

## 📌 Exam Strategy

For SELinux verification, prove both correctness and persistence: `matchpathcon -V` for the live label, `semanage fcontext -l` for the recorded rule, and `restorecon -n` for "already converged." If all three pass, your context fix will survive the grader's reboot.

- `restorecon -n` silence is the strongest "it is correct and persistent" signal.
- `stat -c %C` is the cleanest scriptable context read.
- Always confirm the rule, not just the current label.

---

## 🔗 Related Labs

- [Lab 06a — Listing Files and SELinux (RHCSA)](../lab-06a-listing-files-selinux-rhcsa/) — the labels this audits
- [Lab 06b — Listing Files and SELinux (Ansible)](../lab-06b-listing-files-selinux-ansible/) — the playbook whose output you verify
- [Lab 07c — Touch Timestamps (Verify)](../lab-07c-touch-timestamps-verify/) — the next metadata-verification lab

---

## 👤 Author

**Kelvin R. Tobias**  
[kelvinintech.com](https://kelvinintech.com) · [GitHub](https://github.com/kelvintechnical) · [LinkedIn](https://www.linkedin.com/in/kelvin-r-tobias-211949219)
