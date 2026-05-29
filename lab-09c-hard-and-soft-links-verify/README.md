# Lab 09c: Verifying Links — type/target audit + persistence proof

- **Series:** linux-ops-mastery — File Operations & Shell Fundamentals
- **Trilogy:** `09a` (RHCSA) → `09b` (Ansible) → **`09c` (Verify — you are here)**
- **Career arcs covered:** RHCSA EX200 (verification reflex on every link task), RHCE EX294 (auditor seat — prove a play worked without trusting playbook output), SRE (post-deploy symlink verification), All exams (the "what would you check next" interview reflex)
- **Prerequisite:** Lab 09a and Lab 09b completed — this lab verifies their combined effect
- **Time Estimate:** 20–30 minutes
- **Tasks:** 2 (Task 1 = three-tool audit, Task 2 = simulated-reboot persistence proof)
- **Practice Directory (lab-wide rotation #09):** `/var/log`
- **Sandbox:** `/tmp/links-lab/`
- **Traps rehearsed this lab:** **T11-E equivalent** (trusting `ls` `->` arrow without `readlink -f` to resolve chains) · **T41** (skipping reboot test on a symlink-deployment task)

> **This lab's practice directory is: `/var/log`** — every task references it in at least two commands.

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
echo "📁  PRACTICE DIR: /var/log"
echo ""
echo "🧾 Journal check — Lab 09a and 09b must already be done:"
test -f /root/rhcsa_journal/lab-09a/task2/done.txt && echo "  ✅ lab-09a task2 done"
test -f /root/rhcsa_journal/lab-09b/task2/done.txt && echo "  ✅ lab-09b task2 done"
find /var/log -maxdepth 2 -type l 2>/dev/null | head -3
```

> **STOP — if either `done.txt` check above failed, return and finish Lab 09a or 09b first.**

---

## 🎯 Objective

Take off the operator's hat and put on the **auditor's hat**. Lab 09a built links by hand. Lab 09b recreated them via Ansible and reported `changed=0` on re-run. Neither proves the system is in the expected state **right now**. Lab 09c inspects links with RHCSA-grade commands — no playbook output, no trust in previous labs — then proves the audit survives a simulated reboot by re-running the Lab 09b playbook from journal storage.

---

## 🧠 Concept: `readlink -f` vs `ls -l` for Chain Resolution

`ls -l` shows a symlink's immediate target with a `->` arrow — but it does **not** follow chains. If `A -> B -> C`, `ls -l A` shows `A -> B`, not the final destination.

| What you see | What it tells you | What it hides |
|---|---|---|
| `ls -l TARGET` | Symlink exists; shows `->` arrow | Intermediate links in a chain |
| `stat -c '%n %F'` | File type (`symbolic link`, `regular file`) | Whether the target is reachable |
| `readlink TARGET` | Literal stored path string | Final destination if chain exists |
| `readlink -f TARGET` | Canonical absolute final destination | Nothing — this is the auditor's answer |
| `find -inum N` | All hard-link siblings for inode N | Symlink relationships |

The grader's reflex: **`ls -l` + `stat` + `readlink -f`** for symlinks; **`ls -li` + `stat -c '%h'` + `find -inum`** for hard links. Never claim a symlink deployment is correct based on the `->` arrow alone (T11-E equivalent).

---

## 📚 Inspection Reference (everything for Tasks 1–2)

| Tool | Purpose | Why an auditor reaches for it |
|---|---|---|
| `ls -l TARGET` | Shows `->` rendering for symlinks | First human check — type + target hint |
| `ls -li TARGET` | Inode column + symlink arrow | Side-by-side inode compare for hard links |
| `stat -c '%n %F'` | Name + file type | Proves "symbolic link" vs "regular file" |
| `stat -c '%i links=%h'` | Inode + hard link count | Hard-link audit |
| `readlink TARGET` | Literal target string | What the symlink stores |
| `readlink -f TARGET` | Canonical resolved path | Follows chains — the truth |
| `find DIR -inum N` | Reverse lookup by inode | All hard-link siblings |
| `test -L` / `test -e` | Symlink-ness vs reachability | Catches dangling symlinks |
| `diff -u EXPECTED ACTUAL` | Baseline comparison | Catches discrepancies single checks miss |

---

## 🚦 Lab-Wide Setup — run BEFORE Task 1

```bash
sudo -i

# Ensure Lab 09b artifacts exist — re-seed sandbox if needed
mkdir -p /tmp/links-lab
test -e /tmp/links-lab/data.txt || echo "verify origin" | tee /tmp/links-lab/data.txt

# Verification workspace + declared baseline
mkdir -p /tmp/links-lab/verify
cat > /tmp/links-lab/verify/expected-baseline.txt <<'EOF'
SOFT_LINK=/tmp/links-lab/ansible-soft
SOFT_TARGET=/tmp/links-lab/releases/v2/data.txt
HARD_LINK=/tmp/links-lab/ansible-hard
ORIGIN=/tmp/links-lab/data.txt
HARD_INODE_MATCH=yes
EOF

# If links don't exist yet, run Lab 09b playbooks first
test -L /tmp/links-lab/ansible-soft || ansible-playbook /root/rhcsa_journal/lab-09b/playbooks/links.yml 2>/dev/null
test -f /tmp/links-lab/releases/v2/data.txt || (mkdir -p /tmp/links-lab/releases/v2 && echo "release v2 content" > /tmp/links-lab/releases/v2/data.txt)
test "$(readlink -f /tmp/links-lab/ansible-soft 2>/dev/null)" = "/tmp/links-lab/releases/v2/data.txt" || ansible-playbook /root/rhcsa_journal/lab-09b/playbooks/promote.yml 2>/dev/null

ls -li /tmp/links-lab/
cat /tmp/links-lab/verify/expected-baseline.txt
find /var/log -maxdepth 2 -type l 2>/dev/null | head -3
echo "exit was: $?"
```

> **STOP — paste output before Task 1.**

---

## Task 1 — Three-tool audit: type, target, inode cross-check

**Practice directory this task:** `/var/log` (read-only symlink context), `/tmp/links-lab/` (audit targets)

### 🔁 Warm-Up — commands woven into Task 1

```bash
ls -la /tmp/links-lab/verify/                           2>&1 | tee /tmp/links-lab/verify/warmup.txt
wc -l /tmp/links-lab/verify/expected-baseline.txt
test -f /tmp/links-lab/verify/expected-baseline.txt && echo "baseline OK"
stat -c '%n %F' /tmp/links-lab/ansible-soft 2>/dev/null || echo "run Lab 09b first"
find /var/log -maxdepth 2 -type l 2>/dev/null | head -3
set -o pipefail
echo "Warm-up done by $(whoami) at $(date -Is)"
echo "exit was: $?"
```

> Carry from Lab 09b: `readlink -f` is the independent verification — we cross-check it against the declared baseline, not Ansible's `changed=` output.

### Purpose

Walk through each link Lab 09b created and prove with **three independent RHCSA inspection commands** that type, target, and inode relationships match the expected baseline. Compare against `expected-baseline.txt` with `diff`.

### 🧵 WEAVE TRACE — warm-up commands re-used in this task body

| Warm-up command | Role inside Task 1 |
|---|---|
| `stat -c '%n %F'` | Proves file type (symbolic link vs regular file) |
| `wc -l expected-baseline.txt` | Confirms baseline file is populated |
| `find /var/log -type l` | Practice-dir contrast — real symlinks vs our sandbox |
| `2>&1 \| tee` | Captures full audit into `task1/audit.txt` |
| `$(date -Is)` | Journal timestamp |

### Main command block

Three-tool audit — `ls -l`, `stat`, `readlink -f`, plus hard-link `find -inum`:

```bash
mkdir -p /tmp/links-lab/verify/task1
cd /tmp/links-lab

echo "═══ Audit Pass — Lab 09b links must match baseline ═══" \
  2>&1 | tee /tmp/links-lab/verify/task1/audit.txt

# ── 1) Symlink inspection ──
echo "─── SYMLINK: ansible-soft ───" | tee -a /tmp/links-lab/verify/task1/audit.txt

# Tool 1: ls -l (shows -> rendering)
ls -l /tmp/links-lab/ansible-soft 2>&1 | tee -a /tmp/links-lab/verify/task1/audit.txt

# Tool 2: stat (proves it's a symbolic link)
stat -c '%n %F' /tmp/links-lab/ansible-soft 2>&1 | tee -a /tmp/links-lab/verify/task1/audit.txt

# Tool 3: readlink -f (resolves to final destination — NOT just ls arrow)
readlink /tmp/links-lab/ansible-soft | tee -a /tmp/links-lab/verify/task1/audit.txt
readlink -f /tmp/links-lab/ansible-soft | tee -a /tmp/links-lab/verify/task1/audit.txt

test -L /tmp/links-lab/ansible-soft && echo "  ✅ test -L: is symlink" | tee -a /tmp/links-lab/verify/task1/audit.txt
test -e /tmp/links-lab/ansible-soft && echo "  ✅ test -e: target reachable" | tee -a /tmp/links-lab/verify/task1/audit.txt

# ── 2) Hard-link inspection ──
echo "─── HARD LINK: ansible-hard vs data.txt ───" | tee -a /tmp/links-lab/verify/task1/audit.txt

ls -li /tmp/links-lab/ansible-hard /tmp/links-lab/data.txt 2>&1 | tee -a /tmp/links-lab/verify/task1/audit.txt
stat -c 'inode=%i links=%h' /tmp/links-lab/ansible-hard | tee -a /tmp/links-lab/verify/task1/audit.txt

# Tool 3 for hard links: find -inum (reverse-lookup siblings)
inode=$(stat -c '%i' /tmp/links-lab/data.txt)
find /tmp/links-lab -inum "$inode" 2>&1 | tee -a /tmp/links-lab/verify/task1/audit.txt

# ── 3) Content compare ──
diff <(cat /tmp/links-lab/ansible-soft) <(cat /tmp/links-lab/data.txt) && echo "SOFT_CONTENT_MATCH" | tee -a /tmp/links-lab/verify/task1/audit.txt
diff <(cat /tmp/links-lab/ansible-hard) <(cat /tmp/links-lab/data.txt) && echo "HARD_CONTENT_MATCH" | tee -a /tmp/links-lab/verify/task1/audit.txt

# ── 4) Compare against expected baseline ──
echo "═══ Actual state snapshot ═══" | tee -a /tmp/links-lab/verify/task1/audit.txt
{
  echo "SOFT_LINK=/tmp/links-lab/ansible-soft"
  echo "SOFT_TARGET=$(readlink -f /tmp/links-lab/ansible-soft)"
  echo "HARD_LINK=/tmp/links-lab/ansible-hard"
  echo "ORIGIN=/tmp/links-lab/data.txt"
  if [ "$(stat -c '%i' /tmp/links-lab/ansible-hard)" = "$(stat -c '%i' /tmp/links-lab/data.txt)" ]; then
    echo "HARD_INODE_MATCH=yes"
  else
    echo "HARD_INODE_MATCH=no"
  fi
} | tee /tmp/links-lab/verify/task1/actual-state.txt

diff -u /tmp/links-lab/verify/expected-baseline.txt /tmp/links-lab/verify/task1/actual-state.txt \
  | tee -a /tmp/links-lab/verify/task1/audit.txt || echo "(diff shows promote target — update baseline if v2 expected)"

echo "exit was: $?"
```

### Human-readable breakdown

1. **Symlink audit triangle:** `ls -l` (visual `->`), `stat -c '%F'` (proves type), `readlink -f` (canonical destination — resolves chains T11-E would miss).
2. **Hard-link audit triangle:** `ls -li` (inode column match), `stat -c '%h'` (link count), `find -inum` (all sibling names).
3. `test -L` + `test -e` pair catches dangling symlinks — `-L` true even when dangling; `-e` false when target missing.
4. `diff` against declared baseline catches promote-target mismatches a single `ls` would miss.

### Reading it left to right

- `ls -l TARGET` — long listing; symlinks show `lrwxrwxrwx ... TARGET -> PATH`.
- `stat -c '%n %F'` — `%F` returns `symbolic link`, `regular file`, etc.
- `readlink -f TARGET` — follows every link in the chain to the final absolute path.
- `find /tmp/links-lab -inum "$inode"` — all hard-link names sharing that inode.
- `diff -u EXPECTED ACTUAL` — unified diff; empty output = perfect match.

### The story

You hand a grader `audit.txt` and it reads: "`ansible-soft` is a symlink whose canonical target is v2 (readlink -f), `ansible-hard` shares inode with `data.txt` (find -inum), and reading any link yields identical content (diff)." That's the auditor's full link report. Trusting the `->` arrow from `ls -l` without `readlink -f` is how broken symlink chains hide until a service restart (T11-E equivalent).

### Expected output

```text
═══ Audit Pass — Lab 09b links must match baseline ═══
─── SYMLINK: ansible-soft ───
lrwxrwxrwx. 1 root root 22 ... /tmp/links-lab/ansible-soft -> /tmp/links-lab/releases/v2/data.txt
/tmp/links-lab/ansible-soft symbolic link
/tmp/links-lab/releases/v2/data.txt
/tmp/links-lab/releases/v2/data.txt
  ✅ test -L: is symlink
  ✅ test -e: target reachable
─── HARD LINK: ansible-hard vs data.txt ───
12345 -rw-r--r--. 3 root root ... ansible-hard
12345 -rw-r--r--. 3 root root ... data.txt
inode=12345 links=3
/tmp/links-lab/data.txt
/tmp/links-lab/hard-link
/tmp/links-lab/ansible-hard
SOFT_CONTENT_MATCH
HARD_CONTENT_MATCH
exit was: 0
```

### Switches

| Token | Meaning |
|---|---|
| `ls -l` | Long listing with symlink arrow |
| `ls -li` | Long listing with inode column |
| `stat -c '%F'` | File type string |
| `readlink -f` | Canonical absolute path (follow chain) |
| `find -inum N` | All paths with inode N |
| `test -L` | Is symlink (no follow) |
| `test -e` | Target exists (follow) |
| `diff -u A B` | Unified diff against baseline |

### 🧠 Concept Card

|   | Concept | What it does |
|---|---|---|
|   | Audit triangle (symlink) | `ls -l` + `stat` + `readlink -f` |
|   | Audit triangle (hard link) | `ls -li` + `stat -c '%h'` + `find -inum` |
|   | Declared baseline | Text file listing expected end state |
|   | `readlink -f` over `ls ->` | Resolves chains — the T11-E equivalent fix |
|   | `test -L` + `test -e` | Symlink-ness vs reachability |
| 🪤 | **Trap Risk T11-E** | Trusting `ls` arrow without `readlink -f` — chains hide broken middle links |

### 🔁 PERSISTENCE CHECK

| What was configured | Verification command | Why it matters |
|---|---|---|
| Audit transcript | `wc -l /root/rhcsa_journal/lab-09c/task1/audit.txt` | Must be > 0 |
| Content match | `grep -cE '(SOFT|HARD)_CONTENT_MATCH' /tmp/links-lab/verify/task1/audit.txt` | Both must appear |
| Baseline stored | `ls /root/rhcsa_journal/lab-09c/task1/expected-baseline.txt` | Reproducible audit |

> **Reboot reasoning:** `/tmp/links-lab/` evaporates at reboot. Store `audit.txt` and baseline in `/root/rhcsa_journal/lab-09c/` — that's the only copy that survives.

### Journal write — BEFORE cleanup

```bash
LAB=lab-09c
TASK=task1
JDIR="/root/rhcsa_journal/${LAB}/${TASK}"
mkdir -p "$JDIR"
cp /tmp/links-lab/verify/task1/audit.txt "$JDIR/audit.txt"
cp /tmp/links-lab/verify/task1/actual-state.txt "$JDIR/actual-state.txt"
cp /tmp/links-lab/verify/expected-baseline.txt "$JDIR/expected-baseline.txt"

cat > "$JDIR/done.txt" <<EOF
LAB:    ${LAB}
TASK:   ${TASK}
DATE:   $(date -Is)
USER:   $(whoami)@$(hostname)
STATUS: COMPLETE
soft_target=$(readlink -f /tmp/links-lab/ansible-soft)
hard_inode_match=$([ "$(stat -c '%i' /tmp/links-lab/ansible-hard)" = "$(stat -c '%i' /tmp/links-lab/data.txt)" ] && echo yes || echo no)
EOF

cat > "$JDIR/notes.txt" <<EOF
TOPIC:    Three-tool audit — ls -l, stat, readlink -f, find -inum + baseline diff
COMMANDS: ls -l, stat -c, readlink -f, find -inum, test -L, test -e, diff -u
TRAPS:    T11-E rehearsed (used readlink -f, not just ls arrow)
MISSED:   (fill in if any ⚠️ flags)
NEXT:     task2 — simulated-reboot persistence proof
EOF

ls -la "$JDIR"
echo "exit was: $?"
```

### 🧹 Cleanup

```bash
rm -rf /tmp/links-lab/verify/task1
ls /tmp/links-lab/verify/
echo "exit was: $?"
```

### Troubleshoot

| Symptom | Fix |
|---|---|
| `ansible-soft` missing | Re-run Lab 09b `links.yml` |
| `readlink -f` shows v1 not v2 | Re-run Lab 09b `promote.yml` |
| `HARD_INODE_MATCH=no` | Hard link not created — re-run `links.yml` |
| `SOFT_CONTENT_MATCH` missing | Symlink points at wrong path — check promote |
| Empty `audit.txt` | `tee` failed — turn on `set -o pipefail` |

> **STOP — paste audit summary and both CONTENT_MATCH lines before Task 2.**

---

## Task 2 — Simulated-reboot persistence proof: wipe sandbox, re-run Lab 09b playbook

**Practice directory this task:** `/var/log` (context), `/tmp/links-lab/` vs `/root/rhcsa_journal/` (the contrast is the lesson)

### 🔁 Warm-Up — commands woven into Task 2

```bash
ls /root/rhcsa_journal/lab-09c/task1/                2>&1 | tee /tmp/links-lab/verify/warmup-task2.txt
wc -l /root/rhcsa_journal/lab-09c/task1/audit.txt
test -f /root/rhcsa_journal/lab-09b/playbooks/links.yml && echo "playbook OK"
find /tmp/links-lab -type f 2>/dev/null | wc -l
stat -c '%n mountpoint=%m' /tmp /root
set -o pipefail
echo "Warm-up done by $(whoami) at $(date -Is)"
echo "exit was: $?"
```

> Carry: `stat -c '%m'` reveals mount points — `/tmp` is often tmpfs (evaporates), `/root` is on the persistent root partition.

### Purpose

Wipe `/tmp/links-lab/` entirely to simulate reboot clearing tmpfs. Hard links in the wiped directory are gone — but the Lab 09b playbook under `/root/rhcsa_journal/lab-09b/playbooks/` **is reproducible**. Re-run it, then re-run `promote.yml`, and verify with `readlink -f`. The atomic-update pattern (`ln -sfn` / `force: true`) is the persistence guarantee for symlinks across release deployments.

### 🧵 WEAVE TRACE — warm-up commands re-used in this task body

| Warm-up command | Role inside Task 2 |
|---|---|
| `stat -c '%m'` | Proves which paths are tmpfs vs root (structural persistence reason) |
| `find /tmp/links-lab` | Before/after wipe — confirms sandbox cleared |
| `test -f links.yml` | Playbook survived before we wipe `/tmp/` |
| `2>&1 \| tee` | Post-reboot audit transcript |
| `$(date -Is)` | Timeline stamps |

### Main command block

```bash
mkdir -p /tmp/links-lab/verify/task2
JDIR="/root/rhcsa_journal/lab-09c/task2"
mkdir -p "$JDIR"

echo "═══ Pre-reboot state ═══" \
  2>&1 | tee /tmp/links-lab/verify/task2/timeline.txt
stat -c '  %n  is on  %m' /tmp /root /root/rhcsa_journal \
  2>&1 | tee -a /tmp/links-lab/verify/task2/timeline.txt
ls -li /tmp/links-lab/ 2>&1 | tee -a /tmp/links-lab/verify/task2/timeline.txt
readlink -f /tmp/links-lab/ansible-soft 2>&1 | tee -a /tmp/links-lab/verify/task2/timeline.txt

# Save timeline to /root BEFORE wipe
cp /tmp/links-lab/verify/task2/timeline.txt "$JDIR/timeline.txt"

# ── Simulate reboot: wipe the entire sandbox ──
echo "═══ SIMULATING REBOOT — wiping /tmp/links-lab/ ═══" \
  2>&1 | tee -a "$JDIR/timeline.txt"
echo "  at $(date -Is)" | tee -a "$JDIR/timeline.txt"

rm -rf /tmp/links-lab/*
find /tmp/links-lab -type f 2>/dev/null | wc -l   # must be 0
test ! -L /tmp/links-lab/ansible-soft 2>/dev/null && echo "  links gone — expected after wipe"

# ── Post-reboot: reconstruct from /root/ journal only ──
echo "═══ Post-reboot — re-run Lab 09b playbooks from journal ═══" \
  2>&1 | tee "$JDIR/post-reboot-audit.txt"

# 1. Journal playbooks must survive
for f in /root/rhcsa_journal/lab-09b/playbooks/links.yml \
         /root/rhcsa_journal/lab-09b/playbooks/promote.yml \
         /root/rhcsa_journal/lab-09c/task1/audit.txt \
         /root/rhcsa_journal/lab-09c/task1/expected-baseline.txt; do
  if test -f "$f"; then
    echo "  ✅ survived: $f ($(wc -l < "$f") lines)" | tee -a "$JDIR/post-reboot-audit.txt"
  else
    echo "  ❌ MISSING:  $f" | tee -a "$JDIR/post-reboot-audit.txt"
  fi
done

# 2. Re-seed origin and re-run links playbook (reproducible)
mkdir -p /tmp/links-lab
echo "ansible origin" | tee /tmp/links-lab/data.txt
ansible-playbook /root/rhcsa_journal/lab-09b/playbooks/links.yml \
  2>&1 | tee "$JDIR/post-reboot-links.txt" | grep -E "PLAY RECAP|changed="

# 3. Re-seed v2 and re-run promote playbook
mkdir -p /tmp/links-lab/releases/v2
echo "release v2 content" | tee /tmp/links-lab/releases/v2/data.txt
ansible-playbook /root/rhcsa_journal/lab-09b/playbooks/promote.yml \
  2>&1 | tee "$JDIR/post-reboot-promote.txt" | grep -E "PLAY RECAP|changed="

# 4. Verify with readlink -f — the persistence guarantee for symlink deployments
readlink -f /tmp/links-lab/ansible-soft | tee -a "$JDIR/post-reboot-audit.txt"
[ "$(readlink -f /tmp/links-lab/ansible-soft)" = "/tmp/links-lab/releases/v2/data.txt" ] && \
  echo "  ✅ PROMOTE_VERIFIED" | tee -a "$JDIR/post-reboot-audit.txt"

# 5. Hard-link inode check after rebuild
[ "$(stat -c '%i' /tmp/links-lab/ansible-hard)" = "$(stat -c '%i' /tmp/links-lab/data.txt)" ] && \
  echo "  ✅ HARD_INODE_MATCH" | tee -a "$JDIR/post-reboot-audit.txt"

# 6. Idempotence proof after rebuild
ansible-playbook /root/rhcsa_journal/lab-09b/playbooks/links.yml \
  2>&1 | tee "$JDIR/post-reboot-idempotent.txt" | grep -E "PLAY RECAP|changed="

echo "exit was: $?"
```

### Human-readable breakdown

1. Snapshot pre-reboot state with mount points — explains **why** `/tmp/` evaporates and `/root/` survives.
2. Wipe `/tmp/links-lab/*` — hard links and symlinks in tmpfs are gone; this is expected (T41 lesson).
3. Confirm journal playbooks survived in `/root/rhcsa_journal/lab-09b/playbooks/`.
4. Re-run `links.yml` — recreates soft + hard links from declarative state.
5. Re-run `promote.yml` — atomically repoints symlink to v2 via `force: true`.
6. `readlink -f` proves the promote stuck — the **persistence guarantee** for symlink-based deployments is the playbook + atomic update, not the symlink inode in `/tmp/`.
7. Second `links.yml` run reports `changed=0` — idempotence holds even after full sandbox wipe.

### Reading it left to right

- `rm -rf /tmp/links-lab/*` — wipe contents; simulates tmpfs clear on reboot.
- `ansible-playbook .../links.yml` — declarative rebuild from journal — reproducible from cold storage.
- `readlink -f` — independent verification; must show v2 after promote re-run.
- `grep -E "PLAY RECAP|changed="` — extract audit-critical lines from playbook output.

### The story

Hard links don't survive wiping the directory that contained them — they're just names in a directory entry table. But the **playbook IS reproducible** from `/root/`. The atomic-update pattern (`ln -sfn` / Ansible `force: true` + changed `src:`) is how production teams guarantee symlink deployments survive release swaps. Skipping the reboot/wipe test on symlink-deployment tasks (T41) is how you discover a broken `src:` path only after the next maintenance window.

### Expected output

```text
═══ Pre-reboot state ═══
  /tmp  is on  /tmp
  /root  is on  /
  /root/rhcsa_journal  is on  /
/tmp/links-lab/releases/v2/data.txt
═══ SIMULATING REBOOT — wiping /tmp/links-lab/ ═══
  at 2026-05-28T20:15:00-04:00
0
  links gone — expected after wipe
  ✅ survived: /root/rhcsa_journal/lab-09b/playbooks/links.yml (35 lines)
  ✅ survived: /root/rhcsa_journal/lab-09b/playbooks/promote.yml (18 lines)
PLAY RECAP ***
localhost                  : ok=4 changed=2 unreachable=0 failed=0
PLAY RECAP ***
localhost                  : ok=2 changed=1 unreachable=0 failed=0
/tmp/links-lab/releases/v2/data.txt
  ✅ PROMOTE_VERIFIED
  ✅ HARD_INODE_MATCH
PLAY RECAP ***
localhost                  : ok=4 changed=0 unreachable=0 failed=0
exit was: 0
```

### Switches

| Token | Meaning |
|---|---|
| `stat -c '%m'` | Mount point containing the path |
| `rm -rf /tmp/links-lab/*` | Simulated reboot — wipe tmpfs sandbox |
| `readlink -f` | Post-rebuild verification of symlink target |
| `grep -E "PLAY RECAP\|changed="` | Extract idempotence proof lines |

### 🧠 Concept Card

|   | Concept | What it does |
|---|---|---|
|   | `/tmp` vs `/root/` storage | tmpfs evaporates; journal + playbooks on root partition persist |
|   | Playbook reproducibility | Wipe sandbox → re-run play → links recreated identically |
|   | Atomic promote persistence | `force: true` + `src:` change = deployment-grade symlink swap |
|   | Hard links in tmpfs | Gone after wipe — expected; not a persistence mechanism |
|   | Idempotence after rebuild | Second `links.yml` run → `changed=0` |
| 🪤 | **Trap Risk T41** | Skipping reboot/wipe test on symlink deployments — fix paths before production |

### 🔁 PERSISTENCE CHECK (this lab IS the persistence check)

| What was configured | Verification command | Why it matters |
|---|---|---|
| Post-reboot audit | `grep PROMOTE_VERIFIED /root/rhcsa_journal/lab-09c/task2/post-reboot-audit.txt` | Symlink promote verified after wipe |
| Idempotence after rebuild | `grep 'changed=0' /root/rhcsa_journal/lab-09c/task2/post-reboot-idempotent.txt` | Second run is no-op |
| Trilogy complete | `find /root/rhcsa_journal/lab-09{a,b,c} -name done.txt \| wc -l` | Should be `6` |

### Journal write — BEFORE cleanup

```bash
LAB=lab-09c
TASK=task2
JDIR="/root/rhcsa_journal/${LAB}/${TASK}"

cat > "$JDIR/done.txt" <<EOF
LAB:    ${LAB}
TASK:   ${TASK}
DATE:   $(date -Is)
USER:   $(whoami)@$(hostname)
STATUS: COMPLETE
promote_verified=$(grep -c PROMOTE_VERIFIED "$JDIR/post-reboot-audit.txt" 2>/dev/null || echo 0)
hard_inode_verified=$(grep -c HARD_INODE_MATCH "$JDIR/post-reboot-audit.txt" 2>/dev/null || echo 0)
EOF

cat > "$JDIR/notes.txt" <<EOF
TOPIC:    Simulated-reboot persistence — wipe /tmp/links-lab/, re-run Lab 09b playbooks
COMMANDS: rm -rf, ansible-playbook, readlink -f, stat -c '%m'
TRAPS:    T41 rehearsed (did NOT skip reboot/wipe test)
MISSED:   (fill in if any ⚠️ flags)
NEXT:     Lab 10 / Lab 11 trilogy — continue file-operations series
EOF

ls -la "$JDIR"
echo "── Trilogy state ──"
find /root/rhcsa_journal/lab-09{a,b,c} -name done.txt 2>/dev/null | sort
echo "exit was: $?"
```

### 🧹 Cleanup

```bash
rm -rf /tmp/links-lab
test -d /tmp/links-lab || echo "sandbox gone — clean exit"
echo "exit was: $?"
```

### Troubleshoot

| Symptom | Fix |
|---|---|
| ❌ MISSING playbook | Lab 09b Task 1 journal write not run — go back |
| `readlink -f` shows wrong path | Re-run `promote.yml` after `links.yml` |
| `changed=1` on idempotent re-run | Module call wrong — check for `command:` wrapper |
| Hard links don't match after rebuild | Expected if origin content differed — re-check `data.txt` seed |

> **STOP — paste `PROMOTE_VERIFIED` and trilogy `done.txt` list before completing Lab 09.**

---

## Lab 09c Checklist (2 tasks)

- [ ] Task 1 — Three-tool audit (`ls -l` + `stat` + `readlink -f` + `find -inum`) compared against expected baseline
- [ ] Task 2 — Simulated-reboot persistence proof — wipe `/tmp/links-lab/`, re-run Lab 09b playbooks, verify with `readlink -f`

---

## 🏁 Lab 09 Trilogy — completion check

After all three sub-labs are done, this command should show **six** `done.txt` files:

```bash
find /root/rhcsa_journal/lab-09{a,b,c} -name done.txt | sort
```

Expected output:

```text
/root/rhcsa_journal/lab-09a/task1/done.txt
/root/rhcsa_journal/lab-09a/task2/done.txt
/root/rhcsa_journal/lab-09b/task1/done.txt
/root/rhcsa_journal/lab-09b/task2/done.txt
/root/rhcsa_journal/lab-09c/task1/done.txt
/root/rhcsa_journal/lab-09c/task2/done.txt
```

If any are missing, that sub-lab is incomplete.

---

## 🔗 Related Labs in the Trilogy

| Lab | Connection |
|---|---|
| **Lab 09a** — RHCSA hand-typed links | The imperative form being audited |
| **Lab 09b** — Managing Links via Ansible | The declarative form being audited and re-run after wipe |
| Lab 08 — Copying Files (`cp`, `cp -a`) | Prerequisite for Lab 09a |
| Lab 11c — Verifying File Removal | Mirror audit pattern applied to `state=absent` |

---

## 👤 Author

**Kelvin R. Tobias**
[kelvinintech.com](https://kelvinintech.com) · [GitHub](https://github.com/kelvintechnical) · [LinkedIn](https://www.linkedin.com/in/kelvin-r-tobias-211949219)
