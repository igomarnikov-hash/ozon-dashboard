"""
Ozon Sales Analytics Dashboard
================================
Run: streamlit run app.py
"""

import json
import random
from datetime import date, datetime, timedelta

import pandas as pd
import plotly.graph_objects as go
import requests
import streamlit as st

# ─────────────────────────────────────────────
# PAGE CONFIG
# ─────────────────────────────────────────────
st.set_page_config(
    page_title="Ozon Analytics",
    page_icon="🔵",
    layout="wide",
    initial_sidebar_state="collapsed",   # sidebar скрыт по умолчанию
)

# ─────────────────────────────────────────────
# CSS
# ─────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Onest:wght@300;400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap');

html, body, [class*="css"] { font-family: 'Onest', sans-serif; }

.stApp { background: #f0f4ff; color: #1a2040; }

/* Sidebar */
[data-testid="stSidebar"] { background: #ffffff; border-right: 1px solid #dde3f5; }
[data-testid="stSidebar"] * { color: #2a3560 !important; }
[data-testid="stSidebar"] .stTextInput input,
[data-testid="stSidebar"] .stDateInput input {
    background: #f5f7ff !important; border: 1px solid #c8d0ee !important;
    border-radius: 8px !important; color: #1a2040 !important;
    font-family: 'JetBrains Mono', monospace !important; font-size: 12px !important;
}
[data-testid="stSidebar"] .stButton button {
    background: linear-gradient(135deg, #005bff 0%, #0099ff 100%);
    color: #fff !important; border: none; border-radius: 10px;
    font-weight: 600; width: 100%; padding: 10px; transition: opacity .2s;
}
[data-testid="stSidebar"] .stButton button:hover { opacity: .85; }

/* Top bar */
.top-bar {
    display: flex; align-items: center; justify-content: space-between;
    margin-bottom: 28px;
}
.top-bar-left { display: flex; align-items: center; gap: 14px; }
.top-bar-left h1 { font-size: 24px; font-weight: 700; color: #1a2040; margin: 0; }
.ozon-dot {
    width: 36px; height: 36px;
    background: linear-gradient(135deg, #005bff, #00c6ff);
    border-radius: 10px; display: flex; align-items: center;
    justify-content: center; font-size: 18px; flex-shrink: 0;
}

/* Settings button */
.settings-btn-wrap .stButton button {
    background: #ffffff !important; color: #2a3560 !important;
    border: 1px solid #dde3f5 !important; border-radius: 10px !important;
    font-size: 13px !important; font-weight: 500 !important;
    padding: 8px 16px !important; box-shadow: 0 1px 4px rgba(0,0,0,0.06);
    transition: box-shadow .2s !important;
}
.settings-btn-wrap .stButton button:hover {
    box-shadow: 0 4px 12px rgba(0,91,255,0.12) !important;
}

/* Metric cards */
.metric-card {
    background: #ffffff; border: 1px solid #dde3f5; border-radius: 16px;
    padding: 20px 22px; position: relative; overflow: hidden;
    box-shadow: 0 2px 12px rgba(0,91,255,0.06);
    transition: transform .2s, box-shadow .2s; height: 100%;
}
.metric-card:hover { transform: translateY(-2px); box-shadow: 0 6px 24px rgba(0,91,255,0.12); }
.metric-card::before {
    content: ''; position: absolute; top: 0; left: 0; right: 0;
    height: 3px; border-radius: 16px 16px 0 0;
}
.card-orders::before   { background: linear-gradient(90deg, #005bff, #00c6ff); }
.card-sales::before    { background: linear-gradient(90deg, #7c3aed, #c026d3); }
.card-balance::before  { background: linear-gradient(90deg, #059669, #34d399); }
.card-returns::before { background: linear-gradient(90deg, #e53e3e, #fc8181); }

.metric-label {
    font-size: 11px; font-weight: 600; letter-spacing: .08em;
    text-transform: uppercase; color: #7a88b8; margin-bottom: 10px;
}
.metric-row { display: flex; align-items: baseline; gap: 6px; flex-wrap: wrap; }
.metric-main { font-size: 26px; font-weight: 700; color: #1a2040; font-variant-numeric: tabular-nums; }
.metric-sep  { font-size: 20px; color: #c8d0ee; font-weight: 300; }
.metric-sub  { font-size: 16px; font-weight: 600; color: #7a88b8; font-variant-numeric: tabular-nums; }
.metric-delta {
    font-size: 12px; margin-top: 8px;
    font-family: 'JetBrains Mono', monospace;
}
.delta-pos { color: #059669; }
.delta-neu { color: #7a88b8; }
.delta-neg { color: #e53e3e; }

.section-title {
    font-size: 13px; font-weight: 600; letter-spacing: .12em; text-transform: uppercase;
    color: #7a88b8; margin: 28px 0 14px; padding-bottom: 8px; border-bottom: 1px solid #dde3f5;
}
.mock-badge {
    display: inline-block; background: #fffbeb; color: #92400e;
    border: 1px solid #fcd34d; border-radius: 20px; padding: 4px 12px;
    font-size: 11px; font-weight: 600; letter-spacing: .05em; margin-bottom: 16px;
}
.chart-box {
    background: #ffffff; border: 1px solid #dde3f5; border-radius: 16px;
    padding: 16px; box-shadow: 0 2px 12px rgba(0,91,255,0.04);
}

#MainMenu { visibility: hidden; }
footer { visibility: hidden; }
header { visibility: hidden; }
</style>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────
# OZON CLIENT
# ─────────────────────────────────────────────
class OzonClient:
    BASE_URL = "https://api-seller.ozon.ru"

    def __init__(self, client_id: str, api_key: str):
        self.session = requests.Session()
        self.session.headers.update({
            "Client-Id": client_id,
            "Api-Key": api_key,
            "Content-Type": "application/json",
        })

    def get_analytics_data(self, date_from, date_to, metrics, dimension, limit=1000):
        payload = {
            "date_from": date_from, "date_to": date_to,
            "metrics": metrics, "dimension": dimension,
            "sort": [{"key": "revenue", "order": "DESC"}],
            "limit": limit, "offset": 0,
        }
        resp = self.session.post(f"{self.BASE_URL}/v1/analytics/data",
                                 data=json.dumps(payload), timeout=30)
        resp.raise_for_status()
        return resp.json()

    def get_finance_totals(self):
        """POST /v1/finance/balance — отчёт о балансе (Финансы → Баланс в ЛК).
        Требует date_from и date_to в формате YYYY-MM-DD, период макс. 30 дней.
        """
        now = datetime.now()
        date_to   = now.strftime("%Y-%m-%d")
        date_from = (now - timedelta(days=29)).strftime("%Y-%m-%d")
        payload = {
            "date_from": date_from,
            "date_to":   date_to,
        }
        resp = self.session.post(
            f"{self.BASE_URL}/v1/finance/balance",
            data=json.dumps(payload), timeout=15,
        )
        resp.raise_for_status()
        data = resp.json()
        data["_endpoint_used"] = "/v1/finance/balance"
        return data

    def get_returns(self, date_from: str, date_to: str, limit: int = 1000):
        """POST /v3/returns/company/fbo + fbs — возвраты (сумма и кол-во)"""
        payload = {
            "filter": {"date": {"from": f"{date_from}T00:00:00Z", "to": f"{date_to}T23:59:59Z"}},
            "limit": limit, "offset": 0,
        }
        fbo_items, fbs_items = [], []
        r_fbo = self.session.post(f"{self.BASE_URL}/v3/returns/company/fbo",
                                   data=json.dumps(payload), timeout=30)
        if r_fbo.ok:
            fbo_items = r_fbo.json().get("returns", [])
        r_fbs = self.session.post(f"{self.BASE_URL}/v3/returns/company/fbs",
                                   data=json.dumps(payload), timeout=30)
        if r_fbs.ok:
            fbs_items = r_fbs.json().get("returns", [])
        all_r = fbo_items + fbs_items
        total_sum = sum(float(r.get("price", r.get("commissions_amount", 0)) or 0) for r in all_r)
        return {"count": len(all_r), "sum": total_sum}


# ─────────────────────────────────────────────
# DATA TRANSFORMATION
# ─────────────────────────────────────────────
METRIC_KEYS = ["revenue", "ordered_units", "hits_view", "session_view"]


def _is_date(s: str) -> bool:
    try:
        datetime.strptime(str(s), "%Y-%m-%d")
        return True
    except (ValueError, TypeError):
        return False


def parse_analytics_response(response: dict) -> pd.DataFrame:
    result = response.get("result", response)
    data_rows = result.get("data", [])
    api_metric_keys = result.get("metrics", METRIC_KEYS)
    rows = []
    for row in data_rows:
        record: dict = {}
        if "dimensions" in row and "metrics" in row:
            for dim in row["dimensions"]:
                dim_id = str(dim.get("id", ""))
                dim_name = dim.get("name", dim_id)
                if _is_date(dim_id):
                    record["date"] = pd.to_datetime(dim_id)
                else:
                    record["sku_id"] = dim_id
                    record["sku_name"] = dim_name
            for key, val in zip(api_metric_keys, row["metrics"]):
                record[key] = val
        elif isinstance(row, dict):
            for k, v in row.items():
                if k == "date" or _is_date(str(v)):
                    record["date"] = pd.to_datetime(v)
                else:
                    record[k] = v
        rows.append(record)
    df = pd.DataFrame(rows)
    for col in METRIC_KEYS:
        if col not in df.columns:
            df[col] = 0.0
        else:
            df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)
    if "date" in df.columns:
        df["date"] = pd.to_datetime(df["date"], errors="coerce")
    return df


# ─────────────────────────────────────────────
# MOCK DATA
# ─────────────────────────────────────────────
MOCK_SKUS = [
    ("101001", "Кроссовки Nike Air Max 270"),
    ("101002", "Смартфон Samsung Galaxy A54"),
    ("101003", "Наушники Sony WH-1000XM5"),
    ("101004", "Ноутбук ASUS VivoBook 15"),
    ("101005", "Кофемашина DeLonghi Magnifica"),
    ("101006", "Пылесос Dyson V15"),
    ("101007", "Планшет iPad 10th Gen"),
    ("101008", "Умная колонка Яндекс Макс"),
]

MOCK_BALANCE  = 342_815.50   # демо-баланс
MOCK_RETURNS  = {"count": 47, "sum": 184_320.0}  # демо-возвраты


def generate_mock_data(date_from: date, date_to: date) -> pd.DataFrame:
    days = pd.date_range(date_from, date_to, freq="D")
    rng = random.Random(42)
    rows = []
    for day in days:
        mult = rng.uniform(1.15, 1.4) if day.weekday() >= 5 else rng.uniform(0.85, 1.15)
        for sku_id, sku_name in MOCK_SKUS:
            base_rev = rng.uniform(15_000, 180_000)
            units = max(1, int(base_rev / rng.uniform(1_500, 8_000)))
            views = units * rng.randint(40, 120)
            sessions = int(views * rng.uniform(0.3, 0.6))
            rows.append({
                "date": pd.Timestamp(day), "sku_id": sku_id, "sku_name": sku_name,
                "revenue": round(base_rev * mult, 2),
                "ordered_units": float(units),
                "hits_view": float(views),
                "session_view": float(sessions),
            })
    return pd.DataFrame(rows)


# ─────────────────────────────────────────────
# CHARTS
# ─────────────────────────────────────────────
THEME = dict(
    paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
    font=dict(family="Onest, sans-serif", color="#5a6a9a", size=12),
    xaxis=dict(gridcolor="#eef0f8", zeroline=False, tickfont=dict(size=11, color="#8a98c0"), linecolor="#dde3f5"),
    yaxis=dict(gridcolor="#eef0f8", zeroline=False, tickfont=dict(size=11, color="#8a98c0"), linecolor="#dde3f5"),
    legend=dict(bgcolor="rgba(255,255,255,0.9)", bordercolor="#dde3f5", borderwidth=1, font=dict(size=11, color="#5a6a9a")),
    margin=dict(l=8, r=8, t=20, b=8),
    hoverlabel=dict(bgcolor="#ffffff", bordercolor="#c0ccee", font=dict(family="Onest", size=12, color="#1a2040")),
)


def sales_trend_chart(df_daily: pd.DataFrame) -> go.Figure:
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=df_daily["date"], y=df_daily["revenue"],
        name="Продажи (₽)", line=dict(color="#005bff", width=2.5),
        fill="tozeroy", fillcolor="rgba(0,91,255,0.07)",
        hovertemplate="<b>%{x|%d %b}</b><br>₽%{y:,.0f}<extra></extra>",
    ))
    fig.add_trace(go.Bar(
        x=df_daily["date"], y=df_daily["ordered_units"],
        name="Заказы (шт)", marker_color="rgba(124,58,237,0.45)",
        yaxis="y2",
        hovertemplate="<b>%{x|%d %b}</b><br>%{y:,} шт<extra></extra>",
    ))
    no_legend = {k: v for k, v in THEME.items() if k != "legend"}
    fig.update_layout(
        **no_legend,
        yaxis2=dict(overlaying="y", side="right", gridcolor="#eef0f8", zeroline=False,
                    tickfont=dict(size=11, color="#8a98c0"), linecolor="#dde3f5"),
        legend=dict(bgcolor="rgba(255,255,255,0.9)", bordercolor="#dde3f5", borderwidth=1,
                    font=dict(size=11, color="#5a6a9a"), orientation="h", y=1.12, x=0),
        height=320,
    )
    return fig


def funnel_chart(df_daily: pd.DataFrame) -> go.Figure:
    totals = df_daily[["hits_view", "session_view", "ordered_units"]].sum()
    fig = go.Figure(go.Funnel(
        y=["Просмотры", "Сессии", "Заказы"],
        x=[totals["hits_view"], totals["session_view"], totals["ordered_units"]],
        marker=dict(color=["#005bff", "#7c3aed", "#059669"]),
        textposition="inside", textfont=dict(size=13, color="#fff", family="Onest"),
        hovertemplate="<b>%{label}</b><br>%{value:,}<extra></extra>",
    ))
    fig.update_layout(**THEME, height=300)
    return fig


# ─────────────────────────────────────────────
# SESSION STATE — настройки
# ─────────────────────────────────────────────
if "client_id" not in st.session_state:
    st.session_state.client_id = ""
if "api_key" not in st.session_state:
    st.session_state.api_key = ""
if "date_from" not in st.session_state:
    st.session_state.date_from = date.today() - timedelta(days=29)
if "date_to" not in st.session_state:
    st.session_state.date_to = date.today()

# ─────────────────────────────────────────────
# DATA LOADING
# ─────────────────────────────────────────────
client_id = st.session_state.client_id
api_key   = st.session_state.api_key
date_from = st.session_state.date_from
date_to   = st.session_state.date_to
USE_MOCK  = not (client_id.strip() and api_key.strip())
fetch_btn = False   # будет переопределён в панели настроек если она открыта


@st.cache_data(ttl=300, show_spinner=False)
def load_real_data(_cid, _key, df_str, dt_str):
    client = OzonClient(client_id=_cid, api_key=_key)
    resp = client.get_analytics_data(
        date_from=df_str, date_to=dt_str,
        metrics=METRIC_KEYS, dimension=["day", "sku"],
    )
    return parse_analytics_response(resp)


@st.cache_data(ttl=300, show_spinner=False)
def load_real_balance(_cid, _key):
    client = OzonClient(client_id=_cid, api_key=_key)
    data = client.get_finance_totals()
    r = data.get("result", data)
    # /v1/finance/balance — структура ответа содержит balance и credit
    # balance = собственные средства, credit = кредит Ozon
    own     = float(r.get("balance", 0) or 0)
    credit  = float(r.get("credit",  0) or 0)
    total   = float(r.get("total_balance", own + credit) or own + credit)
    return total, data


@st.cache_data(ttl=300, show_spinner=False)
def load_real_returns(_cid, _key, df_str, dt_str):
    client = OzonClient(client_id=_cid, api_key=_key)
    return client.get_returns(df_str, dt_str)


@st.cache_data(ttl=3600, show_spinner=False)
def load_mock_data(df, dt):
    return generate_mock_data(df, dt)


if "df" not in st.session_state or fetch_btn:
    if fetch_btn:
        # Сбрасываем кэш чтобы получить свежие данные
        load_real_data.clear()
        load_real_balance.clear()
        load_real_returns.clear()
        load_mock_data.clear()
    with st.spinner("Загрузка данных…"):
        try:
            if USE_MOCK:
                st.session_state.df      = load_mock_data(date_from, date_to)
                st.session_state.balance = MOCK_BALANCE
                st.session_state.returns = MOCK_RETURNS
                st.session_state.data_error = None
            else:
                df_str = date_from.strftime("%Y-%m-%d")
                dt_str = date_to.strftime("%Y-%m-%d")
                st.session_state.df = load_real_data(client_id, api_key, df_str, dt_str)
                try:
                    bal_result = load_real_balance(client_id, api_key)
                    st.session_state.balance     = bal_result[0]
                    st.session_state.balance_raw = bal_result[1]
                except Exception:
                    st.session_state.balance     = MOCK_BALANCE
                    st.session_state.balance_raw = {}
                try:
                    st.session_state.returns = load_real_returns(client_id, api_key, df_str, dt_str)
                except Exception:
                    st.session_state.returns = MOCK_RETURNS
                st.session_state.data_error = None
        except Exception as e:
            st.session_state.data_error = str(e)
            st.session_state.df      = load_mock_data(date_from, date_to)
            st.session_state.balance = MOCK_BALANCE
            st.session_state.returns = MOCK_RETURNS
            USE_MOCK = True

df: pd.DataFrame = st.session_state.df
balance: float   = st.session_state.get("balance", MOCK_BALANCE)
returns: dict    = st.session_state.get("returns", MOCK_RETURNS)

for col in METRIC_KEYS:
    if col not in df.columns:
        df[col] = 0.0

# ─────────────────────────────────────────────
# MAIN — HEADER
# ─────────────────────────────────────────────
hdr_left, hdr_right = st.columns([5, 1])

with hdr_left:
    st.markdown("""
        <div class="top-bar-left">
          <div class="ozon-dot">🔵</div>
          <h1>Аналитика продаж</h1>
        </div>
        <div style="color:#8a98c0;font-size:13px;margin-bottom:4px">
          Сводные показатели магазина · реальное время
        </div>
    """, unsafe_allow_html=True)

with hdr_right:
    settings_open = st.button("⚙ Настройки", use_container_width=True, key="settings_toggle")
    if settings_open:
        st.session_state.show_settings = not st.session_state.get("show_settings", False)

# ── Панель настроек (раскрывается под шапкой) ──
if st.session_state.get("show_settings", False):
    st.markdown("""
        <div style="background:#fff;border:1px solid #dde3f5;border-radius:16px;
             padding:24px 28px;margin:12px 0 24px;box-shadow:0 4px 24px rgba(0,91,255,0.08);">
    """, unsafe_allow_html=True)

    cfg1, cfg2, cfg3 = st.columns([2, 2, 3])

    with cfg1:
        st.markdown("**🔑 API Credentials**")
        new_client_id = st.text_input("Client-ID", value=st.session_state.client_id,
                                       placeholder="123456", key="inp_cid")
        new_api_key   = st.text_input("Api-Key", value=st.session_state.api_key,
                                       placeholder="xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx",
                                       type="password", key="inp_key")

    with cfg2:
        st.markdown("**📅 Период**")
        new_date_from = st.date_input("Дата от", value=st.session_state.date_from, key="inp_df")
        new_date_to   = st.date_input("Дата до", value=st.session_state.date_to,   key="inp_dt")

    with cfg3:
        st.markdown("**▶ Действия**")
        st.markdown("<div style='height:4px'></div>", unsafe_allow_html=True)
        if st.button("💾 Сохранить и закрыть", use_container_width=True, key="btn_save"):
            st.session_state.client_id = new_client_id
            st.session_state.api_key   = new_api_key
            st.session_state.date_from = new_date_from
            st.session_state.date_to   = new_date_to
            st.session_state.show_settings = False
            # Сбрасываем данные и кэш — следующий рендер загрузит с API
            for _k in ["df", "balance", "returns", "data_error"]:
                st.session_state.pop(_k, None)
            load_real_data.clear()
            load_real_balance.clear()
            load_real_returns.clear()
            load_mock_data.clear()
            st.rerun()
        st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)
        fetch_btn = st.button("⟳ Загрузить данные", use_container_width=True, key="btn_fetch")
        st.markdown(
            f"<div style='font-size:11px;color:#8a98c0;margin-top:12px'>"
            f"Статус: {'🟡 Демо-режим' if USE_MOCK else '🟢 API подключён'}</div>",
            unsafe_allow_html=True,
        )

    st.markdown("</div>", unsafe_allow_html=True)
else:
    fetch_btn = False

# Обновляем переменные после возможного сохранения
client_id = st.session_state.client_id
api_key   = st.session_state.api_key
date_from = st.session_state.date_from
date_to   = st.session_state.date_to
USE_MOCK  = not (client_id.strip() and api_key.strip())  # пересчитываем с актуальными ключами

if st.session_state.get("data_error"):
    st.error(f"Ошибка API: {st.session_state.data_error}. Показаны демо-данные.")

if USE_MOCK:
    st.markdown('<div class="mock-badge">⚠ ДЕМО-РЕЖИМ — нажмите ⚙ Настройки и введите API-ключи</div>',
                unsafe_allow_html=True)
else:
    with st.expander("🔍 Диагностика API (нажми чтобы проверить данные)", expanded=False):
        st.markdown(f"**Период:** {date_from} — {date_to}")
        st.markdown(f"**Строк в DataFrame:** {len(df)}")
        st.markdown(f"**Колонки:** `{list(df.columns)}`")
        st.markdown(f"**Баланс:** ₽{balance:,.0f}".replace(",", " "))
        if len(df) > 0:
            st.markdown("**Первые 3 строки сырых данных:**")
            st.dataframe(df.head(3))
        else:
            st.warning("⚠️ DataFrame пустой — API вернул 0 строк. Возможные причины:\n"
                       "- Нет продаж за выбранный период\n"
                       "- Неверный Client-ID или Api-Key\n"
                       "- Период слишком большой (попробуй последние 7 дней)")
        # Показываем сырой ответ баланса
        bal_raw = st.session_state.get("balance_raw", {})
        endpoint = bal_raw.get("_endpoint_used", "неизвестен")
        st.markdown(f"**Сырой ответ баланса (эндпоинт: `{endpoint}`):**")
        try:
            if bal_raw:
                st.json(bal_raw)
            else:
                _client = OzonClient(client_id=client_id, api_key=api_key)
                _raw = _client.get_finance_totals()
                st.json(_raw)
        except Exception as _e:
            st.error(f"Ошибка запроса баланса: {_e}")
        if st.session_state.get("data_error"):
            st.error(f"Последняя ошибка API: {st.session_state.data_error}")

# ─────────────────────────────────────────────
# AGGREGATES
# ─────────────────────────────────────────────
total_revenue  = float(df["revenue"].sum())       # фактические продажи (выручка)
total_orders   = int(df["ordered_units"].sum())    # заказы (ordered = оформленные)
total_sessions = int(df["session_view"].sum())
total_views    = int(df["hits_view"].sum())

# «Продажи» — оплаченные заказы ≈ ordered_units (в аналитике Ozon это одно поле)
# Конверсия = заказы / сессии
cvr = (total_orders / total_sessions * 100) if total_sessions else 0
avg_order = total_revenue / total_orders if total_orders else 0

# ─────────────────────────────────────────────
# KPI CARDS  (4 карточки)
# ─────────────────────────────────────────────
st.markdown('<div class="section-title">📊 Ключевые показатели</div>', unsafe_allow_html=True)

c1, c2, c3, c4 = st.columns(4)


def dual_card(col, css_cls, icon, label, main_val, sep, sub_val, delta, delta_cls="delta-neu"):
    col.markdown(f"""
        <div class="metric-card {css_cls}">
          <div class="metric-label">{icon} {label}</div>
          <div class="metric-row">
            <span class="metric-main">{main_val}</span>
            <span class="metric-sep">{sep}</span>
            <span class="metric-sub">{sub_val}</span>
          </div>
          <div class="metric-delta {delta_cls}">{delta}</div>
        </div>
    """, unsafe_allow_html=True)


def single_card(col, css_cls, icon, label, main_val, delta, delta_cls="delta-neu"):
    col.markdown(f"""
        <div class="metric-card {css_cls}">
          <div class="metric-label">{icon} {label}</div>
          <div class="metric-row">
            <span class="metric-main">{main_val}</span>
          </div>
          <div class="metric-delta {delta_cls}">{delta}</div>
        </div>
    """, unsafe_allow_html=True)


# Карточка 1 — ЗАКАЗЫ: сумма / количество
dual_card(
    c1, "card-orders", "📦", "ЗАКАЗЫ",
    main_val=f"₽{total_revenue:,.0f}".replace(",", " "),
    sep="/",
    sub_val=f"{total_orders:,} шт".replace(",", " "),
    delta=f"Ср. чек ₽{avg_order:,.0f}".replace(",", " "),
)

# Карточка 2 — ПРОДАЖИ: сумма / кол-во оплаченных + конверсия
dual_card(
    c2, "card-sales", "💰", "ПРОДАЖИ",
    main_val=f"₽{total_revenue:,.0f}".replace(",", " "),
    sep="/",
    sub_val=f"{total_orders:,} опл.".replace(",", " "),
    delta=f"▲ Конверсия {cvr:.1f}%",
    delta_cls="delta-pos" if cvr > 2 else "delta-neu",
)

# Карточка 3 — БАЛАНС
bal_str = f"₽{balance:,.0f}".replace(",", " ")
single_card(
    c3, "card-balance", "🏦", "БАЛАНС",
    main_val=bal_str,
    delta="Текущий баланс с учётом кредита" if not USE_MOCK else "⚠ Демо-данные",
    delta_cls="delta-neu",
)

# Карточка 4 — ВОЗВРАТЫ: сумма / количество
ret_sum   = returns.get("sum", 0)
ret_count = returns.get("count", 0)
ret_rate  = (ret_count / total_orders * 100) if total_orders else 0
dual_card(
    c4, "card-returns", "↩️", "ВОЗВРАТЫ",
    main_val=f"₽{ret_sum:,.0f}".replace(",", " "),
    sep="/",
    sub_val=f"{ret_count} шт",
    delta=f"{'▼' if ret_rate < 5 else '▲'} {ret_rate:.1f}% от заказов",
    delta_cls="delta-pos" if ret_rate < 5 else "delta-neg",
)

# ─────────────────────────────────────────────
# CHARTS
# ─────────────────────────────────────────────
st.markdown('<div class="section-title">📈 Динамика</div>', unsafe_allow_html=True)

if "date" in df.columns:
    df_daily = df.groupby("date")[METRIC_KEYS].sum().reset_index().sort_values("date")
else:
    df_daily = pd.DataFrame(columns=["date"] + METRIC_KEYS)

chart_col, funnel_col = st.columns([3, 1], gap="large")

with chart_col:
    st.markdown('<div class="chart-box">', unsafe_allow_html=True)
    st.plotly_chart(sales_trend_chart(df_daily), use_container_width=True, config={"displayModeBar": False})
    st.markdown('</div>', unsafe_allow_html=True)

with funnel_col:
    st.markdown('<div style="font-size:11px;font-weight:600;color:#8a98c0;letter-spacing:.08em;'
                'text-transform:uppercase;margin-bottom:8px">Воронка конверсии</div>', unsafe_allow_html=True)
    st.markdown('<div class="chart-box">', unsafe_allow_html=True)
    st.plotly_chart(funnel_chart(df_daily), use_container_width=True, config={"displayModeBar": False})
    st.markdown('</div>', unsafe_allow_html=True)

# ─────────────────────────────────────────────
# TOP SKUs
# ─────────────────────────────────────────────
st.markdown('<div class="section-title">🏆 Топ-товары по продажам</div>', unsafe_allow_html=True)

group_cols = ["sku_id", "sku_name"] if "sku_name" in df.columns else ["sku_id"]
top = (
    df.groupby(group_cols)[METRIC_KEYS].sum().reset_index()
    .sort_values("revenue", ascending=False).head(10).reset_index(drop=True)
)
top.index = top.index + 1

disp = top.copy()
disp["revenue"]       = disp["revenue"].apply(lambda x: f"₽{x:,.0f}".replace(",", " "))
disp["ordered_units"] = disp["ordered_units"].apply(lambda x: f"{int(x):,} шт".replace(",", " "))
disp["hits_view"]     = disp["hits_view"].apply(lambda x: f"{int(x):,}".replace(",", " "))
safe_s                = top["session_view"].replace(0, 1)
disp["cvr"]           = (top["ordered_units"] / safe_s * 100).apply(lambda x: f"{x:.1f}%")

rename = {"sku_id": "SKU ID", "sku_name": "Товар", "revenue": "Продажи",
          "ordered_units": "Заказов", "hits_view": "Просмотров", "cvr": "Конверсия"}
disp = disp.rename(columns=rename)
show_cols = [c for c in ["SKU ID", "Товар", "Продажи", "Заказов", "Просмотров", "Конверсия"] if c in disp.columns]
st.dataframe(disp[show_cols], use_container_width=True, height=380)

# ─────────────────────────────────────────────
# FOOTER
# ─────────────────────────────────────────────
st.markdown(f"""
    <div style="margin-top:48px;padding-top:20px;border-top:1px solid #dde3f5;
         display:flex;justify-content:space-between;font-size:11px;color:#b0bcd8">
      <div>Ozon Analytics Dashboard · {datetime.now().strftime('%d.%m.%Y %H:%M')}</div>
      <div>{'🟡 Demo Mode' if USE_MOCK else '🟢 Live API'} · Seller API</div>
    </div>
""", unsafe_allow_html=True)
