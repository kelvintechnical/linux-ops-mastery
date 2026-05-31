# Lab: Bidirectional Bash Script with Argument Logic

**Series:** linux-ops-mastery — RHCSA Shell Scripting & Automation
**Status:** 📅 Planned — full walkthrough coming soon. The task definition below is exam-accurate; lab content (concept sections, task breakdowns, expected output, troubleshoot tables) has not yet been written.

---

## Task

Write a bash script that, given one argument, prints the **opposite** of two known strings. Specifically:

- If invoked as `./script.sh RHCE` → prints `RHCSA`
- If invoked as `./script.sh RHCSA` → prints `RHCE`
- If invoked with **no** argument → prints a usage message and exits with code `5`

### Steps to be covered

1. Create `/root/script.sh` (or `/usr/local/bin/script.sh`) and make it executable with `chmod +x`.
2. Implement the three-way logic using either a `case` statement or `if`/`elif`/`else`. Recommended:
   ```bash
   #!/bin/bash
   case "$1" in
     RHCE)  echo "RHCSA" ;;
     RHCSA) echo "RHCE" ;;
     "")    echo "Usage: $0 {RHCE|RHCSA}" >&2; exit 5 ;;
     *)     echo "Unknown argument: $1" >&2; exit 5 ;;
   esac
   ```
3. Test the three valid paths:
   - `./script.sh RHCE` → expect `RHCSA`, exit code `0`
   - `./script.sh RHCSA` → expect `RHCE`, exit code `0`
   - `./script.sh` → expect usage on stderr, exit code `5`
4. Verify exit codes with `echo $?` after each run.
5. Bonus: handle the unknown-argument case (anything besides `RHCE`/`RHCSA`) gracefully — also exit `5`.

### Concept: why exit codes matter on the RHCSA exam

The grader scripts run your script and check `$?`. A script that "looks right" but exits `0` when it should exit `5` will silently fail grading. Always:

- `exit 0` → success
- `exit N` for `1 ≤ N ≤ 255` → failure, with N being the specific failure mode

### Career-arc connection

- **RHCSA** — argument-validating scripts are a recurring scripting objective.
- **DevOps / CI** — every CI step is a script whose exit code is the pass/fail signal. The discipline you build here transfers directly.

---

## Author

**Kelvin R. Tobias**
[kelvinintech.com](https://kelvinintech.com) · [GitHub](https://github.com/kelvintechnical) · [LinkedIn](https://www.linkedin.com/in/kelvin-r-tobias-211949219)
