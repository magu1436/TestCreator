# OCR利用上限と公開デモの運用

OCRはOpenAI APIを呼び出すため、1回ごとに料金が発生します。`OCR_DAILY_LIMIT` で、1日あたりのOCR呼び出し回数を全利用者の合計で制限できます。仕様の正本は[公開デモ仕様書](https://docs.google.com/document/d/1ZziDbjLtnwCEcHECjoDa0XChiCCFmQQpeR4HQblHsH4/edit)の第6節と[Issue #33](https://github.com/magu1436/TestCreator/issues/33)です。

## 設定

| `OCR_DAILY_LIMIT` | `DEMO_MODE=true` | 通常環境 |
| --- | --- | --- |
| 未設定・空 | 10回／日 | 無制限 |
| `-1` | 無制限 | 無制限 |
| `0` | OCR停止 | OCR停止 |
| 正の整数 | その回数／日 | その回数／日 |

`-1` 未満の値や整数以外を指定すると、起動時に `ImproperlyConfigured` で停止します。本番 `wordtest` は未設定のままなら従来どおり無制限で、利用回数の記録も行いません。

上限に達したとき、OCRはOpenAI APIを呼び出さずにHTTP 429とエラーメッセージを返します。単語の手動編集やテスト作成は引き続き利用できます。利用再開の時刻は表示しません。

## 回数の数え方

- 日付は `TIME_ZONE`（Asia/Tokyo）のローカル日付で区切ります。日本時間の0時に新しい利用枠になります。
- 外部APIを呼び出す直前に利用枠を1回分確保します。APIの呼び出しが失敗しても、確保した枠は戻しません。失敗を繰り返して無制限に再試行されることを防ぐためです。
- 未ログイン（403）、ファイル未指定（400）、APIキー未設定（503）、上限到達（429）で拒否したリクエストは消費しません。利用枠を記録するDBに書き込めなかった場合も、消費せずに503を返します。
- APIの応答を解析できなかった場合も、課金された呼び出しの推定費用は `APICostLog` に記録します。
- 利用回数は日付ごとに `OCRDailyUsage` の1行で管理し、条件付きUPDATE（`count < 上限` のときだけ加算）で確保します。複数のプロセス・スレッドから同時に要求されても上限を超えません。SQLiteでは書き込みが重なると最大5秒待ち、それでも書き込めなければ `database is locked` のエラーになります。公開デモは最大インスタンス数1で、OCRの回数も少ないことを前提にしています。
- `APICostLog` は、OpenAIが応答を返した（課金された）呼び出しのリクエストID・モデル・推定費用を事後に記録します。呼び出し回数の判定には使いません。

## 公開デモでのリセット

公開デモでは利用回数・費用ログ・単語データをコンテナ内のSQLiteに保存します。インスタンスの終了・再生成、新しいリビジョンへの切り替え（環境変数の変更を含む）でSQLiteは作り直され、利用回数も0に戻ります。

そのため、この上限は「厳密な1日10回」や「請求額の上限」を保証しません。仕様書で受け入れたリスクです。費用の確認はOpenAIの利用状況画面で行ってください。

## ログの確認

`ocr` アプリのINFO以上のログを標準出力に出力します。Cloud Runの標準ログで次のメッセージを確認できます。

| メッセージ | レベル | 内容 |
| --- | --- | --- |
| `OCR利用枠を予約しました: date=… used=… limit=…` | INFO | 利用枠を確保した |
| `OCR利用を拒否しました(上限到達): …` | WARNING | 上限到達で拒否した |
| `OCR利用を拒否しました(OCR停止中): …` | WARNING | `OCR_DAILY_LIMIT=0` で拒否した |

各行の先頭には `INFO ocr.quota:` のようにレベルとロガー名が付きます。OCR処理の失敗、利用枠の確保の失敗、費用ログの保存失敗も `ocr` のログとして記録します。APIキーはログに出力しません。

```powershell
gcloud logging read 'resource.type="cloud_run_revision" AND resource.labels.service_name="DEMO_SERVICE" AND textPayload:"OCR"' --project=PROJECT --freshness=1d --limit=50
```

`DEMO_SERVICE` には公開デモのサービス名を指定します。本番 `wordtest` を指定しないでください。

## 公開デモだけを止める

どの操作も、サービス名にデモ用サービスを明示して実行します。本番 `wordtest` と本番TiDBには影響しません。

OCRだけを止める場合は、上限を0にします。新しいリビジョンが作られるため、SQLiteのデータと利用回数はリセットされます。

```powershell
gcloud run services update DEMO_SERVICE --project=PROJECT --region=REGION --update-env-vars=OCR_DAILY_LIMIT=0
```

デモ全体の公開を止める場合は、外部からの通信を受け付けないようにします。再開するときは `--ingress=all` に戻します。

```powershell
gcloud run services update DEMO_SERVICE --project=PROJECT --region=REGION --ingress=internal
```

APIキーの漏えいが疑われる場合は、デモを止めたうえでOpenAI側でキーを無効化します。本番と同じキーを使っているため、本番のOCRも止まる点に注意してください。
