import streamlit as st
from supabase import create_client, Client
from datetime import date, datetime

# =========================================================
# PAGE CONFIG
# =========================================================

st.set_page_config(
    page_title="Sample Management",
    page_icon="🧪",
    layout="wide",
)

TABLE = "samples"

# =========================================================
# MASTER DATA
# =========================================================

BUYERS = [
    "THURSDAY",
    "ARITZIA",
    "CENTRIC BRAND LLC",
    "M0851",
    "PAIGE",
    "PEERLESS CLOTHING INTERNATIONAL INC.",
    "SPARTINA 449",
    "TAILORED BRANDS",
]

SUPPLIERS = [
    "BALAMURUGAN LEATHER",
    "DHEVA ENTERPRISES",
    "GAUTHAM LEATHER INDUSTRIES",
    "J&J LEATHER ENTERPRISES LTD",
    "LIFFA EXPORTS",
    "MILLENNIUM LEATHER FASHION",
    "NASEER LEATHER",
    "NEW VISION LEATHER SOLUTIONS",
    "OCEAN TANNERS",
    "PRAKASH IMPEX",
    "PRIMUS INTERNATIONAL",
    "RADO EXPORTS",
    "RIYAZ LEATHERS",
    "S.A.LEATHER FINISHERS",
    "SARAPESWARER LEATHER",
    "SHIVA TANNERS",
    "SRI RAGHAVENDRA LEATHERS",
    "SUNRISE LEATHER",
    "WESTERN ALFA LEATHER (P) LTD",
    "ZUHA LEATHER PVT LIMITED",
]

# =========================================================
# SUPABASE
# =========================================================

@st.cache_resource
def get_supabase() -> Client:
    return create_client(
        st.secrets["SUPABASE_URL"].strip().rstrip("/"),
        st.secrets["SUPABASE_KEY"].strip(),
    )


try:
    supabase = get_supabase()
except Exception as exc:
    st.error(f"Unable to connect to Supabase: {exc}")
    st.stop()

# =========================================================
# HELPERS
# =========================================================

def make_unique_id(indent_no, article, color):
    return (
        f"{str(indent_no).strip()} | "
        f"{str(article).strip()} | "
        f"{str(color).strip()}"
    )


def parse_date(value):
    if not value:
        return None

    if isinstance(value, date):
        return value

    try:
        return datetime.strptime(str(value)[:10], "%Y-%m-%d").date()
    except Exception:
        return None


def format_date(value):
    parsed = parse_date(value)
    return parsed.strftime("%d %b %Y") if parsed else "—"


def lead_days(row):
    order_date = parse_date(row.get("order_date"))

    if not order_date:
        return None

    if row.get("status") == "Completed":
        delivered_date = parse_date(row.get("delivered_date"))

        if not delivered_date:
            return None

        return (delivered_date - order_date).days

    return (date.today() - order_date).days


def fetch_samples():
    response = (
        supabase
        .table(TABLE)
        .select("*")
        .execute()
    )
    return response.data or []


def search_rows(rows, query):
    if not query:
        return list(rows)

    query = query.lower().strip()
    result = []

    for row in rows:
        values = [
            row.get("indent_no"),
            row.get("buyer"),
            row.get("article"),
            row.get("color"),
            row.get("supplier"),
            row.get("remarks"),
            row.get("unique_id"),
            row.get("thickness_mm"),
            row.get("status"),
            row.get("delivered_date"),
        ]

        if any(
            query in str(value).lower()
            for value in values
            if value is not None
        ):
            result.append(row)

    return result

# =========================================================
# SHARED SIDEBAR
# =========================================================

def clear_all_filters():
    """Reset all sidebar controls before Streamlit recreates the widgets."""
    st.session_state["global_search"] = ""
    st.session_state["global_buyers"] = []
    st.session_state["global_suppliers"] = []
    st.session_state["global_articles"] = []
    st.session_state["global_colors"] = []
    st.session_state["global_sort_by"] = "Lead Days"
    st.session_state["global_sort_direction"] = "Highest / Newest first"


def sidebar_filters(all_rows):
    buyers = sorted({
        str(row.get("buyer")).strip()
        for row in all_rows
        if row.get("buyer")
    })

    suppliers = sorted({
        str(row.get("supplier")).strip()
        for row in all_rows
        if row.get("supplier")
    })

    articles = sorted({
        str(row.get("article")).strip()
        for row in all_rows
        if row.get("article")
    })

    colors = sorted({
        str(row.get("color")).strip()
        for row in all_rows
        if row.get("color")
    })

    with st.sidebar:
        st.header("🔎 Filters")
        st.caption("Search and filter samples")

        search = st.text_input(
            "Search",
            placeholder="Indent, buyer, article, color...",
            key="global_search",
        )

        st.divider()
        st.markdown("**Filter by**")

        selected_buyers = st.multiselect(
            "Buyer",
            buyers,
            key="global_buyers",
            placeholder="All buyers",
        )

        selected_suppliers = st.multiselect(
            "Supplier",
            suppliers,
            key="global_suppliers",
            placeholder="All suppliers",
        )

        selected_articles = st.multiselect(
            "Article",
            articles,
            key="global_articles",
            placeholder="All articles",
        )

        selected_colors = st.multiselect(
            "Color",
            colors,
            key="global_colors",
            placeholder="All colors",
        )

        st.divider()
        st.subheader("↕ Sorting")

        sort_by = st.selectbox(
            "Sort by",
            [
                "Lead Days",
                "Order Date",
                "Quantity",
                "Buyer",
                "Article",
                "Supplier",
                "Color",
            ],
            key="global_sort_by",
        )

        sort_direction = st.selectbox(
            "Order",
            [
                "Highest / Newest first",
                "Lowest / Oldest first",
            ],
            key="global_sort_direction",
        )

        st.divider()

        st.button(
            "↻ Clear Filters",
            use_container_width=True,
            key="clear_all_filters",
            on_click=clear_all_filters,
        )

    return {
        "search": search,
        "buyers": selected_buyers,
        "suppliers": selected_suppliers,
        "articles": selected_articles,
        "colors": selected_colors,
        "sort_by": sort_by,
        "sort_direction": sort_direction,
    }

# =========================================================
# APPLY FILTERS
# =========================================================

def apply_filters(rows, filters):
    filtered = search_rows(rows, filters["search"])

    if filters["buyers"]:
        filtered = [
            row for row in filtered
            if row.get("buyer") in filters["buyers"]
        ]

    if filters["suppliers"]:
        filtered = [
            row for row in filtered
            if row.get("supplier") in filters["suppliers"]
        ]

    if filters["articles"]:
        filtered = [
            row for row in filtered
            if row.get("article") in filters["articles"]
        ]

    if filters["colors"]:
        filtered = [
            row for row in filtered
            if row.get("color") in filters["colors"]
        ]

    return filtered

# =========================================================
# SORT
# =========================================================

def sort_rows(rows, filters):
    sort_by = filters["sort_by"]
    descending = filters["sort_direction"] == "Highest / Newest first"

    def sort_value(row):
        if sort_by == "Lead Days":
            value = lead_days(row)
            return value if value is not None else -1

        if sort_by == "Order Date":
            value = parse_date(row.get("order_date"))
            return value if value else date.min

        if sort_by == "Quantity":
            try:
                return float(row.get("quantity") or 0)
            except Exception:
                return 0

        if sort_by == "Buyer":
            return str(row.get("buyer") or "").casefold()

        if sort_by == "Article":
            return str(row.get("article") or "").casefold()

        if sort_by == "Supplier":
            return str(row.get("supplier") or "").casefold()

        if sort_by == "Color":
            return str(row.get("color") or "").casefold()

        return ""

    return sorted(rows, key=sort_value, reverse=descending)

# =========================================================
# DATABASE ACTIONS
# =========================================================

def update_remarks(row_id, remarks):
    result = (
        supabase
        .table(TABLE)
        .update({"remarks": remarks.strip()})
        .eq("id", row_id)
        .execute()
    )
    return result.data


def complete_order(row_id, delivered_date):
    result = (
        supabase
        .table(TABLE)
        .update({
            "status": "Completed",
            "delivered_date": delivered_date.isoformat(),
        })
        .eq("id", row_id)
        .execute()
    )
    return result.data

# =========================================================
# DETAILS DIALOG
# =========================================================

@st.dialog("Sample Details", width="large")
def show_sample_details(row):
    row_id = row.get("id")
    article = row.get("article") or "—"
    color = row.get("color") or "—"
    status = row.get("status") or "WIP"

    st.subheader(article)
    st.caption(
        f"{row.get('indent_no', '—')}  •  {color}"
    )

    if status == "WIP":
        st.info("This sample is currently WIP.", icon="🔵")
    else:
        st.success("This sample is Completed.", icon="✅")

    st.markdown("### Sample Information")

    c1, c2, c3 = st.columns(3)
    c1.metric("Buyer", row.get("buyer") or "—")
    c2.metric("Supplier", row.get("supplier") or "—")
    c3.metric("Quantity", f"{int(row.get('quantity') or 0):,}")

    c1, c2, c3 = st.columns(3)
    c1.metric("Thickness", row.get("thickness_mm") or "—")
    c2.metric(
        "Avg. Area",
        f"{float(row.get('avg_area_sdm') or 0):.2f} SDM",
    )

    days = lead_days(row)
    c3.metric(
        "Lead Days",
        f"{days} days" if days is not None else "—",
    )

    c1, c2, c3 = st.columns(3)
    c1.write("**Order Date**")
    c1.write(format_date(row.get("order_date")))

    c2.write("**Delivered Date**")
    c2.write(format_date(row.get("delivered_date")))

    c3.write("**Status**")
    c3.write(status)

    st.caption(f"Unique ID: {row.get('unique_id') or '—'}")

    st.divider()

    # Exactly two actions/options inside the dialog.
    remarks_tab, complete_tab = st.tabs([
        "📝 Update Remarks",
        "✅ Complete Order",
    ])

    with remarks_tab:
        with st.form(f"remarks_form_{row_id}"):
            remarks = st.text_area(
                "Remarks",
                value=row.get("remarks") or "",
                placeholder="Enter remarks...",
                height=140,
            )

            submitted = st.form_submit_button(
                "Update Remarks",
                type="primary",
                use_container_width=True,
            )

        if submitted:
            try:
                result = update_remarks(row_id, remarks)

                if result:
                    st.toast("Remarks updated.")
                    st.rerun()
                else:
                    st.error("No record was updated.")
            except Exception as exc:
                st.error(f"Could not update remarks: {exc}")

    with complete_tab:
        if status == "Completed":
            st.success(
                f"This order was completed on "
                f"{format_date(row.get('delivered_date'))}."
            )
        else:
            st.write("Enter the delivery date to complete this order.")

            with st.form(f"complete_form_{row_id}"):
                delivered_date = st.date_input(
                    "Delivered Date",
                    value=date.today(),
                )

                submitted = st.form_submit_button(
                    "Complete Order",
                    type="primary",
                    use_container_width=True,
                )

            if submitted:
                try:
                    result = complete_order(row_id, delivered_date)

                    if result:
                        st.toast("Sample marked as Completed.")
                        st.rerun()
                    else:
                        st.error("No record was updated.")
                except Exception as exc:
                    st.error(f"Could not complete sample: {exc}")

# =========================================================
# SAMPLE CARD
# =========================================================

def render_sample_card(row):
    row_id = row.get("id")

    article = row.get("article") or "—"
    indent_no = row.get("indent_no") or "—"
    color = row.get("color") or "—"
    buyer = row.get("buyer") or "—"
    supplier = row.get("supplier") or "—"
    thickness = row.get("thickness_mm") or "—"

    try:
        quantity = int(row.get("quantity") or 0)
    except Exception:
        quantity = 0

    try:
        avg_area = float(row.get("avg_area_sdm") or 0)
    except Exception:
        avg_area = 0

    days = lead_days(row)
    status = row.get("status") or "WIP"

    # IMPORTANT:
    # There is intentionally NO key on this container.
    # The database primary key is used only for interactive widgets.
    with st.container(border=True, height=330):
        title_col, status_col, view_col = st.columns(
            [4.5, 1.5, 1],
            vertical_alignment="center",
        )

        with title_col:
            st.markdown(f"### {article}")
            st.caption(f"{indent_no}  •  {color}")

        with status_col:
            if status == "Completed":
                st.badge("Completed", icon=":material/check_circle:")
            else:
                st.badge("WIP", icon=":material/pending:")

        with view_col:
            if st.button(
                "View",
                key=f"view_sample_{row_id}",
                use_container_width=True,
            ):
                show_sample_details(row)

        st.divider()

        # Two balanced rows make the cards more uniform than one
        # five-column row, especially for long supplier/article names.
        c1, c2, c3 = st.columns(3, vertical_alignment="top")

        with c1:
            st.caption("Buyer")
            st.write(buyer)

        with c2:
            st.caption("Supplier")
            st.write(supplier)

        with c3:
            st.caption("Thickness")
            st.write(thickness)

        c1, c2, c3 = st.columns(3, vertical_alignment="top")

        with c1:
            st.caption("Quantity")
            st.write(f"{quantity:,}")

        with c2:
            st.caption("Avg. Area")
            st.write(f"{avg_area:.2f} SDM")

        with c3:
            st.caption("Lead Days")
            st.write(f"{days} days" if days is not None else "—")

# =========================================================
# TABLE
# =========================================================

def display_table(rows):
    display_rows = []

    for row in rows:
        display_rows.append({
            "Indent No.": row.get("indent_no", ""),
            "Order Date": row.get("order_date", ""),
            "Buyer": row.get("buyer", ""),
            "Article": row.get("article", ""),
            "Color": row.get("color", ""),
            "Thickness": row.get("thickness_mm", ""),
            "Avg. Area (SDM)": row.get("avg_area_sdm", ""),
            "Quantity": row.get("quantity", ""),
            "Remarks": row.get("remarks", ""),
            "Supplier": row.get("supplier", ""),
            "Delivered Date": row.get("delivered_date") or "",
            "Status": row.get("status", ""),
            "Lead Days": lead_days(row),
            "Unique ID": row.get("unique_id", ""),
        })

    st.dataframe(
        display_rows,
        use_container_width=True,
        hide_index=True,
        column_config={
            "Avg. Area (SDM)": st.column_config.NumberColumn(
                "Avg. Area (SDM)",
                format="%.2f",
            ),
            "Quantity": st.column_config.NumberColumn(
                "Quantity",
                format="%d",
            ),
            "Lead Days": st.column_config.NumberColumn(
                "Lead Days",
                format="%d",
            ),
        },
    )

# =========================================================
# ADD SAMPLE
# =========================================================

def add_sample_page():
    st.subheader("➕ Add New Sample")
    st.caption("New samples are automatically saved as WIP.")

    with st.form("add_sample_form"):
        c1, c2, c3 = st.columns(3)

        indent_no = c1.text_input(
            "Indent No. *",
            placeholder="Enter indent number",
        )

        order_date = c2.date_input(
            "Order Date *",
            value=date.today(),
        )

        buyer = c3.selectbox(
            "Buyer *",
            BUYERS,
            index=None,
            placeholder="Select or type buyer",
            accept_new_options=True,
        )

        c1, c2, c3 = st.columns(3)

        article = c1.text_input(
            "Article *",
            placeholder="Enter article",
        )

        color = c2.text_input(
            "Color *",
            placeholder="Enter color",
        )

        thickness = c3.text_input(
            "Thickness (mm) *",
            placeholder="e.g. 0.6-0.7",
        )

        c1, c2, c3 = st.columns(3)

        avg_area = c1.number_input(
            "Avg. Area (SDM) *",
            min_value=0.0,
            step=0.01,
            format="%.2f",
        )

        quantity = c2.number_input(
            "Quantity *",
            min_value=0,
            step=1000,
            value=0,
        )

        supplier = c3.selectbox(
            "Supplier *",
            SUPPLIERS,
            index=None,
            placeholder="Select or type supplier",
            accept_new_options=True,
        )

        remarks = st.text_area(
            "Remarks",
            placeholder="Enter remarks if required",
        )

        if indent_no and article and color:
            st.info(
                f"**Unique ID:** "
                f"{make_unique_id(indent_no, article, color)}"
            )

        submitted = st.form_submit_button(
            "➕ Add Sample",
            type="primary",
            use_container_width=True,
        )

        if submitted:
            missing = []

            required = {
                "Indent No.": indent_no,
                "Buyer": buyer,
                "Article": article,
                "Color": color,
                "Thickness (mm)": thickness,
                "Avg. Area (SDM)": avg_area,
                "Quantity": quantity,
                "Supplier": supplier,
            }

            for field, value in required.items():
                if value is None:
                    missing.append(field)
                elif isinstance(value, str) and not value.strip():
                    missing.append(field)
                elif field == "Avg. Area (SDM)" and value <= 0:
                    missing.append(field)
                elif field == "Quantity" and value <= 0:
                    missing.append(field)

            if missing:
                st.error(
                    "Please complete: "
                    + ", ".join(missing)
                    + ". Your existing entries have been retained."
                )
                return

            unique_id = make_unique_id(
                indent_no,
                article,
                color,
            )

            try:
                existing = (
                    supabase
                    .table(TABLE)
                    .select("unique_id")
                    .eq("unique_id", unique_id)
                    .execute()
                )

                if existing.data:
                    st.error(
                        f"This sample already exists: {unique_id}"
                    )
                    return

                payload = {
                    "indent_no": indent_no.strip(),
                    "order_date": order_date.isoformat(),
                    "buyer": str(buyer).strip(),
                    "article": article.strip(),
                    "color": color.strip(),
                    "thickness_mm": thickness.strip(),
                    "avg_area_sdm": avg_area,
                    "quantity": int(quantity),
                    "remarks": remarks.strip(),
                    "supplier": str(supplier).strip(),
                    "delivered_date": None,
                    "status": "WIP",
                    "unique_id": unique_id,
                }

                result = (
                    supabase
                    .table(TABLE)
                    .insert(payload)
                    .execute()
                )

                if result.data:
                    st.success("Sample added successfully.")
                    st.rerun()
                else:
                    st.error("Sample could not be added.")

            except Exception as exc:
                st.error(f"Could not save sample: {exc}")

# =========================================================
# LOAD DATA
# =========================================================

try:
    all_rows = fetch_samples()
except Exception as exc:
    st.error(f"Unable to load data from Supabase: {exc}")
    st.stop()

# =========================================================
# SHARED SIDEBAR
# IMPORTANT: Called exactly ONCE.
# =========================================================

filters = sidebar_filters(all_rows)

# =========================================================
# SPLIT + FILTER + SORT
# =========================================================

wip_rows = [
    row for row in all_rows
    if row.get("status") == "WIP"
]

completed_rows = [
    row for row in all_rows
    if row.get("status") == "Completed"
]

filtered_wip = sort_rows(
    apply_filters(wip_rows, filters),
    filters,
)

filtered_completed = sort_rows(
    apply_filters(completed_rows, filters),
    filters,
)

# =========================================================
# HEADER
# =========================================================

st.title("🧪 Sample Management")
st.caption("Track sample orders from WIP to completion.")

# =========================================================
# TABS
# =========================================================

tab_wip, tab_completed, tab_add = st.tabs([
    f"📋 Sample WIP · {len(wip_rows)}",
    f"✅ Sample Completed · {len(completed_rows)}",
    "➕ Add Sample",
])

# =========================================================
# WIP TAB
# =========================================================

with tab_wip:
    lead_values = [
        lead_days(row)
        for row in filtered_wip
        if lead_days(row) is not None
    ]

    c1, c2, c3, c4 = st.columns(4)

    c1.metric("WIP Samples", len(filtered_wip))
    c2.metric(
        "Total Quantity",
        f"{sum(int(row.get('quantity') or 0) for row in filtered_wip):,}",
    )
    c3.metric(
        "Average Lead Days",
        round(sum(lead_values) / len(lead_values), 1)
        if lead_values else 0,
    )
    c4.metric(
        "Suppliers",
        len({
            row.get("supplier")
            for row in filtered_wip
            if row.get("supplier")
        }),
    )

    st.divider()

    st.subheader(f"Samples · {len(filtered_wip)}")
    st.caption(
        f"Sorted by {filters['sort_by']} · "
        f"{filters['sort_direction']}"
    )

    if filtered_wip:
        for i in range(0, len(filtered_wip), 2):
            columns = st.columns(2, gap="medium")

            for column, row in zip(
                columns,
                filtered_wip[i:i + 2],
            ):
                with column:
                    render_sample_card(row)
    else:
        st.info("No WIP samples match the selected filters.")

    st.divider()

    with st.expander("📊 View WIP Table", expanded=False):
        if filtered_wip:
            display_table(filtered_wip)
        else:
            st.info("No data to display.")

# =========================================================
# COMPLETED TAB
# =========================================================

with tab_completed:
    lead_values = [
        lead_days(row)
        for row in filtered_completed
        if lead_days(row) is not None
    ]

    c1, c2, c3, c4 = st.columns(4)

    c1.metric("Completed Samples", len(filtered_completed))
    c2.metric(
        "Total Quantity",
        f"{sum(int(row.get('quantity') or 0) for row in filtered_completed):,}",
    )
    c3.metric(
        "Average Lead Days",
        round(sum(lead_values) / len(lead_values), 1)
        if lead_values else 0,
    )
    c4.metric(
        "Buyers",
        len({
            row.get("buyer")
            for row in filtered_completed
            if row.get("buyer")
        }),
    )

    st.divider()

    st.subheader(f"Completed Samples · {len(filtered_completed)}")
    st.caption(
        f"Sorted by {filters['sort_by']} · "
        f"{filters['sort_direction']}"
    )

    if filtered_completed:
        for i in range(0, len(filtered_completed), 2):
            columns = st.columns(2, gap="medium")

            for column, row in zip(
                columns,
                filtered_completed[i:i + 2],
            ):
                with column:
                    render_sample_card(row)
    else:
        st.info("No completed samples match the selected filters.")

    st.divider()

    with st.expander("📊 View Completed Table", expanded=False):
        if filtered_completed:
            display_table(filtered_completed)
        else:
            st.info("No data to display.")

# =========================================================
# ADD SAMPLE TAB
# =========================================================

with tab_add:
    add_sample_page()

# =========================================================
# FOOTER
# =========================================================

st.divider()
st.caption("Sample Management • Streamlit + Supabase")
