# Kanameliser Blender Extensions

[English](README.md)

Blender Extensions の配布リポジトリ。GitHub Pages でホストし、Blender 4.2+ の Extension 形式でアドオンを配布する。

**ランディングページ:** `https://kxn4t.github.io/blender-extensions/`

**リポジトリ URL (Blender 用):** `https://kxn4t.github.io/blender-extensions/index.json`

## リポジトリの追加方法

1. Blender で **Edit > Preferences > Get Extensions** を開く
2. **Repositories** ドロップダウン → **+** → **Add Remote Repository**
3. URL を入力: `https://kxn4t.github.io/blender-extensions/index.json`

## 収録アドオン

| アドオン | 概要 | リンク |
|---|---|---|
| Vertex Group Merger | 複数の頂点グループを1つのターゲットグループにマージ | [GitHub](https://github.com/kxn4t/vertex-group-merger) / [BOOTH](https://kanameliser.booth.pm/items/6853101) |
| Pose to Rest Pose | シェイプキーとドライバーを保持したままレストポーズを適用 | [GitHub](https://github.com/kxn4t/pose-to-rest-pose) / [BOOTH](https://kanameliser.booth.pm/items/6999784) |

---

## 開発者向け情報

### リポジトリの仕組み

```
アドオンリポジトリ                    配布リポジトリ (blender-extensions)
       |                                        |
  タグ push → release.yml                        |
    zip ビルド → draft リリース作成              |
       |                                        |
  手動で publish                                 |
       |                                        |
  dispatch.yml → repository_dispatch ──────────> |
       |                                  update-extension.yml:
       |                                    zip ダウンロード
       |                                    index.json 更新
       |                                    ランディングページ更新
       |                                    commit & push
       |                                        |
       |                                  pages.yml → GitHub Pages デプロイ
```

### リリース手順（既存アドオンの更新）

1. **アドオンリポジトリ**で `blender_manifest.toml` のバージョンを更新し、タグを push する
   ```bash
   git tag v1.2.0
   git push origin v1.2.0
   ```
2. `release.yml` が走り、zip をビルドして **draft リリース**が作成される
3. GitHub のリリースページで内容を確認し、**Publish release** をクリック
4. `dispatch.yml` が走り、配布リポジトリへ `repository_dispatch` が送信される
5. 配布リポジトリの `update-extension.yml` が自動で zip ダウンロード・`index.json` 更新・commit & push を行う
6. push をトリガーに `pages.yml` が走り、GitHub Pages にデプロイされる

> 手順 3 の Publish 以降はすべて自動。手動操作は **タグ push** と **Publish release** の 2 つだけ。

### アドオン `id` の命名規則

`blender_manifest.toml` の `id` フィールドがシステム全体の識別子となる。以下すべて `id` に基づいて統一する。

| 用途 | 形式 | 例 |
|---|---|---|
| `blender_manifest.toml` の `id` | `snake_case` | `vertex_group_merger` |
| zip ファイル名 | `{id}-{version}.zip` | `vertex_group_merger-0.6.0.zip` |
| 配布リポジトリのフォルダ名 | `{id}/` | `vertex_group_merger/` |
| `index.json` のエントリ識別 | `id` フィールドで一致判定 | 同一 `id` は最新1件のみ |

> `id` は Blender 内部でパッケージを識別するために使われる。英小文字・数字・アンダースコアのみ使用可能（ハイフン不可）。一度公開した `id` は変更しないこと。

### レガシーアドオンから Extension への移行チェックリスト

既存アドオンを Extension 形式に変換する際の確認事項（公式ドキュメント: [Getting Started](https://docs.blender.org/manual/en/latest/advanced/extensions/getting_started.html) / [Add-ons](https://docs.blender.org/manual/en/latest/advanced/extensions/addons.html)）:

**コード移行:**

- [ ] `blender_manifest.toml` を作成する
- [ ] `bl_info` を削除する（バージョン情報は manifest に一本化）
- [ ] モジュール名のハードコードを `__package__` に置き換える（`AddonPreferences.bl_idname`、翻訳登録など）
- [ ] すべてのインポートを相対インポートにする（`from .module import ...`）
- [ ] サードパーティ Python モジュールを使用している場合は [wheels でバンドル](https://docs.blender.org/manual/en/latest/advanced/extensions/python_wheels.html)する
- [ ] アドオン自身のディレクトリへの書き込みがある場合は `bpy.utils.extension_path_user(__package__)` に変更する

**manifest の注意事項:**

- `tagline` は句読点（`.`）で終わってはいけない
- `version` はセマンティックバージョニングに従う
- `license` は `SPDX:` プレフィクス付きの SPDX 識別子を使う
- 値を設定しないオプショナルフィールドは空文字や空リストではなく、フィールドごと省略する

**テスト:**

- [ ] ディスクからインストールして動作確認する

### 新しいアドオンの追加手順

1. アドオンリポジトリに `blender_manifest.toml` を追加
2. `.github/workflows/release.yml` を Extension 形式に対応（manifest 同梱、ファイル名を `id` に統一）
3. `.github/workflows/dispatch.yml` を追加（テンプレート: [`templates/dispatch.yml`](templates/dispatch.yml)）
4. リポジトリの Secrets に `EXTENSIONS_REPO_TOKEN` を設定
5. `scripts/addons_meta.json` に新しいアドオンのエントリを追加（ランディングページの説明文・リンクに使用）
6. タグを打って draft リリース → publish で自動的に配布リポジトリに追加される

配布リポジトリ側で必要な変更は `addons_meta.json` への追加のみ（`generate_index.py` がフォルダを自動検出）。

### `generate_index.py` の使い方

**add モード** — 通常のパイプラインで使用:

```bash
python scripts/generate_index.py add <addon_id> <version>
```

指定バージョンの zip から `blender_manifest.toml` を読み、`index.json` を差分更新する。同一 `id` のエントリは最新バージョンで置き換え。

**backfill モード** — 初期セットアップや手動で zip を追加した場合:

```bash
python scripts/generate_index.py backfill
```

各フォルダ内の全 `.zip` をスキャンし、最新バージョンを `index.json` に追加する（既存エントリの削除や更新はしない）。

### `generate_pages.py` の使い方

```bash
python scripts/generate_pages.py
```

`index.json` と `scripts/addons_meta.json` を読み、ランディングページ（`ja/README.md`・`en/README.md`）のアドオン一覧を更新する。各 README 内の `<!-- EXTENSIONS_LIST_START -->` ～ `<!-- EXTENSIONS_LIST_END -->` マーカー間を最新の内容で差し替える仕組み。

通常は `update-extension.yml` のパイプライン内で自動実行されるため、手動で呼ぶ必要はない。`addons_meta.json` の説明文やリンクを修正した場合など、手動で再生成したいときに使う。

### ロールバック手順

過去バージョンの zip がフォルダに残っているため、以下で戻せる:

```bash
python scripts/generate_index.py add <addon_id> <old_version>
```

### 参考ソース

- [Extensions の作り方 (公式マニュアル)](https://docs.blender.org/manual/en/latest/advanced/extensions/getting_started.html)
- [静的リポジトリの作成 (公式マニュアル)](https://docs.blender.org/manual/en/latest/advanced/extensions/creating_repository/static_repository.html)
- [Extensions API Listing v1 (開発者ドキュメント)](https://developer.blender.org/docs/features/extensions/api_listing/v1/)
- [Manifest Schema (開発者ドキュメント)](https://developer.blender.org/docs/features/extensions/schema/)
- [`blender_ext.py` (Blender ソースコード)](https://projects.blender.org/blender/blender/src/branch/main/scripts/addons_core/bl_pkg/cli/blender_ext.py)
