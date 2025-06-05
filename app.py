import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import pyomo.environ as pyo
import os

# Set up the Streamlit page
st.set_page_config(page_title="ICU Allocation Dashboard", layout="wide")
st.title("🏥 Hospital ICU Bed Allocation Optimizer")
st.markdown("""
This dashboard visualizes the **optimized ICU bed allocation** based on actual COVID demand
and hospital capacity. You can also simulate your own demand scenarios below.
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

# Download link
st.download_button(
    label="💾 Download Optimized CSV",
    data=df.to_csv(index=False).encode('utf-8'),
    file_name='hospital_optimized_allocation_filtered.csv',
    mime='text/csv'
)

# ------------------------------
# Simulation Section
# ------------------------------
st.markdown("---")
st.subheader("🧪 Simulate ICU Demand by Severity")

with st.form("simulate_form"):
    total_patients = st.slider("Projected Total ICU COVID Patients:", min_value=10, max_value=500, value=100)
    col1, col2, col3 = st.columns(3)
    perc_moderate = col1.number_input("% Moderate", min_value=0.0, max_value=100.0, value=30.0)
    perc_severe = col2.number_input("% Severe", min_value=0.0, max_value=100.0, value=40.0)
    perc_critical = col3.number_input("% Critical", min_value=0.0, max_value=100.0, value=30.0)

    col4, col5, col6 = st.columns(3)
    weight_moderate = col4.number_input("Priority Weight: Moderate", value=1.0)
    weight_severe = col5.number_input("Priority Weight: Severe", value=2.0)
    weight_critical = col6.number_input("Priority Weight: Critical", value=3.0)

    simulate_button = st.form_submit_button("Run Simulation")

if simulate_button:
    # Compute synthetic demand
    weights = {
        "moderate": weight_moderate,
        "severe": weight_severe,
        "critical": weight_critical,
    }
    demand_dist = {
        "moderate": total_patients * (perc_moderate / 100),
        "severe": total_patients * (perc_severe / 100),
        "critical": total_patients * (perc_critical / 100),
    }

    # Prepare optimization model
    sim_model = pyo.ConcreteModel()
    sim_model.GROUPS = pyo.Set(initialize=["moderate", "severe", "critical"])
    sim_model.x = pyo.Var(sim_model.GROUPS, domain=pyo.NonNegativeReals)

    sim_model.obj = pyo.Objective(
        expr=sum(weights[g] * (demand_dist[g] - sim_model.x[g]) for g in sim_model.GROUPS),
        sense=pyo.minimize
    )

    # Constraint: total allocation must be less than hospital system capacity
    sim_model.capacity_limit = pyo.Constraint(expr=sum(sim_model.x[g] for g in sim_model.GROUPS) <= total_patients)

    # Use GLPK solver (works on Streamlit Cloud)
    solver = pyo.SolverFactory("glpk")
    if not solver.available():
        st.error("❌ GLPK solver not available in current environment.")
    else:
        results = solver.solve(sim_model, tee=False)

        st.success("✅ Optimization complete.")
        sim_results = {g: pyo.value(sim_model.x[g]) for g in sim_model.GROUPS}
        result_df = pd.DataFrame({
            "Group": list(sim_results.keys()),
            "Allocated": list(sim_results.values()),
            "Demand": [demand_dist[g] for g in sim_model.GROUPS],
            "Unmet": [demand_dist[g] - sim_results[g] for g in sim_model.GROUPS]
        })

        st.dataframe(result_df.style.format("{:.1f}"))

        fig2, ax2 = plt.subplots()
        ax2.bar(result_df["Group"], result_df["Demand"], label="Demand", alpha=0.6)
        ax2.bar(result_df["Group"], result_df["Allocated"], label="Allocated", alpha=0.8)
        ax2.set_ylabel("Beds")
        ax2.set_title("Simulated ICU Allocation vs Demand")
        ax2.legend()
        st.pyplot(fig2)
