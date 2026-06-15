# Lab 217a: Monitor Security Updates (RHCSA) — `dnf check-update`, `dnf updateinfo`

**Series:** linux-ops-mastery — Security Administration · **Lab 217a of the Novice → RHCA path**  
**Certifications covered:** RHCSA EX200 (install/update software packages, manage updates), RHCE EX294 (the patch posture your playbooks automate), SRE/DevOps (vulnerability triage, patch SLAs)  
**Prerequisite:** A RHEL 9 / Rocky / Alma sandbox you can `sudo` on; a working network or repo mirror so `dnf` can reach metadata — no prior lab required, though the [package-management labs](../) help  
**Time Estimate:** 25–35 minutes  
**Difficulty:** Beginner → Intermediate

---

## 🎯 Objective

Learn to *survey* a system's update posture without changing it, the daily reflex of every security-minded admin: ask "what needs patching?", separate ordinary bug-fix updates from **security** errata (Red Hat Security Advisories, RHSA), preview exactly which packages a security-only upgrade would touch, and finally decide whether the box needs a service restart or a full reboot. Everything here is **read-only by design** — you will use `dnf check-update`, `dnf updateinfo`, `--assumeno`, and `needs-restarting` so the system is *queried*, never mutated, and every report you generate is saved into a single throwaway sandbox.

---

## 🧠 Concept

Patching is two distinct jobs: **discovery** (what is available and how urgent) and **application** (installing it, then restarting what still runs stale code). `dnf check-update` lists available updates and — crucially — returns **exit code 100** when updates exist (not the `0` you might expect), a quirk that trips every script written by someone who assumed "nonzero means error." `dnf updateinfo` reads the **errata** metadata Red Hat ships alongside packages, letting you filter to `security` advisories (RHSA) and rank them by severity. `dnf upgrade --security` would install only the security fixes — and run with `--assumeno` it *prints the plan and stops*, a perfect dry preview. After patching, libraries on disk are new but running processes still hold the old ones in memory; `needs-restarting` finds those processes and `needs-restarting -r` answers the bigger question — does the whole host need a reboot?

```
dnf check-update      → exit 0   = nothing to do
                      → exit 100 = updates available  (NOT an error!)
                      → exit 1   = a real failure (repo/network)

dnf updateinfo summary           →  counts: Security / Bugfix / Enhancement
dnf updateinfo list security     →  RHSA-2026:1234  Important/Sec  openssl-...

dnf upgrade --security --assumeno →  shows the plan, answers "no", changes nothing
needs-restarting                  →  PID : process using a deleted/updated lib
needs-restarting -r               →  exit 0 = no reboot, exit 1 = reboot recommended
```

> **Why this matters:** On the exam and on call, the dangerous move is patching blind. Knowing the `100` exit code, reading RHSA severity, and previewing with `--assumeno` is how you report a system's risk *before* you touch it — and `needs-restarting` is how you avoid the classic "I patched OpenSSL but never restarted the service still running the vulnerable copy."

---

## 📚 Command Reference

| Command | Purpose | Critical flags |
|---|---|---|
| `dnf update` | The anchor: apply all available updates (interactive) | `-y` to auto-confirm; here we only *reference* it, we do not run it |
| `dnf check-update` | List available updates and signal availability via exit code | exit `100` = updates exist, `0` = none, `1` = failure |
| `dnf updateinfo summary` | Count pending errata by type (Security/Bugfix/Enhancement) | `--security` narrows to security advisories only |
| `dnf updateinfo list security` | List each pending security advisory (RHSA) and its package | severity shows as Critical/Important/Moderate/Low |
| `dnf upgrade --security --assumeno` | Preview the security-only upgrade plan without applying it | `--assumeno` answers "no" automatically; `upgrade-minimal` patches to the lowest fixing version |
| `needs-restarting` / `needs-restarting -r` | Find processes using stale libs / decide if a reboot is needed | `-r` exits `1` when a reboot is recommended; provided by `dnf-plugins-core` |

---

## 🧰 LAB-WIDE SETUP

**In plain English:** We make one throwaway sandbox folder under `/tmp` to hold every report this lab generates, and we confirm the `needs-restarting` helper is present (it ships with `dnf-plugins-core` / `dnf-utils`) — without installing anything if we can avoid it.

> Run this block **once** before Task 1. It defines a single sandbox root (`LAB_ROOT`) that every file in this lab lives under, so Teardown can wipe it in one safe command.

```bash
export LAB_ROOT=/tmp/lab-217
mkdir -p "$LAB_ROOT"
cd "$LAB_ROOT"

# needs-restarting comes from dnf-plugins-core (a.k.a. dnf-utils on some builds).
# Check WITHOUT installing; only install if you accept the cleanup note in Teardown.
command -v needs-restarting && echo "needs-restarting present (OK)" \
  || echo "needs-restarting MISSING — see note below"

ls -ld "$LAB_ROOT"
echo "Sandbox ready at $(date -Is)"
echo "exit was: $?"
```

**Expected output:**

```
/usr/bin/needs-restarting
needs-restarting present (OK)
drwxr-xr-x. 2 root root 6 Jun 15 17:40 /tmp/lab-217
Sandbox ready at 2026-06-15T17:40:03-04:00
exit was: 0
```

> If it is MISSING and you choose to add it: `sudo dnf install -y dnf-plugins-core` (this *does* mutate the box — note it and remove with `sudo dnf remove -y dnf-plugins-core` in Teardown only if it was not already required by the system).

---

## TASK 1 of 2 — Discover what needs updating

**In plain English:** We ask the system two questions — "what updates are pending?" and "which of those are security advisories?" — and save both answers as reports, all without changing a single package.

---

### Step 1 of 2 — `dnf check-update`, capture the exit code, save the list

**In plain English:** We run the availability check, immediately capture its exit code into a variable, interpret it (0 = up to date, 100 = updates available), and write the full list of pending packages to a report file.

```bash
dnf check-update | tee "$LAB_ROOT/pending.txt"
rc=$?
echo "check-update exit code: $rc"
case "$rc" in
  0)   echo "RESULT: system is up to date (no updates)";;
  100) echo "RESULT: updates ARE available (exit 100 is normal here)";;
  *)   echo "RESULT: a real error occurred (repo/network) — investigate";;
esac
```

**Expected output:**

```
Last metadata expiration check: 0:05:11 ago on Mon 15 Jun 2026 05:35:00 PM EDT.

bash.x86_64                     5.1.8-9.el9_4               baseos
openssl.x86_64                  1:3.2.2-6.el9_5             appstream
sudo.x86_64                     1.9.5p2-10.el9_5            baseos
check-update exit code: 100
RESULT: updates ARE available (exit 100 is normal here)
```

**Line-by-line breakdown:**

- `dnf check-update | tee "$LAB_ROOT/pending.txt"` → Query the repos for newer package versions and write the list both to the screen and into `pending.txt`; `check-update` does **not** install anything, it only reports.
- `rc=$?` → Capture the exit code *immediately* (the very next command would overwrite `$?`); this is the value that carries the real meaning.
- `case "$rc" in ...` → Translate the code: `0` means nothing to do, `100` means updates are available (the famous DNF quirk — **not** an error), and anything else is a genuine failure to chase down.

**New words in this step:**

- **errata / advisory** — a published notice from the vendor that a package update fixes a specific bug or security flaw.
- **exit code 100** — DNF's special "updates are available" signal from `check-update`; scripts must treat it as success, not failure.

---

### Step 2 of 2 — `dnf updateinfo summary` and `list security` (the RHSA view)

**In plain English:** We switch from "all updates" to the security lens — first a count of advisories by type, then the per-advisory list of security errata (RHSA) — and save the security listing as its own report.

```bash
dnf updateinfo summary
dnf updateinfo list security | tee "$LAB_ROOT/security-advisories.txt"
echo "exit was: $?"
```

**Expected output:**

```
Last metadata expiration check: 0:06:02 ago on Mon 15 Jun 2026 05:35:00 PM EDT.
Updates Information Summary: available
    2 Security notice(s)
        1 Important Security notice(s)
        1 Moderate Security notice(s)
    5 Bugfix notice(s)
    1 Enhancement notice(s)
RHSA-2026:1234 Important/Sec.  openssl-3.2.2-6.el9_5.x86_64
RHSA-2026:1290 Moderate/Sec.   sudo-1.9.5p2-10.el9_5.x86_64
exit was: 0
```

**Line-by-line breakdown:**

- `dnf updateinfo summary` → Read the errata metadata and print *counts* by category; the `Security notice(s)` lines, broken down by severity (Critical/Important/Moderate/Low), are what a security review cares about.
- `dnf updateinfo list security | tee "$LAB_ROOT/security-advisories.txt"` → List each individual security advisory with its RHSA ID, severity, and the package it fixes, saving it to a report; `list security` is the filter that hides bugfix/enhancement noise.
- `echo "exit was: $?"` → Confirm the listing command itself succeeded (`0`).

**New words in this step:**

- **RHSA** — Red Hat Security Advisory, the identifier (e.g. `RHSA-2026:1234`) for a published security fix.
- **severity** — the urgency rating on an advisory (Critical, Important, Moderate, Low) that drives patch priority.

---

### Concept card (Task 1)

| Concept | What it does | Exam trap |
|---|---|---|
| `dnf check-update` exit `100` | signals updates are available | `100` is success, not an error — scripts that test `$? -ne 0` break |
| `dnf updateinfo summary` | counts errata by type/severity | needs errata metadata; minimal/offline repos may show nothing |
| `updateinfo list security` | lists only RHSA security errata | `list` ≠ `list security` — the bare form includes bugfix/enhancement noise |

---

### Troubleshoot (Task 1)

| Symptom | Likely cause | Fix |
|---|---|---|
| `updateinfo` shows nothing despite updates | Repo lacks errata metadata (e.g. a bare mirror) | Enable a repo that publishes advisories; refresh with `dnf makecache` |
| Script aborts after `check-update` | It treated exit `100` as failure | Capture `$?` and special-case `100` as "updates available" |

---

## TASK 2 of 2 — Plan a security-only upgrade and restart audit

**In plain English:** We preview exactly which packages a security-only upgrade would install — without applying it — then audit whether anything would need a service restart or a full reboot afterward.

---

### Step 1 of 2 — Preview the security-only upgrade with `--assumeno`

**In plain English:** We ask `dnf` to plan a security-only upgrade and answer "no" for us, so it prints the exact package list it *would* install and then changes nothing — the safe dry run.

```bash
dnf upgrade --security --assumeno | tee "$LAB_ROOT/security-upgrade-plan.txt"
echo "exit was: $?"
```

**Expected output:**

```
Last metadata expiration check: 0:07:40 ago on Mon 15 Jun 2026 05:35:00 PM EDT.
Dependencies resolved.
================================================================================
 Package        Arch     Version              Repository        Size
================================================================================
Upgrading:
 openssl        x86_64   1:3.2.2-6.el9_5      appstream        1.2 M
 sudo           x86_64   1.9.5p2-10.el9_5     baseos           1.1 M

Transaction Summary
================================================================================
Upgrade  2 Packages

Total download size: 2.3 M
Operation aborted.
exit was: 1
```

**Line-by-line breakdown:**

- `dnf upgrade --security --assumeno` → Resolve a **security-only** upgrade transaction and auto-answer "no" at the confirmation prompt, so DNF prints the full plan and then aborts without downloading or installing; `tee` saves the plan for your report.
- To *actually apply* it you would drop `--assumeno` (DNF prompts) or add `-y` to auto-confirm: `dnf upgrade --security -y`. For the most conservative patch — bumping each package to the *lowest* version that fixes the advisory — use `dnf upgrade-minimal --security`.
- `echo "exit was: $?"` → Prints `1` because `--assumeno` aborts the transaction on purpose; that nonzero code here means "you declined," not "it failed."

**New words in this step:**

- **`--assumeno`** — the inverse of `-y`/`--assumeyes`: it answers "no" to every prompt, turning any DNF action into a safe preview.
- **`upgrade-minimal`** — upgrade each package only to the lowest version that resolves the advisory, minimizing change/risk.

---

### Step 2 of 2 — Restart audit with `needs-restarting` and `needs-restarting -r`

**In plain English:** We check which running processes are still using outdated libraries (so you'd restart those services) and then ask whether the whole machine needs a reboot, reading the exit code as the verdict.

```bash
needs-restarting | tee "$LAB_ROOT/needs-restarting.txt"
needs-restarting -r
echo "reboot-check exit code: $?"
```

**Expected output:**

```
1842 : /usr/lib/systemd/systemd --switched-root --system --deserialize 31
2391 : sshd: /usr/sbin/sshd -D [listener]
Core libraries or services have been updated since boot-up:
  * kernel
  * openssl-libs
Reboot is required to fully utilize these updates.
reboot-check exit code: 1
```

**Line-by-line breakdown:**

- `needs-restarting | tee "$LAB_ROOT/needs-restarting.txt"` → List the PIDs and command lines of processes that started before their on-disk libraries were updated — these are the services you would restart after patching; the output is saved for the report.
- `needs-restarting -r` → Ask the bigger question: have *core* libraries (kernel, glibc, openssl, systemd) changed such that a full reboot is required? It prints which subsystems changed.
- `echo "reboot-check exit code: $?"` → Read the verdict: exit `0` = no reboot needed, exit `1` = **reboot recommended**; this closes the patch loop — patch, then know whether to restart services or the host.

**New words in this step:**

- **stale library** — a newer library on disk while a still-running process holds the old copy in memory until restarted.
- **`needs-restarting -r`** — the reboot recommendation check; exit `1` means a reboot is advised after the updates.

---

### Concept card (Task 2)

| Concept | What it does | Exam trap |
|---|---|---|
| `upgrade --security --assumeno` | previews the security-only plan, applies nothing | exit `1` here means "you said no," not failure |
| `upgrade-minimal --security` | patches to lowest fixing version | smaller blast radius than full `--security` upgrade |
| `needs-restarting -r` | reboot recommendation check | exit `1` = reboot advised; don't read it as an error |

---

### Troubleshoot (Task 2)

| Symptom | Likely cause | Fix |
|---|---|---|
| `needs-restarting: command not found` | `dnf-plugins-core` not installed | `sudo dnf install -y dnf-plugins-core` (note it in Teardown) |
| `--assumeno` still downloads packages | You used `-y` or omitted `--assumeno` | Re-run with `--assumeno` to preview only |

---

## ✅ Lab Checklist

- [ ] Task 1 · Step 1 — `dnf check-update`, capture the exit code, save the list
- [ ] Task 1 · Step 2 — `dnf updateinfo summary` and `list security` (the RHSA view)
- [ ] Task 2 · Step 1 — Preview the security-only upgrade with `--assumeno`
- [ ] Task 2 · Step 2 — Restart audit with `needs-restarting` and `needs-restarting -r`

---

## 🧹 Teardown

**In plain English:** Delete everything this lab created so the box is clean for the next run.

> Run this after you've verified the lab. `lab_teardown.sh` safely removes the single sandbox root — it refuses to touch `/`, `$HOME`, or any protected path.

```bash
bash lab_teardown.sh "$LAB_ROOT"     # = /tmp/lab-217
```

This lab is **read-only**: it queries DNF but applies no upgrades, so there is no system state to reverse. Two optional cleanups: refresh the metadata cache with `sudo dnf clean all` if you want a clean slate, and — **only if you installed it for this lab and the system did not already require it** — remove the plugin you added with `sudo dnf remove -y dnf-plugins-core`. Prefer leaving an already-present `dnf-plugins-core` in place.

**Expected output:**

```
✅ Removed /tmp/lab-217 — lab workspace is clean.
```

---

## ⚠️ Common Pitfalls

| Mistake | Symptom | Fix |
|---|---|---|
| Treating `check-update` exit `100` as an error | Patch automation aborts on healthy systems | Special-case `100` as "updates available" |
| Running a bare `dnf update -y` to "see" updates | The box is mutated when you only wanted to look | Use `check-update` / `updateinfo` / `--assumeno` to query |
| Patching but never restarting | The old, vulnerable code keeps running in memory | Run `needs-restarting` and `-r`, then restart services or reboot |

---

## 📌 Exam Strategy

On the RHCSA you are asked to install and update software; the professional habit is to *survey before you patch*. Lead with `dnf check-update` (remember exit `100`), narrow to `dnf updateinfo list security` to report risk, and preview with `--assumeno` before committing. When the task says "apply updates," do it — but always finish by checking `needs-restarting -r` so you know whether a reboot is part of "done."

- Memorize the three exit codes of `check-update`: `0` (none), `100` (available), `1` (error).
- Reach for `dnf updateinfo list security` to separate security errata from ordinary bugfixes.
- `--assumeno` (preview) and `-y` (apply) are opposites — pick deliberately, and treat `--assumeno`'s nonzero exit as "declined," not "failed."

---

## 🔗 Related Labs

- [Lab 217a — Monitor Security Updates (RHCSA)](../lab-217a-monitor-security-updates-rhcsa/) — this lab: survey update posture by hand
- [Lab 217b — Monitor Security Updates (Ansible)](../lab-217b-monitor-security-updates-ansible/) — the same survey expressed as a playbook, including the rc-100 idiom
- [Lab 217c — Monitor Security Updates (Verify)](../lab-217c-monitor-security-updates-verify/) — prove the reports exist and the exit codes are sane
- [Lab 218a — Build a Bastion Server (RHCSA)](../lab-218a-build-bastion-server-rhcsa/) — the neighbor lab: lock down the jump box you patch from

---

## 👤 Author

**Kelvin R. Tobias**  
[kelvinintech.com](https://kelvinintech.com) · [GitHub](https://github.com/kelvintechnical) · [LinkedIn](https://www.linkedin.com/in/kelvin-r-tobias-211949219)
