# Lab 35a: Text-Based Network Config (RHCSA) — `nmtui`

**Series:** linux-ops-mastery — Networking · **Lab 35a of the Novice → RHCA path**  
**Certifications covered:** RHCSA EX200 (configure networking with `nmtui`), SRE/DevOps (quick console fixes on headless boxes)  
**Prerequisite:** [Lab 34c](../lab-34c-ss-listening-sockets-verify/) completed  
**Time Estimate:** 25–35 minutes  
**Difficulty:** Beginner

---

## 🎯 Today's Focus Coverage

> Stay on-subject via the ANCHOR rows; expand vocabulary via the NEW rows. Every row is exercised by a STEP below.

**⚓ Anchor — already learned (on-topic reuse)**

| # | Command / switch | Covered by |
|---|---|---|
| A1 | `nmcli con show` (from Lab 31) | _Task 1 · Step 2_ |
| A2 | `ip addr` verification | _Task 2 · Step 2_ |

**🆕 NEW this lab — introduced for the first time** (minimum 3)

| # | Command / switch | First taught in | Covered by |
|---|---|---|---|
| N1 | `nmtui` (menu launcher) | Task 1 · Step 1 | _Task 1 · Step 1_ |
| N2 | `nmtui-edit` / `nmtui-connect` | Task 1 · Step 2 | _Task 1 · Step 2_ |
| N3 | `nmtui-hostname` | Task 2 · Step 1 | _Task 2 · Step 1_ |
| N4 | `nmcli con reload` (apply) | Task 2 · Step 2 | _Task 2 · Step 2_ |

---

## 🎯 Objective

Use NetworkManager's text UI to configure networking without memorizing every `nmcli` flag — the RHCSA-friendly path on a console. You'll launch `nmtui` and its direct sub-screens (`nmtui-edit`, `nmtui-connect`, `nmtui-hostname`), understand what each does, and verify the results with `nmcli`/`ip`. Because `nmtui` is interactive, we pair every screen with the non-interactive command that proves the outcome.

> **Safety note:** This lab uses a throwaway **dummy** connection (`lab-tui` on `dummy0`) so nothing touches your real NIC. Teardown removes it. On the exam you'd edit the real interface.

---

## 🧠 Concept

`nmtui` is a curses (text) front-end to NetworkManager — the same engine `nmcli` drives. It's ideal when you're on a console with no GUI and don't want to recall flags. Running `nmtui` opens a menu with three choices: **Edit a connection**, **Activate a connection**, and **Set system hostname**. Each has a direct launcher: `nmtui-edit`, `nmtui-connect`, and `nmtui-hostname` — handy for jumping straight in or scripting which screen opens. Whatever you change in `nmtui` is stored as a NetworkManager connection profile (under `/etc/NetworkManager/system-connections/`), identical to what `nmcli con mod` writes — so `nmcli con show` and `ip addr` verify `nmtui`'s work. The TUI is a convenience layer, not a separate system.

```
nmtui            → menu: Edit / Activate / Set hostname
nmtui-edit NAME  → jump straight to editing a connection
nmtui-connect    → activate/deactivate a connection
nmtui-hostname   → set the static hostname
nmcli con show   → verify what nmtui saved (same backend)
```

> **Why this matters:** On a headless server with a broken network, `nmtui` is the fastest reliable way to fix addressing without a flag reference. RHCSA explicitly expects you to configure networking, and `nmtui` is an accepted, low-error method.

---

## 📚 Command Reference

| Command | Purpose | Notes |
|---|---|---|
| `nmtui` | Open the menu | full TUI |
| `nmtui-edit [NAME]` | Edit a connection | direct screen |
| `nmtui-connect [NAME]` | Activate/deactivate | direct screen |
| `nmtui-hostname` | Set hostname | direct screen |
| `nmcli con show` | Verify profiles | same backend |
| `nmcli con reload` | Reload from disk | apply edits |

---

## 🧰 LAB-WIDE SETUP

**In plain English:** Create the sandbox and a safe dummy connection for `nmtui` to edit.

> Run this block **once** before Task 1. It creates a disposable `lab-tui` profile on a virtual `dummy0` device so the exercises never disturb your real NIC.

```bash
export LAB_ROOT=/tmp/lab-35
mkdir -p "$LAB_ROOT"
sudo modprobe dummy 2>/dev/null || true
sudo nmcli con add type dummy ifname dummy0 con-name lab-tui ipv4.method manual ipv4.addresses 10.55.55.2/24 2>/dev/null
nmcli con show lab-tui >/dev/null && echo "lab-tui ready"
echo "exit was: $?"
```

**Expected output:**

```
lab-tui ready
exit was: 0
```

---

## TASK 1 of 2 — Edit a connection in the TUI

**In plain English:** We open `nmtui`, then jump straight to editing our dummy connection.

---

### Step 1 of 2 — Launch the `nmtui` menu

**In plain English:** We open the main text UI and note its three options.

```bash
# Interactive — opens a full-screen menu:
nmtui
# Menu shows:
#   Edit a connection
#   Activate a connection
#   Set system hostname
# Use arrows + Enter; choose "Edit a connection", then Back/Quit to exit.
echo "nmtui closed, exit was: $?"
```

**Expected output:**

```
(full-screen text menu appears; after you Quit:)
nmtui closed, exit was: 0
```

**Line-by-line breakdown:**

- `nmtui` → Opens the curses menu; navigate with arrows/Tab and Enter. Quit returns to the shell with exit 0.
- The three menu items map exactly to the three `nmtui-*` direct launchers.

**New words in this step:**

- **`nmtui`** — the NetworkManager text user interface (curses menu).

---

### Step 2 of 2 — Jump straight to editing with `nmtui-edit`

**In plain English:** We open the edit screen for our dummy connection directly, then verify with `nmcli`.

```bash
# Interactive — opens the editor for lab-tui:
nmtui-edit lab-tui
# In the editor: set IPv4 to Manual, address 10.55.55.3/24, then OK/Back.
# Now verify non-interactively what nmtui saved:
nmcli -g ipv4.addresses con show lab-tui
```

**Expected output:**

```
(edit screen appears; after OK:)
10.55.55.3/24
```

**Line-by-line breakdown:**

- `nmtui-edit lab-tui` → Opens the editor directly on `lab-tui` — no menu navigation needed.
- `nmcli -g ipv4.addresses con show lab-tui` → Reads back exactly the field you set, proving `nmtui` wrote it.

**New words in this step:**

- **`nmtui-edit`** — direct launcher for the connection editor.

---

### Concept card (Task 1)

| Concept | What it does | Exam trap |
|---|---|---|
| `nmtui` | full menu | arrows + Enter |
| `nmtui-edit` | direct edit | takes a con name |
| `nmcli -g` | read one field | verify the save |

---

### Troubleshoot (Task 1)

| Symptom | Likely cause | Fix |
|---|---|---|
| `nmtui` blank/garbled | Bad TERM | `export TERM=xterm` |
| Edit not saved | Quit without OK | Re-edit, select OK |

---

## TASK 2 of 2 — Hostname and applying changes

**In plain English:** We set the hostname via the TUI launcher, then apply/activate changes.

---

### Step 1 of 2 — Set hostname with `nmtui-hostname`

**In plain English:** We open the hostname screen directly and verify with `hostnamectl`.

```bash
# Interactive — opens the hostname entry screen:
nmtui-hostname
# Type a hostname (e.g. labhost.example.com), select OK.
# Verify non-interactively:
hostnamectl status | grep -i 'hostname'
```

**Expected output:**

```
(hostname screen appears; after OK:)
   Static hostname: labhost.example.com
```

**Line-by-line breakdown:**

- `nmtui-hostname` → Direct screen to set the static hostname (same as `hostnamectl set-hostname`).
- `hostnamectl status | grep hostname` → Confirms the static hostname took effect.

> **Reset note:** Teardown restores your original hostname — capture it first if you run this on a real box.

**New words in this step:**

- **`nmtui-hostname`** — direct launcher for the system-hostname screen.

---

### Step 2 of 2 — Activate/reload the change

**In plain English:** We apply the saved profile so the new settings go live.

```bash
sudo nmcli con reload
sudo nmcli con up lab-tui
ip -4 -br addr show dev dummy0
echo "exit was: $?"
```

**Expected output:**

```
Connection successfully activated ...
dummy0           UP             10.55.55.3/24
exit was: 0
```

**Line-by-line breakdown:**

- `nmcli con reload` → Re-reads profiles from disk (picks up `nmtui` edits made on-disk).
- `nmcli con up lab-tui` → Activates the profile so the address is applied to `dummy0`.
- `ip -4 -br addr show dev dummy0` → Confirms the live address matches what you set in the TUI.

**New words in this step:**

- **`nmcli con reload` / `up`** — reload profiles from disk and activate one.

---

### Concept card (Task 2)

| Concept | What it does | Exam trap |
|---|---|---|
| `nmtui-hostname` | set hostname | static vs transient |
| `con reload` | re-read disk | after manual edits |
| `con up` | activate | apply to live iface |

---

### Troubleshoot (Task 2)

| Symptom | Likely cause | Fix |
|---|---|---|
| Address not applied | Not activated | `nmcli con up` |
| Hostname reverts | Transient only | Use static (nmtui sets static) |

---

## ✅ Lab Checklist

- [ ] Task 1 · Step 1 — Launch the `nmtui` menu
- [ ] Task 1 · Step 2 — Jump straight to editing with `nmtui-edit`
- [ ] Task 2 · Step 1 — Set hostname with `nmtui-hostname`
- [ ] Task 2 · Step 2 — Activate/reload the change
- [ ] Every 🎯 Focus Coverage row (Anchor + NEW) mapped to a step
- [ ] 🧹 Teardown run — sandbox + dummy connection removed

---

## 🧹 Teardown

**In plain English:** Remove the dummy connection and sandbox so the box is clean.

> This lab created a NetworkManager profile and (optionally) changed the hostname — both are reversed here. `lab_teardown.sh` clears the sandbox root.

```bash
sudo nmcli con down lab-tui 2>/dev/null || true
sudo nmcli con delete lab-tui 2>/dev/null || true
# If you changed the hostname, restore it (replace with your original):
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
| Editing real NIC by accident | Lost connectivity | Use the `lab-tui` dummy |
| Quitting without OK | Change not saved | Always confirm with OK |
| Not activating | Profile saved but inactive | `nmcli con up` |

---

## 📌 Exam Strategy

`nmtui` is the low-error way to configure networking on a console — perfect when you can't recall `nmcli` syntax. Remember the three direct launchers and always verify with `nmcli`/`ip` afterward.

- `nmtui` menu = Edit / Activate / Set hostname.
- `nmtui-edit`, `nmtui-connect`, `nmtui-hostname` jump straight in.
- Same backend as `nmcli` — verify your work with `nmcli con show`.

---

## 🔗 Related Labs

- [Lab 35b — Text-Based Network Config (Ansible)](../lab-35b-nmtui-tui-config-ansible/) — the declarative equivalent of TUI edits
- [Lab 35c — Text-Based Network Config (Verify)](../lab-35c-nmtui-tui-config-verify/) — prove the profile and hostname
- [Lab 36a — Command-Line Network Config (RHCSA)](../lab-36a-nmcli-cli-config-rhcsa/) — the `nmcli` flags `nmtui` hides

---

## 👤 Author

**Kelvin R. Tobias**  
[kelvinintech.com](https://kelvinintech.com) · [GitHub](https://github.com/kelvintechnical) · [LinkedIn](https://www.linkedin.com/in/kelvin-r-tobias-211949219)
