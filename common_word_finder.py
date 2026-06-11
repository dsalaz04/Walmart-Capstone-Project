"""Survey a subreddit (or CSV) for its most common meaningful words.

Used when tuning the analysis for a new community: the words this prints are
candidates for the CATALYSTS topic list in data.py. Filters out the BLACKLIST of
high-frequency filler words; tune that list until the output is meaningful — too
strict and real topics are hidden, too loose and the list is all noise.
"""

from __future__ import annotations

import argparse
import sys
from collections import Counter
from pathlib import Path

import matplotlib

from data import BLACKLIST
from reddit_sentiment import Comment, fetch_comments, load_csv, strip_token


def count_words(comments: list[Comment]) -> Counter:
    """Count cleaned words across all comments, ignoring blacklist filler."""
    counts: Counter = Counter()
    for _, body in comments:
        counts.update(word for raw in body.split()
                      if (word := strip_token(raw)) and word not in BLACKLIST)
    return counts


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Find the most common meaningful words in a subreddit.")
    source = parser.add_mutually_exclusive_group()
    source.add_argument("--subreddit", default=None,
                        help="subreddit to scrape live (needs API credentials)")
    source.add_argument("--input", default=None,
                        help="CSV with a 'comment' column to analyze offline")
    parser.add_argument("--top", type=int, default=30,
                        help="how many words to show (default: 30)")
    parser.add_argument("--posts", type=int, default=None,
                        help="post limit in live mode (default: 25)")
    parser.add_argument("--save", default=None, metavar="DIR",
                        help="write the chart to DIR instead of opening a window")
    args = parser.parse_args(argv)

    if not args.subreddit and not args.input:
        parser.error("choose a source: --subreddit NAME or --input FILE.csv")
    if args.input and args.posts is not None:
        print("Warning: --posts is ignored in offline mode.", file=sys.stderr)
    if args.save:
        matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    comments = (load_csv(args.input) if args.input
                else fetch_comments(args.subreddit,
                                    args.posts if args.posts is not None else 25))
    top = count_words(comments).most_common(args.top)
    if not top:
        print("No words found.")
        return 1

    source_name = args.input or f"r/{args.subreddit}"
    print(f"Top {len(top)} words in {len(comments)} comments from {source_name}:")
    for word, n in top:
        print(f"  {word}: {n}")

    # Horizontal bar chart, most common at the top.
    words, counts = zip(*reversed(top))
    plt.figure(figsize=(10, max(4, len(top) * 0.3)))
    plt.barh(words, counts)
    plt.title(f"Most common words: {source_name}")
    plt.tight_layout()
    if args.save:
        out = Path(args.save)
        out.mkdir(parents=True, exist_ok=True)
        plt.savefig(out / "common_words.png", dpi=120, bbox_inches="tight")
        print(f"\nChart written to {out}/common_words.png")
    else:
        plt.show()
    return 0


if __name__ == "__main__":
    sys.exit(main())
