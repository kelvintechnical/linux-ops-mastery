# Lab: Apply Recursive SELinux Contexts to a New Directory

**Series:** linux-ops-mastery — RHCSA SELinux Administration
**Status:** 📅 Planned — full walkthrough coming soon. The task definition below is exam-accurate; lab content (concept sections, task breakdowns, expected output, troubleshoot tables) has not yet been written.

---

## Task

Create a new top-level directory `/direct01`, configure it to inherit the SELinux file context of `/root` (using an equivalence rule), apply the contexts recursively, and prove the result with `ls -Zd` before and after.

### Steps to be covered

1. Confirm SELinux is **enforcing** with `getenforce`. If permissive, switch with `setenforce 1` for the duration of the lab.
2. Create the directory: `mkdir /direct01`.
3. Inspect the **default** context applied: `ls -Zd /direct01` and compare against `ls -Zd /root`. They will differ — `/direct01` will receive `default_t` or similar.
4. Add the SELinux equivalency rule: `semanage fcontext -a -e /root /direct01`. This tells SELinux: "treat `/direct01` and everything under it the same way you treat `/root`."
5. Apply the rule recursively to existing content: `restorecon -RFv /direct01`.
6. Re-run `ls -Zd /direct01` — its context now matches `/root`'s exactly.
7. Verify inheritance by creating a subdir/file inside `/direct01` and confirming the child inherits the expected context with `ls -Z`.

### Concept: equivalency vs explicit context

| Approach | Command | When to use |
|---|---|---|
| Equivalency rule | `semanage fcontext -a -e /src /dst` | "Treat `/dst` exactly like `/src`" — clean for cloned hierarchies |
| Explicit context | `semanage fcontext -a -t <type> '/dst(/.*)?'` | When you want a specific type, e.g. `httpd_sys_content_t` |
| One-shot relabel | `chcon -R --reference=/src /dst` | Temporary fix; lost on next `restorecon` |

### Career-arc connection

- **RHCSA** — every exam has at least one "non-default directory + correct SELinux context" task.
- **SRE / Platform** — moving a service's data directory off `/var` requires this exact pattern.

---

## Author

**Kelvin R. Tobias**
[kelvinintech.com](https://kelvinintech.com) · [GitHub](https://github.com/kelvintechnical) · [LinkedIn](https://www.linkedin.com/in/kelvin-r-tobias-211949219)
