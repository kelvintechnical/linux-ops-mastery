# Lab 08c: Verifying Copies — attribute preservation + persistence proof

- **Series:** linux-ops-mastery — File Operations & Shell Fundamentals
- **Trilogy:** `08a` (RHCSA) → `08b` (Ansible) → **`08c` (Verify — you are here)**
- **Career arcs covered:** RHCSA EX200 (verification reflex on every copy task), RHCE EX294 (auditor seat — prove a playbook worked without trusting the playbook output), SRE (post-change verification + reboot-survives-config drill), DevOps (artifact integrity audit after promotion)
- **Prerequisite:** Lab 08a and Lab 08b completed — this lab verifies their combined effect
- **Time Estimate:** 20–30 minutes
- **Tasks:** 2 (Task 1 = three-tool audit, Task 2 = simulated-reboot persistence proof)
- **Practice Directory (rotation #08):** `/etc/skel`
- **Sandbox:** `/tmp/copy-lab/`
- **Traps rehearsed this lab:** **T11-E equivalent for copies** (running `cp` or `ansible.builtin.copy` and only checking with `ls` — missing the SELinux-context and ownership checks that the next service start would have caught) · **T41** (skipping the reboot-persistence test on a config-deploy playbook — discovering the missing change only after the next reboot)

> **This lab's practice directory is: `/etc/skel`** — the same source from 08a and 08b. We re-read it (read-only) to validate that the copies under `/tmp/copy-lab/new-home/` match it byte-for-byte and attribute-for-attribute.

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
echo "⚠️  TRAP REMINDERS THIS LAB: T11-E-for-copies T41"
echo "📁  PRACTICE DIR: /etc/skel"
echo ""
echo "🧾 Journal check — Lab 08a and 08b must already be done:"
test -f /root/rhcsa_journal/lab-08a/task2/done.txt && echo "  ✅ lab-08a task2 done"
test -f /root/rhcsa_journal/lab-08b/task2/done.txt && echo "  ✅ lab-08b task2 done"
test -f /root/rhcsa_journal/lab-08b/playbooks/task1.yml && echo "  ✅ lab-08b playbook present (needed for Task 2 reboot replay)"
```

> **STOP — if any check above failed, return and finish Lab 08a or 08b first. Task 2 depends on the playbook artifacts they produce.**

---

## 🎯 Objective

Put on the **auditor's hat**. Lab 08a copied files by hand. Lab 08b copied them via Ansible and reported `changed=0` on re-run. Neither proves the destination actually matches the source right now, with the right mode, the right ownership, the right SELinux context, and that the playbook is reproducible after a reboot. Lab 08c is the inspection step that **proves all four** using only RHCSA-grade inspection commands — `diff -r`, `stat`, `ls -lZ` — and a simulated reboot.

---

## 🧠 Concept: `diff -r` is the content audit, `stat` is the metadata audit, `ls -lZ` is the context audit

A copy operation has three independent dimensions. Each needs its own audit tool:

```
   ┌──────────────────┬──────────────────────────────────────────────┐
   │  diff -r SRC DST │  CONTENT audit — bytes match recursively     │
   │                  │  (catches truncation, corruption, missing    │
   │                  │   files in subdirs)                          │
   ├──────────────────┼──────────────────────────────────────────────┤
   │  stat -c '%a %U %G' │ METADATA audit — mode + owner + group     │
   │                  │  (catches DAC drift the next service start   │
   │                  │   would have caught the hard way)            │
   ├──────────────────┼──────────────────────────────────────────────┤
   │  ls -lZ          │  SELinux CONTEXT audit — label match         │
   │                  │  (catches the silent 403/permission-denied   │
   │                  │   that DAC alone cannot)                     │
   └──────────────────┴──────────────────────────────────────────────┘
```

The grader's reflex — and the senior engineer's reflex — is to run all three after **every** copy operation and compare against a known-expected baseline. `ansible.builtin.copy` reporting `changed=0` is **not** the same as "the destination actually matches the source in all three dimensions." A different process may have re-written the file. SELinux may have been disabled at the time of the copy. The destination's mode may have been clobbered by an aggressive `chmod -R` in a different play.

> **The grader's failure mode (T11-E for copies):** trusting `ls` alone. A copy that landed at the right path but with the wrong owner, the wrong mode, or the wrong SELinux context will pass `ls` and fail the next service start. The three-tool audit catches all three failure modes before the service touches the file.

> **The graybeard's failure mode (T41):** never rebooting between "I deployed it" and "I called it done." A `cp` or `ansible.builtin.copy` that wrote the right thing to `/tmp/` is gone after reboot. A config that depends on a file under `/tmp/` is similarly gone. The reboot-persistence drill catches "I forgot to put it under `/root/` or `/etc/`" before the next maintenance window does.

---

## 📚 Verification Reference (everything for Tasks 1–2)

| Tool | Purpose | Why an auditor reaches for it |
|---|---|---|
| `diff FILE1 FILE2` | Line-level diff | Quick single-file content check |
| `cmp FILE1 FILE2` | Byte-level binary compare | Binary-safe (jpeg, tar, etc.) |
| `md5sum FILE` / `sha256sum FILE` | Cryptographic checksum | Network-safe — share the hash, not the file |
| `diff -r DIR1 DIR2` | Recursive directory diff | The big one for `cp -a` / tree copies |
| `stat -c '%a %U %G'` | Mode + owner + group in one shot | Scriptable DAC snapshot |
| `stat -c '%y'` | mtime (human-readable) | Validates `preserve: true` / `cp -a` |
| `ls -lZ` | DAC + SELinux in one row | Auditor's primary view |
| `matchpathcon PATH` | Default SELinux context for PATH | Catches drift from policy |
| `getfacl PATH` | POSIX ACLs | Catches non-standard permissions |
| `find PATH -type f` | Exhaustive file listing | Catches files where you didn't expect them |
| `test -f` / `test -d` | Boolean existence | The scriptable form of "is it there?" |

---

## 🚦 Lab-Wide Setup — run BEFORE Task 1

```bash
sudo -i

# Verification sandbox (separate from /tmp/copy-lab/ so we can wipe one without the other)
mkdir -p /tmp/copy-verify-lab

# Re-create the source-config.conf and dest layout that Lab 08b ended with.
# (If Lab 08b's cleanup ran, /tmp/copy-lab is gone — that's the realistic Task 2 starting state.)
mkdir -p /tmp/copy-lab/new-home/etc /tmp/copy-lab/new-home/skel
if ! test -f /tmp/copy-lab/source-config.conf; then
  echo "updated-config-v2" > /tmp/copy-lab/source-config.conf
  chmod 0640                /tmp/copy-lab/source-config.conf
fi

# Declare the expected baseline (what the playbook PROMISED to produce)
cat > /tmp/copy-verify-lab/expected-baseline.txt <<'EOF'
# path | expected mode | expected owner | expected group | content source
/tmp/copy-lab/new-home/etc/config.conf|0640|root|root|/tmp/copy-lab/source-config.conf
/tmp/copy-lab/new-home/skel/.bashrc|0644|root|root|/etc/skel/.bashrc
/tmp/copy-lab/new-home/skel/.bash_profile|0644|root|root|/etc/skel/.bash_profile
/tmp/copy-lab/new-home/skel/.bash_logout|0644|root|root|/etc/skel/.bash_logout
EOF

# Re-run the Lab 08b playbook to make sure the destination is at the expected v2 state
ansible-playbook /root/rhcsa_journal/lab-08b/playbooks/task1.yml >/dev/null 2>&1 || true

ls -la /tmp/copy-verify-lab
ls -la /tmp/copy-lab/new-home/etc/ /tmp/copy-lab/new-home/skel/ 2>/dev/null
cat /tmp/copy-verify-lab/expected-baseline.txt
echo "exit was: $?"
```

> **STOP — paste output before Task 1. Confirm both the baseline file AND the destination tree are present.**

---

## Task 1 — Three-tool audit: `diff -r` + `stat` + `ls -lZ` against the declared baseline

**Practice directory this task:** `/etc/skel` (re-read for content baseline), `/tmp/copy-lab/new-home/` (audit target) · The auditor never trusts the operator. Every claim Lab 08a/b made about content, mode, owner, group, and SELinux context gets independently verified.

### 🔁 Warm-Up — commands woven into Task 1

```bash
ls -la /tmp/copy-verify-lab                         2>&1 | tee /tmp/copy-verify-lab/warmup.txt
wc -l /tmp/copy-verify-lab/expected-baseline.txt
test -f /tmp/copy-verify-lab/expected-baseline.txt && echo "baseline OK"
stat -c '%n %F' /tmp/copy-verify-lab/expected-baseline.txt
find /tmp/copy-lab/new-home -maxdepth 3 -type f      2>/dev/null | wc -l
set -o pipefail
echo "Warm-up done by $(whoami) at $(date -Is)"
echo "exit was: $?"
```

> Carry from Lab 08b: the `register` + `debug` output told us *Ansible believed* the dest matches. Now we **independently** verify that with `diff -r`, `stat`, and `ls -lZ` — no `ansible` CLI involvement.

### Purpose

Walk the declared baseline (`expected-baseline.txt`) and prove with three independent inspection commands that each row is satisfied:

1. **`diff` / `diff -r`** — content matches the declared content source byte-for-byte
2. **`stat -c '%a %U %G'`** — mode, owner, group match the declared values
3. **`ls -lZ`** — SELinux context matches between the source and the destination (or matches the destination's policy default, depending on whether `cp -a` / `preserve: true` was used)

Maintain `PASS` and `FAIL` counters per dimension. Anything other than `0 fail` across all three dimensions means Lab 08a or 08b is silently broken — investigate before moving on.

### 🧵 WEAVE TRACE — warm-up commands re-used in this task body

| Warm-up command | Role inside Task 1 |
|---|---|
| `wc -l expected-baseline.txt` | Counts how many rows we expect — drives the loop iteration count |
| `test -f` / `test -d` | The exit-status form of "is this path here?" — used inside the audit loop |
| `stat -c '%n %F'` | Confirms whether a path is a file, directory, or symlink (or missing) |
| `find /tmp/copy-lab/new-home` | Catches files that exist in the destination but are NOT in the baseline (extras) |
| `2>&1 \| tee` | Captures every check into `task1/audit.txt` — the journal proof |
| `$(date -Is)` | Stamps the journal `notes.txt` |

### Main command block

```bash
mkdir -p /tmp/copy-verify-lab/task1

echo "═══ Audit Pass — Lab 08b destinations must MATCH the declared baseline ═══" \
  | tee /tmp/copy-verify-lab/task1/audit.txt

CONTENT_PASS=0; CONTENT_FAIL=0
META_PASS=0;    META_FAIL=0
CTX_PASS=0;     CTX_FAIL=0

while IFS='|' read -r path mode owner group src; do
  # Skip comment rows
  case "$path" in \#*|"") continue;; esac

  echo "─── checking: $path ───" | tee -a /tmp/copy-verify-lab/task1/audit.txt

  # Dimension 1: CONTENT — diff against declared source
  if diff "$src" "$path" >/dev/null 2>&1; then
    echo "  ✅ content match (vs $src)" | tee -a /tmp/copy-verify-lab/task1/audit.txt
    CONTENT_PASS=$(( CONTENT_PASS + 1 ))
  else
    echo "  ❌ content DIFFERS from $src" | tee -a /tmp/copy-verify-lab/task1/audit.txt
    CONTENT_FAIL=$(( CONTENT_FAIL + 1 ))
  fi

  # Dimension 2: METADATA — stat -c '%a %U %G'
  ACTUAL=$(stat -c '%a %U %G' "$path" 2>/dev/null)
  EXPECTED="${mode#0} $owner $group"   # stat prints mode without the leading 0
  ALT_EXPECTED="$mode $owner $group"   # in case stat returns the leading 0
  if [ "$ACTUAL" = "$EXPECTED" ] || [ "$ACTUAL" = "$ALT_EXPECTED" ]; then
    echo "  ✅ metadata match (mode=$mode owner=$owner group=$group)" \
      | tee -a /tmp/copy-verify-lab/task1/audit.txt
    META_PASS=$(( META_PASS + 1 ))
  else
    echo "  ❌ metadata MISMATCH expected='$EXPECTED' got='$ACTUAL'" \
      | tee -a /tmp/copy-verify-lab/task1/audit.txt
    META_FAIL=$(( META_FAIL + 1 ))
  fi

  # Dimension 3: SELINUX CONTEXT — ls -lZ on src + dst, compare
  SRC_CTX=$(stat -c '%C' "$src" 2>/dev/null)
  DST_CTX=$(stat -c '%C' "$path" 2>/dev/null)
  echo "    src ctx: $SRC_CTX" | tee -a /tmp/copy-verify-lab/task1/audit.txt
  echo "    dst ctx: $DST_CTX" | tee -a /tmp/copy-verify-lab/task1/audit.txt
  if [ -n "$DST_CTX" ] && [ "$DST_CTX" != "?" ]; then
    echo "  ✅ SELinux context present on dst" | tee -a /tmp/copy-verify-lab/task1/audit.txt
    CTX_PASS=$(( CTX_PASS + 1 ))
  else
    echo "  ❌ SELinux context MISSING on dst" | tee -a /tmp/copy-verify-lab/task1/audit.txt
    CTX_FAIL=$(( CTX_FAIL + 1 ))
  fi
done < /tmp/copy-verify-lab/expected-baseline.txt

echo "═══ Audit summary ═══" | tee -a /tmp/copy-verify-lab/task1/audit.txt
echo "  CONTENT : $CONTENT_PASS pass, $CONTENT_FAIL fail" | tee -a /tmp/copy-verify-lab/task1/audit.txt
echo "  METADATA: $META_PASS pass, $META_FAIL fail"       | tee -a /tmp/copy-verify-lab/task1/audit.txt
echo "  CONTEXT : $CTX_PASS pass, $CTX_FAIL fail"          | tee -a /tmp/copy-verify-lab/task1/audit.txt

# Recursive-tree audit — catches anything missing or extra under skel/
echo "═══ diff -r /etc/skel /tmp/copy-lab/new-home/skel ═══" \
  | tee -a /tmp/copy-verify-lab/task1/audit.txt
diff -r /etc/skel /tmp/copy-lab/new-home/skel \
  | tee -a /tmp/copy-verify-lab/task1/audit.txt \
  | head -n 20
TREE_EXIT=${PIPESTATUS[0]}
if [ "$TREE_EXIT" -eq 0 ]; then
  echo "  ✅ TREE_CLEAN (diff -r exit 0)" | tee -a /tmp/copy-verify-lab/task1/audit.txt
else
  echo "  ❌ TREE_DIFFER (diff -r exit $TREE_EXIT)" | tee -a /tmp/copy-verify-lab/task1/audit.txt
fi

echo "exit was: $?"
```

### Human-readable breakdown

1. Read `expected-baseline.txt` row by row — each row declares one path's expected mode, owner, group, and content source.
2. For each path, run **three independent inspection commands**:
   - **`diff`** against the declared content source — if they differ, content fails.
   - **`stat -c '%a %U %G'`** — read the actual mode/owner/group and compare to the declared values. The `%a` format omits the leading `0`, so we compare against both `0640` and `640` to handle either form.
   - **`stat -c '%C'`** — read the SELinux context of both source and destination; record both. We do not assert exact equality (`cp -a` would preserve it but `cp -R` would not — both can be valid depending on intent) but we DO assert the destination has *some* context (not `?`, which means SELinux is off or the inode is unlabeled).
3. Maintain three pairs of `PASS`/`FAIL` counters — one per dimension.
4. After the per-row loop, run a single `diff -r /etc/skel /tmp/copy-lab/new-home/skel` for the exhaustive recursive cross-check. This catches a file that exists in the destination but NOT in the baseline (an "extra" file), or a file that exists in the source but was somehow skipped.

### Reading it left to right

- `while IFS='|' read -r path mode owner group src; do ...; done < FILE` — read pipe-separated rows from FILE. `IFS='|'` splits each line on `|` into the four named fields.
- `case "$path" in \#*|"") continue;; esac` — skip lines that start with `#` (comments) or are empty.
- `diff "$src" "$path" >/dev/null 2>&1` — quiet diff; the exit code is the verdict (0 = identical, 1 = differ).
- `stat -c '%a %U %G' "$path"` — custom format: `%a` numeric mode (no leading 0), `%U` owner name, `%G` group name.
- `${mode#0}` — parameter expansion: strip a leading `0` from `$mode`. The declared `0640` becomes `640`, matching what `stat -c '%a'` prints.
- `stat -c '%C' "$path"` — the full SELinux context (`user:role:type:level`).
- `${PIPESTATUS[0]}` — the exit code of the **first** command in the pipeline (the `diff -r`, not the `head -n 20`). Without `PIPESTATUS`, `$?` would only give us `head`'s exit, which is always 0.

### The story

The grader's reflex after any `cp` or `ansible.builtin.copy` is the three-tool audit. Running just `ls` proves the path exists. Running just `diff` proves the content matches. Running just `stat` proves the metadata matches. None of those three commands alone catches everything; all three together do. Combined with `diff -r` for the recursive case, that is the auditor's complete kit.

The declared-baseline pattern (`expected-baseline.txt`) is the senior-engineer move. Anyone can eyeball `ls -lZ` and feel good. The baseline file makes the audit **reproducible by anyone with access to the journal** — including future-you a year from now, looking at the same playbook and wondering "what was this supposed to produce?" The baseline file *is* the answer.

### Expected output

```text
═══ Audit Pass — Lab 08b destinations must MATCH the declared baseline ═══
─── checking: /tmp/copy-lab/new-home/etc/config.conf ───
  ✅ content match (vs /tmp/copy-lab/source-config.conf)
  ✅ metadata match (mode=0640 owner=root group=root)
    src ctx: unconfined_u:object_r:user_tmp_t:s0
    dst ctx: unconfined_u:object_r:user_tmp_t:s0
  ✅ SELinux context present on dst
─── checking: /tmp/copy-lab/new-home/skel/.bashrc ───
  ✅ content match (vs /etc/skel/.bashrc)
  ✅ metadata match (mode=0644 owner=root group=root)
    src ctx: system_u:object_r:etc_t:s0
    dst ctx: system_u:object_r:etc_t:s0
  ✅ SELinux context present on dst
─── checking: /tmp/copy-lab/new-home/skel/.bash_profile ───
  ✅ content match (vs /etc/skel/.bash_profile)
  ✅ metadata match (mode=0644 owner=root group=root)
    src ctx: system_u:object_r:etc_t:s0
    dst ctx: system_u:object_r:etc_t:s0
  ✅ SELinux context present on dst
─── checking: /tmp/copy-lab/new-home/skel/.bash_logout ───
  ✅ content match (vs /etc/skel/.bash_logout)
  ✅ metadata match (mode=0644 owner=root group=root)
    src ctx: system_u:object_r:etc_t:s0
    dst ctx: system_u:object_r:etc_t:s0
  ✅ SELinux context present on dst
═══ Audit summary ═══
  CONTENT : 4 pass, 0 fail
  METADATA: 4 pass, 0 fail
  CONTEXT : 4 pass, 0 fail
═══ diff -r /etc/skel /tmp/copy-lab/new-home/skel ═══
  ✅ TREE_CLEAN (diff -r exit 0)
exit was: 0
```

> **The win condition: `0 fail` across CONTENT, METADATA, and CONTEXT, plus `TREE_CLEAN` from `diff -r`.** Anything else means Lab 08a or 08b is incomplete and Task 2 should not proceed until it is fixed.

### Switches

| Token | Meaning |
|---|---|
| `diff FILE1 FILE2` | Line-level diff; exit 0 if identical |
| `cmp FILE1 FILE2` | Byte-level binary compare; exit 0 if identical |
| `diff -r DIR1 DIR2` | Recursive directory diff; exit 0 if every file in both trees matches |
| `stat -c '%a'` | Numeric mode, no leading 0 |
| `stat -c '%U %G'` | Owner name + group name |
| `stat -c '%C'` | Full SELinux context |
| `stat -c '%y'` | mtime (human-readable) |
| `ls -lZ PATH` | DAC + SELinux in one row |
| `matchpathcon PATH` | The default SELinux context the policy would assign to PATH |
| `${var#prefix}` | Parameter expansion — strip leading prefix |
| `${PIPESTATUS[N]}` | Exit code of the Nth command in the last pipeline |
| `while IFS='\|' read ...` | Read pipe-separated rows from stdin |

### 🧠 Concept Card

|   | Concept | What it does |
|---|---|---|
|   | Three-tool audit | `diff` (content) + `stat` (metadata) + `ls -lZ` (SELinux) — three independent dimensions |
|   | `diff -r` for trees | The single recursive check that catches missing/extra files in subdirectories |
|   | Declared baseline | A pipe-separated text file listing the expected end state; drives the audit loop |
|   | `%a` vs leading `0` | `stat -c '%a'` omits the leading 0; compare against both forms |
|   | `PIPESTATUS` | The pipeline-aware exit code; `$?` alone hides earlier failures |
|   | Three-dimension counters | Per-dimension PASS/FAIL — a single counter conflates content with metadata with context |
| 🪤 | **Trap Risk T11-E for copies** | Trusting Ansible's `changed=0` without running `diff` + `stat` + `ls -lZ` independently |

### 🔁 PERSISTENCE CHECK

| What was configured | Verification command | Why it matters |
|---|---|---|
| Audit transcript | `wc -l /root/rhcsa_journal/lab-08c/task1/audit.txt` | Must be > 0 — proves we actually inspected |
| Baseline file preserved | `ls /root/rhcsa_journal/lab-08c/task1/expected-baseline.txt` | The audit is reproducible only if the baseline survives — store it in `/root/` |
| All three dimensions passed | `grep -E '(CONTENT\|METADATA\|CONTEXT) :' /root/rhcsa_journal/lab-08c/task1/audit.txt` | Every line must end in `0 fail` |
| Tree diff clean | `grep TREE_CLEAN /root/rhcsa_journal/lab-08c/task1/audit.txt` | The exhaustive cross-check |

> **Reboot reasoning:** `/tmp/copy-verify-lab/` and `/tmp/copy-lab/` both evaporate at reboot. The **only** thing that survives is the journal under `/root/rhcsa_journal/`. If the journal does not contain `audit.txt` and `expected-baseline.txt`, the audit cannot be reproduced — meaning the verification is effectively gone too. Task 2 proves the journal artifacts survive AND that the playbook can rebuild the destination from scratch.

### Journal write — BEFORE cleanup

```bash
LAB=lab-08c
TASK=task1
JDIR="/root/rhcsa_journal/${LAB}/${TASK}"
mkdir -p "$JDIR"
cp /tmp/copy-verify-lab/task1/audit.txt        "$JDIR/audit.txt"
cp /tmp/copy-verify-lab/expected-baseline.txt  "$JDIR/expected-baseline.txt"

cat > "$JDIR/done.txt" <<EOF
LAB:    ${LAB}
TASK:   ${TASK}
DATE:   $(date -Is)
USER:   $(whoami)@$(hostname)
STATUS: COMPLETE
EOF

cat > "$JDIR/notes.txt" <<EOF
TOPIC:    Three-tool audit (diff + stat + ls -lZ) + diff -r against declared baseline
COMMANDS: diff, diff -r, stat -c '%a %U %G %C', ls -lZ, matchpathcon, PIPESTATUS
TRAPS:    T11-E for copies rehearsed (we did NOT trust Ansible's changed=0 — independent verification)
MISSED:   (fill in if any ⚠️ flags)
NEXT:     task2 — simulated reboot, wipe /tmp, replay playbook from /root/ journal, prove no spurious backup
EOF

ls -la "$JDIR"
echo "exit was: $?"
```

### 🧹 Cleanup

```bash
# Keep the journal, drop the live verify workspace
rm -rf /tmp/copy-verify-lab/task1
ls /tmp/copy-verify-lab/
echo "exit was: $?"
```

### Troubleshoot

| Symptom | Fix |
|---|---|
| `CONTENT: N fail` | Content drift — re-run Lab 08b's playbook; if still failing, check that `source-config.conf` is at the expected v2 content. |
| `METADATA: N fail expected='0640 root root' got='600 root root'` | DAC drift — somebody `chmod`'d the dest. Re-run Lab 08b which sets mode unconditionally. |
| `CONTEXT: N fail` (dst ctx = `?`) | SELinux is disabled (`getenforce` → `Disabled`) OR the inode is unlabeled. `restorecon -v $path`. |
| `TREE_DIFFER` from `diff -r` | An extra file exists in `new-home/skel/` that is not in `/etc/skel/`, or vice versa. Read the diff output for the path. |
| `stat: cannot statx` | Path doesn't exist — Lab 08b's tree copy failed. Re-run `task1.yml`. |
| `<(...)` syntax error | You're running `sh` or `dash`, not `bash`. Switch shells. |

> **STOP — paste the "Audit summary" block AND the `TREE_CLEAN` line before Task 2. All three dimensions must be `0 fail` for Task 2 to be meaningful.**

---

## Task 2 — Simulated-reboot persistence proof + honest-backup confirmation

**Practice directory this task:** `/etc/skel` (read-only, the durable source), `/tmp/copy-lab/` (wiped to simulate reboot), `/root/rhcsa_journal/lab-08b/playbooks/` (the durable playbook) · The whole lesson is the contrast — `/tmp` evaporates, `/root/` survives, and the playbook under `/root/` can reproduce the entire `/tmp/copy-lab/new-home/` layout from cold storage.

### 🔁 Warm-Up — commands woven into Task 2

```bash
ls /root/rhcsa_journal/lab-08c/task1/                2>&1 | tee /tmp/copy-verify-lab/warmup-task2.txt
wc -l /root/rhcsa_journal/lab-08c/task1/audit.txt
test -f /root/rhcsa_journal/lab-08b/playbooks/task1.yml && echo "playbook OK"
test -d /etc/skel && echo "skel source OK (durable on this host)"
find /tmp/copy-lab -type f                           2>/dev/null | wc -l
stat -c '%n mountpoint=%m' /tmp /root /etc
set -o pipefail
echo "Warm-up done by $(whoami) at $(date -Is)"
echo "exit was: $?"
```

> Carry: `stat -c '%m'` exposes the **mount point** for each path. On a typical RHEL layout, `/tmp` may be on `tmpfs` (evaporates), `/root` is on the root partition (survives), and `/etc/skel` is also on the root partition (survives). That is the structural reason the journal + playbook + skel source all survive a reboot together.

### Purpose

Two interlocking proofs:

1. **Persistence proof** — wipe `/tmp/copy-lab/` entirely (simulates reboot), then re-run the Lab 08b playbook from the journal (`/root/rhcsa_journal/lab-08b/playbooks/task1.yml`). Re-run Task 1's three-tool audit. If everything still passes, the deploy is **reproducible from cold storage** — the contract for any config-deploy playbook.
2. **Honest-backup proof** — after the persistence-proof re-run, the destination is freshly created; there should be **no** `dest.NNNN.bak` file (because there was nothing to back up — the previous dest was wiped). Then run the playbook a *third* time without mutating the source. Still no backup, because the source and dest match (`changed=0`). This is the safety-check that `backup: true` is not spuriously rotating files on every run — which would be a quiet form of incorrectness that a careless implementation might exhibit.

### 🧵 WEAVE TRACE — warm-up commands re-used in this task body

| Warm-up command | Role inside Task 2 |
|---|---|
| `stat -c '%m'` | Confirms which paths are on tmpfs (will evaporate) vs the root partition (will survive) |
| `find /tmp/copy-lab` | Before and after the simulated reboot — verifies `/tmp/copy-lab` was cleared |
| `wc -l audit.txt` | Confirms the journal copy survived the simulated reboot |
| `test -f` | Verifies the playbook still exists under `/root/` after the wipe |
| `2>&1 \| tee` | Captures the re-audit transcript into `task2/post-reboot-audit.txt` |
| `$(date -Is)` | Stamps both the simulated reboot and the re-audit completion |

### Main command block

```bash
mkdir -p /tmp/copy-verify-lab/task2
JDIR="/root/rhcsa_journal/lab-08c/task2"
mkdir -p "$JDIR"

echo "═══ Pre-reboot state ═══" \
  2>&1 | tee /tmp/copy-verify-lab/task2/timeline.txt
stat -c '  %n  is on  %m' /tmp /root /etc /root/rhcsa_journal \
  2>&1 | tee -a /tmp/copy-verify-lab/task2/timeline.txt
ls /tmp/copy-lab/new-home/etc/ /tmp/copy-lab/new-home/skel/ \
  2>&1 | tee -a /tmp/copy-verify-lab/task2/timeline.txt

# Move task2 transcript to /root BEFORE we delete /tmp/copy-lab
cp /tmp/copy-verify-lab/task2/timeline.txt "$JDIR/timeline.txt"

# ── SIMULATE REBOOT — wipe /tmp/copy-lab entirely (preserve source-config.conf for re-deploy) ──
echo "═══ SIMULATING REBOOT — wiping /tmp/copy-lab/* and /tmp/copy-verify-lab/* ═══" \
  | tee -a "$JDIR/timeline.txt"
echo "  at $(date -Is)" | tee -a "$JDIR/timeline.txt"

# Snapshot source-config.conf content; reseed after the wipe (a real reboot would lose tmpfs entirely)
SOURCE_SNAPSHOT=$(cat /tmp/copy-lab/source-config.conf 2>/dev/null || echo "updated-config-v2")
rm -rf /tmp/copy-lab /tmp/copy-verify-lab/task2
mkdir -p /tmp/copy-lab /tmp/copy-verify-lab/task2
echo "$SOURCE_SNAPSHOT" > /tmp/copy-lab/source-config.conf
chmod 0640                /tmp/copy-lab/source-config.conf

find /tmp/copy-lab -type f 2>/dev/null | wc -l   # should be 1 — just source-config.conf

# ── POST-REBOOT — journal files must still exist under /root/ ──
echo "═══ Post-reboot — journal files survived? ═══" \
  | tee "$JDIR/post-reboot-audit.txt"
for f in /root/rhcsa_journal/lab-08b/playbooks/task1.yml \
         /root/rhcsa_journal/lab-08b/playbooks/task2.yml \
         /root/rhcsa_journal/lab-08c/task1/expected-baseline.txt \
         /root/rhcsa_journal/lab-08c/task1/audit.txt; do
  if test -f "$f"; then
    echo "  ✅ survived: $f ($(wc -l < "$f") lines)" | tee -a "$JDIR/post-reboot-audit.txt"
  else
    echo "  ❌ MISSING:  $f" | tee -a "$JDIR/post-reboot-audit.txt"
  fi
done

# ── Re-run the Lab 08b playbook from the journal (FIRST post-reboot apply) ──
echo "═══ Re-deploy via journal-resident playbook (first post-reboot apply) ═══" \
  | tee -a "$JDIR/post-reboot-audit.txt"
ansible-playbook /root/rhcsa_journal/lab-08b/playbooks/task1.yml \
  2>&1 | tee "$JDIR/post-reboot-apply.txt" | grep -E "PLAY RECAP|changed=|backup_file"

# ── Honest-backup check — there should be NO backup file (dest didn't exist pre-deploy) ──
echo "── honest-backup check #1: no backup expected (fresh dest after wipe) ──" \
  | tee -a "$JDIR/post-reboot-audit.txt"
ls /tmp/copy-lab/new-home/etc/config.conf.* 2>/dev/null \
  | tee -a "$JDIR/post-reboot-audit.txt"
if [ -z "$(ls /tmp/copy-lab/new-home/etc/config.conf.* 2>/dev/null)" ]; then
  echo "  ✅ no spurious backup created on fresh-deploy" \
    | tee -a "$JDIR/post-reboot-audit.txt"
else
  echo "  ❌ spurious backup found — backup: true is firing when it should not" \
    | tee -a "$JDIR/post-reboot-audit.txt"
fi

# ── Replay the Lab 08c Task 1 audit using ONLY journal artifacts ──
echo "═══ Re-run Task 1's three-tool audit from journal baseline ═══" \
  | tee -a "$JDIR/post-reboot-audit.txt"
CONTENT_PASS=0; CONTENT_FAIL=0; META_PASS=0; META_FAIL=0; CTX_PASS=0; CTX_FAIL=0
while IFS='|' read -r path mode owner group src; do
  case "$path" in \#*|"") continue;; esac
  echo "─── $path ───" | tee -a "$JDIR/post-reboot-audit.txt"
  diff "$src" "$path" >/dev/null 2>&1 \
    && { echo "  ✅ content match";   CONTENT_PASS=$(( CONTENT_PASS + 1 )); } \
    || { echo "  ❌ content DIFFER";   CONTENT_FAIL=$(( CONTENT_FAIL + 1 )); }
  ACTUAL=$(stat -c '%a %U %G' "$path" 2>/dev/null)
  EXPECTED="${mode#0} $owner $group"; ALT="$mode $owner $group"
  if [ "$ACTUAL" = "$EXPECTED" ] || [ "$ACTUAL" = "$ALT" ]; then
    echo "  ✅ metadata match";  META_PASS=$(( META_PASS + 1 ))
  else
    echo "  ❌ metadata DRIFT '$ACTUAL' vs '$EXPECTED'";  META_FAIL=$(( META_FAIL + 1 ))
  fi
  DST_CTX=$(stat -c '%C' "$path" 2>/dev/null)
  [ -n "$DST_CTX" ] && [ "$DST_CTX" != "?" ] \
    && { echo "  ✅ ctx present ($DST_CTX)"; CTX_PASS=$(( CTX_PASS + 1 )); } \
    || { echo "  ❌ ctx missing";              CTX_FAIL=$(( CTX_FAIL + 1 )); }
done < /root/rhcsa_journal/lab-08c/task1/expected-baseline.txt \
    | tee -a "$JDIR/post-reboot-audit.txt"

echo "═══ Post-reboot summary ═══"               | tee -a "$JDIR/post-reboot-audit.txt"
echo "  CONTENT : $CONTENT_PASS pass, $CONTENT_FAIL fail" | tee -a "$JDIR/post-reboot-audit.txt"
echo "  METADATA: $META_PASS pass, $META_FAIL fail"       | tee -a "$JDIR/post-reboot-audit.txt"
echo "  CONTEXT : $CTX_PASS pass, $CTX_FAIL fail"          | tee -a "$JDIR/post-reboot-audit.txt"

# ── SECOND post-reboot apply — idempotence still holds + no spurious backup ──
echo "═══ Second post-reboot apply — idempotence + no spurious backup ═══" \
  | tee -a "$JDIR/post-reboot-audit.txt"
ansible-playbook /root/rhcsa_journal/lab-08b/playbooks/task1.yml \
  2>&1 | tee "$JDIR/post-reboot-apply-2.txt" | grep -E "PLAY RECAP|changed=|backup_file"

echo "── honest-backup check #2: no backup expected (src and dst already match) ──" \
  | tee -a "$JDIR/post-reboot-audit.txt"
ls /tmp/copy-lab/new-home/etc/config.conf.* 2>/dev/null \
  | tee -a "$JDIR/post-reboot-audit.txt"
if [ -z "$(ls /tmp/copy-lab/new-home/etc/config.conf.* 2>/dev/null)" ]; then
  echo "  ✅ still no spurious backup — backup: true is honest" \
    | tee -a "$JDIR/post-reboot-audit.txt"
fi

echo "exit was: $?"
```

### Human-readable breakdown

1. **Snapshot pre-reboot state.** Record which paths are on `tmpfs` (will evaporate) vs the root partition (will survive) via `stat -c '%m'`. Save the timeline to `/root/` BEFORE the wipe.
2. **Simulate reboot.** `rm -rf /tmp/copy-lab /tmp/copy-verify-lab/task2`. Re-create only the bare minimum (`/tmp/copy-lab/` directory + `source-config.conf`) that a fresh system would have — the rest must be reproduced by the playbook.
3. **Verify journal artifacts survived.** Check that the playbooks + baseline file + Task 1 audit transcript all still exist under `/root/rhcsa_journal/`. If any are missing, the lab is incomplete and Task 2 fails.
4. **First post-reboot apply.** Run `task1.yml` from the journal. Expect `changed=N` (multiple changes — directories + file + tree all newly created). Check that `backup_file` is `(none ...)` because there was no pre-existing dest to back up. **This is the "honest backup" check #1** — `backup: true` should NOT spuriously create a backup when there is nothing to back up.
5. **Replay the Task 1 three-tool audit** using the journal-resident baseline file. All three dimensions must report `0 fail`. This is the structural proof of reproducibility.
6. **Second post-reboot apply.** Run `task1.yml` again. Expect `changed=0` (idempotence holds across reboot). Check again that no backup file exists — **honest backup check #2** — because the source and destination already match.

### Reading it left to right

- `stat -c '%m' /tmp /root /etc` — print the mount point that contains each path. `/tmp` may show `/tmp` (separately mounted on tmpfs) or `/` (mounted as part of root). Either way, `/tmp` is ephemeral on RHEL by default because `systemd-tmpfiles --clean-on-boot` runs at every boot.
- `rm -rf /tmp/copy-lab /tmp/copy-verify-lab/task2` — wipe both at once. `/tmp/copy-lab` is the destination from Lab 08b; `/tmp/copy-verify-lab/task2` is our workspace.
- `mkdir -p /tmp/copy-lab` after the wipe — recreate the bare directory because the playbook expects to write a file into it (the directory itself isn't auto-created by `ansible.builtin.copy` when the parent of `dest:` doesn't exist; that's `ansible.builtin.file` territory).
- `for f in ...; do test -f "$f" ...` — the journal-file existence loop. Every artifact that should have survived gets a ✅ or ❌.
- `< /root/rhcsa_journal/lab-08c/task1/expected-baseline.txt` — **redirect from the journal copy**, not the original under `/tmp/`. This is the structural test of persistence: the audit must read from `/root/`.
- `ansible-playbook ... | tee "$JDIR/post-reboot-apply.txt" | grep -E "PLAY RECAP|changed=|backup_file"` — full output to file, three audit-critical lines to screen.
- `[ -z "$(ls ... 2>/dev/null)" ]` — empty-glob check. If `ls` finds nothing matching `config.conf.*`, the substitution is empty and `-z` is true.

### The story

This task is the **only** thing that distinguishes a real deploy from theater. Running `ansible-playbook` once and seeing `changed=2` proves Ansible **did** something. Running `audit.txt` once on the same host that just ran the play proves the destination is at the right state **right now**. Neither proves the deploy is reproducible after a reboot, after a fresh shell, after weeks of drift.

Wiping `/tmp` and re-running from `/root/` proves the deploy is reproducible by **anyone** with access to the journal — including future-you, a different engineer, or a disaster-recovery rebuild from cold backup of `/root/`. The two-phase honest-backup check (no backup on fresh deploy, no backup on no-change re-run) proves that `backup: true` is not silently creating clutter on every run — a quiet form of incorrectness that creates noise in production and makes the real "yes, this run rotated a backup" event harder to spot.

For RHCSA: every change must produce verifiable evidence under `/root/`. For RHCE: every playbook must be reproducible from `/root/rhcsa_journal/lab-XX/playbooks/`. For the auditor seat in any role: if the deploy cannot be re-run from cold storage and produce the same result, it is not a deploy — it is a manual procedure that someone happened to write down in YAML.

### Expected output

```text
═══ Pre-reboot state ═══
  /tmp  is on  /tmp                  (or /, depending on layout)
  /root  is on  /
  /etc  is on  /
  /root/rhcsa_journal  is on  /
config.conf
.bash_logout  .bash_profile  .bashrc
═══ SIMULATING REBOOT — wiping /tmp/copy-lab/* and /tmp/copy-verify-lab/* ═══
  at 2026-05-28T20:15:00-04:00
1
═══ Post-reboot — journal files survived? ═══
  ✅ survived: /root/rhcsa_journal/lab-08b/playbooks/task1.yml (39 lines)
  ✅ survived: /root/rhcsa_journal/lab-08b/playbooks/task2.yml (32 lines)
  ✅ survived: /root/rhcsa_journal/lab-08c/task1/expected-baseline.txt (5 lines)
  ✅ survived: /root/rhcsa_journal/lab-08c/task1/audit.txt (45 lines)
═══ Re-deploy via journal-resident playbook (first post-reboot apply) ═══
PLAY RECAP ********************************************************************
localhost                  : ok=4    changed=3    unreachable=0    failed=0
── honest-backup check #1: no backup expected (fresh dest after wipe) ──
  ✅ no spurious backup created on fresh-deploy
═══ Re-run Task 1's three-tool audit from journal baseline ═══
─── /tmp/copy-lab/new-home/etc/config.conf ───
  ✅ content match
  ✅ metadata match
  ✅ ctx present (unconfined_u:object_r:user_tmp_t:s0)
─── /tmp/copy-lab/new-home/skel/.bashrc ───
  ✅ content match
  ✅ metadata match
  ✅ ctx present (system_u:object_r:etc_t:s0)
... (.bash_profile and .bash_logout follow the same pattern) ...
═══ Post-reboot summary ═══
  CONTENT : 4 pass, 0 fail
  METADATA: 4 pass, 0 fail
  CONTEXT : 4 pass, 0 fail
═══ Second post-reboot apply — idempotence + no spurious backup ═══
PLAY RECAP ********************************************************************
localhost                  : ok=4    changed=0    unreachable=0    failed=0
── honest-backup check #2: no backup expected (src and dst already match) ──
  ✅ still no spurious backup — backup: true is honest
exit was: 0
```

> **Three required lines:** (1) `Post-reboot summary` block with all three dimensions at `0 fail`. (2) First-apply `no spurious backup`. (3) Second-apply `changed=0` AND `still no spurious backup`. All three together = full persistence + idempotence + honest-backup proof.

### Switches

| Token | Meaning |
|---|---|
| `stat -c '%m'` | Print the mount point that contains the path |
| `rm -rf /tmp/X /tmp/Y` | Wipe two paths at once |
| `< FILE` | Redirect FILE to stdin for a while loop |
| `wc -l < FILE` | Line count without the filename column |
| `grep -E "A\|B\|C"` | Extended regex; match any of three alternations |
| `[ -z "$VAR" ]` | True if `$VAR` is empty |
| `2>/dev/null` | Discard stderr (used here to silence missing-glob noise from `ls`) |
| `\| head -n N` | Cap displayed output; full transcript still lands in `tee`'d file |

### 🧠 Concept Card

|   | Concept | What it does |
|---|---|---|
|   | `/tmp` vs `/root/` storage | `/tmp` is ephemeral (tmpfs or cleared on boot); `/root/` is on the persistent root partition |
|   | Journal as cold-storage deploy | Every playbook + baseline file lives in `/root/rhcsa_journal/` to survive reboot |
|   | Reproducible deploy | Re-running the playbook from journal-only artifacts is the test of real persistence |
|   | Honest backup | `backup: true` should fire only when dest existed AND content differed — NOT on every run |
|   | Two-phase backup check | First apply (no backup, dest was wiped) + second apply (no backup, content matches) = proves the safety net is honest |
|   | Mount-point awareness | `stat -c '%m'` exposes the structural reason for persistence — not just "it survived," but **why** |
| 🪤 | **Trap Risk T41** | Skipping the reboot test on a config-deploy playbook. The cost is discovering the missing change after the next reboot — too late. |

### 🔁 PERSISTENCE CHECK (this lab IS the persistence check)

| What was configured | Verification command | Why it matters |
|---|---|---|
| Post-reboot audit transcript | `wc -l /root/rhcsa_journal/lab-08c/task2/post-reboot-audit.txt` | The proof artifact of Task 2 itself |
| Timeline preserved | `head -n 10 /root/rhcsa_journal/lab-08c/task2/timeline.txt` | Pre-reboot evidence we did not fabricate |
| Idempotence holds across reboot | `grep changed=0 /root/rhcsa_journal/lab-08c/task2/post-reboot-apply-2.txt` | Second post-reboot apply must report `changed=0` |
| No spurious backup | `ls /tmp/copy-lab/new-home/etc/config.conf.* 2>/dev/null \| wc -l` | Must be `0` after both post-reboot applies |
| Trilogy complete | `find /root/rhcsa_journal/lab-08{a,b,c} -name done.txt \| wc -l` | Should be `6` — three sub-labs × two tasks each |

### Journal write — BEFORE cleanup

```bash
LAB=lab-08c
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
TOPIC:    Simulated-reboot persistence proof + honest-backup confirmation
COMMANDS: stat -c '%m', rm -rf /tmp/copy-lab, ansible-playbook from journal, three-tool re-audit
TRAPS:    T41 rehearsed (we did NOT skip the reboot test — replayed playbook from journal)
          Honest-backup verified — no spurious backup on either post-reboot apply
MISSED:   (fill in if any ⚠️ flags)
NEXT:     Lab 09 (mv/rename) — the relative of cp that doesn't need --preserve because mv preserves by default
EOF

ls -la "$JDIR"
echo "── Trilogy state ──"
find /root/rhcsa_journal/lab-08{a,b,c} -name done.txt | sort
echo "exit was: $?"
```

### 🧹 Cleanup

```bash
rm -rf /tmp/copy-lab /tmp/copy-verify-lab
test -d /tmp/copy-lab        || echo "copy sandbox gone — clean exit"
test -d /tmp/copy-verify-lab || echo "verify sandbox gone — clean exit"
echo "exit was: $?"
```

### Troubleshoot

| Symptom | Fix |
|---|---|
| `❌ MISSING` on any journal file | Lab 08a, 08b, or 08c Task 1 did not run its journal write step — go back and finish it |
| Post-reboot audit shows `1 fail` in CONTENT | The playbook is using a different source than the baseline declares. Inspect `expected-baseline.txt` and align. |
| Post-reboot audit shows `1 fail` in METADATA | The playbook does NOT set `mode:` explicitly — add it, re-run. |
| Post-reboot audit shows `1 fail` in CONTEXT (`?`) | SELinux is disabled. Re-enable, reboot, retry. |
| `❌ spurious backup found` on first post-reboot apply | `backup: true` fired when there was nothing to back up — likely a stale `dest~` file from a previous run that survived the wipe. Inspect and fix the playbook. |
| Second apply shows `changed=1` | Idempotence broken across reboot. Most likely cause: the source file content drifted between the two applies. Check `cat /tmp/copy-lab/source-config.conf`. |
| `grep PLAY RECAP` returns nothing | `ansible-playbook` failed to run — check toolchain (Lab 00). |

> **STOP — paste the "Post-reboot summary" block (all three dimensions at `0 fail`) AND the trilogy `done.txt` list (six entries) before completing Lab 08.**

---

## Lab 08c Checklist (2 tasks)

- [ ] Task 1 — Three-tool audit (`diff` + `stat` + `ls -lZ`) against `expected-baseline.txt` + `diff -r` tree check + journal evidence
- [ ] Task 2 — Simulated-reboot persistence proof: wipe `/tmp/copy-lab`, replay playbook from `/root/rhcsa_journal/lab-08b/playbooks/`, re-audit, confirm no spurious backup on either post-reboot apply

---

## 🏁 Lab 08 Trilogy — completion check

After all three sub-labs are done, this command should show **six** `done.txt` files:

```bash
find /root/rhcsa_journal/lab-08{a,b,c} -name done.txt | sort
```

Expected output:

```text
/root/rhcsa_journal/lab-08a/task1/done.txt
/root/rhcsa_journal/lab-08a/task2/done.txt
/root/rhcsa_journal/lab-08b/task1/done.txt
/root/rhcsa_journal/lab-08b/task2/done.txt
/root/rhcsa_journal/lab-08c/task1/done.txt
/root/rhcsa_journal/lab-08c/task2/done.txt
```

If any are missing, that sub-lab is incomplete. Do not start Lab 09 until the trilogy is closed.

---

## 🔗 Related Labs in the Trilogy

| Lab | Connection |
|---|---|
| **Lab 08a** — RHCSA hand-typed copy | The imperative form being audited |
| **Lab 08b** — Copying Files via Ansible | The declarative form being audited |
| Lab 07 — Timestamps and `stat` | `stat -c '%y'` and `%C` are the verification primitives that make this lab possible |
| Lab 09 — Moving and Renaming Files (`mv`) | The relative of `cp` — `mv` preserves attributes by default, so the audit looks slightly different |
| Lab 11c — Verifying File Removal | The mirror pattern: prove a `state=absent` actually emptied what it promised |
| Lab 12c — Verifying Created Directories (later) | Pattern reuse: declared baseline + three-tool audit + reboot replay |

---

## 👤 Author

**Kelvin R. Tobias**
[kelvinintech.com](https://kelvinintech.com) · [GitHub](https://github.com/kelvintechnical) · [LinkedIn](https://www.linkedin.com/in/kelvin-r-tobias-211949219)
