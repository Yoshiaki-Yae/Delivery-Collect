import streamlit as st
import pandas as pd
import os
import hashlib
from datetime import datetime
from streamlit_js_eval import get_geolocation

# --- 画面設定 ---
st.set_page_config(page_title="現場・位置しるべ", page_icon="📍", layout="centered")

# --- 改ざん防止ハッシュ ---
def make_hash(row):
    text = f"{row['日時']}{row['番地']}{row['枝番']}{row['号']}{row['緯度']}{row['経度']}"
    return hashlib.sha256(text.encode()).hexdigest()

# --- CSV 準備 ---
CSV_PATH = ".streamlit/data.csv"

if os.path.exists(CSV_PATH):
    df_history = pd.read_csv(CSV_PATH)
else:
    df_history = pd.DataFrame(columns=["日時", "番地", "枝番", "号", "緯度", "経度", "署名"])

# --- 改ざんチェック ---
if len(df_history) > 0:
    tampered = False
    for _, row in df_history.iterrows():
        if row["署名"] != make_hash(row):
            tampered = True
            break

    if tampered:
        st.error("⚠️ データが改ざんされています。")
    else:
        st.success("🔒 データは正しく保護されています。")

st.title("📍 現場・位置しるべ")
st.caption("〜 地図の嘘を正し、正解を刻む 〜")

# --- 町名 ---
target_town = st.radio(
    "町名",
    ["南今津", "高西町3丁目", "高西町2丁目", "高須町"],
    horizontal=True
)

# --- 横3列固定テンキー ---
def keypad_input(label, key, max_len):
    st.markdown(f"### {label}")

    if key not in st.session_state:
        st.session_state[key] = ""

    # 表示欄（編集不可）
    st.text_input("", st.session_state[key], key=f"{key}_display", disabled=True)

    # CSS：スマホでも横3列を維持
    st.markdown("""
        <style>
        .stButton>button {
            height: 60px !important;
            font-size: 1.4em !important;
            font-weight: bold !important;
        }
        </style>
    """, unsafe_allow_html=True)

    # テンキーの配置
    keys = [
        ["1", "2", "3"],
        ["4", "5", "6"],
        ["7", "8", "9"],
        ["←", "0", "C"]
    ]

    for row in keys:
        cols = st.columns(3)
        for i, k in enumerate(row):
            if cols[i].button(k, key=f"{key}_{k}", use_container_width=True):
                if k == "C":
                    st.session_state[key] = ""
                elif k == "←":
                    st.session_state[key] = st.session_state[key][:-1]
                else:
                    if len(st.session_state[key]) < max_len:
                        st.session_state[key] += k

                st.session_state[f"{key}_display"] = st.session_state[key]

    return st.session_state[key]

# --- 番地・枝番・号 ---
col1, col2, col3 = st.columns(3)

with col1:
    banchi = keypad_input("番地", "banchi", 5)

with col2:
    edaban = keypad_input("枝番", "edaban", 4)

with col3:
    go = keypad_input("号", "go", 4)

# --- GPS ---
st.subheader("其の二：位置を確かめる")
location = get_geolocation()

if location:
    lat = location["coords"]["latitude"]
    lon = location["coords"]["longitude"]
    st.info(f"緯度: {lat} / 経度: {lon}")
else:
    st.warning("GPS を取得中…（スマホの位置情報を ON にしてください）")

# --- 登録 ---
st.divider()

if banchi:
    is_registered = (
        (df_history["番地"] == banchi) &
        (df_history["枝番"] == edaban) &
        (df_history["号"] == go)
    ).any()

    if is_registered:
        st.warning("この住所は既に記録されています（追記のみ）。")
    else:
        st.success("新しい住所です。記録できます。")

    if st.button("✅ 座標を書き記す", use_container_width=True):
        if location:
            now = datetime.now().strftime("%Y-%m-%d %H:%M")

            new_row = {
                "日時": now,
                "番地": banchi,
                "枝番": edaban,
                "号": go,
                "緯度": lat,
                "経度": lon
            }
            new_row["署名"] = make_hash(new_row)

            updated_df = pd.concat([df_history, pd.DataFrame([new_row])], ignore_index=True)
            updated_df.to_csv(CSV_PATH, index=False)

            st.balloons()
            st.success("正しく書き記しました！")
        else:
            st.error("GPS が取得できていません。")
else:
    st.info("番地を入力すると記録できます。")

# --- 履歴 ---
with st.expander("これまでの歩み（最新10件）"):
    st.dataframe(df_history.tail(10))
