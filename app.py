import streamlit as st
import pandas as pd
import re
import streamlit.components.v1 as components

# 구글 시트 주소
SHEET_ID = "1KrgYU9dPGVWJgHeKJ4k4F6o0fqTtHvs7P5w7KmwSwwA"
CSV_URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv"

st.set_page_config(page_title="JLPT N2", page_icon="🎴", layout="centered")

# --- [스타일] f-string 제거 (일반 문자열 사용) -> 에러 원천 차단 ---
st.markdown("""
    <link href="https://fonts.googleapis.com/css2?family=Noto+Sans+JP:wght@400;700;900&display=swap" rel="stylesheet">
    <style>
    /* 1. 기본 초기화 */
    *, *::before, *::after { box-sizing: border-box !important; }
    html, body, [class*="css"] { font-family: 'Noto Sans JP', sans-serif !important; }
    .stApp { background-color: #050505 !important; overflow-x: hidden !important; }
    
    /* 2. UI 숨기기 & 여백 최적화 */
    #MainMenu, footer, header { visibility: hidden; }
    .block-container { 
        padding-top: 2rem !important; 
        padding-left: 5px !important; padding-right: 5px !important;
        max-width: 100vw !important;
    }

    /* 3. [핵심] 모바일 Grid 레이아웃 (스타일이 적용되면 이것도 작동함) */
    @media (max-width: 640px) {
        /* st.columns를 강제로 Grid로 변환 */
        [data-testid="stHorizontalBlock"] {
            display: grid !important; 
            grid-template-columns: 1fr 1fr !important; /* 1:1 비율 격자 */
            gap: 10px !important; 
            width: 100% !important;
        }
        [data-testid="column"] { 
            width: auto !important; 
            flex: unset !important; 
            min-width: 0 !important; 
        }
    }
    
    /* 4. 디자인 컴포넌트 */
    :root { --neon: #00FFC6; --dark: #121212; }

    /* 현황판 */
    .status-box {
        background-color: var(--dark); padding: 12px; border-radius: 8px;
        color: var(--neon) !important; font-weight: bold; text-align: center;
        margin-bottom: 15px; width: 100%; border: 1px solid #333;
        box-shadow: 0 0 8px rgba(0, 255, 198, 0.15); font-size: 0.9rem;
    }

    /* 단어 카드 */
    .word-card { 
        background: #111; padding: 35px 10px; border-radius: 16px; 
        border: 1px solid #333; text-align: center; margin-bottom: 20px; width: 100%;
        box-shadow: 0 10px 30px rgba(0,0,0,0.5);
    }
    .japanese-word { 
        font-size: 3.2rem !important; color: #fff !important; margin: 0; font-weight: 900; 
        letter-spacing: -1px;
    }
    
    /* 정답 박스 (텍스트만) */
    .ans-normal {
        background: #1a1a1a; color: #ddd; padding: 14px; width: 100%;
        border-radius: 8px; text-align: center; font-weight: 500; font-size: 1rem;
        margin-bottom: 8px; border: 1px solid #333; display: block;
    }
    
    /* 버튼 스타일 */
    .stButton>button { 
        height: 50px !important; border-radius: 8px !important; 
        font-weight: 700 !important; width: 100% !important; font-size: 0.95rem !important;
        background: #000 !important; border: 1px solid #444 !important; color: #888 !important;
        transition: all 0.2s !important;
    }
    .stButton>button:hover { border-color: var(--neon) !important; color: var(--neon) !important; }
    .stButton>button:active { transform: scale(0.98); background: #111 !important; }
    
    /* '외웠다' 버튼 (Primary) */
    button[kind="primary"] {
        background: var(--neon) !important; border: none !important; color: #000 !important;
        box-shadow: 0 0 15px rgba(0, 255, 198, 0.4) !important;
    }

    /* 토글, 체크박스 */
    .stToggle label, .stCheckbox label { font-size: 12px !important; color: #666 !important; }
    .stToggle, .stCheckbox { transform: scale(0.9); margin-right: -10px !important; }

    /* 레벨바 */
    .stProgress > div > div > div > div { background-color: var(--neon) !important; }
    </style>
    """, unsafe_allow_html=True)

# --- [자바스크립트] f-string 사용 (CSS 중괄호 {{ }} 두 번 감싸기 필수) ---
def js_audio_button(text, key_suffix):
    clean_text = re.sub(r'[\(（].*?[\)）]', '', text).replace('*', '').replace("'", "")
    
    html_code = f"""
    <!DOCTYPE html>
    <html>
    <head>
    <link href="https://fonts.googleapis.com/css2?family=Noto+Sans+JP:wght@700&display=swap" rel="stylesheet">
    <style>
        /* 여기서 중괄호는 {{ }} 로 두 번 써야 파이썬이 에러를 안 냅니다 */
        body {{ margin: 0; padding: 0; background: transparent; overflow: hidden; font-family: 'Noto Sans JP', sans-serif; }}
        .voice-btn {{
            width: 100%; height: 50px;
            background: #111; 
            color: #00FFC6; border: 1px solid #00FFC6; border-radius: 8px;
            font-size: 15px; font-weight: bold; cursor: pointer;
            display: flex; align-items: center; justify-content: center;
            -webkit-tap-highlight-color: transparent;
            box-sizing: border-box; transition: all 0.2s;
        }}
        .voice-btn:active {{ background: #00FFC6; color: #000; transform: scale(0.98); }}
    </style>
    </head>
    <body>
        <button class="voice-btn" onclick="speak()">{text}</button>
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
    components.html(html_code, height=55, scrolling=False)

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
        sel_day = st.selectbox("구간", days)
        if st.button("🔄 리셋"): st.session_state.learned = set(); st.rerun()
        if 'p_day' not in st.session_state or st.session_state.p_day != sel_day:
            st.session_state.idx = 0; st.session_state.p_day = sel_day

day_df = df[df['Day'] == sel_day].copy()

# 상단 컨트롤바
c1, c2 = st.columns(2) 
with c1: do_shuffle = st.toggle("순서 섞기", value=False)
with c2: show_all = st.checkbox("복습 모드", value=False)

if do_shuffle:
    day_df = day_df.sample(frac=1, random_state=st.session_state.shuffle_seed).reset_index(drop=True)

display_df = day_df if show_all else day_df[~day_df['GlobalID'].isin(st.session_state.learned)].reset_index(drop=True)

if not display_df.empty:
    if st.session_state.idx >= len(display_df): st.session_state.idx = 0
    row = display_df.iloc[st.session_state.idx]
    
    # 1. 현황판
    current_learned = len([i for i in st.session_state.learned if i in day_df['GlobalID'].values])
    st.markdown(f'<div class="status-box">DAY {sel_day.replace("일차","")} - PROGRESS {current_learned}/{len(day_df)}</div>', unsafe_allow_html=True)

    # 2. 단어 카드
    st.markdown(f'<div class="word-card"><h1 class="japanese-word">{row.iloc[1]}</h1></div>', unsafe_allow_html=True)

    # 3. 정답 및 음성 영역
    def reveal_section(label, key, content, has_voice=False):
        if not st.session_state.show[key]:
            if st.button(f"{label} 확인", key=f"btn_{key}", use_container_width=True):
                st.session_state.show[key] = True; st.rerun()
        else:
            if has_voice:
                js_audio_button(content, key)
            else:
                st.markdown(f'<div class="ans-normal">{content}</div>', unsafe_allow_html=True)

    # 읽기/뜻 병렬 배치
    c_read, c_mean = st.columns(2)
    with c_read:
        reveal_section("읽기", "reading", row.iloc[2], has_voice=True)
    with c_mean:
        reveal_section("뜻", "mean", row.iloc[3])
    
    reveal_section("예문", "ex", row.iloc[4], has_voice=True)
    reveal_section("한자", "kanji", row.iloc[5] if len(row)>5 else "-")

    # 4. 하단 액션 버튼
    st.write("")
    cl, cr = st.columns(2)
    with cl:
        if st.button("패스", use_container_width=True):
            st.session_state.idx = (st.session_state.idx + 1) % len(display_df)
            st.session_state.show = {k:False for k in st.session_state.show}; st.rerun()
    with cr:
        if st.button("암기 완료", type="primary", use_container_width=True):
            st.session_state.learned.add(row['GlobalID'])
            st.session_state.show = {k:False for k in st.session_state.show}; st.rerun()

    # 5. 레벨 바
    total_learned = len(st.session_state.learned)
    user_level = (total_learned // 10) + 1
    exp_in_level = total_learned % 10
    st.markdown(f"""
    <div style="margin-top:20px; text-align:center; color:#555; font-size:0.8rem; letter-spacing:1px; font-weight:bold;">
        LEVEL {user_level}
    </div>
    """, unsafe_allow_html=True)
    st.progress(exp_in_level / 10)

else:
    st.balloons()
    st.markdown("""
        <div style="text-align: center; padding: 50px 20px;">
            <h1 style="color: #00FFC6; font-size: 2.5rem;">ALL CLEAR</h1>
        </div>
    """, unsafe_allow_html=True)