import datetime as dt
import locale
import pandas as pd
import simplejson as json

# DATE FORMAT
FULL_DATETIME = '%Y-%m-%dT%H:%M:%S.000Z'
DATETIME = '%Y/%m/%d %H:%M'
DATE = '%Y-%m-%d'
SHORT_DATE = '%m/%d'
SHORT_DATE_NO_ZERO_PADDING = '%-m/%-d'
NUMBER_OF_A_WEEK = '%w'


def main():
    create_json()


def create_json():
    updated_at = pd.read_csv('./dist/csv/updated_at.csv')
    updated_at = updated_at.set_index('name')

    updated_at['updated_at'] = pd.to_datetime(updated_at['updated_at'], format=FULL_DATETIME)
    updated_at['updated_at'] = updated_at['updated_at'].dt.strftime(DATETIME)

    patients_last_date = updated_at.at['patients', 'updated_at']
    test_last_date = updated_at.at['test_count', 'updated_at']
    call_center_last_date = updated_at.at['call_center', 'updated_at']


    data = {
        'contacts': {
            'date': None,
            'data': [],
        },
        'querents': {
            'date': call_center_last_date,
            'data': get_querents(),
        },
        'patients': {
            'date': patients_last_date,
            'data': get_patients(),
        },
        'patients_summary': {
            'date': patients_last_date,
            'data': get_patients_summary(),
        },
        'discharges_summary': {
            'date': None,
            'data': [],
        },
        'inspections': {
            'date': test_last_date,
            'data': get_inspections(),
        },
        'inspections_summary': {
            'date': test_last_date,
            'data': get_inspections_summary(),
        },
        'lastUpdate': test_last_date,
        'main_summary': get_main_summary(),
    }

    with open('dist/json/data.json', 'w') as f:
        json.dump(data, f, indent=4, ensure_ascii=False, ignore_nan=True)


def get_querents():
    call_center = pd.read_csv('./dist/csv/150002_niigata_covid19_call_center.csv')

    call_center['_date'] = pd.to_datetime(call_center['受付_年月日'], format=DATE)
    call_center['_count'] = call_center['相談件数']

    call_center['日付'] = call_center['_date'].dt.strftime(FULL_DATETIME)
    call_center['9-17時'] = call_center['_count']
    call_center['17-翌9時'] = 0
    call_center['date'] = call_center['_date'].dt.strftime(DATE)
    call_center['w'] = call_center['_date'].dt.strftime(NUMBER_OF_A_WEEK).astype(int)
    call_center['short_date'] = call_center['_date'].dt.strftime(SHORT_DATE)
    call_center['小計'] = call_center['_count']

    day_of_a_weeks = get_day_of_a_weeks()
    call_center = call_center.join(day_of_a_weeks, on='w', rsuffix='_week')
    call_center['曜日'] = call_center['_day_of_a_week']

    call_center = call_center[[
        '日付',
        '曜日',
        '9-17時',
        '17-翌9時',
        'date',
        'w',
        'short_date',
        '小計',
    ]]

    return call_center.to_dict(orient='records')


def get_patients():
    patients = pd.read_csv('./dist/csv/150002_niigata_covid19_patients.csv')

    patients['_date'] = pd.to_datetime(patients['公表_年月日'], format=DATE)

    patients['リリース日'] = patients['_date'].dt.strftime(FULL_DATETIME)
    patients['居住地'] = patients['患者_居住地']
    patients['年代'] = patients['患者_年代']
    patients['性別'] = patients['患者_性別']
    patients['退院'] = None
    patients['date'] = patients['_date'].dt.strftime(DATE)

    patients['w'] = patients['_date'].dt.strftime(NUMBER_OF_A_WEEK).astype(int)
    day_of_a_weeks = get_day_of_a_weeks()
    patients = patients.join(day_of_a_weeks, on='w', rsuffix='_week')
    patients['曜日'] = patients['_day_of_a_week']

    patients = patients[[
        'リリース日',
        '曜日',
        '居住地',
        '年代',
        '性別',
        '退院',
        'date',
    ]]

    return patients.to_dict(orient='records')


def get_patients_summary():
    patients = pd.read_csv('./dist/csv/150002_niigata_covid19_patients.csv')
    updated_at = pd.read_csv('./dist/csv/updated_at.csv')
    updated_at = updated_at.set_index('name')

    print(updated_at)
    last_date = updated_at.at['patients', 'updated_at']
    last_date = dt.datetime.strptime(last_date, '%Y-%m-%dT%H:%M:%S.000Z')
    last_date = dt.date(last_date.year, last_date.month, last_date.day)

    patients['_date'] = pd.to_datetime(patients['公表_年月日'], format=DATE)
    first_date = patients['_date'].min()

    patients_counts = patients.groupby('_date').count().reset_index()
    patients_counts['_count'] = patients_counts['No']
    patients_counts = patients_counts[['_date', '_count']]
    patients_counts = patients_counts.set_index('_date')

    range = pd.date_range(first_date, last_date)
    df = pd.DataFrame(index=range)
    patients_summary = pd.merge(patients_counts, df, left_index=True, right_index=True, how='outer')

    patients_summary['_count'] = patients_summary['_count'].fillna(0)
    patients_summary['_count'] = patients_summary['_count'].astype(int)
    patients_summary = patients_summary.reset_index()
    patients_summary['日付'] = patients_summary['index']
    patients_summary['日付'] = patients_summary['日付'].dt.strftime('%Y-%m-%dT00:00:00.000Z')
    patients_summary['小計'] = patients_summary['_count']
    patients_summary = patients_summary[['日付', '小計']]

    return patients_summary.to_dict(orient='records')


def get_inspections():
    test_count = pd.read_csv('./dist/csv/150002_niigata_covid19_test_count.csv')
    confirm_negative = pd.read_csv('./dist/csv/150002_niigata_covid19_confirm_negative.csv')

    test_count['_date'] = test_count['実施_年月日']
    test_count['_test_count'] = test_count['検査実施_件数']
    test_count = test_count[['_date', '_test_count']]

    confirm_negative['_date'] = confirm_negative['完了_年月日']
    confirm_negative['_negative_count'] = confirm_negative['陰性確認_件数']
    confirm_negative = confirm_negative[['_date', '_negative_count']]

    inspections = pd.merge(test_count, confirm_negative, on='_date')
    inspections['_date'] = pd.to_datetime(inspections['_date'], format=DATE)

    inspections['判明日'] = inspections['_date'].dt.strftime(DATE)
    inspections['検査検体数'] = inspections['_test_count']
    inspections['疑い例検査'] = 0
    inspections['接触者調査'] = 0
    inspections['陰性確認'] = inspections['_negative_count']
    inspections['（小計①）'] = inspections['_negative_count']
    inspections['チャーター便'] = 0
    inspections['クルーズ船'] = 0
    inspections['陰性確認2'] = 0
    inspections['（小計②）'] = 0

    inspections = inspections[[
        '判明日',
        '検査検体数',
        '疑い例検査',
        '接触者調査',
        '陰性確認',
        '（小計①）',
        'チャーター便',
        'クルーズ船',
        '陰性確認2',
        '（小計②）',
    ]]

    return inspections.to_dict(orient='records')


def get_inspections_summary():
    test_count = pd.read_csv('./dist/csv/150002_niigata_covid19_test_count.csv')

    test_count['日付'] = test_count['実施_年月日']
    test_count['日付'] = pd.to_datetime(test_count['日付'], format=DATE)
    test_count['日付'] = test_count['日付'].dt.strftime(FULL_DATETIME)
    test_count['小計'] = test_count['検査実施_件数']

    test_count = test_count[['日付', '小計']]

    return test_count.to_dict(orient='records')


def get_main_summary():
    test_count = pd.read_csv('./dist/csv/150002_niigata_covid19_test_count.csv')
    confirm_negative = pd.read_csv('./dist/csv/150002_niigata_covid19_confirm_negative.csv')
    hospitalization = pd.read_csv('./dist/csv/hospitalization.csv')
    hospitalization = hospitalization.set_index('type')
    test_count['_date'] = test_count['実施_年月日']
    test_count['_test_count'] = test_count['検査実施_件数']
    test_count = test_count[['_date', '_test_count']]

    confirm_negative['_date'] = confirm_negative['完了_年月日']
    confirm_negative['_negative_count'] = confirm_negative['陰性確認_件数']
    confirm_negative = confirm_negative[['_date', '_negative_count']]

    inspections = pd.merge(test_count, confirm_negative, on='_date')
    inspections['_date'] = pd.to_datetime(inspections['_date'], format=DATE)

    # TODO 新潟に存在しないデータも計算すべき
    return {
        'attr': '検査実施人数',
        'value': int(inspections['_test_count'].sum()),
        'children': [
            {
                'attr': '陽性患者数',
                'value': int(inspections['_test_count'].sum() - inspections['_negative_count'].sum()),
                'children': [
                    {
                        'attr': '入院中',
                        'value': int(hospitalization.loc['hospitalization']['count']),
                        'children': [
                            {
                                'attr': '軽症・中等症',
                                'value': None
                            },
                            {
                                'attr': '重症',
                                'value': None
                            }
                        ]
                    },
                    {
                        'attr': '退院',
                        'value': int(hospitalization.loc['discharge']['count'])
                    },
                    {
                        'attr': '死亡',
                        'value': None
                    }
                ]
            }
        ]
    }


def get_day_of_a_weeks():
    return pd.DataFrame({
        'w': [0, 1, 2, 3, 4, 5, 6],
        '_day_of_a_week': ['日', '月', '火', '水', '木', '金', '土'],
    })


if __name__ == '__main__':
    main()
