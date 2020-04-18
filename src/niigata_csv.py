import numpy as np
import pandas as pd
import tabula


def main():
    (city_table, ku_table) = get_city_code()

    create_positive_patients(city_table, ku_table)
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
    houkoku_pdf = tabula.read_pdf('./dist/pdf/150002_niigata_covid19_patients.pdf', lattice=True, pages='all')
    patients = houkoku_pdf[0]
    patients.columns = ['患者No.', '_', '判明日', '年代', '性別', '居住地', '職業']

    patients['判明日'] = '2020年' + patients['判明日']
    patients['判明日'] = pd.to_datetime(patients['判明日'], format='%Y年%m月%d日')
    patients['判明日'] = patients['判明日'].dt.strftime('%Y-%m-%d')

    patients['年代'] = patients['年代'].str.replace('\(乳幼児\)', '')

    patients['居住地'] = patients['居住地'].str.replace('\r', '', regex=True)
    patients['居住地'] = patients['居住地'].str.replace('調査中', '新潟市')
    patients['居住地'] = patients['居住地'].str.replace('東京都\(', '')
    patients['居住地'] = patients['居住地'].str.replace('\)', '')

    patients['職業'] = patients['職業'].str.replace('\r', '', regex=True)
    patients['職業'] = patients['職業'].str.replace('―', '')

    return patients


def get_tests():
    kensa_pdf = tabula.read_pdf('./dist/pdf/150002_niigata_covid19_test.pdf', lattice=True, pages='all')
    tests = kensa_pdf[0]

    tests = tests[tests['結果判明日'] != '計']

    tests['結果判明日'] = tests['結果判明日'].str.replace('令和2年', '2月29日')
    tests['結果判明日'] = '2020年' + tests['結果判明日']
    tests['結果判明日'] = pd.to_datetime(tests['結果判明日'], format='%Y年%m月%d日')
    tests['結果判明日'] = tests['結果判明日'].dt.strftime('%Y-%m-%d')

    tests['曜日'] = tests['曜日'].str.replace('2月', '土')

    tests['うち陽性件数'] = tests['うち陽性件数'].fillna(0)

    return tests


def get_call_centers():
    soudan_pdf = tabula.read_pdf('./dist/pdf/150002_niigata_covid19_call_center.pdf', lattice=True, pages='all')
    call_centers = soudan_pdf[0]

    call_centers.columns = ['日', '曜日', '相談対応件数', '帰国者・接触者外来を紹介した人数', '備考', '_']

    call_centers.iat[0, 0] = call_centers.iat[0, 1]
    call_centers.iat[0, 1] = call_centers.iat[0, 2]
    call_centers.iat[0, 2] = call_centers.iat[0, 3]
    call_centers.iat[0, 3] = call_centers.iat[0, 4]
    call_centers.iat[0, 4] = call_centers.iat[0, 5]
    call_centers.iat[0, 5] = None

    call_centers = call_centers[call_centers['日'] != '計']

    call_centers['日'] = '2020年' + call_centers['日']
    call_centers['日'] = pd.to_datetime(call_centers['日'], format='%Y年%m月%d日')
    call_centers['日'] = call_centers['日'].dt.strftime('%Y-%m-%d')

    return call_centers


# 陽性患者属性
def create_positive_patients(city_table, ku_table):
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
    inspectors.to_csv('dist/csv/150002_niigata_covid19_test_people.csv', index=False)


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
    inspections_performed.to_csv('dist/csv/150002_niigata_covid19_test_count.csv', index=False)


# 陰性確認数
# negative_confirmations
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
    call_center_consultations.to_csv('dist/csv/150002_niigata_covid19_call_center.csv', index=False)


if __name__ == '__main__':
    main()
