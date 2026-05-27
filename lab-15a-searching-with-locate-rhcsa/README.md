# Lab 15a: Instant File Searching with `locate` (RHCSA) — index, `updatedb`, PRUNEPATHS

- **Series:** linux-ops-mastery — File Operations & Shell Fundamentals
- **Trilogy:** `15a` (RHCSA) → `15b` (Ansible) → `15c` (Verify)
- **Prerequisite:** Lab 14 trilogy complete (`find` live walk)
- **Time Estimate:** 30–40 minutes
- **Tasks:** 2 (Task 1 = install + `updatedb` + queries, Task 2 = staleness + `/etc/updatedb.conf` capstone)
- **Practice Directory (rotation #15):** `/srv/scratch`
- **Traps rehearsed:** **T15-A** (searching for a file you just created without running `updatedb`) · **T15-B** (expecting `locate` to respect live deletes — use `locate -e` or `find`)

> **This lab's practice directory is: `/srv/scratch`** — excluded from the index in Task 2 via `PRUNEPATHS`.

---

## LAB HEADER BLOCK

```bash
echo "🖥️  ENV:   ${ENV:-DECLARE_ME}"
echo "💿  DISK:  $(lsblk 2>/dev/null | awk '$NF=="disk"{print "/dev/"$1}' | paste -sd, -)"
echo "🌐  NIC:   $(ip -o addr show 2>/dev/null | awk '$2!="lo"{print $2}' | paste -sd, -)"
echo "🔐  SE:    $(getenforce 2>/dev/null || echo n/a)"
echo "📦  OS:    $(cat /etc/redhat-release 2>/dev/null || grep PRETTY_NAME /etc/os-release)"
echo "🕒  TIME:  $(date -Is)"
echo "👤  USER:  $(whoami)@$(hostname)"
echo "⚠️  TRAP REMINDERS THIS LAB: T15-A T15-B"
echo "📁  PRACTICE DIR: /srv/scratch"
echo ""
test -d /srv/scratch && echo "scratch exists" || echo "will create /srv/scratch in setup"
```

---

## Objective

Use `locate` for millisecond "where is file X?" answers. Install `mlocate`, refresh with `updatedb`, query with flags, and tune `PRUNEPATHS` so `/srv/scratch` never enters the index.

---

## Concept: `locate` Trades Freshness for Speed

```
   Filesystem  ──updatedb──►  /var/lib/mlocate/mlocate.db  ──locate──►  instant paths
```

| Tool | When to use |
|---|---|
| `locate` | "Does a path containing X exist anywhere?" — fast, maybe stale |
| `find` (Lab 14) | "What matches these predicates right now?" — live, slower |
| `updatedb` | Refresh index after bulk changes or before trusting `locate` |

---

## Reference

| Task | Command |
|---|---|
| Install | `dnf install -y mlocate` |
| Rebuild index | `sudo updatedb` |
| Substring search | `locate sshd_config` |
| Case-insensitive | `locate -i PATTERN` |
| Count | `locate -c PATTERN` |
| Limit | `locate -l 10 PATTERN` |
| Regex | `locate -r '/sshd_config$'` |
| Existing only | `locate -e PATTERN` (T15-B) |
| Stats | `locate -S` |
| Exclude path | Add to `PRUNEPATHS` in `/etc/updatedb.conf`, then `updatedb` |

---

## Lab-Wide Setup

```bash
sudo -i
mkdir -p /srv/scratch/locate-lab/hidden
mkdir -p /tmp/locate-lab

cat > /tmp/locate-lab/THIS_DIRECTORY.txt <<'EOF'
/srv/scratch — Ephemeral high-churn data (models, caches, build artifacts)

Operations teams often exclude /srv/scratch from locate indexes because
millions of short-lived files bloat the database and slow updatedb.
PRUNEPATHS in /etc/updatedb.conf is the knob.
EOF

cat /tmp/locate-lab/THIS_DIRECTORY.txt
echo "exit was: $?"
```

---

## Task 1 — Install `mlocate`, `updatedb`, and query flags

**Practice directory:** `/etc` (queries) + `/srv/scratch` (fixture path referenced in warm-up)

### Warm-Up

```bash
find /etc -maxdepth 1 -name 'passwd' 2>/dev/null
wc -l /etc/passwd
test -d /srv/scratch && echo "/srv/scratch ready"
dnf list installed mlocate 2>/dev/null | head -n 2
echo "Warm-up at $(date -Is)"
```

### Purpose

Install `mlocate` if missing, run `updatedb`, inspect `/var/lib/mlocate/mlocate.db`, practice `-i`, `-c`, `-l`, `-r`, and `-S`.

### WEAVE TRACE

| Warm-up | Role in Task 1 |
|---|---|
| `find /etc ... passwd` | Live anchor — compare speed mindset vs locate |
| `wc -l /etc/passwd` | Line-count habit from prior labs |
| `test -d /srv/scratch` | Task 2 will prune this tree |
| `dnf list installed` | Idempotent install check |
| `2>&1 \| tee` | Evidence file |
| `time updatedb` | Shows index build cost (seconds) vs query cost (ms) |

### Main command block

```bash
mkdir -p /tmp/locate-lab/task1
cd /tmp/locate-lab/task1

dnf list installed mlocate 2>/dev/null || dnf install -y mlocate
which locate updatedb                                       2>&1 | tee op.txt

echo "── building index (timed) ──"                          | tee -a op.txt
/usr/bin/time -f 'updatedb elapsed: %e sec' updatedb        2>&1 | tee -a op.txt

ls -lh /var/lib/mlocate/mlocate.db                            2>&1 | tee -a op.txt
locate -S                                                     2>&1 | tee -a op.txt

echo "── queries on /etc-related names ──"                   | tee -a op.txt
locate sshd_config | head -n 3                                2>&1 | tee -a op.txt
locate -i SSHD_CONFIG | head -n 3                             2>&1 | tee -a op.txt
locate -c '\.conf$' 2>/dev/null || locate -c '.conf'          2>&1 | tee -a op.txt
locate -l 5 -r '/sshd_config$'                                2>&1 | tee -a op.txt

echo "exit was: $?"
```

### Expected output (excerpt)

```text
/usr/bin/locate
/usr/bin/updatedb
updatedb elapsed: 12.34 sec
-rw-r----- 1 root mlocate 45M ... /var/lib/mlocate/mlocate.db
Database /var/lib/mlocate/mlocate.db:
...
/etc/ssh/sshd_config
...
exit was: 0
```

### Concept Card

| Concept | What it does |
|---|---|
| Index file | `/var/lib/mlocate/mlocate.db` — mmap'd for speed |
| Staleness | New files invisible until next `updatedb` (T15-A) |
| `-e` | Filters phantom deleted paths (T15-B) |
| `locate -S` | Size, paths, last update — health check |

### Journal write

```bash
LAB=lab-15a
TASK=task1
JDIR="/root/rhcsa_journal/${LAB}/${TASK}"
mkdir -p "$JDIR"
cp /tmp/locate-lab/task1/op.txt "$JDIR/evidence.txt"

cat > "$JDIR/done.txt" <<EOF
LAB: ${LAB}  TASK: ${TASK}  DATE: $(date -Is)  STATUS: COMPLETE
EOF

cat > "$JDIR/notes.txt" <<EOF
TOPIC: mlocate install, updatedb, locate flags
TRAPS: T15-A (staleness) introduced — fixed in Task 2 drill
NEXT: task2 — PRUNEPATHS + pem capstone
EOF
```

> **STOP — paste `locate -S` summary before Task 2.**

---

## Task 2 — Staleness drill + PRUNEPATHS capstone (`/srv/scratch`)

**Practice directory:** `/srv/scratch`

### Warm-Up

```bash
grep -E '^PRUNEPATHS' /etc/updatedb.conf 2>/dev/null | head -n 1
locate -c scratch 2>/dev/null || echo "count may be 0 before fixtures"
test -d /srv/scratch/locate-lab/hidden && echo "hidden dir OK"
echo "Warm-up at $(date -Is)"
```

### Purpose

Demonstrate T15-A (file invisible until `updatedb`), configure `PRUNEPATHS` to exclude `/srv/scratch`, place probe `*.pem` files in `/etc` and `/srv/scratch`, prove `locate '*.pem'` hits `/etc` but not scratch.

### WEAVE TRACE

| Warm-up | Role in Task 2 |
|---|---|
| `grep PRUNEPATHS` | Shows current config before edit |
| `locate -c scratch` | Baseline index awareness |
| `test -d .../hidden` | Probe directory guard |
| `cp` fixtures | Creates searchable paths |
| `updatedb` | Required after config + file changes |
| `diff` / `grep -v` | Proves exclusion worked |

### Main command block

```bash
mkdir -p /tmp/locate-lab/task2
PROBE_ETC=/etc/locate-lab-probe
PROBE_SCR=/srv/scratch/locate-lab/hidden

# Staleness drill (T15-A)
echo "probe-before-update" > /tmp/locate-lab/task2/brand-new.txt
locate brand-new.txt 2>/dev/null | wc -l | awk '{print "before updatedb: "$1" hits"}' \
                                                              | tee /tmp/locate-lab/task2/op.txt
updatedb
locate brand-new.txt | tee -a /tmp/locate-lab/task2/op.txt

# PRUNEPATHS — add /srv/scratch if not present
cp -a /etc/updatedb.conf /etc/updatedb.conf.bak-lab15
grep -q '/srv/scratch' /etc/updatedb.conf || \
  sed -i 's|^PRUNEPATHS=|PRUNEPATHS="/srv/scratch" |' /etc/updatedb.conf

grep '^PRUNEPATHS' /etc/updatedb.conf | tee -a /tmp/locate-lab/task2/op.txt

# Fixtures
mkdir -p "$PROBE_ETC" "$PROBE_SCR"
echo "etc probe"  > "$PROBE_ETC/test-capstone.pem"
echo "scratch probe" > "$PROBE_SCR/secret.pem"
updatedb

echo "── locate *.pem (should include /etc, exclude /srv/scratch) ──" \
                                                              | tee -a /tmp/locate-lab/task2/op.txt
locate '*.pem' 2>/dev/null | tee /tmp/locate-lab/task2/pem-hits.txt \
                                                              | tee -a /tmp/locate-lab/task2/op.txt

grep -F "$PROBE_ETC" /tmp/locate-lab/task2/pem-hits.txt && echo "HIT: /etc probe indexed"
grep -F "$PROBE_SCR" /tmp/locate-lab/task2/pem-hits.txt && echo "FAIL: scratch should be pruned" \
  || echo "PASS: /srv/scratch excluded from index"

echo "exit was: $?"
```

### Restore config

```bash
mv -f /etc/updatedb.conf.bak-lab15 /etc/updatedb.conf
updatedb
rm -rf "$PROBE_ETC" /srv/scratch/locate-lab "$PROBE_SCR" 2>/dev/null
rm -f /tmp/locate-lab/task2/brand-new.txt
```

### PERSISTENCE CHECK

| Check | Command |
|---|---|
| `/etc` hit | `grep locate-lab-probe pem-hits.txt` |
| Scratch miss | `! grep /srv/scratch pem-hits.txt` |
| Config restored | `diff -q /etc/updatedb.conf.bak-lab15 /etc/updatedb.conf` (after restore) |

### Journal write

```bash
LAB=lab-15a
TASK=task2
JDIR="/root/rhcsa_journal/${LAB}/${TASK}"
mkdir -p "$JDIR"
cp /tmp/locate-lab/task2/op.txt "$JDIR/evidence.txt"
cp /tmp/locate-lab/task2/pem-hits.txt "$JDIR/" 2>/dev/null || true

cat > "$JDIR/done.txt" <<EOF
LAB: ${LAB}  TASK: ${TASK}  DATE: $(date -Is)  STATUS: COMPLETE
EOF
```

### Cleanup

```bash
rm -rf /tmp/locate-lab
```

> **STOP — paste PASS line for scratch exclusion before Lab 15b.**

---

## Lab 15a Checklist

- [ ] Task 1 — `mlocate` + `updatedb` + flag queries + `locate -S`
- [ ] Task 2 — Staleness drill + PRUNEPATHS capstone on `/srv/scratch`

---

## Related Labs

| Lab | Connection |
|---|---|
| Lab 14a | `find` — live alternative when index is wrong |
| Lab 15b | Ansible manages `updatedb.conf` + `updatedb` |
| Lab 15c | Verify prune + index refresh |

---

## Author

**Kelvin R. Tobias** — [kelvinintech.com](https://kelvinintech.com)
