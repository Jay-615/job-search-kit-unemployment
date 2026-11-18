# Manifest

Files the job-search-kit installer (`add-addon`) copies into a job-search-kit folder. Sources are relative to this add-on; destinations are relative to the job-search-kit folder. Destinations are only ever under `.claude/skills/` or `.claude/agents/`. Update, reinstall and removal all use this list, and nothing else is touched.

| source | destination |
|---|---|
| skills/log-work-search/SKILL.md | .claude/skills/log-work-search/SKILL.md |
| skills/log-work-search/uicsv.py | .claude/skills/log-work-search/uicsv.py |

## Data this add-on creates (in the user's private folder, never removed by uninstall)

- `my-search/work-search/employer-contacts.csv`
- `my-search/work-search/activities.csv`
- `my-search/work-search/weekly-claims.csv`
- `my-search/work-search/filings/` (where the user saves the state's confirmations)

## Settings it reads from `my-search/profile.md` → `## Add-ons`

- `unemployment: installed`, set by the installer
- `unemployment_version: <x.y.z>`, set by the installer
