import pandas as pd
import tabula


def create_csv(url):
    houkoku_pdf = tabula.read_pdf(url, pages='all')
    houkoku_table = houkoku_pdf[0]
    houkoku_table.columns = ['患者No', '例', '判明日', '年代', '性別', '居住地', '職業']
    houkoku_table['判明日'] = '2020年' + houkoku_table['判明日']
    houkoku_table['判明日'] = pd.to_datetime(houkoku_table['判明日'], format='%Y年%m月%d日')
    houkoku_table['居住地'] = houkoku_table['居住地'].replace('\r', '', regex=True)
    houkoku_table['職業'] = houkoku_table['職業'].replace('\r', '', regex=True)
    houkoku_table = houkoku_table.set_index('患者No')
    houkoku_table.to_csv('dist/patients.csv')
