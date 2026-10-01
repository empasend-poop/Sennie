"""Import panel for the existing Streamlit album."""
import hashlib
import hmac
import re
import secrets
import time
from datetime import date, datetime
from io import BytesIO

import requests
import streamlit as st
from PIL import Image, UnidentifiedImageError

from photo_services import (ServiceError, login_url, exchange_url, picker_call,
                            list_photos, photo_bytes, photo_date, normalize_photo, caption, KST)
from album_storage import save_photo, export_album


def setting(name, default=''):
    try:
        return st.secrets.get(name, default)
    except (FileNotFoundError, st.errors.StreamlitSecretNotFoundError):
        return default


def run_import(base):
    with st.expander('📷 사진 가져오기 · ✨ AI 문구 작성', expanded=False):
        st.caption('Google Photos에서 선택한 사진 또는 PC 사진을 가져와 문구를 작성합니다.')
        password = str(setting('ALBUM_ADMIN_PASSWORD'))
        if not password:
            st.info('이 기능을 사용하려면 Secrets에 ALBUM_ADMIN_PASSWORD를 설정해주세요. 설정 방법은 GOOGLE_PHOTOS_SETUP.md에 있습니다.')
            return
        if not st.session_state.get('album_editor'):
            entered = st.text_input('앨범 관리 비밀번호', type='password', key='album_password')
            if st.button('관리 기능 열기'):
                if hmac.compare_digest(entered, password):
                    st.session_state.album_editor = True
                    st.rerun()
                else:
                    st.error('비밀번호를 확인해주세요.')
            return
        if st.button('관리 기능 잠그기'):
            for key in list(st.session_state):
                if key.startswith(('gp_', 'draft_', 'album_')) or key == 'drafts':
                    del st.session_state[key]
            st.rerun()
        st.warning('저장 후 반드시 아래에서 앨범 ZIP을 내려받아 보관하세요. Streamlit Cloud의 파일은 재시작·재배포 후 사라질 수 있습니다.')
        st.caption('앨범의 보기 권한은 별도입니다. 가족 사진을 보호하려면 배포 앱도 비공개로 설정하세요.')
        google_tab, upload_tab = st.tabs(['Google Photos', 'PC 사진 업로드'])
        with google_tab:
            google_panel()
        with upload_tab:
            uploaded = st.file_uploader('JPG · PNG · WebP 사진', type=['jpg', 'jpeg', 'png', 'webp'])
            if uploaded and st.button('이 사진으로 기록 작성'):
                try:
                    raw = uploaded.getvalue()
                    if len(raw) > 20 * 1024 * 1024:
                        raise ValueError('사진은 20MB 이하로 업로드해주세요.')
                    st.session_state['drafts'] = [{'id': 'upload:' + hashlib.sha256(raw).hexdigest(),
                        'bytes': normalize_photo(raw), 'date': datetime.now(KST).date(), 'name': uploaded.name}]
                    st.rerun()
                except (OSError, ValueError, Image.DecompressionBombError):
                    st.error('사진을 읽을 수 없습니다. 20MB 이하의 JPG·PNG·WebP 파일을 확인해주세요.')
        drafts = st.session_state.get('drafts', [])
        if drafts:
            st.markdown('#### 사진별 기록 작성')
            selected = st.selectbox('작성할 사진', range(len(drafts)), format_func=lambda i: drafts[i]['name'])
            draft = drafts[selected]
            key = hashlib.sha256(draft['id'].encode()).hexdigest()[:20]
            left, right = st.columns([1, 2])
            with left:
                st.image(Image.open(BytesIO(draft['bytes'])), width=250)
            with right:
                when = st.date_input('기록 날짜 (촬영일을 확인해주세요)', value=draft['date'], key=f'draft_date_{key}')
                context = st.text_input('추가 정보 (선택)', placeholder='예: 가족과 서울숲에 다녀온 날', key=f'draft_context_{key}')
                consent = st.checkbox('이 사진을 Gemini로 전송하여 앨범 문구를 만드는 데 동의합니다.', key=f'draft_consent_{key}')
                api_key = str(setting('GEMINI_API_KEY'))
                paid = setting('GEMINI_PAID_SERVICE', False) is True
                if not api_key or not paid:
                    st.caption('AI 문구 기능: 유료 Gemini API와 GEMINI_PAID_SERVICE = true 설정이 필요합니다. 직접 작성은 가능합니다.')
                if st.button('✨ 이 사진의 문구 자동 생성', key=f'draft_ai_{key}', disabled=not(consent and api_key and paid)):
                    try:
                        model = str(setting('GEMINI_MODEL', 'gemini-2.5-flash'))

                        if not re.fullmatch(r'[A-Za-z0-9._-]+', model):
                            raise ServiceError('GEMINI_MODEL 설정을 확인해주세요.')

                        with st.spinner('사진을 보고 문구를 작성하고 있어요…'):
                            result = caption(
                                draft['bytes'],
                                api_key,
                                model,
                                context,
                            )

                        st.session_state[f'draft_title_{key}'] = result['title']
                        st.session_state[f'draft_description_{key}'] = result['description']

                    except ServiceError as exc:
                        st.error(f"AI 요청 실패: {exc}")

                    except requests.RequestException:
                        st.error("Gemini 연결에 실패했습니다. 잠시 후 다시 시도해주세요.")
                      
                title = st.text_input('제목', value='소중한 하루 🩷', key=f'draft_title_{key}', max_chars=120)
                description = st.text_area('설명 (AI 문구를 자유롭게 고쳐주세요)', key=f'draft_description_{key}', max_chars=4000)
                timeline = st.checkbox('Timeline에도 함께 등록', value=True, key=f'draft_timeline_{key}')
                if st.button('💾 이 사진과 문구 저장', key=f'draft_save_{key}'):
                    try:
                        added = save_photo(base, draft['bytes'], draft['id'], when, title, description, timeline)
                        st.session_state['album_notice'] = '저장했습니다. 앨범 ZIP을 내려받아 보관해주세요.' if added else '이미 가져온 사진입니다. 중복 저장하지 않았습니다.'
                        st.session_state.pop('album_zip', None)
                        st.rerun()
                    except (ValueError, OSError):
                        st.error('저장하지 못했습니다. 제목, 기존 JSON 형식과 파일 쓰기 권한을 확인해주세요.')
        if st.session_state.get('album_notice'):
            st.success(st.session_state['album_notice'])
        if st.button('📦 현재 앨범 ZIP 만들기 (사진·문구 포함)'):
            st.session_state['album_zip'] = export_album(base)
        if st.session_state.get('album_zip'):
            st.download_button('⬇️ 앨범 ZIP 다운로드', st.session_state['album_zip'],
                               file_name='Sennie-album-backup.zip', mime='application/zip')
            st.caption('다운로드한 ZIP에는 사진과 기록이 들어 있습니다. API 키와 실제 secrets.toml은 제외됩니다.')


def google_panel():
    client_id, client_secret, redirect = [str(setting(k)) for k in
        ('GOOGLE_CLIENT_ID', 'GOOGLE_CLIENT_SECRET', 'GOOGLE_REDIRECT_URI')]
    if not all((client_id, client_secret, redirect)):
        st.info('Google Photos 연결 설정이 필요합니다. GOOGLE_PHOTOS_SETUP.md를 따라 Secrets를 입력해주세요.')
        return
    st.caption('선택한 사진만 앱으로 가져옵니다. 최대 20장씩, 긴 변은 최대 2,048px로 가져오며 동영상은 제외합니다. 새 사진을 가져올 때마다 다시 선택해주세요.')
    consent = st.checkbox('Google Photos에서 선택한 사진을 이 성장앨범으로 가져와 저장하는 데 동의합니다.', key='gp_consent')
    if st.button('① Google 로그인 준비', disabled=not consent):
        st.session_state['gp_state'] = secrets.token_urlsafe(32)
        st.session_state['gp_verifier'] = secrets.token_urlsafe(64)
        st.session_state['gp_started'] = time.time()
        st.session_state['gp_login_url'] = login_url(client_id, redirect, st.session_state['gp_state'], st.session_state['gp_verifier'])
    if st.session_state.get('gp_login_url'):
        st.link_button('② Google 로그인 (새 탭)', st.session_state['gp_login_url'])
        st.caption('새 탭에서 로그인 후 주소창의 전체 URL을 복사하여 원래 탭의 아래 칸에 붙여 넣으세요. 로그인 완료 탭은 닫아도 됩니다.')
        callback = st.text_input('로그인 완료 탭의 전체 주소', type='password', key='gp_callback')
        if st.button('③ 로그인 연결 완료'):
            try:
                if time.time() - st.session_state['gp_started'] > 600:
                    raise ServiceError('로그인 준비 후 10분이 지났습니다. 다시 준비해주세요.')
                token = exchange_url(callback, redirect, st.session_state['gp_state'], st.session_state['gp_verifier'], client_id, client_secret)
                st.session_state['gp_token'] = token
                for k in ['gp_login_url', 'gp_state', 'gp_verifier', 'gp_started', 'gp_session', 'gp_items']:
                    st.session_state.pop(k, None)
                st.rerun()
            except (ServiceError, requests.RequestException):
                st.error('로그인 연결에 실패했습니다. 로그인 준비를 다시 누르고 완료 주소를 확인해주세요.')
    token = st.session_state.get('gp_token')
    if not token:
        return
    st.success('Google Photos에 연결되었습니다.')
    if st.button('④ Google Photos 사진 선택 준비', disabled=not consent):
        try:
            session = picker_call(token, 'POST', '/sessions', json={'pickingConfig': {'maxItemCount': '20'}})
            st.session_state['gp_session'] = session
            st.session_state.pop('gp_items', None)
        except (ServiceError, requests.RequestException):
            st.error('사진 선택을 시작하지 못했습니다. 토큰이 만료되었다면 다시 로그인해주세요.')
    session = st.session_state.get('gp_session')
    if session:
        st.link_button('⑤ Google Photos 열고 사진 선택', session['pickerUri'])
        st.caption('Google Photos에서 사진 선택 후 완료를 누르고 이 탭으로 돌아오세요.')
        if st.button('⑥ 선택 완료 확인'):
            try:
                latest = picker_call(token, 'GET', '/sessions/' + session['id'])
                if latest.get('mediaItemsSet'):
                    st.session_state['gp_items'] = list_photos(token, session['id'])
                    st.success(f"사진 {len(st.session_state['gp_items'])}장을 선택했습니다.")
                else:
                    st.info('아직 선택이 완료되지 않았습니다. Google Photos에서 완료를 눌러주세요.')
            except (ServiceError, requests.RequestException):
                st.error('선택 확인에 실패했습니다. 로그인을 다시 하거나 사진을 다시 선택해주세요.')
        items = st.session_state.get('gp_items', [])
        if items and st.button('⑦ 선택한 사진 가져오기', disabled=not consent):
            drafts, failures = [], 0
            with st.spinner('선택한 사진을 가져오고 있어요…'):
                for item in items[:20]:
                    try:
                        drafts.append({'id': 'google:' + item['id'], 'bytes': photo_bytes(token, item),
                            'date': photo_date(item), 'name': item.get('mediaFile', {}).get('filename', '사진')})
                    except (ServiceError, requests.RequestException, KeyError, OSError, ValueError):
                        failures += 1
            if drafts:
                st.session_state['drafts'] = drafts
            if failures:
                st.warning(f'{failures}장을 가져오지 못했습니다. 다시 선택해주세요.')
            if drafts:
                st.success(f'{len(drafts)}장 가져왔습니다. 아래에서 사진별 문구를 작성하고 저장하세요.')
    if st.button('Google 연결 정보 지우기'):
        for k in list(st.session_state):
            if k.startswith('gp_'):
                del st.session_state[k]
        st.rerun()
    st.caption('토큰은 현재 접속의 메모리에만 보관합니다. 새로고침·세션 종료 시 재로그인이 필요할 수 있습니다. 계정 권한 철회는 Google 계정의 연결된 앱에서 할 수 있습니다.')
