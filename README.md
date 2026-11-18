# job-search-kit-unemployment

**This is an add-on for [job-search-kit](https://github.com/Jay-615/job-search-kit), for people claiming Oregon unemployment benefits. To install it, open your job-search-kit folder in the Claude app and say "add the unemployment add-on."** There's nothing to download from this page yourself.

## What it does

Oregon asks you to show, every week you claim, that you made **2 direct employer contacts** (with six details each) and **3 other work-seeking activities**. The requirement is reasonable. Keeping the record and typing it into Frances Online each week is the tedious part. This add-on does the record-keeping:

- It builds each week's record from what you actually did. Applications you marked `applied` in your spreadsheet become employer contacts automatically, and searches and tailored resumes become activities. It asks about anything it can't see, like interviews, phone calls and job fairs.
- It tells you whether the week is covered, and what's missing if not. Extra applications count toward the activities too, so five applications covers a whole week.
- When you're ready to file, it prints the week's contacts in the order Frances Online asks for them, ready to copy.
- It keeps track of which weeks you've filed.

Say **log my work search** any time during the week, or right before you file.

## What it won't do

- **Log anything that didn't happen, or that you haven't confirmed.** You're attesting to this record to the state. It only proposes, and you decide.
- Fill in or submit your claim. You file on Frances Online yourself.
- Answer the other claim questions (able and available to work, earnings). Those are yours.

**Oregon only.** Other states have different rules, so this add-on doesn't try to cover them. Rules can change, so check https://unemployment.oregon.gov if anything looks different from what your claim asks.

## Privacy

Your work-search record stays in the `my-search/work-search` folder on your Mac. Nothing is sent to the state or anywhere else. You copy it into the form yourself.

## What gets installed

See [manifest.md](manifest.md). To remove it, say **remove the unemployment add-on**. Your records stay.

<sub>MIT licensed. Not affiliated with the Oregon Employment Department. This is a record-keeping helper, not legal advice.</sub>
