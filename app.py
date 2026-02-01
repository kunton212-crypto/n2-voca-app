import streamlit as st
import pandas as pd
import re
import streamlit.components.v1 as components

# 1. 페이지 설정
st.set_page_config(page_title="JLPT N2", page_icon="🎴", layout="centered")

# --- [스타일] 들여쓰기/공백 제거된 안전한 CSS ---
fixed_css = """
<style>
/* 1. 기본 설정 */
@import url('https://fonts.googleapis.com/css2?family=Noto+Sans+JP:wght@400;700;900&display=swap');
*, *::before, *::after { box-sizing: border-box !important; }
html, body, [class*="css"] { font-family: 'Noto Sans JP', sans-serif !important; }
.stApp { background-color: #050505 !important; overflow-x: hidden !important; }

/* 2. UI 숨기기 */
#MainMenu {visibility: hidden;}
footer {visibility: hidden;}
header {visibility: hidden;} /* 상단바 숨김 (사이드바 버튼도 같이 숨겨짐 -> 기능을 메인으로 이동) */
.block-container {
    padding-top: 1rem !important; /* 상단 여백 살짝 줄임 */
    padding-left: 0.5rem !important;
    padding-right: 0.5rem !important;
    max-width: 100vw !important;
}

/* 3. 모바일 레이아웃 (640px 이하 강제 Grid) */
@media (max-width: 640px) {
    [data-testid="stHorizontalBlock"] {
        display: grid !important;
        grid-template-columns: 1fr 1fr !important;
        gap: 8px !important;
        width: 100% !important;
    }
    [data-testid="column"] {
        width: auto !important;
        flex: unset !important;
        min-width: 0 !important;
    }
    .stButton button {
        padding-left: 0px !important;
        padding-right: 0px !important;
        font-size: 0.85rem !important;
        white-space: nowrap !important;
    }
}

/* 4. 디자인 테마 (네온) */
:root { --neon: #00FFC6; --dark: #121212; }

/* 콤보박스(Selectbox) 커스텀 */
div[data-baseweb="select"] > div {
    background-color: #111 !important;
    border-color: #333 !important;
    color: #fff !important;
}

.status-box {
    background-color: var(--dark);
    padding: 12px;
    border-radius: 8px;
    color: var(--neon) !important;
    font-weight: bold;
    text-align: center;
    margin-bottom: 15px;
    width: 100%;
    border: 1px solid #333;
    box-shadow: 0 0 8px rgba(0, 255, 198, 0.15);
    font-size: 0.9rem;
}

.word-card {
    background: #111;
    padding: 35px 10px;
    border-radius: 16px;
    border: 1px solid #333;
    text-align: center;
    margin-bottom: 20px;
    width: 100%;
    box-shadow: 0 10px 30px rgba(0,0,0,0.5);
}
.japanese-word {
    font-size: 3.2rem !important;
    color: #fff !important;
    margin: 0;
    font-weight: 900;
    letter-spacing: -1px;
}

.ans-normal {
    background: #1a1a1a;
    color: #ddd;
    padding: 14px;
    width: 100%;
    border-radius: 8px;
    text-align: center;
    font-weight: 500;
    font-size: 1rem;
    margin-bottom: 8px;
    border: 1px solid #333;
    display: block;
}

.stButton>button {
    height: 50px !important;
    border-radius: 8px !important;
    font-weight: 700 !important;
    width: 100% !important;
    font-size: 0.95rem !important;
    background: #000 !important;
    border: 1px solid #444 !important;
    color: #888 !important;
    transition: all 0.2s !important;
}
.stButton>button:hover {
    border-color: var(--neon) !important;
    color: var(--neon) !important;
}
.stButton>button:active {
    transform: scale(0.98);
    background: #111 !important;
}

button[kind="primary"] {
    background: var(--neon) !important;
    border: none !important;
    color: #000 !important;
    box-shadow: 0 0 15px rgba(0, 255, 198, 0.4) !important;
}

.stToggle label, .stCheckbox label { font-size: 12px !important; color: #666 !important; }
.stToggle, .stCheckbox { transform: scale(0.9); margin-right: -10px !important; }
.stProgress > div > div > div > div { background-color: var(--neon) !important; }
</style>
"""
st.markdown(fixed_css, unsafe_allow_html=True)


# --- [기능] 데이터 로드 ---
SHEET_ID = "1KrgYU9dPGVWJgHeKJ4k4F6o0fqTtHvs7P5w7KmwSwwA"
CSV_URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv"

@st.cache_data(ttl=60)
def load_data():
    try:
        df = pd.read_csv(CSV_URL).fillna(" ")
        df['Day'] = ((df.index) // 30 + 1).astype(str) + "일차"
        df['GlobalID'] = df.index
        return df
    except: return pd.DataFrame()

df = load_data()

# --- [기능] 오디오 버튼 ---
def js_audio_button(text, key_suffix):
    clean_text = re.sub(r'[\(（].*?[\)）]', '', text).replace('*', '').replace("'", "")
    
    html_code = f"""
    <!DOCTYPE html>
    <html>
    <head>
    <link href="https://fonts.googleapis.com/css2?family=Noto+Sans+JP:wght@700&display=swap" rel="stylesheet">
    <style>
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

# --- [로직] 세션 관리 ---
if 'idx' not in st.session_state: st.session_state.idx = 0
if 'learned' not in st.session_state: st.session_state.learned = set()
if 'show' not in st.session_state: st.session_state.show = {k:False for k in ["reading", "mean", "ex", "kanji"]}
if 'shuffle_seed' not in st.session_state: st.session_state.shuffle_seed = 42


# --- [메인] 상단 컨트롤바 (사이드바 대체) ---
if not df.empty:
    days = sorted(df['Day'].unique(), key=lambda x: int(x.replace("일차", "")))
    
    # 1. 회차 선택 & 리셋 (모바일에서도 50:50 정렬됨)
    top_c1, top_c2 = st.columns(2)
    with top_c1:
        # label_visibility="collapsed"로 라벨 숨겨서 깔끔하게
        sel_day = st.selectbox("구간", days, label_visibility="collapsed")
    with top_c2:
        if st.button("🔄 리셋", use_container_width=True):
            st.session_state.learned = set()
            st.rerun()
            
    # 세션 업데이트
    if 'p_day' not in st.session_state or st.session_state.p_day != sel_day:
        st.session_state.idx = 0; st.session_state.p_day = sel_day

day_df = df[df['Day'] == sel_day].copy()


# 2. 순서 섞기 & 복습 모드
c1, c2 = st.columns(2) 
with c1: do_shuffle = st.toggle("순서 섞기", value=False)
with c2: show_all = st.checkbox("복습 모드", value=False)

if do_shuffle:
    day_df = day_df.sample(frac=1, random_state=st.session_state.shuffle_seed).reset_index(drop=True)

display_df = day_df if show_all else day_df[~day_df['GlobalID'].isin(st.session_state.learned)].reset_index(drop=True)

if not display_df.empty:
    if st.session_state.idx >= len(display_df): st.session_state.idx = 0
    row = display_df.iloc[st.session_state.idx]
    
    # 3. 현황판
    current_learned = len([i for i in st.session_state.learned if i in day_df['GlobalID'].values])
    st.markdown(f'<div class="status-box">DAY {sel_day.replace("일차","")} - PROGRESS {current_learned}/{len(day_df)}</div>', unsafe_allow_html=True)

    # 4. 단어 카드
    st.markdown(f'<div class="word-card"><h1 class="japanese-word">{row.iloc[1]}</h1></div>', unsafe_allow_html=True)

    # 5. 정답 확인 및 오디오 (읽기/뜻 50:50)
    def reveal_section(label, key, content, has_voice=False):
        if not st.session_state.show[key]:
            if st.button(f"{label} 확인", key=f"btn_{key}", use_container_width=True):
                st.session_state.show[key] = True; st.rerun()
        else:
            if has_voice:
                js_audio_button(content, key)
            else:
                st.markdown(f'<div class="ans-normal">{content}</div>', unsafe_allow_html=True)

    c_read, c_mean = st.columns(2)
    with c_read:
        reveal_section("읽기", "reading", row.iloc[2], has_voice=True)
    with c_mean:
        reveal_section("뜻", "mean", row.iloc[3])
    
    reveal_section("예문", "ex", row.iloc[4], has_voice=True)
    reveal_section("한자", "kanji", row.iloc[5] if len(row)>5 else "-")

    # 6. 하단 이동 버튼
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

    # --- [새로운 레벨링 엔진] ---
    total_learned = len(st.session_state.learned)
    
    # 117회차 총 단어수를 약 3510개로 가정할 때, 100레벨까지 지수 곡선 적용
    # 공식: level = (learned / 3510) ^ 0.7 * 99 + 1 (0.7은 초반 속도 보정치)
    if total_learned == 0:
        user_level = 1
        progress_val = 0
    else:
        # 현재 레벨 계산 (소수점 포함)
        raw_level = ((total_learned / 3510) ** 0.7) * 99 + 1
        user_level = int(raw_level)
        progress_val = raw_level - user_level # 현재 레벨 내에서의 진행도 (0~1)

    # 칭호 시스템 (100레벨 기준)
    if user_level <= 15: title, t_color = "일본어 신생아", "#888"
    elif user_level <= 40: title, t_color = "N2 훈련병", "#00FFAA"
    elif user_level <= 70: title, t_color = "단어 사냥꾼", "#00E1FF"
    elif user_level <= 90: title, t_color = "N2 상급 닌자", "#AA00FF"
    elif user_level < 100: title, t_color = "언어의 지배자", "#FF5500"
    else: title, t_color = "N2 마스터 (神)", "#FFD700"

    # 레벨 바 출력
    st.markdown(f"""
    <div style="margin-top:20px; padding:15px; background:#121212; border-radius:12px; border:1px solid #333; text-align:center; box-shadow: 0 4px 10px rgba(0,0,0,0.5);">
        <div style="color:{t_color}; font-size:0.85rem; font-weight:bold; letter-spacing:1px; margin-bottom:5px; text-shadow: 0 0 5px {t_color}55;">{title}</div>
        <div style="color:#FFF; font-weight:900; font-size: 1.4rem; letter-spacing: 1px;">LV. {user_level}</div>
        <div style="color:#555; font-size:0.7rem; margin-top:3px;">누적 암기 {total_learned} / 3510</div>
    </div>
    """, unsafe_allow_html=True)
    
    # 레벨 내부 진행도 바
    st.progress(min(progress_val, 1.0))

else:
    st.balloons()
    st.markdown("""
        <div style="text-align: center; padding: 50px 20px;">
            <h1 style="color: #00FFC6; font-size: 2.5rem;">ALL CLEAR</h1>
        </div>
    """, unsafe_allow_html=True)