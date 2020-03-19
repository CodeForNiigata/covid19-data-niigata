from bs4 import BeautifulSoup
import openpyxl
import pandas as pd
import requests
import tabula

base_url = 'https://www.pref.niigata.lg.jp'


def get_url():
    page_url = base_url + '/sec/kenko/bukan-haien.html'
    page = requests.get(page_url)
    soup = BeautifulSoup(page.content, 'html.parser')

    links = soup.select('a:contains("【新潟県内の報告一覧表】")')
    houkoku_url = base_url + links[0].get('href')
    links = soup.select('a:contains("センター相談件数一覧表")')
    soudan_url = base_url + links[0].get('href')
    links = soup.select('a:contains("検査件数一覧表")')
    kensa_url = base_url + links[0].get('href')

    return houkoku_url, soudan_url, kensa_url
