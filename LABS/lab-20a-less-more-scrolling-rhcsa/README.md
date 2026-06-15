# Lab 20a: Scrolling Through Large Files (RHCSA) — `less`, `more`

**Series:** linux-ops-mastery — Text Processing & Filters · **Lab 20a of the Novice → RHCA path**  
**Certifications covered:** RHCSA EX200 (paging through logs and configs), SRE/DevOps (reading large logs without flooding the terminal)  
**Prerequisite:** [Lab 19c](../lab-19c-cat-concatenate-files-verify/) completed  
**Time Estimate:** 20–30 minutes  
**Difficulty:** Beginner

---

## 🎯 Today's Focus Coverage

> Stay on-subject via the ANCHOR rows; expand vocabulary via the NEW rows. Every row is exercised by a STEP below.

**⚓ Anchor — already learned (on-topic reuse)**

| # | Command / switch | Covered by |
|---|---|---|
| A1 | `cat` (and why it floods) | _Task 1 · Step 1_ |
| A2 | `seq` to build content | _Lab-wide setup_ |

**🆕 NEW this lab — introduced for the first time** (minimum 3)

| # | Command / switch | First taught in | Covered by |
|---|---|---|---|
| N1 | `less` + `/` `?` `n` `N` | Task 1 · Step 1 | _Task 1 · Step 1_ |
| N2 | `less -N` / `G` / `g` | Task 1 · Step 2 | _Task 1 · Step 2_ |
| N3 | `less +F` (follow mode) | Task 2 · Step 1 | _Task 2 · Step 1_ |
| N4 | `more` paging | Task 2 · Step 2 | _Task 2 · Step 2_ |

---

## 🎯 Objective

Read files too big for one screen without flooding your terminal. You will page through a large log with `less`, search forward (`/`) and backward (`?`), jump to the top (`g`) and bottom (`G`), show line numbers (`-N`), tail-follow live output (`+F`), and contrast it all with the older `more`. By the end you navigate any log confidently from the keyboard.

> **Note:** `less` is interactive. Run these commands and use the listed keys; the "expected output" describes what you should see on screen. Press `q` to quit the pager each time.

---

## 🧠 Concept

`cat` dumps a whole file to the terminal — fine for 10 lines, useless for 10,000. A **pager** shows one screen at a time and lets you move around. `less` is the modern pager: arrow/PageUp/PageDown to scroll, `/pattern` to search forward, `?pattern` backward, `n`/`N` for next/previous match, `g`/`G` for top/bottom, `-N` to number lines, and `+F` to "follow" a growing file like `tail -f` (Ctrl-C drops back to paging). `more` is the older, simpler pager (forward-mostly), still found on minimal systems. The mantra: *less is more* — `less` does everything `more` does and far more.

```
less big.log        → page; /error finds, n=next, q=quit
less -N big.log     → with line numbers
less +F big.log     → follow new lines (Ctrl-C to stop, q to quit)
more big.log        → simple forward pager (Space=page, q=quit)
```

> **Why this matters:** On the exam and on call you live in logs. Knowing `/`, `n`, `G`, and `+F` turns a 50,000-line log from a wall of text into a searchable, navigable document.

---

## 📚 Command Reference

| Command / key | Purpose | Notes |
|---|---|---|
| `less FILE` | Open the pager | `q` quits |
| `/pat` `?pat` | Search fwd / back | `n` next, `N` previous |
| `g` / `G` | Top / bottom | jump instantly |
| `less -N` | Show line numbers | toggle in-pager with `-N` |
| `less +F` | Follow growth | Ctrl-C to page, `q` to quit |
| `more FILE` | Simple pager | Space pages, `q` quits |

---

## 🧰 LAB-WIDE SETUP

**In plain English:** Build a sandbox with a large multi-line log to scroll through.

> Run this block **once** before Task 1. It defines a single sandbox root
> (`LAB_ROOT`) that every file in this lab lives under, so the Teardown
> section can wipe it in one safe command.

```bash
export LAB_ROOT=/tmp/lab-20
mkdir -p "$LAB_ROOT"
cd "$LAB_ROOT"
seq 1 500 | sed 's/^/line /' > big.log
echo "ERROR disk full" >> big.log
seq 501 1000 | sed 's/^/line /' >> big.log
wc -l big.log
echo "exit was: $?"
```

**Expected output:**

```
1001 big.log
exit was: 0
```

---

## TASK 1 of 2 — Page and search with `less`

**In plain English:** We open the big log, search for a needle, and jump around it.

---

### Step 1 of 2 — Search forward and back

**In plain English:** We open the log in `less` and find the `ERROR` line by searching.

```bash
cd "$LAB_ROOT"
less big.log
# Inside less, type:
#   /ERROR   then Enter   → jumps to the ERROR line
#   n                     → next match (none here, stays put / bell)
#   ?line 5               → search backward for "line 5"
#   q                     → quit
```

**Expected output (on screen):**

```
line 1
line 2
...
(after /ERROR Enter, the view jumps to:)
ERROR disk full
```

**Line-by-line breakdown:**

- `less big.log` → Open the file in the pager, showing the first screen.
- `/ERROR` → Search forward; `less` jumps to and highlights the next match.
- `?line 5` → Search backward from the cursor.

**New words in this step:**

- **pager** — a program that shows a file one screen at a time.
- **`/` and `?`** — search forward and backward inside `less`.

---

### Step 2 of 2 — Line numbers and top/bottom jumps

**In plain English:** We reopen with line numbers and jump to the end and start of the file.

```bash
cd "$LAB_ROOT"
less -N big.log
# Inside less, type:
#   G   → jump to the last line (line 1000)
#   g   → jump back to the first line
#   q   → quit
```

**Expected output (on screen):**

```
      1 line 1
      2 line 2
      3 line 3
... (line numbers on the left; G jumps to the bottom, g to the top)
```

**Line-by-line breakdown:**

- `less -N big.log` → Open with a line-number gutter on the left.
- `G` / `g` → Jump to the bottom / top instantly — vital in huge logs.

**New words in this step:**

- **`-N`** — show line numbers in the pager.
- **`g` / `G`** — jump to top / bottom of the file.

---

### Concept card (Task 1)

| Concept | What it does | Exam trap |
|---|---|---|
| `/` vs `?` | search fwd / back | `n`/`N` repeat the search |
| `g` / `G` | top / bottom | uppercase = bottom |
| `-N` | line numbers | helps cross-reference errors |

---

### Troubleshoot (Task 1)

| Symptom | Likely cause | Fix |
|---|---|---|
| Stuck in `less` | Don't know how to exit | Press `q` |
| Search wraps unexpectedly | Hit top/bottom | `n` continues; watch for "Pattern not found" |

---

## TASK 2 of 2 — Follow growth and the older `more`

**In plain English:** We follow a growing file like `tail -f`, then compare with `more`.

---

### Step 1 of 2 — Follow a growing file with `less +F`

**In plain English:** We open the log in follow mode while a background writer appends lines, watching them appear live.

```bash
cd "$LAB_ROOT"
( for i in $(seq 1 5); do echo "new entry $i"; sleep 1; done >> big.log ) &
less +F big.log
# In less follow mode you see new lines arrive; then:
#   Ctrl-C   → stop following, return to normal paging
#   q        → quit
```

**Expected output (on screen):**

```
...
line 1000
new entry 1
new entry 2
new entry 3
new entry 4
new entry 5
(Waiting for data... press Ctrl-C to stop)
```

**Line-by-line breakdown:**

- `( ... ) &` → Background writer that appends a line per second.
- `less +F big.log` → Open in follow mode; new lines appear as they're written — like `tail -f` but you can Ctrl-C and scroll back.

**New words in this step:**

- **follow mode (`+F`)** — `less` tails a growing file; Ctrl-C returns to paging.

---

### Step 2 of 2 — Page with the older `more`

**In plain English:** We open the same log with `more` to see the simpler, forward-only pager.

```bash
cd "$LAB_ROOT"
more big.log
# Inside more, type:
#   Space   → next page
#   Enter   → next line
#   /entry  → search forward
#   q       → quit
```

**Expected output (on screen):**

```
line 1
line 2
...
--More--(5%)
```

**Line-by-line breakdown:**

- `more big.log` → Open the simple pager; `--More--(5%)` shows progress.
- `Space` / `Enter` → Page / line forward; `more` is mostly forward-only.

**New words in this step:**

- **`more`** — the older, simpler forward pager; `less` superseded it.

---

### Concept card (Task 2)

| Concept | What it does | Exam trap |
|---|---|---|
| `less +F` | follow growth | Ctrl-C to scroll, `q` to quit |
| `more` | simple pager | limited backward movement |
| pipe to pager | `cmd | less` | page any command's output |

---

### Troubleshoot (Task 2)

| Symptom | Likely cause | Fix |
|---|---|---|
| `+F` never shows new lines | Nothing writing | Confirm the writer is running |
| `more` can't scroll back | By design | Use `less` instead |

---

## ✅ Lab Checklist

- [ ] Task 1 · Step 1 — Search forward and back
- [ ] Task 1 · Step 2 — Line numbers and top/bottom jumps
- [ ] Task 2 · Step 1 — Follow a growing file with `less +F`
- [ ] Task 2 · Step 2 — Page with the older `more`
- [ ] Every 🎯 Focus Coverage row (Anchor + NEW) mapped to a step
- [ ] 🧹 Teardown run — sandbox + any system state removed

---

## 🧹 Teardown

**In plain English:** Delete everything this lab created so the box is clean for the next run.

> Run this after you've verified the lab. `lab_teardown.sh` safely removes the single sandbox root — it refuses to touch `/`, `$HOME`, or any protected path. This lab changed **no** system state. If the background writer is still running, it will exit on its own after 5 seconds.

```bash
cd /tmp
bash lab_teardown.sh "$LAB_ROOT"     # = /tmp/lab-20
```

**Expected output:**

```
✅ Removed /tmp/lab-20 — lab workspace is clean.
```

---

## ⚠️ Common Pitfalls

| Mistake | Symptom | Fix |
|---|---|---|
| `cat`-ing a huge file | Terminal flooded | Use `less` |
| Forgetting `q` | "Stuck" in the pager | Press `q` to exit |
| Using `more` for big logs | Can't scroll back | Switch to `less` |

---

## 📌 Exam Strategy

Never `cat` a large log — open it in `less`, search with `/`, repeat with `n`, and jump with `g`/`G`. Pipe any verbose command into `less` to page its output. Use `+F` when you need live follow but want to scroll back.

- `less` searches; `/pat` then `n` is your log-hunting combo.
- `G` to the bottom is the fastest way to the newest entries.
- Pipe `journalctl`, `dmesg`, etc. into `less`.

---

## 🔗 Related Labs

- [Lab 20b — Scrolling Large Files (Ansible)](../lab-20b-less-more-scrolling-ansible/) — extracting page ranges without a pager
- [Lab 20c — Scrolling Large Files (Verify)](../lab-20c-less-more-scrolling-verify/) — prove the right lines were read
- [Lab 21a — Monitoring Live Log Files (RHCSA)](../lab-21a-tail-f-live-logs-rhcsa/) — `tail -f` for live following

---

## 👤 Author

**Kelvin R. Tobias**  
[kelvinintech.com](https://kelvinintech.com) · [GitHub](https://github.com/kelvintechnical) · [LinkedIn](https://www.linkedin.com/in/kelvin-r-tobias-211949219)
