#!/usr/bin/env python3
"""Regenerate the ticker list on the Web Appendix page from the PDFs on disk.

Usage:
    python3 tools/build_web_appendix.py [--date "15 September 2026"]

Drop the TICKER.pdf files into filtering-web-appendix/reports/ (and the combined
filtering-web-appendix.pdf into filtering-web-appendix/), then run this. It rewrites
the marked blocks in filtering-web-appendix/index.html:

  - the ticker grid, sorted by ticker
  - the "last updated" date (today unless --date is given)
  - the combined-PDF slot, which becomes a live link, with its size, once the file exists

The version notice is editorial text; the script never touches it. Nothing else
in the file is touched either.
"""

import argparse
import datetime as dt
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PAGE = os.path.join(ROOT, "filtering-web-appendix", "index.html")
REPORTS = os.path.join(ROOT, "filtering-web-appendix", "reports")
COMBINED_NAME = "filtering-web-appendix.pdf"
COMBINED = os.path.join(ROOT, "filtering-web-appendix", COMBINED_NAME)


def replace_block(text, name, body):
    pattern = re.compile(
        r"(<!-- BEGIN %s -->)(.*?)(<!-- END %s -->)" % (name, name), re.S
    )
    if not pattern.search(text):
        sys.exit("marker %s not found in %s" % (name, PAGE))
    return pattern.sub(lambda m: m.group(1) + body + m.group(3), text, count=1)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--date", help='e.g. "15 September 2026"; defaults to today')
    args = ap.parse_args()

    tickers = sorted(
        os.path.splitext(f)[0]
        for f in os.listdir(REPORTS)
        if f.lower().endswith(".pdf")
    )

    if tickers:
        rows = ['      <li><a href="reports/%s.pdf">%s</a></li>' % (t, t)
                for t in tickers]
        grid = "\n    <ul class=\"tickers\">\n%s\n    </ul>\n" % "\n".join(rows)
    else:
        print("no PDFs in %s; leaving the ticker grid as it is" % REPORTS)
        grid = None

    stamp = args.date or dt.date.today().strftime("%-d %B %Y")

    # The combined document is built from the per-asset reports, so it must not
    # be older than any of them. mtimes are advisory (a plain copy resets them),
    # but a stale combined file is the one failure a reader cannot see.
    if tickers and os.path.exists(COMBINED):
        newest = max(os.path.getmtime(os.path.join(REPORTS, f))
                     for f in os.listdir(REPORTS) if f.lower().endswith(".pdf"))
        if newest > os.path.getmtime(COMBINED) + 1:
            print("WARNING: %s is older than the newest report (%s vs %s)."
                  % (COMBINED_NAME,
                     dt.datetime.fromtimestamp(os.path.getmtime(COMBINED)).strftime("%Y-%m-%d %H:%M"),
                     dt.datetime.fromtimestamp(newest).strftime("%Y-%m-%d %H:%M")))
            print("         Rebuild it from filtering-web-appendix.tex before publishing,")
            print("         or the page will serve fresh chapters beside a stale document.")

    if os.path.exists(COMBINED):
        mb = os.path.getsize(COMBINED) / (1024.0 * 1024.0)
        combined = ('\n      <a class="btn" href="%s">Complete appendix '
                    "(PDF, %d MB)</a>\n" % (COMBINED_NAME, round(mb)))
    else:
        combined = ('\n      <span class="btn pending">Complete appendix (PDF) '
                    "&middot; not yet available</span>\n")

    with open(PAGE, encoding="utf-8") as fh:
        text = fh.read()

    if grid is not None:
        text = replace_block(text, "TICKERS", grid)
    text = replace_block(text, "COMBINED", combined)
    text = replace_block(text, "UPDATED", stamp)

    with open(PAGE, "w", encoding="utf-8") as fh:
        fh.write(text)

    print("%d reports linked, last updated %s, combined PDF %s"
          % (len(tickers), stamp, "present" if os.path.exists(COMBINED) else "absent"))


if __name__ == "__main__":
    main()
