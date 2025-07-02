FROM eclipse-temurin:22-jdk

WORKDIR /app

# システムパッケージのインストール
RUN apt-get update && \
    apt-get install -y git wget unzip bash && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# コンテナのデフォルトコマンド
CMD ["bash"]
