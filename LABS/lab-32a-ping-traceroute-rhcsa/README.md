# Lab 32a: Check Network Connectivity (RHCSA) — `ping`, `traceroute`, `ss`

**Series:** linux-ops-mastery — Networking · **Lab 32a of the Novice → RHCA path**  
**Certifications covered:** RHCSA EX200 (diagnosing connectivity), SRE/DevOps (incident triage, path analysis)  
**Prerequisite:** [Lab 31c](../lab-31c-static-ip-nmcli-verify/) completed  
**Time Estimate:** 20–30 minutes  
**Difficulty:** Beginner

---

## 🎯 Today's Focus Coverage

> Stay on-subject via the ANCHOR rows; expand vocabulary via the NEW rows. Every row is exercised by a STEP below.

**⚓ Anchor — already learned (on-topic reuse)**

| # | Command / switch | Covered by |
|---|---|---|
| A1 | `ping -c` | _Task 1 · Step 1_ |
| A2 | exit codes for scripting | _Task 1 · Step 2_ |

**🆕 NEW this lab — introduced for the first time** (minimum 3)

| # | Command / switch | First taught in | Covered by |
|---|---|---|---|
| N1 | `ping -c -W` (count/timeout) | Task 1 · Step 1 | _Task 1 · Step 1_ |
| N2 | `ping` stats (loss / rtt) | Task 1 · Step 2 | _Task 1 · Step 2_ |
| N3 | `traceroute` / `-n` | Task 2 · Step 1 | _Task 2 · Step 1_ |
| N4 | `ping -s` packet size | Task 2 · Step 2 | _Task 2 · Step 2_ |

---

## 🎯 Objective

Diagnose "is it reachable, and where does it break?" You will send bounded pings (`-c`, `-W`), read packet loss and round-trip time, trace the network path with `traceroute` (`-n` to skip DNS), and test with larger packets (`-s`) to surface MTU issues. By the end you can triage connectivity methodically instead of guessing.

> **Note:** Examples target `127.0.0.1`/`localhost` so they work on any box, online or not. Substitute a real host/gateway when triaging for real.

---

## 🧠 Concept

`ping` sends ICMP echo requests and times the replies; **always bound it** with `-c COUNT` (so it stops) and `-W SECONDS` (per-packet timeout) in scripts. Its summary is the diagnosis: **packet loss** (0% good, >0% trouble) and **round-trip time** (min/avg/max). `ping`'s exit code is scriptable: 0 = at least one reply, non-zero = no replies. `traceroute` reveals the *path* hop by hop, showing where latency spikes or packets die; `-n` skips reverse-DNS for speed. `ping -s SIZE` sends larger payloads to expose MTU/fragmentation problems that small pings miss. The triage ladder: ping the loopback (stack OK?), the gateway (LAN OK?), then a remote host (routing/DNS OK?).

```
ping -c4 -W2 127.0.0.1   → 4 packets, 2s timeout, then summary
ping -c2 host | grep loss → packet loss %
traceroute -n 127.0.0.1  → path, numeric (no DNS)
ping -c2 -s 1400 host    → larger packets (MTU test)
echo $?                  → 0 reachable, non-zero not
```

> **Why this matters:** Connectivity triage is a core admin reflex. Knowing loss vs latency, where `traceroute` shows the break, and bounding `ping` so scripts don't hang are everyday and exam-relevant skills.

---

## 📚 Command Reference

| Command | Purpose | Notes |
|---|---|---|
| `ping -c N` | Send N packets | always bound count |
| `ping -W S` | Per-packet timeout | seconds |
| `ping -s SIZE` | Payload size | MTU testing |
| `traceroute` | Trace the path | hop by hop |
| `traceroute -n` | No DNS | faster |
| `$?` | Reachability | 0 = reply |

---

## 🧰 LAB-WIDE SETUP

**In plain English:** Make a sandbox for saved results; targets are loopback/local.

> Run this block **once** before Task 1. `LAB_ROOT` holds any saved output.

```bash
export LAB_ROOT=/tmp/lab-32
mkdir -p "$LAB_ROOT"
cd "$LAB_ROOT"
command -v traceroute >/dev/null || echo "note: install traceroute (dnf install -y traceroute)"
echo "ready"
echo "exit was: $?"
```

**Expected output:**

```
ready
exit was: 0
```

---

## TASK 1 of 2 — Ping and read the stats

**In plain English:** We send bounded pings and interpret loss and latency.

---

### Step 1 of 2 — Bounded ping with `-c` and `-W`

**In plain English:** We ping the loopback a fixed number of times with a timeout.

```bash
ping -c4 -W2 127.0.0.1
echo "ping rc: $?"
```

**Expected output:**

```
PING 127.0.0.1 (127.0.0.1) 56(84) bytes of data.
64 bytes from 127.0.0.1: icmp_seq=1 ttl=64 time=0.0xx ms
... (4 replies) ...
--- 127.0.0.1 ping statistics ---
4 packets transmitted, 4 received, 0% packet loss, time ...
ping rc: 0
```

**Line-by-line breakdown:**

- `ping -c4 -W2 127.0.0.1` → Send exactly 4 packets, each with a 2-second timeout, then stop.
- `ping rc: 0` → Exit 0 means at least one reply — reachable.

**New words in this step:**

- **`-c` / `-W`** — packet count and per-packet timeout (bound the command).

---

### Step 2 of 2 — Read loss and round-trip time

**In plain English:** We extract the packet-loss and latency lines for a clean diagnosis.

```bash
ping -c3 127.0.0.1 | grep -E 'packet loss|rtt|round-trip'
LOSS=$(ping -c3 -W2 127.0.0.1 | grep -oP '\d+(?=% packet loss)')
echo "loss%: $LOSS"
[ "$LOSS" -eq 0 ] && echo "NO LOSS (OK)" || echo "LOSS DETECTED"
```

**Expected output:**

```
3 packets transmitted, 3 received, 0% packet loss, time ...
rtt min/avg/max/mdev = 0.0xx/0.0xx/0.0xx/0.0xx ms
loss%: 0
NO LOSS (OK)
```

**Line-by-line breakdown:**

- `grep -E 'packet loss|rtt'` → Pull the two summary lines that matter: loss and round-trip time.
- `grep -oP '\d+(?=% packet loss)'` → Extract just the loss percentage for a script.

**New words in this step:**

- **packet loss / rtt** — the percentage of dropped packets and the round-trip latency.

---

### Concept card (Task 1)

| Concept | What it does | Exam trap |
|---|---|---|
| `-c`/`-W` | bound ping | unbounded hangs |
| loss % | reliability | >0 = problem |
| rtt | latency | high avg = slow path |

---

### Troubleshoot (Task 1)

| Symptom | Likely cause | Fix |
|---|---|---|
| ping hangs | No `-c` | Always set `-c` |
| 100% loss | Host/firewall down | Try gateway first |

---

## TASK 2 of 2 — Trace the path and test MTU

**In plain English:** We trace the route to a target, then test with larger packets.

---

### Step 1 of 2 — Trace with `traceroute -n`

**In plain English:** We map the hops to the loopback (one hop) numerically.

```bash
traceroute -n -m 5 127.0.0.1
echo "exit was: $?"
```

**Expected output:**

```
traceroute to 127.0.0.1 (127.0.0.1), 5 hops max, 60 byte packets
 1  127.0.0.1  0.0xx ms  0.0xx ms  0.0xx ms
exit was: 0
```

**Line-by-line breakdown:**

- `traceroute -n -m 5 127.0.0.1` → Trace the path; `-n` skips reverse-DNS, `-m 5` caps hops. Loopback is a single hop.
- For a real host, each line is a router on the path with its latency — where the line stops is where the break is.

**New words in this step:**

- **`traceroute`** — show the hop-by-hop network path to a target.
- **`-n`** — numeric output (no DNS lookups).

---

### Step 2 of 2 — Larger packets with `ping -s`

**In plain English:** We send bigger payloads to probe for MTU/fragmentation issues.

```bash
ping -c2 -s 1400 127.0.0.1 | grep -E 'bytes from|packet loss'
echo "exit was: $?"
```

**Expected output:**

```
1408 bytes from 127.0.0.1: icmp_seq=1 ttl=64 time=0.0xx ms
2 packets transmitted, 2 received, 0% packet loss, ...
exit was: 0
```

**Line-by-line breakdown:**

- `ping -c2 -s 1400 127.0.0.1` → 1400-byte payloads; on a real path, loss only with large packets points to an MTU problem.
- `grep 'packet loss'` → Confirm large packets also get through.

**New words in this step:**

- **`-s SIZE`** — set the ICMP payload size to test MTU handling.

---

### Concept card (Task 2)

| Concept | What it does | Exam trap |
|---|---|---|
| `traceroute -n` | path map | where it stops = break |
| `-m` | max hops | cap long traces |
| `-s` | packet size | MTU diagnosis |

---

### Troubleshoot (Task 2)

| Symptom | Likely cause | Fix |
|---|---|---|
| `traceroute` not found | Not installed | `dnf install traceroute` |
| Large ping fails only | MTU/fragmentation | Test `-M do -s` sizes |

---

## ✅ Lab Checklist

- [ ] Task 1 · Step 1 — Bounded ping with `-c` and `-W`
- [ ] Task 1 · Step 2 — Read loss and round-trip time
- [ ] Task 2 · Step 1 — Trace with `traceroute -n`
- [ ] Task 2 · Step 2 — Larger packets with `ping -s`
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
| Unbounded `ping` | Runs forever | Always `-c` |
| Confusing loss vs latency | Wrong diagnosis | Read both summary lines |
| Forgetting `-n` | Slow traceroute | Skip DNS with `-n` |

---

## 📌 Exam Strategy

Triage with the ladder: ping loopback, gateway, then remote. Bound `ping` with `-c`/`-W`, read loss vs rtt, and use `traceroute -n` to locate the break. Use `ping -s` only when you suspect MTU.

- Always `-c` so ping (and scripts) terminate.
- Loss = reliability, rtt = latency — diagnose differently.
- `traceroute` shows *where* it breaks, not just *that* it broke.

---

## 🔗 Related Labs

- [Lab 32b — Check Network Connectivity (Ansible)](../lab-32b-ping-traceroute-ansible/) — reachability checks in plays
- [Lab 32c — Check Network Connectivity (Verify)](../lab-32c-ping-traceroute-verify/) — prove loss/latency thresholds
- [Lab 34a — Inspecting Listening Sockets (RHCSA)](../lab-34a-ss-listening-sockets-rhcsa/) — checking which ports are open

---

## 👤 Author

**Kelvin R. Tobias**  
[kelvinintech.com](https://kelvinintech.com) · [GitHub](https://github.com/kelvintechnical) · [LinkedIn](https://www.linkedin.com/in/kelvin-r-tobias-211949219)
