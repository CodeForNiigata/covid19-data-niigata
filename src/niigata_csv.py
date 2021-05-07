from bs4 import BeautifulSoup
import numpy as np
import pandas as pd
import requests

base_url = 'https://www.pref.niigata.lg.jp'

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


def get_city_code():
    city_table = pd.read_excel('./dist/xlsx/city_code.xls', sheet_name='R1.5.1現在の団体')
    city_table = city_table.rename(columns={
        '団体コード': 'code',
        '都道府県名\n（漢字）': 'pref_name',
        '市区町村名\n（漢字）': 'city_name',
        '都道府県名\n（カナ）': 'pref_kana',
        '市区町村名\n（カナ）': 'city_kana',
    })
    city_table['code'] = city_table['code'].astype(str)

    ku_table = pd.read_excel('./dist/xlsx/city_code.xls', sheet_name='H30.10.1政令指定都市', header=None)
    ku_table.columns = ['code', 'city_name', 'city_kana']
    ku_table['code'] = ku_table['code'].astype(str)

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
    patients['性別'] = patients['性別'].str.replace('\n', '', regex=True)
    patients['居住地'] = patients['居住地'].str.replace('\n', '', regex=True)
    patients['職業'] = patients['職業'].str.replace('\n', '', regex=True)

    # 欠番を除去
    patients = patients[patients['判明日'] != '-']
    patients = patients[patients['判明日'] != '－']

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

    # 曜日を除去する
    patients['判明日'] = patients['判明日'].str.replace('（.*曜日', '', regex=True)
    patients['判明日'] = patients['判明日'].str.replace('）', '', regex=True)
    patients['判明日'] = patients['判明日'].str.replace('(.*曜日)', '', regex=True)
    patients['判明日'] = patients['判明日'].str.replace(')', '', regex=True)

    # 全角数字を半角数字にする
    patients['判明日'] = patients['判明日'].str.translate(digits_zenkaku_table)

    # 表記ミスの補正
    patients['判明日'] = patients['判明日'].str.replace('5日4日', '5月4日', regex=True)

    # 型変換
    patients['患者No.'] = patients['患者No.'].astype(int)
    patients.loc[patients['患者No.'] < 548, '判明日'] = '2020年' + patients['判明日']
    patients.loc[patients['患者No.'] >= 548, '判明日'] = '2021年' + patients['判明日']
    patients['判明日'] = pd.to_datetime(patients['判明日'], format='%Y年%m月%d日')
    patients['判明日'] = patients['判明日'].dt.strftime('%Y-%m-%d')

    patients = patients.sort_values('患者No.')
    patients['患者No.'] = patients['患者No.'].astype(str)

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

    positive_patient['city_name'] = positive_patient['居住地']
    positive_patient = pd.merge(positive_patient, city_table, on='city_name', how='left')
    positive_patient = pd.merge(positive_patient, ku_table, on='city_name', how='left')

    positive_patient['No'] = positive_patient['患者No.']
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

    path = './dist/xlsx/150002_niigata_covid19_patients_2000.xlsx'
    dtype = {
        'No': 'object',
        '全国地方公共団体コード': 'object',
        '公表_年月日': 'object',
    }
    past_patient_2000 = pd.read_excel(path, dtype=dtype)
    past_patient_2000 = past_patient_2000[past_patient_2000['No'].isna() == False]
    merged = pd.concat([past_patient_2000, positive_patient])
    merged['No'] = merged['No'].astype(int)
    merged = merged.sort_values('No')
    merged['No'] = merged['No'].astype(str)

    merged.to_csv('dist/csv/150002_niigata_covid19_patients.csv', index=False)


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
