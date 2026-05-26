import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime
import requests
import json

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
    .price-entry { font-size: 1rem; font-weight: 600; color: #e0e0e0; }
    .price-up    { font-size: 1rem; font-weight: 600; color: #3fb950; }
    .price-down  { font-size: 1rem; font-weight: 600; color: #f85149; }
    .pct-up      { font-size: 1.4rem; font-weight: 700; color: #3fb950; }
    .pct-down    { font-size: 1.4rem; font-weight: 700; color: #f85149; }
    .pct-closed-up   { font-size: 1.4rem; font-weight: 700; color: #3fb950; opacity: 0.75; }
    .pct-closed-down { font-size: 1.4rem; font-weight: 700; color: #f85149; opacity: 0.75; }
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

# ── CARTERA ACTIVA ────────────────────────────────────────────────────────────
PORTFOLIO = [
    {"ticker": "NU",   "entry": 14.75,   "currency": "USD", "yTicker": "NU"},
    {"ticker": "MELI", "entry": 1677.38, "currency": "USD", "yTicker": "MELI"},
    {"ticker": "MSFT", "entry": 405.00,  "currency": "USD", "yTicker": "MSFT"},
    {"ticker": "V",    "entry": 303.90,  "currency": "USD", "yTicker": "V"},
    {"ticker": "UL",   "entry": 28800,   "currency": "ARS", "yTicker": "UL.BA"},
    {"ticker": "JNJ",  "entry": 238.56,  "currency": "USD", "yTicker": "JNJ"},
    {"ticker": "VST",  "entry": 146.67,  "currency": "USD", "yTicker": "VST"},
    {"ticker": "PLTR", "entry": 135.34,  "currency": "USD", "yTicker": "PLTR"},
    {"ticker": "MCD",  "entry": 278.79,  "currency": "USD", "yTicker": "MCD"},
    {"ticker": "MDT",  "entry": 77.88,   "currency": "USD", "yTicker": "MDT"},
    {"ticker": "MMM",  "entry": 153.54,  "currency": "USD", "yTicker": "MMM"},
    {"ticker": "META", "entry": 609.19,  "currency": "USD", "yTicker": "META"},
    {"ticker": "UBER", "entry": 70.44,   "currency": "USD", "yTicker": "UBER"},
]

# ── POSICIONES CERRADAS INICIALES (VIST ya cerrada) ───────────────────────────
CLOSED_INITIAL = [
    {
        "ticker":      "VIST",
        "entry":       69.45,
        "close_price": 78.15,
        "currency":    "USD",
        "pct":         round(((78.15 - 69.45) / 69.45) * 100, 2),
        "close_date":  "Manual",
    }
]

# ── SESSION STATE ─────────────────────────────────────────────────────────────
if "closed_positions" not in st.session_state:
    st.session_state.closed_positions = CLOSED_INITIAL.copy()

if "active_portfolio" not in st.session_state:
    st.session_state.active_portfolio = PORTFOLIO.copy()

if "confirm_close" not in st.session_state:
    st.session_state.confirm_close = {}   # {ticker: True/False}

if "close_prices" not in st.session_state:
    st.session_state.close_prices = {}    # {ticker: precio_ingresado}

# ── FUNCIONES ─────────────────────────────────────────────────────────────────
@st.cache_data(ttl=300)
def get_ccl():
    try:
        url = "https://dolarito.ar/api/frontend/cotizaciones"
        headers = {"User-Agent": "Mozilla/5.0", "Accept": "application/json"}
        res = requests.get(url, headers=headers, timeout=10)
        data = res.json()
        for item in data:
            nombre = item.get("nombre", "").upper()
            if "CCL" in nombre:
                venta = item.get("venta") or item.get("valor") or item.get("price")
                if venta:
                    return round(float(str(venta).replace(",", ".")), 2)
    except:
        pass
    try:
        res2 = requests.get("https://dolarapi.com/v1/dolares/contadoconliqui", timeout=10)
        data2 = res2.json()
        venta = data2.get("venta")
        if venta:
            return round(float(venta), 2)
    except:
        pass
    return None

@st.cache_data(ttl=300)
def get_price(yticker):
    try:
        t = yf.Ticker(yticker)
        price = t.fast_info.last_price
        return round(float(price), 2) if price else None
    except:
        return None

def fmt_usd(n):
    return f"${n:,.2f}"

def fmt_ars(n):
    return f"${n:,.0f}"

def do_close_position(ticker, close_price):
    """Mueve una posición de activa a cerrada."""
    item = next((x for x in st.session_state.active_portfolio if x["ticker"] == ticker), None)
    if not item:
        return
    pct = round(((close_price - item["entry"]) / item["entry"]) * 100, 2)
    st.session_state.closed_positions.append({
        "ticker":      ticker,
        "entry":       item["entry"],
        "close_price": close_price,
        "currency":    item["currency"],
        "pct":         pct,
        "close_date":  datetime.now().strftime("%d/%m/%Y %H:%M"),
    })
    st.session_state.active_portfolio = [
        x for x in st.session_state.active_portfolio if x["ticker"] != ticker
    ]
    # Limpiar estado del modal
    st.session_state.confirm_close.pop(ticker, None)
    st.session_state.close_prices.pop(ticker, None)
    get_price.clear()

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
with st.spinner("Cargando precios..."):
    ccl = get_ccl()
    results = []
    for item in st.session_state.active_portfolio:
        price = get_price(item["yTicker"])
        pct   = round(((price - item["entry"]) / item["entry"]) * 100, 2) if price else None
        results.append({**item, "price": price, "pct": pct})

# ── SUMMARY ───────────────────────────────────────────────────────────────────
valid = [r for r in results if r["pct"] is not None]
ups   = [r for r in valid if r["pct"] >= 0]
downs = [r for r in valid if r["pct"] < 0]
best  = max(valid, key=lambda x: x["pct"]) if valid else None
worst = min(valid, key=lambda x: x["pct"]) if valid else None
ccl_text = f"${ccl:,.2f}" if ccl else "N/D"

c1, c2, c3, c4, c5, c6 = st.columns(6)
with c1: st.metric("💱 Dólar CCL", ccl_text, help="Fuente: dolarapi.com")
with c2: st.metric("📁 Posiciones activas", len(st.session_state.active_portfolio))
with c3: st.metric("🟢 En Ganancia", len(ups))
with c4: st.metric("🔴 En Pérdida", len(downs))
with c5:
    if best:  st.metric("🏆 Mejor", best["ticker"],  f"+{best['pct']:.1f}%")
with c6:
    if worst: st.metric("📉 Peor",  worst["ticker"], f"{worst['pct']:.1f}%")

st.divider()

# ── GRÁFICO ───────────────────────────────────────────────────────────────────
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
        margin=dict(l=10, r=60, t=30, b=10),
        xaxis=dict(
            showgrid=True, gridcolor="#21262d",
            zeroline=True, zerolinecolor="#58a6ff",
            zerolinewidth=2, ticksuffix="%",
        ),
        yaxis=dict(showgrid=False),
        title=dict(text="Variación por posición (%)",
                   font=dict(color="#8b949e", size=13), x=0)
    )
    st.plotly_chart(fig, use_container_width=True)

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
                badge     = "ADR · USD"
                badge_cls = "card-badge-usd"

            card_cls  = "card-up"  if is_up else "card-down"
            price_cls = "price-up" if is_up else "price-down"
            pct_cls   = "pct-up"   if is_up else "pct-down"
            arrow     = "▲" if is_up else "▼"
            pct_text  = (
                f"+{pct:.2f}%" if (pct is not None and is_up)
                else (f"{pct:.2f}%" if pct is not None else "—")
            )

            # ── Card HTML ──
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
                    <div style="text-align:right">
                        <div class="price-label">Actual</div>
                        <div class="{price_cls}">{price_fmt}</div>
                    </div>
                </div>
                <div style="border-top:1px solid #21262d; padding-top:10px;
                            display:flex; justify-content:space-between; align-items:center;">
                    <span style="font-size:0.7rem; color:#8b949e; text-transform:uppercase;">
                        Variación
                    </span>
                    <span class="{pct_cls}">{arrow} {pct_text}</span>
                </div>
            </div>
            """, unsafe_allow_html=True)

            # ── Botón cerrar posición ──
            if st.session_state.confirm_close.get(ticker):
                # Formulario de cierre
                close_val = st.number_input(
                    f"Precio de cierre {ticker}",
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
                        do_close_position(ticker, close_val)
                        st.success(f"{ticker} cerrada!")
                        st.rerun()
                with cb:
                    if st.button("❌ Cancelar", key=f"cancel_{ticker}",
                                 use_container_width=True):
                        st.session_state.confirm_close[ticker] = False
                        st.rerun()
            else:
                if st.button(
                    "🔒 Cerrar posición",
                    key=f"close_{ticker}",
                    use_container_width=True
                ):
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
    # Cards de cerradas
    rows_c = [closed[i:i+cols_per_row] for i in range(0, len(closed), cols_per_row)]
    for row in rows_c:
        cols = st.columns(cols_per_row)
        for col, item in zip(cols, row):
            with col:
                pct    = item["pct"]
                is_up  = pct >= 0
                arrow  = "▲" if is_up else "▼"
                pct_cls = "pct-closed-up" if is_up else "pct-closed-down"
                pct_text = f"+{pct:.2f}%" if is_up else f"{pct:.2f}%"

                if item["currency"] == "ARS":
                    entry_fmt = fmt_ars(item["entry"])
                    close_fmt = fmt_ars(item["close_price"])
                else:
                    entry_fmt = fmt_usd(item["entry"])
                    close_fmt = fmt_usd(item["close_price"])

                close_date = item.get("close_date", "—")

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
                        <span style="font-size:0.7rem; color:#8b949e;">
                            📅 {close_date}
                        </span>
                        <span class="{pct_cls}">{arrow} {pct_text}</span>
                    </div>
                </div>
                """, unsafe_allow_html=True)

    # Tabla resumen cerradas
    st.markdown("#### Resumen posiciones cerradas")
    closed_table = []
    for r in closed:
        closed_table.append({
            "Ticker":        r["ticker"],
            "Entrada":       fmt_ars(r["entry"]) if r["currency"] == "ARS" else fmt_usd(r["entry"]),
            "Cierre":        fmt_ars(r["close_price"]) if r["currency"] == "ARS" else fmt_usd(r["close_price"]),
            "Resultado":     f"+{r['pct']:.2f}%" if r["pct"] >= 0 else f"{r['pct']:.2f}%",
            "Estado":        "🟢 Ganancia" if r["pct"] >= 0 else "🔴 Pérdida",
            "Fecha Cierre":  r.get("close_date", "—"),
        })
    st.dataframe(pd.DataFrame(closed_table), use_container_width=True, hide_index=True)

# ── TABLA ACTIVAS ─────────────────────────────────────────────────────────────
st.divider()
st.markdown("### Tabla — Posiciones Activas")
table_data = []
for r in results:
    table_data.append({
        "Ticker":         r["ticker"],
        "Tipo":           r["currency"],
        "Entrada":        fmt_ars(r["entry"]) if r["currency"] == "ARS" else fmt_usd(r["entry"]),
        "Actual":         (fmt_ars(r["price"]) if r["currency"] == "ARS"
                           else fmt_usd(r["price"])) if r["price"] else "—",
        "Variación %":    (f"+{r['pct']:.2f}%" if r["pct"] >= 0
                           else f"{r['pct']:.2f}%") if r["pct"] is not None else "—",
        "Estado":         ("🟢 Ganancia" if r["pct"] >= 0
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
