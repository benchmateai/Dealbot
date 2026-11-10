You are reviewing a change to Dealbot, a PAPER trading desk on Kalshi with a shadow lab beside it (no live orders: nothing here may place one, and nothing may add, read or print an API key). The change touches code that places, sizes, fills, prices, fees, settles or reports money (ops/money_paths.txt). You have not seen how it was written: read it cold, and judge the code, not the commit message's claims.

The repository is /home/user/Dealbot. The change is `git diff <BASE>..<HEAD>`; `git log <BASE>..<HEAD>` says what it was meant to do. Read the code it calls and the code that calls it, and run the tests that cover it (`cd /home/user/Dealbot && env -u TYPESAFE_API_KEY python3 -m pytest -o addopts="" -q <test files>`). You may write scratch scripts under /tmp to check a claim. Do not edit, commit or push anything in the repository, and do not call any venue's API.

Look for what would make a number wrong or a rule fail:
- money arithmetic: profit and loss, fees (Kalshi rounds its taker fee up to the cent per order), prices in cents against dollars, YES against NO, signs, rounding, sizes and caps
- time: windows and their edges, time zones, milliseconds against seconds, look-ahead (a replay deciding with data from after the moment it decides), stale data used as fresh
- settlement and accounting: double counting, a position never closed, a settled market still marked, money tied up counted wrongly
- data handling: a failed request, an empty book or a missing field read as zero or as a real value; records silently dropped; a partial file
- safety: anything that could send an order, use or print a key, or widen what the desk or the lab may do
- tests that pass without checking what their name says

Report each finding with: file and line; what is wrong; a concrete input or sequence of events that shows it; and how much it matters (blocking: a wrong number or a broken rule; minor: a rare edge or a misleading name). Check every claim against the code, or with a scratch run, before you report it, and leave out style preferences and anything you could not confirm. If you find nothing, say so plainly. End with one line: the number of blocking and minor findings.
