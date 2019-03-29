"""
Python PGM to get News article from https://jp.reuters.com.
"""
import urllib
from urllib.request import urlopen
from bs4 import BeautifulSoup
import re
from datetime import datetime
from pyknp import KNP
import pandas as pd


class GetNFudosanNews:
    def __init__(self):
        self.r = re.compile(r"<[^>]*?>")
        self.r_corp = re.compile(r"（[^）]*）")
        self.knp = KNP(option='-tab -anaphora', jumanpp=True)

    @staticmethod
    def nowtime():
        """
        今の時間をstr形式で返すだけの関数
        :return:
        """
        from datetime import datetime
        return str(datetime.now().strftime('%Y年%m月%d日'))

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

    def get_each_news_info_and_link(self, daily_url):
        """
        newsアーカイブ1ページごとに日付、概要、ニュースURLを配列で取得する機能.
        :param daily_url: newsアーカイブ記事のURL
        :return:
        """
        # 変数定義
        section_title_list = []
        title_list = []
        summary_list = []
        link_list = []

        f = urlopen(daily_url)
        soup = BeautifulSoup(f.read(), 'lxml')
        main = soup.findAll('div', id='mainContent')
        news_ary = []
        daily_list = main[0].findAll('section', class_='section article-index')  # Get section.
        # 日単位
        for daily_newses in daily_list:
            # 見出し
            section_title_tmp = daily_newses.find_all('h2')
            if len(section_title_tmp) == 0: continue
            section_title = self.r.sub('', str(section_title_tmp[0]))
            if ('のニュース' not in str(section_title)) and ('新着記事一覧' not in str(section_title)): continue
            for daily_pickup_news in daily_newses.find_all('section', class_='pickup-nfm'):
                a = daily_pickup_news.find_all('a')
                # 1 news内のリンク毎
                for each_a in a:
                    try:
                        # title
                        title_tmp = each_a.find_all('h3')
                        title = self.r.sub('', str(title_tmp[0].get_text()))
                        # summary
                        summary_tmp = each_a.find_all('p', class_='summary')
                        summary = self.r.sub('', str(summary_tmp[0].get_text()))
                        # link
                        link = each_a.attrs['href']
                        # append if all info above is corrected.
                        section_title_list.append(section_title)
                        title_list.append(title)
                        summary_list.append(summary)
                        link_list.append(link)
                    except:
                        continue
            # その他
            other_news = daily_newses.find_all('ul', class_='list-type1')
            # 1 news毎
            for daily_other_news in other_news[0].find_all('li'):
                a = daily_other_news.find_all('a')
                # 1 news内のリンク毎
                for each_a in a:
                    # 関連記事のリンクを避ける為にtryを置く
                    try:
                        # title
                        title_tmp = each_a.find_all('h3')
                        title = self.r.sub('', str(title_tmp[0].get_text()))
                        # summary
                        summary_tmp = each_a.find_all('p', class_='summary')
                        summary = self.r.sub('', summary_tmp[0].get_text())
                        # link
                        link = each_a.attrs['href']
                        # append if all info above is corrected.
                        section_title_list.append(section_title)
                        title_list.append(title)
                        summary_list.append(summary)
                        link_list.append(link)
                    except:
                        continue
        for _st, _t, _s, _a in zip(section_title_list, title_list, summary_list, link_list):
            one_news_info_ary = []
            title = self.r.sub('', str(_st).replace('\n', ''))
            if title == '新着記事一覧':
                title = self.nowtime()
            if 'のニュース一覧' in title:
                title = title.replace('のニュース一覧', '')
                tdatetime = datetime.strptime(title, '%m月%d日')
                tdatetime = tdatetime.replace(year=2019)
                title = tdatetime.strftime('%Y年%m月%d日')
            one_news_info_ary.append(title)
            one_news_info_ary.append(self.r.sub('', str(_t).replace('\n', '')))
            one_news_info_ary.append(self.r.sub('', str(_s).replace('\n', '')))
            one_news_info_ary.append(str('https://tech.nikkeibp.co.jp') + str(_a))  # e.g. https://tech.nikkeibp.co.jp/kn/atcl/nfmnews/15/032705201/
            news_ary.append(one_news_info_ary)

        return news_ary

    def analyse(self, line):
        """
        構文解析を行う機能
        :param line: 構文解析する文章
        :return:
        """
        # 解析
        line = self.r_corp.sub('', line)
        result = self.knp.parse(line)
        # search parent_id = -1
        parent = None
        for res in result._bnst:
            if res.parent_id == -1: parent = res.bnst_id
        # 格解析結果を取得
        kaku_analyse_result = result._bnst[int(parent)]._tag_list._tag[0].features['格解析結果']
        """
        # MEMO 格要素郡(kaku_elements)の例 #
        ['ガ/C/会社/5/0/1',
         'ヲ/C/持分/12/0/1',
         'ニ/U/-/-/-/-',
         'ト/U/-/-/-/-',
         'デ/U/-/-/-/-',
         'カラ/U/-/-/-/-',
         'ヨリ/U/-/-/-/-',
         'マデ/U/-/-/-/-',
         'ヘ/U/-/-/-/-',
         '時間/U/-/-/-/-',
         '外の関係/U/-/-/-/-',
         'ノ/U/-/-/-/-',
         '修飾/U/-/-/-/-',
         'ニヨル/U/-/-/-/-',
         'トスル/U/-/-/-/-',
         'ニオク/U/-/-/-/-',
         'ヲハジメル/U/-/-/-/-',
         'ニツク/U/-/-/-/-',
         'ヲツウジル/U/-/-/-/-',
         'ニクワエル/U/-/-/-/-']
         """
        kaku_elements = kaku_analyse_result.split(':')[-1].split(';')
        # print(kaku_elements)
        kaku_elements_dic = {}
        for element in kaku_elements:
            element_detail = element.split('/')
            kaku_elements_dic[element_detail[0]] = element_detail[1:]
        ######################
        # ガ格を取得
        ######################
        ga_kaku = kaku_elements_dic['ガ'][1]
        try:  # if 'ヲ/U/-/-/-/-', can not convert to integer.
            ga_kaku_tag_id = int(kaku_elements_dic['ガ'][2])
        except ValueError:
            ga_kaku_tag_id = None
        ga_kaku_bnst_midasi = None
        ga_kaku_bnst_id = None
        for res in result._bnst:
            for tag in res._tag_list._tag:
                if tag.normalized_repname.split('/')[0] == ga_kaku and tag.tag_id == ga_kaku_tag_id:
                    ga_kaku_bnst_midasi_tmp = res.repname.split('+')  # res.repname: '特定/とくてい+目的/もくてき+会社/かいしゃ'
                    ga_kaku_bnst_midasi = ''.join([x.split('/')[0] for x in ga_kaku_bnst_midasi_tmp])
                    ga_kaku_bnst_id = res.bnst_id
        for res in result._bnst:
            if res.parent_id == ga_kaku_bnst_id:
                ga_kaku_bnst_midasi = res.midasi + ga_kaku_bnst_midasi
        ######################
        # ヲ格を取得
        ######################
        wo_kaku = kaku_elements_dic['ヲ'][1]  # type: str
        try:  # if 'ヲ/U/-/-/-/-', can not convert to integer.
            wo_kaku_tag_id = int(kaku_elements_dic['ヲ'][2])  # type: int
        except ValueError:
            wo_kaku_tag_id = None
        wo_kaku_bnst_midasi = None
        wo_kaku_bnst_id = None
        for res in result._bnst:
            for tag in res._tag_list._tag:
                if tag.normalized_repname.split('/')[0] == wo_kaku and tag.tag_id == wo_kaku_tag_id:
                    wo_kaku_bnst_midasi_tmp = res.repname.split('+')  # res.repname: '特定/とくてい+目的/もくてき+会社/かいしゃ'
                    wo_kaku_bnst_midasi = ''.join([x.split('/')[0] for x in wo_kaku_bnst_midasi_tmp])
                    wo_kaku_bnst_id = res.bnst_id
        for res in result._bnst:
            if res.parent_id == wo_kaku_bnst_id:
                wo_kaku_bnst_midasi = res.midasi + wo_kaku_bnst_midasi
        ######################
        # 二格を取得
        ######################
        ni_kaku = kaku_elements_dic['ニ'][1]  # type: str
        try:  # if 'ニ/U/-/-/-/-', can not convert to integer.
            ni_kaku_tag_id = int(kaku_elements_dic['ニ'][2])  # type: int
        except ValueError:
            ni_kaku_tag_id = None
        ni_kaku_bnst_midasi = None
        ni_kaku_bnst_id = None
        for res in result._bnst:
            for tag in res._tag_list._tag:
                if tag.normalized_repname.split('/')[0] == ni_kaku and tag.tag_id == ni_kaku_tag_id:
                    ni_kaku_bnst_midasi_tmp = res.repname.split('+')  # res.repname: '特定/とくてい+目的/もくてき+会社/かいしゃ'
                    ni_kaku_bnst_midasi = ''.join([x.split('/')[0] for x in ni_kaku_bnst_midasi_tmp])
                    ni_kaku_bnst_id = res.bnst_id
        for res in result._bnst:
            if res.parent_id == ni_kaku_bnst_id:
                ni_kaku_bnst_midasi = res.midasi + ni_kaku_bnst_midasi
        ######################
        # 動詞を取得
        ######################
        doushi_tmp = result._bnst[int(parent)].head_repname  # doushi_tmp: '開業/かいぎょう'
        doushi = doushi_tmp.split('/')[0]
        return ga_kaku_bnst_midasi, wo_kaku_bnst_midasi, ni_kaku_bnst_midasi, doushi


if __name__ == '__main__':
    get_nikkei_fudosan = GetNFudosanNews()
    news_df = None
    page_link = get_nikkei_fudosan.get_each_news_info_and_link('https://tech.nikkeibp.co.jp/kn/NFM/')
    for num, each_news in enumerate(page_link):
        try:
            if num == 0:
                news_df = pd.DataFrame({'Date': [str(each_news[0])], 'Title': [str(each_news[1])], 'Summary': [str(each_news[2])], 'Link': [str(each_news[3])]}, index=[0])
                news_df = news_df.loc[:, ['Date', 'Title', 'Summary', 'Link']]  # sort columns
            else:
                news_df = news_df.append(pd.Series(data=[str(each_news[0]), str(each_news[1]), str(each_news[2]), str(each_news[3])], index=['Date', 'Title', 'Summary', 'Link']), ignore_index=True)
        except:
            continue
    ga_list = []
    wo_list = []
    ni_list = []
    what_list = []
    kobun_df = None
    for idx, row in news_df.iterrows():
        print(str(row['Summary']).split('。')[0])
        ga, wo, ni, do = get_nikkei_fudosan.analyse(str(row['Summary']).split('。')[0])
        print('ガ: ' + str(ga))
        print('ヲ: ' + str(wo))
        print('二: ' + str(ni))
        print('What:  ' + str(do))
        print('----------------------')
        ga_list.append(ga)
        wo_list.append(wo)
        ni_list.append(ni)
        what_list.append(do)
        if idx == 0:
            kobun_df = pd.DataFrame({'ガ': [ga], 'ヲ': [wo], 'ニ': [ni], 'Do': [do]}, index=[0])
            kobun_df = kobun_df.loc[:, ['ガ', 'ヲ', 'ニ', 'Do']]  # sort columns
        else:
            kobun_df = kobun_df.append(pd.Series(data=[ga, wo, ni, do], index=['ガ', 'ヲ', 'ニ', 'Do']), ignore_index=True)
    kobun_df.reset_index(drop=True, inplace=True)
    news_df = news_df.join(kobun_df)
    news_df.to_excel('news_nikkei_fudosan.xlsx', sheet_name='Reuters', index=False, encoding='utf8')
