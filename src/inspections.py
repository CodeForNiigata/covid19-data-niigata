import pandas as pd
import tabula

def create_csv(url):
    kensa_pdf = tabula.read_pdf(url, pages='all')
    kensa_table = kensa_pdf[0]
    kensa_table.columns = ['結果判明日', 'empty', '曜日', '検査件数', 'うち陽性件数']
    kensa_table = kensa_table[kensa_table['結果判明日'] != '計']
    kensa_table['結果判明日'] = kensa_table['結果判明日'].str.replace('令和2年 2月', '2月29日')
    kensa_table['結果判明日'] = '2020年' + kensa_table['結果判明日']
    kensa_table['結果判明日'] = pd.to_datetime(kensa_table['結果判明日'], format='%Y年%m月%d日')
    kensa_table = kensa_table.drop(columns=['empty'])
    kensa_table = kensa_table.set_index('結果判明日')
    kensa_table.to_csv('dist/inspections.csv')
