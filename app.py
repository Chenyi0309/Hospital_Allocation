import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

# Set up the Streamlit page
st.set_page_config(page_title="ICU Allocation Dashboard", layout="wide")
st.title("🏥 Hospital ICU Bed Allocation Optimizer")
st.markdown("""
This dashboard visualizes the **optimized ICU bed allocation** based on actual COVID demand
and hospital capacity.
""")

# Load dataset
data_path = "hospital_optimized_allocation.csv"
@st.cache_data
def load_data(path):
    df = pd.read_csv(path)
    df["shortage"] = df["staffed_icu_adult_patients_confirmed_covid_7_day_avg"] - df["icu_allocated"]
    df["shortage"] = df["shortage"].clip(lower=0)
    return df

df = load_data(data_path)

# Sidebar filters
st.sidebar.header("Filter Hospitals")
states = df["state"].dropna().unique()
selected_states = st.sidebar.multiselect("Select State(s):", options=states, default=states)

if "urban_status" in df.columns:
    urban_types = df["urban_status"].unique()
    selected_urban = st.sidebar.multiselect("Select Urban Status:", options=urban_types, default=urban_types)
    df = df[df["urban_status"].isin(selected_urban)]

# Apply state filter
df = df[df["state"].isin(selected_states)]

# Summary section
st.subheader("📊 Summary Statistics")
col1, col2, col3 = st.columns(3)
col1.metric("Total ICU Demand", f"{df['staffed_icu_adult_patients_confirmed_covid_7_day_avg'].sum():,.0f}")
col2.metric("Total ICU Allocated", f"{df['icu_allocated'].sum():,.0f}")
col3.metric("Total Shortage", f"{df['shortage'].sum():,.0f}")

# Optional: Grouped summary
if "urban_status" in df.columns:
    st.markdown("### ICU Demand vs Allocation by Urban Status")
    grouped = df.groupby("urban_status")[
        ["staffed_icu_adult_patients_confirmed_covid_7_day_avg", "icu_allocated"]
    ].sum()
    grouped["shortage"] = grouped["staffed_icu_adult_patients_confirmed_covid_7_day_avg"] - grouped["icu_allocated"]
    st.dataframe(grouped.style.format("{:.1f}"))

# Plotting section
st.markdown("### ICU Allocation vs. COVID Demand")
fig, ax = plt.subplots(figsize=(10, 6))
sns.scatterplot(
    data=df,
    x="staffed_icu_adult_patients_confirmed_covid_7_day_avg",
    y="icu_allocated",
    hue="urban_status" if "urban_status" in df.columns else None,
    ax=ax
)
ax.plot(
    [0, df["staffed_icu_adult_patients_confirmed_covid_7_day_avg"].max()],
    [0, df["staffed_icu_adult_patients_confirmed_covid_7_day_avg"].max()],
    'r--', label="Perfect Allocation"
)
ax.set_xlabel("Confirmed ICU COVID Patients")
ax.set_ylabel("ICU Beds Allocated")
ax.set_title("Allocation Effectiveness")
ax.legend()
ax.grid(True)
st.pyplot(fig)

# Show data table
st.markdown("### Raw Data Table (Filtered)")
st.dataframe(df.sort_values("shortage", ascending=False).reset_index(drop=True))

# Optional: Download link
st.download_button(
    label="💾 Download Optimized CSV",
    data=df.to_csv(index=False).encode('utf-8'),
    file_name='hospital_optimized_allocation_filtered.csv',
    mime='text/csv'
)
