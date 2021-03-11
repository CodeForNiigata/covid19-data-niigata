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
    download_xlsxs()


def create_update_date():
    page_url = base_url + '/site/shingata-corona/256362836.html'
    page = requests.get(page_url)
    soup = BeautifulSoup(page.content, 'html.parser')

    soudan_paragraphs = soup.select('p:contains("（1）新潟県新型コロナ受診・相談センター") + p')
    soudan_text = soudan_paragraphs[0].get_text()
    soudan_matches = re.match('.*令和(\w+)年(\w+)月(\w+)日公表分（(\w+)時.*', soudan_text)
    (_, month, day, hour) = soudan_matches.groups()
    month = to_half_width(month).zfill(2)
    day = to_half_width(day).zfill(2)
    hour = to_half_width(hour).zfill(2)
    minute = '0'
    soudan_date = f"2021-{month}-{day}T{hour}:{minute}:00.000Z"

    kensa_paragraphs = soup.select('p:contains("（2）検査件数") + p')
    kensa_text = kensa_paragraphs[0].get_text()
    kensa_matches = re.match('.*令和(\w+)年(\w+)月(\w+)日公表分（(\w+)時.*', kensa_text)
    (_, month, day, hour) = kensa_matches.groups()
    month = to_half_width(month).zfill(2)
    day = to_half_width(day).zfill(2)
    hour = to_half_width(hour).zfill(2)
    minute = '0'
    kensa_date = f"2021-{month}-{day}T{hour}:{minute}:00.000Z"

    df = pd.DataFrame({
        'name': [
            'call_center',
            'confirm_negative',
            'patients',
            'test_count',
            'test_people',
        ],
        'updated_at': [
            soudan_date,
            kensa_date,
            kensa_date,
            kensa_date,
            kensa_date,
        ]
    })
    df.to_csv('./dist/csv/updated_at.csv', index=False)


def create_hospitalization():
    page_url = base_url + '/site/shingata-corona/index.html'
    page = requests.get(page_url)
    soup = BeautifulSoup(page.content, 'html.parser')

    in_count = 0

    table = soup.find('table', summary="入退院状況")
    subject = table.select_one('tbody > tr:nth-of-type(1)')
    data = table.select_one('tbody > tr:nth-of-type(2)')

    matcher = re.compile('([0-9０-９\,]+)')

    # 入院中
    if "入院中" in subject.find_all('th')[2].get_text():
        in_text = data.find_all('td')[1].get_text()
        in_match = matcher.search(in_text)
        [in_count] = in_match.groups()
        in_count = int(to_half_width(in_count.replace(',', '')))

    # 重症者
    seriously_count = ''

    if "うち重症者" in subject.find_all('th')[3].get_text():
        seriously_text = data.find_all('td')[2].get_text()
        seriously_match = matcher.search(seriously_text)
        [seriously_count] = seriously_match.groups()
        seriously_count = int(to_half_width(seriously_count.replace(',', '')))

    # 退院済み
    out_count = ''

    if subject.find_all('th')[5].get_text() == "退院・退所":
        out_text = data.find_all('td')[4].get_text()
        out_match = matcher.search(out_text)
        [out_count] = out_match.groups()
        out_count = int(to_half_width(out_count.replace(',', '')))

    # 死亡
    decease_count = ''
    if subject.find_all('th')[6].get_text() == "うち死亡":
        decease_text = data.find_all('td')[5].get_text()
        decease_match = matcher.search(decease_text)
        [decease_count] = decease_match.groups()
        decease_count = int(to_half_width(decease_count.replace(',', '')))

    df = pd.DataFrame({
        'type': [
            'hospitalization',
            'seriously',
            'discharge',
            'decease',
        ],
        'count': [
            int(in_count),
            int(seriously_count),
            int(out_count),
            int(decease_count),
        ]
    })
    df.to_csv('./dist/csv/hospitalization.csv', index=False)


def to_half_width(text):
    return text.translate(str.maketrans({chr(0xFF01 + i): chr(0x21 + i) for i in range(94)}))


def get_url():
    page_url = base_url + '/site/shingata-corona/256362836.html'
    page = requests.get(page_url)
    soup = BeautifulSoup(page.content, 'html.parser')

    links = soup.select('a:contains("センター相談件数")')
    soudan_url = base_url + links[1].get('href')
    links = soup.select('a:contains("検査件数一覧")')
    kensa_url = base_url + links[1].get('href')

    return soudan_url, kensa_url


def download(url, path):
    try:
        with urllib.request.urlopen(url) as web_file:
            data = web_file.read()
        with open(path, mode='wb') as local_file:
            local_file.write(data)
    except urllib.error.URLError as e:
        print(e)


def download_xlsxs():
    (soudan_url, kensa_url) = get_url()
    download(soudan_url, './dist/xlsx/150002_niigata_covid19_call_center.xlsx')
    download(kensa_url, './dist/xlsx/150002_niigata_covid19_test.xlsx')


if __name__ == '__main__':
    main()
