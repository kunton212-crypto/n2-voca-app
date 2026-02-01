import streamlit as st
import pandas as pd
import random
import re

# 구글 시트 주소
SHEET_ID = "1KrgYU9dPGVWJgHeKJ4k4F6o0fqTtHvs7P5w7KmwSwwA"
CSV_URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv"

st.set_page_config(page_title="N2", page_icon="🎴", layout="centered")

# --- [스타일] 여백 확보 및 버튼 병렬 배치 ---
st.markdown("""
    <style>
    .stApp { background-color: #000000 !important; }
    /* 최상단 공백 강제 확보 */
    .block-container { padding-top: 2rem !important; }
    
    .status-box {
        background-color: #1E1E1E; padding: 10px; border-radius: 8px;
        color: #00FFAA !important; font-weight: bold; text-align: center;
        margin-bottom: 10px; border: 1px solid #333;
    }

    .word-card { 
        background-color: #1A1A1A; padding: 30px 10px; border-radius: 15px; 
        border: 1px solid #444; text-align: center; margin-bottom: 20px;
    }
    .japanese-word { font-size: 3rem !important; color: #FFFFFF !important; margin: 0; }

    /* 정답 텍스트 가독성 */
    .ans-txt { 
        background: #262626; color: #00FFAA; padding: 10px; 
        border-radius: 8px; text-align: center; font-weight: bold; margin-bottom: 5px;
    }

    .stButton>button { width: 100%; height: 45px !important; border-radius: 8px !important; }
    </style>
    """, unsafe_allow_html=True)

def play_voice(text):
    clean = re.sub(r'[\(（].*?[\)）]', '', text).replace('*', '')
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
        sel_day = st.selectbox("구간", days)
        if st.button("🔄 기록 초기화"): st.session_state.learned = set(); st.rerun()
        if 'p_day' not in st.session_state or st.session_state.p_day != sel_day:
            st.session_state.idx = 0; st.session_state.p_day = sel_day

day_df = df[df['Day'] == sel_day].reset_index(drop=True)
learned_in_day = [i for i in st.session_state.learned if i in day_df['GlobalID'].values]
display_df = day_df[~day_df['GlobalID'].isin(st.session_state.learned)].reset_index(drop=True)

if not display_df.empty:
    if st.session_state.idx >= len(display_df): st.session_state.idx = 0
    row = display_df.iloc[st.session_state.idx]
    
    # 상단 공백 및 현황판
    st.write("") 
    st.markdown(f'<div class="status-box">📊 {sel_day} 현황: {len(learned_in_day)} / {len(day_df)}</div>', unsafe_allow_html=True)

    # 단어 카드
    st.markdown(f'<div class="word-card"><h1 class="japanese-word">{row.iloc[1]}</h1></div>', unsafe_allow_html=True)

    # --- 병렬 버튼 배치 로직 ---
    def reveal_and_voice(label, key, content, has_voice=False):
        if not st.session_state.show[key]:
            if st.button(f"👁️ {label} 확인", key=f"btn_{key}"):
                st.session_state.show[key] = True; st.rerun()
        else:
            st.markdown(f'<div class="ans-txt">{content}</div>', unsafe_allow_html=True)
            if has_voice:
                c1, c2 = st.columns(2)
                with c1:
                    if st.button("🔊 다시 듣기", key=f"spk_{key}"): play_voice(content)
                with c2:
                    if st.button("❌ 닫기", key=f"cls_{key}"): st.session_state.show[key] = False; st.rerun()
            else:
                if st.button("❌ 닫기", key=f"cls_{key}"): st.session_state.show[key] = False; st.rerun()

    reveal_and_voice("읽기", "reading", row.iloc[2], has_voice=True)
    reveal_and_voice("뜻", "mean", row.iloc[3])
    reveal_and_voice("예문", "ex", row.iloc[4], has_voice=True)
    reveal_and_voice("한자", "kanji", row.iloc[5] if len(row)>5 else "-")

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
    st.success("클리어!"); st.balloons()