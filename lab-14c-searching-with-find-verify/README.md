# Lab 14c: Searching with `find` (Verify) — audit declared vs live results

- **Series:** linux-ops-mastery — File Operations & Shell Fundamentals
- **Trilogy:** `14a` (RHCSA) → `14b` (Ansible) → `14c` (Verify)
- **Prerequisite:** Labs 14a and 14b complete
- **Time Estimate:** 20–30 minutes
- **Tasks:** 2
- **Practice Directory (rotation #14):** `/etc`

---

## Objective

Prove that `find` output is reproducible: capture a declared baseline, perturb the filesystem, re-run `find`, diff results, and restore. Simulates "did someone add a rogue config file?" auditing.

---

## Lab-Wide Setup

```bash
sudo -i
mkdir -p /root/rhcsa_journal/lab-14c/{task1,task2}
cd /root/rhcsa_journal/lab-14c
echo "exit was: $?"
```

---

## Task 1 — Declare baseline + integrity check on `/etc` sample

**Practice directory:** `/etc`

### Warm-Up

```bash
find /etc -maxdepth 2 -type f -name 'passwd' 2>/dev/null
test -f /etc/passwd && echo "baseline anchor OK"
set -o pipefail
echo "Warm-up at $(date -Is)"
```

### Purpose

Run the Lab 14a capstone predicate set, save sorted baseline to `/root/find-baseline.txt`, checksum it, and verify a second immediate run produces zero diff (idempotence of read-only find).

### Main command block

```bash
BASELINE=/root/find-baseline.txt
CHECKSUM=/root/find-baseline.sha256

find /etc \
  -type f -name '*.conf' -user root -mtime -90 -size +100c \
  2>/dev/null | sort > "$BASELINE"

sha256sum "$BASELINE" | tee "$CHECKSUM" \
  2>&1 | tee /root/rhcsa_journal/lab-14c/task1/op.txt

# Immediate re-run — must be identical
find /etc \
  -type f -name '*.conf' -user root -mtime -90 -size +100c \
  2>/dev/null | sort \
  | diff -u "$BASELINE" - && echo "IDEMPOTENT: zero drift"

wc -l "$BASELINE"
echo "exit was: $?"
```

### WEAVE TRACE

| Warm-up | Role |
|---|---|
| `find /etc ... passwd` | Confirms find can read `/etc` |
| `test -f /etc/passwd` | Anchor file exists |
| `sort` + `diff -u` | Declared vs live comparison primitive |
| `sha256sum` | Tamper-evident baseline |
| `set -o pipefail` | Pipe failures surface |

### Journal write

```bash
JDIR=/root/rhcsa_journal/lab-14c/task1
mkdir -p "$JDIR"
cp /root/rhcsa_journal/lab-14c/task1/op.txt "$JDIR/evidence.txt" 2>/dev/null || true
cp "$BASELINE" "$JDIR/" 2>/dev/null || true
cp "$CHECKSUM" "$JDIR/" 2>/dev/null || true

cat > "$JDIR/done.txt" <<EOF
LAB: lab-14c  TASK: task1  DATE: $(date -Is)  STATUS: COMPLETE
EOF
```

> **STOP — paste `IDEMPOTENT` line and `wc -l` before Task 2.**

---

## Task 2 — Inject drift, detect with `diff`, restore

**Practice directory:** `/etc` (injection under `/etc/find-lab-probe.d`)

### Purpose

Create a fake `.conf` owned by root, confirm it appears in a fresh find, diff against baseline, remove probe, confirm baseline restored.

### Main command block

```bash
PROBE=/etc/find-lab-probe.d
mkdir -p "$PROBE"
install -o root -g root -m 0644 /dev/null "$PROBE/injected.conf"
echo "# probe $(date -Is)" > "$PROBE/injected.conf"

find /etc \
  -type f -name '*.conf' -user root -mtime -90 -size +100c \
  2>/dev/null | sort > /root/find-after-inject.txt

diff -u /root/find-baseline.txt /root/find-after-inject.txt \
  2>&1 | tee /root/rhcsa_journal/lab-14c/task2/op.txt

grep -F injected.conf /root/find-after-inject.txt && echo "DETECTED: probe in find output"

# Restore
rm -rf "$PROBE"
find /etc \
  -type f -name '*.conf' -user root -mtime -90 -size +100c \
  2>/dev/null | sort \
  | diff -u /root/find-baseline.txt - && echo "RESTORED: matches baseline"

echo "exit was: $?"
```

### PERSISTENCE CHECK

| Check | Command |
|---|---|
| Probe removed | `test ! -d /etc/find-lab-probe.d` |
| Baseline match | `diff -q /root/find-baseline.txt <(find ... \| sort)` |

### Cleanup

```bash
rm -f /root/find-baseline.txt /root/find-baseline.sha256 \
      /root/find-after-inject.txt
rm -rf /etc/find-lab-probe.d
```

### Journal write

```bash
JDIR=/root/rhcsa_journal/lab-14c/task2
mkdir -p "$JDIR"
cp /root/rhcsa_journal/lab-14c/task2/op.txt "$JDIR/evidence.txt" 2>/dev/null || true

cat > "$JDIR/done.txt" <<EOF
LAB: lab-14c  TASK: task2  DATE: $(date -Is)  STATUS: COMPLETE
EOF
```

---

## Lab 14c Checklist

- [ ] Task 1 — Baseline + sha256 + idempotent re-run
- [ ] Task 2 — Inject → diff detects → restore → zero diff

---

## Related Labs

| Lab | Connection |
|---|---|
| Lab 15c | `locate` verify uses index staleness instead of live walk |

---

## Author

**Kelvin R. Tobias** — [kelvinintech.com](https://kelvinintech.com)
