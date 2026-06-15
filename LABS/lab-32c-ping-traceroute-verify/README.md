# Lab 32c: Check Network Connectivity (Verify) — prove loss & latency

**Series:** linux-ops-mastery — Networking · **Lab 32c of the Novice → RHCA path**  
**Certifications covered:** RHCSA EX200 (evidence-based triage), SRE (SLO-style thresholds)  
**Prerequisite:** [Lab 32b](../lab-32b-ping-traceroute-ansible/) completed  
**Time Estimate:** 20–30 minutes  
**Difficulty:** Beginner → Intermediate

---

## 🎯 Today's Focus Coverage

> Stay on-subject via the ANCHOR rows; expand vocabulary via the NEW rows. Every row is exercised by a STEP below.

**⚓ Anchor — already learned (on-topic reuse)**

| # | Command / switch | Covered by |
|---|---|---|
| A1 | `ping -c` | _Task 1 · Step 1_ |
| A2 | exit code `$?` | _Task 1 · Step 1_ |

**🆕 NEW this lab — introduced for the first time** (minimum 3)

| # | Command / switch | First taught in | Covered by |
|---|---|---|---|
| N1 | loss extraction (`grep -oP`) | Task 1 · Step 1 | _Task 1 · Step 1_ |
| N2 | reachability gate (`if`) | Task 1 · Step 2 | _Task 1 · Step 2_ |
| N3 | rtt extraction + threshold | Task 2 · Step 1 | _Task 2 · Step 1_ |
| N4 | path-length check (`traceroute \| wc`) | Task 2 · Step 2 | _Task 2 · Step 2_ |

---

## 🎯 Objective

Turn "it pinged fine" into evidence. You will extract the packet-loss percentage and assert it is zero, gate on reachability via exit code, pull the average round-trip time and compare it to a threshold, and count `traceroute` hops to confirm a sane path length. These are objective, repeatable connectivity checks.

---

## 🧠 Concept

A trustworthy connectivity check produces a **number** and a **pass/fail**, not just scrolling output. `ping ... | grep -oP '\d+(?=% packet loss)'` extracts the loss percentage; compare it with `-eq 0`. The exit code of `ping -c` is the simplest reachability gate (`0` = reply). For latency, parse the `rtt min/avg/max` line and `cut` the average, then compare against a budget. For path sanity, count `traceroute` data lines with `wc -l`. Each check is a small extract-then-assert: capture a value, test it, print PASS/FAIL.

```
loss=$(ping -c3 H | grep -oP '\d+(?=% packet loss)')   → 0
ping -c1 -W2 H >/dev/null && echo UP || echo DOWN       → reachability
avg=$(ping -c3 H | awk -F/ '/rtt|round-trip/{print $5}')→ avg ms
hops=$(traceroute -n -m5 H | tail -n +2 | wc -l)        → path length
```

> **Why this matters:** Evidence-based triage — "0% loss, 0.04ms avg, 1 hop" — communicates clearly and can be scripted into monitoring. Vague "seems fine" cannot.

---

## 📚 Command Reference

| Command | Purpose | Notes |
|---|---|---|
| `grep -oP '\d+(?=% packet loss)'` | Extract loss % | PCRE lookahead |
| `ping -c1 && / \|\|` | Reachability gate | exit-code branch |
| `awk -F/ '{print $5}'` | Average rtt | split rtt line |
| `traceroute \| wc -l` | Hop count | path length |

---

## 🧰 LAB-WIDE SETUP

**In plain English:** Make the sandbox; we verify against the loopback for determinism.

> Run this block **once** before Task 1. `LAB_ROOT` holds saved results.

```bash
export LAB_ROOT=/tmp/lab-32
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

## TASK 1 of 2 — Prove loss and reachability

**In plain English:** We assert zero loss and gate on the exit code.

---

### Step 1 of 2 — Assert zero packet loss

**In plain English:** We extract the loss percentage and require it to be 0.

```bash
LOSS=$(ping -c3 -W2 127.0.0.1 | grep -oP '\d+(?=% packet loss)')
echo "loss%: $LOSS"
[ "$LOSS" -eq 0 ] && echo "PASS: no loss" || echo "FAIL: $LOSS% loss"
```

**Expected output:**

```
loss%: 0
PASS: no loss
```

**Line-by-line breakdown:**

- `grep -oP '\d+(?=% packet loss)'` → Capture just the number before "% packet loss".
- `[ "$LOSS" -eq 0 ]` → Pass only when loss is exactly zero.

**New words in this step:**

- **lookahead `(?=...)`** — match the digits *before* the literal text without including it.

---

### Step 2 of 2 — Reachability gate via exit code

**In plain English:** We treat `ping`'s exit status as the up/down signal.

```bash
if ping -c1 -W2 127.0.0.1 >/dev/null 2>&1; then
  echo "PASS: reachable"
else
  echo "FAIL: unreachable"
fi
```

**Expected output:**

```
PASS: reachable
```

**Line-by-line breakdown:**

- `ping -c1 -W2 ... >/dev/null` → One quick probe, output discarded.
- `if ...; then` → Exit 0 (reply) means reachable; non-zero means down.

**New words in this step:**

- **reachability gate** — branching on `ping`'s exit code.

---

### Concept card (Task 1)

| Concept | What it does | Exam trap |
|---|---|---|
| loss extract | quantifies drops | parse exact field |
| `-eq 0` | strict pass | any loss = fail |
| exit gate | up/down | non-zero = down |

---

### Troubleshoot (Task 1)

| Symptom | Likely cause | Fix |
|---|---|---|
| Empty `$LOSS` | Output format/locale | Check the summary line |
| Always FAIL | Host down/firewall | Verify the target |

---

## TASK 2 of 2 — Prove latency and path

**In plain English:** We check average rtt against a budget and count hops.

---

### Step 1 of 2 — Average rtt under a threshold

**In plain English:** We extract the average round-trip time and compare it to a budget.

```bash
AVG=$(ping -c3 127.0.0.1 | awk -F/ '/rtt|round-trip/{print $5}')
echo "avg rtt: ${AVG} ms"
awk -v a="$AVG" 'BEGIN{exit !(a < 50)}' && echo "PASS: under 50ms" || echo "FAIL: too slow"
```

**Expected output:**

```
avg rtt: 0.0xx ms
PASS: under 50ms
```

**Line-by-line breakdown:**

- `awk -F/ '/rtt/{print $5}'` → Split the `rtt min/avg/max/mdev` line on `/` and print the average (field 5).
- `awk -v a="$AVG" 'BEGIN{exit !(a < 50)}'` → Float-aware comparison: pass when avg < 50ms.

**New words in this step:**

- **rtt average** — the mean round-trip latency from the summary line.

---

### Step 2 of 2 — Confirm a sane hop count

**In plain English:** We count the path hops and require at least one.

```bash
HOPS=$(traceroute -n -m 5 127.0.0.1 2>/dev/null | tail -n +2 | wc -l)
echo "hops: $HOPS"
[ "$HOPS" -ge 1 ] && echo "PASS: path resolved" || echo "FAIL: no path"
```

**Expected output:**

```
hops: 1
PASS: path resolved
```

**Line-by-line breakdown:**

- `traceroute -n -m 5 | tail -n +2` → Skip the header line, leaving one line per hop.
- `wc -l` → Count hops; loopback is a single hop, a real host is several.

**New words in this step:**

- **hop count** — number of routers on the path (1 for loopback).

---

### Concept card (Task 2)

| Concept | What it does | Exam trap |
|---|---|---|
| avg rtt | latency budget | use float-aware test |
| `awk BEGIN exit` | numeric compare | `[ ]` can't do floats |
| hop count | path length | skip header line |

---

### Troubleshoot (Task 2)

| Symptom | Likely cause | Fix |
|---|---|---|
| Bad `[ ]` float compare | Shell ints only | Use `awk` for floats |
| 0 hops | traceroute missing | Install / check rc |

---

## ✅ Lab Checklist

- [ ] Task 1 · Step 1 — Assert zero packet loss
- [ ] Task 1 · Step 2 — Reachability gate via exit code
- [ ] Task 2 · Step 1 — Average rtt under a threshold
- [ ] Task 2 · Step 2 — Confirm a sane hop count
- [ ] Every 🎯 Focus Coverage row (Anchor + NEW) mapped to a step
- [ ] 🧹 Teardown run — sandbox + any system state removed

---

## 🧹 Teardown

**In plain English:** Delete everything this lab created so the box is clean for the next run.

> Run this after you've verified the lab. `lab_teardown.sh` safely removes the single sandbox root — it refuses to touch `/`, `$HOME`, or any protected path. This lab changed **no** system state.

```bash
cd /tmp
bash lab_teardown.sh "$LAB_ROOT"     # = /tmp/lab-32
```

**Expected output:**

```
✅ Removed /tmp/lab-32 — lab workspace is clean.
```

---

## ⚠️ Common Pitfalls

| Mistake | Symptom | Fix |
|---|---|---|
| `[ ]` for floats | Syntax error / wrong result | Use `awk` numeric compare |
| Forgetting header skip | Hop count off by one | `tail -n +2` |
| Not bounding ping | Hangs | `-c` and `-W` |

---

## 📌 Exam Strategy

Every connectivity claim should produce a number and a PASS/FAIL: loss %, rtt average, reachability exit code, hop count. Use `awk` for float comparisons since `[ ]` only handles integers.

- Extract loss/rtt; assert against thresholds.
- `ping` exit code is the simplest reachability test.
- `traceroute | wc -l` quantifies path length.

---

## 🔗 Related Labs

- [Lab 32a — Check Network Connectivity (RHCSA)](../lab-32a-ping-traceroute-rhcsa/) — the commands behind these checks
- [Lab 32b — Check Network Connectivity (Ansible)](../lab-32b-ping-traceroute-ansible/) — reachability gates in plays
- [Lab 33c — Display IP and Routing Info (Verify)](../lab-33c-ip-addr-route-show-verify/) — verifying addresses and routes

---

## 👤 Author

**Kelvin R. Tobias**  
[kelvinintech.com](https://kelvinintech.com) · [GitHub](https://github.com/kelvintechnical) · [LinkedIn](https://www.linkedin.com/in/kelvin-r-tobias-211949219)
