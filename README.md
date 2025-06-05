# 🏥 Hospital ICU Bed Allocation Optimizer

This interactive Streamlit application helps visualize and optimize ICU bed allocation based on real COVID-19 data and simulated patient severity distributions.

It incorporates:
- Real hospital-level data on ICU demand and capacity
- A mathematical optimization model using Pyomo
- A Streamlit dashboard with filtering, plotting, and download features
- A simulated demand tool for experimenting with hypothetical ICU load and severity splits

---

## 🔍 Project Context

During the COVID-19 pandemic, hospitals experienced sudden surges in ICU demand. This tool supports ICU resource planning by helping explore optimal allocation strategies using historical and simulated data.

The data used comes from the **National Healthcare Safety Network (NHSN)** COVID-19 reports, including weekly counts of:
- Staffed ICU beds
- Confirmed ICU COVID-19 patients
- Hospital location and urban/rural status

---

## ✅ Key Features

### 📊 1. Real Allocation Viewer
- View ICU allocations for each hospital
- Filter by state or urban status
- See shortages across facilities

### 📉 2. Allocation Effectiveness Plot
- Scatterplot: ICU demand vs allocation
- Dashed reference line shows perfect 1-to-1 allocation

### 📄 3. Filtered Data Table
- Raw data shown below the dashboard
- Download as CSV using the 💾 button

---

## 🧪 4. Simulate ICU Demand by Severity

Use the **simulation tool** to test hypothetical ICU demand profiles:

- Total ICU COVID patients (10–500)
- % distribution across severity: Moderate / Severe / Critical
- Assign **priority weights** (e.g., critical patients valued more)

💡 Example:
- 100 patients, with 30% moderate, 40% severe, 30% critical
- Priorities: [1.0, 2.0, 3.0] → critical patients get 3× allocation weight

You will see:
- Optimized allocation results
- Unmet demand per group
- Interactive bar charts for comparison

---

## 📐 Optimization Model Details

The ICU allocation problem is formulated as a **linear program** (LP):

### Inputs:
- ICU demand per group \( d_i \)
- Priority weights \( w_i \)
- Total available ICU beds \( B \)

### Decision Variables:
- Allocated beds per group \( x_i \)

### Objective:
Minimize total weighted unmet demand:
\[
\min \sum_i w_i (d_i - x_i)
\]

### Subject to:
\[
\sum_i x_i \le B \quad\text{and}\quad x_i \ge 0
\]

🧮 Solved using [GLPK](https://www.gnu.org/software/glpk/) via Pyomo.

---

## 🖥 How to Run This App

### 🧱 1. Local Setup

```bash
# Clone this repo
git clone https://github.com/your-username/hospital-allocation.git
cd hospital-allocation

# Install dependencies
pip install -r requirements.txt

# Run app
streamlit run app.py
