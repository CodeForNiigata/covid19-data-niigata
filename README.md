get niigata covid19 data
====

新潟県のWebサイトのコロナに関する情報のPDFをよしなにしていい感じのデータを取得するスクリプトです。

## Requirement

- Python
- Pipenv
- Java 13

## Usage

```
# 全てのデータを県のサイトから取ってくる
$ pipenv run main scrape all
# 患者数だけ県のサイトから取ってくる
$ pipenv run main scrape patients
# 検査数だけ県のサイトから取ってくる
$ pipenv run main scrape inspections
# 相談数だけ県のサイトから取ってくる
$ pipenv run main scrape querents

# Google SpreadSheetからdata.jsonを生成する
$ pipenv run main convert
```

## Install

```
$ pipenv install
```
