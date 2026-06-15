# Lab 33a: Display IP and Routing Info (RHCSA) — `ip addr`, `ip route`, `ip -br`

**Series:** linux-ops-mastery — Networking · **Lab 33a of the Novice → RHCA path**  
**Certifications covered:** RHCSA EX200 (inspect interfaces & routes), SRE/DevOps (network state triage)  
**Prerequisite:** [Lab 32c](../lab-32c-ping-traceroute-verify/) completed  
**Time Estimate:** 20–30 minutes  
**Difficulty:** Beginner

---

## 🎯 Today's Focus Coverage

> Stay on-subject via the ANCHOR rows; expand vocabulary via the NEW rows. Every row is exercised by a STEP below.

**⚓ Anchor — already learned (on-topic reuse)**

| # | Command / switch | Covered by |
|---|---|---|
| A1 | `ip addr` (from Lab 31) | _Task 1 · Step 1_ |
| A2 | `ip route` (from Lab 31) | _Task 2 · Step 1_ |

**🆕 NEW this lab — introduced for the first time** (minimum 3)

| # | Command / switch | First taught in | Covered by |
|---|---|---|---|
| N1 | `ip -br addr` (brief) | Task 1 · Step 1 | _Task 1 · Step 1_ |
| N2 | `ip -4 addr show dev` | Task 1 · Step 2 | _Task 1 · Step 2_ |
| N3 | `ip route` / default gw | Task 2 · Step 1 | _Task 2 · Step 1_ |
| N4 | `ip route get` (path picker) | Task 2 · Step 2 | _Task 2 · Step 2_ |

---

## 🎯 Objective

Read the live network state with the modern `ip` suite. You'll list interfaces and addresses (including the compact `-br` view), filter to one device's IPv4, read the routing table and identify the default gateway, and use `ip route get` to ask the kernel which route a given destination would take. This is the read-only counterpart to configuring with `nmcli`.

> **Note:** Examples use the always-present loopback (`lo`) so they run anywhere. Substitute a real device (e.g. `eth0`) on a configured host.

---

## 🧠 Concept

`ip` is the modern replacement for `ifconfig`/`route`. `ip addr` (or `ip a`) shows every interface with its addresses and flags; `ip -br addr` gives a one-line-per-interface summary that's ideal for scanning. Add `-4`/`-6` to filter by family and `show dev NAME` to focus one interface. `ip route` (or `ip r`) prints the routing table; the line starting `default via` is your gateway. `ip route get DEST` is the killer diagnostic: it asks the kernel exactly which source address and gateway *would* be used to reach `DEST`, resolving the routing decision without sending traffic. These are all read-only — perfect for triage.

```
ip addr / ip a            → full interface + address list
ip -br addr               → compact one-line summary
ip -4 addr show dev lo    → just IPv4 on one device
ip route / ip r           → routing table (default via = gateway)
ip route get 127.0.0.1    → which route/source the kernel picks
```

> **Why this matters:** "What's my IP, what's my gateway, and how would I reach X?" are the first three questions in any network problem. `ip` answers all three without changing anything.

---

## 📚 Command Reference

| Command | Purpose | Notes |
|---|---|---|
| `ip addr` / `ip a` | List addresses | full detail |
| `ip -br addr` | Brief view | one line/iface |
| `ip -4 addr show dev` | IPv4 of one device | family filter |
| `ip route` / `ip r` | Routing table | `default via` = gw |
| `ip route get` | Route decision | no traffic sent |
| `ip link` | Link/MAC/state | layer 2 |

---

## 🧰 LAB-WIDE SETUP

**In plain English:** Create a sandbox for any saved snapshots; inspection targets are live interfaces.

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

## TASK 1 of 2 — Inspect interfaces and addresses

**In plain English:** We list interfaces, then focus one device's IPv4.

---

### Step 1 of 2 — Brief interface summary

**In plain English:** We use the compact `-br` view to scan all interfaces at a glance.

```bash
ip -br addr
echo "exit was: $?"
```

**Expected output:**

```
lo               UNKNOWN        127.0.0.1/8 ::1/128
eth0             UP             192.168.x.x/24 ...
exit was: 0
```

**Line-by-line breakdown:**

- `ip -br addr` → One line per interface: name, operational state, and addresses — fast to scan.
- The state column (`UP`/`DOWN`/`UNKNOWN`) tells you whether the link is usable.

**New words in this step:**

- **`-br` (brief)** — compact, one-line-per-interface output.

---

### Step 2 of 2 — One device's IPv4

**In plain English:** We filter to a single interface and the IPv4 family.

```bash
ip -4 addr show dev lo
echo "---"
ip -4 -br addr show dev lo
```

**Expected output:**

```
1: lo: <LOOPBACK,UP,LOWER_UP> mtu 65536 ...
    inet 127.0.0.1/8 scope host lo
       valid_lft forever preferred_lft forever
---
lo               UNKNOWN        127.0.0.1/8
```

**Line-by-line breakdown:**

- `ip -4 addr show dev lo` → IPv4 only (`-4`), just the `lo` device — the `inet` line is the address.
- `ip -4 -br ... dev lo` → Same info, compact form for scripting.

**New words in this step:**

- **`show dev NAME`** — restrict output to one interface.

---

### Concept card (Task 1)

| Concept | What it does | Exam trap |
|---|---|---|
| `ip addr` | addresses | replaces `ifconfig` |
| `-br` | brief | great for scanning |
| `-4`/`show dev` | filter | family + device |

---

### Troubleshoot (Task 1)

| Symptom | Likely cause | Fix |
|---|---|---|
| No `inet` line | No IPv4 assigned | Configure with `nmcli` |
| Device DOWN | Link not up | `ip link set DEV up` |

---

## TASK 2 of 2 — Read routes and route decisions

**In plain English:** We read the routing table and ask the kernel how it would reach a target.

---

### Step 1 of 2 — Routing table and gateway

**In plain English:** We print the routing table and pick out the default gateway.

```bash
ip route
echo "---"
ip route | awk '/^default/{print "gateway:", $3; exit}'
```

**Expected output:**

```
default via 192.168.x.1 dev eth0 proto dhcp ...
127.0.0.0/8 dev lo ...
---
gateway: 192.168.x.1
```

**Line-by-line breakdown:**

- `ip route` → The full routing table; each line is a destination network and how to reach it.
- `awk '/^default/{print $3}'` → The `default` route's third field is the gateway IP.

**New words in this step:**

- **default route** — `default via GW` is the path for anything not otherwise matched.

---

### Step 2 of 2 — Ask the kernel: `ip route get`

**In plain English:** We ask which source and route would be used to reach a destination.

```bash
ip route get 127.0.0.1
echo "---"
ip route get 127.0.0.1 | awk '{print "src:", $NF; exit}'
```

**Expected output:**

```
local 127.0.0.1 dev lo src 127.0.0.1 uid ...
    cache <local>
---
src: <uid value>
```

**Line-by-line breakdown:**

- `ip route get 127.0.0.1` → The kernel reports the chosen `dev` and `src` for that destination — without sending a packet.
- For a real target it shows the outgoing device, source IP, and gateway it would use.

**New words in this step:**

- **`ip route get`** — query the routing decision for a specific destination.

---

### Concept card (Task 2)

| Concept | What it does | Exam trap |
|---|---|---|
| `ip route` | routing table | `default via` = gw |
| `ip route get` | route decision | no packet sent |
| `proto` | route source | dhcp/static/kernel |

---

### Troubleshoot (Task 2)

| Symptom | Likely cause | Fix |
|---|---|---|
| No default route | No gateway set | Set `gw4` via `nmcli` |
| `route get` unexpected dev | Routing misconfig | Review routes/metrics |

---

## ✅ Lab Checklist

- [ ] Task 1 · Step 1 — Brief interface summary
- [ ] Task 1 · Step 2 — One device's IPv4
- [ ] Task 2 · Step 1 — Routing table and gateway
- [ ] Task 2 · Step 2 — Ask the kernel: `ip route get`
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
| Using `ifconfig` | Deprecated/missing | Use `ip addr` |
| Reading wrong field | Wrong gateway | `default` line, field 3 |
| Confusing link vs addr | Missing info | `ip link` vs `ip addr` |

---

## 📌 Exam Strategy

`ip` answers the three triage questions: addresses (`ip addr`), gateway (`ip route`), and route decision (`ip route get`). Use `-br` to scan quickly and `-4`/`show dev` to focus. All read-only — safe to run anytime.

- `ip -br addr` for a fast overview.
- `default via` is the gateway.
- `ip route get` resolves routing without sending traffic.

---

## 🔗 Related Labs

- [Lab 33b — Display IP and Routing Info (Ansible)](../lab-33b-ip-addr-route-show-ansible/) — gather and assert on network facts
- [Lab 33c — Display IP and Routing Info (Verify)](../lab-33c-ip-addr-route-show-verify/) — prove addresses and routes
- [Lab 31a — Configure a Static IP (RHCSA)](../lab-31a-static-ip-nmcli-rhcsa/) — setting the addresses you inspect here

---

## 👤 Author

**Kelvin R. Tobias**  
[kelvinintech.com](https://kelvinintech.com) · [GitHub](https://github.com/kelvintechnical) · [LinkedIn](https://www.linkedin.com/in/kelvin-r-tobias-211949219)
