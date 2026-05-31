# Lab 15b: Instant File Searching with `locate` (Ansible) — `updatedb.conf` + `updatedb`

- **Series:** linux-ops-mastery — File Operations & Shell Fundamentals
- **Trilogy:** `15a` → `15b` → `15c`
- **Prerequisite:** Lab 15a complete
- **Time Estimate:** 25–35 minutes
- **Tasks:** 2
- **Practice Directory (rotation #15):** `/srv/scratch`

> Ansible has no `locate` module. This lab uses **`ansible.builtin.dnf`**, **`ansible.builtin.lineinfile`** on `/etc/updatedb.conf`, and **`ansible.builtin.command`** for `updatedb` with explicit `changed_when`.

---

## Objective

Declaratively install `mlocate`, ensure `/srv/scratch` is in `PRUNEPATHS`, run `updatedb`, and verify with `ansible.builtin.command: locate` (read-only, `changed_when: false`).

---

## Lab-Wide Setup

```bash
sudo -i
mkdir -p /root/rhcsa_journal/lab-15b/playbooks
ansible --version | head -n 1
```

Copy `playbooks/task1.yml` and `task2.yml` from this repo into `/root/rhcsa_journal/lab-15b/playbooks/`.

---

## Task 1 — Install `mlocate` and run `updatedb`

**Practice directory:** `/etc` (package + timer) · index at `/var/lib/mlocate/`

### Warm-Up

```bash
dnf list installed mlocate 2>/dev/null | head -n 2
test -f /var/lib/mlocate/mlocate.db && echo "index exists" || echo "will build"
ansible localhost -m ping 2>/dev/null | head -n 3
```

### Run

```bash
ansible-playbook /root/rhcsa_journal/lab-15b/playbooks/task1.yml \
  2>&1 | tee /root/rhcsa_journal/lab-15b/task1/op.txt
locate -S | head -n 5
echo "exit was: $?"
```

### Journal

```bash
JDIR=/root/rhcsa_journal/lab-15b/task1
mkdir -p "$JDIR"
cp /root/rhcsa_journal/lab-15b/task1/op.txt "$JDIR/evidence.txt" 2>/dev/null || true
```

---

## Task 2 — `lineinfile` PRUNEPATHS + capstone probes

**Practice directory:** `/srv/scratch`

### Purpose

Playbook adds `/srv/scratch` to `PRUNEPATHS`, creates probe PEM files, runs `updatedb`, runs `locate '*.pem'`, asserts scratch path absent via `ansible.builtin.assert`.

### Run

```bash
ansible-playbook /root/rhcsa_journal/lab-15b/playbooks/task2.yml \
  2>&1 | tee /root/rhcsa_journal/lab-15b/task2/op.txt
echo "exit was: $?"
```

### Cleanup (playbook should remove probes; manual fallback)

```bash
rm -rf /etc/locate-lab-probe /srv/scratch/locate-lab 2>/dev/null
```

> **STOP — Lab 15c.**

---

## Lab 15b Checklist

- [ ] Task 1 — `dnf` + `updatedb` + index exists
- [ ] Task 2 — PRUNEPATHS + locate assertion passes

---

## Author

**Kelvin R. Tobias** — [kelvinintech.com](https://kelvinintech.com)
