# Lab 36c: Command-Line Network Config (Verify) — prove `nmcli` settings

**Series:** linux-ops-mastery — Networking · **Lab 36c of the Novice → RHCA path**  
**Certifications covered:** RHCSA EX200 (verify network config), SRE (config drift detection)  
**Prerequisite:** [Lab 36b](../lab-36b-nmcli-cli-config-ansible/) completed  
**Time Estimate:** 20–30 minutes  
**Difficulty:** Beginner → Intermediate

---

## 🎯 Today's Focus Coverage

> Stay on-subject via the ANCHOR rows; expand vocabulary via the NEW rows. Every row is exercised by a STEP below.

**⚓ Anchor — already learned (on-topic reuse)**

| # | Command / switch | Covered by |
|---|---|---|
| A1 | `nmcli -g` field read | _Task 1 · Step 1_ |
| A2 | `ip addr` live check | _Task 2 · Step 2_ |

**🆕 NEW this lab — introduced for the first time** (minimum 3)

| # | Command / switch | First taught in | Covered by |
|---|---|---|---|
| N1 | method assertion | Task 1 · Step 1 | _Task 1 · Step 1_ |
| N2 | DNS-list membership check | Task 1 · Step 2 | _Task 1 · Step 2_ |
| N3 | active-state check (`GENERAL.STATE`) | Task 2 · Step 1 | _Task 2 · Step 1_ |
| N4 | stored-vs-live address compare | Task 2 · Step 2 | _Task 2 · Step 2_ |

---

## 🎯 Objective

Prove an `nmcli`-built profile is correct and applied. You will assert the addressing method, confirm a specific DNS server is in the list, check the connection is active, and verify the live interface address matches the stored profile. These are the objective checks behind any network change.

> **Setup note:** Re-create the `lab-cli` dummy profile (as in Lab 36a setup) before these checks if it was removed by Lab 36b's teardown.

---

## 🧠 Concept

Verifying `nmcli` config means reducing each property to a pass/fail. `nmcli -g FIELD con show NAME` returns a single field cleanly — perfect for `[ "$x" = ... ]` checks on `ipv4.method`, or for membership tests on the comma-separated `ipv4.dns` list. Active state comes from `nmcli -g GENERAL.STATE con show NAME` (or `nmcli con show --active`). The decisive check, as always, is **stored vs live**: compare the profile's `ipv4.addresses` against `ip addr`'s actual address on the device — a mismatch means the profile was edited but not activated. Each check captures a value, tests it, prints PASS/FAIL.

```
nmcli -g ipv4.method con show lab-cli            → manual?
nmcli -g ipv4.dns con show lab-cli | grep -q X   → DNS member?
nmcli -g GENERAL.STATE con show lab-cli          → activated?
ip -4 -br addr show dev dummy0                    → live == stored?
```

> **Why this matters:** A profile can be perfectly configured yet inactive. Checking method, DNS membership, active state, and stored-vs-live address is the full proof that a network change is both correct and in effect.

---

## 📚 Command Reference

| Command | Purpose | Notes |
|---|---|---|
| `nmcli -g ipv4.method` | Method | manual/auto |
| `nmcli -g ipv4.dns` | DNS list | comma-separated |
| `nmcli -g GENERAL.STATE` | Active state | activated? |
| `nmcli con show --active` | Active profiles | quick list |
| `ip -4 -br addr show dev` | Live address | compare |

---

## 🧰 LAB-WIDE SETUP

**In plain English:** Make the sandbox and ensure a profile exists to verify.

> Run this block **once** before Task 1. It re-creates `lab-cli` if a prior teardown removed it.

```bash
export LAB_ROOT=/tmp/lab-36
mkdir -p "$LAB_ROOT"
sudo modprobe dummy 2>/dev/null || true
nmcli con show lab-cli >/dev/null 2>&1 || sudo nmcli con add type dummy ifname dummy0 \
  con-name lab-cli ipv4.method manual ipv4.addresses 10.66.66.2/24 ipv4.dns 10.66.66.53 2>/dev/null
sudo nmcli con up lab-cli >/dev/null 2>&1
echo "ready"
echo "exit was: $?"
```

**Expected output:**

```
ready
exit was: 0
```

---

## TASK 1 of 2 — Prove method and DNS

**In plain English:** We assert the method is manual and a DNS server is present.

---

### Step 1 of 2 — Assert the addressing method

**In plain English:** We confirm the profile uses manual (static) addressing.

```bash
M=$(nmcli -g ipv4.method con show lab-cli 2>/dev/null)
echo "method: $M"
[ "$M" = "manual" ] && echo "PASS: static addressing" || echo "FAIL: method is '$M'"
```

**Expected output:**

```
method: manual
PASS: static addressing
```

**Line-by-line breakdown:**

- `nmcli -g ipv4.method con show lab-cli` → Reads just the method field.
- `[ "$M" = "manual" ]` → Pass only for static addressing.

**New words in this step:**

- **method assertion** — proving static vs DHCP configuration.

---

### Step 2 of 2 — Assert a DNS server is in the list

**In plain English:** We check the comma-separated DNS list for a required server.

```bash
if nmcli -g ipv4.dns con show lab-cli 2>/dev/null | tr ',' '\n' | grep -qx '10.66.66.53'; then
  echo "PASS: 10.66.66.53 in DNS list"
else
  echo "FAIL: required DNS server missing"
fi
```

**Expected output:**

```
PASS: 10.66.66.53 in DNS list
```

**Line-by-line breakdown:**

- `nmcli -g ipv4.dns ... | tr ',' '\n'` → Split the comma-separated list into one server per line.
- `grep -qx '10.66.66.53'` → Exact-line match so `10.66.66.5` can't match `10.66.66.53` partially.

**New words in this step:**

- **list membership check** — confirming a value is present in a multi-value property.

---

### Concept card (Task 1)

| Concept | What it does | Exam trap |
|---|---|---|
| `-g method` | static/DHCP | exact compare |
| split DNS | per-server | `tr ',' '\n'` |
| `grep -qx` | exact line | avoids substring match |

---

### Troubleshoot (Task 1)

| Symptom | Likely cause | Fix |
|---|---|---|
| Empty method | Profile missing | Re-run setup |
| DNS FAIL | Replaced not appended | Re-add with `+ipv4.dns` |

---

## TASK 2 of 2 — Prove active and live state

**In plain English:** We confirm the profile is active and live matches stored.

---

### Step 1 of 2 — Assert the connection is active

**In plain English:** We check the profile's general state is activated.

```bash
S=$(nmcli -g GENERAL.STATE con show lab-cli 2>/dev/null)
echo "state: ${S:-inactive}"
echo "$S" | grep -q 'activated' && echo "PASS: connection active" || echo "FAIL: not activated (nmcli con up lab-cli)"
```

**Expected output:**

```
state: activated
PASS: connection active
```

**Line-by-line breakdown:**

- `nmcli -g GENERAL.STATE con show lab-cli` → The runtime activation state of the profile.
- `grep -q 'activated'` → Pass only when the profile is currently active.

**New words in this step:**

- **activation state** — whether a saved profile is currently applied.

---

### Step 2 of 2 — Confirm live matches stored

**In plain English:** We compare the live interface address to the stored profile.

```bash
STORED=$(nmcli -g ipv4.addresses con show lab-cli 2>/dev/null)
LIVE=$(ip -4 -br addr show dev dummy0 2>/dev/null | awk '{print $3}')
echo "stored: $STORED  live: $LIVE"
[ "${STORED%% *}" = "$LIVE" ] && echo "PASS: live matches stored" || echo "FAIL: not applied"
```

**Expected output:**

```
stored: 10.66.66.2/24  live: 10.66.66.2/24
PASS: live matches stored
```

**Line-by-line breakdown:**

- `nmcli -g ipv4.addresses ...` vs `ip -4 -br addr show dev dummy0` → Stored profile address vs the address actually on the interface.
- `[ "${STORED%% *}" = "$LIVE" ]` → Equality catches the "saved but not activated" gap.

**New words in this step:**

- **stored-vs-live** — the on-disk profile must equal the applied address.

---

### Concept card (Task 2)

| Concept | What it does | Exam trap |
|---|---|---|
| `GENERAL.STATE` | active? | inactive ≠ misconfigured |
| live compare | applied? | saved ≠ active |
| `con up` | apply | needed after `mod` |

---

### Troubleshoot (Task 2)

| Symptom | Likely cause | Fix |
|---|---|---|
| state inactive | Not activated | `nmcli con up lab-cli` |
| Mismatch | Edited not applied | Reactivate the profile |

---

## ✅ Lab Checklist

- [ ] Task 1 · Step 1 — Assert the addressing method
- [ ] Task 1 · Step 2 — Assert a DNS server is in the list
- [ ] Task 2 · Step 1 — Assert the connection is active
- [ ] Task 2 · Step 2 — Confirm live matches stored
- [ ] Every 🎯 Focus Coverage row (Anchor + NEW) mapped to a step
- [ ] 🧹 Teardown run — sandbox + dummy profile removed

---

## 🧹 Teardown

**In plain English:** Remove the dummy connection and sandbox so the box is clean.

> Removes the `lab-cli` profile this lab (re)created and clears the sandbox root.

```bash
sudo nmcli con down lab-cli 2>/dev/null || true
sudo nmcli con delete lab-cli 2>/dev/null || true
cd /tmp
bash lab_teardown.sh "$LAB_ROOT"     # = /tmp/lab-36
```

**Expected output:**

```
Connection 'lab-cli' (...) successfully deleted.
✅ Removed /tmp/lab-36 — lab workspace is clean.
```

---

## ⚠️ Common Pitfalls

| Mistake | Symptom | Fix |
|---|---|---|
| Substring DNS match | False PASS | Use `grep -qx` |
| Only checking stored | Misses inactive | Check `GENERAL.STATE` |
| CIDR vs bare IP | False FAIL | Strip mask before compare |

---

## 📌 Exam Strategy

Prove method, DNS membership, activation, and stored-vs-live address — each a clean `nmcli -g` read plus a test. The two decisive checks are `GENERAL.STATE` (is it active?) and stored-vs-live (was it applied?).

- `nmcli -g` for single-field reads.
- `tr ',' '\n' | grep -qx` for exact DNS membership.
- Live must equal stored, or activation was skipped.

---

## 🔗 Related Labs

- [Lab 36a — Command-Line Network Config (RHCSA)](../lab-36a-nmcli-cli-config-rhcsa/) — the commands these checks verify
- [Lab 36b — Command-Line Network Config (Ansible)](../lab-36b-nmcli-cli-config-ansible/) — the declarative version
- [Lab 38a — Configuring DNS Servers (RHCSA)](../lab-38a-resolv-conf-dns-rhcsa/) — where the DNS list ends up resolving

---

## 👤 Author

**Kelvin R. Tobias**  
[kelvinintech.com](https://kelvinintech.com) · [GitHub](https://github.com/kelvintechnical) · [LinkedIn](https://www.linkedin.com/in/kelvin-r-tobias-211949219)
