import streamlit as st
import pandas as pd
import random
import re

# 구글 시트 주소
SHEET_ID = "1KrgYU9dPGVWJgHeKJ4k4F6o0fqTtHvs7P5w7KmwSwwA"
CSV_URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv"

st.set_page_config(page_title="N2", page_icon="🎴", layout="centered")

# --- [초압축 디자인] 버튼 삭제 및 터치 영역 최적화 ---
st.markdown("""
    <style>
    .stApp { background-color: #000000 !important; }
    .block-container { padding-top: 1.5rem !important; padding-bottom: 0px !important; }
    
    /* 현황판 */
    .status-box {
        background-color: #1E1E1E; padding: 8px; border-radius: 8px;
        color: #00FFAA !important; font-weight: bold; text-align: center;
        margin-bottom: 8px; font-size: 0.9rem;
    }

    /* 단어 카드 */
    .word-card { 
        background-color: #1A1A1A; padding: 20px 10px; border-radius: 12px; 
        border: 1px solid #444; text-align: center; margin-bottom: 10px;
    }
    .japanese-word { font-size: 2.8rem !important; color: #FFFFFF !important; margin: 0; }

    /* 정답 터치 박스 (클릭 가능한 느낌을 줌) */
    .ans-clickable { 
        background: #262626; color: #00FFAA; padding: 12px; 
        border-radius: 8px; text-align: center; font-weight: bold; 
        margin-bottom: 5px; border: 1px solid #00FFAA;
        cursor: pointer;
    }
    .ans-normal {
        background: #262626; color: #FFFFFF; padding: 12px; 
        border-radius: 8px; text-align: center; font-weight: bold; 
        margin-bottom: 5px; border: 1px solid #444;
    }

    /* 하단 조작 버튼 크기 축소 */
    .stButton>button { height: 42px !important; border-radius: 8px !important; }
    </style>
    """, unsafe_allow_html=True)

# --- 자바스크립트 음성 재생 함수 ---
def play_voice(text):
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

# 사이드바
with st.sidebar:
    if not df.empty:
        days = sorted(df['Day'].unique(), key=lambda x: int(x.replace("일차", "")))
        sel_day = st.selectbox("구간", days)
        if st.button("🔄 초기화"): st.session_state.learned = set(); st.rerun()
        if 'p_day' not in st.session_state or st.session_state.p_day != sel_day:
            st.session_state.idx = 0; st.session_state.p_day = sel_day

day_df = df[df['Day'] == sel_day].reset_index(drop=True)
learned_in_day = [i for i in st.session_state.learned if i in day_df['GlobalID'].values]
display_df = day_df[~day_df['GlobalID'].isin(st.session_state.learned)].reset_index(drop=True)

if not display_df.empty:
    if st.session_state.idx >= len(display_df): st.session_state.idx = 0
    row = display_df.iloc[st.session_state.idx]
    
    # 1. 현황판
    st.markdown(f'<div class="status-box">📊 {sel_day}: {len(learned_in_day)} / {len(day_df)}</div>', unsafe_allow_html=True)

    # 2. 단어 카드
    st.markdown(f'<div class="word-card"><h1 class="japanese-word">{row.iloc[1]}</h1></div>', unsafe_allow_html=True)

    # 3. 터치형 정답 확인 로직
    def touch_reveal(label, key, content, has_voice=False):
        if not st.session_state.show[key]:
            # 아직 안 봤을 때는 '확인' 버튼
            if st.button(f"👁️ {label} 확인", key=f"btn_{key}"):
                st.session_state.show[key] = True; st.rerun()
        else:
            # 봤을 때는 텍스트 상자 노출
            if has_voice:
                # 소리 나는 박스는 민트색 테두리 + 클릭 시 소리 재생
                if st.button(f"🔊 {content}", key=f"txt_{key}"):
                    play_voice(content)
            else:
                # 소리 없는 박스는 일반 회색 테두리
                st.markdown(f'<div class="ans-normal">{content}</div>', unsafe_allow_html=True)

    touch_reveal("읽기", "reading", row.iloc[2], has_voice=True)
    touch_reveal("뜻", "mean", row.iloc[3])
    touch_reveal("예문", "ex", row.iloc[4], has_voice=True)
    touch_reveal("한자", "kanji", row.iloc[5] if len(row)>5 else "-")

    # 4. 하단 조작
    st.write("")
    cl, cr = st.columns(2)
    with cl:
        if st.button("⏭️ 패스"):
            st.session_state.idx = (st.session_state.idx + 1) % len(display_df)
            st.session_state.show = {k:False for k in st.session_state.show}; st.rerun()
    with cr:
        if st.button("✅ 외웠다", type="primary"):
            st.session_state.learned.add(row['GlobalID'])
            st.session_state.show = {k:False for k in st.session_state.show}; st.rerun()
else:
    st.success("해당 구간을 모두 정복했습니다!"); st.balloons()