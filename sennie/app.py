"""사진 폴더와 JSON으로 관리하는 우리 아이 성장앨범."""
from datetime import date, datetime, timedelta, timezone
from html import escape
import json
from pathlib import Path

import streamlit as st
from PIL import Image, ImageOps, UnidentifiedImageError

BASE = Path(__file__).resolve().parent
EXTENSIONS = {'.jpg', '.jpeg', '.png', '.webp', '.bmp'}
st.set_page_config(page_title='우리 아이 성장앨범', page_icon='🩷', layout='wide')
st.markdown('''<style>
/* 메인 배경 */
.stApp {
    background: #F0F7FC;
    color: #455566;
}

/* 왼쪽 사이드바 배경 */
section[data-testid="stSidebar"] {
    background: #F0F7FC;
}
.block-container {max-width:1200px;padding-top:2rem;padding-bottom:4rem}
h1,h2,h3 {color:#56758b!important}
.hero {background:#ffffffcc;border:1px solid #eee3d7;border-radius:24px;padding:28px;margin-bottom:20px}
.kicker {color:#b47a7e;letter-spacing:3px;font-size:12px;font-weight:700}
.hero h1 {margin:6px 0;font-size:36px}
.event {border-left:4px solid #a6c6d8;background:#ffffffdd;padding:18px 24px;border-radius:0 18px 18px 0;margin:8px 0 22px}
.event p {white-space:pre-wrap;color:#6b7785}
[data-testid="stImage"] img {border-radius:16px}
[data-testid="stMetric"] {background:#ffffffbb;border-radius:18px;padding:18px;border:1px solid #eee3d7}
button {border-radius:14px!important}
@media(max-width:640px){.hero h1{font-size:27px}.block-container{padding:1rem}}
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
        st.info('📷 여기에 소중한 사진을 넣어주세요.')
        return
    try:
        with Image.open(path) as source:
            image = ImageOps.exif_transpose(source).convert('RGB')
            if thumbnail:
                image = ImageOps.fit(image, (720, 720), method=Image.Resampling.LANCZOS)
            else:
                image.thumbnail((1600, 1600))
            st.image(image, width='stretch')
    except (OSError, ValueError, UnidentifiedImageError):
        st.warning(f'{path.name}: 사진을 읽을 수 없습니다. JPG 또는 PNG로 다시 저장해주세요.')


profile = read_object('profile.json', {})
timeline = read_object('timeline.json', {})
metadata = read_object('pictures.json', {})
try:
    birthday = date.fromisoformat(str(profile.get('birth_date', '2022-03-10')))
except ValueError:
    st.warning('생년월일 형식은 YYYY-MM-DD입니다. 기본 생년 2022년을 사용합니다.')
    birthday = date(2022, 3, 10)
folder_years = {int(p.name) for p in (BASE / 'images').glob('*') if p.is_dir() and p.name.isdigit() and len(p.name) == 4}
years = sorted(set(range(birthday.year, max(birthday.year, 2026) + 1)) | folder_years | {int(k) for k in timeline if k.isdigit() and len(k) == 4})
years = [y for y in years if y >= birthday.year]
events = {}
for year in years:
    raw = timeline.get(str(year), [])
    if not isinstance(raw, list):
        st.warning(f'{year}년 이벤트는 JSON 배열이어야 합니다.')
        raw = []
    events[year] = sorted([e for e in raw if isinstance(e, dict)], key=lambda e: str(e.get('date', '')))


def year_label(year):
    return f'{year} · {year - birthday.year + 1}살'


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

    for year in family_years:
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
    
st.markdown(f'<div class="hero"><div class="kicker">OUR LITTLE STORY</div><h1>🧸 {escape(str(profile.get("name", "우리 아기")))}의 성장앨범</h1><p>{escape(str(profile.get("message", "매일매일 자라나는 소중한 순간들 ❤️")))}</p><span>{years[0]} — {years[-1]} · {escape(str(profile.get("nickname", "사랑둥이")))}</span></div>', unsafe_allow_html=True)
with st.expander('🌷 앨범 표지', expanded=False):
    show_image(local_image(str(profile.get('cover_image', 'images/profile/main.jpg'))))

# 한국 시간: UTC + 9시간
KST = timezone(timedelta(hours=9))

# 출생 시각: 2022년 1월 1일 오전 2시 34분
BIRTH_DATETIME = datetime(
    2022, 1, 1, 2, 34, 0,
    tzinfo=KST,
)


@st.fragment(run_every="1s")
def show_growth_clock():
    now = datetime.now(KST)

    total_seconds = max(
        0,
        int((now - BIRTH_DATETIME).total_seconds()),
    )

    days, remainder = divmod(total_seconds, 86400)
    hours, remainder = divmod(remainder, 3600)
    minutes, seconds = divmod(remainder, 60)

 st.markdown("함께한 시간 ❤️")

st.markdown(
    f"""
    <div style="
        font-size: clamp(16px, 2vw, 26px);
        font-weight: 700;
        color: #455566;
        white-space: nowrap;
    ">
        {days:,}일 {hours:02d}시간 {minutes:02d}분 {seconds:02d}초
    </div>
    """,
    unsafe_allow_html=True,
)
    st.caption("2022.01.01 오전 02:34부터")


a, b, c = st.columns(3)

with a:
    show_growth_clock()

b.metric(
    "Timeline 이벤트",
    sum(len(v) for v in events.values()),
)

c.metric(
    "Picture 사진",
    sum(len(pictures(y)) for y in years),
)

st.caption('샘플 이벤트는 실제 성장 기록에 맞게 수정해주세요. 사진 수는 Picture 폴더 기준입니다.')

timeline_tab, picture_tab = st.tabs(['🌱 Timeline', '📸 Picture'])
with timeline_tab:
    selected = st.selectbox('Timeline 연도', ['전체'] + years, format_func=lambda y: y if y == '전체' else year_label(y), key='timeline_year')
    for year in years if selected == '전체' else [selected]:
        st.subheader(year_label(year))
        if not events[year]:
            st.info('아직 기록된 이벤트가 없습니다.')
        for event in events[year]:
            with st.container(border=True):
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
    year = st.selectbox('Picture 연도', years, index=len(years)-1, format_func=year_label, key='picture_year')
    columns_count = st.radio('한 줄 사진 수', [2, 3, 4], index=1, horizontal=True)
    items = pictures(year)
    st.caption(f'{year_label(year)}의 추억 · {len(items)}장 (30장 이상도 모두 표시됩니다)')
    if not items:
        st.info(f'images/{year}/pictures/ 폴더에 사진을 넣어주세요.')
    for start in range(0, len(items), columns_count):
        columns = st.columns(columns_count)
        for column, path in zip(columns, items[start:start+columns_count]):
            with column:
                with st.container(border=True):
                    show_image(path, thumbnail=True)
                    key = path.relative_to(BASE).as_posix()
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
