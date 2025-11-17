# Python 3.11 베이스 이미지
FROM python:3.11-slim

# 작업 디렉토리 설정
WORKDIR /app

# 시스템 패키지 설치 (HWP 파일 처리용)
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Python 패키지 복사 및 설치
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 애플리케이션 코드 복사
COPY . .

# 환경 변수 설정 (API 키는 Cloud Run에서 설정)
ENV CHROMA_DB_PATH=./data/vector_db
ENV CHUNK_SIZE=1000
ENV CHUNK_OVERLAP=200

# 빌드 시 규정 파일 인덱싱
ARG GOOGLE_API_KEY
ENV GOOGLE_API_KEY=${GOOGLE_API_KEY}
RUN python scripts/process_documents.py --force || echo "Indexing completed or will be done later"

# 포트 설정 (Cloud Run은 PORT 환경변수 사용)
ENV PORT=8080

# 서버 실행
CMD exec uvicorn src.api.search_api:app --host 0.0.0.0 --port ${PORT}
