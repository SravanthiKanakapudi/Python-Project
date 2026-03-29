
import streamlit as st
import pandas as pd
import plotly.express as px
import io
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet

# Configure page
st.set_page_config(page_title="Epidemic Spread Intelligence", layout="wide")
st.title("🦠 Epidemic Spread Intelligence Dashboard")

# File upload
uploaded_file = st.file_uploader("Upload CSV/Excel file", type=['csv', 'xlsx', 'xls'])

if uploaded_file:

    # Read file
    if uploaded_file.name.endswith('.csv'):
        df = pd.read_csv(uploaded_file)
    else:
        df = pd.read_excel(uploaded_file)

    # Clean column names
    df.columns = df.columns.str.strip().str.lower()

    st.sidebar.success(f"Data loaded: {len(df)} rows, {len(df.columns)} columns")

    # Detect cases column
    case_col = next((col for col in df.columns if 'case' in col), None)

    if not case_col:
        st.error(f"No 'cases' column found. Available columns: {df.columns.tolist()}")
        st.stop()

    # Ensure numeric values
    df[case_col] = pd.to_numeric(df[case_col], errors='coerce')
    df = df.dropna(subset=[case_col])

    # Detect date column
    date_col = df.columns[0]
    try:
        df[date_col] = pd.to_datetime(df[date_col])
    except:
        pass

    date_cols = df.select_dtypes(include=['datetime']).columns

    epidemic_title = "COVID-19 Spread Analysis" if 'covid' in uploaded_file.name.lower() else "Epidemic Spread Analysis"
    st.header(epidemic_title)

    tab1, tab2, tab3, tab4, tab5 = st.tabs(
        ["📊 Data Overview", "📈 Spread Model", "🔮 Predictions", "🛡️ Interventions", "📋 Report"]
    )

    # ---------------- TAB 1 ----------------
    with tab1:
        st.subheader("Input Data Summary")
        st.dataframe(df.head())
        st.write(f"**Dataset Shape:** {df.shape}")

        if len(date_cols) > 0:
            dcol = date_cols[0]
            st.write(f"**Date Range:** {df[dcol].min()} to {df[dcol].max()}")
        else:
            st.write("No datetime column found")

    # ---------------- TAB 2 ----------------
    with tab2:
        st.subheader("Epidemic Spread Modeling")

        fig = px.line(df, x=date_col, y=case_col, title='Case Progression')
        st.plotly_chart(fig)

        col1, col2, col3 = st.columns(3)

        total_cases = df[case_col].sum()
        peak_cases = df[case_col].max()

        growth = 0
        if df[case_col].iloc[0] != 0:
            growth = ((df[case_col].iloc[-1] - df[case_col].iloc[0]) / df[case_col].iloc[0]) * 100

        with col1:
            st.metric("Total Cases", f"{total_cases:,}")
        with col2:
            st.metric("Peak Cases", f"{peak_cases:,}")
        with col3:
            st.metric("Growth Rate", f"{growth:.1f}%")

    # ---------------- TAB 3 ----------------
    with tab3:
        st.subheader("Predictions & Forecast")

        pred_days = st.slider("Forecast Days", 1, 30, 7)

        last_value = df[case_col].iloc[-1]

        growth_rate = (
            df[case_col]
            .pct_change()
            .replace([float('inf'), -float('inf')], 0)
            .fillna(0)
            .mean()
        )

        st.write("📈 Growth Rate Used:", round(growth_rate, 4))

        if len(date_cols) > 0:
            future_dates = pd.date_range(start=df[date_col].iloc[-1], periods=pred_days+1)[1:]
        else:
            future_dates = list(range(1, pred_days+1))

        predictions = [
            last_value * (1 + growth_rate) ** i
            for i in range(1, pred_days + 1)
        ]

        pred_df = pd.DataFrame({
            'Date': future_dates,
            'Predicted Cases': predictions
        })

        st.dataframe(pred_df)

        fig_pred = px.line(pred_df, x='Date', y='Predicted Cases', title='Forecast')
        st.plotly_chart(fig_pred)

    # ---------------- TAB 4 (UPGRADED) ----------------
    with tab4:
        st.subheader("Intervention Impact Analysis")

        interventions = st.multiselect(
            "Select Interventions",
            ["Lockdown", "Vaccination", "Social Distancing", "Mask Mandate"]
        )

        effectiveness = st.slider("Base Effectiveness %", 0, 100, 50)

        base_cases = df[case_col].iloc[-1]

        impact_factors = {
            "Lockdown": 0.7,
            "Vaccination": 0.6,
            "Social Distancing": 0.5,
            "Mask Mandate": 0.4
        }

        if not interventions:
            st.warning("⚠️ Please select at least one intervention")
        else:
            total_effect = 0
            contributions = []

            for i, intervention in enumerate(interventions):
                factor = impact_factors[intervention]
                adjusted = effectiveness * factor * (0.9 ** i)
                total_effect += adjusted

                contributions.append({
                    "Intervention": intervention,
                    "Impact %": adjusted
                })

            total_effect = min(total_effect, 95)

            reduced_cases = base_cases * (1 - total_effect / 100)

            st.metric(
                "Cases after interventions",
                f"{reduced_cases:,.0f}",
                delta=f"-{total_effect:.1f}%"
            )

            # Comparison chart
            impact_data = pd.DataFrame({
                'Scenario': ['Current', 'After Interventions'],
                'Cases': [base_cases, reduced_cases]
            })

            fig_impact = px.bar(
                impact_data,
                x='Scenario',
                y='Cases',
                title='Combined Intervention Impact'
            )
            st.plotly_chart(fig_impact)

            # Contribution chart
            st.subheader("Intervention Contributions")

            contrib_df = pd.DataFrame(contributions)

            fig_contrib = px.bar(
                contrib_df,
                x='Intervention',
                y='Impact %',
                title='Individual Contribution'
            )

            st.plotly_chart(fig_contrib)

    # ---------------- TAB 5 ----------------
    with tab5:
        st.subheader("Comprehensive Report")

        st.write("### Policy Recommendations")
        recs = [
            "Implement targeted testing in high-risk areas",
            "Enhance healthcare infrastructure capacity",
            "Develop public awareness campaigns",
            "Establish data-driven containment zones"
        ]

        for i, rec in enumerate(recs, 1):
            st.write(f"{i}. {rec}")

        if st.button("📥 Download PDF Report"):
            buffer = io.BytesIO()
            doc = SimpleDocTemplate(buffer, pagesize=letter)
            styles = getSampleStyleSheet()
            story = []

            story.append(Paragraph(epidemic_title, styles['Title']))
            story.append(Spacer(1, 12))

            story.append(Paragraph("Data Summary", styles['Heading2']))
            story.append(Paragraph(f"Records: {len(df)} | Features: {len(df.columns)}", styles['Normal']))
            story.append(Spacer(1, 12))

            story.append(Paragraph("Key Findings", styles['Heading2']))

            findings = [
                f"Total cases analyzed: {total_cases:,}",
                "Peak infection period identified",
                f"Growth trend: {growth:.1f}% overall"
            ]

            for finding in findings:
                story.append(Paragraph(f"• {finding}", styles['Normal']))

            doc.build(story)
            buffer.seek(0)

            st.download_button(
                label="Download PDF",
                data=buffer,
                file_name="epidemic_report.pdf",
                mime="application/pdf"
            )

# Sidebar
st.sidebar.markdown("---")
st.sidebar.info("Upload your epidemic data file to begin analysis")
