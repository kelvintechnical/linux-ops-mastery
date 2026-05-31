# Lab 15c: Instant File Searching with `locate` (Verify) — index health + prune audit

- **Series:** linux-ops-mastery — File Operations & Shell Fundamentals
- **Trilogy:** `15a` → `15b` → `15c`
- **Prerequisite:** Labs 15a and 15b complete
- **Time Estimate:** 20–30 minutes
- **Tasks:** 2
- **Practice Directory (rotation #15):** `/srv/scratch`

---

## Objective

Audit the locate index: confirm `mlocate` package and timer, verify `PRUNEPATHS` contains `/srv/scratch`, run a controlled inject/refresh cycle, and restore a known-good state.

---

## Lab-Wide Setup

```bash
sudo -i
mkdir -p /root/rhcsa_journal/lab-15c/{task1,task2}
```

---

## Task 1 — Four-property audit (package, db, config, timer)

**Practice directory:** `/srv/scratch` (config) · `/var/lib/mlocate` (index)

### Warm-Up

```bash
rpm -q mlocate 2>/dev/null || echo "mlocate not installed"
test -f /var/lib/mlocate/mlocate.db && echo "db OK"
grep '^PRUNEPATHS' /etc/updatedb.conf | head -n 1
systemctl is-enabled mlocate.timer 2>/dev/null || ls /etc/cron.daily/mlocate 2>/dev/null
```

### Main command block

```bash
AUDIT=/root/rhcsa_journal/lab-15c/task1/audit.txt
: > "$AUDIT"

{
  echo "=== 1. Package ==="
  rpm -q mlocate || echo "FAIL: mlocate missing"

  echo "=== 2. Database ==="
  ls -lh /var/lib/mlocate/mlocate.db 2>/dev/null || echo "FAIL: no db"
  locate -S 2>/dev/null | head -n 6

  echo "=== 3. PRUNEPATHS includes /srv/scratch ==="
  grep '^PRUNEPATHS' /etc/updatedb.conf | grep -q '/srv/scratch' \
    && echo "PASS: /srv/scratch pruned" \
    || echo "WARN: add /srv/scratch for Lab 15 capstone"

  echo "=== 4. Refresh mechanism ==="
  systemctl is-enabled mlocate.timer 2>/dev/null \
    || test -x /etc/cron.daily/mlocate && echo "cron.daily present"
} 2>&1 | tee "$AUDIT"

echo "exit was: $?"
```

### WEAVE TRACE

| Warm-up | Role |
|---|---|
| `rpm -q` | Package presence |
| `test -f` db | Index file exists |
| `grep PRUNEPATHS` | Config matches lab intent |
| `systemctl` / cron | Automated refresh path |
| `tee` audit | Single evidence artifact |

### Journal

```bash
JDIR=/root/rhcsa_journal/lab-15c/task1
cp "$AUDIT" "$JDIR/evidence.txt" 2>/dev/null || true
cat > "$JDIR/done.txt" <<EOF
LAB: lab-15c  TASK: task1  DATE: $(date -Is)  STATUS: COMPLETE
EOF
```

---

## Task 2 — Simulated "index stale after deploy" + rebuild

**Practice directory:** `/srv/scratch`

### Purpose

Create a uniquely named file under `/tmp`, confirm `locate` misses it (T15-A), run `updatedb`, confirm hit, then delete file and show phantom with `locate` vs `locate -e` (T15-B).

### Main command block

```bash
UNIQ="deploy-marker-$(date +%s).txt"
echo "deploy test" > "/tmp/$UNIQ"

BEFORE=$(locate "$UNIQ" 2>/dev/null | wc -l)
echo "hits before updatedb: $BEFORE" | tee /root/rhcsa_journal/lab-15c/task2/op.txt

updatedb
AFTER=$(locate "$UNIQ" 2>/dev/null | wc -l)
echo "hits after updatedb: $AFTER" | tee -a /root/rhcsa_journal/lab-15c/task2/op.txt
locate "$UNIQ" | tee -a /root/rhcsa_journal/lab-15c/task2/op.txt

rm -f "/tmp/$UNIQ"
PHANTOM=$(locate "$UNIQ" 2>/dev/null | wc -l)
EXISTING=$(locate -e "$UNIQ" 2>/dev/null | wc -l)
echo "phantom hits (no -e): $PHANTOM" | tee -a /root/rhcsa_journal/lab-15c/task2/op.txt
echo "existing-only hits (-e): $EXISTING" | tee -a /root/rhcsa_journal/lab-15c/task2/op.txt

test "$BEFORE" -eq 0 -a "$AFTER" -ge 1 -a "$EXISTING" -eq 0 \
  && echo "VERIFY: staleness + phantom behavior demonstrated"

updatedb
echo "exit was: $?"
```

### PERSISTENCE CHECK

| Phase | Expected |
|---|---|
| Before `updatedb` | 0 hits (T15-A) |
| After `updatedb` | ≥1 hit |
| After delete, `locate` | May still show phantom |
| After delete, `locate -e` | 0 hits (T15-B) |

### Journal

```bash
JDIR=/root/rhcsa_journal/lab-15c/task2
cp /root/rhcsa_journal/lab-15c/task2/op.txt "$JDIR/evidence.txt" 2>/dev/null || true
cat > "$JDIR/done.txt" <<EOF
LAB: lab-15c  TASK: task2  DATE: $(date -Is)  STATUS: COMPLETE
EOF
```

---

## Lab 15c Checklist

- [ ] Task 1 — Four-property audit (package, db, PRUNEPATHS, timer/cron)
- [ ] Task 2 — Staleness + phantom (`locate` vs `locate -e`)

---

## Author

**Kelvin R. Tobias** — [kelvinintech.com](https://kelvinintech.com)
