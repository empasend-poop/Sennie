import json
from pathlib import Path
from datetime import datetime

import streamlit as st
from PIL import Image, ImageOps


# ============================================================
# 기본 설정
# ============================================================

st.set_page_config(
    page_title="우리 아이 성장앨범",
    page_icon="🧸",
    layout="wide",
    initial_sidebar_state="expanded",
)

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
IMAGE_DIR = BASE_DIR / "images"

START_YEAR = 2022
END_YEAR = 2026

YEAR_AGES = {
    2022: 1,
    2023: 2,
    2024: 3,
    2025: 4,
    2026: 5,
}


# ============================================================
# 디자인 CSS
# ============================================================

st.markdown(
    """
    <style>

    /* 전체 배경 */
    .stApp {
        background:
            linear-gradient(
                180deg,
                #FFFDF9 0%,
                #FFF9F5 45%,
                #F9FCFF 100%
            );
    }

    /* 기본 글자 */
    html, body, [class*="css"] {
        font-family:
            "Pretendard",
            "Apple SD Gothic Neo",
            "Malgun Gothic",
            sans-serif;
    }

    /* Streamlit 기본 여백 */
    .block-container {
        padding-top: 2rem;
        padding-bottom: 5rem;
        max-width: 1450px;
    }

    /* 메인 제목 */
    .album-title {
        font-size: 42px;
        font-weight: 800;
        text-align: center;
        color: #44546A;
        margin-top: 10px;
        margin-bottom: 5px;
    }

    .album-subtitle {
        text-align: center;
        font-size: 17px;
        color: #8B95A5;
        margin-bottom: 30px;
    }

    /* 프로필 카드 */
    .profile-card {
        background: rgba(255,255,255,0.90);
        border: 1px solid #F1ECE7;
        border-radius: 24px;
        padding: 25px 30px;
        box-shadow: 0px 8px 30px rgba(80,80,80,0.06);
        margin-bottom: 20px;
    }

    /* 연도 제목 */
    .year-title {
        font-size: 30px;
        font-weight: 800;
        color: #5B7895;
        margin-top: 30px;
        margin-bottom: 15px;
    }

    .year-age {
        font-size: 16px;
        font-weight: 600;
        color: #E69B9B;
        margin-left: 8px;
    }

    /* Timeline */
    .timeline-card {
        background: white;
        border-radius: 22px;
        padding: 20px 25px;
        border: 1px solid #F0EBE7;
        box-shadow: 0 5px 18px rgba(70,70,70,0.05);
        margin-bottom: 20px;
    }

    .timeline-date {
        color: #8DA9C4;
        font-size: 14px;
        font-weight: 700;
    }

    .timeline-title {
        color: #4D5968;
        font-size: 22px;
        font-weight: 800;
        margin-top: 5px;
    }

    .timeline-description {
        color: #7C8591;
        font-size: 15px;
        margin-top: 8px;
        line-height: 1.7;
    }

    /* 갤러리 카드 느낌 */
    .picture-caption {
        text-align: center;
        font-size: 13px;
        color: #777;
        padding-top: 6px;
        padding-bottom: 18px;
    }

    /* 정보 카드 */
    .info-box {
        background: white;
        padding: 20px;
        border-radius: 20px;
        border: 1px solid #F0EBE7;
        text-align: center;
        box-shadow: 0 5px 15px rgba(70,70,70,0.04);
    }

    .info-number {
        font-size: 30px;
        font-weight: 800;
        color: #7699B8;
    }

    .info-label {
        color: #9299A3;
        font-size: 14px;
    }

    /* 구분선 */
    hr {
        border: none;
        border-top: 1px solid #EEE8E3;
        margin-top: 25px;
        margin-bottom: 25px;
    }

    /* Tabs */
    .stTabs [data-baseweb="tab-list"] {
        gap: 12px;
        justify-content: center;
    }

    .stTabs [data-baseweb="tab"] {
        height: 52px;
        padding-left: 25px;
        padding-right: 25px;
        border-radius: 15px;
        background-color: white;
        font-weight: 700;
    }

    </style>
    """,
    unsafe_allow_html=True,
)


# ============================================================
# JSON 읽기
# ============================================================

def load_json(file_path, default=None):

    if default is None:
        default = {}

    if not file_path.exists():
        return default

    try:
        with open(file_path, "r", encoding="utf-8") as f:
            return json.load(f)

    except Exception as e:
        st.warning(f"{file_path.name} 파일을 읽는 중 문제가 발생했습니다.")
        st.caption(str(e))

        return default


profile = load_json(
    DATA_DIR / "profile.json",
    {
        "name": "우리 아기",
        "birth_date": "2022-01-01",
        "nickname": "",
        "message": "우리 아이의 소중한 성장 기록 ❤️",
    },
)

timeline_data = load_json(
    DATA_DIR / "timeline.json",
    {}
)


# ============================================================
# 이미지 관련 함수
# ============================================================

IMAGE_EXTENSIONS = {
    ".jpg",
    ".jpeg",
    ".png",
    ".webp",
    ".bmp",
}


def get_images(folder):

    if not folder.exists():
        return []

    images = []

    for file in folder.iterdir():

        if (
            file.is_file()
            and file.suffix.lower() in IMAGE_EXTENSIONS
        ):
            images.append(file)

    return sorted(images)


def count_all_picture_images():

    count = 0

    for year in range(START_YEAR, END_YEAR + 1):

        folder = (
            IMAGE_DIR
            / str(year)
            / "pictures"
        )

        count += len(get_images(folder))

    return count


def count_timeline_events():

    count = 0

    for year in range(START_YEAR, END_YEAR + 1):

        count += len(
            timeline_data.get(
                str(year),
                []
            )
        )

    return count


# ============================================================
# HEADER
# ============================================================

st.markdown(
    """
    <div class="album-title">
        🧸 우리 아이 성장앨범
    </div>
    """,
    unsafe_allow_html=True,
)

st.markdown(
    f"""
    <div class="album-subtitle">
        {START_YEAR} ───── ❤️ ───── {END_YEAR}
        <br>
        하루하루 자라나는 소중한 순간들
    </div>
    """,
    unsafe_allow_html=True,
)


# ============================================================
# 사이드바
# ============================================================

with st.sidebar:

    st.markdown("## 🧸 Growth Album")

    st.markdown("---")

    st.markdown(
        f"""
        ### {profile.get("name", "우리 아기")} ❤️
        """
    )

    nickname = profile.get("nickname", "")

    if nickname:
        st.caption(
            f"우리 집 {nickname}"
        )

    st.markdown(
        f"""
        **생년월일**

        {profile.get("birth_date", "-")}
        """
    )

    st.markdown("---")

    st.caption(
        "사진은 각 연도의 pictures 폴더에 "
        "추가하면 자동으로 앨범에 표시됩니다."
    )


# ============================================================
# PROFILE
# ============================================================

profile_col1, profile_col2 = st.columns(
    [1, 3],
    gap="large"
)


with profile_col1:

    profile_image = (
        IMAGE_DIR
        / "profile"
        / "main.jpg"
    )

    if profile_image.exists():

        st.image(
            str(profile_image),
            use_container_width=True,
        )

    else:

        st.info(
            "📷 images/profile/main.jpg\n\n"
            "대표 사진을 넣어주세요."
        )


with profile_col2:

    st.markdown(
        f"""
        <div class="profile-card">

            <div style="
                font-size:14px;
                color:#9AA1AA;
                font-weight:700;
            ">
                OUR LITTLE STORY
            </div>

            <div style="
                font-size:32px;
                font-weight:800;
                color:#4E5D6C;
                margin-top:6px;
            ">
                {profile.get("name", "우리 아기")}
            </div>

            <div style="
                font-size:16px;
                color:#8C939C;
                margin-top:12px;
                line-height:1.8;
            ">
                {profile.get(
                    "message",
                    "우리 아이의 성장 기록 ❤️"
                )}
            </div>

        </div>
        """,
        unsafe_allow_html=True,
    )


# ============================================================
# SUMMARY
# ============================================================

picture_count = count_all_picture_images()
event_count = count_timeline_events()

summary1, summary2, summary3 = st.columns(3)


with summary1:

    st.markdown(
        f"""
        <div class="info-box">
            <div class="info-number">
                5
            </div>

            <div class="info-label">
                YEARS
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


with summary2:

    st.markdown(
        f"""
        <div class="info-box">
            <div class="info-number">
                {event_count}
            </div>

            <div class="info-label">
                TIMELINE EVENTS
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


with summary3:

    st.markdown(
        f"""
        <div class="info-box">
            <div class="info-number">
                {picture_count}
            </div>

            <div class="info-label">
                MEMORIES
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


st.write("")


# ============================================================
# MAIN TABS
# ============================================================

timeline_tab, picture_tab = st.tabs(
    [
        "🌱  Timeline",
        "📸  Picture",
    ]
)


# ============================================================
# TIMELINE
# ============================================================

with timeline_tab:

    st.markdown("## 🌱 Growing Timeline")

    st.caption(
        "우리 아이와 함께한 특별한 순간들을 "
        "시간 순서대로 기록합니다."
    )

    timeline_year = st.selectbox(
        "연도 선택",
        ["전체"] + [
            str(year)
            for year in range(
                START_YEAR,
                END_YEAR + 1
            )
        ],
        key="timeline_year",
    )

    if timeline_year == "전체":

        selected_years = range(
            START_YEAR,
            END_YEAR + 1
        )

    else:

        selected_years = [
            int(timeline_year)
        ]


    for year in selected_years:

        age = YEAR_AGES.get(year, "")

        st.markdown(
            f"""
            <div class="year-title">
                {year}
                <span class="year-age">
                    {age}살
                </span>
            </div>
            """,
            unsafe_allow_html=True,
        )

        events = timeline_data.get(
            str(year),
            []
        )

        if not events:

            st.info(
                f"{year}년 Timeline 기록이 없습니다."
            )

            continue


        for event in events:

            col_image, col_text = st.columns(
                [1.1, 2.4],
                gap="large"
            )

            image_path = (
                BASE_DIR
                / event.get(
                    "image",
                    ""
                )
            )


            with col_image:

                if image_path.exists():

                    st.image(
                        str(image_path),
                        use_container_width=True,
                    )

                else:

                    st.markdown(
                        """
                        <div style="
                            height:200px;
                            background:#F8F4F1;
                            border-radius:20px;
                            display:flex;
                            align-items:center;
                            justify-content:center;
                            color:#B4AAA4;
                        ">
                            📷 사진을 넣어주세요
                        </div>
                        """,
                        unsafe_allow_html=True,
                    )


            with col_text:

                st.markdown(
                    f"""
                    <div class="timeline-card">

                        <div class="timeline-date">
                            {event.get("date", "")}
                        </div>

                        <div class="timeline-title">
                            {event.get("title", "")}
                        </div>

                        <div class="timeline-description">
                            {event.get("description", "")}
                        </div>

                    </div>
                    """,
                    unsafe_allow_html=True,
                )

        st.markdown("---")


# ============================================================
# PICTURE
# ============================================================

with picture_tab:

    st.markdown(
        "## 📸 Our Precious Memories"
    )

    st.caption(
        "사진을 통해 다시 만나는 "
        "우리 아이의 성장 순간들 ❤️"
    )


    picture_year = st.selectbox(
        "앨범 선택",
        [
            f"{year} · {YEAR_AGES[year]}살"
            for year in range(
                START_YEAR,
                END_YEAR + 1
            )
        ],
        index=4,
        key="picture_year",
    )


    selected_year = int(
        picture_year.split(" · ")[0]
    )

    age = YEAR_AGES[
        selected_year
    ]


    st.markdown(
        f"""
        <div class="year-title">
            {selected_year}
            <span class="year-age">
                {age}살의 추억
            </span>
        </div>
        """,
        unsafe_allow_html=True,
    )


    picture_folder = (
        IMAGE_DIR
        / str(selected_year)
        / "pictures"
    )


    pictures = get_images(
        picture_folder
    )


    if not pictures:

        st.info(
            f"""
            아직 {selected_year}년 사진이 없습니다.

            아래 폴더에 사진을 넣어주세요.

            images/{selected_year}/pictures/
            """
        )

    else:

        st.caption(
            f"총 {len(pictures)}장의 추억"
        )

        # 한 줄 4장
        columns_per_row = 4

        for start in range(
            0,
            len(pictures),
            columns_per_row,
        ):

            row_images = pictures[
                start:
                start + columns_per_row
            ]

            columns = st.columns(
                columns_per_row,
                gap="medium",
            )


            for index, image_path in enumerate(
                row_images
            ):

                with columns[index]:

                    try:

                        image = Image.open(
                            image_path
                        )

                        # EXIF 회전 정보 반영
                        image = ImageOps.exif_transpose(
                            image
                        )

                        st.image(
                            image,
                            use_container_width=True,
                        )

                        st.markdown(
                            f"""
                            <div class="picture-caption">
                                🤍 {image_path.stem}
                            </div>
                            """,
                            unsafe_allow_html=True,
                        )

                    except Exception:

                        st.warning(
                            f"{image_path.name} "
                            "사진을 불러올 수 없습니다."
                        )


# ============================================================
# FOOTER
# ============================================================

st.markdown("---")

st.markdown(
    """
    <div style="
        text-align:center;
        color:#A1A7AF;
        padding:25px 0 40px 0;
        font-size:14px;
    ">

        Made with ❤️ for our little one

        <br><br>

        Every day with you is a beautiful memory.

    </div>
    """,
    unsafe_allow_html=True,
)
