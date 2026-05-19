# Labs

## Lab 01 — Static Network Configuration (RHCSA EX200)

**Objective:** Configure persistent static networking on a RHEL node using `nmcli`.

**Constraint:** Must survive reboot; no GUI allowed.

---

### Step 1 — Discover current config
```bash
ip addr show
ip route show
nmcli device status
```
> Note your interface name (e.g., `ens33`, `ens160`) and current IP — you'll use the same network, host ID `.50`.

---

### Step 2 — Set static IP
```bash
nmcli con mod "ensXXX" ipv4.addresses 192.168.X.50/24
nmcli con mod "ensXXX" ipv4.gateway 192.168.X.1
nmcli con mod "ensXXX" ipv4.dns "8.8.8.8"
nmcli con mod "ensXXX" ipv4.dns-search "example.local"
nmcli con mod "ensXXX" ipv4.method manual
nmcli con up "ensXXX"
```
> Replace `ensXXX` and `192.168.X` with your actual interface and network.

---

### Step 3 — Set hostname
```bash
hostnamectl set-hostname rhel-node1.example.com
```

---

### Step 4 — Verify persistence
```bash
ip addr show ensXXX
nmcli con show ensXXX | grep ipv4
hostnamectl
```

---

### Key Concepts
| Concept | Tool |
|---------|------|
| Interface config | `nmcli con mod` |
| Apply immediately | `nmcli con up` |
| Hostname | `hostnamectl` |
| Verify | `ip addr`, `nmcli con show` |

---

**Pitfall:** Forgetting `ipv4.method manual` leaves DHCP active — static won't persist.
