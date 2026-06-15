# Lab 34c: Inspecting Listening Sockets (Verify) — prove port state

**Series:** linux-ops-mastery — Networking · **Lab 34c of the Novice → RHCA path**  
**Certifications covered:** RHCSA EX200 (evidence-based service checks), SRE (port audits, exposure review)  
**Prerequisite:** [Lab 34b](../lab-34b-ss-listening-sockets-ansible/) completed  
**Time Estimate:** 20–30 minutes  
**Difficulty:** Beginner → Intermediate

---

## 🎯 Today's Focus Coverage

> Stay on-subject via the ANCHOR rows; expand vocabulary via the NEW rows. Every row is exercised by a STEP below.

**⚓ Anchor — already learned (on-topic reuse)**

| # | Command / switch | Covered by |
|---|---|---|
| A1 | `ss -tuln` | _Task 1 · Step 1_ |
| A2 | `grep -q` | _Task 1 · Step 1_ |

**🆕 NEW this lab — introduced for the first time** (minimum 3)

| # | Command / switch | First taught in | Covered by |
|---|---|---|---|
| N1 | `ss -H` (no header) + count | Task 1 · Step 1 | _Task 1 · Step 1_ |
| N2 | absence assertion (`! grep`) | Task 1 · Step 2 | _Task 1 · Step 2_ |
| N3 | bind-scope check (`0.0.0.0` vs `127`) | Task 2 · Step 1 | _Task 2 · Step 1_ |
| N4 | owner check (`ss -p`) | Task 2 · Step 2 | _Task 2 · Step 2_ |

---

## 🎯 Objective

Turn socket inspection into pass/fail evidence. You will assert a required port *is* listening, assert a forbidden port is *not*, verify the bind scope (exposed on all interfaces vs loopback-only), and confirm the expected process owns a port. These are the checks behind a port/exposure audit.

---

## 🧠 Concept

A socket audit answers three questions provably: **presence** (is the port listening?), **exposure** (bound to `0.0.0.0`/`[::]` = all interfaces, or `127.0.0.1` = loopback only?), and **ownership** (which process holds it?). Use `ss -Htuln` (`-H` strips the header) piped to `grep -q ':PORT '` for presence, an inverted test (`! ... grep -q`) for required-absence, a `grep -q '0.0.0.0:PORT'` for exposure scope, and `ss -tulnp | grep` for ownership. Each is an extract-then-assert producing PASS/FAIL — exactly what a security review or exam grader expects. Exposure is the subtle one: a service listening on `0.0.0.0` is reachable from the network; on `127.0.0.1` it is local-only.

```
ss -Htuln | grep -q ':22 '          → presence (PASS if exit 0)
! ss -Htuln | grep -q ':23 '        → required absence (telnet off)
ss -Htuln | grep -q '127.0.0.1:25'  → loopback-only exposure
ss -Htulnp | grep ':22 '            → owning process
```

> **Why this matters:** "Required service up, forbidden service off, sensitive service loopback-only, owned by the right process" is a real security/operational checklist. `ss` + `grep -q` makes each item auditable.

---

## 📚 Command Reference

| Command | Purpose | Notes |
|---|---|---|
| `ss -H` | No header | clean counting |
| `grep -q ':PORT '` | Presence | exit code |
| `! ... grep -q` | Required absence | inverted |
| `grep '0.0.0.0:'` | Exposure scope | all-interfaces |
| `ss -p` | Owner | needs root |

---

## 🧰 LAB-WIDE SETUP

**In plain English:** Make the sandbox; socket checks run live.

> Run this block **once** before Task 1.

```bash
export LAB_ROOT=/tmp/lab-34
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

## TASK 1 of 2 — Presence and absence

**In plain English:** We assert a required port is up and a forbidden port is down.

---

### Step 1 of 2 — Assert a required port is listening

**In plain English:** We confirm SSH (22) is in the listener list.

```bash
if ss -Htuln | grep -q ':22 '; then
  echo "PASS: port 22 listening"
else
  echo "FAIL: port 22 not listening"
fi
```

**Expected output:**

```
PASS: port 22 listening
```

**Line-by-line breakdown:**

- `ss -Htuln` → Listeners without the header line, so `grep` sees only data.
- `grep -q ':22 '` → Silent presence test; the trailing space avoids matching `:2200`.

**New words in this step:**

- **`-H`** — suppress the header row for clean parsing/counting.

---

### Step 2 of 2 — Assert a forbidden port is absent

**In plain English:** We require that an insecure service (telnet, 23) is NOT listening.

```bash
if ! ss -Htuln | grep -q ':23 '; then
  echo "PASS: telnet (23) not listening"
else
  echo "FAIL: telnet is listening — disable it"
fi
```

**Expected output:**

```
PASS: telnet (23) not listening
```

**Line-by-line breakdown:**

- `! ... grep -q ':23 '` → Inverts the test: pass when port 23 is *absent*.

**New words in this step:**

- **required absence** — asserting a forbidden port is not open.

---

### Concept card (Task 1)

| Concept | What it does | Exam trap |
|---|---|---|
| presence | required up | trailing space |
| absence (`!`) | forbidden off | invert exit code |
| `-H` | clean output | easier matching |

---

### Troubleshoot (Task 1)

| Symptom | Likely cause | Fix |
|---|---|---|
| Matches `:2200` | No trailing space | Use `':22 '` |
| Absence fails | Service running | Stop/disable it |

---

## TASK 2 of 2 — Exposure and ownership

**In plain English:** We check the bind scope and the owning process.

---

### Step 1 of 2 — Verify the bind scope

**In plain English:** We confirm whether a service is exposed on all interfaces or loopback-only.

```bash
ss -Htuln | awk '{print $5}' | sort -u | head
echo "---"
if ss -Htuln | grep -qE '0\.0\.0\.0:22|\[::\]:22'; then
  echo "INFO: SSH is exposed on all interfaces"
else
  echo "INFO: SSH not on all interfaces (loopback/specific only)"
fi
```

**Expected output:**

```
0.0.0.0:22
127.0.0.1:25
[::]:22
---
INFO: SSH is exposed on all interfaces
```

**Line-by-line breakdown:**

- `awk '{print $5}' | sort -u` → The Local Address:Port column — the distinct bind endpoints.
- `grep -qE '0\.0\.0\.0:22|\[::\]:22'` → All-interfaces exposure check for SSH (informational, not a failure).

**New words in this step:**

- **bind scope** — `0.0.0.0`/`[::]` (all interfaces) vs `127.0.0.1` (loopback only).

---

### Step 2 of 2 — Confirm the owning process

**In plain English:** We verify the expected program owns the port.

```bash
OWNER=$(ss -Htulnp 2>/dev/null | grep ':22 ' | grep -oP 'users:\(\("\K[^"]+' | head -n1)
echo "port 22 owner: ${OWNER:-unknown}"
[ "$OWNER" = "sshd" ] && echo "PASS: owned by sshd" || echo "INFO: owner is ${OWNER:-unknown}"
```

**Expected output:**

```
port 22 owner: sshd
PASS: owned by sshd
```

**Line-by-line breakdown:**

- `ss -Htulnp | grep ':22 '` → The port-22 listener line including the process info (root needed).
- `grep -oP 'users:\(\("\K[^"]+'` → Extract just the process name from `users:(("sshd",...))`.

**New words in this step:**

- **ownership check** — confirming the expected process holds the port.

---

### Concept card (Task 2)

| Concept | What it does | Exam trap |
|---|---|---|
| bind scope | exposure | all vs loopback |
| owner extract | process name | needs root |
| `\K` (PCRE) | reset match start | keep only owner |

---

### Troubleshoot (Task 2)

| Symptom | Likely cause | Fix |
|---|---|---|
| Owner unknown | Not root | Run with `sudo` |
| Wrong exposure | Service config | Edit `ListenAddress` |

---

## ✅ Lab Checklist

- [ ] Task 1 · Step 1 — Assert a required port is listening
- [ ] Task 1 · Step 2 — Assert a forbidden port is absent
- [ ] Task 2 · Step 1 — Verify the bind scope
- [ ] Task 2 · Step 2 — Confirm the owning process
- [ ] Every 🎯 Focus Coverage row (Anchor + NEW) mapped to a step
- [ ] 🧹 Teardown run — sandbox + any system state removed

---

## 🧹 Teardown

**In plain English:** Delete everything this lab created so the box is clean for the next run.

> Run this after you've verified the lab. `lab_teardown.sh` safely removes the single sandbox root — it refuses to touch `/`, `$HOME`, or any protected path. This lab changed **no** system state.

```bash
cd /tmp
bash lab_teardown.sh "$LAB_ROOT"     # = /tmp/lab-34
```

**Expected output:**

```
✅ Removed /tmp/lab-34 — lab workspace is clean.
```

---

## ⚠️ Common Pitfalls

| Mistake | Symptom | Fix |
|---|---|---|
| No trailing space in pattern | Matches `:2200` etc. | Use `':22 '` |
| Confusing exposure | Wrong risk call | `0.0.0.0` ≠ `127.0.0.1` |
| Owner check without root | Empty owner | Use `sudo` |

---

## 📌 Exam Strategy

A socket audit checks presence, absence, exposure, and ownership — each a `grep -q` exit code over `ss -H` output. The exposure check (`0.0.0.0` vs `127.0.0.1`) is the high-value security item.

- Trailing space (`':22 '`) prevents false matches.
- Invert with `!` for required-absence checks.
- Exposure scope = real security signal.

---

## 🔗 Related Labs

- [Lab 34a — Inspecting Listening Sockets (RHCSA)](../lab-34a-ss-listening-sockets-rhcsa/) — the `ss` commands these checks verify
- [Lab 34b — Inspecting Listening Sockets (Ansible)](../lab-34b-ss-listening-sockets-ansible/) — port-state checks in plays
- [Lab 39a — Configure SSH and Key-Based Auth (RHCSA)](../lab-39a-ssh-key-auth-rhcsa/) — securing the SSH service you audited here

---

## 👤 Author

**Kelvin R. Tobias**  
[kelvinintech.com](https://kelvinintech.com) · [GitHub](https://github.com/kelvintechnical) · [LinkedIn](https://www.linkedin.com/in/kelvin-r-tobias-211949219)
