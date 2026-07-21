import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px

st.set_page_config(page_title="Tronox Dashboard", page_icon="🏭", layout="wide")

st.title("🏭 Tronox KZN Sands Integrated Operations Dashboard")
st.markdown("**Powered by PraxiomAI.io** | Real-time Mining & Metallurgical Performance Analytics")
st.markdown("---")

# =============================================================================
# SIDEBAR - INPUT PARAMETERS
# =============================================================================
with st.sidebar:
    st.header("📊 Input Parameters")
    
    st.subheader("🏭 Mining Operations")
    rom_tons = st.number_input("ROM Tons/Day (Total Mined)", min_value=0.0, value=45000.0, step=1000.0, 
                                  help="Total Run of Mine material - everything extracted from the pit")
    waste_fraction = st.number_input("Waste Fraction of ROM (%)", min_value=0.0, max_value=100.0, value=65.0, step=1.0,
                                      help="Percentage of ROM that is waste material")
    mining_recovery = st.number_input("Mining Recovery (%)", min_value=0.0, max_value=100.0, value=95.0, step=1.0,
                                       help="Percentage of ore successfully recovered during mining")
    
    st.subheader("🗺️ Geology Parameters")
    thm_pct = st.number_input("THM Grade in Ore (%)", min_value=0.0, max_value=100.0, value=8.5, step=0.1,
                               help="Total Heavy Minerals percentage in the ore fraction")
    slimes_pct = st.number_input("Slimes (%)", min_value=0.0, max_value=100.0, value=12.0, step=0.5,
                                  help="Fine clay/slime content affecting recovery")
    tio2_in_thm = st.number_input("TiO₂ in THM (%)", min_value=0.0, max_value=100.0, value=45.0, step=0.5,
                                   help="Titanium dioxide content in heavy minerals")
    zro2_in_thm = st.number_input("ZrO₂ in THM (%)", min_value=0.0, max_value=100.0, value=8.0, step=0.5,
                                   help="Zirconium dioxide content - indicates zircon presence")
    block_life_days = st.number_input("Block Life (Days)", min_value=1, value=180, step=10)
    
    st.subheader("⚙️ Metallurgical/Plant")
    base_recovery = st.number_input("Base Recovery (%)", min_value=0.0, max_value=100.0, value=82.0, step=1.0)
    base_throughput = st.number_input("Base Throughput (tph)", min_value=0.0, value=500.0, step=50.0)
    concentrate_grade = st.number_input("Concentrate Grade (%)", min_value=0.0, max_value=100.0, value=65.0, step=0.5)
    operating_hours = st.number_input("Operating Hours/Day", min_value=0.0, max_value=24.0, value=20.0, step=1.0)
    
    st.subheader("💰 Economic Parameters")
    price_per_ton = st.number_input("Concentrate Price ($/ton)", min_value=0.0, value=350.0, step=10.0)
    zircon_price_per_ton = st.number_input("Zircon Price ($/ton)", min_value=0.0, value=1200.0, step=50.0)
    mining_cost_per_ton = st.number_input("Mining Cost ($/ton ROM)", min_value=0.0, value=8.5, step=0.5)
    processing_cost_per_ton = st.number_input("Processing Cost ($/ton HMC)", min_value=0.0, value=45.0, step=1.0)

# =============================================================================
# CALCULATIONS - CORRECTED MATERIAL FLOW
# =============================================================================

# Mining Material Flow (ROM = Total Mined)
waste_tons = rom_tons * (waste_fraction / 100.0)
ore_tons = rom_tons - waste_tons  # Ore is ROM minus waste
hmc_tons = ore_tons * (thm_pct / 100.0) * (mining_recovery / 100.0)
tailings_tons = ore_tons - hmc_tons  # Remaining ore after HMC extraction

# Metallurgical Calculations
recovery = base_recovery
throughput = base_throughput
concentrate_tons = hmc_tons * (recovery / 100.0) * (concentrate_grade / 100.0)

# Zircon Calculations (from ZrO₂ in THM)
zircon_factor = zro2_in_thm / 67.2  # ZrO₂ is ~67.2% of pure zircon (ZrSiO₄)
zircon_tons = hmc_tons * (recovery / 100.0) * zircon_factor
ilmenite_rutile_tons = concentrate_tons - zircon_tons

# Plant Performance Prediction
slimes_factor = max(0.7, 1.0 - (slimes_pct - 10.0) * 0.02)
thm_factor = min(1.15, 1.0 + (thm_pct - 5.0) * 0.015)
predicted_recovery = min(95.0, base_recovery * slimes_factor * thm_factor)
predicted_throughput = base_throughput * (1.0 + (thm_pct - 8.0) * 0.01) * slimes_factor

# Economic Calculations
zircon_revenue = zircon_tons * zircon_price_per_ton
base_revenue = ilmenite_rutile_tons * price_per_ton
total_revenue = base_revenue + zircon_revenue

daily_mining_cost = rom_tons * mining_cost_per_ton
daily_processing_cost = hmc_tons * processing_cost_per_ton
total_daily_cost = daily_mining_cost + daily_processing_cost
nsr_per_day = total_revenue - total_daily_cost
nsr_per_ton_rom = nsr_per_day / rom_tons if rom_tons > 0 else 0.0

# Block Economics
total_block_rom = rom_tons * block_life_days
total_block_nsr = nsr_per_day * block_life_days

# Ore Classification
if thm_pct < 4.0:
    ore_class, ore_color = "Low Grade - Stockpile", "🔴"
elif thm_pct < 7.0:
    ore_class, ore_color = "Medium Grade - Blend", "🟠"
elif thm_pct < 10.0:
    ore_class, ore_color = "High Grade - Process", "🟡"
else:
    ore_class, ore_color = "Premium Grade - Priority", "🟢"

# =============================================================================
# MAIN DASHBOARD
# =============================================================================

# SECTION 1: MINING OPERATIONS
st.subheader("🏭 Mining Operations - Material Flow")
c1, c2, c3, c4 = st.columns(4)
c1.metric("ROM Tons/Day (Total Mined)", f"{rom_tons:,.0f}")
c2.metric("Waste Tons/Day", f"{waste_tons:,.0f}")
c3.metric("Ore Tons/Day", f"{ore_tons:,.0f}")
c4.metric("HMC Tons/Day", f"{hmc_tons:,.0f}")

# Mining Material Flow Sankey-style Visualization
flow_data = pd.DataFrame({
    'Stage': ['ROM', 'Waste', 'Ore', 'HMC', 'Tailings'],
    'Tons': [rom_tons, waste_tons, ore_tons, hmc_tons, tailings_tons],
    'Type': ['Total', 'Removed', 'Processed', 'Product', 'Discard']
})

col1, col2 = st.columns([2, 1])
with col1:
    fig_mining = px.bar(flow_data, x='Stage', y='Tons', color='Type',
                        color_discrete_map={'Total': '#2E86AB', 'Removed': '#A23B72', 
                                           'Processed': '#F18F01', 'Product': '#28a745', 'Discard': '#6c757d'},
                        title="📊 Mining Material Flow (ROM → Waste → Ore → HMC)")
    st.plotly_chart(fig_mining, use_container_width=True)

with col2:
    # Pie chart showing ROM composition
    rom_comp = pd.DataFrame({
        'Component': ['Waste', 'Ore (to HMC)', 'Ore (to Tailings)'],
        'Tons': [waste_tons, hmc_tons, tailings_tons]
    })
    fig_pie = px.pie(rom_comp, values='Tons', names='Component', 
                     title="🥧 ROM Composition Breakdown",
                     color_discrete_sequence=px.colors.qualitative.Set2)
    st.plotly_chart(fig_pie, use_container_width=True)

st.markdown("---")

# SECTION 2: GEOLOGY PARAMETERS
st.subheader("🗺️ Geology Parameters")
c1, c2, c3, c4, c5 = st.columns(5)
c1.metric("THM Grade", f"{thm_pct:.1f}%")
c2.metric("Slimes", f"{slimes_pct:.1f}%")
c3.metric("TiO₂ in THM", f"{tio2_in_thm:.1f}%")
c4.metric("ZrO₂ in THM", f"{zro2_in_thm:.1f}%")
c5.metric(f"{ore_color} Ore Class", ore_class)

# Geology Visualizations
col1, col2 = st.columns(2)
with col1:
    fig_thm_rec = go.Figure()
    fig_thm_rec.add_trace(go.Scatter(x=[thm_pct], y=[predicted_recovery], 
                                      mode='markers+text', 
                                      marker=dict(size=20, color='#2E86AB'),
                                      text=[f'{predicted_recovery:.1f}%'],
                                      textposition='top center'))
    fig_thm_rec.update_layout(title="THM vs Predicted Recovery", 
                               xaxis_title="THM (%)", 
                               yaxis_title="Recovery (%)",
                               xaxis=dict(range=[0, 15]),
                               yaxis=dict(range=[60, 95]))
    st.plotly_chart(fig_thm_rec, use_container_width=True)

with col2:
    mineralogy_data = pd.DataFrame({
        'Mineral': ['Ilmenite/Rutile', 'Zircon', 'Monazite', 'Other HM', 'Slimes'],
        'Percent': [tio2_in_thm * 0.7, zro2_in_thm * 1.5, 2.5, (thm_pct - tio2_in_thm*0.7 - zro2_in_thm*1.5 - 2.5), slimes_pct]
    })
    mineralogy_data['Percent'] = mineralogy_data['Percent'].clip(lower=0)  # Ensure no negative values
    fig_min = px.pie(mineralogy_data, values='Percent', names='Mineral', 
                     title="🔬 Estimated Mineralogy Distribution",
                     color_discrete_sequence=px.colors.qualitative.Set3)
    st.plotly_chart(fig_min, use_container_width=True)

st.markdown("---")

# SECTION 3: METALLURGICAL/PLANT PERFORMANCE
st.subheader("⚙️ Metallurgical/Plant Performance")
c1, c2, c3, c4 = st.columns(4)
c1.metric("Base Recovery", f"{base_recovery:.1f}%")
c2.metric("Predicted Recovery", f"{predicted_recovery:.1f}%")
c3.metric("Base Throughput", f"{base_throughput:.0f} tph")
c4.metric("Predicted Throughput", f"{predicted_throughput:.0f} tph")

# Plant Performance Visualizations
col1, col2 = st.columns(2)
with col1:
    perf_data = pd.DataFrame({
        'Metric': ['Base Recovery', 'Predicted Recovery', 'Base Throughput/10', 'Predicted Throughput/10'],
        'Value': [base_recovery, predicted_recovery, base_throughput/10, predicted_throughput/10]
    })
    fig_perf = px.bar(perf_data, x='Metric', y='Value', color='Metric',
                      title="⚙️ Plant Performance Comparison",
                      color_discrete_sequence=px.colors.qualitative.Bold)
    st.plotly_chart(fig_perf, use_container_width=True)

with col2:
    grade_rec_data = pd.DataFrame({
        'Grade Scenario': ['Low (50%)', 'Medium (65%)', 'High (80%)'],
        'Recovery': [base_recovery * 0.9, base_recovery, base_recovery * 1.05],
        'Throughput': [base_throughput * 0.85, base_throughput, base_throughput * 1.1]
    })
    fig_grade = go.Figure()
    fig_grade.add_trace(go.Scatter(x=grade_rec_data['Throughput'], y=grade_rec_data['Recovery'],
                                    mode='lines+markers', name='Performance Curve',
                                    line=dict(color='#2E86AB', width=3)))
    fig_grade.update_layout(title="Grade vs Performance Curve",
                            xaxis_title="Throughput (tph)",
                            yaxis_title="Recovery (%)")
    st.plotly_chart(fig_grade, use_container_width=True)

# Concentrate Breakdown
st.markdown("#### 📦 Concentrate Product Breakdown")
c1, c2, c3 = st.columns(3)
c1.metric("Total Concentrate", f"{concentrate_tons:,.0f} tons/day")
c2.metric("Ilmenite/Rutile", f"{ilmenite_rutile_tons:,.0f} tons/day")
c3.metric("Zircon", f"{zircon_tons:,.0f} tons/day")

conc_breakdown = pd.DataFrame({
    'Product': ['Ilmenite/Rutile', 'Zircon'],
    'Tons/Day': [ilmenite_rutile_tons, zircon_tons]
})
fig_conc = px.bar(conc_breakdown, x='Product', y='Tons/Day', color='Product',
                  color_discrete_map={'Ilmenite/Rutile': '#2E86AB', 'Zircon': '#F18F01'},
                  title="📦 Daily Concentrate Production")
st.plotly_chart(fig_conc, use_container_width=True)

st.markdown("---")

# SECTION 4: ECONOMIC SUMMARY
st.subheader("💰 Economic Summary")
c1, c2, c3, c4 = st.columns(4)
c1.metric("Daily Revenue", f"${total_revenue:,.0f}")
c2.metric("Total Daily Cost", f"${total_daily_cost:,.0f}")
c3.metric("NSR/Day", f"${nsr_per_day:,.0f}")
c4.metric("NSR/Ton ROM", f"${nsr_per_ton_rom:.2f}")

# Block Economics
st.markdown("#### 📊 Block Economics (Entire Mining Block)")
c1, c2, c3 = st.columns(3)
c1.metric("Total Block ROM", f"{total_block_rom:,.0f} tons")
c2.metric("Block Life", f"{block_life_days} days")
c3.metric("Total Block NSR", f"${total_block_nsr:,.0f}")

# Economic Visualization
econ_data = pd.DataFrame({
    'Category': ['Base Revenue', 'Zircon Revenue', 'Mining Cost', 'Processing Cost', 'Net NSR'],
    'Amount': [base_revenue, zircon_revenue, -daily_mining_cost, -daily_processing_cost, nsr_per_day]
})
fig_econ = go.Figure(data=[go.Bar(
    x=econ_data['Category'],
    y=econ_data['Amount'],
    marker_color=['#28a745', '#17a2b8', '#dc3545', '#dc3545', '#28a745']
)])
fig_econ.update_layout(title="💰 Daily Economic Breakdown (Including Zircon Revenue)",
                       yaxis_title="USD ($)",
                       showlegend=False)
st.plotly_chart(fig_econ, use_container_width=True)

st.markdown("---")

# SECTION 5: PERFORMANCE ANALYTICS & RECOMMENDATIONS
st.subheader("📈 Performance Analytics & Recommendations")

recommendations = []

# Ore Classification Logic
if thm_pct < 4.0:
    recommendations.append("🔴 **LOW GRADE:** Consider stockpiling for future blending")
elif thm_pct < 7.0:
    recommendations.append("🟠 **MEDIUM GRADE:** Blend with high-grade ore for optimal processing")
elif thm_pct < 10.0:
    recommendations.append("🟡 **HIGH GRADE:** Optimal for current plant configuration")
else:
    recommendations.append("🟢 **PREMIUM GRADE:** Prioritize this block - maximum economic value")

# TiO₂ Analysis
if tio2_in_thm < 35.0:
    recommendations.append("🟠 **LOW TiO₂:** Ilmenite-dominant - Optimize magnetic separation")
elif tio2_in_thm > 55.0:
    recommendations.append("✅ **HIGH TiO₂:** Rutile-rich - Premium product, prioritize this block")

# Zircon Analysis
if zro2_in_thm < 5.0:
    recommendations.append("🟠 **LOW ZrO₂:** Limited zircon recovery - focus on TiO₂ products")
elif zro2_in_thm > 10.0:
    recommendations.append("✅ **HIGH ZrO₂:** Significant zircon value - optimize zircon circuit")

# Slimes Impact
if slimes_pct > 15.0:
    recommendations.append("⚠️ **HIGH SLIMES:** Expect reduced recovery - adjust classifier settings")
elif slimes_pct < 8.0:
    recommendations.append("✅ **LOW SLIMES:** Optimal conditions for maximum recovery")

# Economic Viability
if nsr_per_day < 0:
    recommendations.append("🚨 **NEGATIVE MARGIN:** Not economic - consider stockpiling or blending")
elif nsr_per_ton_rom < 5.0:
    recommendations.append("⚠️ **LOW MARGIN:** Review cost structure or wait for better pricing")
else:
    recommendations.append("✅ **POSITIVE MARGIN:** Economically viable - proceed with mining")

# Recovery Performance
if predicted_recovery < 75.0:
    recommendations.append("⚠️ **LOW RECOVERY:** Review circuit parameters, check classifier settings")
elif predicted_recovery > 85.0:
    recommendations.append("✅ **EXCELLENT RECOVERY:** Plant performing optimally")

# Waste Ratio Check
if waste_fraction > 75.0:
    recommendations.append("⚠️ **HIGH WASTE RATIO:** Review mining selectivity - can waste be reduced?")
elif waste_fraction < 50.0:
    recommendations.append("✅ **GOOD WASTE RATIO:** Efficient mining selectivity")

for rec in recommendations:
    st.markdown(rec)

st.markdown("---")

# =============================================================================
# EXPORT
# =============================================================================
st.subheader("📥 Export Results")

export_data = {
    'Timestamp': pd.Timestamp.now(),
    'THM_Percent': thm_pct,
    'Slimes_Percent': slimes_pct,
    'TiO2_in_THM': tio2_in_thm,
    'ZrO2_in_THM': zro2_in_thm,
    'Ore_Classification': ore_class,
    'ROM_tons_day': rom_tons,
    'Waste_tons_day': waste_tons,
    'Ore_tons_day': ore_tons,
    'HMC_tons_day': hmc_tons,
    'Concentrate_tons_day': concentrate_tons,
    'Zircon_tons_day': zircon_tons,
    'Base_Recovery': base_recovery,
    'Predicted_Recovery': predicted_recovery,
    'Base_Throughput': base_throughput,
    'Predicted_Throughput': predicted_throughput,
    'Base_Revenue': base_revenue,
    'Zircon_Revenue': zircon_revenue,
    'Total_Revenue': total_revenue,
    'Total_Cost': total_daily_cost,
    'NSR_per_day': nsr_per_day,
    'NSR_per_ton_ROM': nsr_per_ton_rom,
    'Block_Life_Days': block_life_days,
    'Total_Block_NSR': total_block_nsr
}

export_df = pd.DataFrame([export_data])
csv = export_df.to_csv(index=False).encode('utf-8')

st.download_button(
    label="📊 Download Results as CSV",
    data=csv,
    file_name=f"tronox_prediction_{pd.Timestamp.now().strftime('%Y%m%d_%H%M%S')}.csv",
    mime="text/csv"
)

# Footer
st.markdown("---")
st.markdown("**🏭 Tronox KZN Sands Integrated Operations Dashboard v5.0** | Powered by PraxiomAI.io")