import streamlit as st
import pandas as pd
import re

# 구글 시트 주소
SHEET_ID = "1KrgYU9dPGVWJgHeKJ4k4F6o0fqTtHvs7P5w7KmwSwwA"
CSV_URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv"

st.set_page_config(page_title="JLPT N2", page_icon="🎴", layout="centered")

# --- [디자인] 사용자 스타일 + 터치 음성 UI ---
st.markdown("""
    <style>
    .stApp { background-color: #000000 !important; }
    .block-container { padding-top: 3rem !important; }
    
    .status-box {
        background-color: #1E1E1E; padding: 10px; border-radius: 10px;
        color: #00FFAA !important; font-weight: bold; text-align: center;
        margin-bottom: 10px; border: 1.5px solid #00FFAA;
    }

    .word-card { 
        background-color: #1A1A1A; padding: 25px 10px; border-radius: 15px; 
        border: 1px solid #444; text-align: center; margin-bottom: 10px; 
    }
    .japanese-word { font-size: 3.2rem !important; color: #FFFFFF !important; margin: 0; font-weight: 800; }

    /* 정답 박스: 터치 가능한 느낌을 주도록 민트색 테두리 추가 */
    .ans-box { 
        background: #262626; color: #00FFAA; padding: 12px; 
        border-radius: 8px; text-align: center; font-weight: bold; 
        margin-bottom: 6px; border: 1px solid #00FFAA;
        cursor: pointer;
    }
    
    .stButton>button { height: 48px !important; border-radius: 12px !important; font-weight: bold !important; }

    .growth-log {
        margin-top: 15px; padding: 10px; background: #111; border-radius: 10px;
        border: 1px dashed #444; text-align: center;
    }
    .level-text { color: #FFD700 !important; font-size: 0.9rem; font-weight: bold; }
    </style>
    """, unsafe_allow_html=True)

# --- [핵심] 아이폰용 음성 재생 자바스크립트 ---
def play_audio_js(text):
    clean = re.sub(r'[\(（].*?[\)）]', '', text).replace('*', '').replace("'", "\\'")
    tts_url = f"https://translate.google.com/translate_tts?ie=UTF-8&q={clean}&tl=ja&client=tw-ob"
    st.components.v1.html(f"""
        <script>
            var audio = new Audio("{tts_url}");
            audio.play();
        </script>
    """, height=0)

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

with st.sidebar:
    if not df.empty:
        days = sorted(df['Day'].unique(), key=lambda x: int(x.replace("일차", "")))
        sel_day = st.selectbox("구간 선택", days)
        if st.button("🔄 전체 초기화"): 
            st.session_state.learned = set()
            st.rerun()
        if 'p_day' not in st.session_state or st.session_state.p_day != sel_day:
            st.session_state.idx = 0; st.session_state.p_day = sel_day

day_df = df[df['Day'] == sel_day].reset_index(drop=True)
total_learned = len(st.session_state.learned) 
current_day_learned = [i for i in st.session_state.learned if i in day_df['GlobalID'].values]
display_df = day_df[~day_df['GlobalID'].isin(st.session_state.learned)].reset_index(drop=True)

if not display_df.empty:
    if st.session_state.idx >= len(display_df): st.session_state.idx = 0
    row = display_df.iloc[st.session_state.idx]
    
    # 1. 현황판
    st.markdown(f'<div class="status-box">📊 {sel_day} : {len(current_day_learned)} / {len(day_df)}</div>', unsafe_allow_html=True)

    # 2. 단어 카드
    st.markdown(f'<div class="word-card"><h1 class="japanese-word">{row.iloc[1]}</h1></div>', unsafe_allow_html=True)

    # 3. 정답 확인 (터치 시 음성 재생)
    def reveal_and_play(label, key, content, can_play=False):
        if not st.session_state.show[key]:
            if st.button(f"👁️ {label} 확인", key=f"btn_{key}"):
                st.session_state.show[key] = True; st.rerun()
        else:
            # 버튼 형식으로 정답을 보여주어 터치 시 소리 재생 유도
            if can_play:
                if st.button(f"{content}", key=f"play_{key}"):
                    play_audio_js(content)
            else:
                st.markdown(f'<div class="ans-box">{content}</div>', unsafe_allow_html=True)

    reveal_and_play("읽기", "reading", row.iloc[2], can_play=True)
    reveal_and_play("뜻", "mean", row.iloc[3])
    reveal_and_play("예문", "ex", row.iloc[4], can_play=True)
    reveal_and_play("한자", "kanji", row.iloc[5] if len(row)>5 else "-")

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

    # 5. 성장 로그
    user_level = (total_learned // 10) + 1
    exp_in_level = total_learned % 10
    st.markdown(f'<div class="growth-log"><span class="level-text">🔥 LV.{user_level} (누적 {total_learned}개)</span></div>', unsafe_allow_html=True)
    st.progress(exp_in_level / 10)

else:
    st.balloons(); st.success("클리어!")