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
> Note the device name (e.g., `ens160`). Replace `ens160` in Steps 2 & 3 with your actual interface.

---

### Step 2 — Configure static IP, gateway, DNS, and autoconnect (one-shot)
```bash
sudo nmcli con mod ens160 ipv4.addresses 192.168.50.10/24 ipv4.gateway 192.168.50.1 ipv4.dns "8.8.8.8 8.8.4.4" ipv4.method manual connection.autoconnect yes && sudo nmcli con up ens160
```

---

### Step 3 — Verify settings and connectivity
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
