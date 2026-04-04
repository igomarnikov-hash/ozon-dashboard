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
            "sort": [{"key": metrics[0], "order": "DESC"}],
            "limit": min(limit, 1000), "offset": 0,
        }
        resp = self.session.post(f"{self.BASE_URL}/v1/analytics/data",
                                 data=json.dumps(payload), timeout=30)
        if not resp.ok:
            # Пробуем без сортировки
            payload.pop("sort")
            resp = self.session.post(f"{self.BASE_URL}/v1/analytics/data",
                                     data=json.dumps(payload), timeout=30)
        resp.raise_for_status()
        return resp.json()

    def get_finance_totals(self):
        """POST /v1/finance/balance — текущий баланс (Финансы → Баланс в ЛК).
        Пробуем несколько вариантов формата дат.
        """
        now = datetime.now()
        # Вариант 1: ISO datetime с Z
        for date_fmt in ("%Y-%m-%dT%H:%M:%SZ", "%Y-%m-%d"):
            try:
                payload = {
                    "date_from": (now - timedelta(days=1)).strftime(date_fmt.replace("T%H:%M:%SZ", "T00:00:00Z").replace("%Y-%m-%d", "%Y-%m-%d")),
                    "date_to":   now.strftime(date_fmt.replace("T%H:%M:%SZ", "T23:59:59Z").replace("%Y-%m-%d", "%Y-%m-%d")),
                }
                resp = self.session.post(
                    f"{self.BASE_URL}/v1/finance/balance",
                    data=json.dumps(payload), timeout=15,
                )
                if resp.ok:
                    data = resp.json()
                    data["_endpoint_used"] = "/v1/finance/balance"
                    data["_payload_sent"]  = payload
                    return data
            except Exception:
                continue

        # Fallback: transaction totals
        now = datetime.now()
        payload = {
            "date": {
                "from": now.replace(day=1).strftime("%Y-%m-%dT00:00:00.000Z"),
                "to":   now.strftime("%Y-%m-%dT23:59:59.000Z"),
            },
            "transaction_type": "all",
        }
        resp = self.session.post(f"{self.BASE_URL}/v3/finance/transaction/totals",
                                 data=json.dumps(payload), timeout=15)
        if resp.ok:
            data = resp.json()
            data["_endpoint_used"] = "/v3/finance/transaction/totals (fallback)"
            return data
        raise RuntimeError("Все финансовые эндпоинты вернули ошибку")

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

    def get_warehouse_stocks(self):
        """Получает FBO остатки и цены для расчёта капитализации."""
        # Шаг 1: получаем список товаров с остатками через /v3/product/info/stocks
        all_items, offset = [], 0
        while True:
            payload = {"limit": 1000, "offset": offset}
            r = self.session.post(f"{self.BASE_URL}/v3/product/info/stocks",
                                  data=json.dumps(payload), timeout=30)
            if not r.ok:
                break
            result = r.json().get("result", {})
            items  = result.get("items", [])
            all_items.extend(items)
            if len(items) < 1000:
                break
            offset += 1000

        if not all_items:
            return []

        # Шаг 2: получаем цены
        product_ids = [item.get("product_id") for item in all_items if item.get("product_id")]
        prices_resp = self.session.post(
            f"{self.BASE_URL}/v5/product/info/prices",
            data=json.dumps({"filter": {"product_id": product_ids[:1000]}, "limit": 1000, "offset": 0}),
            timeout=30,
        )
        price_map = {}
        if prices_resp.ok:
            for p in prices_resp.json().get("result", {}).get("items", []):
                pid   = str(p.get("product_id", ""))
                price = float(p.get("price", {}).get("price", 0) or 0)
                if price:
                    price_map[pid] = price

        # Шаг 3: формируем результат
        rows = []
        for item in all_items:
            pid      = str(item.get("product_id", ""))
            sku_id   = str(item.get("offer_id", pid))
            sku_name = item.get("name", sku_id)
            # FBO остатки — суммируем present по всем складам типа fbo
            stocks = item.get("stocks", [])
            units  = sum(int(s.get("present", 0))
                         for s in stocks if s.get("type", "").lower() == "fbo")
            if units > 0:
                rows.append({
                    "sku": sku_id, "item_name": sku_name,
                    "free_to_sell_amount": units,
                    "product_id": pid,
                    "_price": price_map.get(pid, 0.0),
                })
        return rows

    def get_product_prices(self, product_ids: list):
        """POST /v5/product/info/prices — цены товаров."""
        if not product_ids:
            return []
        payload = {
            "filter": {"product_id": [int(p) for p in product_ids[:1000] if str(p).isdigit()]},
            "limit": 1000, "offset": 0,
        }
        r = self.session.post(f"{self.BASE_URL}/v5/product/info/prices",
                              data=json.dumps(payload), timeout=30)
        if r.ok:
            return r.json().get("result", {}).get("items", [])
        return []

    def get_localization(self):
        """Уровень локализации через /v1/analytics/data с dimension sku + cluster."""
        # Пробуем специальный эндпоинт локализации
        for path, payload in [
            ("/v1/analytics/item-localization", {"limit": 1000, "offset": 0}),
            ("/v1/product/list", {"filter": {}, "limit": 1000, "offset": 0}),
        ]:
            try:
                r = self.session.post(f"{self.BASE_URL}{path}",
                                      data=json.dumps(payload), timeout=15)
                if r.ok:
                    data  = r.json()
                    items = (data.get("result", {}).get("items") or
                             data.get("result", {}).get("rows") or [])
                    # Проверяем что есть поля локализации
                    if items and any("cluster" in str(i).lower() or
                                     "locali" in str(i).lower() for i in items[:3]):
                        return items
            except Exception:
                continue
        return []


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

MOCK_BALANCE  = 342_815.50
MOCK_RETURNS  = {"count": 47, "sum": 184_320.0}
MOCK_WAREHOUSE = {
    "total_sum": 4_821_500.0,
    "total_units": 1_243,
    "items": [
        {"sku_id": "101001", "sku_name": "Кроссовки Nike Air Max 270",     "units": 145, "sum": 724_550.0},
        {"sku_id": "101002", "sku_name": "Смартфон Samsung Galaxy A54",    "units": 82,  "sum": 1_312_000.0},
        {"sku_id": "101003", "sku_name": "Наушники Sony WH-1000XM5",       "units": 210, "sum": 630_000.0},
        {"sku_id": "101004", "sku_name": "Ноутбук ASUS VivoBook 15",       "units": 34,  "sum": 1_088_000.0},
        {"sku_id": "101005", "sku_name": "Кофемашина DeLonghi Magnifica",  "units": 56,  "sum": 448_000.0},
        {"sku_id": "101006", "sku_name": "Пылесос Dyson V15",              "units": 28,  "sum": 364_000.0},
        {"sku_id": "101007", "sku_name": "Планшет iPad 10th Gen",          "units": 67,  "sum": 201_000.0},
        {"sku_id": "101008", "sku_name": "Умная колонка Яндекс Макс",      "units": 621, "sum": 53_950.0},
    ]
}
MOCK_LOCALIZATION = [
    {"sku_id": "101001", "sku_name": "Кроссовки Nike Air Max 270",    "clusters": 21},
    {"sku_id": "101002", "sku_name": "Смартфон Samsung Galaxy A54",   "clusters": 23},
    {"sku_id": "101003", "sku_name": "Наушники Sony WH-1000XM5",      "clusters": 18},
    {"sku_id": "101004", "sku_name": "Ноутбук ASUS VivoBook 15",      "clusters": 14},
    {"sku_id": "101005", "sku_name": "Кофемашина DeLonghi Magnifica", "clusters": 9},
    {"sku_id": "101006", "sku_name": "Пылесос Dyson V15",             "clusters": 19},
    {"sku_id": "101007", "sku_name": "Планшет iPad 10th Gen",         "clusters": 23},
    {"sku_id": "101008", "sku_name": "Умная колонка Яндекс Макс",     "clusters": 7},
]
TOTAL_CLUSTERS = 23


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
# КОНФИГ — сохранение ключей между сессиями
# ─────────────────────────────────────────────
import os

CONFIG_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".ozon_config")

def load_config() -> dict:
    """Загружает сохранённые ключи из файла конфига."""
    cfg = {"client_id": "", "api_key": ""}
    # 1. Проверяем переменные окружения (Railway / .env)
    cfg["client_id"] = os.environ.get("OZON_CLIENT_ID", "")
    cfg["api_key"]   = os.environ.get("OZON_API_KEY", "")
    # 2. Если нет в env — читаем из локального файла
    if not cfg["client_id"] and os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE) as f:
                for line in f:
                    if "=" in line:
                        k, v = line.strip().split("=", 1)
                        cfg[k.strip()] = v.strip()
        except Exception:
            pass
    return cfg

def save_config(client_id: str, api_key: str):
    """Сохраняет ключи в локальный файл (только если не Railway)."""
    if os.environ.get("RAILWAY_ENVIRONMENT"):
        return  # на Railway не пишем файл — там env vars
    try:
        with open(CONFIG_FILE, "w") as f:
            f.write(f"client_id={client_id}\n")
            f.write(f"api_key={api_key}\n")
    except Exception:
        pass

# ─────────────────────────────────────────────
# SESSION STATE — настройки
# ─────────────────────────────────────────────
_cfg = load_config()

if "client_id" not in st.session_state:
    st.session_state.client_id = _cfg["client_id"]
if "api_key" not in st.session_state:
    st.session_state.api_key = _cfg["api_key"]
if "date_from" not in st.session_state:
    st.session_state.date_from = date.today() - timedelta(days=29)
if "date_to" not in st.session_state:
    st.session_state.date_to = date.today()
if "kpi_date_from" not in st.session_state:
    st.session_state.kpi_date_from = date.today() - timedelta(days=29)
if "kpi_date_to" not in st.session_state:
    st.session_state.kpi_date_to = date.today()

# ─────────────────────────────────────────────
# DATA LOADING
# ─────────────────────────────────────────────
client_id    = st.session_state.client_id
api_key      = st.session_state.api_key
date_from    = st.session_state.date_from
date_to      = st.session_state.date_to
kpi_date_from = st.session_state.kpi_date_from
kpi_date_to   = st.session_state.kpi_date_to
USE_MOCK  = not (client_id.strip() and api_key.strip())
fetch_btn = False   # будет переопределён в панели настроек если она открыта


@st.cache_data(ttl=600, show_spinner=False)
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

    # Структура: { "total": { "closing_balance": { "value": 33693.79 } } }
    total = data.get("total", {})
    closing = total.get("closing_balance", {})
    balance = float(closing.get("value", 0) or 0)

    return balance, data


@st.cache_data(ttl=300, show_spinner=False)
def load_real_returns(_cid, _key, df_str, dt_str):
    client = OzonClient(client_id=_cid, api_key=_key)
    return client.get_returns(df_str, dt_str)


@st.cache_data(ttl=600, show_spinner=False)
def load_real_warehouse(_cid, _key):
    client = OzonClient(client_id=_cid, api_key=_key)
    rows = client.get_warehouse_stocks()
    if not rows:
        return MOCK_WAREHOUSE

    result_items, total_sum, total_units = [], 0.0, 0
    for row in rows:
        sku_id   = str(row.get("sku", row.get("offer_id", "")))
        sku_name = row.get("item_name", sku_id)
        units    = int(row.get("free_to_sell_amount", 0))
        price    = float(row.get("_price", 0.0))
        item_sum = units * price
        total_sum   += item_sum
        total_units += units
        result_items.append({"sku_id": sku_id, "sku_name": sku_name,
                              "units": units, "sum": item_sum})

    result_items.sort(key=lambda x: x["sum"], reverse=True)
    return {"total_sum": total_sum, "total_units": total_units,
            "items": result_items[:50]}


@st.cache_data(ttl=600, show_spinner=False)
def load_real_localization(_cid, _key):
    """Загружает уровень локализации по SKU."""
    client = OzonClient(client_id=_cid, api_key=_key)
    items = client.get_localization()
    if not items:
        return MOCK_LOCALIZATION
    result = []
    for item in items:
        result.append({
            "sku_id":   str(item.get("sku", item.get("product_id", ""))),
            "sku_name": item.get("name", ""),
            "clusters": int(item.get("clusters_count", item.get("warehouses_count", 0))),
        })
    return sorted(result, key=lambda x: x["clusters"], reverse=True)


@st.cache_data(ttl=3600, show_spinner=False)
def load_mock_data(df, dt):
    return generate_mock_data(df, dt)


if "df" not in st.session_state or fetch_btn:
    if fetch_btn:
        load_real_data.clear()
        load_real_balance.clear()
        load_real_returns.clear()
        load_real_warehouse.clear()
        load_real_localization.clear()
        load_mock_data.clear()
    with st.spinner("Загрузка данных…"):
        try:
            if USE_MOCK:
                st.session_state.df           = load_mock_data(date_from, date_to)
                st.session_state.df_kpi       = st.session_state.df
                st.session_state.balance      = MOCK_BALANCE
                st.session_state.balance_raw  = {}
                st.session_state.returns      = MOCK_RETURNS
                st.session_state.warehouse    = MOCK_WAREHOUSE
                st.session_state.localization = MOCK_LOCALIZATION
                st.session_state.data_error   = None
            else:
                df_str  = date_from.strftime("%Y-%m-%d")
                dt_str  = date_to.strftime("%Y-%m-%d")
                kdf_str = kpi_date_from.strftime("%Y-%m-%d")
                kdt_str = kpi_date_to.strftime("%Y-%m-%d")

                # Основные данные графика
                st.session_state.df = load_real_data(client_id, api_key, df_str, dt_str)

                # KPI данные — переиспользуем если период тот же
                if kdf_str == df_str and kdt_str == dt_str:
                    st.session_state.df_kpi = st.session_state.df
                else:
                    st.session_state.df_kpi = load_real_data(client_id, api_key, kdf_str, kdt_str)

                # Баланс — независимый запрос
                try:
                    bal_result = load_real_balance(client_id, api_key)
                    st.session_state.balance     = bal_result[0]
                    st.session_state.balance_raw = bal_result[1]
                except Exception:
                    st.session_state.balance     = 0.0
                    st.session_state.balance_raw = {}

                try:
                    st.session_state.returns = load_real_returns(client_id, api_key, kdf_str, kdt_str)
                except Exception:
                    st.session_state.returns = MOCK_RETURNS
                try:
                    st.session_state.warehouse = load_real_warehouse(client_id, api_key)
                except Exception:
                    st.session_state.warehouse = MOCK_WAREHOUSE
                try:
                    st.session_state.localization = load_real_localization(client_id, api_key)
                except Exception:
                    st.session_state.localization = MOCK_LOCALIZATION
                st.session_state.data_error = None
        except Exception as e:
            st.session_state.data_error   = str(e)
            st.session_state.df           = load_mock_data(date_from, date_to)
            st.session_state.df_kpi       = st.session_state.df
            st.session_state.balance      = 0.0
            st.session_state.balance_raw  = {}
            st.session_state.returns      = MOCK_RETURNS
            st.session_state.warehouse    = MOCK_WAREHOUSE
            st.session_state.localization = MOCK_LOCALIZATION
            USE_MOCK = True

df: pd.DataFrame     = st.session_state.df
df_kpi: pd.DataFrame = st.session_state.get("df_kpi", st.session_state.df)
balance: float       = st.session_state.get("balance", MOCK_BALANCE)
returns: dict        = st.session_state.get("returns", MOCK_RETURNS)
warehouse: dict      = st.session_state.get("warehouse", MOCK_WAREHOUSE)
localization: list   = st.session_state.get("localization", MOCK_LOCALIZATION)

for col in METRIC_KEYS:
    if col not in df.columns:
        df[col] = 0.0
    if col not in df_kpi.columns:
        df_kpi[col] = 0.0

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
        st.markdown("**📅 Период — KPI карточки**")
        new_kpi_from = st.date_input("KPI от", value=st.session_state.kpi_date_from, key="inp_kf")
        new_kpi_to   = st.date_input("KPI до", value=st.session_state.kpi_date_to,   key="inp_kt")
        st.markdown("**📈 Период — График динамики**")
        new_date_from = st.date_input("График от", value=st.session_state.date_from, key="inp_df")
        new_date_to   = st.date_input("График до", value=st.session_state.date_to,   key="inp_dt")

    with cfg3:
        st.markdown("**▶ Действия**")
        st.markdown("<div style='height:4px'></div>", unsafe_allow_html=True)
        if st.button("💾 Сохранить и закрыть", use_container_width=True, key="btn_save"):
            st.session_state.client_id     = new_client_id
            st.session_state.api_key       = new_api_key
            st.session_state.date_from     = new_date_from
            st.session_state.date_to       = new_date_to
            st.session_state.kpi_date_from = new_kpi_from
            st.session_state.kpi_date_to   = new_kpi_to
            st.session_state.show_settings = False
            save_config(new_client_id, new_api_key)  # сохраняем на диск
            for _k in ["df", "df_kpi", "balance", "returns", "data_error"]:
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
# AGGREGATES  (KPI период)
# ─────────────────────────────────────────────
total_revenue    = float(df_kpi["revenue"].sum())
total_orders     = int(df_kpi["ordered_units"].sum())
total_sessions   = int(df_kpi["session_view"].sum())
total_views      = int(df_kpi["hits_view"].sum())

cvr       = (total_orders / total_views * 100) if total_views else 0
avg_order = total_revenue / total_orders if total_orders else 0

kpi_period = f"{kpi_date_from.strftime('%d.%m')}–{kpi_date_to.strftime('%d.%m.%y')}"

# ─────────────────────────────────────────────
# KPI CARDS  (4 карточки)
# ─────────────────────────────────────────────
# ─────────────────────────────────────────────
# KPI DATE PICKER — inline прямо над карточками
# ─────────────────────────────────────────────
st.markdown(f'<div class="section-title">📊 Ключевые показатели · <span style="font-weight:400;color:#8a98c0">{kpi_period}</span></div>', unsafe_allow_html=True)

dp_col1, dp_col2, dp_col3, dp_spacer = st.columns([1.5, 1.5, 1.5, 5])
with dp_col1:
    new_kpi_from = st.date_input("От", value=kpi_date_from, key="kpi_dp_from", label_visibility="collapsed")
with dp_col2:
    new_kpi_to = st.date_input("До", value=kpi_date_to, key="kpi_dp_to", label_visibility="collapsed")
with dp_col3:
    if st.button("✓ Применить", key="kpi_apply", use_container_width=True):
        st.session_state.kpi_date_from = new_kpi_from
        st.session_state.kpi_date_to   = new_kpi_to
        # Сбрасываем df_kpi чтобы принудительно перезагрузить
        for _k in ["df_kpi", "returns"]:
            st.session_state.pop(_k, None)
        load_real_data.clear()
        load_real_returns.clear()
        st.rerun()

kpi_date_from = st.session_state.kpi_date_from
kpi_date_to   = st.session_state.kpi_date_to
kpi_period    = f"{kpi_date_from.strftime('%d.%m')}–{kpi_date_to.strftime('%d.%m.%y')}"

# Перезагружаем df_kpi только если нужно
if "df_kpi" not in st.session_state:
    kdf_str = kpi_date_from.strftime("%Y-%m-%d")
    kdt_str = kpi_date_to.strftime("%Y-%m-%d")
    df_str  = date_from.strftime("%Y-%m-%d")
    dt_str  = date_to.strftime("%Y-%m-%d")
    # Если периоды совпадают — не делаем лишний запрос
    if kdf_str == df_str and kdt_str == dt_str:
        st.session_state.df_kpi = st.session_state.df
    else:
        with st.spinner("Загрузка KPI…"):
            try:
                if USE_MOCK:
                    st.session_state.df_kpi = load_mock_data(kpi_date_from, kpi_date_to)
                else:
                    st.session_state.df_kpi = load_real_data(client_id, api_key, kdf_str, kdt_str)
            except Exception:
                st.session_state.df_kpi = st.session_state.df
    try:
        if not USE_MOCK:
            st.session_state.returns = load_real_returns(client_id, api_key, kdf_str, kdt_str)
    except Exception:
        pass

df_kpi  = st.session_state.get("df_kpi", df)
returns = st.session_state.get("returns", MOCK_RETURNS)
for col in METRIC_KEYS:
    if col not in df_kpi.columns:
        df_kpi[col] = 0.0

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


# Карточка 1 — ЗАКАЗЫ: выручка / количество оформленных
dual_card(
    c1, "card-orders", "📦", "ЗАКАЗЫ",
    main_val=f"₽{total_revenue:,.0f}".replace(",", " "),
    sep="/",
    sub_val=f"{total_orders:,} шт".replace(",", " "),
    delta=f"Ср. чек ₽{avg_order:,.0f}".replace(",", " "),
)

# Карточка 2 — ПРОДАЖИ: выручка / заказы + конверсия
dual_card(
    c2, "card-sales", "💰", "ПРОДАЖИ",
    main_val=f"₽{total_revenue:,.0f}".replace(",", " "),
    sep="/",
    sub_val=f"{total_orders:,} шт".replace(",", " "),
    delta=f"▲ Конверсия {cvr:.1f}%" if cvr > 0 else "Нет данных о просмотрах",
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
chart_period = f"{date_from.strftime('%d.%m')}–{date_to.strftime('%d.%m.%y')}"
st.markdown(f'<div class="section-title">📈 Динамика · {chart_period}</div>', unsafe_allow_html=True)

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
st.caption(f"За период {kpi_period}")

group_cols = ["sku_id", "sku_name"] if "sku_name" in df_kpi.columns else ["sku_id"]
top = (
    df_kpi.groupby(group_cols)[METRIC_KEYS].sum().reset_index()
    .sort_values("revenue", ascending=False).head(10).reset_index(drop=True)
)
top.index = top.index + 1

disp = top.copy()
disp["revenue"]       = disp["revenue"].apply(lambda x: f"₽{x:,.0f}".replace(",", " "))
disp["ordered_units"] = disp["ordered_units"].apply(lambda x: f"{int(x):,} шт".replace(",", " "))
disp["hits_view"]     = disp["hits_view"].apply(lambda x: f"{int(x):,}".replace(",", " "))
# CVR = заказы / просмотры (hits_view), не session_view
safe_v  = top["hits_view"].replace(0, 1)
disp["cvr"] = (top["ordered_units"] / safe_v * 100).apply(lambda x: f"{x:.1f}%")

rename = {"sku_id": "SKU ID", "sku_name": "Товар", "revenue": "Продажи",
          "ordered_units": "Заказов", "hits_view": "Просмотров", "cvr": "Конверсия"}
disp = disp.rename(columns=rename)
show_cols = [c for c in ["SKU ID", "Товар", "Продажи", "Заказов", "Просмотров", "Конверсия"] if c in disp.columns]
st.dataframe(disp[show_cols], use_container_width=True, height=380)

# ─────────────────────────────────────────────
# WAREHOUSE CAPITALIZATION
# ─────────────────────────────────────────────
st.markdown('<div class="section-title">🏭 Капитализация складов</div>', unsafe_allow_html=True)

wh_sum   = warehouse.get("total_sum", 0)
wh_units = warehouse.get("total_units", 0)
wh_items = warehouse.get("items", [])

wh_c1, wh_c2 = st.columns([1, 3], gap="large")

with wh_c1:
    avg_price = wh_sum / wh_units if wh_units else 0
    wh_sum_fmt   = f"₽{wh_sum:,.0f}".replace(",", " ")
    wh_units_fmt = f"{wh_units:,} шт".replace(",", " ")
    avg_fmt      = f"₽{avg_price:,.0f}".replace(",", " ")
    wh_c1.markdown(f"""
        <div class="metric-card card-balance" style="height:auto">
          <div class="metric-label">🏭 Итого на складах</div>
          <div class="metric-row">
            <span class="metric-main">{wh_sum_fmt}</span>
          </div>
          <div style="font-size:14px;color:#c8d0ee;margin:6px 0">/</div>
          <div class="metric-sub">{wh_units_fmt}</div>
          <div class="metric-delta delta-neu" style="margin-top:8px">Ср. цена {avg_fmt}</div>
        </div>
    """, unsafe_allow_html=True)

with wh_c2:
    if wh_items:
        wh_df = pd.DataFrame(wh_items)
        wh_df["sum_fmt"]   = wh_df["sum"].apply(lambda x: f"₽{x:,.0f}".replace(",", " "))
        wh_df["units_fmt"] = wh_df["units"].apply(lambda x: f"{x:,} шт".replace(",", " "))
        wh_df["share"]     = (wh_df["sum"] / wh_sum * 100).apply(lambda x: f"{x:.1f}%") if wh_sum else "—"
        wh_disp = wh_df[["sku_id", "sku_name", "sum_fmt", "units_fmt", "share"]].rename(columns={
            "sku_id": "SKU", "sku_name": "Товар",
            "sum_fmt": "Стоимость", "units_fmt": "Остаток", "share": "Доля"
        })
        st.dataframe(wh_disp, use_container_width=True, height=320)
    else:
        st.info("Нет данных об остатках на складе")

# ─────────────────────────────────────────────
# LOCALIZATION
# ─────────────────────────────────────────────
st.markdown('<div class="section-title">📍 Уровень локализации</div>', unsafe_allow_html=True)
st.caption(f"Доля присутствия товара на складах относительно {TOTAL_CLUSTERS} кластеров Ozon")

if localization:
    loc_df = pd.DataFrame(localization)
    loc_df["pct"]     = (loc_df["clusters"] / TOTAL_CLUSTERS * 100).round(1)
    loc_df["pct_fmt"] = loc_df["pct"].apply(lambda x: f"{x:.1f}%")
    loc_df["bar"]     = loc_df["pct"].apply(lambda x:
        "🟢" if x >= 80 else ("🟡" if x >= 50 else "🔴"))

    # Plotly horizontal bar chart
    fig_loc = go.Figure()
    colors  = ["#059669" if p >= 80 else ("#f59e0b" if p >= 50 else "#ef4444")
               for p in loc_df["pct"]]
    fig_loc.add_trace(go.Bar(
        y=loc_df["sku_name"],
        x=loc_df["pct"],
        orientation="h",
        marker_color=colors,
        text=loc_df["pct_fmt"],
        textposition="outside",
        hovertemplate="<b>%{y}</b><br>%{x:.1f}% (%{customdata} кластеров)<extra></extra>",
        customdata=loc_df["clusters"],
    ))
    no_legend = {k: v for k, v in THEME.items() if k not in ("legend", "xaxis", "yaxis")}
    fig_loc.update_layout(
        **no_legend,
        height=max(300, len(loc_df) * 36),
        xaxis=dict(range=[0, 110], ticksuffix="%", gridcolor="#eef0f8", zeroline=False,
                   tickfont=dict(size=11, color="#8a98c0")),
        yaxis=dict(tickfont=dict(size=11, color="#1a2040"), automargin=True),
        shapes=[dict(type="line", x0=80, x1=80, y0=-0.5, y1=len(loc_df)-0.5,
                     line=dict(color="#005bff", width=1, dash="dot"))],
        annotations=[dict(x=81, y=len(loc_df)-0.5, text="цель 80%",
                          showarrow=False, font=dict(size=10, color="#005bff"))],
    )
    st.markdown('<div class="chart-box">', unsafe_allow_html=True)
    st.plotly_chart(fig_loc, use_container_width=True, config={"displayModeBar": False})
    st.markdown('</div>', unsafe_allow_html=True)
else:
    st.info("Нет данных об уровне локализации")

# ─────────────────────────────────────────────
# ФИНАНСЫ — детализация затрат
# ─────────────────────────────────────────────
st.markdown('<div class="section-title">💳 Финансы · детализация затрат</div>',
            unsafe_allow_html=True)

# Кнопка переключения
if "show_finance" not in st.session_state:
    st.session_state.show_finance = False

fin_col1, fin_col2 = st.columns([2, 8])
with fin_col1:
    if st.button("📊 Показать / скрыть", key="fin_toggle", use_container_width=True):
        st.session_state.show_finance = not st.session_state.show_finance

if st.session_state.show_finance:
    bal_raw = st.session_state.get("balance_raw", {})
    total_r = bal_raw.get("total", {})
    cf      = bal_raw.get("cashflows", {})
    services = bal_raw.get("services", [])

    if not total_r and USE_MOCK:
        st.info("⚠ В демо-режиме финансовая детализация недоступна. Подключите API.")
    else:
        # ── Сводка ──
        opening = float((total_r.get("opening_balance") or {}).get("value", 0))
        closing = float((total_r.get("closing_balance") or {}).get("value", 0))
        accrued = float((total_r.get("accrued") or {}).get("value", 0))

        sales_cf = cf.get("sales", {})
        sales_amt = float((sales_cf.get("amount") or {}).get("value", 0))
        sales_fee = float((sales_cf.get("fee") or {}).get("value", 0))

        ret_cf  = cf.get("returns", {})
        ret_amt = float((ret_cf.get("amount") or {}).get("value", 0))

        # ── KPI строка финансов ──
        fc1, fc2, fc3, fc4 = st.columns(4)
        def fin_card(col, label, value, cls="delta-neu"):
            col.markdown(f"""
                <div class="metric-card" style="border-top:3px solid #{'005bff' if cls=='delta-pos' else ('e53e3e' if cls=='delta-neg' else '8a98c0')}">
                  <div class="metric-label">{label}</div>
                  <div class="metric-main">{'₽' + f'{abs(value):,.0f}'.replace(',', ' ')}</div>
                </div>
            """, unsafe_allow_html=True)

        fin_card(fc1, "💰 Начислено за продажи", sales_amt, "delta-pos")
        fin_card(fc2, "📦 Комиссия Ozon",         abs(sales_fee), "delta-neg")
        fin_card(fc3, "↩️ Возвраты",               abs(ret_amt),  "delta-neg")
        fin_card(fc4, "🏦 Баланс на конец",        closing,       "delta-pos")

        # ── Детализация услуг ──
        if services:
            st.markdown("""<div style="font-size:11px;font-weight:600;color:#7a88b8;
                letter-spacing:.08em;text-transform:uppercase;margin:20px 0 8px">
                Детализация услуг</div>""", unsafe_allow_html=True)

            SERVICE_NAMES = {
                "goods_shelf_life_processing": "Обработка срока годности",
                "reverse_logistics":           "Обратная логистика",
                "promotion_with_cost_per_order": "Продвижение (за заказ)",
                "cross_docking":               "Кросс-докинг",
                "points_for_reviews":          "Баллы за отзывы",
                "pay_per_click":               "Реклама (клики)",
                "acquiring":                   "Эквайринг",
                "brand_promotion":             "Продвижение бренда",
                "seller_bonuses":              "Бонусы продавца",
                "logistics":                   "Логистика",
                "courier_client_reinvoice":    "Курьерская доставка",
            }
            svc_rows = []
            for svc in services:
                name = svc.get("name", "")
                amt  = float((svc.get("amount") or {}).get("value", 0))
                svc_rows.append({
                    "Услуга": SERVICE_NAMES.get(name, name),
                    "Сумма":  f"₽{amt:,.2f}".replace(",", " "),
                    "_val":   amt,
                })
            svc_rows.sort(key=lambda x: x["_val"])

            # Горизонтальный бар-чарт услуг
            svc_df = pd.DataFrame(svc_rows)
            fig_svc = go.Figure(go.Bar(
                y=svc_df["Услуга"],
                x=svc_df["_val"].abs(),
                orientation="h",
                marker_color=["#ef4444" if v < 0 else "#059669" for v in svc_df["_val"]],
                text=svc_df["Сумма"],
                textposition="outside",
                hovertemplate="<b>%{y}</b><br>%{text}<extra></extra>",
            ))
            no_leg = {k: v for k, v in THEME.items() if k not in ("legend", "xaxis", "yaxis")}
            fig_svc.update_layout(
                **no_leg,
                height=max(250, len(svc_df) * 34),
                xaxis=dict(gridcolor="#eef0f8", zeroline=False,
                           tickfont=dict(size=11, color="#8a98c0")),
                yaxis=dict(tickfont=dict(size=11, color="#1a2040"), automargin=True),
            )
            st.markdown('<div class="chart-box">', unsafe_allow_html=True)
            st.plotly_chart(fig_svc, use_container_width=True, config={"displayModeBar": False})
            st.markdown('</div>', unsafe_allow_html=True)

            # Период финансов
            payload_sent = bal_raw.get("_payload_sent", {})
            if payload_sent:
                st.caption(f"Период: {payload_sent.get('date_from', '')} — {payload_sent.get('date_to', '')}")

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
