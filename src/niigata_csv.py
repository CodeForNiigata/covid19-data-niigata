from bs4 import BeautifulSoup
import glob
import pandas as pd
import re
from tabula import read_pdf

pd.set_option('display.max_columns', 100)
pd.set_option('display.unicode.east_asian_width', True)

index_path = 'dist/html/index.html'
latest_path = 'dist/html/latest.html'


digits_zenkaku_table = str.maketrans({
    '０': '0',
    '１': '1',
    '２': '2',
    '３': '3',
    '４': '4',
    '５': '5',
    '６': '6',
    '７': '7',
    '８': '8',
    '９': '9',
})


def main():
    create_positive_patients()
    create_inspectors()
    create_inspections_performed()
    create_negative_confirmations()
    create_call_center_consultations()
    create_update_date()
    create_hospitalization()


def get_city_code():
    city_table = pd.read_excel('./src/city_code.xls', sheet_name='R1.5.1現在の団体')
    city_table = city_table.rename(columns={
        '団体コード': 'code',
        '都道府県名\n（漢字）': 'pref_name',
        '市区町村名\n（漢字）': 'city_name',
        '都道府県名\n（カナ）': 'pref_kana',
        '市区町村名\n（カナ）': 'city_kana',
    })
    city_table['code'] = city_table['code'].astype(str)

    ku_table = pd.read_excel('./src/city_code.xls', sheet_name='H30.10.1政令指定都市', header=None)
    ku_table.columns = ['code', 'city_name', 'city_kana']
    ku_table['code'] = ku_table['code'].astype(str)

    return city_table, ku_table


def _7columns(page):
    page = pd.concat([page, page['患者 No.'].str.split(' ', expand=True)], axis=1).drop('患者 No.', axis=1)
    page = pd.concat([page, page['濃厚接触者数 備考'].str.split(' ', expand=True)], axis=1).drop('濃厚接触者数 備考', axis=1)
    page.columns = [
        '判明日',
        '年代',
        '性別',
        '居住地',
        '職業',
        '患者No.',
        '_',
        '濃厚接触者数',
        '備考',
    ]
    page = page[[
        '患者No.',
        '_',
        '判明日',
        '年代',
        '性別',
        '居住地',
        '職業',
        '濃厚接触者数',
        '備考',
    ]]
    return page

def _8columns(page):
    page = pd.concat([page, page['患者 No.'].str.split(' ', expand=True)], axis=1).drop('患者 No.', axis=1)
    page.columns = [
        '判明日',
        '年代',
        '性別',
        '居住地',
        '職業',
        '濃厚接触者数',
        '備考',
        '患者No.',
        '_',
    ]
    page = page[[
        '患者No.',
        '_',
        '判明日',
        '年代',
        '性別',
        '居住地',
        '職業',
        '濃厚接触者数',
        '備考',
    ]]
    return page

def _9columns(page):
    page.columns = [
        '患者No.',
        '_',
        '判明日',
        '年代',
        '性別',
        '居住地',
        '職業',
        '濃厚接触者数',
        '備考',
    ]
    return page

def _10columns(page):
    page = pd.concat([page, page['患者 No.'].str.split(' ', expand=True)], axis=1).drop('患者 No.', axis=1)
    page.columns = [
        '判明日',
        '年代',
        '性別',
        '居住地',
        '職業',
        '_1',
        '濃厚接触者数',
        '_2',
        '備考',
        '患者No.',
        '_',
    ]
    page = page[[
        '患者No.',
        '_',
        '判明日',
        '年代',
        '性別',
        '居住地',
        '職業',
        '濃厚接触者数',
        '備考',
    ]]
    return page

def get_patients():
    files = glob.glob('dist/pdf/150002_niigata_covid19_patients_*.pdf')
    tables = []
    for file in files:
        pages = read_pdf(file, pages='all')
        for index, page in enumerate(pages):
            if len(page.columns) == 7:
                pages[index] = _7columns(page)
            elif len(page.columns) == 8:
                pages[index] = _8columns(page)
            elif len(page.columns) == 9:
                pages[index] = _9columns(page)
            elif len(page.columns) == 10:
                pages[index] = _10columns(page)

        table = pd.concat(pages)
        tables.append(table)

    patients = pd.concat(tables)

    patients['患者No.'] = patients['患者No.'].astype(int)
    patients = patients.sort_values('患者No.')
    patients = patients.reset_index(drop=True)
    
    patients = patients[patients['患者No.'] != '欠番']
    patients = patients[patients['備考'].str.contains('取り下げ', na=False) == False]
    patients = patients[patients['判明日'] != '−']
    patients = patients[patients['判明日'] != '-']
    patients = patients[patients['判明日'] != '―']
    patients = patients[patients['判明日'] != '非公表']

    patients['判明日'] = patients['判明日'].str.replace('5日4日', '5月4日', regex=True)
    patients['判明日'] = patients['判明日'].str.replace('[(（].*曜日[)）]', '', regex=True)
    patients.loc[patients['患者No.'] < 548, '判明日'] = '2020年' + patients['判明日']
    patients.loc[patients['患者No.'] >= 548, '判明日'] = '2021年' + patients['判明日']
    patients['判明日'] = pd.to_datetime(patients['判明日'], format='%Y年%m月%d日')
    patients['判明日'] = patients['判明日'].dt.strftime('%Y-%m-%d')

    patients['年代'] = patients['年代'].str.replace('[(（]乳幼児[)）]', '', regex=True)
    patients['年代'] = patients['年代'].str.replace('\r', '', regex=True)
    patients['年代'] = patients['年代'].str.replace(' ', '', regex=True)
    patients['年代'] = patients['年代'].str.replace('[-―－]', '非公表', regex=True)
    patients['年代'] = patients['年代'].str.replace('非公表', '', regex=True)
    patients['年代'] = patients['年代'].str.replace('10歳代未満', '10歳未満', regex=True)
    patients['年代'] = patients['年代'].str.replace('90歳以上', '90歳代', regex=True)
    patients['年代'] = patients['年代'].str.replace('90歳代以上', '90歳代', regex=True)
    patients['年代'] = patients['年代'].str.replace('90歳代', '90歳以上', regex=True)

    patients['性別'] = patients['性別'].str.replace('[-―－]', '非公表', regex=True)
    patients['性別'] = patients['性別'].str.replace('非公表', '', regex=True)
    patients['性別'] = patients['性別'].str.replace('長岡市', '', regex=True)

    patients['職業'] = patients['職業'].str.replace('[-−―－]', '非公表', regex=True)
    patients['職業'] = patients['職業'].str.replace('非公表', '', regex=True)

    return patients


def get_tests():
    path = './dist/xlsx/150002_niigata_covid19_test.xlsx'
    tests = pd.read_excel(path, skiprows=[0, 1, 2], skipfooter=2, header=0, index_col=None, sheet_name='HP用検査表（月毎）')
    tests = tests.rename(columns={
        '月日': '検査実施日',
        '曜日': '検査実施曜日',
        '検査件数': 'PCR検査_検査件数',
        '陽性件数※': 'PCR検査_陽性件数',
        '検査件数.1': '抗原検査_検査件数',
        '陽性件数': '抗原検査_陽性件数',
    })
    # いらないデータの除去
    tests = tests[tests['検査実施曜日'].isna() == False]

    # 型をいい感じに
    tests['検査実施日'] = pd.to_datetime(tests['検査実施日'].astype(float), unit="D", origin=pd.Timestamp("1899/12/30"))
    tests['検査実施日'] = tests['検査実施日'].dt.strftime('%Y-%m-%d')

    tests['PCR検査_検査件数'] = tests['PCR検査_検査件数'].astype(int)

    tests['PCR検査_陽性件数'] = tests['PCR検査_陽性件数'].fillna(0)
    tests['PCR検査_陽性件数'] = tests['PCR検査_陽性件数'].astype(int)

    tests['結果判明日'] = tests['検査実施日']
    tests['検査件数'] = tests['PCR検査_検査件数']
    tests['うち陽性件数'] = tests['PCR検査_陽性件数']

    tests = tests[['結果判明日', '検査件数', 'うち陽性件数']]

    return tests


def get_call_centers():
    path = './dist/xlsx/150002_niigata_covid19_call_center.xlsx'
    call_centers = pd.read_excel(path, skiprows=[0, 1, 2], skipfooter=1)
    call_centers = call_centers.rename(columns={
        '日': '年号',
        'Unnamed: 1': '日',
        '曜日': '曜日',
        '相談対応件数（件）': '相談対応件数',
        '備考': '備考',
    })

    # 年号は無視
    call_centers = call_centers[call_centers['日'] != '1月']
    call_centers = call_centers[call_centers['日'] != '2月']
    call_centers = call_centers[call_centers['日'] != '3月']
    call_centers = call_centers[call_centers['日'] != '4月']
    call_centers = call_centers[call_centers['日'] != '5月']
    call_centers = call_centers[call_centers['日'] != '6月']
    call_centers = call_centers[call_centers['日'] != '7月']
    call_centers = call_centers[call_centers['日'] != '8月']
    call_centers = call_centers[call_centers['日'] != '9月']
    call_centers = call_centers[call_centers['日'] != '10月']
    call_centers = call_centers[call_centers['日'] != '11月']
    call_centers = call_centers[call_centers['日'] != '12月']
    call_centers = call_centers[call_centers['日'] != '計']

    call_centers['日'] = pd.to_datetime(call_centers['日'].astype(float), unit="D", origin=pd.Timestamp("1899/12/30"))
    call_centers['日'] = call_centers['日'].dt.strftime('%Y-%m-%d')

    call_centers = call_centers[call_centers['相談対応件数'].isna() == False]
    call_centers['相談対応件数'] = call_centers['相談対応件数'].astype(int)

    return call_centers


# 検査実施人数
def create_inspectors():
    inspectors = get_tests()

    inspectors['実施_年月日'] = inspectors['結果判明日']
    inspectors['全国地方公共団体コード'] = '150002'
    inspectors['都道府県名'] = '新潟県'
    inspectors['市区町村名'] = ''
    inspectors['検査実施_人数'] = inspectors['検査件数'].astype(int)
    inspectors['備考'] = ''

    inspectors = inspectors[[
        '実施_年月日',
        '全国地方公共団体コード',
        '都道府県名',
        '市区町村名',
        '検査実施_人数',
        '備考',
    ]]

    # 集計されてしまった部分をCSVから取得する
    old = pd.read_csv('./dist/csv/150002_niigata_covid19_test_people.csv')
    days = inspectors['実施_年月日']
    old = old[old['実施_年月日'].isin(days) == False]
    inspectors = pd.concat([old, inspectors])

    inspectors.to_csv('dist/csv/150002_niigata_covid19_test_people.csv', index=False)


# 陽性患者属性
def create_positive_patients():
    (city_table, ku_table) = get_city_code()
    positive_patient = get_patients()

    positive_patient['市区町村名'] = positive_patient['居住地']
    positive_patient['市区町村名'] = positive_patient['市区町村名'].str.replace('.*[(（]', '', regex=True)
    positive_patient['市区町村名'] = positive_patient['市区町村名'].str.replace('[)）]', '', regex=True)
    positive_patient['市区町村名'] = positive_patient['市区町村名'].str.replace('.*:', '', regex=True)

    positive_patient['市区町村名'] = positive_patient['市区町村名'].str.replace('保健所管内', '保健所')
    positive_patient['市区町村名'] = positive_patient['市区町村名'].str.replace('保健所', '市')
    positive_patient['市区町村名'] = positive_patient['市区町村名'].str.replace('新潟市内滞在中', '市内滞在中')
    positive_patient['市区町村名'] = positive_patient['市区町村名'].str.replace('市内滞在中', '新潟市滞在')
    positive_patient['市区町村名'] = positive_patient['市区町村名'].str.replace('滞在', '')

    positive_patient['市区町村名'] = positive_patient['市区町村名'].replace('新潟市中', '新潟市')
    positive_patient['市区町村名'] = positive_patient['市区町村名'].replace('上越市中', '上越市')

    positive_patient['市区町村名'] = positive_patient['市区町村名'].replace('北区', '新潟市北区')
    positive_patient['市区町村名'] = positive_patient['市区町村名'].replace('東区', '新潟市東区')
    positive_patient['市区町村名'] = positive_patient['市区町村名'].replace('中央区', '新潟市中央区')
    positive_patient['市区町村名'] = positive_patient['市区町村名'].replace('江南区', '新潟市江南区')
    positive_patient['市区町村名'] = positive_patient['市区町村名'].replace('秋葉区', '新潟市秋葉区')
    positive_patient['市区町村名'] = positive_patient['市区町村名'].replace('南区', '新潟市南区')
    positive_patient['市区町村名'] = positive_patient['市区町村名'].replace('西区', '新潟市西区')
    positive_patient['市区町村名'] = positive_patient['市区町村名'].replace('西蒲区', '新潟市西蒲区')

    positive_patient['市区町村名'] = positive_patient['市区町村名'].replace('聖篭町', '聖籠町')
    positive_patient['市区町村名'] = positive_patient['市区町村名'].replace('新潟市江新潟市南区', '新潟市江南区')

    positive_patient['市区町村名'] = positive_patient['市区町村名'].replace('北海道', '')
    positive_patient['市区町村名'] = positive_patient['市区町村名'].replace('埼玉県', '')
    positive_patient['市区町村名'] = positive_patient['市区町村名'].replace('東京都', '')
    positive_patient['市区町村名'] = positive_patient['市区町村名'].replace('非公表', '')

    positive_patient['city_name'] = positive_patient['市区町村名']
    positive_patient = pd.merge(positive_patient, city_table, on='city_name', how='left')
    positive_patient = pd.merge(positive_patient, ku_table, on='city_name', how='left')

    positive_patient['No'] = positive_patient['患者No.']
    positive_patient['都道府県名'] = '新潟県'
    positive_patient['公表_年月日'] = positive_patient['判明日']
    positive_patient['発症_年月日'] = ''
    positive_patient['患者_居住地'] = positive_patient['居住地']
    positive_patient['患者_年代'] = positive_patient['年代']
    positive_patient['患者_性別'] = positive_patient['性別']
    positive_patient['患者_職業'] = positive_patient['職業']
    positive_patient['患者_状態'] = ''
    positive_patient['患者_症状'] = ''
    positive_patient['患者_渡航歴の有無フラグ'] = ''
    positive_patient['患者_退院済フラグ'] = ''
    positive_patient['備考'] = ''

    positive_patient.loc[positive_patient['code_y'].isna(), '全国地方公共団体コード'] = positive_patient['code_x']
    positive_patient.loc[positive_patient['code_x'].isna(), '全国地方公共団体コード'] = positive_patient['code_y']
    positive_patient.loc[positive_patient['全国地方公共団体コード'].isna(), '全国地方公共団体コード'] = positive_patient['code_y']
    positive_patient.loc[positive_patient['全国地方公共団体コード'].isna(), '全国地方公共団体コード'] = '150002'

    positive_patient = positive_patient[[
        'No',
        '全国地方公共団体コード',
        '都道府県名',
        '市区町村名',
        '公表_年月日',
        '発症_年月日',
        '患者_居住地',
        '患者_年代',
        '患者_性別',
        '患者_職業',
        '患者_状態',
        '患者_症状',
        '患者_渡航歴の有無フラグ',
        '患者_退院済フラグ',
        '備考',
    ]]

    positive_patient.to_csv('dist/csv/150002_niigata_covid19_patients.csv', index=False)


# 検査実施件数
def create_inspections_performed():
    inspections_performed = get_tests()

    inspections_performed['実施_年月日'] = inspections_performed['結果判明日']
    inspections_performed['全国地方公共団体コード'] = '150002'
    inspections_performed['都道府県名'] = '新潟県'
    inspections_performed['市区町村名'] = ''
    inspections_performed['検査実施_件数'] = inspections_performed['検査件数'].astype(int)
    inspections_performed['備考'] = ''

    inspections_performed = inspections_performed[[
        '実施_年月日',
        '全国地方公共団体コード',
        '都道府県名',
        '市区町村名',
        '検査実施_件数',
        '備考',
    ]]

    # 集計されてしまった部分をCSVから取得する
    old = pd.read_csv('./dist/csv/150002_niigata_covid19_test_count.csv')
    days = inspections_performed['実施_年月日']
    old = old[old['実施_年月日'].isin(days) == False]
    inspections_performed = pd.concat([old, inspections_performed])

    inspections_performed.to_csv('dist/csv/150002_niigata_covid19_test_count.csv', index=False)


# 陰性確認数
def create_negative_confirmations():
    negative_confirmations = get_tests()

    negative_confirmations['完了_年月日'] = negative_confirmations['結果判明日']
    negative_confirmations['全国地方公共団体コード'] = '150002'
    negative_confirmations['都道府県名'] = '新潟県'
    negative_confirmations['市区町村名'] = ''
    negative_confirmations['陰性確認_件数'] = negative_confirmations['検査件数'] - negative_confirmations['うち陽性件数']
    negative_confirmations['陰性確認_件数'] = negative_confirmations['陰性確認_件数'].astype(int)
    negative_confirmations['備考'] = ''

    negative_confirmations = negative_confirmations[[
        '完了_年月日',
        '全国地方公共団体コード',
        '都道府県名',
        '市区町村名',
        '陰性確認_件数',
        '備考',
    ]]

    # 集計されてしまった部分をCSVから取得する
    old = pd.read_csv('./dist/csv/150002_niigata_covid19_confirm_negative.csv')
    days = negative_confirmations['完了_年月日']
    old = old[old['完了_年月日'].isin(days) == False]

    negative_confirmations = pd.concat([old, negative_confirmations])
    negative_confirmations.to_csv('dist/csv/150002_niigata_covid19_confirm_negative.csv', index=False)


# コールセンター相談件数
def create_call_center_consultations():
    call_center_consultations = get_call_centers()

    call_center_consultations['受付_年月日'] = call_center_consultations['日']
    call_center_consultations['全国地方公共団体コード'] = '150002'
    call_center_consultations['都道府県名'] = '新潟県'
    call_center_consultations['市区町村名'] = ''
    call_center_consultations['相談件数'] = call_center_consultations['相談対応件数'].astype(int)
    call_center_consultations['備考'] = call_center_consultations['備考']

    call_center_consultations = call_center_consultations[[
        '受付_年月日',
        '全国地方公共団体コード',
        '都道府県名',
        '市区町村名',
        '相談件数',
        '備考',
    ]]

    # 集計されてしまった部分をCSVから取得する
    old = pd.read_csv('./dist/csv/150002_niigata_covid19_call_center.csv')
    days = call_center_consultations['受付_年月日']
    old = old[old['受付_年月日'].isin(days) == False]

    call_center_consultations = pd.concat([old, call_center_consultations])
    call_center_consultations.to_csv('dist/csv/150002_niigata_covid19_call_center.csv', index=False)



def create_update_date():
    with open(latest_path) as file:
        soup = BeautifulSoup(file, 'html.parser')

    patients_text = soup.select_one('.detail_free h2').get_text()
    patients_match = re.match('県内における感染者の発生状況 （令和(\w+)年(\w+)月(\w+)日現在）', patients_text)
    (year, month, day) = patients_match.groups()
    year = str(int(to_half_width(year)) + 2018).zfill(2)
    month = to_half_width(month).zfill(2)
    day = to_half_width(day).zfill(2)
    patients_date = f"{year}-{month}-{day}T00:00:00.000Z"

    soudan_text = soup.select_one('p:contains("（1）新潟県新型コロナ受診・相談センター") + p').get_text()
    soudan_matches = re.match('.*令和(\w+)年(\w+)月(\w+)日公表分（(\w+)時.*', soudan_text)
    (year, month, day, hour) = soudan_matches.groups()
    year = str(int(to_half_width(year)) + 2018).zfill(2)
    month = to_half_width(month).zfill(2)
    day = to_half_width(day).zfill(2)
    hour = to_half_width(hour).zfill(2)
    soudan_date = f"{year}-{month}-{day}T{hour}:00:00.000Z"

    kensa_text = soup.select_one('p:contains("（2）検査件数") + p').get_text()
    kensa_matches = re.match('.*令和(\w+)年(\w+)月(\w+)日公表分（(\w+)時.*', kensa_text)
    (year, month, day, hour) = kensa_matches.groups()
    year = str(int(to_half_width(year)) + 2018).zfill(2)
    month = to_half_width(month).zfill(2)
    day = to_half_width(day).zfill(2)
    hour = to_half_width(hour).zfill(2)
    kensa_date = f"2021-{month}-{day}T{hour}:00:00.000Z"

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
            patients_date,
            kensa_date,
            kensa_date,
        ]
    })
    df.to_csv('./dist/csv/updated_at.csv', index=False)


def create_hospitalization():
    with open(index_path) as file:
        soup = BeautifulSoup(file, 'html.parser')

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


if __name__ == '__main__':
    main()
