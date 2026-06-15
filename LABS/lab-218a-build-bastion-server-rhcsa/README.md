# Lab 218a: Build a Bastion Server (RHCSA) — `systemctl is-active`, `systemctl get-default`

**Series:** linux-ops-mastery — Security Administration · **Lab 218a of the Novice → RHCA path**  
**Certifications covered:** RHCSA EX200 (manage services with `systemctl`, set the default target, install from package groups), RHCE EX294 (the service posture you later enforce in playbooks), Security+/SRE (attack-surface reduction, hardened jump hosts)  
**Prerequisite:** A RHEL 9 / Rocky / Alma sandbox you can `sudo` on, with `openssh-server` installed (it is on every default server install) — no prior lab required, though [Lab 216](../lab-216a-service-isolation-rhcsa/) pairs well  
**Time Estimate:** 25–35 minutes  
**Difficulty:** Intermediate

---

## 🎯 Objective

Build the confidence to look at a server and answer one question a security auditor always asks: *"Is this box doing only what a bastion should — accept SSH and nothing else?"* You will confirm the machine boots to a text-only target, that `sshd` (the single service a jump host must run) is active and enabled, and that the system was installed from the **Minimal Install** package group so its attack surface is tiny. Then you will create a harmless throwaway listener, see it show up as an open port, and trim it away — proving you can reduce a bastion down to SSH-only and verify the result.

---

## 🧠 Concept

A **bastion server** (also called a jump host) is the single hardened door into a private network: admins SSH into it, then hop to internal machines. Its entire job is to be boring and small — the fewer services it runs, the fewer ways in an attacker has. Two ideas drive the whole lab. First, **posture**: what target does the box boot to (`multi-user.target` = text, no desktop), and what is actually running and enabled (`systemctl is-active`, `systemctl is-enabled`)? Second, **surface area**: which package groups built the box (`dnf group list`) and which TCP ports are accepting connections (`ss -tlnp`). A bastion should boot to multi-user, run `sshd`, and listen on essentially port 22 alone — every extra listener is one more thing to patch, audit, and worry about.

```
A BASTION should look like this:                A BLOATED box looks like this:
─────────────────────────────────              ─────────────────────────────────
get-default → multi-user.target                 get-default → graphical.target
sshd            active / enabled                 sshd, cockpit, httpd, cups...
ss -tlnp → :22  (one listener)                   ss -tlnp → :22 :9090 :80 :631 ...
                  small attack surface                       large attack surface
```

> **Why this matters:** The number-one rule of host hardening is "turn off what you do not need." Every listening socket is a doorway. Knowing how to *read* the posture (`get-default`, `is-active`, `ss -tlnp`) and *trim* it (`systemctl disable --now`) is the difference between a jump host you can defend and a server nobody can vouch for.

---

## 📚 Command Reference

| Command | Purpose | Critical flags |
|---|---|---|
| `systemctl is-active` / `is-enabled` | Read-only check: is a unit running now / set to start at boot | exit code is the verdict — `0` = active/enabled |
| `systemctl get-default` | Show the target the system boots into | a server should be `multi-user.target`, not `graphical.target` |
| `dnf group list` | List available/installed package groups | `--installed` shows only what is on the box; `info "Minimal Install"` shows a group's packages |
| `ss -tlnp` | List listening TCP sockets and the process behind each | `-t` TCP, `-l` listening, `-n` numeric ports, `-p` process (needs root) |
| `systemctl disable --now <unit>` | Stop a unit *and* remove its boot symlink in one move | `--now` = stop immediately too, not just at next boot |
| `systemctl daemon-reload` | Re-read unit files after you add or edit one | required whenever you create a unit under `/etc/systemd/system` |

---

## 🧰 LAB-WIDE SETUP

**In plain English:** We make one throwaway sandbox folder under `/tmp` to hold any scratch files this lab produces, so Teardown can wipe everything in a single safe command; the read-only service checks themselves touch nothing.

> Run this block **once** before Task 1. It defines a single sandbox root (`LAB_ROOT`) that every file in this lab lives under, so Teardown can wipe it in one safe command.

```bash
export LAB_ROOT=/tmp/lab-218
mkdir -p "$LAB_ROOT"
cd "$LAB_ROOT"

echo "Bastion lab workspace ready at $(date -Is)"
ls -ld "$LAB_ROOT"
echo "exit was: $?"
```

**Expected output:**

```
Bastion lab workspace ready at 2026-06-15T17:40:03-04:00
drwxr-xr-x. 2 root root 6 Jun 15 17:40 /tmp/lab-218
exit was: 0
```

---

## TASK 1 of 2 — Confirm the minimal, SSH-only posture

**In plain English:** Before changing anything, we prove the box is already built like a bastion — text-only boot target, `sshd` up and enabled, and a small package footprint from the Minimal Install group.

---

### Step 1 of 2 — Read the boot target and the one service that must run

**In plain English:** We confirm the server boots to a text target (no graphical desktop) and that `sshd` — the single service a bastion exists to provide — is both running now and set to start at every boot.

```bash
systemctl get-default
systemctl is-active sshd
systemctl is-enabled sshd
echo "exit was: $?"
```

**Expected output:**

```
multi-user.target
active
enabled
exit was: 0
```

**Line-by-line breakdown:**

- `systemctl get-default` → Print the default boot target; `multi-user.target` means "full text-mode multi-user system, no GUI" — exactly what a server wants. `graphical.target` here would be a red flag: a desktop stack you neither need nor want to patch on a bastion.
- `systemctl is-active sshd` → A read-only check that prints `active` if the SSH daemon is currently running; its exit code is `0` when active, so it is safe to script.
- `systemctl is-enabled sshd` → Confirms `sshd` is wired to start at boot (`enabled`); a bastion that does not auto-start SSH locks you out after a reboot.
- `echo "exit was: $?"` → Print the exit status of the last check so you have a scriptable pass/fail signal.

**New words in this step:**

- **target** — a systemd grouping of units that defines a system state (`multi-user.target` = text login; `graphical.target` = desktop).
- **bastion** — a single hardened host that is the only allowed entry point into a protected network.

---

### Step 2 of 2 — Confirm the small attack surface from the package group

**In plain English:** We list the package groups and inspect the **Minimal Install** group to show the box was built from the smallest sensible footprint — the foundation of a low attack surface.

```bash
dnf group list
dnf group list --installed
dnf group info "Minimal Install"
echo "exit was: $?"
```

**Expected output:**

```
Available Environment Groups:
   Server with GUI
   Server
   Workstation
   Custom Operating System
Installed Environment Groups:
   Minimal Install
Available Groups:
   Container Management
   Development Tools
   ...
Group: Minimal Install
 Description: Basic functionality.
 Mandatory Packages:
   dnf
   glibc
   ...
exit was: 0
```

**Line-by-line breakdown:**

- `dnf group list` → Show every environment group and package group `dnf` knows about, split into Available vs Installed; the **Installed Environment Groups** section is where you confirm the build profile.
- `dnf group list --installed` → Narrow the listing to only the groups actually present on this box, so you are not reading past a wall of available-but-absent groups.
- `dnf group info "Minimal Install"` → Print the package contents and description of the Minimal Install group; seeing only core packages (no desktop, no web stack) is the evidence of a small attack surface. Quote the name because it contains a space.
- `echo "exit was: $?"` → Print the exit status of the inspection.

**New words in this step:**

- **package group** — a named bundle of RPMs `dnf` can install or report on together (e.g. *Minimal Install*, *Development Tools*).
- **attack surface** — the total set of services, ports, and software an attacker could target; smaller is safer.

---

### Concept card (Task 1)

| Concept | What it does | Exam trap |
|---|---|---|
| `systemctl get-default` | shows the boot target | a server on `graphical.target` wastes resources and surface |
| `is-active` vs `is-enabled` | running *now* vs starts *at boot* | a service can be active but not enabled (dies on reboot) |
| `dnf group info "Minimal Install"` | lists a group's packages | the group name has a space — must be quoted |

---

### Troubleshoot (Task 1)

| Symptom | Likely cause | Fix |
|---|---|---|
| `is-enabled` prints `disabled` | `sshd` will not start on reboot | `sudo systemctl enable --now sshd` |
| `get-default` shows `graphical.target` | Box was installed with a GUI | `sudo systemctl set-default multi-user.target` |

---

## TASK 2 of 2 — Trim an extra listener

**In plain English:** We create a harmless throwaway socket so we have a safe "extra service" to remove, watch it open a port, then disable it and prove the listener is gone while `sshd` stays up — the SSH-only result, fully reversible.

---

### Step 1 of 2 — Create and enable a throwaway extra listener

**In plain English:** We write a tiny disposable socket unit (plus its paired service) listening on a high local port, reload systemd so it sees the new units, enable it, and confirm it is now an open listener — exactly the kind of extra service a bastion should not run.

```bash
sudo tee /etc/systemd/system/lab218-extra.socket >/dev/null <<'EOF'
[Unit]
Description=Lab 218 throwaway extra listener (safe to disable)

[Socket]
ListenStream=127.0.0.1:2189

[Install]
WantedBy=sockets.target
EOF

sudo tee /etc/systemd/system/lab218-extra.service >/dev/null <<'EOF'
[Unit]
Description=Lab 218 throwaway service paired with lab218-extra.socket

[Service]
ExecStart=/usr/bin/cat
StandardInput=socket
EOF

sudo systemctl daemon-reload
sudo systemctl enable --now lab218-extra.socket
systemctl is-active lab218-extra.socket
sudo ss -tlnp | grep 2189
```

**Expected output:**

```
Created symlink /etc/systemd/system/sockets.target.wants/lab218-extra.socket → /etc/systemd/system/lab218-extra.socket.
active
LISTEN 0      4096       127.0.0.1:2189       0.0.0.0:*    users:(("systemd",pid=1,fd=...))
```

**Line-by-line breakdown:**

- `sudo tee /etc/systemd/system/lab218-extra.socket <<'EOF' ... EOF` → Write a throwaway **socket unit** that tells systemd to listen on `127.0.0.1:2189`; the quoted `'EOF'` heredoc writes the text exactly. We use a dummy unit (not a real service) so disabling it is 100% safe and reversible.
- `sudo tee /etc/systemd/system/lab218-extra.service <<'EOF' ... EOF` → Write the paired **service unit** systemd starts when the socket gets a connection; `StandardInput=socket` hands the connection to `cat`. It is inert until something connects.
- `sudo systemctl daemon-reload` → Make systemd re-read unit files; required any time you add or edit a unit under `/etc/systemd/system`, or systemd will not know it exists.
- `sudo systemctl enable --now lab218-extra.socket` → Enable the socket (create the boot symlink) *and* start it immediately (`--now`), so it begins listening right away.
- `systemctl is-active lab218-extra.socket` → Read-only confirm it is `active` — the extra listener is live.
- `sudo ss -tlnp | grep 2189` → List listening TCP sockets and filter to our port; seeing `:2189` proves a new doorway is open (the surface a bastion should not have).

**New words in this step:**

- **socket unit** — a systemd unit that listens on a port/path and starts a paired service on demand (socket activation).
- **listener** — a socket in the `LISTEN` state accepting new connections; every one is a potential entry point.

---

### Step 2 of 2 — Disable the extra listener and prove SSH-only

**In plain English:** We disable and stop the throwaway socket in one command, re-run `ss -tlnp` to show the `:2189` listener is gone, and confirm `sshd` is still active — the bastion is back to SSH-only.

```bash
sudo systemctl disable --now lab218-extra.socket
sudo ss -tlnp | grep 2189 || echo "no extra listener (OK)"
systemctl is-active sshd
echo "exit was: $?"
```

**Expected output:**

```
Removed "/etc/systemd/system/sockets.target.wants/lab218-extra.socket".
no extra listener (OK)
active
exit was: 0
```

**Line-by-line breakdown:**

- `sudo systemctl disable --now lab218-extra.socket` → Stop the socket *and* remove its boot symlink at once; `--now` adds the immediate stop, so the port closes instantly instead of staying open until reboot.
- `sudo ss -tlnp | grep 2189 || echo "no extra listener (OK)"` → Re-check the port; `grep` finding nothing exits non-zero, so the `||` branch fires and prints `no extra listener (OK)` — proof the doorway is closed.
- `systemctl is-active sshd` → Confirm the one service that must stay up is still `active`; we trimmed an extra, not SSH.
- `echo "exit was: $?"` → Print the final exit status as a scriptable pass signal.

**New words in this step:**

- **socket activation** — systemd holding a listening socket and only launching the service when a connection arrives.
- **SSH-only posture** — a host whose sole listening service is `sshd`; the bastion ideal.

---

### Concept card (Task 2)

| Concept | What it does | Exam trap |
|---|---|---|
| `systemctl disable --now` | stops a unit AND removes its boot symlink | plain `disable` leaves it running until reboot |
| `ss -tlnp` | shows listening TCP sockets + owning process | `-p` (process name) needs root to be useful |
| `daemon-reload` | re-reads new/edited unit files | skip it and `enable` fails with "No such file" |

---

### Troubleshoot (Task 2)

| Symptom | Likely cause | Fix |
|---|---|---|
| `enable` says "No such file or directory" | You forgot `systemctl daemon-reload` after writing the unit | Run `sudo systemctl daemon-reload`, then enable again |
| `:2189` still listed after disable | You ran `disable` without `--now` | Run `sudo systemctl disable --now lab218-extra.socket` |

---

## ✅ Lab Checklist

- [ ] Task 1 · Step 1 — Read the boot target and the one service that must run
- [ ] Task 1 · Step 2 — Confirm the small attack surface from the package group
- [ ] Task 2 · Step 1 — Create and enable a throwaway extra listener
- [ ] Task 2 · Step 2 — Disable the extra listener and prove SSH-only

---

## 🧹 Teardown

**In plain English:** Delete everything this lab created so the box is clean for the next run.

> Run this after you've verified the lab. `lab_teardown.sh` safely removes the single sandbox root — it refuses to touch `/`, `$HOME`, or any protected path.

```bash
bash lab_teardown.sh "$LAB_ROOT"     # = /tmp/lab-218
```

**System-state reversal (required — `rm` does NOT undo systemd changes):**

```bash
sudo systemctl disable --now lab218-extra.socket 2>/dev/null
sudo rm -f /etc/systemd/system/lab218-extra.socket /etc/systemd/system/lab218-extra.service
sudo systemctl daemon-reload
```

**Expected output:**

```
✅ Removed /tmp/lab-218 — lab workspace is clean.
```

---

## ⚠️ Common Pitfalls

| Mistake | Symptom | Fix |
|---|---|---|
| Editing a real service to "trim surface" | You break SSH or another live service | Practice on the throwaway `lab218-extra.socket`, never production units |
| `disable` without `--now` | Port stays open until the next reboot | Always add `--now` to stop immediately as well |
| Running `ss -tlnp` without root | The process/PID column is blank | Use `sudo ss -tlnp` to see who owns each listener |

---

## 📌 Exam Strategy

Hardening questions reward you for *reading* a system before you change it. Lead with the read-only triple — `systemctl get-default`, `systemctl is-active <svc>`, `ss -tlnp` — to learn the posture, then make the smallest change that meets the requirement. When asked to "ensure only required services run," `systemctl disable --now` is your scalpel: it stops the unit now and at boot in one move.

- Memorize `ss -tlnp` flags as a sentence: **t**cp, **l**istening, **n**umeric, **p**rocess.
- `is-active` and `is-enabled` answer two different questions — running *now* vs starts *at boot*; checking both avoids the reboot surprise.
- Quote group names with spaces: `dnf group info "Minimal Install"`.

---

## 🔗 Related Labs

- [Lab 218b — Build a Bastion Server (Ansible)](../lab-218b-build-bastion-server-ansible/) — enforce the same SSH-only posture declaratively with `systemd_service`
- [Lab 218c — Build a Bastion Server (Verify)](../lab-218c-build-bastion-server-verify/) — prove the posture with scripted OK/FAIL assertions
- [Lab 216a — Service Isolation (RHCSA)](../lab-216a-service-isolation-rhcsa/) — the neighboring discipline of confining what a service may touch

---

## 👤 Author

**Kelvin R. Tobias**  
[kelvinintech.com](https://kelvinintech.com) · [GitHub](https://github.com/kelvintechnical) · [LinkedIn](https://www.linkedin.com/in/kelvin-r-tobias-211949219)
