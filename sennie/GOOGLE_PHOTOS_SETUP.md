# 성장앨범: Google Photos 가져오기 + AI 문구

기존 앨범 디자인, 사진과 JSON 기록을 유지했습니다. 상단의 **📷 사진 가져오기 · ✨ AI 문구 작성**을 열어 사용합니다.

## 1. GitHub에 반영하기

현재 app.py가 있는 sennie 폴더에 다음 파일을 교체/추가합니다.

- app.py: 사진 가져오기 패널 연결, 출생 이전 가족 기록도 표시
- requirements.txt: requests 추가
- photo_import.py: 로그인·사진 선택·문구 작성·저장 화면
- photo_services.py: Google Photos Picker와 Gemini API 호출
- album_storage.py: 사진/JSON 저장과 ZIP 백업
- GOOGLE_PHOTOS_SETUP.md: 이 설명서
- .streamlit/secrets.toml.example: 설정 예시 (실제 키 입력 금지)
- .gitignore: 실제 비밀 설정과 임시 파일 제외

기존 data와 images는 그대로 두세요. 수정 파일만 ZIP을 사용할 경우 압축을 풀어 동일한 경로에 덮어씁니다. ZIP 자체를 GitHub에 올리는 방식은 실행 코드에 반영되지 않습니다.

Streamlit Cloud의 진입 파일이 sennie/app.py이면 그대로 유지합니다. app.py가 저장소 루트에 있다면 새 Python 모듈도 그 옆에 둡니다. requirements.txt도 배포에서 읽히는 위치에 교체합니다.

## 2. Google Photos 연결 설정

1. https://console.cloud.google.com/ 에서 프로젝트를 생성하거나 선택합니다.
2. API 라이브러리에서 **Google Photos Picker API**를 검색하고 사용 설정합니다. Library API로 기존 사진 전체를 동기화하는 방식은 사용하지 않습니다.
3. Google Auth Platform에서 앱 이름, 지원 이메일과 연락처를 설정합니다.
4. Audience를 External / Testing으로 설정하고 **Test users에 본인의 Google 계정**을 추가합니다. 가족도 로그인하려면 해당 계정도 추가합니다. 실제 UI 이름은 변경될 수 있습니다.
5. Data Access에 다음 범위를 추가합니다.
   `https://www.googleapis.com/auth/photospicker.mediaitems.readonly`
6. Clients에서 OAuth 클라이언트를 **Web application** 유형으로 만듭니다.
7. Authorized redirect URIs에 배포한 앱의 주소를 정확히 추가합니다.
   예: `https://sennie-example.streamlit.app/`
   끝의 `/` 유무를 포함해 아래 GOOGLE_REDIRECT_URI와 동일해야 합니다.
8. Client ID와 Client Secret을 보관합니다. GitHub에 업로드하지 않습니다.

로컬 실행이라면 redirect URI를 `http://localhost:8501/`로 등록하고 설정합니다. Google 로그인 경고 화면이 나올 경우 개발 중인 본인 앱과 테스트 계정인지 확인합니다. 공개 배포는 Google의 OAuth 검증·데이터 정책을 별도로 충족해야 합니다.

## 3. Gemini API 설정

사진을 읽는 문구 생성에는 텍스트 전용 모델이 아닌 이미지 입력을 지원하는 모델이 필요합니다.

1. https://aistudio.google.com/ 에서 사용할 프로젝트의 Gemini API 키를 생성합니다.
2. **활성 결제 계정이 연결된 프로젝트의 키**를 사용합니다. Google Photos에서 받은 가족 사진을 일반 모델 학습/개선에 사용하지 않도록 무료 서비스의 키는 이 기능에 사용하지 않습니다.
3. 해당 프로젝트의 결제 상태와 데이터 처리 조건을 확인한 뒤 `GEMINI_PAID_SERVICE = true`로 설정합니다. 이 설정만 true로 바꾼다고 유료 프로젝트로 전환되지는 않습니다.
4. `GEMINI_MODEL`은 기본 `gemini-2.5-flash`입니다. 계정에서 사용할 수 있는 이미지 입력·JSON 출력을 지원하는 모델로 변경할 수 있습니다.

유료 API 호출 비용은 본인의 Google 계정에 청구됩니다. 자동 문구는 버튼을 누를 때만 생성하여 화면 새로고침 시 중복 호출되지 않게 했습니다. 무료 서비스는 개인/민감 정보를 제출하지 말라는 조건이 있고, 유료 서비스도 안전성 확인을 위한 제한적 보관이 있으므로 무보관이라고 간주하지 않습니다.

## 4. Streamlit Cloud Secrets 입력

Streamlit 앱 설정의 **Secrets**에 다음을 추가합니다. 기존 다른 키는 유지하고 같은 이름은 중복 작성하지 마세요.

```toml
ALBUM_ADMIN_PASSWORD = "본인만-아는-길고-고유한-비밀번호"
GOOGLE_CLIENT_ID = "본인의-client-id.apps.googleusercontent.com"
GOOGLE_CLIENT_SECRET = "본인의-client-secret"
GOOGLE_REDIRECT_URI = "https://본인의앱.streamlit.app/"
GEMINI_API_KEY = "본인의-Gemini-API-키"
GEMINI_MODEL = "gemini-2.5-flash"
GEMINI_PAID_SERVICE = true
```

로컬에서는 `.streamlit/secrets.toml`을 만들고 같은 값을 넣습니다. 실제 secrets.toml, API 키, Google 클라이언트 비밀키를 GitHub에 올리지 마세요. 관리자 비밀번호가 없으면 새 관리 기능은 비활성화되고 기존 앨범은 표시됩니다. 관리자 비밀번호는 편집 기능만 잠급니다. 가족 사진의 보기 권한을 보호하려면 배포 앱 자체도 비공개로 설정하세요.

Google 설정을 아직 하지 않아도 ALBUM_ADMIN_PASSWORD만 설정하면 PC 사진 업로드와 직접 문구 작성은 사용할 수 있습니다.

## 5. 사용 순서

1. 앨범 상단에서 가져오기 패널을 펼치고 관리 비밀번호를 입력합니다.
2. Google Photos 탭에서 사진 가져오기 동의를 선택하고 **① Google 로그인 준비**를 누릅니다.
3. **② Google 로그인**을 새 탭으로 열고 본인 계정으로 승인합니다. 원래 앨범 탭은 열어 둡니다.
4. 로그인 완료 탭에 안내가 나오면 **주소창의 전체 URL**을 복사합니다. 원래 탭의 '로그인 완료 탭의 전체 주소'에 붙여 넣고 **③ 로그인 연결 완료**를 누릅니다. 이 URL을 타인에게 공유하지 마세요.
5. **④ 사진 선택 준비 → ⑤ Google Photos 열고 사진 선택**을 누릅니다. 사진을 선택하고 Google Photos에서 완료합니다.
6. 원래 탭으로 돌아와 **⑥ 선택 완료 확인 → ⑦ 선택한 사진 가져오기**를 누릅니다.
7. 아래 '작성할 사진'에서 사진을 선택합니다. 촬영일은 한국 시간으로 변환하며 직접 수정할 수 있습니다.
8. 추가 정보에 장소나 가족 이야기를 적고 AI 전송에 동의한 뒤 **✨ 문구 자동 생성**을 누릅니다.
9. 제목과 설명을 확인·수정하고 Timeline 등록 여부를 선택한 뒤 저장합니다. 날짜에 맞춰 Picture와 Timeline에 반영됩니다.
10. 여러 사진은 하나씩 선택하여 문구를 생성하고 저장합니다. 같은 Google Photos ID는 중복 등록하지 않습니다.
11. **📦 현재 앨범 ZIP 만들기 → ⬇️ 다운로드**로 보관합니다.

Google Photos의 기존 앨범 전체나 새 사진을 백그라운드에서 무인 동기화하는 기능은 아닙니다. 한 번에 최대 20장 선택하며 동영상은 제외합니다. 가져온 사진은 긴 변 최대 2,048px의 JPEG 복사본이고 원본 Google Photos 사진은 변경하지 않습니다. 사진만으로 관계, 이름, 장소와 첫 경험을 단정하지 않도록 프롬프트를 설정했지만 결과를 확인하세요.

로그인 탭과 원래 앨범 탭이 서로 다른 Streamlit 세션이 되기 때문에 완료 주소를 원래 탭에 전달하는 방식을 사용합니다. 보안 확인값(state)과 PKCE를 검증하며 토큰은 현재 세션 메모리에만 보관하고 파일에는 저장하지 않습니다. 새로고침이나 앱 재시작 후 재로그인이 필요할 수 있습니다. Google의 권한 철회는 https://myaccount.google.com/connections 에서 합니다.

## 6. 저장과 백업: 반드시 확인

이 버전은 기존 JSON/사진 폴더 방식을 유지합니다. 개인 로컬 PC에서는 해당 폴더에 저장되지만 **Streamlit Cloud의 런타임 디스크는 영구 저장소가 아닙니다.** 새 기록은 앱 재시작·재배포로 사라질 수 있습니다.

- 저장 후 ZIP을 다운로드합니다. ZIP에는 현재 모든 사진과 JSON, 실행 코드가 포함되고 실제 키와 토큰은 제외됩니다.
- GitHub에서 계속 유지하려면 백업 ZIP을 풀어 새 `images/연도/pictures/import_....jpg`와 최신 `data/pictures.json`, `data/timeline.json`을 기존 경로에 올리고 commit합니다. 자동 GitHub 업로드는 없습니다.
- GitHub에는 가족 사진이 있으므로 비공개 저장소를 사용합니다. 웹 업로드 시 .gitignore만으로 사진이 제외되지는 않습니다.
- 잘못된 기록은 JSON에서 해당 source_id의 이벤트와 사진 정보를 지우고 연결된 images 파일도 삭제합니다. Google Photos 원본은 삭제되지 않습니다.
- 새로 가져온 사진/기록 삭제 후 다시 ZIP을 만들어 이전 백업을 대체하세요. 다운로드한 백업 파일의 삭제는 직접 관리해야 합니다.

재시작 후에도 자동 유지하려면 이후 S3·Supabase 등 영구 저장소에 연결하는 별도 작업이 필요합니다. 현재는 한 앱 프로세스/관리자가 사용하는 가족 앨범을 전제로 하며 여러 서버 간 동시 편집용 DB는 제공하지 않습니다.

## 7. 오류 대응

- `redirect_uri_mismatch`: Google에 등록한 redirect URI와 Secrets 값을 슬래시까지 일치시킵니다.
- 로그인 실패/403: 테스트 사용자 계정, Picker API 활성화, scope를 확인합니다.
- 사진 선택 오류/401: 로그인 준비부터 다시 진행합니다. 토큰이 만료될 수 있습니다.
- 다운로드 오류: 임시 사진 URL은 만료되므로 사진을 다시 선택합니다.
- AI 400/404: GEMINI_MODEL이 현재 계정에서 지원되는지 확인합니다.
- AI 429: 결제·할당량을 확인하고 잠시 뒤 다시 시도합니다.
- 저장 오류: 제목과 JSON 문법, 로컬 쓰기 권한을 확인합니다. 기존 JSON이 손상된 경우 덮어쓰지 않습니다.

## 8. 로컬 실행

Python 3.10 이상 환경에서 app.py가 있는 폴더로 이동합니다.

```bash
python -m pip install -r requirements.txt
python -m streamlit run app.py
```

## 참고한 공식 문서

- https://developers.google.com/photos/picker/guides/get-started-picker
- https://developers.google.com/photos/picker/guides/media-items
- https://developers.google.com/identity/protocols/oauth2/web-server
- https://developers.google.com/photos/support/api-policy
- https://ai.google.dev/gemini-api/docs/image-understanding
- https://ai.google.dev/gemini-api/terms

이 앱의 Google Photos API 데이터 이용은 Google API Services User Data Policy와 Limited Use requirements를 따릅니다. 선택한 사진은 앨범 저장·문구 생성에만 사용하며, AI 전송은 별도 동의를 받아 진행합니다. 모델 학습에 사용하지 않습니다.
