import streamlit as st
import pandas as pd
from datetime import date
import json
from google.oauth2.service_account import Credentials
import gspread
# -----------------------------
# Google Sheet setup
# -----------------------------
SHEET_NAME = "RoomExpense"

# Connect to Google Sheets
scope = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive"
]


creds_dict = json.loads(st.secrets["GOOGLE_CREDS"])
creds = Credentials.from_service_account_info(creds_dict, scopes=scope)
client = gspread.authorize(creds)
sheet = client.open(SHEET_NAME).sheet1
# Initialize session state

# if "expenses" not in st.session_state:
#     st.session_state["expenses"] = []

st.title("💰 Roommate Expense Sharing App")

# Expense entry form
with st.form("expense_form", clear_on_submit=True):
    name = st.selectbox("Who spent?", ["Baskaran", "Ganga", "Kannan"])
    amount = st.number_input("Amount spent", min_value=0.0, step=0.01)
    log_date = st.date_input("Date of expense")
    description = st.text_input("Description (optional)")
    submitted = st.form_submit_button("Add Expense")

    if submitted and amount > 0:
        new_row=[name, amount, log_date.strftime("%Y-%m-%d"),description]
        sheet.append_row(new_row)
        # st.session_state["expenses"].append(
        #     {"Date": log_date, "Name": name, "Amount": amount, "Description": description}
        # )
        st.success(f"✅ Added {amount:.2f} by {name} on {log_date}")

# -----------------------------
# Load existing data
# -----------------------------
data = sheet.get_all_records()
df = pd.DataFrame(data)
if df.empty:
    df = pd.DataFrame(columns=["Name", "Amount", "Date", "Descriptionals"])
else:
    ##df['ThisMonth'] = pd.to_datetime(df['Date']).dt.month
# Filter records for the current month
    this_month=pd.to_datetime(date.today()).month
    df_thismonth = df[pd.to_datetime(df['Date']).dt.month == this_month]
    st.subheader("📒 Expenses Recorded")
    st.dataframe(df_thismonth.sort_values(by="Date"), use_container_width=True)


# ---- Show Records and Monthly Summary ----
#if st.session_state["expenses"]

    # Calculate totals
    total = df_thismonth["Amount"].sum()
    per_person = total / 3
    spent = (
        df_thismonth.groupby("Name")["Amount"]
        .sum()
        .reindex(["Baskaran", "Ganga", "Kannan"], fill_value=0)
    )

    # Monthly Summary
    st.subheader("📊 Monthly Summary")
    st.markdown(f"- **Total Amount Spent:** {total:.2f}")
    st.markdown(f"- **Each Individual Share:** {per_person:.2f}")
    st.markdown(f"- **Baskaran spent:** {spent['Baskaran']:.2f}")
    st.markdown(f"- **Ganga spent:** {spent['Ganga']:.2f}")
    st.markdown(f"- **Kannan spent:** {spent['Kannan']:.2f}")

    # Balances
    balances = spent - per_person

    # Settlement Instructions
    st.subheader("💡 Settlement Instructions")
    creditors = balances[balances > 0]  # people who should receive
    debtors = balances[balances < 0]    # people who should pay

    if creditors.empty and debtors.empty:
        st.info("✅ Everyone is settled. No payments needed.")
    else:
        for debtor, d_amount in debtors.items():
            for creditor, c_amount in creditors.items():
                pay_amount = min(-d_amount, c_amount)
                if pay_amount > 0:
                    st.write(f"👉 {debtor} owes {pay_amount:.2f} to {creditor}")
                    # Update balances live
                    balances[debtor] += pay_amount
                    balances[creditor] -= pay_amount

    # Reset button for new month
    if st.button("🔄 Reset for New Month"):
        st.session_state["expenses"] = []
        st.success("✅ Expenses cleared for the new month!")
