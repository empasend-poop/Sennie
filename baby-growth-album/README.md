# 🧸 우리 아이 성장앨범

2022년생 아이의 추억을 담는 Python / Streamlit 앨범입니다. 따뜻한 아이보리와 파스텔 디자인으로 Timeline과 Picture를 나누었습니다.

- Timeline: 2022~2026년 각 5개씩, 총 25개 샘플 이벤트. 이벤트당 사진 1~3장.
- Picture: 연도별 사진 폴더 자동 탐색. 30장씩 넣으면 총 150장, 더 많은 사진도 지원.
- 세는나이: 2022년 1살 → 2026년 5살. 생년 기준으로 자동 계산합니다.
- 정사각형 갤러리, 원본 비율 확대, EXIF 회전 보정, 없는 사진 안내.
- 실제 사진은 포함하지 않으며, 사진 없이도 실행할 수 있습니다.

## 1. 실행 (Windows, Python 3.10 이상)

ZIP을 풀고 `baby-growth-album` 폴더에서 명령 프롬프트를 여세요.

```bat
python -m venv .venv
.venv\Scripts\activate.bat
python -m pip install -r requirements.txt
python -m streamlit run app.py
```

PowerShell에서는 활성화 없이 아래처럼 실행할 수 있습니다.

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m streamlit run app.py
```

Mac / Linux:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python -m streamlit run app.py
```

브라우저가 자동으로 열리지 않으면 터미널에 표시된 주소(보통 http://localhost:8501)를 여세요. 종료는 터미널에서 Ctrl+C입니다.

## 2. 파일 구성

- `app.py`: 앨범 화면
- `requirements.txt`: 설치할 라이브러리
- `.gitignore`: 사진·가상환경·비밀 파일 제외
- `.streamlit/config.toml`: 색상 테마
- `data/profile.json`: 이름·생년월일·별명·메시지·대표 사진 경로
- `data/timeline.json`: 연도별 이벤트
- `data/pictures.json`: 선택 사항인 사진 날짜·설명
- `images/profile/`: 대표 사진
- `images/2022/` ~ `images/2026/`: 연도별 `timeline/`, `pictures/`

샘플 생일은 임의 날짜입니다. 실제 생년월일로 수정해주세요. 생일의 회차는 2023년 첫 번째, 2026년 네 번째이며, 연도별 세는나이와 구분됩니다.

## 3. 사진 넣기

대표 사진: `images/profile/main.jpg`

Timeline 사진: 각 연도의 `timeline` 폴더에 `01.jpg` ~ `05.jpg`를 넣으세요. JSON의 `image` 경로와 파일명이 같아야 합니다.

Picture 사진: 각 연도의 `pictures` 폴더에 `001.jpg` ~ `030.jpg` 등을 넣으세요. JPG, JPEG, PNG, WEBP, BMP를 지원합니다. HEIC는 JPG로 변환해주세요. 파일명 순으로 표시되므로 번호는 001처럼 맞추는 것이 편합니다.

사진이나 JSON을 수정한 뒤 사이드바의 **사진·기록 새로고침**을 누르세요. 앱은 실행 중 폴더 변경을 주기적으로 감시하지 않습니다. 버튼 또는 화면 조작으로 다시 실행될 때 읽습니다. Python 코드를 바꿀 필요는 없습니다.

## 4. 기록 수정

`data/timeline.json`의 날짜·제목·설명·사진 경로를 바꾸세요. JSON은 UTF-8로 저장하고 마지막 항목 뒤에 쉼표를 넣지 마세요.

```json
{
  "date": "2022-03-10",
  "title": "처음 만난 날 👶",
  "description": "우리 가족에게 가장 소중한 날",
  "image": "images/2022/timeline/01.jpg"
}
```

사진 여러 장은 `image` 대신 아래 필드를 사용하세요(최대 3장 표시).

```json
"images": ["images/2022/timeline/01.jpg", "images/2022/timeline/02.jpg"]
```

`pictures.json`에는 앱 기준 경로를 키로 기록합니다. 등록하지 않은 사진도 파일명과 함께 표시됩니다.

```json
{
  "images/2022/pictures/001.jpg": {
    "date": "2022-03-10",
    "caption": "처음 만난 소중한 날 ❤️"
  }
}
```

## 5. 2027년 이후 추가

`images/2027/pictures/`를 만들고 사진을 넣으면 `2027 · 6살`이 추가됩니다. Timeline은 `timeline.json`에 `"2027": [...]`을 추가하세요. 갤러리 폴더 또는 Timeline에 등록된 연도를 자동 탐색합니다.

## 6. GitHub에 올리기

Git이 설치되어 있다면 프로젝트 폴더에서:

```bash
git init
git add .
git status
git commit -m "Add baby growth album"
git branch -M main
```

GitHub에서 빈 저장소를 만든 뒤 실제 주소로 바꾸어 실행하세요.

```bash
git remote add origin https://github.com/YOUR_ID/baby-growth-album.git
git push -u origin main
```

`git status`에서 사진 파일이 추가되지 않았는지 확인하세요. 기본 `.gitignore`는 모든 실제 사진을 제외하고 빈 폴더용 `.gitkeep`만 포함합니다. 이미 Git에 추적된 사진은 `.gitignore`만으로 제외되지 않습니다.

GitHub 웹에서 수동 업로드할 때는 `.gitignore`가 파일 선택을 막지 않으므로 실제 사진을 선택하지 마세요. 개인 이름·생일을 JSON에 입력하면 해당 정보는 코드와 함께 올라갑니다. 공개 저장소에는 샘플 정보를 유지하세요.

GitHub 업로드는 웹앱 배포가 아닙니다. 이 프로젝트는 우선 PC에서 실행하는 구성이며, 원격 서버에 배포할 경우 그 서버에도 사진이 있어야 합니다. 사진을 Git에서 제외했으므로 GitHub 코드만 배포하면 사진이 보이지 않습니다. 하트 즐겨찾기 및 웹 화면에서 사진 업로드·기록 편집 기능은 이 버전에 포함하지 않았습니다.
