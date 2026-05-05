import streamlit as st
import pandas as pd
import os
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

# --- CSV ファイルの準備 ---
CSV_PATH = "data.csv"

if os.path.exists(CSV_PATH):
    df_history = pd.read_csv(CSV_PATH)
else:
    df_history = pd.DataFrame(columns=["日時", "住所", "緯度", "経度"])

st.title("📍 現場・位置しるべ")
st.caption("〜 地図の嘘を正し、正解を刻む 〜")

# --- 入力部 ---
st.subheader("其の一：処（ところ）を選ぶ")

# 町名選択
target_town = st.radio(
    "町名", 
    ["南今津", "高西町3丁目", "高西町2丁目", "高須町"], 
    horizontal=True
)

# 番地入力
col1, col2 = st.columns(2)
with col1:
    search_base = st.text_input("番地（例：4803）", placeholder="4803")
with col2:
    address_suffix = st.text_input("枝番（例：-8）", placeholder="-8")

full_address = f"福山市{target_town}{search_base}{address_suffix}"

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

if search_base:
    # 登録済みか確認（住所の重複チェック）
    is_registered = full_address in df_history['住所'].values
    
    if is_registered:
        st.warning(f"「{full_address}」は既に書き記されています。上書きとなります。")
    else:
        st.success(f"「{full_address}」は新しき処です。")

    # 登録ボタン
    if st.button("✅ 座標（しるべ）を書き記す", use_container_width=True):
        if location:
            now = datetime.now().strftime("%Y-%m-%d %H:%M")
            new_data = pd.DataFrame([{
                "日時": now,
                "住所": full_address,
                "緯度": lat,
                "経度": lon
            }])
            
            # 既存データと結合し、同じ住所は最新で上書き
            updated_df = pd.concat([df_history, new_data]).drop_duplicates(subset=["住所"], keep="last")

            # CSV に保存
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
