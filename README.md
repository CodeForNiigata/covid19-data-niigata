get niigata covid19 data
====

新潟県のWebサイトのコロナに関する情報からデータを生成するスクリプトです。

- 生成結果はdistに出力されています
    - csvには標準形式のcsvが出力されています
    - jsonには https://niigata.stopcovid19.jp 用のjsonが出力されます
- 毎日定期的に自動で更新しています

## Requirement

- Python
- Pipenv
- Java 13

## Usage

```
# 県のページからCSVとJSONを生成する
$ pipenv run main

# 県のページからデータを取得する
$ pipenv run pdf
# 取得したデータから標準形式のCSVを生成する
$ pipenv run csv
# 標準形式のCSVからstopcovid19のjsonを生成する
$ pipenv run json
```

## Install

```
$ pipenv install
```
