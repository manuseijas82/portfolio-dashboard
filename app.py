import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime
import requests

# ── CONFIG ────────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Mi Portfolio",
    page_icon="📊",
    layout="wide"
)

# ── ESTILOS ───────────────────────────────────────────────────────────────────
st.markdown("""
<style>
    .stApp { background-color: #0a0a0f; }
    .main-title {
        font-size: 2rem; font-weight: 700;
        color: #58a6ff; margin-bottom: 0px;
    }
    .subtitle { font-size: 0.85rem; color: #8b949e; margin-bottom: 20px; }
    .card {
        background: #161b22; border-radius: 14px;
        padding: 18px; margin-bottom: 12px; border-left: 4px solid;
    }
    .card-up      { border-left-color: #3fb950; }
    .card-down    { border-left-color: #f85149; }
    .card-closed  { border-left-color: #8b949e; }
    .card-ticker  { font-size: 1.2rem; font-weight: 700; color: #f0f6fc; }
    .card-badge-usd {
        background: #1f4068; color: #58a6ff;
        font-size: 0.65rem; padding: 2px 8px;
        border-radius: 10px; font-weight: 600;
    }
    .card-badge-ars {
        background: #3d2b00; color: #e3b341;
        font-size: 0.65rem; padding: 2px 8px;
        border-radius: 10px; font-weight: 600;
    }
    .card-badge-closed {
        background: #21262d; color: #8b949e;
        font-size: 0.65rem; padding: 2px 8px;
        border-radius: 10px; font-weight: 600;
    }
    .price-label {
        font-size: 0.65rem; color: #8b949e;
        text-transform: uppercase; letter-spacing: 0.8px;
    }
    .price-entry  { font-size: 0.95rem; font-weight: 600; color: #e0e0e0; }
    .price-up     { font-size: 0.95rem; font-weight: 600; color: #3fb950; }
    .price-down   { font-size: 0.95rem; font-weight: 600; color: #f85149; }
    .pct-up       { font-size: 1.1rem; font-weight: 700; color: #3fb950; }
    .pct-down     { font-size: 1.1rem; font-weight: 700; color: #f85149; }
    .pnl-up       { font-size: 1.1rem; font-weight: 700; color: #3fb950; }
    .pnl-down     { font-size: 1.1rem; font-weight: 700; color: #f85149; }
    .pct-closed-up   { font-size: 1.1rem; font-weight: 700; color: #3fb950; opacity: 0.75; }
    .pct-closed-down { font-size: 1.1rem; font-weight: 700; color: #f85149; opacity: 0.75; }
    .closed-stamp {
        font-size: 0.7rem; color: #8b949e;
        text-transform: uppercase; letter-spacing: 1px;
        border: 1px solid #30363d; border-radius: 6px;
        padding: 2px 6px; margin-left: 6px;
    }
    .section-title {
        font-size: 1.3rem; font-weight: 700;
        color: #f0f6fc; margin: 10px 0 16px 0;
    }
</style>
""", unsafe_allow_html=True)

# ── CARTERA ───────────────────────────────────────────────────────────────────
PORTFOLIO = [
    {"ticker": "NU",   "entry": 14.75,   "currency": "USD", "yTicker": "NU",    "cedears": 196, "ratio": 2},
    {"ticker": "MELI", "entry": 1677.38, "currency": "USD", "yTicker": "MELI",  "cedears": 95,  "ratio": 120},
    {"ticker": "MSFT", "entry": 405.00,  "currency": "USD", "yTicker": "MSFT",  "cedears": 106, "ratio": 30},
    {"ticker": "V",    "entry": 303.90,  "currency": "USD", "yTicker": "V",     "cedears": 23, "ratio": 18},
    {"ticker": "UL",   "entry": 28800,   "currency": "ARS", "yTicker": "UL.BA", "cedears": 20,  "ratio": 3},
    {"ticker": "JNJ",  "entry": 238.56,  "currency": "USD", "yTicker": "JNJ",   "cedears": 25,  "ratio": 15},
    {"ticker": "VST",  "entry": 146.67,  "currency": "USD", "yTicker": "VST",   "cedears": 66,  "ratio": 3},
    {"ticker": "PLTR", "entry": 135.34,  "currency": "USD", "yTicker": "PLTR",  "cedears": 8,   "ratio": 3},
    {"ticker": "MCD",  "entry": 278.79,  "currency": "USD", "yTicker": "MCD",   "cedears": 32,  "ratio": 24},
    {"ticker": "MDT",  "entry": 77.88,   "currency": "USD", "yTicker": "MDT",   "cedears": 24,  "ratio": 4},
    {"ticker": "MMM",  "entry": 153.54,  "currency": "USD", "yTicker": "MMM",   "cedears": 31,  "ratio": 10},
    {"ticker": "META", "entry": 609.19,  "currency": "USD", "yTicker": "META",  "cedears": 15,  "ratio": 24},
    {"ticker": "UBER", "entry": 70.44,   "currency": "USD", "yTicker": "UBER",  "cedears": 13,  "ratio": 2},
]

# ── POSICION CERRADA INICIAL ──────────────────────────────────────────────────
CLOSED_INITIAL = [
    {
        "ticker":      "VIST",
        "entry":       69.45,
        "close_price": 78.15,
        "currency":    "USD",
        "cedears":     0,
        "ratio":       3,
        "pct":         round(((78.15 - 69.45) / 69.45) * 100, 2),
        "pnl_usd":     None,
        "close_date":  "Manual",
    }
]

# ── SESSION STATE ─────────────────────────────────────────────────────────────
if "closed_positions" not in st.session_state:
    st.session_state.closed_positions = CLOSED_INITIAL.copy()
if "active_portfolio" not in st.session_state:
    st.session_state.active_portfolio = PORTFOLIO.copy()
if "confirm_close" not in st.session_state:
    st.session_state.confirm_close = {}
if "close_prices" not in st.session_state:
    st.session_state.close_prices = {}

# ── FUNCIONES ─────────────────────────────────────────────────────────────────
@st.cache_data(ttl=300)
def get_ccl():
    try:
        res  = requests.get("https://dolarapi.com/v1/dolares/contadoconliqui", timeout=10)
        data = res.json()
        venta = data.get("venta")
        if venta:
            return round(float(venta), 2)
    except:
        pass
    return None

@st.cache_data(ttl=300)
def get_price(yticker):
    try:
        t     = yf.Ticker(yticker)
        price = t.fast_info.last_price
        return round(float(price), 2) if price else None
    except:
        return None

def calc_shares(item):
    cedears = item.get("cedears", 0)
    ratio   = item.get("ratio", 1)
    if not cedears or not ratio:
        return 0
    return cedears / ratio

def calc_pnl_usd(item, current_price, ccl):
    shares = calc_shares(item)
    if shares == 0:
        return None
    if item["currency"] == "USD":
        return round((current_price - item["entry"]) * shares, 2)
    else:
        if ccl and ccl > 0:
            return round(((current_price - item["entry"]) / ccl) * shares, 2)
        return None

def calc_invested_usd(item, ccl):
    shares = calc_shares(item)
    if shares == 0:
        return None
    if item["currency"] == "USD":
        return round(item["entry"] * shares, 2)
    else:
        if ccl and ccl > 0:
            return round((item["entry"] / ccl) * shares, 2)
        return None

def fmt_usd(n):
    return f"${n:,.2f}"

def fmt_ars(n):
    return f"${n:,.0f}"

def fmt_pnl(n):
    if n is None:
        return "—"
    sign = "+" if n >= 0 else ""
    return f"{sign}${n:,.2f}"

def do_close_position(ticker, close_price, ccl):
    item = next(
        (x for x in st.session_state.active_portfolio if x["ticker"] == ticker), None
    )
    if not item:
        return
    shares  = calc_shares(item)
    pct     = round(((close_price - item["entry"]) / item["entry"]) * 100, 2)
    if item["currency"] == "USD":
        pnl_usd = round((close_price - item["entry"]) * shares, 2)
    else:
        pnl_usd = round(((close_price - item["entry"]) / ccl) * shares, 2) if ccl else None

    st.session_state.closed_positions.append({
        "ticker":      ticker,
        "entry":       item["entry"],
        "close_price": close_price,
        "currency":    item["currency"],
        "cedears":     item["cedears"],
        "ratio":       item["ratio"],
        "pct":         pct,
        "pnl_usd":     pnl_usd,
        "close_date":  datetime.now().strftime("%d/%m/%Y %H:%M"),
    })
    st.session_state.active_portfolio = [
        x for x in st.session_state.active_portfolio if x["ticker"] != ticker
    ]
    st.session_state.confirm_close.pop(ticker, None)
    st.session_state.close_prices.pop(ticker, None)
    st.cache_data.clear()

# ── HEADER ────────────────────────────────────────────────────────────────────
col_title, col_refresh = st.columns([4, 1])
with col_title:
    st.markdown('<p class="main-title">📊 Mi Portfolio</p>', unsafe_allow_html=True)
    st.markdown(
        f'<p class="subtitle">Última actualización: '
        f'{datetime.now().strftime("%d/%m/%Y %H:%M:%S")}</p>',
        unsafe_allow_html=True
    )
with col_refresh:
    if st.button("⟳ Actualizar precios", use_container_width=True):
        st.cache_data.clear()
        st.rerun()

st.divider()

# ── OBTENER DATOS ─────────────────────────────────────────────────────────────
with st.spinner("Cargando precios del mercado..."):
    ccl = get_ccl()
    results = []
    for item in st.session_state.active_portfolio:
        price    = get_price(item["yTicker"])
        shares   = calc_shares(item)
        pct      = round(((price - item["entry"]) / item["entry"]) * 100, 2) if price else None
        pnl_usd  = calc_pnl_usd(item, price, ccl) if price else None
        invested = calc_invested_usd(item, ccl)
        results.append({
            **item,
            "price":    price,
            "shares":   shares,
            "pct":      pct,
            "pnl_usd":  pnl_usd,
            "invested": invested,
        })

# ── SUMMARY ───────────────────────────────────────────────────────────────────
valid      = [r for r in results if r["pct"] is not None]
ups        = [r for r in valid if r["pct"] >= 0]
downs      = [r for r in valid if r["pct"] < 0]
best       = max(valid, key=lambda x: x["pct"]) if valid else None
worst      = min(valid, key=lambda x: x["pct"]) if valid else None
total_pnl  = sum(r["pnl_usd"] for r in valid if r["pnl_usd"] is not None)
total_inv  = sum(r["invested"] for r in results if r["invested"] is not None)
ccl_text   = f"${ccl:,.2f}" if ccl else "N/D"

c1, c2, c3, c4, c5, c6, c7 = st.columns(7)
with c1: st.metric("💱 Dólar CCL",        ccl_text)
with c2: st.metric("📁 Posiciones",        len(st.session_state.active_portfolio))
with c3: st.metric("💰 Capital Invertido", f"${total_inv:,.0f}" if total_inv else "—")
with c4: st.metric("📈 P&L Total USD",
                   f"{'+' if total_pnl >= 0 else ''}${total_pnl:,.2f}",
                   delta=f"{(total_pnl/total_inv*100):.1f}%" if total_inv else None)
with c5: st.metric("🟢 En Ganancia",       len(ups))
with c6: st.metric("🔴 En Pérdida",        len(downs))
with c7:
    if best: st.metric("🏆 Mejor", best["ticker"], f"+{best['pct']:.1f}%")

st.divider()

# ── GRÁFICOS ──────────────────────────────────────────────────────────────────
tab1, tab2 = st.tabs(["📊 Variación %", "💵 Ganancia/Pérdida USD"])

with tab1:
    if valid:
        df = pd.DataFrame(valid).dropna(subset=["pct"]).sort_values("pct", ascending=True)
        colors = ["#3fb950" if p >= 0 else "#f85149" for p in df["pct"]]
        fig = go.Figure(go.Bar(
            x=df["pct"], y=df["ticker"], orientation="h",
            marker_color=colors,
            text=[f"+{p:.1f}%" if p >= 0 else f"{p:.1f}%" for p in df["pct"]],
            textposition="outside",
            textfont=dict(color="white", size=12),
        ))
        fig.update_layout(
            paper_bgcolor="#0a0a0f", plot_bgcolor="#161b22",
            font=dict(color="#e0e0e0"), height=420,
            margin=dict(l=10, r=80, t=30, b=10),
            xaxis=dict(showgrid=True, gridcolor="#21262d", zeroline=True,
                       zerolinecolor="#58a6ff", zerolinewidth=2, ticksuffix="%"),
            yaxis=dict(showgrid=False),
            title=dict(text="Variación % por posición",
                       font=dict(color="#8b949e", size=13), x=0)
        )
        st.plotly_chart(fig, use_container_width=True)

with tab2:
    pnl_valid = [r for r in results if r["pnl_usd"] is not None]
    if pnl_valid:
        df2 = pd.DataFrame(pnl_valid).sort_values("pnl_usd", ascending=True)
        colors2 = ["#3fb950" if p >= 0 else "#f85149" for p in df2["pnl_usd"]]
        fig2 = go.Figure(go.Bar(
            x=df2["pnl_usd"], y=df2["ticker"], orientation="h",
            marker_color=colors2,
            text=[f"+${p:,.0f}" if p >= 0 else f"-${abs(p):,.0f}" for p in df2["pnl_usd"]],
            textposition="outside",
            textfont=dict(color="white", size=12),
        ))
        fig2.update_layout(
            paper_bgcolor="#0a0a0f", plot_bgcolor="#161b22",
            font=dict(color="#e0e0e0"), height=420,
            margin=dict(l=10, r=100, t=30, b=10),
            xaxis=dict(showgrid=True, gridcolor="#21262d", zeroline=True,
                       zerolinecolor="#58a6ff", zerolinewidth=2, tickprefix="$"),
            yaxis=dict(showgrid=False),
            title=dict(text="Ganancia / Pérdida en USD por posición",
                       font=dict(color="#8b949e", size=13), x=0)
        )
        st.plotly_chart(fig2, use_container_width=True)

st.divider()

# ── CARDS ACTIVAS ─────────────────────────────────────────────────────────────
st.markdown('<p class="section-title">📂 Posiciones Activas</p>', unsafe_allow_html=True)

cols_per_row = 4
rows = [results[i:i+cols_per_row] for i in range(0, len(results), cols_per_row)]

for row in rows:
    cols = st.columns(cols_per_row)
    for col, item in zip(cols, row):
        with col:
            price  = item["price"]
            pct    = item["pct"]
            pnl    = item["pnl_usd"]
            shares = item["shares"]
            is_up  = pct is not None and pct >= 0
            ticker = item["ticker"]

            if item["currency"] == "ARS":
                entry_fmt = fmt_ars(item["entry"])
                price_fmt = fmt_ars(price) if price else "—"
                badge     = "CEDEAR · ARS"
                badge_cls = "card-badge-ars"
            else:
                entry_fmt = fmt_usd(item["entry"])
                price_fmt = fmt_usd(price) if price else "—"
                badge     = "CEDEAR · USD"
                badge_cls = "card-badge-usd"

            card_cls  = "card-up"  if is_up else "card-down"
            price_cls = "price-up" if is_up else "price-down"
            pct_cls   = "pct-up"   if is_up else "pct-down"
            pnl_cls   = "pnl-up"   if (pnl is not None and pnl >= 0) else "pnl-down"
            arrow     = "▲" if is_up else "▼"
            pct_text  = (
                f"+{pct:.2f}%" if (pct is not None and is_up)
                else (f"{pct:.2f}%" if pct is not None else "—")
            )
            pnl_text = fmt_pnl(pnl)

            st.markdown(f"""
            <div class="card {card_cls}">
                <div style="display:flex; justify-content:space-between;
                            align-items:center; margin-bottom:12px;">
                    <span class="card-ticker">{ticker}</span>
                    <span class="{badge_cls}">{badge}</span>
                </div>
                <div style="display:flex; justify-content:space-between; margin-bottom:10px;">
                    <div>
                        <div class="price-label">Entrada</div>
                        <div class="price-entry">{entry_fmt}</div>
                    </div>
                    <div style="text-align:center">
                        <div class="price-label">Acciones</div>
                        <div class="price-entry">{shares:.4f}</div>
                    </div>
                    <div style="text-align:right">
                        <div class="price-label">Actual</div>
                        <div class="{price_cls}">{price_fmt}</div>
                    </div>
                </div>
                <div style="border-top:1px solid #21262d; padding-top:10px;
                            display:flex; justify-content:space-between; align-items:center;">
                    <div>
                        <div class="price-label">P&L USD</div>
                        <span class="{pnl_cls}">{pnl_text}</span>
                    </div>
                    <span class="{pct_cls}">{arrow} {pct_text}</span>
                </div>
            </div>
            """, unsafe_allow_html=True)

            # ── Botón cerrar ──
            if st.session_state.confirm_close.get(ticker):
                close_val = st.number_input(
                    f"Precio cierre {ticker}",
                    min_value=0.01,
                    value=float(price) if price else float(item["entry"]),
                    step=0.01,
                    key=f"input_{ticker}",
                    label_visibility="collapsed",
                )
                ca, cb = st.columns(2)
                with ca:
                    if st.button("✅ Confirmar", key=f"confirm_{ticker}",
                                 use_container_width=True):
                        do_close_position(ticker, close_val, ccl)
                        st.success(f"✅ {ticker} cerrada!")
                        st.rerun()
                with cb:
                    if st.button("❌ Cancelar", key=f"cancel_{ticker}",
                                 use_container_width=True):
                        st.session_state.confirm_close[ticker] = False
                        st.rerun()
            else:
                if st.button("🔒 Cerrar posición", key=f"close_{ticker}",
                             use_container_width=True):
                    st.session_state.confirm_close[ticker] = True
                    st.rerun()

st.divider()

# ── POSICIONES CERRADAS ───────────────────────────────────────────────────────
closed = st.session_state.closed_positions
st.markdown(
    f'<p class="section-title">🔒 Posiciones Cerradas ({len(closed)})</p>',
    unsafe_allow_html=True
)

if not closed:
    st.info("No hay posiciones cerradas aún.")
else:
    rows_c = [closed[i:i+cols_per_row] for i in range(0, len(closed), cols_per_row)]
    for row in rows_c:
        cols = st.columns(cols_per_row)
        for col, item in zip(cols, row):
            with col:
                pct     = item["pct"]
                pnl     = item["pnl_usd"]
                is_up   = pct >= 0
                arrow   = "▲" if is_up else "▼"
                pct_cls = "pct-closed-up"  if is_up else "pct-closed-down"
                pnl_cls = "pnl-up" if (pnl is not None and pnl >= 0) else "pnl-down"
                pct_text = f"+{pct:.2f}%" if is_up else f"{pct:.2f}%"
                pnl_text = fmt_pnl(pnl)

                if item["currency"] == "ARS":
                    entry_fmt = fmt_ars(item["entry"])
                    close_fmt = fmt_ars(item["close_price"])
                else:
                    entry_fmt = fmt_usd(item["entry"])
                    close_fmt = fmt_usd(item["close_price"])

                st.markdown(f"""
                <div class="card card-closed">
                    <div style="display:flex; justify-content:space-between;
                                align-items:center; margin-bottom:12px;">
                        <div>
                            <span class="card-ticker">{item['ticker']}</span>
                            <span class="closed-stamp">CERRADA</span>
                        </div>
                        <span class="card-badge-closed">{item['currency']}</span>
                    </div>
                    <div style="display:flex; justify-content:space-between; margin-bottom:10px;">
                        <div>
                            <div class="price-label">Entrada</div>
                            <div class="price-entry">{entry_fmt}</div>
                        </div>
                        <div style="text-align:right">
                            <div class="price-label">Cierre</div>
                            <div class="price-entry">{close_fmt}</div>
                        </div>
                    </div>
                    <div style="border-top:1px solid #21262d; padding-top:10px;
                                display:flex; justify-content:space-between; align-items:center;">
                        <div>
                            <div class="price-label">P&L USD</div>
                            <span class="{pnl_cls}">{pnl_text}</span>
                        </div>
                        <span class="{pct_cls}">{arrow} {pct_text}</span>
                    </div>
                    <div style="margin-top:8px;">
                        <span style="font-size:0.7rem; color:#8b949e;">
                            📅 {item.get('close_date','—')}
                        </span>
                    </div>
                </div>
                """, unsafe_allow_html=True)

    # Tabla cerradas
    st.markdown("#### Resumen posiciones cerradas")
    closed_table = []
    for r in closed:
        closed_table.append({
            "Ticker":       r["ticker"],
            "Entrada":      fmt_ars(r["entry"]) if r["currency"] == "ARS" else fmt_usd(r["entry"]),
            "Cierre":       fmt_ars(r["close_price"]) if r["currency"] == "ARS" else fmt_usd(r["close_price"]),
            "Resultado %":  f"+{r['pct']:.2f}%" if r["pct"] >= 0 else f"{r['pct']:.2f}%",
            "P&L USD":      fmt_pnl(r["pnl_usd"]),
            "Estado":       "🟢 Ganancia" if r["pct"] >= 0 else "🔴 Pérdida",
            "Fecha Cierre": r.get("close_date", "—"),
        })
    st.dataframe(pd.DataFrame(closed_table), use_container_width=True, hide_index=True)

st.divider()

# ── TABLA ACTIVAS ─────────────────────────────────────────────────────────────
st.markdown("### Tabla — Posiciones Activas")
table_data = []
for r in results:
    table_data.append({
        "Ticker":    r["ticker"],
        "CEDEARs":   r["cedears"],
        "Acciones":  f"{r['shares']:.4f}",
        "Entrada":   fmt_ars(r["entry"]) if r["currency"] == "ARS" else fmt_usd(r["entry"]),
        "Actual":    (fmt_ars(r["price"]) if r["currency"] == "ARS"
                      else fmt_usd(r["price"])) if r["price"] else "—",
        "Var %":     (f"+{r['pct']:.2f}%" if r["pct"] >= 0
                      else f"{r['pct']:.2f}%") if r["pct"] is not None else "—",
        "P&L USD":   fmt_pnl(r["pnl_usd"]),
        "Invertido": f"${r['invested']:,.0f}" if r["invested"] else "—",
        "Estado":    ("🟢 Ganancia" if r["pct"] >= 0
                      else "🔴 Pérdida") if r["pct"] is not None else "⚪ Sin datos",
    })
st.dataframe(pd.DataFrame(table_data), use_container_width=True, hide_index=True)

st.divider()
st.markdown(
    '<p style="text-align:center; color:#484f58; font-size:0.75rem;">'
    'Precios vía Yahoo Finance · CCL vía dolarapi.com · Cache 5 min'
    '</p>',
    unsafe_allow_html=True
)
