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
        return datetime.strptime(
            str(value)[:10],
            "%Y-%m-%d"
        ).date()

    except Exception:
        return None


def format_date(value):

    parsed = parse_date(value)

    if not parsed:
        return "—"

    return parsed.strftime("%d %b %Y")


def lead_days(row):

    order_date = parse_date(
        row.get("order_date")
    )

    if not order_date:
        return None

    if row.get("status") == "Completed":

        delivered_date = parse_date(
            row.get("delivered_date")
        )

        if not delivered_date:
            return None

        return (
            delivered_date - order_date
        ).days

    return (
        date.today() - order_date
    ).days


def fetch_samples():

    response = (
        supabase
        .table(TABLE)
        .select("*")
        .order(
            "order_date",
            desc=True
        )
        .execute()
    )

    return response.data or []


def search_rows(rows, query):

    if not query:
        return rows

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
        ]

        if any(
            query in str(value).lower()
            for value in values
            if value is not None
        ):
            result.append(row)

    return result


# =========================================================
# FILTERS
# =========================================================

def apply_sidebar_filters(rows, prefix):

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


    # -----------------------------------------------------
    # SIDEBAR
    # -----------------------------------------------------

    with st.sidebar:

        st.header("🔎 Filters")

        st.caption(
            "Use the filters below to narrow the sample list."
        )

        search = st.text_input(
            "Search",
            placeholder=(
                "Indent, buyer, article, color..."
            ),
            key=f"{prefix}_search",
        )

        st.divider()

        selected_buyers = st.multiselect(
            "Buyer",
            buyers,
            key=f"{prefix}_buyers",
            placeholder="All buyers",
        )

        selected_suppliers = st.multiselect(
            "Supplier",
            suppliers,
            key=f"{prefix}_suppliers",
            placeholder="All suppliers",
        )

        selected_articles = st.multiselect(
            "Article",
            articles,
            key=f"{prefix}_articles",
            placeholder="All articles",
        )

        selected_colors = st.multiselect(
            "Color",
            colors,
            key=f"{prefix}_colors",
            placeholder="All colors",
        )

        st.divider()

        if st.button(
            "↺ Clear Filters",
            use_container_width=True,
            key=f"{prefix}_clear",
        ):

            st.session_state[f"{prefix}_search"] = ""
            st.session_state[f"{prefix}_buyers"] = []
            st.session_state[f"{prefix}_suppliers"] = []
            st.session_state[f"{prefix}_articles"] = []
            st.session_state[f"{prefix}_colors"] = []

            st.rerun()


    # -----------------------------------------------------
    # APPLY SEARCH
    # -----------------------------------------------------

    filtered = search_rows(
        rows,
        search
    )


    # -----------------------------------------------------
    # APPLY BUYER
    # -----------------------------------------------------

    if selected_buyers:

        filtered = [
            row
            for row in filtered
            if row.get("buyer") in selected_buyers
        ]


    # -----------------------------------------------------
    # APPLY SUPPLIER
    # -----------------------------------------------------

    if selected_suppliers:

        filtered = [
            row
            for row in filtered
            if row.get("supplier") in selected_suppliers
        ]


    # -----------------------------------------------------
    # APPLY ARTICLE
    # -----------------------------------------------------

    if selected_articles:

        filtered = [
            row
            for row in filtered
            if row.get("article") in selected_articles
        ]


    # -----------------------------------------------------
    # APPLY COLOR
    # -----------------------------------------------------

    if selected_colors:

        filtered = [
            row
            for row in filtered
            if row.get("color") in selected_colors
        ]


    return filtered


# =========================================================
# UPDATE REMARKS
# =========================================================

def update_remarks(unique_id, remarks):

    result = (
        supabase
        .table(TABLE)
        .update({
            "remarks": remarks.strip()
        })
        .eq(
            "unique_id",
            unique_id
        )
        .execute()
    )

    return result.data


# =========================================================
# COMPLETE SAMPLE
# =========================================================

def complete_order(unique_id, delivered_date):

    result = (
        supabase
        .table(TABLE)
        .update({
            "status": "Completed",
            "delivered_date": delivered_date.isoformat(),
        })
        .eq(
            "unique_id",
            unique_id
        )
        .execute()
    )

    return result.data


# =========================================================
# SAMPLE DETAILS DIALOG
# =========================================================

@st.dialog(
    "Sample Details",
    width="large",
)
def show_sample_details(row):

    indent_no = row.get(
        "indent_no",
        ""
    )

    article = row.get(
        "article",
        ""
    )

    color = row.get(
        "color",
        ""
    )

    unique_id = row.get(
        "unique_id",
        ""
    )

    status = row.get(
        "status",
        "WIP"
    )


    # -----------------------------------------------------
    # HEADER
    # -----------------------------------------------------

    st.subheader(
        f"{article}"
    )

    st.caption(
        f"{indent_no}  •  {color}"
    )


    # -----------------------------------------------------
    # STATUS
    # -----------------------------------------------------

    if status == "WIP":

        st.info(
            "🔵 This sample is currently WIP."
        )

    else:

        st.success(
            "✅ This sample is Completed."
        )


    # -----------------------------------------------------
    # SAMPLE INFORMATION
    # -----------------------------------------------------

    st.markdown("### Sample Information")


    c1, c2, c3 = st.columns(3)

    c1.write("**Indent No.**")
    c1.write(indent_no)

    c2.write("**Order Date**")
    c2.write(
        format_date(
            row.get("order_date")
        )
    )

    c3.write("**Buyer**")
    c3.write(
        row.get("buyer") or "—"
    )


    c1, c2, c3 = st.columns(3)

    c1.write("**Article**")
    c1.write(article)

    c2.write("**Color**")
    c2.write(color)

    c3.write("**Thickness**")
    c3.write(
        row.get("thickness_mm")
        or "—"
    )


    c1, c2, c3 = st.columns(3)

    c1.write("**Average Area**")
    c1.write(
        f"{float(row.get('avg_area_sdm') or 0):.2f} SDM"
    )

    c2.write("**Quantity**")
    c2.write(
        f"{int(row.get('quantity') or 0):,}"
    )

    c3.write("**Supplier**")
    c3.write(
        row.get("supplier") or "—"
    )


    c1, c2, c3 = st.columns(3)

    c1.write("**Order Date**")
    c1.write(
        format_date(
            row.get("order_date")
        )
    )

    c2.write("**Delivered Date**")
    c2.write(
        format_date(
            row.get("delivered_date")
        )
    )

    c3.write("**Lead Days**")

    days = lead_days(row)

    c3.write(
        f"{days} days"
        if days is not None
        else "—"
    )


    st.divider()


    # =====================================================
    # OPTION 1 — UPDATE REMARKS
    # =====================================================

    st.markdown("### 📝 Update Remarks")

    current_remarks = (
        row.get("remarks")
        or ""
    )

    remarks = st.text_area(
        "Remarks",
        value=current_remarks,
        placeholder="Enter sample remarks...",
        key=f"remarks_{unique_id}",
    )


    if st.button(
        "💾 Update Remarks",
        type="secondary",
        use_container_width=True,
        key=f"update_remarks_{unique_id}",
    ):

        try:

            updated = update_remarks(
                unique_id,
                remarks
            )

            if updated:

                st.success(
                    "Remarks updated successfully."
                )

                st.rerun()

            else:

                st.error(
                    "No record was updated."
                )

        except Exception as exc:

            st.error(
                f"Could not update remarks: {exc}"
            )


    # =====================================================
    # OPTION 2 — COMPLETE ORDER
    # =====================================================

    if status == "WIP":

        st.divider()

        st.markdown(
            "### ✅ Complete Order"
        )

        st.caption(
            "Select the date on which the sample was delivered."
        )

        delivered_date = st.date_input(
            "Delivered Date",
            value=date.today(),
            key=f"delivered_{unique_id}",
        )


        if st.button(
            "✅ Complete Order",
            type="primary",
            use_container_width=True,
            key=f"complete_{unique_id}",
        ):

            try:

                updated = complete_order(
                    unique_id,
                    delivered_date
                )

                if updated:

                    st.success(
                        "Sample marked as Completed."
                    )

                    st.rerun()

                else:

                    st.error(
                        "No record was updated."
                    )

            except Exception as exc:

                st.error(
                    f"Could not complete sample: {exc}"
                )


# =========================================================
# SAMPLE CARD
# =========================================================

def render_sample_card(row, card_number):

    unique_id = row.get(
        "unique_id",
        f"sample_{card_number}"
    )

    article = row.get(
        "article",
        "—"
    )

    color = row.get(
        "color",
        "—"
    )

    indent_no = row.get(
        "indent_no",
        "—"
    )

    buyer = row.get(
        "buyer",
        "—"
    )

    supplier = row.get(
        "supplier",
        "—"
    )

    quantity = int(
        row.get("quantity") or 0
    )

    avg_area = float(
        row.get("avg_area_sdm") or 0
    )

    thickness = row.get(
        "thickness_mm",
        "—"
    )

    remarks = row.get(
        "remarks"
    )

    days = lead_days(row)


    # -----------------------------------------------------
    # CARD
    # -----------------------------------------------------

    with st.container(
        border=True
    ):

        # -------------------------------------------------
        # CARD HEADER
        # -------------------------------------------------

        top_left, top_middle, top_right = st.columns(
            [4, 2, 1],
            vertical_alignment="center",
        )


        with top_left:

            st.subheader(
                article
            )

            st.caption(
                f"{indent_no}  •  {color}"
            )


        with top_middle:

            if row.get("status") == "WIP":

                st.info(
                    "WIP",
                    icon="🔵"
                )

            else:

                st.success(
                    "Completed",
                    icon="✅"
                )


        with top_right:

            if st.button(
                "View Details",
                key=f"details_{unique_id}",
                use_container_width=True,
            ):

                show_sample_details(row)


        # -------------------------------------------------
        # MAIN DETAILS
        # -------------------------------------------------

        st.divider()


        c1, c2, c3, c4, c5 = st.columns(
            5,
            vertical_alignment="center",
        )


        with c1:

            st.caption("Buyer")
            st.write(buyer)


        with c2:

            st.caption("Supplier")
            st.write(supplier)


        with c3:

            st.caption("Thickness")
            st.write(thickness)


        with c4:

            st.caption("Quantity")
            st.write(
                f"{quantity:,}"
            )


        with c5:

            st.caption("Lead Days")

            if days is not None:

                st.write(
                    f"{days} days"
                )

            else:

                st.write("—")


        # -------------------------------------------------
        # REMARKS
        # -------------------------------------------------

        if remarks:

            st.divider()

            st.caption("Remarks")

            st.write(
                remarks
            )


# =========================================================
# TABLE
# =========================================================

def display_table(rows, key):

    display_rows = []

    for row in rows:

        display_rows.append({

            "Indent No.": row.get(
                "indent_no",
                ""
            ),

            "Order Date": row.get(
                "order_date",
                ""
            ),

            "Buyer": row.get(
                "buyer",
                ""
            ),

            "Article": row.get(
                "article",
                ""
            ),

            "Color": row.get(
                "color",
                ""
            ),

            "Thickness": row.get(
                "thickness_mm",
                ""
            ),

            "Avg. Area (SDM)": row.get(
                "avg_area_sdm",
                ""
            ),

            "Quantity": row.get(
                "quantity",
                ""
            ),

            "Remarks": row.get(
                "remarks",
                ""
            ),

            "Supplier": row.get(
                "supplier",
                ""
            ),

            "Delivered Date": row.get(
                "delivered_date"
            ) or "",

            "Status": row.get(
                "status",
                ""
            ),

            "Lead Days": lead_days(
                row
            ),

            "Unique ID": row.get(
                "unique_id",
                ""
            ),
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

        key=key,
    )


# =========================================================
# ADD SAMPLE
# =========================================================

def add_sample_page():

    st.subheader(
        "➕ Add New Sample"
    )

    st.caption(
        "New samples are automatically saved as WIP."
    )


    with st.form(
        "add_sample_form"
    ):

        c1, c2, c3 = st.columns(3)


        with c1:

            indent_no = st.text_input(
                "Indent No. *",
                placeholder="Enter indent number",
            )


        with c2:

            order_date = st.date_input(
                "Order Date *",
                value=date.today(),
            )


        with c3:

            buyer = st.selectbox(
                "Buyer *",
                BUYERS,
                index=None,
                placeholder="Select or type buyer",
                accept_new_options=True,
            )


        c1, c2, c3 = st.columns(3)


        with c1:

            article = st.text_input(
                "Article *",
                placeholder="Enter article",
            )


        with c2:

            color = st.text_input(
                "Color *",
                placeholder="Enter color",
            )


        with c3:

            thickness = st.text_input(
                "Thickness (mm) *",
                placeholder="e.g. 0.6-0.7",
            )


        c1, c2, c3 = st.columns(3)


        with c1:

            avg_area = st.number_input(
                "Avg. Area (SDM) *",
                min_value=0.0,
                step=0.01,
                format="%.2f",
            )


        with c2:

            quantity = st.number_input(
                "Quantity *",
                min_value=0,
                step=1000,
                value=0,
            )


        with c3:

            supplier = st.selectbox(
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


        if (
            indent_no
            and article
            and color
        ):

            unique_id_preview = make_unique_id(
                indent_no,
                article,
                color
            )

            st.info(
                f"**Unique ID:** {unique_id_preview}"
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

                elif (
                    isinstance(value, str)
                    and not value.strip()
                ):

                    missing.append(field)

                elif (
                    field == "Avg. Area (SDM)"
                    and value <= 0
                ):

                    missing.append(field)

                elif (
                    field == "Quantity"
                    and value <= 0
                ):

                    missing.append(field)


            if missing:

                st.error(
                    "Please complete: "
                    + ", ".join(missing)
                    + ". Your entered values have been retained."
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
                        .eq(
                            "unique_id",
                            unique_id
                        )
                        .execute()
                    )


                    if existing.data:

                        st.error(
                            f"This sample already exists: "
                            f"{unique_id}"
                        )


                    else:

                        payload = {

                            "indent_no":
                                indent_no.strip(),

                            "order_date":
                                order_date.isoformat(),

                            "buyer":
                                str(buyer).strip(),

                            "article":
                                article.strip(),

                            "color":
                                color.strip(),

                            "thickness_mm":
                                thickness.strip(),

                            "avg_area_sdm":
                                avg_area,

                            "quantity":
                                int(quantity),

                            "remarks":
                                remarks.strip(),

                            "supplier":
                                str(supplier).strip(),

                            "delivered_date":
                                None,

                            "status":
                                "WIP",

                            "unique_id":
                                unique_id,
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


# =========================================================
# LOAD DATA
# =========================================================

try:

    all_rows = fetch_samples()

except Exception as exc:

    st.error(
        f"Unable to load data from Supabase: {exc}"
    )

    st.stop()


wip_rows = [
    row
    for row in all_rows
    if row.get("status") == "WIP"
]


completed_rows = [
    row
    for row in all_rows
    if row.get("status") == "Completed"
]


# =========================================================
# HEADER
# =========================================================

st.title(
    "🧪 Sample Management"
)

st.caption(
    "Track sample orders from WIP to completion."
)


# =========================================================
# TABS
# =========================================================

tab_wip, tab_completed, tab_add = st.tabs(
    [
        f"📋 Sample WIP  ·  {len(wip_rows)}",
        f"✅ Sample Completed  ·  {len(completed_rows)}",
        "➕ Add Sample",
    ]
)


# =========================================================
# WIP TAB
# =========================================================

with tab_wip:

    filtered_wip = apply_sidebar_filters(
        wip_rows,
        "wip"
    )


    # -----------------------------------------------------
    # SUMMARY
    # -----------------------------------------------------

    lead_values = [
        lead_days(row)
        for row in filtered_wip
        if lead_days(row) is not None
    ]


    c1, c2, c3, c4 = st.columns(4)


    c1.metric(
        "WIP Samples",
        len(filtered_wip)
    )


    c2.metric(
        "Total Quantity",
        f"{sum(int(row.get('quantity') or 0) for row in filtered_wip):,}"
    )


    c3.metric(
        "Average Lead Days",
        round(
            sum(lead_values) / len(lead_values),
            1
        )
        if lead_values
        else 0
    )


    c4.metric(
        "Suppliers",
        len({
            row.get("supplier")
            for row in filtered_wip
            if row.get("supplier")
        })
    )


    st.divider()


    # -----------------------------------------------------
    # SAMPLE CARDS
    # -----------------------------------------------------

    if filtered_wip:

        st.subheader(
            f"Samples · {len(filtered_wip)}"
        )

        st.caption(
            "Select a sample card to view details, update remarks or complete the order."
        )


        # 2 cards per row

        for i in range(
            0,
            len(filtered_wip),
            2
        ):

            columns = st.columns(
                2,
                gap="medium"
            )


            for column, row in zip(
                columns,
                filtered_wip[i:i + 2]
            ):

                with column:

                    render_sample_card(
                        row,
                        i
                    )


    else:

        st.info(
            "No WIP samples match the selected filters."
        )


    # -----------------------------------------------------
    # TABLE AT BOTTOM
    # -----------------------------------------------------

    st.divider()

    with st.expander(
        "📊 View WIP Table",
        expanded=False
    ):

        if filtered_wip:

            display_table(
                filtered_wip,
                "wip_table"
            )

        else:

            st.info(
                "No data to display."
            )


# =========================================================
# COMPLETED TAB
# =========================================================

with tab_completed:

    filtered_completed = apply_sidebar_filters(
        completed_rows,
        "completed"
    )


    # -----------------------------------------------------
    # SUMMARY
    # -----------------------------------------------------

    lead_values = [
        lead_days(row)
        for row in filtered_completed
        if lead_days(row) is not None
    ]


    c1, c2, c3, c4 = st.columns(4)


    c1.metric(
        "Completed Samples",
        len(filtered_completed)
    )


    c2.metric(
        "Total Quantity",
        f"{sum(int(row.get('quantity') or 0) for row in filtered_completed):,}"
    )


    c3.metric(
        "Average Lead Days",
        round(
            sum(lead_values) / len(lead_values),
            1
        )
        if lead_values
        else 0
    )


    c4.metric(
        "Buyers",
        len({
            row.get("buyer")
            for row in filtered_completed
            if row.get("buyer")
        })
    )


    st.divider()


    # -----------------------------------------------------
    # COMPLETED CARDS
    # -----------------------------------------------------

    if filtered_completed:

        st.subheader(
            f"Completed Samples · {len(filtered_completed)}"
        )

        st.caption(
            "Select a sample to view its complete details."
        )


        for i in range(
            0,
            len(filtered_completed),
            2
        ):

            columns = st.columns(
                2,
                gap="medium"
            )


            for column, row in zip(
                columns,
                filtered_completed[i:i + 2]
            ):

                with column:

                    render_sample_card(
                        row,
                        f"completed_{i}"
                    )


    else:

        st.info(
            "No completed samples match the selected filters."
        )


    # -----------------------------------------------------
    # TABLE AT BOTTOM
    # -----------------------------------------------------

    st.divider()

    with st.expander(
        "📊 View Completed Table",
        expanded=False
    ):

        if filtered_completed:

            display_table(
                filtered_completed,
                "completed_table"
            )

        else:

            st.info(
                "No data to display."
            )


# =========================================================
# ADD SAMPLE TAB
# =========================================================

with tab_add:

    # Hide the sidebar filters on Add Sample page
    # by simply showing the form in the main area.

    add_sample_page()


# =========================================================
# FOOTER
# =========================================================

st.divider()

st.caption(
    "Sample Management • Streamlit + Supabase"
)
