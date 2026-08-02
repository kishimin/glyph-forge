## Overview

一般公開する画像生成APIについて、入力値、生成画像、アップロード画像、リクエスト頻度および同時実行を制限し、CPU・メモリ・一時ストレージの過剰消費を防ぎます。あわせて、レビューで確認されたmultipart解析前の本文制限、イベントループの占有、生成タイムアウトの未適用を修正します。

## Related Tasks

TBD（関連Issue・チケットは根拠未確認）

## Changes Made

- JSONおよびmultipart入力に共通の文字列制約を追加しました。
  - `frame_text`: 1〜64文字。空白のみと制御文字を拒否
  - `inner_text`、`outer_text`: 1〜128文字。片方のみ空白文字列を許可し、両方が空白のみの場合は拒否
  - 検証前にUnicode NFCで正規化
- `frame_font_size`を8〜128、`output_font_size`を10〜64、RGB各成分を0〜255に制限しました。
- 公開リクエストから`max_chars_per_line`と`frame_cell_padding_ratio`を削除し、未定義フィールドを拒否するようにしました。一般画像は内部で5文字ごとに折り返し、プロフィール画像はキャンバスに合わせて配置を決定します。
- 生成画像を幅2,048px、高さ2,048px、総画素数4,194,304以下に制限し、大きな出力バッファや文字グリッドを確保する前に検証するようにしました。
- アップロード画像を次の条件で検証するようにしました。
  - ファイル本体は2MiB以下
  - 幅・高さは各204px以下、総画素数は41,616以下
  - 実データ形式がPNG、JPEG、WebPのいずれか
  - アニメーション画像とPillowのDecompression Bomb検出対象を拒否
- `/images/frame-file`ではmultipart解析前に、2MiBのファイル本体と64KiBのフォームオーバーヘッドを合わせた本文上限をASGI受信チャンクへ適用しました。受け付けるファイルは1件、フォームフィールドは5件までです。
- 全画像生成エンドポイントへ、クライアントIP単位のトークンバケットを追加しました。バーストは3件、補充速度は10件/分で、超過時は`Retry-After`付きの`429`を返します。`/health`は対象外です。
- 1プロセスあたり同時生成1件、待機4件、待機時間10秒の実行制限を追加しました。キュー満杯または待機超過時は`Retry-After`付きの`503`を返します。
- Pillowによるデコード、描画、PNGエンコードを子プロセスへ分離し、30秒で停止・回収するようにしました。タイムアウト後も同時実行枠を解放します。
- 入力制約、出力制約、アップロード検証、レート制限、待機キュー、イベントループ応答性、子プロセス停止と実行枠再利用を対象とするテストを追加しました。
- READMEへ公開APIの入力・出力・アップロード・トラフィック制限を追記しました。

## Out of Scope

- 複数プロセスまたは複数インスタンス間で共有するレート制限と同時実行制限
- 前段プロキシでの本文容量制限および信頼済みクライアントIPの書き換え設定
- 外部負荷試験と本番プロキシを含む統合試験
- デプロイ基盤の構築・変更

## Impact

- 対象は`POST /images`、`POST /images/x-icon`、`POST /images/background`、`POST /images/frame-file`です。
- 旧公開フィールド`max_chars_per_line`または`frame_cell_padding_ratio`を送信するクライアントは`422 Unprocessable Entity`になります。
- 入力値・画像寸法・実画像形式の違反は`422`、multipart本文上限の超過は`413`、レート超過は`429`、処理容量超過または生成タイムアウトは`503`になります。
- レート制限と同時実行状態はアプリケーションプロセス内で管理されるため、インスタンスを増やすと制限状態は共有されません。
- 固定サイズのXアイコン400×400pxと背景画像1,500×500pxは生成画像上限内です。

## Testing

以下を現在の`feature/expansion`で実行し、すべて成功しました。

- `python -m pytest -q`: 103 tests passed
- `autoflake --check --recursive .`: passed
- `isort --check-only .`: passed
- `black --check .`: passed（24 files would be left unchanged）
- `flake8 .`: passed
- `mypy src`: passed（9 source files）

## Notes

- 対象差分は`new-origin/main`との共通祖先`1e518414e2ed5be18f85af556c84f56ef6f48303`から`feature/expansion`の`960438e`までです。
- `review/public-image-safety-limits-20260802.md`の3件の指摘は、`review/responses/public-image-safety-limits-20260802-responses.md`に対応内容を記録しています。
- `mypy app`はリポジトリのREADMEに記載された検証コマンドではなく、本PRの成功条件には含めていません。レビュー時の実行では、型情報未提供パッケージなどに関する4件のエラーが記録されています。
- 制限がプロセス内であること、実クライアントIPが前段プロキシの設定に依存すること、外部負荷試験を実施していないことは残存リスクです。
