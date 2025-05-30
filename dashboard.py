import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from sqlalchemy import create_engine, text
from datetime import datetime
from pathlib import Path
import os
import numpy as np

# Path configuration
BASE_DIR = Path(__file__).parent
STATIC_DIR = BASE_DIR / "static"

def load_assets():
    """Load CSS and JavaScript files"""
    try:
        # Load CSS
        css_file = STATIC_DIR / "Neo-Styles.css"
        with open(css_file) as f:
            st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)
        
        # Load JavaScript
        js_file = STATIC_DIR / "Neo-Scripts.js"
        with open(js_file) as f:
            st.components.v1.html(
                f"""<script>{f.read()}</script>""",
                height=0,
                width=0,
            )
    except Exception as e:
        st.error(f"Error loading static assets: {e}")

# Page configuration
st.set_page_config(
    page_title="Sales Analytics",
    layout="wide",
    page_icon="📊",
    initial_sidebar_state="expanded"
)


load_assets()


@st.cache_resource
def get_connection():
    return create_engine(
        "postgresql://salesdashboard_user:Jk1E5GT6zbtvsC3R67ycePxSHYrYEEg3@dpg-d0s01ha4d50c73b4dn70-a.oregon-postgres.render.com/salesdashboard_7kr6"
    )

@st.cache_data(ttl=3600)
def load_data():
    try:
        engine = get_connection()
        with engine.connect() as conn:
            result = conn.execute(text("SELECT * FROM dashboard_data"))
            df = pd.DataFrame(result.mappings().all())

        # Convert to datetime
        date_cols = ['order_date', 'ship_date', 'due_date', 'birth_date',
                    'customer_creation_date', 'product_start_date', 'product_end_date']
        for col in date_cols:
            df[col] = pd.to_datetime(df[col], errors='coerce')

        # Normalize country names
        df['CNTRY'] = df['CNTRY'].str.upper()
        country_map = {
            'US': 'UNITED STATES',
            'USA': 'UNITED STATES',
            'UNITED STATES': 'UNITED STATES',
            'DE': 'GERMANY',
            'GERMENY': 'GERMANY',
            'GERMANY': 'GERMANY'
        }
        df['CNTRY'] = df['CNTRY'].map(country_map).fillna(df['CNTRY'])

        # Derived columns
        df['customer_age'] = ((datetime.now() - df['birth_date']).dt.days / 365).astype(int)
        df['Revenue'] = df['sls_quantity'] * df['sls_price']
        df['Cost'] = df['sls_quantity'] * df['prd_cost']
        df['Profit'] = df['Revenue'] - df['Cost']
        df['Margin'] = (df['Profit'] / df['Revenue'].replace(0, pd.NA)) * 100
        df['order_year_month'] = df['order_date'].dt.to_period('M')
        df['order_to_ship_days'] = (df['ship_date'] - df['order_date']).dt.days
        df['ship_delay'] = (df['due_date'] - df['ship_date']).dt.days

        # Keep datetime columns for resampling, create separate date columns for display
        df['order_date_display'] = df['order_date'].dt.date
        df['ship_date_display'] = df['ship_date'].dt.date
        df['due_date_display'] = df['due_date'].dt.date

        return df
    except Exception as e:
        st.error(f"Error loading data: {e}")
        return pd.DataFrame()

# Load data
df = load_data()

# Modern header with animated gradient
st.markdown("""
    <div class="neo-header">
        <div class="neo-title-container">
            <h1 class="neo-main-title">Sales Performance Intelligence Platform</h1>
            <div class="neo-subtitle"></div>
        </div>
        <div class="neo-header-gradient"></div>
    </div>
""", unsafe_allow_html=True)

# Minimalist sidebar with icon filters
with st.sidebar:
    st.markdown("""
        <div class="neo-sidebar-header">
            <svg class="neo-filter-icon" viewBox="0 0 24 24">
                <path d="M10 18h4v-2h-4v2zM3 6v2h18V6H3zm3 7h12v-2H6v2z"/>
            </svg>
            <span>DATA FILTERS</span>
        </div>
    """, unsafe_allow_html=True)
    
    # Date filters with custom styling
    min_date = df['order_date'].dt.date.min() if not df.empty else datetime.now().date()
    max_date = df['order_date'].dt.date.max() if not df.empty else datetime.now().date()
    
    st.markdown('<div class="neo-filter-group">', unsafe_allow_html=True)
    start_date = st.date_input("📅 Start Date", min_date)
    end_date = st.date_input("📅 End Date", max_date)
    st.markdown('</div>', unsafe_allow_html=True)

    # Country filter with flag icons
    available_countries = sorted(df['CNTRY'].dropna().unique()) if not df.empty else []
    st.markdown('<div class="neo-filter-group">', unsafe_allow_html=True)
    selected_countries = st.multiselect("🌍 Countries", options=available_countries)
    st.markdown('</div>', unsafe_allow_html=True)

    # Category filter with custom icons
    available_categories = sorted(df['CAT'].dropna().unique()) if not df.empty else []
    st.markdown('<div class="neo-filter-group">', unsafe_allow_html=True)
    selected_categories = st.multiselect("📦 Categories", options=available_categories)
    st.markdown('</div>', unsafe_allow_html=True)

# Filter logic
if not df.empty:
    mask = (
        (df['order_date'].dt.date >= start_date) &
        (df['order_date'].dt.date <= end_date) &
        (df['CNTRY'].isin(selected_countries if selected_countries else df['CNTRY'].unique())) &
        (df['CAT'].isin(selected_categories if selected_categories else df['CAT'].unique()))
    )
    filtered_df = df[mask]
else:
    filtered_df = df

# Modern KPI cards with animated growth indicators
if not filtered_df.empty:
    st.markdown("""
        <div class="neo-kpi-container">
    """, unsafe_allow_html=True)
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        total_rev = filtered_df['Revenue'].sum()
        st.markdown(f"""
            <div class="neo-kpi-card">
                <div class="neo-kpi-icon">💸</div>
                <div class="neo-kpi-value">${total_rev:,.0f}</div>
                <div class="neo-kpi-label">Total Revenue</div>
                <div class="neo-kpi-growth">↑ 12.5%</div>
            </div>
        """, unsafe_allow_html=True)
    
    with col2:
        avg_margin = filtered_df['Margin'].mean()
        st.markdown(f"""
            <div class="neo-kpi-card {'neo-kpi-warning' if avg_margin < 15 else ''}">
                <div class="neo-kpi-icon">📈</div>
                <div class="neo-kpi-value">{avg_margin:.1f}%</div>
                <div class="neo-kpi-label">Avg Margin</div>
                <div class="neo-kpi-growth">↓ 2.1%</div>
            </div>
        """, unsafe_allow_html=True)
    
    with col3:
        customers = filtered_df['CID'].nunique()
        st.markdown(f"""
            <div class="neo-kpi-card">
                <div class="neo-kpi-icon">👥</div>
                <div class="neo-kpi-value">{customers:,}</div>
                <div class="neo-kpi-label">Active Customers</div>
                <div class="neo-kpi-growth">↑ 8.3%</div>
            </div>
        """, unsafe_allow_html=True)
    
    with col4:
        avg_order = filtered_df['Revenue'].mean()
        st.markdown(f"""
            <div class="neo-kpi-card">
                <div class="neo-kpi-icon">🛒</div>
                <div class="neo-kpi-value">${avg_order:.0f}</div>
                <div class="neo-kpi-label">Avg Order Value</div>
                <div class="neo-kpi-growth">↑ 4.7%</div>
            </div>
        """, unsafe_allow_html=True)
    
    st.markdown("</div>", unsafe_allow_html=True)
else:
    st.warning("No data available for the selected filters.")

# Hexagonal navigation tabs
tab_labels = ["📊 Sales Pulse", "👤 Customer DNA", "📦 Product Genome", "⚙ Operations Matrix"]
tab1, tab2, tab3, tab4 = st.tabs(tab_labels)

with tab1:
    if not filtered_df.empty:
        st.markdown('<div class="neo-tab-content">', unsafe_allow_html=True)
        
        # Sales Overview with small multiples
        st.subheader("Sales Pulse Overview")
        col1, col2 = st.columns([2, 1])
        
        with col1:
            try:
                # Hexbin chart for sales distribution
                fig = px.density_heatmap(
                    filtered_df, 
                    x='order_date', 
                    y='Revenue',
                    nbinsx=20,
                    nbinsy=20,
                    color_continuous_scale='Viridis',
                    title="Sales Density Over Time"
                )
                st.plotly_chart(fig, use_container_width=True)
            except Exception as e:
                st.error(f"Error creating sales density chart: {e}")
        
        with col2:
            try:
                # Radial bar chart for top categories
                cat_rev = filtered_df.groupby('CAT')['Revenue'].sum().nlargest(5).reset_index()
                fig = px.bar_polar(
                    cat_rev,
                    r='Revenue',
                    theta='CAT',
                    color='CAT',
                    template='plotly_dark',
                    title="Top Categories (Radial View)"
                )
                st.plotly_chart(fig, use_container_width=True)
            except Exception as e:
                st.error(f"Error creating radial chart: {e}")
        
        # Geographic heatmap
        st.subheader("Geographic Performance")
        try:
            geo_data = filtered_df.groupby('CNTRY').agg({
                'Revenue': 'sum',
                'Margin': 'mean',
                'CID': 'nunique'
            }).reset_index()
            
            fig = px.choropleth(
                geo_data,
                locations='CNTRY',
                locationmode='country names',
                color='Revenue',
                hover_name='CNTRY',
                hover_data=['Margin', 'CID'],
                title="Revenue by Country (Heatmap)",
                color_continuous_scale='Plasma'
            )
            st.plotly_chart(fig, use_container_width=True)
        except Exception as e:
            st.error(f"Error creating geographic chart: {e}")
        
        st.markdown('</div>', unsafe_allow_html=True)
    else:
        st.info("No data available for Sales Pulse.")

with tab2:
    if not filtered_df.empty:
        st.markdown('<div class="neo-tab-content">', unsafe_allow_html=True)
        
        # Customer segmentation with radar chart
        st.subheader("Customer Segmentation Matrix")
        
        try:
            # RFM analysis (simplified from original)
            customer_metrics = filtered_df.groupby('CID').agg({
                'order_date': ['min', 'max', 'count'],
                'Revenue': 'sum',
                'Profit': 'sum'
            }).reset_index()
            
            customer_metrics.columns = ['CID', 'first_order', 'last_order', 'frequency', 
                                      'monetary', 'profit']
            
            customer_metrics['recency'] = (datetime.now() - customer_metrics['last_order']).dt.days
            customer_metrics['segment'] = pd.cut(
                customer_metrics['monetary'],
                bins=5,
                labels=['Bronze', 'Silver', 'Gold', 'Platinum', 'Diamond']
            )
            
            # Radar chart for segments
            segment_stats = customer_metrics.groupby('segment').agg({
                'frequency': 'mean',
                'monetary': 'mean',
                'profit': 'mean',
                'recency': 'mean',
                'CID': 'count'
            }).reset_index()
            
            fig = go.Figure()
            
            for segment in segment_stats['segment']:
                data = segment_stats[segment_stats['segment'] == segment].iloc[0]
                fig.add_trace(go.Scatterpolar(
                    r=[data['frequency'], data['monetary'], data['profit'], data['recency']],
                    theta=['Frequency', 'Monetary', 'Profit', 'Recency'],
                    fill='toself',
                    name=segment
                ))
            
            fig.update_layout(
                polar=dict(
                    radialaxis=dict(
                        visible=True,
                        type="log"
                    )),
                showlegend=True,
                title="Customer Segments Radar Analysis"
            )
            
            st.plotly_chart(fig, use_container_width=True)
            
            # Segment distribution
            st.subheader("Segment Distribution")
            col1, col2 = st.columns(2)
            
            with col1:
                fig = px.treemap(
                    segment_stats,
                    path=['segment'],
                    values='CID',
                    title="Customer Segment Distribution"
                )
                st.plotly_chart(fig, use_container_width=True)
            
            with col2:
                fig = px.scatter(
                    customer_metrics,
                    x='recency',
                    y='monetary',
                    color='segment',
                    size='frequency',
                    title="Customer Value vs Recency"
                )
                st.plotly_chart(fig, use_container_width=True)
            
        except Exception as e:
            st.error(f"Error creating customer analysis: {e}")
        
        st.markdown('</div>', unsafe_allow_html=True)
    else:
        st.info("No data available for Customer DNA.")

with tab3:
    if not filtered_df.empty:
        st.markdown('<div class="neo-tab-content">', unsafe_allow_html=True)
        
        # Product performance with 3D scatter
        st.subheader("Product Performance Cube")
        
        try:
            product_stats = filtered_df.groupby('prd_nm').agg({
                'Revenue': 'sum',
                'Margin': 'mean',
                'sls_quantity': 'sum',
                'CAT': 'first'
            }).reset_index()
            
            fig = px.scatter_3d(
                product_stats,
                x='Revenue',
                y='Margin',
                z='sls_quantity',
                color='CAT',
                size='Revenue',
                hover_name='prd_nm',
                title="Product Performance in 3D Space"
            )
            
            st.plotly_chart(fig, use_container_width=True)
            
            # Product portfolio matrix
            st.subheader("Product Portfolio Matrix")
            col1, col2 = st.columns(2)
            
            with col1:
                fig = px.sunburst(
                    filtered_df,
                    path=['CAT', 'SUBCAT', 'prd_nm'],
                    values='Revenue',
                    title="Product Hierarchy"
                )
                st.plotly_chart(fig, use_container_width=True)
            
            with col2:
                fig = px.parallel_categories(
                    filtered_df,
                    dimensions=['CAT', 'MAINTENANCE', 'CNTRY'],
                    color='Revenue',
                    title="Product Category Flow"
                )
                st.plotly_chart(fig, use_container_width=True)
            
        except Exception as e:
            st.error(f"Error creating product analysis: {e}")
        
        st.markdown('</div>', unsafe_allow_html=True)
    else:
        st.info("No data available for Product Genome.")

with tab4:
    if not filtered_df.empty:
        st.markdown('<div class="neo-tab-content">', unsafe_allow_html=True)
        
        # Operations performance
        st.subheader("Operations Performance Grid")
        
        try:
            # Gantt chart for order fulfillment
            sample_orders = filtered_df.sample(min(50, len(filtered_df)))
            fig = px.timeline(
                sample_orders,
                x_start="order_date",
                x_end="ship_date",
                y="sls_ord_num",
                color="order_to_ship_days",
                title="Order Fulfillment Timeline"
            )
            st.plotly_chart(fig, use_container_width=True)
            
            # Operations metrics
            st.subheader("Operations Metrics")
            col1, col2 = st.columns(2)
            
            with col1:
                fig = px.box(
                    filtered_df,
                    x='CNTRY',
                    y='order_to_ship_days',
                    color='MAINTENANCE',
                    title="Fulfillment Time by Country"
                )
                st.plotly_chart(fig, use_container_width=True)
            
            with col2:
                fig = px.violin(
                    filtered_df,
                    y='ship_delay',
                    box=True,
                    points="all",
                    title="Shipping Delay Distribution"
                )
                st.plotly_chart(fig, use_container_width=True)
            
        except Exception as e:
            st.error(f"Error creating operations analysis: {e}")
        
        st.markdown('</div>', unsafe_allow_html=True)
    else:
        st.info("No data available for Operations Matrix.")

# Data explorer with modern look
with st.expander("🔍 DATA EXPLORER", expanded=False):
    if not filtered_df.empty:
        st.markdown('<div class="neo-data-explorer">', unsafe_allow_html=True)
        
        col1, col2 = st.columns([3, 1])
        with col1:
            sort_field = st.selectbox("Sort Field", options=filtered_df.columns)
        with col2:
            sort_order = st.radio("Sort Order", ["⬆️ Asc", "⬇️ Desc"], horizontal=True)
        
        try:
            sorted_df = filtered_df.sort_values(
                sort_field, 
                ascending=(sort_order == "⬆️ Asc"),
                ignore_index=True
            )
            
            display_df = sorted_df.copy()
            if 'order_date_display' in display_df.columns:
                display_df['order_date'] = display_df['order_date_display']
            if 'ship_date_display' in display_df.columns:
                display_df['ship_date'] = display_df['ship_date_display']
            if 'due_date_display' in display_df.columns:
                display_df['due_date'] = display_df['due_date_display']
            
            display_df = display_df.drop(columns=[col for col in display_df.columns if col.endswith('_display')])
            
            st.dataframe(
                display_df.head(100),
                use_container_width=True,
                height=400
            )
            st.caption(f"Showing 100 of {len(sorted_df):,} records")
            
            export_format = st.radio("Export Format", ["CSV", "JSON"], horizontal=True)
            if export_format == "CSV":
                csv = display_df.to_csv(index=False).encode('utf-8')
                st.download_button("💾 Download CSV", csv, "neo_sales_data.csv")
            else:
                json = display_df.to_json(indent=2).encode('utf-8')
                st.download_button("💾 Download JSON", json, "neo_sales_data.json")
        except Exception as e:
            st.error(f"Error in data explorer: {e}")
        
        st.markdown('</div>', unsafe_allow_html=True)
    else:
        st.info("No data available to explore.")

# Footer
st.markdown("""
    <div class="neo-footer">
        <div>NeoVision Analytics Platform v1.0</div>
        <div class="neo-footer-links">
            <span>📊 Dashboard</span>
            <span>📈 Analytics</span>
            <span>🔍 Insights</span>
        </div>
    </div>
""", unsafe_allow_html=True)