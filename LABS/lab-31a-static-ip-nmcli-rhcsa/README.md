# Lab 31a: Configure a Static IP Address (RHCSA) — `nmcli con add/mod`, `ip addr`

**Series:** linux-ops-mastery — Networking · **Lab 31a of the Novice → RHCA path**  
**Certifications covered:** RHCSA EX200 (persistent static IP with NetworkManager), RHCE EX294 (the `nmcli` module work), SRE/DevOps (host network config)  
**Prerequisite:** [Lab 30c](../lab-30c-info-pages-verify/) completed · **root/sudo required**  
**Time Estimate:** 30–40 minutes  
**Difficulty:** Intermediate

---

## 🎯 Today's Focus Coverage

> Stay on-subject via the ANCHOR rows; expand vocabulary via the NEW rows. Every row is exercised by a STEP below.

**⚓ Anchor — already learned (on-topic reuse)**

| # | Command / switch | Covered by |
|---|---|---|
| A1 | `ip addr show` | _Task 2 · Step 1_ |
| A2 | `ip route` | _Task 2 · Step 2_ |

**🆕 NEW this lab — introduced for the first time** (minimum 3)

| # | Command / switch | First taught in | Covered by |
|---|---|---|---|
| N1 | `nmcli con add` (profile) | Task 1 · Step 1 | _Task 1 · Step 1_ |
| N2 | `nmcli con mod` (edit) | Task 1 · Step 2 | _Task 1 · Step 2_ |
| N3 | `nmcli con up` (activate) | Task 2 · Step 1 | _Task 2 · Step 1_ |
| N4 | `ipv4.method manual` + addresses/gateway | Task 1 · Step 1 | _Task 1 · Step 1_ |

---

## 🎯 Objective

Configure a persistent static IP with NetworkManager — without risking your SSH session. You will create a **dummy interface** profile (so the real NIC is never touched), set a static IPv4 address/gateway/DNS with `nmcli con add`/`mod`, activate it, and inspect it with `ip addr`/`ip route`. By the end you know the exact `nmcli` workflow the exam tests, practiced safely.

> **⚠️ System-state lab — done safely.** All changes are on a throwaway `dummy0` interface and a profile named `lab-static`. Your primary connection is never modified. Teardown deletes the profile and interface. Use a practice VM.

---

## 🧠 Concept

On RHEL, **NetworkManager** owns the network, and `nmcli` is its CLI. Configuration lives in **connection profiles** (not directly on interfaces): a profile binds settings (IP method, address, gateway, DNS) to a device. `nmcli con add` creates a profile; `nmcli con mod` edits it; `nmcli con up`/`down` activates/deactivates it; changes persist across reboots (unlike a raw `ip addr add`, which is runtime-only). Key static-IP settings: `ipv4.method manual`, `ipv4.addresses 10.x/24`, `ipv4.gateway`, `ipv4.dns`. We practice on a **dummy** interface (`type dummy`) — a safe virtual NIC — so a typo can't knock you offline. `ip addr`/`ip route` then show the live result.

```
nmcli con add type dummy ifname dummy0 con-name lab-static \
      ipv4.method manual ipv4.addresses 10.99.99.2/24
nmcli con mod lab-static ipv4.gateway 10.99.99.1 ipv4.dns 10.99.99.53
nmcli con up lab-static
ip addr show dummy0      → the static IP is live
ip route                 → routes via the profile
```

> **Why this matters:** "Set a persistent static IP" is a classic RHCSA task. Doing it through `nmcli` profiles (not transient `ip` commands) is what makes it survive reboot — and practicing on a dummy interface means you can't accidentally cut your own connection.

---

## 📚 Command Reference

| Command | Purpose | Notes |
|---|---|---|
| `nmcli con add` | Create a profile | `type`, `con-name`, `ifname` |
| `nmcli con mod` | Edit a profile | `ipv4.*` settings |
| `nmcli con up/down` | Activate / deactivate | persistent |
| `nmcli con show` | List/inspect profiles | `--active` for live |
| `ip addr show DEV` | Live addresses | runtime view |
| `ip route` | Routing table | runtime view |

---

## 🧰 LAB-WIDE SETUP

**In plain English:** Make a marker sandbox; the network changes live on a dummy interface.

> Run this block **once** before Task 1. `LAB_ROOT` is just a Teardown marker; the real changes are the `lab-static` profile and `dummy0` device, removed in Teardown.

```bash
export LAB_ROOT=/tmp/lab-31
mkdir -p "$LAB_ROOT"
sudo modprobe dummy 2>/dev/null || true
echo "ready"
echo "exit was: $?"
```

**Expected output:**

```
ready
exit was: 0
```

---

## TASK 1 of 2 — Create and edit a static profile

**In plain English:** We create a dummy-interface profile with a static IP, then refine it.

---

### Step 1 of 2 — Create the profile with `nmcli con add`

**In plain English:** We create a connection on a safe dummy interface with a manual IPv4 address.

```bash
sudo nmcli con add type dummy ifname dummy0 con-name lab-static \
  ipv4.method manual ipv4.addresses 10.99.99.2/24
nmcli con show lab-static | grep -E 'ipv4.method|ipv4.addresses'
echo "exit was: $?"
```

**Expected output:**

```
Connection 'lab-static' (...) successfully added.
ipv4.method:                            manual
ipv4.addresses:                         10.99.99.2/24
exit was: 0
```

**Line-by-line breakdown:**

- `nmcli con add type dummy ifname dummy0 con-name lab-static` → Create a profile bound to a safe dummy device.
- `ipv4.method manual ipv4.addresses 10.99.99.2/24` → Static (manual) addressing with a private test address.

**New words in this step:**

- **connection profile** — the named bundle of network settings NetworkManager applies to a device.
- **`ipv4.method manual`** — static addressing (vs `auto`/DHCP).

---

### Step 2 of 2 — Refine with `nmcli con mod`

**In plain English:** We add a gateway and DNS server to the profile.

```bash
sudo nmcli con mod lab-static ipv4.gateway 10.99.99.1 ipv4.dns 10.99.99.53
nmcli con show lab-static | grep -E 'ipv4.gateway|ipv4.dns'
echo "exit was: $?"
```

**Expected output:**

```
ipv4.gateway:                           10.99.99.1
ipv4.dns:                               10.99.99.53
exit was: 0
```

**Line-by-line breakdown:**

- `nmcli con mod lab-static ipv4.gateway ... ipv4.dns ...` → Edit the existing profile to add gateway and DNS.
- `nmcli con show ... | grep` → Confirm the new settings are stored in the profile.

**New words in this step:**

- **`nmcli con mod`** — modify settings on an existing profile.

---

### Concept card (Task 1)

| Concept | What it does | Exam trap |
|---|---|---|
| profile vs device | settings bound to NIC | edit the profile, not `ip` |
| `manual` | static IP | `auto` = DHCP |
| `con mod` | persistent edit | survives reboot |

---

### Troubleshoot (Task 1)

| Symptom | Likely cause | Fix |
|---|---|---|
| "device not found" | dummy module missing | `sudo modprobe dummy` |
| Settings not saved | Typo in key | Use exact `ipv4.*` names |

---

## TASK 2 of 2 — Activate and inspect

**In plain English:** We bring the profile up and view the live result.

---

### Step 1 of 2 — Activate with `nmcli con up`

**In plain English:** We activate the profile and confirm the IP is live on the dummy interface.

```bash
sudo nmcli con up lab-static
ip addr show dummy0
echo "exit was: $?"
```

**Expected output:**

```
Connection successfully activated (...)
N: dummy0: <BROADCAST,NOARP,UP,LOWER_UP> ...
    inet 10.99.99.2/24 brd 10.99.99.255 scope global dummy0
exit was: 0
```

**Line-by-line breakdown:**

- `nmcli con up lab-static` → Activate the profile, applying its settings to `dummy0`.
- `ip addr show dummy0` → The `inet 10.99.99.2/24` line confirms the static IP is live.

**New words in this step:**

- **`nmcli con up`** — activate a profile, applying it to its device.

---

### Step 2 of 2 — Inspect routes with `ip route`

**In plain English:** We confirm a route to the static subnet exists.

```bash
ip route show dev dummy0
nmcli -g ipv4.addresses con show lab-static
echo "exit was: $?"
```

**Expected output:**

```
10.99.99.0/24 proto kernel scope link src 10.99.99.2
10.99.99.2/24
exit was: 0
```

**Line-by-line breakdown:**

- `ip route show dev dummy0` → The kernel route for the static subnet, created when the profile came up.
- `nmcli -g ipv4.addresses con show lab-static` → `-g` prints just the requested field — script-friendly output.

**New words in this step:**

- **`nmcli -g`** — get a single field value (clean, parseable).

---

### Concept card (Task 2)

| Concept | What it does | Exam trap |
|---|---|---|
| `con up` | activate | applies to device |
| `ip addr` | live view | runtime, not config |
| `nmcli -g` | one field | great for scripts |

---

### Troubleshoot (Task 2)

| Symptom | Likely cause | Fix |
|---|---|---|
| No IP after `up` | Profile not active | Re-run `con up` |
| No route | Address/method wrong | Recheck `ipv4.*` |

---

## ✅ Lab Checklist

- [ ] Task 1 · Step 1 — Create the profile with `nmcli con add`
- [ ] Task 1 · Step 2 — Refine with `nmcli con mod`
- [ ] Task 2 · Step 1 — Activate with `nmcli con up`
- [ ] Task 2 · Step 2 — Inspect routes with `ip route`
- [ ] Every 🎯 Focus Coverage row (Anchor + NEW) mapped to a step
- [ ] 🧹 Teardown run — sandbox + **profile and dummy interface removed**

---

## 🧹 Teardown

**In plain English:** Delete the test profile and dummy interface, then the marker sandbox.

> This lab changed system state (added the `lab-static` profile and `dummy0`). These commands **reverse** it; your real connection was never touched.

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
| `ip addr add` instead of nmcli | Not persistent | Use `nmcli con` profiles |
| Editing the real NIC | Lose SSH | Practice on `dummy0` |
| Forgetting `con up` | Settings not live | Activate the profile |

---

## 📌 Exam Strategy

Static IP = NetworkManager profile: `nmcli con add ... ipv4.method manual`, set address/gateway/DNS with `con mod`, activate with `con up`. Verify with `ip addr`/`ip route`. Profiles persist; raw `ip` commands do not.

- Always configure via `nmcli con`, never transient `ip addr add`.
- `ipv4.method manual` + addresses/gateway/dns is the full set.
- `nmcli -g` gives clean values for scripting.

---

## 🔗 Related Labs

- [Lab 31b — Configure a Static IP (Ansible)](../lab-31b-static-ip-nmcli-ansible/) — the `community.general.nmcli` module
- [Lab 31c — Configure a Static IP (Verify)](../lab-31c-static-ip-nmcli-verify/) — prove the address and persistence
- [Lab 33a — Display IP and Routing Info (RHCSA)](../lab-33a-ip-addr-route-show-rhcsa/) — reading what you configured

---

## 👤 Author

**Kelvin R. Tobias**  
[kelvinintech.com](https://kelvinintech.com) · [GitHub](https://github.com/kelvintechnical) · [LinkedIn](https://www.linkedin.com/in/kelvin-r-tobias-211949219)
