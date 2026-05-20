<<<<<<< HEAD
# 01 — System Management

> RHCSA core skills: networking fundamentals, system configuration, and persistent settings.

---

## Lab 01 — Configure a Static IP Address

### 📋 Scenario
You are working on **Node1**, which currently obtains its IP address via DHCP. The management team requires that Node1 be configured with a static IPv4 address so that it can reliably communicate with other servers.

### 🎯 Requirements
1. The static IP address must be `192.168.50.10` with a subnet mask of `255.255.255.0`.
2. The default gateway must be `192.168.50.1`.
3. DNS should be set to `8.8.8.8` and `8.8.4.4`.
4. Ensure the network interface is enabled at boot.
5. Confirm the configuration is persistent across reboots.
6. After configuration, verify connectivity by pinging `192.168.50.1`.

### ✅ Tasks
- Identify the primary network interface on Node1.
- Configure the interface with the static IP, gateway, and DNS.
- Bring the interface up and enable it to start on boot.
- Verify the settings and connectivity.

---

### Step 1 — Identify the primary network interface
```bash
nmcli device status
```
> Note the device name (e.g., `ens5`, `ens160`). Replace `ens5` below with your actual interface.

---

### Step 2 — Configure static IP, gateway, DNS, and autoconnect
```bash
sudo nmcli con mod ens5 ipv4.method manual ipv4.addresses 192.168.50.10/24 ipv4.gateway 192.168.50.1 ipv4.dns "8.8.8.8 8.8.4.4" connection.autoconnect yes
```

---

### Step 3 — Bring interface up
```bash
sudo nmcli con up ens5
```

> ⚠️ **EC2 warning:** Skip this on a remote EC2 instance — it drops your SSH session. Safe on local VMs and the exam.

---

### Step 4 — Verify settings and connectivity
```bash
ip addr show ens5; ip route; nmcli con show ens5 | grep ipv4; ping -c 3 192.168.50.1
```

---

### 🧠 Key Concepts
| Setting | Purpose |
|---------|---------|
| `ipv4.method manual` | Disables DHCP — required for static |
| `connection.autoconnect yes` | Persists across reboots |
| `ipv4.dns "8.8.8.8 8.8.4.4"` | Multiple DNS servers in one quoted string |

### ⚠️ Pitfalls
- Forgetting `ipv4.method manual` → DHCP overrides static
- Wrong interface name → silent failure; always run `nmcli device status` first
- Running `nmcli con down/up` over SSH on EC2 → locked out of instance

---

[← Back to main README](../README.md)
=======
﻿# 01 — System Management

> RHCSA core skills: networking fundamentals, system configuration, package management, and persistent settings.

---

## 🧪 Labs in This Module

| # | Lab Title | Topic | Exam Relevance |
|---|-----------|-------|----------------|
| 01 | [Configure a Static IP Address](#lab-01--configure-a-static-ip-address) | nmcli, DNS, hostname, persistence | RHCSA EX200 |
| 02 | [Configure Repository Access](#lab-02--configure-repository-access) | dnf, .repo files, BaseOS/AppStream | RHCSA EX200 |

---

## Lab 01 — Configure a Static IP Address

*(existing Lab 01 content — keep what you already have here)*

---

## Lab 02 — Configure Repository Access

### 📋 Scenario
On **Node1**, you need to configure access to the RHEL 9 repositories so that packages can be installed. The repositories are hosted at the base URL:

`https://repos.examplelab.com/rhel9`

### 🎯 Requirements
1. Configure both `BaseOS` and `AppStream` repositories using the base URL above.
2. Ensure the repositories are enabled.
3. The configuration must persist across reboots.
4. Verify that the repositories are correctly configured and available for package installation.

### ✅ Tasks
- Create repo file(s) in `/etc/yum.repos.d/`
- Define both `BaseOS` and `AppStream` sections
- Enable each repo with `enabled=1`
- Verify with `dnf repolist`

---

### 📚 Command Decision Map

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

### 🧠 Key Concepts

| Setting | Purpose |
|---------|---------|
| `[RepoName]` | Section header — must be unique |
| `name=` | Human-readable label |
| `baseurl=` | Where packages live |
| `enabled=1` | Activates the repo |
| `gpgcheck=0` | Skips GPG verification (use `1` in production) |
| `/etc/yum.repos.d/*.repo` | Auto-loaded by dnf — survives reboot |

### ⚠️ Pitfalls

- Forgetting `enabled=1` → repo defined but ignored
- Missing trailing slash issues → check URL exactly matches what server expects
- Using `gpgcheck=1` without importing the GPG key → install fails
- Editing the wrong file (e.g., `/etc/dnf/dnf.conf`) → repos go elsewhere
- Not running `dnf clean all` → stale cache hides new repos

---

[← Back to main README](../README.md)
>>>>>>> 7a4c6b7 (docs: add Lab 02 - Configure Repository Access)
