import pandas as pd
import tabula


def create_csv(url):
    houkoku_pdf = tabula.read_pdf(url, pages='all')
    houkoku_table = houkoku_pdf[0]
    houkoku_table.columns = ['no', 'case_no', 'date', 'age', 'sex', 'address', 'job']
    houkoku_table['date'] = '2020年' + houkoku_table['date']
    houkoku_table['date'] = pd.to_datetime(houkoku_table['date'], format='%Y年%m月%d日')
    houkoku_table['address'] = houkoku_table['address'].replace('\r', '', regex=True)
    houkoku_table['job'] = houkoku_table['job'].replace('\r', '', regex=True)
    houkoku_table.to_csv('houkoku.csv')
