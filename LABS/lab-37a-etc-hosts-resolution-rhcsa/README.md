# Lab 37a: Configuring Local Host Resolution (RHCSA) — `/etc/hosts`

**Series:** linux-ops-mastery — Networking · **Lab 37a of the Novice → RHCA path**  
**Certifications covered:** RHCSA EX200 (static name resolution), SRE/DevOps (host overrides, split-horizon testing)  
**Prerequisite:** [Lab 36c](../lab-36c-nmcli-cli-config-verify/) completed  
**Time Estimate:** 25–35 minutes  
**Difficulty:** Beginner

---

## 🎯 Today's Focus Coverage

> Stay on-subject via the ANCHOR rows; expand vocabulary via the NEW rows. Every row is exercised by a STEP below.

**⚓ Anchor — already learned (on-topic reuse)**

| # | Command / switch | Covered by |
|---|---|---|
| A1 | `cat`/`grep` reading files | _Task 1 · Step 1_ |
| A2 | `getent` (from Lab 27) | _Task 2 · Step 1_ |

**🆕 NEW this lab — introduced for the first time** (minimum 3)

| # | Command / switch | First taught in | Covered by |
|---|---|---|---|
| N1 | `/etc/hosts` format | Task 1 · Step 1 | _Task 1 · Step 1_ |
| N2 | add a host entry (`tee -a`) | Task 1 · Step 2 | _Task 1 · Step 2_ |
| N3 | `getent hosts` resolution | Task 2 · Step 1 | _Task 2 · Step 1_ |
| N4 | `/etc/nsswitch.conf` order | Task 2 · Step 2 | _Task 2 · Step 2_ |

---

## 🎯 Objective

Control name resolution locally with `/etc/hosts` — the file checked before DNS for many lookups. You'll read its format, add a name→IP mapping (with aliases), resolve names with `getent hosts` to prove the entry works, and understand how `/etc/nsswitch.conf` decides whether `files` (hosts) or `dns` is consulted first. This is the fastest way to override or pin a hostname.

> **Safety note:** We append a clearly-marked block to `/etc/hosts` and remove it in Teardown, and we keep a sandbox backup. The mappings use reserved/private addresses that won't affect real traffic.

---

## 🧠 Concept

`/etc/hosts` is a static lookup table: each line is `IP  canonical-name  [aliases...]`. It's consulted according to the `hosts:` line in `/etc/nsswitch.conf` (typically `files dns`, meaning `/etc/hosts` is checked **before** DNS). That ordering makes `/etc/hosts` perfect for overriding a name (point `app.example.com` at a test box), pinning a host when DNS is unreliable, or naming machines on a network with no DNS. `getent hosts NAME` performs a lookup using the same NSS path the system uses, so it's the correct way to test (`ping` also works but adds ICMP). Comments start with `#`. The loopback lines (`127.0.0.1 localhost`, `::1 localhost`) must stay intact. Because `files` usually precedes `dns`, a wrong `/etc/hosts` entry silently shadows DNS — a classic debugging gotcha.

```
IP  canonical  alias1 alias2     → one mapping line
getent hosts app.example.com     → resolve via NSS (files+dns)
/etc/nsswitch.conf hosts: files dns → hosts file wins over DNS
# comment                        → ignored
```

> **Why this matters:** `/etc/hosts` overrides DNS for the whole machine. Knowing its format, how to test with `getent`, and that `files` precedes `dns` lets you redirect or pin names — and explains baffling "DNS says X but the box reaches Y" bugs.

---

## 📚 Command Reference

| Command | Purpose | Notes |
|---|---|---|
| `cat /etc/hosts` | View table | format reference |
| `tee -a` | Append a line | with `sudo` |
| `getent hosts` | Resolve via NSS | correct test |
| `/etc/nsswitch.conf` | Lookup order | `hosts:` line |
| `ping -c1` | Quick sanity | adds ICMP |

---

## 🧰 LAB-WIDE SETUP

**In plain English:** Make the sandbox and back up `/etc/hosts` before editing it.

> Run this block **once** before Task 1. The backup lets Teardown restore the original file exactly.

```bash
export LAB_ROOT=/tmp/lab-37
mkdir -p "$LAB_ROOT"
sudo cp -a /etc/hosts "$LAB_ROOT/hosts.backup"
echo "backup saved"
echo "exit was: $?"
```

**Expected output:**

```
backup saved
exit was: 0
```

---

## TASK 1 of 2 — Read and extend `/etc/hosts`

**In plain English:** We read the file's format, then add a mapping with an alias.

---

### Step 1 of 2 — Read the hosts table

**In plain English:** We view `/etc/hosts` and identify its column format.

```bash
cat /etc/hosts
echo "exit was: $?"
```

**Expected output:**

```
127.0.0.1   localhost localhost.localdomain localhost4
::1         localhost localhost.localdomain localhost6
exit was: 0
```

**Line-by-line breakdown:**

- `127.0.0.1 localhost ...` → IP first, then the canonical name, then any aliases — all space/tab separated.
- The IPv6 loopback (`::1`) line mirrors the IPv4 one; both must remain.

**New words in this step:**

- **canonical name / alias** — the primary name for an IP and its alternates.

---

### Step 2 of 2 — Add a mapping with an alias

**In plain English:** We append a marked entry pointing a test name at a private IP.

```bash
sudo tee -a /etc/hosts >/dev/null <<'EOF'
# LAB-37 BEGIN
192.0.2.10   app.lab.local app web.lab.local
# LAB-37 END
EOF
grep -A1 'LAB-37 BEGIN' /etc/hosts
echo "exit was: $?"
```

**Expected output:**

```
# LAB-37 BEGIN
192.0.2.10   app.lab.local app web.lab.local
exit was: 0
```

**Line-by-line breakdown:**

- `tee -a /etc/hosts <<'EOF' ... EOF` → Append a clearly-marked block (markers make Teardown precise).
- `192.0.2.10 app.lab.local app web.lab.local` → One IP, a canonical name, and two aliases (`192.0.2.0/24` is TEST-NET — safe).

**New words in this step:**

- **marked block** — `BEGIN`/`END` comments so the edit can be removed cleanly later.

---

### Concept card (Task 1)

| Concept | What it does | Exam trap |
|---|---|---|
| hosts format | IP + names | canonical first |
| aliases | extra names | space-separated |
| markers | safe edits | enable clean removal |

---

### Troubleshoot (Task 1)

| Symptom | Likely cause | Fix |
|---|---|---|
| Permission denied | Not root | Use `sudo tee` |
| Loopback broke things | Edited `127.0.0.1` line | Restore from backup |

---

## TASK 2 of 2 — Resolve and understand ordering

**In plain English:** We resolve the new name, then inspect NSS lookup order.

---

### Step 1 of 2 — Resolve with `getent hosts`

**In plain English:** We confirm the system resolves our name via the hosts file.

```bash
getent hosts app.lab.local
getent hosts app
echo "exit was: $?"
```

**Expected output:**

```
192.0.2.10      app.lab.local app web.lab.local
192.0.2.10      app.lab.local app web.lab.local
```

**Line-by-line breakdown:**

- `getent hosts app.lab.local` → Resolves the canonical name to the IP via NSS (the real lookup path).
- `getent hosts app` → The alias resolves too — same line returned.

**New words in this step:**

- **`getent hosts`** — query name resolution through the system's NSS configuration.

---

### Step 2 of 2 — Inspect NSS lookup order

**In plain English:** We read which sources are tried, and in what order, for host lookups.

```bash
grep '^hosts:' /etc/nsswitch.conf
echo "---"
grep '^hosts:' /etc/nsswitch.conf | grep -q 'files' && echo "files is consulted (hosts file active)"
```

**Expected output:**

```
hosts:      files dns myhostname
---
files is consulted (hosts file active)
```

**Line-by-line breakdown:**

- `grep '^hosts:' /etc/nsswitch.conf` → The order of resolution sources; `files` = `/etc/hosts`, `dns` = resolver.
- Because `files` precedes `dns`, a hosts-file entry wins over DNS — the override mechanism.

**New words in this step:**

- **NSS order** — the `hosts:` line dictates whether `/etc/hosts` or DNS answers first.

---

### Concept card (Task 2)

| Concept | What it does | Exam trap |
|---|---|---|
| `getent hosts` | NSS lookup | correct test |
| `files dns` | order | files wins |
| alias resolve | extra names | all map to one IP |

---

### Troubleshoot (Task 2)

| Symptom | Likely cause | Fix |
|---|---|---|
| Name not resolving | Typo in `/etc/hosts` | Fix the entry |
| DNS ignored unexpectedly | hosts entry shadows it | Remove the override |

---

## ✅ Lab Checklist

- [ ] Task 1 · Step 1 — Read the hosts table
- [ ] Task 1 · Step 2 — Add a mapping with an alias
- [ ] Task 2 · Step 1 — Resolve with `getent hosts`
- [ ] Task 2 · Step 2 — Inspect NSS lookup order
- [ ] Every 🎯 Focus Coverage row (Anchor + NEW) mapped to a step
- [ ] 🧹 Teardown run — `/etc/hosts` restored + sandbox removed

---

## 🧹 Teardown

**In plain English:** Restore the original `/etc/hosts` and clear the sandbox.

> This lab edited a system file; the marked block is removed and the backup restored. `lab_teardown.sh` clears the sandbox root.

```bash
# Remove the marked block (precise) ...
sudo sed -i '/# LAB-37 BEGIN/,/# LAB-37 END/d' /etc/hosts
# ... or fully restore from backup if anything looks off:
# sudo cp -a "$LAB_ROOT/hosts.backup" /etc/hosts
cd /tmp
bash lab_teardown.sh "$LAB_ROOT"     # = /tmp/lab-37
```

**Expected output:**

```
✅ Removed /tmp/lab-37 — lab workspace is clean.
```

---

## ⚠️ Common Pitfalls

| Mistake | Symptom | Fix |
|---|---|---|
| Editing loopback lines | Local breakage | Never change `127.0.0.1`/`::1` |
| Testing with `nslookup`/`dig` | Skips hosts file | Use `getent hosts` |
| Forgetting markers | Hard cleanup | Use BEGIN/END block |

---

## 📌 Exam Strategy

`/etc/hosts` overrides DNS because `files` precedes `dns` in `/etc/nsswitch.conf`. Add `IP canonical aliases`, test with `getent hosts` (not `dig`, which bypasses the file), and never touch the loopback lines.

- Format: `IP  canonical  aliases`.
- `getent hosts` tests the real NSS path.
- `files dns` order = hosts file wins.

---

## 🔗 Related Labs

- [Lab 37b — Configuring Local Host Resolution (Ansible)](../lab-37b-etc-hosts-resolution-ansible/) — manage entries idempotently
- [Lab 37c — Configuring Local Host Resolution (Verify)](../lab-37c-etc-hosts-resolution-verify/) — prove resolution works
- [Lab 38a — Configuring DNS Servers (RHCSA)](../lab-38a-resolv-conf-dns-rhcsa/) — the DNS that `/etc/hosts` overrides

---

## 👤 Author

**Kelvin R. Tobias**  
[kelvinintech.com](https://kelvinintech.com) · [GitHub](https://github.com/kelvintechnical) · [LinkedIn](https://www.linkedin.com/in/kelvin-r-tobias-211949219)
