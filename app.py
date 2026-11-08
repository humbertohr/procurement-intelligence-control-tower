# -*- coding: utf-8 -*-
"""
PROCUREMENT INTELLIGENCE CONTROL TOWER
Streamlit application | Plotly | Pandas

Required files in the same folder:
    dashboard_data.pkl
    agent_outputs.json

dashboard_data.pkl must contain the validated `dashboard_data` dictionary
exported from the Colab notebook. See the export cell supplied separately.
agent_outputs.json must contain the four CrewAI report strings.
"""

from pathlib import Path
import json
import pickle
import re

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st


# ============================================================
# 1. PAGE CONFIGURATION AND THEME
# ============================================================

st.set_page_config(
    page_title="Procurement Intelligence Control Tower",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

BASE_DIR = Path(__file__).resolve().parent
DATA_FILE = BASE_DIR / "dashboard_data.pkl"
AGENT_FILE = BASE_DIR / "agent_outputs.json"

NAVY = "#142B4A"
BLUE = "#2878B5"
TEAL = "#159D91"
AMBER = "#E6A23C"
RED = "#C94C4C"
GREY = "#718096"

st.markdown(
    f"""
    <style>
      .stApp, [data-testid="stAppViewContainer"], [data-testid="stMain"] {{
        background-color: #F5F7FA !important;
      }}
      [data-testid="stSidebar"] {{ background-color: #10243D !important; }}
      [data-testid="stSidebar"] * {{ color: #F4F7FB !important; }}

      /* Force readable dark typography in the light main workspace. */
      [data-testid="stMain"] .block-container,
      [data-testid="stMain"] .block-container p,
      [data-testid="stMain"] .block-container li,
      [data-testid="stMain"] .block-container label,
      [data-testid="stMain"] .block-container span,
      [data-testid="stMain"] .block-container strong,
      [data-testid="stMain"] .block-container em,
      [data-testid="stMain"] .block-container td,
      [data-testid="stMain"] .block-container th {{
        color: #243447;
      }}
      [data-testid="stMain"] h1,
      [data-testid="stMain"] h2,
      [data-testid="stMain"] h3,
      [data-testid="stMain"] h4 {{
        color: {NAVY} !important;
      }}
      [data-testid="stMain"] [data-testid="stMetric"] {{
        background: #FFFFFF !important;
        border: 1px solid #DCE4ED !important;
        padding: 14px 16px !important;
        border-radius: 9px !important;
        box-shadow: 0 1px 3px rgba(16,36,61,0.06);
      }}
      [data-testid="stMain"] [data-testid="stMetricLabel"],
      [data-testid="stMain"] [data-testid="stMetricLabel"] * {{
        color: #526276 !important;
      }}
      [data-testid="stMain"] [data-testid="stMetricValue"],
      [data-testid="stMain"] [data-testid="stMetricValue"] * {{
        color: {NAVY} !important;
        font-weight: 750 !important;
      }}
      [data-testid="stMain"] [data-testid="stMetricDelta"] {{
        color: #526276 !important;
      }}

      .main-title {{
        color: {NAVY} !important; font-size: 2rem; font-weight: 800;
        letter-spacing: -0.6px; margin-bottom: 0;
      }}
      .sub-title {{ color: #5B6B7F !important; font-size: 0.95rem; margin-top: 3px; }}
      .section-note {{
        background: #EAF1F8; border-left: 4px solid {BLUE};
        padding: 10px 14px; border-radius: 5px; color: #243B53 !important;
        font-size: 0.90rem; margin: 6px 0 14px 0;
      }}
      .section-note * {{ color: #243B53 !important; }}
      .agent-label {{
        color: {BLUE} !important; font-size: 0.78rem; font-weight: 700;
        text-transform: uppercase; letter-spacing: 1px;
      }}
      .executive-summary {{
        background: #FFFFFF; border: 1px solid #DCE4ED;
        border-left: 5px solid {BLUE}; border-radius: 9px;
        padding: 18px 20px; margin: 10px 0 18px 0;
      }}
      .executive-summary p, .executive-summary li {{
        color: #243447 !important; line-height: 1.55;
      }}
      .executive-summary h3, .executive-summary h4 {{
        color: {NAVY} !important; margin-top: 0.35rem;
      }}
      [data-testid="stAlert"] * {{ color: #243447 !important; }}
      [data-testid="stDataFrame"] {{ background: #FFFFFF; }}
      footer {{ visibility: hidden; }}
    </style>
    """,
    unsafe_allow_html=True
)


# ============================================================
# 2. LOAD EXPORTED DATA
# ============================================================

@st.cache_data(show_spinner=False)
def load_dashboard_data(path):
    with open(path, "rb") as file:
        return pickle.load(file)


@st.cache_data(show_spinner=False)
def load_agent_outputs(path):
    with open(path, "r", encoding="utf-8") as file:
        return json.load(file)


def money(value):
    """Format monetary values with a dollar sign."""
    try:
        return f"${float(value):,.2f}"
    except (TypeError, ValueError):
        return "—"

import re

def format_report_currency(text):
    """Add dollar signs to monetary values in AI-generated reports."""
    if not isinstance(text, str):
        return text

    return re.sub(
        r'(?<![\w$])(\d{1,3}(?:,\d{3})+\.\d{2})(?!\s*%)',
        r'$\1',
        text
    )


def number(value):
    try:
        return f"{int(value):,}"
    except (TypeError, ValueError):
        return "—"


def pct(value):
    try:
        return f"{float(value):.2f}%"
    except (TypeError, ValueError):
        return "—"


def safe_df(tables, key):
    value = tables.get(key)
    if isinstance(value, pd.DataFrame):
        return value.copy()
    return pd.DataFrame()


def show_table(df, title=None, height=360):
    if title:
        st.markdown(f"#### {title}")

    if df is None or df.empty:
        st.info("No records available for this view.")
        return

    monetary_keywords = (
        "amount",
        "balance",
        "value",
        "total_po_value",
        "total_invoiced",
        "total_paid"
    )

    formatters = {}

    # Format monetary columns with dollar sign and two decimals
    for col in df.columns:
        col_lower = str(col).lower()

        if any(keyword in col_lower for keyword in monetary_keywords):
            if pd.api.types.is_numeric_dtype(df[col]):
                formatters[col] = lambda x: (
                    f"${x:,.2f}" if pd.notna(x) else "—"
                )

    # Format delivery metrics to exactly two decimal places
    decimal_columns = [
        "average_actual_lead_time",
        "average_delivery_variance",
        "avg_days_overdue",
        "avg_lead_time_days",
        "delivery_variance_days"
    ]

    for col in decimal_columns:
        if col in df.columns:
            formatters[col] = lambda x: (
                f"{x:.2f}" if pd.notna(x) else "—"
            )

    # Format monetary values in the validation table
    if "check" in df.columns:
        monetary_rows = df["check"].astype(str).str.contains(
            "value|amount|variance",
            case=False,
            regex=True
        )

        for col in ["actual", "expected"]:
            if col in df.columns:
                formatters[col] = lambda x: (
                    f"${float(x):,.2f}" if pd.notna(x) else "—"
                )

    st.dataframe(
        df.style.format(formatters, na_rep="—"),
        use_container_width=True,
        hide_index=True,
        height=height
    )


def purpose(text):
    st.markdown(
        f'<div class="section-note"><b>Chart purpose:</b> {text}</div>',
        unsafe_allow_html=True
    )


def report_block(report_text):
    import re

    if not report_text or not str(report_text).strip():
        st.warning("This agent report was not included in agent_outputs.json.")
        return

    report_text = str(report_text).replace("`", "")

    lines = report_text.split("\n")
    formatted_lines = []
    table_headers = None

    monetary_keywords = (
        "amount",
        "value",
        "financial",
        "balance",
        "spend",
        "invoiced",
        "paid",
        "payment",
        "purchasing",
        "outstanding",
        "receipt value",
        "po value"
    )

    non_monetary_keywords = (
        "count",
        "number",
        "orders",
        "invoices",
        "days",
        "rate",
        "percentage",
        "quantity",
        "qty",
        "units",
        "rank"
    )

    for line in lines:
        stripped = line.strip()

        if "|" in stripped:
            cells = [
                cell.strip()
                for cell in stripped.strip("|").split("|")
            ]

            # Identify table headers.
            if table_headers is None:
                table_headers = cells
                formatted_lines.append(line)
                continue

            # Preserve Markdown table separators.
            if all(
                re.fullmatch(r":?-{3,}:?", cell.replace(" ", ""))
                for cell in cells
            ):
                formatted_lines.append(line)
                continue

            if len(cells) == len(table_headers):

                for i, header in enumerate(table_headers):
                    header_clean = re.sub(
                        r"[*_]",
                        "",
                        header
                    ).lower().strip()

                    is_non_monetary = any(
                        keyword in header_clean
                        for keyword in non_monetary_keywords
                    )

                    is_monetary = (
                        not is_non_monetary
                        and any(
                            keyword in header_clean
                            for keyword in monetary_keywords
                        )
                    )

                    if is_monetary:
                        original_value = cells[i]

                        # Detect bold formatting.
                        is_bold = (
                            original_value.startswith("**")
                            and original_value.endswith("**")
                        )

                        # Remove Markdown formatting and currency symbols.
                        clean_value = re.sub(
                            r"[*_$,\s]",
                            "",
                            original_value
                        )

                        # Format numeric monetary values.
                        if re.fullmatch(
                            r"-?\d+(?:\.\d+)?",
                            clean_value
                        ):
                            formatted_value = (
                                f"${float(clean_value):,.2f}"
                            )

                            if is_bold:
                                formatted_value = (
                                    f"**{formatted_value}**"
                                )

                            cells[i] = formatted_value

                formatted_lines.append(
                    "| " + " | ".join(cells) + " |"
                )

            else:
                formatted_lines.append(line)

        else:
            table_headers = None
            formatted_lines.append(line)

    report_text = "\n".join(formatted_lines)

    st.markdown(report_text)


def management_summary(portfolio, delivery, financial, fulfillment,
                       supplier_view, overdue_supplier_df, missing_receipt_df):
    """Present a concise management view from validated deterministic metrics."""
    st.subheader("Management summary")
    st.caption(
        "A concise decision-support summary calculated from the validated dashboard data. "
        "The complete Gemini Agent 4 report follows below. Use always a dolar sign for the amounts and values when talking about money"
    )

    total_value = portfolio.get("total_purchasing_value", 0)
    late_rate = delivery.get("late_delivery_rate_pct", 0)
    late_count = delivery.get("late_orders", 0)
    overdue_amount = financial.get(
        "overdue_amount", financial.get("total_outstanding", 0)
    )
    overdue_count = financial.get("overdue_invoice_count", 0)
    open_value = fulfillment.get("open_po_value", 0)
    open_count = fulfillment.get("open_po_count", 0)

    m1, m2, m3 = st.columns(3)
    m1.metric("Portfolio purchasing value", money(total_value))
    m2.metric("Late delivery rate", pct(late_rate))
    m3.metric("Overdue invoices", f"{number(overdue_count)} · {money(overdue_amount)}")

    st.markdown('<div class="executive-summary">', unsafe_allow_html=True)
    st.markdown("#### What management should know")

    late_supplier = None
    if not supplier_view.empty and "late_delivery_rate_pct" in supplier_view.columns:
        tmp = supplier_view.dropna(subset=["late_delivery_rate_pct"]).copy()
        if not tmp.empty:
            late_supplier = tmp.sort_values(
                "late_delivery_rate_pct", ascending=False
            ).iloc[0]

    overdue_supplier = None
    if not overdue_supplier_df.empty and "overdue_amount" in overdue_supplier_df.columns:
        overdue_supplier = overdue_supplier_df.sort_values(
            "overdue_amount", ascending=False
        ).iloc[0]

    missing_supplier = None
    if not missing_receipt_df.empty and "missing_receipt_value" in missing_receipt_df.columns:
        missing_supplier = missing_receipt_df.sort_values(
            "missing_receipt_value", ascending=False
        ).iloc[0]

    st.markdown(
        f"- **Delivery:** {number(late_count)} of {number(delivery.get('received_orders', 0))} "
        f"received orders were late ({pct(late_rate)})."
    )
    st.markdown(
        f"- **Accounts payable:** {number(overdue_count)} overdue invoices total "
        f"{money(overdue_amount)}. These are buyer-side payment obligations; the data "
        f"does not establish why they remain unpaid."
    )
    st.markdown(
        f"- **Fulfillment records:** {number(open_count)} sent POs worth {money(open_value)} "
        f"have no linked invoice or recorded goods receipt. This is a documentation/verification "
        f"exception, not proof of non-delivery or confirmed AP."
    )
    if late_supplier is not None:
        st.markdown(
            f"- **Highest observed late-delivery rate:** {late_supplier.get('supplier_name', 'Supplier')} "
            f"at {pct(late_supplier.get('late_delivery_rate_pct'))}."
        )
    if overdue_supplier is not None:
        st.markdown(
            f"- **Largest overdue supplier balance:** {overdue_supplier.get('supplier_name', 'Supplier')} "
            f"at {money(overdue_supplier.get('overdue_amount'))}."
        )
    if missing_supplier is not None:
        st.markdown(
            f"- **Largest missing-receipt PO value:** {missing_supplier.get('supplier_name', 'Supplier')} "
            f"at {money(missing_supplier.get('missing_receipt_value'))}."
        )

    st.markdown("#### Recommended management sequence")
    st.markdown(
        "1. **Verify the 25 open POs:** reconcile warehouse receiving logs, proof of delivery, "
        "supplier confirmations and PO status before closing or escalating them.\n"
        "2. **Validate the 17 overdue invoices:** check invoice approval, disputes, supplier "
        "statements and bank/accounting records before authorizing payment.\n"
        "3. **Address delivery reliability:** review corrective actions and service levels "
        "with suppliers showing elevated late-delivery rates; do not transfer volume without "
        "capacity and alternative-supplier validation."
    )
    st.markdown(
        "**Interpretation guardrail:** delivery performance, overdue AP and open-PO "
        "documentation are separate dimensions. Do not add their values together or infer "
        "causation from supplier-level overlap."
    )
    st.markdown("</div>", unsafe_allow_html=True)


def plotly_layout(fig, height=420):
    fig.update_layout(
        template="plotly_white",
        paper_bgcolor="#FFFFFF",
        plot_bgcolor="#FFFFFF",
        height=height,
        margin=dict(l=35, r=35, t=55, b=40),

        # Chart title
        title_font=dict(
            family="Arial",
            size=17,
            color="#17324D"
        ),

        # General text
        font=dict(
            family="Arial",
            size=12,
            color="#17324D"
        ),

        # Legend
        legend_title_text="",
        legend=dict(
            font=dict(
                family="Arial",
                size=12,
                color="#17324D"
            )
        ),

        # Hover information
        hoverlabel=dict(
            bgcolor="#FFFFFF",
            font=dict(
                family="Arial",
                size=12,
                color="#17324D"
            )
        )
    )

    # X-axis
    fig.update_xaxes(
        title_font=dict(
            family="Arial",
            size=12,
            color="#17324D"
        ),
        tickfont=dict(
            family="Arial",
            size=11,
            color="#17324D"
        ),
        linecolor="#17324D",
        zerolinecolor="#AAB7C4",
        gridcolor="#E2E8F0"
    )

    # Y-axis
    fig.update_yaxes(
        title_font=dict(
            family="Arial",
            size=12,
            color="#17324D"
        ),
        tickfont=dict(
            family="Arial",
            size=11,
            color="#17324D"
        ),
        linecolor="#17324D",
        zerolinecolor="#AAB7C4",
        gridcolor="#E2E8F0"
    )

    return fig


if not DATA_FILE.exists():
    st.error(f"Missing file: {DATA_FILE.name}")
    st.markdown(
        "Export `dashboard_data.pkl` from the Colab notebook and place it "
        "in the same folder as `app.py`."
    )
    st.stop()

if not AGENT_FILE.exists():
    st.error(f"Missing file: {AGENT_FILE.name}")
    st.markdown(
        "Create `agent_outputs.json` from the four CrewAI report outputs "
        "and place it in the same folder as `app.py`."
    )
    st.stop()

try:
    data = load_dashboard_data(str(DATA_FILE))
    agents = load_agent_outputs(str(AGENT_FILE))
except Exception as exc:
    st.exception(exc)
    st.stop()

metadata = data.get("metadata", {})
portfolio = data.get("portfolio", {})
delivery = data.get("delivery", {})
financial = data.get("financial", {})
fulfillment = data.get("fulfillment", {})
tables = data.get("tables", {})

if metadata.get("validation_status") != "PASS":
    st.error("DATA VALIDATION FAILED — dashboard is blocked from presenting KPIs.")
    st.json(data.get("validation", []))
    st.stop()


# ============================================================
# 3. SIDEBAR AND GLOBAL FILTERS
# ============================================================

st.sidebar.markdown("## PROCUREMENT")
st.sidebar.caption("INTELLIGENCE CONTROL TOWER")
st.sidebar.caption("by Humberto H.")
st.sidebar.markdown("---")

pages = [
    "Executive Overview",
    "Agent 1 · Supplier Performance",
    "Agent 2 · Financial Reconciliation",
    "Agent 3 · Fulfillment Exceptions",
    "Agent 4 · Executive Intelligence",
    "Data Validation & Methodology"
]

selected_page = st.sidebar.radio("Navigate", pages)

st.sidebar.markdown("---")
st.sidebar.markdown("**Dataset information**")
st.sidebar.write(f"Analysis date: {metadata.get('analysis_date', '—')}")
st.sidebar.write(f"Dataset: {metadata.get('dataset_type', '—')}")
st.sidebar.markdown(
    """
    <div style="
        background-color: #145C50;
        color: #FFFFFF;
        padding: 14px;
        border-radius: 8px;
        font-weight: 700;
        text-align: center;
    ">
        Deterministic validation: PASS
    </div>
    """,
    unsafe_allow_html=True
)


# ============================================================
# 4. PREPARE TABLES AND COMMON SUPPLIER VIEW
# ============================================================

spend_df = safe_df(tables, "supplier_spend")
overdue_supplier_df = safe_df(tables, "supplier_overdue_exposure")
missing_receipt_df = safe_df(tables, "supplier_missing_receipts")
overdue_df = safe_df(tables, "overdue_invoices")
open_po_df = safe_df(tables, "open_purchase_orders")

# Join the three independent supplier dimensions for dashboard comparison.
supplier_view = spend_df.copy()

supplier_delivery_df = safe_df(tables, "supplier_delivery")

if not supplier_view.empty:
    if "supplier_name" not in supplier_view.columns and "name" in supplier_view.columns:
        supplier_view = supplier_view.rename(columns={"name": "supplier_name"})


if not supplier_delivery_df.empty:
    if "supplier_name" not in supplier_delivery_df.columns and "name" in supplier_delivery_df.columns:
        supplier_delivery_df = supplier_delivery_df.rename(
            columns={"name": "supplier_name"}
        )
    if "supplier_name" in supplier_delivery_df.columns:
        supplier_view = supplier_view.merge(
            supplier_delivery_df, on="supplier_name", how="left"
        )

if not overdue_supplier_df.empty and "supplier_name" in overdue_supplier_df.columns:
    supplier_view = supplier_view.merge(
        overdue_supplier_df, on="supplier_name", how="left"
    )

if not missing_receipt_df.empty and "supplier_name" in missing_receipt_df.columns:
    supplier_view = supplier_view.merge(
        missing_receipt_df, on="supplier_name", how="left"
    )

for col in [
    "overdue_amount", "overdue_invoice_count", "avg_days_overdue",
    "missing_receipt_orders", "missing_receipt_value"
]:
    if col in supplier_view.columns:
        supplier_view[col] = pd.to_numeric(
            supplier_view[col], errors="coerce"
        ).fillna(0)


# ============================================================
# 5. HEADER
# ============================================================

import base64
from pathlib import Path

# Load CrewAI logo
crewai_logo = Path(__file__).parent / "crewai.png"

with open(crewai_logo, "rb") as image_file:
    logo_base64 = base64.b64encode(image_file.read()).decode()

# Title and logo in one horizontal container
st.markdown(
    f"""
    <div style="
        display: flex;
        align-items: center;
        gap: 12px;
        flex-wrap: wrap;
        margin-bottom: 20px;
    ">
        <h1 style="
            color: #17324D;
            font-family: Arial, sans-serif;
            font-size: 40px;
            font-weight: 700;
            margin: 0;
            line-height: 1.2;
        ">
            Procurement Intelligence Control Tower | Powered by
        </h1>
        <img
            src="data:image/png;base64,{logo_base64}"
            style="
                width: 122px;
                height: auto;
                object-fit: contain;
            "
        />
    </div>
    """,
    unsafe_allow_html=True
)

st.markdown("""
<div style="
    background-color: #EAF2FA;
    border-left: 5px solid #2878B5;
    border-radius: 8px;
    padding: 16px 20px;
    margin: 12px 0 18px 0;
    color: #17324D;
    font-size: 15px;
    line-height: 1.6;
">
    <strong>Platform Overview</strong><br>
    An AI-powered procurement intelligence platform that combines
    supplier performance analytics, financial reconciliation,
    fulfillment monitoring, and Gemini-generated insights to identify
    risks and support data-driven purchasing and operational decisions.
</div>
""", unsafe_allow_html=True)

st.caption(
    f"Analysis date: {metadata.get('analysis_date', '—')}"
)
st.markdown("")


# ============================================================
# PAGE: EXECUTIVE OVERVIEW
# ============================================================

if selected_page == "Executive Overview":

    st.markdown('<div class="agent-label">Portfolio command view</div>', unsafe_allow_html=True)
    st.header("Executive Overview")

    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("Purchasing value", money(portfolio.get("total_purchasing_value")))
    c2.metric("Purchase orders", number(portfolio.get("total_purchase_orders")))
    c3.metric("Late delivery rate", pct(delivery.get("late_delivery_rate_pct")))
    c4.metric("Overdue invoices", money(financial.get("overdue_amount")))
    c5.metric("Open PO exceptions", money(fulfillment.get("open_po_value")))

    st.caption(
        f"{number(portfolio.get('total_suppliers'))} suppliers in master data · "
        f"{number(portfolio.get('suppliers_with_purchase_history'))} with purchasing history · "
        f"{number(delivery.get('received_orders'))} received orders used in delivery-rate denominator"
    )

    left, right = st.columns(2)

    with left:
        purpose(
            "Shows the composition of confirmed delivery outcomes. "
            "The denominator excludes 25 orders without a confirmed delivery outcome."
        )
        delivery_mix = pd.DataFrame({
            "Delivery outcome": ["On time", "Late"],
            "Orders": [
                delivery.get("on_time_orders", 0),
                delivery.get("late_orders", 0)
            ]
        })
        fig = px.pie(
            delivery_mix,
            names="Delivery outcome",
            values="Orders",
            hole=0.62,
            title="Received-order delivery outcome",
            color="Delivery outcome",
            color_discrete_map={"On time": TEAL, "Late": RED}
        )
        fig.update_traces(
            textposition="inside",
            textinfo="percent+label",
            hovertemplate="%{label}<br>Orders: %{value:,}<br>Share: %{percent}<extra></extra>"
        )
        st.plotly_chart(plotly_layout(fig, 390), use_container_width=True)

    with right:
        purpose(
            "Compares the three distinct procurement exception categories. "
            "Open PO value is not accounts payable and must not be added to overdue invoices."
        )

        exposure = pd.DataFrame({
            "Exception category": [
                "Overdue invoice balance",
                "Open POs without invoice/receipt record"
            ],
            "Value": [
                financial.get("overdue_amount", 0),
                fulfillment.get("open_po_value", 0)
            ]
        })

        fig = px.bar(
            exposure,
            x="Exception category",
            y="Value",
            title="Financial and fulfillment exception values",
            text="Value",
            color="Exception category",
            color_discrete_sequence=[AMBER, BLUE]
        )

        fig.update_traces(
            texttemplate="$%{text:,.2f}",
            textposition="outside",
            textfont=dict(
                color="#17324D",
                size=12
            ),
            hovertemplate="%{x}<br>Value: $%{y:,.2f}<extra></extra>"
        )

        fig.update_layout(
            font=dict(
                color="#17324D",
                size=12
            ),
            title_font=dict(
                color="#17324D",
                size=16
            ),
            legend=dict(
                font=dict(color="#17324D")
            ),
            plot_bgcolor="#FFFFFF",
            paper_bgcolor="#FFFFFF"
        )

        fig.update_xaxes(
            title_font=dict(color="#17324D"),
            tickfont=dict(color="#17324D")
        )

        fig.update_yaxes(
            title="Value ($)",
            title_font=dict(color="#17324D"),
            tickfont=dict(color="#17324D"),
            tickprefix="$",
            tickformat=",.0f"
        )

        st.plotly_chart(
            plotly_layout(fig, 390),
            use_container_width=True
        )

    st.subheader("Supplier portfolio: spend and delivery performance")
    purpose(
        "Places purchasing concentration beside late-delivery performance. "
        "Bubble size represents PO value; late-delivery percentage uses received orders only. "
        "This is a descriptive comparison, not a causal or statistical correlation analysis."
    )

    if not supplier_view.empty and {
        "total_po_value", "late_delivery_rate_pct"
    }.issubset(supplier_view.columns):
        chart_df = supplier_view.copy()
        chart_df["late_delivery_rate_pct"] = pd.to_numeric(
            chart_df["late_delivery_rate_pct"], errors="coerce"
        )
        if "purchase_order_count" in chart_df.columns:
            size_col = "purchase_order_count"
        else:
            size_col = "total_po_value"

        fig = px.scatter(
            chart_df,
            x="total_po_value",
            y="late_delivery_rate_pct",
            size=size_col,
            color="late_delivery_rate_pct",
            hover_name="supplier_name",
            hover_data={
                "total_po_value": ":,.2f",
                "late_delivery_rate_pct": ":.2f",
                size_col: True
            },
            title="Supplier spend versus late-delivery rate",
            color_continuous_scale="RdYlGn_r",
            labels={
                "total_po_value": "Total PO value",
                "late_delivery_rate_pct": "Late delivery rate (%)"
            }
        )
        fig.update_yaxes(ticksuffix="%", rangemode="tozero")
        st.plotly_chart(plotly_layout(fig, 470), use_container_width=True)
    else:
        st.info("Supplier spend and delivery fields are not available for this chart.")

    st.subheader("Priority indicators")
    priority_rows = [
        ["Supplier delivery", "Elliott and Sons", "Highest late rate: 64.58%"],
        ["Supplier delivery", "Ford, Barton and Lee", "Late rate: 64.42%"],
        ["Supplier delivery", "Allen PLC", "Largest PO value: 412,197.65; late rate: 60.11%"],
        ["Accounts payable", "Thomas Ltd", "Largest overdue balance: 6,482.35"],
        ["Fulfillment records", "Elliott and Sons", "8 POs without recorded goods receipts/invoices"],
        ["Fulfillment records", "Lozano, Chaney and Carr", "6 POs without recorded goods receipts/invoices"]
    ]
    show_table(
        pd.DataFrame(priority_rows, columns=["Dimension", "Supplier", "Evidence"]),
        height=270
    )

    st.info(
        "Interpretation: delivery performance, buyer-side overdue invoices, and "
        "open-PO record exceptions are separate dimensions. No composite supplier "
        "risk score is calculated."
    )


# ============================================================
# PAGE: AGENT 1 — SUPPLIER PERFORMANCE
# ============================================================

elif selected_page == "Agent 1 · Supplier Performance":

    st.markdown('<div class="agent-label">Agent 1 · Senior Supplier Performance Analyst</div>', unsafe_allow_html=True)
    st.header("Supplier Performance Intelligence")

    c1, c2, c3 = st.columns(3)
    c1.metric("Received orders", number(delivery.get("received_orders")))
    c2.metric("On-time delivery", pct(delivery.get("on_time_delivery_rate_pct")))
    c3.metric("Late delivery", pct(delivery.get("late_delivery_rate_pct")))

    if not supplier_view.empty:
        chart_df = supplier_view.copy()

        if "late_delivery_rate_pct" in chart_df.columns:
            chart_df = chart_df.sort_values(
                "late_delivery_rate_pct", ascending=True
            )

            purpose(
                "Ranks suppliers by late-delivery rate. This helps identify "
                "where supplier corrective-action discussions should begin. "
                "Supplier rates are descriptive and should be read with order counts."
            )

            fig = px.bar(
                chart_df,
                x="late_delivery_rate_pct",
                y="supplier_name",
                orientation="h",
                text="late_delivery_rate_pct",
                title="Late-delivery rate by supplier",
                color="late_delivery_rate_pct",
                color_continuous_scale="RdYlGn_r",
                labels={
                    "late_delivery_rate_pct": "Late delivery rate (%)",
                    "supplier_name": "Supplier"
                }
            )

            fig.update_traces(
                texttemplate="%{text:.2f}%",
                textposition="outside",
                textfont=dict(color="#17324D", size=12),
                hovertemplate="%{y}<br>Late rate: %{x:.2f}%<extra></extra>"
            )

            fig = plotly_layout(fig, 470)

            fig.update_layout(
                font=dict(color="#17324D", size=12),
                title_font=dict(color="#17324D", size=16),
                plot_bgcolor="#FFFFFF",
                paper_bgcolor="#FFFFFF",
                coloraxis_colorbar=dict(
                    tickfont=dict(color="#17324D"),
                    title_font=dict(color="#17324D")
                )
            )

            fig.update_xaxes(
                title="Late delivery rate (%)",
                title_font=dict(color="#17324D"),
                tickfont=dict(color="#17324D"),
                ticksuffix="%",
                range=[0, 100]
            )

            fig.update_yaxes(
                title="Supplier",
                title_font=dict(color="#17324D"),
                tickfont=dict(color="#17324D")
            )

            st.plotly_chart(fig, use_container_width=True)


        if "total_po_value" in chart_df.columns:
            purpose(
                "Shows the distribution of purchasing value across suppliers. "
                "Use it to identify concentration and commercial dependency, not to infer performance."
            )

            spend_plot = chart_df.sort_values(
                "total_po_value", ascending=True
            )

            fig = px.bar(
                spend_plot,
                x="total_po_value",
                y="supplier_name",
                orientation="h",
                text="total_po_value",
                title="Supplier purchasing value",
                color_discrete_sequence=[BLUE],
                labels={
                    "total_po_value": "Total PO value",
                    "supplier_name": "Supplier"
                }
            )

            fig.update_traces(
                texttemplate="$%{text:,.2f}",
                textposition="outside",
                textfont=dict(color="#17324D", size=12),
                hovertemplate="%{y}<br>Purchasing value: $%{x:,.2f}<extra></extra>"
            )

            fig = plotly_layout(fig, 470)

            fig.update_layout(
                font=dict(color="#17324D", size=12),
                title_font=dict(color="#17324D", size=16),
                plot_bgcolor="#FFFFFF",
                paper_bgcolor="#FFFFFF"
            )

            fig.update_xaxes(
                title="Total PO value ($)",
                title_font=dict(color="#17324D"),
                tickfont=dict(color="#17324D"),
                tickprefix="$",
                tickformat=",.0f"
            )

            fig.update_yaxes(
                title="Supplier",
                title_font=dict(color="#17324D"),
                tickfont=dict(color="#17324D")
            )

            st.plotly_chart(fig, use_container_width=True)

    st.subheader("Supplier performance scorecard")
    score_cols = [
        c for c in [
            "supplier_name", "total_po_value", "purchase_order_count",
            "received_orders", "late_orders", "on_time_orders",
            "late_delivery_rate_pct", "on_time_delivery_rate_pct",
            "average_actual_lead_time", "average_delivery_variance"
        ] if c in supplier_view.columns
    ]
    if score_cols:
        show_table(supplier_view[score_cols].round(2), height=390)
    else:
        show_table(spend_df)

    st.subheader("Agent 1 analytical output")
    report_block(agents.get("supplier_performance", ""))


# ============================================================
# PAGE: AGENT 2 — FINANCIAL RECONCILIATION
# ============================================================

elif selected_page == "Agent 2 · Financial Reconciliation":

    st.markdown('<div class="agent-label">Agent 2 · Procurement Financial Reconciliation Analyst</div>', unsafe_allow_html=True)
    st.header("Financial Reconciliation & Accounts Payable")

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Total invoiced", money(financial.get("total_invoiced")))
    c2.metric("Total paid", money(financial.get("total_paid")))
    c3.metric("Outstanding balance", money(financial.get("total_outstanding")))
    c4.metric("Overdue invoices", number(financial.get("overdue_invoice_count")))

    purpose(
        "Reconciles the invoice portfolio into paid and outstanding components. "
        "The values are portfolio totals; they are not supplier performance measures."
    )
    reconciliation = pd.DataFrame({
        "Category": ["Paid", "Outstanding"],
        "Amount": [
            financial.get("total_paid", 0),
            financial.get("total_outstanding", 0)
        ]
    })
    fig = px.bar(
        reconciliation,
        x="Category",
        y="Amount",
        color="Category",
        text="Amount",
        title="Invoice payment reconciliation",
        color_discrete_map={"Paid": TEAL, "Outstanding": AMBER}
    )
    fig.update_traces(
        texttemplate="$%{text:,.2f}",
        textposition="outside",
        hovertemplate="%{x}<br>Amount: %{y:,.2f}<extra></extra>"
    )
    fig.update_yaxes(title="Value ($)", tickprefix="$", tickformat=",.0f")
    st.plotly_chart(plotly_layout(fig, 390), use_container_width=True)

    if not overdue_supplier_df.empty:
        purpose(
            "Ranks suppliers by overdue invoice balance. This supports AP workload "
            "prioritization; it does not establish why invoices remain unpaid."
        )
        fin_plot = overdue_supplier_df.sort_values("overdue_amount", ascending=True)
        fig = px.bar(
            fin_plot,
            x="overdue_amount",
            y="supplier_name",
            orientation="h",
            text="overdue_amount",
            title="Overdue accounts-payable exposure by supplier",
            color_discrete_sequence=[AMBER],
            labels={
                "overdue_amount": "Overdue amount",
                "supplier_name": "Supplier"
            }
        )
        fig.update_traces(
            texttemplate="$%{text:,.2f}",
            textposition="outside"
        )
        fig.update_xaxes(title="Value ($)", tickprefix="$", tickformat=",.0f")
        st.plotly_chart(plotly_layout(fig, 430), use_container_width=True)

    st.subheader("Supplier overdue exposure")
    show_table(overdue_supplier_df.round(2), height=300)

    st.subheader("Invoice-level overdue register")
    if not overdue_df.empty:
        preferred = [
            c for c in [
                "invoice_number", "supplier_name", "due_date",
                "days_overdue", "total_amount", "total_paid",
                "outstanding_balance", "status"
            ] if c in overdue_df.columns
        ]
        invoice_table = overdue_df[preferred].copy()
        if "due_date" in invoice_table.columns:
            invoice_table["due_date"] = pd.to_datetime(
                invoice_table["due_date"], errors="coerce"
            ).dt.strftime("%Y-%m-%d")
        show_table(invoice_table, height=400)
    else:
        st.info("No overdue invoice records were supplied.")

    st.caption(
        f"Financial reconciliation variance: {money(financial.get('reconciliation_variance'))}. "
        "A zero variance indicates arithmetic reconciliation of the supplied invoice, "
        "payment and outstanding fields; it does not replace invoice approval controls."
    )

    st.subheader("Agent 2 analytical output")
    report_block(agents.get("financial_reconciliation", ""))


# ============================================================
# PAGE: AGENT 3 — FULFILLMENT EXCEPTIONS
# ============================================================

elif selected_page == "Agent 3 · Fulfillment Exceptions":

    st.markdown('<div class="agent-label">Agent 3 · Procurement Fulfillment & Open PO Exception Analyst</div>', unsafe_allow_html=True)
    st.header("Open Purchase Orders & Fulfillment Exceptions")

    c1, c2, c3 = st.columns(3)
    c1.metric("Open PO exceptions", number(fulfillment.get("open_po_count")))
    c2.metric("Open PO value", money(fulfillment.get("open_po_value")))
    c3.metric("No receipt records", number(fulfillment.get("missing_receipt_count")))

    if not missing_receipt_df.empty:
        purpose(
            "Shows suppliers with the largest value of POs lacking recorded goods receipts. "
            "A missing receipt record is an investigation flag, not proof that goods were not delivered."
        )
        fr_plot = missing_receipt_df.sort_values(
            "missing_receipt_value", ascending=True
        )
        fig = px.bar(
            fr_plot,
            x="missing_receipt_value",
            y="supplier_name",
            orientation="h",
            text="missing_receipt_value",
            title="PO value without recorded goods receipts by supplier",
            color_discrete_sequence=[BLUE],
            labels={
                "missing_receipt_value": "PO value",
                "supplier_name": "Supplier"
            }
        )
        fig.update_traces(
            texttemplate="$%{text:,.2f}",
            textposition="outside"
        )
        fig.update_xaxes(title="Value ($)", tickprefix="$", tickformat=",.0f")
        st.plotly_chart(plotly_layout(fig, 420), use_container_width=True)

        purpose(
            "Compares the number of affected POs per supplier. Counts complement value "
            "because a supplier with many small POs may require a different investigation "
            "sequence from one with fewer high-value POs."
        )
        fig = px.bar(
            missing_receipt_df.sort_values(
                "missing_receipt_orders", ascending=True
            ),
            x="missing_receipt_orders",
            y="supplier_name",
            orientation="h",
            text="missing_receipt_orders",
            title="PO count without recorded goods receipts by supplier",
            color_discrete_sequence=[TEAL]
        )
        fig.update_traces(textposition="outside")
        fig.update_xaxes(title="Purchase orders", dtick=1)
        st.plotly_chart(plotly_layout(fig, 420), use_container_width=True)

    st.subheader("Supplier fulfillment exception register")
    show_table(missing_receipt_df.round(2), height=300)

    st.subheader("Open purchase order detail")
    if not open_po_df.empty:
        po_columns = [
            c for c in [
                "po_number", "supplier_name", "order_date",
                "expected_date", "status_po", "status",
                "total_amount_po", "total_amount"
            ] if c in open_po_df.columns
        ]
        if po_columns:
            show_table(open_po_df[po_columns], height=420)
        else:
            show_table(open_po_df, height=420)
    else:
        st.info("No open purchase order records were supplied.")

    st.warning(
        "Control distinction: these 25 POs have no linked invoice and no recorded "
        "goods receipt in the supplied records. Their value is not confirmed AP, "
        "loss, or proof of non-delivery. Verify warehouse logs, proof of delivery, "
        "supplier confirmation, and PO status before closure or escalation."
    )

    st.subheader("Agent 3 analytical output")
    report_block(agents.get("fulfillment_exceptions", ""))


# ============================================================
# PAGE: AGENT 4 — EXECUTIVE INTELLIGENCE
# ============================================================

elif selected_page == "Agent 4 · Executive Intelligence":

    st.markdown('<div class="agent-label">Agent 4 · Senior Procurement Intelligence Manager</div>', unsafe_allow_html=True)
    st.header("Integrated Executive Procurement Intelligence")

    st.markdown(
        "This section combines a concise management view from validated metrics "
        "with the full integrated narrative generated by Gemini Agent 4."
    )

    management_summary(
        portfolio, delivery, financial, fulfillment,
        supplier_view, overdue_supplier_df, missing_receipt_df
    )

    st.divider()
    st.subheader("Full Gemini Agent 4 report")
    report_block(agents.get("executive_intelligence", ""))


# ============================================================
# PAGE: DATA VALIDATION & METHODOLOGY
# ============================================================

elif selected_page == "Data Validation & Methodology":

    st.markdown('<div class="agent-label">Deterministic Python control layer</div>', unsafe_allow_html=True)
    st.header("Data Validation & Methodology")

    st.success(
        f"Validation status: {metadata.get('validation_status', 'UNKNOWN')}"
    )

    validation_records = data.get("validation", [])
    validation_df = pd.DataFrame(validation_records)
    show_table(validation_df, "Deterministic validation checks", height=430)

    st.subheader("Metric definitions and interpretation")
    definitions = pd.DataFrame([
        ["Late delivery rate", "Late received orders / all received orders", "25 orders without confirmed delivery outcome are excluded."],
        ["On-time delivery rate", "On-time received orders / all received orders", "Denominator = 902 received orders."],
        ["Overdue invoice balance", "Outstanding invoice balance where due date precedes analysis date", "Buyer-side AP obligation; cause of nonpayment is unknown."],
        ["Open PO exception value", "Value of POs without linked invoice and without recorded goods receipt", "Not confirmed AP, loss, or proof of non-delivery."],
        ["Supplier spend", "Sum of purchase-order total_amount by supplier", "Currency is not independently verified."],
        ["Insufficient supplier history", "Supplier master record without purchase history", "Not classified as low risk or as a confirmed onboarding/data issue."]
    ], columns=["Metric", "Calculation", "Interpretation"])
    show_table(definitions, height=320)

    st.subheader("Portfolio controls")
    st.write(
        f"- Total purchase orders: **{number(portfolio.get('total_purchase_orders'))}**\n"
        f"- Received orders in delivery denominator: **{number(delivery.get('received_orders'))}**\n"
        f"- Orders without confirmed delivery outcome: **{number(delivery.get('unclassified_orders'))}**\n"
        f"- Invoice reconciliation variance: **{money(financial.get('reconciliation_variance'))}**\n"
        f"- Dataset type: **{metadata.get('dataset_type', 'Not specified')}**"
    )


# ============================================================
# 6. FOOTER
# ============================================================

st.markdown("---")
st.caption(
    "Procurement Intelligence Control Tower · Python validation + CrewAI insights "
)
