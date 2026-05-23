# Lab: Install Development Tools Package Group with Output Capture

**Series:** linux-ops-mastery — RHCSA Package Management
**Status:** 📅 Planned — full walkthrough coming soon. The task definition below is exam-accurate; lab content (concept sections, task breakdowns, expected output, troubleshoot tables) has not yet been written.

---

## Task

Install the entire **"Development Tools"** package group with `dnf`, then capture detailed group info into `/var/tmp/systemtools.out` as a proof-of-install artifact.

### Steps to be covered

1. Confirm enabled repos with `dnf repolist enabled` — the Development Tools group lives in AppStream/BaseOS.
2. List the available package groups: `dnf group list` — verify `Development Tools` appears under **Available Groups**.
3. Install the group:
   ```
   dnf groupinstall -y "Development Tools"
   ```
4. Verify the group is now under **Installed Groups**: `dnf group list --installed`.
5. Capture detailed info into the proof file:
   ```
   dnf group info "Development Tools" > /var/tmp/systemtools.out
   ```
6. Spot-check core tools landed: `which gcc make git autoconf`.
7. Inspect the artifact: `cat /var/tmp/systemtools.out` — should list mandatory, default, and optional packages.

### `dnf group` vs `dnf groupinstall` — the modern syntax

| Form | Equivalent |
|---|---|
| `dnf groupinstall "Name"` | Legacy yum-style, still works |
| `dnf group install "Name"` | Modern dnf-native (space-separated subcommand) |
| `@Name` shorthand | `dnf install @"Development Tools"` works too |

### Career-arc connection

- **RHCSA** — package-group installs (Dev Tools, Virtualization Host, Web Server) are exam staples.
- **DevOps** — golden-image baking via `dnf groupinstall` is the standard pattern for VM templates.

---

## Author

**Kelvin R. Tobias**
[kelvinintech.com](https://kelvinintech.com) · [GitHub](https://github.com/kelvintechnical) · [LinkedIn](https://www.linkedin.com/in/kelvin-r-tobias-211949219)
