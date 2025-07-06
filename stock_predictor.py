import yfinance as yf
import pandas as pd
import numpy as np
import streamlit as st
import json
import io
from datetime import datetime, timedelta

# ✳️ RSI Calculation
def calculate_rsi(data, window=14):
    delta = data['Close'].diff()
    gain = delta.where(delta > 0, 0).rolling(window=window).mean()
    loss = -delta.where(delta < 0, 0).rolling(window=window).mean()
    rs = gain / loss
    rsi = 100 - (100 / (1 + rs))
    return rsi

# 🔍 Stock Evaluation
def evaluate_stock(symbol, rsi_threshold):
    end_date = datetime.today()
    start_date = end_date - timedelta(days=30)

    try:
        stock_data = yf.download(symbol, start=start_date, end=end_date)
        if stock_data.empty or len(stock_data) < 15:
            return symbol, None, None, None, None, "Skipped – insufficient data"

        stock_data['RSI'] = calculate_rsi(stock_data)
        rsi_today = float(stock_data['RSI'].iloc[-1])
        price_today = float(stock_data['Close'].iloc[-1])
        price_yesterday = float(stock_data['Close'].iloc[-2])
        volume_today = float(stock_data['Volume'].iloc[-1])
        volume_yesterday = float(stock_data['Volume'].iloc[-2])

        price_up = price_today > price_yesterday
        volume_up = volume_today > volume_yesterday

        if rsi_today > rsi_threshold and price_up and volume_up:
            verdict = "Strong Buy"
        else:
            verdict = "Not a strong buy"

        return symbol, round(price_today, 2), round(rsi_today, 2), price_up, volume_up, verdict

    except Exception as e:
        return symbol, None, None, None, None, f"Skipped – error fetching data ({e})"

# 🖥️ Streamlit UI
def main():
    st.set_page_config(page_title="NSE Stock Screener", layout="wide")
    st.title("📊 RSI + Volume Based Stock Screener (NSE)")

    # 🎛️ RSI Threshold Input
    rsi_threshold = st.slider("Set RSI Threshold for Strong Buy", min_value=30, max_value=70, value=50)

    # 📁 Load Symbols from symbols.json
    try:
        with open("symbols.json") as f:
            symbols = json.load(f)["symbols"]
    except Exception as e:
        st.error(f"Error loading symbols.json: {e}")
        return

    st.markdown(f"Evaluating **{len(symbols)}** stocks with RSI threshold > **{rsi_threshold}**")

    strong_buy_data = []

    for symbol in symbols:
        name, price, rsi, price_up, volume_up, verdict = evaluate_stock(symbol, rsi_threshold)

        with st.expander(f"{symbol} Analysis"):
            if verdict.startswith("Skipped"):
                st.warning(verdict)
            else:
                st.write(f"**Current Price**: ₹{price}")
                st.write(f"**RSI**: {rsi}")
                st.write(f"**Price Increased**: {'✅' if price_up else '❌'}")
                st.write(f"**Volume Increased**: {'✅' if volume_up else '❌'}")
                st.markdown(f"### Verdict: **{verdict}**")

                if verdict == "Strong Buy":
                    strong_buy_data.append({
                        "Symbol": symbol,
                        "Price": price,
                        "RSI": rsi
                    })

    # ✅ Final Summary & CSV Download
    st.markdown("---")
    st.success(f"🏆 Found {len(strong_buy_data)} Strong Buy stock(s):")

    if strong_buy_data:
        summary_df = pd.DataFrame(strong_buy_data)
        st.dataframe(summary_df.set_index("Symbol"))

        # 📤 Downloadable CSV
        csv_buffer = io.StringIO()
        summary_df.to_csv(csv_buffer, index=False)
        csv_contents = csv_buffer.getvalue()

        timestamp_str = datetime.now().strftime("%Y-%m-%d_%H-%M")
        filename = f"strong_buy_{timestamp_str}.csv"

        st.download_button(
            label="📥 Download Strong Buy Stocks as CSV",
            data=csv_contents,
            file_name=filename,
            mime="text/csv"
        )

if __name__ == "__main__":
    main()
