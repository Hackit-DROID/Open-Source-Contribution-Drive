# app.py
import os
import io
import json
from pathlib import Path
from dotenv import load_dotenv

# Ensure environment variables from .env files are loaded
current_dir = Path(__file__).resolve().parent
load_dotenv(current_dir / ".env")
load_dotenv(current_dir.parent / ".env")

import streamlit as st
import pandas as pd
import plotly.express as px

# Safe module-level imports
import extract_data
import store_data
from store_data import DB_PATH
import reports

# Page Setup
st.set_page_config(
    page_title="DeepLearning Invoice Extractor Pro",
    page_icon="🧾",
    layout="wide"
)

# Custom Styling
st.markdown("""
<style>
    .main-header {
        font-size: 2.2rem;
        font-weight: 700;
        color: #1E293B;
        margin-bottom: 0.2rem;
    }
    .sub-header {
        color: #64748B;
        font-size: 1.0rem;
        margin-bottom: 1.5rem;
    }
    .badge-paid {
        background-color: #DCFCE7;
        color: #166534;
        padding: 3px 8px;
        border-radius: 4px;
        font-weight: 600;
    }
    .badge-pending {
        background-color: #FEF3C7;
        color: #92400E;
        padding: 3px 8px;
        border-radius: 4px;
        font-weight: 600;
    }
    .badge-overdue {
        background-color: #FEE2E2;
        color: #991B1B;
        padding: 3px 8px;
        border-radius: 4px;
        font-weight: 600;
    }
</style>
""", unsafe_allow_html=True)

# Ensure DB initialized
store_data.init_db(DB_PATH)

# Retrieve keys safely with fallbacks
groq_key = getattr(extract_data, "get_groq_key", lambda: os.getenv("GROQ_API_KEY"))() or os.getenv("GROQ_API_KEY")
gemini_key = getattr(extract_data, "get_gemini_key", lambda: os.getenv("GEMINI_API_KEY"))() or os.getenv("GEMINI_API_KEY")

# Sidebar
with st.sidebar:
    st.header("⚙️ Settings & Models")
    
    if groq_key:
        st.success("✅ Groq Connected")
        model_choice = st.selectbox(
            "Groq LLM Model",
            ["openai/gpt-oss-20b", "qwen/qwen3.8-27b", "openai/gpt-oss-120b"],
            index=0
        )
    elif gemini_key:
        st.success("✅ Gemini Connected")
        model_choice = "gemini-2.5-flash"
    else:
        st.warning("⚠️ No API Key found in .env")
        model_choice = "openai/gpt-oss-20b"

    st.markdown("---")
    st.subheader("💡 Key Capabilities")
    st.markdown("""
    - **Rich Schema**: Invoice #, dates, taxes, vendor, line items
    - **Human-in-the-Loop**: Edit & correct data in real time
    - **Multi-Format Export**: CSV and Excel (.xlsx) with line item sheets
    - **Analytics**: Monthly spending trends & status metrics
    """)

# Main Title
st.markdown('<div class="main-header">🧾 DeepLearning Invoice Extractor Pro</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-header">AI-powered invoice extraction with line-item breakdown, fraud/duplicate checks, interactive editor, and financial reporting.</div>', unsafe_allow_html=True)

# Tabs
tab1, tab2, tab3, tab4 = st.tabs([
    "📤 Upload & Extract",
    "✏️ Review & Edit Invoices",
    "📊 Financial Analytics",
    "📁 Export & Database"
])

# ==========================================
# --- Tab 1: Upload & Extract ---
# ==========================================
with tab1:
    st.subheader("Batch Invoice Extraction")
    uploaded_files = st.file_uploader(
        "Upload PDF Invoices (Digital or Scanned)",
        type=["pdf"],
        accept_multiple_files=True
    )

    if uploaded_files:
        if st.button("🚀 Process & Store Invoices", type="primary"):
            progress_bar = st.progress(0)
            status_text = st.empty()
            results = []
            errors = []

            for i, uploaded_file in enumerate(uploaded_files):
                status_text.text(f"Processing: {uploaded_file.name} ({i+1}/{len(uploaded_files)})")
                
                data, err = store_data.store_invoice(
                    uploaded_file,
                    filename=uploaded_file.name,
                    db_path=DB_PATH,
                    model=model_choice
                )

                if data:
                    results.append(data)
                else:
                    errors.append(f"**{uploaded_file.name}**: {err or 'Extraction failed'}")

                progress_bar.progress((i + 1) / len(uploaded_files))

            status_text.text("Extraction complete!")
            if results:
                st.success(f"Successfully processed {len(results)} invoice(s)!")
                df_res = pd.DataFrame(results)
                cols_to_show = [c for c in ["invoice_number", "client_name", "vendor_name", "invoice_amount", "invoice_date", "status", "pdf_file"] if c in df_res.columns]
                st.dataframe(df_res[cols_to_show], width="stretch")

            if errors:
                st.error("Some files could not be processed:")
                for e in errors:
                    st.markdown(f"- {e}")

    st.markdown("---")
    st.markdown("#### Sample Invoice Quick Test")
    sample_path = Path(__file__).resolve().parent / "sample_invoice.pdf"
    if sample_path.exists():
        if st.button("📄 Run Quick Test on sample_invoice.pdf"):
            with st.spinner("Extracting with chosen AI model..."):
                sample_data, s_err = store_data.store_invoice(
                    str(sample_path),
                    filename="sample_invoice.pdf",
                    db_path=DB_PATH,
                    model=model_choice
                )
                if sample_data:
                    st.success("Sample invoice processed and saved!")
                    st.json(sample_data)
                else:
                    st.error(f"Could not extract sample invoice: {s_err}")
    else:
        st.info("sample_invoice.pdf not found in directory.")

# ==========================================
# --- Tab 2: Review & Edit (Human-in-the-Loop) ---
# ==========================================
with tab2:
    st.subheader("Human-in-the-Loop Review & Corrections")
    st.caption("Verify extracted invoice data, correct missing or misread values, and update payment statuses.")

    all_invoices = reports.get_all_invoices(DB_PATH)
    if all_invoices:
        filenames = [inv["filename"] for inv in all_invoices]
        selected_file = st.selectbox("Select Invoice to Inspect / Edit:", filenames)
        
        target_inv = next((inv for inv in all_invoices if inv["filename"] == selected_file), None)
        if target_inv:
            with st.form("edit_invoice_form"):
                col_e1, col_e2, col_e3 = st.columns(3)
                with col_e1:
                    new_inv_num = st.text_input("Invoice Number", value=target_inv.get("invoice_number") or "")
                    new_client = st.text_input("Client Name", value=target_inv.get("client_name") or "")
                    new_vendor = st.text_input("Vendor Name", value=target_inv.get("vendor_name") or "")
                with col_e2:
                    new_inv_date = st.text_input("Invoice Date (YYYY-MM-DD)", value=target_inv.get("invoice_date") or "")
                    new_due_date = st.text_input("Due Date (YYYY-MM-DD)", value=target_inv.get("due_date") or "")
                    new_prod = st.text_input("Product / Service Name", value=target_inv.get("product_name") or "")
                with col_e3:
                    new_amt = st.number_input("Invoice Amount", value=float(target_inv.get("invoice_amount") or 0.0), step=10.0)
                    new_tax = st.number_input("Tax Amount", value=float(target_inv.get("tax_amount") or 0.0), step=5.0)
                    status_options = ["Pending", "Paid", "Overdue"]
                    curr_status = target_inv.get("status") or "Pending"
                    status_idx = status_options.index(curr_status) if curr_status in status_options else 0
                    new_status = st.selectbox("Payment Status", status_options, index=status_idx)

                new_notes = st.text_area("Notes", value=target_inv.get("notes") or "")

                col_btn1, col_btn2 = st.columns([1, 5])
                with col_btn1:
                    submit_save = st.form_submit_button("💾 Save Changes", type="primary")

            if submit_save:
                updated_data = {
                    "invoice_number": new_inv_num,
                    "client_name": new_client,
                    "vendor_name": new_vendor,
                    "invoice_date": new_inv_date,
                    "due_date": new_due_date,
                    "product_name": new_prod,
                    "invoice_amount": new_amt,
                    "tax_amount": new_tax,
                    "status": new_status,
                    "notes": new_notes
                }
                success = store_data.update_invoice_record(selected_file, updated_data, db_path=DB_PATH)
                if success:
                    st.success(f"Updated record for {selected_file}!")
                    st.rerun()
                else:
                    st.error("Failed to update record.")

            # Line items display
            line_items_raw = target_inv.get("line_items_json")
            if line_items_raw:
                try:
                    items = json.loads(line_items_raw)
                    if items and isinstance(items, list):
                        st.markdown("##### Extracted Line Items")
                        st.dataframe(pd.DataFrame(items), width="stretch")
                except Exception:
                    pass

            # Danger zone
            st.markdown("---")
            if st.button(f"🗑️ Delete {selected_file}", type="secondary"):
                store_data.delete_invoice_record(selected_file, db_path=DB_PATH)
                st.warning(f"Deleted {selected_file} from database.")
                st.rerun()
    else:
        st.info("No invoices found to edit. Upload or run a sample invoice first!")

# ==========================================
# --- Tab 3: Financial Analytics ---
# ==========================================
with tab3:
    st.subheader("Executive Financial Analytics")
    summary = reports.overall_summary(DB_PATH)

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Total Invoices", summary["total_invoices"])
    with col2:
        st.metric("Total Spend", f"${summary['total_amount']:,.2f}")
    with col3:
        st.metric("Average Invoice", f"${summary['average_amount']:,.2f}")
    with col4:
        st.metric("Total Tax / VAT", f"${summary['total_tax']:,.2f}")

    col_s1, col_s2, col_s3, col_s4 = st.columns(4)
    with col_s1:
        st.metric("Unique Clients", summary["unique_clients"])
    with col_s2:
        st.metric("Pending Invoices", summary["pending_count"])
    with col_s3:
        st.metric("Paid Invoices", summary["paid_count"])
    with col_s4:
        st.metric("Overdue Invoices", summary["overdue_count"])

    st.markdown("---")
    col_chart1, col_chart2 = st.columns(2)

    # Breakdown by Client
    breakdown = reports.client_breakdown(DB_PATH)
    if breakdown:
        df_client = pd.DataFrame(breakdown)
        with col_chart1:
            fig_bar = px.bar(
                df_client,
                x="client_name",
                y="total_spent",
                title="Total Spend by Client",
                labels={"client_name": "Client Name", "total_spent": "Total ($)"},
                color="total_spent",
                color_continuous_scale="Tealgrn"
            )
            st.plotly_chart(fig_bar, width="stretch")

        with col_chart2:
            fig_pie = px.pie(
                df_client,
                names="client_name",
                values="total_spent",
                title="Spend Share by Client",
                hole=0.45
            )
            st.plotly_chart(fig_pie, width="stretch")

    # Monthly Trends
    trends = reports.monthly_trends(DB_PATH)
    if trends:
        st.markdown("#### Monthly Spend Timeline")
        df_trends = pd.DataFrame(trends)
        fig_trend = px.line(
            df_trends,
            x="month",
            y="total_amount",
            markers=True,
            title="Monthly Invoice Total Trends",
            labels={"month": "Month", "total_amount": "Total Amount ($)"}
        )
        st.plotly_chart(fig_trend, width="stretch")

# ==========================================
# --- Tab 4: Export & Database ---
# ==========================================
with tab4:
    st.subheader("Invoice Records & Multi-Format Export")
    all_invs = reports.get_all_invoices(DB_PATH)

    if all_invs:
        df_all = pd.DataFrame(all_invs)
        cols_display = [
            "filename", "invoice_number", "invoice_date", "due_date",
            "client_name", "vendor_name", "invoice_amount", "tax_amount",
            "currency", "product_name", "status"
        ]
        st.dataframe(df_all[cols_display], width="stretch")

        col_d1, col_d2 = st.columns(2)

        # CSV Export
        with col_d1:
            csv_data = df_all[cols_display].to_csv(index=False).encode('utf-8')
            st.download_button(
                "📥 Download Invoices as CSV",
                data=csv_data,
                file_name="invoices_report.csv",
                mime="text/csv"
            )

        # Excel Export (Multiple Sheets: Summary + Detailed)
        with col_d2:
            excel_buf = io.BytesIO()
            with pd.ExcelWriter(excel_buf, engine='openpyxl') as writer:
                df_all[cols_display].to_excel(writer, sheet_name="Invoices", index=False)
                if breakdown:
                    pd.DataFrame(breakdown).to_excel(writer, sheet_name="Client Breakdown", index=False)
                if trends:
                    pd.DataFrame(trends).to_excel(writer, sheet_name="Monthly Trends", index=False)

            st.download_button(
                "📊 Download Comprehensive Excel (.xlsx)",
                data=excel_buf.getvalue(),
                file_name="invoice_financial_report.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
    else:
        st.info("The database is currently empty. Process invoices to view and export records.")
