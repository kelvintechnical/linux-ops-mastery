# Lab 00c: Ansible Control Node — Verification Capstone & Persistence Proof

- **Series:** linux-ops-mastery — Prerequisite Trilogy (run BEFORE Lab 01)
- **Trilogy:** `00a` (RHCSA) → `00b` (Ansible) → **`00c` (Verify — you are here)**
- **Career arcs covered:** RHCSA EX200 (verification reflex), RHCE EX294 (auditor seat — prove the toolchain works without trusting any single command), SRE (post-change verification habit), All exams (the "what would you check next" interview reflex)
- **Prerequisite:** Lab 00a and Lab 00b completed — this lab verifies their combined effect
- **Time Estimate:** 20–30 minutes
- **Tasks:** 2 (Task 1 = three-tool audit, Task 2 = simulated-reboot persistence proof)
- **Practice Directory (rotation #00):** `/root/rhcsa_journal`
- **Sandbox:** `/root/rhcsa_journal/lab-00c`
- **Traps rehearsed this lab:** **T11-E-equivalent** (trusting `ansible -m ping` once and never re-verifying after a reboot — for Lab 00 specifically, this is "trusting Lab 00a/00b's done.txt without re-running the four-tool audit")

> **This lab's practice directory is: `/root/rhcsa_journal`** — every task references it in at least two commands. The audit workspace lives at `/root/rhcsa_journal/lab-00c/`; the artifacts being audited are at `/root/rhcsa_journal/lab-00a/`, `lab-00b/`, the package install from Task 1 of 00a, the collections + config from Task 1 of 00b, and the playbooks at `/root/rhcsa_journal/lab-00b/playbooks/`.

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
echo "⚠️  TRAP REMINDERS THIS LAB: T11-E-equivalent (trust-but-verify on the toolchain)"
echo "📁  PRACTICE DIR: /root/rhcsa_journal/lab-00c"
echo ""
echo "🧾 Journal check — Lab 00a and 00b must already be done:"
test -f /root/rhcsa_journal/lab-00a/task1/done.txt && echo "  ✅ lab-00a task1 done (ansible-core installed)"
test -f /root/rhcsa_journal/lab-00a/task2/done.txt && echo "  ✅ lab-00a task2 done (journal tree built)"
test -f /root/rhcsa_journal/lab-00b/task1/done.txt && echo "  ✅ lab-00b task1 done (collections + cfg + first playbook)"
test -f /root/rhcsa_journal/lab-00b/task2/done.txt && echo "  ✅ lab-00b task2 done (idempotence proof + register/debug)"
```

> **STOP — if any `done.txt` check above failed, return and finish Lab 00a or 00b first. This lab verifies their combined output — without all four `done.txt` files, the verification has nothing to verify.**

---

## 🎯 Objective

Take off the operator's hat and put on the **auditor's hat**. Lab 00a installed `ansible-core` and built the journal tree. Lab 00b installed collections, wrote the config + inventory, and ran the first playbook with idempotence proof. Neither of those proves the control node is actually working **right now, today**, with confidence high enough to start Lab 01a on top of it. Lab 00c is the inspection step that **proves** the toolchain works — using a four-tool audit against a declared baseline of expected facts, followed by a simulated-reboot proof that the whole stack survives losing `/tmp` entirely.

The Lab 00 trilogy is the one prerequisite every later lab depends on. Lab 00c is what lets you start Lab 01a without ever wondering "but is the control node really set up?"

---

## 🧠 Concept: Trust But Verify — Especially On a Toolchain

`done.txt` from Lab 00a says `ansible-core` was installed last Tuesday. That is **not** the same as "`ansible-core` is installed right now." Examples of the gap:

| What the journal recorded | What can still be wrong |
|---|---|
| Lab 00a Task 1 `done.txt` shows install OK | A `dnf remove` (intended or by mistake) cleared the package |
| Lab 00b Task 1 `done.txt` shows collections installed | `~/.ansible/collections/` was wiped by an unrelated cleanup script |
| `config_file = /root/.ansible.cfg` recorded | A second `~/.ansible.cfg` got written at a different `$HOME` for a different user |
| `ping pong` recorded once | SELinux denial, firewall change, or sudo policy change can break it later |

The grader's reflex — and the senior engineer's reflex — is to **inspect the system directly** before relying on any prior journal entry. `rpm -qi ansible-core`, `ansible-galaxy collection list`, `ansible -m ping localhost`, `ansible --version | grep "config file"`. Four independent answers, all of which must align with a declared baseline before you proceed. That is the **trust-but-verify on a toolchain** pattern, and it is what this lab teaches.

The persistence proof in Task 2 is the structural counterpart. The whole reason Lab 00a wrote the journal under `/root/` and not `/tmp/` is so that wiping `/tmp` does not break verification. Lab 00c proves that by literally wiping `/tmp` and re-running the audit using only `/root/rhcsa_journal/`, `~/.ansible.cfg`, `~/inventory`, and the playbook at `/root/rhcsa_journal/lab-00b/playbooks/`. If anything fails, the journal was incomplete and the trilogy did not actually deliver what it claimed.

---

## 📚 Inspection Reference (everything for Tasks 1–2)

| Tool | Purpose | Why an auditor reaches for it |
|---|---|---|
| `rpm -q PKG` | Is PKG installed? Print NEVRA | "Is `ansible-core` here right now?" — first check |
| `rpm -qi PKG` | Install metadata (version, repo, install date, signer) | Cross-check against Lab 00a's recorded NEVRA |
| `ansible-galaxy collection list` | List installed collections | "Are `ansible.posix` and `community.general` reachable?" |
| `ansible-doc FQCN` | Read module docs from the local install | Module reachable = collection wiring intact |
| `ansible --version` | Engine + config file + Python interpreter | The four-line engine self-report |
| `ansible --version \| grep "config file"` | Which config file is in effect | The T00-C reflex |
| `ansible -m ping HOST` | Sanity ping — config + inventory + Python + sudo | The end-to-end "all the wires are connected" check |
| `ansible-playbook PATH` | Apply a playbook | Used for the idempotence proof on re-run |
| `diff -u EXPECTED ACTUAL` | Line-level comparison | "Does the current state match the declared baseline?" |
| `stat -c '%m'` | Mount point containing a path | The structural why behind persistence |
| `findmnt -T PATH` | Find the mount backing PATH | Independent confirmation of persistence |
| `test -f` / `test -d` | Existence checks | Scriptable verification |

---

## 🚦 Lab-Wide Setup — run BEFORE Task 1

```bash
sudo -i

# Build the verify workspace + the declared-baseline file
mkdir -p /root/rhcsa_journal/lab-00c/{task1,task2}
chmod 0750 /root/rhcsa_journal/lab-00c
chown -R root:root /root/rhcsa_journal/lab-00c
cd /root/rhcsa_journal/lab-00c

# The DECLARED BASELINE — the four facts the trilogy promised
cat > /root/rhcsa_journal/lab-00c/expected-baseline.txt <<'EOF'
# Lab 00 trilogy declared baseline — the four facts that must be true
#   on the control node before ANY Lab 01+ Task 4 can run.
#
# Format: key=expected-value-or-regex
PKG_NAME=ansible-core
PKG_REPO=appstream
COLLECTION_POSIX=ansible.posix
COLLECTION_GENERAL=community.general
CONFIG_FILE=/root/.ansible.cfg
INVENTORY_FILE=/root/inventory
PING_RESPONSE="ping": "pong"
JOURNAL_ROOT=/root/rhcsa_journal
PLAYBOOK_SMOKETEST=/root/rhcsa_journal/lab-00b/playbooks/smoketest.yml
SMOKETEST_DIR=/root/rhcsa_journal/_ansible_smoketest
SMOKETEST_MODE=750
SMOKETEST_OWNER=root:root
EOF

ls -la /root/rhcsa_journal/lab-00c
cat /root/rhcsa_journal/lab-00c/expected-baseline.txt
echo "exit was: $?"
```

> **STOP — paste the baseline file before Task 1. If anything in it does not match your expectation from Lab 00a/00b, fix Lab 00a/00b first — do not relax the baseline.**

---

## Task 1 — Four-tool audit + diff against declared baseline

**Practice directory this task:** `/root/rhcsa_journal` · the journal where all prior evidence lives. The audit workspace is at `/root/rhcsa_journal/lab-00c/task1/`, the baseline at `/root/rhcsa_journal/lab-00c/expected-baseline.txt`.

### 🔁 Warm-Up — commands woven into Task 1

```bash
cd /root/rhcsa_journal/lab-00c/task1
date -Is                                            2>&1 | tee start.txt
test -f /root/rhcsa_journal/lab-00c/expected-baseline.txt && echo "baseline OK"
wc -l /root/rhcsa_journal/lab-00c/expected-baseline.txt
stat -c '%n %F mode=%a' /root/rhcsa_journal/lab-00c/expected-baseline.txt \
                                                    2>&1 | tee -a start.txt
find /root/rhcsa_journal -maxdepth 2 -name 'done.txt' 2>/dev/null \
                                                    | tee -a start.txt
set -o pipefail
echo "Warm-up done by $(whoami) at $(date -Is)"
echo "exit was: $?"
```

> Carry from Lab 11c (the template): the `wc -l baseline.txt` + `test -f` pattern is the same — only the baseline content changes. Here the baseline asserts facts about the **toolchain**, not about deletion targets.

### Purpose

Run the **four-tool audit** of the Ansible control node — `rpm -qi ansible-core`, `ansible-galaxy collection list`, `ansible -m ping localhost`, `ansible --version | grep "config file"`. Each tool produces an independent answer to "is the control node working?" Compare the actual answers against the declared baseline with `diff -u`. The win condition is a clean diff: every declared fact matches the current state of the system.

### 🧵 WEAVE TRACE — warm-up commands re-used in this task body

| Warm-up command | Role inside Task 1 |
|---|---|
| `wc -l expected-baseline.txt` | Counts how many facts we must verify (drives the audit-loop iteration count) |
| `test -f` | Guards each artifact existence check inside the audit |
| `stat -c '%n %F mode=%a'` | Cross-check on metadata (mode 0644 on the baseline file is fine — it's not secret) |
| `find ... -name 'done.txt'` | Defensive: confirms all four prior `done.txt` files survive (T11-E-equivalent reflex) |
| `2>&1 \| tee` | Captures every check into `task1/audit.txt` — the journal proof |
| `$(date -Is)` | Stamps the audit timeline |

### Main command block

```bash
cd /root/rhcsa_journal/lab-00c/task1

echo "═══ Lab 00 Trilogy Audit — Four-Tool Toolchain Check ═══" \
  2>&1 | tee audit.txt

PASS=0
FAIL=0

# ── Tool 1: rpm -qi ansible-core (Lab 00a Task 1 fact) ───────────────
echo "── Tool 1: rpm -qi ansible-core ──" | tee -a audit.txt
PKG_REPO=$(rpm -qi ansible-core 2>/dev/null | awk -F': ' '/From repo/ {print $2; exit}')
if [ "$PKG_REPO" = "appstream" ]; then
  echo "  ✅ ansible-core installed from appstream (T00-A satisfied)" | tee -a audit.txt
  PASS=$(( PASS + 1 ))
else
  echo "  ❌ ansible-core repo is '$PKG_REPO' — expected appstream (T00-A trap!)" | tee -a audit.txt
  FAIL=$(( FAIL + 1 ))
fi
rpm -qi ansible-core | grep -E 'Name|Version|From repo' | tee -a audit.txt

# ── Tool 2: ansible-galaxy collection list (Lab 00b Task 1 fact) ─────
echo "── Tool 2: ansible-galaxy collection list ──" | tee -a audit.txt
for COL in ansible.posix community.general; do
  if ansible-galaxy collection list 2>/dev/null | grep -q "^$COL "; then
    echo "  ✅ collection $COL present" | tee -a audit.txt
    PASS=$(( PASS + 1 ))
  else
    echo "  ❌ collection $COL MISSING (T00-B trap!)" | tee -a audit.txt
    FAIL=$(( FAIL + 1 ))
  fi
done
ansible-galaxy collection list \
  | grep -E 'ansible.posix|community.general' | tee -a audit.txt

# ── Tool 3: ansible -m ping localhost (Lab 00b end-to-end fact) ──────
echo "── Tool 3: ansible -m ping localhost ──" | tee -a audit.txt
PING_OUT=$(ansible -m ping localhost 2>&1)
if echo "$PING_OUT" | grep -q '"ping": "pong"'; then
  echo "  ✅ ping returned pong (config + inventory + python + sudo all wired)" | tee -a audit.txt
  PASS=$(( PASS + 1 ))
else
  echo "  ❌ ping did not return pong — toolchain broken" | tee -a audit.txt
  FAIL=$(( FAIL + 1 ))
fi
echo "$PING_OUT" | head -n 6 | tee -a audit.txt

# ── Tool 4: ansible --version | grep "config file" (T00-C reflex) ────
echo "── Tool 4: ansible --version | grep 'config file' ──" | tee -a audit.txt
CFG=$(ansible --version 2>/dev/null | awk '/config file/ {print $4}')
if [ "$CFG" = "/root/.ansible.cfg" ]; then
  echo "  ✅ config file = $CFG (T00-C satisfied)" | tee -a audit.txt
  PASS=$(( PASS + 1 ))
else
  echo "  ❌ config file = '$CFG' — expected /root/.ansible.cfg (T00-C trap!)" | tee -a audit.txt
  FAIL=$(( FAIL + 1 ))
fi
ansible --version | head -n 4 | tee -a audit.txt

# ── Summary ──────────────────────────────────────────────────────────
echo "═══ Audit summary: $PASS pass, $FAIL fail ═══" | tee -a audit.txt

# ── Cross-check: diff the actual collected facts against the baseline ─
{
  echo "PKG_NAME=$(rpm -q ansible-core 2>/dev/null | awk -F'-' '{print $1"-"$2}')"
  echo "PKG_REPO=$PKG_REPO"
  echo "COLLECTION_POSIX=$(ansible-galaxy collection list 2>/dev/null | awk '/ansible.posix/ {print $1; exit}')"
  echo "COLLECTION_GENERAL=$(ansible-galaxy collection list 2>/dev/null | awk '/community.general/ {print $1; exit}')"
  echo "CONFIG_FILE=$CFG"
  echo "INVENTORY_FILE=$(awk '/^inventory/ {print $3}' /root/.ansible.cfg)"
  echo "PING_RESPONSE=$(ansible -m ping localhost 2>&1 | grep -oP '\"ping\": \"\w+\"')"
  echo "JOURNAL_ROOT=/root/rhcsa_journal"
  echo "PLAYBOOK_SMOKETEST=/root/rhcsa_journal/lab-00b/playbooks/smoketest.yml"
  echo "SMOKETEST_DIR=/root/rhcsa_journal/_ansible_smoketest"
  echo "SMOKETEST_MODE=$(stat -c '%a' /root/rhcsa_journal/_ansible_smoketest 2>/dev/null)"
  echo "SMOKETEST_OWNER=$(stat -c '%U:%G' /root/rhcsa_journal/_ansible_smoketest 2>/dev/null)"
} | sort > actual-facts.txt

# Diff: declared (filtered to lines we collect) vs actual
grep -v '^#' /root/rhcsa_journal/lab-00c/expected-baseline.txt | sort > expected-facts.txt
echo "── diff -u expected vs actual ──" | tee -a audit.txt
diff -u expected-facts.txt actual-facts.txt | tee -a audit.txt || true

echo "exit was: $?"
```

### Human-readable breakdown

1. **Tool 1 — `rpm -qi ansible-core`.** Extract the `From repo:` line. If it says `appstream`, T00-A is satisfied (the right package from the right repo). If it says `epel` or anything else, the trap was triggered in Lab 00a — return there and reinstall.
2. **Tool 2 — `ansible-galaxy collection list`.** Loop through `ansible.posix` and `community.general`. Each missing collection is a T00-B failure that must be fixed before any later lab will work.
3. **Tool 3 — `ansible -m ping localhost`.** The end-to-end "all wires connected" test. A `"ping": "pong"` line in the output is the four-stack proof: config loaded, inventory parsed, Python interpreter found, sudo working.
4. **Tool 4 — `ansible --version | grep "config file"`.** The T00-C reflex. Must show `/root/.ansible.cfg` — not `None`, not some other path, not a different user's config.
5. **PASS/FAIL counters.** A correct trilogy produces `5 pass, 0 fail` (one for each of: T00-A repo, posix, general, ping, config). Any FAIL means a prior task is broken and the trilogy is not actually done.
6. **`diff -u expected vs actual`.** Exhaustive cross-check: build a normalized "actual" facts file from the live system, sort it, and diff against the declared baseline (also sorted). A clean diff is the win condition. Any line in the diff exposes a fact the trilogy promised but did not deliver.

### Reading it left to right

`rpm -qi ansible-core | awk -F': ' '/From repo/ {print $2; exit}'`

- `rpm -qi ansible-core` — print full metadata
- `awk -F': '` — field separator is the literal colon-space (so `From repo` and its value split cleanly)
- `/From repo/` — match only the line containing "From repo"
- `{print $2; exit}` — print the second field (the repo name) and stop awk

`ansible-galaxy collection list | grep -q "^$COL "`

- `ansible-galaxy collection list` — list installed collections
- `grep -q` — quiet grep; exit status only (no output)
- `"^$COL "` — match a line **starting** with `$COL` followed by a space (column-anchored; avoids substring false positives)

`ansible -m ping localhost 2>&1 | grep -q '"ping": "pong"'`

- `ansible -m ping localhost` — ad-hoc invoke the `ping` module against localhost
- `2>&1` — merge stderr into stdout so grep sees both
- `grep -q '"ping": "pong"'` — match the JSON-like response line; quiet (exit status only)

`diff -u expected-facts.txt actual-facts.txt | tee -a audit.txt || true`

- `diff -u` — unified diff format
- `expected-facts.txt` vs `actual-facts.txt` — sorted file pair
- `|| true` — keep the script's exit at 0 even when `diff` reports differences (we want to see them, not abort)

### The story

The auditor's reflex is what separates "I think the control node is set up" from "I have proof the control node is set up right now." Four tools, four independent answers, one diff against a declared baseline. The pattern takes 90 seconds to run and produces a transcript that survives reboot — meaning future-you (or a teammate, or a grader) can open `audit.txt` weeks later and know exactly what state the control node was in.

The declared baseline at `/root/rhcsa_journal/lab-00c/expected-baseline.txt` is the **contract** the Lab 00 trilogy promised to deliver. Writing it as a separate file (instead of hardcoding the asserts into the audit script) means the contract is **portable** — you can copy the baseline file to another host, run the same audit script, and answer "is this host's control node set up correctly?" in 90 seconds. That is the reproducibility property RHCE-grade work has and ad-hoc work does not.

For the RHCSA mindset: every change you make should produce two artifacts — the change itself, and a verification commands file that proves the change. For the RHCE mindset: every playbook should have a baseline and an audit script. For Lab 00c specifically: the verification script you wrote here is the template every later "verify capstone" lab (11c, 12c, …) will reuse.

### Expected output

```text
═══ Lab 00 Trilogy Audit — Four-Tool Toolchain Check ═══
── Tool 1: rpm -qi ansible-core ──
  ✅ ansible-core installed from appstream (T00-A satisfied)
Name        : ansible-core
Version     : 2.14.17
From repo   : appstream
── Tool 2: ansible-galaxy collection list ──
  ✅ collection ansible.posix present
  ✅ collection community.general present
ansible.posix      1.5.x
community.general  7.x.x
── Tool 3: ansible -m ping localhost ──
  ✅ ping returned pong (config + inventory + python + sudo all wired)
localhost | SUCCESS => {
    "ansible_facts": { "discovered_interpreter_python": "/usr/bin/python3" },
    "changed": false,
    "ping": "pong"
}
── Tool 4: ansible --version | grep 'config file' ──
  ✅ config file = /root/.ansible.cfg (T00-C satisfied)
ansible [core 2.14.17]
  config file = /root/.ansible.cfg
  configured module search path = [...]
  ansible python module location = ...
═══ Audit summary: 5 pass, 0 fail ═══
── diff -u expected vs actual ──
(empty diff — clean exit)
exit was: 0
```

> **The win condition: `5 pass, 0 fail` and an empty diff.** Anything else means a prior trilogy task is incomplete or has drifted.

### Switches

| Token | Meaning |
|---|---|
| `rpm -qi PKG` | Full install metadata for PKG |
| `awk -F': '` | Field separator = colon-space |
| `grep -q PATTERN` | Quiet grep; exit status only |
| `grep "^X "` | Column-anchored match for `X` at start of line, space after |
| `for X in A B C; do ... done` | Loop over a fixed list of values |
| `if [ COND ]; then ... fi` | Conditional based on test exit status |
| `2>&1` | Merge stderr into stdout |
| `\|\| true` | Mask non-zero exit so the script continues |
| `sort > FILE` | Build a sorted snapshot suitable for `diff` |
| `diff -u A B` | Unified-format line-level diff |

### 🧠 Concept Card

|   | Concept | What it does |
|---|---|---|
|   | Four-tool independent audit | Four tools, four independent answers — beats single-command trust |
|   | Declared baseline | A file of expected facts; drives both the audit and the diff |
|   | `diff -u` against baseline | Exhaustive cross-check that catches drift between declared and actual |
|   | T00-A audit | "From repo: appstream" — proves the right package from the right repo |
|   | T00-B audit | Collection list grep — proves the right collections are reachable |
|   | T00-C audit | `config file = /root/.ansible.cfg` — proves the right config is in effect |
|   | End-to-end ping | `"ping": "pong"` — proves config + inventory + python + sudo all line up |
|   | PASS/FAIL counters | Simple integer summary; the bottom-line number |
| 🪤 | **Trap Risk T11-E-equivalent** | Trusting Lab 00a/00b's `done.txt` without re-running the four-tool audit. Things change; always verify. |

### 🔁 PERSISTENCE CHECK

| What was configured | Verification command | Why it matters |
|---|---|---|
| Audit transcript | `wc -l /root/rhcsa_journal/lab-00c/task1/audit.txt` | Must be > 0 — proves we actually ran the audit |
| Baseline survives | `ls /root/rhcsa_journal/lab-00c/expected-baseline.txt` | The audit is reproducible only if the baseline survives — stored in `/root/` |
| Actual-facts snapshot | `cat /root/rhcsa_journal/lab-00c/task1/actual-facts.txt` | The point-in-time state captured for cross-reference |
| Pass count | `grep "Audit summary" /root/rhcsa_journal/lab-00c/task1/audit.txt` | Must show `5 pass, 0 fail` |

> **Reboot reasoning:** The audit workspace and the baseline both live under `/root/rhcsa_journal/` — persistent. The artifacts being audited (RPM database at `/var/lib/rpm/`, collections at `/root/.ansible/collections/`, config at `/root/.ansible.cfg`, inventory at `/root/inventory`, playbook at `/root/rhcsa_journal/lab-00b/playbooks/`) are **also** all persistent. After a reboot you could re-run the entire audit script and get the same `5 pass, 0 fail` result. Task 2 actively tests this by wiping `/tmp` and re-running.

### Journal write — BEFORE cleanup

```bash
LAB=lab-00c
TASK=task1
JDIR="/root/rhcsa_journal/${LAB}/${TASK}"
mkdir -p "$JDIR"

# audit.txt, expected-facts.txt, actual-facts.txt already live at
# /root/rhcsa_journal/lab-00c/task1/ — they ARE the journal artifacts.

cat > "$JDIR/done.txt" <<EOF
LAB:    ${LAB}
TASK:   ${TASK}
DATE:   $(date -Is)
USER:   $(whoami)@$(hostname)
STATUS: COMPLETE
PASS_COUNT: $(grep -oP 'Audit summary: \K\d+' "$JDIR/audit.txt" 2>/dev/null | head -n 1)
FAIL_COUNT: $(grep -oP 'fail' -B1 "$JDIR/audit.txt" 2>/dev/null | grep -oP '\d+ fail' | head -n 1)
DIFF_LINES: $(grep -cE '^[-+]' "$JDIR/audit.txt" 2>/dev/null)
EOF

cat > "$JDIR/notes.txt" <<EOF
TOPIC:    Four-tool audit (rpm -qi + galaxy list + ping + version) + diff vs declared baseline
COMMANDS: rpm -qi, ansible-galaxy collection list, ansible -m ping, ansible --version,
          diff -u, awk, grep -q, for loop over collection list
TRAPS:    T11-E-equivalent rehearsed — re-verified the toolchain instead of trusting prior done.txt
MISSED:   (fill in if any ⚠️ flags)
NEXT:     task2 — simulated-reboot persistence proof (wipe /tmp, re-run the four-tool audit)
EOF

ls -la "$JDIR"
cat "$JDIR/done.txt"
echo "exit was: $?"
```

### 🧹 Cleanup

Nothing to clean in the persistent journal — the audit and its artifacts are evidence and must survive. The `actual-facts.txt` snapshot is intentionally a point-in-time record; Task 2 will produce a second one after the simulated reboot and the two are meant to be identical.

### Troubleshoot

| Symptom | Fix |
|---|---|
| `4 pass, 1 fail` on Tool 1 (repo) | `From repo` is not `appstream`. Remove the wrong package (`dnf remove ansible`) and reinstall (`dnf install ansible-core`) — return to Lab 00a Task 1. |
| `pass < 5` on Tool 2 | Re-run `ansible-galaxy collection install ansible.posix community.general` — return to Lab 00b Task 1. |
| Tool 3 fails (no pong) | `cat /root/inventory` — confirm `localhost ansible_connection=local`. Re-run Lab 00b Task 1's inventory write. |
| Tool 4 shows `config file = None` | You are not running as root or `$HOME` is not `/root`. `sudo -i` and retry. |
| `diff` shows unexpected lines | Read the `+` and `-` columns: `-` = expected (in baseline) but not actual; `+` = actual but not in baseline. Either fix the system or update the baseline if the deviation is intentional. |
| `From repo` shows `(none)` instead of `appstream` | The RPM was installed without repo metadata (e.g., direct rpm install). Reinstall via `dnf reinstall -y ansible-core` to restore the repo provenance. |

> **STOP — paste the "Audit summary" line and the diff output (or "empty diff" confirmation) before Task 2.**

---

## Task 2 — Simulated-reboot persistence proof — wipe `/tmp`, re-run from `/root/` alone

**Practice directory this task:** `/root/rhcsa_journal` · the contrast with `/tmp` is the entire lesson. The audit reproducibility comes from everything being in `/root/`. Task 2 proves it.

### 🔁 Warm-Up — commands woven into Task 2

```bash
cd /root/rhcsa_journal/lab-00c/task2
date -Is                                            2>&1 | tee start.txt
stat -c '%n mountpoint=%m fstype-follows' /tmp /root /root/rhcsa_journal \
                                                    2>&1 | tee -a start.txt
findmnt -T /root/rhcsa_journal -no SOURCE,FSTYPE    2>&1 | tee -a start.txt
findmnt -T /tmp -no SOURCE,FSTYPE                   2>&1 | tee -a start.txt
df -hT /tmp /root                                   2>&1 | tee -a start.txt
ls /tmp 2>&1 | head -n 10                           2>&1 | tee -a start.txt
set -o pipefail
echo "Warm-up done by $(whoami) at $(date -Is)"
echo "exit was: $?"
```

> Carry from Task 1: the same four-tool audit will run **after** the simulated reboot, against the same baseline. `findmnt` exposes the structural reason `/root` survives a reboot but `/tmp` does not — `tmpfs` for `/tmp`, real block device for `/`.

### Purpose

Simulate a reboot by deliberately wiping everything under `/tmp/`, then re-run the four-tool audit from Task 1 using **only** the artifacts under `/root/`. The win condition: same `5 pass, 0 fail` result, same empty diff against the baseline, and the first playbook from Lab 00b still applies cleanly with `changed=0`. If anything fails, the trilogy was leaking state into `/tmp` and the persistence claim is false.

### 🧵 WEAVE TRACE — warm-up commands re-used in this task body

| Warm-up command | Role inside Task 2 |
|---|---|
| `stat -c '%m'` | Confirms which paths are on tmpfs (will evaporate) vs root (will survive) |
| `findmnt -T PATH -no SOURCE,FSTYPE` | Independent structural confirmation per mount point |
| `df -hT /tmp /root` | Filesystem type cross-check (tmpfs vs xfs/ext4) |
| `ls /tmp` | Pre-reboot snapshot for comparison after the wipe |
| `2>&1 \| tee` | Captures every transition into `task2/timeline.txt` and `post-reboot-audit.txt` |
| `set -o pipefail` | Ensures the wipe + audit chain reports failures honestly |
| `$(date -Is)` | Stamps both the simulated reboot and the post-reboot audit |

### Main command block

```bash
cd /root/rhcsa_journal/lab-00c/task2

# ── Step 1: Pre-reboot state snapshot ────────────────────────────────
echo "═══ Pre-reboot state ═══" | tee timeline.txt
stat -c '  %n is on %m' /tmp /root /root/rhcsa_journal | tee -a timeline.txt
findmnt -T /tmp /root -no TARGET,SOURCE,FSTYPE | tee -a timeline.txt
ls /tmp 2>&1 | head -n 10 | tee -a timeline.txt

# ── Step 2: Make sure NOTHING this lab needs lives in /tmp ───────────
echo "═══ Pre-wipe sanity check — are any /tmp paths in the baseline? ═══" | tee -a timeline.txt
if grep -E '/tmp/' /root/rhcsa_journal/lab-00c/expected-baseline.txt; then
  echo "  ⚠️ baseline references /tmp — persistence claim is COMPROMISED" | tee -a timeline.txt
else
  echo "  ✅ baseline references /root only — safe to simulate reboot" | tee -a timeline.txt
fi

# ── Step 3: Simulate the reboot — wipe /tmp ──────────────────────────
echo "═══ SIMULATING REBOOT at $(date -Is) — wiping /tmp/ ═══" | tee -a timeline.txt
# Be careful: we wipe /tmp/* not /tmp itself (the directory stays so future labs can use it)
rm -rf /tmp/* /tmp/.[!.]* 2>/dev/null
ls /tmp 2>&1 | head -n 10 | tee -a timeline.txt
find /tmp -maxdepth 1 -type f 2>/dev/null | wc -l | tee -a timeline.txt

# ── Step 4: Verify the journal + config + inventory + playbook ALL survived ─
echo "═══ Post-reboot — checking /root/ artifacts ═══" | tee post-reboot-audit.txt
for f in /root/rhcsa_journal/lab-00a/task1/done.txt \
         /root/rhcsa_journal/lab-00a/task2/done.txt \
         /root/rhcsa_journal/lab-00b/task1/done.txt \
         /root/rhcsa_journal/lab-00b/task2/done.txt \
         /root/rhcsa_journal/lab-00b/playbooks/smoketest.yml \
         /root/rhcsa_journal/lab-00b/playbooks/register-demo.yml \
         /root/.ansible.cfg \
         /root/inventory \
         /root/rhcsa_journal/lab-00c/expected-baseline.txt \
         /root/rhcsa_journal/_ansible_smoketest; do
  if test -e "$f"; then
    echo "  ✅ survived: $f" | tee -a post-reboot-audit.txt
  else
    echo "  ❌ MISSING:  $f" | tee -a post-reboot-audit.txt
  fi
done

# ── Step 5: Re-run the four-tool audit from /root/ alone ─────────────
echo "═══ Re-running the four-tool audit post-reboot ═══" | tee -a post-reboot-audit.txt

PASS=0; FAIL=0
rpm -qi ansible-core | grep -q 'From repo *: appstream' \
  && { echo "  ✅ Tool 1: ansible-core repo=appstream" | tee -a post-reboot-audit.txt; PASS=$(( PASS + 1 )); } \
  || { echo "  ❌ Tool 1 FAIL" | tee -a post-reboot-audit.txt; FAIL=$(( FAIL + 1 )); }

ansible-galaxy collection list | grep -q '^ansible.posix' \
  && { echo "  ✅ Tool 2a: ansible.posix" | tee -a post-reboot-audit.txt; PASS=$(( PASS + 1 )); } \
  || { echo "  ❌ Tool 2a FAIL" | tee -a post-reboot-audit.txt; FAIL=$(( FAIL + 1 )); }

ansible-galaxy collection list | grep -q '^community.general' \
  && { echo "  ✅ Tool 2b: community.general" | tee -a post-reboot-audit.txt; PASS=$(( PASS + 1 )); } \
  || { echo "  ❌ Tool 2b FAIL" | tee -a post-reboot-audit.txt; FAIL=$(( FAIL + 1 )); }

ansible -m ping localhost 2>&1 | grep -q '"ping": "pong"' \
  && { echo "  ✅ Tool 3: ping=pong" | tee -a post-reboot-audit.txt; PASS=$(( PASS + 1 )); } \
  || { echo "  ❌ Tool 3 FAIL" | tee -a post-reboot-audit.txt; FAIL=$(( FAIL + 1 )); }

ansible --version | grep -q 'config file = /root/.ansible.cfg' \
  && { echo "  ✅ Tool 4: config=/root/.ansible.cfg" | tee -a post-reboot-audit.txt; PASS=$(( PASS + 1 )); } \
  || { echo "  ❌ Tool 4 FAIL" | tee -a post-reboot-audit.txt; FAIL=$(( FAIL + 1 )); }

echo "═══ Post-reboot audit: $PASS pass, $FAIL fail ═══" | tee -a post-reboot-audit.txt

# ── Step 6: Re-apply the smoketest playbook — must report changed=0 ──
echo "═══ Re-applying smoketest.yml post-reboot — must be changed=0 ═══" \
  | tee -a post-reboot-audit.txt
ansible-playbook /root/rhcsa_journal/lab-00b/playbooks/smoketest.yml \
  2>&1 | tee post-reboot-ansible.txt | grep -E "PLAY RECAP|changed=" \
                                     | tee -a post-reboot-audit.txt
echo "exit was: $?"
```

### Human-readable breakdown

1. **Step 1** snapshots which paths are on which mount point. `/tmp` shows mount `/tmp` with fstype `tmpfs` (or, on layouts where `/tmp` is not separately mounted, shows `/` but is still cleared by `systemd-tmpfiles-clean.timer`); `/root` shows mount `/` with fstype `xfs`/`ext4`. The `findmnt` output is the **structural** evidence for "why does this work."
2. **Step 2** is the pre-wipe sanity check: grep the baseline for any `/tmp/` path. If the baseline mentions `/tmp`, the persistence claim is compromised — Lab 00b would have leaked state into ephemeral storage. The grep should return no matches.
3. **Step 3** is the simulated reboot. `rm -rf /tmp/* /tmp/.[!.]*` removes both visible and hidden contents but leaves `/tmp` itself (so future labs can still use it). The `find /tmp -maxdepth 1 -type f | wc -l` cross-check should print `0`.
4. **Step 4** walks through every file the trilogy claims survives reboot — the four `done.txt` files, both playbooks, `~/.ansible.cfg`, `~/inventory`, the baseline, and the smoketest directory. Every one must print ✅.
5. **Step 5** re-runs the four-tool audit. Same five checks as Task 1, same expected `5 pass, 0 fail` result. Because every input to the audit is under `/root/` (or in the RPM/collections databases on the root partition), the result is unchanged.
6. **Step 6** re-applies `smoketest.yml`. Because the smoketest directory at `/root/rhcsa_journal/_ansible_smoketest` survived (it's on `/root`, not `/tmp`), and the playbook is unchanged, the PLAY RECAP must show `changed=0`. That is the deepest form of idempotence — idempotence across simulated reboot.

### Reading it left to right

`rm -rf /tmp/* /tmp/.[!.]*`

- `rm -rf` — recursive force removal
- `/tmp/*` — every non-hidden entry under `/tmp`
- `/tmp/.[!.]*` — every hidden entry whose first character after `.` is **not** another `.` (i.e., excludes `.` and `..`). The `[!.]` is a glob negation — it prevents the trap of trying to recurse into the parent.

`for f in PATH1 PATH2 ... ; do test -e "$f" && ... ; done`

- `for f in LIST` — loop over the explicit path list
- `test -e "$f"` — does PATH exist (file, dir, symlink, anything)
- `&& {...} || {...}` — branch on the test exit status; quote `$f` to survive paths with spaces

`ansible-playbook PATH | tee FILE | grep -E "PLAY RECAP|changed="`

- `ansible-playbook PATH` — apply the playbook
- `| tee FILE` — capture full output AND pass it through
- `| grep -E` — print only the audit-critical lines

### The story

This task is the **only** thing that distinguishes a real persistence claim from a hope. Running `audit.txt` once on the same host that just finished Lab 00a/00b proves very little — anything could have been cached in shell memory or in a still-open SSH session. Wiping `/tmp` and re-running from `/root/` proves the audit is reproducible by **anyone** with access to the journal, in a fresh shell, after a reboot, weeks later. That is the contract of a verifiable trilogy.

For the RHCSA mindset: every change you make should still be true after a reboot — and you should have evidence of it. For the RHCE mindset: every playbook should be re-runnable from a cold-start shell using only files in persistent storage. For Lab 00c specifically: the simulated-reboot pattern you ran here is the template every later "verify capstone" lab (11c, 12c, …) will reuse — with `/tmp` wiped, the journal under `/root/` is the only thing left to work from. If that is enough, the system is genuinely verifiable. If it is not, the previous labs have a leak that must be fixed.

### Expected output

```text
═══ Pre-reboot state ═══
  /tmp is on /tmp
  /root is on /
  /root/rhcsa_journal is on /
TARGET SOURCE                FSTYPE
/tmp   tmpfs                 tmpfs
/      /dev/mapper/rhel-root xfs
(/tmp contents listing — some sockets and X11 dirs)
═══ Pre-wipe sanity check — are any /tmp paths in the baseline? ═══
  ✅ baseline references /root only — safe to simulate reboot
═══ SIMULATING REBOOT at 2026-05-28T20:01:14-04:00 — wiping /tmp/ ═══
(empty ls output)
0
═══ Post-reboot — checking /root/ artifacts ═══
  ✅ survived: /root/rhcsa_journal/lab-00a/task1/done.txt
  ✅ survived: /root/rhcsa_journal/lab-00a/task2/done.txt
  ✅ survived: /root/rhcsa_journal/lab-00b/task1/done.txt
  ✅ survived: /root/rhcsa_journal/lab-00b/task2/done.txt
  ✅ survived: /root/rhcsa_journal/lab-00b/playbooks/smoketest.yml
  ✅ survived: /root/rhcsa_journal/lab-00b/playbooks/register-demo.yml
  ✅ survived: /root/.ansible.cfg
  ✅ survived: /root/inventory
  ✅ survived: /root/rhcsa_journal/lab-00c/expected-baseline.txt
  ✅ survived: /root/rhcsa_journal/_ansible_smoketest
═══ Re-running the four-tool audit post-reboot ═══
  ✅ Tool 1: ansible-core repo=appstream
  ✅ Tool 2a: ansible.posix
  ✅ Tool 2b: community.general
  ✅ Tool 3: ping=pong
  ✅ Tool 4: config=/root/.ansible.cfg
═══ Post-reboot audit: 5 pass, 0 fail ═══
═══ Re-applying smoketest.yml post-reboot — must be changed=0 ═══
PLAY RECAP ********************************************************************
localhost                  : ok=2    changed=0    unreachable=0    failed=0
exit was: 0
```

> **The trilogy win condition: `5 pass, 0 fail` after the simulated reboot AND `changed=0` from the smoketest re-apply.** Lab 00 is now genuinely verified — every later lab can `cd` straight into Task 4 without worrying about toolchain setup.

### Switches

| Token | Meaning |
|---|---|
| `stat -c '%m'` | Mount point that contains the file |
| `findmnt -T PATH -no SOURCE,FSTYPE` | Find mount backing PATH; no-header, only source + fstype |
| `df -hT` | Human-readable disk usage with filesystem type |
| `rm -rf /tmp/* /tmp/.[!.]*` | Wipe contents of `/tmp` (visible + hidden, but not `.` or `..`) |
| `for f in LIST` | Iterate over an explicit list |
| `test -e PATH` | Exists (file/dir/symlink) |
| `&& { ... } \|\| { ... }` | Branch on the previous command's exit status |
| `grep -q PATTERN` | Quiet grep; exit status only |
| `grep -E "A\|B"` | Extended regex; match A or B |

### 🧠 Concept Card

|   | Concept | What it does |
|---|---|---|
|   | `/tmp` vs `/root/` storage | `/tmp` is ephemeral (tmpfs or cleared on reboot); `/root/` is on the persistent root partition |
|   | Journal as cold-storage audit | Every verification artifact must live in `/root/rhcsa_journal/` to survive reboot |
|   | Reproducible audit | Re-running the audit after a wipe is the test of real persistence |
|   | Idempotence across reboot | A correctly-written `state: directory` play still reports `changed=0` after `/tmp` is wiped |
|   | Mount-point awareness | `stat -c '%m'` exposes the structural reason for persistence |
|   | `rm -rf /tmp/* /tmp/.[!.]*` | The safe pattern for wiping contents of `/tmp` without recursing into `..` |
|   | Pre-wipe baseline grep | Sanity-check the persistence claim BEFORE wiping (no `/tmp` paths allowed in baseline) |
| 🪤 | **Trap Risk T11-E-equivalent** | Skipping the reboot test on toolchain setup. The cost is discovering after the next reboot that a playbook leaked state into `/tmp` and the control node no longer works. |

### 🔁 PERSISTENCE CHECK (this lab IS the persistence check)

| What was configured | Verification command | Why it matters |
|---|---|---|
| Post-reboot transcript | `wc -l /root/rhcsa_journal/lab-00c/task2/post-reboot-audit.txt` | The proof artifact of Task 2 itself |
| Timeline preserved | `head -n 10 /root/rhcsa_journal/lab-00c/task2/timeline.txt` | Pre-reboot evidence + the wipe moment, journaled |
| Post-reboot pass count | `grep "Post-reboot audit" /root/rhcsa_journal/lab-00c/task2/post-reboot-audit.txt` | Must show `5 pass, 0 fail` |
| Idempotence across reboot | `grep changed= /root/rhcsa_journal/lab-00c/task2/post-reboot-ansible.txt` | `changed=0` is the proof — same as Lab 00b Task 2 but now after `/tmp` was wiped |
| Trilogy complete | `find /root/rhcsa_journal/lab-00{a,b,c} -name done.txt \| wc -l` | Should be `6` — three sub-labs × two tasks each |

### Journal write — BEFORE cleanup

```bash
LAB=lab-00c
TASK=task2
JDIR="/root/rhcsa_journal/${LAB}/${TASK}"
mkdir -p "$JDIR"

cat > "$JDIR/done.txt" <<EOF
LAB:    ${LAB}
TASK:   ${TASK}
DATE:   $(date -Is)
USER:   $(whoami)@$(hostname)
STATUS: COMPLETE
POST_REBOOT_PASS:    $(grep -oP 'Post-reboot audit: \K\d+' "$JDIR/post-reboot-audit.txt" 2>/dev/null | head -n 1)
POST_REBOOT_CHANGED: $(grep -oP 'changed=\K\d+' "$JDIR/post-reboot-ansible.txt" 2>/dev/null | tail -n 1)
TRILOGY_DONE_FILES:  $(find /root/rhcsa_journal/lab-00{a,b,c} -name done.txt 2>/dev/null | wc -l)
EOF

cat > "$JDIR/notes.txt" <<EOF
TOPIC:    Simulated-reboot persistence proof — wipe /tmp, re-run four-tool audit from /root/ alone
COMMANDS: rm -rf /tmp/* /tmp/.[!.]*, for-loop test -e, ansible -m ping, ansible-playbook,
          stat -c '%m', findmnt -T, grep -q
TRAPS:    T11-E-equivalent rehearsed — proved persistence instead of trusting it
MISSED:   (fill in if any ⚠️ flags)
NEXT:     Lab 01a (stdout / > / >>) — the next foundational lab, with a verified control node behind it
EOF

ls -la "$JDIR"
echo "── Trilogy state ──"
find /root/rhcsa_journal/lab-00{a,b,c} -name done.txt | sort
cat "$JDIR/done.txt"
echo "exit was: $?"
```

### 🧹 Cleanup

```bash
# The audit + timeline + post-reboot evidence is intentional persistent.
# Nothing in /tmp survives the simulated reboot anyway — already wiped.
# The control node remains fully working — that is the whole point.
echo "Trilogy complete — nothing to clean."
echo "exit was: $?"
```

### Troubleshoot

| Symptom | Fix |
|---|---|
| `/tmp` mount point shown as `/` | `/tmp` is not separately mounted on this layout — still ephemeral on reboot if `tmp.mount` / `systemd-tmpfiles-clean.timer` is enabled. Confirm: `systemctl is-enabled systemd-tmpfiles-clean.timer`. |
| ❌ MISSING on any journal file | A prior lab did not run its journal write step — return and finish |
| Post-reboot audit shows `< 5 pass` | A `/tmp`-side dependency was masked in Tasks 1–2. Re-do Lab 00a/00b and stop using `/tmp` for any persistent artifact. |
| Ansible re-run shows `changed=1` after wipe | The smoketest directory itself was on `/tmp` — that is a persistence leak. The directory should be at `/root/rhcsa_journal/_ansible_smoketest`. |
| `grep PLAY RECAP` returns nothing | `ansible-playbook` failed to run — Tool 1/2/3/4 will tell you which prerequisite broke |
| `rm -rf /tmp/.[!.]*` warns about `.X11-unix` busy | The X11 socket directory has an active session attached — expected on a desktop install, harmless |

> **STOP — paste the `Post-reboot audit: 5 pass, 0 fail` line, the `changed=0` PLAY RECAP, and the trilogy `done.txt` list before completing the Lab 00 trilogy.**

---

## Lab 00c Checklist (2 tasks)

- [ ] Task 1 — Four-tool audit (`rpm -qi` + `ansible-galaxy collection list` + `ansible -m ping` + `ansible --version | grep "config file"`) + `diff -u` against the declared baseline = `5 pass, 0 fail` + empty diff
- [ ] Task 2 — Simulated-reboot persistence proof: wipe `/tmp`, re-verify all `/root/` artifacts survive, re-run the four-tool audit, re-apply `smoketest.yml` with `changed=0`

---

## 🏁 Lab 00 Trilogy — completion check

After all three sub-labs are done, this command should show **six** `done.txt` files:

```bash
find /root/rhcsa_journal/lab-00{a,b,c} -name done.txt | sort
```

Expected output:

```text
/root/rhcsa_journal/lab-00a/task1/done.txt
/root/rhcsa_journal/lab-00a/task2/done.txt
/root/rhcsa_journal/lab-00b/task1/done.txt
/root/rhcsa_journal/lab-00b/task2/done.txt
/root/rhcsa_journal/lab-00c/task1/done.txt
/root/rhcsa_journal/lab-00c/task2/done.txt
```

If any are missing, that sub-lab is incomplete. Do not start Lab 01a until the trilogy is closed.

---

## 🔗 Related Labs in the Trilogy

| Lab | Connection |
|---|---|
| **Lab 00a** — Ansible Control Node — RHCSA Prerequisites | The RHCSA half being audited (`ansible-core` install + journal tree) |
| **Lab 00b** — Ansible Control Node — Collections, Config & First Playbook | The Ansible half being audited (collections + `~/.ansible.cfg` + `~/inventory` + first playbook) |
| Lab 01a — `stdout`, `>`, `>>` (Output Redirection RHCSA) | The next foundational lab — runs ON TOP OF a verified control node from this trilogy |
| Lab 11c — Verifying File Removal | The pattern this lab generalizes from — both use a declared baseline + diff + simulated-reboot proof |

---

## 👤 Author

**Kelvin R. Tobias**
[kelvinintech.com](https://kelvinintech.com) · [GitHub](https://github.com/kelvintechnical) · [LinkedIn](https://www.linkedin.com/in/kelvin-r-tobias-211949219)
