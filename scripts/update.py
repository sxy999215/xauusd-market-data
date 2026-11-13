#!/usr/bin/env python3
"""Hourly updater for sxy999215/xauusd-market-data.

Rebuilds every derived file from the merged 1-minute series, so any
mid-run inconsistency self-heals on the next run. Layout (unchanged):
  data/xauusd_1m.csv   full 1m series, datetime_utc,open,high,low,close,vol
  data/xauusd_5m.csv   5m aggregates on UTC boundaries, volume summed
  data/xauusd_1h.csv   1h aggregates on UTC boundaries, volume summed
  data/1m/YYYY-Www.csv 1m shards by ISO week, each under 500 KB
  data/raw/YYYY-MM-DD.json  decoded bars by UTC date, under 500 KB each
  data/jinrong_raw.json    last fetch envelope + full decoded series
  data/manifest.json       paths, counts, start/end, update time
  UPDATE_LOG.md            newest-first run log

Usage (run from the repo root):
  python3 scripts/update.py                 # live: calls jinrong_fetch
  python3 scripts/update.py --new-bars-json <file>
                                            # test: bars from a JSON file
                                            # {"bars": [...]} or a bare list
Exit 0 with NO_CHANGE when the fetch returns no new bars (weekend/holiday).
Stdlib only.
"""
import argparse
import csv
import json
import os
import sys
from datetime import datetime, timezone

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from jinrong_fetch import FetchNotWired, fetch_new_bars  # noqa: E402

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
DATA = os.path.join(ROOT, "data")
CSV_HEAD = "datetime_utc,open,high,low,close,vol"


def utc(dt):
    return datetime.fromtimestamp(dt, tz=timezone.utc)


def fmt_ts(t):
    return utc(t).strftime("%Y-%m-%d %H:%M:%S")


def fmt_price(x):
    return f"{float(x):.2f}"


def fmt_vol(x):
    return str(int(round(float(x))))


def bar_row(b):
    return [fmt_ts(b["time"]), fmt_price(b["open"]), fmt_price(b["high"]),
            fmt_price(b["low"]), fmt_price(b["close"]), fmt_vol(b["vol"])]


def read_csv(path):
    bars = []
    with open(path, newline="") as f:
        for row in csv.DictReader(f):
            bars.append({
                "time": int(datetime.strptime(
                    row["datetime_utc"], "%Y-%m-%d %H:%M:%S"
                ).replace(tzinfo=timezone.utc).timestamp()),
                "open": float(row["open"]), "high": float(row["high"]),
                "low": float(row["low"]), "close": float(row["close"]),
                "vol": float(row["vol"]),
            })
    return bars


def write_csv(path, bars):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(CSV_HEAD.split(","))
        for b in bars:
            w.writerow(bar_row(b))


def aggregate(bars, step_seconds):
    """Bucket bars by UTC clock boundary. The bucket label is the timestamp
    of its FIRST bar (the repo's convention: day-start buckets read 22:01,
    not 22:00, because the first 1m bar of the day is 22:01)."""
    out = []
    cur = None
    cur_bucket = None
    for b in bars:
        bucket = (b["time"] // step_seconds) * step_seconds
        if cur is None or bucket != cur_bucket:
            cur = {"time": b["time"], "open": b["open"], "high": b["high"],
                   "low": b["low"], "close": b["close"], "vol": 0.0}
            cur_bucket = bucket
            out.append(cur)
        cur["high"] = max(cur["high"], b["high"])
        cur["low"] = min(cur["low"], b["low"])
        cur["close"] = b["close"]
        cur["vol"] += b["vol"]
    return out


def write_shards_1m(bars):
    by_week = {}
    for b in bars:
        d = utc(b["time"])
        iso = d.isocalendar()
        by_week.setdefault(f"{iso[0]}-W{iso[1]:02d}", []).append(b)
    # drop shards that no longer have bars
    shard_dir = os.path.join(DATA, "1m")
    for name in os.listdir(shard_dir):
        if name.endswith(".csv") and name[:-4] not in by_week:
            os.remove(os.path.join(shard_dir, name))
    files = []
    for week in sorted(by_week):
        week_bars = by_week[week]
        write_csv(os.path.join(shard_dir, f"{week}.csv"), week_bars)
        files.append({"path": f"data/1m/{week}.csv", "rows": len(week_bars),
                      "start": fmt_ts(week_bars[0]["time"]),
                      "end": fmt_ts(week_bars[-1]["time"])})
    return files


def write_shards_raw(bars):
    by_day = {}
    for b in bars:
        by_day.setdefault(utc(b["time"]).strftime("%Y-%m-%d"), []).append(b)
    raw_dir = os.path.join(DATA, "raw")
    for name in os.listdir(raw_dir):
        if name.endswith(".json") and name[:-5] not in by_day:
            os.remove(os.path.join(raw_dir, name))
    files = []
    for day in sorted(by_day):
        day_bars = by_day[day]
        with open(os.path.join(raw_dir, f"{day}.json"), "w") as f:
            json.dump({"date": day, "count": len(day_bars), "bars": day_bars}, f)
        files.append({"path": f"data/raw/{day}.json", "rows": len(day_bars),
                      "start": fmt_ts(day_bars[0]["time"]),
                      "end": fmt_ts(day_bars[-1]["time"])})
    return files


def prepend_log(now_utc, latest, counts):
    path = os.path.join(ROOT, "UPDATE_LOG.md")
    lines = open(path).read().splitlines()
    # find the table separator line (|---|---|...) and insert after it
    sep = next(i for i, l in enumerate(lines) if l.startswith("|---"))
    row = (f"| {now_utc} | {latest} | {counts['1m']} | {counts['5m']} | "
           f"{counts['1h']} | Hourly update |")
    lines.insert(sep + 1, row)
    with open(path, "w") as f:
        f.write("\n".join(lines) + "\n")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--new-bars-json")
    args = ap.parse_args()

    if args.new_bars_json:
        data = json.load(open(args.new_bars_json))
        new_bars = data["bars"] if isinstance(data, dict) else data
    else:
        try:
            fetched = fetch_new_bars()
        except FetchNotWired as e:
            print(f"SKIP: {e}")
            return 0
        new_bars = fetched["bars"]

    old = read_csv(os.path.join(DATA, "xauusd_1m.csv"))
    by_time = {b["time"]: b for b in old}
    n_new = 0
    for b in sorted(new_bars, key=lambda x: x["time"]):
        if b["time"] not in by_time:
            n_new += 1
        by_time[b["time"]] = {
            "time": int(b["time"]), "open": float(b["open"]),
            "high": float(b["high"]), "low": float(b["low"]),
            "close": float(b["close"]), "vol": float(b["vol"])}
    bars = [by_time[t] for t in sorted(by_time)]
    if n_new == 0 and not args.new_bars_json:
        print("NO_CHANGE: no new bars (weekend/holiday or nothing fetched)")
        return 0

    bars_5m = aggregate(bars, 300)
    bars_1h = aggregate(bars, 3600)
    write_csv(os.path.join(DATA, "xauusd_1m.csv"), bars)
    write_csv(os.path.join(DATA, "xauusd_5m.csv"), bars_5m)
    write_csv(os.path.join(DATA, "xauusd_1h.csv"), bars_1h)
    week_files = write_shards_1m(bars)
    raw_files = write_shards_raw(bars)

    now = datetime.now(timezone.utc)
    now_s = now.strftime("%Y-%m-%d %H:%M:%S")
    counts = {"1m": len(bars), "5m": len(bars_5m), "1h": len(bars_1h)}
    manifest = {
        "updated_at_utc": now_s,
        "latest_kline_utc": fmt_ts(bars[-1]["time"]),
        "counts": counts,
        "status": "complete",
        "files": week_files + raw_files + [
            {"path": "data/xauusd_1h.csv", "rows": len(bars_1h),
             "start": fmt_ts(bars_1h[0]["time"]),
             "end": fmt_ts(bars_1h[-1]["time"])},
            {"path": "data/xauusd_5m.csv", "rows": len(bars_5m),
             "start": fmt_ts(bars_5m[0]["time"]),
             "end": fmt_ts(bars_5m[-1]["time"])},
        ],
        "source": "jinrong",
    }
    with open(os.path.join(DATA, "manifest.json"), "w") as f:
        json.dump(manifest, f, indent=2)
    prepend_log(now_s, fmt_ts(bars[-1]["time"]), counts)
    print(f"OK: +{n_new} new 1m bars, latest {fmt_ts(bars[-1]['time'])}, "
          f"counts 1m={counts['1m']} 5m={counts['5m']} 1h={counts['1h']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
