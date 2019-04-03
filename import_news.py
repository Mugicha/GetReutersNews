"""
Python PGM to get News article from https://www.reuters.com.
created by D.S 2018.09.12
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


def get_news_link(daily_url):
    """
    特定の日付のニュースURLを取得する機能
    :param daily_url: 特定の日付のnewsURLが乗っているURL
    :return: 特定の日付のニュースURLを配列形式で
    """
    f = urlopen(daily_url)
    soup = BeautifulSoup(f.read(), 'lxml')
    each_news = soup.findAll('div', class_='headlineMed')
    daily_news_urls = []
    for news in each_news:
        a = news.findAll('a')
        for _a in a:
            daily_news_urls.append(_a.attrs['href'])
    return daily_news_urls


def get_daily_news_link(year_url):
    """
    日ごとのニュースURLを取得する処理
    :param year_url: 日毎のニュースURLが載っているURL
    :return: 日毎のニュースURLを配列形式で
    """
    f = urlopen(year_url)
    soup = BeautifulSoup(f.read(), 'lxml')
    daily_link = soup.findAll('p')
    daily_link_ary = []
    for line in daily_link:
        a = line.findAll('a')
        for _a in a:
            if not _a.attrs['href'] == '//thomsonreuters.com/' or not _a.attrs['href'] == '/info/disclaimer':
                daily_link_ary.append('https://www.reuters.com' + _a.attrs['href'])
    return daily_link_ary


if __name__ == '__main__':
    year_ary = [y for y in range(2016, 2019, 1)]
    # get each Year
    for year in year_ary:
        print('Year:\t' + str(year))
        daily_link = get_daily_news_link('https://www.reuters.com/resources/archive/us/' + str(year) + '.html')
        # get each day newses.
        for daily in daily_link:
            print('\tDaily:\t' + daily)
            # URLから日付情報を抜き出す処理
            # e.g.
            # INPUT  :https://www.reuters.com/resources/archive/us/20161227.html
            # OUTPUT :20161227
            day = np.array(daily.split('/')[-1].split('.')[0])
            # news already exist in data folder is skipped.
            output = './data/daily_news' + str(day) + '.txt'
            newsURL = get_news_link(daily)
            # ファイルが存在し、かつ、ファイルに書き出したnews数と
            # reutersサイトにあるnews数の差が10件より少なければスキップする
            if os.path.isfile(output) and (len(newsURL) - len([s for s in newsURL if 'http://www.reuters.com/news/video' in s])) - sum(1 for i in open(output, 'r')) < 10:
                print('\t\t-> Skipped')
                # print(len(newsURL) - len([s for s in newsURL if 'http://www.reuters.com/news/video' in s]))
                # print(sum(1 for i in open(output, 'r')))
                continue
            fw = codecs.open(output, 'w', 'utf-8')
            # get each news in the day.
            for each_news_url in newsURL:
                print('\t\tnow getting news from:\t' + each_news_url)
                # skip getting char of video news URL.
                if 'news/video' in each_news_url:
                    print('\t\t- Skipped because it is video news.')
                    main_article = ''
                else:
                    # GET news.
                    main_article = get_news(each_news_url)
                if not main_article == '':
                    fw.write(main_article)
            fw.close()
    # print(get_news("https://www.reuters.com/article/hkn-oilers-jets-writethru-idUSMTZECC2JEEOD1"))
