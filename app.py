import streamlit as st
import pandas as pd
import random
import re

# 구글 시트 주소
SHEET_ID = "1KrgYU9dPGVWJgHeKJ4k4F6o0fqTtHvs7P5w7KmwSwwA"
CSV_URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv"

st.set_page_config(page_title="N2", page_icon="🎴", layout="centered")

# --- [초강력 디자인] 아이폰 사파리 가시성 100% 보장 ---
st.markdown("""
    <style>
    /* 배경 및 전체 여백 */
    .stApp { background-color: #000000 !important; }
    .block-container { padding: 10px !important; }
    
    /* 1. 현황판 - 화면 상단에 명확하게 노출 */
    .status-header {
        background-color: #1E1E1E; border-bottom: 2px solid #00FFAA;
        padding: 10px; border-radius: 8px; margin-bottom: 10px;
        display: flex; justify-content: space-between;
        font-family: monospace; font-size: 1rem; color: #00FFAA !important;
    }

    /* 2. 단어 카드 - 흰색 글자 */
    .word-card { 
        background-color: #1A1A1A; padding: 25px 10px; 
        border-radius: 12px; border: 1px solid #333; text-align: center; 
        margin-bottom: 15px;
    }
    .japanese-word { font-size: 3rem !important; color: #FFFFFF !important; margin: 0; }

    /* 3. 줄 바꿈 방지용 테이블 레이아웃 */
    .info-table { width: 100%; border-collapse: collapse; margin-bottom: 8px; }
    .info-td-content { 
        background: #262626; border-radius: 8px 0 0 8px; border: 1px solid #444;
        padding: 10px; color: white; font-weight: bold; font-size: 0.95rem; text-align: center;
    }
    .info-td-btn { 
        width: 50px; background: #333; border-radius: 0 8px 8px 0; border: 1px solid #444;
        text-align: center;
    }

    /* 버튼 기본 스타일 */
    .stButton>button { width: 100%; height: 45px !important; border-radius: 8px !important; }
    </style>
    """, unsafe_allow_html=True)

# --- [아이폰 무조건 성공] 음성 재생 방식 ---
def play_voice(text):
    clean = re.sub(r'[\(（].*?[\)）]', '', text).replace('*', '')
    tts_url = f"https://translate.google.com/translate_tts?ie=UTF-8&q={clean}&tl=ja&client=tw-ob"
    # 폰에서 즉각 반응하는 iframe 방식
    st.components.v1.html(f"""
        <iframe src="{tts_url}" allow="autoplay" style="display:none"></iframe>
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

# 사이드바 설정
with st.sidebar:
    if not df.empty:
        days = sorted(df['Day'].unique(), key=lambda x: int(x.replace("일차", "")))
        sel_day = st.selectbox("구간", days)
        if st.button("🔄 기록 초기화"): st.session_state.learned = set(); st.rerun()
        if 'p_day' not in st.session_state or st.session_state.p_day != sel_day:
            st.session_state.idx = 0; st.session_state.p_day = sel_day

# 데이터 필터링
day_df = df[df['Day'] == sel_day].reset_index(drop=True)
learned_in_day = [i for i in st.session_state.learned if i in day_df['GlobalID'].values]
display_df = day_df[~day_df['GlobalID'].isin(st.session_state.learned)].reset_index(drop=True)

if not display_df.empty:
    if st.session_state.idx >= len(display_df): st.session_state.idx = 0
    row = display_df.iloc[st.session_state.idx]
    
    # 1. 현황판 (배경이 있는 박스로 상단 노출)
    st.markdown(f'''
        <div class="status-header">
            <span>📍 {sel_day}</span>
            <span>📊 {len(learned_in_day)} / {len(day_df)}</span>
        </div>
    ''', unsafe_allow_html=True)

    # 2. 단어 카드 (흰색)
    st.markdown(f'<div class="word-card"><h1 class="japanese-word">{row.iloc[1]}</h1></div>', unsafe_allow_html=True)

    # 3. 정답 확인 (줄 바꿈 방지 테이블)
    def render_row(label, key, content, speech=False):
        if not st.session_state.show[key]:
            if st.button(f"👁️ {label}", key=f"btn_{key}"):
                st.session_state.show[key] = True; st.rerun()
        else:
            if speech:
                # 정답과 음성 아이콘을 하나의 테이블로 묶어 줄 바꿈 방지
                st.markdown(f'''
                    <table class="info-table">
                        <tr>
                            <td class="info-td-content">{content}</td>
                        </tr>
                    </table>
                ''', unsafe_allow_html=True)
                if st.button(f"🔊 {label} 듣기", key=f"spk_{key}"):
                    play_voice(content)
            else:
                st.markdown(f'<div class="info-td-content" style="border-radius:8px; margin-bottom:8px;">{content}</div>', unsafe_allow_html=True)

    render_row("읽기", "reading", row.iloc[2], speech=True)
    render_row("뜻", "mean", row.iloc[3])
    render_row("예문", "ex", row.iloc[4], speech=True)
    render_row("한자", "kanji", row.iloc[5] if len(row)>5 else "-")

    # 4. 조작 버튼
    st.write("")
    c1, c2 = st.columns(2)
    with c1:
        if st.button("⏭️ 패스"):
            st.session_state.idx = (st.session_state.idx + 1) % len(display_df)
            st.session_state.show = {k:False for k in st.session_state.show}; st.rerun()
    with c2:
        if st.button("✅ 외웠다", type="primary"):
            st.session_state.learned.add(row['GlobalID'])
            st.session_state.show = {k:False for k in st.session_state.show}; st.rerun()
else:
    st.balloons(); st.success("완벽합니다!")