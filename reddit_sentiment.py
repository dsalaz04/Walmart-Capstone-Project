"""Sentiment analysis of Walmart-employee discussion on Reddit.

Collects comments from a subreddit (or an offline CSV), finds which workplace topics
("catalysts" — pay, management, scheduling, ...) are being discussed, and scores the
sentiment of the discussion around each topic with VADER, using a lexicon tuned to
r/walmart vocabulary.

Live mode needs Reddit API credentials in the environment:

    export REDDIT_CLIENT_ID=...      # from https://www.reddit.com/prefs/apps
    export REDDIT_CLIENT_SECRET=...
    python reddit_sentiment.py --subreddit walmart

Offline mode needs no credentials:

    python reddit_sentiment.py --input sample_comments.csv
"""

from __future__ import annotations

import argparse
import os
import string
import sys
import time
from collections import Counter
from pathlib import Path

import emoji
import matplotlib
import pandas as pd

import nltk
from data import CATALYSTS, LEXICON

# Comments are (author, body) pairs; offline sources have no author.
Comment = tuple[str | None, str]

_NLTK_RESOURCES = [
    ("sentiment/vader_lexicon.zip", "vader_lexicon"),
    ("corpora/wordnet.zip", "wordnet"),
    ("corpora/stopwords.zip", "stopwords"),
]


def ensure_nltk_data() -> None:
    """Download the NLTK resources we use, once, quietly."""
    for path, name in _NLTK_RESOURCES:
        try:
            nltk.data.find(path)
        except LookupError:
            nltk.download(name, quiet=True)


# --- collection -------------------------------------------------------------

def fetch_comments(subreddit_name: str, post_limit: int | None) -> list[Comment]:
    """Pull comments from well-received posts in a subreddit via PRAW."""
    import praw  # imported lazily so offline mode needs no credentials

    client_id = os.environ.get("REDDIT_CLIENT_ID")
    client_secret = os.environ.get("REDDIT_CLIENT_SECRET")
    if not client_id or not client_secret:
        sys.exit("error: live mode needs REDDIT_CLIENT_ID and REDDIT_CLIENT_SECRET "
                 "in the environment (create an app at reddit.com/prefs/apps), "
                 "or use --input to analyze a CSV offline")

    reddit = praw.Reddit(
        client_id=client_id,
        client_secret=client_secret,
        user_agent=os.environ.get("REDDIT_USER_AGENT", "walmart-sentiment-tool"),
    )

    wanted_flairs = {"Daily Discussion", "Weekly Salt Mod", None}
    min_upvote_ratio = 0.70   # posts: at least 70% upvoted ...
    min_post_upvotes = 20     # ... with this many upvotes
    min_comment_score = 2     # comments: small quality bar

    comments: list[Comment] = []
    for post in reddit.subreddit(subreddit_name).hot(limit=post_limit):
        if (post.upvote_ratio < min_upvote_ratio or post.ups <= min_post_upvotes
                or post.link_flair_text not in wanted_flairs):
            continue
        post.comments.replace_more(limit=1)
        for comment in post.comments:
            if comment.score > min_comment_score:
                author = comment.author.name if comment.author else None
                comments.append((author, comment.body))
    return comments


def load_csv(path: str | Path) -> list[Comment]:
    """Read comments from a CSV with a 'comment' column (offline mode)."""
    frame = pd.read_csv(path)
    if "comment" not in frame.columns:
        sys.exit(f"error: {path} has no 'comment' column")
    return [(None, str(body)) for body in frame["comment"].dropna()]


# --- analysis -----------------------------------------------------------------

def strip_token(word: str) -> str:
    """Lowercase a word and trim surrounding punctuation, for matching."""
    return word.strip(string.punctuation).lower()


def find_topics(comments: list[Comment]) -> tuple[Counter, dict[str, list[str]]]:
    """Count catalyst mentions and group comments by the topics they mention.

    Each comment counts at most once per topic, and (when authors are known) each
    author counts at most once per topic, so one prolific commenter can't dominate.
    """
    catalysts = {c.lower(): c for c in CATALYSTS}
    counts: Counter = Counter()
    by_topic: dict[str, list[str]] = {}
    seen_authors: dict[str, set[str]] = {}

    for author, body in comments:
        mentioned = {catalysts[t] for w in body.split()
                     if (t := strip_token(w)) in catalysts}
        for topic in mentioned:
            if author is not None and author in seen_authors.setdefault(topic, set()):
                continue
            if author is not None:
                seen_authors[topic].add(author)
            counts[topic] += 1
            by_topic.setdefault(topic, []).append(body)
    return counts, by_topic


def make_analyzer():
    """A VADER analyzer with the r/walmart lexicon overrides applied."""
    from nltk.sentiment.vader import SentimentIntensityAnalyzer

    analyzer = SentimentIntensityAnalyzer()
    analyzer.lexicon.update(LEXICON)
    return analyzer


def score_topics(by_topic: dict[str, list[str]], topics: list[str],
                 analyzer=None) -> pd.DataFrame:
    """Average comment-level VADER sentiment for each topic.

    Comments are scored whole (emojis stripped), so VADER can use negation,
    capitalization and punctuation — scoring word-by-word would lose all of that.
    Returns a DataFrame indexed by topic with Negative/Neutral/Positive columns.
    """
    analyzer = analyzer or make_analyzer()
    rows = {}
    for topic in topics:
        totals = {"neg": 0.0, "neu": 0.0, "pos": 0.0}
        bodies = by_topic.get(topic, [])
        for body in bodies:
            polarity = analyzer.polarity_scores(emoji.replace_emoji(body, ""))
            for key in totals:
                totals[key] += polarity[key]
        n = max(1, len(bodies))
        rows[topic] = {"Negative": totals["neg"] / n,
                       "Neutral": totals["neu"] / n,
                       "Positive": totals["pos"] / n}
    return pd.DataFrame.from_dict(rows, orient="index")


# --- reporting --------------------------------------------------------------

def visualize(counts: Counter, scores: pd.DataFrame, top_n: int,
              save_dir: Path | None) -> None:
    import matplotlib.pyplot as plt
    import squarify

    # Treemap of the most mentioned topics.
    top = counts.most_common(top_n)
    plt.figure(figsize=(10, 6))
    squarify.plot(sizes=[n for _, n in top],
                  label=[f"{t}: {n}" for t, n in top], alpha=0.7)
    plt.axis("off")
    plt.title(f"{len(top)} most mentioned topics")
    if save_dir:
        plt.savefig(save_dir / "topics.png", dpi=120, bbox_inches="tight")

    # Sentiment bars per analyzed topic.
    scores.plot(kind="bar", color=["red", "gold", "forestgreen"],
                title="Sentiment by topic", figsize=(10, 6))
    plt.tight_layout()
    if save_dir:
        plt.savefig(save_dir / "sentiment.png", dpi=120, bbox_inches="tight")
    else:
        plt.show()


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Analyze sentiment around workplace topics in Reddit comments.")
    source = parser.add_mutually_exclusive_group()
    source.add_argument("--subreddit", default=None,
                        help="subreddit to scrape live (needs API credentials)")
    source.add_argument("--input", default=None,
                        help="CSV with a 'comment' column to analyze offline")
    parser.add_argument("--posts", type=int, default=25,
                        help="post limit in live mode (default: 25)")
    parser.add_argument("--top", type=int, default=10,
                        help="how many topics to count in the treemap (default: 10)")
    parser.add_argument("--analyze", type=int, default=5,
                        help="how many top topics to sentiment-score (default: 5)")
    parser.add_argument("--save", default=None, metavar="DIR",
                        help="write charts to DIR instead of opening windows")
    args = parser.parse_args(argv)

    if not args.subreddit and not args.input:
        parser.error("choose a source: --subreddit NAME or --input FILE.csv")
    save_dir = None
    if args.save:
        matplotlib.use("Agg")              # headless: don't try to open windows
        save_dir = Path(args.save)
        save_dir.mkdir(parents=True, exist_ok=True)

    ensure_nltk_data()
    started = time.time()
    if args.input:
        comments = load_csv(args.input)
        source_name = args.input
    else:
        comments = fetch_comments(args.subreddit, args.posts)
        source_name = f"r/{args.subreddit}"

    counts, by_topic = find_topics(comments)
    if not counts:
        print(f"No catalyst topics found in {len(comments)} comments from {source_name}.")
        return 1

    topics = [t for t, _ in counts.most_common(args.analyze)]
    scores = score_topics(by_topic, topics)

    print(f"Analyzed {len(comments)} comments from {source_name} "
          f"in {time.time() - started:.1f}s.\n")
    print("Most mentioned topics:")
    for topic, n in counts.most_common(args.top):
        print(f"  {topic}: {n}")
    print(f"\nSentiment of top {len(topics)} topics:")
    print(scores.round(3).to_string())

    visualize(counts, scores, args.top, save_dir)
    if save_dir:
        print(f"\nCharts written to {save_dir}/")
    return 0


if __name__ == "__main__":
    sys.exit(main())
