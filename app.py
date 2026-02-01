import streamlit as st
import pandas as pd
import re
import streamlit.components.v1 as components

# 구글 시트 주소
SHEET_ID = "1KrgYU9dPGVWJgHeKJ4k4F6o0fqTtHvs7P5w7KmwSwwA"
CSV_URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv"

st.set_page_config(page_title="JLPT N2", page_icon="🎴", layout="centered")

# --- [스타일] 모바일 레이아웃 '진짜' 강제 고정 ---
st.markdown("""
    <style>
    .stApp { background-color: #000000 !important; }
    .block-container { padding-top: 3.5rem !important; }
    
    /* [핵심] 모바일에서 컬럼이 쌓이는 걸 막는 강력한 CSS */
    [data-testid="column"] {
        width: 50% !important;
        flex: 1 1 50% !important;
        min-width: 50% !important;
    }
    
    /* 컬럼을 감싸는 부모 컨테이너가 줄바꿈 하지 않도록 강제 */
    [data-testid="stHorizontalBlock"] {
        flex-direction: row !important;
        flex-wrap: nowrap !important;
        gap: 10px !important;
    }
    
    /* 텍스트 및 박스 스타일 */
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
    
    /* 정답 텍스트 박스 */
    .ans-normal {
        background: #262626; color: #FFFFFF; padding: 12px; width: 100%;
        border-radius: 8px; text-align: center; font-weight: bold; 
        margin-bottom: 6px; border: 1px solid #555; display: block;
    }
    
    /* 버튼 스타일 */
    .stButton>button { height: 48px !important; border-radius: 12px !important; font-weight: bold !important; }
    
    /* 토글/체크박스 간격 조절 */
    .stToggle { margin-top: -5px; }
    .stCheckbox { margin-top: -5px; }
    </style>
    """, unsafe_allow_html=True)

# --- [자바스크립트] 일본어 성우 스마트 선택 ---
def js_audio_button(text, key_suffix):
    clean_text = re.sub(r'[\(（].*?[\)）]', '', text).replace('*', '').replace("'", "")
    
    html_code = f"""
    <!DOCTYPE html>
    <html>
    <head>
    <style>
        body {{ margin: 0; padding: 0; background-color: transparent; }}
        .voice-btn {{
            width: 100%; height: 48px;
            background-color: #262626; color: #00FFAA;
            border: 1.5px solid #00FFAA; border-radius: 8px;
            font-size: 16px; font-weight: bold; cursor: pointer;
            display: flex; align-items: center; justify-content: center;
            font-family: sans-serif; -webkit-tap-highlight-color: transparent;
        }}
        .voice-btn:active {{ background-color: #333333; }}
    </style>
    </head>
    <body>
        <button class="voice-btn" onclick="speak()">🔊 {text}</button>
        <script>
            function speak() {{
                window.speechSynthesis.cancel();
                const msg = new SpeechSynthesisUtterance('{clean_text}');
                msg.lang = 'ja-JP';
                msg.rate = 1.0; 

                // 사용 가능한 목소리 가져오기
                let voices = window.speechSynthesis.getVoices();
                
                // [우선순위] 1. Siri(혹시 열려있다면) 2. Kyoko(고음질) 3. Otoya 4. 아무 일본어
                let jaVoice = voices.find(v => v.name.includes('Siri') && v.lang === 'ja-JP') ||
                              voices.find(v => v.name.includes('Kyoko')) || 
                              voices.find(v => v.name.includes('Otoya')) ||
                              voices.find(v => v.lang === 'ja-JP');
                
                if (jaVoice) {{
                    msg.voice = jaVoice;
                    console.log("Selected voice: " + jaVoice.name);
                }}
                
                window.speechSynthesis.speak(msg);
            }}
            
            if (window.speechSynthesis.onvoiceschanged !== undefined) {{
                window.speechSynthesis.onvoiceschanged = () => window.speechSynthesis.getVoices();
            }}
        </script>
    </body>
    </html>
    """
    components.html(html_code, height=50)

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
if 'shuffle_seed' not in st.session_state: st.session_state.shuffle_seed = 42

with st.sidebar:
    if not df.empty:
        days = sorted(df['Day'].unique(), key=lambda x: int(x.replace("일차", "")))
        sel_day = st.selectbox("구간 선택", days)
        if st.button("🔄 전체 초기화"): 
            st.session_state.learned = set()
            st.rerun()
        if 'p_day' not in st.session_state or st.session_state.p_day != sel_day:
            st.session_state.idx = 0; st.session_state.p_day = sel_day

day_df = df[df['Day'] == sel_day].copy()

# [수정] 모바일 레이아웃: st.columns는 잊고 HTML/CSS로 제어되는 컨테이너 사용
col1, col2 = st.columns([1, 1]) # 비율 1:1 강제
with col1:
    do_shuffle = st.toggle("🔀 순서 섞기", value=False)
with col2:
    show_all = st.checkbox("✅ 복습 모드", value=False)

if do_shuffle:
    day_df = day_df.sample(frac=1, random_state=st.session_state.shuffle_seed).reset_index(drop=True)

display_df = day_df if show_all else day_df[~day_df['GlobalID'].isin(st.session_state.learned)].reset_index(drop=True)

if not display_df.empty:
    if st.session_state.idx >= len(display_df): st.session_state.idx = 0
    row = display_df.iloc[st.session_state.idx]
    
    # 1. 현황판
    current_learned = len([i for i in st.session_state.learned if i in day_df['GlobalID'].values])
    st.markdown(f'<div class="status-box">📊 {sel_day} : {current_learned} / {len(day_df)}</div>', unsafe_allow_html=True)

    # 2. 단어 카드
    st.markdown(f'<div class="word-card"><h1 class="japanese-word">{row.iloc[1]}</h1></div>', unsafe_allow_html=True)

    # 3. 정답 및 음성 버튼
    def reveal_section(label, key, content, has_voice=False):
        if not st.session_state.show[key]:
            if st.button(f"👁️ {label} 확인", key=f"btn_{key}", use_container_width=True):
                st.session_state.show[key] = True; st.rerun()
        else:
            if has_voice:
                js_audio_button(content, key)
            else:
                st.markdown(f'<div class="ans-normal">{content}</div>', unsafe_allow_html=True)

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

    # 5. 레벨 바
    total_learned = len(st.session_state.learned)
    user_level = (total_learned // 10) + 1
    exp_in_level = total_learned % 10
    st.markdown(f"""
    <div style="margin-top:15px; padding:10px; background:#111; border-radius:10px; border:1px dashed #444; text-align:center;">
        <span style="color:#FFD700; font-weight:bold;">🔥 LV.{user_level} (총 {total_learned}개)</span>
    </div>
    """, unsafe_allow_html=True)
    st.progress(exp_in_level / 10)

else:
    st.balloons(); st.success("오늘 분량 끝!")