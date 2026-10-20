import math
from datetime import date, timedelta

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
import yfinance as yf

st.set_page_config(page_title="StockEasy", page_icon="📈", layout="wide")

st.markdown("""
<style>
.block-container {padding-top: 1.5rem; max-width: 1400px;}
div[data-testid="stMetric"] {background: rgba(120,120,120,.07); padding: 14px; border-radius: 12px;}
.small-note {font-size: .85rem; opacity: .8;}
</style>
""", unsafe_allow_html=True)

st.title("📈 StockEasy")
st.caption("Understand stocks with long-term charts, company fundamentals, risks, comparisons, and a simple investment calculator.")

st.warning(
    "Educational research tool — not investment advice. Market data may be delayed, incomplete, or unavailable. "
    "Do not use this app alone to make investment decisions."
)

COMMON_TICKERS = {
    "Indian examples": ["RELIANCE.NS", "TCS.NS", "HDFCBANK.NS", "INFY.NS", "ICICIBANK.NS", "ITC.NS", "SBIN.NS", "NIFTYBEES.NS"],
    "US examples": ["AAPL", "MSFT", "NVDA", "GOOGL", "AMZN", "TSLA", "KO", "SPY"],
    "Global examples": ["ASML", "TSM", "BABA", "NVO", "SHEL"]
}

@st.cache_data(ttl=900, show_spinner=False)
def load_history(symbol: str):
    ticker = yf.Ticker(symbol.strip().upper())
    hist = ticker.history(period="max", auto_adjust=True, actions=True)
    if hist is None or hist.empty:
        return pd.DataFrame(), {}
    hist = hist.copy()
    hist.index = pd.to_datetime(hist.index).tz_localize(None)
    info = {}
    try:
        info = ticker.get_info() or {}
    except Exception:
        try:
            info = ticker.info or {}
        except Exception:
            info = {}
    return hist, info

@st.cache_data(ttl=1800, show_spinner=False)
def load_financials(symbol: str):
    t = yf.Ticker(symbol.strip().upper())
    output = {}
    for label, attr in [
        ("Annual income statement", "income_stmt"),
        ("Annual balance sheet", "balance_sheet"),
        ("Annual cash flow", "cashflow"),
        ("Quarterly income statement", "quarterly_income_stmt"),
    ]:
        try:
            output[label] = getattr(t, attr)
        except Exception:
            output[label] = pd.DataFrame()
    return output

def fmt_money(value, currency=""):
    try:
        if value is None or pd.isna(value):
            return "N/A"
        value = float(value)
        sign = "-" if value < 0 else ""
        value = abs(value)
        if value >= 1e12:
            return f"{sign}{currency}{value/1e12:.2f}T"
        if value >= 1e9:
            return f"{sign}{currency}{value/1e9:.2f}B"
        if value >= 1e7:
            return f"{sign}{currency}{value/1e7:.2f}Cr"
        if value >= 1e6:
            return f"{sign}{currency}{value/1e6:.2f}M"
        return f"{sign}{currency}{value:,.2f}"
    except Exception:
        return "N/A"

def fmt_pct(value):
    try:
        if value is None or pd.isna(value):
            return "N/A"
        return f"{float(value) * 100:.2f}%"
    except Exception:
        return "N/A"

def safe_num(info, key):
    try:
        v = info.get(key)
        return float(v) if v is not None and pd.notna(v) else None
    except Exception:
        return None

def metrics_for(hist):
    if hist.empty or "Close" not in hist:
        return {}
    close = hist["Close"].dropna()
    if len(close) < 2:
        return {}
    daily = close.pct_change().dropna()
    years = max((close.index[-1] - close.index[0]).days / 365.25, 0)
    cagr = (close.iloc[-1] / close.iloc[0]) ** (1 / years) - 1 if years > 0 and close.iloc[0] > 0 else None
    drawdown = close / close.cummax() - 1
    return {
        "last": float(close.iloc[-1]),
        "start": float(close.iloc[0]),
        "total_return": float(close.iloc[-1] / close.iloc[0] - 1),
        "cagr": cagr,
        "volatility": float(daily.std() * math.sqrt(252)) if len(daily) > 1 else None,
        "max_drawdown": float(drawdown.min()),
        "high": float(close.max()),
        "low": float(close.min()),
        "start_date": close.index[0],
        "end_date": close.index[-1],
    }

def explain_metric(name, value):
    explanations = {
        "P/E ratio": "Price compared with earnings per share. A high value can mean high growth expectations, but can also mean an expensive valuation.",
        "Price-to-book": "Share price compared with the accounting value of net assets. It is more useful for some industries than others.",
        "Return on equity": "Profit relative to shareholders' equity. Compare with similar companies and check whether debt is unusually high.",
        "Debt-to-equity": "Debt relative to equity. Definitions vary by provider; compare firms in the same industry.",
        "Profit margin": "The share of revenue left as profit. Check the trend over several years.",
        "Annualized volatility": "A rough measure of how much daily prices moved. Higher volatility means a bumpier historical ride, not a prediction.",
        "Maximum drawdown": "The largest peak-to-trough fall in the selected history. It shows a historical worst decline, not the maximum possible future loss.",
        "CAGR": "Compound annual growth rate: the smoothed yearly growth rate between the first and last prices. It hides the ups and downs along the way.",
    }
    st.caption(f"**{name}:** {explanations.get(name, '')}")

with st.sidebar:
    st.header("Find a stock")
    symbol = st.text_input("Ticker symbol", value="RELIANCE.NS", help="Examples: RELIANCE.NS (India), TCS.NS, AAPL (US), MSFT (US), ASML (Europe).")
    symbol = symbol.strip().upper()
    st.markdown("**Example symbols**")
    for group, symbols in COMMON_TICKERS.items():
        with st.expander(group):
            st.write(", ".join(symbols))
    st.caption("For NSE stocks, Yahoo Finance-style symbols often end in `.NS`; BSE listings often end in `.BO`. Availability varies.")

if not symbol:
    st.info("Enter a ticker symbol in the sidebar to get started.")
    st.stop()

with st.spinner(f"Loading historical data for {symbol}…"):
    try:
        hist, info = load_history(symbol)
    except Exception as exc:
        st.error(f"Could not load data for {symbol}. Check the ticker and your internet connection.")
        st.caption(f"Technical detail: {exc}")
        st.stop()

if hist.empty:
    st.error(f"No historical data was returned for **{symbol}**. Try a different ticker (for example RELIANCE.NS or AAPL).")
    st.stop()

company = info.get("longName") or info.get("shortName") or symbol
currency = info.get("currency") or ""
exchange = info.get("exchange") or info.get("fullExchangeName") or "Not provided"
metrics = metrics_for(hist)
st.subheader(company)
st.caption(f"{symbol} · {exchange} · Currency: {currency or 'not provided'} · Latest available record: {hist.index[-1].date()}")

# Select the history window for the main chart
period_options = {
    "1 month": 30, "6 months": 183, "1 year": 365, "3 years": 365*3,
    "5 years": 365*5, "10 years": 365*10, "Maximum available": None
}

overview, fundamentals, comparison, calculator, statements = st.tabs(
    ["📊 Overview & risks", "🏢 Fundamentals", "⚖️ Compare stocks", "🧮 Investment calculator", "📑 Financial statements"]
)

with overview:
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Latest available close", f"{currency} {metrics['last']:,.2f}")
    col2.metric("Full available-history return", fmt_pct(metrics["total_return"]))
    col3.metric("Annualized volatility", fmt_pct(metrics["volatility"]))
    col4.metric("Maximum drawdown", fmt_pct(metrics["max_drawdown"]))

    selected_period = st.selectbox("Chart period", list(period_options.keys()), index=5)
    days = period_options[selected_period]
    chart_data = hist if days is None else hist[hist.index >= (hist.index[-1] - pd.Timedelta(days=days))]
    if chart_data.empty:
        chart_data = hist
    chart_type = st.radio("Chart style", ["Line", "Candlestick"], horizontal=True)
    if chart_type == "Line":
        fig = px.line(chart_data, x=chart_data.index, y="Close", title=f"{symbol} — adjusted historical price ({selected_period.lower()})")
        fig.update_traces(line_width=2)
    else:
        fig = go.Figure(data=[go.Candlestick(
            x=chart_data.index, open=chart_data["Open"], high=chart_data["High"],
            low=chart_data["Low"], close=chart_data["Close"], name=symbol
        )])
        fig.update_layout(title=f"{symbol} — historical candles ({selected_period.lower()})", xaxis_rangeslider_visible=False)
    fig.update_layout(height=480, xaxis_title="Date", yaxis_title=f"Price ({currency or 'currency not provided'})", hovermode="x unified")
    st.plotly_chart(fig, use_container_width=True)

    if "Volume" in chart_data.columns:
        volume_fig = px.bar(chart_data, x=chart_data.index, y="Volume", title="Trading volume")
        volume_fig.update_layout(height=220, xaxis_title="Date", yaxis_title="Volume")
        st.plotly_chart(volume_fig, use_container_width=True)

    st.markdown("### Historical performance and risk")
    r1, r2, r3 = st.columns(3)
    r1.metric("CAGR over full available history", fmt_pct(metrics["cagr"]))
    r2.metric("Highest adjusted close in history", f"{currency} {metrics['high']:,.2f}")
    r3.metric("Lowest adjusted close in history", f"{currency} {metrics['low']:,.2f}")
    explain_metric("CAGR", metrics["cagr"])
    explain_metric("Annualized volatility", metrics["volatility"])
    explain_metric("Maximum drawdown", metrics["max_drawdown"])

    annual = hist["Close"].resample("YE").last().dropna()
    annual_returns = annual.pct_change().dropna() * 100
    if not annual_returns.empty:
        st.markdown("### Calendar-year returns")
        annual_df = annual_returns.rename("Return (%)").to_frame()
        annual_df.index = annual_df.index.year
        st.bar_chart(annual_df)
        st.dataframe(annual_df.style.format("{:.2f}%"), use_container_width=True)

    st.download_button(
        "Download displayed historical data (CSV)",
        data=chart_data.to_csv(index_label="Date").encode("utf-8"),
        file_name=f"{symbol.replace('.', '_')}_history.csv",
        mime="text/csv"
    )
    st.caption("Prices are adjusted historical prices from the data provider where available; the latest date may not be today's date.")

with fundamentals:
    st.markdown("### Company snapshot")
    info_rows = [
        ("Sector", info.get("sector")), ("Industry", info.get("industry")),
        ("Country", info.get("country")), ("Website", info.get("website")),
        ("Employees", info.get("fullTimeEmployees")),
        ("Market capitalization", fmt_money(info.get("marketCap"), currency + " ")),
        ("Enterprise value", fmt_money(info.get("enterpriseValue"), currency + " ")),
        ("Revenue (latest provider snapshot)", fmt_money(info.get("totalRevenue"), currency + " ")),
        ("Net income (latest provider snapshot)", fmt_money(info.get("netIncomeToCommon"), currency + " ")),
        ("EPS", fmt_money(info.get("trailingEps"), currency + " ")),
        ("P/E ratio", info.get("trailingPE")),
        ("Forward P/E", info.get("forwardPE")),
        ("Price-to-book", info.get("priceToBook")),
        ("Return on equity", fmt_pct(info.get("returnOnEquity"))),
        ("Profit margin", fmt_pct(info.get("profitMargins"))),
        ("Debt-to-equity (provider definition)", info.get("debtToEquity")),
        ("Dividend yield", fmt_pct(info.get("dividendYield"))),
        ("52-week range low", fmt_money(info.get("fiftyTwoWeekLow"), currency + " ")),
        ("52-week range high", fmt_money(info.get("fiftyTwoWeekHigh"), currency + " ")),
        ("Beta", info.get("beta")),
    ]
    fundamentals_df = pd.DataFrame(info_rows, columns=["Metric", "Value"])
    fundamentals_df["Value"] = fundamentals_df["Value"].apply(lambda x: "Not available" if x is None or (isinstance(x, float) and pd.isna(x)) or x == "" else x)
    st.dataframe(fundamentals_df, hide_index=True, use_container_width=True)
    for key in ["P/E ratio", "Price-to-book", "Return on equity", "Debt-to-equity", "Profit margin"]:
        explain_metric(key, None)
    st.info("Company metrics may be missing, stale, or defined differently across markets. Verify important figures against official company filings.")

with comparison:
    st.markdown("### Compare up to 5 stocks")
    compare_input = st.text_input("Comma-separated tickers", value="RELIANCE.NS,TCS.NS,AAPL,MSFT")
    compare_symbols = list(dict.fromkeys([s.strip().upper() for s in compare_input.split(",") if s.strip()]))[:5]
    compare_period = st.selectbox("Comparison period", ["1 year", "3 years", "5 years", "10 years"], index=3, key="compare_period")
    compare_days = {"1 year":365, "3 years":1095, "5 years":1825, "10 years":3650}[compare_period]
    normalized = pd.DataFrame()
    summary_rows = []
    with st.spinner("Loading comparison data…"):
        for s in compare_symbols:
            try:
                h, inf = load_history(s)
                if h.empty:
                    continue
                h = h[h.index >= (h.index[-1] - pd.Timedelta(days=compare_days))]
                if h.empty:
                    continue
                close = h["Close"].dropna()
                if close.empty:
                    continue
                normalized[s] = (close / close.iloc[0]) * 100
                mm = metrics_for(h)
                summary_rows.append({
                    "Ticker": s,
                    "Company": inf.get("shortName") or inf.get("longName") or s,
                    "Return in selected window": fmt_pct(mm.get("total_return")),
                    "Annualized volatility": fmt_pct(mm.get("volatility")),
                    "Maximum drawdown": fmt_pct(mm.get("max_drawdown")),
                    "Data points": len(close),
                })
            except Exception:
                continue
    if not normalized.empty:
        st.caption("All lines are indexed to 100 at the start of each available series. This compares percentage movement, not absolute share prices.")
        st.line_chart(normalized, height=400)
        st.dataframe(pd.DataFrame(summary_rows), hide_index=True, use_container_width=True)
    else:
        st.warning("No comparison data was loaded. Check ticker symbols and try again.")

with calculator:
    st.markdown("### What if you had invested?")
    st.caption("A historical illustration using adjusted prices. It does not include taxes, fees, slippage, or all possible cash-flow details.")
    invest_amount = st.number_input("Starting investment amount", min_value=1.0, value=10000.0, step=1000.0)
    available_start = hist.index[0].date()
    available_end = hist.index[-1].date()
    calc_start = st.date_input("Investment start date", value=max(available_start, available_end - timedelta(days=365*5)), min_value=available_start, max_value=available_end)
    calc_end = st.date_input("Valuation date", value=available_end, min_value=available_start, max_value=available_end)
    close = hist["Close"].dropna()
    start_candidates = close[close.index.date >= calc_start]
    end_candidates = close[close.index.date <= calc_end]
    if calc_start >= calc_end:
        st.error("Choose a valuation date later than the investment start date.")
    elif start_candidates.empty or end_candidates.empty:
        st.warning("There is no price data for the selected date range.")
    else:
        start_date_used = start_candidates.index[0]
        end_date_used = end_candidates.index[-1]
        start_price = float(start_candidates.iloc[0])
        end_price = float(end_candidates.iloc[-1])
        shares = invest_amount / start_price
        final_value = shares * end_price
        profit_loss = final_value - invest_amount
        ret = final_value / invest_amount - 1
        c1, c2, c3 = st.columns(3)
        c1.metric("Illustrative ending value", f"{currency} {final_value:,.2f}")
        c2.metric("Profit / loss", f"{currency} {profit_loss:,.2f}", fmt_pct(ret))
        c3.metric("Approx. shares", f"{shares:,.4f}")
        st.caption(f"Used nearest available prices: {start_date_used.date()} at {start_price:,.2f} and {end_date_used.date()} at {end_price:,.2f}.")
        st.line_chart(close[(close.index >= start_date_used) & (close.index <= end_date_used)], height=300)

with statements:
    st.markdown("### Provider financial statements")
    st.caption("Statements are shown as returned by the provider. Missing years or rows are normal; confirm with company filings.")
    financials = load_financials(symbol)
    statement_name = st.selectbox("Choose statement", list(financials.keys()))
    statement_df = financials.get(statement_name, pd.DataFrame())
    if statement_df is not None and not statement_df.empty:
        display_df = statement_df.copy()
        display_df.columns = [str(c.date()) if hasattr(c, "date") else str(c) for c in display_df.columns]
        st.dataframe(display_df, use_container_width=True)
        st.download_button(
            "Download statement as CSV",
            data=display_df.to_csv().encode("utf-8"),
            file_name=f"{symbol.replace('.', '_')}_{statement_name.lower().replace(' ', '_')}.csv",
            mime="text/csv"
        )
    else:
        st.info("This provider did not return this statement for the selected ticker.")

st.divider()
st.markdown("**Data and limitations**")
st.write(
    "This first version uses the `yfinance` open-source Python package to access Yahoo Finance data. "
    "It is an unofficial interface, intended by its maintainers for research and educational use; availability, "
    "accuracy, coverage, and rate limits are not guaranteed. Check the data provider's current terms before use. "
    "Do not redistribute data or deploy this as a commercial service without confirming you have the necessary rights."
)
st.caption("StockEasy is a learning project. It does not provide personalized financial advice or execute trades.")
