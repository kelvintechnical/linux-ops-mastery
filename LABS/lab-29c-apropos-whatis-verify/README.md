# Lab 29c: Searching Manuals by Keyword (Verify) — `whatis`, `apropos`, `grep`

**Series:** linux-ops-mastery — Documentation · **Lab 29c of the Novice → RHCA path**  
**Certifications covered:** RHCSA EX200 (proving keyword discovery works), SRE (tool-inventory validation), DevOps (dependency checks)  
**Prerequisite:** [Lab 29a](../lab-29a-apropos-whatis-rhcsa/) and [Lab 29b](../lab-29b-apropos-whatis-ansible/) completed  
**Time Estimate:** 15–25 minutes  
**Difficulty:** Beginner

---

## 🎯 Today's Focus Coverage

> Stay on-subject via the ANCHOR rows; expand vocabulary via the NEW rows. Every row is exercised by a STEP below.

**⚓ Anchor — already learned (on-topic reuse)**

| # | Command / switch | Covered by |
|---|---|---|
| A1 | `whatis` / `apropos` | _Task 1 · Step 1_ |
| A2 | `grep -q` / `-c` | _Task 1 · Step 1_ |

**🆕 NEW this lab — introduced for the first time** (minimum 3)

| # | Command / switch | First taught in | Covered by |
|---|---|---|---|
| N1 | `whatis` rc as existence | Task 1 · Step 1 | _Task 1 · Step 1_ |
| N2 | `apropos | grep -q` presence | Task 1 · Step 2 | _Task 1 · Step 2_ |
| N3 | section-tag verification | Task 2 · Step 1 | _Task 2 · Step 1_ |
| N4 | index freshness check | Task 2 · Step 2 | _Task 2 · Step 2_ |

---

## 🎯 Objective

Prove keyword discovery actually finds the right tools. You will use `whatis`'s exit code as an existence test, confirm `apropos` lists a required command, verify a result carries the expected section tag, and confirm the whatis index is fresh. These checks certify that "search the manuals" will work when you need it.

---

## 🧠 Concept

Discovery verification mirrors documentation verification but through the *index*. `whatis NAME` exits 0 when a summary exists and 16 ("nothing appropriate") otherwise — a boolean for "is this command documented?" `apropos KEY | grep -q '^cmd '` proves a specific tool appears in a keyword search. The section tag in results (`(1)`, `(5)`, `(8)`) confirms you found the right *kind* of page. And because `whatis`/`apropos` read a cached index, freshness matters: comparing a known command's presence before/after `mandb`, or checking the index file exists, confirms the cache is usable.

```
whatis chmod; echo $?        → 0 = documented, 16 = not
apropos owner | grep -q '^chown ' → required tool present
whatis passwd | grep -q '(5)' → section-5 page exists
ls /var/cache/man/index.db   → whatis index present
```

> **Why this matters:** A role's "ensure the tool exists" check relies on the man index being correct. Proving `whatis`/`apropos` resolve the tools you depend on — in the right section — is the validation behind that assumption.

---

## 📚 Command Reference

| Command | Purpose | Critical flags |
|---|---|---|
| `whatis` (rc) | Existence test | 0 found, 16 none |
| `apropos | grep -q` | Tool presence | exit-code only |
| section tag `(N)` | Right kind of page | grep the tag |
| `mandb` | Refresh index | freshness |
| index file | Cache present | usability |

---

## 🧰 LAB-WIDE SETUP

**In plain English:** Make a sandbox for saved checks; data comes from the man index.

> Run this block **once** before Task 1. `LAB_ROOT` holds any notes.

```bash
export LAB_ROOT=/tmp/lab-29
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

## TASK 1 of 2 — Prove existence and presence

**In plain English:** We confirm a command is documented and appears in a keyword search.

---

### Step 1 of 2 — Existence via `whatis` rc

**In plain English:** We test that a known command is documented and an unknown one is not.

```bash
whatis chmod >/dev/null 2>&1 && echo "CHMOD OK" || echo "CHMOD MISSING (FAIL)"
whatis no-such-tool-xyz >/dev/null 2>&1 && echo "unexpected" || echo "ABSENCE DETECTED (OK)"
```

**Expected output:**

```
CHMOD OK
ABSENCE DETECTED (OK)
```

**Line-by-line breakdown:**

- `whatis chmod >/dev/null 2>&1 && ...` → Exit 0 means documented; output discarded.
- `whatis no-such-tool-xyz ...` → Non-zero (16) confirms the absence path works.

**New words in this step:**

- **whatis existence** — using `whatis`'s exit code as a documented/not boolean.

---

### Step 2 of 2 — Presence via `apropos | grep -q`

**In plain English:** We confirm a keyword search actually lists the command we need.

```bash
apropos owner | grep -q '^chown ' && echo "CHOWN DISCOVERABLE (OK)" || echo "NOT FOUND (FAIL)"
C=$(apropos owner | wc -l)
echo "ownership tools: $C"
```

**Expected output:**

```
CHOWN DISCOVERABLE (OK)
ownership tools: 5
```

**Line-by-line breakdown:**

- `apropos owner | grep -q '^chown '` → Anchored match proves `chown` appears in the keyword results.
- `apropos owner | wc -l` → Count of matching tools (varies by system).

**New words in this step:**

- **discoverability** — confirming a tool surfaces in a keyword search.

---

### Concept card (Task 1)

| Concept | What it does | Exam trap |
|---|---|---|
| `whatis` rc | existence | 16 = none |
| `apropos | grep -q` | presence | anchor `^cmd ` |
| count | metric | system-dependent |

---

### Troubleshoot (Task 1)

| Symptom | Likely cause | Fix |
|---|---|---|
| `whatis` rc 16 | Not documented / stale | `mandb` |
| grep no match | Wrong anchor | Match `^cmd ` exactly |

---

## TASK 2 of 2 — Prove section and freshness

**In plain English:** We confirm a result's section and that the index is current.

---

### Step 1 of 2 — Verify the section tag

**In plain English:** We confirm `passwd` is discoverable as a section-5 (file format) page.

```bash
whatis passwd
whatis passwd | grep -q '(5)' && echo "SECTION 5 PRESENT (OK)" || echo "NO SECTION 5 (FAIL)"
```

**Expected output:**

```
passwd (1)           - change user password
passwd (5)           - the password file
SECTION 5 PRESENT (OK)
```

**Line-by-line breakdown:**

- `whatis passwd` → Shows all sections `passwd` is documented in.
- `... | grep -q '(5)'` → Confirm the section-5 (config-file) page is present — what you need when editing `/etc/passwd`.

**New words in this step:**

- **section-tag check** — verifying a result carries the expected `(N)` section.

---

### Step 2 of 2 — Confirm index freshness

**In plain English:** We rebuild the index and re-verify a lookup, proving the cache is usable.

```bash
sudo mandb >/dev/null 2>&1
whatis ls >/dev/null 2>&1 && echo "INDEX USABLE (OK)" || echo "INDEX BROKEN (FAIL)"
ls /var/cache/man/index.db >/dev/null 2>&1 && echo "INDEX FILE PRESENT (OK)" || echo "NO INDEX FILE (info)"
echo "exit was: $?"
```

**Expected output:**

```
INDEX USABLE (OK)
INDEX FILE PRESENT (OK)
exit was: 0
```

**Line-by-line breakdown:**

- `sudo mandb` → Rebuild the whatis index.
- `whatis ls` → A successful lookup after rebuild proves the index is usable.
- `ls /var/cache/man/index.db` → Confirm the cache file exists (path may vary by distro).

**New words in this step:**

- **index freshness** — confirming the whatis cache is current and usable.

---

### Concept card (Task 2)

| Concept | What it does | Exam trap |
|---|---|---|
| `(5)` tag | section check | config-file page |
| `mandb` | refresh | run after installs |
| index file | cache | path varies |

---

### Troubleshoot (Task 2)

| Symptom | Likely cause | Fix |
|---|---|---|
| No `(5)` | Format page absent | Install the package |
| Lookup fails post-mandb | Permission/corrupt | Re-run `sudo mandb` |

---

## ✅ Lab Checklist

- [ ] Task 1 · Step 1 — Existence via `whatis` rc
- [ ] Task 1 · Step 2 — Presence via `apropos | grep -q`
- [ ] Task 2 · Step 1 — Verify the section tag
- [ ] Task 2 · Step 2 — Confirm index freshness
- [ ] Every 🎯 Focus Coverage row (Anchor + NEW) mapped to a step
- [ ] 🧹 Teardown run — sandbox + any system state removed

---

## 🧹 Teardown

**In plain English:** Delete everything this lab created so the box is clean for the next run.

> Run this after you've verified the lab. `lab_teardown.sh` safely removes the single sandbox root — it refuses to touch `/`, `$HOME`, or any protected path. This verify lab only refreshed the man index (harmless) and changed **no** other system state.

```bash
cd /tmp
bash lab_teardown.sh "$LAB_ROOT"     # = /tmp/lab-29
```

**Expected output:**

```
✅ Removed /tmp/lab-29 — lab workspace is clean.
```

---

## ⚠️ Common Pitfalls

| Mistake | Symptom | Fix |
|---|---|---|
| Assuming discoverable | Tool not indexed | Test with `whatis`/`apropos` |
| Ignoring section | Wrong page kind | Check the `(N)` tag |
| Stale index | Missing tools | `sudo mandb` |

---

## 📌 Exam Strategy

Validate discovery with `whatis` exit codes (documented?), `apropos | grep -q` (discoverable?), section-tag checks (right page?), and index freshness (`mandb`). If a tool should be findable and isn't, refresh the index before concluding it's missing.

- `whatis` rc 0/16 is your documented boolean.
- Anchor `apropos | grep '^cmd '` for presence.
- `mandb` before declaring a tool undocumented.

---

## 🔗 Related Labs

- [Lab 29a — Searching Manuals by Keyword (RHCSA)](../lab-29a-apropos-whatis-rhcsa/) — the `whatis`/`apropos` this audits
- [Lab 29b — Searching Manuals by Keyword (Ansible)](../lab-29b-apropos-whatis-ansible/) — the discovery plays you verify
- [Lab 30a — Navigating info Pages (RHCSA)](../lab-30a-info-pages-rhcsa/) — the other built-in documentation system

---

## 👤 Author

**Kelvin R. Tobias**  
[kelvinintech.com](https://kelvinintech.com) · [GitHub](https://github.com/kelvintechnical) · [LinkedIn](https://www.linkedin.com/in/kelvin-r-tobias-211949219)
