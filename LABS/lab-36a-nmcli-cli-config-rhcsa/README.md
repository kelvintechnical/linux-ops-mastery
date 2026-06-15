# Lab 36a: Command-Line Network Config (RHCSA) — `nmcli`

**Series:** linux-ops-mastery — Networking · **Lab 36a of the Novice → RHCA path**  
**Certifications covered:** RHCSA EX200 (configure networking with `nmcli`), SRE/DevOps (scripted network changes)  
**Prerequisite:** [Lab 35c](../lab-35c-nmtui-tui-config-verify/) completed  
**Time Estimate:** 30–40 minutes  
**Difficulty:** Beginner → Intermediate

---

## 🎯 Today's Focus Coverage

> Stay on-subject via the ANCHOR rows; expand vocabulary via the NEW rows. Every row is exercised by a STEP below.

**⚓ Anchor — already learned (on-topic reuse)**

| # | Command / switch | Covered by |
|---|---|---|
| A1 | `nmcli con add/up` (from Lab 31) | _Task 1 · Step 1_ |
| A2 | `ip addr` verification | _Task 2 · Step 2_ |

**🆕 NEW this lab — introduced for the first time** (minimum 3)

| # | Command / switch | First taught in | Covered by |
|---|---|---|---|
| N1 | `nmcli dev status` / `gen` | Task 1 · Step 1 | _Task 1 · Step 1_ |
| N2 | `nmcli con show NAME` (detail) | Task 1 · Step 2 | _Task 1 · Step 2_ |
| N3 | `nmcli con mod +ipv4.x` (add/remove) | Task 2 · Step 1 | _Task 2 · Step 1_ |
| N4 | `nmcli con mod ipv4.method auto` (toggle) | Task 2 · Step 2 | _Task 2 · Step 2_ |

---

## 🎯 Objective

Master `nmcli` for fast, scriptable network configuration — the CLI behind `nmtui` and the RHCSA's preferred tool. You'll survey device and connection state, read a profile's full settings, modify individual IPv4 properties (including the `+`/`-` syntax to add/remove list values), and toggle a connection between manual and automatic addressing. Everything runs on a safe dummy interface.

> **Safety note:** This lab uses a throwaway **dummy** connection (`lab-cli` on `dummy0`). Teardown removes it; your real NIC is untouched.

---

## 🧠 Concept

`nmcli` has four object types you'll use constantly: `nmcli general` (NM status), `nmcli device` (`dev`) for hardware/interface state, `nmcli connection` (`con`) for saved profiles, and `nmcli` (radio/networking) for on/off. The workflow is **add → modify → activate**: `nmcli con add` creates a profile, `nmcli con mod` changes properties, `nmcli con up` applies it. Properties use dotted names (`ipv4.addresses`, `ipv4.gateway`, `ipv4.dns`, `ipv4.method`). For list-valued properties, plain `mod ipv4.dns X` *replaces*, while `mod +ipv4.dns X` *appends* and `mod -ipv4.dns X` *removes* — a frequent exam subtlety. `ipv4.method manual` means static (requires addresses); `auto` means DHCP. `nmcli con show NAME` dumps every setting for inspection. Crucially, `nmcli con mod` only edits the stored profile — you must `nmcli con up` (or reactivate) to apply changes to the live interface.

```
nmcli dev status              → interfaces + their connection
nmcli con show               → list profiles
nmcli con show lab-cli       → full settings of one profile
nmcli con mod lab-cli +ipv4.dns 1.1.1.1   → APPEND a DNS server
nmcli con mod lab-cli ipv4.method auto    → switch to DHCP
nmcli con up lab-cli         → apply changes to the live interface
```

> **Why this matters:** `nmcli` is the exam's go-to for networking and the only practical way to script network changes across servers. The add/modify/activate flow and the `+`/`-` list syntax are exactly what gets tested and used daily.

---

## 📚 Command Reference

| Command | Purpose | Notes |
|---|---|---|
| `nmcli general status` | NM overall state | connectivity |
| `nmcli dev status` | Device/iface state | + bound con |
| `nmcli con show [NAME]` | List / detail | profiles |
| `nmcli con add` | Create profile | type/ifname |
| `nmcli con mod` | Change property | dotted names |
| `nmcli con mod +X / -X` | Append / remove | list values |
| `nmcli con up/down` | Activate/deactivate | apply changes |

---

## 🧰 LAB-WIDE SETUP

**In plain English:** Create the sandbox and a safe dummy connection to configure.

> Run this block **once** before Task 1.

```bash
export LAB_ROOT=/tmp/lab-36
mkdir -p "$LAB_ROOT"
sudo modprobe dummy 2>/dev/null || true
sudo nmcli con add type dummy ifname dummy0 con-name lab-cli \
  ipv4.method manual ipv4.addresses 10.66.66.2/24 ipv4.dns 10.66.66.53 2>/dev/null
nmcli con show lab-cli >/dev/null && echo "lab-cli ready"
echo "exit was: $?"
```

**Expected output:**

```
lab-cli ready
exit was: 0
```

---

## TASK 1 of 2 — Survey state and inspect a profile

**In plain English:** We look at devices and connections, then read one profile in full.

---

### Step 1 of 2 — Survey devices and connections

**In plain English:** We list interface state and saved profiles.

```bash
nmcli general status
echo "--- devices ---"
nmcli dev status
echo "--- connections ---"
nmcli con show | head
```

**Expected output:**

```
STATE      CONNECTIVITY  WIFI-HW  WIFI  WWAN-HW  WWAN
connected  full          ...
--- devices ---
DEVICE   TYPE      STATE         CONNECTION
dummy0   dummy     connected     lab-cli
eth0     ethernet  connected     eth0
lo       loopback  unmanaged     --
--- connections ---
NAME    UUID                                  TYPE      DEVICE
lab-cli ...                                   dummy     dummy0
```

**Line-by-line breakdown:**

- `nmcli general status` → Overall NetworkManager state and connectivity.
- `nmcli dev status` → Each interface, its type, state, and the connection bound to it.
- `nmcli con show` → All saved profiles and which device (if any) each is active on.

**New words in this step:**

- **device vs connection** — hardware/interface (`dev`) vs the saved profile (`con`).

---

### Step 2 of 2 — Inspect one profile in full

**In plain English:** We dump every setting of our dummy profile and read key fields.

```bash
nmcli con show lab-cli | grep -E 'ipv4.method|ipv4.addresses|ipv4.dns'
```

**Expected output:**

```
ipv4.method:                            manual
ipv4.addresses:                         10.66.66.2/24
ipv4.dns:                               10.66.66.53
```

**Line-by-line breakdown:**

- `nmcli con show lab-cli` → Prints the complete property list for the profile.
- `grep -E 'ipv4.method|...'` → Focus on the addressing fields we care about.

**New words in this step:**

- **dotted property** — settings like `ipv4.addresses` you read and set by name.

---

### Concept card (Task 1)

| Concept | What it does | Exam trap |
|---|---|---|
| `dev status` | iface state | shows bound con |
| `con show NAME` | full settings | dotted names |
| general status | NM health | connectivity |

---

### Troubleshoot (Task 1)

| Symptom | Likely cause | Fix |
|---|---|---|
| Device `unmanaged` | NM not managing it | Check NM config |
| Profile not shown | Wrong name | `nmcli con show` to list |

---

## TASK 2 of 2 — Modify and toggle addressing

**In plain English:** We append/remove a DNS server, then switch between manual and auto.

---

### Step 1 of 2 — Append and remove list values

**In plain English:** We add a second DNS server with `+`, then remove it with `-`.

```bash
sudo nmcli con mod lab-cli +ipv4.dns 10.66.66.54
nmcli -g ipv4.dns con show lab-cli
sudo nmcli con mod lab-cli -ipv4.dns 10.66.66.54
nmcli -g ipv4.dns con show lab-cli
```

**Expected output:**

```
10.66.66.53,10.66.66.54
10.66.66.53
```

**Line-by-line breakdown:**

- `con mod lab-cli +ipv4.dns 10.66.66.54` → `+` **appends** to the DNS list (plain `mod` would replace it).
- `con mod lab-cli -ipv4.dns 10.66.66.54` → `-` **removes** that one value, leaving the original.

**New words in this step:**

- **`+`/`-` modifiers** — append/remove a single value from a list property.

---

### Step 2 of 2 — Toggle manual ↔ auto and apply

**In plain English:** We switch the method to auto, then back to manual, applying each.

```bash
sudo nmcli con mod lab-cli ipv4.method auto
sudo nmcli con up lab-cli >/dev/null
nmcli -g ipv4.method con show lab-cli
# switch back to static and re-apply:
sudo nmcli con mod lab-cli ipv4.method manual ipv4.addresses 10.66.66.2/24
sudo nmcli con up lab-cli >/dev/null
ip -4 -br addr show dev dummy0
```

**Expected output:**

```
auto
dummy0           UP             10.66.66.2/24
```

**Line-by-line breakdown:**

- `con mod ... ipv4.method auto` → Switch to DHCP-style addressing (stored only until activated).
- `con up lab-cli` → Apply the change to the live interface — edits aren't live until you do this.
- Back to `manual` + `con up` → Restore the static address and confirm with `ip`.

**New words in this step:**

- **method auto/manual** — DHCP vs static; `manual` requires an address.

---

### Concept card (Task 2)

| Concept | What it does | Exam trap |
|---|---|---|
| `+`/`-` | list edit | plain `mod` replaces |
| `method` | static/DHCP | manual needs address |
| `con up` | apply | mod alone isn't live |

---

### Troubleshoot (Task 2)

| Symptom | Likely cause | Fix |
|---|---|---|
| Change not live | Didn't activate | `nmcli con up` |
| `manual` rejected | No address set | Provide `ipv4.addresses` |

---

## ✅ Lab Checklist

- [ ] Task 1 · Step 1 — Survey devices and connections
- [ ] Task 1 · Step 2 — Inspect one profile in full
- [ ] Task 2 · Step 1 — Append and remove list values
- [ ] Task 2 · Step 2 — Toggle manual ↔ auto and apply
- [ ] Every 🎯 Focus Coverage row (Anchor + NEW) mapped to a step
- [ ] 🧹 Teardown run — sandbox + dummy connection removed

---

## 🧹 Teardown

**In plain English:** Remove the dummy connection and sandbox so the box is clean.

> This lab created a NetworkManager profile — removed here. `lab_teardown.sh` clears the sandbox root.

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
| `mod` instead of `+mod` | Replaced whole list | Use `+`/`-` for lists |
| Forgetting `con up` | Edit not applied | Activate the profile |
| `manual` without address | Activation fails | Set `ipv4.addresses` |

---

## 📌 Exam Strategy

Internalize add → modify → activate and the dotted property names. The two classic traps: list edits need `+`/`-` (plain `mod` replaces), and `con mod` is not live until `con up`.

- `nmcli dev status` / `con show NAME` to survey.
- `+ipv4.dns`/`-ipv4.dns` to append/remove.
- `con up` to apply — always verify with `ip addr`.

---

## 🔗 Related Labs

- [Lab 36b — Command-Line Network Config (Ansible)](../lab-36b-nmcli-cli-config-ansible/) — the same config declaratively
- [Lab 36c — Command-Line Network Config (Verify)](../lab-36c-nmcli-cli-config-verify/) — prove profile properties
- [Lab 35a — Text-Based Network Config (RHCSA)](../lab-35a-nmtui-tui-config-rhcsa/) — the `nmtui` front-end to these commands

---

## 👤 Author

**Kelvin R. Tobias**  
[kelvinintech.com](https://kelvinintech.com) · [GitHub](https://github.com/kelvintechnical) · [LinkedIn](https://www.linkedin.com/in/kelvin-r-tobias-211949219)
