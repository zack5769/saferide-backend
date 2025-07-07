# SafeRide Backend

雨を考慮したルート案内システムのバックエンド

## 主な機能

- リアルタイム雨データの取得（Yahoo!気象情報API）
- 雨を考慮したルート計算（GraphHopper）

## 注意

- 動きはするけどエラーハンドリングとかまだ全然やってない
  - スタート地点ですでに雨が降っている場合はまだ対応不可
  - 雨降ってるエリアが多すぎても同様
  - 最終的には雨ガン無視のルート案内するつもり

## システム要件

- Docker入ってるよね
- Yahoo!気象情報API キー（YAHOO_API_KEY）
- GraphHopperで8GBメモリ使うようにしてるから適宜減らしてくれ
 
## セットアップ

### 1. 必要ファイルのダウンロード

GraphHopperの実行ファイルと地図データを`/graphhopper`ディレクトリに配置

#### GraphHopperのダウンロード

```bash
cd graphhopper
wget https://repo1.maven.org/maven2/com/graphhopper/graphhopper-web/10.0/graphhopper-web-10.0.jar
```

#### 地図データのダウンロード

日本の地図データを[Geofabrik](https://download.geofabrik.de/asia/japan.html)からダウンロード：

```bash
cd graphhopper
wget https://download.geofabrik.de/asia/japan-latest.osm.pbf
```

### 2. 環境変数の設定

Yahoo!気象情報APIのキー`.env`に記述

### 3. アプリケーションの起動

プロジェクトルートディレクトリで以下のコマンドを実行：

```bash
docker-compose build
docker-compose up -d
```

## API仕様

### エンドポイント（まだ途中）

#### GET /route/{start}/{goal}

ルート情報を返す

**パラメータ:**

- `start`: 開始地点の座標（例: "35.6762,139.6503"）
- `goal`: 目的地の座標（例: "35.7169,139.7774"）

### アクセス方法

- **API ドキュメント**: <http://localhost:5000/docs>
  - Swagger UIでインタラクティブにAPIをテスト可能
- **GraphHopper エンジン**: <http://localhost:8989>
  - ルーティングエンジンの管理画面

## プロジェクト構造

```text
saferide-backend/
├── src/
│   └── modules/
│       ├── api.py          # FastAPI エンドポイント
│       ├── service.py      # ビジネスロジック
│       ├── rain_data.py    # 雨データ処理
│       └── values.py       # 座標・境界計算
├── Docker/
│   ├── graphhopper/        # GraphHopper Dockerfile
│   └── python/             # Python Dockerfile
├── graphhopper/            # GraphHopper実行環境
├── requirements.txt        # Python依存関係
├── docker-compose.yml      # Docker設定
└── __main__.py            # スタンドアローン実行用
```
