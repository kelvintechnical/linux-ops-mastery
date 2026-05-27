# Lab: Check NTP Sync Status — `chronyc tracking`, `chronyc sources`, `chronyc sourcestats`, `timedatectl`, `ntpq -p`

- **Series:** linux-ops-mastery — RHCSA System Time & Locale
- **Subjects covered:** `chrony` as the RHEL 9 default NTP client, `chronyc tracking` (current sync state, stratum, offset, frequency, RMS), `chronyc sources -v` (per-server status with `^*`/`^+`/`^-`/`^x`/`^?` markers), `chronyc sourcestats` (long-term statistics per server), `chronyc activity` (one-line summary), `chronyc makestep` (force step instead of slew), `timedatectl status` (system clock + NTP sync flag), `timedatectl show -p NTPSynchronized`, the rarely-installed `ntpq -p` (ntpsec/ntp.org client), correlating with `journalctl -u chronyd.service`, reading `/var/run/chrony/sources`, building a "drift report" with `chronyc tracking | grep` parsing
- **Career arcs covered:** RHCSA (EX200 — "verify NTP is synchronized"), RHCE (Ansible health gate), SRE (clock-skew alerting), DevOps (Kerberos / etcd / log-correlation depend on accurate clocks), AI / MLOps (distributed training clock alignment)
- **Prerequisite:** Lab 107 (Configure Timezone and Time Synchronization)
- **Time Estimate:** 25 to 35 minutes
- **Difficulty arc:** Tasks 1–2 baseline + service status · Tasks 3–4 `chronyc tracking` + `chronyc sources -v` · Task 5 source markers explained · Task 6 `chronyc sourcestats` · Task 7 `timedatectl` view · Task 8 `chronyc activity` and `chronyc waitsync` · Task 9 `chronyc makestep` and journal correlation · Task 10 capstone sync report + cleanup

---

## Objective

Stop guessing whether the clock is synchronized. By the end of this lab you can verify in three independent ways that NTP is doing its job on a RHEL 9 host: `chronyc tracking` for the current offset, `chronyc sources -v` for the per-server status, and `timedatectl status` for the systemd-level summary. You will also know how to force a step adjustment if the host drifted too far during boot, and how to write a one-paragraph "clock health" report a manager can quote.

The capstone is the engineer-realistic prompt: *"On this RHEL 9 host, verify the system clock is NTP-synchronized, capture the current offset in microseconds, list the upstream sources with their reachability markers, and write a one-paragraph clock-health report. Do not change configuration."*

> **Lab safety note:** This lab is read-only except for one optional `chronyc makestep` (which only steps the clock if drift is bounded). Nothing else is changed.

---

## Concept: Three Independent Views of "Is the Clock OK?"

`chrony` is the RHEL 9 default NTP implementation (it replaced `ntpd` from RHEL 7 onward). The user-facing CLI is `chronyc`, which talks to the running `chronyd.service` over a Unix socket. The companion systemd command `timedatectl` provides a simpler, higher-level view via `systemd-timedated`.

```
   ┌──────────────────────────────────────────────────────────────┐
   │  chronyd.service                                             │
   │    ├── reads /etc/chrony.conf and /etc/chrony.d/*.sources    │
   │    ├── talks to upstream NTP servers (UDP 123)               │
   │    ├── disciplines the system clock (slew or step)           │
   │    └── exposes status over /var/run/chrony/chronyd.sock      │
   │                                                              │
   │  chronyc (CLI) reads chronyd over the socket                 │
   │    ├── tracking      ← current offset, freq, stratum         │
   │    ├── sources -v    ← per-server status with state markers  │
   │    ├── sourcestats   ← long-term stats per source            │
   │    ├── activity      ← one-line "Y sources are online"       │
   │    ├── makestep      ← force a step if slew would be too slow│
   │    └── waitsync N    ← block until synced (or N retries)     │
   │                                                              │
   │  timedatectl reads systemd-timedated (which talks to chrony) │
   │    ├── status        ← human-readable system clock view      │
   │    └── show -p NTPSynchronized ← bool for scripts            │
   └──────────────────────────────────────────────────────────────┘
```

> **Why this matters:** RHCSA exam tasks phrase the same question three ways: "Is the clock synced?", "Is chrony running?", "Show the NTP sources." Use the right tool for each phrasing.

---

## 📜 Why chrony Replaced ntpd on RHEL — The Story

`ntpd` (NTP Project from David Mills, 1980s) was the original NTP daemon. It worked, but had three weaknesses that mattered in the 2010s:

1. **Slow convergence after long sleeps** — VMs that resumed from snapshot took many minutes to re-sync.
2. **Limited NAT / firewall friendliness** — needed open UDP 123 in both directions.
3. **Less robust on intermittent connections** — laptops with WiFi flapping struggled.

`chrony` (Richard Curnow, 1997-2010s) was rewritten with virtualization, laptops, and intermittent connectivity in mind. It converges in seconds, supports `chronyc makestep` for fast first-time alignment, and is the upstream default on RHEL 9 (and most modern distros). The protocol on the wire is still NTPv4 — only the client implementation changed.

> **The point of the story:** `chronyc` is the modern tool. `ntpq` may still appear on legacy hosts or in `ntpsec` deployments — know its output too, because exam questions can reference either.

---

## 👪 The chrony Family — Who Lives Where

```
Daemon
├── chronyd.service                          ← systemd unit
└── /usr/sbin/chronyd                        ← binary

Config
├── /etc/chrony.conf                         ← canonical (Lab 109)
└── /etc/chrony.d/*.sources                  ← drop-in sources

State / runtime
├── /var/run/chrony/chronyd.sock             ← chronyc → chronyd channel
├── /var/lib/chrony/drift                    ← long-term frequency offset
└── /var/lib/chrony/rtc                      ← optional RTC tracking

User-facing
├── chronyc tracking                         ← key status command
├── chronyc sources [-v]                     ← per-source state + verbose
├── chronyc sourcestats                      ← stats over time
├── chronyc activity                         ← one-line summary
├── chronyc makestep                         ← force step adjustment
└── chronyc waitsync N                       ← wait for sync (returns 0 on success)

System-level
├── timedatectl status                       ← high-level view
├── timedatectl show -p NTPSynchronized      ← scriptable bool
└── journalctl -u chronyd.service            ← daemon logs
```

### `chronyc sources -v` markers (column 1, two characters)

| Marker | Meaning |
|---|---|
| `^*` | Current best selected source (primary sync) |
| `^+` | Acceptable, not currently selected |
| `^-` | Excluded by selection algorithm |
| `^?` | Unreachable |
| `^x` | Believed to be a falseticker (lying) |
| `=*` | Local reference (refclock) |

| Second char | Meaning |
|---|---|
| `^` | Server |
| `=` | Peer (symmetric) |

---

## 📚 NTP Status Reference Table

| Goal | Command | Notes |
|---|---|---|
| One-line "is it synced?" | `timedatectl show -p NTPSynchronized` | `yes`/`no` |
| Full system clock view | `timedatectl status` | Time, zone, NTP synced, RTC |
| Current offset / stratum | `chronyc tracking` | Reference ID, stratum, last update |
| Per-source status | `chronyc sources -v` | Markers + reach/offset |
| Long-term stats | `chronyc sourcestats` | Frequency/skew per source |
| One-line activity | `chronyc activity` | "X sources online, Y offline, ..." |
| Force step | `sudo chronyc makestep` | Only steps if within bounds |
| Wait for sync | `chronyc waitsync N M T H` | Exit 0 on sync, retry budgets |
| Reload sources | `sudo chronyc reload sources` | Re-read `/etc/chrony.d/*.sources` |
| List which servers | `chronyc -n sources` | `-n` skips DNS reverse |
| Watch live | `watch -n 1 'chronyc tracking; chronyc sources -v'` | Operator's tmux pane |
| Daemon logs | `journalctl -u chronyd.service` | Boot-time + drift events |
| Legacy ntpq | `ntpq -p` | Only if `ntp` package installed |

---

## 🎯 Career Pathway Sidebar

| Level | Why this lab matters |
|---|---|
| **RHCSA candidate** | EX200: "Verify NTP synchronization." → `timedatectl status` + `chronyc tracking`. |
| **RHCE candidate** | Ansible: `command: chronyc tracking` register output, `failed_when: 'Leap status' not in result.stdout` |
| **SRE / Platform** | Clock skew > 100 ms breaks Kerberos, breaks etcd quorum, breaks distributed traces. |
| **DevOps** | CI runners must be synced for accurate build timestamps and signed artifact validity. |
| **AI / MLOps** | NCCL synchronizes by wall clock during certain initialization paths; skew > 1 s causes hangs. |

---

## 🔧 The 10 Tasks

> Ten phases that build the **service-up → tracking → sources -v → markers → stats → systemd-level → activity → step → correlate** habit.

---

### Task 1 — Set up the sandbox and confirm `chronyd` is running

**Purpose:** Build the workspace, confirm the daemon is active, capture status for the artifact set.

```bash
sudo -i
mkdir -p /root/ntp-status-lab && cd /root/ntp-status-lab

which chronyc chronyd
chronyc -V 2>&1 | head -n 1
systemctl is-active chronyd.service | tee 01-active.txt
systemctl status chronyd.service --no-pager | head -n 10 | tee 01-status.txt
```

**Human-Readable Breakdown:** Become root, confirm both binaries exist, capture chrony version, confirm the service is active, and save the first 10 lines of status output.

**Reading it left to right:** `chronyc -V` prints the chrony version. `systemctl is-active` returns `active`/`inactive`/`failed`. `--no-pager` ensures the pipe to `head` works.

**The story:** On RHEL 9, chronyd is enabled by default. If `inactive`, someone disabled it intentionally — confirm before re-enabling. Most "clock skew" tickets begin with the daemon not running.

**Expected output:**

```text
/usr/bin/chronyc
/usr/sbin/chronyd
chronyd (chrony) version 4.3 (+CMDMON +NTP +REFCLOCK +RTC +PRIVDROP +SCFILTER +SIGND +ASYNCDNS +NTS +SECHASH +IPV6 +DEBUG)
active
● chronyd.service - NTP client/server
     Loaded: loaded (/usr/lib/systemd/system/chronyd.service; enabled; preset: enabled)
     Active: active (running) since Tue 2026-01-14 09:00:11 EST; 1h ago
```

**Switches**

| Token | Meaning |
|---|---|
| `chronyc -V` | Version |
| `systemctl is-active UNIT` | Active state |
| `--no-pager` | Disable pager |

**Troubleshoot**

| Symptom | Fix |
|---|---|
| `chronyc: command not found` | `dnf install chrony` |
| `inactive` | `systemctl enable --now chronyd` |
| `failed` | `journalctl -xeu chronyd.service` |

---

### Task 2 — `chronyc tracking` — the canonical "is the clock OK?" command

**Purpose:** Capture the current sync state, reference server, stratum, offset, and frequency.

```bash
cd /root/ntp-status-lab

chronyc tracking | tee 02-tracking.txt

grep -E '^(Reference ID|Stratum|Ref time|System time|Last offset|RMS offset|Frequency|Skew|Residual freq|Root delay|Root dispersion|Update interval|Leap status)' 02-tracking.txt | tee 02-tracking-fields.txt
```

**Human-Readable Breakdown:** Run `chronyc tracking`, save the full output, then extract the canonical fields for downstream parsing.

**Reading it left to right:** `chronyc tracking` is a one-shot command that returns a multi-line block — Reference ID, stratum, last offset, frequency, skew, leap status, etc. Each line has a label and value separated by spaces.

**The story:** This is the **first** command operators reach for. Three fields matter most:

- **Leap status: Normal** = synced.
- **System time** offset (in seconds) — the live deviation from upstream.
- **Reference ID** — which server is currently primary.

If `Leap status: Not synchronised`, the clock is not aligned yet.

**Expected output:**

```text
Reference ID    : A29FC87B (time.google.com)
Stratum         : 2
Ref time (UTC)  : Tue Jan 14 14:42:11 2026
System time     : 0.000012345 seconds slow of NTP time
Last offset     : -0.000002111 seconds
RMS offset      : 0.000098876 seconds
Frequency       : 12.456 ppm slow
Residual freq   : -0.001 ppm
Skew            : 0.045 ppm
Root delay      : 0.012345 seconds
Root dispersion : 0.001234 seconds
Update interval : 64.2 seconds
Leap status     : Normal
```

**Switches**

| Token | Meaning |
|---|---|
| `chronyc tracking` | Status |
| `grep -E '^(field|...)'` | Anchor at line start |

**Troubleshoot**

| Symptom | Fix |
|---|---|
| `Leap status: Not synchronised` | Wait a minute, then `chronyc makestep` |
| `Reference ID: 00000000` | Source 0 — no source selected |
| `chronyc: 506 Cannot talk to daemon` | `chronyd` not running |

---

### Task 3 — `chronyc sources -v` — per-server status

**Purpose:** See every upstream source, with markers indicating reachability and selection.

```bash
cd /root/ntp-status-lab

chronyc sources -v | tee 03-sources-v.txt
chronyc -n sources -v | tee 03-sources-numeric.txt
```

**Human-Readable Breakdown:** Run the verbose form (which prints a marker legend at the top), then run with `-n` to skip reverse-DNS so server IPs print numerically.

**Reading it left to right:** `chronyc sources -v` prints a header explaining the markers, then a table of sources. `-n` swaps DNS hostnames for IPs (useful in scripts where DNS resolution is slow or unreliable).

**The story:** The marker column is where you read the state at a glance: `^*` is good (selected), `^?` is bad (unreachable). Every well-running host has one `^*` and 2-3 `^+` peers.

**Expected output (excerpt):**

```text
MS Name/IP address         Stratum Poll Reach LastRx Last sample
===============================================================================
^* time.google.com               1   6   377    32  -1234ns[-1234ns] +/- 5.6ms
^+ time.cloudflare.com           1   6   377    35  +789us[+789us]   +/- 4.2ms
^+ ntp1.example.com              2   6   377    27  -0.001s[-0.001s] +/- 7.1ms
^? old.example.org               0   6    0      -  +0ns[   +0ns]   +/-    0ns
```

**Switches**

| Token | Meaning |
|---|---|
| `chronyc sources` | Per-server table |
| `-v` | Show marker legend |
| `-n` | Numeric IPs |

**Troubleshoot**

| Symptom | Fix |
|---|---|
| All sources show `^?` | Network not reachable — check firewall UDP 123 |
| Only one source | Lab default; OK if syncing |
| Reach column `0` | Have not heard from server yet — wait |

---

### Task 4 — Decode every marker in `chronyc sources -v`

**Purpose:** Internalize what each marker character means.

```bash
cd /root/ntp-status-lab

cat <<'EOF' | tee 04-marker-legend.txt
First character (S = source state)
  ^   server
  =   peer (symmetric)

Second character (M = source mode)
  *   current best (selected for synchronization)
  +   acceptable, not currently the primary
  -   excluded by selection algorithm (e.g. too slow / drifting too much)
  ?   unreachable
  x   believed to be a falseticker (output disagrees with majority)
  ~   no recent measurements

Columns
  Stratum  — distance from a reference clock (lower = closer to authoritative)
  Poll     — log2(seconds) between polls; 6 = every 64 s
  Reach    — 8-bit shift register of last 8 polls; 377 octal = 11111111 = all reached
  LastRx   — seconds since last reply
  Last sample — last measured offset and ± error
EOF
cat 04-marker-legend.txt
```

**Human-Readable Breakdown:** Save the marker legend to disk so future-you doesn't have to recall it.

**Reading it left to right:** First character indicates source type (`^` server vs `=` peer). Second character is state. `Reach=377` (octal) means all eight recent polls succeeded — a happy source. `Reach=0` means the daemon has not heard back yet.

**The story:** RHCSA tests recognition. If the question says "which source is currently being used for time?", the answer is the line that starts with `^*`. If the question says "which source is unreachable?", look for `^?`.

**Switches**

| Marker | Meaning |
|---|---|
| `^*` | Selected |
| `^+` | Acceptable backup |
| `^-` | Excluded |
| `^?` | Unreachable |
| `^x` | Falseticker |

**Troubleshoot**

| Symptom | Fix |
|---|---|
| Every source shows `^-` | Configuration mismatch — check `/etc/chrony.conf` |
| `^x` source | Likely a misconfigured local server — remove it |

---

### Task 5 — `chronyc sourcestats` — long-term statistics

**Purpose:** Per-source long-term stats: standard deviation, frequency offset, residual.

```bash
cd /root/ntp-status-lab

chronyc sourcestats | tee 05-sourcestats.txt
```

**Human-Readable Breakdown:** Run the long-term stats command and save output. Useful for "which source is the most stable?" investigations.

**Reading it left to right:** Columns include `Name/IP`, `NP` (number of points used in regression), `NR` (residuals runs), `Span` (over how long the stats apply), `Frequency`, and `Freq Skew`, plus offset and standard deviation.

**The story:** `tracking` is the **right now** snapshot; `sourcestats` is the **history**. Use stats to identify slowly-drifting sources before they get excluded by `sources -v`.

**Expected output:**

```text
Name/IP Address            NP  NR  Span  Frequency  Freq Skew  Offset  Std Dev
================================================================================
time.google.com            12   6   17m     +0.012      0.030  +20us    0.0123s
time.cloudflare.com         8   4   12m     -0.003      0.054  -45us    0.0098s
```

**Switches**

| Token | Meaning |
|---|---|
| `chronyc sourcestats` | Long-term stats |

**Troubleshoot**

| Symptom | Fix |
|---|---|
| Empty | Just started — no stats yet |
| All sources same | Lab/single-source environment |

---

### Task 6 — `timedatectl status` — the systemd view

**Purpose:** High-level "is it synced" view via systemd-timedated.

```bash
cd /root/ntp-status-lab

timedatectl status | tee 06-timedatectl.txt
timedatectl show -p NTPSynchronized | tee 06-ntp-synced-flag.txt
timedatectl show | tee 06-timedatectl-show-all.txt
```

**Human-Readable Breakdown:** Three views — human-readable status, the single `NTPSynchronized` property for scripts, and every property timedated exposes.

**Reading it left to right:** `timedatectl status` prints a human block: Local time, Universal time, RTC time, Time zone, **System clock synchronized**, **NTP service: active**. `show -p NAME` prints just that property in `Name=Value` form — easy for scripts. `show` alone prints every property.

**The story:** `timedatectl` is the **system-administration friendly** wrapper. It does not know which sources chrony uses, but it knows whether systemd believes the clock is synchronized. The two answers (`chronyc tracking` Leap status and `NTPSynchronized=`) should agree.

**Expected output:**

```text
               Local time: Tue 2026-01-14 09:43:11 EST
           Universal time: Tue 2026-01-14 14:43:11 UTC
                 RTC time: Tue 2026-01-14 14:43:11
                Time zone: America/New_York (EST, -0500)
System clock synchronized: yes
              NTP service: active
          RTC in local TZ: no
NTPSynchronized=yes
...
```

**Switches**

| Token | Meaning |
|---|---|
| `timedatectl status` | Human block |
| `show` | All properties |
| `show -p NAME` | One property |

**Troubleshoot**

| Symptom | Fix |
|---|---|
| `NTP service: inactive` | `systemctl enable --now chronyd` |
| `System clock synchronized: no` | Wait, then `chronyc makestep` |
| Both disagree | Restart chronyd; one minute later both update |

---

### Task 7 — `chronyc activity` and `waitsync`

**Purpose:** One-line activity summary; programmatic "wait until synced."

```bash
cd /root/ntp-status-lab

chronyc activity | tee 07-activity.txt
chronyc waitsync 5 0.05 0 2 2>&1 | tee 07-waitsync.txt
echo "Exit code: $?" | tee -a 07-waitsync.txt
```

**Human-Readable Breakdown:** `activity` produces one summary line; `waitsync N M T H` blocks until synced (within tolerance M) or until N retries elapse.

**Reading it left to right:** `activity` says e.g. "4 sources online, 0 sources offline, 0 sources doing burst (return to online), 0 sources doing burst (return to offline), 1 sources with unknown address." `waitsync` arguments are: max retries (5), max distance in seconds (0.05), max RMS distance (0 = ignore), how many attempts to wait (2 seconds between).

**The story:** `waitsync` is the script-friendly tool. In a kickstart `%post`, run `chronyc waitsync 60 0.1 0 1` to block until the clock is synced before continuing with package installs that need accurate timestamps.

**Expected output:**

```text
200 OK
4 sources online
0 sources offline
0 sources doing burst (return to online)
0 sources doing burst (return to offline)
0 sources with unknown address
try: 1, refid: A29FC87B, correction: 0.000012, skew: 0.045
System clock wrong by 0.000012 seconds (ignored)
Exit code: 0
```

**Switches**

| Token | Meaning |
|---|---|
| `chronyc activity` | Summary |
| `chronyc waitsync N M T H` | Wait for sync; returns 0 on success |

**Troubleshoot**

| Symptom | Fix |
|---|---|
| `waitsync` exits non-zero | Not synced within budget — investigate sources |
| `0 sources online` | Network or firewall — check UDP 123 |

---

### Task 8 — Force a step adjustment with `chronyc makestep`

**Purpose:** Trigger an immediate step (if drift is bounded). Useful on boot or after suspend.

```bash
cd /root/ntp-status-lab

date -Iseconds | tee 08-pre-step.txt
sudo chronyc makestep 2>&1 | tee 08-makestep.txt
sleep 2
date -Iseconds | tee 08-post-step.txt
chronyc tracking | grep -E 'Last offset|System time' | tee 08-post-step-tracking.txt
```

**Human-Readable Breakdown:** Record current time, force a step, record time again, then inspect `tracking` for the new offset.

**Reading it left to right:** `chronyc makestep` requests an immediate step — chrony slews by default (gradual), but makestep tells it to step (instant). The daemon only honors this if the magnitude is within the configured `makestep` directive's bounds.

**The story:** Useful when a host was suspended for hours and the clock is wildly off — slewing at 0.05 s/s would take forever, but stepping is instantaneous. RHCSA exam labs sometimes ask "after this `date -s` modification, sync immediately."

**Expected output:**

```text
2026-01-14T09:45:11-05:00
200 OK
2026-01-14T09:45:11-05:00
System time     : 0.000001 seconds slow of NTP time
Last offset     : -0.000002 seconds
```

**Switches**

| Token | Meaning |
|---|---|
| `chronyc makestep` | Immediate step |
| `chronyc burst 4/4` | Burst-poll a source |

**Troubleshoot**

| Symptom | Fix |
|---|---|
| `400 BadRequest` | Privilege missing — needs root |
| No visible change | Already within tolerance |
| `Disabled` | Server-only mode — `makestep` directive not in chrony.conf |

---

### Task 9 — Correlate with `journalctl -u chronyd.service`

**Purpose:** Read chronyd's own log entries for sync events.

```bash
cd /root/ntp-status-lab

journalctl -u chronyd.service -b --no-pager | head -n 20 | tee 09-chronyd-journal.txt
journalctl -u chronyd.service --since today --no-pager | grep -Ei 'select|step|leap' | tee 09-events.txt || true
```

**Human-Readable Breakdown:** Capture the first 20 chronyd log lines on the current boot, then today's "interesting" lines — selection changes, step adjustments, leap-second events.

**Reading it left to right:** `journalctl -u chronyd.service -b` filters to this boot. The grep keeps only events you care about.

**The story:** When `tracking` reports unexpected offset, the journal is the next stop. "Selected source 192.0.2.5" or "System clock wrong by 1.234 seconds, adjustment started" are the kinds of lines you want.

**Expected output (excerpt):**

```text
Jan 14 09:00:33 host1 chronyd[1108]: chronyd version 4.3 starting (...)
Jan 14 09:00:33 host1 chronyd[1108]: Loaded seccomp filter (level 1)
Jan 14 09:00:34 host1 chronyd[1108]: Using right/UTC timezone to obtain leap second data
Jan 14 09:00:34 host1 chronyd[1108]: Frequency 12.456 +/- 0.045 ppm read from /var/lib/chrony/drift
Jan 14 09:00:34 host1 chronyd[1108]: Selected source 162.159.200.1 (time.cloudflare.com)
```

**Switches**

| Token | Meaning |
|---|---|
| `-u chronyd.service` | Unit filter |
| `-b` | Current boot |
| `--since today` | Today only |
| `grep -Ei` | Extended + case-insensitive |

**Troubleshoot**

| Symptom | Fix |
|---|---|
| No selection event | Sources all unreachable |
| Frequent "step" lines | Clock unstable — VM time-jump? |

---

### Task 10 — Capstone: NTP health report + cleanup

**Task statement:** *"Produce a one-paragraph clock-health report citing: System clock synchronized? Reference server? Current offset? Stratum? How many sources online?"*

```bash
cd /root/ntp-status-lab

SYNCED=$(timedatectl show -p NTPSynchronized | cut -d= -f2)
REF=$(chronyc tracking | awk -F': *' '/Reference ID/ {print $2}')
STRATUM=$(chronyc tracking | awk -F': *' '/Stratum/ {print $2}')
OFFSET=$(chronyc tracking | awk -F': *' '/Last offset/ {print $2}')
ONLINE=$(chronyc activity 2>/dev/null | awk '/sources online/ {print $1}')
LEAP=$(chronyc tracking | awk -F': *' '/Leap status/ {print $2}')

cat > 10-report.txt <<EOF
NTP health report — $(hostname) — $(date -Iseconds)

System clock synchronized:  ${SYNCED}
Leap status:                ${LEAP}
Current primary source:     ${REF}
Stratum:                    ${STRATUM}
Last offset:                ${OFFSET}
Sources online:             ${ONLINE}

How to reproduce:
  timedatectl show -p NTPSynchronized
  chronyc tracking
  chronyc sources -v
  chronyc activity
EOF

cat 10-report.txt
```

**Layer stack you built:**

```text
10-report.txt                       ← deliverable
  ├── 02-tracking.txt                ← full tracking output
  ├── 03-sources-v.txt               ← per-source table
  ├── 05-sourcestats.txt             ← long-term stats
  ├── 06-timedatectl.txt             ← systemd view
  ├── 07-activity.txt                ← one-line summary
  ├── 08-makestep.txt                ← step evidence (if any)
  └── 09-chronyd-journal.txt         ← daemon logs
```

**Cleanup**

```bash
cd /root
rm -rf /root/ntp-status-lab
ls -ld /root/ntp-status-lab 2>&1 | head -n 1
exit
```

**Troubleshoot**

| Symptom | Fix |
|---|---|
| Empty fields in report | Re-run after waiting 60 s for chrony to settle |
| `Leap status: Not synchronised` | `chronyc makestep`, then re-run |
| `ONLINE` empty | `chronyc activity` failing — daemon not running |

---

## 🔍 NTP Sync Decision Guide

```
"Is the clock OK?"               → timedatectl show -p NTPSynchronized
"Full status"                    → chronyc tracking
"Which servers?"                 → chronyc sources -v
"Long-term stability"            → chronyc sourcestats
"Force immediate alignment"      → sudo chronyc makestep
"Wait until synced"              → chronyc waitsync N M T H
"Daemon logs"                    → journalctl -u chronyd.service -b
"One-liner activity"             → chronyc activity
```

---

## Lab Checklist (10 Tasks)

- [ ] 01 Confirm `chronyd.service` running
- [ ] 02 `chronyc tracking` baseline
- [ ] 03 `chronyc sources -v`
- [ ] 04 Decode every marker
- [ ] 05 `chronyc sourcestats`
- [ ] 06 `timedatectl status` + `show -p NTPSynchronized`
- [ ] 07 `chronyc activity` and `waitsync`
- [ ] 08 `chronyc makestep` (force step)
- [ ] 09 Correlate with `journalctl -u chronyd.service`
- [ ] 10 NTP health report + cleanup

---

## ⚠️ Common Pitfalls

| Mistake | Symptom | Fix |
|---|---|---|
| `ntpq -p` on RHEL 9 | "command not found" | `ntp` package not installed; use `chronyc sources` |
| Forgetting `-v` with `chronyc sources` | No marker legend printed | Add `-v` |
| `chronyc makestep` without root | `400 BadRequest` | Use `sudo` |
| Disagreement between `tracking` and `timedatectl` | Confusion during triage | One usually updates first — wait 60 s |
| `Reach=0` interpreted as "broken" | Just hasn't polled yet | Wait one full poll interval |
| Treating `^?` as "down forever" | Source temporarily unreachable | Wait or check firewall |
| `^x` ignored | A source is lying — drop it | Edit `/etc/chrony.d/` or `/etc/chrony.conf` |
| Running on a host without UDP 123 outbound | Sources unreachable | Open firewall or pick reachable peers |

---

## 🎯 Career & Interview Strategy

**RHCSA candidate**
- "Verify NTP." Answer: `timedatectl status` and confirm "System clock synchronized: yes" + `chronyc sources -v` shows `^*`.

**RHCE candidate**
- Ansible health gate: `command: chronyc tracking` register, `failed_when: 'Leap status     : Normal' not in result.stdout`.

**SRE / Platform interview**
- Be ready to explain why Kerberos and etcd require sub-second clock skew (KDC ticket validity, etcd lease comparisons).

**DevOps**
- CI runners assert `timedatectl show -p NTPSynchronized=yes` before recording build start times.

**AI / MLOps**
- GPU training fleets often run `chronyc waitsync 60 0.01 0 1` in kickstart to ensure sub-10ms skew before NCCL init.

---

## 🔗 Related Labs

| Lab | Connection |
|---|---|
| Lab 107 — Configure Timezone and Time Sync | Sets up what this lab verifies |
| Lab 109 — Configure NTP Time Source | Where the `/etc/chrony.conf` server lines come from |
| Lab 101 — `journalctl` query | `chronyd.service` logs are queried with `-u` |
| Lab 106 — Service-Specific Journals | `-u chronyd.service` is the model query |

---

## 👤 Author

**Kelvin R. Tobias**
[kelvinintech.com](https://kelvinintech.com) · [GitHub](https://github.com/kelvintechnical) · [LinkedIn](https://www.linkedin.com/in/kelvin-r-tobias-211949219)
