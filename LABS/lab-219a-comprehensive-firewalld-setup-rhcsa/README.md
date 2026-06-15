# Lab 219a: Comprehensive firewalld Setup (RHCSA) — `firewall-cmd`, `--add-service`, `--add-rich-rule`

**Series:** linux-ops-mastery — Security Administration · **Lab 219a of the Novice → RHCA path**  
**Certifications covered:** RHCSA EX200 (configure firewall settings with `firewall-cmd`), RHCE EX294 (the manual baseline behind `ansible.posix.firewalld`), SRE/DevOps (host-based packet filtering, NAT, and least-privilege exposure)  
**Prerequisite:** A RHEL 9 / Rocky / Alma sandbox you can `sudo` on with `firewalld` running (`systemctl is-active firewalld`) — [Lab 218a](../lab-218a-bastion-host-hardening-rhcsa/) (bastion host hardening) is a useful warm-up  
**Time Estimate:** 30–40 minutes  
**Difficulty:** Beginner → Intermediate

---

## 🎯 Objective

Build a complete `firewalld` policy from scratch in a **dedicated throwaway zone** so a single command can wipe it later. You will open named services and a raw custom port, block ICMP echo (ping), enable masquerade (NAT) for a routed subnet, and add a rich rule that accepts SSH from one specific source network. Along the way you will internalize the most-tested `firewalld` distinction on the RHCSA: the difference between **runtime** rules (in memory, lost on reload) and **permanent** rules (written to XML under `/etc/firewalld/zones`, applied only after `--reload`). Crucially, you will do all of this **without touching the active zone**, so you can never lock yourself out of SSH.

---

## 🧠 Concept

`firewalld` is the dynamic firewall manager that fronts `nftables` on RHEL 9. Its central abstraction is the **zone** — a named bucket of rules (services, ports, ICMP blocks, masquerade, rich rules) that you attach to interfaces or sources. The exam-critical subtlety is that almost every change is either **runtime** (applied immediately, evaporates on reload or reboot) or **permanent** (`--permanent`, written to disk but *not* live until `firewall-cmd --reload` re-reads the on-disk config). Forgetting `--reload` after `--permanent` is the single most common firewalld mistake. To stay safe, this lab never edits the default/active zone — instead it creates a disposable permanent zone called `bastion`, applies every rule there, and leaves no interface bound to it, so deleting that one zone reverses the whole lab cleanly.

```
RUNTIME  (--zone=bastion --add-service=ssh)        live now, gone on --reload/reboot
PERMANENT(--permanent --add-service=ssh) ──▶ /etc/firewalld/zones/bastion.xml
                                          └─ not live until ──▶ firewall-cmd --reload

zone "bastion" ──┬─ services: ssh, http
                 ├─ ports:    8080/tcp
                 ├─ icmp-block: echo-request
                 ├─ masquerade: yes
                 └─ rich rule: accept ssh from 192.0.2.0/24
(no interface bound → safe to delete the whole zone in teardown)
```

> **Why this matters:** On a real bastion you can lock yourself out forever by editing the live zone over SSH and getting one rule wrong. The professional habit — stage rules in a separate permanent zone, review with `--list-all`, and only then bind it — is exactly what this lab drills, and it is the same caution graders reward on the RHCSA.

---

## 📚 Command Reference

| Command | Purpose | Critical flags |
|---|---|---|
| `firewall-cmd` | The runtime + permanent firewalld client | `--permanent` writes to disk; without it the change is runtime-only |
| `firewall-cmd --new-zone` | Create a brand-new (empty) zone | `--permanent` is **required**; follow with `--reload` to make it usable |
| `firewall-cmd --add-service` / `--add-port` | Allow a named service or a raw `port/proto` | `--permanent` to persist; service = named bundle, port = literal number |
| `firewall-cmd --add-icmp-block` / `--add-masquerade` | Block an ICMP type / enable source NAT | `--remove-icmp-block` and `--remove-masquerade` undo them |
| `firewall-cmd --add-rich-rule` | Add fine-grained source/service/action logic | quote the whole rule; persist with `--permanent` |
| `firewall-cmd --reload` / `--list-all` | Re-read permanent config into runtime / show a zone's full state | `--list-all` scoped with `--zone=bastion`; `--reload` is mandatory after `--permanent` |

---

## 🧰 LAB-WIDE SETUP

**In plain English:** We define one sandbox root for any files this lab creates, then create the dedicated throwaway `bastion` zone we will pour every firewall rule into — without binding any live interface to it, so we can never lock ourselves out.

> Run this block **once** before Task 1. It defines a single sandbox root (`LAB_ROOT`) that every file in this lab lives under, so Teardown can wipe it in one safe command.

```bash
export LAB_ROOT=/tmp/lab-219
mkdir -p "$LAB_ROOT"
cd "$LAB_ROOT"

# Confirm firewalld is the active firewall backend
sudo systemctl is-active firewalld

# Create a DEDICATED, throwaway permanent zone — never the active/default zone
sudo firewall-cmd --permanent --new-zone=bastion
sudo firewall-cmd --reload

# Confirm the new zone exists and is empty (no interface bound to it = safe)
sudo firewall-cmd --get-zones | tr ' ' '\n' | grep -x bastion
sudo firewall-cmd --zone=bastion --list-all
echo "exit was: $?"
```

**Expected output:**

```
active
success
success
bastion
bastion
  target: default
  icmp-block-inversion: no
  interfaces:
  sources:
  services:
  ports:
  protocols:
  forward: yes
  masquerade: no
  forward-ports:
  source-ports:
  icmp-blocks:
  rich rules:
exit was: 0
```

---

## TASK 1 of 2 — Open services and a custom port (permanent) in the bastion zone

**In plain English:** We allow two named services (SSH and HTTP) and one raw custom port (8080/tcp) in the bastion zone, persisting each change to disk and reloading so it becomes live.

---

### Step 1 of 2 — Allow named services `ssh` and `http` (permanent)

**In plain English:** We add the SSH and HTTP services to the bastion zone permanently, reload so the on-disk rules become live, then list the zone to confirm both services are present.

```bash
sudo firewall-cmd --zone=bastion --permanent --add-service=ssh --add-service=http
sudo firewall-cmd --reload
sudo firewall-cmd --zone=bastion --list-all
echo "exit was: $?"
```

**Expected output:**

```
success
success
bastion
  target: default
  icmp-block-inversion: no
  interfaces:
  sources:
  services: http ssh
  ports:
  protocols:
  forward: yes
  masquerade: no
  forward-ports:
  source-ports:
  icmp-blocks:
  rich rules:
exit was: 0
```

**Line-by-line breakdown:**

- `firewall-cmd --zone=bastion --permanent --add-service=ssh --add-service=http` → Add the `ssh` and `http` **named services** to the bastion zone; `--permanent` writes them into `/etc/firewalld/zones/bastion.xml` but does **not** make them live yet. A service is a pre-defined bundle (port + protocol) shipped under `/usr/lib/firewalld/services`.
- `firewall-cmd --reload` → Re-read the permanent config into the running firewall; this is the mandatory step that turns the on-disk rules into live rules.
- `firewall-cmd --zone=bastion --list-all` → Print the bastion zone's complete state; `services: http ssh` confirms both were applied.

**New words in this step:**

- **zone** — a named set of firewall rules in firewalld that you can attach to interfaces or source addresses.
- **service (firewalld)** — a named, reusable bundle of ports/protocols (e.g. `ssh` = 22/tcp) defined in an XML file, so you allow it by name instead of memorizing port numbers.

---

### Step 2 of 2 — Allow a raw custom port `8080/tcp` (permanent)

**In plain English:** We open a literal port that has no named service, persist it, reload, and confirm it appears under `ports:` — the escape hatch for software firewalld doesn't ship a service file for.

```bash
sudo firewall-cmd --zone=bastion --permanent --add-port=8080/tcp
sudo firewall-cmd --reload
sudo firewall-cmd --zone=bastion --list-all
echo "exit was: $?"
```

**Expected output:**

```
success
success
bastion
  target: default
  icmp-block-inversion: no
  interfaces:
  sources:
  services: http ssh
  ports: 8080/tcp
  protocols:
  forward: yes
  masquerade: no
  forward-ports:
  source-ports:
  icmp-blocks:
  rich rules:
exit was: 0
```

**Line-by-line breakdown:**

- `firewall-cmd --zone=bastion --permanent --add-port=8080/tcp` → Open TCP port `8080` directly; you must give both the number and the protocol as `port/proto`. Use this when no named service exists for your app.
- `firewall-cmd --reload` → Apply the new permanent rule to the running firewall.
- `firewall-cmd --zone=bastion --list-all` → Confirm `ports: 8080/tcp` now appears alongside the two services.

**New words in this step:**

- **port (raw)** — a literal `number/protocol` rule (e.g. `8080/tcp`) used when no named firewalld service bundles that port for you.

---

### Concept card (Task 1)

| Concept | What it does | Exam trap |
|---|---|---|
| `--add-service` | allows a named bundle by name (`ssh`, `http`) | the service must exist under `/usr/lib/firewalld/services` |
| `--add-port` | allows a literal `port/proto` | omitting `/tcp` or `/udp` is rejected |
| `--permanent` + `--reload` | persist to disk, then make live | `--permanent` alone never takes effect until `--reload` |

---

### Troubleshoot (Task 1)

| Symptom | Likely cause | Fix |
|---|---|---|
| Rule not active after `--permanent` | You forgot `firewall-cmd --reload` | Run `--reload`, then re-check with `--list-all` |
| `INVALID_SERVICE` error | Service name typo or no XML for it | Use `firewall-cmd --get-services` to find the exact name, or use `--add-port` |

---

## TASK 2 of 2 — ICMP, masquerade, and a rich rule

**In plain English:** We harden and extend the bastion zone — block ping, enable NAT for a routed subnet, then add a rich rule that accepts SSH only from one specific source network.

---

### Step 1 of 2 — Block ICMP echo and enable masquerade (permanent)

**In plain English:** We tell the bastion zone to drop ping requests and to perform source NAT for traffic it routes, persist both, reload, and confirm them in the zone listing.

```bash
sudo firewall-cmd --zone=bastion --permanent --add-icmp-block=echo-request --add-masquerade
sudo firewall-cmd --reload
sudo firewall-cmd --zone=bastion --list-all
echo "exit was: $?"
```

**Expected output:**

```
success
success
bastion
  target: default
  icmp-block-inversion: no
  interfaces:
  sources:
  services: http ssh
  ports: 8080/tcp
  protocols:
  forward: yes
  masquerade: yes
  forward-ports:
  source-ports:
  icmp-blocks: echo-request
  rich rules:
exit was: 0
```

**Line-by-line breakdown:**

- `firewall-cmd --zone=bastion --permanent --add-icmp-block=echo-request` → Block inbound ICMP `echo-request` (ping) for this zone so the host stops answering pings; `--remove-icmp-block=echo-request` would re-allow it.
- `--add-masquerade` → Enable **source NAT** (masquerade) so packets the host forwards from a private/routed subnet leave with the host's address — the classic gateway behavior.
- `firewall-cmd --reload` → Make both permanent changes live.
- `firewall-cmd --zone=bastion --list-all` → Confirm `masquerade: yes` and `icmp-blocks: echo-request`.

**New words in this step:**

- **ICMP block** — a firewalld rule that drops a specific ICMP message type (here `echo-request`, i.e. ping) for a zone.
- **masquerade** — source NAT: rewrite forwarded packets to appear to come from the host's own IP, letting a private subnet reach the outside through this box.

---

### Step 2 of 2 — Add a rich rule accepting SSH from one source subnet (permanent)

**In plain English:** We add a single fine-grained rule that accepts SSH only from the `192.0.2.0/24` network, persist it, reload, and confirm it shows up under `rich rules:`.

```bash
sudo firewall-cmd --zone=bastion --permanent \
  --add-rich-rule='rule family="ipv4" source address="192.0.2.0/24" service name="ssh" accept'
sudo firewall-cmd --reload
sudo firewall-cmd --zone=bastion --list-all
echo "exit was: $?"
```

**Expected output:**

```
success
success
bastion
  target: default
  icmp-block-inversion: no
  interfaces:
  sources:
  services: http ssh
  ports: 8080/tcp
  protocols:
  forward: yes
  masquerade: yes
  forward-ports:
  source-ports:
  icmp-blocks: echo-request
  rich rules:
	rule family="ipv4" source address="192.0.2.0/24" service name="ssh" accept
exit was: 0
```

**Line-by-line breakdown:**

- `firewall-cmd --zone=bastion --permanent --add-rich-rule='...'` → Add a **rich rule**, firewalld's expressive syntax that combines a source match, a service/port match, and an action in one statement. The whole rule is single-quoted so the shell passes it intact.
- `rule family="ipv4" source address="192.0.2.0/24" service name="ssh" accept` → Read it as: for IPv4 traffic *from* `192.0.2.0/24` hitting the `ssh` service, **accept**. This is finer-grained than a plain `--add-service`, which would accept SSH from everyone.
- `firewall-cmd --reload` → Apply the permanent rich rule to the running firewall.
- `firewall-cmd --zone=bastion --list-all` → Confirm the rule is listed under `rich rules:`.

**New words in this step:**

- **rich rule** — a firewalld rule language that lets you express source/destination, service/port, logging, and an explicit action (`accept`/`reject`/`drop`) in one rule.
- **source address** — the network or host a rule matches *from* (here a `/24` subnet), used to scope access to known clients.

---

### Concept card (Task 2)

| Concept | What it does | Exam trap |
|---|---|---|
| `--add-icmp-block=echo-request` | drops inbound ping for the zone | per-zone — only affects zones it's set on |
| `--add-masquerade` | enables source NAT for forwarded traffic | needs IP forwarding for real routing to work |
| `--add-rich-rule` | source+service+action in one rule | must be quoted; persist with `--permanent` |

---

### Troubleshoot (Task 2)

| Symptom | Likely cause | Fix |
|---|---|---|
| Rich rule rejected as `INVALID_RULE` | Unbalanced quotes or wrong keyword order | Single-quote the whole rule; keep `family`/`source`/`service`/action order |
| Ping still answered after icmp-block | Change was runtime-only or wrong zone | Re-add with `--permanent`, `--reload`, and target `--zone=bastion` |

---

## ✅ Lab Checklist

- [ ] Task 1 · Step 1 — Allow named services `ssh` and `http` (permanent)
- [ ] Task 1 · Step 2 — Allow a raw custom port `8080/tcp` (permanent)
- [ ] Task 2 · Step 1 — Block ICMP echo and enable masquerade (permanent)
- [ ] Task 2 · Step 2 — Add a rich rule accepting SSH from one source subnet (permanent)

---

## 🧹 Teardown

**In plain English:** Delete everything this lab created so the box is clean for the next run.

> Run this after you've verified the lab. `lab_teardown.sh` safely removes the single sandbox root — it refuses to touch `/`, `$HOME`, or any protected path.

```bash
bash lab_teardown.sh "$LAB_ROOT"     # = /tmp/lab-219
```

**System-state reversal (REQUIRED — `rm` does NOT undo firewall rules):**
Because every rule lives in the dedicated `bastion` zone, deleting that one zone removes them all in a single shot:

```bash
sudo firewall-cmd --permanent --delete-zone=bastion
sudo firewall-cmd --reload
sudo firewall-cmd --get-zones | tr ' ' '\n' | grep -x bastion || echo "bastion zone gone (OK)"
```

```bash
# Granular alternative (for learners) — undo each rule individually instead of
# deleting the zone. Equivalent end state when run before the delete above:
# sudo firewall-cmd --zone=bastion --permanent --remove-service=ssh --remove-service=http
# sudo firewall-cmd --zone=bastion --permanent --remove-port=8080/tcp
# sudo firewall-cmd --zone=bastion --permanent --remove-icmp-block=echo-request
# sudo firewall-cmd --zone=bastion --permanent --remove-masquerade
# sudo firewall-cmd --zone=bastion --permanent \
#   --remove-rich-rule='rule family="ipv4" source address="192.0.2.0/24" service name="ssh" accept'
# sudo firewall-cmd --reload
```

**Expected output:**

```
✅ Removed /tmp/lab-219 — lab workspace is clean.
```

---

## ⚠️ Common Pitfalls

| Mistake | Symptom | Fix |
|---|---|---|
| Editing the active zone over SSH | A bad rule locks you out of the box | Stage rules in a separate zone (`bastion`) and review before binding |
| `--permanent` without `--reload` | Rules visible in config but not enforced | Always follow `--permanent` with `firewall-cmd --reload` |
| Mixing runtime and permanent state | `--list-all` differs from `--permanent --list-all` | Decide per change; reload to sync runtime from permanent |

---

## 📌 Exam Strategy

On the RHCSA, firewall tasks read like "permit service X" or "allow port Y" — and the grader reboots or reloads, so a runtime-only change scores zero. Make `--permanent ... && firewall-cmd --reload` your reflex pair, then prove the result with `--list-all`. When a task is unusual or risky (NAT, source-scoped access, anything that could affect your own SSH session), do it in a named zone you control rather than gambling with the live one.

- Say "permanent, then reload" before you hit Enter — it prevents the most common firewalld point loss.
- Use `--get-services` when you can't recall a service name instead of guessing a raw port.
- Verify with `firewall-cmd --zone=ZONE --list-all` (and `--permanent --list-all`) so runtime and on-disk state both check out.

---

## 🔗 Related Labs

- [Lab 219b — Comprehensive firewalld Setup (Ansible)](../lab-219b-comprehensive-firewalld-setup-ansible/) — the same zone built idempotently with `ansible.posix.firewalld`
- [Lab 219c — Comprehensive firewalld Setup (Verify)](../lab-219c-comprehensive-firewalld-setup-verify/) — assert every rule is present with `firewall-cmd --list-all` greps
- [Lab 218a — Bastion Host Hardening (RHCSA)](../lab-218a-bastion-host-hardening-rhcsa/) — the bastion pattern this firewall policy protects

---

## 👤 Author

**Kelvin R. Tobias**  
[kelvinintech.com](https://kelvinintech.com) · [GitHub](https://github.com/kelvintechnical) · [LinkedIn](https://www.linkedin.com/in/kelvin-r-tobias-211949219)
