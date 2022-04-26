"""Common word finder

When programming NLP for a specific subreddit, I need to gather a list of meaningful words in order to fulfill one
of the requirements to make a good sentiment analysis tool. This script will gather that list and tell me everything I
want to know about a subreddit, specifically, its most commonly used words. This process takes careful tweaking
involving the blacklisted words. Too broad, and we risk missing out on words that could be meaningful to the subreddit.
Too vague, and we risk false positives, namely, adding words that have no meaning to the subreddit.

"""

import praw
import matplotlib.pyplot as plt


def find_common_words():
    reddit = praw.Reddit(user_agent="",
                         client_id="",
                         client_secret="",
                         username="",
                         password="")

    subreddit_name = "walmart"

    subreddit = reddit.subreddit(subreddit_name)

    top_subreddit = subreddit.top()
    count = 0
    MAX_WORDS = 10000
    print('success')
    words = []
    wordCount = {}

    commonWords = {'that', 'this', 'and', 'of', 'the', 'for', 'I', 'it', 'has', 'in',
                   'you', 'to', 'was', 'but', 'have', 'they', 'a', 'is', '', 'be', 'on', 'are', 'an', 'or',
                   'at', 'as', 'do', 'if', 'your', 'not', 'can', 'my', 'their', 'them', 'they', 'with',
                   'at', 'about', 'would', 'like', 'there', 'You', 'from', 'get', 'just', 'more', 'so',
                   'me', 'more', 'out', 'up', 'some', 'will', 'how', 'one', 'what', "don't", 'should',
                   'could', 'did', 'no', 'know', 'were', 'did', "it's", 'This', 'he', 'The', 'we',
                   'all', 'when', 'had', 'see', 'his', 'him', 'who', 'by', 'her', 'she', 'our', 'thing', '-',
                   'now', 'what', 'going', 'been', 'we', "I'm", 'than', 'any', 'because', 'We', 'even',
                   'said', 'only', 'want', 'other', 'into', 'He', 'what', 'i', 'That', 'thought',
                   'think', "that's", 'Is', 'much'}

    for submission in subreddit.top(limit=500):
        submission.comments.replace_more(limit=0)
        for top_level_comment in submission.comments:
            count += 1
            if count == MAX_WORDS:
                break
            word = ""
            for letter in top_level_comment.body:
                if letter == ' ':
                    if word and not word[-1].isalnum():
                        word = word[:-1]
                    if not word.lower() in commonWords:
                        words.append(word)
                    word = ""
                else:
                    word += letter
        if count == MAX_WORDS:
            break

    for word in words:
        if word in wordCount:
            wordCount[word] += 1
        else:
            wordCount[word] = 1

    sortedList = sorted(wordCount, key=wordCount.get, reverse=True)

    keyWords = []
    keyCount = []
    amount = 0

    for entry in sortedList:
        keyWords.append(entry)
        keyCount.append(wordCount[entry])
        amount += 1
        if amount == 100:
            break
    print(keyWords)

    labels = keyWords
    sizes = keyCount
    # explode = (0, 0.1, 0, 0)  # only "explode" the 2nd slice (i.e. 'Hogs')

    plt.title('Top comments for: r/' + subreddit_name)
    plt.pie(sizes, labels=labels, autopct='%1.1f%%',
            shadow=True, startangle=90)
    plt.axis('equal')  # Equal aspect ratio ensures that pie is drawn as a circle.

    plt.show()


if __name__ == '__main__':
    find_common_words()
