"""
Python PGM to get News article from https://jp.reuters.com.
"""
import urllib
from urllib.request import urlopen
from bs4 import BeautifulSoup
import re
import codecs
import os
import numpy as np


def get_news(news_url):
    """
    ニュースの本文を取得する処理
    :param news_url: 1ニュースのURL
    :return: ニュースの本文
    """
    try:
        f = urlopen(news_url)
    # Error because of not to exist Web page such as 404.
    except urllib.error.HTTPError as e:
        print('URL: ' + news_url + ' can not read. Error code: ' + str(e.code))
        return ''
    # Error because of network connection.
    except urllib.error.URLError as e:
        print(e.reason)
    soup = BeautifulSoup(f.read(), 'lxml')
    honbun = soup.findAll('div', class_='StandardArticleBody_body')
    entire_honbun = ''
    """
    # news本文が<div class='StandardArticleBody_body'>に含まれていなかった時の処理
    if honbun == '':
        meta_honbun = soup.findAll('meta', name='description')
        honbun = meta_honbun['content']
    """
    for line in honbun:
        h = line.findAll('p')
        # pタグが無い場合(少数)
        if h == []:
            entire_honbun = re.sub(r'\n|<p*>|</p>|<br>|</br>|<a*>|</a>|\(|\)|,|\.|“|"|”|\'|’', '', str(line)).lower()
        # pタグが有る場合(大多数はこっち)
        else:
            for para in h:
                honbun_paragraph = re.sub(r'\n|<p*>|</p>|<br>|</br>|<a*>|</a>|\(|\)|,|\.|“|"|”|\'|’', '', str(para)).lower()
                entire_honbun = entire_honbun + honbun_paragraph
    return entire_honbun + '\n'


def get_each_page_news_title_and_link(daily_url):
    """
    newsアーカイブ1ページごとに日付、概要、ニュースURLを配列で取得する機能.
    :param daily_url: newsアーカイブ記事のURL
    :return:
    """
    f = urlopen(daily_url)
    soup = BeautifulSoup(f.read(), 'lxml')
    rep = re.compile(r"<[^>]*?>")
    each_news = soup.findAll('div', class_='news-headline-list')
    news_ary = []
    for news in each_news:
        t = news.findAll('time')  # Get date.
        p = news.findAll('p')  # Get abstract.
        a = news.findAll('a')  # Get Link

        for _t, _p, _a in zip(t, p, a):
            one_news_info_ary = []
            one_news_info_ary.append(rep.sub('', str(_t).replace('\n', '')))
            one_news_info_ary.append(rep.sub('', str(_p).replace('\n', '')))
            one_news_info_ary.append(str('https://jp.reuters.com') + str(_a.attrs['href']))  # e.g. https://jp.reuters.com/article/idJPJAPAN-21788920110620
            news_ary.append(one_news_info_ary)
    return news_ary


if __name__ == '__main__':
    with open('output.csv', 'w') as f:
        for page in range(1, 10):
            page_link = get_each_page_news_title_and_link('https://jp.reuters.com/news/archive/?view=page&page=' + str(page) + '&pageSize=10')
            for each_news in page_link:
                f.writelines(','.join(each_news) + '\n')
        f.close()
