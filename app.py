import streamlit as st
import pandas as pd
from gtts import gTTS
from io import BytesIO

# 구글 시트 주소
SHEET_ID = "1KrgYU9dPGVWJgHeKJ4k4F6o0fqTtHvs7P5w7KmwSwwA"
CSV_URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv"

st.set_page_config(page_title="JLPT N2", page_icon="🎴", layout="centered")

# --- [스타일] 디자인 유지 + 오디오 플레이어 숨기기 ---
st.markdown("""
    <style>
    .stApp { background-color: #000000 !important; }
    .block-container { padding-top: 3rem !important; }
    
    /* 오디오 플레이어 숨기기 (소리는 나고 화면엔 안 보임) */
    .stAudio { display: none !important; }

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

    /* 정답 박스 (버튼처럼 보이게) */
    .ans-btn { 
        background: #262626; color: #00FFAA; padding: 12px; width: 100%;
        border-radius: 8px; text-align: center; font-weight: bold; 
        margin-bottom: 6px; border: 1px solid #00FFAA; display: block;
    }
    .ans-text {
        background: #262626; color: #FFFFFF; padding: 12px; width: 100%;
        border-radius: 8px; text-align: center; font-weight: bold; 
        margin-bottom: 6px; border: 1px solid #555; display: block;
    }
    
    .stButton>button { height: 48px !important; border-radius: 12px !important; font-weight: bold !important; }
    .growth-log {
        margin-top: 15px; padding: 10px; background: #111; border-radius: 10px;
        border: 1px dashed #444; text-align: center;
    }
    .level-text { color: #FFD700 !important; font-size: 0.9rem; font-weight: bold; }
    </style>
    """, unsafe_allow_html=True)

# --- [정석] gTTS를 이용한 고음질 오디오 생성 ---
def get_audio_bytes(text):
    sound_file = BytesIO()
    tts = gTTS(text, lang='ja')
    tts.write_to_fp(sound_file)
    return sound_file

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

    # 3. 정답 확인 및 음성 재생
    def reveal_section(label, key, content, has_voice=False):
        # 1) 아직 안 뒤집었을 때
        if not st.session_state.show[key]:
            if st.button(f"👁️ {label} 확인", key=f"btn_{key}"):
                st.session_state.show[key] = True; st.rerun()
        
        # 2) 뒤집었을 때
        else:
            if has_voice:
                # 소리 나는 항목은 버튼으로 표시 (누르면 소리 남)
                if st.button(f"🔊 {content}", key=f"play_{key}"):
                    # 여기서 서버가 만든 진짜 오디오 파일을 재생
                    sound = get_audio_bytes(content)
                    st.audio(sound, format='audio/mp3', autoplay=True)
            else:
                # 소리 없는 항목은 그냥 텍스트 박스
                st.markdown(f'<div class="ans-text">{content}</div>', unsafe_allow_html=True)

    reveal_section("읽기", "reading", row.iloc[2], has_voice=True)
    reveal_section("뜻", "mean", row.iloc[3])
    reveal_section("예문", "ex", row.iloc[4], has_voice=True)
    reveal_section("한자", "kanji", row.iloc[5] if len(row)>5 else "-")

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