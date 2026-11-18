#!/usr/bin/env python3
"""Oregon unemployment work-search log: the arithmetic and the safe writes.

The weekly count is computed HERE, never re-derived in prose. Quote what this
script prints.

Oregon rules (per benefit week, Sunday-Saturday, named by its Saturday):
  - 2 direct employer contacts, six fields each
  - 3 additional work-seeking activities
  - surplus employer contacts count as additional activities:
      contacts   = employer-contacts rows + activities rows where counts_as == direct employer contact
      additional = max(0, contacts - 2) + activities rows where counts_as == job seeking activity

Files (all in my-search/work-search/):
  employer-contacts.csv, activities.csv, weekly-claims.csv

Run from the job-search-kit folder:
  python3 .claude/skills/log-work-search/uicsv.py week [YYYY-MM-DD]
  python3 .claude/skills/log-work-search/uicsv.py status [YYYY-MM-DD]          # any date inside the week
  python3 .claude/skills/log-work-search/uicsv.py from-pipeline [YYYY-MM-DD]   # applied rows not yet logged
  python3 .claude/skills/log-work-search/uicsv.py recent-files [YYYY-MM-DD]    # application files touched that week
  python3 .claude/skills/log-work-search/uicsv.py add contacts|activities <rows.json> [--allow-duplicates]
  python3 .claude/skills/log-work-search/uicsv.py filing-block [YYYY-MM-DD]
  python3 .claude/skills/log-work-search/uicsv.py record-filed <week date> <date filed> [notes]
Exit code 2 = a file is open (ask the user to close it). Exit code 3 = possible duplicates, nothing written.
"""
import csv
import datetime
import glob
import json
import os
import shutil
import sys


def kit_root():
    d = os.path.dirname(os.path.abspath(__file__))
    while d != os.path.dirname(d):
        if os.path.isdir(os.path.join(d, ".claude")) and os.path.isfile(os.path.join(d, "VERSION")):
            return d
        d = os.path.dirname(d)
    return os.getcwd()


KIT = kit_root()
DATA = os.path.join(KIT, "my-search")
WS = os.path.join(DATA, "work-search")
BACKUPS = os.path.join(DATA, ".backups", "work-search")
FILES = {
    "contacts": ("employer-contacts.csv", ["week_start", "week_ending", "date", "company",
                 "location_or_posting_id", "contact_method", "position", "outcome", "notes", "pipeline_id"]),
    "activities": ("activities.csv", ["week_start", "week_ending", "date", "activity_type", "counts_as",
                   "description", "notes", "pipeline_id"]),
    "claims": ("weekly-claims.csv", ["week_start", "week_ending", "claim_filed", "claim_paid",
               "date_filed", "notes"]),
}
CONTACT = "direct employer contact"
ACTIVITY = "job seeking activity"
ACTIVITY_TYPES = ["Searched job listings", "Reviewed/screened job postings", "Updated resume",
                  "Researched employer connections", "Networking outreach", "Attended workshop/event",
                  "Interview", "Additional employer contact", "Other"]
NEED_CONTACTS, NEED_ADDITIONAL = 2, 3
_backed_up = set()


def out(obj, code=0):
    print(json.dumps(obj, indent=1, ensure_ascii=False))
    sys.exit(code)


def path(kind):
    return os.path.join(WS, FILES[kind][0])


def parse_day(s=None):
    if not s:
        return datetime.date.today()          # the computer's local date, not UTC
    return datetime.date.fromisoformat(s.strip()[:10])


def week_of(day):
    start = day - datetime.timedelta(days=(day.weekday() + 1) % 7)   # back to Sunday
    return start, start + datetime.timedelta(days=6)


def load(kind):
    p = path(kind)
    cols = FILES[kind][1]
    if not os.path.exists(p):
        return list(cols), []
    with open(p, newline="", encoding="utf-8-sig") as fh:
        r = csv.DictReader(fh)
        header = [h for h in (r.fieldnames or []) if h]
        rows = [{h: (row.get(h) or "") for h in header} for row in r]
    for c in cols:
        if c not in header:
            header.append(c)
    return header, rows


def check_open(p):
    d, f = os.path.split(p)
    for lock in (os.path.join(d, "~$" + f), os.path.join(d, ".~lock." + f + "#")):
        if os.path.exists(lock):
            out({"open": True, "file": p,
                 "message": "Your " + f + " looks open in a spreadsheet. Please save and close it, then ask me again."}, 2)


def backup(p):
    if p in _backed_up or not os.path.exists(p):
        return None
    os.makedirs(BACKUPS, exist_ok=True)
    dest = os.path.join(BACKUPS, os.path.basename(p) + ".bak-" + datetime.datetime.now().strftime("%Y%m%d-%H%M%S"))
    shutil.copy2(p, dest)
    for old in sorted(glob.glob(os.path.join(BACKUPS, os.path.basename(p) + ".bak-*")), reverse=True)[3:]:
        os.remove(old)
    _backed_up.add(p)
    return dest


def save(kind, header, rows):
    p = path(kind)
    os.makedirs(WS, exist_ok=True)
    tmp = p + ".tmp"
    # Quote every field: semicolons already in the user's text survive spreadsheet imports intact.
    with open(tmp, "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=header, quoting=csv.QUOTE_ALL, extrasaction="ignore")
        w.writeheader()
        for r in rows:
            w.writerow({h: r.get(h, "") for h in header})
    with open(tmp, newline="", encoding="utf-8") as fh:
        if sum(1 for _ in csv.DictReader(fh)) != len(rows):
            os.remove(tmp)
            out({"error": "verification failed, nothing written"}, 1)
    os.replace(tmp, p)


def clean(v):
    return "" if v is None else str(v).replace(";", " -").replace("\r", " ").replace("\n", " ").strip()


def in_week(row, start):
    return (row.get("week_start") or "") == start.isoformat()


def status(day):
    start, end = week_of(day)
    _, contacts = load("contacts")
    _, acts = load("activities")
    c_rows = [r for r in contacts if in_week(r, start)]
    a_contact = [r for r in acts if in_week(r, start) and (r.get("counts_as") or "").strip().lower() == CONTACT]
    a_activity = [r for r in acts if in_week(r, start) and (r.get("counts_as") or "").strip().lower() == ACTIVITY]
    a_unlabeled = [r for r in acts if in_week(r, start) and (r.get("counts_as") or "").strip().lower() not in (CONTACT, ACTIVITY)]
    n_contacts = len(c_rows) + len(a_contact)
    surplus = max(0, n_contacts - NEED_CONTACTS)
    n_additional = surplus + len(a_activity)
    met_c, met_a = n_contacts >= NEED_CONTACTS, n_additional >= NEED_ADDITIONAL
    days_left = (end - datetime.date.today()).days
    lines = [
        "Week ending %s (Oregon unemployment):" % end.isoformat(),
        "  Direct employer contacts:  %d / %d  %s" % (n_contacts, NEED_CONTACTS, "met ✓" if met_c else "SHORT"),
        "  Additional activities:     %d / %d  %s" % (n_additional, NEED_ADDITIONAL, "met ✓" if met_a else "SHORT"),
        "     (%d surplus employer contact%s + %d logged activit%s)" % (
            surplus, "" if surplus == 1 else "s", len(a_activity), "y" if len(a_activity) == 1 else "ies"),
        "  Overall: %s" % ("MET" if met_c and met_a else "NOT MET YET"),
    ]
    return {
        "week_start": start.isoformat(), "week_ending": end.isoformat(),
        "contacts": n_contacts, "contacts_from_contacts_file": len(c_rows),
        "contacts_from_activities_file": len(a_contact), "surplus_contacts": surplus,
        "logged_activities": len(a_activity), "additional": n_additional,
        "contacts_met": met_c, "additional_met": met_a, "met": met_c and met_a,
        "days_left_in_week": days_left, "unlabeled_activity_rows": len(a_unlabeled),
        "status_text": "\n".join(lines),
    }


def from_pipeline(day):
    start, end = week_of(day)
    p = os.path.join(DATA, "pipeline.csv")
    if not os.path.exists(p):
        out({"week_ending": end.isoformat(), "candidates": [], "note": "no pipeline.csv yet"})
    with open(p, newline="", encoding="utf-8-sig") as fh:
        rows = list(csv.DictReader(fh))
    _, contacts = load("contacts")
    _, acts = load("activities")
    logged_ids = {(r.get("pipeline_id") or "").strip() for r in contacts + acts if (r.get("pipeline_id") or "").strip()}
    logged_keys = {((r.get("company") or "").lower(), (r.get("position") or "").lower(), r.get("date")) for r in contacts}
    cands, already, bad_dates = [], [], []
    for r in rows:
        if (r.get("status") or "").strip().lower() != "applied":
            continue
        raw = (r.get("date_applied") or "").strip()
        try:
            d = datetime.date.fromisoformat(raw[:10])
        except ValueError:   # applied but no usable date: surface it, don't guess a week
            bad_dates.append({"company": r.get("company"), "title": r.get("title"), "date_applied": raw})
            continue
        if not (start <= d <= end):
            continue
        rid = (r.get("id") or "").strip()
        key = ((r.get("company") or "").lower(), (r.get("title") or "").lower(), d.isoformat())
        if (rid and rid in logged_ids) or key in logged_keys:
            already.append(r.get("company"))
            continue
        url = r.get("url") or ""
        posting = url.rstrip("/").split("/")[-1].split("=")[-1] if url else ""
        loc = (r.get("location") or "").strip()
        cands.append({
            "week_start": start.isoformat(), "week_ending": end.isoformat(), "date": d.isoformat(),
            "company": r.get("company", ""),
            "location_or_posting_id": (loc + (" (posting %s)" % posting if posting else "")).strip(),
            "contact_method": (r.get("applied_via") or "").strip() or "?",
            "position": r.get("title", ""), "outcome": "Applied", "notes": "", "pipeline_id": rid,
        })
    out({"week_ending": end.isoformat(), "candidates": cands, "already_logged": already,
         "applied_rows_with_missing_or_odd_date": bad_dates})


def recent_files(day):
    start, end = week_of(day)
    lo = datetime.datetime.combine(start, datetime.time.min).timestamp()
    hi = datetime.datetime.combine(end, datetime.time.max).timestamp()
    hits = []
    for f in glob.glob(os.path.join(DATA, "applications", "*", "*")):
        m = os.path.getmtime(f)
        if lo <= m <= hi:
            hits.append({"file": os.path.relpath(f, KIT),
                         "modified": datetime.datetime.fromtimestamp(m).strftime("%Y-%m-%d %a")})
    out({"week_ending": end.isoformat(), "files": sorted(hits, key=lambda h: h["modified"])})


def add(kind, src, allow_dup):
    if kind not in ("contacts", "activities"):
        out({"error": "kind must be contacts or activities"}, 1)
    p = path(kind)
    check_open(p)
    new = json.load(open(src, encoding="utf-8"))
    header, rows = load(kind)
    problems, dups, ready = [], [], []
    for n in new:
        r = {k: clean(v) for k, v in n.items()}
        try:
            d = datetime.date.fromisoformat(r.get("date", "")[:10])
        except ValueError:
            problems.append({"row": n, "problem": "date must be YYYY-MM-DD"})
            continue
        s, e = week_of(d)
        r["week_start"], r["week_ending"] = s.isoformat(), e.isoformat()   # always derived, never typed
        if kind == "activities":
            cnt = (r.get("counts_as") or "").lower()
            if cnt not in (CONTACT, ACTIVITY):
                problems.append({"row": n, "problem": "counts_as must be '%s' or '%s'" % (ACTIVITY, CONTACT)})
                continue
            r["counts_as"] = cnt
            key = (r["date"], (r.get("activity_type") or "").lower(), (r.get("description") or "").lower())
            same = [x for x in rows if (x.get("date"), (x.get("activity_type") or "").lower(), (x.get("description") or "").lower()) == key]
        else:
            missing = [f for f in ("date", "company", "location_or_posting_id", "contact_method", "position", "outcome") if not r.get(f) or r.get(f) == "?"]
            if missing:
                problems.append({"row": n, "problem": "missing required field(s): " + ", ".join(missing)})
                continue
            key = (r["date"], r["company"].lower(), r["position"].lower())
            same = [x for x in rows if (x.get("date"), (x.get("company") or "").lower(), (x.get("position") or "").lower()) == key]
        pid = r.get("pipeline_id")
        if pid:
            same += [x for x in rows if x.get("pipeline_id") == pid and x not in same]
        if same and not allow_dup:
            dups.append({"new": r, "looks_like": same[0]})
            continue
        for k in r:
            if k not in header:
                header.append(k)
        ready.append(r)
    if problems or dups:
        out({"written": 0, "problems": problems, "possible_duplicates": dups,
             "message": "Nothing written. Fix the problems, or confirm duplicates with the user and re-run with --allow-duplicates."}, 3)
    b = backup(p)
    rows.extend(ready)
    save(kind, header, rows)
    out({"written": len(ready), "file": os.path.relpath(p, KIT), "backup": b})


def filing_block(day):
    start, end = week_of(day)
    _, contacts = load("contacts")
    _, acts = load("activities")
    lines = ["WORK SEARCH FOR THE WEEK ENDING %s" % end.isoformat(), ""]
    c = [r for r in contacts if in_week(r, start)]
    ac = [r for r in acts if in_week(r, start) and (r.get("counts_as") or "").lower() == CONTACT]
    n = 0
    for r in sorted(c, key=lambda x: x.get("date", "")):
        n += 1
        lines += ["EMPLOYER CONTACT %d" % n,
                  "Date: " + r.get("date", ""),
                  "Employer: " + r.get("company", ""),
                  "Location or job posting number: " + r.get("location_or_posting_id", ""),
                  "How you contacted them: " + r.get("contact_method", ""),
                  "Position or type of work: " + r.get("position", ""),
                  "Result: " + r.get("outcome", ""), ""]
    pipe = {}
    pp = os.path.join(DATA, "pipeline.csv")
    if os.path.exists(pp):
        with open(pp, newline="", encoding="utf-8-sig") as fh:
            pipe = {(x.get("id") or "").strip(): x for x in csv.DictReader(fh)}
    for r in sorted(ac, key=lambda x: x.get("date", "")):
        n += 1
        job = pipe.get((r.get("pipeline_id") or "").strip())
        if job:
            url = job.get("url") or ""
            posting = url.rstrip("/").split("/")[-1].split("=")[-1] if url else ""
            loc = ((job.get("location") or "") + (" (posting %s)" % posting if posting else "")).strip()
            lines += ["EMPLOYER CONTACT %d" % n,
                      "Date: " + r.get("date", ""),
                      "Employer: " + (job.get("company") or ""),
                      "Location or job posting number: " + loc,
                      "How you contacted them: " + (r.get("activity_type") or "Interview"),
                      "Position or type of work: " + (job.get("title") or ""),
                      "Result: " + ("Interviewed" if (r.get("activity_type") or "").lower() == "interview" else "Contacted"), ""]
        else:
            lines += ["EMPLOYER CONTACT %d" % n,
                      "Date: " + r.get("date", ""),
                      "Details: " + r.get("description", ""),
                      "  (Couldn't find this job in your spreadsheet. Fill in employer, location, position and result from the description.)", ""]
    a = [r for r in acts if in_week(r, start) and (r.get("counts_as") or "").lower() == ACTIVITY]
    for i, r in enumerate(sorted(a, key=lambda x: x.get("date", "")), 1):
        lines += ["OTHER WORK-SEEKING ACTIVITY %d" % i,
                  "Date: " + r.get("date", ""),
                  "Activity: " + r.get("activity_type", ""),
                  "Details: " + r.get("description", ""), ""]
    st = status(day)
    out({"week_ending": end.isoformat(), "block": "\n".join(lines).rstrip(),
         "status_text": st["status_text"], "met": st["met"]})


def record_filed(day, filed, notes=""):
    start, end = week_of(day)
    p = path("claims")
    check_open(p)
    header, rows = load("claims")
    hit = [r for r in rows if r.get("week_start") == start.isoformat()]
    if hit:
        r = hit[0]
    else:
        r = {h: "" for h in header}
        rows.append(r)
    r.update({"week_start": start.isoformat(), "week_ending": end.isoformat(), "claim_filed": "yes",
              "date_filed": parse_day(filed).isoformat()})
    if notes:
        r["notes"] = clean(notes)
    rows.sort(key=lambda x: x.get("week_start", ""))
    b = backup(p)
    save("claims", header, rows)
    # Weeks with logged evidence but no filing recorded: worth a question, never an assertion.
    _, contacts = load("contacts")
    _, acts = load("activities")
    logged = {x.get("week_start") for x in contacts + acts if x.get("week_start")}
    filed_weeks = {x.get("week_start") for x in rows if (x.get("claim_filed") or "").lower() == "yes"}
    out({"recorded": end.isoformat(), "backup": b,
         "weeks_with_evidence_but_no_filing_recorded": sorted(w for w in logged - filed_weeks if w < week_of(datetime.date.today())[0].isoformat())})


def main():
    a = sys.argv[1:]
    if not a:
        out({"error": __doc__}, 1)
    cmd, rest = a[0], a[1:]
    arg = rest[0] if rest else None
    if cmd == "week":
        s, e = week_of(parse_day(arg))
        out({"week_start": s.isoformat(), "week_ending": e.isoformat()})
    elif cmd == "status":
        out(status(parse_day(arg)))
    elif cmd == "from-pipeline":
        from_pipeline(parse_day(arg))
    elif cmd == "recent-files":
        recent_files(parse_day(arg))
    elif cmd == "add":
        add(rest[0], rest[1], "--allow-duplicates" in rest)
    elif cmd == "filing-block":
        filing_block(parse_day(arg))
    elif cmd == "record-filed":
        record_filed(parse_day(rest[0]), rest[1], " ".join(rest[2:]))
    elif cmd == "types":
        out({"activity_types": ACTIVITY_TYPES, "counts_as": [ACTIVITY, CONTACT]})
    else:
        out({"error": "unknown command " + cmd}, 1)


if __name__ == "__main__":
    main()
