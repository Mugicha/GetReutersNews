"""
Python PGM to get News article from https://jp.reuters.com.
"""
import urllib
from urllib.request import urlopen
from bs4 import BeautifulSoup
import re
from tqdm import tqdm
import pandas as pd


class GetReutersNews:
    def __init__(self):
        self.r = re.compile(r"<[^>]*?>")

    def get_news(self, news_url):
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
            return ''
        soup = BeautifulSoup(f.read(), 'lxml')
        honbun = soup.findAll('div', class_='StandardArticleBody_body')
        entire_honbun = ''
        for line in honbun:
            h = line.findAll('p')
            for ptag in h:
                entire_honbun = entire_honbun + self.r.sub('', str(ptag).replace('\n', '').replace(',', ''))
        return entire_honbun

    def get_each_page_news_title_and_link(self, daily_url):
        """
        newsアーカイブ1ページごとに日付、概要、ニュースURLを配列で取得する機能.
        :param daily_url: newsアーカイブ記事のURL
        :return:
        """
        f = urlopen(daily_url)
        soup = BeautifulSoup(f.read(), 'lxml')
        each_news = soup.findAll('div', class_='news-headline-list')
        news_ary = []
        for news in each_news:
            t = news.findAll('time')  # Get date.
            p = news.findAll('p')  # Get abstract.
            tmp_a = news.findAll('a')  # Get Link
            a = []
            for link in tmp_a:
                a.append(link.attrs['href'])
            a = a[::2]

            for _t, _p, _a in zip(t, p, a):
                one_news_info_ary = []
                one_news_info_ary.append(self.r.sub('', str(_t).replace('\n', '')))
                one_news_info_ary.append(self.r.sub('', str(_p).replace('\n', '')))
                one_news_info_ary.append(str('https://jp.reuters.com') + str(_a))  # e.g. https://jp.reuters.com/article/idJPJAPAN-21788920110620
                honbun = self.get_news(str('https://jp.reuters.com') + str(_a))
                one_news_info_ary.append(honbun)
                news_ary.append(one_news_info_ary)
        return news_ary


if __name__ == '__main__':
    getreuters = GetReutersNews()
    news_df = None
    for page in tqdm(range(1, 100)):
        try:
            page_link = getreuters.get_each_page_news_title_and_link('https://jp.reuters.com/news/archive/?view=page&page=' + str(page) + '&pageSize=10')
        except:
            continue
        for num, each_news in enumerate(page_link):
            if num == 0 and page == 1:
                news_df = pd.DataFrame({'Date': [str(each_news[0])], 'Summary': [str(each_news[1])], 'Link': [str(each_news[2])], 'Detail': [str(each_news[3])]}, index=[0])
            else:
                news_df = news_df.append(pd.Series(data=[str(each_news[0]), str(each_news[1]), str(each_news[2]), str(each_news[3])], index=news_df.columns), ignore_index=True)
    news_df.to_excel('news.xlsx', sheet_name='Reuters', index=False, encoding='utf8')
