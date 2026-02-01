import streamlit as st
import pandas as pd
import random
import re
import streamlit.components.v1 as components

# 구글 시트 주소
SHEET_ID = "1KrgYU9dPGVWJgHeKJ4k4F6o0fqTtHvs7P5w7KmwSwwA"
CSV_URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv"

st.set_page_config(page_title="N2 단어장", page_icon="🎴", layout="centered")

# --- [초압축 & 고대비] 스타일 (현황판 가시성 100%) ---
st.markdown("""
    <style>
    .stApp { background-color: #000000 !important; } /* 배경을 완전 검정으로 */
    h1, h2, h3, h4, h5, h6, p, span, label, div { color: #FFFFFF !important; }
    .block-container { padding: 0px 10px !important; }

    /* 현황판을 화면 최상단에 배경색과 함께 고정 */
    .status-bar {
        background-color: #1E1E1E; padding: 10px; border-radius: 0 0 10px 10px;
        display: flex; justify-content: space-between; font-weight: bold;
        color: #00FFAA !important; font-size: 0.9rem; border-bottom: 2px solid #00FFAA;
    }

    /* 단어 카드 여백 최소화 */
    .word-card { 
        background-color: #111111 !important; padding: 15px 5px !important; 
        border-radius: 12px; border: 1px solid #333; text-align: center; margin-top: 10px;
    }
    .japanese-word { font-size: 3rem !important; color: #FFD700 !important; margin: 0; }

    /* 정답 박스와 음성 버튼을 같은 줄에 배치 */
    .answer-row { display: flex; align-items: center; gap: 5px; margin-bottom: 5px; }
    .answer-text { 
        flex: 1; background: #222; padding: 10px; border-radius: 8px; border: 1px solid #444;
        font-size: 0.95rem; font-weight: bold; text-align: center; color: #FFF !important;
    }

    /* 버튼 스타일 */
    .stButton>button { height: 42px !important; border-radius: 8px !important; }
    </style>
    """, unsafe_allow_html=True)

# --- [핵심] 폰에서 소리 나게 하는 자바스크립트 ---
def play_audio_js(text):
    clean = re.sub(r'[\(（].*?[\)）]', '', text).replace('*', '').replace("'", "\\'")
    js_code = f"""
        <script>
        window.speechSynthesis.cancel();
        var msg = new SpeechSynthesisUtterance('{clean}');
        msg.lang = 'ja-JP';
        msg.rate = 1.0;
        window.speechSynthesis.speak(msg);
        </script>
    """
    components.html(js_code, height=0)

@st.cache_data(ttl=60)
def load_data():
    try:
        df = pd.read_csv(CSV_URL).fillna(" ")
        df['Day'] = ((df.index) // 30 + 1).astype(str) + "일차"
        df['GlobalID'] = df.index
        return df
    except: return pd.DataFrame()

df = load_data()

# 세션 상태
if 'idx' not in st.session_state: st.session_state.idx = 0
if 'learned_list' not in st.session_state: st.session_state.learned_list = set()
if 'show' not in st.session_state: st.session_state.show = {k:False for k in ["reading", "mean", "ex", "kanji"]}

with st.sidebar:
    if not df.empty:
        days = sorted(df['Day'].unique(), key=lambda x: int(x.replace("일차", "")))
        sel_day = st.selectbox("📅 구간", days)
        if st.button("🔄 기록 초기화"): st.session_state.learned_list = set(); st.rerun()
        if 'p_day' not in st.session_state or st.session_state.p_day != sel_day:
            st.session_state.idx = 0; st.session_state.p_day = sel_day

# 필터링
day_df = df[df['Day'] == sel_day].reset_index(drop=True)
learned_count = len(day_df[day_df['GlobalID'].isin(st.session_state.learned_list)])
display_df = day_df[~day_df['GlobalID'].isin(st.session_state.learned_list)].reset_index(drop=True)

if not display_df.empty:
    if st.session_state.idx >= len(display_df): st.session_state.idx = 0
    row = display_df.iloc[st.session_state.idx]
    
    # 1. 현황판 (최상단 고정)
    st.markdown(f'<div class="status-bar"><span>📍 {sel_day}</span><span>📊 {learned_count} / {len(day_df)}</span></div>', unsafe_allow_html=True)
    st.progress(learned_count / len(day_df))

    # 2. 단어 카드
    st.markdown(f'<div class="word-card"><h1 class="japanese-word">{row.iloc[1]}</h1></div>', unsafe_allow_html=True)

    # 3. 정답 확인 (한 줄 레이아웃)
    def reveal_item(label, key, content, speech=False):
        if not st.session_state.show[key]:
            if st.button(f"👁️ {label}", key=f"btn_{key}", use_container_width=True):
                st.session_state.show[key] = True; st.rerun()
        else:
            c_text, c_btn = st.columns([4, 1])
            with c_text:
                st.markdown(f'<div class="answer-text">{content}</div>', unsafe_allow_html=True)
            with c_btn:
                if speech:
                    if st.button("🔊", key=f"spk_{key}"): play_audio_js(content)
                else:
                    if st.button("X", key=f"cls_{key}"): st.session_state.show[key] = False; st.rerun()

    reveal_item("읽기", "reading", row.iloc[2], speech=True)
    reveal_item("뜻", "mean", row.iloc[3])
    reveal_item("예문", "ex", row.iloc[4], speech=True)
    reveal_item("한자", "kanji", row.iloc[5] if len(row)>5 else "-")

    # 4. 하단 버튼
    st.write("")
    cl, cr = st.columns(2)
    with cl:
        if st.button("⏭️ 패스"):
            st.session_state.idx = (st.session_state.idx + 1) % len(display_df)
            st.session_state.show = {k:False for k in st.session_state.show}; st.rerun()
    with cr:
        if st.button("✅ 외웠다", type="primary"):
            st.session_state.learned_list.add(row['GlobalID'])
            st.session_state.show = {k:False for k in st.session_state.show}; st.rerun()
else:
    st.success("클리어!"); st.balloons()