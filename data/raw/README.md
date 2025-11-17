# 본교 규정 파일 폴더

이 폴더는 **대학 자체에서 작성한 공문서 규정 파일**을 저장하는 곳입니다.

## 📁 파일 추가 방법

### 1. GitHub 웹사이트에서 추가
1. 이 폴더로 이동
2. "Add file" → "Upload files" 클릭
3. MD 또는 TXT 파일 업로드
4. GitHub Actions가 자동으로 `rules-config.json`에 등록

### 2. Git 명령어로 추가
```bash
# 새 파일 생성
echo "# 우리대학 특별규정" > rules/local/우리대학특별규정.md

# 커밋 및 푸시
git add rules/local/우리대학특별규정.md
git commit -m "feat: 새 규정 추가"
git push
```

## 📝 파일 형식

### Markdown (.md) - 권장
```markdown
# 규정 제목

## 1. 맞춤법 규칙

| 잘못된 표현 | 올바른 표현 | 설명 |
|------------|------------|------|
| 안됩니다 | 안 됩니다 | 띄어쓰기 |
```

### 텍스트 (.txt)
- PDF를 변환한 순수 텍스트 파일
- AI 컨텍스트로만 사용됨

## ⚠️ 주의사항

- **이 README.md와 .gitkeep 파일은 삭제하지 마세요!**
- 이 파일들이 있어야 폴더 안의 모든 규정 파일을 삭제해도 폴더가 유지됩니다
- 파일명에는 특수문자 사용을 자제하세요

## 🔗 관련 문서

- [PDF 변환 가이드](../PDF-CONVERSION.md)
- [문제 해결 가이드](../../TROUBLESHOOTING.md)
