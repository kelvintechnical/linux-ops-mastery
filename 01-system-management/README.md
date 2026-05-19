# 01 — System Management

> RHCSA core skills: networking fundamentals, system configuration, and persistent settings — practiced on a real RHEL 9 environment.

---

## 🖥️ Environment Setup

These labs are practiced on a **Red Hat Enterprise Linux 9** EC2 instance (matches the RHCSA EX200 exam OS exactly).

### Why RHEL 9 and not Amazon Linux 2023?

| Tool | RHEL 9 | Amazon Linux 2023 |
|------|--------|-------------------|
| `nmcli` | ✅ | ❌ |
| `firewalld` | ✅ | ❌ |
| `SELinux` | ✅ | ❌ |
| `NetworkManager` | ✅ | ❌ uses `systemd-networkd` |
| `hostnamectl` | ✅ | partial |
| `dnf` | ✅ | ✅ |

Amazon Linux uses a completely different network stack — practicing on it builds the wrong muscle memory for the exam.

### Instance Reference

| Detail | Value |
|--------|-------|
| AMI | RHEL 9 HVM SSD (`ami-0d5e8769671b48387`) |
| Username | `ec2-user` |
| Region | `us-east-1` |
| SSH Source | `My IP /32` (not `0.0.0.0/0`) |

### Daily SSH Connect

```bash
ssh -i C:\Users\kelvint\Downloads\rhcsa-rhce-prep.pem ec2-user@<PUBLIC_IP>
```

> ⚠️ **Wait for `2/2 checks passed`** in EC2 console before SSHing — connecting too early gives `Connection refused`. Public IP changes on stop/start unless you set an Elastic IP.

---

## 🧪 Labs in This Module

| # | Lab Title | Topic | Exam Relevance |
|---|-----------|-------|----------------|
| 01 | [Configure a Static IP Address](#lab-01--configure-a-static-ip-address) | nmcli, DNS, hostname, persistence | RHCSA EX200 |

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

### 📚 Command Decision Map

| Lab Phrase | Question Being Asked | Command |
|------------|---------------------|---------|
| "Determine current config" | What OS? What tools? | `cat /etc/os-release` |
| "Configure interface" | What's my interface name? | `ip a` or `nmcli dev status` |
| "Same network" | What network am I on? | `ip a` → math |
| "Default gateway" | What's my current gateway? | `ip route` |
| "Set DNS" | Where do I configure DNS? | `nmcli con mod` |
| "Set hostname" | How do I change hostname? | `hostnamectl` |
| "Persistent across reboots" | Did config survive reboot? | `connection.autoconnect yes` |

---

### Step 1 — Identify OS and Network Stack

```bash
cat /etc/os-release
```

**What you're looking for:**
- `ID="rhel"` + `VERSION_ID="9"` → confirms `nmcli` path (RHCSA exam path ✅)
- `ID="amzn"` → wrong OS for RHCSA; uses `systemd-networkd` instead

**Alternatives:**
- `hostnamectl` — shows OS + kernel
- `uname -a` — kernel only (not distro)
- `cat /etc/redhat-release` — RHEL-specific

---

### Step 2 — Identify Interface and Current Network Config

```bash
ip a; ip route; cat /etc/resolv.conf
```

**Reading the output:**

| Line | Meaning |
|------|---------|
| `2: ens5: <UP,LOWER_UP>` | interface name = `ens5` |
| `inet 172.31.30.179/20` | current DHCP IP + subnet |
| `dynamic` / `valid_lft` | confirms DHCP, not static |
| `default via 172.31.16.1` | gateway = `172.31.16.1` |
| `nameserver 172.31.0.2` | DNS (AWS internal) |

> 🚨 **Never edit `/etc/resolv.conf` directly** — it's auto-managed by `systemd-resolved`. Set DNS via `nmcli` or it resets on reboot.

**Better alternative on RHEL:**

```bash
nmcli dev status; nmcli con show
```

---

### Step 3 — Configure Static IP, Gateway, DNS, and Autoconnect (one-shot)

```bash
sudo nmcli con mod ens5 ipv4.method manual ipv4.addresses 192.168.50.10/24 ipv4.gateway 192.168.50.1 ipv4.dns "8.8.8.8 8.8.4.4" connection.autoconnect yes
```

> ⚠️ **EC2 warning:** Do NOT run `nmcli con down && con up` on a remote EC2 instance — it drops your SSH session. On the exam (local VM), follow with `sudo nmcli con up ens5` to activate immediately.

**Local VM activation:**

```bash
sudo nmcli con up ens5
```

---

### Step 4 — Set Hostname (if required)

```bash
sudo hostnamectl set-hostname rhel-node1.example.com
```

---

### Step 5 — Verify Settings and Connectivity

```bash
ip addr show ens5; ip route; nmcli con show ens5 | grep ipv4; ping -c 3 192.168.50.1
```

---

### 🧠 Key Concepts

| Setting | Purpose |
|---------|---------|
| `ipv4.method manual` | Disables DHCP — required for static |
| `connection.autoconnect yes` | Persists across reboots |
| `ipv4.dns "8.8.8.8 8.8.4.4"` | Multiple DNS servers go in one quoted string |
| `nmcli con up` | Applies config immediately |
| `/etc/resolv.conf` | Auto-managed — never edit directly |

### ⚠️ Pitfalls

- Forgetting `ipv4.method manual` → DHCP overrides your static IP
- Wrong interface name → silent failure; always run `nmcli dev status` first
- Editing `/etc/resolv.conf` directly → resets on reboot
- Running `nmcli con down/up` over SSH on EC2 → locked out of instance
- Missing `connection.autoconnect yes` → interface doesn't come up at boot

---

[← Back to main README](../README.md)
