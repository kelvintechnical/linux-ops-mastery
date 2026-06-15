# Lab 31c: Configure a Static IP (Verify) — `nmcli -g`, `ip addr`, `ping`

**Series:** linux-ops-mastery — Networking · **Lab 31c of the Novice → RHCA path**  
**Certifications covered:** RHCSA EX200 (proving a static IP is set and persistent), SRE (network-config validation), DevOps (host networking checks)  
**Prerequisite:** [Lab 31a](../lab-31a-static-ip-nmcli-rhcsa/) and [Lab 31b](../lab-31b-static-ip-nmcli-ansible/) completed · **root/sudo required**  
**Time Estimate:** 15–25 minutes  
**Difficulty:** Intermediate

---

## 🎯 Today's Focus Coverage

> Stay on-subject via the ANCHOR rows; expand vocabulary via the NEW rows. Every row is exercised by a STEP below.

**⚓ Anchor — already learned (on-topic reuse)**

| # | Command / switch | Covered by |
|---|---|---|
| A1 | `nmcli -g` | _Task 1 · Step 1_ |
| A2 | `ip addr show` | _Task 1 · Step 2_ |

**🆕 NEW this lab — introduced for the first time** (minimum 3)

| # | Command / switch | First taught in | Covered by |
|---|---|---|---|
| N1 | config vs live comparison | Task 1 · Step 2 | _Task 1 · Step 2_ |
| N2 | `ping -c` reachability | Task 2 · Step 1 | _Task 2 · Step 1_ |
| N3 | persistence (`nmcli con show`) | Task 2 · Step 2 | _Task 2 · Step 2_ |
| N4 | `method` is manual proof | Task 2 · Step 2 | _Task 2 · Step 2_ |

---

## 🎯 Objective

Prove the static IP is configured, live, reachable, and persistent. You will read the stored address with `nmcli -g`, confirm it matches the live interface (`ip addr`), ping it to prove it actually works, and verify the profile is `manual` (persistent) — not DHCP. Config + live + reachable + persistent is a fully verified static IP.

> **⚠️ System-state lab.** Assumes the `lab-static`/`dummy0` from 31a/31b exist; setup recreates them if needed. Teardown removes them.

---

## 🧠 Concept

A static IP claim has four parts. **Stored config**: `nmcli -g ipv4.addresses con show lab-static` returns what the profile *says*. **Live state**: `ip addr show dummy0` returns what the kernel *has*; the two must agree, or the profile isn't active. **Reachability**: `ping -c1 10.99.99.2` proves the address actually responds, not just that it's listed. **Persistence**: `nmcli -g ipv4.method con show lab-static` must be `manual` — a `manual` profile survives reboot, whereas `auto` would mean DHCP. Verifying all four distinguishes "I typed an IP" from "the host has a working, persistent static address."

```
nmcli -g ipv4.addresses con show lab-static → 10.99.99.2/24 (config)
ip -o addr show dummy0 | grep 10.99.99.2     → live matches config
ping -c1 10.99.99.2                          → address responds
nmcli -g ipv4.method con show lab-static     → manual (persistent)
```

> **Why this matters:** An IP listed in a profile but not active, or set to `auto`, fails silently. Proving config==live, reachable, and `manual` is the real definition of "static IP configured."

---

## 📚 Command Reference

| Command | Purpose | Critical flags |
|---|---|---|
| `nmcli -g ipv4.addresses` | Stored address | one field |
| `ip -o addr show DEV` | Live address | one line per addr |
| `ping -c1` | Reachability | one packet |
| `nmcli -g ipv4.method` | Persistence | `manual` |
| `nmcli -t` | Terse output | scriptable |

---

## 🧰 LAB-WIDE SETUP

**In plain English:** Ensure the static profile exists so there's something to verify.

> Run this block **once** before Task 1. It recreates `dummy0`/`lab-static` idempotently if 31a/31b's Teardown removed them, so this verify lab stands alone.

```bash
export LAB_ROOT=/tmp/lab-31
mkdir -p "$LAB_ROOT"
sudo modprobe dummy 2>/dev/null || true
nmcli con show lab-static >/dev/null 2>&1 || \
  sudo nmcli con add type dummy ifname dummy0 con-name lab-static \
    ipv4.method manual ipv4.addresses 10.99.99.2/24 ipv4.gateway 10.99.99.1
sudo nmcli con up lab-static >/dev/null 2>&1 || true
ip -o addr show dummy0 | grep -o '10.99.99.2'
echo "exit was: $?"
```

**Expected output:**

```
10.99.99.2
exit was: 0
```

---

## TASK 1 of 2 — Prove config matches live

**In plain English:** We read the stored address and confirm it's live on the interface.

---

### Step 1 of 2 — Read the stored address

**In plain English:** We get the configured IPv4 address from the profile.

```bash
A=$(nmcli -g ipv4.addresses con show lab-static)
echo "config: $A"
[ "$A" = "10.99.99.2/24" ] && echo "CONFIG OK" || echo "WRONG CONFIG (FAIL)"
```

**Expected output:**

```
config: 10.99.99.2/24
CONFIG OK
```

**Line-by-line breakdown:**

- `nmcli -g ipv4.addresses con show lab-static` → Print just the stored address field.
- `[ "$A" = "10.99.99.2/24" ]` → Assert the profile holds the expected static address.

**New words in this step:**

- **stored config** — what the NetworkManager profile records.

---

### Step 2 of 2 — Confirm config equals live

**In plain English:** We confirm the live interface carries the same address.

```bash
ip -o addr show dummy0 | grep -q '10.99.99.2/24' && echo "LIVE MATCHES (OK)" || echo "LIVE MISMATCH (FAIL)"
ip -o -4 addr show dummy0
```

**Expected output:**

```
LIVE MATCHES (OK)
N: dummy0    inet 10.99.99.2/24 brd 10.99.99.255 scope global dummy0 ...
```

**Line-by-line breakdown:**

- `ip -o addr show dummy0 | grep -q '10.99.99.2/24'` → The live kernel address matches the profile — proof the profile is active.
- `ip -o -4 addr show dummy0` → One-line IPv4 view of the interface.

**New words in this step:**

- **config-vs-live** — confirming the stored profile equals the kernel's live address.

---

### Concept card (Task 1)

| Concept | What it does | Exam trap |
|---|---|---|
| `nmcli -g` | config value | profile, not live |
| `ip -o addr` | live value | runtime |
| match | profile active | mismatch = inactive |

---

### Troubleshoot (Task 1)

| Symptom | Likely cause | Fix |
|---|---|---|
| Config but no live | Not activated | `nmcli con up lab-static` |
| Mismatch | Edited but not re-upped | Re-activate the profile |

---

## TASK 2 of 2 — Prove reachable and persistent

**In plain English:** We ping the address and confirm the profile is `manual`.

---

### Step 1 of 2 — Reachability with `ping`

**In plain English:** We send one ping to the static address and confirm a reply.

```bash
ping -c1 -W2 10.99.99.2 >/dev/null 2>&1 && echo "REACHABLE (OK)" || echo "UNREACHABLE (FAIL)"
ping -c1 10.99.99.2 | grep -E 'bytes from|packet loss'
```

**Expected output:**

```
REACHABLE (OK)
64 bytes from 10.99.99.2: icmp_seq=1 ttl=64 time=0.0xx ms
1 packets transmitted, 1 received, 0% packet loss, ...
```

**Line-by-line breakdown:**

- `ping -c1 -W2 10.99.99.2 >/dev/null && ...` → One packet, 2s timeout; exit 0 means it replied.
- `... | grep 'packet loss'` → Confirm 0% loss — the address truly responds.

**New words in this step:**

- **reachability** — proving the configured address actually answers.

---

### Step 2 of 2 — Persistence via `method`

**In plain English:** We confirm the profile uses `manual` addressing (persistent across reboot).

```bash
M=$(nmcli -g ipv4.method con show lab-static)
echo "method: $M"
[ "$M" = "manual" ] && echo "PERSISTENT STATIC (OK)" || echo "NOT MANUAL (FAIL)"
echo "exit was: $?"
```

**Expected output:**

```
method: manual
PERSISTENT STATIC (OK)
exit was: 0
```

**Line-by-line breakdown:**

- `nmcli -g ipv4.method con show lab-static` → Read the addressing method.
- `[ "$M" = "manual" ]` → `manual` confirms a persistent static config (not DHCP `auto`).

**New words in this step:**

- **persistence proof** — confirming `manual` so the address survives reboot.

---

### Concept card (Task 2)

| Concept | What it does | Exam trap |
|---|---|---|
| `ping -c1` | reachability | `-W` for timeout |
| `ipv4.method` | persistence | `manual` vs `auto` |
| 0% loss | working address | partial loss = problem |

---

### Troubleshoot (Task 2)

| Symptom | Likely cause | Fix |
|---|---|---|
| Unreachable | Profile down | `nmcli con up` |
| method `auto` | DHCP, not static | Set `ipv4.method manual` |

---

## ✅ Lab Checklist

- [ ] Task 1 · Step 1 — Read the stored address
- [ ] Task 1 · Step 2 — Confirm config equals live
- [ ] Task 2 · Step 1 — Reachability with `ping`
- [ ] Task 2 · Step 2 — Persistence via `method`
- [ ] Every 🎯 Focus Coverage row (Anchor + NEW) mapped to a step
- [ ] 🧹 Teardown run — sandbox + **profile and dummy interface removed**

---

## 🧹 Teardown

**In plain English:** Delete the test profile and dummy interface, then the sandbox.

> This lab (and its setup) changed system state. These commands **reverse** it; the real NIC was never touched.

```bash
sudo nmcli con down lab-static 2>/dev/null || true
sudo nmcli con delete lab-static 2>/dev/null || true
sudo ip link delete dummy0 2>/dev/null || true
nmcli con show | grep -q lab-static && echo "still present (FAIL)" || echo "lab-static removed"
cd /tmp
bash lab_teardown.sh "$LAB_ROOT"     # = /tmp/lab-31
```

**Expected output:**

```
lab-static removed
✅ Removed /tmp/lab-31 — lab workspace is clean.
```

---

## ⚠️ Common Pitfalls

| Mistake | Symptom | Fix |
|---|---|---|
| Checking config only | Profile may be inactive | Compare to live `ip addr` |
| Skipping ping | Address may not respond | `ping -c1` |
| Ignoring `method` | Might be DHCP | Confirm `manual` |

---

## 📌 Exam Strategy

Verify a static IP four ways: stored config (`nmcli -g`), live match (`ip addr`), reachability (`ping`), and persistence (`ipv4.method manual`). All four passing means the address is real, active, working, and reboot-safe.

- Config must equal live, or the profile isn't active.
- `ping -c1` proves the address responds.
- `ipv4.method manual` proves it's persistent.

---

## 🔗 Related Labs

- [Lab 31a — Configure a Static IP (RHCSA)](../lab-31a-static-ip-nmcli-rhcsa/) — the `nmcli` config this audits
- [Lab 31b — Configure a Static IP (Ansible)](../lab-31b-static-ip-nmcli-ansible/) — the `nmcli` module plays you verify
- [Lab 32a — Check Network Connectivity (RHCSA)](../lab-32a-ping-traceroute-rhcsa/) — deeper reachability testing

---

## 👤 Author

**Kelvin R. Tobias**  
[kelvinintech.com](https://kelvinintech.com) · [GitHub](https://github.com/kelvintechnical) · [LinkedIn](https://www.linkedin.com/in/kelvin-r-tobias-211949219)
