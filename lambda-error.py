import pandas as pd
import os
import re
from pathlib import Path

def process_lambda_csv(file_path):
    # CSVファイルを読み込む
    df = pd.read_csv(file_path)
    
    # ヘッダー情報を探索して関数名を抽出
    function_name = None
    for _, row in df.head(5).iterrows():
        for col in df.columns:
            value = str(row[col])
            if 'FunctionName:' in value:
                function_name = re.search(r'FunctionName:(\w+)', value).group(1)
                break
        if function_name:
            break
    
    if not function_name:
        raise ValueError("関数名が見つかりません")
    
    # タイムスタンプデータの開始行を特定
    start_row = None
    for idx, row in df.iterrows():
        if isinstance(row['Id'], str) and re.match(r'\d{4}/\d{2}/\d{2}', row['Id']):
            start_row = idx
            break
    
    if start_row is None:
        raise ValueError("タイムスタンプデータが見つかりません")
    
    # データを抽出して処理
    df = df.iloc[start_row:]
    df.columns = ['timestamp', 'errors']
    df['errors'] = pd.to_numeric(df['errors'], errors='coerce')
    df = df[df['errors'] >= 1].dropna()
    
    # エラー件数を整数に変換
    df['errors'] = df['errors'].astype(int)
    
    # 新しいファイル名を作成
    output_dir = Path('processed_results')
    output_dir.mkdir(exist_ok=True)
    output_file = output_dir / f"{function_name}.csv"
    
    # 関数名をヘッダーとして追加して保存
    with open(output_file, 'w') as f:
        f.write(f"{function_name}\n")  # 1行目に関数名
        df.to_csv(f, index=False)  # 2行目以降にデータ
    
    return output_file

def find_lambda_csv_files():
    # lambdaディレクトリ内のすべてのCSVファイルを検索
    base_dir = Path('lambda')
    if not base_dir.exists():
        raise FileNotFoundError("lambdaディレクトリが見つかりません")
    
    csv_files = []
    for year_month_dir in base_dir.iterdir():
        if year_month_dir.is_dir() and re.match(r'\d{6}', year_month_dir.name):
            csv_files.extend(year_month_dir.glob('*.csv'))
    
    return csv_files

# スクリプトを実行
if __name__ == "__main__":
    try:
        # すべてのCSVファイルを検索
        csv_files = find_lambda_csv_files()
        
        if not csv_files:
            print("処理対象のCSVファイルが見つかりません")
            exit()
        
        # 各ファイルを処理
        for file_path in csv_files:
            try:
                output_file = process_lambda_csv(file_path)
                print(f"処理完了: {file_path} -> {output_file}")
            except Exception as e:
                print(f"エラー発生 {file_path}: {str(e)}")
                
    except Exception as e:
        print(f"エラー発生: {str(e)}")