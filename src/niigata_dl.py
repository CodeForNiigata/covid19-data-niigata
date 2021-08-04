from bs4 import BeautifulSoup
import re
import urllib.error
import urllib.request


base_url = 'https://www.pref.niigata.lg.jp'

index_path = 'dist/html/index.html'
latest_path = 'dist/html/latest.html'


def __download(url, path):
    try:
        with urllib.request.urlopen(url) as web_file:
            data = web_file.read()
        with open(path, mode='wb') as local_file:
            local_file.write(data)
    except urllib.error.URLError as e:
        print(e)


def download_page():
    __download(f'{base_url}/site/shingata-corona/', index_path)
    with open(index_path) as file:
        soup = BeautifulSoup(file, 'html.parser')
    link_url = soup.find('a', string='県内における発生状況の詳細はこちら').attrs['href']
    __download(f'{base_url}{link_url}', latest_path)


def download_patients():
    with open(latest_path) as file:
        soup = BeautifulSoup(file, 'html.parser')
    pattern = re.compile('県内における感染者の発生状況.*\[PDFファイル／.*\]')
    links = soup.find_all('a', string=pattern)
    urls = [i.attrs['href'] for i in links]
    for index, url in enumerate(urls):
        print(f'download from {url}')
        __download(f'{base_url}{url}', f'dist/pdf/150002_niigata_covid19_patients_{index}.pdf')


def download_test():
    with open(latest_path) as file:
        soup = BeautifulSoup(file, 'html.parser')
    pattern = re.compile('検査件数一覧 \[Excelファイル／.*\].*')
    link = soup.find('a', string=pattern)
    url = link.attrs['href']
    __download(f'{base_url}{url}', 'dist/xlsx/150002_niigata_covid19_test.xlsx')


def download_call_center():
    with open(latest_path) as file:
        soup = BeautifulSoup(file, 'html.parser')
    pattern = re.compile('センター相談件数 \[Excelファイル／.*\].*')
    link = soup.find('a', string=pattern)
    url = link.attrs['href']
    __download(f'{base_url}{url}', 'dist/xlsx/150002_niigata_covid19_call_center.xlsx')


def main():
    download_page()
    download_patients()
    download_test()
    download_call_center()


if __name__ == '__main__':
    main()
