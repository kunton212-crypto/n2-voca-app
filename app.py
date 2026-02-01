import streamlit as st
import pandas as pd
import re
import streamlit.components.v1 as components

# 구글 시트 주소
SHEET_ID = "1KrgYU9dPGVWJgHeKJ4k4F6o0fqTtHvs7P5w7KmwSwwA"
CSV_URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv"

st.set_page_config(page_title="JLPT N2", page_icon="🎴", layout="centered")

# --- [스타일] 사이버펑크 네온 테마 & 레이아웃 고정 ---
st.markdown("""
    <link href="https://fonts.googleapis.com/css2?family=Noto+Sans+JP:wght@400;700;900&display=swap" rel="stylesheet">

    <style>
    /* 기본 초기화 & 폰트 적용 */
    *, *::before, *::after { box-sizing: border-box !important; }
    html, body, [class*="css"] {
        font-family: 'Noto Sans JP', sans-serif !important;
    }
    .stApp { 
        background-color: #050505 !important; /* 완전 블랙보다 아주 살짝 밝은 딥다크 */
        overflow-x: hidden !important; 
    }
    
    /* 2. 불필요한 스트림릿 기본 UI 숨기기 (햄버거 메뉴, 푸터 등) */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}

    /* 컨테이너 여백 설정 */
    .block-container { 
        padding-top: 2rem !important; /* 상단 여백 조금 줄임 */
        padding-left: 5px !important; 
        padding-right: 5px !important;
        max-width: 100vw !important;
    }

    /* 모바일 전용 Grid 레이아웃 (이전과 동일) */
    @media (max-width: 640px) {
        [data-testid="stHorizontalBlock"] {
            display: grid !important;
            grid-template-columns: 1fr 1fr !important;
            gap: 10px !important;
            width: 100% !important;
        }
        [data-testid="column"] { width: auto !important; flex: unset !important; min-width: 0 !important; }
    }
    
    /* --- [디자인 업그레이드] --- */

    /* 메인 컬러 정의 */
    :root {
        --neon-green: #00FFC6;
        --neon-blue: #00E1FF;
        --dark-bg: #121212;
    }

    /* 현황판: 네온 글로우 효과 */
    .status-box {
        background-color: var(--dark-bg);
        padding: 12px; border-radius: 12px;
        color: var(--neon-green) !important; font-weight: bold; text-align: center;
        margin-bottom: 15px; width: 100%;
        border: none;
        /* 핵심: 테두리 대신 빛나는 효과 */
        box-shadow: 0 0 10px rgba(0, 255, 198, 0.3), inset 0 0 5px rgba(0, 255, 198, 0.1);
        letter-spacing: 1px;
    }

    /* 단어 카드: 깊이감 있는 배경 */
    .word-card { 
        background: linear-gradient(145deg, #1a1a1a, #0d0d0d);
        padding: 30px 10px; border-radius: 20px; 
        border: 1px solid #333; text-align: center; margin-bottom: 15px; width: 100%;
        box-shadow: 0 5px 15px rgba(0,0,0,0.5);
    }
    .japanese-word { 
        font-size: 3.5rem !important; color: #FFFFFF !important; margin: 0; font-weight: 900; 
        text-shadow: 0 0 10px rgba(255,255,255,0.3);
    }
    
    /* 정답 박스 (소리 X) */
    .ans-normal {
        background: #222; color: #E0E0E0; padding: 14px; width: 100%;
        border-radius: 10px; text-align: center; font-weight: bold; font-size: 1.05rem;
        margin-bottom: 8px; border: 1px solid #444; display: block;
    }
    
    /* 버튼 스타일 업그레이드 */
    .stButton>button { 
        height: 52px !important; border-radius: 12px !important; font-weight: bold !important; width: 100% !important;
        font-size: 1rem !important;
        transition: all 0.2s ease-in-out;
        box-shadow: 0 4px 6px rgba(0,0,0,0.2);
    }
    /* 버튼 눌렀을 때 효과 */
    .stButton>button:active { transform: scale(0.98); box-shadow: none; }

    /* 토글/체크박스 라벨 스타일 */
    .stToggle label, .stCheckbox label {
        font-size: 0.9rem !important; color: #ccc !important; font-weight: bold;
    }
    /* 체크박스 체크됐을 때 색상 커스텀 (스트림릿 기본은 파랑) */
    /* Note: 스트림릿 내부 구조상 완벽한 색상 변경은 어렵지만 최선을 다함 */
    span[data-baseweb="checkbox"] > div {
        background-color: var(--neon-green) !important;
    }

    /* 레벨바 색상 변경 (황금색) */
    .stProgress > div > div > div > div {
        background-color: #FFD700 !important;
        box-shadow: 0 0 10px rgba(255, 215, 0, 0.5);
    }
    </style>
    """, unsafe_allow_html=True)

# --- [자바스크립트] Kyoko 소환 (버튼 디자인 적용) ---
def js_audio_button(text, key_suffix):
    clean_text = re.sub(r'[\(（].*?[\)）]', '', text).replace('*', '').replace("'", "")
    html_code = f"""
    <!DOCTYPE html>
    <html>
    <head>
    <link href="https://fonts.googleapis.com/css2?family=Noto+Sans+JP:wght@700&display=swap" rel="stylesheet">
    <style>
        body {{ margin: 0; padding: 0; background-color: transparent; overflow: hidden; font-family: 'Noto Sans JP', sans-serif; }}
        .voice-btn {{
            width: 100%; height: 52px;
            background: #1a1a1a; /* 약간 밝은 배경 */
            color: #00FFC6; /* 네온 민트색 */
            border: none; /* 테두리 삭제 */
            /* 네온 글로우 효과 적용 */
            box-shadow: 0 0 8px rgba(0, 255, 198, 0.4), inset 0 0 3px rgba(0, 255, 198, 0.2);
            border-radius: 12px;
            font-size: 17px; font-weight: bold; cursor: pointer;
            display: flex; align-items: center; justify-content: center;
            -webkit-tap-highlight-color: transparent;
            box-sizing: border-box; transition: all 0.2s;
            margin-bottom: 8px;
        }}
        .voice-btn:active {{ transform: scale(0.98); background-color: #222; }}
        .icon { margin-right: 8px; font-size: 1.2rem; }
    </style>
    </head>
    <body>
        <button class="voice-btn" onclick="speak()"><span class="icon">🔊</span> {text}</button>
        <script>
            function speak() {{
                window.speechSynthesis.cancel();
                const msg = new SpeechSynthesisUtterance('{clean_text}');
                msg.lang = 'ja-JP'; msg.rate = 1.0; 
                let voices = window.speechSynthesis.getVoices();
                let jaVoice = voices.find(v => v.name.includes('Kyoko')) || 
                              voices.find(v => v.name.includes('Otoya')) ||
                              voices.find(v => v.lang === 'ja-JP');
                if (jaVoice) {{ msg.voice = jaVoice; }}
                window.speechSynthesis.speak(msg);
            }}
            if (window.speechSynthesis.onvoiceschanged !== undefined) {{
                window.speechSynthesis.onvoiceschanged = () => window.speechSynthesis.getVoices();
            }}
        </script>
    </body>
    </html>
    """
    components.html(html_code, height=60, scrolling=False) # 높이 약간 증가

@st.cache_data(ttl=60)
def load_data():
    try:
        df = pd.read_csv(CSV_URL).fillna(" ")
        df['Day'] = ((df.index) // 30 + 1).astype(str) + "일차"
        df['GlobalID'] = df.index
        return df
    except: return pd.DataFrame()

df = load_data()

if 'idx' not in st.session_state: st.session_state.idx = 0
if 'learned' not in st.session_state: st.session_state.learned = set()
if 'show' not in st.session_state: st.session_state.show = {k:False for k in ["reading", "mean", "ex", "kanji"]}
if 'shuffle_seed' not in st.session_state: st.session_state.shuffle_seed = 42

with st.sidebar:
    if not df.empty:
        days = sorted(df['Day'].unique(), key=lambda x: int(x.replace("일차", "")))
        sel_day = st.selectbox("구간 선택", days)
        if st.button("🔄 전체 초기화"): 
            st.session_state.learned = set()
            st.rerun()
        if 'p_day' not in st.session_state or st.session_state.p_day != sel_day:
            st.session_state.idx = 0; st.session_state.p_day = sel_day

day_df = df[df['Day'] == sel_day].copy()

# [수정] Grid 적용, 라벨에 이모지 추가로 직관성 높임
c1, c2 = st.columns(2) 
with c1:
    do_shuffle = st.toggle("🔀 순서 섞기", value=False)
with c2:
    show_all = st.checkbox("🔄 복습 모드", value=False)

if do_shuffle:
    day_df = day_df.sample(frac=1, random_state=st.session_state.shuffle_seed).reset_index(drop=True)

display_df = day_df if show_all else day_df[~day_df['GlobalID'].isin(st.session_state.learned)].reset_index(drop=True)

if not display_df.empty:
    if st.session_state.idx >= len(display_df): st.session_state.idx = 0
    row = display_df.iloc[st.session_state.idx]
    
    # 1. 현황판
    current_learned = len([i for i in st.session_state.learned if i in day_df['GlobalID'].values])
    st.markdown(f'<div class="status-box">📊 {sel_day} 진행중 : <span style="color:#FFFFFF">{current_learned}</span> / {len(day_df)}</div>', unsafe_allow_html=True)

    # 2. 단어 카드
    st.markdown(f'<div class="word-card"><h1 class="japanese-word">{row.iloc[1]}</h1></div>', unsafe_allow_html=True)

    # 3. 정답 및 음성 버튼
    def reveal_section(label, key, content, has_voice=False):
        if not st.session_state.show[key]:
            # 버튼에 아이콘 추가로 직관성 높임
            icon = "👁️" if not has_voice else "👂"
            if st.button(f"{icon} {label} 확인", key=f"btn_{key}", use_container_width=True):
                st.session_state.show[key] = True; st.rerun()
        else:
            if has_voice:
                js_audio_button(content, key)
            else:
                st.markdown(f'<div class="ans-normal">{content}</div>', unsafe_allow_html=True)

    reveal_section("읽기", "reading", row.iloc[2], has_voice=True)
    reveal_section("뜻", "mean", row.iloc[3])
    reveal_section("예문", "ex", row.iloc[4], has_voice=True)
    reveal_section("한자", "kanji", row.iloc[5] if len(row)>5 else "-")

    # 4. 하단 버튼
    st.write("")
    cl, cr = st.columns(2)
    with cl:
        if st.button("⏭️ 패스", use_container_width=True):
            st.session_state.idx = (st.session_state.idx + 1) % len(display_df)
            st.session_state.show = {k:False for k in st.session_state.show}; st.rerun()
    with cr:
        # Primary 버튼 색상도 테마에 맞게 자동 적용됨
        if st.button("✅ 외웠다!", type="primary", use_container_width=True):
            st.session_state.learned.add(row['GlobalID'])
            st.session_state.show = {k:False for k in st.session_state.show}; st.rerun()

    # 5. 레벨 바 (황금색 적용됨)
    total_learned = len(st.session_state.learned)
    user_level = (total_learned // 10) + 1
    exp_in_level = total_learned % 10
    st.markdown(f"""
    <div style="margin-top:20px; padding:12px; background:#121212; border-radius:12px; border:1px solid #333; text-align:center; box-shadow: 0 4px 6px rgba(0,0,0,0.3);">
        <span style="color:#FFD700; font-weight:900; font-size: 1.1rem; letter-spacing: 1px;">🏆 LV.{user_level} 마스터 (총 {total_learned}개)</span>
    </div>
    """, unsafe_allow_html=True)
    st.progress(exp_in_level / 10)

else:
    # 완료 화면도 조금 더 화려하게
    st.balloons()
    st.markdown("""
        <div style="text-align: center; padding: 50px 20px;">
            <h1 style="color: #00FFC6; font-size: 3rem; text-shadow: 0 0 20px #00FFC6;">MISSION COMPLETE!</h1>
            <p style="color: #FFFFFF; font-size: 1.2rem;">오늘의 분량을 모두 완파했습니다!</p>
        </div>
    """, unsafe_allow_html=True)