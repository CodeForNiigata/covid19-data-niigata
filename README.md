get niigata covid19 data
====

![CI](https://github.com/CodeForNiigata/covid19-data-niigata/workflows/CI/badge.svg)

新潟県のWebサイトのコロナに関する情報からデータを生成するスクリプトです。

- 生成結果はdistに出力されています
    - csvには標準形式のcsvが出力されています
    - jsonには https://niigata.stopcovid19.jp 用のjsonが出力されます
- 毎日定期的に自動で更新しています

## Requirement

- Python
- Pipenv


## Install

```
$ pipenv install
```

## Usage

```
# 患者情報に更新がある場合は手動で更新する
$ vim dist/csv/150002_niigata_covid19_patients.csv

# 県のページからCSVとJSONを生成する
$ pipenv run main

# 県のページからデータを取得する
$ pipenv run dl

# 取得したデータから標準形式のCSVを生成する
$ pipenv run csv

# 標準形式のCSVからstopcovid19のjsonを生成する
$ pipenv run json
```

## Docker

docker-compose upでdistの中身を更新します。

```
$ docker-compose up
```

## Note

CIで毎日自動で実行して結果を更新しています。

CIが失敗したなどの理由でCIを手動で実行する場合は下記のコマンドを実行してください。

なお、<personal_token> には、"repo"の権限が付いたpersonal access tokenを指定してください。

```bash
$ curl -X POST -H "Authorization: token <personal_token>" \
    -H "Content-Type: application/json" \
    https://api.github.com/repos/CodeForNiigata/covid19-data-niigata/dispatches \
    --data '{"event_type":"manual_build"}'
```

