# Authors: Daniel Salazar, Jonathan Montoya
# Created: 02.08.2022
# Description: Reddit scraper using PRAW api
# -*- coding: utf-8 -*-
# Copyright 2022 University of Arkansas Capstone Group 10

import praw
import time
import pandas as pd
import matplotlib.pyplot as plt
import squarify
import emoji
import re
import en_core_web_sm
import string
from data import *
from nltk.sentiment.vader import SentimentIntensityAnalyzer
from nltk.tokenize import RegexpTokenizer
from nltk.stem import WordNetLemmatizer


def sentiment_analysis(num_posts_to_analyze, a_comments, top_keywords):
    scores = {}

    vader = SentimentIntensityAnalyzer()
    vader.lexicon.update(new_words)  # adding custom words from data.py
    topic_sentiment = list(top_keywords.keys())[0:num_posts_to_analyze]

    for topic in topic_sentiment:
        comments_of_interest = a_comments[topic]
        for comment in comments_of_interest:

            removed_emojis = emoji.get_emoji_regexp().sub(u'', comment)  # remove emojis

            # remove punctuation
            text_punc = "".join([char for char in removed_emojis if char not in string.punctuation])
            text_punc = re.sub('[0-9]+', '', text_punc)

            # tokenizing and cleaning
            tokenizer = RegexpTokenizer('\w+|\$[\d\.]+|http\S+')
            tokenized_string = tokenizer.tokenize(text_punc)
            lower_tokenized = [word.lower() for word in tokenized_string]  # convert to lower case

            # remove stop words
            nlp = en_core_web_sm.load()
            stopwords = nlp.Defaults.stop_words
            sw_removed = [word for word in lower_tokenized if not word in stopwords]

            # normalize the words using lemmatization
            lemmatizer = WordNetLemmatizer()
            lemmatized_tokens = ([lemmatizer.lemmatize(w) for w in sw_removed])

            # calculating sentiment of every word in comments and combining them
            comments_score = {'neg': 0.0, 'neu': 0.0, 'pos': 0.0, 'compound': 0.0}

            word_count = 0
            for word in lemmatized_tokens:
                if word.upper() not in possible_catalysts:
                    score = vader.polarity_scores(word)
                    word_count += 1
                    for key, _ in score.items():
                        comments_score[key] += score[key]
                else:
                    comments_score['pos'] = 2.0

                    # Calculating average
            try:  # handles: ZeroDivisionError: float division by zero
                for key in comments_score:
                    comments_score[key] = comments_score[key] / word_count
            except:
                pass

            # Adding score to the specific post
            if topic in scores:
                for key, _ in comments_score.items():
                    scores[topic][key] += comments_score[key]
            else:
                scores[topic] = comments_score

                # calculating avg.
        for key in comments_score:
            scores[topic][key] = scores[topic][key] / top_keywords[topic]
            scores[topic][key] = "{pol:.3f}".format(pol=scores[topic][key])

    # Deleting compound from dictionary since we don't need it
    for i in scores.items():
        val = i[1]['neu']
        del i[1]['compound']
        # Neutral score is too high, so we will divide by 4
        i[1]['neu'] = str(float(val) / 4)

    return scores


def print_helper(keywords, catalysts, c_analyzed, posts, subs, titles, time, start_time):
    top_keywords = dict(sorted(keywords.items(), key=lambda item: item[1], reverse=True))
    topics = list(top_keywords.keys())[0:catalysts]
    time = (time.time() - start_time)

    # Print top catalysts
    print(
        "It took {t:.2f} seconds to analyze {c} comments in {p} posts in {s} subreddit.\n".format(t=time, c=c_analyzed,
                                                                                                  p=posts,
                                                                                                  s=len(subs)))
    print("Posts analyzed: ")
    for i in titles:
        print(i)

    print(f"\n{catalysts} most mentioned topics: ")
    times = []
    top = []
    for i in topics:
        print(f"{i}: {top_keywords[i]}")
        times.append(top_keywords[i])
        top.append(f"{i}: {top_keywords[i]}")

    return top_keywords, times, top


def create_graphs(num_posts_to_analyze, scores, catalysts, times, top):
    # Print square chart
    print(f"\nSentiment analysis of top {num_posts_to_analyze} catalysts:")
    data_frame = pd.DataFrame(scores)
    data_frame.index = ['Negative', 'Neutral', 'Positive']
    data_frame = data_frame.T
    print(data_frame)

    # Data Visualization
    # most mentioned catalysts
    squarify.plot(sizes=times, label=top, alpha=.7)
    plt.axis('off')
    plt.title(f"{catalysts} most mentioned catalysts")
    plt.show()

    # Sentiment analysis
    data_frame = data_frame.astype(float)
    colors = ['red', 'springgreen', 'forestgreen']
    data_frame.plot(kind='bar', color=colors, title=f"Sentiment analysis of top {num_posts_to_analyze} catalysts:")
    plt.tight_layout()
    plt.show()


def data_extractor(reddit):
    subs = ['walmart']  # subreddit to search
    post_flairs = {'Daily Discussion', 'Weekly Salt Mod'}  # post flairs to search. No flair is automatically considered
    whitelist_author = {'AutoModerator'}  # authors whose comments are allowed more than once
    comments_unique = True  # allow one comment per author, per post
    ignore_post_authors = {'example'}  # authors to ignore for posts
    ignore_comment_authors = {'example'}  # authors to ignore for comments
    upvote_ratio = 0.70  # upvote ratio for post to be considered, 0.70 = 70%
    upvote_threshold = 20  # define # of upvotes, post is considered if upvotes exceed this
    limit = 1  # define the limit, comments 'replace more' limit
    upvotes = 2  # define # of upvotes, comment is considered if upvotes exceed this #
    catalysts = 10  # define # of catalysts here, prints as "Top ## catalysts are:"
    num_posts_to_analyze = 5  # define # of catalysts for sentiment analysis

    posts, count, c_analyzed, keywords, titles, a_comments = 0, 0, 0, {}, [], {}
    cmt_auth = {}

    for sub in subs:
        subreddit = reddit.subreddit(sub)
        # hot_python = subreddit.top("month")  # sorting posts by top this month
        hot_python = subreddit.hot()  # sorting posts by hot
        # Extracting comments, top_keywords from subreddit
        for post in hot_python:
            # Uncomment the following 2 lines to print titles of posts
            # title = post.title
            # print(title)
            flair = post.link_flair_text
            try:
                author = post.author.name
            except Exception as e:
                print(e)

            if post.upvote_ratio >= upvote_ratio and post.ups > upvote_threshold and (
                    flair in post_flairs or flair is None) and author not in ignore_post_authors:
                post.comment_sort = 'new'
                comments = post.comments
                titles.append(post.title)
                posts += 1
                try:
                    post.comments.replace_more(limit=limit)
                    for comment in comments:
                        # try except for deleted account?
                        try:
                            auth = comment.author.name
                        except:
                            pass
                        c_analyzed += 1

                        # checking: comment upvotes and author
                        if comment.score > upvotes and auth not in ignore_comment_authors:
                            split = comment.body.split(" ")
                            for word in split:
                                if word not in blacklist and word in possible_catalysts:
                                    # unique comments, try/except for key errors
                                    if comments_unique and auth not in whitelist_author:
                                        try:
                                            if auth in cmt_auth[word]:
                                                break
                                        except:
                                            pass

                                    # counting keywords
                                    if word in keywords:
                                        keywords[word] += 1
                                        a_comments[word].append(comment.body)
                                        cmt_auth[word].append(auth)
                                        count += 1
                                    else:
                                        keywords[word] = 1
                                        cmt_auth[word] = [auth]
                                        a_comments[word] = [comment.body]
                                        count += 1
                except Exception as e:
                    print(e)

    return posts, c_analyzed, keywords, titles, a_comments, catalysts, subs, num_posts_to_analyze


def main():
    start_time = time.time()

    reddit = praw.Reddit(user_agent="",
                         client_id="",
                         client_secret="",
                         username="",
                         password="")

    posts, c_analyzed, keywords, titles, a_comments, catalysts, subs, num_posts_to_analyze = data_extractor(reddit)
    top_keywords, times, top = print_helper(keywords, catalysts, c_analyzed, posts, subs, titles, time, start_time)
    scores = sentiment_analysis(num_posts_to_analyze, a_comments, top_keywords)
    create_graphs(num_posts_to_analyze, scores, catalysts, times, top)


if __name__ == '__main__':
    main()
