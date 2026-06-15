# Lab 38c: Configuring DNS Servers (Verify) — prove the resolver

**Series:** linux-ops-mastery — Networking · **Lab 38c of the Novice → RHCA path**  
**Certifications covered:** RHCSA EX200 (evidence-based resolver checks), SRE (DNS config audits)  
**Prerequisite:** [Lab 38b](../lab-38b-resolv-conf-dns-ansible/) completed  
**Time Estimate:** 20–30 minutes  
**Difficulty:** Beginner → Intermediate

---

## 🎯 Today's Focus Coverage

> Stay on-subject via the ANCHOR rows; expand vocabulary via the NEW rows. Every row is exercised by a STEP below.

**⚓ Anchor — already learned (on-topic reuse)**

| # | Command / switch | Covered by |
|---|---|---|
| A1 | `nmcli -g ipv4.dns` | _Task 1 · Step 1_ |
| A2 | `grep -q` assertions | _Task 1 · Step 2_ |

**🆕 NEW this lab — introduced for the first time** (minimum 3)

| # | Command / switch | First taught in | Covered by |
|---|---|---|---|
| N1 | nameserver-in-file assertion | Task 1 · Step 1 | _Task 1 · Step 1_ |
| N2 | stored-vs-generated consistency | Task 1 · Step 2 | _Task 1 · Step 2_ |
| N3 | `search` directive check | Task 2 · Step 1 | _Task 2 · Step 1_ |
| N4 | server-count / order check | Task 2 · Step 2 | _Task 2 · Step 2_ |

---

## 🎯 Objective

Prove the resolver is configured as intended. You will assert the expected `nameserver` is in `/etc/resolv.conf`, confirm the generated file matches the connection's stored DNS, verify the `search` domain, and check the number/order of nameservers. These checks catch the "configured the profile but the file didn't update" gap.

> **Setup note:** Re-create the `lab-dns` dummy profile (as in Lab 38a setup) and activate it before these checks if a prior teardown removed it.

---

## 🧠 Concept

Resolver verification spans two layers that must agree: the **connection's stored DNS** (`nmcli -g ipv4.dns con show NAME`) and the **generated file** (`/etc/resolv.conf`'s `nameserver` lines). If they disagree, the profile was edited but not activated. Use `grep -q '^nameserver 10.88.88.53'` for presence, compare the stored list against the file for consistency, `grep -q '^search '` for the search domain, and `grep -c '^nameserver'` to count/cap servers (the resolver typically honors only the first few). The `^` anchors avoid matching comments. Each check is extract-then-assert producing PASS/FAIL — a real resolver audit.

```
grep -q '^nameserver 10.88.88.53' /etc/resolv.conf  → server present
nmcli -g ipv4.dns con show lab-dns  vs  resolv.conf  → stored == generated
grep -q '^search lab.local' /etc/resolv.conf         → search domain set
grep -c '^nameserver' /etc/resolv.conf               → server count
```

> **Why this matters:** "I set the DNS server" must mean "it's in the active resolv.conf". Proving stored == generated, plus search and count, is the difference between configured and actually-working resolution.

---

## 📚 Command Reference

| Command | Purpose | Notes |
|---|---|---|
| `grep -q '^nameserver'` | Server present | anchored |
| `nmcli -g ipv4.dns` | Stored servers | comma-list |
| `grep -q '^search'` | Search domain | name completion |
| `grep -c '^nameserver'` | Count servers | resolver caps it |

---

## 🧰 LAB-WIDE SETUP

**In plain English:** Make the sandbox and ensure the lab-dns profile is active.

> Run this block **once** before Task 1. It re-creates and activates `lab-dns` if needed.

```bash
export LAB_ROOT=/tmp/lab-38
mkdir -p "$LAB_ROOT"
sudo modprobe dummy 2>/dev/null || true
nmcli con show lab-dns >/dev/null 2>&1 || sudo nmcli con add type dummy ifname dummy0 \
  con-name lab-dns ipv4.method manual ipv4.addresses 10.88.88.2/24 \
  ipv4.dns "10.88.88.53 10.88.88.54" ipv4.dns-search "lab.local" 2>/dev/null
sudo nmcli con up lab-dns >/dev/null 2>&1
echo "ready"
echo "exit was: $?"
```

**Expected output:**

```
ready
exit was: 0
```

---

## TASK 1 of 2 — Prove the nameserver and consistency

**In plain English:** We assert the server is in the file and matches the profile.

---

### Step 1 of 2 — Assert the nameserver is present

**In plain English:** We confirm the expected DNS server is in `/etc/resolv.conf`.

```bash
if grep -q '^nameserver 10.88.88.53' /etc/resolv.conf; then
  echo "PASS: nameserver present"
else
  echo "FAIL: nameserver missing (activate lab-dns?)"
fi
```

**Expected output:**

```
PASS: nameserver present
```

**Line-by-line breakdown:**

- `grep -q '^nameserver 10.88.88.53'` → Anchored match for the active server line (`^` skips comments).

**New words in this step:**

- **anchored nameserver check** — `^nameserver` ensures a real directive, not a comment.

---

### Step 2 of 2 — Confirm stored matches generated

**In plain English:** We compare the profile's DNS to what's in the file.

```bash
STORED=$(nmcli -g ipv4.dns con show lab-dns 2>/dev/null | tr ',' '\n' | sort)
FILE=$(grep '^nameserver' /etc/resolv.conf | awk '{print $2}' | sort)
echo "stored: $STORED"
echo "file:   $FILE"
[ "$STORED" = "$FILE" ] && echo "PASS: stored matches generated" || echo "INFO: differ (extra system servers?)"
```

**Expected output:**

```
stored: 10.88.88.53
10.88.88.54
file:   10.88.88.53
10.88.88.54
PASS: stored matches generated
```

**Line-by-line breakdown:**

- `nmcli -g ipv4.dns ... | tr ',' '\n' | sort` → The profile's DNS servers, one per line, sorted.
- `grep '^nameserver' ... | awk '{print $2}' | sort` → The file's servers, sorted; comparing proves NM applied the profile.

**New words in this step:**

- **stored-vs-generated** — the connection's DNS must match resolv.conf.

---

### Concept card (Task 1)

| Concept | What it does | Exam trap |
|---|---|---|
| `^nameserver` | active line | not a comment |
| stored vs file | applied? | activation needed |
| sort + compare | order-agnostic | normalize first |

---

### Troubleshoot (Task 1)

| Symptom | Likely cause | Fix |
|---|---|---|
| nameserver FAIL | Not activated | `nmcli con up lab-dns` |
| Lists differ | Other connections add DNS | Expected on multi-conn hosts |

---

## TASK 2 of 2 — Prove search and count

**In plain English:** We verify the search domain and the nameserver count.

---

### Step 1 of 2 — Assert the search domain

**In plain English:** We confirm the search domain is configured.

```bash
if grep -qE '^search .*lab.local' /etc/resolv.conf; then
  echo "PASS: search domain set"
else
  echo "FAIL: search domain missing"
fi
```

**Expected output:**

```
PASS: search domain set
```

**Line-by-line breakdown:**

- `grep -qE '^search .*lab.local'` → Confirms the `search` directive includes our domain (`^` anchors the directive).

**New words in this step:**

- **search directive check** — proving bare-name completion is configured.

---

### Step 2 of 2 — Check the nameserver count

**In plain English:** We count nameservers and warn if it exceeds the resolver's limit.

```bash
N=$(grep -c '^nameserver' /etc/resolv.conf)
echo "nameservers: $N"
if [ "$N" -ge 1 ] && [ "$N" -le 3 ]; then
  echo "PASS: $N nameserver(s) (within resolver limit)"
else
  echo "WARN: $N nameservers (resolver typically uses first 3)"
fi
```

**Expected output:**

```
nameservers: 2
PASS: 2 nameserver(s) (within resolver limit)
```

**Line-by-line breakdown:**

- `grep -c '^nameserver'` → Counts active nameserver lines.
- The range check reflects that glibc's resolver only consults the first three (`MAXNS`).

**New words in this step:**

- **MAXNS limit** — the resolver honors only the first ~3 nameservers.

---

### Concept card (Task 2)

| Concept | What it does | Exam trap |
|---|---|---|
| `^search` | name completion | anchored |
| `grep -c` | count servers | first 3 used |
| MAXNS | resolver cap | extras ignored |

---

### Troubleshoot (Task 2)

| Symptom | Likely cause | Fix |
|---|---|---|
| search FAIL | `dns-search` unset | Set `ipv4.dns-search` |
| Too many servers | Extra ignored | Trim to ≤3 |

---

## ✅ Lab Checklist

- [ ] Task 1 · Step 1 — Assert the nameserver is present
- [ ] Task 1 · Step 2 — Confirm stored matches generated
- [ ] Task 2 · Step 1 — Assert the search domain
- [ ] Task 2 · Step 2 — Check the nameserver count
- [ ] Every 🎯 Focus Coverage row (Anchor + NEW) mapped to a step
- [ ] 🧹 Teardown run — dummy profile removed + sandbox cleared

---

## 🧹 Teardown

**In plain English:** Remove the dummy DNS profile and clear the sandbox.

> Removing the profile lets NM restore resolv.conf from your real connection.

```bash
sudo nmcli con down lab-dns 2>/dev/null || true
sudo nmcli con delete lab-dns 2>/dev/null || true
cd /tmp
bash lab_teardown.sh "$LAB_ROOT"     # = /tmp/lab-38
```

**Expected output:**

```
Connection 'lab-dns' (...) successfully deleted.
✅ Removed /tmp/lab-38 — lab workspace is clean.
```

---

## ⚠️ Common Pitfalls

| Mistake | Symptom | Fix |
|---|---|---|
| Unanchored grep | Matches comments | Use `^nameserver` |
| Checking only the file | Misses profile drift | Compare stored too |
| Ignoring MAXNS | 4th+ server "ignored" | Keep ≤3 |

---

## 📌 Exam Strategy

Prove the nameserver is present (anchored), the stored list matches the generated file, the search domain is set, and the count is within MAXNS. Stored-vs-generated is the decisive check — it proves the profile was actually activated.

- `^nameserver`/`^search` anchors avoid false matches.
- Compare `nmcli -g ipv4.dns` to resolv.conf's servers.
- Resolver uses only the first ~3 nameservers.

---

## 🔗 Related Labs

- [Lab 38a — Configuring DNS Servers (RHCSA)](../lab-38a-resolv-conf-dns-rhcsa/) — the config these checks verify
- [Lab 38b — Configuring DNS Servers (Ansible)](../lab-38b-resolv-conf-dns-ansible/) — the declarative version
- [Lab 37c — Configuring Local Host Resolution (Verify)](../lab-37c-etc-hosts-resolution-verify/) — `/etc/hosts`, checked before DNS

---

## 👤 Author

**Kelvin R. Tobias**  
[kelvinintech.com](https://kelvinintech.com) · [GitHub](https://github.com/kelvintechnical) · [LinkedIn](https://www.linkedin.com/in/kelvin-r-tobias-211949219)
