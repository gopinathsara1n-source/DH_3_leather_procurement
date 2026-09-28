import streamlit as st
from supabase import create_client, Client
from datetime import date, datetime

st.set_page_config(
    page_title="Sample Management",
    page_icon="🧪",
    layout="wide",
)

TABLE = "samples"


@st.cache_resource
def get_supabase() -> Client:
    return create_client(
        st.secrets["SUPABASE_URL"],
        st.secrets["SUPABASE_KEY"],
    )


supabase = get_supabase()


def make_unique_id(indent_no, article, color):
    return f"{str(indent_no).strip()} | {str(article).strip()} | {str(color).strip()}"


def parse_date(value):
    if not value:
        return None
    if isinstance(value, date):
        return value
    return datetime.strptime(str(value)[:10], "%Y-%m-%d").date()


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
        .order("order_date", desc=True)
        .execute()
    )
    return response.data or []


def search_rows(rows, query):
    if not query:
        return rows

    q = query.lower().strip()
    result = []

    for row in rows:
        searchable_values = [
            row.get("indent_no"),
            row.get("buyer"),
            row.get("article"),
            row.get("color"),
            row.get("supplier"),
            row.get("remarks"),
            row.get("unique_id"),
        ]

        if any(
            q in str(value).lower()
            for value in searchable_values
            if value is not None
        ):
            result.append(row)

    return result


def apply_filters(rows, key_prefix):
    buyers = sorted({
        str(row.get("buyer")).strip()
        for row in rows
        if row.get("buyer")
    })

    suppliers = sorted({
        str(row.get("supplier")).strip()
        for row in rows
        if row.get("supplier")
    })

    articles = sorted({
        str(row.get("article")).strip()
        for row in rows
        if row.get("article")
    })

    colors = sorted({
        str(row.get("color")).strip()
        for row in rows
        if row.get("color")
    })

    with st.expander("🔎 Filters", expanded=False):
        c1, c2, c3, c4 = st.columns(4)

        selected_buyers = c1.multiselect(
            "Buyer",
            buyers,
            key=f"{key_prefix}_buyer",
        )

        selected_suppliers = c2.multiselect(
            "Supplier",
            suppliers,
            key=f"{key_prefix}_supplier",
        )

        selected_articles = c3.multiselect(
            "Article",
            articles,
            key=f"{key_prefix}_article",
        )

        selected_colors = c4.multiselect(
            "Color",
            colors,
            key=f"{key_prefix}_color",
        )

    filtered = rows

    if selected_buyers:
        filtered = [
            row for row in filtered
            if row.get("buyer") in selected_buyers
        ]

    if selected_suppliers:
        filtered = [
            row for row in filtered
            if row.get("supplier") in selected_suppliers
        ]

    if selected_articles:
        filtered = [
            row for row in filtered
            if row.get("article") in selected_articles
        ]

    if selected_colors:
        filtered = [
            row for row in filtered
            if row.get("color") in selected_colors
        ]

    return filtered


def display_table(rows, key):
    display_rows = []

    for row in rows:
        display_rows.append({
            "Indent No.": row.get("indent_no", ""),
            "Order Date": row.get("order_date", ""),
            "Buyer": row.get("buyer", ""),
            "Article": row.get("article", ""),
            "Color": row.get("color", ""),
            "Thickness (mm)": row.get("thickness_mm", ""),
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
            "Thickness (mm)": st.column_config.NumberColumn(
                "Thickness (mm)",
                format="%.2f",
            ),
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
        key=key,
    )


def complete_sample(rows):
    wip_rows = [
        row for row in rows
        if row.get("status") == "WIP"
    ]

    if not wip_rows:
        return

    st.divider()
    st.subheader("✅ Complete a Sample")

    options = {
        f"{row['indent_no']} | {row['article']} | {row['color']}":
            row["unique_id"]
        for row in wip_rows
    }

    c1, c2, c3 = st.columns([2, 1, 1])

    selected_label = c1.selectbox(
        "Select sample",
        list(options.keys()),
        key="complete_sample_select",
    )

    delivered_date = c2.date_input(
        "Delivered Date",
        value=date.today(),
        key="complete_delivered_date",
    )

    if c3.button(
        "Mark Completed",
        type="primary",
        use_container_width=True,
        key="mark_completed",
    ):
        unique_id = options[selected_label]

        try:
            result = (
                supabase
                .table(TABLE)
                .update({
                    "status": "Completed",
                    "delivered_date": delivered_date.isoformat(),
                })
                .eq("unique_id", unique_id)
                .execute()
            )

            if result.data:
                st.success("Sample marked as Completed.")
                st.rerun()
            else:
                st.error("No record was updated.")

        except Exception as exc:
            st.error(f"Could not update sample: {exc}")


# -------------------------------------------------------------------
# PAGE
# -------------------------------------------------------------------

st.title("🧪 Sample Management")
st.caption(
    "Track sample orders, WIP samples, completed samples and lead time."
)

try:
    all_rows = fetch_samples()
except Exception as exc:
    st.error(f"Unable to load data from Supabase: {exc}")
    st.stop()


wip_rows = [
    row for row in all_rows
    if row.get("status") == "WIP"
]

completed_rows = [
    row for row in all_rows
    if row.get("status") == "Completed"
]


# Global search
search = st.text_input(
    "🔍 Search",
    placeholder=(
        "Search Indent No., Buyer, Article, Color, Supplier, "
        "Remarks or Unique ID..."
    ),
)


tab_wip, tab_completed, tab_add = st.tabs([
    f"📋 Sample ({len(wip_rows)})",
    f"✅ Sample Completed ({len(completed_rows)})",
    "➕ Add Sample",
])


# -------------------------------------------------------------------
# WIP TAB
# -------------------------------------------------------------------

with tab_wip:
    st.subheader("Sample — WIP")

    filtered = search_rows(wip_rows, search)
    filtered = apply_filters(filtered, "wip")

    lead_values = [
        lead_days(row)
        for row in filtered
        if lead_days(row) is not None
    ]

    c1, c2, c3, c4 = st.columns(4)

    c1.metric("WIP Samples", len(filtered))

    c2.metric(
        "Total Quantity",
        sum(int(row.get("quantity") or 0) for row in filtered),
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
            for row in filtered
            if row.get("supplier")
        }),
    )

    if filtered:
        display_table(filtered, "wip_table")
        complete_sample(filtered)
    else:
        st.info("No WIP samples found.")


# -------------------------------------------------------------------
# COMPLETED TAB
# -------------------------------------------------------------------

with tab_completed:
    st.subheader("Sample Completed")

    filtered = search_rows(completed_rows, search)
    filtered = apply_filters(filtered, "completed")

    lead_values = [
        lead_days(row)
        for row in filtered
        if lead_days(row) is not None
    ]

    c1, c2, c3, c4 = st.columns(4)

    c1.metric("Completed Samples", len(filtered))

    c2.metric(
        "Total Quantity",
        sum(int(row.get("quantity") or 0) for row in filtered),
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
            for row in filtered
            if row.get("buyer")
        }),
    )

    if filtered:
        display_table(filtered, "completed_table")
    else:
        st.info("No completed samples found.")


# -------------------------------------------------------------------
# ADD SAMPLE TAB
# -------------------------------------------------------------------

with tab_add:
    st.subheader("➕ Add New Sample")
    st.caption("Every newly created sample starts with status = WIP.")

    with st.form("add_sample_form", clear_on_submit=True):

        c1, c2, c3 = st.columns(3)

        indent_no = c1.text_input("Indent No. *")
        order_date = c2.date_input(
            "Order Date *",
            value=date.today(),
        )
        buyer = c3.text_input("Buyer *")

        c1, c2, c3 = st.columns(3)

        article = c1.text_input("Article *")
        color = c2.text_input("Color *")
        thickness = c3.number_input(
            "Thickness (mm) *",
            min_value=0.0,
            step=0.01,
            format="%.2f",
        )

        c1, c2, c3 = st.columns(3)

        avg_area = c1.number_input(
            "Avg. Area (SDM)",
            min_value=0.0,
            step=0.01,
            format="%.2f",
        )

        quantity = c2.number_input(
            "Quantity *",
            min_value=1,
            step=1,
        )

        supplier = c3.text_input("Supplier *")

        remarks = st.text_area("Remarks")

        unique_id_preview = make_unique_id(
            indent_no,
            article,
            color,
        )

        st.info(f"**Unique ID:** {unique_id_preview}")

        submitted = st.form_submit_button(
            "➕ Add Sample",
            type="primary",
            use_container_width=True,
        )

        if submitted:

            required = {
                "Indent No.": indent_no,
                "Buyer": buyer,
                "Article": article,
                "Color": color,
                "Supplier": supplier,
            }

            missing = [
                field
                for field, value in required.items()
                if not str(value).strip()
            ]

            if missing:
                st.error(
                    "Please fill: " + ", ".join(missing)
                )

            else:
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
                    else:
                        payload = {
                            "indent_no": indent_no.strip(),
                            "order_date": order_date.isoformat(),
                            "buyer": buyer.strip(),
                            "article": article.strip(),
                            "color": color.strip(),
                            "thickness_mm": thickness,
                            "avg_area_sdm": avg_area,
                            "quantity": int(quantity),
                            "remarks": remarks.strip(),
                            "supplier": supplier.strip(),
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
                            st.success(
                                "Sample added successfully."
                            )
                            st.rerun()
                        else:
                            st.error(
                                "Sample could not be added."
                            )

                except Exception as exc:
                    st.error(
                        f"Could not save sample: {exc}"
                    )


st.divider()
st.caption("Sample Management • Streamlit + Supabase")
