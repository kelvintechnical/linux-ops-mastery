# Lab 06c: Verifying SELinux Contexts — audit + relabel-survival proof

- **Series:** linux-ops-mastery — File Operations & Shell Fundamentals
- **Trilogy:** `06a` (RHCSA) → `06b` (Ansible) → **`06c` (Verify — you are here)**
- **Career arcs covered:** RHCSA EX200, RHCE EX294 (auditor seat), SRE (post-change context audit), All exams (verification reflex)
- **Prerequisite:** Lab 06a and Lab 06b completed — this lab verifies their combined effect
- **Time Estimate:** 25–35 minutes
- **Tasks:** 2 (Task 1 = audit, Task 2 = relabel-survival proof)
- **Practice Directory (rotation #06):** `/etc`
- **Sandbox:** `/tmp/listing-lab/` · `/srv/www-lab-06/`
- **Traps rehearsed this lab:** **T11-E** (trusting `chcon` without checking policy) · **T41** (skipping the relabel test)

> **This lab's practice directory is: `/etc`** — every task references it in at least two commands.

---

## 🖥️ LAB HEADER BLOCK — run this FIRST

```bash
echo "🖥️  ENV:   ${ENV:-DECLARE_ME}"
echo "💿  DISK:  $(lsblk 2>/dev/null | awk '$NF=="disk"{print "/dev/"$1}' | paste -sd, -)"
echo "🌐  NIC:   $(ip -o addr show 2>/dev/null | awk '$2!="lo"{print $2}' | sort -u | paste -sd, -)"
echo "🔐  SE:    $(getenforce 2>/dev/null || echo n/a)"
echo "📦  OS:    $(cat /etc/redhat-release 2>/dev/null || grep PRETTY_NAME /etc/os-release)"
echo "🕒  TIME:  $(date -Is)"
echo "👤  USER:  $(whoami)@$(hostname)"
echo "⚠️  TRAP REMINDERS THIS LAB: T11-E T41"
echo "📁  PRACTICE DIR: /etc"
echo ""
echo "🧾 Journal check — Lab 06a and 06b must already be done:"
test -f /root/rhcsa_journal/lab-06a/task2/done.txt && echo "  ✅ lab-06a task2 done"
test -f /root/rhcsa_journal/lab-06b/task2/done.txt && echo "  ✅ lab-06b task2 done"
```

> **STOP — if either `done.txt` check above failed, return and finish Lab 06a or 06b first. This lab depends on the journal artifacts they produce.**

---

## 🎯 Objective

Take off the operator's hat and put on the **auditor's hat**. Lab 06a labeled files by hand; Lab 06b applied policy via Ansible. Neither proves contexts are correct **right now** or will survive relabel. Lab 06c **proves** contexts match policy using RHCSA-grade inspection only — no playbook output, no trust in prior labs.

---

## 🧠 Concept: Trust But Verify — Especially When `chcon` "Worked"

`chcon` changing a context on the command line means "I manually set this label." That is **not** the same as "this label matches the system policy and will survive a relabel." Examples of the gap:

| What the operator saw | What can still be wrong |
|---|---|
| `chcon` returned exit 0 | Temporary — `restorecon` will revert it |
| `ls -Z` shows expected type | Policy (`semanage fcontext`) may not match — only live label changed |
| Ansible reported `changed=0` | A process relabeled the file between runs |

The grader's reflex is to **inspect the system directly** after any SELinux change: `ls -Z`, `matchpathcon`, `semanage fcontext -l`, `restorecon -n`. No `ansible.*` commands.

---

## 📚 Inspection Reference (everything for Tasks 1–2)

| Tool | Purpose |
|---|---|
| `ls -Z PATH` | Live SELinux context on disk |
| `matchpathcon -V PATH` | Policy-expected default context |
| `semanage fcontext -l` | Persistent policy rules |
| `restorecon -Rv PATH` | Apply policy labels (full relabel) |
| `restorecon -nRv PATH` | Dry-run relabel — safe audit |
| `chcon -t TYPE PATH` | Manual override — wiped by `restorecon` unless policy matches |
| `getenforce` | SELinux mode — context checks meaningless if off |
| `diff -u EXPECTED ACTUAL` | Line-level comparison against baseline |

---

## 🚦 Lab-Wide Setup — run BEFORE Task 1

```bash
sudo -i

# Set up the verification sandbox and seed it with a decoy file
# (so we can prove our audit catches mislabeled files).
mkdir -p /tmp/listing-lab/selinux-verify
mkdir -p /srv/www-lab-06
cd /tmp/listing-lab/selinux-verify

# Capture what Lab 06b's playbook expected to label
cat > /tmp/listing-lab/selinux-verify/expected-contexts.txt <<'EOF'
/srv/www-lab-06/index.html httpd_sys_content_t
/srv/www-lab-06/ httpd_sys_content_t
EOF

# Decoy: a file with a WRONG context that chcon set but policy does not declare
echo "decoy page" > /tmp/listing-lab/selinux-verify/decoy-wrong-context.html
chcon -t bin_t /tmp/listing-lab/selinux-verify/decoy-wrong-context.html

# Ensure the real web content from Lab 06a/b exists
test -f /srv/www-lab-06/index.html || echo "<h1>Lab 06</h1>" > /srv/www-lab-06/index.html

ls -laZ /tmp/listing-lab/selinux-verify/
ls -laZ /srv/www-lab-06/
cat /tmp/listing-lab/selinux-verify/expected-contexts.txt
echo "exit was: $?"
```

> **STOP — paste output before Task 1.**

---

## Task 1 — Audit SELinux contexts with ≥3 RHCSA inspection commands

**Practice directory this task:** `/etc` · SELinux policy files live under `/etc/selinux/` — the audit cross-checks live labels against the policy database that governs them.

### 🔁 Warm-Up — commands woven into Task 1

```bash
ls -laZ /etc/selinux/config                          2>&1 | tee /tmp/listing-lab/selinux-verify/warmup.txt
getenforce
matchpathcon -V /etc/selinux/config
semanage fcontext -l | grep -c www-lab-06
test -f /etc/selinux/config && echo "selinux config OK"
find /etc/selinux -maxdepth 2 -name '*.conf'         2>/dev/null | head -n 5
set -o pipefail
echo "Warm-up done by $(whoami) at $(date -Is)"
echo "exit was: $?"
```

> Carry from Lab 06b: the `semanage fcontext -l | grep` pattern continues — but now we cross-check against the **declared** baseline (`expected-contexts.txt`), not just count rules.

### Purpose

Walk through each expected-labeled path and prove with three independent RHCSA inspection commands that the live context matches policy. Then run a **diff** between the declared baseline and the actual contexts to catch any discrepancy a single command might miss.

### 🧵 WEAVE TRACE — warm-up commands re-used in this task body

| Warm-up command | Role inside Task 1 |
|---|---|
| `matchpathcon -V` | Policy-expected context — the "should be" answer |
| `semanage fcontext -l \| grep` | Persistent policy rule — the "declared" answer |
| `ls -Z` | Live on-disk context — the "actually is" answer |
| `2>&1 \| tee` | Captures checks into `task1/audit.txt` |

### Main command block

```bash
mkdir -p /tmp/listing-lab/selinux-verify/task1
cd /tmp/listing-lab/selinux-verify

echo "═══ SELinux Context Audit — Lab 06b targets must match policy ═══" \
  2>&1 | tee /tmp/listing-lab/selinux-verify/task1/audit.txt

PASS=0
FAIL=0
while IFS= read -r line; do
  path=$(echo "$line" | awk '{print $1}')
  expected_type=$(echo "$line" | awk '{print $2}')
  echo "─── checking: $path (expect type: $expected_type) ───" \
    | tee -a /tmp/listing-lab/selinux-verify/task1/audit.txt

  actual=$(ls -dZ "$path" 2>/dev/null | awk '{print $1}' | cut -d: -f3)
  echo "  ls -Z type: $actual" | tee -a /tmp/listing-lab/selinux-verify/task1/audit.txt
  policy=$(matchpathcon -V "$path" 2>/dev/null | awk '{print $1}' | cut -d: -f3)
  echo "  matchpathcon type: $policy" | tee -a /tmp/listing-lab/selinux-verify/task1/audit.txt
  semanage fcontext -l 2>/dev/null | grep "www-lab-06" \
    | tee -a /tmp/listing-lab/selinux-verify/task1/audit.txt
  if [ "$actual" = "$expected_type" ] && [ "$policy" = "$expected_type" ]; then
    echo "  ✅ PASS: live=$actual policy=$policy expected=$expected_type" \
      | tee -a /tmp/listing-lab/selinux-verify/task1/audit.txt
    PASS=$(( PASS + 1 ))
  else
    echo "  ❌ FAIL: live=$actual policy=$policy expected=$expected_type" \
      | tee -a /tmp/listing-lab/selinux-verify/task1/audit.txt
    FAIL=$(( FAIL + 1 ))
  fi
done < /tmp/listing-lab/selinux-verify/expected-contexts.txt

echo "═══ Audit summary: $PASS pass, $FAIL fail ═══" \
  | tee -a /tmp/listing-lab/selinux-verify/task1/audit.txt

# Diff + decoy (T11-E trap)
echo "═══ Diff: declared baseline vs actual contexts ═══" \
  | tee -a /tmp/listing-lab/selinux-verify/task1/audit.txt
{
  while IFS= read -r line; do
    path=$(echo "$line" | awk '{print $1}')
    expected_type=$(echo "$line" | awk '{print $2}')
    actual=$(ls -dZ "$path" 2>/dev/null | awk '{print $1}' | cut -d: -f3)
    echo "$path $actual"
  done < /tmp/listing-lab/selinux-verify/expected-contexts.txt
} | sort > /tmp/listing-lab/selinux-verify/task1/actual-contexts.txt

diff -u /tmp/listing-lab/selinux-verify/expected-contexts.txt \
        /tmp/listing-lab/selinux-verify/task1/actual-contexts.txt \
  | tee -a /tmp/listing-lab/selinux-verify/task1/audit.txt || true

# Decoy: chcon without policy
echo "═══ Decoy check — chcon without policy should FAIL ═══" \
  | tee -a /tmp/listing-lab/selinux-verify/task1/audit.txt
decoy_type=$(ls -Z /tmp/listing-lab/selinux-verify/decoy-wrong-context.html \
  | awk '{print $1}' | cut -d: -f3)
decoy_policy=$(matchpathcon -V /tmp/listing-lab/selinux-verify/decoy-wrong-context.html \
  2>/dev/null | awk '{print $1}' | cut -d: -f3)
echo "  decoy live=$decoy_type policy=$decoy_policy (mismatch = T11-E trap caught)" \
  | tee -a /tmp/listing-lab/selinux-verify/task1/audit.txt

echo "exit was: $?"
```

### Human-readable breakdown

1. For each path in `expected-contexts.txt`, run **three inspection commands**: `ls -Z`, `matchpathcon -V`, `semanage fcontext -l | grep`.
2. Maintain `PASS`/`FAIL` counters — `FAIL` should be 0 if Lab 06a/b did their job.
3. Run `diff -u` against actual live contexts; check the decoy proves T11-E (`chcon` without policy).

### The story

The auditor seat is the most under-trained skill in RHCSA prep. The three-tool cross-check (`ls -Z` + `matchpathcon` + `semanage fcontext`) catches what `chcon` misses: labels that look correct on disk but do not match policy, paths forgotten in `semanage fcontext`, or contexts relabeled between Lab 06b and Lab 06c. Lab 06c bakes the audit reflex into your workflow — every SELinux change generates a paired audit.

### Expected output

```text
═══ SELinux Context Audit — Lab 06b targets must match policy ═══
─── checking: /srv/www-lab-06/index.html (expect type: httpd_sys_content_t) ───
  ls -Z type: httpd_sys_content_t
  matchpathcon type: httpd_sys_content_t
  /srv/www-lab-06(/.*)?    all files    system_u:object_r:httpd_sys_content_t:s0
  ✅ PASS: live=httpd_sys_content_t policy=httpd_sys_content_t expected=httpd_sys_content_t
(... second path identical pattern ...)
═══ Audit summary: 2 pass, 0 fail ═══
═══ Diff: declared baseline vs actual contexts ═══
(empty diff — clean exit)
═══ Decoy check — chcon without policy should FAIL ═══
  decoy live=bin_t policy=admin_home_t (mismatch = T11-E trap caught)
exit was: 0
```

> **The win condition: `2 pass, 0 fail` and an empty diff.** Anything else means Lab 06a or 06b is incomplete.

### Switches

| Token | Meaning |
|---|---|
| `ls -Z PATH` / `ls -dZ PATH` | Live SELinux context (directory itself with `-d`) |
| `matchpathcon -V PATH` | Policy-expected context — verify mode |
| `semanage fcontext -l` | List all persistent file context rules |
| `cut -d: -f3` | Extract the type field from `user:role:type:level` |
| `diff -u A B` | Unified diff — empty output means match |
| `\|\| true` | Mask a non-zero exit so the script continues — use sparingly |

### 🧠 Concept Card

|   | Concept | What it does |
|---|---|---|
|   | Three-tool cross-check | `ls -Z`, `matchpathcon`, `semanage fcontext` — three answers to "is this labeled correctly?" |
|   | Declared baseline + `diff` | Text file drives the audit loop; `diff` catches what single-path inspection misses |
|   | Decoy file | Proves `chcon` without policy is a trap — won't survive relabel |
| 🪤 | **Trap Risk T11-E** | Trusting `chcon` without checking policy — always verify with `matchpathcon` and `semanage fcontext`. |

### 🔁 PERSISTENCE CHECK

| What was configured | Verification command | Why it matters |
|---|---|---|
| Audit transcript | `wc -l /root/rhcsa_journal/lab-06c/task1/audit.txt` | Must be > 0 |
| All contexts match | `matchpathcon -V /srv/www-lab-06/index.html` | Re-run any time; no mismatch |
| Policy rule exists | `semanage fcontext -l \| grep www-lab-06` | Persistent rule in policy database |

> **Reboot reasoning:** Both `/tmp/listing-lab/` (the audit workspace) and any `chcon`-only changes evaporate at reboot. The **only** things that survive are the journal under `/root/rhcsa_journal/` and the `semanage fcontext` policy rules. If the journal does not contain `audit.txt` and `expected-contexts.txt`, this audit cannot be reproduced — and that means the verification is effectively gone too.

### Journal write — BEFORE cleanup

```bash
LAB=lab-06c
TASK=task1
JDIR="/root/rhcsa_journal/${LAB}/${TASK}"
mkdir -p "$JDIR"
cp /tmp/listing-lab/selinux-verify/task1/audit.txt           "$JDIR/audit.txt"
cp /tmp/listing-lab/selinux-verify/task1/actual-contexts.txt "$JDIR/actual-contexts.txt"
cp /tmp/listing-lab/selinux-verify/expected-contexts.txt     "$JDIR/expected-contexts.txt"

cat > "$JDIR/done.txt" <<EOF
LAB:    ${LAB}
TASK:   ${TASK}
DATE:   $(date -Is)
USER:   $(whoami)@$(hostname)
STATUS: COMPLETE
EOF

cat > "$JDIR/notes.txt" <<EOF
TOPIC:    Three-tool SELinux audit (ls -Z + matchpathcon + semanage fcontext) + diff against declared baseline
COMMANDS: ls -Z, matchpathcon -V, semanage fcontext -l, diff -u, cut -d:
TRAPS:    T11-E rehearsed (we independently verified — did not trust chcon alone)
MISSED:   (fill in if any ⚠️ flags)
NEXT:     task2 — prove policy-based contexts survive restorecon and simulated reboot
EOF

ls -la "$JDIR"
echo "exit was: $?"
```

### 🧹 Cleanup

```bash
# Keep the journal, drop the live audit workspace
rm -rf /tmp/listing-lab/selinux-verify/task1
ls /tmp/listing-lab/selinux-verify/
echo "exit was: $?"
```

### Troubleshoot

| Symptom | Fix |
|---|---|
| `1 fail` instead of `0` | Re-run Lab 06b or `restorecon -Rv /srv/www-lab-06/` |
| `matchpathcon` differs from `ls -Z` | Live label wrong — run `restorecon -Rv` |
| `semanage fcontext` returns nothing | Persistent rule missing — re-run Lab 06a/b |
| Empty `audit.txt` | Enable `set -o pipefail`; re-run with `tee` |
| Decoy shows matching types | Re-create with `chcon -t bin_t` |

> **STOP — paste the "Audit summary" line and the diff output (or "empty diff" confirmation) before Task 2.**

---

## Task 2 — Relabel-survival proof: prove policy contexts survive restorecon + simulated reboot

**Practice directory this task:** `/etc` · the contrast with `/tmp/` is the entire lesson — `/tmp` evaporates, `/etc/selinux/` and `/root/rhcsa_journal/` do not.

### 🔁 Warm-Up — commands woven into Task 2

```bash
ls -laZ /etc/selinux/targeted/contexts/files/       2>&1 | tee /tmp/listing-lab/selinux-verify/warmup-task2.txt
getenforce
restorecon -nRv /srv/www-lab-06/                     2>&1 | head -n 5
semanage fcontext -l | grep www-lab-06
test -f /root/rhcsa_journal/lab-06c/task1/audit.txt && echo "task1 journal OK"
find /tmp/listing-lab -type f                          2>/dev/null | wc -l
stat -c '%n mountpoint=%m' /tmp /root /etc/selinux
set -o pipefail
echo "Warm-up done by $(whoami) at $(date -Is)"
echo "exit was: $?"
```

> Carry: `stat -c '%m'` reveals the **mount point** for each path — `/tmp` is often on `tmpfs` and `/root` + `/etc` are on the root partition, which is the **structural reason** the journal and policy survive reboot.

### Purpose

Prove that policy-based contexts (set via `semanage fcontext` + `restorecon`) survive a full relabel, while manual `chcon` changes do not. Then simulate a reboot — clear `/tmp/listing-lab/` entirely — and re-run the audit from Task 1 using **only** the journal artifacts under `/root/rhcsa_journal/`. If the audit reproduces the same `2 pass, 0 fail` result, persistence is proven.

### 🧵 WEAVE TRACE — warm-up commands re-used in this task body

| Warm-up command | Role inside Task 2 |
|---|---|
| `restorecon -nRv` | Dry-run relabel — shows what would change |
| `stat -c '%m'` | Confirms tmpfs vs root partition |
| `find /tmp/listing-lab` | Verifies `/tmp` was cleared after simulated reboot |
| `2>&1 \| tee` | Captures relabel-survival transcript |

### Main command block

```bash
mkdir -p /tmp/listing-lab/selinux-verify/task2

echo "═══ Pre-relabel state ═══" \
  2>&1 | tee /tmp/listing-lab/selinux-verify/task2/relabel-proof.txt
ls -Z /srv/www-lab-06/index.html \
  | tee -a /tmp/listing-lab/selinux-verify/task2/relabel-proof.txt

# ── Step 1: chcon on parallel test file (wiped by restorecon) ──
echo "═══ chcon test — manual override ═══" \
  | tee -a /tmp/listing-lab/selinux-verify/task2/relabel-proof.txt
cp /srv/www-lab-06/index.html /srv/www-lab-06/chcon-test.html
chcon -t bin_t /srv/www-lab-06/chcon-test.html
ls -Z /srv/www-lab-06/chcon-test.html \
  | tee -a /tmp/listing-lab/selinux-verify/task2/relabel-proof.txt

# ── Step 2: restorecon -Rv — policy wins, chcon loses ──
echo "═══ restorecon -Rv /srv/www-lab-06/ ═══" \
  | tee -a /tmp/listing-lab/selinux-verify/task2/relabel-proof.txt
restorecon -Rv /srv/www-lab-06/ \
  2>&1 | tee -a /tmp/listing-lab/selinux-verify/task2/relabel-proof.txt
ls -Z /srv/www-lab-06/chcon-test.html /srv/www-lab-06/index.html \
  | tee -a /tmp/listing-lab/selinux-verify/task2/relabel-proof.txt

# Verify: chcon-test should now be httpd_sys_content_t (policy restored it)
chcon_type=$(ls -Z /srv/www-lab-06/chcon-test.html | awk '{print $1}' | cut -d: -f3)
if [ "$chcon_type" = "httpd_sys_content_t" ]; then
  echo "  ✅ chcon override WIPED by restorecon — policy survived" \
    | tee -a /tmp/listing-lab/selinux-verify/task2/relabel-proof.txt
else
  echo "  ❌ chcon override STILL $chcon_type — policy rule missing?" \
    | tee -a /tmp/listing-lab/selinux-verify/task2/relabel-proof.txt
fi

# ── Step 3: Simulate a reboot — wipe /tmp, keep /root/ and /etc/ ──
echo "═══ SIMULATING REBOOT — clearing /tmp/listing-lab/ ═══" \
  | tee -a /tmp/listing-lab/selinux-verify/task2/relabel-proof.txt
echo "  at $(date -Is)" | tee -a /tmp/listing-lab/selinux-verify/task2/relabel-proof.txt
stat -c '  %n  is on  %m' /tmp /root /etc/selinux /srv/www-lab-06 \
  2>&1 | tee -a /tmp/listing-lab/selinux-verify/task2/relabel-proof.txt

# Move task2 transcript to /root BEFORE we delete /tmp/listing-lab/
JDIR="/root/rhcsa_journal/lab-06c/task2"
mkdir -p "$JDIR"
cp /tmp/listing-lab/selinux-verify/task2/relabel-proof.txt "$JDIR/relabel-proof.txt"

# Now the simulated reboot — wipe /tmp/listing-lab/
rm -rf /tmp/listing-lab/* 2>/dev/null
test -d /tmp/listing-lab && echo "  /tmp/listing-lab still exists (we kept the dir, wiped contents)"
find /tmp/listing-lab -type f 2>/dev/null | wc -l  # must be 0

# ── Post-reboot: reconstruct audit from /root/ journal only ──
echo "═══ Post-reboot — reconstructing from journal under /root/ ═══" \
  2>&1 | tee "$JDIR/post-reboot-audit.txt"

# 1. Journal files must still exist
for f in /root/rhcsa_journal/lab-06c/task1/audit.txt \
         /root/rhcsa_journal/lab-06c/task1/expected-contexts.txt \
         /root/rhcsa_journal/lab-06b/playbooks/task1.yml \
         /root/rhcsa_journal/lab-06b/playbooks/task2.yml; do
  if test -f "$f"; then
    echo "  ✅ survived: $f ($(wc -l < "$f") lines)" \
      | tee -a "$JDIR/post-reboot-audit.txt"
  else
    echo "  ❌ MISSING:  $f" \
      | tee -a "$JDIR/post-reboot-audit.txt"
  fi
done

# 2. Policy rule must still exist (lives in /etc/, not /tmp/)
echo "═══ Policy rule check (survives reboot) ═══" \
  | tee -a "$JDIR/post-reboot-audit.txt"
semanage fcontext -l 2>/dev/null | grep www-lab-06 \
  | tee -a "$JDIR/post-reboot-audit.txt"

# 3. Re-run the audit loop using ONLY the journal baseline
PASS=0
FAIL=0
while IFS= read -r line; do
  path=$(echo "$line" | awk '{print $1}')
  expected_type=$(echo "$line" | awk '{print $2}')
  actual=$(ls -dZ "$path" 2>/dev/null | awk '{print $1}' | cut -d: -f3)
  policy=$(matchpathcon -V "$path" 2>/dev/null | awk '{print $1}' | cut -d: -f3)
  if [ "$actual" = "$expected_type" ] && [ "$policy" = "$expected_type" ]; then
    echo "  ✅ $path live=$actual policy=$policy" \
      | tee -a "$JDIR/post-reboot-audit.txt"
    PASS=$(( PASS + 1 ))
  else
    echo "  ❌ $path live=$actual policy=$policy expected=$expected_type" \
      | tee -a "$JDIR/post-reboot-audit.txt"
    FAIL=$(( FAIL + 1 ))
  fi
done < /root/rhcsa_journal/lab-06c/task1/expected-contexts.txt

echo "═══ Post-reboot summary: $PASS pass, $FAIL fail ═══" \
  | tee -a "$JDIR/post-reboot-audit.txt"

# 4. Re-run the Ansible idempotence proof — if the playbook is truly idempotent,
#    this still reports changed=0 even though /tmp was wiped.
ansible-playbook /root/rhcsa_journal/lab-06b/playbooks/task2.yml \
  2>&1 | tee "$JDIR/post-reboot-ansible.txt" | grep -E "PLAY RECAP|changed="

echo "exit was: $?"
```

### Human-readable breakdown

1. Snapshot pre-relabel contexts; copy `index.html` to `chcon-test.html` and `chcon -t bin_t` it (T11-E trap).
2. Run `restorecon -Rv /srv/www-lab-06/` — policy contexts survive; the `chcon` override is wiped back to `httpd_sys_content_t`.
3. Save relabel proof to `/root/` **before** wiping `/tmp/listing-lab/` (simulated reboot).
4. Reconstruct the audit from journal artifacts only — prove policy rule, contexts, and Ansible idempotence all survive.

### Reading it left to right

- `restorecon -Rv` applies policy labels; `chcon -t` is a temporary override wiped by relabel.
- `stat -c '%m'` exposes mount points — `/tmp` evaporates, `/root/` and `/etc/` persist.
- Journal redirect (`< /root/rhcsa_journal/...`) is the structural persistence test.

### The story

Running `ls -Z` once after `chcon` proves very little — the label could vanish on the next relabel. `restorecon -Rv` proves the **policy** is correct, not just the live label. Wiping `/tmp` and re-running from `/root/` proves the audit is reproducible after reboot. For RHCSA: every SELinux verification must survive `restorecon` and reboot. For RHCE: every playbook needs a baseline file stored alongside it.

### Expected output

```text
═══ chcon test — manual override on parallel file ═══
  before restorecon:  .../chcon-test.html  bin_t
═══ restorecon -Rv /srv/www-lab-06/ ═══
Relabeled .../chcon-test.html from bin_t to httpd_sys_content_t
  ✅ chcon override WIPED by restorecon — policy survived
═══ SIMULATING REBOOT — clearing /tmp/listing-lab/ ═══
  /tmp  is on  /tmp    /root  is on  /    /etc/selinux  is on  /
0   (← find /tmp/listing-lab -type f | wc -l)
═══ Post-reboot — reconstructing from journal under /root/ ═══
  ✅ survived: .../lab-06c/task1/audit.txt (28 lines)
  ✅ survived: .../lab-06b/playbooks/task2.yml (28 lines)
/srv/www-lab-06(/.*)?    all files    system_u:object_r:httpd_sys_content_t:s0
═══ Post-reboot summary: 2 pass, 0 fail ═══
PLAY RECAP ****  localhost : ok=3 changed=0 unreachable=0 failed=0
exit was: 0
```

### Switches

| Token | Meaning |
|---|---|
| `restorecon -Rv PATH` | Recursive verbose relabel — applies policy |
| `restorecon -nRv PATH` | Dry-run relabel — no changes |
| `chcon -t TYPE PATH` | Temporary type override |
| `stat -c '%m'` | Mount point containing the path |
| `grep -E "A\|B"` | Match line containing A or B |

### 🧠 Concept Card

|   | Concept | What it does |
|---|---|---|
|   | `restorecon` vs `chcon` | `restorecon` applies policy; `chcon` is a manual override policy reverts |
|   | Relabel-survival test | Only proof a context is policy-backed, not just manually set |
|   | Journal as cold-storage audit | Verification artifacts must live in `/root/rhcsa_journal/` |
| 🪤 | **Trap Risk T41** | Skipping relabel/reboot test — discover `chcon`-only changes too late. |

### 🔁 PERSISTENCE CHECK (this lab IS the persistence check)

| What was configured | Verification command | Why it matters |
|---|---|---|
| Relabel proof persisted | `wc -l /root/rhcsa_journal/lab-06c/task2/relabel-proof.txt` | Task 2 proof artifact |
| Post-reboot audit | `wc -l /root/rhcsa_journal/lab-06c/task2/post-reboot-audit.txt` | Audit reproduced from journal |
| Policy rule survived | `semanage fcontext -l \| grep www-lab-06` | Lives in `/etc/` — survives reboot |
| Trilogy complete | `find /root/rhcsa_journal/lab-06{a,b,c} -name done.txt \| wc -l` | Should be `6` |

### Journal write — BEFORE cleanup

```bash
LAB=lab-06c
TASK=task2
JDIR="/root/rhcsa_journal/${LAB}/${TASK}"
# (already created earlier in the command block)

cat > "$JDIR/done.txt" <<EOF
LAB:    ${LAB}
TASK:   ${TASK}
DATE:   $(date -Is)
USER:   $(whoami)@$(hostname)
STATUS: COMPLETE
EOF

cat > "$JDIR/notes.txt" <<EOF
TOPIC:    Relabel-survival proof + simulated-reboot persistence — reconstruct audit from /root/ journal only
COMMANDS: restorecon -Rv, chcon -t, stat -c '%m', semanage fcontext -l, journal cross-check
TRAPS:    T41 rehearsed (we did NOT skip the relabel/reboot test — we proved persistence)
MISSED:   (fill in if any ⚠️ flags)
NEXT:     Lab 07a (hard-and-soft-links) — file identity beyond permissions and context
EOF

ls -la "$JDIR"
echo "── Trilogy state ──"
find /root/rhcsa_journal/lab-06{a,b,c} -name done.txt | sort
echo "exit was: $?"
```

### 🧹 Cleanup

```bash
rm -f /srv/www-lab-06/chcon-test.html
rm -rf /tmp/listing-lab
test -d /tmp/listing-lab || echo "verify sandbox gone — clean exit"
echo "exit was: $?"
```

### Troubleshoot

| Symptom | Fix |
|---|---|
| `chcon-test.html` still `bin_t` after `restorecon` | `semanage fcontext` rule missing — re-run Lab 06a/b |
| ❌ MISSING journal file | Go back and finish the prior lab's journal write step |
| Post-reboot audit `1 fail` | Run `restorecon -Rv /srv/www-lab-06/` |
| Ansible shows `changed=1` | Wrong module call — fix playbook before continuing |
| `getenforce` shows `Disabled` | Enable SELinux in `/etc/selinux/config` and reboot |

> **STOP — paste the "Post-reboot summary: 2 pass, 0 fail" line and the trilogy `done.txt` list before completing Lab 06.**

---

## Lab 06c Checklist (2 tasks)

- [ ] Task 1 — Three-tool SELinux audit (`ls -Z` + `matchpathcon` + `semanage fcontext`) of all Lab 06b targets + `diff` against declared baseline
- [ ] Task 2 — Relabel-survival proof (`restorecon -Rv` wipes `chcon`) + simulated-reboot persistence — reconstruct the audit using only `/root/rhcsa_journal/` artifacts

---

## 🏁 Lab 06 Trilogy — completion check

After all three sub-labs are done, this command should show **six** `done.txt` files:

```bash
find /root/rhcsa_journal/lab-06{a,b,c} -name done.txt | sort
```

Expected output:

```text
/root/rhcsa_journal/lab-06a/task1/done.txt
/root/rhcsa_journal/lab-06a/task2/done.txt
/root/rhcsa_journal/lab-06b/task1/done.txt
/root/rhcsa_journal/lab-06b/task2/done.txt
/root/rhcsa_journal/lab-06c/task1/done.txt
/root/rhcsa_journal/lab-06c/task2/done.txt
```

If any are missing, that sub-lab is incomplete. Do not start Lab 07a until the trilogy is closed.

---

## 🔗 Related Labs

| Lab | Connection |
|---|---|
| **Lab 06a** — RHCSA hand-typed SELinux labeling | Imperative form being audited |
| **Lab 06b** — Listing Files & SELinux via Ansible | Declarative form being audited |
| Lab 11c — Verifying File Removal | Same three-tool + diff + reboot audit pattern |

---

## 👤 Author

**Kelvin R. Tobias**
[kelvinintech.com](https://kelvinintech.com) · [GitHub](https://github.com/kelvintechnical) · [LinkedIn](https://www.linkedin.com/in/kelvin-r-tobias-211949219)
