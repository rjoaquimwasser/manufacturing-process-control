import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from main import calculate_kpis, detect_anomalies, six_sigma_rule_detection

# Set page configuration
st.set_page_config(layout='wide')

# Load data
df = pd.read_csv('data/cycle_time.csv', sep=';')

# Calculate KPIs
kpis = calculate_kpis(df)

# Detect anomalies
anomalies = detect_anomalies(df)

# Detect six sigma rule violations
violations = six_sigma_rule_detection(df)

# Display the dashboard title
st.title('🏭 Manufacturing Process Dashboard')

# Display KPIs in a 4-column layout
col1, col2, col3, col4 = st.columns(4)
col1.metric("Mean Cycle Time (s)", f"{kpis['mean']:.2f}s")
col2.metric("Max Cycle Time (s)", f"{kpis['max']:.2f}s")
col3.metric("Min Cycle Time (s)", f"{kpis['min']:.2f}s")
col4.metric("Compliance (%)", f"{kpis['compliance_rate (%)']:.2f}%")

# Non-compliance rate classification
if kpis['non_compliance_rate (%)'] > 10:
    st.error('🔴 Process out of control')
elif kpis['non_compliance_rate (%)'] > 5:
    st.warning('🟠 Process warning')
else:
    st.success('🟢 Process stable')

# Display cycle time trend with anomalies
st.subheader('Cycle Time Trend')
fig, ax = plt.subplots()
ax.plot(df['time'], df['cycle_time'], label='Cycle Time')

# Highlight anomalies on the control chart
if not anomalies.empty:
    ax.scatter(anomalies['time'], anomalies['cycle_time'], color='red', label='Anomalies')

# Highlight six sigma rule violations on the control chart
for rule_name, subset in violations:
    if not subset.empty:
        ax.scatter(subset['time'], subset['cycle_time'], s=80, label=rule_name)

ax.legend()
ax.grid()
st.pyplot(fig)

# Display anomalies in a table
st.subheader('🚨 Anomalies Detected')
st.dataframe(anomalies.reset_index(drop=True))

# Display six sigma rule violations
st.subheader('⚠️ Six Sigma Rule Violations')
for rule_name, subset in violations:
    if not subset.empty:
        subset_clean = subset.reset_index(drop=True)
        st.markdown(f'**{rule_name}:** {len(subset_clean)} points')
        st.dataframe(subset_clean)
