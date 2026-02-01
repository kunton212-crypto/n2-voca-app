import streamlit as st
import pandas as pd
import random
import re
import streamlit.components.v1 as components

# 구글 시트 주소
SHEET_ID = "1KrgYU9dPGVWJgHeKJ4k4F6o0fqTtHvs7P5w7KmwSwwA"
CSV_URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv"

st.set_page_config(page_title="N2 단어장", page_icon="🎴", layout="centered")

# --- [모바일 최적화 CSS] ---
st.markdown("""
    <style>
    /* 전체 배경 및 텍스트 고정 */
    .stApp { background-color: #121212 !important; }
    h1, h2, h3, h4, h5, h6, p, span, label, div { color: #FFFFFF !important; }
    
    /* 카드 크기 축소 및 모바일 대응 */
    .word-card { 
        background-color: #1E1E1E !important; 
        padding: 30px 10px !important; 
        border-radius: 15px; 
        border: 1px solid #333; 
        text-align: center; 
        margin-bottom: 10px !important;
    }
    
    /* 단어 폰트 크기 조절 (모바일 우선) */
    .japanese-word { 
        font-size: clamp(2.5rem, 8vw, 4.5rem) !important; 
        color: #FFD700 !important; 
        font-weight: 800 !important; 
        margin: 0;
    }

    /* 정보 박스 슬림화 */
    .reveal-box {
        background-color: #2C2C2C !important;
        padding: 8px 12px !important;
        border-radius: 8px;
        border: 1px solid #444;
        margin-bottom: 5px !important;
        font-size: 0.95rem;
    }
    .hidden-box {
        background-color: #1A1A1A !important;
        padding: 8px !important;
        border-radius: 8px;
        text-align: center;
        color: #888 !important;
        border: 1px dashed #555;
        font-size: 0.9rem;
    }

    /* 버튼 간격 및 높이 최적화 */
    .stButton>button {
        height: 2.8em !important;
        padding: 0 !important;
        font-size: 0.9rem !important;
        border-radius: 10px !important;
    }
    
    /* 불필요한 Streamlit 기본 여백 제거 */
    .block-container { padding-top: 1rem !important; padding-bottom: 1rem !important; }
    </style>
    """, unsafe_allow_html=True)

# --- 음성 제어 ---
def control_audio(text, action="play"):
    if action == "stop":
        js = "<script>window.speechSynthesis.cancel();</script>"
    else:
        clean = re.sub(r'[\(（].*?[\)）]', '', text).replace('*', '').replace("'", "\\'")
        js = f"<script>window.speechSynthesis.cancel(); var msg = new SpeechSynthesisUtterance('{clean}'); msg.lang = 'ja-JP'; msg.rate = 1.0; window.speechSynthesis.speak(msg);</script>"
    components.html(js, height=0)

@st.cache_data(ttl=60)
def load_data():
    try:
        df = pd.read_csv(CSV_URL).fillna("정보 없음")
        df['Day'] = ((df.index) // 30 + 1).astype(str) + "일차"
        df['GlobalID'] = df.index
        return df
    except: return pd.DataFrame()

df = load_data()

# --- 세션 상태 ---
if 'idx' not in st.session_state: st.session_state.idx = 0
if 'learned_list' not in st.session_state: st.session_state.learned_list = set()
if 'show' not in st.session_state: st.session_state.show = {k:False for k in ["reading", "mean", "ex", "kanji"]}

# 사이드바
with st.sidebar:
    st.header("⚙️ 설정")
    if not df.empty:
        days = sorted(df['Day'].unique(), key=lambda x: int(x.replace("일차", "")))
        sel_day = st.selectbox("구간", days)
        show_all = st.checkbox("외운 단어 포함", value=False)
        if st.button("기록 초기화"): st.session_state.learned_list = set(); st.rerun()
        if 'p_day' not in st.session_state or st.session_state.p_day != sel_day:
            st.session_state.idx = 0; st.session_state.p_day = sel_day

# 데이터 필터링
day_df = df[df['Day'] == sel_day].reset_index(drop=True)
display_df = day_df if show_all else day_df[~day_df['GlobalID'].isin(st.session_state.learned_list)].reset_index(drop=True)

if not display_df.empty:
    if st.session_state.idx >= len(display_df): st.session_state.idx = 0
    row = display_df.iloc[st.session_state.idx]
    
    # 상단 요약 (한 줄 배치)
    col_info, col_count = st.columns([1, 1])
    col_info.caption(f"📍 {sel_day} ({st.session_state.idx + 1}/{len(display_df)})")
    col_count.caption(f"✅ 외운 단어: {len(st.session_state.learned_list)}개")
    st.progress((st.session_state.idx + 1) / len(display_df))

    # 단어 카드
    st.markdown(f'<div class="word-card"><h1 class="japanese-word">{row.iloc[1]}</h1></div>', unsafe_allow_html=True)

    # 정보 영역 (레이아웃 압축)
    def reveal_compact(label, key, content, speech=False):
        c1, c2, c3 = st.columns([0.8, 2, 0.4])
        with c1:
            if st.button(f"👁️{label}", key=f"b_{key}", use_container_width=True):
                st.session_state.show[key] = True; st.rerun()
        with c2:
            if st.session_state.show[key]: st.markdown(f'<div class="reveal-box">{content}</div>', unsafe_allow_html=True)
            else: st.markdown('<div class="hidden-box">???</div>', unsafe_allow_html=True)
        with c3:
            if speech and st.session_state.show[key]:
                if st.button("🔊", key=f"p_{key}"): control_audio(content)

    reveal_compact("읽기", "reading", row.iloc[2], speech=True)
    reveal_compact("뜻", "mean", row.iloc[3])
    reveal_compact("예문", "ex", row.iloc[4], speech=True)
    reveal_compact("한자", "kanji", row.iloc[5] if len(row)>5 else "-")

    # 하단 네비게이션
    st.write("")
    cl, cr = st.columns(2)
    with cl:
        if st.button("⏭️ 넘기기", use_container_width=True):
            st.session_state.idx = (st.session_state.idx + 1) % len(display_df)
            st.session_state.show = {k:False for k in st.session_state.show}; st.rerun()
    with cr:
        if st.button("✅ 외웠다", type="primary", use_container_width=True):
            st.session_state.learned_list.add(row['GlobalID'])
            st.session_state.show = {k:False for k in st.session_state.show}; st.rerun()
else:
    st.balloons(); st.success("클리어! 복습하시겠어요?")