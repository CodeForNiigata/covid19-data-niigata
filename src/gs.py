import datetime
import pandas as pd
import requests
import simplejson as json

base_url = 'https://docs.google.com/spreadsheets/d/1daadRce3i3gyz6ufTN1xwz3N52McVt99FwtppYWuc7o'

contacts_url = f"{base_url}/export?format=csv&gid=0"
querents_url = f"{base_url}/export?format=csv&gid=1956045137"
patients_url = f"{base_url}/export?format=csv&gid=423471974"
patients_summary_url = f"{base_url}/export?format=csv&gid=1940153659"
discharges_summary_url = f"{base_url}/export?format=csv&gid=1730758426"
inspections_url = f"{base_url}/export?format=csv&gid=940251992"
inspections_summary_url = f"{base_url}/export?format=csv&gid=916719826"
main_summary_url = f"{base_url}/export?format=csv&gid=2018159084"

contacts_table = pd.read_csv(contacts_url)
querents_table = pd.read_csv(querents_url)
patients_table = pd.read_csv(patients_url)
patients_summary_table = pd.read_csv(patients_summary_url)
discharges_summary_table = pd.read_csv(discharges_summary_url)
inspections_table = pd.read_csv(inspections_url)
inspections_summary_table = pd.read_csv(inspections_summary_url)
main_summary_table = pd.read_csv(main_summary_url)

_contacts = contacts_table[querents_table['日付'].isna() == False]
contacts = _contacts.to_dict(orient='records')

_querents = querents_table[querents_table['日付'].isna() == False]
_querents['9-17時'] = _querents['9-17時'].astype(int)
querents = _querents.to_dict(orient='records')

_patients = patients_table
patients = _patients.to_dict(orient='records')

_patients_summary = patients_summary_table[patients_summary_table['日付'].isna() == False]
patients_summary = _patients_summary.to_dict(orient='records')

_discharges_summary = discharges_summary_table[discharges_summary_table['日付'].isna() == False]
discharges_summary = _discharges_summary.to_dict(orient='records')

_inspections = inspections_table[inspections_table['判明日'].isna() == False]
_inspections['検査検体数'] = _inspections['検査検体数'].astype(int)
_inspections['疑い例検査'] = _inspections['疑い例検査'].astype(int)
_inspections['接触者調査'] = _inspections['接触者調査'].astype(int)
_inspections['陰性確認'] = _inspections['陰性確認'].astype(int)
_inspections['（小計①）'] = _inspections['（小計①）'].astype(int)
_inspections['チャーター便'] = _inspections['チャーター便'].astype(int)
_inspections['クルーズ船'] = _inspections['クルーズ船'].astype(int)
_inspections['陰性確認2'] = _inspections['陰性確認2'].astype(int)
_inspections['（小計②）'] = _inspections['（小計②）'].astype(int)
inspections = _inspections.to_dict(orient='records')

_inspections_summary = inspections_summary_table[inspections_summary_table['labels'].isna() == False]
_inspections_summary['都内'] = _inspections_summary['都内'].astype(int)
_inspections_summary['その他'] = _inspections_summary['その他'].astype(int)
_inspections_summary_label = _inspections_summary[['labels']]
_inspections_summary_data = _inspections_summary[['都内', 'その他']]
inspections_summary_label = _inspections_summary_label.values.squeeze().tolist()
inspections_summary_data = _inspections_summary_data.to_dict(orient='list')

_main_summary = main_summary_table
main_summaries = _main_summary.to_dict(orient='records')
main_summary = main_summaries[0]

now = datetime.datetime.now()
date = now.strftime("%Y/%m/%d %H:%M")  # TODO ダミー、あとでなおす
last_update = now.strftime("%Y/%m/%d %H:%M")

data = {
    'contacts': {
        'date': date,
        'data': contacts
    },
    'querents': {
        'date': date,
        'data': querents
    },
    'patients': {
        'date': date,
        'data': patients
    },
    'patients_summary': {
        'date': date,
        'data': patients_summary
    },
    'discharges_summary': {
        'date': date,
        'data': discharges_summary
    },
    'inspections': {
        'date': date,
        'data': inspections
    },
    'inspections_summary': {
        'date': date,
        'labels': inspections_summary_label,
        'data': inspections_summary_data
    },
    'lastUpdate': last_update,
    'main_summary': {
        'attr': '検査実施人数',
        'value': main_summary['検査実施人数'],
        'children': [
            {
                'attr': '陽性患者数',
                'value': main_summary['陽性患者数'],
                'children': [
                    {
                        'attr': '入院中',
                        'value': main_summary['入院中'],
                        'children': [
                            {
                                'attr': '軽症・中等症',
                                'value': main_summary['軽症・中等症']
                            },
                            {
                                'attr': '重症',
                                'value': main_summary['重症']
                            }
                        ]
                    },
                    {
                        'attr': '退院',
                        'value': main_summary['退院']
                    },
                    {
                        'attr': '死亡',
                        'value': main_summary['死亡']
                    }
                ]
            }
        ]
    }
}

with open('data.json', 'w') as f:
    json.dump(data, f, indent=4, ensure_ascii=False, ignore_nan=True)
