from bs4 import BeautifulSoup
import pandas as pd
import re
import requests
import urllib.error
import urllib.request


base_url = 'https://www.pref.niigata.lg.jp'


def main():
    create_hospitalization()
    create_update_date()
    download_pdfs()


def create_update_date():
    page_url = base_url + '/sec/kenko/covid19.html'
    page = requests.get(page_url)
    soup = BeautifulSoup(page.content, 'html.parser')

    houkoku_date = ''
    paragraphs = soup.select('h2:contains("重要なお知らせ") + p')
    if len(paragraphs) == 1:
        houkoku_text = paragraphs[0].get_text()
        houkoku_matches = re.match('.*令和(\w+)年(\w+)月(\w+)日(\w+)時.*', houkoku_text, re.U)
        (_, month, day, hour) = houkoku_matches.groups()
        month = to_half_width(month).zfill(2)
        day = to_half_width(day).zfill(2)
        hour = to_half_width(hour).zfill(2)
        houkoku_date = f"2020-{month}-{day}T{hour}:00:00.000Z"

    soudan_kensa_date = ''
    paragraphs = soup.select('h3:contains("県内における「帰国者・接触者相談センター」への相談件数及び検査件数") + p')
    if len(paragraphs) == 1:
        soudan_kensa_text = paragraphs[0].get_text()
        soudan_kensa_matches = re.match('.*令和(\w+)年(\w+)月(\w+)日(\w+)時(\w+)分.*', soudan_kensa_text, re.U)
        (_, month, day, hour, _) = soudan_kensa_matches.groups()
        month = to_half_width(month).zfill(2)
        day = to_half_width(day).zfill(2)
        hour = to_half_width(hour).zfill(2)
        soudan_kensa_date = f"2020-{month}-{day}T{hour}:00:00.000Z"

    df = pd.DataFrame({
        'name': [
            'call_center',
            'confirm_negative',
            'patients',
            'test_count',
            'test_people',
        ],
        'updated_at': [
            soudan_kensa_date,
            soudan_kensa_date,
            houkoku_date,
            soudan_kensa_date,
            soudan_kensa_date,
        ]
    })
    df.to_csv('./dist/csv/updated_at.csv', index=False)


def create_hospitalization():
    page_url = base_url + '/sec/kenko/covid19.html'
    page = requests.get(page_url)
    soup = BeautifulSoup(page.content, 'html.parser')

    in_count = ''
    paragraphs = soup.select('p:contains("・入院中（準備中含む）：")')
    if len(paragraphs) == 1:
        in_text = paragraphs[0].get_text()
        in_match = re.search('.*・入院中（準備中含む）：(\w+)例.*', in_text, re.U)
        [in_count] = in_match.groups()
        in_count = to_half_width(in_count)

    out_count = ''
    paragraphs = soup.select('p:contains("・退院済：")')
    if len(paragraphs) == 1:
        out_text = paragraphs[0].get_text()
        out_match = re.search('.*・退院済：(\w+)例.*', out_text, re.U)
        [out_count] = out_match.groups()
        out_count = to_half_width(out_count)

    df = pd.DataFrame({
        'type': [
            'hospitalization',
            'discharge',
        ],
        'count': [
            int(in_count),
            int(out_count),
        ]
    })
    df.to_csv('./dist/csv/hospitalization.csv', index=False)


def to_half_width(text):
    return text.translate(str.maketrans({chr(0xFF01 + i): chr(0x21 + i) for i in range(94)}))


def get_url():
    page_url = base_url + '/sec/kenko/covid19.html'
    page = requests.get(page_url)
    soup = BeautifulSoup(page.content, 'html.parser')

    links = soup.select('a:contains("【新潟県内の報告一覧表】")')
    houkoku_url = base_url + links[0].get('href')
    links = soup.select('a:contains("センター相談件数一覧表")')
    soudan_url = base_url + links[0].get('href')
    links = soup.select('a:contains("検査件数一覧表")')
    kensa_url = base_url + links[0].get('href')

    return houkoku_url, soudan_url, kensa_url


def download(url, path):
    try:
        with urllib.request.urlopen(url) as web_file:
            data = web_file.read()
        with open(path, mode='wb') as local_file:
            local_file.write(data)
    except urllib.error.URLError as e:
        print(e)


def download_pdfs():
    (houkoku_url, soudan_url, kensa_url) = get_url()
    download(houkoku_url, './dist/pdf/150002_niigata_covid19_patients.pdf')
    download(soudan_url, './dist/pdf/150002_niigata_covid19_call_center.pdf')
    download(kensa_url, './dist/pdf/150002_niigata_covid19_test.pdf')


if __name__ == '__main__':
    main()
