# Lab 21a: Monitoring Live Log Files (RHCSA) — `tail`, `tail -f`, `tail -F`

**Series:** linux-ops-mastery — Text Processing & Filters · **Lab 21a of the Novice → RHCA path**  
**Certifications covered:** RHCSA EX200 (watching logs in real time), SRE/DevOps (live incident triage)  
**Prerequisite:** [Lab 20c](../lab-20c-less-more-scrolling-verify/) completed  
**Time Estimate:** 20–30 minutes  
**Difficulty:** Beginner

---

## 🎯 Today's Focus Coverage

> Stay on-subject via the ANCHOR rows; expand vocabulary via the NEW rows. Every row is exercised by a STEP below.

**⚓ Anchor — already learned (on-topic reuse)**

| # | Command / switch | Covered by |
|---|---|---|
| A1 | reading file ends (`less +F`) | _Task 1 · Step 1_ |
| A2 | `grep` filtering | _Task 2 · Step 2_ |

**🆕 NEW this lab — introduced for the first time** (minimum 3)

| # | Command / switch | First taught in | Covered by |
|---|---|---|---|
| N1 | `tail -n N` | Task 1 · Step 1 | _Task 1 · Step 1_ |
| N2 | `tail -f` (follow) | Task 1 · Step 2 | _Task 1 · Step 2_ |
| N3 | `tail -F` (follow + reopen) | Task 2 · Step 1 | _Task 2 · Step 1_ |
| N4 | `tail -f | grep` live filter | Task 2 · Step 2 | _Task 2 · Step 2_ |

---

## 🎯 Objective

Watch logs as they happen. You will show the last N lines with `tail -n`, follow a growing file live with `tail -f`, survive log rotation with `tail -F`, and filter a live stream through `grep`. By the end you can sit on a log during an incident and see new events the instant they're written.

> **Note:** `tail -f`/`-F` run until you stop them. Press **Ctrl-C** to return to the prompt.

---

## 🧠 Concept

`tail` prints the *end* of a file — the newest content. `tail -n 20` shows the last 20 lines. `tail -f` ("follow") keeps the file open and streams new lines as they're appended — the core live-monitoring tool. `tail -F` is `-f` plus *reopen on rotation*: when logrotate renames the file and starts a fresh one, `-F` reattaches to the new file while plain `-f` would keep watching the now-stale old inode. Pipe a follow into `grep` (`tail -f file | grep ERROR`) to watch only the events you care about in real time.

```
tail -n 20 app.log     → last 20 lines
tail -f app.log        → stream new lines (Ctrl-C to stop)
tail -F app.log        → follow across log rotation
tail -f app.log | grep --line-buffered ERROR → live error feed
```

> **Why this matters:** During an incident you watch the log live. `tail -f` is muscle memory; `-F` saves you when rotation silently cuts off `-f`; piping to `grep` keeps the signal visible in a noisy stream.

---

## 📚 Command Reference

| Command | Purpose | Notes |
|---|---|---|
| `tail -n N` | Last N lines | default is 10 |
| `tail -f` | Follow appends | Ctrl-C to stop |
| `tail -F` | Follow + reopen | survives rotation |
| `tail -f | grep` | Live filter | add `--line-buffered` |
| `tail file1 file2` | Multiple files | prints `==> name <==` headers |

---

## 🧰 LAB-WIDE SETUP

**In plain English:** Build a sandbox with a log we can append to.

> Run this block **once** before Task 1. It defines a single sandbox root
> (`LAB_ROOT`) that every file in this lab lives under, so the Teardown
> section can wipe it in one safe command.

```bash
export LAB_ROOT=/tmp/lab-21
mkdir -p "$LAB_ROOT"
cd "$LAB_ROOT"
seq 1 30 | sed 's/^/event /' > app.log
wc -l app.log
echo "exit was: $?"
```

**Expected output:**

```
30 app.log
exit was: 0
```

---

## TASK 1 of 2 — Last lines and live follow

**In plain English:** We view the tail of the log, then follow it as it grows.

---

### Step 1 of 2 — Show the last N lines

**In plain English:** We print the last 5 lines of the log.

```bash
cd "$LAB_ROOT"
tail -n 5 app.log
echo "exit was: $?"
```

**Expected output:**

```
event 26
event 27
event 28
event 29
event 30
exit was: 0
```

**Line-by-line breakdown:**

- `tail -n 5 app.log` → Print only the last 5 lines — the newest events.

**New words in this step:**

- **`tail -n N`** — print the last N lines of a file (default 10).

---

### Step 2 of 2 — Follow the file with `tail -f`

**In plain English:** We follow the log while a background writer appends events, watching them appear live.

```bash
cd "$LAB_ROOT"
( for i in $(seq 31 35); do echo "event $i"; sleep 1; done >> app.log ) &
tail -f app.log
# New lines appear once per second. Press Ctrl-C after event 35 to stop.
```

**Expected output (on screen):**

```
event 26
...
event 30
event 31
event 32
event 33
event 34
event 35
^C
```

**Line-by-line breakdown:**

- `( ... ) &` → Background writer appending one event per second.
- `tail -f app.log` → Stream new lines as they're written; Ctrl-C ends the follow.

**New words in this step:**

- **`tail -f`** — follow a file, printing new lines as they are appended.

---

### Concept card (Task 1)

| Concept | What it does | Exam trap |
|---|---|---|
| `tail -n` | last N lines | default is 10, not all |
| `tail -f` | live follow | runs until Ctrl-C |
| newest first? | no — chronological | tail shows end, in order |

---

### Troubleshoot (Task 1)

| Symptom | Likely cause | Fix |
|---|---|---|
| `-f` shows nothing new | Nothing writing | Confirm a writer is active |
| Can't get prompt back | Still following | Press Ctrl-C |

---

## TASK 2 of 2 — Survive rotation and filter live

**In plain English:** We use `-F` to survive a rotation, then filter a live stream with `grep`.

---

### Step 1 of 2 — Follow across rotation with `tail -F`

**In plain English:** We follow with `-F`, simulate logrotate by renaming the file and creating a fresh one, and watch `-F` reattach.

```bash
cd "$LAB_ROOT"
tail -F app.log &
TAILPID=$!
sleep 1
mv app.log app.log.1                 # simulate logrotate
echo "event after rotation" > app.log
sleep 1
kill "$TAILPID"
echo "exit was: $?"
```

**Expected output (on screen):**

```
event 26
...
event 35
tail: 'app.log' has become inaccessible: No such file or directory
tail: 'app.log' has appeared;  following new file
event after rotation
exit was: 0
```

**Line-by-line breakdown:**

- `tail -F app.log &` → Follow with reopen-on-rotation, in the background.
- `mv app.log app.log.1; echo ... > app.log` → Simulate logrotate: rename old, create new.
- `-F` reattaches → It detects the new file and continues; plain `-f` would have stayed on the old inode.

**New words in this step:**

- **`tail -F`** — follow *and* reopen the file when it's rotated/recreated.

---

### Step 2 of 2 — Filter a live stream with `grep`

**In plain English:** We follow the log and show only lines containing ERROR, live.

```bash
cd "$LAB_ROOT"
( for i in 1 2 3; do echo "info ok $i"; echo "ERROR fault $i"; sleep 1; done >> app.log ) &
tail -f app.log | grep --line-buffered ERROR
# Only ERROR lines appear. Press Ctrl-C after three to stop.
```

**Expected output (on screen):**

```
ERROR fault 1
ERROR fault 2
ERROR fault 3
^C
```

**Line-by-line breakdown:**

- `tail -f app.log | grep --line-buffered ERROR` → Stream the file but show only matching lines.
- `--line-buffered` → Flush each matching line immediately so the live feed isn't held in a buffer.

**New words in this step:**

- **`--line-buffered`** — make `grep` emit each match instantly in a pipe.

---

### Concept card (Task 2)

| Concept | What it does | Exam trap |
|---|---|---|
| `tail -F` | follow + reopen | use for rotated logs |
| `-f` vs `-F` | inode vs name | `-f` misses rotation |
| live `grep` | filter the stream | add `--line-buffered` |

---

### Troubleshoot (Task 2)

| Symptom | Likely cause | Fix |
|---|---|---|
| `-f` stops after rotation | Followed old inode | Use `-F` |
| Filtered feed lags | Buffering | Add `--line-buffered` |

---

## ✅ Lab Checklist

- [ ] Task 1 · Step 1 — Show the last N lines
- [ ] Task 1 · Step 2 — Follow the file with `tail -f`
- [ ] Task 2 · Step 1 — Follow across rotation with `tail -F`
- [ ] Task 2 · Step 2 — Filter a live stream with `grep`
- [ ] Every 🎯 Focus Coverage row (Anchor + NEW) mapped to a step
- [ ] 🧹 Teardown run — sandbox + any system state removed

---

## 🧹 Teardown

**In plain English:** Delete everything this lab created so the box is clean for the next run.

> Run this after you've verified the lab. `lab_teardown.sh` safely removes the single sandbox root — it refuses to touch `/`, `$HOME`, or any protected path. This lab changed **no** system state. Make sure no `tail -f`/`-F` is still running (Ctrl-C / `kill` any leftover).

```bash
cd /tmp
bash lab_teardown.sh "$LAB_ROOT"     # = /tmp/lab-21
```

**Expected output:**

```
✅ Removed /tmp/lab-21 — lab workspace is clean.
```

---

## ⚠️ Common Pitfalls

| Mistake | Symptom | Fix |
|---|---|---|
| `-f` on rotated logs | Feed silently stops | Use `-F` |
| Forgetting Ctrl-C | Terminal "hangs" | It's following; Ctrl-C |
| Unbuffered live grep | Delayed matches | `--line-buffered` |

---

## 📌 Exam Strategy

`tail -f` is the live-log reflex; reach for `-F` whenever rotation is possible, and pipe to `grep --line-buffered` to isolate the signal. For systemd services, `journalctl -f` is the same idea.

- `-F` over `-f` for anything logrotate touches.
- `--line-buffered` keeps piped live feeds responsive.
- `journalctl -fu SERVICE` follows a unit's log live.

---

## 🔗 Related Labs

- [Lab 21b — Monitoring Live Logs (Ansible)](../lab-21b-tail-f-live-logs-ansible/) — capturing recent log lines in plays
- [Lab 21c — Monitoring Live Logs (Verify)](../lab-21c-tail-f-live-logs-verify/) — prove the right tail was captured
- [Lab 20a — Scrolling Large Files (RHCSA)](../lab-20a-less-more-scrolling-rhcsa/) — `less +F` follow mode

---

## 👤 Author

**Kelvin R. Tobias**  
[kelvinintech.com](https://kelvinintech.com) · [GitHub](https://github.com/kelvintechnical) · [LinkedIn](https://www.linkedin.com/in/kelvin-r-tobias-211949219)
