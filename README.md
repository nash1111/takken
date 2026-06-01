# 宅建即答ラボ

`takkensokuto.com` は、宅建の一問一答を無料・登録不要で練習できる静的サイトです。

## YouTube / Shorts 流入のUTM命名ルール

YouTube Shorts、固定コメント、チャンネル概要からの流入を区別するため、サイトURLには次のUTMを付与します。

| 用途 | URL例 | source | medium | campaign |
| --- | --- | --- | --- | --- |
| Shorts説明欄 | `/flashcards/?utm_source=youtube&utm_medium=shorts&utm_campaign=daily_flashcards` | `youtube` | `shorts` | `daily_flashcards` |
| 固定コメント | `/quiz/?utm_source=youtube&utm_medium=pinned_comment&utm_campaign=daily_quiz` | `youtube` | `pinned_comment` | `daily_quiz` |
| チャンネル概要 | `/?utm_source=youtube&utm_medium=channel_profile&utm_campaign=profile_home` | `youtube` | `channel_profile` | `profile_home` |
| Shorts受け皿LP | `/shorts/?utm_source=youtube&utm_medium=shorts&utm_campaign=shorts_lp` | `youtube` | `shorts` | `shorts_lp` |

### 命名原則

- `utm_source`: 流入元プラットフォーム。YouTubeは `youtube` で統一。
- `utm_medium`: クリック位置。`shorts`, `pinned_comment`, `channel_profile` など。
- `utm_campaign`: 投稿/導線の目的。日次導線は `daily_*`、常設導線は `profile_*`。
- 日本語やスペースは使わず、英小文字・数字・アンダースコアに統一。

## Shorts説明欄テンプレート

```text
宅建の一問一答を無料で練習できます。
登録不要・スマホですぐ解けます。

▼動画で見た論点をすぐ復習
{QUESTION_URL}?utm_source=youtube&utm_medium=shorts&utm_campaign={CAMPAIGN}

▼10問まとめて解く
https://takkensokuto.com/quiz/?utm_source=youtube&utm_medium=shorts&utm_campaign=daily_quiz
```

## 固定コメントテンプレート

```text
この問題を解いたら、次は無料の10問クイズへ👇
https://takkensokuto.com/quiz/?utm_source=youtube&utm_medium=pinned_comment&utm_campaign=daily_quiz

不動産営業・宅建受験生向けに毎日サクッと確認できます。
```

## 論点別の直リンクルール

- 動画が個別問題に対応する場合: 個別問題URLを最優先
- 論点だけ対応する場合: `/topics/takken-gyoho/`, `/topics/article35-37/`, `/topics/hikkake/`, `/topics/fudosan-sales/` のうち最も近いページ
- どれにも当てはまらない場合: `/quiz/` または `/flashcards/`

## Cloudflare Pages 手動プレビュー

このプロジェクトはCloudflare Pagesのdirect uploadで運用されています。ブランチプレビューは、対象ブランチから以下の形で手動デプロイします。

```sh
CLOUDFLARE_ACCOUNT_ID=<account_id> wrangler pages deploy . \
  --project-name takken-sokuto-lab \
  --branch <branch-name>
```
