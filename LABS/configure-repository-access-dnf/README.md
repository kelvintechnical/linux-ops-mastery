# Configure Repository Access (dnf, .repo files)

> RHCSA EX200 — Package Management: define BaseOS + AppStream repos that survive reboot.

---

## 📋 Scenario

On **Node1**, you need to configure access to the RHEL 9 repositories so that packages can be installed. The repositories are hosted at the base URL:

`https://repos.examplelab.com/rhel9`

---

## 🎯 Requirements

1. Configure both `BaseOS` and `AppStream` repositories using the base URL above.
2. Ensure the repositories are enabled.
3. The configuration must persist across reboots.
4. Verify that the repositories are correctly configured and available for package installation.

---

## ✅ Tasks

- Create repo file(s) in `/etc/yum.repos.d/`
- Define both `BaseOS` and `AppStream` sections
- Enable each repo with `enabled=1`
- Verify with `dnf repolist`

---

## 📚 Command Decision Map

| Lab Phrase | Question Being Asked | Tool |
|------------|---------------------|------|
| "Configure repositories" | Where do repo files live? | `/etc/yum.repos.d/*.repo` |
| "BaseOS and AppStream" | What two sections do I need? | `[BaseOS]` and `[AppStream]` |
| "Ensure enabled" | How do I activate a repo? | `enabled=1` |
| "Persist across reboots" | Where does dnf read from? | `/etc/yum.repos.d/` (auto-loaded) |
| "Verify available" | How do I confirm? | `dnf repolist` |

---

### Step 1 — Create the repo file (one-shot)

```bash
sudo tee /etc/yum.repos.d/examplelab.repo > /dev/null << EOF
[BaseOS]
name=RHEL 9 BaseOS
baseurl=https://repos.examplelab.com/rhel9/BaseOS
enabled=1
gpgcheck=0

[AppStream]
name=RHEL 9 AppStream
baseurl=https://repos.examplelab.com/rhel9/AppStream
enabled=1
gpgcheck=0
EOF
```

> **What this does:** `tee` writes the heredoc content to a root-owned file in one command. `> /dev/null` suppresses duplicate output to your terminal.

---

### Step 2 — Verify the repos are loaded

```bash
sudo dnf clean all; sudo dnf repolist; sudo dnf repolist enabled
```

---

### Step 3 — Confirm package availability

```bash
sudo dnf list available | head -20
```

---

## 🧠 Key Concepts

| Setting | Purpose |
|---------|---------|
| `[RepoName]` | Section header — must be unique |
| `name=` | Human-readable label |
| `baseurl=` | Where packages live |
| `enabled=1` | Activates the repo |
| `gpgcheck=0` | Skips GPG verification (use `1` in production) |
| `/etc/yum.repos.d/*.repo` | Auto-loaded by dnf — survives reboot |

---

## ⚠️ Pitfalls

- Forgetting `enabled=1` → repo defined but ignored
- Missing trailing slash issues → check URL exactly matches what server expects
- Using `gpgcheck=1` without importing the GPG key → install fails
- Editing the wrong file (e.g., `/etc/dnf/dnf.conf`) → repos go elsewhere
- Not running `dnf clean all` → stale cache hides new repos

---

[← Back to main README](../README.md)
