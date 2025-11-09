# 🍜 Mai Shan Yun Inventory Intelligence Dashboard

An interactive, data-powered inventory management dashboard that helps restaurant managers optimize inventory levels, minimize waste, avoid shortages, and predict restocking needs.

## 🎯 Overview

The Mai Shan Yun Inventory Intelligence Dashboard transforms raw restaurant data into actionable insights. Built with Streamlit and powered by advanced analytics, it provides:

- **Real-time inventory tracking** with low stock alerts
- **Usage trend analysis** across daily, weekly, and monthly periods
- **Demand forecasting** using moving average and linear trend methods
- **Shipment delay analysis** to identify supply chain issues
- **Cost optimization** insights by ingredient and supplier
- **Automated reorder recommendations** based on forecasted demand

## ✨ Key Features

### 🏠 Overview Dashboard
- Real-time inventory health metrics
- Menu viability score
- Risk alerts preview
- Recent activity summary
- Enhanced visualizations with donut charts and scatter plots

### 📦 Inventory Levels
- Current stock levels for all ingredients
- Visual indicators for low, normal, and high stock status
- Days until stockout calculations
- Min/max stock level tracking
- **NEW: Shelf-life tracker** with expiration date monitoring
- **NEW: Use-it-now recipe suggestions** for expiring ingredients

### ⚠️ Real-Time Risk Alerts
- **NEW: Velocity-based risk calculations** (7-day and 30-day usage rates)
- **NEW: Overstock detection** based on usage patterns
- **NEW: Risk scores (0-100)** for each ingredient
- **NEW: "Reorder Now" buttons** for critical items
- Risk type classification (Shortage, Overstock, Velocity Spike)

### 📈 Usage Trends
- Historical usage patterns by ingredient
- Daily, weekly, and monthly trend analysis
- Top ingredients by usage volume
- Usage distribution visualizations

### 🔮 Demand Forecasting
- 7-90 day demand forecasts
- Multiple forecasting methods (moving average, linear trend)
- **NEW: Seasonality detection** and adjustment
- **NEW: Holiday calendar integration** for demand spikes
- Confidence intervals for predictions
- Forecast accuracy metrics

### 🍽️ Menu-Driven Forecasting
- **NEW: Forecast ingredient demand based on menu item sales trends**
- **NEW: Ingredient impact scores** showing which menu items drive ingredient usage
- Menu item popularity analysis
- Ingredient consumption prediction from menu sales

### 📋 Recipe Mapper
- **NEW: Map menu items to required ingredients**
- **NEW: Calculate servings possible with current stock**
- **NEW: Daily menu viability score (0-100%)**
- **NEW: Identify missing ingredients** for menu items
- Viability status (High/Medium/Low/Cannot Make)

### 🚚 Shipment Analysis
- Average and maximum delay tracking
- Delay rate analysis by ingredient
- Shipment frequency patterns
- Status distribution (Delivered, In Transit, Delayed)
- **NEW: Supplier reliability scores (0-100)**
- **NEW: On-time delivery rate tracking**
- **NEW: Fulfillment accuracy tracking**
- **NEW: Alternative supplier suggestions** based on performance

### 💰 Cost Analysis
- Total and average daily spending
- Top ingredients by cost
- Spending distribution by supplier
- Spending trends over time

### 💸 Cost vs. Waste Heatmap
- **NEW: Waste analysis** (purchased vs. used)
- **NEW: Cost vs. waste heatmap visualization**
- **NEW: High-risk item identification** (high cost + high waste)
- **NEW: Optimization suggestions** for reducing waste

### 🧊 Storage Estimator
- **NEW: Cold storage load estimation** by type (refrigerated/frozen/shelf)
- **NEW: Capacity vs. incoming load visualization**
- **NEW: Overload warnings** for storage types
- **NEW: Storage optimization suggestions**

### 📋 Smart Reorder Recommendations
- Automated reorder quantity calculations
- Urgency classification (Critical, High, Medium, Low)
- Lead time estimates
- Recommended reorder dates
- **NEW: Confidence scores** based on forecast volatility
- **NEW: Seasonality integration** in recommendations
- **NEW: Multi-factor reorder logic** (stock + velocity + forecast + seasonality)

### 🧪 What-If Simulator
- **NEW: Simulate sales volume changes** (e.g., +20% dumplings)
- **NEW: Simulate price changes**
- **NEW: Simulate supplier delays**
- **NEW: Real-time inventory impact visualization**
- **NEW: Side-by-side comparison** (current vs. simulated)
- Interactive sliders for parameters

## 🚀 Getting Started

### Prerequisites

- Python 3.8 or higher (Python 3.12 recommended)
- pip package manager

### Setup Instructions

#### Step 1: Create Virtual Environment (Recommended)

Create an isolated virtual environment to avoid dependency conflicts:

```bash
# Create virtual environment
python3 -m venv msy

# Activate virtual environment
# On macOS/Linux:
source msy/bin/activate
# On Windows:
# msy\Scripts\activate
```

You should see `(msy)` in your terminal prompt when the environment is active.

#### Step 2: Install Dependencies

```bash
# Upgrade pip
pip install --upgrade pip

# Install build tools (if needed)
pip install setuptools wheel

# Install all dependencies
pip install -r requirements.txt
```

#### Step 3: Verify Installation

```bash
python -c "import streamlit; import pandas; import numpy; import plotly; import sklearn; import holidays; import openpyxl; print('✓ All dependencies verified')"
```

#### Step 4: Download MSY Data (Recommended)

```bash
python download_msy_data.py
```

This downloads the real Mai Shan Yun dataset from the challenge repository.

#### Step 5: Run the Dashboard

**Option 1: Using the convenience script (Easiest)**
```bash
./run_dashboard.sh
```

**Option 2: Manual activation**
```bash
# Activate virtual environment (if not already active)
source msy/bin/activate

# Run dashboard
streamlit run app.py
```

The dashboard will open in your browser at `http://localhost:8501`

### Quick Reference

**Activate virtual environment:**
```bash
source msy/bin/activate
```

**Run dashboard:**
```bash
./run_dashboard.sh
```

**Deactivate virtual environment:**
```bash
deactivate
```

### Troubleshooting

**If you encounter dependency errors:**
1. Ensure virtual environment is activated: `which python` should show `.../msy/bin/python`
2. Reinstall dependencies: `pip install -r requirements.txt --force-reinstall`
3. Recreate virtual environment if needed:
   ```bash
   rm -rf msy
   python3 -m venv msy
   source msy/bin/activate
   pip install --upgrade pip
   pip install -r requirements.txt
   ```

### Data Setup

The dashboard requires MSY data files in the `data/` directory.

**Download MSY Data**

Download the real Mai Shan Yun dataset from the challenge repository:

```bash
python download_msy_data.py
```

This will download:
- `MSY Data - Ingredient.csv` - Recipe matrix (menu items × ingredients)
- `MSY Data - Shipment.csv` - Shipment frequency data
- Monthly Excel matrices (May, June, July, August, September, October) containing transaction data

The dashboard automatically detects and loads MSY data if available. It will:
- Parse the recipe matrix to create ingredient master list
- Generate purchase data from shipment frequency
- Extract sales and usage data from Excel matrices
- Generate usage data from sales × recipe matrix

**Required Files:**
- `MSY Data - Ingredient.csv` (recipe matrix)
- `MSY Data - Shipment.csv` (shipment frequency)
- Monthly Excel matrices (`*_Data_Matrix*.xlsx`)

### Data Format Requirements

#### Ingredients CSV
Required columns:
- `ingredient` - Ingredient name
- `min_stock_level` - Minimum stock level
- `max_stock_level` - Maximum stock level

Optional columns:
- `unit` - Unit of measurement
- `category` - Ingredient category
- `shelf_life_days` - Shelf life in days

#### Purchases CSV
Required columns:
- `date` - Purchase date
- `ingredient` - Ingredient name
- `quantity` - Quantity purchased
- `total_cost` - Total cost (or `cost_per_unit` × `quantity`)

Optional columns:
- `supplier` - Supplier name
- `cost_per_unit` - Cost per unit

#### Shipments CSV
Required columns:
- `date` - Shipment date
- `ingredient` - Ingredient name

Optional columns:
- `expected_date` - Expected delivery date (for delay analysis)
- `status` - Shipment status
- `quantity` - Quantity shipped
- `supplier` - Supplier name

#### Sales CSV
Required columns:
- `date` - Sale date
- `menu_item` - Menu item name

Optional columns:
- `quantity_sold` - Quantity sold
- `revenue` - Revenue from sale
- `price` - Item price

#### Usage CSV
Required columns:
- `date` - Usage date
- `ingredient` - Ingredient name
- `quantity_used` - Quantity used

Optional columns:
- `menu_item` - Associated menu item

### Running the Dashboard

The dashboard will automatically open in your default web browser at `http://localhost:8501` when you run:

```bash
streamlit run app.py
```

Or use the quick start script:

```bash
./run.sh
```

## 📊 Dashboard Sections

### 🏠 Overview
- Key metrics summary
- Inventory status distribution
- Top ingredients by stock
- Recent activity feed

### 📦 Inventory Levels
- Detailed inventory table
- Stock level vs. thresholds visualization
- Days until stockout analysis
- Filterable and sortable views

### 📈 Usage Trends
- Time-series usage charts
- Top ingredients by usage
- Usage distribution analysis
- Period-based filtering (daily/weekly/monthly)

### 🔮 Demand Forecasting
- Interactive forecast charts
- Multiple forecasting methods
- Confidence intervals
- Forecast summary metrics

### 🚚 Shipment Analysis
- Delay analysis by ingredient
- Shipment frequency trends
- Status distribution
- Supplier performance metrics

### 💰 Cost Analysis
- Spending trends over time
- Top ingredients by cost
- Supplier spending distribution
- Cost optimization insights

### 📋 Reorder Recommendations
- Automated reorder suggestions
- Urgency-based prioritization
- Lead time considerations
- Recommended reorder dates

## 🔧 Technical Details

### Architecture

- **Frontend**: Streamlit (Python web framework)
- **Data Processing**: Pandas, NumPy
- **Visualization**: Plotly (interactive charts)
- **Analytics**: scikit-learn (forecasting models)
- **Data Loading**: Custom DataLoader class

### Key Components

1. **DataLoader** (`src/data_loader.py`)
   - Loads and cleans CSV data files
   - Handles various column name formats
   - Data validation and normalization

2. **InventoryAnalytics** (`src/analytics.py`)
   - Inventory level calculations
   - Demand forecasting algorithms
   - Trend analysis
   - Cost analysis
   - Reorder recommendations

3. **SampleDataGenerator** (`src/data_generator.py`)
   - Generates realistic sample data
   - Useful for testing and demonstration

4. **Dashboard** (`app.py`)
   - Main Streamlit application
   - Interactive visualizations
   - User interface components

### Forecasting Methods

1. **Moving Average**
   - Uses 7-day and 30-day moving averages
   - Weighted combination for stability
   - Suitable for stable demand patterns

2. **Linear Trend**
   - Linear regression on historical data
   - Captures trend patterns
   - Suitable for trending demand

## 📈 Example Insights

### Inventory Optimization
- Identify ingredients running low before stockout
- Avoid overstocking with max level alerts
- Optimize reorder timing based on lead times

### Cost Management
- Track spending by ingredient and supplier
- Identify cost drivers
- Optimize supplier relationships

### Demand Prediction
- Forecast ingredient needs 30-90 days ahead
- Plan purchases based on predicted demand
- Reduce waste through better planning

### Supply Chain Analysis
- Identify shipment delay patterns
- Track supplier performance
- Optimize order timing

## 🎨 Customization

### Adjusting Forecast Parameters
Edit `src/analytics.py` to modify:
- Forecast horizon (default: 30 days)
- Moving average windows
- Confidence intervals

### Customizing Stock Levels
Update ingredient data in `data/ingredients.csv`:
- `min_stock_level` - Minimum threshold
- `max_stock_level` - Maximum threshold

### Adding New Visualizations
Extend `app.py` to add:
- Custom charts
- New analysis sections
- Additional metrics

## 🐛 Troubleshooting

### No Data Files Found
**Error**: "No data files found in the 'data' directory"

**Solution**: Run `python src/data_generator.py` to generate sample data, or place your own data files in the `data/` directory.

### Missing Columns Error
**Error**: "KeyError: 'column_name'"

**Solution**: Ensure your CSV files have the required columns (see Data Format Requirements section). The DataLoader automatically handles common column name variations.

### Forecast Not Available
**Error**: "Forecast data not available for this ingredient"

**Solution**: Ensure you have sufficient historical usage data (at least 7 days) for the ingredient.

### Performance Issues
**Solution**: 
- Reduce the date range in data files
- Use data aggregation for large datasets
- Enable Streamlit caching (already implemented)

## 📝 Dataset Integration

The dashboard integrates multiple data sources from the Mai Shan Yun restaurant:

1. **Purchases** → Inventory levels, cost analysis, waste calculation
2. **Usage** → Trends, forecasting, inventory calculations, recipe mapping
3. **Shipments** → Delay analysis, lead time estimates, supplier reliability
4. **Sales** → Menu item demand, ingredient consumption prediction, menu-driven forecasting
5. **Ingredients** → Master data, stock thresholds, shelf life, storage requirements

### MSY Dataset Structure

The real MSY dataset includes:
- **MSY Data - Ingredient.csv**: Master ingredient list with categories, units, and stock levels
- **MSY Data - Shipment.csv**: Shipment records with dates, expected dates, and status
- **Monthly Data Matrices (Excel)**: May through October data containing:
  - Purchase transactions
  - Sales records by menu item
  - Ingredient usage linked to menu items

The dashboard automatically detects and loads MSY data when available, falling back to sample data or standard CSV format if needed.

## 🎥 Video Demo

*Note: Please provide a link to your video demo here or include it in your submission.*

## 🎯 Features

This dashboard meets all requirements for the Mai Shan Yun Inventory Intelligence Challenge:

✅ **Interactive Visualizations**: Engaging and clear visual insights with Plotly charts
✅ **Smart Analytics**: Meaningful trends, predictions, and actionable insights
✅ **Actionability**: Reorder alerts, trend forecasts, risk alerts, and optimization suggestions
✅ **Functionality**: Fully functional dashboard pulling insights from multiple data sources
✅ **Data Handling**: Robust data cleaning, merging, and analysis of multiple datasets
✅ **Usability**: Intuitive interface with well-organized navigation
✅ **Performance**: Efficient data handling with caching and optimized calculations
✅ **Predictive Features**: Multiple forecasting methods with seasonality and event awareness
✅ **Multiple Data Sources**: Integrates purchases, shipments, ingredients, sales, and usage data
✅ **MSY Data Support**: Automatic detection and loading of real MSY dataset

## 🎨 Creative Features

- **Risk Scoring System**: Comprehensive 0-100 risk score for each ingredient
- **Menu Viability Dashboard**: Real-time assessment of which menu items can be made
- **What-If Scenarios**: Interactive simulation tool for planning and experimentation
- **Supplier Reliability Tracking**: Data-driven supplier performance analysis
- **Waste Optimization**: Cost vs. waste heatmap for identifying inefficiencies
- **Storage Management**: Cold storage capacity planning and overload prevention
- **Recipe Suggestions**: AI-powered recommendations for using expiring ingredients

## 🚀 Future Enhancements

- [ ] Real-time data integration via API
- [ ] Multi-restaurant support
- [ ] Email/SMS alerts for low stock and expiring items
- [ ] Export reports (PDF, Excel)
- [ ] User authentication and role-based access
- [ ] Historical data archival
- [ ] Mobile app support
- [ ] Integration with POS systems





