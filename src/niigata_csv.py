from bs4 import BeautifulSoup
import numpy as np
import pandas as pd
import requests
import tabula

base_url = 'https://www.pref.niigata.lg.jp'

def main():
    create_positive_patients()
    create_inspectors()
    create_inspections_performed()
    create_negative_confirmations()
    create_call_center_consultations()


def get_city_code():
    city_code_pdf = tabula.read_pdf('./dist/pdf/city_code.pdf', pages='all', pandas_options={'header': None})
    [city_tables, ku_tables] = np.split(city_code_pdf, [31])
    city_table = pd.concat(city_tables)
    city_table = city_table.drop(0)
    city_table.columns = ['code', 'pref_name', 'city_name', 'pref_kana', 'city_kana']
    ku_table = pd.concat(ku_tables)
    ku_table.columns = ['code', 'city_name', 'city_kana']
    return city_table, ku_table


def get_patients():
    page_url = base_url + '/site/shingata-corona/256362836.html'
    page = requests.get(page_url)
    soup = BeautifulSoup(page.content, 'html.parser')
    rows = soup.select('table[summary="県内における感染者の発生状況"] tbody tr')

    records = []
    for i, row in enumerate(rows):
        cols = row.select('td')
        record = [col.getText() for col in cols[2:7]]
        record.insert(0, cols[0].getText())
        records.append(record)

    columns = ['患者No.', '判明日', '年代', '性別', '居住地', '職業']
    patients = pd.DataFrame(records, columns=columns)

    # 改行の除去
    patients['患者No.'] = patients['患者No.'].str.replace('\n', '', regex=True)
    patients['判明日'] = patients['判明日'].str.replace('\n', '', regex=True)
    patients['年代'] = patients['年代'].str.replace('\n', '', regex=True)
    patients['居住地'] = patients['居住地'].str.replace('\n', '', regex=True)
    patients['職業'] = patients['職業'].str.replace('\n', '', regex=True)

    # カッコの中身を消す
    patients['判明日'] = patients['判明日'].str.replace('[\(（].*[\)）]', '', regex=True)
    patients['年代'] = patients['年代'].str.replace('[\(（].*[\)）]', '', regex=True)

    # カッコの外側を消す
    patients['居住地'] = patients['居住地'].str.replace('.*[\(（]', '', regex=True)
    patients['居住地'] = patients['居住地'].str.replace('[\)）].*', '')

    # データなしを表現する文字の除去
    patients['年代'] = patients['年代'].str.replace('[-―－]', '', regex=True)
    patients['性別'] = patients['性別'].str.replace('[-―－]', '', regex=True)
    patients['職業'] = patients['職業'].str.replace('[-―－]', '', regex=True)

    # 型変換
    patients['患者No.'] = patients['患者No.'].astype(int)
    patients['判明日'] = '2020年' + patients['判明日']
    patients['判明日'] = pd.to_datetime(patients['判明日'], format='%Y年%m月%d日')
    patients['判明日'] = patients['判明日'].dt.strftime('%Y-%m-%d')

    patients = patients.sort_values('患者No.')
    return patients


def get_tests():
    kensa_pdf = tabula.read_pdf('./dist/pdf/150002_niigata_covid19_test.pdf', pages='all')
    tests = kensa_pdf[0]

    try:
        tests.columns = ['結果判明日', '曜日', '検査件数', 'うち陽性件数']
    except ValueError:
        tests.drop(tests.filter(regex="Unnamed.+[01]"),axis=1, inplace=True)
        tests.columns = ['結果判明日', '曜日', '検査件数', 'うち陽性件数']

    # いらないデータの除去
    tests = tests[tests['結果判明日'] != '令和2年']  # 2月のデータ
    tests = tests[tests['結果判明日'] != '2月']  # 2月のデータ
    tests = tests[tests['結果判明日'] != '3月']
    tests = tests[tests['結果判明日'] != '4月']
    tests = tests[tests['結果判明日'] != '5月']
    tests = tests[tests['結果判明日'] != '6月']
    tests = tests[tests['結果判明日'] != '7月']
    tests = tests[tests['結果判明日'] != '8月']
    tests = tests[tests['結果判明日'] != '9月']
    tests = tests[tests['結果判明日'] != '10月']
    tests = tests[tests['結果判明日'] != '11月']
    tests = tests[tests['結果判明日'] != '12月']
    tests = tests[tests['結果判明日'] != '計']

    # 型をいい感じに
    tests['結果判明日'] = '2020年' + tests['結果判明日']
    tests['結果判明日'] = pd.to_datetime(tests['結果判明日'], format='%Y年%m月%d日')
    tests['結果判明日'] = tests['結果判明日'].dt.strftime('%Y-%m-%d')

    tests['検査件数'] = tests['検査件数'].str.replace('\(\d+\)', '', regex=True)
    tests['検査件数'] = tests['検査件数'].astype(int)

    tests['うち陽性件数'] = tests['うち陽性件数'].fillna(0)
    tests['うち陽性件数'] = tests['うち陽性件数'].astype(int)

    return tests


def get_call_centers():
    soudan_pdf = tabula.read_pdf('./dist/pdf/150002_niigata_covid19_call_center.pdf', lattice=True, pages='all')
    call_centers = pd.concat(soudan_pdf)
    call_centers.columns = ['日', '曜日', '相談対応件数', '帰国者・接触者外来を紹介した人数', '備考']
    call_centers = call_centers[call_centers['日'].str.endswith('年') == False]
    call_centers = call_centers[call_centers['日'].str.endswith('月') == False]
    call_centers = call_centers[call_centers['日'].str.endswith('計') == False]

    # 年号がある列のズレを補正する
    call_centers['_年号'] = call_centers['日'] == '令和2年'
    call_centers['日'][call_centers['_年号']] = call_centers['曜日']
    call_centers['曜日'][call_centers['_年号']] = call_centers['相談対応件数']
    call_centers['相談対応件数'][call_centers['_年号']] = call_centers['帰国者・接触者外来を紹介した人数']
    call_centers['帰国者・接触者外来を紹介した人数'][call_centers['_年号']] = call_centers['備考']

    # 型をいい感じに
    call_centers['日'] = '2020年' + call_centers['日']
    call_centers['日'] = pd.to_datetime(call_centers['日'], format='%Y年%m月%d日')
    call_centers['日'] = call_centers['日'].dt.strftime('%Y-%m-%d')

    call_centers['相談対応件数'] = call_centers['相談対応件数'].astype(int)

    call_centers['帰国者・接触者外来を紹介した人数'] = call_centers['帰国者・接触者外来を紹介した人数'].astype(int)

    call_centers = call_centers[['日', '曜日', '相談対応件数', '帰国者・接触者外来を紹介した人数', '備考']]

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

    positive_patient['city_name'] = positive_patient['居住地']
    positive_patient = pd.merge(positive_patient, city_table, on='city_name', how='left')
    positive_patient = pd.merge(positive_patient, ku_table, on='city_name', how='left')

    serial_num = pd.RangeIndex(start=1, stop=len(positive_patient.index) + 1, step=1)
    positive_patient['No'] = serial_num
    positive_patient.loc[positive_patient['code_y'].isna(), '全国地方公共団体コード'] = positive_patient['code_x']
    positive_patient.loc[positive_patient['code_x'].isna(), '全国地方公共団体コード'] = positive_patient['code_y']
    positive_patient.loc[positive_patient['全国地方公共団体コード'].isna(), '全国地方公共団体コード'] = positive_patient['code_y']
    positive_patient['都道府県名'] = '新潟県'
    positive_patient['市区町村名'] = positive_patient['居住地']
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


if __name__ == '__main__':
    main()
