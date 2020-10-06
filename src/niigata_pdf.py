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
    page_url = base_url + '/site/shingata-corona/256362836.html'
    page = requests.get(page_url)
    soup = BeautifulSoup(page.content, 'html.parser')

    houkoku_date = ''
    soudan_kensa_date = ''
    paragraphs = soup.select('h3:contains("県内における「帰国者・接触者相談センター」への相談件数及び検査件数") + p')
    if len(paragraphs) == 1:
        soudan_kensa_text = paragraphs[0].get_text()
        soudan_kensa_matches = re.match('.*令和(\w+)年(\w+)月(\w+)日公表分（(\w+)時(\w+)分.*', soudan_kensa_text)
        (_, month, day, hour, minute) = soudan_kensa_matches.groups()
        month = to_half_width(month).zfill(2)
        day = to_half_width(day).zfill(2)
        hour = to_half_width(hour).zfill(2)
        minute = to_half_width(minute).zfill(2)
        houkoku_date = f"2020-{month}-{day}T{hour}:{minute}:00.000Z"
        soudan_kensa_date = f"2020-{month}-{day}T{hour}:{minute}:00.000Z"

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
    page_url = base_url + '/site/shingata-corona/index.html'
    page = requests.get(page_url)
    soup = BeautifulSoup(page.content, 'html.parser')

    in_count = 0

    table = soup.find('table', summary="入退院状況")
    subject = table.select_one('tbody > tr:nth-of-type(1)')
    data = table.select_one('tbody > tr:nth-of-type(2)')

    matcher = re.compile('([0-9０-９]+)')

    # 入院中
    if "入院中" in subject.find_all('th')[2].get_text():
        in_text = data.find_all('td')[1].get_text()
        in_match = matcher.search(in_text)
        [in_count] = in_match.groups()
        in_count = int(to_half_width(in_count))

    # 宿泊療養中
    if subject.find_all('th')[4].get_text() == "宿泊療養中":
        in_hotel_text = data.find_all('td')[3].get_text()
        in_hotel_match = matcher.search(in_hotel_text)
        [in_hotel_count] = in_hotel_match.groups()
        in_hotel_count = int(to_half_width(in_hotel_count))
        in_count = in_count + in_hotel_count

    # 退院済み
    out_count = ''

    if subject.find_all('th')[5].get_text() == "退院・退所":
        out_text = data.find_all('td')[4].get_text()
        out_match = matcher.search(out_text)
        [out_count] = out_match.groups()
        out_count = int(to_half_width(out_count))

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
    page_url = base_url + '/site/shingata-corona/256362836.html'
    page = requests.get(page_url)
    soup = BeautifulSoup(page.content, 'html.parser')

    links = soup.select('a:contains("センター相談件数")')
    soudan_url = base_url + links[0].get('href')
    links = soup.select('a:contains("検査件数")')
    kensa_url = base_url + links[0].get('href')

    return soudan_url, kensa_url


def download(url, path):
    try:
        with urllib.request.urlopen(url) as web_file:
            data = web_file.read()
        with open(path, mode='wb') as local_file:
            local_file.write(data)
    except urllib.error.URLError as e:
        print(e)


def download_pdfs():
    (soudan_url, kensa_url) = get_url()
    download(soudan_url, './dist/pdf/150002_niigata_covid19_call_center.pdf')
    download(kensa_url, './dist/pdf/150002_niigata_covid19_test.pdf')


if __name__ == '__main__':
    main()
