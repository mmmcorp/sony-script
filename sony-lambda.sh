#!/bin/bash

# 引数チェック
if [ "$#" -ne 2 ]; then
    echo "Usage: $0 <start-date> <end-date>"
    echo "Date format: yyyy-mm-dd"
    echo "Example: $0 2024-11-01 2024-11-05"
    exit 1
fi

# 引数から開始日と終了日を取得し、ISO 8601形式に変換
START_DATE=$1
END_DATE=$2
START_TIME="${START_DATE}T00:00:00Z"
END_TIME="${END_DATE}T23:59:59Z"

# 定数
NAMESPACE="AWS/Lambda"
METRIC_NAME="Duration"
PERIOD=3600  # データポイントの期間（秒単位）

# Lambda関数リストの取得
FUNCTION_NAMES=$(aws cloudwatch list-metrics --profile sony --namespace $NAMESPACE --metric-name $METRIC_NAME --query 'Metrics[*].{FunctionName:Dimensions[?Name==`FunctionName`].Value | [0]}' --output text)

# GetMetricData用のクエリを作成
QUERY=""
INDEX=0
for FUNCTION_NAME in $FUNCTION_NAMES; do
    QUERY+="{
        \"Id\": \"metric${INDEX}\",
        \"MetricStat\": {
            \"Metric\": {
                \"Namespace\": \"$NAMESPACE\",
                \"MetricName\": \"$METRIC_NAME\",
                \"Dimensions\": [{\"Name\": \"FunctionName\", \"Value\": \"$FUNCTION_NAME\"}]
            },
            \"Period\": $PERIOD,
            \"Stat\": \"Average\"
        },
        \"ReturnData\": true
    },"
    INDEX=$((INDEX + 1))
done

# クエリから最後のカンマを削除
QUERY="[${QUERY%,}]"

# メトリクスデータの取得
METRIC_DATA=$(aws cloudwatch get-metric-data \
    --profile sony \
    --start-time "$START_TIME" \
    --end-time "$END_TIME" \
    --metric-data-queries "$QUERY" \
    --query 'MetricDataResults[*].{Id:Id,Values:Values,Label:Label}' \
    --output json)

# 最大値を抽出し、重複を除外して並び替え
echo "$METRIC_DATA" | jq -r '.[] | select(.Values != null) | [(.Values | max), .Label] | @tsv' | sort -nr | awk '!seen[$2]++' | head -n 5

echo "Processing completed."
