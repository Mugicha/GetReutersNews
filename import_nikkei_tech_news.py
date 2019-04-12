"""
Python PGM to get News article from https://tech.nikkeibp.co.jp/
"""
from urllib.request import urlopen
from bs4 import BeautifulSoup
from UtilTools import file_operation
from UtilTools import natural_language
import re
from pyknp import KNP
from tqdm import tqdm
import pandas as pd
import MeCab


class GetNTechNews:
    def __init__(self):
        self.r = re.compile(r"<[^>]*?>")
        self.r_corp = re.compile(r"（[^）]*）")
        self.r_time = re.compile(r" \(.*\)")
        self.knp = KNP(option='-tab -anaphora', jumanpp=True)
        self.fope = file_operation.FileOperation()
        self.nal = natural_language.NaturalLang()
        self.mecab = MeCab.Tagger()

    def get_each_news_info_and_link(self, daily_url):
        """
        newsアーカイブ1ページごとに日付、概要、ニュースURLを配列で取得する機能.
        :param daily_url: newsアーカイブ記事のURL
        :return:
        """
        # 変数定義
        section_title_list = []
        section_snippet_list = []
        link_list = []
        time_list = []
        honbun_list = []

        f = urlopen(daily_url)
        soup = BeautifulSoup(f.read(), 'lxml')
        main = soup.findAll('div', id='CONTENTS_MAIN')
        news_ary = []
        daily_list = main[0].findAll('div', class_='m-miM09')  # Get each news div tag.
        # 日単位
        for daily_newses in daily_list:
            # Get Title
            section_title_tmp = daily_newses.find_all('span', class_='m-miM09_titleL')
            if len(section_title_tmp) == 0: continue
            section_title = self.r.sub('', str(section_title_tmp[0]))
            section_title_list.append(section_title)
            # Get Snippet
            section_snippet_tmp = daily_newses.find_all('p')
            section_snippet = self.r.sub('', str(section_snippet_tmp[0]))
            section_snippet = section_snippet.replace('\u3000', '')
            section_snippet = section_snippet.replace('…続き', '')
            section_snippet_list.append(section_snippet)
            # Get Link
            link_tmp = daily_newses.find_all('a')
            link_tmp = link_tmp[0].attrs['href']
            link_list.append(link_tmp)
            # Get Time and Main article.
            f_detail = urlopen(str('https://www.nikkei.com') + str(link_tmp))
            soup = BeautifulSoup(f_detail.read(), 'lxml')
            # Time
            time_tmp = soup.findAll('dd', class_='cmnc-publish')
            time_tmp = self.r_time.sub('', time_tmp[0].text)
            time_list.append(time_tmp)
            # Article
            main_article = soup.find_all('div', class_='cmn-article_text a-cf JSID_key_fonttxt m-streamer_medium')
            parts_article = main_article[0].find_all('p')
            entire_honbun = ''
            for parts in parts_article:
                tmp = parts.text
                tmp = tmp.replace('\u3000', '')
                entire_honbun = entire_honbun + tmp
            honbun_list.append(entire_honbun)

        for _t, _st, _ss, _l, _h in zip(time_list, section_title_list, section_snippet_list, link_list, honbun_list):
            one_news_info_ary = []
            one_news_info_ary.append(self.r.sub('', str(_t).replace('\n', '')))
            one_news_info_ary.append(self.r.sub('', str(_st).replace('\n', '')))
            one_news_info_ary.append(self.r.sub('', str(_ss).replace('\n', '')))
            one_news_info_ary.append(str('https://www.nikkei.com') + str(_l))  # e.g. https://www.nikkei.com/article/DGXMZO43602750R10C19A4I00000/
            one_news_info_ary.append(self.r.sub('', str(_h).replace('\n', '')))
            news_ary.append(one_news_info_ary)

        return news_ary

    def create_histogram(self, _input_path: str):
        _df = self.fope.excel_to_df(_input_path=_input_path)

        histogram = self.nal.create_histogram(_df=_df, _column='Snippet', _typ='meishi')
        print('done')


if __name__ == '__main__':
    get_nikkei_tech = GetNTechNews()
    kobun_df = None
    for i in tqdm(range(1, 9884)):
        try:
            page_link = get_nikkei_tech.get_each_news_info_and_link('https://www.nikkei.com/technology/archive/?bn=' + str(i))
        except:
            print('error: page' + str(i))
            continue
        for idx, each_news in enumerate(page_link):
            if i == 1 and idx == 0:
                kobun_df = pd.DataFrame({'Date': [each_news[0]], 'Title': [each_news[1]], 'Snippet': [each_news[2]], 'link': [each_news[3]], 'honbun': [each_news[4]]}, index=[0])
                kobun_df = kobun_df.loc[:, ['Date', 'Title', 'Snippet', 'link', 'honbun']]  # sort columns
            else:
                kobun_df = kobun_df.append(pd.Series(data=[each_news[0], each_news[1], each_news[2], each_news[3], each_news[4]], index=['Date', 'Title', 'Snippet', 'link', 'honbun']), ignore_index=True)
        kobun_df.reset_index(drop=True, inplace=True)
        # 途中経過
        if i % 500 == 0: get_nikkei_tech.fope.df_to_excel(kobun_df, _output_file='../export_' + str(i) + '.xlsx')

    get_nikkei_tech.fope.df_to_excel(kobun_df, _output_file='../export.xlsx')
    # get_nikkei_tech.create_histogram('../news_nikkei_tech.xlsx')
