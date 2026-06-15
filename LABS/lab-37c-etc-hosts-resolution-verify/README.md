# Lab 37c: Configuring Local Host Resolution (Verify) — prove `/etc/hosts`

**Series:** linux-ops-mastery — Networking · **Lab 37c of the Novice → RHCA path**  
**Certifications covered:** RHCSA EX200 (evidence-based resolution checks), SRE (resolution-order audits)  
**Prerequisite:** [Lab 37b](../lab-37b-etc-hosts-resolution-ansible/) completed  
**Time Estimate:** 20–30 minutes  
**Difficulty:** Beginner → Intermediate

---

## 🎯 Today's Focus Coverage

> Stay on-subject via the ANCHOR rows; expand vocabulary via the NEW rows. Every row is exercised by a STEP below.

**⚓ Anchor — already learned (on-topic reuse)**

| # | Command / switch | Covered by |
|---|---|---|
| A1 | `getent hosts` | _Task 1 · Step 1_ |
| A2 | `grep -q` assertions | _Task 1 · Step 2_ |

**🆕 NEW this lab — introduced for the first time** (minimum 3)

| # | Command / switch | First taught in | Covered by |
|---|---|---|---|
| N1 | resolution assertion (`getent` rc) | Task 1 · Step 1 | _Task 1 · Step 1_ |
| N2 | exact IP match | Task 1 · Step 2 | _Task 1 · Step 2_ |
| N3 | `getent ahosts` family check | Task 2 · Step 1 | _Task 2 · Step 1_ |
| N4 | precedence proof (files vs dns) | Task 2 · Step 2 | _Task 2 · Step 2_ |

---

## 🎯 Objective

Turn host-file entries into provable resolution. You will assert a name resolves at all (exit code), assert it maps to the *exact* expected IP, inspect the address family with `getent ahosts`, and demonstrate that `/etc/hosts` takes precedence over DNS for a managed name. These checks validate static resolution objectively.

---

## 🧠 Concept

Verifying `/etc/hosts` means proving the *system* resolves names the way you intend. `getent hosts NAME` returns 0 and prints the mapping if resolvable (using the real NSS path), non-zero otherwise — the cleanest reachability-of-name check. For exactness, grep the IP from `getent` output rather than trusting presence alone. `getent ahosts NAME` shows all address families (IPv4/IPv6), useful when an entry should be v4-only. Precedence is the subtle proof: because `nsswitch.conf` lists `files` before `dns`, a name in `/etc/hosts` resolves to the file's value even if DNS would say otherwise — you can demonstrate this for a TEST-NET name that no real DNS would return. Each check is extract-then-assert with PASS/FAIL.

```
getent hosts NAME; echo $?       → resolves? (0 = yes)
getent hosts NAME | awk '{print $1}' == EXPECTED → exact IP
getent ahosts NAME               → address families
files-before-dns in nsswitch     → /etc/hosts wins
```

> **Why this matters:** "The entry is in the file" isn't the same as "the system resolves it correctly". Asserting exit code, exact IP, family, and precedence is the complete proof of static resolution.

---

## 📚 Command Reference

| Command | Purpose | Notes |
|---|---|---|
| `getent hosts` | Resolve via NSS | rc + mapping |
| `getent ahosts` | All families | v4/v6 |
| `awk '{print $1}'` | Extract IP | first field |
| `grep '^hosts:'` | NSS order | files vs dns |

---

## 🧰 LAB-WIDE SETUP

**In plain English:** Make the sandbox and ensure a test mapping exists to verify.

> Run this block **once** before Task 1. It re-adds a marked entry if a prior teardown removed it.

```bash
export LAB_ROOT=/tmp/lab-37
mkdir -p "$LAB_ROOT"
getent hosts verify.lab.local >/dev/null 2>&1 || \
  echo '198.51.100.7  verify.lab.local verify  # LAB-37 VERIFY' | sudo tee -a /etc/hosts >/dev/null
echo "ready"
echo "exit was: $?"
```

**Expected output:**

```
ready
exit was: 0
```

---

## TASK 1 of 2 — Prove resolution and exact IP

**In plain English:** We assert the name resolves, then that the IP is exactly right.

---

### Step 1 of 2 — Assert the name resolves

**In plain English:** We use `getent`'s exit code as a resolvable/not signal.

```bash
if getent hosts verify.lab.local >/dev/null; then
  echo "PASS: name resolves"
else
  echo "FAIL: name does not resolve"
fi
```

**Expected output:**

```
PASS: name resolves
```

**Line-by-line breakdown:**

- `getent hosts verify.lab.local >/dev/null` → Exit 0 means the NSS path resolved the name.
- The `if` branches purely on that exit code.

**New words in this step:**

- **resolvable check** — using `getent`'s exit status as a yes/no.

---

### Step 2 of 2 — Assert the exact IP

**In plain English:** We extract the resolved IP and require it to match.

```bash
IP=$(getent hosts verify.lab.local | awk '{print $1}')
echo "resolved: $IP"
[ "$IP" = "198.51.100.7" ] && echo "PASS: exact IP" || echo "FAIL: got '$IP'"
```

**Expected output:**

```
resolved: 198.51.100.7
PASS: exact IP
```

**Line-by-line breakdown:**

- `getent hosts ... | awk '{print $1}'` → The first field of the mapping is the resolved IP.
- `[ "$IP" = "198.51.100.7" ]` → Strict equality — presence isn't enough; the value must be right.

**New words in this step:**

- **exact-IP assertion** — verifying the resolved value, not just that it resolved.

---

### Concept card (Task 1)

| Concept | What it does | Exam trap |
|---|---|---|
| `getent` rc | resolvable? | 0 = yes |
| IP extract | first field | `awk '{print $1}'` |
| exact compare | right value | presence ≠ correct |

---

### Troubleshoot (Task 1)

| Symptom | Likely cause | Fix |
|---|---|---|
| FAIL resolve | Entry missing | Re-run setup |
| Wrong IP | Typo in entry | Fix `/etc/hosts` |

---

## TASK 2 of 2 — Prove family and precedence

**In plain English:** We check the address family and that files beat DNS.

---

### Step 1 of 2 — Inspect the address family

**In plain English:** We confirm the entry resolves IPv4 (and note if any IPv6).

```bash
getent ahosts verify.lab.local
echo "---"
getent ahosts verify.lab.local | awk '{print $1}' | grep -q '198.51.100.7' && echo "PASS: IPv4 present"
```

**Expected output:**

```
198.51.100.7    STREAM verify.lab.local
198.51.100.7    DGRAM
198.51.100.7    RAW
---
PASS: IPv4 present
```

**Line-by-line breakdown:**

- `getent ahosts ...` → Shows every socket-type/family the name resolves to.
- `grep -q '198.51.100.7'` → Confirms the expected IPv4 appears among them.

**New words in this step:**

- **`getent ahosts`** — resolve showing all address families/socket types.

---

### Step 2 of 2 — Prove files-before-DNS precedence

**In plain English:** We show the name resolves to the file's value, which DNS would never return.

```bash
grep '^hosts:' /etc/nsswitch.conf | grep -q 'files.*dns' && echo "order: files before dns"
# 198.51.100.0/24 is TEST-NET-2: no public DNS returns this for our name,
# so a successful resolution proves /etc/hosts (files) answered first.
getent hosts verify.lab.local | awk '{print "/etc/hosts answered:", $1}'
```

**Expected output:**

```
order: files before dns
/etc/hosts answered: 198.51.100.7
```

**Line-by-line breakdown:**

- `grep '^hosts:' ... | grep -q 'files.*dns'` → Confirms `files` precedes `dns` in NSS order.
- Resolving a TEST-NET name (which no public DNS serves) proves `/etc/hosts` answered first.

**New words in this step:**

- **precedence proof** — demonstrating the hosts file wins over DNS.

---

### Concept card (Task 2)

| Concept | What it does | Exam trap |
|---|---|---|
| `ahosts` | families | v4 vs v6 |
| NSS order | files first | precedence |
| TEST-NET trick | isolates source | proves files won |

---

### Troubleshoot (Task 2)

| Symptom | Likely cause | Fix |
|---|---|---|
| Unexpected IPv6 | AAAA entry | Remove/adjust entry |
| dns before files | Custom NSS | Reorder `hosts:` line |

---

## ✅ Lab Checklist

- [ ] Task 1 · Step 1 — Assert the name resolves
- [ ] Task 1 · Step 2 — Assert the exact IP
- [ ] Task 2 · Step 1 — Inspect the address family
- [ ] Task 2 · Step 2 — Prove files-before-DNS precedence
- [ ] Every 🎯 Focus Coverage row (Anchor + NEW) mapped to a step
- [ ] 🧹 Teardown run — `/etc/hosts` entry removed + sandbox cleared

---

## 🧹 Teardown

**In plain English:** Remove the verify entry and clear the sandbox.

> Removes the marked verify line this lab may have added. `lab_teardown.sh` clears the sandbox root.

```bash
sudo sed -i '/# LAB-37 VERIFY/d' /etc/hosts
cd /tmp
bash lab_teardown.sh "$LAB_ROOT"     # = /tmp/lab-37
```

**Expected output:**

```
✅ Removed /tmp/lab-37 — lab workspace is clean.
```

---

## ⚠️ Common Pitfalls

| Mistake | Symptom | Fix |
|---|---|---|
| Presence-only check | Wrong IP passes | Assert exact value |
| Using `dig`/`nslookup` | Bypasses hosts file | Use `getent` |
| Assuming files-first | Custom NSS order | Verify `hosts:` line |

---

## 📌 Exam Strategy

Prove resolution four ways: exit code (resolvable), exact IP, address family (`ahosts`), and files-before-dns precedence. The exact-IP and precedence checks are what separate a real verification from a superficial one.

- `getent hosts` rc = resolvable; `awk '{print $1}'` = the value.
- `getent ahosts` reveals the families.
- A resolvable TEST-NET name proves `/etc/hosts` won over DNS.

---

## 🔗 Related Labs

- [Lab 37a — Configuring Local Host Resolution (RHCSA)](../lab-37a-etc-hosts-resolution-rhcsa/) — the entries these checks verify
- [Lab 37b — Configuring Local Host Resolution (Ansible)](../lab-37b-etc-hosts-resolution-ansible/) — managing the block idempotently
- [Lab 38c — Configuring DNS Servers (Verify)](../lab-38c-resolv-conf-dns-verify/) — verifying the DNS path that hosts overrides

---

## 👤 Author

**Kelvin R. Tobias**  
[kelvinintech.com](https://kelvinintech.com) · [GitHub](https://github.com/kelvintechnical) · [LinkedIn](https://www.linkedin.com/in/kelvin-r-tobias-211949219)
