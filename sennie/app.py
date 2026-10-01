"""사진 폴더와 JSON으로 관리하는 우리 아이 성장앨범."""
import base64
from io import BytesIO
from datetime import date, datetime, timedelta, timezone
from html import escape
import json
import hashlib
import hmac
from pathlib import Path

import streamlit as st
from PIL import Image, ImageOps, UnidentifiedImageError

BASE = Path(__file__).resolve().parent
EXTENSIONS = {'.jpg', '.jpeg', '.png', '.webp', '.bmp'}
st.set_page_config(page_title='우리 아이 성장앨범', page_icon='🩷', layout='wide')
# Google 로그인 완료 탭: 원래 탭으로 주소를 전달합니다.
if 'code' in st.query_params or 'error' in st.query_params:
    st.title('Google 로그인 응답')
    st.info('이 탭 주소창의 전체 URL을 복사해 원래 앨범 탭의 로그인 완료 주소 칸에 붙여 넣으세요. 이 주소는 다른 사람과 공유하지 마세요.')
    st.stop()

# 앨범 보기 비밀번호: 인증 전에는 사진과 기록을 읽거나 표시하지 않습니다.
try:
    view_password = str(st.secrets.get('ALBUM_VIEW_PASSWORD', ''))
except (FileNotFoundError, st.errors.StreamlitSecretNotFoundError):
    view_password = ''

if not view_password:
    st.title('🩷 성장앨범')
    st.info('앨범 비밀번호 설정이 필요합니다. 운영자는 Streamlit Secrets에 ALBUM_VIEW_PASSWORD를 추가해주세요.')
    st.stop()

password_version = hashlib.sha256(view_password.encode()).hexdigest()
if not hmac.compare_digest(str(st.session_state.get('album_view_auth', '')), password_version):
    st.title('🩷 우리 가족 성장앨범')
    st.caption('앨범 비밀번호를 입력하면 사진과 추억을 볼 수 있어요.')

    def check_album_password():
        entered = st.session_state.pop('album_view_input', '')
        if hmac.compare_digest(entered, view_password):
            st.session_state['album_view_auth'] = password_version
            st.session_state.pop('album_view_error', None)
        else:
            st.session_state['album_view_error'] = True

    with st.form('album_view_login'):
        st.text_input('앨범 비밀번호', type='password', key='album_view_input')
        st.form_submit_button('앨범 열기 🩷', on_click=check_album_password)
    if st.session_state.get('album_view_error'):
        st.error('비밀번호를 확인해주세요.')
    st.stop()

if st.sidebar.button('🔒 앨범 잠그기', key='lock_album_view', use_container_width=True):
    st.session_state.clear()
    st.rerun()

from photo_import import run_import
run_import(BASE)

st.markdown('''<style>

/* 메인과 사이드바 */
.stApp,
section[data-testid="stSidebar"] {
    background: #f8e5f2 !important;
    color: #2e4c6b;
}

/* 상단 제목 카드 */
.hero {
    background: #f8e5f2 !important;
    border-color: #eca2d3 !important;
}

/* 이벤트 수 / 사진 수 카드 */
[data-testid="stMetric"] {
    background: #f8e5f2 !important;
    border-color: #eca2d3 !important;
}

/* Timeline 설명 카드 */
.event {
    background: #f8e5f2 !important;
    border-left-color: #eca2d3 !important;
}

/* 제목과 주요 숫자 */
h1, h2, h3,
[data-testid="stMetricLabel"],
[data-testid="stMetricValue"] {
    color: #2e4c6b !important;
}

/* 카드 설명 */
.hero p,
.event p {
    color: #2e4c6b !important;
}

</style>''', unsafe_allow_html=True)


def read_object(name, fallback):
    try:
        value = json.loads((BASE / 'data' / name).read_text(encoding='utf-8-sig'))
        if not isinstance(value, dict):
            raise ValueError('JSON 최상위 값은 객체여야 합니다.')
        return value
    except (OSError, ValueError) as exc:
        st.warning(f'{name}을 읽을 수 없어 기본값으로 표시합니다: {exc}')
        return fallback


def local_image(value):
    if not isinstance(value, str) or not value.strip():
        return None
    path = (BASE / value).resolve()
    if not path.is_relative_to(BASE) or not path.is_file():
        return None
    return path


def pictures(year):
    folder = BASE / 'images' / str(year) / 'pictures'
    return sorted((p for p in folder.glob('*') if p.is_file() and p.suffix.lower() in EXTENSIONS), key=lambda p: p.name.casefold())


def show_image(path, thumbnail=False):
    if path is None:
        st.info("📷 여기에 소중한 사진을 넣어주세요.")
        return

    try:
        with Image.open(path) as source:
            image = ImageOps.exif_transpose(source).convert("RGB")

            # 모든 사진을 동일한 정사각형으로 맞추기
            image = ImageOps.fit(
                image,
                (200, 200),
                method=Image.Resampling.LANCZOS,
                centering=(0.5, 0.5),
            )

            # 컬럼 너비보다 커지지 않도록 표시
            st.image(image, width=300)

    except (OSError, ValueError, UnidentifiedImageError):
        st.warning(
            f"{path.name}: 사진을 읽을 수 없습니다. "
            "JPG 또는 PNG로 다시 저장해주세요."
        )


profile = read_object('profile.json', {})
timeline = read_object('timeline.json', {})
metadata = read_object('pictures.json', {})
try:
    birthday = date.fromisoformat(str(profile.get('birth_date', '2022-03-10')))
except ValueError:
    st.warning('생년월일 형식은 YYYY-MM-DD입니다. 기본 생년 2022년을 사용합니다.')
    birthday = date(2022, 3, 10)
folder_years = {int(p.name) for p in (BASE / 'images').glob('*') if p.is_dir() and p.name.isdigit() and len(p.name) == 4}
current_year_kst = datetime.now(timezone(timedelta(hours=9))).year
years = sorted(set(range(birthday.year, max(birthday.year, current_year_kst) + 1)) | folder_years | {int(k) for k in timeline if k.isdigit() and len(k) == 4})
# 출생 전 연애·결혼 기록도 표시합니다.
events = {}
for year in years:
    raw = timeline.get(str(year), [])
    if not isinstance(raw, list):
        st.warning(f'{year}년 이벤트는 JSON 배열이어야 합니다.')
        raw = []
    events[year] = sorted([e for e in raw if isinstance(e, dict)], key=lambda e: str(e.get('date', '')))


def year_label(year):
    return f'{year} · 가족의 추억' if year < birthday.year else f'{year} · {year - birthday.year + 1}살'


FAMILY_GROUP = '2020~2021'
combined_years = [year for year in years if year in (2020, 2021)]
periods = ([FAMILY_GROUP] if combined_years else []) + [year for year in years if year not in (2020, 2021)]


def period_label(period):
    return '2020~2021 · 연애&결혼 🩷' if period == FAMILY_GROUP else year_label(period)


def period_years(period):
    return combined_years if period == FAMILY_GROUP else [period]


# 이전 선택값을 새 그룹으로 옮깁니다.
for state_key in ('timeline_year', 'picture_year'):
    if st.session_state.get(state_key) in (2020, 2021):
        st.session_state[state_key] = FAMILY_GROUP


# 나이별 바로가기: Timeline과 Picture의 연도를 함께 변경
def jump_to_year(year):
    st.session_state["timeline_year"] = year
    st.session_state["picture_year"] = year


with st.sidebar:
    st.title("🩷 Growth Album")

    # 대표 사진: 앨범 표지와 같은 사진 사용
    cover_path = local_image(
        str(
            profile.get(
                "cover_image",
                "images/profile/main.jpg",
            )
        )
    )
    show_image(cover_path)

    st.subheader(
        str(profile.get("name", "우리 아기"))
    )
    st.caption(
        f"🎂 생년월일 · {birthday.isoformat()}"
    )

    st.divider()
    st.markdown("### 🌷 추억 바로가기")
    st.caption("버튼을 누르면 두 탭의 연도가 함께 바뀝니다.")

    # 아이가 태어나기 전 가족의 추억
    family_years = [
        year for year in years
        if year < birthday.year
    ]

    if combined_years:
        st.button(
            period_label(FAMILY_GROUP),
            key='family_jump_combined',
            on_click=jump_to_year,
            args=(FAMILY_GROUP,),
            use_container_width=True,
        )

    for year in family_years:
        if year in (2020, 2021):
            continue
        st.button(
            year_label(year),
            key=f"family_jump_{year}",
            on_click=jump_to_year,
            args=(year,),
            use_container_width=True,
        )

    # 아이 성장 기록: 한 줄에 버튼 두 개
    growth_years = [
        year for year in years
        if year >= birthday.year
    ]

    for start in range(0, len(growth_years), 2):
        columns = st.columns(2)

        for column, year in zip(
            columns,
            growth_years[start:start + 2],
        ):
            age = year - birthday.year + 1

            with column:
                st.button(
                    f"🌱 {age}살",
                    key=f"growth_jump_{year}",
                    help=f"{year}년 추억 보기",
                    on_click=jump_to_year,
                    args=(year,),
                    use_container_width=True,
                )

    st.divider()

    if st.button(
        "🔄 사진·기록 새로고침",
        use_container_width=True,
    ):
        st.rerun()

    st.caption(
        "사진이나 JSON 수정 후 "
        "새로고침 버튼을 눌러주세요."
    )
    
st.markdown(f'<div class="hero"><div class="kicker">OUR LITTLE STORY</div><h1>🩷 {escape(str(profile.get("name", "우리 아기")))}의 성장앨범</h1><p>{escape(str(profile.get("message", "매일매일 자라나는 소중한 순간들 ❤️")))}</p></div>', unsafe_allow_html=True)

# 한국 시간: UTC + 9시간
KST = timezone(timedelta(hours=9))

# 출생 시각: 2022년 1월 1일 오전 2시 34분
BIRTH_DATETIME = datetime(
    2022, 1, 1, 2, 34, 0,
    tzinfo=KST,
)


st.markdown("""
<style>
.album-stats {
    display: grid;
    grid-template-columns: minmax(0, 1.6fr) minmax(0, 1fr) minmax(0, 1fr);
    gap: 18px;
    margin: 24px 0 30px;
}
.album-stat {
    min-width: 0;
    padding: 24px 14px;
    background: #f8e5f2;
    border: 1px solid #e6bdd8;
    border-radius: 18px;
    text-align: center;
    color: #2e4c6b;
    box-shadow: 0 3px 12px rgba(120, 70, 105, 0.04);
}
.album-stat-label {
    font-size: 16px;
    font-weight: 500;
    line-height: 24px;
    margin-bottom: 14px;
}
.album-stat-value {
    font-size: 20px;
    font-weight: 700;
    line-height: 32px;
    font-variant-numeric: tabular-nums;
    white-space: nowrap;
}
.album-stat-note {
    font-size: 12px;
    line-height: 20px;
    color: #7e8199;
    margin-top: 10px;
}
@media (max-width: 1050px) {
    .album-stats { grid-template-columns: minmax(0, 1fr); gap: 12px; }
}
@media (max-width: 380px) {
    .album-stat-value { font-size: 15px; }
    .album-stat { padding: 20px 8px; }
}
</style>
""", unsafe_allow_html=True)


@st.fragment(run_every="1s")
def show_growth_clock(event_count, photo_count):
    now = datetime.now(KST)
    total_seconds = max(0, int((now - BIRTH_DATETIME).total_seconds()))
    days, remainder = divmod(total_seconds, 86400)
    hours, remainder = divmod(remainder, 3600)
    minutes, seconds = divmod(remainder, 60)
    clock = f"{days:,}일 {hours:02d}시간 {minutes:02d}분 {seconds:02d}초"
    st.markdown(
        '<div class="album-stats">'
        '<div class="album-stat">'
        '<div class="album-stat-label">함께한 시간 ❤️</div>'
        f'<div class="album-stat-value">{clock}</div>'
        '<div class="album-stat-note">2022.01.01 오전 02:34부터</div>'
        '</div>'
        '<div class="album-stat">'
        '<div class="album-stat-label">Timeline 이벤트</div>'
        f'<div class="album-stat-value">{event_count:,}</div>'
        '<div class="album-stat-note">기록한 소중한 순간</div>'
        '</div>'
        '<div class="album-stat">'
        '<div class="album-stat-label">Picture 사진</div>'
        f'<div class="album-stat-value">{photo_count:,}</div>'
        '<div class="album-stat-note">사진으로 남긴 추억</div>'
        '</div></div>',
        unsafe_allow_html=True,
    )


show_growth_clock(
    sum(len(v) for v in events.values()),
    sum(len(pictures(y)) for y in years),
)

# ==================================================
# 메인 화면: 우리 가족의 성장 타임라인
# ==================================================

st.markdown(
    """
    <style>
    .family-timeline {
        position: relative;
        max-width: 950px;
        margin: 25px auto 40px;
        padding: 10px 0;
    }

    /* 가운데 세로선 */
    .family-timeline::before {
        content: "";
        position: absolute;
        top: 0;
        bottom: 0;
        left: 50%;
        width: 3px;
        transform: translateX(-50%);
        background: #eca2d3;
        border-radius: 3px;
    }

    .family-row {
        position: relative;
        display: flex;
        margin-bottom: 28px;
    }

    .family-row.left {
        justify-content: flex-start;
    }

    .family-row.right {
        justify-content: flex-end;
    }

    /* 세로선 위의 동그라미 */
    .family-dot {
        position: absolute;
        left: 50%;
        top: 24px;
        width: 16px;
        height: 16px;
        transform: translateX(-50%);
        background: var(--accent);
        border: 4px solid #f8e5f2;
        border-radius: 50%;
        box-sizing: content-box;
        z-index: 1;
    }

    .family-card {
        position: relative;
        width: 44%;
        padding: 18px;
        background: #f8e5f2;
        border: 1px solid var(--accent);
        border-radius: 18px;
        box-sizing: border-box;
    }

    /* 카드와 중앙선을 연결 */
    .family-card::after {
        content: "";
        position: absolute;
        top: 35px;
        width: 14%;
        height: 2px;
        background: var(--accent);
    }

    .family-row.left .family-card::after {
        left: 100%;
    }

    .family-row.right .family-card::after {
        right: 100%;
    }

    .family-year {
        color: #2e4c6b;
        font-size: 21px;
        font-weight: 800;
        margin-bottom: 12px;
    }

    .family-photo {
        display: block;
        width: 100%;
        max-width: 240px;
        aspect-ratio: 1 / 1;
        object-fit: cover;
        border-radius: 14px;
        margin-bottom: 12px;
    }

    .family-placeholder {
        padding: 30px 12px;
        border: 1px dashed var(--accent);
        border-radius: 14px;
        color: #68788a;
        text-align: center;
        margin-bottom: 12px;
    }

    .family-title {
        color: #2e4c6b;
        font-size: 17px;
        font-weight: 700;
        margin-bottom: 6px;
    }

    .family-description {
        color: #52677b;
        font-size: 14px;
        line-height: 1.7;
        white-space: pre-wrap;
        overflow-wrap: anywhere;
    }

    /* 휴대폰에서는 한쪽으로 정렬 */
    @media (max-width: 640px) {
        .family-timeline::before {
            left: 12px;
        }

        .family-row.left,
        .family-row.right {
            justify-content: flex-end;
        }

        .family-dot {
            left: 12px;
        }

        .family-card {
            width: calc(100% - 42px);
        }

        .family-row .family-card::after {
            left: auto;
            right: 100%;
            width: 18px;
        }
    }
    </style>
    """,
    unsafe_allow_html=True,
)


def timeline_photo_html(event):
    """대표 사진을 작은 이미지로 변환해 타임라인에 표시."""
    values = event.get("images")

    if not isinstance(values, list) or not values:
        values = [event.get("image", "")]

    path = local_image(values[0])

    if path is None:
        return (
            '<div class="family-placeholder">'
            '📷 추억의 사진을 넣어주세요'
            '</div>'
        )

    try:
        with Image.open(path) as source:
            image = ImageOps.exif_transpose(source).convert("RGB")

            image = ImageOps.fit(
                image,
                (480, 480),
                method=Image.Resampling.LANCZOS,
            )

            buffer = BytesIO()
            image.save(buffer, format="JPEG", quality=85)

        encoded = base64.b64encode(
            buffer.getvalue()
        ).decode("ascii")

        return (
            '<img class="family-photo" '
            f'src="data:image/jpeg;base64,{encoded}" '
            'alt="우리 가족의 추억">'
        )

    except (OSError, ValueError, UnidentifiedImageError):
        return (
            '<div class="family-placeholder">'
            '📷 사진을 확인해주세요'
            '</div>'
        )


with st.expander("🩷 우리 가족의 이야기 · 타임라인", expanded=False):
    st.caption("연애부터 결혼, 그리고 함께 자라는 소중한 시간")

    colors = [
        "#c68aaa",
        "#87adc4",
        "#a1b780",
        "#d4ad72",
        "#aa95c4",
    ]

    cards = []

    for index, period in enumerate(periods):
        side = "left" if index % 2 == 0 else "right"
        accent = colors[index % len(colors)]
        label = escape(period_label(period))
        content = []

        # 2020·2021년 대표 기록을 카드 하나에 함께 표시합니다.
        for year in period_years(period):
            year_events = events.get(year, [])
            event = year_events[0] if year_events else {}
            title = escape(str(event.get("title", "우리의 소중한 추억")))
            description = escape(
                str(event.get("description", "이 해의 이야기를 기록해주세요."))
            )
            photo = timeline_photo_html(event)
            if period == FAMILY_GROUP:
                content.append(
                    '<div style="margin-bottom:20px;">'
                    f'<div class="family-title">{year}년</div>'
                    f'{photo}'
                    f'<div class="family-title">{title}</div>'
                    f'<div class="family-description">{description}</div>'
                    '</div>'
                )
            else:
                content.append(
                    f'{photo}'
                    f'<div class="family-title">{title}</div>'
                    f'<div class="family-description">{description}</div>'
                )

        cards.append(
            f'<div class="family-row {side}" '
            f'style="--accent:{accent};">'
            '<div class="family-dot"></div>'
            '<div class="family-card">'
            f'<div class="family-year">{label}</div>'
            + "".join(content)
            + '</div></div>'
        )

    st.markdown(
        '<div class="family-timeline">'
        + "".join(cards)
        + "</div>",
        unsafe_allow_html=True,
    )

from album_storage import remove_timeline_event, delete_picture, edit_caption


def can_delete_cards():
    return bool(st.session_state.get('album_editor'))


@st.dialog('제목·설명 수정')
def edit_card_text(kind, target, year=None):
    if not can_delete_cards():
        st.error('관리 기능을 먼저 열어주세요.')
        return
    if kind == 'timeline':
        title = str(target.get('title', ''))
        description = str(target.get('description', ''))
    else:
        caption_text = str(metadata.get(target, {}).get('caption', Path(target).stem))
        title, separator, description = caption_text.partition('\n')
        for entries in events.values():
            matches = [event for event in entries if target in event.get('images', [event.get('image', '')])]
            if matches:
                title = str(matches[0].get('title', title))
                description = str(matches[0].get('description', description))
                break
    identity = hashlib.sha256((kind + str(year) + json.dumps(target, ensure_ascii=False, sort_keys=True)).encode()).hexdigest()[:16]
    st.caption('사진과 날짜는 그대로 두고, 같은 사진을 사용하는 Timeline·Picture의 문구를 함께 수정합니다.')
    new_title = st.text_input('제목', value=title, max_chars=120, key=f'edit_title_{identity}')
    new_description = st.text_area('설명', value=description, height=200, max_chars=4000, key=f'edit_description_{identity}')
    if st.button('수정 저장', type='primary', key=f'edit_save_{identity}'):
        if not can_delete_cards():
            st.error('관리 기능을 먼저 열어주세요.')
            return
        try:
            edit_caption(BASE, kind, target, new_title, new_description, year)
            st.session_state.pop('album_zip', None)
            st.session_state['card_edit_notice'] = True
            st.rerun()
        except (ValueError, OSError) as exc:
            st.error(str(exc) if isinstance(exc, ValueError) else '저장하지 못했습니다. 파일 쓰기 권한을 확인해주세요.')


if st.session_state.pop('card_edit_notice', False):
    st.success('문구를 수정했습니다. 최신 앨범 ZIP을 백업하고 GitHub에도 반영해주세요.')


@st.dialog('기록 삭제')
def confirm_card_delete(kind, target, year=None):
    # Password validation is repeated for every deletion.
    if not can_delete_cards():
        st.error('관리 기능을 먼저 열어주세요.')
        return
    delete_password = str(st.secrets.get('ALBUM_DELETE_PASSWORD', ''))
    if not delete_password:
        st.info('삭제 비밀번호가 설정되지 않았습니다. Secrets에 ALBUM_DELETE_PASSWORD를 추가해주세요.')
        return
    if kind == 'timeline':
        st.write(str(target.get('title', '선택한 기록')))
        st.caption('Timeline 기록만 삭제합니다. 사진 파일과 Picture 기록은 유지됩니다.')
    else:
        st.write(Path(target).name)
        st.caption('앱의 사진 파일과 Picture 문구를 삭제합니다. 같은 사진을 쓰는 Timeline 기록도 함께 제거합니다. Google Photos 원본은 유지됩니다.')
    st.caption('아직 백업하지 않았다면 이 창을 닫고 앨범 ZIP부터 다운로드해주세요.')
    entered = st.text_input('삭제 비밀번호', type='password', key='card_delete_password')
    submitted = st.button('삭제하기', type='primary', key='card_delete_submit')
    if submitted:
        if not hmac.compare_digest(entered, delete_password):
            st.error('삭제 비밀번호가 맞지 않습니다.')
            return
        try:
            if kind == 'timeline':
                if not remove_timeline_event(BASE, year, target):
                    st.info('이미 삭제되었거나 변경된 기록입니다. 창을 닫고 목록을 다시 확인해주세요.')
                    return
            else:
                delete_picture(BASE, target)
            st.session_state.pop('album_zip', None)
            st.session_state.pop('card_delete_password', None)
            st.session_state['card_delete_notice'] = '삭제했습니다. 변경된 앨범 ZIP을 다운로드하고 GitHub에도 반영해주세요.'
            st.rerun()
        except (ValueError, OSError):
            st.error('삭제하지 못했습니다. 파일 상태와 JSON 형식을 확인해주세요.')


if st.session_state.pop('card_delete_notice', None):
    st.success('삭제했습니다. 변경된 앨범 ZIP을 다운로드하고 GitHub에도 반영해주세요.')

timeline_tab, picture_tab = st.tabs(['🌱 Timeline', '📸 Picture'])
with timeline_tab:
    selected = st.selectbox('Timeline 연도', ['전체'] + periods, format_func=lambda y: y if y == '전체' else period_label(y), key='timeline_year')
    if selected == FAMILY_GROUP:
        st.subheader(period_label(selected))
    for year in years if selected == '전체' else period_years(selected):
        st.subheader(f'{year}년' if year in (2020, 2021) else year_label(year))
        if not events[year]:
            st.info('아직 기록된 이벤트가 없습니다.')
        for event_index, event in enumerate(events[year]):
            with st.container(border=True):
                if can_delete_cards():
                    spacer, edit, close = st.columns([10, 1, 1])
                    with edit:
                        if st.button('✏️', key=f'edit_timeline_{year}_{event_index}', help='제목·설명 수정'):
                            edit_card_text('timeline', event, year)
                    with close:
                        if st.button('×', key=f'delete_timeline_{year}_{event_index}', help='Timeline 기록 삭제'):
                            confirm_card_delete('timeline', event, year)
                left, right = st.columns([1, 2])
                with right:
                    st.markdown(f'<div class="event"><small>{escape(str(event.get("date", "")))}</small><h3>{escape(str(event.get("title", "소중한 순간")))}</h3><p>{escape(str(event.get("description", "")))}</p></div>', unsafe_allow_html=True)
                with left:
                    paths = event.get('images', [event.get('image', '')])
                    if not isinstance(paths, list):
                        paths = []
                    for value in paths[:3] or ['']:
                        show_image(local_image(value))
with picture_tab:
    year = st.selectbox('Picture 연도', periods, index=len(periods)-1, format_func=period_label, key='picture_year')
    columns_count = st.radio('한 줄 사진 수', [2, 3, 4], index=1, horizontal=True)
    items = [path for actual_year in period_years(year) for path in pictures(actual_year)]
    st.caption(f'{period_label(year)}의 추억 · {len(items)}장 (30장 이상도 모두 표시됩니다)')
    if not items:
        folders = ', '.join(f'images/{actual_year}/pictures/' for actual_year in period_years(year))
        st.info(f'{folders} 폴더에 사진을 넣어주세요.')
    for start in range(0, len(items), columns_count):
        columns = st.columns(columns_count)
        for column, path in zip(columns, items[start:start+columns_count]):
            with column:
                with st.container(border=True):
                    key = path.relative_to(BASE).as_posix()
                    if can_delete_cards():
                        spacer, edit, close = st.columns([3, 1, 1])
                        with edit:
                            if st.button('✏️', key=f'edit_picture_{key}', help='제목·설명 수정'):
                                edit_card_text('picture', key)
                        with close:
                            if st.button('×', key=f'delete_picture_{key}', help='사진과 연결된 기록 삭제'):
                                confirm_card_delete('picture', key)
                    show_image(path, thumbnail=True)
                    info = metadata.get(key, {})
                    if not isinstance(info, dict):
                        info = {}
                    st.write(str(info.get('caption', path.stem)))
                    if info.get('date'):
                        st.caption(str(info['date']))
                    with st.expander('🔍 원본 비율로 크게 보기'):
                        show_image(path)
st.divider()
st.caption('Made with ❤️ · Every day with you is a beautiful memory.')
