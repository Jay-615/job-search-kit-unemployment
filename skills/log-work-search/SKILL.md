---
name: log-work-search
description: Keep the weekly work-search record for Oregon unemployment insurance (unemployment add-on). Oregon requires, for each Sunday–Saturday week, 2 direct employer contacts (six fields each) and 3 additional work-seeking activities. Proposes entries from what the user actually did (applications in the spreadsheet, searches, tailored resumes, interviews), logs only what the user confirms, checks whether the week is met, and prints a copy-paste block for the weekly claim on Frances Online. Use when the user says "log my work search", "am I covered for this week?", "get my unemployment claim ready", "I had an interview", or "I filed my claim".
argument-hint: "[a date in the week, default this week]"
---

# Log my work search (Oregon unemployment)

You keep an honest weekly record of the user's work search, so they can file their Oregon unemployment claim. For each week claimed, Oregon requires:

- **2 direct employer contacts**, each with six details: date, employer, location or job posting number, how they contacted the employer, the position or type of work, and the result.
- **3 additional work-seeking activities**: more employer contacts, updating a resume, searching job listings, networking, workshops, and so on.

Weeks run **Sunday through Saturday**. A week is named by its **ending date** (the Saturday). That's the date Frances Online asks for, so lead with it when talking to the user.

> **Honesty is the whole point.** The user attests to this record to a government agency. **Only record what genuinely happened.** Propose entries based on real evidence, and never invent, pad or round up. If you're unsure whether something counts, show it and let the user decide. A short, honest week is correct. A padded week is not.

**Stay in your lane.** This covers the work-search part of the claim only. The other eligibility questions (able to work, available for work, earnings) are the user's to answer. Don't remind them about those or comment on them.

All arithmetic and every write goes through the helper. **Quote the numbers it prints.** Never re-derive the weekly count in your own words. A count worked out in prose has been wrong before, in both directions.

```
python3 .claude/skills/log-work-search/uicsv.py <command>
```

## The files (in `my-search/work-search/`)

- `employer-contacts.csv`: direct employer contacts, one row each, with the six required details and a `pipeline_id` linking to the row in `my-search/pipeline.csv`.
- `activities.csv`: other work-seeking activities **and interviews**. Every row has `counts_as` set to either `job seeking activity` or `direct employer contact`. **An interview is a direct employer contact** (the strongest kind), so it goes here with `counts_as: direct employer contact`. The helper credits it as a contact.
- `weekly-claims.csv`: which weeks were filed, and when.

Link rows to the spreadsheet by **`pipeline_id`**, never by company name. Names drift between files.

## Step 1: Which week?

`uicsv.py week $ARGUMENTS` gives the week (default: this week). If today is Sunday or Monday, ask which they mean: "the week that just ended (ending <date>), or this new week?". People usually log right before filing for the week just finished.

Then show where it stands now: `uicsv.py status <date>`. Print its `status_text` as is.

## Step 2: Direct employer contacts

Contacts come from three places. Check all three, in this order:

1. **Applications in the spreadsheet.** `uicsv.py from-pipeline <date>` lists rows with `status` = `applied` and a `date_applied` inside the week that aren't logged yet. Each already has most of the six details. If `contact_method` comes back `?` (the `applied_via` cell was empty), ask how they applied ("on LinkedIn", "on the company's site", "emailed the hiring manager"). If it lists **applied rows with a missing or odd date**, ask about those too: when did they apply? Never guess a date.
2. **Evidence the spreadsheet can't see.** `uicsv.py recent-files <date>` lists tailored-resume folders touched that week. A folder touched for a job that isn't marked `applied` might mean an application they forgot to mark, or an interview. Ask about each one in a word or two. **A resume that was prepared but never sent is an activity ("Updated resume"), not a contact.**
3. **Ask** about anything else: "Any other contact with employers this week? A phone call, an email to a hiring manager, a job fair, an interview?" These never pass through the spreadsheet, so you have to ask.

## Step 3: Other activities

Propose activities from what actually happened, this conversation or earlier (look at file dates, not just this chat):

| Evidence | Activity type |
|---|---|
| A job scan ran that week (new rows in `pipeline.csv` with `first_seen` in the week) | Searched job listings |
| Scoring or reviewing jobs that week | Reviewed/screened job postings |
| A tailored resume made that week (`my-search/applications/…`) | Updated resume |
| Network add-on: mapping connections at a company | Researched employer connections |
| The user says they messaged or met a contact | Networking outreach |
| The user says they attended a workshop, webinar or job fair | Attended workshop/event |

One row per real event. Don't split one search session into three rows to reach a count. The valid types are listed by `uicsv.py types`.

## Step 4: Confirm, then save

Show the proposed rows as two short tables (contacts, activities) and ask: "Log these? (Recommended)" / "Change something" / "Cancel". Only after a yes, write them:

```bash
python3 .claude/skills/log-work-search/uicsv.py add contacts my-search/.cache/tmp/contacts.json
python3 .claude/skills/log-work-search/uicsv.py add activities my-search/.cache/tmp/activities.json
```

Each file holds a JSON list. Contacts need `date`, `company`, `location_or_posting_id`, `contact_method`, `position`, `outcome` (plus `pipeline_id`, `notes`). Activities need `date`, `activity_type`, `counts_as`, `description` (plus `pipeline_id`, `notes`). The helper fills in the week dates itself.

- **Exit code 3** means it wrote nothing: it found possible duplicates or missing details. Show the user what it found. Re-run with `--allow-duplicates` only if they confirm it really is a second, separate event.
- **Exit code 2** means a file is open in a spreadsheet. Ask them to close it.

Then delete the temporary files with `rm -rf my-search/.cache/tmp`.

## Step 5: Is the week covered?

Run `uicsv.py status <date>` again and print `status_text` exactly. The rule it applies:

- contacts = rows in the contacts file + activity rows marked `direct employer contact`
- additional activities = (contacts beyond the first 2) + activity rows marked `job seeking activity`

So five applications in a week covers both requirements with nothing else logged. **Don't tell the user they're short when the helper says met, and don't suggest moving a contact into the activities column.** A contact is always a contact. The helper already credits the surplus.

If it's not met, say plainly what's missing ("1 more employer contact and 2 more activities") and how many days are left in the week (`days_left_in_week`). If the week has already ended, say it as it is. Don't suggest back-dating anything.

## Step 6: The filing block

If the user is about to file (or asks), run `uicsv.py filing-block <date>` and show the `block` text in a code block, so it copies cleanly. It lists each employer contact with its fields in the order the Frances Online form asks for them, then the other activities. Say: "Copy each contact into Frances Online for the week ending <date>."

Show anything useful that the form doesn't ask for (notes, links) **separately, after the block**, so it can't be pasted in by accident.

## Step 7: After filing

When the user says they filed: `uicsv.py record-filed <date in week> <date filed>`. Suggest saving the state's confirmation (PDF or screenshot) in `my-search/work-search/filings/`.

The helper also reports **past weeks with logged evidence but no filing recorded**. Mention them as a question ("I don't have a record of filing for the week ending <date>. Did you?"), never as a statement. Missing paperwork isn't proof of anything.

## Rules

- Only log what happened, and only after the user confirms.
- Use the computer's local date. Never move an event to a different week to make a week work.
- Never write to these files except through the helper.
- Never fill in or submit anything on Frances Online. The user files the claim themselves.
- Rules can change. If the user mentions something different from what's here (a different number of contacts, a waiver, a reemployment program), believe them over this file, and suggest they check https://unemployment.oregon.gov.
