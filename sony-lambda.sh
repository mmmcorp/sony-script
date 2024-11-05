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

# ISO 8601形式に変換（時間はデフォルトで00:00:00Zと23:59:59Zを設定）
START_TIME="${START_DATE}T00:00:00Z"
END_TIME="${END_DATE}T23:59:59Z"

# 定数
NAMESPACE="AWS/Lambda"
METRIC_NAME="Duration"
PERIOD=3600  # データポイントの期間（秒単位）

# CloudWatchメトリクスを取得して並び替え
aws cloudwatch list-metrics --profile sony --namespace $NAMESPACE --metric-name $METRIC_NAME --query 'Metrics[*].{FunctionName:Dimensions[?Name==`FunctionName`].Value | [0]}' --output text | while read -r FUNCTION_NAME; do
    # メトリクス統計情報の取得
    AVG_DURATION=$(aws cloudwatch get-metric-statistics --profile sony --namespace $NAMESPACE \
        --metric-name $METRIC_NAME \
        --dimensions Name=FunctionName,Value="$FUNCTION_NAME" \
        --start-time "$START_TIME" \
        --end-time "$END_TIME" \
        --period $PERIOD \
        --statistics Average \
        --query 'Datapoints[*].Average' \
        --output text)

    # 平均レイテンシーの最大値を取得
    if [ ! -z "$AVG_DURATION" ]; then
        MAX_AVG=$(echo "$AVG_DURATION" | tr '\t' '\n' | sort -nr | head -n 1)
        echo "$MAX_AVG $FUNCTION_NAME"
    fi
done | sort -nr | awk '!seen[$2]++' | head -n 5

echo "Processing completed."
