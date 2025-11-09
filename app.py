"""
Mai Shan Yun Inventory Intelligence Dashboard
Interactive dashboard for restaurant inventory management
"""
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime, timedelta
import sys
from pathlib import Path

# Add src to path
sys.path.append(str(Path(__file__).parent / "src"))

from data_loader import DataLoader
from analytics import InventoryAnalytics

# Try to import chatbot
try:
    from chatbot import InventoryChatbot
    CHATBOT_AVAILABLE = True
except ImportError:
    CHATBOT_AVAILABLE = False
    InventoryChatbot = None

# Page configuration
st.set_page_config(
    page_title="Mai Shan Yun Inventory Dashboard",
    page_icon="🍜",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
    <style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 2rem;
    }
    .metric-card {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 4px solid #1f77b4;
    }
    .stAlert {
        margin-top: 1rem;
    }
    </style>
""", unsafe_allow_html=True)

@st.cache_data(ttl=3600, show_spinner=False)  # Cache for 1 hour
def load_data(cache_version="v2.2"):  # Version parameter to force cache refresh (v2.2: fixed normalization + Peas+Carrot splitting)
    """Load all data files"""
    loader = DataLoader(data_dir="data")
    data = loader.load_all_data()
    return data

@st.cache_data(ttl=3600)  # Cache for 1 hour
def initialize_analytics(data):
    """Initialize analytics engine"""
    return InventoryAnalytics(data)

def main():
    # Header
    st.markdown('<h1 class="main-header">🍜 Mai Shan Yun Inventory Intelligence Dashboard</h1>', unsafe_allow_html=True)
    
    # Data loading section
    st.sidebar.header("📥 Data Management")
    
    # Reload button
    if st.sidebar.button("🔄 Reload"):
        st.cache_data.clear()
        st.rerun()
    
    # Check if MSY data exists (silently, no UI prompts)
    msy_ingredient_file = Path("data") / "MSY Data - Ingredient.csv"
    msy_shipment_file = Path("data") / "MSY Data - Shipment.csv"
    excel_files = list(Path("data").glob("*_Data_Matrix*.xlsx"))
    has_msy_data = msy_ingredient_file.exists() or msy_shipment_file.exists() or len(excel_files) > 0
    
    if not has_msy_data:
        st.sidebar.warning("⚠️ MSY data not found")
        st.sidebar.info("💡 Download real MSY data from the challenge repository")
        if st.sidebar.button("📥 Download MSY Data"):
            with st.spinner("Downloading MSY data from GitHub..."):
                try:
                    import subprocess
                    result = subprocess.run(["python", "download_msy_data.py"],
                                          capture_output=True, text=True, timeout=120)
                    if result.returncode == 0:
                        st.sidebar.success("✅ MSY data downloaded! Please refresh the page.")
                        st.rerun()
                    else:
                        st.sidebar.error(f"Download failed: {result.stderr}")
                except Exception as e:
                    st.sidebar.error(f"Error downloading data: {str(e)}")
                    st.sidebar.info("You can manually download data from:\nhttps://github.com/tamu-datathon-org/mai-shen-yun")
    
    # Load data
    with st.spinner("Loading MSY restaurant data..."):
        try:
            data = load_data(cache_version="v2.2")  # Updated version to clear cache (v2.2: fixed normalization + Peas+Carrot splitting)
            
            # Show data summary
            data_summary = []
            total_records = 0
            for key, df in data.items():
                if isinstance(df, pd.DataFrame):
                    row_count = len(df) if not df.empty else 0
                    total_records += row_count
                    # For ingredients, show tracked count (from purchases/usage) instead of raw count
                    if key == 'ingredients' and not df.empty and 'ingredient' in df.columns:
                        # Calculate actual tracked ingredients (those with purchase/usage data)
                        tracked_ingredients = set()
                        if 'purchases' in data and not data['purchases'].empty and 'ingredient' in data['purchases'].columns:
                            tracked_ingredients.update(data['purchases']['ingredient'].unique())
                        if 'usage' in data and not data['usage'].empty and 'ingredient' in data['usage'].columns:
                            tracked_ingredients.update(data['usage']['ingredient'].unique())
                        
                        tracked_count = len(tracked_ingredients) if tracked_ingredients else 0
                        
                        if tracked_count > 0:
                            data_summary.append(f"{key}: {tracked_count} ingredients")
                        else:
                            unique_count = df['ingredient'].nunique()
                            data_summary.append(f"{key}: {unique_count} ingredients")
                    else:
                        data_summary.append(f"{key}: {row_count} records")
            
            # Show data summary in expander
            if data_summary and total_records > 0:
                with st.sidebar.expander("📊 Data Summary"):
                    for summary in data_summary:
                        st.text(summary)
                    st.text(f"Total: {total_records} records")
                    
            elif data_summary:
                st.sidebar.warning("⚠️ Data loaded but appears empty")
                with st.sidebar.expander("📊 Data Summary"):
                    for summary in data_summary:
                        st.text(summary)
        except Exception as e:
            st.error(f"❌ Error loading data: {str(e)}")
            st.info("💡 Make sure MSY data files exist in the 'data' directory.")
            st.info("Required files:")
            st.info("- MSY Data - Ingredient.csv (recipe matrix)")
            st.info("- MSY Data - Shipment.csv (shipment frequency)")
            st.info("- Monthly Excel matrices (May-October)")
            if st.button("📥 Download MSY Data"):
                import subprocess
                with st.spinner("Downloading MSY data..."):
                    try:
                        result = subprocess.run(["python", "download_msy_data.py"], 
                                              capture_output=True, text=True, timeout=120)
                        if result.returncode == 0:
                            st.success("✅ MSY data downloaded! Please refresh the page.")
                            st.rerun()
                        else:
                            st.error(f"Download failed: {result.stderr}")
                    except Exception as e:
                        st.error(f"Error: {str(e)}")
            return
    
    # Check if we have at least some data
    has_any_data = data and any(
        (isinstance(df, pd.DataFrame) and not df.empty) 
        for df in data.values()
    )
    
    if not has_any_data:
        st.error("⚠️ No data loaded. Please ensure MSY data files are in the 'data' directory.")
        st.info("💡 Required files:")
        st.info("1. MSY Data - Ingredient.csv (recipe matrix)")
        st.info("2. MSY Data - Shipment.csv (shipment data)")
        st.info("3. Monthly Excel matrices (*_Data_Matrix*.xlsx)")
        if st.button("📥 Download MSY Data"):
            import subprocess
            with st.spinner("Downloading MSY data..."):
                try:
                    result = subprocess.run(["python", "download_msy_data.py"], 
                                          capture_output=True, text=True, timeout=120)
                    if result.returncode == 0:
                        st.success("✅ MSY data downloaded! Please refresh the page.")
                        st.rerun()
                    else:
                        st.error(f"Download failed: {result.stderr}")
                except Exception as e:
                    st.error(f"Error: {str(e)}")
        return
    
    # Initialize analytics
    try:
        analytics = initialize_analytics(data)
    except Exception as e:
        st.error(f"❌ Error initializing analytics: {str(e)}")
        return
    
    # Sidebar navigation
    st.sidebar.title("📊 Navigation")
    
    # Chatbot toggle
    if CHATBOT_AVAILABLE:
        st.sidebar.divider()
        chat_enabled = st.sidebar.checkbox("🤖 AI Chatbot", value=st.session_state.get('chat_enabled', False), 
                                           help="Enable AI assistant for natural language queries")
        st.session_state['chat_enabled'] = chat_enabled
    
    page = st.sidebar.selectbox(
        "Select Dashboard Section",
        [
            "🏠 Overview",
            "📦 Inventory Levels",
            "⚠️ Risk Alerts",
            "📈 Usage Trends",
            "🔮 Demand Forecasting",
            "🍽️ Menu Forecasting",
            "📋 Recipe Mapper",
            "🚚 Shipment Analysis",
            "💰 Cost Analysis",
            "💸 Cost vs Waste",
            "🧊 Storage Estimator",
            "📋 Reorder Recommendations",
            "🧪 What-If Simulator"
        ]
    )
    
    # Initialize chatbot if enabled
    chatbot = None
    if CHATBOT_AVAILABLE and chat_enabled:
        if 'chatbot' not in st.session_state:
            try:
                st.session_state.chatbot = InventoryChatbot(analytics)
                st.session_state.chat_history = []
            except Exception as e:
                st.sidebar.error(f"Chatbot error: {str(e)}")
                st.sidebar.info("Set OPENROUTER_API_KEY in .streamlit/secrets.toml or as environment variable")
                chat_enabled = False
        chatbot = st.session_state.get('chatbot')
    
    # Layout: if chat enabled, use 2 columns, else full width
    if chat_enabled and chatbot:
        main_col, chat_col = st.columns([2, 1])
        with main_col:
            # Display selected page
            display_page_content(page, analytics, data)
        with chat_col:
            show_chatbot_ui(chatbot, analytics)
    else:
        # Display selected page
        display_page_content(page, analytics, data)

def display_page_content(page, analytics, data):
    """Display the selected page content"""
    if page == "🏠 Overview":
        show_overview(analytics, data)
    elif page == "📦 Inventory Levels":
        show_inventory_levels(analytics)
    elif page == "⚠️ Risk Alerts":
        show_risk_alerts(analytics)
    elif page == "📈 Usage Trends":
        show_usage_trends(analytics, data)
    elif page == "🔮 Demand Forecasting":
        show_demand_forecasting(analytics, data)
    elif page == "🍽️ Menu Forecasting":
        show_menu_forecasting(analytics, data)
    elif page == "📋 Recipe Mapper":
        show_recipe_mapper(analytics, data)
    elif page == "🚚 Shipment Analysis":
        show_shipment_analysis(analytics, data)
    elif page == "💰 Cost Analysis":
        show_cost_analysis(analytics, data)
    elif page == "💸 Cost vs Waste":
        show_cost_waste_heatmap(analytics)
    elif page == "🧊 Storage Estimator":
        show_storage_estimator(analytics)
    elif page == "📋 Reorder Recommendations":
        show_reorder_recommendations(analytics)
    elif page == "🧪 What-If Simulator":
        show_what_if_simulator(analytics, data)

def show_overview(analytics, data):
    """Display overview dashboard with enhanced visualizations"""
    st.header("📊 Dashboard Overview")
    
    # Calculate key metrics
    inventory = analytics.calculate_inventory_levels()
    
    if inventory.empty:
        st.warning("No inventory data available.")
        return
    
    # Key metrics with enhanced styling
    col1, col2, col3, col4, col5 = st.columns(5)
    
    with col1:
        total_ingredients = len(inventory)
        st.metric("Total Ingredients", total_ingredients, help="Total number of ingredients tracked")
    
    with col2:
        low_stock = len(inventory[inventory['stock_status'] == 'Low'])
        st.metric("Low Stock Items", low_stock, 
                 delta=f"-{low_stock} need reorder" if low_stock > 0 else None,
                 delta_color="inverse",
                 help="Ingredients below minimum stock level")
    
    with col3:
        high_stock = len(inventory[inventory['stock_status'] == 'High'])
        st.metric("Overstocked Items", high_stock,
                 help="Ingredients above maximum stock level")
    
    with col4:
        reorder_count = inventory['reorder_needed'].sum()
        st.metric("Reorder Needed", int(reorder_count), 
                 delta="Urgent" if reorder_count > 0 else None,
                 delta_color="inverse",
                 help="Items that need immediate reordering")
    
    with col5:
        # Calculate menu viability if available
        try:
            menu_viability = analytics.calculate_menu_viability_score()
            st.metric("Menu Viability", f"{menu_viability:.0f}%",
                     help="Percentage of menu items that can be made with current stock")
        except:
            st.metric("Menu Viability", "N/A")
    
    st.divider()
    
    # Enhanced visualizations row 1
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("📊 Inventory Status Distribution")
        status_counts = inventory['stock_status'].value_counts()
        
        # Create enhanced pie chart with custom colors
        fig = px.pie(
            values=status_counts.values,
            names=status_counts.index,
            color_discrete_map={'Low': '#ff4444', 'Normal': '#44ff44', 'High': '#ffaa44'},
            hole=0.4,  # Donut chart for modern look
            title="Inventory Health Status"
        )
        fig.update_traces(
            textposition='inside', 
            textinfo='percent+label',
            marker=dict(line=dict(color='#FFFFFF', width=2))
        )
        fig.update_layout(showlegend=True, height=400)
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        st.subheader("⏱️ Days Until Stockout - Critical Items")
        critical_stockout = inventory[inventory['days_until_stockout'] < 30].copy()
        if not critical_stockout.empty:
            critical_stockout = critical_stockout.sort_values('days_until_stockout').head(10)
            
            # Create horizontal bar chart with gradient colors
            fig = px.bar(
                critical_stockout,
                x='days_until_stockout',
                y='ingredient',
                orientation='h',
                color='days_until_stockout',
                color_continuous_scale='Reds',
                labels={'days_until_stockout': 'Days Until Stockout', 'ingredient': 'Ingredient'},
                title="Items Running Out Soon"
            )
            fig.update_layout(
                yaxis={'categoryorder': 'total ascending'},
                height=400,
                xaxis_title="Days Remaining",
                yaxis_title=""
            )
            fig.add_vline(x=7, line_dash="dash", line_color="red", 
                         annotation_text="Critical (7 days)", annotation_position="top")
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("✅ No critical stockout items (all items have >30 days of stock)")
    
    st.divider()
    
    # Enhanced visualizations row 2 - Top ingredients
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("🔝 Top 10 Ingredients by Current Stock")
        top_stock = inventory.nlargest(10, 'current_stock')[['ingredient', 'current_stock', 'stock_status']]
        fig = px.bar(
            top_stock,
            x='current_stock',
            y='ingredient',
            orientation='h',
            color='stock_status',
            color_discrete_map={'Low': '#ff4444', 'Normal': '#44ff44', 'High': '#ffaa44'},
            labels={'current_stock': 'Current Stock', 'ingredient': 'Ingredient'},
            title="Highest Stock Levels"
        )
        fig.update_layout(yaxis={'categoryorder': 'total ascending'}, height=400)
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        # Risk alerts preview
        st.subheader("⚠️ Top Risk Items")
        try:
            risk_alerts = analytics.calculate_risk_alerts()
            if not risk_alerts.empty:
                top_risks = risk_alerts.head(10)
                fig = px.scatter(
                    top_risks,
                    x='current_stock',
                    y='risk_score',
                    size='usage_velocity_7d',
                    color='risk_type',
                    hover_name='ingredient',
                    labels={'current_stock': 'Current Stock', 'risk_score': 'Risk Score', 
                           'usage_velocity_7d': 'Usage Velocity'},
                    title="Risk Analysis: Stock vs. Risk Score",
                    color_discrete_sequence=px.colors.qualitative.Set3
                )
                fig.update_layout(height=400)
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("No risk alerts available")
        except:
            st.info("Risk analysis not available")
    
    st.divider()
    
    # Recent activity with enhanced visualization
    st.subheader("📋 Recent Activity Summary")
    
    col1, col2 = st.columns(2)
    
    with col1:
        if 'purchases' in data and not data['purchases'].empty:
            st.write("**Recent Purchases**")
            recent_purchases = data['purchases'].nlargest(10, 'date')[['date', 'ingredient', 'quantity', 'total_cost']].copy()
            recent_purchases['date'] = pd.to_datetime(recent_purchases['date']).dt.strftime('%Y-%m-%d')
            recent_purchases.columns = ['Date', 'Ingredient', 'Quantity', 'Total Cost ($)']
            st.dataframe(recent_purchases, use_container_width=True, hide_index=True)
        else:
            st.info("No purchase data available")
    
    with col2:
        if 'usage' in data and not data['usage'].empty:
            st.write("**Recent Usage**")
            recent_usage = data['usage'].nlargest(10, 'date')[['date', 'ingredient', 'quantity_used']].copy()
            if 'menu_item' in data['usage'].columns:
                recent_usage = data['usage'].nlargest(10, 'date')[['date', 'ingredient', 'quantity_used', 'menu_item']].copy()
                recent_usage['date'] = pd.to_datetime(recent_usage['date']).dt.strftime('%Y-%m-%d')
                recent_usage.columns = ['Date', 'Ingredient', 'Quantity Used', 'Menu Item']
            else:
                recent_usage['date'] = pd.to_datetime(recent_usage['date']).dt.strftime('%Y-%m-%d')
                recent_usage.columns = ['Date', 'Ingredient', 'Quantity Used']
            st.dataframe(recent_usage, use_container_width=True, hide_index=True)
        else:
            st.info("No usage data available")

def show_inventory_levels(analytics):
    """Display inventory levels dashboard"""
    st.header("📦 Inventory Levels")
    
    inventory = analytics.calculate_inventory_levels()
    
    if inventory.empty:
        st.warning("No inventory data available.")
        return
    
    # Filters
    col1, col2, col3 = st.columns(3)
    
    with col1:
        status_filter = st.multiselect(
            "Filter by Status",
            options=['Low', 'Normal', 'High'],
            default=['Low', 'Normal', 'High']
        )
    
    with col2:
        sort_by = st.selectbox(
            "Sort by",
            options=['current_stock', 'days_until_stockout', 'ingredient'],
            index=0
        )
    
    with col3:
        ascending = st.checkbox("Ascending", value=False)
    
    # Filter inventory
    filtered_inventory = inventory[inventory['stock_status'].isin(status_filter)].copy()
    filtered_inventory = filtered_inventory.sort_values(sort_by, ascending=ascending)
    
    # Display inventory table
    st.subheader("📊 Current Inventory Levels")
    
    # Format for display
    display_cols = ['ingredient', 'current_stock', 'min_stock_level', 'max_stock_level', 
                    'stock_status', 'days_until_stockout', 'reorder_needed']
    display_inventory = filtered_inventory[display_cols].copy()
    display_inventory['current_stock'] = display_inventory['current_stock'].round(2)
    display_inventory['days_until_stockout'] = display_inventory['days_until_stockout'].astype(int)
    display_inventory.columns = ['Ingredient', 'Current Stock', 'Min Level', 'Max Level', 
                                  'Status', 'Days Until Stockout', 'Reorder Needed']
    
    st.dataframe(display_inventory, use_container_width=True, hide_index=True)
    
    # Visualizations
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("📈 Stock Level vs. Thresholds")
        top_n = st.slider("Show top N ingredients", 5, 30, 15)
        top_inventory = filtered_inventory.nlargest(top_n, 'current_stock')
        
        fig = go.Figure()
        fig.add_trace(go.Bar(
            x=top_inventory['ingredient'],
            y=top_inventory['current_stock'],
            name='Current Stock',
            marker_color='lightblue'
        ))
        fig.add_trace(go.Scatter(
            x=top_inventory['ingredient'],
            y=top_inventory['min_stock_level'],
            name='Min Level',
            mode='lines+markers',
            line=dict(color='red', width=2, dash='dash')
        ))
        fig.add_trace(go.Scatter(
            x=top_inventory['ingredient'],
            y=top_inventory['max_stock_level'],
            name='Max Level',
            mode='lines+markers',
            line=dict(color='green', width=2, dash='dash')
        ))
        fig.update_layout(
            xaxis_tickangle=-45,
            yaxis_title="Quantity",
            hovermode='x unified'
        )
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        st.subheader("⏰ Days Until Stockout")
        stockout_data = filtered_inventory[filtered_inventory['days_until_stockout'] < 365].copy()
        stockout_data = stockout_data.sort_values('days_until_stockout', ascending=True).head(15)
        
        colors = ['red' if x < 7 else 'orange' if x < 30 else 'yellow' for x in stockout_data['days_until_stockout']]
        fig = px.bar(
            stockout_data,
            x='days_until_stockout',
            y='ingredient',
            orientation='h',
            color='days_until_stockout',
            color_continuous_scale='Reds_r',
            labels={'days_until_stockout': 'Days Until Stockout', 'ingredient': 'Ingredient'}
        )
        fig.update_layout(yaxis={'categoryorder': 'total ascending'})
        st.plotly_chart(fig, use_container_width=True)
    
    # Shelf-Life Tracker Section
    st.divider()
    st.subheader("🧊 Ingredient Shelf-Life Tracker")
    
    shelf_life = analytics.track_shelf_life()
    if not shelf_life.empty:
        # Expiring ingredients
        expiring_7d = analytics.get_expiring_ingredients(days_ahead=7)
        expiring_14d = analytics.get_expiring_ingredients(days_ahead=14)
        expiring_30d = analytics.get_expiring_ingredients(days_ahead=30)
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Expiring in 7 Days", len(expiring_7d))
        with col2:
            st.metric("Expiring in 14 Days", len(expiring_14d))
        with col3:
            st.metric("Expiring in 30 Days", len(expiring_30d))
        
        # Show expiring ingredients
        days_filter = st.selectbox("Show ingredients expiring within", [7, 14, 30], index=0)
        expiring = analytics.get_expiring_ingredients(days_ahead=days_filter)
        
        if not expiring.empty:
            st.write(f"**Ingredients expiring within {days_filter} days:**")
            display_expiring = expiring[['ingredient', 'remaining_quantity', 'days_until_expiration', 'expiration_status']].copy()
            display_expiring.columns = ['Ingredient', 'Remaining Quantity', 'Days Until Expiration', 'Status']
            st.dataframe(display_expiring, use_container_width=True, hide_index=True)
            
            # Use-it-now recipes
            if st.button("Get Recipe Suggestions"):
                expiring_ingredients = expiring['ingredient'].unique().tolist()
                recipes = analytics.get_use_it_now_recipes(expiring_ingredients)
                if not recipes.empty:
                    st.write("**Recommended Recipes to Use Expiring Ingredients:**")
                    st.dataframe(recipes, use_container_width=True, hide_index=True)
        else:
            st.info("No ingredients expiring within the selected timeframe.")
    else:
        st.info("Shelf-life tracking data not available. Ensure purchase data includes dates and ingredients have shelf_life_days.")

def show_usage_trends(analytics, data):
    """Display usage trends"""
    st.header("📈 Usage Trends")
    
    if 'usage' not in data or data['usage'].empty:
        st.warning("No usage data available.")
        st.info("💡 Usage data is generated from sales × recipe matrix.")
        st.info("Ensure sales data is loaded from Excel matrices.")
        return
    
    # Filters
    col1, col2 = st.columns(2)
    
    with col1:
        ingredients_list = data['usage']['ingredient'].unique().tolist() if 'ingredient' in data['usage'].columns else []
        selected_ingredient = st.selectbox(
            "Select Ingredient",
            options=['All'] + sorted(ingredients_list),
            index=0
        )
    
    with col2:
        period = st.selectbox(
            "Time Period",
            options=['daily', 'weekly', 'monthly'],
            index=2
        )
    
    # Get trends
    ingredient_filter = None if selected_ingredient == 'All' else selected_ingredient
    trends = analytics.get_usage_trends(ingredient=ingredient_filter, period=period)
    
    if trends.empty:
        st.warning("No trend data available for the selected criteria.")
        return
    
    # Usage trend chart
    st.subheader(f"📊 Usage Trends ({period.capitalize()})")
    fig = px.line(
        trends,
        x='period',
        y='quantity_used',
        labels={'period': 'Period', 'quantity_used': 'Quantity Used'},
        markers=True
    )
    fig.update_traces(line_width=2)
    st.plotly_chart(fig, use_container_width=True)
    
    # Top ingredients
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("🔝 Top Ingredients by Usage (Last 30 Days)")
        top_usage = analytics.get_top_ingredients(metric='usage', limit=10, period_days=30)
        if not top_usage.empty:
            fig = px.bar(
                top_usage,
                x='value',
                y='ingredient',
                orientation='h',
                labels={'value': 'Usage', 'ingredient': 'Ingredient'},
                color='value',
                color_continuous_scale='Blues'
            )
            fig.update_layout(yaxis={'categoryorder': 'total ascending'})
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No usage data available.")
    
    with col2:
        st.subheader("📊 Usage Distribution by Ingredient")
        if ingredient_filter:
            usage_data = data['usage'][data['usage']['ingredient'] == ingredient_filter].copy()
        else:
            usage_data = data['usage'].copy()
        
        if not usage_data.empty and 'ingredient' in usage_data.columns:
            usage_summary = usage_data.groupby('ingredient')['quantity_used'].sum().reset_index()
            usage_summary = usage_summary.sort_values('quantity_used', ascending=False).head(15)
            
            fig = px.pie(
                usage_summary,
                values='quantity_used',
                names='ingredient',
                title="Usage Distribution"
            )
            st.plotly_chart(fig, use_container_width=True)

def show_demand_forecasting(analytics, data):
    """Display demand forecasting"""
    st.header("🔮 Demand Forecasting")
    
    if 'usage' not in data or data['usage'].empty:
        st.warning("No usage data available for forecasting.")
        st.info("💡 Usage data is needed for forecasting. It's generated from sales × recipe matrix.")
        return
    
    # Ingredient selection
    ingredients_list = data['usage']['ingredient'].unique().tolist()
    selected_ingredient = st.selectbox(
        "Select Ingredient to Forecast",
        options=sorted(ingredients_list),
        index=0
    )
    
    col1, col2 = st.columns(2)
    
    with col1:
        forecast_days = st.slider("Forecast Days Ahead", 7, 90, 30)
    
    with col2:
        forecast_method = st.selectbox(
            "Forecast Method",
            options=['moving_average', 'linear_trend'],
            index=0
        )
    
    col3, col4 = st.columns(2)
    with col3:
        include_seasonality = st.checkbox("Include Seasonality Adjustments", value=True)
    with col4:
        include_holidays = st.checkbox("Include Holiday Adjustments", value=True)
    
    # Get forecast
    forecast = analytics.forecast_demand(
        selected_ingredient,
        days_ahead=forecast_days,
        method=forecast_method
    )
    
    # Apply seasonality and holiday adjustments
    if include_seasonality or include_holidays:
        forecast = analytics.adjust_forecast_for_events(selected_ingredient, forecast)
    
    # Show seasonality info
    if include_seasonality:
        seasonality = analytics.detect_seasonality(selected_ingredient)
        if seasonality.get('has_seasonality', False):
            st.info(f"📊 Seasonality detected: Peak in month {seasonality['peak_month']} (factor: {seasonality['peak_factor']:.2f}), "
                   f"Low in month {seasonality['low_month']} (factor: {seasonality['low_factor']:.2f})")
    
    if forecast.empty:
        st.warning("Forecast data not available for this ingredient.")
        return
    
    # Get historical data
    trends = analytics.get_usage_trends(ingredient=selected_ingredient, period='daily')
    
    # Combine historical and forecast
    st.subheader(f"📈 Demand Forecast for {selected_ingredient}")
    
    fig = go.Figure()
    
    # Historical data
    if not trends.empty:
        fig.add_trace(go.Scatter(
            x=trends['period'],
            y=trends['quantity_used'],
            name='Historical Usage',
            mode='lines+markers',
            line=dict(color='blue', width=2)
        ))
    
    # Forecast
    fig.add_trace(go.Scatter(
        x=forecast['date'],
        y=forecast['forecasted_usage'],
        name='Forecast',
        mode='lines+markers',
        line=dict(color='red', width=2, dash='dash')
    ))
    
    # Confidence intervals
    fig.add_trace(go.Scatter(
        x=forecast['date'].tolist() + forecast['date'].tolist()[::-1],
        y=forecast['confidence_high'].tolist() + forecast['confidence_low'].tolist()[::-1],
        fill='toself',
        fillcolor='rgba(255,0,0,0.2)',
        line=dict(color='rgba(255,255,255,0)'),
        name='Confidence Interval',
        showlegend=True
    ))
    
    fig.update_layout(
        xaxis_title="Date",
        yaxis_title="Quantity",
        hovermode='x unified',
        title=f"{selected_ingredient} - {forecast_days} Day Forecast"
    )
    st.plotly_chart(fig, use_container_width=True)
    
    # Forecast summary
    col1, col2, col3 = st.columns(3)
    
    with col1:
        avg_forecast = forecast['forecasted_usage'].mean()
        st.metric("Average Daily Forecast", f"{avg_forecast:.2f}")
    
    with col2:
        total_forecast = forecast['forecasted_usage'].sum()
        st.metric(f"Total Forecast ({forecast_days} days)", f"{total_forecast:.2f}")
    
    with col3:
        max_forecast = forecast['forecasted_usage'].max()
        st.metric("Peak Forecast", f"{max_forecast:.2f}")
    
    # Forecast table
    st.subheader("📋 Detailed Forecast")
    forecast_display = forecast.copy()
    forecast_display['date'] = forecast_display['date'].dt.strftime('%Y-%m-%d')
    forecast_display = forecast_display.round(2)
    forecast_display.columns = ['Date', 'Forecasted Usage', 'Confidence Low', 'Confidence High']
    st.dataframe(forecast_display, use_container_width=True, hide_index=True)

def show_shipment_analysis(analytics, data):
    """Display shipment analysis"""
    st.header("🚚 Shipment Analysis")
    
    if 'shipments' not in data or data['shipments'].empty:
        st.warning("No shipment data available.")
        return
    
    shipments = data['shipments'].copy()
    
    # Delay analysis
    delay_analysis = analytics.analyze_shipment_delays()
    
    # Show shipment frequency data if delay analysis is not available
    if delay_analysis.empty and not shipments.empty:
        # Show shipment frequency data
        if 'ingredient' in shipments.columns and 'frequency' in shipments.columns:
            st.subheader("📊 Shipment Frequency by Ingredient")
            shipment_summary = shipments.groupby('ingredient').agg({
                'quantity': 'first' if 'quantity' in shipments.columns else 'count',
                'frequency': 'first',
                'num_shipments': 'first' if 'num_shipments' in shipments.columns else 'count'
            }).reset_index()
            # Rename columns for better display
            if 'quantity' in shipment_summary.columns:
                shipment_summary = shipment_summary.rename(columns={'quantity': 'Quantity per Shipment'})
            if 'frequency' in shipment_summary.columns:
                shipment_summary = shipment_summary.rename(columns={'frequency': 'Frequency'})
            if 'num_shipments' in shipment_summary.columns:
                shipment_summary = shipment_summary.rename(columns={'num_shipments': 'Number of Shipments'})
            shipment_summary = shipment_summary.rename(columns={'ingredient': 'Ingredient'})
            st.dataframe(shipment_summary, use_container_width=True, hide_index=True)
    
    if not delay_analysis.empty:
        st.subheader("⏱️ Shipment Delay Analysis")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            avg_delay = delay_analysis['avg_delay'].mean()
            st.metric("Average Delay (Days)", f"{avg_delay:.2f}")
        
        with col2:
            max_delay = delay_analysis['max_delay'].max()
            st.metric("Max Delay (Days)", f"{max_delay:.0f}")
        
        with col3:
            total_delayed = delay_analysis['delayed_count'].sum()
            total_shipments = delay_analysis['total_shipments'].sum()
            delay_rate = (total_delayed / total_shipments * 100) if total_shipments > 0 else 0
            st.metric("Delay Rate", f"{delay_rate:.1f}%")
        
        # Delay by ingredient
        st.subheader("📊 Average Delay by Ingredient")
        top_delays = delay_analysis.nlargest(15, 'avg_delay')
        fig = px.bar(
            top_delays,
            x='avg_delay',
            y='ingredient',
            orientation='h',
            color='avg_delay',
            color_continuous_scale='Reds',
            labels={'avg_delay': 'Average Delay (Days)', 'ingredient': 'Ingredient'}
        )
        fig.update_layout(yaxis={'categoryorder': 'total ascending'})
        st.plotly_chart(fig, use_container_width=True)
        
        # Delay table
        st.subheader("📋 Delay Analysis Details")
        delay_display = delay_analysis[['ingredient', 'avg_delay', 'max_delay', 'total_shipments', 'delayed_count', 'delay_rate']].copy()
        delay_display = delay_display.round(2)
        delay_display.columns = ['Ingredient', 'Avg Delay (Days)', 'Max Delay (Days)', 'Total Shipments', 'Delayed Count', 'Delay Rate']
        st.dataframe(delay_display, use_container_width=True, hide_index=True)
    
    # Shipment frequency
    if 'date' in shipments.columns:
        st.subheader("📈 Shipment Frequency Over Time")
        shipments['date'] = pd.to_datetime(shipments['date'])
        shipments_by_date = shipments.groupby(shipments['date'].dt.to_period('M')).size().reset_index()
        shipments_by_date['date'] = shipments_by_date['date'].astype(str)
        
        fig = px.bar(
            shipments_by_date,
            x='date',
            y=0,
            labels={'date': 'Month', '0': 'Number of Shipments'}
        )
        st.plotly_chart(fig, use_container_width=True)
    
    # Status distribution
    if 'status' in shipments.columns:
        st.subheader("📊 Shipment Status Distribution")
        status_counts = shipments['status'].value_counts()
        fig = px.pie(
            values=status_counts.values,
            names=status_counts.index
        )
        st.plotly_chart(fig, use_container_width=True)
    
    # Supplier Reliability Section
    st.divider()
    enhance_shipment_analysis(analytics, data)

def show_cost_analysis(analytics, data):
    """Display cost analysis"""
    st.header("💰 Cost Analysis")
    
    if 'purchases' not in data or data['purchases'].empty:
        st.warning("No purchase data available.")
        return
    
    # Time period filter
    period_days = st.slider("Analysis Period (Days)", 7, 365, 30)
    
    # Get cost analysis
    cost_analysis = analytics.get_cost_analysis(period_days=period_days)
    
    if not cost_analysis:
        st.warning("Cost analysis data not available.")
        return
    
    # Key metrics
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Total Spending", f"${cost_analysis.get('total_spending', 0):,.2f}")
    
    with col2:
        st.metric("Average Daily Spending", f"${cost_analysis.get('avg_daily_spending', 0):,.2f}")
    
    with col3:
        days_in_period = period_days
        projected_monthly = cost_analysis.get('avg_daily_spending', 0) * 30
        st.metric("Projected Monthly Spending", f"${projected_monthly:,.2f}")
    
    # Spending trends
    if 'spending_trend' in cost_analysis and not cost_analysis['spending_trend'].empty:
        st.subheader("📈 Spending Trend Over Time")
        spending_trend = cost_analysis['spending_trend'].copy()
        spending_trend.columns = ['date', 'total_cost']
        fig = px.line(
            spending_trend,
            x='date',
            y='total_cost',
            labels={'date': 'Date', 'total_cost': 'Total Cost ($)'},
            markers=True
        )
        st.plotly_chart(fig, use_container_width=True)
    
    # Top spending ingredients
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("🔝 Top Ingredients by Cost")
        top_cost = analytics.get_top_ingredients(metric='cost', limit=15, period_days=period_days)
        if not top_cost.empty:
            fig = px.bar(
                top_cost,
                x='value',
                y='ingredient',
                orientation='h',
                labels={'value': 'Total Cost ($)', 'ingredient': 'Ingredient'},
                color='value',
                color_continuous_scale='Greens'
            )
            fig.update_layout(yaxis={'categoryorder': 'total ascending'})
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No cost data available.")
    
    with col2:
        st.subheader("🏢 Spending by Supplier")
        if 'spending_by_supplier' in cost_analysis and cost_analysis['spending_by_supplier']:
            supplier_spending = pd.DataFrame([
                {'supplier': k, 'total_cost': v}
                for k, v in cost_analysis['spending_by_supplier'].items()
            ])
            supplier_spending = supplier_spending.sort_values('total_cost', ascending=False)
            
            fig = px.pie(
                supplier_spending,
                values='total_cost',
                names='supplier',
                title="Spending Distribution by Supplier"
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Supplier data not available.")

def show_reorder_recommendations(analytics):
    """Display reorder recommendations"""
    st.header("📋 Reorder Recommendations")
    
    # Include seasonality toggle
    include_seasonality = st.checkbox("Include Seasonality in Recommendations", value=True)
    
    try:
        recommendations = analytics.calculate_reorder_recommendations(include_seasonality=include_seasonality)
    except Exception as e:
        st.error(f"Error calculating recommendations: {str(e)}")
        st.info("This might be due to missing inventory or forecast data.")
        return
    
    if recommendations.empty:
        st.warning("No reorder recommendations available.")
        st.info("💡 This usually means:")
        st.info("1. Inventory levels cannot be calculated (missing purchases/usage)")
        st.info("2. All items are well-stocked")
        st.info("3. Forecast data is unavailable")
        return
    
    # Filter by urgency only (removed confusing confidence filter)
    urgency_filter = st.multiselect(
        "Filter by Urgency",
        options=['Critical', 'High', 'Medium', 'Low'],
        default=['Critical', 'High', 'Medium', 'Low']
    )
    
    filtered_recommendations = recommendations[recommendations['urgency'].isin(urgency_filter)].copy()
    
    # Summary metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        critical = len(filtered_recommendations[filtered_recommendations['urgency'] == 'Critical'])
        st.metric("Critical", critical, delta="⚠️ Urgent" if critical > 0 else None)
    
    with col2:
        high = len(filtered_recommendations[filtered_recommendations['urgency'] == 'High'])
        st.metric("High", high)
    
    with col3:
        medium = len(filtered_recommendations[filtered_recommendations['urgency'] == 'Medium'])
        st.metric("Medium", medium)
    
    with col4:
        total_reorder = filtered_recommendations['recommended_order_quantity'].sum()
        st.metric("Total Recommended Order", f"{total_reorder:.0f}")
    
    # Recommendations table
    st.subheader("📊 Detailed Reorder Recommendations")
    
    # Build display columns
    display_cols = ['ingredient', 'current_stock', 'min_stock_level', 'days_until_stockout',
                   'forecasted_demand_30d', 'recommended_order_quantity', 'urgency', 
                   'estimated_lead_time_days', 'reorder_date']
    
    # Add data quality if available
    if 'data_quality' in filtered_recommendations.columns:
        display_cols.append('data_quality')
    
    # Only select columns that exist
    display_cols = [col for col in display_cols if col in filtered_recommendations.columns]
    display_recommendations = filtered_recommendations[display_cols].copy()
    
    # Format dates
    if 'reorder_date' in display_recommendations.columns:
        display_recommendations['reorder_date'] = pd.to_datetime(display_recommendations['reorder_date']).dt.strftime('%Y-%m-%d')
    
    # Round numeric columns
    numeric_cols = ['current_stock', 'forecasted_demand_30d', 'recommended_order_quantity']
    for col in numeric_cols:
        if col in display_recommendations.columns:
            display_recommendations[col] = display_recommendations[col].round(2)
    
    if 'days_until_stockout' in display_recommendations.columns:
        display_recommendations['days_until_stockout'] = display_recommendations['days_until_stockout'].round(1)
    if 'estimated_lead_time_days' in display_recommendations.columns:
        display_recommendations['estimated_lead_time_days'] = display_recommendations['estimated_lead_time_days'].astype(int)
    
    # Set column names
    col_names = [
        'Ingredient', 'Current Stock', 'Min Stock Level', 'Days Until Stockout',
        'Forecasted Demand (30d)', 'Recommended Order Qty', 'Urgency',
        'Lead Time (Days)', 'Recommended Reorder Date'
    ]
    if 'data_quality' in display_recommendations.columns:
        col_names.append('Data Quality')
    
    display_recommendations.columns = col_names
    
    st.dataframe(display_recommendations, use_container_width=True, hide_index=True)
    
    # Visualizations
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("📊 Recommended Order Quantities")
        top_orders = filtered_recommendations.nlargest(15, 'recommended_order_quantity')
        fig = px.bar(
            top_orders,
            x='recommended_order_quantity',
            y='ingredient',
            orientation='h',
            color='urgency',
            color_discrete_map={
                'Critical': 'red',
                'High': 'orange',
                'Medium': 'yellow',
                'Low': 'green'
            },
            labels={'recommended_order_quantity': 'Recommended Order Quantity', 'ingredient': 'Ingredient'}
        )
        fig.update_layout(yaxis={'categoryorder': 'total ascending'})
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        st.subheader("⏰ Urgency Distribution")
        urgency_counts = filtered_recommendations['urgency'].value_counts()
        fig = px.pie(
            values=urgency_counts.values,
            names=urgency_counts.index,
            color_discrete_map={
                'Critical': 'red',
                'High': 'orange',
                'Medium': 'yellow',
                'Low': 'green'
            }
        )
        st.plotly_chart(fig, use_container_width=True)

def show_risk_alerts(analytics):
    """Display real-time inventory risk alerts"""
    st.header("⚠️ Real-Time Inventory Risk Alerts")
    
    try:
        risk_alerts = analytics.calculate_risk_alerts()
    except Exception as e:
        st.error(f"Error calculating risk alerts: {str(e)}")
        st.info("This might be due to missing inventory or usage data.")
        return
    
    if risk_alerts.empty:
        st.warning("No risk alert data available.")
        st.info("💡 This usually means:")
        st.info("1. Inventory levels cannot be calculated")
        st.info("2. Usage data is missing (needed for velocity calculations)")
        return
    
    # Summary metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        high_risk = len(risk_alerts[risk_alerts['risk_score'] >= 50])
        st.metric("High Risk Items", high_risk, delta="⚠️" if high_risk > 0 else None)
    
    with col2:
        needs_reorder = risk_alerts['needs_reorder'].sum()
        st.metric("Needs Reorder", int(needs_reorder), delta="Urgent" if needs_reorder > 0 else None)
    
    with col3:
        overstock = len(risk_alerts[risk_alerts['risk_type'].str.contains('Overstock', na=False)])
        st.metric("Overstocked Items", overstock)
    
    with col4:
        avg_risk_score = risk_alerts['risk_score'].mean()
        st.metric("Average Risk Score", f"{avg_risk_score:.1f}")
    
    st.divider()
    
    # Filter by risk level
    risk_filter = st.multiselect(
        "Filter by Risk Type",
        options=risk_alerts['risk_type'].unique().tolist(),
        default=risk_alerts['risk_type'].unique().tolist()
    )
    
    filtered_alerts = risk_alerts[risk_alerts['risk_type'].isin(risk_filter)].copy()
    filtered_alerts = filtered_alerts.sort_values('risk_score', ascending=False)
    
    # Display risk alerts table
    st.subheader("📊 Risk Alerts Details")
    display_alerts = filtered_alerts[['ingredient', 'current_stock', 'min_stock_level', 'max_stock_level',
                                     'usage_velocity_7d', 'days_until_stockout', 'risk_score', 'risk_type', 'needs_reorder']].copy()
    display_alerts.columns = ['Ingredient', 'Current Stock', 'Min Level', 'Max Level',
                             'Usage Velocity (7d)', 'Days Until Stockout', 'Risk Score', 'Risk Type', 'Needs Reorder']
    st.dataframe(display_alerts, use_container_width=True, hide_index=True)
    
    # Reorder Now button for critical items
    critical_items = filtered_alerts[filtered_alerts['needs_reorder'] == True]
    if not critical_items.empty:
        st.subheader("🚨 Critical Items - Reorder Now")
        for _, item in critical_items.head(5).iterrows():
            col1, col2, col3 = st.columns([3, 1, 1])
            with col1:
                st.write(f"**{item['ingredient']}** - Risk Score: {item['risk_score']:.0f} - {item['risk_type']}")
            with col2:
                if st.button(f"Reorder Now", key=f"reorder_{item['ingredient']}"):
                    st.success(f"Reorder request sent for {item['ingredient']}")
            with col3:
                st.write(f"Days until stockout: {item['days_until_stockout']:.0f}")
    
    # Visualizations
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("📊 Risk Score Distribution")
        fig = px.histogram(
            filtered_alerts,
            x='risk_score',
            nbins=20,
            labels={'risk_score': 'Risk Score', 'count': 'Number of Ingredients'}
        )
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        st.subheader("📈 Top Risk Items")
        top_risks = filtered_alerts.head(10)
        fig = px.bar(
            top_risks,
            x='risk_score',
            y='ingredient',
            orientation='h',
            color='risk_score',
            color_continuous_scale='Reds',
            labels={'risk_score': 'Risk Score', 'ingredient': 'Ingredient'}
        )
        fig.update_layout(yaxis={'categoryorder': 'total ascending'})
        st.plotly_chart(fig, use_container_width=True)

def show_menu_forecasting(analytics, data):
    """Display menu-driven ingredient forecasting"""
    st.header("🍽️ Menu-Driven Ingredient Forecasting")
    
    if 'usage' not in data or data['usage'].empty or 'menu_item' not in data['usage'].columns:
        st.warning("Menu item data not available. Ensure usage data includes menu_item column.")
        return
    
    if 'sales' not in data or data['sales'].empty:
        st.warning("Sales data not available for menu forecasting.")
        return
    
    # Ingredient selection
    ingredients_list = data['usage']['ingredient'].unique().tolist()
    selected_ingredient = st.selectbox(
        "Select Ingredient to Forecast",
        options=sorted(ingredients_list),
        index=0
    )
    
    forecast_days = st.slider("Forecast Days Ahead", 7, 90, 30)
    
    # Get menu-driven forecast
    try:
        forecast = analytics.forecast_by_menu_trends(selected_ingredient, days_ahead=forecast_days)
    except Exception as e:
        st.error(f"Error generating forecast: {str(e)}")
        st.info("This might be due to missing menu item or sales data.")
        return
    
    if forecast.empty:
        st.warning("Forecast data not available for this ingredient.")
        st.info("💡 This usually means:")
        st.info("1. No menu items use this ingredient")
        st.info("2. Sales data doesn't match menu items in recipe matrix")
        st.info("3. Insufficient historical sales data")
        return
    
    # Display forecast summary
    st.subheader(f"📈 Menu-Driven Forecast for {selected_ingredient}")
    
    # Determine unit for display (check if ingredient is count-based)
    if analytics.preprocessor:
        is_count_based = analytics.preprocessor.is_count_based_ingredient(selected_ingredient)
        display_unit = "count" if is_count_based else "units"
    else:
        ingredient_lower = str(selected_ingredient).lower()
        is_count_based = any(keyword in ingredient_lower for keyword in ['wing', 'ramen', 'egg', 'noodle'])
        display_unit = "count" if is_count_based else "units"
    
    # Show summary metrics with smaller font
    col1, col2, col3 = st.columns(3)
    with col1:
        daily_forecast = forecast['forecasted_usage'].iloc[0] if not forecast.empty else 0
        if is_count_based:
            daily_forecast = round(daily_forecast)
        forecast_str = f"{daily_forecast:,.0f} ({display_unit})" if is_count_based else f"{daily_forecast:.2f} ({display_unit})"
        st.markdown(f"**Daily Forecast**<br><span style='font-size: 0.9em'>{forecast_str}</span>", unsafe_allow_html=True)
    with col2:
        total_forecast = forecast['forecasted_usage'].sum() if not forecast.empty else 0
        if is_count_based:
            total_forecast = round(total_forecast)
        forecast_str = f"{total_forecast:,.0f} ({display_unit})" if is_count_based else f"{total_forecast:.2f} ({display_unit})"
        st.markdown(f"**Total Forecast ({forecast_days} days)**<br><span style='font-size: 0.9em'>{forecast_str}</span>", unsafe_allow_html=True)
    with col3:
        avg_forecast = forecast['forecasted_usage'].mean() if not forecast.empty else 0
        if is_count_based:
            avg_forecast = round(avg_forecast)
        forecast_str = f"{avg_forecast:,.0f} ({display_unit})" if is_count_based else f"{avg_forecast:.2f} ({display_unit})"
        st.markdown(f"**Average Daily**<br><span style='font-size: 0.9em'>{forecast_str}</span>", unsafe_allow_html=True)
    
    # Display forecast chart
    fig = px.line(
        forecast,
        x='date',
        y='forecasted_usage',
        labels={'date': 'Date', 'forecasted_usage': 'Daily Forecasted Usage'},
        markers=True,
        title=f"Daily Ingredient Demand Forecast ({forecast_days} days ahead)"
    )
    fig.add_trace(go.Scatter(
        x=forecast['date'].tolist() + forecast['date'].tolist()[::-1],
        y=forecast['confidence_high'].tolist() + forecast['confidence_low'].tolist()[::-1],
        fill='toself',
        fillcolor='rgba(0,100,255,0.2)',
        line=dict(color='rgba(255,255,255,0)'),
        name='Confidence Interval',
        showlegend=True
    ))
    fig.update_layout(
        xaxis_title="Date",
        yaxis_title="Daily Forecasted Usage",
        hovermode='x unified'
    )
    st.plotly_chart(fig, use_container_width=True)
    
    st.caption(f"💡 The daily forecast stays constant, but the total forecast increases with more days. Total = {daily_forecast:.2f} × {forecast_days} days = {total_forecast:.2f}")
    
    # Ingredient impact scores
    st.subheader("📊 Ingredient Impact Scores by Menu Item")
    impact_scores = analytics.calculate_ingredient_impact_score()
    
    if not impact_scores.empty:
        # Filter for selected ingredient
        ingredient_impact = impact_scores[impact_scores['ingredient'] == selected_ingredient].copy()
        if not ingredient_impact.empty:
            ingredient_impact = ingredient_impact.sort_values('impact_score', ascending=False)
            
            fig = px.bar(
                ingredient_impact,
                x='impact_score',
                y='menu_item',
                orientation='h',
                color='impact_score',
                color_continuous_scale='Blues',
                labels={'impact_score': 'Impact Score', 'menu_item': 'Menu Item'}
            )
            fig.update_layout(yaxis={'categoryorder': 'total ascending'})
            st.plotly_chart(fig, use_container_width=True)
            
            # Rename column for clarity and format with units
            display_impact = ingredient_impact.copy()
            
            # Format usage_per_serving with unit in brackets
            if 'usage_unit' in display_impact.columns:
                display_impact['Usage Per Serving'] = display_impact.apply(
                    lambda row: f"{row['usage_per_serving']} ({row['usage_unit']})" 
                    if pd.notna(row['usage_per_serving']) else "N/A",
                    axis=1
                )
            else:
                display_impact['Usage Per Serving'] = display_impact['usage_per_serving']
            
            display_impact = display_impact.rename(columns={
                'popularity_score': 'Popularity Score',
                'impact_score': 'Impact Score'
            })
            st.dataframe(display_impact[['menu_item', 'Usage Per Serving', 'Popularity Score', 'Impact Score']], 
                        use_container_width=True, hide_index=True)
            st.caption("💡 Usage Per Serving = amount of ingredient needed to make 1 serving of this dish")
        else:
            st.info("No impact score data available for this ingredient.")
    else:
        st.info("Impact score calculation not available.")

def show_recipe_mapper(analytics, data):
    """Display recipe-to-inventory mapper"""
    st.header("📋 Recipe-to-Inventory Mapper")
    
    if 'usage' not in data or data['usage'].empty or 'menu_item' not in data['usage'].columns:
        st.warning("Menu item data not available. Ensure usage data includes menu_item column.")
        return
    
    # Calculate menu viability
    try:
        menu_viability = analytics.map_recipes_to_inventory()
        menu_viability_score = analytics.calculate_menu_viability_score()
    except Exception as e:
        st.error(f"Error calculating menu viability: {str(e)}")
        st.info("This might be due to missing inventory or recipe data.")
        return
    
    # Display menu viability score
    st.subheader("📊 Menu Viability Summary")
    col1, col2, col3 = st.columns(3)
    
    # Calculate counts
    if not menu_viability.empty:
        can_make_count = len(menu_viability[menu_viability['servings_possible'] > 0]) if 'servings_possible' in menu_viability.columns else 0
        cannot_make_count = len(menu_viability[menu_viability['servings_possible'] == 0]) if 'servings_possible' in menu_viability.columns else 0
        total_items = len(menu_viability)
    else:
        can_make_count = 0
        cannot_make_count = 0
        total_items = 0
    
    with col1:
        st.metric("Overall Menu Viability", f"{menu_viability_score:.1f}%")
    with col2:
        st.metric("Can Be Made", can_make_count, help="Number of dishes that can be made with current inventory")
    with col3:
        st.metric("Cannot Be Made", cannot_make_count, help="Number of dishes that cannot be made (missing ingredients)")
    
    st.divider()
    
    if menu_viability.empty:
        st.warning("Menu viability data not available.")
        return
    
    # Filter by can make / cannot make
    filter_option = st.selectbox(
        "Filter Dishes",
        options=['Can Be Made', 'Cannot Be Made'],
        index=0,
        help="Filter dishes by whether they can be made with current inventory"
    )
    
    # Apply filter
    if filter_option == 'Can Be Made':
        filtered_viability = menu_viability[menu_viability['servings_possible'] > 0].copy()
    else:  # Cannot Be Made
        filtered_viability = menu_viability[menu_viability['servings_possible'] == 0].copy()
    
    filtered_viability = filtered_viability.sort_values('servings_possible', ascending=False)
    
    # Display menu viability table
    st.subheader("📋 Menu Item Details")
    
    # Prepare display columns
    display_cols = ['menu_item', 'servings_possible']
    if 'viability_status' in filtered_viability.columns:
        display_cols.append('viability_status')
    if 'missing_ingredients' in filtered_viability.columns:
        display_cols.append('missing_ingredients')
    
    display_viability = filtered_viability[display_cols].copy()
    
    # Ensure servings_possible is never negative
    display_viability['servings_possible'] = display_viability['servings_possible'].apply(lambda x: max(0, int(x)) if pd.notna(x) else 0)
    
    # Rename columns
    col_names = ['Menu Item', 'Servings Possible']
    if 'viability_status' in display_viability.columns:
        col_names.append('Status')
    if 'missing_ingredients' in display_viability.columns:
        col_names.append('Missing Ingredients')
    
    display_viability.columns = col_names
    
    # Show message if no dishes match the filter
    if filter_option == 'Can Be Made' and display_viability.empty:
        st.info("No dishes can be made with current inventory. Switch to 'Cannot Be Made' to see missing ingredients.")
    elif filter_option == 'Cannot Be Made' and display_viability.empty:
        st.success("All dishes can be made! No missing ingredients.")
    else:
        st.dataframe(display_viability, use_container_width=True, hide_index=True)
    
    # Visualizations
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("📊 Servings Possible by Menu Item")
        top_viable = filtered_viability.head(15)
        fig = px.bar(
            top_viable,
            x='servings_possible',
            y='menu_item',
            orientation='h',
            color='viability_status',
            color_discrete_map={
                'High Viability': 'green',
                'Medium Viability': 'yellow',
                'Low Viability': 'orange',
                'Cannot Make': 'red'
            },
            labels={'servings_possible': 'Servings Possible', 'menu_item': 'Menu Item'}
        )
        fig.update_layout(yaxis={'categoryorder': 'total ascending'})
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        st.subheader("📈 Viability Status Distribution")
        status_counts = filtered_viability['viability_status'].value_counts()
        fig = px.pie(
            values=status_counts.values,
            names=status_counts.index,
            color_discrete_map={
                'High Viability': 'green',
                'Medium Viability': 'yellow',
                'Low Viability': 'orange',
                'Cannot Make': 'red'
            }
        )
        st.plotly_chart(fig, use_container_width=True)

def show_cost_waste_heatmap(analytics):
    """Display cost vs waste heatmap"""
    st.header("💸 Cost vs. Waste Heatmap")
    
    period_days = st.slider("Analysis Period (Days)", 7, 365, 30)
    
    waste_analysis = analytics.calculate_waste_analysis(period_days=period_days)
    heatmap_data = analytics.get_cost_waste_heatmap_data(period_days=period_days)
    
    if waste_analysis.empty:
        st.warning("Waste analysis data not available.")
        return
    
    # Summary metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        total_waste = waste_analysis['waste'].sum()
        st.metric("Total Waste", f"{total_waste:.2f}")
    
    with col2:
        total_waste_cost = waste_analysis['waste_cost'].sum()
        st.metric("Total Waste Cost", f"${total_waste_cost:,.2f}")
    
    with col3:
        avg_waste_percentage = waste_analysis['waste_percentage'].mean()
        st.metric("Average Waste %", f"{avg_waste_percentage:.2f}%")
    
    with col4:
        high_risk_items = len(heatmap_data[heatmap_data['risk_level'] == 'High Risk']) if not heatmap_data.empty else 0
        st.metric("High Risk Items", high_risk_items)
    
    st.divider()
    
    # Cost vs Waste Heatmap
    if not heatmap_data.empty:
        st.subheader("🔥 Cost vs. Waste Heatmap")
        # Clean data - remove NaN values and ensure numeric
        heatmap_clean = heatmap_data.copy()
        heatmap_clean = heatmap_clean.dropna(subset=['total_cost', 'waste', 'waste_cost', 'ingredient'])
        heatmap_clean['waste_cost'] = pd.to_numeric(heatmap_clean['waste_cost'], errors='coerce').fillna(0)
        heatmap_clean['total_cost'] = pd.to_numeric(heatmap_clean['total_cost'], errors='coerce').fillna(0)
        heatmap_clean['waste'] = pd.to_numeric(heatmap_clean['waste'], errors='coerce').fillna(0)
        
        # Show all items with purchases (even if waste_cost is 0, they're still relevant)
        # Use a minimum size for items with zero waste_cost so they're still visible
        max_cost_val = heatmap_clean['total_cost'].max() if not heatmap_clean.empty else 0
        min_size = max_cost_val * 0.01 if max_cost_val > 0 else 1
        heatmap_clean['size_for_plot'] = heatmap_clean['waste_cost'].apply(
            lambda x: max(x, min_size) if x > 0 else min_size
        )
        
        if not heatmap_clean.empty and (heatmap_clean['total_cost'].sum() > 0 or heatmap_clean['waste'].sum() > 0):
            fig = px.scatter(
                heatmap_clean,
                x='total_cost',
                y='waste',
                size='size_for_plot',
                color='risk_level',
                hover_name='ingredient',
                hover_data={'waste_cost': True, 'waste_percentage': ':.2f'},
                color_discrete_map={
                    'High Risk': 'red',
                    'Medium Risk': 'orange',
                    'Low Risk': 'green'
                },
                labels={
                    'total_cost': 'Total Cost ($)', 
                    'waste': 'Waste (units)', 
                    'waste_cost': 'Waste Cost ($)',
                    'risk_level': 'Risk Level'
                },
                title="Cost vs. Waste Analysis"
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No valid data points for heatmap visualization.")
    
    # Top waste items
    st.subheader("📊 Top Waste Items")
    top_waste = waste_analysis.head(15)
    fig = px.bar(
        top_waste,
        x='waste_cost',
        y='ingredient',
        orientation='h',
        color='waste_percentage',
        color_continuous_scale='Reds',
        labels={'waste_cost': 'Waste Cost ($)', 'ingredient': 'Ingredient', 'waste_percentage': 'Waste %'}
    )
    fig.update_layout(yaxis={'categoryorder': 'total ascending'})
    st.plotly_chart(fig, use_container_width=True)
    
    # Waste analysis table
    st.subheader("📋 Detailed Waste Analysis")
    display_waste = waste_analysis[['ingredient', 'total_purchased', 'total_used', 'waste', 
                                    'waste_percentage', 'total_cost', 'waste_cost']].copy()
    display_waste.columns = ['Ingredient', 'Total Purchased', 'Total Used', 'Waste', 
                            'Waste %', 'Total Cost', 'Waste Cost']
    st.dataframe(display_waste, use_container_width=True, hide_index=True)
    
    # Optimization suggestions
    st.subheader("💡 Optimization Suggestions")
    high_waste = waste_analysis[waste_analysis['waste_percentage'] > 20].head(5)
    if not high_waste.empty:
        st.write("**High waste items (>20% waste) - Consider:**")
        for _, item in high_waste.iterrows():
            st.write(f"- **{item['ingredient']}**: {item['waste_percentage']:.1f}% waste - "
                    f"Consider reducing purchase quantity or adjusting menu usage")

def show_storage_estimator(analytics):
    """Display cold storage load estimator"""
    st.header("🧊 Cold Storage Load Estimator")
    
    days_ahead = st.slider("Estimate Storage Load (Days Ahead)", 1, 30, 7)
    
    storage_load = analytics.estimate_storage_load(days_ahead=days_ahead)
    
    if storage_load.empty:
        st.warning("Storage load data not available. Ensure ingredients have storage_type and storage_space_units.")
        return
    
    # Summary metrics
    col1, col2, col3 = st.columns(3)
    
    with col1:
        total_current_load = storage_load['current_load'].sum()
        st.metric("Total Current Load", f"{total_current_load:.2f} cu ft")
    
    with col2:
        total_incoming_load = storage_load['incoming_load'].sum()
        st.metric("Total Incoming Load", f"{total_incoming_load:.2f} cu ft")
    
    with col3:
        overloaded_count = storage_load['is_overloaded'].sum()
        st.metric("Overloaded Storage Types", int(overloaded_count), delta="⚠️" if overloaded_count > 0 else None)
    
    st.divider()
    
    # Storage load by type
    st.subheader("📊 Storage Load by Type")
    fig = go.Figure()
    
    fig.add_trace(go.Bar(
        x=storage_load['storage_type'],
        y=storage_load['current_load'],
        name='Current Load',
        marker_color='lightblue'
    ))
    fig.add_trace(go.Bar(
        x=storage_load['storage_type'],
        y=storage_load['incoming_load'],
        name='Incoming Load',
        marker_color='orange'
    ))
    fig.add_trace(go.Scatter(
        x=storage_load['storage_type'],
        y=storage_load['estimated_capacity'],
        name='Estimated Capacity',
        mode='lines+markers',
        line=dict(color='red', width=2, dash='dash')
    ))
    
    fig.update_layout(
        xaxis_title="Storage Type",
        yaxis_title="Load (cubic feet)",
        barmode='group'
    )
    st.plotly_chart(fig, use_container_width=True)
    
    # Storage load table
    st.subheader("📋 Storage Load Details")
    display_storage = storage_load[['storage_type', 'current_load', 'incoming_load', 'total_load',
                                   'estimated_capacity', 'utilization_percentage', 'is_overloaded']].copy()
    display_storage.columns = ['Storage Type', 'Current Load', 'Incoming Load', 'Total Load',
                              'Estimated Capacity', 'Utilization %', 'Is Overloaded']
    st.dataframe(display_storage, use_container_width=True, hide_index=True)
    
    # Utilization visualization
    st.subheader("📈 Storage Utilization")
    fig = px.bar(
        storage_load,
        x='storage_type',
        y='utilization_percentage',
        color='is_overloaded',
        color_discrete_map={True: 'red', False: 'green'},
        labels={'storage_type': 'Storage Type', 'utilization_percentage': 'Utilization %', 'is_overloaded': 'Overloaded'}
    )
    fig.add_hline(y=100, line_dash="dash", line_color="red", annotation_text="100% Capacity")
    st.plotly_chart(fig, use_container_width=True)
    
    # Optimization suggestions
    overloaded = storage_load[storage_load['is_overloaded'] == True]
    if not overloaded.empty:
        st.subheader("⚠️ Overload Warnings")
        for _, item in overloaded.iterrows():
            st.warning(f"**{item['storage_type']}** storage is overloaded! "
                      f"Current + Incoming: {item['total_load']:.2f} cu ft, "
                      f"Capacity: {item['estimated_capacity']:.2f} cu ft")

def show_what_if_simulator(analytics, data):
    """Display interactive what-if simulator"""
    st.header("🧪 What-If Simulator")
    
    st.info("""
    **What this does:** This tool lets you simulate "what if" scenarios to see how changes would affect your inventory.
    
    **How it works:**
    1. Adjust the sliders below to change sales or supplier delays
    2. Click "Run Simulation" to see the impact
    3. Compare current inventory vs. simulated inventory to see what would change
    """)
    
    # Scenario parameters
    st.subheader("⚙️ Adjust Scenario Parameters")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.write("**Overall Changes:**")
        sales_multiplier = st.slider(
            "Change All Sales Volume", 
            0.5, 2.0, 1.0, 0.1,
            help="1.0 = no change, 1.5 = 50% increase, 0.5 = 50% decrease"
        )
        st.caption(f"Example: {sales_multiplier:.1f}x means sales would be {sales_multiplier*100:.0f}% of current")
        
        supplier_delay_days = st.slider(
            "Add Supplier Delay (Days)", 
            0, 30, 0,
            help="Simulate if suppliers are delayed by this many days. Note: Only works if shipment data includes dates."
        )
        if supplier_delay_days > 0:
            st.caption(f"Future shipments would arrive {supplier_delay_days} days later (if shipment dates are available)")
        else:
            st.caption("No delay applied")
    
    with col2:
        st.write("**Specific Menu Item Changes:**")
        if 'sales' in data and not data['sales'].empty and 'menu_item' in data['sales'].columns:
            menu_items = data['sales']['menu_item'].unique().tolist()
            selected_menu_item = st.selectbox(
                "Select Menu Item to Change", 
                options=['None'] + sorted(menu_items),
                help="Choose a specific menu item to change separately from overall sales"
            )
            if selected_menu_item != 'None':
                menu_item_multiplier = st.slider(
                    f"Change {selected_menu_item} Sales", 
                    0.5, 2.0, 1.0, 0.1,
                    help=f"1.0 = no change, 1.5 = 50% increase for {selected_menu_item} only"
                )
                st.caption(f"{selected_menu_item} sales would be {menu_item_multiplier*100:.0f}% of current")
            else:
                menu_item_multiplier = 1.0
                selected_menu_item = None
        else:
            selected_menu_item = None
            menu_item_multiplier = 1.0
            st.caption("No menu item data available")
    
    # Build scenario
    scenario = {
        'sales_multiplier': sales_multiplier,
        'price_multiplier': 1.0,  # Not used in simulation, kept for compatibility
        'supplier_delay_days': supplier_delay_days,
        'menu_item_changes': {}
    }
    
    if selected_menu_item:
        scenario['menu_item_changes'] = {selected_menu_item: menu_item_multiplier}
    
    st.divider()
    
    # Run simulation
    if st.button("▶️ Run Simulation", type="primary", use_container_width=True):
        with st.spinner("Running simulation..."):
            simulation_results = analytics.simulate_scenario(scenario)
            
            if simulation_results.empty:
                st.warning("Simulation results not available.")
                return
            
            st.subheader("📊 Simulation Results")
            st.write("**Comparison:** Current inventory vs. what would happen with your changes")
            
            # Summary metrics
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                avg_stock_change = simulation_results['stock_change'].mean()
                st.metric(
                    "Average Stock Change", 
                    f"{avg_stock_change:.1f}",
                    help="Average change in inventory levels across all ingredients"
                )
            
            with col2:
                items_affected = len(simulation_results[simulation_results['stock_change'] != 0])
                st.metric(
                    "Ingredients Affected", 
                    items_affected,
                    help="Number of ingredients that would see a change in stock"
                )
            
            with col3:
                items_low_stock = len(simulation_results[simulation_results['days_until_stockout_simulated'] < 7])
                st.metric(
                    "At Risk (Low Stock)", 
                    items_low_stock, 
                    delta="⚠️" if items_low_stock > 0 else None,
                    help="Ingredients that would run out in less than 7 days"
                )
            
            with col4:
                avg_days_change = simulation_results['days_change'].mean()
                st.metric(
                    "Avg Days Until Stockout Change", 
                    f"{avg_days_change:.1f}",
                    help="Average change in days until ingredients run out"
                )
            
            st.divider()
            
            # Filter significant changes
            significant_changes = simulation_results[
                (simulation_results['stock_change_percentage'].abs() > 10) |
                (simulation_results['days_change'].abs() > 7)
            ].copy()
            
            if not significant_changes.empty:
                st.subheader("⚠️ Ingredients with Significant Changes")
                st.caption("Showing ingredients with >10% stock change or >7 days change in stockout time")
                display_sim = significant_changes[['ingredient', 'current_stock_base', 'current_stock_simulated',
                                                  'stock_change', 'stock_change_percentage', 'days_until_stockout_base',
                                                  'days_until_stockout_simulated', 'days_change']].copy()
                display_sim.columns = [
                    'Ingredient', 
                    'Current Stock (Now)', 
                    'Current Stock (After Changes)',
                    'Stock Change', 
                    'Stock Change %', 
                    'Days Until Stockout (Now)',
                    'Days Until Stockout (After Changes)', 
                    'Days Change'
                ]
                st.dataframe(display_sim, use_container_width=True, hide_index=True)
            else:
                st.info("No ingredients show significant changes (>10% stock change or >7 days change)")
            
            # Visualizations
            st.subheader("📈 Visual Impact Analysis")
            col1, col2 = st.columns(2)
            
            with col1:
                st.write("**Stock Level Changes**")
                st.caption("Ingredients with the biggest percentage change in stock levels")
                top_changes = simulation_results.nlargest(15, 'stock_change_percentage', keep='all')
                if not top_changes.empty:
                    fig = px.bar(
                        top_changes,
                        x='stock_change_percentage',
                        y='ingredient',
                        orientation='h',
                        color='stock_change',
                        color_continuous_scale='RdYlGn',
                        labels={
                            'stock_change_percentage': 'Stock Change (%)', 
                            'ingredient': 'Ingredient', 
                            'stock_change': 'Stock Change'
                        }
                    )
                    fig.update_layout(
                        yaxis={'categoryorder': 'total ascending'},
                        title="Top 15 Ingredients by Stock Change %"
                    )
                    st.plotly_chart(fig, use_container_width=True)
                else:
                    st.info("No significant stock changes to display")
            
            with col2:
                st.write("**Days Until Stockout Changes**")
                st.caption("Ingredients with the biggest reduction in days until stockout (most at risk)")
                days_changes = simulation_results.nsmallest(15, 'days_change', keep='all')
                if not days_changes.empty:
                    fig = px.bar(
                        days_changes,
                        x='days_change',
                        y='ingredient',
                        orientation='h',
                        color='days_change',
                        color_continuous_scale='Reds',
                        labels={
                            'days_change': 'Days Change', 
                            'ingredient': 'Ingredient'
                        }
                    )
                    fig.update_layout(
                        yaxis={'categoryorder': 'total ascending'},
                        title="Top 15 Ingredients at Risk (Days Reduction)"
                    )
                    st.plotly_chart(fig, use_container_width=True)
                else:
                    st.info("No significant days changes to display")

# Enhance shipment analysis with supplier reliability
def enhance_shipment_analysis(analytics, data):
    """Enhance shipment analysis with supplier reliability"""
    supplier_reliability = analytics.track_supplier_reliability()
    
    if not supplier_reliability.empty:
        st.subheader("🏢 Supplier Reliability Tracker")
        
        # Summary metrics
        col1, col2, col3 = st.columns(3)
        
        with col1:
            avg_reliability = supplier_reliability['reliability_score'].mean()
            st.metric("Average Reliability Score", f"{avg_reliability:.1f}/100")
        
        with col2:
            top_supplier = supplier_reliability.iloc[0]['supplier']
            top_score = supplier_reliability.iloc[0]['reliability_score']
            st.metric("Top Supplier", top_supplier, delta=f"{top_score:.1f}")
        
        with col3:
            low_reliability = len(supplier_reliability[supplier_reliability['reliability_score'] < 70])
            st.metric("Low Reliability Suppliers", low_reliability, delta="⚠️" if low_reliability > 0 else None)
        
        # Supplier reliability table
        st.subheader("📋 Supplier Reliability Details")
        display_reliability = supplier_reliability[['supplier', 'reliability_score', 'on_time_rate', 
                                                    'fulfillment_rate', 'avg_delay', 'total_shipments', 'total_spending']].copy()
        display_reliability.columns = ['Supplier', 'Reliability Score', 'On-Time Rate %', 
                                      'Fulfillment Rate %', 'Avg Delay (Days)', 'Total Shipments', 'Total Spending']
        st.dataframe(display_reliability, use_container_width=True, hide_index=True)
        
        # Reliability visualization
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("📊 Reliability Scores")
            fig = px.bar(
                supplier_reliability,
                x='reliability_score',
                y='supplier',
                orientation='h',
                color='reliability_score',
                color_continuous_scale='RdYlGn',
                labels={'reliability_score': 'Reliability Score', 'supplier': 'Supplier'}
            )
            fig.update_layout(yaxis={'categoryorder': 'total ascending'})
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            st.subheader("📈 Supplier Performance Comparison")
            fig = go.Figure()
            fig.add_trace(go.Bar(
                x=supplier_reliability['supplier'],
                y=supplier_reliability['on_time_rate'],
                name='On-Time Rate',
                marker_color='lightblue'
            ))
            fig.add_trace(go.Bar(
                x=supplier_reliability['supplier'],
                y=supplier_reliability['fulfillment_rate'],
                name='Fulfillment Rate',
                marker_color='lightgreen'
            ))
            fig.update_layout(
                xaxis_title="Supplier",
                yaxis_title="Rate (%)",
                barmode='group'
            )
            st.plotly_chart(fig, use_container_width=True)
        
        # Alternative supplier suggestions
        st.subheader("💡 Alternative Supplier Suggestions")
        ingredient_for_alt = st.selectbox(
            "Select Ingredient to Find Alternative Suppliers",
            options=sorted(data.get('purchases', pd.DataFrame()).get('ingredient', pd.Series()).unique().tolist() if not data.get('purchases', pd.DataFrame()).empty else []),
            index=0 if not data.get('purchases', pd.DataFrame()).empty else None
        )
        
        if ingredient_for_alt:
            current_supplier = st.selectbox(
                "Current Supplier (optional)",
                options=['None'] + sorted(data.get('purchases', pd.DataFrame())[data.get('purchases', pd.DataFrame())['ingredient'] == ingredient_for_alt]['supplier'].unique().tolist() if not data.get('purchases', pd.DataFrame()).empty else [])
            )
            
            if st.button("Find Alternative Suppliers"):
                current = current_supplier if current_supplier != 'None' else None
                alternatives = analytics.get_alternative_suppliers(ingredient_for_alt, current_supplier=current)
                if not alternatives.empty:
                    st.write(f"**Alternative suppliers for {ingredient_for_alt}:**")
                    st.dataframe(alternatives, use_container_width=True, hide_index=True)
                else:
                    st.info("No alternative suppliers found.")


def show_chatbot_ui(chatbot, analytics):
    """Display chatbot UI component"""
    st.header("🤖 AI Assistant")
    st.caption("Ask questions about your inventory, costs, waste, and more!")
    
    # Initialize chat history in session state
    if 'chat_history' not in st.session_state:
        st.session_state.chat_history = []
    
    # Display chat history
    chat_container = st.container()
    with chat_container:
        # Welcome message
        if len(st.session_state.chat_history) == 0:
            st.info("👋 Hi! I can help you with:\n- Most used/wasted ingredients\n- Revenue by dish\n- Inventory status\n- Cost analysis\n- Menu viability\n- Reorder recommendations")
        
        # Display messages
        for message in st.session_state.chat_history:
            if message['role'] == 'user':
                with st.chat_message("user"):
                    st.write(message['content'])
            else:
                with st.chat_message("assistant"):
                    st.write(message['content'])
                    # Display chart if available
                    if 'chart_info' in message and message['chart_info']:
                        render_chart_from_info(message['chart_info'], analytics)
    
    # Chat input
    user_input = st.chat_input("Ask a question about your inventory...")
    
    if user_input:
        # Add user message to history
        st.session_state.chat_history.append({'role': 'user', 'content': user_input})
        
        # Get response from chatbot
        with st.spinner("Thinking..."):
            try:
                response_text, chart_info = chatbot.ask(user_input)
                
                # Add assistant response to history
                st.session_state.chat_history.append({
                    'role': 'assistant', 
                    'content': response_text,
                    'chart_info': chart_info
                })
                
                # Rerun to display new messages
                st.rerun()
            except Exception as e:
                error_msg = f"Error: {str(e)}"
                st.session_state.chat_history.append({'role': 'assistant', 'content': error_msg})
                st.rerun()
    
    # Clear chat button
    if st.button("🗑️ Clear Chat", use_container_width=True):
        st.session_state.chat_history = []
        chatbot.clear_history()
        st.rerun()

def render_chart_from_info(chart_info, analytics):
    """Render a chart based on chart_info dictionary"""
    if not chart_info:
        return
    
    chart_type = chart_info.get('type', 'bar')
    data_info = chart_info.get('data', {})
    title = chart_info.get('title', 'Chart')
    
    try:
        if chart_type == 'bar':
            # Handle different data structures
            data_list = data_info.get('data', [])
            if isinstance(data_list, list) and len(data_list) > 0:
                df = pd.DataFrame(data_list)
                
                # Determine x and y columns based on available columns
                if 'ingredient' in df.columns:
                    y_col = 'ingredient'
                    # For waste analysis, use waste_cost, otherwise use value
                    if 'waste_cost' in df.columns:
                        x_col = 'waste_cost'
                        x_label = 'Waste Cost ($)'
                    elif 'waste' in df.columns:
                        x_col = 'waste'
                        x_label = 'Waste (units)'
                    elif 'value' in df.columns:
                        x_col = 'value'
                        x_label = 'Value'
                    else:
                        x_col = df.columns[1]
                        x_label = x_col.replace('_', ' ').title()
                elif 'menu_item' in df.columns:
                    y_col = 'menu_item'
                    x_col = 'revenue' if 'revenue' in df.columns else df.columns[1]
                    x_label = 'Revenue ($)' if 'revenue' in df.columns else x_col.replace('_', ' ').title()
                else:
                    x_col = df.columns[1] if len(df.columns) > 1 else df.columns[0]
                    y_col = df.columns[0]
                    x_label = x_col.replace('_', ' ').title()
                
                fig = px.bar(
                    df.head(10),  # Limit to top 10 for readability
                    x=x_col,
                    y=y_col,
                    orientation='h',
                    title=title,
                    labels={x_col: x_label, y_col: y_col.replace('_', ' ').title()}
                )
                fig.update_layout(
                    yaxis={'categoryorder': 'total ascending'},
                    height=400
                )
                st.plotly_chart(fig, use_container_width=True)
        
        elif chart_type == 'table':
            data_list = data_info.get('data', [])
            if isinstance(data_list, list) and len(data_list) > 0:
                df = pd.DataFrame(data_list)
                # Limit columns for display
                display_cols = [col for col in df.columns if col not in ['metric', 'info']]
                if len(display_cols) > 8:
                    display_cols = display_cols[:8]
                st.dataframe(df[display_cols], use_container_width=True, hide_index=True)
    
    except Exception as e:
        st.error(f"Error rendering chart: {str(e)}")
        import traceback
        st.code(traceback.format_exc())

if __name__ == "__main__":
    main()

