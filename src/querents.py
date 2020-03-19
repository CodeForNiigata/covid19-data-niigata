import pandas as pd
import tabula


def create_csv(url):
    soudan_pdf = tabula.read_pdf(url, pages='all')
    soudan_table = soudan_pdf[0]
    soudan_table.columns = ['日', 'empty', '曜日', '相談対応件数', '帰国者・接触者外来を紹介した人数', '備考']
    soudan_table = soudan_table[soudan_table['日'] != '計']
    soudan_table = soudan_table[4:]
    soudan_table['日'] = soudan_table['日'].str.replace('令和2年 ', '')
    soudan_table['日'] = '2020年' + soudan_table['日']
    soudan_table['日'] = pd.to_datetime(soudan_table['日'], format='%Y年%m月%d日')
    soudan_table = soudan_table.drop(columns=['empty'])
    soudan_table = soudan_table.set_index('日')
    soudan_table.to_csv('dist/querents.csv')
