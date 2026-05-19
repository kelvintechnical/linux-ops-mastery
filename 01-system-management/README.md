# 01 — System Management

> RHCSA core skills: networking basics, system configuration, and persistent settings.

---

## 🧪 Labs in This Module

| # | Lab Title | Topic | Exam Relevance |
|---|-----------|-------|----------------|
| 01 | [Configure a Static IP Address](#lab-01--configure-a-static-ip-address) | nmcli, persistent networking | RHCSA EX200 |

---

## Lab 01 — Configure a Static IP Address

### 📋 Scenario
You are working on **Node1**, which currently obtains its IP address via DHCP. The management team requires that Node1 be configured with a static IPv4 address so it can reliably communicate with other servers.

### 🎯 Requirements
1. Static IP `192.168.50.10` / netmask `255.255.255.0`
2. Default gateway `192.168.50.1`
3. DNS: `8.8.8.8`, `8.8.4.4`
4. Interface enabled at boot
5. Configuration persists across reboots
6. Verify by pinging `192.168.50.1`

### ✅ Tasks
- Identify primary network interface
- Configure static IP, gateway, DNS
- Bring interface up + enable on boot
- Verify settings and connectivity

---

### Step 1 — Identify the interface
```bash
nmcli device status
```
> Note the device name (e.g., `ens160`). Replace `ens160` below with yours.

---

### Step 2 — Configure everything (one-shot)
```bash
sudo nmcli con mod ens160 ipv4.addresses 192.168.50.10/24 ipv4.gateway 192.168.50.1 ipv4.dns "8.8.8.8 8.8.4.4" ipv4.method manual connection.autoconnect yes && sudo nmcli con up ens160
```

---

### Step 3 — Verify
```bash
ip addr show ens160; ip route; cat /etc/resolv.conf; ping -c 3 192.168.50.1
```

---

### 🧠 Key Concepts
| Setting | Purpose |
|---------|---------|
| `ipv4.method manual` | Disables DHCP — required for static |
| `connection.autoconnect yes` | Persists across reboots |
| `nmcli con up` | Applies immediately |

### ⚠️ Pitfalls
- Forgetting `ipv4.method manual` → DHCP overrides static
- Wrong interface name → silent failure; always run `nmcli device status` first
- DNS quotes matter → multiple DNS servers go in one quoted string

---

[← Back to main README](../README.md)
