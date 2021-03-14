import numpy as np
import pandas as pd

def main():
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

  tests = tests[tests['検査実施曜日'].isna() == True]
  tests['検査実施日'] = tests['検査実施日'].str.replace('R2.', '2020-')
  tests['検査実施日'] = tests['検査実施日'].str.replace('R3.', '2021-')
  tests['検査実施日'] = tests['検査実施日'].str.replace('月', '')
  tests['検査実施日'] = tests['検査実施日'] + '-1'
  tests['検査実施日'] = pd.to_datetime(tests['検査実施日'])
  tests.set_index('検査実施日', inplace=True)
  sum_tests = tests.resample('M').sum()
  sum_tests = sum_tests[['PCR検査_検査件数']]

  data = pd.read_csv('./dist/csv/150002_niigata_covid19_test_count.csv', index_col=0, parse_dates=True)
  data.index.rename('実施_年月日', inplace=True)
  sum_data = data.resample('M').sum()
  sum_data = sum_data[['検査実施_件数']]

  merged = sum_data.join(sum_tests, lsuffix='_l', rsuffix='_r')
  merged['diff'] = merged['PCR検査_検査件数'] - merged['検査実施_件数']
  merged['days'] = merged.index.day
  merged['per_day'] = merged['diff'] / merged['days']
  merged['per_day'] = merged['per_day'].apply(np.floor)
  merged['overly'] = merged['diff'] - merged['per_day'] * merged['days']

  negative_counts = pd.read_csv('./dist/csv/150002_niigata_covid19_confirm_negative.csv', index_col=0, parse_dates=True)
  test_counts = pd.read_csv('./dist/csv/150002_niigata_covid19_test_count.csv', index_col=0, parse_dates=True)

  for index, row in negative_counts.iterrows():
    target = merged[(merged.index.year == index.year) & (merged.index.month == index.month)]
    per_day = 0 if np.isnan(target['per_day'][0]) else target['per_day'][0]
    overly = 0 if np.isnan(target['overly'][0]) else target['overly'][0]
    overly = 0 if index.day > overly else 1
    negative_counts.at[index, '陰性確認_件数'] += per_day + overly

  for index, row in test_counts.iterrows():
    target = merged[(merged.index.year == index.year) & (merged.index.month == index.month)]
    per_day = 0 if np.isnan(target['per_day'][0]) else target['per_day'][0]
    overly = 0 if np.isnan(target['overly'][0]) else target['overly'][0]
    overly = 0 if index.day > overly else 1
    test_counts.at[index, '検査実施_件数'] += per_day + overly

  negative_counts.to_csv('./dist/csv/150002_niigata_covid19_confirm_negative.csv')
  test_counts.to_csv('./dist/csv/150002_niigata_covid19_test_count.csv')

if __name__ == '__main__':
  main()
