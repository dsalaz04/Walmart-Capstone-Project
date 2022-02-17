# Authors: Daniel Salazar, Jonathan Montoya
# Created: 02.08.2022
# Description: Reddit scraper using PRAW api
# -*- coding: utf-8 -*-
# Copyright 2021 University of Arkansas Capstone Group 10

import praw
import pandas as pd
from praw.models import MoreComments


def reddit_scraper(reddit_read_only, subreddit):
    # Display the name of the Subreddit
    print("Display Name:", subreddit.display_name)

    # Display the title of the Subreddit
    print("Title:", subreddit.title)

    # Display the description of the Subreddit
    print("Description:", subreddit.description)

    for post in subreddit.hot(limit=5):
        print(post.title)
        print()

        posts = subreddit.top("month")
    # Scraping the top posts of the current month

    posts_dict = {"Title": [], "Post Text": [],
                  "ID": [], "Score": [],
                  "Total Comments": [], "Post URL": []
                  }

    for post in posts:
        # Title of each post
        posts_dict["Title"].append(post.title)

        # Text inside a post
        posts_dict["Post Text"].append(post.selftext)

        # Unique ID of each post
        posts_dict["ID"].append(post.id)

        # The score of a post
        posts_dict["Score"].append(post.score)

        # Total number of comments inside the post
        posts_dict["Total Comments"].append(post.num_comments)

        # URL of each post
        posts_dict["Post URL"].append(post.url)

    # Saving the data in a pandas dataframe
    top_posts = pd.DataFrame(posts_dict)
    top_posts

    top_posts.to_csv("Top Posts.csv", index=True)

    # URL of the post
    url = "https://www.reddit.com/gallery/soivqj"

    # Creating a submission object
    submission = reddit_read_only.submission(url=url)

    post_comments = []

    for comment in submission.comments:
        if type(comment) == MoreComments:
            continue

        post_comments.append(comment.body)

    # creating a dataframe
    comments_df = pd.DataFrame(post_comments, columns=['comment'])
    comments_df

    comments_df.to_csv("Top Comments.csv", index=True)


if __name__ == '__main__':

    reddit_read_only = praw.Reddit(client_id="", client_secret="", user_agent="")
    subreddit = reddit_read_only.subreddit("walmart")

    reddit_scraper(reddit_read_only, subreddit)
