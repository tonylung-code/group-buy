# debug_config.py
import streamlit as st

st.title("🔍 Secrets 診斷工具")

if "connections" in st.secrets:
    st.success("✅ 找到 [connections] 標籤")
    if "gsheets" in st.secrets.connections:
        st.success("✅ 找到 [gsheets] 配置")
        conf = st.secrets.connections.gsheets
        st.write("讀取到的 Keys:", list(conf.keys()))
        if "spreadsheet" in conf:
            st.info(f"網址偵測成功: {conf['spreadsheet']}")
        else:
            st.error("❌ 找不到 'spreadsheet' 鍵值，請檢查 .toml 拼字或格式")
    else:
        st.error("❌ 找不到 'gsheets' 區塊")
else:
    st.error("❌ 完全找不到 [connections] 標籤，請確認檔案路徑是否為 .streamlit/secrets.toml")