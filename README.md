[![news-image-20261126](https://make.fun/badge/news-image-20261126.svg)](https://make.fun/c/news-image-20261126)
[![rank](https://make.fun/badge/news-image-20261126/xyzar29/world-news-26-nov-2026/rank.svg)](https://make.fun/c/news-image-20261126)
[![reward](https://make.fun/badge/news-image-20261126/xyzar29/world-news-26-nov-2026/reward.svg)](https://make.fun/c/news-image-20261126)

# The World Today — Thursday 26 November 2026

A one-day world news front page for Thursday 26 November 2026, rendered as a
single 1024×1024 image. Every story on the page was first reported on that
day (UTC) by the news service named beside it.

## What it shows

- **Masthead** — "The World Today", Thursday 26 November 2026.
- **Lead story** — the EU's search for a new ECB chief as Christine Lagarde
  resigns, with Russia's $600bn military budget and Korea's rate rise.
- **The Day in UTC** — a timeline strip of the day's moments, 00:23 to 09:05 UTC.
- **45 stories** across World, Markets & Business, and Tech & Life — each
  with its source (Reuters, BBC, EUR Radio, C54, Libre News, Sky).
- **The Day in Numbers** — Korea 3.25%, Russia $600bn, Petrobras $122bn,
  Venezuela $237.5bn.
- **Date check** — an explicit line stating every story was first reported on
  Thursday 26 November 2026.

## How it is made

`main.py` (Python 3, standard library only) draws the whole front page with a
hand-drawn 5×7 bitmap font, a small software rasteriser and a hand-rolled PNG
encoder. No network, no files read, no randomness: every run writes the same
bytes to `$MAKEFUN_OUTPUT_DIR/entry.png`.

Run it:

```sh
mkdir -p out && MAKEFUN_OUTPUT_DIR=out python3 main.py
```

## Entry

Built for the make.fun competition
[news-image-20261126](https://make.fun/c/news-image-20261126)
("Sum up 26 November's world news in one image").
