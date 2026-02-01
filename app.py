import streamlit as st
import pandas as pd
import random
import re

# 구글 시트 주소
SHEET_ID = "1KrgYU9dPGVWJgHeKJ4k4F6o0fqTtHvs7P5w7KmwSwwA"
CSV_URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv"

st.set_page_config(page_title="N2", page_icon="🎴", layout="centered")

# --- [초압축 디자인] 폰 화면에 무조건 맞추기 ---
st.markdown("""
    <style>
    /* 1. 배경 및 전체 여백 강제 조정 */
    .stApp { background-color: #000000 !important; }
    /* 현황판을 위해 상단 여백을 살짝 확보 */
    .block-container { padding: 35px 10px 0px 10px !important; margin: 0px !important; }
    
    /* 2. 현황판을 상단에 고정 (민트색 텍스트) */
    .status-bar {
        position: fixed; top: 0; left: 0; right: 0; z-index: 999;
        background: #1A1A1A; padding: 8px 15px;
        display: flex; justify-content: space-between;
        border-bottom: 1px solid #333; font-size: 0.85rem; font-weight: bold;
        color: #00FFAA !important;
    }

    /* 3. 카드 디자인 (단어 색상: 흰색) */
    .word-card { 
        background-color: #1A1A1A !important; padding: 20px 5px !important; 
        border-radius: 12px; border: 1px solid #333; text-align: center; 
        margin-bottom: 8px !important;
    }
    .japanese-word { 
        font-size: 2.8rem !important; 
        color: #FFFFFF !important; /* 노란색에서 흰색으로 변경 */
        margin: 0; 
    }

    /* 4. 버튼 및 텍스트 레이아웃 압축 */
    .answer-box {
        background: #262626; padding: 10px 5px; border-radius: 8px;
        color: white; font-weight: bold; font-size: 0.9rem; text-align: center;
        border: 1px solid #444; width: 100%; min-height: 42px;
        display: flex; align-items: center; justify-content: center;
    }

    .stButton>button { height: 42px !important; border-radius: 8px !important; font-size: 0.85rem !important; }
    .stProgress { height: 4px !important; margin-bottom: 10px !important; }
    </style>
    """, unsafe_allow_html=True)

# --- [아이폰 대응] 음성 재생 로직 ---
def play_voice(text):
    clean = re.sub(r'[\(（].*?[\)）]', '', text).replace('*', '')
    # 구글 번역 TTS를 활용한 자동 재생 유도
    tts_url = f"https://translate.google.com/translate_tts?ie=UTF-8&q={clean}&tl=ja&client=tw-ob"
    audio_html = f"""
        <audio autoplay><source src="{tts_url}" type="audio/mpeg"></audio>
        <iframe src="{tts_url}" allow="autoplay" style="display:none"></iframe>
    """
    st.markdown(audio_html, unsafe_allow_html=True)

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
if 'learned' not in st.session_state: st.session_state.learned = set()
if 'show' not in st.session_state: st.session_state.show = {k:False for k in ["reading", "mean", "ex", "kanji"]}

with st.sidebar:
    if not df.empty:
        days = sorted(df['Day'].unique(), key=lambda x: int(x.replace("일차", "")))
        sel_day = st.selectbox("구간", days)
        if st.button("🔄 초기화"): st.session_state.learned = set(); st.rerun()
        if 'p_day' not in st.session_state or st.session_state.p_day != sel_day:
            st.session_state.idx = 0; st.session_state.p_day = sel_day

# 필터링
day_df = df[df['Day'] == sel_day].reset_index(drop=True)
learned_in_day = [i for i in st.session_state.learned if i in day_df['GlobalID'].values]
display_df = day_df[~day_df['GlobalID'].isin(st.session_state.learned)].reset_index(drop=True)

if not display_df.empty:
    if st.session_state.idx >= len(display_df): st.session_state.idx = 0
    row = display_df.iloc[st.session_state.idx]
    
    # 1. 현황판 (상단 고정 바)
    st.markdown(f'''
        <div class="status-bar">
            <span>📍 {sel_day}</span>
            <span>📊 {len(learned_in_day)} / {len(day_df)}</span>
        </div>
    ''', unsafe_allow_html=True)
    st.progress(len(learned_in_day) / len(day_df))

    # 2. 단어 카드 (글자색 흰색)
    st.markdown(f'<div class="word-card"><h1 class="japanese-word">{row.iloc[1]}</h1></div>', unsafe_allow_html=True)

    # 3. 인라인 리빌 (가로 한 줄 강제 고정)
    def reveal_item(label, key, content, speech=False):
        if not st.session_state.show[key]:
            if st.button(f"👁️ {label}", key=f"btn_{key}", use_container_width=True):
                st.session_state.show[key] = True; st.rerun()
        else:
            if speech:
                col_t, col_s = st.columns([4, 1])
                with col_t: st.markdown(f'<div class="answer-box">{content}</div>', unsafe_allow_html=True)
                with col_s: 
                    if st.button("🔊", key=f"spk_{key}"): play_voice(content)
            else:
                st.markdown(f'<div class="answer-box">{content}</div>', unsafe_allow_html=True)

    reveal_item("읽기", "reading", row.iloc[2], speech=True)
    reveal_item("뜻", "mean", row.iloc[3])
    reveal_item("예문", "ex", row.iloc[4], speech=True)
    reveal_item("한자", "kanji", row.iloc[5] if len(row)>5 else "-")

    st.write("")
    cl, cr = st.columns(2)
    with cl:
        if st.button("⏭️ 패스", use_container_width=True):
            st.session_state.idx = (st.session_state.idx + 1) % len(display_df)
            st.session_state.show = {k:False for k in st.session_state.show}; st.rerun()
    with cr:
        if st.button("✅ 외웠다", type="primary", use_container_width=True):
            st.session_state.learned.add(row['GlobalID'])
            st.session_state.show = {k:False for k in st.session_state.show}; st.rerun()
else:
    st.balloons(); st.success("클리어!")