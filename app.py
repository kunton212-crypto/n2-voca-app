import streamlit as st
import pandas as pd
import random
import re
import streamlit.components.v1 as components

# 구글 시트 주소
SHEET_ID = "1KrgYU9dPGVWJgHeKJ4k4F6o0fqTtHvs7P5w7KmwSwwA"
CSV_URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv"

st.set_page_config(page_title="N2 단어 마스터", page_icon="🎴", layout="centered")

# --- 스타일 설정 (배경색/가독성 이슈 해결) ---
st.markdown("""
    <style>
    .stApp { background-color: #121212 !important; }
    h1, h2, h3, h4, h5, h6, p, span, label, div, li { color: #FFFFFF !important; }
    .word-card { 
        background-color: #1E1E1E !important; padding: 50px 20px; border-radius: 20px; 
        border: 2px solid #333; text-align: center; margin-bottom: 25px;
    }
    .japanese-word { font-size: 5rem !important; color: #FFD700 !important; font-weight: 800 !important; }
    .reveal-box {
        background-color: #2C2C2C !important; padding: 12px; border-radius: 10px;
        border: 1px solid #444; color: #FFFFFF !important; font-weight: bold;
    }
    .hidden-box {
        background-color: #1A1A1A !important; border: 1px dashed #555 !important;
        padding: 12px; border-radius: 10px; text-align: center; color: #888 !important;
    }
    </style>
    """, unsafe_allow_html=True)

# --- 음성 제어 함수 ---
def control_audio(text, action="play"):
    if action == "stop":
        js = "<script>window.speechSynthesis.cancel();</script>"
    else:
        clean = re.sub(r'[\(（].*?[\)）]', '', text).replace('*', '').replace("'", "\\'")
        js = f"""
            <script>
            window.speechSynthesis.cancel();
            var msg = new SpeechSynthesisUtterance('{clean}');
            msg.lang = 'ja-JP'; msg.rate = 0.9;
            window.speechSynthesis.speak(msg);
            </script>
        """
    components.html(js, height=0)

@st.cache_data(ttl=60)
def load_data():
    try:
        df = pd.read_csv(CSV_URL).fillna("내용 없음")
        df['Day'] = ((df.index) // 30 + 1).astype(str) + "일차"
        df['GlobalID'] = df.index # 단어 고유 식별자
        return df
    except: return pd.DataFrame()

df = load_data()

# --- 세션 상태 초기화 ---
if 'idx' not in st.session_state: st.session_state.idx = 0
if 'learned_list' not in st.session_state: st.session_state.learned_list = set()
if 'show' not in st.session_state: 
    st.session_state.show = {"reading": False, "mean": False, "ex": False, "kanji": False}

# --- 사이드바 설정 ---
with st.sidebar:
    st.header("⚙️ 학습 설정")
    if not df.empty:
        days = sorted(df['Day'].unique(), key=lambda x: int(x.replace("일차", "")))
        sel_day = st.selectbox("📅 구간 선택", days)
        
        # [핵심 기능] 외운 단어 포함 여부
        show_all = st.checkbox("✅ 외운 단어도 포함해서 보기", value=False)
        
        # [초기화 버튼]
        if st.button("🔄 전체 암기 기록 초기화"):
            st.session_state.learned_list = set()
            st.rerun()

        if 'p_day' not in st.session_state or st.session_state.p_day != sel_day:
            st.session_state.idx = 0
            st.session_state.p_day = sel_day

# --- 데이터 필터링 로직 ---
day_df = df[df['Day'] == sel_day].reset_index(drop=True)

# '모두 보기'가 체크되지 않았다면, 외운 단어 목록에 없는 것만 추출
if not show_all:
    display_df = day_df[~day_df['GlobalID'].isin(st.session_state.learned_list)].reset_index(drop=True)
else:
    display_df = day_df

# --- 화면 출력 ---
if not display_df.empty:
    # 인덱스 범위 초과 방지
    if st.session_state.idx >= len(display_df):
        st.session_state.idx = 0
        
    row = display_df.iloc[st.session_state.idx]
    
    st.write(f"📊 학습 가능 단어: **{len(display_df)}개** (전체 {len(day_df)}개 중)")
    st.progress((st.session_state.idx + 1) / len(display_df))

    # 단어 카드
    st.markdown(f'<div class="word-card"><h1 class="japanese-word">{row.iloc[1]}</h1></div>', unsafe_allow_html=True)

    def reveal_row(label, key, content, speech=False):
        c1, c2, c3, c4 = st.columns([1, 2, 0.4, 0.4])
        with c1:
            if st.button(f"👁️ {label}", key=f"b_{key}", use_container_width=True):
                st.session_state.show[key] = True
                st.rerun()
        with c2:
            if st.session_state.show[key]:
                st.markdown(f'<div class="reveal-box">{content}</div>', unsafe_allow_html=True)
            else:
                st.markdown('<div class="hidden-box">???</div>', unsafe_allow_html=True)
        with c3:
            if speech and st.session_state.show[key]:
                if st.button("🔊", key=f"p_{key}"): control_audio(content)
        with c4:
            if speech and st.session_state.show[key]:
                if st.button("⏹️", key=f"s_{key}"): control_audio("", "stop")

    reveal_row("읽기", "reading", row.iloc[2], speech=True)
    reveal_row("뜻", "mean", row.iloc[3])
    reveal_row("예문", "ex", row.iloc[4], speech=True)
    reveal_row("한자", "kanji", row.iloc[5] if len(row)>5 else "정보 없음")

    st.write("")
    
    def move_next():
        control_audio("", "stop")
        st.session_state.idx = (st.session_state.idx + 1) % len(display_df)
        st.session_state.show = {k:False for k in st.session_state.show}

    cl, cr = st.columns(2)
    with cl:
        if st.button("⏭️ 그냥 넘기기", use_container_width=True):
            move_next()
            st.rerun()
    with cr:
        if st.button("✅ 외웠어요!", type="primary", use_container_width=True):
            # 외운 단어 목록에 추가 (GlobalID 사용)
            st.session_state.learned_list.add(row['GlobalID'])
            # 목록에서 사라지므로 인덱스를 늘릴 필요 없이 유지 (단, 마지막 단어였으면 0으로)
            if st.session_state.idx >= len(display_df) - 1:
                st.session_state.idx = 0
            st.session_state.show = {k:False for k in st.session_state.show}
            st.rerun()

else:
    st.balloons()
    st.success(f"🎊 {sel_day}의 모든 단어를 암기하셨습니다!")
    if not show_all:
        st.info("사이드바의 '외운 단어도 포함해서 보기'를 체크하면 복습할 수 있습니다.")