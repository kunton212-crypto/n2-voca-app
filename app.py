import streamlit as st
import pandas as pd
import re
import streamlit.components.v1 as components
import textwrap

# 1. 페이지 설정
st.set_page_config(page_title="JLPT N2 MASTER", page_icon="🎴", layout="centered")

# --- [스타일] 디자인 및 레이아웃 강제 고정 ---
# f-string 에러 방지를 위해 일반 문자열로 작성 후 주입
css_code = """
<link href="https://fonts.googleapis.com/css2?family=Noto+Sans+JP:wght@400;700;900&display=swap" rel="stylesheet">
<style>
/* 기본 초기화 */
*, *::before, *::after { box-sizing: border-box !important; }
html, body, [class*="css"] { font-family: 'Noto Sans JP', sans-serif !important; }
.stApp { background-color: #050505 !important; overflow-x: hidden !important; }

/* UI 요소 숨기기 */
#MainMenu, footer, header { visibility: hidden; }
.block-container { 
    padding-top: 1.5rem !important; 
    padding-left: 10px !important; padding-right: 10px !important;
    max-width: 100vw !important;
}

/* 모바일 2열 Grid 강제 고정 */
@media (max-width: 640px) {
    [data-testid="stHorizontalBlock"] {
        display: grid !important; 
        grid-template-columns: 1fr 1fr !important;
        gap: 10px !important; 
        width: 100% !important;
    }
    [data-testid="column"] { width: auto !important; flex: unset !important; min-width: 0 !important; }
    .stButton button { font-size: 0.85rem !important; padding: 0 !important; }
}

/* 테마 디자인 */
:root { --neon: #00FFC6; --dark: #121212; }

.status-box {
    background-color: var(--dark); padding: 12px; border-radius: 10px;
    color: var(--neon) !important; font-weight: bold; text-align: center;
    margin-bottom: 15px; width: 100%; border: 1px solid #333;
    box-shadow: 0 0 10px rgba(0, 255, 198, 0.2);
}

.word-card { 
    background: linear-gradient(145deg, #111, #050505);
    padding: 40px 10px; border-radius: 20px; 
    border: 1px solid #333; text-align: center; margin-bottom: 20px;
}
.japanese-word { font-size: 3.5rem !important; color: #fff !important; margin: 0; font-weight: 900; }

.ans-normal {
    background: #1a1a1a; color: #ccc; padding: 15px; width: 100%;
    border-radius: 10px; text-align: center; font-weight: 500;
    margin-bottom: 8px; border: 1px solid #333; display: block;
}

.stButton>button { 
    height: 52px !important; border-radius: 12px !important; 
    font-weight: 700 !important; width: 100% !important;
    background: #000 !important; border: 1px solid #444 !important; color: #888 !important;
}
.stButton>button:hover { border-color: var(--neon) !important; color: var(--neon) !important; }
button[kind="primary"] {
    background: var(--neon) !important; border: none !important; color: #000 !important;
    box-shadow: 0 0 15px rgba(0, 255, 198, 0.4) !important;
}

.stToggle label, .stCheckbox label { font-size: 13px !important; color: #777 !important; }
.stProgress > div > div > div > div { background-color: var(--neon) !important; }

/* 콤보박스 색상 */
div[data-baseweb="select"] > div { background-color: #111 !important; color: white !important; }
</style>
"""
st.markdown(css_code, unsafe_allow_html=True)

# --- [기능] 데이터 및 로직 ---
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

def js_audio_button(text, key_suffix):
    clean_text = re.sub(r'[\(（].*?[\)）]', '', text).replace('*', '').replace("'", "")
    html_code = f"""
    <html>
    <head>
    <style>
        body {{ margin: 0; padding: 0; background: transparent; overflow: hidden; }}
        .v-btn {{
            width: 100%; height: 52px; background: #111; color: #00FFC6;
            border: 1px solid #00FFC6; border-radius: 12px; font-weight: bold;
            display: flex; align-items: center; justify-content: center; cursor: pointer;
        }}
        .v-btn:active {{ background: #00FFC6; color: #000; }}
    </style>
    </head>
    <body>
        <button class="v-btn" onclick="spk()">{text}</button>
        <script>
            function spk() {{
                window.speechSynthesis.cancel();
                const m = new SpeechSynthesisUtterance('{clean_text}');
                m.lang = 'ja-JP';
                let v = window.speechSynthesis.getVoices();
                let jv = v.find(x => x.name.includes('Kyoko')) || v.find(x => x.lang === 'ja-JP');
                if(jv) m.voice = jv;
                window.speechSynthesis.speak(m);
            }}
        </script>
    </body>
    </html>
    """
    components.html(html_code, height=60, scrolling=False)

# 세션 관리
if 'idx' not in st.session_state: st.session_state.idx = 0
if 'learned' not in st.session_state: st.session_state.learned = set()
if 'show' not in st.session_state: st.session_state.show = {k:False for k in ["reading", "mean", "ex", "kanji"]}
if 'shuffle_seed' not in st.session_state: st.session_state.shuffle_seed = 42

# --- [메인 화면] ---
if not df.empty:
    days = sorted(df['Day'].unique(), key=lambda x: int(x.replace("일차", "")))
    
    # 상단 회차 선택 및 리셋
    t_c1, t_c2 = st.columns(2)
    with t_c1: sel_day = st.selectbox("DAY", days, label_visibility="collapsed")
    with t_c2: 
        if st.button("🔄 리셋", use_container_width=True):
            st.session_state.learned = set(); st.rerun()
    
    if 'p_day' not in st.session_state or st.session_state.p_day != sel_day:
        st.session_state.idx = 0; st.session_state.p_day = sel_day

    day_df = df[df['Day'] == sel_day].copy()

    # 옵션
    o1, o2 = st.columns(2)
    with o1: do_shuffle = st.toggle("순서 섞기", value=False)
    with o2: show_all = st.checkbox("복습 모드", value=False)

    if do_shuffle:
        day_df = day_df.sample(frac=1, random_state=st.session_state.shuffle_seed).reset_index(drop=True)

    display_df = day_df if show_all else day_df[~day_df['GlobalID'].isin(st.session_state.learned)].reset_index(drop=True)

    if not display_df.empty:
        if st.session_state.idx >= len(display_df): st.session_state.idx = 0
        row = display_df.iloc[st.session_state.idx]
        
        current_learned = len([i for i in st.session_state.learned if i in day_df['GlobalID'].values])
        st.markdown(f'<div class="status-box">PROGRESS {current_learned}/{len(day_df)}</div>', unsafe_allow_html=True)
        st.markdown(f'<div class="word-card"><h1 class="japanese-word">{row.iloc[1]}</h1></div>', unsafe_allow_html=True)

        def reveal(label, key, content, has_voice=False):
            if not st.session_state.show[key]:
                if st.button(f"{label} 확인", key=f"btn_{key}", use_container_width=True):
                    st.session_state.show[key] = True; st.rerun()
            else:
                if has_voice: js_audio_button(content, key)
                else: st.markdown(f'<div class="ans-normal">{content}</div>', unsafe_allow_html=True)

        c_r, c_m = st.columns(2)
        with c_r: reveal("읽기", "reading", row.iloc[2], True)
        with c_m: reveal("뜻", "mean", row.iloc[3])
        reveal("예문", "ex", row.iloc[4], True)
        reveal("한자", "kanji", row.iloc[5] if len(row)>5 else "-")

        st.write("")
        b1, b2 = st.columns(2)
        with b1:
            if st.button("패스", use_container_width=True):
                st.session_state.idx = (st.session_state.idx + 1) % len(display_df)
                st.session_state.show = {k:False for k in st.session_state.show}; st.rerun()
        with b2:
            if st.button("암기 완료", type="primary", use_container_width=True):
                st.session_state.learned.add(row['GlobalID'])
                st.session_state.show = {k:False for k in st.session_state.show}; st.rerun()

        # --- [레벨링 시스템] ---
        total_learned = len(st.session_state.learned)
        max_words = 3510  # 117회차 총 예상 단어수
        if total_learned == 0:
            u_lv, p_val = 1, 0.0
        else:
            raw_lv = ((total_learned / max_words) ** 0.7) * 99 + 1
            u_lv = int(raw_lv)
            p_val = raw_lv - u_lv

        # 칭호 결정
        if u_lv <= 15: title, color = "N2 입문자", "#888"
        elif u_lv <= 40: title, color = "단어 사냥꾼", "#00FFAA"
        elif u_lv <= 75: title, color = "N2 베테랑", "#00E1FF"
        elif u_lv <= 95: title, color = "언어의 지배자", "#AA00FF"
        else: title, color = "N2 마스터 (神)", "#FFD700"

        st.markdown(f"""
        <div style="margin-top:25px; padding:15px; background:#111; border-radius:15px; border:1px solid #333; text-align:center;">
            <div style="color:{color}; font-size:0.8rem; font-weight:bold; letter-spacing:1px; margin-bottom:5px;">{title}</div>
            <div style="color:#FFF; font-weight:900; font-size: 1.3rem;">LV. {u_lv}</div>
            <div style="color:#444; font-size:0.7rem; margin-top:5px;">TOTAL {total_learned} / {max_words}</div>
        </div>
        """, unsafe_allow_html=True)
        st.progress(min(p_val, 1.0))

    else:
        st.balloons()
        st.markdown('<h1 style="text-align:center; color:#00FFC6; margin-top:50px;">ALL CLEAR!</h1>', unsafe_allow_html=True)