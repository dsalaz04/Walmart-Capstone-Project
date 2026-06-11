"""Domain vocabulary for r/walmart sentiment analysis.

CATALYSTS are the workplace topics worth tracking (pay, scheduling, management, ...),
as a token -> canonical-topic map so variants ("wage", "wages") merge into one topic.
BLACKLIST holds high-frequency words with no topical meaning, used when surveying a
subreddit for candidate catalysts. LEXICON adjusts VADER's scores for words that carry
a specific charge in Walmart-employee speech (e.g. "coached" is a disciplinary action,
strongly negative, not a sports term).
"""

# Topics of interest. A comment counts toward a topic when it mentions a token (key);
# counts and sentiment are reported under the canonical topic name (value).
# PTO and PPTO stay separate (PPTO is Walmart's protected PTO — a distinct system),
# as do 'coach'/'ASM'/'manager' (distinct roles) and 'masks' (policy gripes, not
# pandemic discussion generally).
CATALYSTS = {
    'OGP': 'OGP',
    'manager': 'manager',
    'covid': 'covid/pandemic',
    'pandemic': 'covid/pandemic',
    'customer': 'customer',
    'pay': 'pay',
    'wage': 'pay',
    'wages': 'pay',
    'coach': 'coach',
    'PTO': 'PTO',
    'warehouse': 'warehouse',
    'zoning': 'zoning',
    'overnight': 'overnight',
    'ASM': 'ASM',
    'union': 'union',
    'unionize': 'union',
    'unionizing': 'union',
    'vest': 'vest',
    'vests': 'vest',
    'retail': 'retail',
    'pallets': 'pallets',
    'vendors': 'vendors',
    'Amazon': 'Amazon',
    'promoted': 'promotion',
    'promotion': 'promotion',
    'masks': 'masks',
    'ppto': 'ppto',
}

# Common words to ignore when surveying a subreddit for new catalyst candidates.
BLACKLIST = {
    'that', 'this', 'and', 'of', 'the', 'for', 'i', 'it', 'has', 'in', 'you', 'to',
    'was', 'but', 'have', 'they', 'a', 'is', '', 'be', 'on', 'are', 'an', 'or', 'at',
    'as', 'do', 'if', 'your', 'not', 'can', 'my', 'their', 'them', 'with', 'about',
    'would', 'like', 'there', 'from', 'get', 'just', 'more', 'so', 'me', 'out', 'up',
    'some', 'will', 'how', 'one', 'what', "don't", 'should', 'could', 'did', 'no',
    'know', 'were', "it's", 'he', 'we', 'all', 'when', 'had', 'see', 'his', 'him',
    'who', 'by', 'her', 'she', 'our', 'thing', '-', 'now', 'going', 'been', "i'm",
    'than', 'any', 'because', 'even', 'said', 'only', 'want', 'other', 'into',
    'thought', 'think', "that's", 'much',
}

# VADER lexicon overrides tuned to r/walmart (scores range 4.0 to -4.0).
# Only words VADER's stock lexicon misses or misreads belong here: general
# profanity/negativity (fuck, hate, pissed, ...) is already calibrated in stock
# VADER, and overriding it to the floor flattened the signal. These are
# Walmart-employee terms — disciplinary jargon, scheduling pain, benefits.
LEXICON = {
    # Discipline and termination (a "coaching" is a formal write-up step).
    'coached': -3.5,
    'coaching': -3.0,
    'write-up': -3.0,
    'writeup': -3.0,
    'terminated': -3.5,
    # Working conditions and scheduling.
    'understaffed': -2.5,
    'underpaid': -3.0,
    'overworked': -2.5,
    'favoritism': -2.5,   # stock VADER scores this +0.7; in a workplace it's a gripe
    'clopen': -2.0,       # closing shift followed by opening shift
    'zoning': -1.5,       # tidying shelves: tedious, not catastrophic
    'restock': -1.0,
    'quitting': -2.0,     # talk of quitting signals dissatisfaction with the job
    'corporate': -1.5,    # usually a venting target ("corporate doesn't care")
    # Benefits.
    'ppto': 1.5,          # Protected PTO — viewed positively as a benefit
}
