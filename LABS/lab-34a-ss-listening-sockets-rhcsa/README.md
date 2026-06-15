# Lab 34a: Inspecting Listening Sockets (RHCSA) — `ss`

**Series:** linux-ops-mastery — Networking · **Lab 34a of the Novice → RHCA path**  
**Certifications covered:** RHCSA EX200 (which services listen on which ports), SRE/DevOps (service triage, port conflicts)  
**Prerequisite:** [Lab 33c](../lab-33c-ip-addr-route-show-verify/) completed  
**Time Estimate:** 20–30 minutes  
**Difficulty:** Beginner

---

## 🎯 Today's Focus Coverage

> Stay on-subject via the ANCHOR rows; expand vocabulary via the NEW rows. Every row is exercised by a STEP below.

**⚓ Anchor — already learned (on-topic reuse)**

| # | Command / switch | Covered by |
|---|---|---|
| A1 | `grep` filtering | _Task 1 · Step 2_ |
| A2 | pipelines `|` | _Task 2 · Step 2_ |

**🆕 NEW this lab — introduced for the first time** (minimum 3)

| # | Command / switch | First taught in | Covered by |
|---|---|---|---|
| N1 | `ss -tuln` (listening) | Task 1 · Step 1 | _Task 1 · Step 1_ |
| N2 | `ss -tulnp` (process) | Task 1 · Step 2 | _Task 1 · Step 2_ |
| N3 | `ss -s` (summary) | Task 2 · Step 1 | _Task 2 · Step 1_ |
| N4 | `ss state` / `sport` filters | Task 2 · Step 2 | _Task 2 · Step 2_ |

---

## 🎯 Objective

Answer "what is listening, and who owns it?" with `ss`, the modern replacement for `netstat`. You'll list listening TCP/UDP sockets numerically (`-tuln`), attach the owning process (`-tulnp`), read socket summary statistics (`-s`), and filter by state and port. This is the fast path to diagnosing port conflicts and confirming a service is actually bound.

---

## 🧠 Concept

`ss` (socket statistics) reads kernel socket data directly and is faster than legacy `netstat`. The everyday invocation is `ss -tuln`: `-t` TCP, `-u` UDP, `-l` listening only, `-n` numeric (don't resolve ports/hosts to names — faster and clearer). Add `-p` (as root) to show the owning **process** (`users:(("sshd",pid=...))`) — essential for "what's holding port 8080?". `ss -s` prints a one-screen summary of total sockets by type and state. `ss` also supports a filter language: `ss -t state established`, `ss -tuln 'sport = :22'`. Reading the `Local Address:Port` column tells you the bind: `0.0.0.0:22` (all IPv4), `127.0.0.1:25` (loopback only), `[::]:80` (all IPv6).

```
ss -tuln          → listening TCP+UDP, numeric
ss -tulnp         → + owning process (root)
ss -s             → socket summary statistics
ss -t state established → filter by state
ss -tuln 'sport = :22'  → filter by source port
```

> **Why this matters:** "Is the service listening, on which address, and who owns the port?" is the core of service triage. `ss` answers all three instantly; the bind address (all vs loopback) is a frequent gotcha.

---

## 📚 Command Reference

| Command | Purpose | Notes |
|---|---|---|
| `ss -t` / `-u` | TCP / UDP | protocol select |
| `ss -l` | Listening only | servers |
| `ss -n` | Numeric | no name resolution |
| `ss -p` | Process | needs root |
| `ss -a` | All sockets | listening + connected |
| `ss -s` | Summary | counts by type/state |

---

## 🧰 LAB-WIDE SETUP

**In plain English:** Create a sandbox for saved output; sockets are inspected live.

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

## TASK 1 of 2 — List listeners and their owners

**In plain English:** We list listening sockets, then attach the owning process.

---

### Step 1 of 2 — Listening sockets, numeric

**In plain English:** We list every listening TCP/UDP socket without name resolution.

```bash
ss -tuln
echo "exit was: $?"
```

**Expected output:**

```
Netid State   Recv-Q  Send-Q   Local Address:Port   Peer Address:Port
tcp   LISTEN  0       128      0.0.0.0:22           0.0.0.0:*
tcp   LISTEN  0       128      127.0.0.1:25         0.0.0.0:*
udp   UNCONN  0       0        127.0.0.1:323        0.0.0.0:*
exit was: 0
```

**Line-by-line breakdown:**

- `ss -tuln` → `-t`+`-u` both protocols, `-l` listening only, `-n` numeric ports.
- `Local Address:Port` → `0.0.0.0:22` = all interfaces; `127.0.0.1:25` = loopback only — the bind scope matters.

**New words in this step:**

- **`-l` / `-n`** — listening-only and numeric (no DNS/service-name lookups).

---

### Step 2 of 2 — Show the owning process

**In plain English:** We add `-p` to see which program owns each socket.

```bash
ss -tulnp 2>/dev/null | head -n 5
echo "exit was: $?"
```

**Expected output:**

```
Netid State  ... Local Address:Port  Peer Address:Port Process
tcp   LISTEN ... 0.0.0.0:22          0.0.0.0:*         users:(("sshd",pid=1234,fd=3))
...
exit was: 0
```

**Line-by-line breakdown:**

- `ss -tulnp` → `-p` appends `users:(("name",pid=...))` — the program and PID holding the port (root needed for other users' processes).
- This is how you find "what's holding port X" before killing or reconfiguring it.

**New words in this step:**

- **`-p`** — show the process (name + PID) that owns each socket.

---

### Concept card (Task 1)

| Concept | What it does | Exam trap |
|---|---|---|
| `-tuln` | listeners | `-n` avoids slow DNS |
| `-p` | owner | needs root |
| bind addr | scope | `0.0.0.0` vs `127.0.0.1` |

---

### Troubleshoot (Task 1)

| Symptom | Likely cause | Fix |
|---|---|---|
| No process column | Not root | Run with `sudo` |
| Port not listed | Service down | Start/check the service |

---

## TASK 2 of 2 — Summarize and filter

**In plain English:** We read socket summary stats, then filter by state and port.

---

### Step 1 of 2 — Socket summary with `-s`

**In plain English:** We print a one-screen overview of socket counts.

```bash
ss -s
echo "exit was: $?"
```

**Expected output:**

```
Total: 200
TCP:   8 (estab 2, closed 0, orphaned 0, ...)
Transport Total  IP  IPv6
RAW    0  0  0
UDP    4  3  1
TCP    8  6  2
...
exit was: 0
```

**Line-by-line breakdown:**

- `ss -s` → Aggregate counts of sockets by transport and state — a quick health snapshot.

**New words in this step:**

- **`-s` (summary)** — totals of sockets by type and state.

---

### Step 2 of 2 — Filter by state and port

**In plain English:** We use `ss`'s filter language to narrow results.

```bash
ss -tan state listening 'sport = :22'
echo "---"
ss -t state established | head -n 3
```

**Expected output:**

```
State   Recv-Q  Send-Q  Local Address:Port  Peer Address:Port
LISTEN  0       128     0.0.0.0:22          0.0.0.0:*
---
State   Recv-Q  Send-Q  Local Address:Port  Peer Address:Port
ESTAB   0       0       192.168.x.x:22      192.168.x.y:54321
```

**Line-by-line breakdown:**

- `ss -tan state listening 'sport = :22'` → TCP, all, numeric, filtered to listening sockets on source port 22.
- `ss -t state established` → Only currently established TCP connections.

**New words in this step:**

- **state / sport filters** — `ss`'s query language to narrow by connection state and port.

---

### Concept card (Task 2)

| Concept | What it does | Exam trap |
|---|---|---|
| `-s` | summary | quick overview |
| `state X` | filter state | listening/established |
| `sport`/`dport` | port filter | quote the expression |

---

### Troubleshoot (Task 2)

| Symptom | Likely cause | Fix |
|---|---|---|
| Filter ignored | Unquoted expression | Quote `'sport = :22'` |
| Empty established | No active conns | Expected on idle host |

---

## ✅ Lab Checklist

- [ ] Task 1 · Step 1 — Listening sockets, numeric
- [ ] Task 1 · Step 2 — Show the owning process
- [ ] Task 2 · Step 1 — Socket summary with `-s`
- [ ] Task 2 · Step 2 — Filter by state and port
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
| Omitting `-n` | Slow / odd names | Add `-n` |
| Forgetting root for `-p` | No process info | Use `sudo` |
| Misreading bind addr | Wrong scope assumption | `0.0.0.0` ≠ `127.0.0.1` |

---

## 📌 Exam Strategy

`ss -tulnp` is the one to memorize: listening TCP/UDP, numeric, with owning process. Read the bind address carefully — `0.0.0.0`/`[::]` is all interfaces, `127.0.0.1` is loopback only. Use `-s` for a quick overview and the filter language to narrow.

- `ss -tuln` for listeners, add `-p` (root) for owners.
- Bind address tells you the exposure scope.
- `ss` replaces `netstat` — faster, same answers.

---

## 🔗 Related Labs

- [Lab 34b — Inspecting Listening Sockets (Ansible)](../lab-34b-ss-listening-sockets-ansible/) — port-state checks in plays
- [Lab 34c — Inspecting Listening Sockets (Verify)](../lab-34c-ss-listening-sockets-verify/) — prove a port is (not) listening
- [Lab 32a — Check Network Connectivity (RHCSA)](../lab-32a-ping-traceroute-rhcsa/) — reachability before checking the socket

---

## 👤 Author

**Kelvin R. Tobias**  
[kelvinintech.com](https://kelvinintech.com) · [GitHub](https://github.com/kelvintechnical) · [LinkedIn](https://www.linkedin.com/in/kelvin-r-tobias-211949219)
