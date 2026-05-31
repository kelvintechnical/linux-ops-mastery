# Lab 12c: Verifying Created Directories — audit + persistence

- **Series:** linux-ops-mastery — File Operations & Shell Fundamentals
- **Trilogy:** `12a` (RHCSA) → `12b` (Ansible) → **`12c` (Verify — you are here)**
- **Career arcs covered:** RHCSA EX200 (verification reflex on directory-tree tasks), RHCE EX294 (auditor seat: prove the play's properties hold without trusting playbook output), SRE (post-deploy directory layout verification)
- **Prerequisite:** Lab 12a and Lab 12b complete
- **Time Estimate:** 20–30 minutes
- **Tasks:** 2 (Task 1 = three-tool audit + spec diff, Task 2 = simulated-reboot rebuild proof)
- **Practice Directory (rotation #12):** `/opt`
- **Sandbox:** `/tmp/mk-verify-lab`
- **Traps rehearsed this lab:** **T12-E** (verifying only directory existence and ignoring mode/owner) · **T41** (skipping reboot rebuild test on layout tasks)

> **This lab's practice directory is: `/opt`** — referenced as the real-world vendor layout we compare against.

---

## LAB HEADER BLOCK

```bash
echo "🖥️  ENV:   ${ENV:-DECLARE_ME}"
echo "🕒  TIME:  $(date -Is)"
echo "👤  USER:  $(whoami)@$(hostname)"
echo "⚠️  TRAP REMINDERS THIS LAB: T12-E T41"
echo "📁  PRACTICE DIR: /opt"
echo ""
echo "🧾 Journal check — Lab 12a and 12b must already be done:"
test -f /root/rhcsa_journal/lab-12a/task2/done.txt && echo "  lab-12a task2 done"
test -f /root/rhcsa_journal/lab-12b/task2/done.txt && echo "  lab-12b task2 done"
```

> **STOP — if either `done.txt` check failed, finish the missing lab first.**

---

## Objective

Audit a directory tree against a **declared specification** (path, mode, owner, group) — not just "does it exist." Then prove the audit is reproducible: wipe the live tree, reconstruct it from the journal + playbook, and re-run the same audit successfully.

---

## Concept: Directory Audit Is Four-Property, Not One

Whether the directory exists is the **least interesting** of four questions an auditor asks:

| Property | Verification primitive |
|---|---|
| **Existence** | `test -d PATH` (exit 0/1) |
| **Mode** | `stat -c '%a' PATH` (returns octal) |
| **Owner** | `stat -c '%U' PATH` (returns username) |
| **Group** | `stat -c '%G' PATH` (returns groupname) |

A "verification" that only checks the first property misses every drift introduced by `chmod`, `chown`, or a misconfigured Ansible module. T12-E is exactly this trap: candidates run `ls -ld` (which shows existence) and call it done, then lose points when the grader runs `stat -c '%a'`.

---

## Reference (everything for Tasks 1–2)

| Tool | Purpose |
|---|---|
| `test -d PATH` | Exit 0 only if PATH is a directory |
| `stat -c FORMAT PATH` | Programmatic property extraction (`%a`, `%U`, `%G`, `%n`, `%F`, `%y`) |
| `find PATH -type d` | Enumerate every directory under PATH |
| `getfacl PATH` | POSIX ACLs (rare on `mkdir`-created dirs but worth checking) |
| `ls -lZ PATH` | SELinux context |
| `diff -u DECLARED ACTUAL` | Cross-check against a specification file |

---

## Lab-Wide Setup

```bash
sudo -i
mkdir -p /tmp/mk-verify-lab

# The declared specification — what Lab 12b's playbook PROMISED to build
cat > /tmp/mk-verify-lab/spec.txt <<'EOF'
# Each line: PATH MODE OWNER GROUP
/tmp/mk-ansible-lab/projects/web/logs       750 root wheel
/tmp/mk-ansible-lab/projects/web/configs    750 root wheel
/tmp/mk-ansible-lab/projects/web/backups    750 root wheel
/tmp/mk-ansible-lab/projects/api/logs       750 root wheel
/tmp/mk-ansible-lab/projects/api/configs    750 root wheel
/tmp/mk-ansible-lab/projects/api/backups    750 root wheel
/tmp/mk-ansible-lab/projects/db/logs        750 root wheel
/tmp/mk-ansible-lab/projects/db/configs     750 root wheel
/tmp/mk-ansible-lab/projects/db/backups     750 root wheel
EOF

# Rebuild the tree from Lab 12b's playbook (since Task 2 of 12b ended with cleanup)
mkdir -p /tmp/mk-ansible-lab
ansible-playbook /root/rhcsa_journal/lab-12b/playbooks/task1.yml 2>&1 | tail -n 5

ls /tmp/mk-verify-lab
wc -l /tmp/mk-verify-lab/spec.txt
echo "exit was: $?"
```

> **STOP — paste output before Task 1.**

---

## Task 1 — Four-property audit + spec diff (T12-E)

**Practice directory this task:** `/opt` · we compare our built tree against `/opt`'s ls -ld output as a sanity check that mode 0750 is **intentionally tighter** than vendor 0755.

### Warm-Up

```bash
ls -ld /opt /tmp/mk-ansible-lab/projects                       2>&1 | tee /tmp/mk-verify-lab/warmup.txt
wc -l /tmp/mk-verify-lab/spec.txt
test -f /tmp/mk-verify-lab/spec.txt && echo "spec OK"
find /tmp/mk-ansible-lab/projects -mindepth 2 -type d          2>/dev/null | wc -l
stat -c '%n mode=%a owner=%U:%G' /opt
set -o pipefail
echo "Warm-up done by $(whoami) at $(date -Is)"
echo "exit was: $?"
```

### Purpose

Audit each leaf in `/tmp/mk-ansible-lab/projects/` against the declared specification (`spec.txt`). For each line, check existence, mode, owner, group — four independent properties. Tally PASS/FAIL. Then `diff` the actual layout against the declared layout to catch anything `spec.txt` didn't anticipate.

### WEAVE TRACE

| Warm-up command | Role inside Task 1 |
|---|---|
| `wc -l spec.txt` | Drives the loop iteration count — we audit exactly that many leaves |
| `test -f spec.txt` | Guards the loop — refuses to run if the spec is missing |
| `find ... -mindepth 2 -type d` | Cross-check: actual leaf count must equal spec line count |
| `stat -c '%n mode=%a owner=%U:%G'` | The four-property primitive — the single most important tool in this lab |
| `2>&1 \| tee` | Captures every PASS/FAIL line into `task1/audit.txt` |
| `$(date -Is)` | Stamps the audit completion |

### Main command block

```bash
mkdir -p /tmp/mk-verify-lab/task1

echo "═══ Four-property audit against spec.txt ═══" \
  2>&1 | tee /tmp/mk-verify-lab/task1/audit.txt

PASS=0
FAIL=0
FAIL_DETAILS=""
while IFS=' ' read -r path mode owner group; do
  # Skip comment lines and blank lines
  case "$path" in
    \#*|"") continue ;;
  esac

  # Property 1: existence
  if ! test -d "$path"; then
    echo "  FAIL  $path  (does not exist)" | tee -a /tmp/mk-verify-lab/task1/audit.txt
    FAIL=$(( FAIL + 1 ))
    continue
  fi

  # Properties 2–4: mode, owner, group
  actual_mode=$(stat -c '%a' "$path")
  actual_owner=$(stat -c '%U' "$path")
  actual_group=$(stat -c '%G' "$path")

  if [ "$actual_mode" = "$mode" ] && \
     [ "$actual_owner" = "$owner" ] && \
     [ "$actual_group" = "$group" ]; then
    echo "  PASS  $path  mode=$actual_mode owner=$actual_owner:$actual_group" \
      | tee -a /tmp/mk-verify-lab/task1/audit.txt
    PASS=$(( PASS + 1 ))
  else
    echo "  FAIL  $path  expected mode=$mode owner=$owner:$group  actual mode=$actual_mode owner=$actual_owner:$actual_group" \
      | tee -a /tmp/mk-verify-lab/task1/audit.txt
    FAIL=$(( FAIL + 1 ))
  fi
done < /tmp/mk-verify-lab/spec.txt

echo "═══ Audit summary: $PASS pass, $FAIL fail ═══" \
  | tee -a /tmp/mk-verify-lab/task1/audit.txt

# Cross-check: leaf count must match spec line count (no extras, no missing)
SPEC_COUNT=$(grep -vE '^\s*(#|$)' /tmp/mk-verify-lab/spec.txt | wc -l)
ACTUAL_COUNT=$(find /tmp/mk-ansible-lab/projects -mindepth 2 -type d | wc -l)
echo "spec leaves: $SPEC_COUNT  actual leaves: $ACTUAL_COUNT" \
  | tee -a /tmp/mk-verify-lab/task1/audit.txt

# Diff actual layout against declared layout
find /tmp/mk-ansible-lab/projects -mindepth 2 -type d | sort \
  > /tmp/mk-verify-lab/task1/actual-layout.txt
grep -vE '^\s*(#|$)' /tmp/mk-verify-lab/spec.txt | awk '{print $1}' | sort \
  > /tmp/mk-verify-lab/task1/spec-layout.txt
echo "═══ Diff: spec vs actual layout ═══" \
  | tee -a /tmp/mk-verify-lab/task1/audit.txt
diff -u /tmp/mk-verify-lab/task1/spec-layout.txt /tmp/mk-verify-lab/task1/actual-layout.txt \
  2>&1 | tee -a /tmp/mk-verify-lab/task1/audit.txt || true

echo "exit was: $?"
```

### Human-readable breakdown

1. Read `spec.txt` line by line, splitting on whitespace into `path mode owner group`.
2. Skip comments and blank lines.
3. For each leaf:
   - Check existence with `test -d`. If missing, FAIL immediately.
   - Capture actual mode/owner/group with three `stat` calls.
   - Compare actual against expected. All three must match for PASS.
4. Tally PASS and FAIL counts.
5. Cross-check leaf count: `spec.txt` lists N leaves; `find` must return exactly N.
6. `diff` the actual layout vs the spec layout. An empty diff is the win condition.

### Reading it left to right

- `while IFS=' ' read -r path mode owner group; do ... done < FILE` — read whitespace-separated fields into four variables.
- `case "$path" in \#*|"") continue ;; esac` — skip comments and blanks.
- `stat -c '%a' "$path"` — octal mode without leading zero. `%U` is username, `%G` is groupname.
- `[ "$a" = "$b" ] && [ "$c" = "$d" ] && [ "$e" = "$f" ]` — AND chain; all three must pass.
- `grep -vE '^\s*(#|$)'` — invert match: exclude comment lines and blank lines.
- `diff -u SPEC ACTUAL || true` — diff returns non-zero on differences; `|| true` keeps the script going while still printing the diff.

### The story

The `stat -c '%a %U %G'` four-property audit is what RHCSA graders run. If your verification only checks existence (via `ls` or `test -d`), you are auditing one of four properties and ignoring three. T12-E is the trap: candidates feel "verified" after running `ls -ld /path/web/logs` and seeing it listed, but never confirm the mode is `0750` instead of `0755`. The grader's `stat -c '%a'` catches it instantly.

### Expected output

```text
═══ Four-property audit against spec.txt ═══
  PASS  /tmp/mk-ansible-lab/projects/web/logs  mode=750 owner=root:wheel
  PASS  /tmp/mk-ansible-lab/projects/web/configs  mode=750 owner=root:wheel
  ... (9 PASS lines) ...
═══ Audit summary: 9 pass, 0 fail ═══
spec leaves: 9  actual leaves: 9
═══ Diff: spec vs actual layout ═══
(empty diff — clean exit)
exit was: 0
```

### Switches

| Token | Meaning |
|---|---|
| `while IFS=' ' read -r a b c d` | Whitespace-split read |
| `stat -c '%a'` / `'%U'` / `'%G'` | Octal mode / username / groupname |
| `case PATTERN in ... esac` | Pattern match for line filtering |
| `grep -vE 'REGEX'` | Invert-match with extended regex |
| `diff -u FILE1 FILE2 \|\| true` | Diff that doesn't fail the script |

### Concept Card

| Concept | What it does |
|---|---|
| Four-property audit | Existence + mode + owner + group — all four checked per leaf |
| Spec file as declaration | `spec.txt` is the contract; actual state is compared against it |
| Cross-count check | Number of actual leaves must equal number of declared leaves (no extras) |
| Layout diff | Catches any structural mismatch the per-line audit might miss |
| `stat -c` programmatic mode | Parsable output, scriptable verification |
| **🪤 Trap Risk T12-E** | Verifying only existence and skipping mode/owner. Always run `stat -c '%a %U %G'`. |

### PERSISTENCE CHECK

| What was configured | Verification command | Why it matters |
|---|---|---|
| Audit transcript | `wc -l /root/rhcsa_journal/lab-12c/task1/audit.txt` | The journal proof of the audit |
| Spec preserved | `ls /root/rhcsa_journal/lab-12c/task1/spec.txt` | Auditable contract for future reproductions |
| Diff was empty | `wc -l /root/rhcsa_journal/lab-12c/task1/spec-layout.txt; wc -l /root/rhcsa_journal/lab-12c/task1/actual-layout.txt` | Both should be `9` |

> **Reboot reasoning:** The tree is in `/tmp` — gone at reboot. The spec, audit transcript, and playbook live under `/root/` — survive. Task 2 proves the audit is reproducible.

### Journal write — BEFORE cleanup

```bash
LAB=lab-12c
TASK=task1
JDIR="/root/rhcsa_journal/${LAB}/${TASK}"
mkdir -p "$JDIR"
cp /tmp/mk-verify-lab/task1/audit.txt          "$JDIR/audit.txt"
cp /tmp/mk-verify-lab/task1/spec-layout.txt    "$JDIR/spec-layout.txt"
cp /tmp/mk-verify-lab/task1/actual-layout.txt  "$JDIR/actual-layout.txt"
cp /tmp/mk-verify-lab/spec.txt                 "$JDIR/spec.txt"

cat > "$JDIR/done.txt" <<EOF
LAB:    ${LAB}
TASK:   ${TASK}
DATE:   $(date -Is)
USER:   $(whoami)@$(hostname)
STATUS: COMPLETE
EOF

cat > "$JDIR/notes.txt" <<EOF
TOPIC:    Four-property audit (existence + mode + owner + group) + layout diff
COMMANDS: stat -c '%a %U %G', test -d, while read, diff -u, grep -vE
TRAPS:    T12-E rehearsed (we did NOT stop at existence — checked all four properties)
MISSED:   (fill in if any ⚠️ flags)
NEXT:     task2 — wipe everything and rebuild from journal + playbook (persistence proof)
EOF

ls -la "$JDIR"
echo "exit was: $?"
```

### Cleanup

```bash
rm -rf /tmp/mk-verify-lab/task1
ls /tmp/mk-verify-lab/
echo "exit was: $?"
```

### Troubleshoot

| Symptom | Fix |
|---|---|
| All leaves FAIL with mode=755 | Lab 12b apply used unquoted `mode: 0750` (YAML int trap). Fix the playbook and re-run. |
| Spec leaf count > actual | Some leaves missing. Re-run Lab 12b task1.yml. |
| Actual leaf count > spec | Extra directories created — check for typo in `vars` or unrelated mkdir during the lab. |
| `wheel` group missing → owner audit fails | `groupadd wheel` and re-run Lab 12b apply. |
| Trailing whitespace in spec.txt breaks read | Use `read -r path mode owner group` and trim spec.txt — IFS=' ' collapses runs of spaces. |

> **STOP — paste the "Audit summary" line and the empty-diff confirmation before Task 2.**

---

## Task 2 — Simulated-reboot rebuild + reproducible audit

**Practice directory this task:** `/opt` · the contrast `/tmp` vs `/opt` is the lesson — vendor `/opt` directories survive reboot because the underlying disk does; ours don't because tmpfs.

### Warm-Up

```bash
ls /root/rhcsa_journal/lab-12c/task1/                       2>&1 | tee /tmp/mk-verify-lab/warmup-task2.txt
wc -l /root/rhcsa_journal/lab-12c/task1/audit.txt
test -f /root/rhcsa_journal/lab-12c/task1/spec.txt && echo "spec persisted"
test -f /root/rhcsa_journal/lab-12b/playbooks/task1.yml && echo "playbook persisted"
stat -c '%n mountpoint=%m' /tmp /root
set -o pipefail
echo "Warm-up done by $(whoami) at $(date -Is)"
echo "exit was: $?"
```

### Purpose

Wipe `/tmp/mk-ansible-lab/` entirely, then prove the **entire layout can be reconstructed from journal artifacts alone**:

1. Spec file (declares what to verify) lives in `/root/`.
2. Playbook (builds the tree) lives in `/root/`.
3. Audit script (re-uses the same logic) is reproducible from the journal transcript.

Then re-run the audit against the rebuilt tree. Same `9 pass, 0 fail` result proves the trilogy is reproducible cold-start.

### WEAVE TRACE

| Warm-up command | Role inside Task 2 |
|---|---|
| `stat -c '%m'` | Shows `/tmp` mount point vs `/root` mount point — the structural reason persistence works |
| `test -f` on each journal artifact | Verifies the three persistence-critical files survived (spec, playbook, audit) |
| `wc -l` | Counts spec lines (must still be 9) and audit lines (must still be > 0) |
| `2>&1 \| tee` | Captures the rebuild + re-audit transcript to `task2/timeline.txt` |
| `$(date -Is)` | Stamps each phase boundary |

### Main command block

```bash
mkdir -p /tmp/mk-verify-lab/task2
JDIR="/root/rhcsa_journal/lab-12c/task2"
mkdir -p "$JDIR"

echo "═══ Phase 1: pre-wipe state ═══" \
  2>&1 | tee "$JDIR/timeline.txt"
stat -c '  %n  is on  %m' /tmp /root \
  | tee -a "$JDIR/timeline.txt"
find /tmp/mk-ansible-lab/projects -mindepth 2 -type d | wc -l \
  | tee -a "$JDIR/timeline.txt"

echo "═══ Phase 2: SIMULATE REBOOT — wipe /tmp/mk-ansible-lab ═══" \
  | tee -a "$JDIR/timeline.txt"
echo "  at $(date -Is)" | tee -a "$JDIR/timeline.txt"
rm -rf /tmp/mk-ansible-lab
test -d /tmp/mk-ansible-lab || echo "  /tmp/mk-ansible-lab gone — expected" \
  | tee -a "$JDIR/timeline.txt"

echo "═══ Phase 3: REBUILD from journal playbook ═══" \
  | tee -a "$JDIR/timeline.txt"
mkdir -p /tmp/mk-ansible-lab
ansible-playbook /root/rhcsa_journal/lab-12b/playbooks/task1.yml \
  2>&1 | tee "$JDIR/rebuild.txt" \
       | grep -E "PLAY RECAP|changed=" \
       | tee -a "$JDIR/timeline.txt"

echo "═══ Phase 4: REPRODUCE the four-property audit ═══" \
  | tee -a "$JDIR/timeline.txt"
PASS=0
FAIL=0
while IFS=' ' read -r path mode owner group; do
  case "$path" in
    \#*|"") continue ;;
  esac
  if test -d "$path" && \
     [ "$(stat -c '%a' "$path")" = "$mode" ] && \
     [ "$(stat -c '%U' "$path")" = "$owner" ] && \
     [ "$(stat -c '%G' "$path")" = "$group" ]; then
    PASS=$(( PASS + 1 ))
  else
    echo "  FAIL  $path" | tee -a "$JDIR/timeline.txt"
    FAIL=$(( FAIL + 1 ))
  fi
done < /root/rhcsa_journal/lab-12c/task1/spec.txt

echo "═══ Post-reboot summary: $PASS pass, $FAIL fail ═══" \
  | tee -a "$JDIR/timeline.txt"

# Cross-check against Task 1's audit
ORIGINAL=$(grep -c '^  PASS' /root/rhcsa_journal/lab-12c/task1/audit.txt)
echo "Original Task 1 pass count: $ORIGINAL" \
  | tee -a "$JDIR/timeline.txt"
echo "Task 2 reproduced pass count: $PASS" \
  | tee -a "$JDIR/timeline.txt"
test "$PASS" = "$ORIGINAL" && echo "REPRODUCED — audit is journal-persistent" \
  | tee -a "$JDIR/timeline.txt"
echo "exit was: $?"
```

### Human-readable breakdown

1. **Phase 1** — capture pre-wipe state (mount points and leaf count).
2. **Phase 2** — wipe `/tmp/mk-ansible-lab/` entirely. Verify it's gone.
3. **Phase 3** — re-run the Lab 12b playbook from the journal copy at `/root/rhcsa_journal/lab-12b/playbooks/task1.yml`. PLAY RECAP shows `changed=1` because the tree was just wiped.
4. **Phase 4** — re-run the four-property audit using the journal spec (`/root/rhcsa_journal/lab-12c/task1/spec.txt`). Must produce the same `9 pass, 0 fail` result as Task 1.
5. Cross-check: pass count from Task 1's audit equals pass count from this rebuild. Equality proves cold-start reproducibility.

### Reading it left to right

- `stat -c '%m' PATH` — mount point containing PATH. `/tmp` typically on `tmpfs` or `/`; `/root` always on `/` on standard layouts.
- `ansible-playbook .../task1.yml | tee file | grep -E "PLAY RECAP|changed="` — runs the play, full output to file, audit-critical lines to timeline.
- `grep -c '^  PASS' AUDIT_FILE` — counts PASS lines from Task 1's audit; this is the comparison baseline.
- `test "$PASS" = "$ORIGINAL"` — string equality; the explicit-quote form is safe even if `$PASS` is empty.

### The story

A reproducible audit is the **only** kind of audit. Running `audit.sh` once on the same host that just ran the playbook proves very little — anything could be cached in memory, ambient state, or shell history. Wiping the tree, rebuilding from `/root/`, and re-running the audit proves the system can be reconstructed and re-verified by anyone with access to the journal, in a fresh shell, after a reboot, weeks later. That is the contract of a real audit.

For RHCSA: every task's verification command must survive the test environment's reset. For RHCE: every playbook + verification must live on persistent storage. For any auditor seat: if the verification cannot be re-run from cold storage, it is not verification — it is just `echo "looks good"`.

### Expected output

```text
═══ Phase 1: pre-wipe state ═══
  /tmp  is on  /tmp                 (or /, depending on layout)
  /root  is on  /
9
═══ Phase 2: SIMULATE REBOOT — wipe /tmp/mk-ansible-lab ═══
  at 2026-05-27T16:05:42-04:00
  /tmp/mk-ansible-lab gone — expected
═══ Phase 3: REBUILD from journal playbook ═══
PLAY RECAP ********************************************************************
localhost                  : ok=2    changed=1    unreachable=0    failed=0
═══ Phase 4: REPRODUCE the four-property audit ═══
═══ Post-reboot summary: 9 pass, 0 fail ═══
Original Task 1 pass count: 9
Task 2 reproduced pass count: 9
REPRODUCED — audit is journal-persistent
exit was: 0
```

### Concept Card

| Concept | What it does |
|---|---|
| `/tmp` vs `/root/` persistence | Mount-point structure is the **reason** journals survive; tmpfs is the **reason** tmp does not |
| Three persistence-critical artifacts | spec + playbook + audit transcript — losing any one breaks reproducibility |
| Rebuild from journal | Playbook + spec are enough to reconstruct the entire lab outcome |
| Cross-check baseline | Pass count must equal the original to prove reproducibility |
| Idempotent rebuild | The play that built the tree can rebuild it after any wipe |
| **🪤 Trap Risk T41** | Skipping the reboot rebuild test on layout tasks. The cost is discovering a non-persistent config-only change later — too late. |

### PERSISTENCE CHECK (this lab IS the persistence check)

| What was verified | Verification command | Why it matters |
|---|---|---|
| Timeline transcript saved | `wc -l /root/rhcsa_journal/lab-12c/task2/timeline.txt` | The narrative proof of the rebuild |
| Rebuild succeeded | `grep 'changed=1' /root/rhcsa_journal/lab-12c/task2/timeline.txt` | PLAY RECAP confirms playbook re-created tree |
| Audit reproduced | `grep 'REPRODUCED' /root/rhcsa_journal/lab-12c/task2/timeline.txt` | Final assertion line |
| Trilogy complete | `find /root/rhcsa_journal/lab-12{a,b,c} -name done.txt \| wc -l` | Should be `6` |

### Journal write — BEFORE cleanup

```bash
LAB=lab-12c
TASK=task2
JDIR="/root/rhcsa_journal/${LAB}/${TASK}"

cat > "$JDIR/done.txt" <<EOF
LAB:    ${LAB}
TASK:   ${TASK}
DATE:   $(date -Is)
USER:   $(whoami)@$(hostname)
STATUS: COMPLETE
EOF

cat > "$JDIR/notes.txt" <<EOF
TOPIC:    Wipe + rebuild + re-audit — full reproducibility proof
COMMANDS: stat -c '%m', ansible-playbook from journal, four-property re-audit
TRAPS:    T41 rehearsed (we did NOT skip the rebuild test)
MISSED:   (fill in if any ⚠️ flags)
NEXT:     lab-13a (creating-command-aliases) — `alias`, `unalias`, /etc/profile.d/
EOF

ls -la "$JDIR"
echo "── Trilogy state ──"
find /root/rhcsa_journal/lab-12{a,b,c} -name done.txt | sort
echo "exit was: $?"
```

### Cleanup

```bash
rm -rf /tmp/mk-verify-lab /tmp/mk-ansible-lab
test -d /tmp/mk-verify-lab || echo "verify sandbox gone"
test -d /tmp/mk-ansible-lab || echo "ansible sandbox gone"
echo "exit was: $?"
```

### Troubleshoot

| Symptom | Fix |
|---|---|
| Rebuild fails with "wheel group missing" | `groupadd wheel` then re-run |
| Post-reboot audit shows `1 fail` | A property in spec.txt no longer matches what playbook produces. Re-sync spec.txt to playbook. |
| `REPRODUCED` line missing | Pass counts don't match. Inspect the timeline.txt for which leaf failed. |
| `/tmp` mount point shows `/` | `/tmp` not separately mounted — still tmpfs-cleared on reboot if `tmp.mount` is enabled, but check with `systemctl status tmp.mount` |

> **STOP — paste the "REPRODUCED" line and the trilogy `done.txt` list before completing Lab 12.**

---

## Lab 12c Checklist (2 tasks)

- [ ] Task 1 — Four-property audit (existence + mode + owner + group) against spec.txt + layout diff
- [ ] Task 2 — Wipe `/tmp/mk-ansible-lab`, rebuild from journal playbook, re-audit, prove `REPRODUCED`

---

## Lab 12 Trilogy — completion check

```bash
find /root/rhcsa_journal/lab-12{a,b,c} -name done.txt | sort
```

Expected: six paths (12a/{task1,task2}, 12b/{task1,task2}, 12c/{task1,task2}). Do not start Lab 13a until the trilogy is closed.

---

## Related Labs

| Lab | Connection |
|---|---|
| **Lab 12a** — RHCSA hand-typed mkdir | The imperative form being audited |
| **Lab 12b** — Creating Directories via Ansible | The declarative form being audited |
| Lab 11 — Safe Deletion | The inverse: 11 removes what 12 builds; trilogy structure identical |
| Lab 13c — Verifying Aliases | Mirror pattern: prove `/etc/profile.d/*.sh` deployed and sourced |

---

## Author

**Kelvin R. Tobias**
[kelvinintech.com](https://kelvinintech.com) · [GitHub](https://github.com/kelvintechnical) · [LinkedIn](https://www.linkedin.com/in/kelvin-r-tobias-211949219)
