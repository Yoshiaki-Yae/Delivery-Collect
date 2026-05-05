import streamlit as st
import pandas as pd
import os
import hashlib
from datetime import datetime
from streamlit_js_eval import get_geolocation

# --- 画面の基本設定 ---
st.set_page_config(
    page_title="現場・位置しるべ",
    page_icon="📍",
    layout="centered"
)

# カスタムCSS：現場で押しやすい大きなボタン
st.markdown("""
    <style>
    div.stButton > button:first-child {
        height: 3em;
        font-size: 1.2em;
        font-weight: bold;
        background-color: #007BFF;
        color: white;
        border-radius: 10px;
    }
    </style>
""", unsafe_allow_html=True)

# --- 改ざん防止ハッシュ生成 ---
def make_hash(row):
    text = f"{row['日時']}{row['番地']}{row['枝番']}{row['号']}{row['緯度']}{row['経度']}"
    return hashlib.sha256(text.encode()).hexdigest()

# --- CSV ファイルの準備（.streamlit 内に保存） ---
CSV_PATH = ".streamlit/data.csv"

if os.path.exists(CSV_PATH):
    df_history = pd.read_csv(CSV_PATH)
else:
    df_history = pd.DataFrame(columns=["日時", "番地", "枝番", "号", "緯度", "経度", "署名"])

# --- 改ざんチェック ---
if len(df_history) > 0:
    tampered = False
    for _, row in df_history.iterrows():
        expected = make_hash(row)
        if row["署名"] != expected:
            tampered = True
            break

    if tampered:
        st.error("⚠️ データが改ざんされています。正しい記録ではありません。")
    else:
        st.success("🔒 データは正しく保護されています。")

st.title("📍 現場・位置しるべ")
st.caption("〜 地図の嘘を正し、正解を刻む 〜")

# --- 入力部 ---
st.subheader("其の一：処（ところ）を選ぶ")

target_town = st.radio(
    "町名", 
    ["南今津", "高西町3丁目", "高西町2丁目", "高須町"], 
    horizontal=True
)

# --- 番地・枝番・号の入力欄（テンキー + 桁数制限） ---
col1, col2, col3 = st.columns([1, 1, 1])

with col1:
    banchi = st.text_input(
        "番地（最大5桁）",
        placeholder="4803",
        input_type="number",
        max_chars=5
    )

with col2:
    edaban = st.text_input(
        "枝番（最大4桁）",
        placeholder="8",
        input_type="number",
        max_chars=4
    )

with col3:
    go = st.text_input(
        "号（最大4桁）",
        placeholder="1",
        input_type="number",
        max_chars=4
    )

# --- GPS情報の取得 ---
st.subheader("其の二：位置を確かめる")
location = get_geolocation()

if location:
    lat = location['coords']['latitude']
    lon = location['coords']['longitude']
    st.info(f"現在の位置を捉えました：\n緯度: {lat} / 経度: {lon}")
else:
    st.warning("⚠️ 位置情報を測っています。スマホのGPSを有効にして、少々お待ちください。")

# --- 登録処理 ---
st.divider()

if banchi:
    # 番地＋枝番＋号の組み合わせで重複チェック
    is_registered = (
        (df_history["番地"] == banchi) &
        (df_history["枝番"] == edaban) &
        (df_history["号"] == go)
    ).any()
    
    if is_registered:
        st.warning("この住所は既に記録されています（追記のみのため上書き不可）。")
    else:
        st.success("新しい住所です。記録できます。")

    if st.button("✅ 座標（しるべ）を書き記す", use_container_width=True):
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
            st.success("正しく書き記しました。次の現場へ参りましょう！")
        else:
            st.error("位置情報が取得できていないため、記録できません。")
else:
    st.info("番地を入力すると、記録ボタンが現れます。")

# --- 進行状況の確認 ---
with st.expander("これまでの歩み（登録履歴）"):
    st.write(f"現在、{len(df_history)} 件の正解が蓄積されています。")
    st.dataframe(df_history.tail(10))
