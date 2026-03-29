import streamlit as st
import yfinance as yf
import pandas as pd
from ta.trend import EMAIndicator, ADXIndicator
import plotly.graph_objects as go

# ページ設定
st.set_page_config(page_title="もっちのMarketPhase", layout="wide")
st.title("🚀 もっちのFX解析ツール (MarketPhase / CHIMERA)")

# --- サイドバーで設定変更 (MT5のインプットパラメータを再現) ---
st.sidebar.header("⚙️ パラメータ設定")
symbol = st.sidebar.text_input("通貨ペア", "USDJPY=X")
interval = st.sidebar.selectbox("時間足", ["5m", "15m", "1h", "1d"], index=1)

# MT5と同じデフォルト値に設定
adx_period = st.sidebar.number_input("ADX Period", value=14)
adx_threshold = st.sidebar.number_input("ADX Threshold", value=25.0)
ema_period = st.sidebar.number_input("EMA Period", value=50)
noise_filter_bars = st.sidebar.number_input("NoiseFilter Bars", value=2, min_value=1)

# --- データ取得 ---
df = yf.download(symbol, period="5d", interval=interval)

if not df.empty:
    # データ成形 (yfinance仕様変更対応)
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.droplevel(1)

    # --- インジケーターの計算 ---
    df['EMA'] = EMAIndicator(close=df['Close'], window=ema_period).ema_indicator()
    df['ADX'] = ADXIndicator(high=df['High'], low=df['Low'], close=df['Close'], window=adx_period).adx()
    
    # --- 生のカラーインデックス計算 (GetRawColorIndexの再現) ---
    # 0: Uptrend (Maroon), 1: Range (None), 2: Downtrend (DarkBlue)
    raw_colors = []
    for i in range(len(df)):
        if df['ADX'].iloc[i] >= adx_threshold:
            if df['Close'].iloc[i] > df['EMA'].iloc[i]:
                raw_colors.append(0)
            else:
                raw_colors.append(2)
        else:
            raw_colors.append(1)
            
    df['RawColor'] = raw_colors

    # --- ノイズフィルターの適用 ---
    filtered_colors = [1] * len(df) # 初期値はRange(1)
    filter_bars = max(1, noise_filter_bars)
    
    for i in range(len(df)):
        if i < filter_bars:
            filtered_colors[i] = df['RawColor'].iloc[i]
            continue
            
        is_consistent = True
        for j in range(1, filter_bars):
            if df['RawColor'].iloc[i - j] != df['RawColor'].iloc[i]:
                is_consistent = False
                break
                
        if is_consistent:
            filtered_colors[i] = df['RawColor'].iloc[i]
        else:
            filtered_colors[i] = filtered_colors[i - 1]
            
    df['FinalColor'] = filtered_colors

    # --- 最新のデータでシグナル判定 ---
    latest_color = df['FinalColor'].iloc[-1]
    
    st.subheader("💡 現在のMarketPhase")
    if latest_color == 0:
        st.success("🔥 強い上昇トレンド発生中！ (Buy Phase)")
    elif latest_color == 2:
        st.error("📉 強い下降トレンド発生中！ (Sell Phase)")
    else:
        st.info("⏳ レンジ相場（様子見）です。")

    # --- チャート描画 (Plotly) ---
    fig = go.Figure()
    
    # ローソク足
    fig.add_trace(go.Candlestick(
        x=df.index, open=df['Open'], high=df['High'], low=df['Low'], close=df['Close'], name="価格"
    ))
    
    # EMAライン (Magenta)
    fig.add_trace(go.Scatter(
        x=df.index, y=df['EMA'], line=dict(color='magenta', width=2), name=f"Trend EMA({ema_period})"
    ))
    
    # --- 背景のハイライト（DRAW_COLOR_HISTOGRAMの再現） ---
    # 色が変わったタイミングで長方形(vrect)を描画して背景色をつける
    current_color = df['FinalColor'].iloc[0]
    start_idx = df.index[0]
    
    for i in range(1, len(df)):
        if df['FinalColor'].iloc[i] != current_color:
            # 色が変わったら、そこまでの期間を塗りつぶす
            if current_color == 0: # Maroon
                fig.add_vrect(x0=start_idx, x1=df.index[i], fillcolor="maroon", opacity=0.2, layer="below", line_width=0)
            elif current_color == 2: # DarkBlue
                fig.add_vrect(x0=start_idx, x1=df.index[i], fillcolor="darkblue", opacity=0.2, layer="below", line_width=0)
            
            # 次の期間のスタート地点を更新
            current_color = df['FinalColor'].iloc[i]
            start_idx = df.index[i]
            
    # 最後の期間の塗りつぶし
    if current_color == 0:
        fig.add_vrect(x0=start_idx, x1=df.index[-1], fillcolor="maroon", opacity=0.2, layer="below", line_width=0)
    elif current_color == 2:
        fig.add_vrect(x0=start_idx, x1=df.index[-1], fillcolor="darkblue", opacity=0.2, layer="below", line_width=0)

    # チャートのレイアウト調整
    fig.update_layout(height=600, margin=dict(l=0, r=0, t=30, b=0), xaxis_rangeslider_visible=False)
    
    st.plotly_chart(fig, use_container_width=True)

else:
    st.warning("データの取得に失敗しました。")
