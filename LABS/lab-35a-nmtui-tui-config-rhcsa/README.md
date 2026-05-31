# Lab 35a: Text-Based Network Config (RHCSA) — `nmtui`, `nmtui-edit`, `nmtui-connect`, `nmtui-hostname`

- **Series:** linux-ops-mastery — NetworkManager and Host Identity
- **Trilogy:** **`35a`** (RHCSA hand-typed, TUI + CLI parity) → [`35b`](../lab-35b-nmtui-tui-config-ansible/) (Ansible boundary replacement) → [`35c`](../lab-35c-nmtui-tui-config-verify/) (verify capstone: audit + destroy-restore)
- **Time Estimate:** 35-45 minutes
- **Tasks:** 2 (Task 1 = `nmtui-hostname` interactive vs scriptable hostname flow with teardown; Task 2 = `nmtui-edit` field-by-field to `nmcli con mod` mapping)
- **Practice Directory (rotation #35):** `/tmp`
- **Sandbox (Tier B):** `/tmp/lab35a` with `USER=labuser_35_nmtui`, `GROUP=labgrp_35_nmtui`, `USER_HOME=/tmp/lab35a/home_labuser_35_nmtui`
- **Traps rehearsed:** **T35-A** (`nmtui` is interactive only; automation must use `nmcli`) · **T35-B** (`nmtui-hostname` persistent hostname differs from transient runtime behavior) · **T41** · **T44**

> **Boundary focus:** `nmtui` is excellent for humans at a terminal, but it is not scriptable. Every TUI action in this lab is paired with an `nmcli` equivalent you can automate later.

---

## LAB HEADER BLOCK

```bash
echo "🖥️  ENV:   ${ENV:-DECLARE_ME}"
echo "🕒  TIME:  $(date -Is)"
echo "👤  USER:  $(whoami)@$(hostname)"
echo "⚠️  TRAP REMINDERS THIS LAB: T35-A T35-B T41 T44"
echo "📁  PRACTICE DIR: /tmp"
ls -ld /tmp
nmcli --version
nmtui --version 2>/dev/null || echo "nmtui has no --version banner on this build"
```

> **STOP — paste header output before setup.**

---

## Objective

1. Use `nmtui-hostname` and `nmtui` menus confidently for host/network edits.
2. Translate each TUI screen action into an `nmcli` command.
3. Internalize boundary T35-A: interactive tools are for operators, not automation.
4. Rehearse safe teardown using the original hostname.

---

## Lab-Wide Setup — Tier B Sandbox Stack (Section 1.5)

```bash
sudo -i

export LAB_NUM=35
export LAB_SLUG=nmtui
export SANDBOX=/tmp/lab35a
export GROUP=labgrp_${LAB_NUM}_${LAB_SLUG}
export USER=labuser_${LAB_NUM}_${LAB_SLUG}
export USER_HOME=${SANDBOX}/home_${USER}

mkdir -p "${SANDBOX}" "${USER_HOME}"
mkdir -p /root/rhcsa_journal/lab-35a/task1 /root/rhcsa_journal/lab-35a/task2

getent group  "${GROUP}" >/dev/null || groupadd "${GROUP}"
getent passwd "${USER}"  >/dev/null || useradd -d "${USER_HOME}" -M -s /bin/bash -g "${GROUP}" "${USER}"
chown -R "${USER}:${GROUP}" "${SANDBOX}"

ORIG_HOST="$(hostnamectl --static)"
echo "${ORIG_HOST}" > /tmp/lab35a/original-hostname.txt

id "${USER}"
ls -ld "${SANDBOX}" "${USER_HOME}"
hostnamectl status --static
cat /tmp/lab35a/original-hostname.txt
```

---

## Task 1 — `nmtui-hostname` scriptable form vs interactive walkthrough

### Purpose

Practice both sides of hostname work:

- scriptable form: `nmtui-hostname new-host`
- interactive form: `nmtui` menu path `Set system hostname`

Then restore the original hostname with `hostnamectl`.

### Main command block

```bash
TASKLOG=/tmp/lab35a/task1.txt
ORIG_HOST="$(cat /tmp/lab35a/original-hostname.txt)"
NEW_HOST="lab35a-nmtui"

echo "═══ Part A: scriptable nmtui-hostname form ═══"                  2>&1 | tee "$TASKLOG"
nmtui-hostname "${NEW_HOST}"                                          2>&1 | tee -a "$TASKLOG"
hostnamectl --static                                                   | tee -a "$TASKLOG"
hostname                                                               | tee -a "$TASKLOG"

echo "═══ Part B: interactive nmtui walkthrough (manual) ═══"          | tee -a "$TASKLOG"
cat <<'EOF' | tee -a "$TASKLOG"
Open menu:
  1) run: nmtui
  2) arrow down to: "Set system hostname" -> Enter
  3) type: lab35a-interactive
  4) Tab to <OK> -> Enter
  5) Tab to <Quit> -> Enter
EOF

echo "After manual TUI step, verify immediately:"                      | tee -a "$TASKLOG"
hostnamectl --static                                                   | tee -a "$TASKLOG"
hostname                                                               | tee -a "$TASKLOG"

echo "═══ Part C: teardown back to original (required) ═══"            | tee -a "$TASKLOG"
hostnamectl set-hostname "${ORIG_HOST}"
hostnamectl --static                                                   | tee -a "$TASKLOG"
hostname                                                               | tee -a "$TASKLOG"

echo "exit was: $?"                                                    | tee -a "$TASKLOG"
```

### TUI vs CLI parity card

| `nmtui` screen/action | Equivalent CLI |
|---|---|
| `Set system hostname` save | `nmcli general hostname <new-host>` (or `hostnamectl set-hostname <new-host>`) |
| Verify current hostname | `hostnamectl --static` and `hostname` |
| Restore prior value | `hostnamectl set-hostname "$(cat /tmp/lab35a/original-hostname.txt)"` |

### Trap callout

- **T35-A:** There is no non-interactive automation channel inside the TUI flow itself.
- **T35-B:** A permanent hostname write and a transient runtime name are not the same concept; always verify via `hostnamectl --static` and plain `hostname`.

### Journal write

```bash
LAB=lab-35a
TASK=task1
JDIR="/root/rhcsa_journal/${LAB}/${TASK}"
mkdir -p "$JDIR"
cp /tmp/lab35a/task1.txt "$JDIR/evidence.txt"
cp /tmp/lab35a/original-hostname.txt "$JDIR/original-hostname.txt"
```

---

## Task 2 — `nmtui-edit` fields mapped to `nmcli con mod`

### Purpose

Treat `nmtui-edit` as a visual front-end and learn the exact `nmcli` knobs for every common field.

### Main command block

```bash
TASKLOG=/tmp/lab35a/task2.txt
CON_NAME="$(nmcli -t -f NAME con show --active | head -n 1)"

echo "Active connection: ${CON_NAME}"                                  2>&1 | tee "$TASKLOG"
nmcli con show "${CON_NAME}"                                           2>&1 | tee -a "$TASKLOG"

echo "Manual TUI drill (do not skip):"                                 | tee -a "$TASKLOG"
cat <<EOF | tee -a "$TASKLOG"
1) run: nmtui-edit "${CON_NAME}"
2) visit IPv4 CONFIGURATION, Addresses, Gateway, DNS
3) visit "Automatically connect"
4) review profile name then cancel out without destructive edits
EOF

echo "Equivalent nmcli examples (safe demonstrations):"                | tee -a "$TASKLOG"
echo "nmcli con mod \"${CON_NAME}\" connection.autoconnect yes"        | tee -a "$TASKLOG"
echo "nmcli con mod \"${CON_NAME}\" ipv4.method manual"                | tee -a "$TASKLOG"
echo "nmcli con mod \"${CON_NAME}\" ipv4.addresses 192.0.2.35/24"      | tee -a "$TASKLOG"
echo "nmcli con mod \"${CON_NAME}\" ipv4.gateway 192.0.2.1"            | tee -a "$TASKLOG"
echo "nmcli con mod \"${CON_NAME}\" ipv4.dns \"1.1.1.1 8.8.8.8\""      | tee -a "$TASKLOG"
echo "nmcli con mod \"${CON_NAME}\" ipv6.method auto"                  | tee -a "$TASKLOG"
echo "nmcli con up  \"${CON_NAME}\""                                   | tee -a "$TASKLOG"

nmcli -f NAME,TYPE,AUTOCONNECT con show "${CON_NAME}"                  | tee -a "$TASKLOG"
echo "exit was: $?"                                                    | tee -a "$TASKLOG"
```

### `nmtui-edit` field map

| TUI field | `nmcli` equivalent |
|---|---|
| Profile name | `nmcli con mod <name> connection.id <new-name>` |
| Device binding | `nmcli con mod <name> connection.interface-name <ifname>` |
| Automatic connect | `nmcli con mod <name> connection.autoconnect yes|no` |
| IPv4 method | `nmcli con mod <name> ipv4.method auto|manual|disabled` |
| IPv4 addresses | `nmcli con mod <name> ipv4.addresses <CIDR>` |
| IPv4 gateway | `nmcli con mod <name> ipv4.gateway <GW_IP>` |
| IPv4 DNS | `nmcli con mod <name> ipv4.dns "IP1 IP2"` |
| IPv6 method | `nmcli con mod <name> ipv6.method auto|manual|ignore|disabled` |
| Save/apply | `nmcli con up <name>` |

### Journal write

```bash
LAB=lab-35a
TASK=task2
JDIR="/root/rhcsa_journal/${LAB}/${TASK}"
mkdir -p "$JDIR"
cp /tmp/lab35a/task2.txt "$JDIR/evidence.txt"
```

---

## Lab Closeout — Bulletproof Teardown (Section 6)

```bash
set +e

ORIG_HOST="$(cat /tmp/lab35a/original-hostname.txt 2>/dev/null)"
test -n "${ORIG_HOST}" && hostnamectl set-hostname "${ORIG_HOST}"

awk -v s="${SANDBOX}" '$2 ~ s {print $2}' /proc/mounts | tac | xargs -r -n1 umount -l 2>/dev/null
if getent passwd "${USER}" >/dev/null 2>&1; then userdel -r "${USER}" 2>/dev/null; fi
if getent group "${GROUP}" >/dev/null 2>&1; then groupdel "${GROUP}" 2>/dev/null; fi
rm -rf "${SANDBOX}"

echo "── Lab 35a cleanup audit ──"
getent passwd "${USER}" >/dev/null && echo "❌ user remains"   || echo "✅ user gone"
getent group  "${GROUP}" >/dev/null && echo "❌ group remains" || echo "✅ group gone"
test -d "${SANDBOX}"               && echo "❌ sandbox remains"|| echo "✅ sandbox gone"
test -d "${USER_HOME}"             && echo "❌ home remains"   || echo "✅ home gone"

set -e
```

---

## Lab 35a Checklist (2 tasks + closeout)

- [ ] Task 1 covered scriptable `nmtui-hostname` plus interactive menu keystrokes and restored original hostname
- [ ] Task 2 mapped `nmtui-edit` fields to `nmcli con mod` equivalents
- [ ] T35-A and T35-B were explicitly documented with verification commands
- [ ] Section 6 closeout ended with four `✅` audit lines

---

## Author

**Kelvin R. Tobias**  
[kelvinintech.com](https://kelvinintech.com) · [GitHub](https://github.com/kelvintechnical) · [LinkedIn](https://www.linkedin.com/in/kelvin-r-tobias-211949219)
