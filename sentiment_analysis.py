from collections import defaultdict
from datetime import datetime
import re
import sys

import matplotlib
import nltk
from nltk.sentiment.vader import SentimentIntensityAnalyzer
import numpy as np
import tweepy

from authorization import authorization

nltk.download('vader_lexicon', quiet=True)
matplotlib.use('agg', warn=False, force=True)
from matplotlib import pyplot as plt


class SentimentAnalysis(object):

    def __init__(self):
        self.nltk_sentiment = SentimentIntensityAnalyzer()
        self.remove_emojis = re.compile('[\U00010000-\U0010ffff]', flags=re.UNICODE)
        self.data_array = []

    def analyze_user(self, user_handle):
        self.data_array = []
        tweets = self.__get_tweets(user_handle)
        for tweet in tweets:
            date_time = str(tweet.created_at)
            score = self.__sentiment_analysis(tweet.text)
            self.data_array.append((date_time, score))
        return self.data_array

    @staticmethod
    def __get_tweets(user_handle):
        api = tweepy.API(authorization())
        all_tweets = []
        new_tweets = api.user_timeline(screen_name=user_handle, count=200)
        all_tweets.extend(new_tweets)
        oldest = all_tweets[-1].id - 1
        while len(new_tweets) > 0:
            new_tweets = api.user_timeline(screen_name=user_handle, count=200, max_id=oldest)
            all_tweets.extend(new_tweets)
            oldest = all_tweets[-1].id - 1
        return all_tweets

    @staticmethod
    def __timestamp_ms_to_datetime(timestamp):
        return datetime.utcfromtimestamp(int(float(timestamp)/1000)).strftime('%Y-%m-%d %H:%M:%S')

    def __sentiment_analysis(self, sentence):
        return self.nltk_sentiment.polarity_scores(self.__filter_sentence(sentence))['compound']

    def __filter_sentence(self, sentence):
        return self.remove_emojis.sub(r'', sentence)

    @staticmethod
    def __key_equals(my_dict, key, value):
        return key in my_dict and my_dict[key] == value


class PlotSentiment(object):
    one = {i for i in range(1, 9)}
    two = {i for i in range(9, 17)}
    three = {i for i in range(17, 25)}
    four = {i for i in range(25, 33)}
    xres = 4

    def save_plot(self, my_dict, keys, title, save_name, alpha):
        fig, ax = plt.subplots(1, 1)
        for key in keys:
            key_ = key
            if key[-2] == '3':
                key_ = key[:7]
            if key in my_dict:
                for value in my_dict[key]:
                    ax.plot(key_, value, 'b.', alpha=alpha)
                ax.plot(key_, np.mean(my_dict[key]), 'r.', alpha=0.5)
            else:
                ax.plot(key_, 0, 'r.', alpha=0.0)
        plt.title(title)
        plt.xlabel('Year-Month')
        plt.xticks(rotation=30)
        plt.ylim(bottom=-1, top=1)
        start, stop = ax.get_xlim()
        ticks = np.arange(start, stop + self.xres, self.xres)
        ax.set_xticks(ticks)
        plt.tight_layout()
        plt.savefig(save_name)

    def get_data_dict(self, data_array):
        my_dict = defaultdict(list)
        for line in data_array:
            date_time, value = line
            date, time = date_time.split(' ')
            year, month, day = date.split('-')
            hour, minute, second = time[:-1].split(':')
            key = '{year}-{month}-({day})'.format(year=year, month=month, day=self.__split_days(day))
            my_dict[key].append(value)
        return my_dict

    def get_keys(self, my_dict, fill=False):
        keys = list(my_dict.keys())
        keys.sort()
        if fill:
            min_year = int(keys[0][:4])
            max_year = int(keys[-1][:4])
            keys = []
            for year_ in range(min_year, max_year + 1):
                yearly_keys = []
                year = str(year_)
                for i in range(1, 13):
                    for j in range(1, 5):
                        yearly_keys.append("{year}-{month:02d}-({day})".format(year=year, month=i, day=j))
                keys.append(yearly_keys)
        return keys

    def get_alpha(self, my_dict):
        max_count = 1
        for _, value in my_dict.items():
            max_count = max(max_count, len(value))
        return max(0.05, 1 / max_count)

    def __split_days(self, date_):
        date = int(date_)
        if date in self.one:
            return 1
        elif date in self.two:
            return 2
        elif date in self.three:
            return 3
        elif date in self.four:
            return 4
        else:
            raise ValueError('({date} is not a valid date, must be between 1 and 32)'.format(date=date))


def main():

    handle = sys.argv[1]

    sa = SentimentAnalysis()
    data_array = sa.analyze_user(handle)

    ps = PlotSentiment()
    my_dict = ps.get_data_dict(data_array)
    keys = ps.get_keys(my_dict, fill=True)
    alpha = ps.get_alpha(my_dict)

    for yearly_keys in keys:
        ps.save_plot(my_dict, yearly_keys,
                     "@{handle} {year} Twitter Sentiment".format(handle=handle, year=yearly_keys[0][:4]),
                     '{handle}-{year}.png'.format(handle=handle, year=yearly_keys[0][:4]), alpha)
        print('Made "{handle}-{year}.png"'.format(handle=handle, year=yearly_keys[0][:4]))


if __name__ == "__main__":
    main()
