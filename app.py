import streamlit as st
import pandas as pd
import random

# 구글 시트 직통 주소
SHEET_ID = "1KrgYU9dPGVWJgHeKJ4k4F6o0fqTtHvs7P5w7KmwSwwA"
CSV_URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv"

st.set_page_config(page_title="JLPT N2 마스터", layout="centered")

@st.cache_data(ttl=60)
def load_data():
    try:
        df = pd.read_csv(CSV_URL)
        return df
    except Exception as e:
        st.error(f"연결 실패: {e}")
        return pd.DataFrame()

st.title("🇯🇵 N2 단어 마스터")

df = load_data()

if not df.empty:
    if 'idx' not in st.session_state:
        st.session_state.idx = 0

    # 시트 구조에 맞게 열 인덱스 수정 (0번은 번호이므로 제외)
    # 1:단어, 2:읽기, 3:뜻, 4:예문, 5:한자풀이
    row = df.iloc[st.session_state.idx]
    
    col1, col2 = st.columns([4, 1])
    with col1:
        # 단어(1번 열)를 제목으로 표시
        st.subheader(f"현재 단어: :blue[{row.iloc[1]}]")
    with col2:
        if st.button("다음 단어 ➡️"):
            st.session_state.idx = random.randint(0, len(df)-1)
            st.rerun()

    # 요청하신 5가지 탭
    t1, t2, t3, t4, t5 = st.tabs(["📖 단어/읽기", "🎯 뜻", "📝 예문", "🔍 한자풀이", "📊 전체목록"])

    with t1:
        st.write("### 표기 및 읽기")
        st.info(f"**단어:** {row.iloc[1]}")
        st.info(f"**읽기:** {row.iloc[2]}")

    with t2:
        st.write("### 의미")
        st.success(f"**뜻:** {row.iloc[3]}")

    with t3:
        st.write("### 문장 학습")
        st.warning(f"**예문:** {row.iloc[4] if pd.notna(row.iloc[4]) else '등록된 예문이 없습니다.'}")

    with t4:
        st.write("### 상세 풀이")
        st.help(f"**한자풀이:** {row.iloc[5] if len(row) > 5 and pd.notna(row.iloc[5]) else '등록된 풀이가 없습니다.'}")
        
    with t5:
        st.write("### 학습 진도")
        st.write(f"총 {len(df)}개의 단어 중 {row.iloc[0]}번 단어 학습 중")
        st.dataframe(df)