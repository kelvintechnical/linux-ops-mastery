# Lab: Rootless Container with Bind Mount and systemd Auto-Start

**Series:** linux-ops-mastery — RHCSA Containers & Container Management
**Status:** 📅 Planned — full walkthrough coming soon. The task definition below is exam-accurate; lab content (concept sections, task breakdowns, expected output, troubleshoot tables) has not yet been written.

---

## Task

As an unprivileged user (`user80`), run a rootless podman container based on `ubi9` with a bind-mount, generate a user-level systemd unit for it, enable lingering so the container survives logout, and prove that the container auto-starts after a reboot **without** `user80` logging in.

### Steps to be covered

1. As root, create `user80` and a host directory to bind-mount: `mkdir -p /data01 && chown user80:user80 /data01`.
2. Switch to `user80` and start the container manually first:
   ```bash
   podman run -d --name databox -v /data01:/data01:Z registry.access.redhat.com/ubi9 sleep infinity
   ```
   - `:Z` relabels the bind-mount for SELinux on rootless podman — exam graders look for this.
3. Verify the container is running with `podman ps`.
4. Generate a user-level systemd unit:
   ```bash
   mkdir -p ~/.config/systemd/user
   podman generate systemd --new --files --name databox
   mv container-databox.service ~/.config/systemd/user/
   ```
5. Stop the manual container, then enable + start via systemd:
   ```bash
   podman stop databox && podman rm databox
   systemctl --user daemon-reload
   systemctl --user enable --now container-databox.service
   ```
6. As root, enable lingering for `user80` so user-level services start at boot without login:
   ```bash
   loginctl enable-linger user80
   ```
7. Reboot the host. Once back up — **without logging in as user80** — verify the container is running:
   ```bash
   sudo machinectl shell user80@ /bin/bash -c "podman ps"
   ```

### The three pieces that make rootless auto-start work

| Piece | Purpose |
|---|---|
| `podman generate systemd --new` | Produces a unit file whose `ExecStart` recreates the container on each start |
| `~/.config/systemd/user/` | User-level systemd unit directory (no root required to install) |
| `loginctl enable-linger USER` | Without this, user-level systemd shuts down when the user logs out |

### Career-arc connection

- **RHCSA 9 / 10** — rootless container + persistent systemd unit + linger is the canonical containers objective.
- **DevOps / Platform** — same pattern is how Kubernetes-less single-node deployments (homelab, edge, IoT) keep services up.

---

## Author

**Kelvin R. Tobias**
[kelvinintech.com](https://kelvinintech.com) · [GitHub](https://github.com/kelvintechnical) · [LinkedIn](https://www.linkedin.com/in/kelvin-r-tobias-211949219)
