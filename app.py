import streamlit as st
import yfinance as yf

# ページの設定（スマホで見やすいように）
st.set_page_config(page_title="もっちのFXツールテスト", layout="centered")

st.title("🚀 もっちのFX解析ツール (Test Ver.)")
st.write("GitHubとStreamlitの連携テスト中。")

# データの取得テスト (ドル円の最新情報を取得)
ticker = "USDJPY=X"
data = yf.Ticker(ticker)
latest_price = data.history(period="1d")['Close'].iloc[-1]

# 画面に表示
st.metric(label="現在のドル円", value=f"{latest_price:.3f} JPY")

st.success("これが表示されていれば、Web公開成功です！")