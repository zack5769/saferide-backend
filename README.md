# SafeRide Backend

雨を考慮したルート案内システムのバックエンド

## 主な機能

- リアルタイム雨データの取得（Yahoo!気象情報API）
- 雨を考慮したルート計算（GraphHopper）

## 注意

- スタート地点，ゴール地点で雨が降っている場合には対応不可能としてエラーを返す
  - その後，雨を考慮しないルート案内をするという使い方を想定

## システム要件

- Docker
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

Yahoo!気象情報APIのキーを`.env`に記述。ログ関連のオプションとして、以下の環境変数も設定可能:

- `LOG_LEVEL` - ログレベル（デフォルト: `INFO`）
- `LOG_FILE`  - ログファイルのパス（デフォルト: `logs/app.log`）

### 3. アプリケーションの起動

プロジェクトルートディレクトリで以下のコマンドを実行：

```bash
docker-compose build
docker-compose up -d
```

`__main__.py`を直接実行する必要はなく、上記コマンドでAPIサーバーとGraphHopperが同時に起動する。

## API仕様

### エンドポイント

#### `GET /route/{start}/{goal}`

雨が降っているエリアを回避したルート情報を取得する。

**パラメータ**

- `start` - 開始地点の座標（例: `35.6762,139.6503`）
- `goal`  - 目的地の座標（例: `35.7169,139.7774`）

**処理の流れ**

1. `start` と `goal` から経路全体を含むバウンディングボックスを計算。
2. バウンディングボックスをタイルに分割し、それぞれの中心座標で
   Yahoo! 気象情報 API から降雨データを取得。
3. 雨が観測されたタイルを GraphHopper の `custom_model` 用データに変換。
4. GraphHopper (`http://graphhopper:8989/route`) へルート計算リクエストを送信し、
   雨エリアを回避するよう priority ルールを適用。
5. 計算結果と雨タイルのリストを JSON で返却。

#### `GET /normal_route/{start}/{goal}`

雨を考慮せず通常のルートを取得する。

**処理の流れ**

1. `start` と `goal` を GraphHopper の `/route` エンドポイントへ送信。
2. 返ってきたルート情報をそのまま返却する。

### アクセス方法

- **API ドキュメント**: <http://localhost:5000/docs>
  - Swagger UIでインタラクティブにAPIをテスト可能
- **GraphHopper エンジン**: <http://localhost:8989>
  - ルーティングエンジンの管理画面
  - 主要エンドポイント: `/route` (POST) ほか

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
