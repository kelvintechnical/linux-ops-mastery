# Lab 33c: Display IP and Routing Info (Verify) — prove addresses & routes

**Series:** linux-ops-mastery — Networking · **Lab 33c of the Novice → RHCA path**  
**Certifications covered:** RHCSA EX200 (evidence-based network checks), SRE (config drift detection)  
**Prerequisite:** [Lab 33b](../lab-33b-ip-addr-route-show-ansible/) completed  
**Time Estimate:** 20–30 minutes  
**Difficulty:** Beginner → Intermediate

---

## 🎯 Today's Focus Coverage

> Stay on-subject via the ANCHOR rows; expand vocabulary via the NEW rows. Every row is exercised by a STEP below.

**⚓ Anchor — already learned (on-topic reuse)**

| # | Command / switch | Covered by |
|---|---|---|
| A1 | `ip addr` | _Task 1 · Step 1_ |
| A2 | `ip route` | _Task 2 · Step 1_ |

**🆕 NEW this lab — introduced for the first time** (minimum 3)

| # | Command / switch | First taught in | Covered by |
|---|---|---|---|
| N1 | `ip -br addr \| grep -q` | Task 1 · Step 1 | _Task 1 · Step 1_ |
| N2 | address present assertion | Task 1 · Step 2 | _Task 1 · Step 2_ |
| N3 | default-route assertion | Task 2 · Step 1 | _Task 2 · Step 1_ |
| N4 | `ip route get` device check | Task 2 · Step 2 | _Task 2 · Step 2_ |

---

## 🎯 Objective

Turn network inspection into pass/fail checks. You will assert that a specific interface is UP, that an expected address is assigned, that a default route exists (or correctly does not on isolated hosts), and that `ip route get` selects the expected device for a destination. These checks catch config drift objectively.

---

## 🧠 Concept

Verification reduces `ip` output to booleans. `ip -br addr show dev DEV` plus `grep -q` proves an interface exists and is UP. Grepping the address line proves the *expected* IP is assigned. `ip route` piped to `grep -q '^default'` proves a gateway is configured. `ip route get DEST` plus a field check proves the kernel routes a destination through the expected device. Each check captures output, tests a condition, and prints PASS/FAIL — exactly what a monitoring probe or exam grader needs.

```
ip -br addr show dev lo | grep -q UNKNOWN/UP    → interface state
ip -br addr show dev lo | grep -q 127.0.0.1     → address present
ip route get 127.0.0.1 | grep -q 'dev lo'       → route to expected dev
echo $?                                          → 0 PASS / non-zero FAIL
```

> **Why this matters:** "The interface is UP with the right IP and a working default route" must be provable, not assumed. These checks make network state auditable.

---

## 📚 Command Reference

| Command | Purpose | Notes |
|---|---|---|
| `ip -br addr show dev` | Iface + state | grep the state |
| `grep -q` | Silent assert | sets exit code |
| `ip route` | Routing table | check `default` |
| `ip route get` | Route decision | check `dev` |

---

## 🧰 LAB-WIDE SETUP

**In plain English:** Make the sandbox; checks run against the loopback for determinism.

> Run this block **once** before Task 1.

```bash
export LAB_ROOT=/tmp/lab-33
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

## TASK 1 of 2 — Prove interface and address

**In plain English:** We assert the interface is up and the expected IP is present.

---

### Step 1 of 2 — Assert the interface exists and is up

**In plain English:** We confirm `lo` is present and in an operational state.

```bash
if ip -br addr show dev lo | grep -qE 'UP|UNKNOWN'; then
  echo "PASS: lo is operational"
else
  echo "FAIL: lo not up"
fi
```

**Expected output:**

```
PASS: lo is operational
```

**Line-by-line breakdown:**

- `ip -br addr show dev lo` → Brief status of the loopback interface.
- `grep -qE 'UP|UNKNOWN'` → Loopback reports `UNKNOWN` state but is usable; either counts as operational.

**New words in this step:**

- **operational state** — `UP`/`UNKNOWN` mean usable; `DOWN` does not.

---

### Step 2 of 2 — Assert the expected address

**In plain English:** We confirm the expected IPv4 is assigned to the interface.

```bash
if ip -br addr show dev lo | grep -q '127.0.0.1'; then
  echo "PASS: 127.0.0.1 present"
else
  echo "FAIL: address missing"
fi
```

**Expected output:**

```
PASS: 127.0.0.1 present
```

**Line-by-line breakdown:**

- `grep -q '127.0.0.1'` → Silent test for the expected address; exit 0 = present.

**New words in this step:**

- **address assertion** — confirming a specific IP is bound to an interface.

---

### Concept card (Task 1)

| Concept | What it does | Exam trap |
|---|---|---|
| state grep | iface up? | `lo` is `UNKNOWN` |
| address grep | IP present? | exact match |
| `grep -q` | silent | exit code only |

---

### Troubleshoot (Task 1)

| Symptom | Likely cause | Fix |
|---|---|---|
| FAIL on `lo` UP | Matched only `UP` | Include `UNKNOWN` |
| Address FAIL | Not assigned | Configure with `nmcli` |

---

## TASK 2 of 2 — Prove routing

**In plain English:** We assert a default route exists and route selection is correct.

---

### Step 1 of 2 — Assert a default route (or note its absence)

**In plain English:** We check whether a default gateway is configured and report clearly.

```bash
if ip route | grep -q '^default'; then
  echo "PASS: default route present -> $(ip route | awk '/^default/{print $3; exit}')"
else
  echo "INFO: no default route (isolated host)"
fi
```

**Expected output:**

```
PASS: default route present -> 192.168.x.1
```

> On an isolated host with no gateway you'll see `INFO: no default route (isolated host)` instead — both are valid, documented outcomes.

**Line-by-line breakdown:**

- `grep -q '^default'` → Tests for a default route line.
- `awk '/^default/{print $3}'` → Extracts the gateway when present.

**New words in this step:**

- **default-route assertion** — proving (or explicitly noting the absence of) a gateway.

---

### Step 2 of 2 — Assert route selection with `ip route get`

**In plain English:** We confirm the kernel routes the loopback target via `lo`.

```bash
if ip route get 127.0.0.1 | grep -q 'dev lo'; then
  echo "PASS: 127.0.0.1 routes via lo"
else
  echo "FAIL: unexpected route device"
fi
```

**Expected output:**

```
PASS: 127.0.0.1 routes via lo
```

**Line-by-line breakdown:**

- `ip route get 127.0.0.1` → The kernel's routing decision for that destination.
- `grep -q 'dev lo'` → Confirms it selected the expected device.

**New words in this step:**

- **route selection check** — proving the kernel picks the expected egress device.

---

### Concept card (Task 2)

| Concept | What it does | Exam trap |
|---|---|---|
| default grep | gateway present? | absence can be valid |
| `route get` | decision | check `dev` field |
| clear reporting | PASS/INFO/FAIL | distinguish states |

---

### Troubleshoot (Task 2)

| Symptom | Likely cause | Fix |
|---|---|---|
| Unexpected FAIL | No gateway on host | Treat as INFO if isolated |
| Wrong dev | Routing misconfig | Review routes/metrics |

---

## ✅ Lab Checklist

- [ ] Task 1 · Step 1 — Assert the interface exists and is up
- [ ] Task 1 · Step 2 — Assert the expected address
- [ ] Task 2 · Step 1 — Assert a default route (or note its absence)
- [ ] Task 2 · Step 2 — Assert route selection with `ip route get`
- [ ] Every 🎯 Focus Coverage row (Anchor + NEW) mapped to a step
- [ ] 🧹 Teardown run — sandbox + any system state removed

---

## 🧹 Teardown

**In plain English:** Delete everything this lab created so the box is clean for the next run.

> Run this after you've verified the lab. `lab_teardown.sh` safely removes the single sandbox root — it refuses to touch `/`, `$HOME`, or any protected path. This lab changed **no** system state.

```bash
cd /tmp
bash lab_teardown.sh "$LAB_ROOT"     # = /tmp/lab-33
```

**Expected output:**

```
✅ Removed /tmp/lab-33 — lab workspace is clean.
```

---

## ⚠️ Common Pitfalls

| Mistake | Symptom | Fix |
|---|---|---|
| Matching only `UP` | `lo` fails | Accept `UNKNOWN` too |
| Assuming a gateway exists | False FAIL | Handle isolated hosts |
| Reading wrong route field | Wrong gateway | `default` line, field 3 |

---

## 📌 Exam Strategy

Reduce each network claim to a `grep -q` exit code: interface up, address present, default route present, route selection correct. Distinguish a legitimately isolated host (no gateway) from a real failure.

- `grep -q` turns `ip` output into PASS/FAIL.
- `lo` is `UNKNOWN`, not `UP` — match both.
- `ip route get` proves which device is chosen.

---

## 🔗 Related Labs

- [Lab 33a — Display IP and Routing Info (RHCSA)](../lab-33a-ip-addr-route-show-rhcsa/) — the commands these checks verify
- [Lab 33b — Display IP and Routing Info (Ansible)](../lab-33b-ip-addr-route-show-ansible/) — facts and JSON parsing
- [Lab 34a — Inspecting Listening Sockets (RHCSA)](../lab-34a-ss-listening-sockets-rhcsa/) — which services are bound to those addresses

---

## 👤 Author

**Kelvin R. Tobias**  
[kelvinintech.com](https://kelvinintech.com) · [GitHub](https://github.com/kelvintechnical) · [LinkedIn](https://www.linkedin.com/in/kelvin-r-tobias-211949219)
