import pandas as pd
import tabula

def create_csv(url):
    kensa_pdf = tabula.read_pdf(url, pages='all')
    kensa_table = kensa_pdf[0]
    kensa_table.columns = ['date', 'empty', 'youbi', 'kensa', 'yousei']
    kensa_table = kensa_table[kensa_table['date'] != '計']
    kensa_table['date'] = kensa_table['date'].str.replace('令和2年 2月', '2月29日')
    kensa_table['date'] = '2020年' + kensa_table['date']
    kensa_table['date'] = pd.to_datetime(kensa_table['date'], format='%Y年%m月%d日')
    kensa_table.to_csv('dist/inspections.csv')
