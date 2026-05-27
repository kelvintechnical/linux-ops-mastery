# Configure a Static IP Address (nmcli)

> RHCSA EX200 — Networking: configure a persistent static IPv4 address with `nmcli`.

---

## 📋 Scenario

You are working on **Node1**, which currently obtains its IP address via DHCP. The management team requires that Node1 be configured with a static IPv4 address so that it can reliably communicate with other servers.

---

## 🎯 Requirements

1. The static IP address must be `192.168.50.10` with a subnet mask of `255.255.255.0`.
2. The default gateway must be `192.168.50.1`.
3. DNS should be set to `8.8.8.8` and `8.8.4.4`.
4. Ensure the network interface is enabled at boot.
5. Confirm the configuration is persistent across reboots.
6. After configuration, verify connectivity by pinging `192.168.50.1`.

---

## ✅ Tasks

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

## 🧠 Key Concepts

| Setting | Purpose |
|---------|---------|
| `ipv4.method manual` | Disables DHCP — required for static |
| `connection.autoconnect yes` | Persists across reboots |
| `ipv4.dns "8.8.8.8 8.8.4.4"` | Multiple DNS servers in one quoted string |

---

## ⚠️ Pitfalls

- Forgetting `ipv4.method manual` → DHCP overrides static
- Wrong interface name → silent failure; always run `nmcli device status` first
- Running `nmcli con down/up` over SSH on EC2 → locked out of instance

---

[← Back to main README](../README.md)
