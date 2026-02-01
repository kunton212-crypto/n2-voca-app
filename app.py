import streamlit as st
import pandas as pd
import random
import re
import base64

# 구글 시트 주소
SHEET_ID = "1KrgYU9dPGVWJgHeKJ4k4F6o0fqTtHvs7P5w7KmwSwwA"
CSV_URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv"

st.set_page_config(page_title="N2", page_icon="🎴", layout="centered")

# --- [초압축 디자인] 폰 화면에 무조건 맞추기 ---
st.markdown("""
    <style>
    /* 1. 배경 및 전체 여백 제거 */
    .stApp { background-color: #000000 !important; }
    .block-container { padding: 0px !important; margin: 0px !important; }
    
    /* 2. 현황판을 카드 안쪽으로 배치 (가시성 확보) */
    .status-text {
        text-align: right; color: #00FFAA !important; font-size: 0.8rem;
        padding: 5px 15px 0 0; font-weight: bold;
    }

    /* 3. 카드 크기 대폭 축소 */
    .word-card { 
        background-color: #1A1A1A !important; padding: 15px 5px !important; 
        border-radius: 12px; border: 1px solid #333; text-align: center; 
        margin: 5px 10px !important;
    }
    .japanese-word { font-size: 2.5rem !important; color: #FFD700 !important; margin: 0; }

    /* 4. [핵심] 정답 한 줄 고정 로직 */
    .row-container {
        display: flex; align-items: center; justify-content: center;
        gap: 5px; margin: 0 10px 6px 10px;
    }
    .answer-box {
        flex: 1; background: #262626; padding: 10px 5px; border-radius: 8px;
        color: white; font-weight: bold; font-size: 0.9rem; text-align: center;
        border: 1px solid #444; min-height: 42px; display: flex; align-items: center; justify-content: center;
    }

    /* 버튼 스타일 압축 */
    .stButton>button { height: 42px !important; border-radius: 8px !important; font-size: 0.85rem !important; }
    .stProgress { margin: 0 10px !important; height: 4px !important; }
    </style>
    """, unsafe_allow_html=True)

# --- [무조건 성공] 구글 TTS API 직접 호출 방식 ---
def play_voice(text):
    clean = re.sub(r'[\(（].*?[\)）]', '', text).replace('*', '')
    # 구글 번역 TTS API를 활용하여 음성 파일 생성 없이 즉석 재생
    tts_url = f"https://translate.google.com/translate_tts?ie=UTF-8&q={clean}&tl=ja&client=tw-ob"
    audio_html = f"""
        <iframe src="{tts_url}" allow="autoplay" style="display:none"></iframe>
        <audio autoplay><source src="{tts_url}" type="audio/mpeg"></audio>
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
    
    # 1. 현황판 (카드 바로 위로 이동)
    st.markdown(f'<div class="status-text">📊 {len(learned_in_day)} / {len(day_df)}</div>', unsafe_allow_html=True)
    st.progress(len(learned_in_day) / len(day_df))

    # 2. 단어 카드
    st.markdown(f'<div class="word-card"><h1 class="japanese-word">{row.iloc[1]}</h1></div>', unsafe_allow_html=True)

    # 3. 인라인 리빌 (가로 한 줄 강제 고정)
    def reveal_item(label, key, content, speech=False):
        if not st.session_state.show[key]:
            if st.button(f"👁️ {label}", key=f"btn_{key}", use_container_width=True):
                st.session_state.show[key] = True; st.rerun()
        else:
            # 버튼이 사라지고 그 자리에 [정답 박스 + 스피커] 한 줄 배치
            c_text, c_spk = st.columns([4, 1])
            with c_text:
                st.markdown(f'<div class="answer-box">{content}</div>', unsafe_allow_html=True)
            with c_spk:
                if speech:
                    if st.button("🔊", key=f"spk_{key}"): play_voice(content)
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
        if st.button("⏭️ 패스", use_container_width=True):
            st.session_state.idx = (st.session_state.idx + 1) % len(display_df)
            st.session_state.show = {k:False for k in st.session_state.show}; st.rerun()
    with cr:
        if st.button("✅ 외웠다", type="primary", use_container_width=True):
            st.session_state.learned.add(row['GlobalID'])
            st.session_state.show = {k:False for k in st.session_state.show}; st.rerun()
else:
    st.balloons(); st.success("클리어!")