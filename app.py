import streamlit as st
import yfinance as yf
import pandas_ta as ta
import plotly.graph_objects as go

# ページ設定
st.set_page_config(page_title="もっちのカスタムインジケーター", layout="wide")
st.title("🚀 もっちのFX解析ツール (ADX + EMA)")

# --- サイドバーで設定変更 ---
st.sidebar.header("⚙️ パラメータ設定")
symbol = st.sidebar.text_input("通貨ペア", "USDJPY=X")
interval = st.sidebar.selectbox("時間足", ["5m", "15m", "1h", "1d"], index=1) # デフォルトを15分足に
ema_period = st.sidebar.number_input("EMAの期間", value=20)
adx_period = st.sidebar.number_input("ADXの期間", value=14)

# --- データ取得 ---
# 15分足などの短い足は、長期間取れないので直近5日分を取得
df = yf.download(symbol, period="5d", interval=interval)

if not df.empty:
    # --- インジケーターの計算 ---
    # pandas_taを使うと一行で計算できます
    df.ta.ema(length=ema_period, append=True)
    df.ta.adx(length=adx_period, append=True)
    
    # 計算された列名を変数化
    ema_col = f"EMA_{ema_period}"
    adx_col = f"ADX_{adx_period}"
    
    # --- 最新のデータでシグナル判定 ---
    latest = df.iloc[-1]
    
    st.subheader("💡 現在の相場状況")
    if latest[adx_col] > 25 and latest['Close'] > latest[ema_col]:
        st.success(f"🔥 上昇トレンド発生中！ (ADX: {latest[adx_col]:.1f})")
    elif latest[adx_col] > 25 and latest['Close'] < latest[ema_col]:
        st.error(f"📉 下降トレンド発生中！ (ADX: {latest[adx_col]:.1f})")
    else:
        st.info(f"⏳ レンジまたはトレンドが弱いです。(ADX: {latest[adx_col]:.1f})")

    # --- チャート描画 (Plotly) ---
    fig = go.Figure()
    
    # ローソク足
    fig.add_trace(go.Candlestick(
        x=df.index, open=df['Open'], high=df['High'], low=df['Low'], close=df['Close'], name="価格"
    ))
    
    # EMAライン
    fig.add_trace(go.Scatter(
        x=df.index, y=df[ema_col], line=dict(color='orange', width=2), name=f"EMA({ema_period})"
    ))
    
    # チャートのレイアウト調整（スマホでも見やすく）
    fig.update_layout(height=600, margin=dict(l=0, r=0, t=30, b=0), xaxis_rangeslider_visible=False)
    
    st.plotly_chart(fig, use_container_width=True)

else:
    st.warning("データの取得に失敗しました。ティッカーシンボルを確認してください。")