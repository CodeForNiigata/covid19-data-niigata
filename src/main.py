from bs4 import BeautifulSoup
import openpyxl
import pandas as pd
import requests
import tabula

base_url = 'https://www.pref.niigata.lg.jp'

page_url = base_url + '/sec/kenko/bukan-haien.html'
page = requests.get(page_url)
soup = BeautifulSoup(page.content, 'html.parser')

links = soup.select('a:contains("【新潟県内の報告一覧表】")')
houkoku_url = links[0].get('href')
links = soup.select('a:contains("センター相談件数一覧表")')
soudan_url = links[0].get('href')
links = soup.select('a:contains("検査件数一覧表")')
kensa_url = links[0].get('href')

houkoku_pdf = tabula.read_pdf(base_url + houkoku_url, pages='all')
houkoku_table = houkoku_pdf[0]
houkoku_table.columns = ['no', 'case_no', 'date', 'age', 'sex', 'address', 'job']
houkoku_table['date'] = '2020年' + houkoku_table['date']
houkoku_table['date'] = pd.to_datetime(houkoku_table['date'], format='%Y年%m月%d日')
houkoku_table['address'] = houkoku_table['address'].replace('\r', '', regex=True)
houkoku_table['job'] = houkoku_table['job'].replace('\r', '', regex=True)
houkoku_table.to_csv('houkoku.csv')

soudan_pdf = tabula.read_pdf(base_url + soudan_url, pages='all')
soudan_table = soudan_pdf[0]
soudan_table.columns = ['date', 'empty', 'youbi', 'soudan', 'shoukai', 'note']
soudan_table = soudan_table[soudan_table['date'] != '計']
soudan_table = soudan_table[4:]
soudan_table['date'] = soudan_table['date'].str.replace('令和2年 ', '')
soudan_table['date'] = '2020年' + soudan_table['date']
soudan_table['date'] = pd.to_datetime(soudan_table['date'], format='%Y年%m月%d日')
soudan_table.to_csv('soudan.csv')

kensa_pdf = tabula.read_pdf(base_url + kensa_url, pages='all')
kensa_table = kensa_pdf[0]
kensa_table.columns = ['date', 'empty', 'youbi', 'kensa', 'yousei']
kensa_table = kensa_table[kensa_table['date'] != '計']
kensa_table['date'] = kensa_table['date'].str.replace('令和2年 2月', '2月29日')
kensa_table['date'] = '2020年' + kensa_table['date']
kensa_table['date'] = pd.to_datetime(kensa_table['date'], format='%Y年%m月%d日')
kensa_table.to_csv('kensa.csv')
