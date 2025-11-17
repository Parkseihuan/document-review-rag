# PDF 파일을 텍스트로 변환하는 방법

규정 파일이 PDF 형식인 경우, 텍스트로 변환하여 사용해야 합니다.

---

## 방법 1: 온라인 변환 (가장 간단) ⭐

### Adobe Acrobat Online (무료)
1. https://www.adobe.com/acrobat/online/pdf-to-text.html 접속
2. PDF 파일 업로드
3. "Convert to TXT" 클릭
4. 변환된 .txt 파일 다운로드
5. `rules/government/` 폴더에 저장

### 장점:
- 설치 불필요
- 빠르고 정확
- 무료

---

## 방법 2: Google Docs (무료, 추천)

1. **Google Drive 업로드**
   - https://drive.google.com 접속
   - PDF 파일 업로드

2. **Google Docs로 열기**
   - 업로드한 PDF 우클릭
   - "연결 앱 → Google Docs"

3. **텍스트 복사**
   - Google Docs에서 열린 내용 전체 선택 (Ctrl+A)
   - 복사 (Ctrl+C)

4. **텍스트 파일로 저장**
   - 메모장이나 VS Code에 붙여넣기
   - UTF-8 인코딩으로 .txt 파일로 저장
   - `rules/government/` 폴더에 저장

### 장점:
- 무료
- OCR 자동 적용 (스캔 PDF도 변환 가능)
- 한글 인식 우수

---

## 방법 3: Windows 내장 기능

### Notepad++ 사용 (무료 프로그램)

1. **Notepad++ 설치**
   - https://notepad-plus-plus.org/ 다운로드
   - 설치

2. **PDF 내용 복사**
   - PDF 뷰어(Adobe Reader, 브라우저 등)로 PDF 열기
   - 내용 선택 후 복사

3. **저장**
   - Notepad++에 붙여넣기
   - 인코딩: UTF-8
   - 파일명: `행정업무운영편람.txt`
   - 저장 위치: `rules/government/`

---

## 방법 4: 프로그래밍 (고급 사용자용)

### Python 사용

```python
# 필요한 패키지 설치
pip install PyPDF2

# 변환 스크립트
import PyPDF2

def pdf_to_text(pdf_path, txt_path):
    with open(pdf_path, 'rb') as file:
        reader = PyPDF2.PdfReader(file)
        text = ''
        for page in reader.pages:
            text += page.extract_text()

    with open(txt_path, 'w', encoding='utf-8') as file:
        file.write(text)

# 사용
pdf_to_text('행정업무운영편람.pdf', 'rules/government/행정업무운영편람.txt')
```

---

## 변환 후 확인사항

### 1. 인코딩 확인
파일이 UTF-8로 저장되었는지 확인하세요.

```bash
# VS Code에서 확인
우측 하단에 "UTF-8" 표시 확인
```

### 2. 내용 확인
- 줄바꿈이 적절한지
- 특수문자가 제대로 변환되었는지
- 표나 그림 설명이 이상하지 않은지

### 3. 불필요한 내용 제거 (선택사항)
- 목차, 페이지 번호 등 불필요한 내용 제거
- AI가 검토할 때 더 정확한 결과를 얻을 수 있음

---

## 저장 위치 및 파일명

### 파일명 규칙
- 한글 사용 가능
- 공백 대신 하이픈(-) 권장
- 예: `행정업무운영편람.txt`, `행정-효율-규정.txt`

### 저장 위치
```
rules/
├── government/          # 정부 자료
│   ├── 행정업무운영편람.txt
│   ├── 행정규정시행규칙.txt
│   └── 알기쉬운행정용어.txt
└── local/              # 대학 자체 규정
    └── 본교-공문서작성안내.md
```

---

## 파일 등록

변환한 파일을 `rules-config.json`에 등록하세요:

```json
{
  "id": "my-new-rule",
  "name": "파일 이름",
  "path": "rules/government/파일명.txt",
  "type": "text",
  "enabled": true,
  "priority": 6,
  "description": "설명",
  "source": "정부",
  "originalFormat": "pdf"
}
```

---

## 문제 해결

### Q: 한글이 깨져요
**A**:
- 인코딩을 UTF-8로 변경
- Google Docs 방법 사용 (한글 인식 우수)

### Q: 표나 그래프가 이상해요
**A**:
- 수동으로 정리 필요
- 또는 해당 부분 삭제 (AI는 텍스트만 이해)

### Q: 파일이 너무 커요 (수백 페이지)
**A**:
- 중요한 부분만 추출하여 별도 파일로 저장
- 또는 AI 검토 시에만 사용 (로컬 규칙 검사에서는 제외)

---

## 자동화 스크립트 (선택사항)

### 여러 PDF를 한 번에 변환

```bash
# Bash 스크립트 (Linux/Mac)
for file in *.pdf; do
    pdftotext "$file" "rules/government/${file%.pdf}.txt"
done
```

```powershell
# PowerShell 스크립트 (Windows)
Get-ChildItem *.pdf | ForEach-Object {
    # Adobe Reader 사용
    & "C:\Program Files\Adobe\Acrobat DC\Acrobat\Acrobat.exe" /t /o "$($_.FullName)"
}
```

---

**도움이 필요하면 Issue를 올려주세요!**
