# Lab: Display Logical Volumes — `lvs`, `lvdisplay`, `lvscan`

- **Series:** linux-ops-mastery — RHCSA LVM
- **Subjects covered:** the LV-level "display" verbs (`lvs` for tables, `lvdisplay [-m]` for verbose blocks, `lvscan` for re-discovery), default `lvs` columns (LV, VG, Attr, LSize, Pool, Origin, Data%, Meta%, Move, Log, Cpy%Sync, Convert), the 10-character `lv_attr` flag string decoded position-by-position (`-wi-a-----`, `swi-a-s---`, `Vwi-a-tz--`, etc.), useful add-on columns (`segtype`, `stripes`, `stripesize`, `chunksize`, `origin`, `pool_lv`, `lv_layout`, `lv_role`, `lv_tags`, `lv_seg_count`, `seg_start_pe`, `seg_size_pe`, `devices`), `lvs --units b|m|g|h` and `lvs --reportformat json`, `lvs --select` filters (`lv_role=thin`, `lv_attr=~^V`, `data_percent>80`, `origin=lv_app`, `lv_tags=prod`), `lvs -a` (show hidden internal LVs like `_tdata`, `_tmeta`, `_rimage`), `lvdisplay --maps` (per-segment LE→PE map — what physically backs this LV?), the difference between `LV Status` (`available`/`NOT available`) and the `a` bit in `lv_attr` (activation), reading the `Open count` field to know if anything is using the LV, scripting "find every LV with data_percent over 80%" or "snapshot every LV tagged prod," parsing `lvs` JSON in Python and Ansible, monitoring patterns
- **Career arcs covered:** RHCSA (EX200 — "show LV size and origin"), RHCE (Ansible facts), SRE (LV-fill alerting + thin-pool overcommit dashboards), DevOps (CI guards on thin-pool data_percent), AI / MLOps (track snapshot accumulation per experiment)
- **Prerequisite:** Lab 125 (lvcreate)
- **Time Estimate:** 30 to 45 minutes
- **Difficulty arc:** Task 1 sandbox with diverse LV types · Task 2 default `lvs` · Task 3 custom columns · Task 4 `lvs -a` hidden LVs · Task 5 JSON output · Task 6 `lvdisplay --maps` segment view · Task 7 `--select` filters · Task 8 decode `lv_attr` · Task 9 monitoring-ready Prometheus exporter · Task 10 capstone + cleanup

---

## Objective

Become fluent with LV-level inspection. By the end you can answer "show me every thin-provisioned LV with data_percent over 80%," "which PV holds which segment of this LV," and "produce JSON of all LV state for Ansible" — all without reaching for awk or sed.

The capstone is: *"Across a VG containing linear / striped / snapshot / thin-pool / thin LVs, produce three reports: a human table grouped by `lv_role`, JSON of every LV's segment layout, and a Prometheus metrics dump suitable for `node_exporter`."*

> **Lab safety note:** Read-only verbs. Safe to run on production.

---

## Concept: `lvs` Mirrors `pvs`/`vgs`

Same SQL-cursor mental model:

```
   ┌─────────────────────────────────────────────────────────────┐
   │   lvs                                                        │
   │    ├── -o COLS / -o +COL          ← project                  │
   │    ├── --sort [-]COL              ← order by                 │
   │    ├── --select "EXPR"            ← where                    │
   │    ├── --units b|m|g|h            ← units                    │
   │    ├── --reportformat json        ← machine-readable         │
   │    ├── -a                         ← include hidden internal LVs│
   │    └── --noheadings --separator , ← script-friendly          │
   └─────────────────────────────────────────────────────────────┘
```

> **Why this matters:** Internal LVs (`_tdata`, `_tmeta`, `_rimage_N`, `_rmeta_N`) are hidden from `lvs` by default but exist as device-mapper targets. Pass `-a` to see them when debugging RAID or thin pool issues.

---

## 📜 Why `lvs` Has So Many Columns — The Story

When LVM2 added new LV types (mirror → raid → thin → cache → raid1/4/5/6/10/integrity), each shipped with new attributes. Rather than add new commands, the LVM team extended `lvs` with **lots** of columns and a `--select` filter. Today the available columns cover:

- Plain-LV facts (`lv_size`, `lv_attr`, `segtype`)
- Snapshot facts (`origin`, `data_percent`)
- Thin facts (`pool_lv`, `data_percent`, `metadata_percent`)
- RAID facts (`raid_sync_action`, `raid_mismatch_count`, `sync_percent`)
- Cache facts (`cache_read_misses`, `cache_dirty_blocks`)
- Layout facts (`lv_role`, `lv_layout`)

That is why `lvs --help | wc -l` is intimidating. You learn the **15 columns you actually use** and rely on `lvs -h` or `man lvs` for the rest.

> **The point of the story:** `lvs` is a query interface, not a fixed report. Build the query you need.

---

## 👪 The LV Display Family

```
Tabular
├── lvs
├── lvs -o COLS                         ← projection
├── lvs -o +COL                         ← add
├── lvs -a                              ← include internal hidden LVs
├── lvs --sort [-]COL
├── lvs --select EXPR
├── lvs --units h|b|m|g
├── lvs --noheadings
├── lvs --separator ,
└── lvs --reportformat json

Verbose
├── lvdisplay
├── lvdisplay VG/LV
└── lvdisplay --maps VG/LV              ← segment layout

Discovery
└── lvscan                              ← rare; re-read PVs to find LVs
```

---

## 📚 Common lvs Columns

| Column | Meaning |
|---|---|
| `lv_name` | LV name |
| `vg_name` | VG name |
| `lv_attr` | 10-char flag string |
| `lv_size` | Allocated size (apparent for thin) |
| `pool_lv` | Backing thin pool (thin LVs only) |
| `origin` | Origin LV (snapshots only) |
| `data_percent` | Used data % (snapshot / thin / cache) |
| `metadata_percent` | Used meta % (thin pool / cache) |
| `move_pv` | `pvmove` in progress, source PV |
| `mirror_log` | Mirror log device (legacy mirror) |
| `copy_percent` | Sync % during pvmove / mirror init |
| `convert_lv` | `lvconvert` in progress |
| `segtype` | linear / striped / raid1 / thin / thin-pool / cache / snapshot |
| `stripes` | stripe count |
| `stripesize` | stripe unit size |
| `chunksize` | snapshot/thin chunk size |
| `devices` | Underlying segment devices |
| `lv_role` | public / private (private = internal) |
| `lv_layout` | high-level layout name |
| `lv_tags` | user tags |

---

## 🎯 Career Pathway Sidebar

| Level | Why this lab matters |
|---|---|
| **RHCSA candidate** | "Report LV size and FS type" is exam-table material. |
| **RHCE candidate** | `lvs --reportformat json` → Ansible facts. |
| **SRE / Platform** | Thin-pool overcommit dashboards driven by `lvs`. |
| **DevOps** | CI guard: refuse deploy if any thin-pool data_percent > 80%. |
| **AI / MLOps** | Snapshot-accumulation tracking per experiment. |

---

## 🔧 The 10 Tasks

---

### Task 1 — Sandbox with diverse LV types

```bash
sudo -i
mkdir -p /root/lvs-lab && cd /root/lvs-lab

for n in 1 2 3 4; do
  IMG=/var/tmp/lvs-pv-$n.img
  truncate -s 1G "$IMG"
  L=$(sudo losetup --find --show "$IMG")
  eval "LOOP_$n=$L"
done

sudo pvcreate "$LOOP_1" "$LOOP_2" "$LOOP_3" "$LOOP_4" >/dev/null
sudo vgcreate vg_demo "$LOOP_1" "$LOOP_2" "$LOOP_3" "$LOOP_4" >/dev/null

sudo lvcreate -L 200M -n lv_app vg_demo                               >/dev/null
sudo lvcreate --type striped -i 2 -I 64K -L 200M -n lv_fast vg_demo   >/dev/null
sudo lvcreate -s -L 50M -n lv_app_snap vg_demo/lv_app                  >/dev/null
sudo lvcreate --type thin-pool -L 200M -n thin_pool vg_demo            >/dev/null
sudo lvcreate --thin -V 1G -n lv_thin1 vg_demo/thin_pool               >/dev/null

sudo lvchange --addtag prod vg_demo/lv_app vg_demo/lv_fast >/dev/null
sudo lvchange --addtag dev  vg_demo/lv_thin1               >/dev/null

sudo lvs vg_demo | tee 01-lvs-initial.txt
```

---

### Task 2 — Default `lvs`

```bash
cd /root/lvs-lab
sudo lvs | tee 02-default.txt
```

**Expected output:**

```text
  LV          VG      Attr       LSize   Pool      Origin Data%  Meta%  Move Log Cpy%Sync Convert
  lv_app      vg_demo owi-aos--- 200.00m
  lv_app_snap vg_demo swi-a-s---  50.00m            lv_app  0.00
  lv_fast     vg_demo -wi-a----- 200.00m
  lv_thin1    vg_demo Vwi-a-tz--   1.00g thin_pool         0.00
  thin_pool   vg_demo twi-aotz-- 200.00m                   0.00   10.94
```

---

### Task 3 — Custom columns

```bash
cd /root/lvs-lab

sudo lvs -o lv_name,segtype,stripes,stripesize,chunksize,origin,pool_lv,data_percent,metadata_percent,lv_role | tee 03-explicit.txt
sudo lvs -o +lv_tags,devices | tee 03-additive.txt
```

**Reading it left to right:** `lv_role` is the cleanest column for filtering "real" LVs from internals — `public` means user-visible, `private` is for hidden machinery.

**Expected output (excerpt):**

```text
  LV          Type      #Str Stripe Chunk  Origin  Pool      Data%  Meta% Role
  lv_app      linear      1     0     0                                   public
  lv_app_snap snapshot    1     0    4.00k lv_app           0.00         public
  lv_fast     striped     2 64.00k     0                                   public
  lv_thin1    thin        1     0     0           thin_pool 0.00          public
  thin_pool   thin-pool   1     0   64.00k                  0.00 10.94    public
```

---

### Task 4 — Hidden internal LVs with `-a`

```bash
cd /root/lvs-lab

sudo lvs -a -o lv_name,lv_role,lv_attr,lv_size vg_demo | tee 04-with-internal.txt
```

**Reading it left to right:** `-a` reveals the under-the-hood pieces:
- `thin_pool_tdata` — data backing of the thin pool
- `thin_pool_tmeta` — metadata backing of the thin pool
- `lvol0_pmspare` — spare metadata area
- `[N]` brackets around hidden LV names

**The story:** When a thin pool reports metadata pressure, you must extend `_tmeta`, not the pool itself. `lvs -a` is how you find the right name.

**Expected output (excerpt):**

```text
  LV                  Role                       Attr       LSize
  [lvol0_pmspare]     private,pool,spare         ewi-------   4.00m
  lv_app              public                     owi-aos--- 200.00m
  lv_app_snap         public,snapshot,thinsnap   swi-a-s---  50.00m
  lv_fast             public                     -wi-a----- 200.00m
  lv_thin1            public,origin              Vwi-a-tz--   1.00g
  thin_pool           public                     twi-aotz-- 200.00m
  [thin_pool_tdata]   private,pool,data          Twi-ao---- 200.00m
  [thin_pool_tmeta]   private,pool,metadata      ewi-ao----   4.00m
```

---

### Task 5 — JSON output

```bash
cd /root/lvs-lab

sudo lvs --reportformat json -o lv_name,lv_size,segtype,origin,pool_lv,data_percent,lv_tags vg_demo | jq . | tee 05-pretty.json

sudo lvs --reportformat json -o lv_name,segtype,data_percent --select 'segtype=thin || segtype=snapshot' vg_demo | jq '.report[0].lv' | tee 05-thinandsnap.json
```

**Expected output (`05-thinandsnap.json`):**

```json
[
  {
    "lv_name": "lv_app_snap",
    "segtype": "linear",
    "data_percent": "0.00"
  },
  {
    "lv_name": "lv_thin1",
    "segtype": "thin",
    "data_percent": "0.00"
  }
]
```

---

### Task 6 — `lvdisplay --maps` segment view

```bash
cd /root/lvs-lab

sudo lvdisplay --maps /dev/vg_demo/lv_fast | tee 06-maps-fast.txt
sudo lvdisplay --maps /dev/vg_demo/lv_app  | tee 06-maps-app.txt
```

**Reading it left to right:** `--maps` prints **logical extents → physical extents** for the LV. For striped LVs, you see two segments (one per stripe) interleaved. For linear LVs, one contiguous segment.

**The story:** Reading this view confirms a striped LV is **actually** striped across the right PVs. It is also how you find candidates for `pvmove` (LE on a PV you want to drain).

**Expected output (excerpt for striped):**

```text
  --- Segments ---
  Logical extents 0 to 49:
    Type            striped
    Stripes         2
    Stripe size     64.00 KiB

    Stripe 0:
      Physical volume   /dev/loop10
      Physical extents  0 to 24

    Stripe 1:
      Physical volume   /dev/loop11
      Physical extents  0 to 24
```

---

### Task 7 — `--select` WHERE clause

```bash
cd /root/lvs-lab

sudo lvs --select 'lv_tags=prod'       -o lv_name,lv_tags,lv_size | tee 07-prod.txt
sudo lvs --select 'segtype=thin'        -o lv_name,segtype,pool_lv | tee 07-thin.txt
sudo lvs --select 'origin!=""'          -o lv_name,origin           | tee 07-snaps.txt
sudo lvs --select 'data_percent>0'      -o lv_name,data_percent     | tee 07-active.txt
sudo lvs --select 'lv_size>100m && lv_size<500m' -o lv_name,lv_size | tee 07-medium.txt
```

**Reading it left to right:** Selection language ops:
- `=`, `!=` (string/tag)
- `<`, `<=`, `>`, `>=` (size, percent)
- `=~`, `!~` (regex on string)
- `&&`, `||`, `!` (logical)
- `""` (empty)

**The story:** `--select` is the single most underused LVM feature. It removes thousands of lines of awk-pipeline glue from production scripts.

---

### Task 8 — Decode `lv_attr` (10 chars)

```bash
cd /root/lvs-lab

cat > 08-lvattr.txt <<'EOF'
lv_attr is 10 characters:

  1. Volume type:
     m=mirrored, M=mirrored without initial sync, o=origin,
     O=origin with merging snapshot, s=snapshot, S=invalid snapshot,
     p=pvmove, v=virtual, i=mirror/raid image, I=out-of-sync image,
     l=mirror log, c=conversion, V=thin volume, t=thin pool,
     T=thin pool data, e=raid/thin metadata, r=raid, R=raid w/o sync,
     -=normal LV

  2. Permissions:
     w=writable, r=read-only, R=read-only activation override

  3. Allocation policy:
     a=anywhere, c=contiguous, i=inherited, l=cling, n=normal
     (uppercase = locked)

  4. Fixed minor:
     m / -

  5. State:
     a=active, h=historical, s=suspended, I=invalid snapshot,
     S=invalid suspended snapshot, m=snapshot merge failed,
     M=suspended snapshot (merge failed), d=mapped device
     present w/o tables, i=mapped device present w/ inactive table,
     c=check needed (raid), X=invalid

  6. Open:
     o=open (in use)

  7. Target type:
     C=cache, m=mirror, r=raid, s=snapshot, t=thin, u=unknown,
     v=virtual, -=other

  8. Newly-allocated zero block flag:
     z / -

  9. Volume health:
     p=partial, r=refresh needed, m=mismatches exist,
     w=writemostly, X=invalid, -=ok

  10. SkipActivation flag:
     k / -

Common values:
  -wi-a-----  → linear LV, writable, inherited alloc, active, idle           (default LV)
  owi-aos---  → origin LV, writable, active, OPEN, snapshot-target           (lv_app while mounted with snapshot present)
  swi-a-s---  → snapshot LV, writable, active, snapshot-target
  Vwi-a-tz--  → thin volume, active, thin-target, zeroed
  twi-aotz--  → thin pool, active, OPEN, thin-target, zeroed
EOF

sudo lvs -a -o lv_name,lv_attr,lv_role | tee 08-attr.txt
cat 08-lvattr.txt
```

---

### Task 9 — Prometheus metrics

```bash
cd /root/lvs-lab

cat > 09-prom.sh <<'EOF'
#!/usr/bin/env bash
sudo lvs --noheadings --units b --separator , \
  -o lv_name,vg_name,lv_size,segtype,data_percent,metadata_percent,pool_lv,origin,lv_tags 2>/dev/null \
| awk -F, '
  function trim(s) { gsub(/^ +| +$/, "", s); return s }
  {
    lv  = trim($1); vg = trim($2); sz = trim($3); sub(/B$/, "", sz)
    typ = trim($4); dp = trim($5); mp = trim($6); pool = trim($7); orig = trim($8); tag = trim($9)
    if (tag == "") tag = "none"
    printf "lvm_lv_size_bytes{vg=\"%s\",lv=\"%s\",type=\"%s\",tag=\"%s\"} %d\n", vg, lv, typ, tag, sz
    if (dp != "")  printf "lvm_lv_data_percent{vg=\"%s\",lv=\"%s\",type=\"%s\",tag=\"%s\"} %s\n", vg, lv, typ, tag, dp
    if (mp != "")  printf "lvm_lv_metadata_percent{vg=\"%s\",lv=\"%s\",type=\"%s\",tag=\"%s\"} %s\n", vg, lv, typ, tag, mp
  }
'
EOF
chmod +x 09-prom.sh
./09-prom.sh | tee 09-metrics.txt
```

**Expected output (excerpt):**

```text
lvm_lv_size_bytes{vg="vg_demo",lv="lv_app",type="linear",tag="prod"} 209715200
lvm_lv_size_bytes{vg="vg_demo",lv="lv_fast",type="striped",tag="prod"} 209715200
lvm_lv_size_bytes{vg="vg_demo",lv="thin_pool",type="thin-pool",tag="none"} 209715200
lvm_lv_data_percent{vg="vg_demo",lv="thin_pool",type="thin-pool",tag="none"} 0.00
lvm_lv_metadata_percent{vg="vg_demo",lv="thin_pool",type="thin-pool",tag="none"} 10.94
```

---

### Task 10 — Capstone report + cleanup

```bash
cd /root/lvs-lab

cat > 10-report.txt <<EOF
LV display report — $(hostname) — $(date -Iseconds)

All LVs (default):
$(sudo lvs vg_demo)

All LVs grouped by role (with internals):
$(sudo lvs -a -o lv_name,lv_role,lv_attr,lv_size vg_demo --sort lv_role)

JSON (thin + snapshot only):
$(sudo lvs --reportformat json --select 'segtype=thin || segtype=snapshot' -o lv_name,segtype,pool_lv,origin,data_percent vg_demo | jq .)

Maps for striped LV:
$(sudo lvdisplay --maps /dev/vg_demo/lv_fast | sed -n '/--- Segments/,/Open count/p' | head -n 25)

Prometheus metrics:
$(./09-prom.sh)

Recommendation:
  - Alert on lvm_lv_data_percent > 80% for thin-pool and snapshot LVs.
  - Use --select for queries; avoid awk on default output.
  - --reportformat json is the Ansible interface.
EOF
cat 10-report.txt
```

**Cleanup**

```bash
sudo lvremove -fy vg_demo
sudo vgremove -fy vg_demo
sudo pvremove -fy "$LOOP_1" "$LOOP_2" "$LOOP_3" "$LOOP_4"
for n in 1 2 3 4; do
  eval "L=\$LOOP_$n"
  sudo losetup -d "$L"
done
sudo rm -f /var/tmp/lvs-pv-*.img

cd /root
rm -rf /root/lvs-lab
exit
```

---

## 🔍 LV Display Decision Guide

```
"List all LVs"                  → lvs
"Including internal LVs"        → lvs -a
"Specific columns / sortable"   → lvs -o ... --sort ... --noheadings --separator ,
"Filter by attribute"           → lvs --select 'EXPR'
"One LV in detail"              → lvdisplay VG/LV
"Segment-by-segment LE→PE"      → lvdisplay --maps VG/LV
"JSON for Ansible / monitoring" → lvs --reportformat json
```

---

## ✅ Lab Checklist (10 Tasks)

- [ ] 01 Diverse LV sandbox
- [ ] 02 Default `lvs`
- [ ] 03 Custom columns
- [ ] 04 `lvs -a` hidden LVs
- [ ] 05 JSON output
- [ ] 06 `lvdisplay --maps`
- [ ] 07 `--select` filters
- [ ] 08 Decode `lv_attr`
- [ ] 09 Prometheus metrics
- [ ] 10 Capstone + cleanup

---

## ⚠️ Common Pitfalls

| Mistake | Symptom | Fix |
|---|---|---|
| Forgetting `-a` when debugging thin pools | "tmeta not visible" | `lvs -a` |
| awk math on mixed units | Wrong totals | Always `--units b` |
| Misreading `lv_attr` middle chars | Wrong conclusion about state | Read all 10 characters |
| Trusting cached `lvs` after `pvremove` | Stale rows | `pvscan --cache` |
| `--select` with quotes wrong | "Selection error" | Quote the whole expression |
| Reading `LV Status` instead of `lv_attr` activation bit | Inconsistent answer | They're the same fact; pick one |

---

## 🎯 Career & Interview Strategy

**RHCSA candidate**
- Default `lvs` is plenty. Memorize `lvs -o +segtype,origin`.

**RHCE candidate**
- Ansible: `lvs --reportformat json` → register → `from_json`.

**SRE / Platform interview**
- "How do you find thin pools near full?" → `lvs --select 'segtype=thin-pool && data_percent>80'`.

**DevOps**
- CI gate: refuse deploy if `lvs --select 'segtype=thin-pool && data_percent>90'` returns rows.

**AI / MLOps**
- Snapshot accumulation tracker: `lvs --select 'origin!=""'` rolled up per experiment tag.

---

## 🔗 Related Labs

| Lab | Connection |
|---|---|
| Lab 122 — `pvs`/`pvdisplay` | PV layer (same patterns) |
| Lab 124 — `vgs`/`vgdisplay` | VG layer (same patterns) |
| Lab 125 — `lvcreate` | Builds what you inspect |
| Lab 128 — `lvextend` | Grow LVs you display |

---

## 👤 Author

**Kelvin R. Tobias**
[kelvinintech.com](https://kelvinintech.com) · [GitHub](https://github.com/kelvintechnical) · [LinkedIn](https://www.linkedin.com/in/kelvin-r-tobias-211949219)
