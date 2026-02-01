import streamlit as st
import pandas as pd
import re
import streamlit.components.v1 as components

# 구글 시트 주소
SHEET_ID = "1KrgYU9dPGVWJgHeKJ4k4F6o0fqTtHvs7P5w7KmwSwwA"
CSV_URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv"

st.set_page_config(page_title="JLPT N2", page_icon="🎴", layout="centered")

# --- [스타일] 모바일 전용(@media) 강제 정렬 CSS ---
st.markdown("""
    <style>
    /* 기본 설정: 가로 스크롤 방지 */
    .stApp { 
        background-color: #000000 !important; 
        overflow-x: hidden !important;
    }
    
    /* 전체 컨테이너 여백 극한으로 줄이기 */
    .block-container { 
        padding-top: 3rem !important; 
        padding-left: 2px !important; 
        padding-right: 2px !important;
        max-width: 100vw !important;
    }

    /* [핵심] 모바일 화면(폭 640px 이하)에서만 발동하는 강제 명령 */
    @media (max-width: 640px) {
        /* 가로 배치 강제 (Streamlit이 세로로 바꾸는 걸 막음) */
        [data-testid="stHorizontalBlock"] {
            flex-direction: row !important;
            flex-wrap: nowrap !important;
            gap: 5px !important;
        }
        
        /* 컬럼 너비 강제 50:50 */
        [data-testid="column"] {
            width: 50% !important;
            flex: 0 0 50% !important;
            min-width: 50% !important;
            max-width: 50% !important;
        }
        
        /* 버튼 텍스트 크기 자동 조절 */
        .stButton button {
            padding-left: 5px !important;
            padding-right: 5px !important;
        }
    }
    
    /* 위젯 크기 조절 */
    .stToggle, .stCheckbox {
        white-space: nowrap !important;
        transform: scale(0.85);
        transform-origin: left center;
        margin-right: -20px !important;
    }
    
    /* 디자인 요소들 */
    .status-box {
        background-color: #1E1E1E; padding: 10px; border-radius: 10px;
        color: #00FFAA !important; font-weight: bold; text-align: center;
        margin-bottom: 10px; border: 1.5px solid #00FFAA; width: 100%;
    }
    .word-card { 
        background-color: #1A1A1A; padding: 25px 10px; border-radius: 15px; 
        border: 1px solid #444; text-align: center; margin-bottom: 10px; width: 100%;
    }
    .japanese-word { font-size: 3rem !important; color: #FFFFFF !important; margin: 0; font-weight: 800; }
    
    .ans-normal {
        background: #262626; color: #FFFFFF; padding: 12px; width: 100%;
        border-radius: 8px; text-align: center; font-weight: bold; 
        margin-bottom: 6px; border: 1px solid #555; display: block;
    }
    
    .stButton>button { height: 48px !important; border-radius: 12px !important; font-weight: bold !important; width: 100% !important; }
    </style>
    """, unsafe_allow_html=True)

# --- [자바스크립트] Kyoko 소환 (이전과 동일) ---
def js_audio_button(text, key_suffix):
    clean_text = re.sub(r'[\(（].*?[\)）]', '', text).replace('*', '').replace("'", "")
    
    html_code = f"""
    <!DOCTYPE html>
    <html>
    <head>
    <style>
        body {{ margin: 0; padding: 0; background-color: transparent; overflow: hidden; }}
        .voice-btn {{
            width: 100%; height: 48px;
            background-color: #262626; color: #00FFAA;
            border: 1.5px solid #00FFAA; border-radius: 8px;
            font-size: 16px; font-weight: bold; cursor: pointer;
            display: flex; align-items: center; justify-content: center;
            font-family: sans-serif; -webkit-tap-highlight-color: transparent;
            box-sizing: border-box;
        }}
        .voice-btn:active {{ background-color: #333333; }}
    </style>
    </head>
    <body>
        <button class="voice-btn" onclick="speak()">🔊 {text}</button>
        <script>
            function speak() {{
                window.speechSynthesis.cancel();
                const msg = new SpeechSynthesisUtterance('{clean_text}');
                msg.lang = 'ja-JP';
                msg.rate = 1.0; 
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
    components.html(html_code, height=50, scrolling=False)

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

# [수정] 간격 0으로 설정
c1, c2 = st.columns([1, 1], gap="small") 
with c1:
    do_shuffle = st.toggle("🔀 순서 섞기", value=False)
with c2:
    show_all = st.checkbox("✅ 복습 모드", value=False)

if do_shuffle:
    day_df = day_df.sample(frac=1, random_state=st.session_state.shuffle_seed).reset_index(drop=True)

display_df = day_df if show_all else day_df[~day_df['GlobalID'].isin(st.session_state.learned)].reset_index(drop=True)

if not display_df.empty:
    if st.session_state.idx >= len(display_df): st.session_state.idx = 0
    row = display_df.iloc[st.session_state.idx]
    
    # 1. 현황판
    current_learned = len([i for i in st.session_state.learned if i in day_df['GlobalID'].values])
    st.markdown(f'<div class="status-box">📊 {sel_day} : {current_learned} / {len(day_df)}</div>', unsafe_allow_html=True)

    # 2. 단어 카드
    st.markdown(f'<div class="word-card"><h1 class="japanese-word">{row.iloc[1]}</h1></div>', unsafe_allow_html=True)

    # 3. 정답 및 음성 버튼
    def reveal_section(label, key, content, has_voice=False):
        if not st.session_state.show[key]:
            if st.button(f"👁️ {label} 확인", key=f"btn_{key}", use_container_width=True):
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
    cl, cr = st.columns([1, 1], gap="small")
    with cl:
        if st.button("⏭️ 패스", use_container_width=True):
            st.session_state.idx = (st.session_state.idx + 1) % len(display_df)
            st.session_state.show = {k:False for k in st.session_state.show}; st.rerun()
    with cr:
        if st.button("✅ 외웠다", type="primary", use_container_width=True):
            st.session_state.learned.add(row['GlobalID'])
            st.session_state.show = {k:False for k in st.session_state.show}; st.rerun()

    # 5. 레벨 바
    total_learned = len(st.session_state.learned)
    user_level = (total_learned // 10) + 1
    exp_in_level = total_learned % 10
    st.markdown(f"""
    <div style="margin-top:15px; padding:10px; background:#111; border-radius:10px; border:1px dashed #444; text-align:center;">
        <span style="color:#FFD700; font-weight:bold;">🔥 LV.{user_level} (총 {total_learned}개)</span>
    </div>
    """, unsafe_allow_html=True)
    st.progress(exp_in_level / 10)

else:
    st.balloons(); st.success("오늘 분량 끝!")