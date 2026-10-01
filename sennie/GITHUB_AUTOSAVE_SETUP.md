# 세니 성장앨범 GitHub 자동 저장

설정 후 앱에서 사진·문구를 저장, 수정, 삭제하면 `empasend-poop/Sennie` 저장소에도 반영합니다. 변경한 사진과 JSON을 하나의 커밋으로 묶습니다. 기존 보기·관리·삭제 비밀번호, Google Photos와 Gemini 설정은 유지하세요.

## 적용 전: 기존 기록 한 번만 정리

현재 앱에만 저장된 사진·문구가 있다면 먼저 앨범 ZIP을 다운로드하세요. 최신 `data/pictures.json`, `data/timeline.json`과 새 사진을 GitHub의 `sennie` 폴더에 반영하세요. 앱과 GitHub의 기록이 다르면 자동 저장은 기존 기록을 덮어쓰지 않고 중단합니다. 이후 저장부터 자동 반영합니다. GitHub에서 삭제한 사진과 앱에 남은 사진도 맞춰주세요.

## 1. GitHub 토큰 만들기

https://github.com/settings/personal-access-tokens 에서 Fine-grained token을 만듭니다.

1. Generate new token을 누릅니다.
2. Token name: `Sennie album autosave`
3. Resource owner: `empasend-poop`
4. Expiration: 본인이 관리할 만료 기간을 선택하세요. 만료 전 새 토큰으로 교체해야 합니다.
5. Repository access: **Only select repositories → Sennie만 선택**
6. Repository permissions: **Contents → Read and write**
7. Metadata는 기본 읽기 권한으로 유지합니다. Workflows나 계정 관리 권한은 필요하지 않습니다.
8. Generate token을 누르고 표시된 토큰을 복사합니다. 이 토큰을 채팅, GitHub 파일, 스크린샷으로 공유하지 마세요.

저장소의 보호 규칙이 직접 커밋을 막으면 자동 저장도 실패합니다. 가족용 개인 저장소의 사용 브랜치를 확인하세요. 공개 저장소에 저장하면 사진도 공개됩니다. 가족 사진은 Private 저장소에서 관리하세요.

## 2. Streamlit Secrets

기존 Secrets에 아래 항목을 추가합니다. 같은 키가 이미 있으면 값을 교체하고 중복 작성하지 않습니다.

```toml
GITHUB_SYNC_ENABLED = true
GITHUB_TOKEN = "여기에_방금_생성한_토큰"
GITHUB_REPO = "empasend-poop/Sennie"
GITHUB_BASE_PATH = "sennie"
```

`GITHUB_REPO`에는 https://, .git, /tree/main을 붙이지 않습니다.

브랜치는 기본 브랜치를 자동 조회합니다. Streamlit이 다른 브랜치에서 배포된다면 다음 항목을 그 배포 브랜치에 맞춰 추가하세요.

```toml
GITHUB_BRANCH = "main"
```

저장소에서 app.py가 `sennie/app.py`에 있으므로 GITHUB_BASE_PATH는 `sennie`입니다. 실제로 루트의 app.py를 실행한다면 `GITHUB_BASE_PATH = ""`로 바꿉니다.

## 3. 파일 반영

동봉한 Python 파일 4개를 GitHub의 기존 `sennie` 폴더에 덮어쓰거나 추가하고 Commit합니다.

- app.py
- album_storage.py
- photo_import.py
- github_sync.py (새 파일)

기존 photo_services.py, requirements.txt, 사진과 나머지 설정은 유지합니다. requests는 이전 버전에 포함되어 있어 추가 라이브러리가 필요하지 않습니다. 실제 비밀 설정을 파일에 넣지 마세요.

## 4. 사용

1. 앱을 열고 관리 기능을 엽니다.
2. **🔗 GitHub 연결 확인**을 누릅니다. 이 버튼은 읽기 연결만 확인하며 실제 변경을 커밋하지 않습니다.
3. 사진 한 장을 가져와 문구를 저장합니다.
4. **GitHub에도 자동 반영했습니다**라는 메시지가 나오면 저장소 첫 화면에서 `album: add photo and memory` 커밋을 확인합니다.
5. 문구 수정, Timeline 취소, 사진 삭제도 각각 하나의 커밋으로 반영합니다.

GitHub 파일 변경으로 Streamlit Cloud가 앱을 업데이트하거나 재시작할 수 있습니다. 저장된 사진·문구는 저장소에 있으므로 재배포 후에도 유지됩니다. 아직 저장하지 않은 사진 선택·초안·로그인 상태는 사라질 수 있어 재로그인/사진 재선택이 필요할 수 있습니다. 여러 장을 가져왔더라도 현재 저장 버튼은 사진 한 장씩 저장합니다.

## 실패 처리와 기록 보호

- 저장 전에 현재 GitHub JSON과 앱 JSON을 비교합니다. 공백·줄바꿈만 다른 JSON은 같은 것으로 처리합니다.
- 다른 기록이 발견되면 저장하지 않습니다. 앱 ZIP을 백업하고 GitHub와 비교해 어느 쪽이 최신인지 확인하세요. 기존 기록을 자동으로 합치거나 덮어쓰지는 않습니다.
- 관련 사진과 JSON을 blob/tree/commit으로 만든 뒤 브랜치 참조를 한 번만 업데이트합니다.
- 강제 push는 사용하지 않습니다. 다른 사람이 먼저 커밋하면 거부되고 기존 앱 파일도 이전 상태로 되돌립니다. 최신 앱으로 다시 열고 재시도하세요.
- 네트워크·권한 실패를 완료로 표시하지 않습니다. GitHub가 커밋을 수락한 직후 통신이 끊기는 경우에는 브랜치 참조를 조회해 확인합니다. 확인마저 실패하면 GitHub 커밋 내역을 직접 확인한 후 재시도하세요.
- 이미지 원본 Google Photos는 변경하지 않습니다. Picture 삭제는 저장소 사진 파일과 연결된 기록에 적용됩니다.
- ZIP 백업 기능은 계속 사용할 수 있습니다. 이제 정상 저장된 새 기록을 매번 수동 업로드할 필요는 없습니다.
- GitHub 삭제 커밋은 현재 브랜치에서 파일을 제거합니다. 과거 Git 기록이나 이전 ZIP 백업에는 사진이 남을 수 있습니다.
- 자동 반영 대상은 사진, pictures.json, timeline.json입니다. profile.json, 테마, 앨범 이름 등 다른 설정은 기존처럼 GitHub에서 직접 관리합니다.

## 오류 해결

- HTTP 401: 토큰 오타·만료 확인
- HTTP 403: Contents Read and write 권한·호출 제한 확인
- HTTP 404: Repository access에 Sennie가 포함됐는지, 저장소/브랜치/폴더 설정 확인
- HTTP 409/422: 다른 커밋과 충돌했거나 브랜치 보호 규칙 확인
- 앱과 GitHub 기록이 다름: 기존 앱 ZIP을 백업하고 최신 파일을 GitHub에 반영한 뒤 다시 배포

설정 전에는 기본적으로 새 변경을 막습니다. 자동 저장을 명시적으로 끄고 이전 방식으로 사용하려면 `GITHUB_SYNC_ENABLED = false`로 바꿉니다. 이 경우에만 앱 로컬 저장으로 동작하며 ZIP 백업과 수동 반영이 다시 필요합니다.

## 검증 범위

실제 토큰을 받지 않았으므로 본인 저장소에 실제 커밋을 만들지는 않았습니다. 모의 GitHub API로 원자적 저장, 충돌 거부, 실패 시 복구, 수정·삭제 동기화를 검증한 뒤 제공했습니다. 실제 권한·배포 연동은 설정 후 첫 저장으로 확인해야 합니다.

공식 문서:
- https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/managing-your-personal-access-tokens
- https://docs.github.com/en/rest/git/trees
- https://docs.github.com/en/rest/git/commits
- https://docs.github.com/en/rest/git/refs
