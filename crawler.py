# Author(s): Daniel Salazar, Jonathan Montoya
# Created: 01.26.2022
# Description: Tweet Crawler using Twitter API
# -*- coding: utf-8 -*-
# Copyright 2021 University of Arkansas Capstone Group 10

import time
import datetime
from pymongo import MongoClient
import json
import tweepy
from tweepy import OAuthHandler
#############
#   PyMongo can be installed with pip: pip install pymongo
#   Tweepy can be installed wit pip: pip install tweepy
#############

consumer_key = '14OB10FJSwIWIiYDlm5UMLGjs'
consumer_secret = 'iMCq73JQI8F99WaTKhXFj185BN3eLPWRRwSoBVfnH7bLPYh6lg'
access_token = '192628849-rv7jsrVU2ASppsOqy4xcW3DLrpzRCY1s34lHvV9g'
access_token_secret = 'fk5pPw1qyxJajLn2ia58DN0kVqM3sSV9IMpwGp437z9PD'

auth = OAuthHandler(consumer_key, consumer_secret)
auth.set_access_token(access_token, access_token_secret)
api = tweepy.API(auth, wait_on_rate_limit=True,
                 wait_on_rate_limit_notify=True)
if (not api):
    print ("Can't Authenticate")
    sys.exit(-1)

client = MongoClient('localhost', 27017)
db = client['db_twitter']

start_time = time.time()
last_sun = str(datetime.date.today() -
               datetime.timedelta(days=datetime.date.today().weekday() + 1))
last_mon = str(datetime.date.today() -
               datetime.timedelta(days=datetime.date.today().weekday() + 7))
searchQuery = ['#MussBus', '#Hogs', '#NCAA']


def crawler(searchQuery, maxTweets=500, tweetsPerQry=100):
    for word in searchQuery:
        max_id = -1
        tweetCount = 0
        collection = db['twitter_{0}'.format(word[1:])]
        while tweetCount < maxTweets:
            try:
                if (max_id <= 0):
                    new_tweets = api.search(lang="en",
                                            q=word, count=tweetsPerQry, since=last_mon, until=last_sun)
                else:
                    new_tweets = api.search(lang="en",
                                            q=word, count=tweetsPerQry, since=last_mon, until=last_sun, max_id=str(max_id - 1))

                if not new_tweets:
                    print("No more tweets found")
                    break

                for tweet in new_tweets:
                    collection.insert(json.loads(json.dumps(tweet._json)))

                tweetCount += len(new_tweets)
                print("Downloaded {0} tweets".format(tweetCount))
                max_id = new_tweets[-1].id
            except tweepy.TweepError as e:
                # Just exit if any error
                print("some error : " + str(e))
                break

crawler(searchQuery=searchQuery)