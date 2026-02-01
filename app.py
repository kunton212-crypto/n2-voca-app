import streamlit as st
import pandas as pd

# 구글 시트 주소
SHEET_ID = "1KrgYU9dPGVWJgHeKJ4k4F6o0fqTtHvs7P5w7KmwSwwA"
CSV_URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv"

st.set_page_config(page_title="N2", page_icon="🎴", layout="centered")

# --- [스타일] 현황판 하강 및 디자인 고정 ---
st.markdown("""
    <style>
    .stApp { background-color: #000000 !important; }
    /* 사파리 상단바 피하기 위해 여백 넉넉히 */
    .block-container { padding-top: 4rem !important; }
    
    .status-box {
        background-color: #1E1E1E; padding: 10px; border-radius: 10px;
        color: #00FFAA !important; font-weight: bold; text-align: center;
        margin-bottom: 10px; border: 2px solid #00FFAA; font-size: 1rem;
    }

    .word-card { 
        background-color: #1A1A1A; padding: 25px 10px; border-radius: 15px; 
        border: 1px solid #444; text-align: center; margin-bottom: 10px;
    }
    .japanese-word { font-size: 3rem !important; color: #FFFFFF !important; margin: 0; }

    .ans-box { 
        background: #262626; color: #FFFFFF; padding: 12px; 
        border-radius: 8px; text-align: center; font-weight: bold; 
        margin-bottom: 6px; border: 1px solid #555;
    }
    
    /* 스위치/체크박스 텍스트 색상 */
    .stCheckbox label { color: #FFFFFF !important; font-size: 0.9rem; }
    </style>
    """, unsafe_allow_html=True)

@st.cache_data(ttl=60)
def load_data():
    try:
        df = pd.read_csv(CSV_URL).fillna(" ")
        df['Day'] = ((df.index) // 30 + 1).astype(str) + "일차"
        df['GlobalID'] = df.index
        return df
    except: return pd.DataFrame()

df = load_data()

# 세션 상태 초기화
if 'idx' not in st.session_state: st.session_state.idx = 0
if 'learned' not in st.session_state: st.session_state.learned = set()
if 'show' not in st.session_state: st.session_state.show = {k:False for k in ["reading", "mean", "ex", "kanji"]}
if 'shuffle_seed' not in st.session_state: st.session_state.shuffle_seed = 42

# 사이드바 (일차 선택 전용)
with st.sidebar:
    if not df.empty:
        days = sorted(df['Day'].unique(), key=lambda x: int(x.replace("일차", "")))
        sel_day = st.selectbox("구간 선택", days)
        if st.button("🔄 기록 초기화"): 
            st.session_state.learned = set()
            st.rerun()
        if 'p_day' not in st.session_state or st.session_state.p_day != sel_day:
            st.session_state.idx = 0
            st.session_state.p_day = sel_day

# --- 데이터 필터링 및 섞기 로직 ---
day_df = df[df['Day'] == sel_day].copy()

# 메인 화면 상단 설정 (현황판 위쪽)
col_shuffle, col_all = st.columns(2)
with col_shuffle:
    do_shuffle = st.toggle("🔀 순서 섞기", value=False)
with col_all:
    show_all = st.checkbox("✅ 외운단어 포함", value=False)

if do_shuffle:
    day_df = day_df.sample(frac=1, random_state=st.session_state.shuffle_seed).reset_index(drop=True)

learned_in_day = [i for i in st.session_state.learned if i in day_df['GlobalID'].values]
display_df = day_df if show_all else day_df[~day_df['GlobalID'].isin(st.session_state.learned)].reset_index(drop=True)

# --- 화면 출력 ---
if not display_df.empty:
    if st.session_state.idx >= len(display_df): st.session_state.idx = 0
    row = display_df.iloc[st.session_state.idx]
    
    # 1. 현황판
    st.markdown(f'<div class="status-box">📊 {sel_day} : {len(learned_in_day)} / {len(day_df)}</div>', unsafe_allow_html=True)

    # 2. 단어 카드
    st.markdown(f'<div class="word-card"><h1 class="japanese-word">{row.iloc[1]}</h1></div>', unsafe_allow_html=True)

    # 3. 정답 확인
    def reveal_simple(label, key, content):
        if not st.session_state.show[key]:
            if st.button(f"👁️ {label} 확인", key=f"btn_{key}"):
                st.session_state.show[key] = True
                st.rerun()
        else:
            st.markdown(f'<div class="ans-box">{content}</div>', unsafe_allow_html=True)

    reveal_simple("읽기", "reading", row.iloc[2])
    reveal_simple("뜻", "mean", row.iloc[3])
    reveal_simple("예문", "ex", row.iloc[4])
    reveal_simple("한자", "kanji", row.iloc[5] if len(row)>5 else "-")

    # 4. 하단 버튼
    st.write("")
    cl, cr = st.columns(2)
    with cl:
        if st.button("⏭️ 패스", use_container_width=True):
            st.session_state.idx = (st.session_state.idx + 1) % len(display_df)
            st.session_state.show = {k:False for k in st.session_state.show}
            st.rerun()
    with cr:
        if st.button("✅ 외웠다", type="primary", use_container_width=True):
            st.session_state.learned.add(row['GlobalID'])
            # 섞기 모드일 때 다음 단어를 위해 시드 변경 (선택사항)
            # if do_shuffle: st.session_state.shuffle_seed += 1 
            st.session_state.show = {k:False for k in st.session_state.show}
            st.rerun()
else:
    st.balloons()
    st.success("모든 단어를 마스터했습니다!")