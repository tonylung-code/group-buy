import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd

st.set_page_config(page_title="葡吉 團購系統", layout="wide")
st.markdown(
    """
    <style>
    div[data-testid="stNumberInput"] label p {
        font-size: 1.2rem;
        font-weight: 600;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

ITEM_PRICES = {
    "1. 羅宋": 80,
    "2. 奶露麵包": 90,
    "3. 蔓越莓乳酪": 75,
    "4. 東風芝士堡": 90,
    "5. 小帥哥（肉鬆麵包/5入）": 70,
    "6. 黑眼巧克力": 30,
    "7. 蔥麵包": 30,
    "8. 鹽麵包": 50,
    "9. 紅豆麵包": 35,
    "10. 楓糖吐司": 70,
    "11. 年輪紅豆吐司": 70,
    "12. 可可芋頭吐司 (1/2條)": 70,
    "13. 黑糖麻糬吐司 (1/2條)": 55,
    "14. 歐式-木村核桃堡": 70,
    "15. 歐式-伯爵蔓越莓": 70,
    "16. 歐式-全麥堅果核桃": 70,
    "17. 歐式-酒釀桂圓": 200,
    "18. 千層烤布蕾": 70,
    "19. 湯種風琴司康": 60,
    "20. 休格蘭巧克力": 30,
}
TOTAL_AMOUNT_COLUMN = "個人總額"
ITEM_COLUMNS = ["username", *ITEM_PRICES.keys()]
SHEET_COLUMNS = [*ITEM_COLUMNS, TOTAL_AMOUNT_COLUMN]

if "active_user_id" not in st.session_state:
    st.session_state.active_user_id = ""


def to_int(value) -> int:
    if pd.isna(value) or value == "":
        return 0
    return int(value)


def get_quantity(record: pd.DataFrame, item: str) -> int:
    if record.empty or item not in record.columns:
        return 0

    return to_int(record[item].values[0])


def calculate_order_quantity(row: pd.Series) -> int:
    return sum(to_int(row.get(item, 0)) for item in ITEM_PRICES)


def calculate_order_total(row: pd.Series) -> int:
    return sum(to_int(row.get(item, 0)) * price for item, price in ITEM_PRICES.items())


conn = st.connection("gsheets", type=GSheetsConnection)

df = conn.read(ttl=0)
if df is None or df.empty:
    df = pd.DataFrame(columns=SHEET_COLUMNS)
else:
    if "username" not in df.columns:
        df["username"] = ""
    for item in ITEM_PRICES:
        if item not in df.columns:
            df[item] = 0
    if TOTAL_AMOUNT_COLUMN not in df.columns:
        df[TOTAL_AMOUNT_COLUMN] = 0
    df = df[SHEET_COLUMNS]

for item in ITEM_PRICES:
    df[item] = df[item].apply(to_int)

calculated_totals = df.apply(calculate_order_total, axis=1)
sheet_totals = df[TOTAL_AMOUNT_COLUMN].apply(to_int)
if not calculated_totals.equals(sheet_totals):
    df[TOTAL_AMOUNT_COLUMN] = calculated_totals
    conn.update(data=df[SHEET_COLUMNS])

st.title("🛒 團購系統")
st.info("請盡量準備剛好金額的現金，避免找零造成收款者困擾。")
st.markdown("官網網址：[葡吉麵包官網](https://pujeigiftlp.com.tw/pujei-bread/)")

with st.expander("系統使用說明", expanded=True):
    st.markdown(
        """
        1. 請先輸入姓名，並按下「確認」按鈕。
        2. 依照需求填寫各品項的訂購數量。
        3. 系統會自動顯示個人訂購總數量與總金額。
        4. 確認內容無誤後，按下「更新訂購資訊」送出訂單。
        5. 若要修改/確認原本的訂單，輸入相同姓名後重新調整數量再送出即可。
        6. 結單日期為 5/9（六）15:30，表單關閉逾時不候，產品將於 5/18（一）送達
        """
    )

entered_user_id = st.text_input("請輸入您的姓名 (修改/訂購標籤)：").strip()
confirm_user = st.button("確認")
if confirm_user and entered_user_id:
    st.session_state.active_user_id = entered_user_id

user_id = st.session_state.active_user_id

if user_id:
    user_record = df[df["username"] == user_id]

    with st.form("order_form"):
        st.subheader(f"當前使用者：{user_id}")

        new_data = {"username": user_id}
        order_total = 0
        order_quantity = 0

        for item, price in ITEM_PRICES.items():
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
            new_data[TOTAL_AMOUNT_COLUMN] = order_total
            df = df[df["username"] != user_id]
            new_row = pd.DataFrame([new_data])
            df = pd.concat([df, new_row], ignore_index=True)
            df = df[SHEET_COLUMNS]

            conn.update(data=df)
            st.success(f"✅ {user_id} 的訂單已更新！")
            st.session_state.active_user_id = user_id
            st.rerun()

st.divider()
st.subheader("📋 訂購資訊總覽")
if df is not None and not df.empty:
    overview_df = pd.DataFrame(
        {
            "訂購人姓名": df["username"],
            "訂購數量": df.apply(calculate_order_quantity, axis=1),
            "訂購總金額": df[TOTAL_AMOUNT_COLUMN].apply(to_int),
        }
    )
    overview_df = overview_df[overview_df["訂購人姓名"].astype(str).str.strip() != ""]
    overview_df = overview_df.sort_values(by="訂購人姓名").reset_index(drop=True)

    st.dataframe(overview_df, hide_index=True, use_container_width=True)
    st.metric("全部訂單總金額", f"${int(overview_df['訂購總金額'].sum())}")
else:
    st.info("目前尚無訂購資料。")
