import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd

st.set_page_config(page_title="葡吉 團購系統", layout="wide")

ITEM_PRICES = {
    "羅宋": 80,
    "奶露麵包": 90,
    "蔓越莓乳酪": 75,
    "東風芝士堡": 90,
    "小帥哥（肉鬆麵包/5入）": 70,
    "黑眼巧克力": 30,
    "楓糖吐司": 70,
    "可可芋頭吐司": 70,
    "歐式-木村核桃堡": 70,
    "歐式-伯爵蔓越莓": 70,
    "歐式-酒釀桂圓": 200,
}
ITEM_COLUMNS = ["username", *ITEM_PRICES.keys()]


def get_quantity(record: pd.DataFrame, item: str) -> int:
    if record.empty or item not in record.columns:
        return 0

    value = record[item].values[0]
    if pd.isna(value) or value == "":
        return 0

    return int(value)

# 1. 初始化連線
conn = st.connection("gsheets", type=GSheetsConnection)

# 2. 獲取資料 (設定 ttl=0 以確保每次都是最新數據)
df = conn.read(ttl=0)
if df is None or df.empty:
    df = pd.DataFrame(columns=ITEM_COLUMNS)
else:
    if "username" not in df.columns:
        df["username"] = ""
    for item in ITEM_PRICES:
        if item not in df.columns:
            df[item] = 0
    df = df[ITEM_COLUMNS]

st.title("🛒 團購系統")
st.info("請盡量準備剛好金額的現金，避免找零造成收款者困擾。")

# 3. 使用者登入識別
user_id = st.text_input("請輸入您的姓名 (修改/訂購標籤)：").strip()

if user_id:
    user_record = df[df['username'] == user_id]
    
    with st.form("order_form"):
        st.subheader(f"當前使用者：{user_id}")
        
        new_data = {"username": user_id}
        order_total = 0
        order_quantity = 0
        
        for item, price in ITEM_PRICES.items():
            # 邏輯：如果有舊紀錄就填入舊值，否則預設 0
            default_val = get_quantity(user_record, item)
            
            quantity = st.number_input(
                f"{item}（單價 ${price}）",
                min_value=0,
                value=default_val,
            )
            new_data[item] = quantity
            order_quantity += quantity
            order_total += quantity * price

        st.caption(f"個人訂購總數量：{order_quantity}，個人訂單總金額：${order_total}")
        
        submit = st.form_submit_button("更新訂購資訊")
        
        if submit:
            # 移除舊紀錄並加入新紀錄 (即為修改邏輯)
            df = df[df['username'] != user_id]
            new_row = pd.DataFrame([new_data])
            df = pd.concat([df, new_row], ignore_index=True)
            df = df[ITEM_COLUMNS]
            
            # 寫回 Google Sheets
            conn.update(data=df)
            st.success(f"✅ {user_id} 的訂單已更新！")
            st.rerun()

# 4. 後台統計區域
st.divider()
st.subheader("📊 目前團購統計總量")
if df is not None and not df.empty:
    total_summary = df.reindex(columns=ITEM_PRICES.keys(), fill_value=0).sum().astype(int)
    summary_df = pd.DataFrame(
        {
            "單價": pd.Series(ITEM_PRICES),
            "訂購數量": total_summary,
        }
    )
    summary_df["小計"] = summary_df["單價"] * summary_df["訂購數量"]

    st.table(summary_df)
    st.metric("團購總金額", f"${int(summary_df['小計'].sum())}")
else:
    st.info("目前尚無訂購資料。")
