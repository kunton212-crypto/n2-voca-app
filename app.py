import streamlit as st
import pandas as pd
import random
import re
import streamlit.components.v1 as components

# 구글 시트 주소
SHEET_ID = "1KrgYU9dPGVWJgHeKJ4k4F6o0fqTtHvs7P5w7KmwSwwA"
CSV_URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv"

st.set_page_config(page_title="N2 단어장", page_icon="🎴", layout="centered")

# --- 스타일 설정 ---
st.markdown("""
    <style>
    .stApp { background-color: #121212 !important; }
    h1, h2, h3, h4, h5, h6, p, span, label, div { color: #FFFFFF !important; }
    .word-card { 
        background-color: #1E1E1E !important; padding: 25px 10px !important; 
        border-radius: 15px; border: 1px solid #333; text-align: center; margin-bottom: 12px !important;
    }
    .japanese-word { font-size: clamp(2.5rem, 10vw, 4rem) !important; color: #FFD700 !important; font-weight: 800 !important; margin: 0; }
    .reveal-text {
        background-color: #2C2C2C !important; padding: 10px; border-radius: 10px; border: 1px solid #444;
        text-align: center; font-weight: bold; min-height: 45px; display: flex; align-items: center; justify-content: center; font-size: 1rem;
    }
    .stButton>button { height: 45px !important; border-radius: 10px !important; font-weight: 600 !important; }
    .status-text { font-size: 0.9rem; font-weight: bold; color: #00FFAA !important; margin-bottom: 5px; }
    .block-container { padding-top: 0.5rem !important; padding-bottom: 0.5rem !important; }
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

# --- 세션 상태 ---
if 'idx' not in st.session_state: st.session_state.idx = 0
if 'learned_list' not in st.session_state: st.session_state.learned_list = set()
if 'show' not in st.session_state: st.session_state.show = {k:False for k in ["reading", "mean", "ex", "kanji"]}
if 'shuffle_seed' not in st.session_state: st.session_state.shuffle_seed = 0

with st.sidebar:
    st.header("⚙️ 설정")
    if not df.empty:
        days = sorted(df['Day'].unique(), key=lambda x: int(x.replace("일차", "")))
        sel_day = st.selectbox("📅 구간", days)
        is_shuffle = st.toggle("🔀 순서 섞기", value=False)
        show_all = st.checkbox("✅ 외운 단어 포함", value=False)
        if st.button("🔄 기록 초기화"):
            st.session_state.learned_list = set()
            st.rerun()
        if 'p_day' not in st.session_state or st.session_state.p_day != sel_day:
            st.session_state.idx = 0; st.session_state.p_day = sel_day; st.session_state.shuffle_seed += 1

# 데이터 필터링
day_df = df[df['Day'] == sel_day].copy()
if is_shuffle:
    day_df = day_df.sample(frac=1, random_state=st.session_state.shuffle_seed).reset_index(drop=True)
else:
    day_df = day_df.reset_index(drop=True)

# 현재 구간에서 외운 단어 수 계산 (진행률 표시용)
learned_in_day = day_df[day_df['GlobalID'].isin(st.session_state.learned_list)]
learned_count = len(learned_in_day)
total_count = len(day_df)

# 실제 보여줄 단어 (외운 것 제외 혹은 포함)
display_df = day_df if show_all else day_df[~day_df['GlobalID'].isin(st.session_state.learned_list)].reset_index(drop=True)

if not display_df.empty:
    if st.session_state.idx >= len(display_df): st.session_state.idx = 0
    row = display_df.iloc[st.session_state.idx]
    
    # --- [업데이트] 상단 학습 현황 영역 ---
    st.markdown(f'<div class="status-text">📊 {sel_day} 학습 현황: {learned_count} / {total_count}</div>', unsafe_allow_html=True)
    st.progress(learned_count / total_count if total_count > 0 else 0)

    st.markdown(f'<div class="word-card"><h1 class="japanese-word">{row.iloc[1]}</h1></div>', unsafe_allow_html=True)

    def flip_row(label, key, content, speech=False):
        if not st.session_state.show[key]:
            if st.button(f"👁️ {label}", key=f"btn_{key}", use_container_width=True):
                st.session_state.show[key] = True; st.rerun()
        else:
            c_txt, c_spk = st.columns([4, 1])
            with c_txt: st.markdown(f'<div class="reveal-text">{content}</div>', unsafe_allow_html=True)
            with c_spk:
                if speech:
                    if st.button("🔊", key=f"spk_{key}"): control_audio(content)
                else:
                    if st.button("⏹️", key=f"cls_{key}"): st.session_state.show[key] = False; st.rerun()

    flip_row("읽기", "reading", row.iloc[2], speech=True)
    flip_row("뜻", "mean", row.iloc[3])
    flip_row("예문", "ex", row.iloc[4], speech=True)
    flip_row("한자풀이", "kanji", row.iloc[5] if len(row)>5 else "-")

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
    st.markdown(f'<div class="status-text">📊 {sel_day} 학습 현황: {learned_count} / {total_count}</div>', unsafe_allow_html=True)
    st.progress(1.0)
    st.balloons(); st.success("완벽합니다! 해당 구간을 마스터했습니다.")