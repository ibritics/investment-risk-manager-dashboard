import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
import numpy as np
import os
import asyncio
from datetime import datetime
import yaml

with open("config.yaml", "r") as file:
    config = yaml.safe_load(file)

os.environ["GEMINI_API_KEY"] = config["api_keys"]["gemini"]

from google.adk.agents import Agent
from google.adk.models.google_llm import Gemini
from google.adk.runners import InMemoryRunner
from google.genai import types

# ── page config ───────────────────────────────────────────────────────────────
st.set_page_config(page_title="Portfolio Dashboard", layout="wide", page_icon="📊")

# ── CSS ───────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Geist+Mono:wght@400;500&family=Geist:wght@400;500;600&display=swap');

html, body, [class*="css"] { font-family: 'Geist', sans-serif; }
.stApp { background-color: #f9f8f6; }
h1, h2, h3 { font-family: 'Geist', sans-serif !important; color: #1a1a1a !important; }

.metric-card {
    background: #ffffff;
    border: 1px solid #e8e4de;
    border-radius: 12px;
    padding: 18px 20px;
}

[data-testid="stDataFrame"] {
    background: #ffffff !important;
    border-radius: 10px !important;
}

div[data-testid="stRadio"] > div { gap: 4px !important; flex-direction: row !important; }
div[data-testid="stRadio"] label {
    background: #f2f0ec !important;
    border: 1px solid #e2ddd6 !important;
    border-radius: 6px !important;
    padding: 4px 12px !important;
    color: #888075 !important;
    font-family: 'Geist Mono', monospace !important;
    font-size: 11px !important;
    cursor: pointer !important;
    transition: all 0.15s ease !important;
}
div[data-testid="stRadio"] label:hover { border-color: #c8a97a !important; color: #5a4a2e !important; }
div[data-testid="stRadio"] label[data-checked="true"] {
    border-color: #c8a97a !important;
    color: #5a4a2e !important;
    background: #fdf6ec !important;
}

.stButton > button {
    background: #1a1a1a !important;
    color: #f9f8f6 !important;
    border: none !important;
    border-radius: 8px !important;
    font-family: 'Geist Mono', monospace !important;
    font-size: 11px !important;
    padding: 6px 16px !important;
    transition: opacity 0.15s ease !important;
}
.stButton > button:hover { opacity: 0.75 !important; }

.stDownloadButton > button {
    background: #f2f0ec !important;
    color: #1a1a1a !important;
    border: 1px solid #e2ddd6 !important;
    border-radius: 8px !important;
    font-family: 'Geist Mono', monospace !important;
    font-size: 11px !important;
}

[data-testid="stMultiSelect"] > div {
    background: #ffffff !important;
    border: 1px solid #e2ddd6 !important;
    border-radius: 8px !important;
}

.section-divider { border: none; border-top: 1px solid #e8e4de; margin: 20px 0; }

/* ── info button — ghost style override ── */
button[data-testid="stBaseButton-secondary"] {
    background: transparent !important;
    color: #a09880 !important;
    border: 1px solid #e2ddd6 !important;
    padding: 2px 9px !important;
    font-size: 11px !important;
    border-radius: 6px !important;
    font-family: 'Geist Mono', monospace !important;
}
button[data-testid="stBaseButton-secondary"]:hover {
    border-color: #c8a97a !important;
    color: #5a4a2e !important;
    opacity: 1 !important;
}

/* ── docs panel ── */
.docs-panel {
    background: #ffffff;
    border: 1px solid #e8e4de;
    border-radius: 12px;
    padding: 22px 26px;
    margin-bottom: 14px;
    font-family: 'Geist', sans-serif;
    font-size: 13px;
    color: #2a2520;
    line-height: 1.75;
}
.docs-panel h3 {
    font-size: 13px !important;
    font-weight: 600 !important;
    color: #1a1a1a !important;
    margin: 18px 0 5px !important;
    padding-top: 14px;
    border-top: 1px solid #f0ece6;
}
.docs-panel h3:first-child { border-top: none !important; margin-top: 0 !important; padding-top: 0 !important; }
.docs-panel code {
    font-family: 'Geist Mono', monospace;
    font-size: 11px;
    background: #f4f1ec;
    border: 1px solid #e8e4de;
    border-radius: 4px;
    padding: 2px 6px;
    color: #5a4a2e;
}
.docs-panel pre {
    background: #f4f1ec;
    border: 1px solid #e8e4de;
    border-radius: 8px;
    padding: 11px 15px;
    font-family: 'Geist Mono', monospace;
    font-size: 11px;
    color: #3a3028;
    overflow-x: auto;
    margin: 8px 0;
}
.docs-panel table {
    width: 100%;
    border-collapse: collapse;
    font-size: 12px;
    margin: 10px 0;
}
.docs-panel th {
    background: #f4f1ec;
    padding: 6px 10px;
    text-align: left;
    font-weight: 600;
    border: 1px solid #e8e4de;
    color: #5a4a2e;
    font-family: 'Geist Mono', monospace;
    font-size: 11px;
}
.docs-panel td { padding: 6px 10px; border: 1px solid #e8e4de; vertical-align: top; }
.docs-panel .ref {
    font-size: 11px;
    color: #8a7a60;
    font-family: 'Geist Mono', monospace;
    border-left: 2px solid #e2ddd6;
    padding-left: 10px;
    margin: 6px 0;
}
.docs-panel a { color: #6b8fd4; text-decoration: none; }
.docs-panel a:hover { text-decoration: underline; }
.badge-green { display:inline-block;padding:1px 7px;border-radius:4px;background:#f0faf4;color:#2d7a4f;border:1px solid #b8ddc8;font-family:'Geist Mono',monospace;font-size:10px; }
.badge-blue  { display:inline-block;padding:1px 7px;border-radius:4px;background:#f2f5fc;color:#6b8fd4;border:1px solid #c0d0ed;font-family:'Geist Mono',monospace;font-size:10px; }
.badge-amber { display:inline-block;padding:1px 7px;border-radius:4px;background:#fdf8f0;color:#c8963c;border:1px solid #e8d4a0;font-family:'Geist Mono',monospace;font-size:10px; }
.badge-red   { display:inline-block;padding:1px 7px;border-radius:4px;background:#fdf2f0;color:#c0392b;border:1px solid #e8c0ba;font-family:'Geist Mono',monospace;font-size:10px; }
</style>
""", unsafe_allow_html=True)

# ── session state for info panels ─────────────────────────────────────────────
for _k in ["show_holdings_info", "show_matrix_info", "show_agent_info"]:
    if _k not in st.session_state:
        st.session_state[_k] = False

# ── header ────────────────────────────────────────────────────────────────────
last_update = datetime.now().strftime("%d %b %Y — %H:%M")
st.markdown(f"""
<div style="display:flex;justify-content:space-between;align-items:flex-end;
            margin-bottom:24px;padding-bottom:16px;border-bottom:1px solid #e8e4de;">
    <div>
        <h1 style="font-size:22px;font-weight:600;margin:0;color:#1a1a1a;letter-spacing:-0.3px;">
            Portfolio Dashboard</h1>
        <p style="color:#a09880;font-family:'Geist Mono',monospace;font-size:11px;margin:4px 0 0;">
            Not financial advice · data refreshes every hour</p>
    </div>
    <p style="color:#b0a890;font-family:'Geist Mono',monospace;font-size:11px;margin:0;">
        Updated {last_update}</p>
</div>
""", unsafe_allow_html=True)

# ── STEP 1: load ledger ───────────────────────────────────────────────────────
df_ledger = pd.read_csv("financial_ledger.csv", parse_dates=["Date"])
tickers_list = df_ledger["Ticker"].unique().tolist()

# ── STEP 2: price data ────────────────────────────────────────────────────────
@st.cache_data(ttl=3600)
def load_price_data(tickers):
    df = yf.download(tickers, period="5y", auto_adjust=True)["Close"]
    return df.reset_index()

with st.spinner("Loading market data..."):
    df_prices = load_price_data(tickers_list)

# ── STEP 3: returns & volatility ──────────────────────────────────────────────
df_prices_long = df_prices.melt(id_vars="Date", var_name="Ticker", value_name="Close")
df_prices_long["Close"] = df_prices_long.groupby("Ticker")["Close"].ffill()
df_prices_long["Date"] = pd.to_datetime(df_prices_long["Date"]).dt.tz_localize(None)
df_ledger["Date"] = pd.to_datetime(df_ledger["Date"]).dt.tz_localize(None)
df_prices_long = df_prices_long.sort_values(["Ticker", "Date"])

df_prices_long["Daily_Return_%"] = (
    df_prices_long.groupby("Ticker")["Close"].pct_change(fill_method=None) * 100
).round(2)

df_prices_long["Volatility_30d"] = df_prices_long.groupby("Ticker")["Daily_Return_%"].transform(
    lambda x: x.rolling(window=30).std()
)
df_prices_long["Volatility_Ann_%"] = (df_prices_long["Volatility_30d"] * np.sqrt(252)).round(2)

# ── STEP 4: market value & exposure ──────────────────────────────────────────
df_investments = df_ledger.groupby("Ticker")["Quantity"].sum().reset_index()
df_merged = pd.merge(df_prices_long, df_investments, on="Ticker", how="left")
df_merged["Market_Value"] = df_merged["Quantity"] * df_merged["Close"]
df_merged["total_daily_val"] = df_merged.groupby("Date")["Market_Value"].transform("sum")
df_merged["Exposure_%"] = (df_merged["Market_Value"] / df_merged["total_daily_val"] * 100).round(2)

# ── STEP 5: ROI, P&L, MoM, YoY ───────────────────────────────────────────────
today = df_prices_long["Date"].max()

purchase_list = []
for ticker in tickers_list:
    df_t_prices = df_prices_long[df_prices_long["Ticker"] == ticker].sort_values("Date")
    df_t_ledger = df_ledger[df_ledger["Ticker"] == ticker].sort_values("Date")
    if df_t_prices.empty or df_t_ledger.empty:
        continue
    merged = pd.merge_asof(df_t_ledger, df_t_prices, on="Date", direction="nearest")
    merged["Ticker"] = ticker
    merged = merged.rename(columns={"Close": "Purchase_Price"})
    purchase_list.append(merged[["Ticker", "Date", "Quantity", "Purchase_Price"]])

purchase_data = pd.concat(purchase_list, ignore_index=True)
purchase_data["Initial_Investment"] = purchase_data["Purchase_Price"] * purchase_data["Quantity"]

initial = purchase_data.groupby("Ticker").agg(
    Initial_Investment=("Initial_Investment", "sum"),
    Total_Quantity=("Quantity", "sum")
).reset_index()

latest_prices = (
    df_prices_long.sort_values("Date")
    .groupby("Ticker").last()[["Close"]]
    .reset_index()
    .rename(columns={"Close": "Latest_Price"})
)

summary = initial.merge(latest_prices, on="Ticker")
summary["Total_Investment"] = (summary["Latest_Price"] * summary["Total_Quantity"]).round(2)
summary["Unrealized Profit ($)"] = (summary["Total_Investment"] - summary["Initial_Investment"]).round(2)
summary["ROI (%)"] = summary.apply(
    lambda r: round((r["Unrealized Profit ($)"] / r["Initial_Investment"]) * 100, 2)
    if r["Initial_Investment"] > 0 else None, axis=1
)

def get_price_on(days_ago):
    target = today - pd.Timedelta(days=days_ago)
    result = (
        df_prices_long.groupby("Ticker")
        .apply(
            lambda x: x[x["Date"] <= target]["Close"].iloc[-1]
            if not x[x["Date"] <= target].empty else None,
            include_groups=False
        )
        .reset_index()
    )
    result.columns = ["Ticker", f"Price_{days_ago}d"]
    return result

summary = summary.merge(get_price_on(1), on="Ticker")
summary = summary.merge(get_price_on(30), on="Ticker")
summary = summary.merge(get_price_on(365), on="Ticker")

summary["DoD (%)"] = ((summary["Latest_Price"] - summary["Price_1d"])   / summary["Price_1d"]   * 100).round(2)
summary["MoM (%)"] = ((summary["Latest_Price"] - summary["Price_30d"])  / summary["Price_30d"]  * 100).round(2)
summary["YoY (%)"] = summary.apply(
    lambda r: round(((r["Latest_Price"] - r["Price_365d"]) / r["Price_365d"]) * 100, 2)
    if pd.notna(r["Price_365d"]) and r["Price_365d"] > 0 else None, axis=1
)

latest_vol = df_merged[df_merged["Date"] == today][["Ticker", "Volatility_Ann_%", "Exposure_%"]]
summary = summary.merge(latest_vol, on="Ticker", how="left")
summary = summary.rename(columns={
    "Volatility_Ann_%": "Ann. Volatility (%)",
    "Exposure_%": "Portfolio Weight (%)"
})

# ── agent input ───────────────────────────────────────────────────────────────
cutoff_date = today - pd.Timedelta(days=30)
df_last_30d = df_merged[df_merged["Date"] > cutoff_date].copy().sort_values(["Ticker", "Date"])
agent_summary = df_last_30d.groupby("Ticker").agg(
    Avg_Exposure=("Exposure_%", "mean"),
    Volatility=("Volatility_Ann_%", "last"),
    Price_Change_30d=("Close", lambda x: round((x.iloc[-1] - x.iloc[0]) / x.iloc[0] * 100, 2))
).reset_index()
agent_summary = agent_summary.merge(summary[["Ticker", "ROI (%)"]], on="Ticker")
agent_summary["Avg_Exposure"] = agent_summary["Avg_Exposure"].round(1)
agent_summary["Volatility"]   = agent_summary["Volatility"].round(1)

# ── METRIC CARDS ──────────────────────────────────────────────────────────────
total_capital = summary["Total_Investment"].sum()
unrealized    = summary["Unrealized Profit ($)"].sum()
mom_avg       = summary["MoM (%)"].mean()
mom_color     = "#2d7a4f" if mom_avg >= 0 else "#c0392b"
mom_sign      = "+" if mom_avg >= 0 else ""
total_roi     = round((unrealized / (total_capital - unrealized)) * 100, 2) if (total_capital - unrealized) > 0 else 0
roi_color     = "#2d7a4f" if total_roi >= 0 else "#c0392b"
unr_color     = "#2d7a4f" if unrealized >= 0 else "#c0392b"

st.markdown(f"""
<div style="display:grid;grid-template-columns:repeat(4,1fr);gap:12px;margin-bottom:20px;">
    <div class="metric-card">
        <div style="font-size:10px;color:#a09880;letter-spacing:1.2px;text-transform:uppercase;
                    font-family:'Geist Mono',monospace;margin-bottom:10px;">Total Capital</div>
        <div style="font-size:28px;font-weight:600;color:#1a1a1a;font-family:'Geist Mono',monospace;
                    letter-spacing:-1px;">${total_capital:,.0f}</div>
        <div style="font-size:10px;color:#b0a890;font-family:'Geist Mono',monospace;margin-top:6px;">current value</div>
    </div>
    <div class="metric-card">
        <div style="font-size:10px;color:#a09880;letter-spacing:1.2px;text-transform:uppercase;
                    font-family:'Geist Mono',monospace;margin-bottom:10px;">Unrealised P&amp;L</div>
        <div style="font-size:28px;font-weight:600;color:{unr_color};font-family:'Geist Mono',monospace;
                    letter-spacing:-1px;">${unrealized:+,.0f}</div>
        <div style="font-size:10px;color:#b0a890;font-family:'Geist Mono',monospace;margin-top:6px;">gain since purchase</div>
    </div>
    <div class="metric-card">
        <div style="font-size:10px;color:#a09880;letter-spacing:1.2px;text-transform:uppercase;
                    font-family:'Geist Mono',monospace;margin-bottom:10px;">Total ROI</div>
        <div style="font-size:28px;font-weight:600;color:{roi_color};font-family:'Geist Mono',monospace;
                    letter-spacing:-1px;">{total_roi:+.2f}%</div>
        <div style="font-size:10px;color:#b0a890;font-family:'Geist Mono',monospace;margin-top:6px;">all-time return</div>
    </div>
    <div class="metric-card">
        <div style="font-size:10px;color:#a09880;letter-spacing:1.2px;text-transform:uppercase;
                    font-family:'Geist Mono',monospace;margin-bottom:10px;">MoM Change</div>
        <div style="font-size:28px;font-weight:600;color:{mom_color};font-family:'Geist Mono',monospace;
                    letter-spacing:-1px;">{mom_sign}{mom_avg:.2f}%</div>
        <div style="font-size:10px;color:#b0a890;font-family:'Geist Mono',monospace;margin-top:6px;">last 30 days avg</div>
    </div>
</div>
""", unsafe_allow_html=True)

# ── LAYOUT ────────────────────────────────────────────────────────────────────
col1, col2 = st.columns([1.2, 1.8])

# ═══════════════════════════════════════════════════════════════════════════════
# LEFT: holdings table
# ═══════════════════════════════════════════════════════════════════════════════
with col1:
    h_label, h_info, h_export = st.columns([3, 0.7, 1])

    with h_label:
        st.markdown(
            "<p style='font-size:13px;font-weight:600;color:#1a1a1a;margin-bottom:8px;"
            "font-family:Geist,sans-serif;'>Holdings</p>",
            unsafe_allow_html=True
        )
    with h_info:
        if st.button("ⓘ info", key="btn_holdings_info", type="secondary"):
            st.session_state.show_holdings_info = not st.session_state.show_holdings_info
    with h_export:
        csv = summary.to_csv(index=False).encode("utf-8")
        st.download_button("↓ Export", csv, "portfolio_summary.csv", "text/csv")

    # ── holdings info panel ────────────────────────────────────────────────────
    if st.session_state.show_holdings_info:
        st.markdown("""
<div class="docs-panel">

<h3>ROI (%)</h3>
Return on investment since the date of purchase.
<pre>ROI = (Current Value − Cost Basis) / Cost Basis × 100</pre>
Cost basis is computed by matching each ledger entry (date + quantity) to the closest historical
price using <code>pd.merge_asof</code>, so purchases made at different times are individually
costed and then summed.

<h3>Unrealised Profit ($)</h3>
The dollar gain or loss if the position were closed today.
<pre>Unrealised P&L = (Latest Price × Quantity Held) − Cost Basis</pre>
This is "unrealised" because no sale has taken place — it is a mark-to-market figure.

<h3>MoM (%) — Month-on-Month</h3>
Price change over the last 30 calendar days.
<pre>MoM = (Price_today − Price_30d_ago) / Price_30d_ago × 100</pre>

<h3>YoY (%) — Year-on-Year</h3>
Price change over the last 365 calendar days, using the same formula scaled to a one-year window.

<h3>Ann. Volatility (%)</h3>
Annualised historical volatility — the standard industry measure of price risk. Computed as the
30-day rolling standard deviation of daily returns, then scaled to one year:
<pre>σ_annual = σ_daily_30d × √252</pre>
The factor √252 comes from the <b>square-root-of-time rule</b>: there are approximately 252 trading
days in a US equity year, so daily volatility scales to annual by multiplying by √252. This is the
convention used across equity markets, options pricing (Black–Scholes), and risk systems.
<div class="ref">Hull, J. (2022). Options, Futures, and Other Derivatives (11th ed.). Pearson. Ch. 15.</div>

<h3>Portfolio Weight (%)</h3>
The share of total portfolio market value attributable to each asset on the most recent trading day.
<pre>Weight_i = Market_Value_i / Σ Market_Value × 100</pre>

</div>
""", unsafe_allow_html=True)

    cols_to_show = [
        "Ticker", "ROI (%)", "Unrealized Profit ($)",
        "MoM (%)", "YoY (%)", "Ann. Volatility (%)", "Portfolio Weight (%)"
    ]
    st.dataframe(
        summary[cols_to_show].style.format({
            "ROI (%)":               lambda v: f"{v:+.2f}%" if isinstance(v, float) else "—",
            "Unrealized Profit ($)": lambda v: f"${v:+,.0f}" if isinstance(v, float) else "—",
            "MoM (%)":               lambda v: f"{v:+.2f}%" if isinstance(v, float) else "—",
            "YoY (%)":               lambda v: f"{v:+.2f}%" if isinstance(v, float) else "—",
            "Ann. Volatility (%)":   lambda v: f"{v:.2f}%"  if isinstance(v, float) else "—",
            "Portfolio Weight (%)":  lambda v: f"{v:.2f}%"  if isinstance(v, float) else "—",
        }).map(
            lambda v: "color: #2d7a4f; font-weight:500" if isinstance(v, float) and v > 0
                 else ("color: #c0392b; font-weight:500" if isinstance(v, float) and v < 0 else ""),
            subset=["ROI (%)", "MoM (%)", "YoY (%)"]
        ),
        use_container_width=True,
        height=280
    )

# ═══════════════════════════════════════════════════════════════════════════════
# RIGHT: risk matrix
# ═══════════════════════════════════════════════════════════════════════════════
with col2:
    m_label, m_info = st.columns([6, 0.7])

    with m_label:
        st.markdown(
            "<p style='font-size:13px;font-weight:600;color:#1a1a1a;margin-bottom:2px;"
            "font-family:Geist,sans-serif;'>Risk Matrix</p>",
            unsafe_allow_html=True
        )
    with m_info:
        if st.button("ⓘ info", key="btn_matrix_info", type="secondary"):
            st.session_state.show_matrix_info = not st.session_state.show_matrix_info

    st.markdown(
        "<p style='color:#a09880;font-size:10px;font-family:Geist Mono,monospace;margin-bottom:10px;'>"
        "Annualised volatility vs portfolio weight — bubble size = unrealised P&amp;L</p>",
        unsafe_allow_html=True
    )

    # ── risk matrix info panel ─────────────────────────────────────────────────
    if st.session_state.show_matrix_info:
        st.markdown("""
<div class="docs-panel">

<h3>What it shows</h3>
A two-dimensional scatter where every holding is positioned by two independent risk dimensions:
<table>
  <tr><th>Axis</th><th>Variable</th><th>What it captures</th></tr>
  <tr><td>X (horizontal)</td><td>Ann. Volatility (%)</td><td>How much the asset's price swings — individual asset risk</td></tr>
  <tr><td>Y (vertical)</td><td>Portfolio Weight (%)</td><td>How much capital is concentrated in that asset</td></tr>
  <tr><td>Bubble size</td><td>Unrealised P&amp;L ($)</td><td>How much profit is currently at stake</td></tr>
  <tr><td>Bubble colour</td><td>ROI bracket</td><td>Overall performance since purchase</td></tr>
</table>

<h3>Why these two axes?</h3>
Risk in a portfolio has two distinct sources: the <b>riskiness of the individual asset</b> (its volatility)
and <b>concentration</b> (its share of your total capital). An asset can be individually calm but
dangerous if it represents 60% of your portfolio, and vice versa.
<br><br>
This is grounded in <b>Modern Portfolio Theory</b>. Markowitz (1952) formalised that portfolio risk depends
on both each asset's own variance and its weight in the portfolio:
<pre>σ²_p = w₁²σ₁² + w₂²σ₂² + 2w₁w₂σ₁₂</pre>
The matrix visualises the w²σ² terms — the interaction of weight and volatility — without requiring
a full covariance matrix.
<div class="ref">Markowitz, H. (1952). Portfolio Selection. The Journal of Finance, 7(1), 77–91.</div>

<h3>The four quadrants</h3>
Threshold lines are drawn at <b>25% volatility</b> and <b>25% portfolio weight</b>:
<table>
  <tr><th>Quadrant</th><th>Volatility</th><th>Weight</th><th>Interpretation</th></tr>
  <tr><td><span class="badge-green">LOW RISK</span></td><td>&lt; 25%</td><td>&lt; 25%</td><td>Calm and small — low urgency</td></tr>
  <tr><td><span class="badge-amber">HIGH VOL</span></td><td>&gt; 25%</td><td>&lt; 25%</td><td>Risky but small position — monitor</td></tr>
  <tr><td><span class="badge-blue">CONCENTRATED</span></td><td>&lt; 25%</td><td>&gt; 25%</td><td>Calm asset but overweighted — rebalance candidate</td></tr>
  <tr><td><span class="badge-red">DANGER ZONE</span></td><td>&gt; 25%</td><td>&gt; 25%</td><td>High vol AND high exposure — highest priority</td></tr>
</table>

<h3>Concentration threshold — regulatory context</h3>
The 25% weight line is informed by the Basel Committee on Banking Supervision (BCBS), which sets a
hard cap at <b>25% of Tier 1 capital</b> for single-name exposures at banks. The same principle
applies to a retail portfolio: concentration in any single name amplifies loss given an adverse event.
<div class="ref">BIS/BCBS (2014). Supervisory framework for measuring and controlling large exposures (BCBS 283). <a href="https://www.bis.org/publ/bcbs283.pdf">bis.org/publ/bcbs283.pdf</a></div>
<div class="ref">BIS/BCBS (2006). Studies on credit risk concentration (BCBS WP 15). <a href="https://www.bis.org/publ/bcbs_wp15.pdf">bis.org/publ/bcbs_wp15.pdf</a></div>
<div class="ref">BIS/BCBS (2019). Minimum capital requirements for market risk — FRTB (BCBS 457). <a href="https://www.bis.org/bcbs/publ/d457.pdf">bis.org/bcbs/publ/d457.pdf</a></div>

<h3>Colour coding — ROI brackets</h3>
<table>
  <tr><th>Colour</th><th>ROI range</th><th>Meaning</th></tr>
  <tr><td><span class="badge-green">●</span></td><td>≥ 20%</td><td>Strong performer — consider taking some profit</td></tr>
  <tr><td><span class="badge-blue">●</span></td><td>0 – 20%</td><td>Moderate gain — hold and monitor</td></tr>
  <tr><td><span class="badge-amber">●</span></td><td>−10 – 0%</td><td>Slight loss — watch closely</td></tr>
  <tr><td><span class="badge-red">●</span></td><td>&lt; −10%</td><td>Significant loss — review thesis</td></tr>
</table>

</div>
""", unsafe_allow_html=True)

    # ── build chart ────────────────────────────────────────────────────────────
    risk_df = summary[[
        "Ticker", "Ann. Volatility (%)", "Portfolio Weight (%)",
        "Unrealized Profit ($)", "ROI (%)"
    ]].copy().dropna(subset=["Ann. Volatility (%)", "Portfolio Weight (%)"])

    min_size, max_size = 18, 56
    profit_vals = risk_df["Unrealized Profit ($)"].fillna(0)
    p_min, p_max = profit_vals.min(), profit_vals.max()
    if p_max > p_min:
        risk_df["bubble_size"] = min_size + (profit_vals - p_min) / (p_max - p_min) * (max_size - min_size)
    else:
        risk_df["bubble_size"] = (min_size + max_size) / 2

    def roi_color(roi):
        if pd.isna(roi):  return "#c8c0b0"
        if roi >= 20:     return "#2d7a4f"
        if roi >= 0:      return "#6b8fd4"
        if roi >= -10:    return "#c8963c"
        return "#c0392b"

    risk_df["color"] = risk_df["ROI (%)"].apply(roi_color)

    x_max = max(risk_df["Ann. Volatility (%)"].max() * 1.3 + 4, 50)
    y_max = max(risk_df["Portfolio Weight (%)"].max() * 1.3 + 4, 40)
    x_mid, y_mid = 25, 25

    fig_risk = go.Figure()

    quad_fills = [
        (0,     0,     x_mid, y_mid, "rgba(45,122,79,0.05)",   "LOW RISK",     1,       1,       "#2d7a4f"),
        (x_mid, 0,     x_max, y_mid, "rgba(200,150,60,0.05)",  "HIGH VOL",     x_mid+1, 1,       "#c8963c"),
        (0,     y_mid, x_mid, y_max, "rgba(107,143,212,0.05)", "CONCENTRATED", 1,       y_mid+1, "#6b8fd4"),
        (x_mid, y_mid, x_max, y_max, "rgba(192,57,43,0.07)",   "DANGER ZONE",  x_mid+1, y_mid+1, "#c0392b"),
    ]
    for x0, y0, x1, y1, fill, label, lx, ly, lc in quad_fills:
        fig_risk.add_shape(type="rect", x0=x0, y0=y0, x1=x1, y1=y1,
                           fillcolor=fill, line=dict(width=0), layer="below")
        fig_risk.add_annotation(x=lx, y=ly, text=label, showarrow=False,
                                font=dict(family="Geist Mono", size=8, color=lc),
                                xanchor="left", yanchor="bottom", opacity=0.55)

    for shape in [
        dict(type="line", x0=x_mid, x1=x_mid, y0=0, y1=y_max),
        dict(type="line", x0=0, x1=x_max, y0=y_mid, y1=y_mid),
    ]:
        fig_risk.add_shape(**shape, line=dict(color="#d8d0c4", width=1, dash="dot"))

    for _, row in risk_df.iterrows():
        fig_risk.add_trace(go.Scatter(
            x=[row["Ann. Volatility (%)"]],
            y=[row["Portfolio Weight (%)"]],
            mode="markers+text",
            marker=dict(size=row["bubble_size"], color=row["color"],
                        opacity=0.80, line=dict(color="rgba(255,255,255,0.9)", width=2)),
            text=[row["Ticker"]],
            textposition="middle center",
            textfont=dict(family="Geist Mono", size=9, color="#ffffff"),
            name=row["Ticker"],
            customdata=[[row["ROI (%)"], row["Unrealized Profit ($)"], row["Portfolio Weight (%)"]]],
            hovertemplate=(
                f"<b>{row['Ticker']}</b><br>"
                "Volatility: %{x:.1f}%<br>"
                "Weight: %{y:.1f}%<br>"
                "ROI: %{customdata[0]:.2f}%<br>"
                "Unrealised P&L: $%{customdata[1]:,.0f}"
                "<extra></extra>"
            ),
            showlegend=False
        ))

    fig_risk.update_layout(
        paper_bgcolor="#ffffff",
        plot_bgcolor="#faf9f7",
        font=dict(family="Geist Mono", color="#a09880", size=11),
        xaxis=dict(title=dict(text="Ann. Volatility (%)", font=dict(color="#a09880", size=10)),
                   gridcolor="#ede9e3", showline=False, zeroline=False,
                   range=[0, x_max], tickfont=dict(color="#b0a890", size=10)),
        yaxis=dict(title=dict(text="Portfolio Weight (%)", font=dict(color="#a09880", size=10)),
                   gridcolor="#ede9e3", showline=False, zeroline=False,
                   range=[0, y_max], tickfont=dict(color="#b0a890", size=10)),
        margin=dict(l=8, r=8, t=8, b=8),
        height=310,
        hovermode="closest",
        hoverlabel=dict(bgcolor="#ffffff", bordercolor="#e8e4de",
                        font=dict(family="Geist Mono", color="#1a1a1a", size=11))
    )

    st.plotly_chart(fig_risk, use_container_width=True)

    st.markdown("""
    <div style="display:flex;gap:20px;margin-top:2px;flex-wrap:wrap;">
        <span style="font-size:9px;font-family:'Geist Mono',monospace;color:#2d7a4f;">● ROI ≥ 20%</span>
        <span style="font-size:9px;font-family:'Geist Mono',monospace;color:#6b8fd4;">● ROI 0 – 20%</span>
        <span style="font-size:9px;font-family:'Geist Mono',monospace;color:#c8963c;">● ROI −10 – 0%</span>
        <span style="font-size:9px;font-family:'Geist Mono',monospace;color:#c0392b;">● ROI &lt; −10%</span>
        <span style="font-size:9px;font-family:'Geist Mono',monospace;color:#b0a890;margin-left:8px;">bubble size = unrealised P&amp;L</span>
    </div>
    """, unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════════════════════════════
# STRATEGY AGENT
# ═══════════════════════════════════════════════════════════════════════════════
st.markdown("<hr class='section-divider'>", unsafe_allow_html=True)

a_label, a_info = st.columns([9, 0.7])
with a_label:
    st.markdown(
        "<p style='font-size:13px;font-weight:600;color:#1a1a1a;margin-bottom:2px;"
        "font-family:Geist,sans-serif;'>Strategy Agent</p>",
        unsafe_allow_html=True
    )
with a_info:
    if st.button("ⓘ info", key="btn_agent_info", type="secondary"):
        st.session_state.show_agent_info = not st.session_state.show_agent_info

st.markdown(
    "<p style='color:#a09880;font-size:10px;font-family:Geist Mono,monospace;margin-bottom:12px;'>"
    "AI-powered BUY / SELL / HOLD / REBALANCE signals based on volatility, concentration and momentum</p>",
    unsafe_allow_html=True
)

# ── agent info panel ───────────────────────────────────────────────────────────
if st.session_state.show_agent_info:
    st.markdown("""
<div class="docs-panel">

<h3>How it works</h3>
The agent (Google Gemini 2.5 Flash Lite via Google ADK) reads the 30-day aggregated portfolio
summary and applies a deterministic decision tree to produce one signal per ticker. The LLM is
used to generate the plain-English explanation — the decision logic itself is rule-based.

<h3>Decision rules — applied in priority order</h3>
<table>
  <tr><th>#</th><th>Condition</th><th>Signal</th></tr>
  <tr><td>1</td><td>ROI &gt; 500% AND weight &gt; 20%</td><td><span class="badge-red">SELL</span> — take profit before concentration risk compounds</td></tr>
  <tr><td>2</td><td>Weight &gt; 30%</td><td><span class="badge-blue">REBALANCE</span> — single name too dominant regardless of performance</td></tr>
  <tr><td>3</td><td>Volatility &gt; 40% AND 30d change &lt; −5%</td><td><span class="badge-red">SELL</span> — high-risk asset in downtrend</td></tr>
  <tr><td>4</td><td>Volatility &lt; 15% AND 30d change &gt; 0% AND weight &lt; 10%</td><td><span class="badge-green">BUY</span> — calm, trending asset with room to grow</td></tr>
  <tr><td>5</td><td>Otherwise</td><td><span class="badge-amber">HOLD</span></td></tr>
</table>

<h3>Input data (last 30 days)</h3>
<table>
  <tr><th>Column</th><th>Description</th></tr>
  <tr><td><code>Avg_Exposure</code></td><td>Average % of total portfolio this asset represented over 30 days</td></tr>
  <tr><td><code>Volatility</code></td><td>Most recent annualised volatility %</td></tr>
  <tr><td><code>Price_Change_30d</code></td><td>% price change over the last 30 days</td></tr>
  <tr><td><code>ROI</code></td><td>Total return since purchase %</td></tr>
</table>

<h3>Disclaimer</h3>
This is <b>not financial advice</b>. The agent output is generated by a large language model and
may contain errors. Always consult a qualified financial adviser before making investment decisions.
Past performance is not a guarantee of future results.

</div>
""", unsafe_allow_html=True)

if st.button("Run Analysis"):
    with st.spinner("Analysing portfolio..."):
        retry_config = types.HttpRetryOptions(
            attempts=5, exp_base=7, initial_delay=1,
            http_status_codes=[429, 500, 503, 504]
        )

        analyst_agent = Agent(
            name="StrategyAgent",
            model=Gemini(model="gemini-2.5-flash-lite", retry_options=retry_config),
            instruction=f"""
You are a Senior Portfolio Manager giving clear, direct advice to a retail investor.

Here is the portfolio data for the last 30 days:
{agent_summary.to_string()}

Columns:
- Avg_Exposure: % of total portfolio this asset represents
- Volatility: annualized volatility %
- Price_Change_30d: % price change over last 30 days
- ROI: total return since purchase %

Decision rules (apply in order):
1. SELL if ROI > 500% AND Avg_Exposure > 20%
2. REBALANCE if Avg_Exposure > 30%
3. SELL if Volatility > 40 AND Price_Change_30d < -5
4. BUY if Volatility < 15 AND Price_Change_30d > 0 AND Avg_Exposure < 10%
5. HOLD otherwise

For each ticker write ONE line in this exact format:
TICKER | ACTION | Plain English explanation with the actual numbers

No intro, no summary, no extra text. One line per ticker only.
            """,
        )

        runner = InMemoryRunner(agent=analyst_agent)

        try:
            loop = asyncio.get_event_loop()
            if loop.is_closed():
                raise RuntimeError
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

        response = loop.run_until_complete(
            runner.run_debug("Provide concise strategic advice for my portfolio holdings.")
        )

        output = ""
        for event in response:
            if hasattr(event, "content") and event.content:
                for part in event.content.parts:
                    if hasattr(part, "text") and part.text:
                        output += part.text + "\n"

        action_styles = {
            "BUY":       {"color": "#2d7a4f", "bg": "#f0faf4", "border": "#b8ddc8", "icon": "↑ BUY"},
            "SELL":      {"color": "#c0392b", "bg": "#fdf2f0", "border": "#e8c0ba", "icon": "↓ SELL"},
            "HOLD":      {"color": "#8a7a60", "bg": "#faf8f4", "border": "#e2ddd6", "icon": "— HOLD"},
            "REBALANCE": {"color": "#6b8fd4", "bg": "#f2f5fc", "border": "#c0d0ed", "icon": "⇄ REBALANCE"},
        }

        st.markdown(
            f"<p style='color:#b0a890;font-size:10px;font-family:Geist Mono,monospace;margin-bottom:12px;'>"
            f"Analysis at {datetime.now().strftime('%H:%M')} — Not financial advice</p>",
            unsafe_allow_html=True
        )

        lines = [l.strip() for l in output.strip().split("\n") if "|" in l]
        agent_cols = st.columns(len(tickers_list))

        for i, line in enumerate(lines[:len(tickers_list)]):
            parts = [p.strip() for p in line.split("|", 2)]
            if len(parts) >= 2:
                ticker = parts[0].strip()
                action = parts[1].strip().upper()
                reason = parts[2].strip() if len(parts) > 2 else ""
                s = action_styles.get(action, {
                    "color": "#1a1a1a", "bg": "#f9f8f6",
                    "border": "#e8e4de", "icon": action
                })
                with agent_cols[i % len(agent_cols)]:
                    st.markdown(f"""
                    <div style="background:{s['bg']};border:1px solid {s['border']};
                                border-radius:10px;padding:16px;margin-bottom:8px;">
                        <div style="font-size:11px;color:#8a7a60;font-family:'Geist Mono',monospace;
                                    margin-bottom:6px;">{ticker}</div>
                        <div style="font-size:16px;font-weight:600;color:{s['color']};
                                    font-family:'Geist Mono',monospace;margin-bottom:10px;">{s['icon']}</div>
                        <div style="font-size:12px;color:#4a4035;line-height:1.6;
                                    font-family:Geist,sans-serif;">{reason}</div>
                    </div>""", unsafe_allow_html=True)