import pandas as pd
import tabula


def create_csv(url):
    soudan_pdf = tabula.read_pdf(url, pages='all')
    soudan_table = soudan_pdf[0]
    soudan_table.columns = ['date', 'empty', 'youbi', 'soudan', 'shoukai', 'note']
    soudan_table = soudan_table[soudan_table['date'] != '計']
    soudan_table = soudan_table[4:]
    soudan_table['date'] = soudan_table['date'].str.replace('令和2年 ', '')
    soudan_table['date'] = '2020年' + soudan_table['date']
    soudan_table['date'] = pd.to_datetime(soudan_table['date'], format='%Y年%m月%d日')
    soudan_table.to_csv('dist/querents.csv')