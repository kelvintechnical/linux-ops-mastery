# Lab 35c: Text-Based Network Config (Verify) — prove TUI results

**Series:** linux-ops-mastery — Networking · **Lab 35c of the Novice → RHCA path**  
**Certifications covered:** RHCSA EX200 (verify network/hostname config), SRE (config drift detection)  
**Prerequisite:** [Lab 35b](../lab-35b-nmtui-tui-config-ansible/) completed  
**Time Estimate:** 20–30 minutes  
**Difficulty:** Beginner → Intermediate

---

## 🎯 Today's Focus Coverage

> Stay on-subject via the ANCHOR rows; expand vocabulary via the NEW rows. Every row is exercised by a STEP below.

**⚓ Anchor — already learned (on-topic reuse)**

| # | Command / switch | Covered by |
|---|---|---|
| A1 | `nmcli con show` | _Task 1 · Step 1_ |
| A2 | `grep -q` assertions | _Task 1 · Step 2_ |

**🆕 NEW this lab — introduced for the first time** (minimum 3)

| # | Command / switch | First taught in | Covered by |
|---|---|---|---|
| N1 | `nmcli -g` field check | Task 1 · Step 1 | _Task 1 · Step 1_ |
| N2 | profile-on-disk check | Task 1 · Step 2 | _Task 1 · Step 2_ |
| N3 | `hostnamectl --static` check | Task 2 · Step 1 | _Task 2 · Step 1_ |
| N4 | live-vs-stored consistency | Task 2 · Step 2 | _Task 2 · Step 2_ |

---

## 🎯 Objective

Prove that whatever `nmtui` (or the equivalent play) configured is actually in effect. You will assert the connection's stored IPv4 matches expectations, confirm the profile exists on disk, verify the static hostname, and check that the live interface address agrees with the stored profile. These checks catch the classic "saved but not applied" gap.

---

## 🧠 Concept

`nmtui` writes a NetworkManager connection profile and (optionally) the hostname. Verification confirms three layers agree: **stored** (`nmcli -g FIELD con show NAME` reads a single field from the saved profile), **on-disk** (the keyfile under `/etc/NetworkManager/system-connections/`), and **live** (`ip addr` shows the address actually applied). The hostname has a parallel check: `hostnamectl --static` for the stored static name. The frequent bug is a profile saved but never activated, so stored and live disagree — comparing them is the key verification. Every check is extract-then-assert with a clear PASS/FAIL.

```
nmcli -g ipv4.addresses con show lab-tui   → stored IPv4
ls /etc/NetworkManager/system-connections/ → profile on disk
hostnamectl --static                        → stored hostname
ip -4 -br addr show dev dummy0              → live address (must match stored)
```

> **Why this matters:** "I set it in `nmtui`" isn't proof. Confirming stored == on-disk == live (and the hostname) is what distinguishes a real fix from a half-applied one.

---

## 📚 Command Reference

| Command | Purpose | Notes |
|---|---|---|
| `nmcli -g FIELD con show` | Read one field | stored value |
| `ls .../system-connections` | Profile on disk | keyfile present |
| `hostnamectl --static` | Stored hostname | persistent name |
| `ip -4 -br addr show dev` | Live address | must match stored |

---

## 🧰 LAB-WIDE SETUP

**In plain English:** Make the sandbox; checks read live config (assumes Lab 35a/b ran).

> Run this block **once** before Task 1.

```bash
export LAB_ROOT=/tmp/lab-35
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

## TASK 1 of 2 — Prove the connection profile

**In plain English:** We assert the stored IPv4 and that the profile exists on disk.

---

### Step 1 of 2 — Assert the stored IPv4

**In plain English:** We read the saved address field and require the expected value.

```bash
GOT=$(nmcli -g ipv4.addresses con show lab-tui 2>/dev/null)
echo "stored: $GOT"
[ "$GOT" = "10.55.55.3/24" ] && echo "PASS: stored IPv4 correct" || echo "FAIL: got '$GOT'"
```

**Expected output:**

```
stored: 10.55.55.3/24
PASS: stored IPv4 correct
```

**Line-by-line breakdown:**

- `nmcli -g ipv4.addresses con show lab-tui` → Reads exactly one field from the stored profile (no parsing noise).
- `[ "$GOT" = ... ]` → Strict equality check against the expected address.

**New words in this step:**

- **`nmcli -g`** — get a single field's value, ideal for scripted checks.

---

### Step 2 of 2 — Confirm the profile exists on disk

**In plain English:** We check the keyfile NetworkManager wrote for the connection.

```bash
if sudo ls /etc/NetworkManager/system-connections/ 2>/dev/null | grep -q 'lab-tui'; then
  echo "PASS: lab-tui profile on disk"
else
  echo "FAIL: profile keyfile missing"
fi
```

**Expected output:**

```
PASS: lab-tui profile on disk
```

**Line-by-line breakdown:**

- `ls .../system-connections/ | grep -q 'lab-tui'` → Confirms the persistent keyfile exists — the profile survives reboot.

**New words in this step:**

- **keyfile** — the on-disk file NetworkManager stores a connection profile in.

---

### Concept card (Task 1)

| Concept | What it does | Exam trap |
|---|---|---|
| `-g` field | stored value | exact compare |
| keyfile | persistence | survives reboot |
| stored layer | what's saved | not necessarily live |

---

### Troubleshoot (Task 1)

| Symptom | Likely cause | Fix |
|---|---|---|
| Empty `$GOT` | Profile missing | Re-run Lab 35a/b |
| No keyfile | Not saved | Re-create the profile |

---

## TASK 2 of 2 — Prove hostname and live state

**In plain English:** We verify the static hostname and that live matches stored.

---

### Step 1 of 2 — Assert the static hostname

**In plain English:** We confirm the persistent hostname is what we set.

```bash
HN=$(hostnamectl --static status 2>/dev/null)
echo "static hostname: $HN"
[ "$HN" = "labhost.example.com" ] && echo "PASS: hostname correct" || echo "INFO: hostname is '$HN'"
```

**Expected output:**

```
static hostname: labhost.example.com
PASS: hostname correct
```

**Line-by-line breakdown:**

- `hostnamectl --static status` → Prints just the stored static hostname.
- `[ "$HN" = ... ]` → Strict check against the expected name.

**New words in this step:**

- **static hostname check** — verifying the persistent name, not the transient one.

---

### Step 2 of 2 — Confirm live matches stored

**In plain English:** We compare the address on the live interface to the stored profile.

```bash
STORED=$(nmcli -g ipv4.addresses con show lab-tui 2>/dev/null)
LIVE=$(ip -4 -br addr show dev dummy0 2>/dev/null | awk '{print $3}')
echo "stored: $STORED  live: $LIVE"
if [ "${STORED%% *}" = "$LIVE" ]; then
  echo "PASS: live matches stored"
else
  echo "FAIL: saved but not applied (activate with nmcli con up)"
fi
```

**Expected output:**

```
stored: 10.55.55.3/24  live: 10.55.55.3/24
PASS: live matches stored
```

**Line-by-line breakdown:**

- `ip -4 -br addr show dev dummy0 | awk '{print $3}'` → The address actually applied to the live interface.
- `[ "${STORED%% *}" = "$LIVE" ]` → Compares stored vs live, catching the "saved but not activated" bug.

**New words in this step:**

- **stored-vs-live consistency** — the address on disk must match the one in effect.

---

### Concept card (Task 2)

| Concept | What it does | Exam trap |
|---|---|---|
| static hostname | persistent name | vs transient |
| live vs stored | applied? | saved ≠ active |
| `con up` | apply | needed after edits |

---

### Troubleshoot (Task 2)

| Symptom | Likely cause | Fix |
|---|---|---|
| live empty | Not activated | `nmcli con up lab-tui` |
| Mismatch | Edited not applied | Reload + activate |

---

## ✅ Lab Checklist

- [ ] Task 1 · Step 1 — Assert the stored IPv4
- [ ] Task 1 · Step 2 — Confirm the profile exists on disk
- [ ] Task 2 · Step 1 — Assert the static hostname
- [ ] Task 2 · Step 2 — Confirm live matches stored
- [ ] Every 🎯 Focus Coverage row (Anchor + NEW) mapped to a step
- [ ] 🧹 Teardown run — sandbox + dummy profile removed

---

## 🧹 Teardown

**In plain English:** Remove the dummy profile, restore hostname, clear the sandbox.

> This lab only read state, but it shares the dummy profile/hostname from Labs 35a/b — clean them here.

```bash
sudo nmcli con down lab-tui 2>/dev/null || true
sudo nmcli con delete lab-tui 2>/dev/null || true
# Restore your original hostname if needed:
# sudo hostnamectl set-hostname your-original-hostname
cd /tmp
bash lab_teardown.sh "$LAB_ROOT"     # = /tmp/lab-35
```

**Expected output:**

```
Connection 'lab-tui' (...) successfully deleted.
✅ Removed /tmp/lab-35 — lab workspace is clean.
```

---

## ⚠️ Common Pitfalls

| Mistake | Symptom | Fix |
|---|---|---|
| Checking only stored | Misses live drift | Compare live too |
| Transient hostname | Reverts on reboot | Verify `--static` |
| CIDR vs bare IP mismatch | False FAIL | Strip mask before compare |

---

## 📌 Exam Strategy

Verify three layers: stored (`nmcli -g`), on-disk (keyfile), and live (`ip addr`) — plus the static hostname. The classic failure is stored ≠ live (saved but not activated); comparing them is the decisive check.

- `nmcli -g` for clean single-field reads.
- Keyfile presence proves persistence.
- Live must equal stored, or you forgot `nmcli con up`.

---

## 🔗 Related Labs

- [Lab 35a — Text-Based Network Config (RHCSA)](../lab-35a-nmtui-tui-config-rhcsa/) — the `nmtui` work these checks verify
- [Lab 35b — Text-Based Network Config (Ansible)](../lab-35b-nmtui-tui-config-ansible/) — the declarative version
- [Lab 36c — Command-Line Network Config (Verify)](../lab-36c-nmcli-cli-config-verify/) — deeper `nmcli` verification

---

## 👤 Author

**Kelvin R. Tobias**  
[kelvinintech.com](https://kelvinintech.com) · [GitHub](https://github.com/kelvintechnical) · [LinkedIn](https://www.linkedin.com/in/kelvin-r-tobias-211949219)
