# Lab 216a: Service Isolation Bastion Host (RHCSA) — `systemctl disable`, `systemctl mask`

**Series:** linux-ops-mastery — Security Administration · **Lab 216a of the Novice → RHCA path**  
**Certifications covered:** RHCSA EX200 (control services started at boot — `systemctl enable`/`disable`), RHCE EX294 (the manual behavior behind `ansible.builtin.systemd_service`), SRE/Security (attack-surface reduction, bastion hardening)  
**Prerequisite:** A RHEL/Rocky/Alma sandbox you can `sudo` on, plus comfort with `systemctl status`/`start` from the systemd labs  
**Time Estimate:** 25–35 minutes  
**Difficulty:** Beginner → Intermediate

---

## 🎯 Objective

Learn to shrink a host's attack surface the way a bastion (jump host) demands: first *inventory* what is enabled at boot and what is actually listening on the network, then *isolate* a service in two escalating ways — `systemctl disable` to remove its boot symlink, and `systemctl mask` to make it impossible to start at all. To keep this exercise completely safe you will create a **harmless throwaway unit** (`lab216-dummy.service`) and practice on it, so every change is fully reversible and no real production service is ever touched.

---

## 🧠 Concept

A bastion host is the single, hardened door into a private network, so the golden rule is *fewer running things = fewer ways in*. Two questions define your attack surface: "what starts automatically at boot?" (`systemctl list-unit-files --state=enabled`) and "what is actually listening for connections?" (`ss -tlnp`). Reducing that surface has two levels. `systemctl disable` deletes the unit's `WantedBy` symlink so it no longer auto-starts — but a dependency of another unit can still pull it in, and you can still start it by hand. `systemctl mask` is the nuclear option: it symlinks the unit name to `/dev/null`, so systemd cannot load it at all and any `start` request fails. Disable says "don't start on your own"; mask says "you cannot start, ever."

```
systemctl is-enabled lab216-dummy.service

 enabled   →  /etc/systemd/system/multi-user.target.wants/lab216-dummy.service  (boot symlink present)
 disabled  →  (boot symlink removed — but `systemctl start` still works)
 masked    →  /etc/systemd/system/lab216-dummy.service ─▶ /dev/null  (cannot start at all)
```

> **Why this matters:** On a real bastion, "I disabled it" is not the same as "it can never run." A teammate's dependency or a stray `systemctl start` can re-light a disabled service; a *masked* service is inert until someone deliberately `unmask`s it. Knowing the difference — and that mask is reversible — is the core of safe attack-surface reduction.

---

## 📚 Command Reference

| Command | Purpose | Critical flags |
|---|---|---|
| `systemctl list-unit-files --state=enabled` | List every unit set to start at boot (your attack-surface inventory) | `--state=enabled` filters to just the auto-start units |
| `ss -tlnp` | Show TCP sockets actually **listening**, with owning process | `-t` TCP, `-l` listening, `-n` numeric ports, `-p` process |
| `systemctl is-enabled <unit>` | Report a unit's boot state in one word | prints `enabled` / `disabled` / `masked`; exit code encodes the state |
| `systemctl disable --now <unit>` | Remove the boot symlink (and `--now` stops it immediately) | `disable` alone leaves it running until reboot; dependency can still pull it |
| `systemctl mask <unit>` | Symlink the unit to `/dev/null` so it can never start | strongest isolation; reverse only with `systemctl unmask` |
| `systemctl daemon-reload` | Re-read unit files after you add/change one on disk | required after writing a new `.service` file |

---

## 🧰 LAB-WIDE SETUP

**In plain English:** We create a single sandbox folder and write one **harmless throwaway systemd unit** (`lab216-dummy.service`, which just runs `/bin/true`) so every enable/disable/mask we practice is reversible and no real service is ever endangered.

> Run this block **once** before Task 1. It defines a single sandbox root (`LAB_ROOT`) that every file in this lab lives under, so Teardown can wipe it in one safe command.

```bash
export LAB_ROOT=/tmp/lab-216
mkdir -p "$LAB_ROOT"
cd "$LAB_ROOT"

sudo tee /etc/systemd/system/lab216-dummy.service >/dev/null <<'EOF'
[Unit]
Description=Lab 216 harmless dummy service (safe to enable/disable/mask)

[Service]
Type=oneshot
ExecStart=/bin/true
RemainAfterExit=yes

[Install]
WantedBy=multi-user.target
EOF

sudo systemctl daemon-reload
systemctl cat lab216-dummy.service | head -1
echo "Setup complete at $(date -Is)"
echo "exit was: $?"
```

**Expected output:**

```
# /etc/systemd/system/lab216-dummy.service
Setup complete at 2026-06-15T17:40:03-04:00
exit was: 0
```

---

## TASK 1 of 2 — Inventory what is enabled and listening

**In plain English:** Before isolating anything, a bastion admin takes stock — list everything that auto-starts at boot and everything actually listening on the network — then enable our harmless dummy unit so we have a safe target to isolate in Task 2.

---

### Step 1 of 2 — Take the attack-surface inventory (`list-unit-files`, `ss -tlnp`)

**In plain English:** We list every unit enabled to start at boot and every TCP port currently listening, because those two lists *are* the attack surface a bastion exists to minimize.

```bash
systemctl list-unit-files --state=enabled | head -n 8
echo "---"
sudo ss -tlnp
echo "exit was: $?"
```

**Expected output:**

```
UNIT FILE                   STATE   PRESET
auditd.service              enabled enabled
crond.service               enabled enabled
NetworkManager.service      enabled enabled
sshd.service                enabled enabled
systemd-logind.service      enabled enabled
...
---
State    Recv-Q   Send-Q   Local Address:Port   Peer Address:Port   Process
LISTEN   0        128      0.0.0.0:22           0.0.0.0:*           users:(("sshd",pid=1023,fd=3))
LISTEN   0        128      [::]:22              [::]:*              users:(("sshd",pid=1023,fd=3))
exit was: 0
```

**Line-by-line breakdown:**

- `systemctl list-unit-files --state=enabled` → List the unit files whose install state is `enabled` — i.e. everything systemd will auto-start at boot; `--state=enabled` filters out the hundreds of `static`/`disabled` units so you see only the auto-start attack surface.
- `sudo ss -tlnp` → Show sockets: `-t` TCP only, `-l` listening sockets, `-n` numeric ports (no DNS/`/etc/services` lookups), `-p` the owning process; `sudo` is needed to see the process column. On a clean box, ideally only `sshd` on `:22` is listening.
- `echo "exit was: $?"` → Print the exit status of `ss` (`0` = success).

**New words in this step:**

- **attack surface** — the total set of ways an attacker could interact with a host; on a bastion you minimize it to roughly "just SSH."
- **listening socket** — a socket bound to a port and waiting for inbound connections (what `ss -l` reveals).

---

### Step 2 of 2 — Enable the harmless dummy unit so we have a safe target

**In plain English:** We enable our throwaway `lab216-dummy.service` and confirm with `is-enabled`, giving us a unit that is *set to start at boot* — exactly the kind of thing we will isolate in Task 2, but with zero risk.

```bash
sudo systemctl enable lab216-dummy.service
systemctl is-enabled lab216-dummy.service
ls -l /etc/systemd/system/multi-user.target.wants/lab216-dummy.service
echo "exit was: $?"
```

**Expected output:**

```
Created symlink /etc/systemd/system/multi-user.target.wants/lab216-dummy.service → /etc/systemd/system/lab216-dummy.service.
enabled
lrwxrwxrwx. 1 root root 44 Jun 15 17:41 /etc/systemd/system/multi-user.target.wants/lab216-dummy.service -> /etc/systemd/system/lab216-dummy.service
echo "exit was: $?"
```

**Line-by-line breakdown:**

- `sudo systemctl enable lab216-dummy.service` → Create the boot symlink under the target named in `WantedBy=` (`multi-user.target`); this is precisely the symlink that makes a unit auto-start.
- `systemctl is-enabled lab216-dummy.service` → Report the state in one word; it now prints `enabled`, confirming the unit is part of the boot attack surface.
- `ls -l /etc/systemd/system/multi-user.target.wants/lab216-dummy.service` → Show the symlink `enable` just created, pointing back at our unit file — the concrete artifact behind the word "enabled."

**New words in this step:**

- **`WantedBy`** — the `[Install]` directive that tells `enable` which target's `.wants` directory to drop the boot symlink into.
- **boot symlink** — the symlink in a target's `.wants/` directory that causes a unit to be pulled in (auto-started) at boot.

---

### Concept card (Task 1)

| Concept | What it does | Exam trap |
|---|---|---|
| `list-unit-files --state=enabled` | shows only auto-start units | `enabled` ≠ "running"; a unit can be enabled but stopped |
| `ss -tlnp` | reveals real listening ports + process | needs `sudo` for the process column |
| `systemctl enable` | creates the `WantedBy` boot symlink | enabling does **not** start the unit now (use `--now` for that) |

---

### Troubleshoot (Task 1)

| Symptom | Likely cause | Fix |
|---|---|---|
| `is-enabled` prints `static` | The unit has no `[Install]` section | Add `WantedBy=` (as our dummy has) so it can be enabled |
| `ss -tlnp` shows no process names | You ran it without root | Re-run with `sudo ss -tlnp` |

---

## TASK 2 of 2 — Disable then mask to truly isolate

**In plain English:** We isolate the dummy unit in two escalating stages — first `disable` to strip its boot symlink, then `mask` to make starting it outright impossible — and contrast exactly what each level protects against.

---

### Step 1 of 2 — Disable (remove the boot symlink) with `--now`

**In plain English:** We disable the dummy unit and stop it in the same breath, then confirm `is-enabled` reports `disabled` — but remember this only removes the boot symlink; a dependency or a manual `start` could still run it.

```bash
sudo systemctl disable --now lab216-dummy.service
systemctl is-enabled lab216-dummy.service
echo "disable exit code: $?"
```

**Expected output:**

```
Removed "/etc/systemd/system/multi-user.target.wants/lab216-dummy.service".
disabled
disable exit code: 1
```

**Line-by-line breakdown:**

- `sudo systemctl disable --now lab216-dummy.service` → Delete the `WantedBy` boot symlink so the unit no longer auto-starts; `--now` also stops it immediately (without `--now` it keeps running until the next reboot).
- `systemctl is-enabled lab216-dummy.service` → Now prints `disabled` — the boot symlink is gone, so it will not start at boot.
- `echo "disable exit code: $?"` → `is-enabled` returns a **non-zero** exit code (`1`) for the `disabled` state; that is expected, not an error — the word printed on stdout is the real answer.

**New words in this step:**

- **disable** — remove a unit's boot symlink so it no longer auto-starts; it can still be started manually or pulled in by a dependency.
- **`--now`** — a flag that makes `enable`/`disable` also `start`/`stop` the unit in the same command.

---

### Step 2 of 2 — Mask (symlink to `/dev/null`) so it can never start

**In plain English:** We mask the unit, show that masking literally symlinks it to `/dev/null`, confirm `is-enabled` reports `masked`, and prove that even a deliberate `systemctl start` now fails — the strongest isolation a bastion can apply.

```bash
sudo systemctl mask lab216-dummy.service
systemctl is-enabled lab216-dummy.service
ls -l /etc/systemd/system/lab216-dummy.service
sudo systemctl start lab216-dummy.service
echo "start exit code: $?"
```

**Expected output:**

```
Created symlink /etc/systemd/system/lab216-dummy.service → /dev/null.
masked
lrwxrwxrwx. 1 root root 9 Jun 15 17:42 /etc/systemd/system/lab216-dummy.service -> /dev/null
Failed to start lab216-dummy.service: Unit lab216-dummy.service is masked.
start exit code: 1
```

**Line-by-line breakdown:**

- `sudo systemctl mask lab216-dummy.service` → Replace the unit with a symlink to `/dev/null`; systemd reads `/dev/null` as "this unit does not exist," so it cannot be loaded or started.
- `systemctl is-enabled lab216-dummy.service` → Now prints `masked` — a state stronger than `disabled`.
- `ls -l /etc/systemd/system/lab216-dummy.service` → Show the unit path is now a symlink pointing at `/dev/null` — the concrete mechanism of masking.
- `sudo systemctl start lab216-dummy.service` → Attempt to start it anyway; it **fails** with "Unit is masked," which `disable` alone would never have prevented — this is the whole point of mask.

**New words in this step:**

- **mask** — symlink a unit to `/dev/null` so systemd refuses to load or start it; the strongest, but reversible, isolation.
- **`/dev/null`** — the kernel's bit bucket; pointing a unit here makes systemd treat it as nonexistent.

---

### Concept card (Task 2)

| Concept | What it does | Exam trap |
|---|---|---|
| `systemctl disable` | removes the boot symlink only | a dependency or manual `start` can still run it |
| `systemctl mask` | symlinks the unit to `/dev/null` | even `systemctl start` fails until you `unmask` |
| `is-enabled` exit code | non-zero for `disabled`/`masked` | non-zero is **not** an error here — read the printed word |

---

### Troubleshoot (Task 2)

| Symptom | Likely cause | Fix |
|---|---|---|
| `start` succeeds when you expected it blocked | You only `disable`d, not `mask`ed | Run `systemctl mask` for true isolation |
| `unit not found` after masking, can't undo | Mask points the unit at `/dev/null` | Run `systemctl unmask` to restore the real unit |

---

## ✅ Lab Checklist

- [ ] Task 1 · Step 1 — Take the attack-surface inventory (`list-unit-files`, `ss -tlnp`)
- [ ] Task 1 · Step 2 — Enable the harmless dummy unit so we have a safe target
- [ ] Task 2 · Step 1 — Disable (remove the boot symlink) with `--now`
- [ ] Task 2 · Step 2 — Mask (symlink to `/dev/null`) so it can never start

---

## 🧹 Teardown

**In plain English:** Delete everything this lab created so the box is clean for the next run.

> Run this after you've verified the lab. `lab_teardown.sh` safely removes the single sandbox root — it refuses to touch `/`, `$HOME`, or any protected path.

This lab changed **system state** (it masked, disabled, and installed a unit file), and `rm` alone will NOT undo a mask or daemon registration. Run this explicit reversal block **first**, then the sandbox wipe:

```bash
sudo systemctl unmask lab216-dummy.service
sudo systemctl disable --now lab216-dummy.service
sudo rm -f /etc/systemd/system/lab216-dummy.service /etc/systemd/system/lab216-dummy.socket
sudo systemctl daemon-reload
bash lab_teardown.sh "$LAB_ROOT"     # = /tmp/lab-216
```

**Expected output:**

```
✅ Removed /tmp/lab-216 — lab workspace is clean.
```

---

## ⚠️ Common Pitfalls

| Mistake | Symptom | Fix |
|---|---|---|
| Treating `disable` as "can never run" | A dependency re-starts the service | Use `mask` when it must be impossible to start |
| Reading `is-enabled`'s non-zero exit as failure | Scripts abort on `disabled`/`masked` | Parse the printed word, not just `$?` |
| Forgetting `daemon-reload` after writing a unit | `Unit not found` for the new service | Run `systemctl daemon-reload`, then retry |

---

## 📌 Exam Strategy

On the RHCSA you control boot-time services constantly: `enable --now` to turn something on, `disable --now` to turn it off. The security upgrade — knowing `mask` makes a unit unstartable and that `is-enabled` reports `enabled`/`disabled`/`masked` — is what separates "I stopped it" from "I guaranteed it stays off." Always verify with `is-enabled` rather than trusting that the command did what you meant.

- Say "disable removes the boot link; mask blocks starting entirely" before you choose between them.
- Remember `is-enabled` returns non-zero for `disabled`/`masked` — read the word it prints, don't treat the exit code as an error.
- Anything you `mask` you can always `unmask` — practice the reversal so you never strand a unit at `/dev/null`.

---

## 🔗 Related Labs

- [Lab 216b — Service Isolation Bastion Host (Ansible)](../lab-216b-service-isolation-bastion-host-ansible/) — the same disable/mask outcome expressed idempotently in a playbook
- [Lab 216c — Service Isolation Bastion Host (Verify)](../lab-216c-service-isolation-bastion-host-verify/) — prove the enabled → disabled → masked transitions with hard evidence
- [Lab 218a — Build a Bastion Server (RHCSA)](../lab-218a-build-bastion-server-rhcsa/) — assemble the hardened jump host this isolation work feeds into

---

## 👤 Author

**Kelvin R. Tobias**  
[kelvinintech.com](https://kelvinintech.com) · [GitHub](https://github.com/kelvintechnical) · [LinkedIn](https://www.linkedin.com/in/kelvin-r-tobias-211949219)
