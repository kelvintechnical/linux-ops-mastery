# Lab 219c: Comprehensive firewalld Setup (Verify) — `firewall-cmd --query-*`, `--list-rich-rules`

**Series:** linux-ops-mastery — Security Administration · **Lab 219c of the Novice → RHCA path**  
**Certifications covered:** RHCSA EX200 (confirming firewall rules persist a reload), RHCE EX294 (validating a `firewalld` playbook's result), SRE/Security (policy attestation, drift detection)  
**Prerequisite:** [Lab 219a](../lab-219a-comprehensive-firewalld-setup-rhcsa/) and [Lab 219b](../lab-219b-comprehensive-firewalld-setup-ansible/) completed, on a RHEL 9 / Rocky / Alma sandbox you can `sudo` on with `firewalld` running  
**Time Estimate:** 25–35 minutes  
**Difficulty:** Beginner → Intermediate

---

## 🎯 Objective

Attest the bastion-zone policy built in 219a/219b with the precise tools `firewalld` gives you for *asking yes/no questions*: `--query-service`, `--query-port`, `--query-masquerade`, and `--query-icmp-block` each return a clean `yes`/`no` and a matching exit code, while `--list-rich-rules` lets you confirm the source-scoped SSH rule exists. The make-or-break check on the RHCSA is **persistence**: you will prove every rule survives a `firewall-cmd --reload` by comparing the *runtime* answer with the `--permanent` answer, catching the classic "forgot `--permanent`" mistake.

---

## 🧠 Concept

There are two ways to read a firewalld zone: `--list-all` (human-readable dump) and the `--query-*` family (scriptable yes/no per rule). For verification the query family wins because each returns an exit code — `0` for present, non-zero for absent — so you can assert without parsing text. The deeper idea is **runtime vs permanent**: a rule added without `--permanent` lives only in memory and vanishes on reload, while a `--permanent` rule is on disk but not live until reload. By asking the same question twice — once normally (runtime) and once with `--permanent` (on disk) — and requiring both to agree, you prove the rule is *both* active now and durable across a reboot. That agreement is the real attestation.

```
firewall-cmd --zone=bastion --query-service=ssh            → yes  exit 0   (runtime)
firewall-cmd --permanent --zone=bastion --query-service=ssh → yes exit 0   (on disk)
        both "yes"  ⇒  rule is live AND persistent  (PASS)
        runtime yes / permanent no  ⇒  will vanish on reload  (FAIL)

firewall-cmd --zone=bastion --list-rich-rules  → the exact rich-rule string to grep
```

> **Why this matters:** The grader reloads or reboots before scoring. A rule that is present in runtime but missing from permanent scores zero — and `--list-all` alone won't reveal the gap. Querying runtime *and* permanent is how you guarantee the policy actually persists.

---

## 📚 Command Reference

| Command | Purpose | Critical flags |
|---|---|---|
| `firewall-cmd --query-service=<svc>` | Ask if a service is allowed (yes/no + exit code) | add `--permanent` to ask the on-disk config |
| `firewall-cmd --query-port=<p/proto>` | Ask if a raw port is open | exit `0` = present, non-zero = absent |
| `firewall-cmd --query-masquerade` / `--query-icmp-block=<t>` | Ask if NAT / an ICMP block is set | per-zone; pair runtime with `--permanent` |
| `firewall-cmd --list-rich-rules` | List the zone's rich rules for grepping | scope with `--zone=bastion` |
| `firewall-cmd --reload` | Re-read permanent config into runtime | the persistence test runs a query before *and* after |

---

## 🧰 LAB-WIDE SETUP

**In plain English:** We point at the same `bastion` zone 219a/219b built and, if it is missing (they were torn down), rebuild the full rule set so this verify lab has a policy to attest — then we will reload and re-check to prove persistence.

> Run this block **once** before Task 1. It defines a single sandbox root (`LAB_ROOT`) that every file in this lab lives under, so Teardown can wipe it in one safe command.

```bash
export LAB_ROOT=/tmp/lab-219
mkdir -p "$LAB_ROOT"
cd "$LAB_ROOT"

sudo systemctl is-active firewalld

# Rebuild the bastion zone + rules permanently if it does not already exist.
if ! sudo firewall-cmd --get-zones | tr ' ' '\n' | grep -qx bastion; then
  sudo firewall-cmd --permanent --new-zone=bastion
  sudo firewall-cmd --permanent --zone=bastion --add-service=ssh --add-service=http
  sudo firewall-cmd --permanent --zone=bastion --add-port=8080/tcp
  sudo firewall-cmd --permanent --zone=bastion --add-icmp-block=echo-request --add-masquerade
  sudo firewall-cmd --permanent --zone=bastion \
    --add-rich-rule='rule family="ipv4" source address="192.0.2.0/24" service name="ssh" accept'
  sudo firewall-cmd --reload
fi

sudo firewall-cmd --zone=bastion --list-all | tee "$LAB_ROOT/zone-snapshot.txt"
echo "Sandbox ready at $(date -Is)"
echo "exit was: $?"
```

**Expected output:**

```
active
bastion
  services: http ssh
  ports: 8080/tcp
  masquerade: yes
  icmp-blocks: echo-request
  rich rules:
	rule family="ipv4" source address="192.0.2.0/24" service name="ssh" accept
Sandbox ready at 2026-06-15T17:55:03-04:00
exit was: 0
```

---

## TASK 1 of 2 — Query each rule for a yes/no verdict

**In plain English:** We ask firewalld directly whether each service, the custom port, the masquerade, and the ICMP block are present, turning every answer into an explicit OK/FAIL line.

---

### Step 1 of 2 — Query the services and the custom port

**In plain English:** We use `--query-service` and `--query-port` to confirm `ssh`, `http`, and `8080/tcp` are all allowed in the bastion zone, asserting each result.

```bash
for svc in ssh http; do
  if sudo firewall-cmd --zone=bastion --query-service="$svc" >/dev/null; then
    echo "SERVICE OK: $svc present"
  else
    echo "SERVICE FAIL: $svc missing"
  fi
done

if sudo firewall-cmd --zone=bastion --query-port=8080/tcp >/dev/null; then
  echo "PORT OK: 8080/tcp present"
else
  echo "PORT FAIL: 8080/tcp missing"
fi
```

**Expected output:**

```
SERVICE OK: ssh present
SERVICE OK: http present
PORT OK: 8080/tcp present
```

**Line-by-line breakdown:**

- `for svc in ssh http; do` → Loop over the two named services the policy should allow.
- `if sudo firewall-cmd --zone=bastion --query-service="$svc" >/dev/null; then` → Ask firewalld whether the service is present; the command exits `0` for yes, so the `if` reads the *exit code* and we discard the `yes`/`no` text.
- `echo "SERVICE OK/FAIL ..."` → Emit a clear verdict per service.
- the `--query-port=8080/tcp` block → Same yes/no test for the raw port, asserting it is open.

**New words in this step:**

- **`--query-service`** — a firewalld query that returns `yes`/`no` and an exit code for whether a service is allowed.
- **exit-code assertion** — using a command's exit status (not its text) as the pass/fail signal.

---

### Step 2 of 2 — Query masquerade, the ICMP block, and the rich rule

**In plain English:** We confirm NAT and the ping block are set with their `--query-*` commands, then grep `--list-rich-rules` to prove the source-scoped SSH rule is present.

```bash
sudo firewall-cmd --zone=bastion --query-masquerade >/dev/null \
  && echo "MASQUERADE OK" || echo "MASQUERADE FAIL"

sudo firewall-cmd --zone=bastion --query-icmp-block=echo-request >/dev/null \
  && echo "ICMP-BLOCK OK" || echo "ICMP-BLOCK FAIL"

sudo firewall-cmd --zone=bastion --list-rich-rules | grep -q '192.0.2.0/24' \
  && echo "RICH-RULE OK" || echo "RICH-RULE FAIL"
echo "exit was: $?"
```

**Expected output:**

```
MASQUERADE OK
ICMP-BLOCK OK
RICH-RULE OK
exit was: 0
```

**Line-by-line breakdown:**

- `--query-masquerade` → Ask whether source NAT is enabled for the zone; exit `0` fires the OK branch.
- `--query-icmp-block=echo-request` → Ask whether ping is blocked; exit `0` confirms the block.
- `--list-rich-rules | grep -q '192.0.2.0/24'` → List the zone's rich rules and silently grep for the source subnet; `grep -q` exits `0` if the rule text is found.
- `echo "exit was: $?"` → Record the final assertion's exit status.

**New words in this step:**

- **`--query-masquerade`** — yes/no check for whether masquerade (source NAT) is on for a zone.
- **`grep -q`** — quiet grep that prints nothing and just sets an exit code, ideal for `if`/`&&` tests.

---

### Concept card (Task 1)

| Concept | What it does | Exam trap |
|---|---|---|
| `--query-*` family | yes/no + exit code per rule | read the exit code, not the printed word |
| `grep -q` on rich rules | confirms a rule string exists | match a stable substring (the subnet) |
| per-zone scope | queries target one zone | omit `--zone` and you query the default zone |

---

### Troubleshoot (Task 1)

| Symptom | Likely cause | Fix |
|---|---|---|
| `SERVICE FAIL` for a present rule | Queried the wrong zone | Add `--zone=bastion` to the query |
| `RICH-RULE FAIL` despite the rule existing | Grep substring doesn't match stored text | Grep a stable token like `192.0.2.0/24` |

---

## TASK 2 of 2 — Prove persistence across a reload

**In plain English:** We compare each rule's runtime answer against its `--permanent` answer, then actually reload firewalld and re-query to prove every rule survives — the real persistence attestation.

---

### Step 1 of 2 — Compare runtime vs permanent for a key rule

**In plain English:** We ask whether `ssh` is allowed both in runtime and on disk, and assert the two answers agree — a rule that is runtime-only would fail this check.

```bash
sudo firewall-cmd --zone=bastion --query-service=ssh >/dev/null; rt=$?
sudo firewall-cmd --permanent --zone=bastion --query-service=ssh >/dev/null; pm=$?
echo "runtime exit: $rt | permanent exit: $pm"
test "$rt" = "0" -a "$pm" = "0" \
  && echo "PERSIST OK: ssh is live AND on disk" \
  || echo "PERSIST FAIL: runtime=$rt permanent=$pm"
```

**Expected output:**

```
runtime exit: 0 | permanent exit: 0
PERSIST OK: ssh is live AND on disk
```

**Line-by-line breakdown:**

- `--query-service=ssh ...; rt=$?` → Ask the *runtime* (in-memory) firewall and capture its exit code.
- `--permanent --query-service=ssh ...; pm=$?` → Ask the *on-disk* config and capture that exit code.
- `echo "runtime exit: ... permanent exit: ..."` → Show both codes side by side.
- `test "$rt" = "0" -a "$pm" = "0" && ... || ...` → Assert both are `0`; if runtime is `0` but permanent is non-zero, the rule is live now but will vanish on reload — exactly the bug this catches.

**New words in this step:**

- **runtime config** — the firewall rules currently in memory; lost on reload/reboot unless also permanent.
- **permanent config** — the on-disk rules under `/etc/firewalld`, applied to runtime only after a reload.

---

### Step 2 of 2 — Reload and re-query to prove survival

**In plain English:** We reload firewalld (discarding any runtime-only rules) and re-run the queries; if everything still answers `yes`, the policy is truly persistent.

```bash
sudo firewall-cmd --reload
pass=0; fail=0
for check in "--query-service=ssh" "--query-service=http" "--query-port=8080/tcp" "--query-masquerade" "--query-icmp-block=echo-request"; do
  if sudo firewall-cmd --zone=bastion $check >/dev/null; then
    echo "AFTER-RELOAD OK: $check"; pass=$((pass+1))
  else
    echo "AFTER-RELOAD FAIL: $check"; fail=$((fail+1))
  fi
done
echo "persistence summary: $pass passed, $fail failed"
```

**Expected output:**

```
success
AFTER-RELOAD OK: --query-service=ssh
AFTER-RELOAD OK: --query-service=http
AFTER-RELOAD OK: --query-port=8080/tcp
AFTER-RELOAD OK: --query-masquerade
AFTER-RELOAD OK: --query-icmp-block=echo-request
persistence summary: 5 passed, 0 failed
```

**Line-by-line breakdown:**

- `sudo firewall-cmd --reload` → Re-read the permanent config into runtime; any rule that was *only* in runtime is discarded here — the moment of truth.
- `for check in "--query-..." ; do` → Loop over every rule's query in one pass.
- `if sudo firewall-cmd --zone=bastion $check >/dev/null; then ...` → Re-ask each question *after* the reload; a `yes` now means the rule was genuinely permanent.
- `echo "persistence summary: $pass passed, $fail failed"` → Tally the results into a single attestation line — `0 failed` is the pass condition.

**New words in this step:**

- **persistence attestation** — proof that configuration survives a reload/reboot, established by re-querying after `--reload`.
- **tally** — accumulating pass/fail counts into a summary verdict.

---

### Concept card (Task 2)

| Concept | What it does | Exam trap |
|---|---|---|
| runtime vs `--permanent` query | detects runtime-only rules | both must say yes to be durable |
| `--reload` then re-query | proves survival | the reload *drops* runtime-only rules |
| pass/fail tally | one-line attestation | `0 failed` is the only acceptable result |

---

### Troubleshoot (Task 2)

| Symptom | Likely cause | Fix |
|---|---|---|
| `PERSIST FAIL: runtime=0 permanent=1` | Rule added without `--permanent` | Re-add with `--permanent`, then `--reload` |
| Rule gone after `--reload` | It was runtime-only | Re-create it permanently and reload again |

---

## ✅ Lab Checklist

- [ ] Task 1 · Step 1 — Query the services and the custom port
- [ ] Task 1 · Step 2 — Query masquerade, the ICMP block, and the rich rule
- [ ] Task 2 · Step 1 — Compare runtime vs permanent for a key rule
- [ ] Task 2 · Step 2 — Reload and re-query to prove survival

---

## 🧹 Teardown

**In plain English:** Delete everything this lab created so the box is clean for the next run.

> Run this after you've verified the lab. `lab_teardown.sh` safely removes the single sandbox root — it refuses to touch `/`, `$HOME`, or any protected path.

This lab may have **created firewalld state** (the setup rebuilds the `bastion` zone if it was missing). Because every rule lives in that dedicated zone, deleting it removes them all:

```bash
sudo firewall-cmd --permanent --delete-zone=bastion
sudo firewall-cmd --reload
sudo firewall-cmd --get-zones | tr ' ' '\n' | grep -x bastion || echo "bastion zone gone (OK)"
bash lab_teardown.sh "$LAB_ROOT"     # = /tmp/lab-219
```

**Expected output:**

```
✅ Removed /tmp/lab-219 — lab workspace is clean.
```

---

## ⚠️ Common Pitfalls

| Mistake | Symptom | Fix |
|---|---|---|
| Verifying with `--list-all` only | A runtime-only rule looks fine until reload | Query runtime *and* `--permanent`, then reload |
| Reading the `yes`/`no` text in a script | Brittle parsing | Use the `--query-*` exit code instead |
| Forgetting `--zone=bastion` on a query | You check the default zone by accident | Always scope queries to the zone under test |

---

## 📌 Exam Strategy

Firewall verification is a persistence test in disguise. Use the `--query-*` family for clean exit-code assertions, then prove durability by comparing runtime to `--permanent` and re-querying after a `--reload`. If a rule cannot survive a reload it scores zero, so make "query, reload, re-query" your attestation ritual.

- Prefer `--query-*` exit codes over parsing `--list-all` text.
- A rule must answer `yes` in both runtime and `--permanent` to count as durable.
- Reload, then re-query — that single step catches every runtime-only mistake.

---

## 🔗 Related Labs

- [Lab 219a — Comprehensive firewalld Setup (RHCSA)](../lab-219a-comprehensive-firewalld-setup-rhcsa/) — the hand-typed policy this lab attests
- [Lab 219b — Comprehensive firewalld Setup (Ansible)](../lab-219b-comprehensive-firewalld-setup-ansible/) — the playbook whose converged zone you verify here
- [Lab 217c — Monitor Security Updates (Verify)](../lab-217c-monitor-security-updates-verify/) — the same evidence-and-exit-code discipline for patch surveys

---

## 👤 Author

**Kelvin R. Tobias**  
[kelvinintech.com](https://kelvinintech.com) · [GitHub](https://github.com/kelvintechnical) · [LinkedIn](https://www.linkedin.com/in/kelvin-r-tobias-211949219)
