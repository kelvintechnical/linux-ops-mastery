# Lab: Filter systemd Journals by Priority — `journalctl -p`, Ranges, Numeric and Symbolic Forms

- **Series:** linux-ops-mastery — RHCSA Log Management
- **Subjects covered:** the 8-level syslog priority model (emerg=0 → debug=7), `journalctl -p PRIORITY` as a "this level **and worse**" floor filter, the range form `-p N..M` (and `-p emerg..err`) for inclusive bands, exact-priority filtering with `-p N..N`, numeric vs symbolic priority forms, combining `-p` with `-u`, `-b`, `--since`/`--until`, `-o json` output, building per-priority counts, and the canonical RHCSA pattern "show me all errors-or-worse on this boot, grouped by unit"
- **Career arcs covered:** RHCSA (EX200 — "list emerg and alert messages on this host"), RHCE (Ansible health gate), SRE (alerting thresholds), DevOps (CI failure triage), AI / MLOps (NCCL warning vs error band differentiation)
- **Prerequisite:** Labs 101 and 102 (`journalctl` basics + persistence)
- **Time Estimate:** 30 to 45 minutes
- **Difficulty arc:** Tasks 1–2 baseline + priority model · Tasks 3–4 floor filter and range filter · Task 5 exact-priority form · Tasks 6–7 combine with unit / time / boot · Task 8 inject synthetic priorities · Task 9 per-priority counts and ranking · Task 10 capstone severity-by-unit report + cleanup

---

## Objective

Stop scrolling through a sea of `info` messages looking for the one `crit`. By the end of this lab you can filter the systemd journal to any priority floor (e.g. *"errors and worse"*), any inclusive band (*"warning through error only"*), or any exact priority (*"only `alert`, nothing else"*) — in either symbolic or numeric form. You will also know how to inject synthetic priority messages for testing, count entries per priority, and build a "severity by unit" matrix for a fleet review.

The capstone is the engineer-realistic prompt: *"On this RHEL 9 host, group every error-or-worse log entry on the current boot by systemd unit, write a sorted ranking to disk, and produce a one-paragraph health summary."*

> **Lab safety note:** Read-only. The only write is into `/root/journal-prio-lab/` and via `logger -p` to inject test events into the journal.

---

## Concept: `-p PRIORITY` Is "Floor," Not "Equal"

Every journal entry carries a `PRIORITY` field, an integer 0–7 mirroring the syslog model from RFC 5424:

| # | Name | Meaning |
|---|---|---|
| 0 | `emerg` | System is unusable |
| 1 | `alert` | Action must be taken immediately |
| 2 | `crit` | Critical conditions |
| 3 | `err` | Error conditions |
| 4 | `warning` | Warning conditions |
| 5 | `notice` | Normal but significant |
| 6 | `info` | Informational |
| 7 | `debug` | Debug-level messages |

When you type `journalctl -p err`, **journalctl** treats it as a floor: it returns entries with priority `err` **or lower number** (more severe). So `-p err` includes `err`, `crit`, `alert`, `emerg`.

If you want **only** `err` and not `crit`, use the **range** form: `-p err..err` (inclusive on both ends).

```
   ┌──────────────────────────────────────────────────────────────┐
   │ -p err           => emerg | alert | crit | err  (4 levels)    │
   │ -p warning       => emerg | alert | crit | err | warning      │
   │ -p err..err      => err only            (exact)               │
   │ -p crit..err     => crit | err                                │
   │ -p err..emerg    => emerg | alert | crit | err  (same as -p err)│
   │ -p 3             => same as -p err                            │
   │ -p 3..3          => same as -p err..err                       │
   └──────────────────────────────────────────────────────────────┘
```

> **Why this matters:** This is the single biggest exam-day "gotcha" of `journalctl`. Candidates type `-p err` expecting *only* errors, then count and get more than they expected because crit/alert/emerg snuck in. The fix is the range form.

---

## 📜 Why Priority Filtering Exists — The Story

When `syslog` was created at Berkeley in the 1980s, every log line was a free-text string. The only metadata was the **facility** (who sent it) and the **priority** (how serious). The priority levels are numbered 0–7 specifically so a kernel module can write `printk(KERN_ERR, ...)` and the routing daemon can switch on a single integer comparison — extremely fast on tiny 1980s hardware.

systemd kept the model untouched because every Linux application already knew it. `syslog(3)` is called with `LOG_ERR`, `LOG_WARNING`, `LOG_INFO`, etc.; `journald` records the priority as the `PRIORITY=N` field. `journalctl -p N` then exploits the comparison: "show me entries where PRIORITY ≤ N."

The **range form** (`-p N..M`) was added a few systemd releases later because operators kept asking "I want just warning, not error." Today both forms are standard, and RHCSA EX200 expects fluency in both.

> **The point of the story:** `-p PRIORITY` is a 50-year-old idea wrapped in a modern indexed reader. The numbers are immutable; only the index changed.

---

## 👪 The Priority Family — Who Lives Where

```
Symbolic               Numeric    Typical sender
emerg                  0          kernel panic, watchdog
alert                  1          drbd split-brain, IPMI
crit                   2          oom-killer, disk array fail
err                    3          service start failure, AVC denial
warning                4          dropped packet, expired cert warning
notice                 5          service restart, "host A reachable"
info                   6          start, stop, normal operation
debug                  7          per-message debug trace
```

| Filter | Effect |
|---|---|
| `-p emerg` | priority = 0 only |
| `-p alert` | priorities 0–1 |
| `-p crit` | priorities 0–2 |
| `-p err` | priorities 0–3 |
| `-p warning` | priorities 0–4 |
| `-p notice` | priorities 0–5 |
| `-p info` | priorities 0–6 |
| `-p debug` | every entry |
| `-p err..err` | priority 3 only |
| `-p warning..err` | priorities 3–4 |
| `-p alert..warning` | priorities 1–4 |
| `-p 0..7` | every entry (range form) |

> **Reading rule:** A range `A..B` is inclusive of both ends, in either numeric direction; `-p warning..err` and `-p err..warning` both mean priorities 3 and 4.

---

## 📚 Priority Filter Reference Table

| Goal | Command | Notes |
|---|---|---|
| Errors and worse | `journalctl -p err` | The most common form |
| Warnings and worse | `journalctl -p warning` | Wider net |
| Crit and worse only | `journalctl -p crit` | Tight; usually drills to top 5-10 lines |
| Exactly `err` | `journalctl -p err..err` | Range = same priority on both ends |
| Warnings only (no error) | `journalctl -p warning..warning` | Same idea |
| Warning + err band | `journalctl -p warning..err` | Inclusive band |
| Numeric equivalent | `journalctl -p 3` | Identical to `-p err` |
| Count of errors-or-worse | `journalctl -p err --no-pager \| wc -l` | Standard tally |
| Per-priority counts | `journalctl -o json --no-pager \| jq -r .PRIORITY \| sort \| uniq -c` | One-line histogram |
| With unit | `journalctl -u sshd.service -p warning` | Combine `-u` + `-p` |
| With time | `journalctl -p err --since today` | Combine with `--since` |
| With boot | `journalctl -p err -b -0` | Combine with `-b` |
| Per-unit ranking | `journalctl -p err -o json --no-pager \| jq -r ._SYSTEMD_UNIT \| sort \| uniq -c \| sort -rn` | One-line "noisiest unit" |
| Inject test entry | `logger -p user.err -t prio-test MSG` | facility + priority on logger |

---

## 🎯 Career Pathway Sidebar

| Level | Why this lab matters |
|---|---|
| **RHCSA candidate** | EX200: "Show entries at `alert` or worse." Answer: `journalctl -p alert`. Don't get tricked into `-p alert..alert`. |
| **RHCE candidate** | Ansible health gate: `command: journalctl -u app -p err --since "1 hour ago"` with `failed_when: result.stdout_lines | length > 0`. |
| **SRE / Platform** | Alerting tiers: pager rings on `crit+`, email on `err`, dashboard on `warning`. |
| **DevOps** | CI failure triage: a build run that produces any `err+` journal entry should be flagged. |
| **AI / MLOps** | NCCL emits `warning` for slow allreduce; `err` for collapse. Distinguish before paging. |

---

## 🔧 The 10 Tasks

> Ten phases that build the **floor → range → exact → combine → inject → count → rank → report** habit.

---

### Task 1 — Set up the sandbox and confirm journal access

**Purpose:** Build the workspace, confirm `journalctl` works, capture baseline counts.

```bash
sudo -i
mkdir -p /root/journal-prio-lab && cd /root/journal-prio-lab

which journalctl
journalctl --version | head -n 1

journalctl --disk-usage | tee 01-disk-usage.txt
journalctl --no-pager | wc -l | tee 01-total-lines.txt
```

**Human-Readable Breakdown:** Become root, create the workspace, confirm the binary, version, current store size, and total line count for the journal as-is.

**Reading it left to right:** `--no-pager` makes the count work in a pipe. `wc -l` gives a single integer — the total number of journal lines currently visible.

**The story:** The baseline count is the denominator for every percentage you'll compute later. "75 of 18,242 entries (0.4%) were error-or-worse" reads better than "75 errors."

**Expected output:**

```text
/usr/bin/journalctl
systemd 252 (252-32.el9_4)
Archived and active journals take up 56.0M in the file system.
18242
```

**Switches**

| Token | Meaning |
|---|---|
| `--no-pager` | Disable interactive pager |
| `wc -l` | Count newline-terminated lines |
| `--disk-usage` | Bytes on disk |

**Troubleshoot**

| Symptom | Fix |
|---|---|
| Total lines is small (< 100) | Volatile journal — see Lab 102 |
| `--version` returns ancient | Older RHEL — most filters still work |

---

### Task 2 — Confirm the priority model by listing every level

**Purpose:** Print the priorities table to disk for future reference, plus the JSON view of a single entry showing its `PRIORITY=` field.

```bash
cd /root/journal-prio-lab

cat <<'EOF' | tee 02-priority-table.txt
N  Name      Notes
0  emerg     System is unusable
1  alert     Action must be taken immediately
2  crit      Critical conditions
3  err       Error conditions
4  warning   Warning conditions
5  notice    Normal but significant
6  info      Informational
7  debug     Debug-level messages
EOF

journalctl -n 1 -o json --no-pager | tee 02-one-entry.json | head -n 1
journalctl -n 1 -o json --no-pager | grep -oE '"PRIORITY"[^,]*' | tee 02-priority-field.txt
```

**Human-Readable Breakdown:** Save the table as a reference, then dump the single newest entry as JSON to prove the `PRIORITY` field is present.

**Reading it left to right:** `-o json` emits one JSON object per entry. `-n 1` keeps it small. `grep -oE '"PRIORITY"[^,]*'` extracts just the priority key/value.

**The story:** Memorize the table. Examiners may write tasks using **either** the name (`alert`) or the number (`1`) — be fluent in both directions.

**Expected output:**

```text
{"__CURSOR":"...","PRIORITY":"6","_SYSTEMD_UNIT":"sshd.service","MESSAGE":"...",...}
"PRIORITY":"6"
```

**Switches**

| Token | Meaning |
|---|---|
| `-o json` | One JSON object per line |
| `-n N` | Last N entries |
| `grep -oE` | Only the matching substring, extended regex |

**Troubleshoot**

| Symptom | Fix |
|---|---|
| `PRIORITY` missing | Very old systemd — should be present on RHEL 9 |
| `grep` returns nothing | Field name differs — try `_PRIORITY` (kernel messages) |

---

### Task 3 — Floor filter: `-p err` and what it includes

**Purpose:** Prove that `-p err` includes `err`, `crit`, `alert`, `emerg`.

```bash
cd /root/journal-prio-lab

journalctl -p err --no-pager | tee 03-p-err-all.txt | wc -l

journalctl -p err -o json --no-pager \
  | grep -oE '"PRIORITY":"[0-9]"' \
  | sort | uniq -c | sort -rn | tee 03-priorities-included.txt
```

**Human-Readable Breakdown:** Capture every `-p err` line, count them, then extract the `PRIORITY` field from each entry's JSON, sort and count the distinct priorities present in the result set.

**Reading it left to right:** `-o json` exposes the structured priority. `grep -oE '"PRIORITY":"[0-9]"'` keeps only the priority field token from each line. `sort | uniq -c | sort -rn` gives a count per distinct priority.

**The story:** This is the **proof** that `-p err` is a floor, not equality. The histogram should show priorities 0, 1, 2, 3 — all of them — not just 3.

**Expected output:**

```text
142
    138 "PRIORITY":"3"
      3 "PRIORITY":"2"
      1 "PRIORITY":"0"
```

**Switches**

| Token | Meaning |
|---|---|
| `-p err` | err + worse |
| `-o json` | JSON-per-line |
| `sort \| uniq -c \| sort -rn` | Count-then-rank |

**Troubleshoot**

| Symptom | Fix |
|---|---|
| Only `"3"` shown | Healthy host — no crit/alert/emerg ever happened |
| Lots of `"2"` and `"0"` | Hardware/kernel events present — investigate |
| Empty count | No errors at all — try a busier host or longer time window |

---

### Task 4 — Range filter: `-p warning..err` for exactly the warning+error band

**Purpose:** Restrict to priorities 3–4 only (no crit, no notice).

```bash
cd /root/journal-prio-lab

journalctl -p warning..err --no-pager | wc -l | tee 04-warning-to-err-count.txt

journalctl -p warning..err -o json --no-pager \
  | grep -oE '"PRIORITY":"[0-9]"' \
  | sort | uniq -c | sort -rn | tee 04-warning-to-err-priorities.txt
```

**Human-Readable Breakdown:** Count the band, then list which priorities are actually present in the result.

**Reading it left to right:** `-p warning..err` is an inclusive range — priorities 3 and 4 only. The histogram should show only those two values.

**The story:** The band form is the canonical "I want warnings but **without** the noise of info messages, and **without** mixing in crit/alert/emerg." Useful for daily health checks.

**Expected output:**

```text
612
    470 "PRIORITY":"4"
    142 "PRIORITY":"3"
```

**Switches**

| Token | Meaning |
|---|---|
| `-p A..B` | Inclusive range |
| `-p warning..err` | Priorities 3–4 |
| `-p crit..err` | Priorities 2–3 |
| `-p 0..7` | Every entry |

**Troubleshoot**

| Symptom | Fix |
|---|---|
| Range rejected | Update systemd; `..` requires v210+ |
| Extra priorities present | You typed `-p warning err` (two args) instead of the range form |

---

### Task 5 — Exact form: `-p err..err` for *only* err

**Purpose:** Get exactly one priority — no others.

```bash
cd /root/journal-prio-lab

journalctl -p err..err --no-pager | tee 05-exact-err.txt | wc -l
journalctl -p err..err -o json --no-pager \
  | grep -oE '"PRIORITY":"[0-9]"' | sort -u | tee 05-exact-err-priorities.txt
```

**Human-Readable Breakdown:** Use the range form with the same priority on both ends to get only that priority. The histogram should show **one** value.

**Reading it left to right:** `sort -u` deduplicates — should print exactly one row.

**The story:** This is the "I do not care about crit, only err" form. Useful when separating tiers of severity in dashboards or alerts.

**Expected output:**

```text
138
"PRIORITY":"3"
```

**Switches**

| Token | Meaning |
|---|---|
| `-p N..N` | Exactly priority N |

**Troubleshoot**

| Symptom | Fix |
|---|---|
| Two priorities printed | You used `-p err` (floor), not `-p err..err` |
| Empty | No `err`-priority events |

---

### Task 6 — Combine priority with unit, time, and boot filters

**Purpose:** Build production-grade triage queries by combining `-p` with `-u`, `--since`, `--until`, `-b`.

```bash
cd /root/journal-prio-lab

journalctl -u sshd.service -p err --no-pager | tee 06-sshd-err.txt | wc -l
journalctl -u sshd.service -p warning..err --since today --no-pager | tee 06-sshd-warn-err-today.txt | wc -l
journalctl -p err -b --no-pager | tee 06-err-current-boot.txt | wc -l
journalctl -p err --since "1 hour ago" --until "10 min ago" --no-pager | tee 06-err-narrow-window.txt | wc -l
```

**Human-Readable Breakdown:** Four common combinations — unit + priority floor, unit + band + day window, priority floor + current boot, priority floor + narrow time window.

**Reading it left to right:** Filters are AND'd. `-u UNIT -p err -b --since today` returns entries that satisfy **all** of those constraints.

**The story:** Real triage is always a combination. Memorize the **four** primary filters: `-u UNIT`, `-p PRIORITY`, `-b [N]`, `--since/--until`. Together they answer any "show me X" question.

**Expected output:**

```text
4
0
142
12
```

**Switches**

| Token | Meaning |
|---|---|
| `-u UNIT` | Unit filter |
| `-p PRI` | Priority floor |
| `-b [N]` | Boot index |
| `--since` / `--until` | Time window |

**Troubleshoot**

| Symptom | Fix |
|---|---|
| Empty results | Filters too tight — drop one and retry |
| Many empty unit names | Use a glob: `-u 'systemd-*'` |

---

### Task 7 — Inject synthetic priority messages with `logger`

**Purpose:** Generate one message at each priority so the lab has predictable data to query.

```bash
cd /root/journal-prio-lab

for PRI in emerg alert crit err warning notice info debug; do
  logger -p user.${PRI} -t prio-test "synthetic ${PRI} priority test"
done

sleep 1

journalctl -t prio-test -o json --no-pager \
  | grep -oE '"PRIORITY":"[0-9]"' \
  | sort | uniq -c | sort | tee 07-injected-priorities.txt

journalctl -t prio-test -p err --no-pager | tee 07-injected-err-floor.txt
journalctl -t prio-test -p warning..warning --no-pager | tee 07-injected-warning-only.txt
```

**Human-Readable Breakdown:** Walk every priority by name, inject one message per priority with the `prio-test` tag, then prove the priority filter selects exactly the right subset.

**Reading it left to right:** `logger -p user.${PRI} -t TAG MSG` writes one message per iteration. `-t prio-test` keeps the lab's messages isolated from the host's normal traffic. The journal queries verify the floor and exact-priority behaviors.

**The story:** This is the **calibration step**. After running it, you can predict exactly how many lines each priority filter will return — and any deviation points to a misunderstanding.

**Expected output:**

```text
      1 "PRIORITY":"0"
      1 "PRIORITY":"1"
      1 "PRIORITY":"2"
      1 "PRIORITY":"3"
      1 "PRIORITY":"4"
      1 "PRIORITY":"5"
      1 "PRIORITY":"6"
      1 "PRIORITY":"7"
Jan 14 09:50:11 host1 prio-test[2901]: synthetic emerg priority test
Jan 14 09:50:11 host1 prio-test[2902]: synthetic alert priority test
Jan 14 09:50:11 host1 prio-test[2903]: synthetic crit priority test
Jan 14 09:50:11 host1 prio-test[2904]: synthetic err priority test
Jan 14 09:50:11 host1 prio-test[2905]: synthetic warning priority test
```

**Switches**

| Token | Meaning |
|---|---|
| `logger -p F.P` | Facility.priority |
| `-t TAG` | Syslog tag |
| `journalctl -t TAG` | Filter by tag |

**Troubleshoot**

| Symptom | Fix |
|---|---|
| Some priorities missing | Daemon throttling — `sleep 1` between |
| `wall` triggered on `emerg` | Expected — see `/etc/rsyslog.conf` `*.emerg :omusrmsg:*` |
| Wrong tag in journal | `-t TAG` only (single word) |

---

### Task 8 — Build a per-priority histogram of the current boot

**Purpose:** One command, one histogram — useful for health dashboards.

```bash
cd /root/journal-prio-lab

journalctl -b -o json --no-pager \
  | grep -oE '"PRIORITY":"[0-9]"' \
  | sort | uniq -c | sort -k2,2 | tee 08-histogram.txt

echo "------" | tee -a 08-histogram.txt
awk '{print $1, $2}' 08-histogram.txt | tee -a 08-histogram.txt
```

**Human-Readable Breakdown:** Render the entire current-boot journal as JSON, extract priorities, sort by priority number (not by count), and produce the histogram. The trailing awk re-prints the rows for the report.

**Reading it left to right:** `sort -k2,2` sorts by the second whitespace-delimited field (which is `"PRIORITY":"N"`) so the rows are in priority order, not count order. This format is easier to read like a table.

**The story:** A boot's priority histogram tells you, at a glance, whether the host is healthy. A boot dominated by priority 6/info is normal. A boot with hundreds of priority 3/err is unhealthy.

**Expected output:**

```text
      1 "PRIORITY":"0"
      1 "PRIORITY":"1"
      4 "PRIORITY":"2"
    142 "PRIORITY":"3"
    470 "PRIORITY":"4"
    980 "PRIORITY":"5"
  16500 "PRIORITY":"6"
    142 "PRIORITY":"7"
------
1 "PRIORITY":"0"
1 "PRIORITY":"1"
...
```

**Switches**

| Token | Meaning |
|---|---|
| `sort -k2,2` | Sort by column 2 |
| `tee -a FILE` | Append (don't truncate) |

**Troubleshoot**

| Symptom | Fix |
|---|---|
| Histogram empty | Volatile journal + tiny store — boot a busy host |
| Priorities present > 7 | Impossible — must be a parsing mistake |

---

### Task 9 — Rank noisiest units at error-or-worse priority

**Purpose:** Produce a sorted "top 10 noisy units" list at `-p err`.

```bash
cd /root/journal-prio-lab

journalctl -b -p err -o json --no-pager \
  | grep -oE '"_SYSTEMD_UNIT":"[^"]+"' \
  | sort | uniq -c | sort -rn | head -n 10 | tee 09-top-noisy-units.txt
```

**Human-Readable Breakdown:** Extract `_SYSTEMD_UNIT` from every error-or-worse entry on the current boot; rank descending; keep the top 10.

**Reading it left to right:** `grep -oE '"_SYSTEMD_UNIT":"[^"]+"'` extracts the field token. The count/sort/head pipeline ranks.

**The story:** This is the **"who is making noise?"** report. If `chronyd.service` is at the top with 200 error-priority entries, you have a chronyd problem. If `NetworkManager.service` is there, you have a network problem. The unit's name is your starting point.

**Expected output:**

```text
     74 "_SYSTEMD_UNIT":"chronyd.service"
     38 "_SYSTEMD_UNIT":"sssd.service"
     12 "_SYSTEMD_UNIT":"firewalld.service"
      8 "_SYSTEMD_UNIT":"NetworkManager.service"
      ...
```

**Switches**

| Token | Meaning |
|---|---|
| `grep -oE` | Only matched, extended regex |
| `head -n 10` | Top 10 |

**Troubleshoot**

| Symptom | Fix |
|---|---|
| Empty | No errors on current boot — try `--since "3 days ago"` |
| Strange `(unknown)` entries | Pre-systemd processes — usually safe to ignore |

---

### Task 10 — Capstone: severity-by-unit report + cleanup

**Task statement:** *"Build a one-paragraph report citing total lines, error+ count, error+ as a percentage, the top 5 noisy units at error+, and the count at each priority. Then clean up."*

```bash
cd /root/journal-prio-lab

TOTAL=$(journalctl -b --no-pager | wc -l)
ERR_PLUS=$(journalctl -b -p err --no-pager | wc -l)
PCT=$(awk -v a="$ERR_PLUS" -v b="$TOTAL" 'BEGIN { if (b>0) printf "%.2f", (a*100)/b; else print "0.00" }')

TOP5=$(journalctl -b -p err -o json --no-pager \
  | grep -oE '"_SYSTEMD_UNIT":"[^"]+"' \
  | sort | uniq -c | sort -rn | head -n 5)

HIST=$(journalctl -b -o json --no-pager \
  | grep -oE '"PRIORITY":"[0-9]"' \
  | sort | uniq -c | sort -k2,2)

cat > 10-report.txt <<EOF
Priority audit — $(hostname) — boot 0 — $(date -Iseconds)

Total journal lines this boot: ${TOTAL}
Error-or-worse entries:        ${ERR_PLUS}   (${PCT}% of total)

== Top 5 noisy units at err+ ==
${TOP5:-(none)}

== Histogram of priorities ==
${HIST:-(empty)}

How to reproduce:
  journalctl -b                          (total)
  journalctl -b -p err                   (err and worse)
  journalctl -b -p err -o json | jq ._SYSTEMD_UNIT | sort | uniq -c | sort -rn
EOF

cat 10-report.txt
```

**Layer stack you built:**

```text
10-report.txt                  ← deliverable
  ├── 03-p-err-all.txt         ← raw err+ lines
  ├── 04-warning-to-err-...    ← band counts
  ├── 07-injected-...          ← calibration evidence
  ├── 08-histogram.txt         ← per-priority counts
  └── 09-top-noisy-units.txt   ← ranking
```

**Cleanup**

```bash
cd /root
rm -rf /root/journal-prio-lab
ls -ld /root/journal-prio-lab 2>&1 | head -n 1
exit
```

**Troubleshoot**

| Symptom | Fix |
|---|---|
| `PCT` is 0.00 | No errors on this boot — healthy |
| `TOP5` empty | Same — replace with `(none)` |
| `awk` floating-point off | Bash 5 `printf` works too |

---

## 🔍 Priority Decision Guide

```
"Just show me what's broken"           → journalctl -p err
"Just errors, no crit/alert"           → journalctl -p err..err
"Warnings AND errors only"             → journalctl -p warning..err
"All non-info noise"                   → journalctl -p warning
"Page-worthy events only"              → journalctl -p crit
"Anything at all"                      → journalctl
"Show priorities in JSON"              → journalctl -o json | jq .PRIORITY
"Count per priority"                   → journalctl -o json | jq -r .PRIORITY | sort | uniq -c
```

---

## ✅ Lab Checklist (10 Tasks)

- [ ] 01 Sandbox + baseline counts
- [ ] 02 Save priority table + JSON `PRIORITY` field
- [ ] 03 Floor filter `-p err`
- [ ] 04 Range filter `-p warning..err`
- [ ] 05 Exact filter `-p err..err`
- [ ] 06 Combine with `-u`, `--since`, `-b`
- [ ] 07 Inject synthetic priorities with `logger`
- [ ] 08 Per-priority histogram
- [ ] 09 Rank noisy units at err+
- [ ] 10 Capstone report + cleanup

---

## ⚠️ Common Pitfalls

| Mistake | Symptom | Fix |
|---|---|---|
| Assuming `-p err` is "only err" | Extra crit/alert/emerg lines | Use `-p err..err` |
| Two args instead of range | `-p warning err` interpreted as `-p warning` then filename `err` | Use `-p warning..err` |
| Mixing numeric and symbolic | `-p 3..warning` is unsupported | Use one form throughout |
| Forgetting `-o json` | No `PRIORITY` field extractable | Add `-o json` |
| Glob in tag name | `journalctl -t 'prio-*'` not supported | Use `_PID=` or `SYSLOG_IDENTIFIER=` |
| Range reversed | `-p emerg..err` works same as `-p err..emerg` | Inclusive both directions |
| Quoting JSON paths | `jq .PRIORITY` works; `jq ".PRIORITY"` also fine | Both valid |

---

## 🎯 Career & Interview Strategy

**RHCSA candidate**
- "Show entries at priority `alert` or worse." Two acceptable answers: `-p alert` (floor) or `-p emerg..alert` (range). Both return priorities 0–1.

**RHCE candidate**
- Ansible: `command: journalctl -p err --since "1 hour ago"` with `failed_when: result.stdout_lines | length > 0` — fail the play if any error appears.

**SRE / Platform interview**
- Be ready to explain how alerting tiers should map to priorities (`pager` ≤ crit; `email` = err; `dashboard` = warning).

**DevOps**
- Pipe `journalctl -p err -b --no-pager` into the build's failure report; attach to the PR comment.

**AI / MLOps**
- NCCL: `warning` is normal noise from slow allreduce; `err` is a real collapse. Filter both for different audiences.

---

## 🔗 Related Labs

| Lab | Connection |
|---|---|
| Lab 101 — Query Logs with `journalctl` | Where `-p` lives in the filter set |
| Lab 102 — Persistent Journal | Persistent + priority is the full triage path |
| Lab 103 — Log Routing | Same priorities feed `*.priority` rsyslog rules |
| Lab 104 — Auth Logs | `authpriv.*` lands in `/var/log/secure` with priority |
| Lab 106 — Service-Specific Journals | Pair `-u UNIT` with `-p PRIORITY` |

---

## 👤 Author

**Kelvin R. Tobias**
[kelvinintech.com](https://kelvinintech.com) · [GitHub](https://github.com/kelvintechnical) · [LinkedIn](https://www.linkedin.com/in/kelvin-r-tobias-211949219)
