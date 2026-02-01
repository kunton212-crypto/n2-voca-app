import streamlit as st
import pandas as pd
import random
import re
import streamlit.components.v1 as components

# 구글 시트 주소
SHEET_ID = "1KrgYU9dPGVWJgHeKJ4k4F6o0fqTtHvs7P5w7KmwSwwA"
CSV_URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv"

st.set_page_config(page_title="N2 단어장", page_icon="🎴", layout="centered")

# --- [초압축] 여백 제로 & 현황판 가시성 강화 ---
st.markdown("""
    <style>
    /* 전체 배경 고정 */
    .stApp { background-color: #121212 !important; }
    h1, h2, h3, h4, h5, h6, p, span, label, div { color: #FFFFFF !important; }
    
    /* [핵심] 최상단 여백 완전히 제거 */
    .block-container { 
        padding-top: 0px !important; 
        padding-bottom: 0px !important; 
        max-width: 100% !important;
    }

    /* 현황판 - 카드 상단에 딱 붙임 */
    .status-container {
        display: flex; justify-content: space-between; align-items: center;
        padding: 10px 5px 5px 5px;
        font-size: 0.9rem; font-weight: bold; color: #00FFAA !important;
    }

    /* 단어 카드 더 압축 */
    .word-card { 
        background-color: #1E1E1E !important; padding: 15px 10px !important; 
        border-radius: 12px; border: 1px solid #333; text-align: center; margin-bottom: 5px !important;
    }
    .japanese-word { font-size: clamp(2rem, 9vw, 3.2rem) !important; color: #FFD700 !important; margin: 0; }

    /* 정답 박스 한 줄 고정 */
    .reveal-row { display: flex; align-items: center; gap: 5px; margin-bottom: 4px; height: 40px; }
    .reveal-text {
        flex: 1; background-color: #2C2C2C; padding: 8px; border-radius: 8px;
        border: 1px solid #444; text-align: center; font-weight: bold;
        font-size: 0.9rem; white-space: nowrap; overflow: hidden; text-overflow: ellipsis;
    }
    
    /* 버튼 크기 최적화 */
    .stButton>button { height: 38px !important; border-radius: 8px !important; font-size: 0.85rem !important; }
    
    /* 프로그레스 바 슬림화 */
    .stProgress > div > div > div > div { height: 4px !important; }
    </style>
    """, unsafe_allow_html=True)

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

# 세션 상태
if 'idx' not in st.session_state: st.session_state.idx = 0
if 'learned_list' not in st.session_state: st.session_state.learned_list = set()
if 'show' not in st.session_state: st.session_state.show = {k:False for k in ["reading", "mean", "ex", "kanji"]}

with st.sidebar:
    if not df.empty:
        days = sorted(df['Day'].unique(), key=lambda x: int(x.replace("일차", "")))
        sel_day = st.selectbox("📅 구간", days)
        is_shuffle = st.toggle("🔀 순서 섞기", value=False)
        show_all = st.checkbox("✅ 외운 단어 포함", value=False)
        if st.button("🔄 기록 초기화"): st.session_state.learned_list = set(); st.rerun()
        if 'p_day' not in st.session_state or st.session_state.p_day != sel_day:
            st.session_state.idx = 0; st.session_state.p_day = sel_day

# 데이터 필터링
day_df = df[df['Day'] == sel_day].copy()
if is_shuffle: day_df = day_df.sample(frac=1, random_state=42).reset_index(drop=True)
else: day_df = day_df.reset_index(drop=True)

learned_count = len(day_df[day_df['GlobalID'].isin(st.session_state.learned_list)])
total_count = len(day_df)
display_df = day_df if show_all else day_df[~day_df['GlobalID'].isin(st.session_state.learned_list)].reset_index(drop=True)

if not display_df.empty:
    if st.session_state.idx >= len(display_df): st.session_state.idx = 0
    row = display_df.iloc[st.session_state.idx]
    
    # --- [위치 조정] 카드 위로 현황판 배치 ---
    st.markdown(f'<div class="status-container"><span>📍 {sel_day}</span><span>📊 {learned_count} / {total_count}</span></div>', unsafe_allow_html=True)
    st.progress(learned_count / total_count if total_count > 0 else 0)

    # 단어 카드
    st.markdown(f'<div class="word-card"><h1 class="japanese-word">{row.iloc[1]}</h1></div>', unsafe_allow_html=True)

    # 뒤집기 로직 (가로 한 줄 고정)
    def flip_row(label, key, content, speech=False):
        if not st.session_state.show[key]:
            if st.button(f"👁️ {label}", key=f"btn_{key}", use_container_width=True):
                st.session_state.show[key] = True; st.rerun()
        else:
            cols = st.columns([4.2, 0.8])
            cols[0].markdown(f'<div class="reveal-text">{content}</div>', unsafe_allow_html=True)
            with cols[1]:
                if speech:
                    if st.button("🔊", key=f"spk_{key}"): control_audio(content)
                else:
                    if st.button("X", key=f"cls_{key}"): 
                        st.session_state.show[key] = False; st.rerun()

    flip_row("읽기", "reading", row.iloc[2], speech=True)
    flip_row("뜻", "mean", row.iloc[3])
    flip_row("예문", "ex", row.iloc[4], speech=True)
    flip_row("한자풀이", "kanji", row.iloc[5] if len(row)>5 else "-")

    # 하단 조작
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
    st.success("해당 구간 클리어!"); st.balloons()