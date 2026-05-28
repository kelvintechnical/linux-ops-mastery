# RHCSA v10 — Commands Required Per Objective

> Reference index for [linux-ops-mastery](./README.md) — pairs the official Red Hat RHCSA EX200 v10 objectives with the exact commands that satisfy them. Use this alongside the lab [roadmap](./roadmap.md) to find the canonical command for any exam task.

**Source:** Compiled from the official Red Hat RHCSA v10 (EX200) objectives list. Versions noted as `.RHEL8` / `.RHEL9` mark items specific to those releases.

**How to use this file:**

1. Skim the **Commands by Module** tables (Mod 04 – Mod 24) to find the command for a specific operation.
2. Cross-reference the **Official RHCSA v10 Objectives Index** at the bottom to confirm the exam-blueprint mapping.
3. Every command listed below also appears in at least one lab in this repo — search the repo for the command to find its lab.

---

## Commands by Module

---

## Mod 04: Getting Started / Navigation / File Management

| Objective | Commands |
|---|---|
| Navigate directory paths | `cd`, `pwd`, `ls -la`, `tree` |
| File & directory management | `cp`, `mv`, `rm -rf`, `mkdir -p`, `touch`, `ln -s`, `ln` |
| Remote login | `ssh user@host`, `ssh -i KEY`, `ssh-keygen` |
| Web console | `systemctl enable --now cockpit.socket` |

---

## Mod 05: Text Processing

| Objective | Commands |
|---|---|
| stdin/stdout/stderr | `>`, `>>`, `2>`, `2>/dev/null`, `&>`, `2>&1` |
| Pipelines | `\|`, `tee`, `tee -a` |
| Text tools | `cat`, `head -n`, `tail -n`, `tail -f`, `less`, `wc -l`, `echo` |
| Search | `grep -i`, `grep -v`, `grep -E`, `grep -r`, `grep -n` |
| Find files | `find / -name`, `find -type f`, `find -user`, `find -perm /4000` |
| Locate | `locate`, `updatedb` |
| Docs | `man`, `man -k`, `apropos`, `whatis`, `info` |

---

## Mod 06: Text Editors

| Objective | Commands |
|---|---|
| vim modes | `vim FILE` → `i` insert, `Esc` normal, `:wq` save, `:q!` quit |
| vim editing | `dd` delete line, `yy` yank, `p` paste, `u` undo, `/pattern` search |
| vim replace | `:%s/old/new/g` |

---

## Mod 07: User & Group Administration

| Objective | Commands |
|---|---|
| Create users | `useradd -m -s /bin/bash USER`, `useradd -d HOME -M USER` |
| Modify users | `usermod -aG GROUP USER`, `usermod -L` (lock), `usermod -U` (unlock) |
| Delete users | `userdel -r USER` |
| Create groups | `groupadd GROUP`, `groupmod -n NEW OLD` |
| Passwords | `passwd USER`, `passwd -l USER`, `passwd -e USER` |
| Password aging | `chage -M 90 USER`, `chage -W 7 USER`, `chage -E DATE`, `chage -l USER` |
| Sudo access | `visudo`, `visudo -f /etc/sudoers.d/FILE` |
| Switch user | `su - USER`, `sudo -i`, `sudo -u USER CMD` |
| Inspect | `id USER`, `id -nG USER`, `getent passwd USER`, `getent group GRP` |

---

## Mod 08: Permissions & ACLs

| Objective | Commands |
|---|---|
| View permissions | `ls -l`, `ls -Z`, `stat FILE` |
| Set permissions | `chmod 644`, `chmod 755`, `chmod -R`, `chmod u+s`, `chmod g+s`, `chmod +t` |
| Ownership | `chown USER:GROUP FILE`, `chown -R`, `chgrp GROUP` |
| Special perms | `chmod 4755` (SUID), `chmod 2770` (SGID), `chmod 1777` (sticky) |
| ACLs | `setfacl -m u:USER:rwx FILE`, `setfacl -m g:GRP:rx`, `setfacl -m d:u:USER:rwx DIR` |
| View ACLs | `getfacl FILE` |
| Remove ACLs | `setfacl -b FILE`, `setfacl -x u:USER FILE` |
| Attributes | `chattr +i FILE` (immutable), `chattr +a FILE` (append-only), `lsattr` |
| umask | `umask 022`, `umask 027`, `umask -S` |
| Links | `ln FILE HARDLINK`, `ln -s TARGET SYMLINK` |

---

## Mod 09: Boot & Service Management

| Objective | Commands |
|---|---|
| Boot process | `systemctl get-default`, `systemctl set-default multi-user.target` |
| Services | `systemctl start\|stop\|restart\|reload SERVICE` |
| Enable/disable | `systemctl enable --now SERVICE`, `systemctl disable --now SERVICE` |
| Mask | `systemctl mask SERVICE`, `systemctl unmask SERVICE` |
| Inspect | `systemctl status SERVICE`, `systemctl cat SERVICE`, `systemctl list-units` |
| Reload daemon | `systemctl daemon-reload` |
| Targets | `systemctl isolate rescue.target`, `systemctl isolate emergency.target` |
| GRUB | `grub2-mkconfig -o /boot/grub2/grub.cfg`, `grub2-set-default 0`, `grubby --info=ALL` |
| Reset root pw | `init=/bin/bash` at GRUB → `mount -o remount,rw /` → `passwd` |
| Analyze boot | `systemd-analyze`, `systemd-analyze blame` |

---

## Mod 10: Filesystem Management

| Objective | Commands |
|---|---|
| Identify devices | `lsblk -f`, `blkid`, `df -hT`, `findmnt` |
| MBR partitions | `fdisk /dev/sdX` → `n` new, `t` type, `p` print, `w` write |
| GPT partitions | `gdisk /dev/sdX` → same keys; `parted mklabel gpt` |
| Re-read table | `partprobe /dev/sdX` |
| Create filesystems | `mkfs.xfs -L LABEL /dev/sdX`, `mkfs.ext4 -L LABEL /dev/sdX` |
| Swap | `mkswap /dev/sdX`, `swapon /dev/sdX`, `swapon --show` |
| Mount | `mount /dev/sdX /mnt`, `mount -a`, `umount /mnt` |
| Persistent mount | edit `/etc/fstab` with UUID from `blkid`; test with `mount -a` |
| Repair | `fsck -y /dev/sdX`, `xfs_repair /dev/sdX` |
| Info | `xfs_info /mountpoint`, `dumpe2fs -h /dev/sdX`, `tune2fs -L LABEL /dev/sdX` |

---

## Mod 11: LVM & Swap

| Objective | Commands |
|---|---|
| Physical volumes | `pvcreate /dev/sdX`, `pvs`, `pvdisplay`, `pvremove /dev/sdX` |
| Volume groups | `vgcreate VG /dev/sdX`, `vgs`, `vgdisplay`, `vgextend VG /dev/sdX`, `vgremove VG` |
| Logical volumes | `lvcreate -L 1G -n LV VG`, `lvs`, `lvdisplay`, `lvremove -f /dev/VG/LV` |
| Extend LV | `lvextend -L +1G -r /dev/VG/LV` (`-r` resizes filesystem too) |
| Grow filesystem | `xfs_growfs /mountpoint`, `resize2fs /dev/VG/LV` |
| Swap LV | `lvcreate -L 2G -n swap VG` → `mkswap` → `swapon` → add to fstab |

---

## Mod 12: Network Management

| Objective | Commands |
|---|---|
| View network | `ip addr`, `ip link`, `ip route`, `ss -tuna` |
| nmcli basics | `nmcli con show`, `nmcli dev status` |
| Static IP | `nmcli con mod NAME ipv4.addresses IP/24 ipv4.gateway GW ipv4.dns DNS ipv4.method manual` |
| Apply changes | `nmcli con up NAME` |
| IPv6 | `nmcli con mod NAME ipv6.addresses ADDR/64 ipv6.method manual` |
| Hostname | `hostnamectl set-hostname NAME`, `hostnamectl status` |
| DNS test | `dig NAME`, `dig +short NAME`, `getent hosts NAME` |
| Text UI | `nmtui` |

---

## Mod 13: Package Management

| Objective | Commands |
|---|---|
| DNF install | `dnf install -y PKG`, `dnf remove PKG`, `dnf update` |
| DNF search | `dnf search STR`, `dnf provides FILE`, `dnf info PKG` |
| DNF groups | `dnf group list`, `dnf group install "GROUP"` |
| DNF modules | `dnf module list`, `dnf module enable STREAM`, `dnf module install PROFILE` |
| Repos | `dnf repolist`, `dnf config-manager --add-repo URL`, `dnf clean all` |
| RPM inspect | `rpm -q PKG`, `rpm -qi PKG`, `rpm -ql PKG`, `rpm -qf FILE`, `rpm -V PKG` |
| GPG key | `rpm --import KEY` |

---

## Mod 14: SSH

| Objective | Commands |
|---|---|
| Key gen | `ssh-keygen -t ed25519 -N "" -f ~/.ssh/id_ed25519` |
| Copy key | `ssh-copy-id -i ~/.ssh/id_ed25519.pub user@host` |
| Connect | `ssh -i KEYFILE user@host`, `ssh -p PORT user@host` |
| SSH config | edit `/etc/ssh/sshd_config` → `PermitRootLogin no`, `PasswordAuthentication no` |
| Restart sshd | `systemctl restart sshd` |
| Transfer | `scp -P PORT FILE user@host:PATH`, `rsync -avz SRC user@host:DST` |

---

## Mod 15 & 16: Firewall & SELinux

| Objective | Commands |
|---|---|
| Firewall zones | `firewall-cmd --get-active-zones`, `firewall-cmd --get-default-zone` |
| Add service | `firewall-cmd --permanent --add-service=http`, `firewall-cmd --reload` |
| Add port | `firewall-cmd --permanent --add-port=8080/tcp`, `firewall-cmd --reload` |
| Verify | `firewall-cmd --list-all` |
| SELinux mode | `getenforce`, `setenforce 1`, edit `/etc/selinux/config` |
| Context | `ls -Z FILE`, `chcon -t TYPE FILE`, `restorecon -Rv PATH` |
| Persistent context | `semanage fcontext -a -t TYPE 'REGEX'`, then `restorecon -Rv PATH` |
| Ports | `semanage port -a -t TYPE -p tcp NUM`, `semanage port -l` |
| Booleans | `getsebool -a \| grep SERVICE`, `setsebool -P BOOL on` |
| Troubleshoot | `ausearch -m avc -ts recent`, `sealert -a /var/log/audit/audit.log` |

---

## Mod 17: NFS & Automount

| Objective | Commands |
|---|---|
| NFS server | edit `/etc/exports`, `systemctl enable --now nfs-server`, `exportfs -rv` |
| NFS client | `mount -t nfs SERVER:/export /mnt`, add to `/etc/fstab` with `_netdev` |
| Automount | edit `/etc/auto.master` and `/etc/auto.MAPNAME`, `systemctl enable --now autofs` |
| Verify | `showmount -e SERVER`, `findmnt`, `df -hT` |

---

## Mod 18: Backup & Compression

| Objective | Commands |
|---|---|
| tar create | `tar -czf archive.tar.gz DIR/`, `tar -cjf archive.tar.bz2 DIR/`, `tar -cJf archive.tar.xz DIR/` |
| tar extract | `tar -xzf FILE -C /dest`, `tar -xjf FILE`, `tar -xJf FILE` |
| tar list | `tar -tvf FILE` |
| tar with ACL/SELinux | `tar --selinux --acls --xattrs -czf FILE DIR/` |
| Compress | `gzip -k FILE`, `bzip2 -k FILE`, `xz -k FILE` |
| Remote copy | `scp -r DIR user@host:PATH`, `rsync -avz --delete SRC user@host:DST` |

---

## Mod 19: Bash Scripting

| Objective | Commands / Syntax |
|---|---|
| Variables | `VAR=value`, `echo $VAR`, `export VAR` |
| Arguments | `$1 $2`, `$#` (count), `$@` (all args) |
| Conditionals | `if [ -f FILE ]; then ... fi`, `if [ $? -eq 0 ]` |
| Loops | `for i in $(seq 1 5); do ... done`, `while read line; do ... done` |
| Exit codes | `exit 0`, `exit 1`, `$?` |
| Strict mode | `set -euo pipefail` |
| Heredoc | `cat <<'EOF' > FILE ... EOF` |
| Execute | `chmod +x script.sh`, `bash script.sh`, `./script.sh` |

---

## Mod 20: Cron & Scheduling

| Objective | Commands |
|---|---|
| User crontab | `crontab -e`, `crontab -l`, `crontab -r` |
| System cron | edit `/etc/crontab`, `/etc/cron.d/FILE` (needs USERNAME field) |
| at jobs | `at now + 5 minutes`, `atq`, `atrm JOBNUM` |
| Enable atd | `systemctl enable --now atd` |
| Allow/deny | `/etc/cron.allow`, `/etc/cron.deny`, `/etc/at.allow`, `/etc/at.deny` |

---

## Mod 21: NTP / Chrony

| Objective | Commands |
|---|---|
| Status | `timedatectl status`, `timedatectl list-timezones` |
| Set timezone | `timedatectl set-timezone America/New_York` |
| Enable NTP | `timedatectl set-ntp true` |
| Chrony | `chronyc sources`, `chronyc tracking`, `chronyc makestep` |
| Config | edit `/etc/chrony.conf` → `server NTP_SERVER iburst` |
| Restart | `systemctl restart chronyd` |

---

## Mod 22: Logs & Journal

| Objective | Commands |
|---|---|
| View journal | `journalctl`, `journalctl -b`, `journalctl -b -1` |
| Filter unit | `journalctl -u SERVICE --no-pager` |
| Filter priority | `journalctl -p err`, `journalctl -p warning` |
| Time filter | `journalctl --since "1h ago"`, `journalctl --since "2026-05-01"` |
| Follow | `journalctl -f` |
| Kernel | `journalctl -k`, `dmesg` |
| SELinux/audit | `ausearch -m avc -ts today`, `ausearch -i` |
| Log files | `tail -f /var/log/messages`, `tail -f /var/log/secure` |
| Write log | `logger -t TAG -p local0.info "MESSAGE"` |
| Disk usage | `journalctl --disk-usage`, `journalctl --vacuum-size=500M` |

---

## Mod 23: Process Management & Tuning

| Objective | Commands |
|---|---|
| View processes | `ps aux`, `ps -ef`, `ps -eo pid,ppid,ni,user,cmd` |
| Interactive | `top` → `Shift+M` (mem), `Shift+P` (cpu), `k` (kill) |
| Kill | `kill -9 PID`, `killall PROC`, `pkill -f PATTERN` |
| Find PID | `pgrep -l NAME`, `pgrep -u USER` |
| Priority | `nice -n 10 CMD`, `renice -n 5 -p PID` |
| Jobs | `jobs`, `bg %N`, `fg %N`, `Ctrl+Z` (suspend) |
| Tuned | `tuned-adm recommend`, `tuned-adm profile NAME`, `tuned-adm active` |

---

## Mod 24: Containers (Podman)

| Objective | Commands |
|---|---|
| Pull & run | `podman pull IMAGE`, `podman run --name NAME -d -p 8080:80 IMAGE` |
| Manage | `podman ps -a`, `podman stop NAME`, `podman start NAME`, `podman rm NAME` |
| Images | `podman images`, `podman rmi IMAGE` |
| Exec | `podman exec -it NAME /bin/bash` |
| Logs | `podman logs -f NAME` |
| Inspect | `podman inspect NAME` |
| Rootless systemd | `podman generate systemd --new --files --name NAME` |
| Linger | `loginctl enable-linger USER` |
| Enable | `systemctl --user enable --now NAME.service` |
| Registry | `skopeo inspect docker://REGISTRY/IMAGE` |

---

## Cross-Cutting Commands

These commands appear on essentially every exam task — verification, persistence checks, and the universal "exit code" reflex.

```bash
# Always verify after any change
$?                          # exit code check
echo "exit: $?"

# Always check persistence
systemctl is-enabled SERVICE
firewall-cmd --list-all --permanent
mount -a && df -hT
ls -Z PATH
getfacl PATH
blkid
```

---

## Official RHCSA v10 Objectives Index

Below is the official Red Hat RHCSA v10 (EX200) objective list, as published by Red Hat. Items tagged `.RHEL8` / `.RHEL9` are version-scoped variants.

### 1. Understand and use essential tools

- **1.a** Access a shell prompt and issue commands with correct syntax
- **1.b** Use input-output redirection (`>`, `>>`, `|`, `2>`, etc.)
- **1.c** Use `grep` and regular expressions to analyze text
- **1.d** Access remote systems using SSH
- **1.e** Log in and switch users in multiuser targets
- **1.f** Archive, compress, unpack, and uncompress files using `tar`, `star`, `gzip`, and `bzip2`
- **1.g** Create and edit text files
- **1.h** Create, delete, copy, and move files and directories
- **1.i** Create hard and soft links
- **1.j** List, set, and change standard ugo/rwx permissions
- **1.k** Locate, read, and use system documentation including `man`, `info`, and files in `/usr/share/doc`

### 2. Create simple shell scripts

- **2.a** Conditionally execute code (use of: `if`, `test`, `[]`, etc.)
- **2.b** Use looping constructs (`for`, etc.) to process file, command line input
- **2.c** Process script inputs (`$1`, `$2`, etc.)
- **2.d** Processing output of shell commands within a script
- **2.e.RHEL8** Processing shell command exit codes

### 3. Operate running systems

- **3.a** Boot, reboot, and shut down a system normally
- **3.b** Boot systems into different targets manually
- **3.c** Interrupt the boot process in order to gain access to a system
- **3.d** Identify CPU/memory intensive processes, adjust process priority with `renice`, and kill processes
- **3.e** Adjust process scheduling
- **3.f** Manage tuning profiles
- **3.g** Locate and interpret system log files and journals
- **3.h** Preserve system journals
- **3.i** Start, stop, and check the status of network services
- **3.j** Securely transfer files between systems

### 4. Configure local storage

- **4.a** List, create, delete partitions on MBR and GPT disks
- **4.b** Create and remove physical volumes
- **4.c** Assign physical volumes to volume groups
- **4.d** Create and delete logical volumes
- **4.e** Configure systems to mount file systems at boot by Universally Unique ID (UUID) or label
- **4.f** Add new partitions and logical volumes, and swap to a system non-destructively

### 5. Create and configure file systems

- **5.a** Create, mount, unmount, and use vfat, ext4, and xfs file systems
- **5.b** Mount and unmount network file systems using NFS
- **5.c.RHEL9** Configure Autofs
- **5.d** Extend existing logical volumes
- **5.e** Create and configure set-GID directories for collaboration
- **5.e.RHEL8** Configure disk compression
- **5.f.RHEL8** Manage layered storage
- **5.g** Diagnose and correct file permission problems

### 6. Deploy, configure, and maintain systems

- **6.a** Schedule tasks using `at` and `cron`
- **6.b** Start and stop services and configure services to start automatically at boot
- **6.c** Configure systems to boot into a specific target automatically
- **6.d** Configure time service clients
- **6.e** Install and update software packages from Red Hat Network, a remote repository, or from the local file system
- **6.f.RHEL8** Work with package module streams
- **6.g** Modify the system bootloader

### 7. Manage basic networking

- **7.a** Configure IPv4 and IPv6 addresses
- **7.b** Configure hostname resolution
- **7.c** Configure network services to start automatically at boot
- **7.d** Restrict network access using `firewall-cmd` / firewall

### 8. Manage users and groups

- **8.a** Create, delete, and modify local user accounts
- **8.b** Change passwords and adjust password aging for local user accounts
- **8.c** Create, delete, and modify local groups and group memberships
- **8.d** Configure superuser access

### 9. Manage security

- **9.a** Configure firewall settings using `firewall-config`, `firewall-cmd`, or `iptables`
- **9.b.RHEL8** Create and use file access control lists
- **9.b.RHEL9** Manage default file permissions
- **9.c** Configure key-based authentication for SSH
- **9.d** Set enforcing and permissive modes for SELinux
- **9.e** List and identify SELinux file and process context
- **9.ex.RHEL9** Manage SELinux Ports
- **9.f** Restore default file contexts
- **9.g** Use boolean settings to modify system SELinux settings
- **9.h** Diagnose and address routine SELinux policy violations

### 10. Manage containers

- **10.a** Find and retrieve container images from a remote registry
- **10.b** Inspect container images
- **10.c** Perform container management using commands such as `podman` and `skopeo`
- **10.cx.RHEL9** Build a container from a Containerfile
- **10.d** Perform basic container management such as running, starting, stopping, and listing running containers
- **10.e** Run a service inside a container
- **10.f** Configure a container to start automatically as a systemd service
- **10.g** Attach persistent storage to a container

---

## Related Documents

- [README](./README.md) — main project overview, RHCSA lab index, certification path
- [roadmap.md](./roadmap.md) — full 212+ lab roadmap with status flags
- [Tech-Affiliates-How-To-Install-Linux.md](./Tech-Affiliates-How-To-Install-Linux.md) — install guide for first-time learners
