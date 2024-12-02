# sony-script
ソニーの運用において使用するスクリプト群

# sony-lambda.sh
CloudWatchのLambdaのレイテンシー上位5個を取得するスクリプト。
月次レポート作成に使用する。

# x-ray.py
X-Rayのトレース分析を行うスクリプト。
非機能要件の3秒を超えるトレースを抽出する。

# lambda-error.py
Lambdaのエラー分析を行うスクリプト。
lambda/yyyyMM/****.csvを処理対象とする。
CloudWatchのダッシュボードからエラーが発生しているLambda関数のcsvをダウンロードして配置後、スクリプトを動かすと処理後のcsvが出力される。