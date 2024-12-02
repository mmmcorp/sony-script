import boto3
import os
import json
from datetime import datetime, timedelta, timezone
from collections import defaultdict

# AWS X-Ray クライアントを初期化（sonyプロファイルを使用）
session = boto3.Session(profile_name='sony')
xray_client = session.client('xray')

# 出力ディレクトリを作成
output_dir = "xray_trace_analysis"
os.makedirs(output_dir, exist_ok=True)

# 現在の日時を取得（UTC）
end_time = datetime.now(timezone.utc)
# 30日前の日時を計算（X-Rayの制限による）
start_time = end_time - timedelta(days=30)

# フィルター式を定義
filter_expression = "responsetime > 3"

def get_segment_details(segment):
    document = json.loads(segment['Document'])
    name = document.get('name', 'Unknown')
    start_time = document.get('start_time', 0)
    end_time = document.get('end_time', 0)
    duration = end_time - start_time if end_time and start_time else 0
    return name, duration

# トレースの総数を追跡するための変数
total_traces = 0

# 1日ごとにループ
current_date = start_time
while current_date < end_time:
    next_date = current_date + timedelta(days=1)
    if next_date > end_time:
        next_date = end_time

    trace_summaries = []
    paginator = xray_client.get_paginator('get_trace_summaries')

    try:
        for page in paginator.paginate(
            StartTime=current_date,
            EndTime=next_date,
            FilterExpression=filter_expression
        ):
            trace_summaries.extend(page['TraceSummaries'])

        # トレースの総数を更新
        total_traces += len(trace_summaries)

        # トレースの詳細情報を取得し、分類
        trace_details = defaultdict(list)

        for summary in trace_summaries:
            trace_id = summary['Id']
            response_time = summary['ResponseTime']
            
            # トレースの詳細を取得
            trace = xray_client.batch_get_traces(TraceIds=[trace_id])['Traces'][0]
            
            http_segment = None
            segments_info = []

            for segment in trace['Segments']:
                name, duration = get_segment_details(segment)
                segments_info.append((name, duration))
                
                document = json.loads(segment['Document'])
                if 'http' in document and not http_segment:
                    http_segment = document

            if http_segment:
                http_info = http_segment['http']
                method = http_info.get('request', {}).get('method', 'UNKNOWN')
                path = http_info.get('request', {}).get('url', 'UNKNOWN').split('?')[0]
                
                key = f"{method} {path}"
                trace_details[key].append((trace_id, response_time, segments_info))

        # 結果をファイルに出力
        output_file = os.path.join(output_dir, f"trace_analysis_{current_date.date()}.txt")
        with open(output_file, 'w') as f:
            f.write(f"日付: {current_date.date()}\n")
            f.write(f"応答時間が3秒を超えたトレースの内訳:\n")
            for key, traces in sorted(trace_details.items(), key=lambda x: len(x[1]), reverse=True):
                f.write(f"{key}: {len(traces)}\n")
                for trace_id, response_time, segments_info in traces:
                    f.write(f"  - トレースID: {trace_id}, 応答時間: {response_time:.2f}秒\n")
                    f.write("    セグメント詳細:\n")
                    for name, duration in segments_info:
                        f.write(f"      {name}: {duration:.3f}秒\n")
                    f.write("\n")
                f.write("\n")

        print(f"分析結果を {output_file} に保存しました。")

    except Exception as e:
        print(f"エラーが発生しました: {e}")
        print(f"日付 {current_date.date()} のデータ取得をスキップします。")

    # 次の日に進む
    current_date = next_date

print("全ての日付の分析が完了しました。")
print(f"総トレース数: {total_traces}")

# 総トレース数をファイルに出力
summary_file = os.path.join(output_dir, "summary.txt")
with open(summary_file, 'w') as f:
    f.write(f"分析期間: {start_time.date()} から {end_time.date()} まで\n")
    f.write(f"総トレース数: {total_traces}\n")

print(f"サマリーを {summary_file} に保存しました。")