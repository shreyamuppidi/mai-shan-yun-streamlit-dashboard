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
- **AI-powered chatbot** for inventory queries

## ✨ Key Features

- **Overview Dashboard** - Real-time inventory health metrics, menu viability score, risk alerts
- **Inventory Levels** - Current stock levels with visual indicators and days until stockout
- **Risk Alerts** - Velocity-based risk calculations, overstock detection, risk scores
- **Usage Trends** - Historical usage patterns with daily/weekly/monthly analysis
- **Demand Forecasting** - 7-90 day forecasts with seasonality and holiday integration
- **Menu-Driven Forecasting** - Forecast ingredient demand based on menu item sales
- **Recipe Mapper** - Map menu items to ingredients, calculate servings possible
- **Shipment Analysis** - Supplier reliability scores, on-time delivery tracking
- **Cost Analysis** - Spending trends, top ingredients by cost, supplier distribution
- **Cost vs. Waste Heatmap** - Identify high-risk items (high cost + high waste)
- **Storage Estimator** - Cold storage load estimation and capacity planning
- **Smart Reorder Recommendations** - Automated reorder with confidence scores
- **What-If Simulator** - Simulate sales volume, price, and supplier delay changes
- **AI Chatbot** - Interactive assistant for inventory queries

## 🚀 Getting Started

### Prerequisites

- **Python** 3.8+ (Python 3.12 recommended)
- **pip** package manager

### Quick Start

#### 1. Clone the Repository

```bash
git clone https://github.com/shreyamuppidi/mai-shan-yun-streamlit-dashboard.git
cd mai-shan-yun-dashboard
git checkout streamlit/run
```

#### 2. Create Virtual Environment (Recommended)

```bash
python3 -m venv msy
source msy/bin/activate  # On Windows: msy\Scripts\activate
```

#### 3. Install Dependencies

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

#### 4. Run the Dashboard

**Option 1: Using the convenience script (Easiest)**

```bash
./run_dashboard.sh
```

**Option 2: Manual start**

```bash
streamlit run app.py
```

The dashboard will open in your browser at `http://localhost:8501`

### Environment Variables

For the chatbot to work, set the OpenAI API key:

```bash
export OPENAI_API_KEY=your_key_here
```

Or create a `.env` file in the root directory:

```env
OPENAI_API_KEY=your_key_here
```

## 📁 Project Structure

```
mai-shan-yun-dashboard/
├── app.py                 # Main Streamlit application
├── src/                   # Python modules
│   ├── analytics.py      # Analytics engine
│   ├── chatbot.py        # Chatbot logic
│   ├── data_loader.py    # Data loading
│   └── ...
├── data/                  # Data files (Excel, CSV)
├── requirements.txt       # Python dependencies
└── README.md
```

## 🔧 Technical Stack

- **Frontend**: Streamlit (Python web framework)
- **Data Processing**: Pandas, NumPy
- **Visualization**: Plotly (interactive charts)
- **Analytics**: scikit-learn (forecasting models)
- **AI**: OpenAI API (chatbot)

## 📊 Data Setup

The dashboard requires MSY data files in the `data/` directory. The repository includes sample data files:

- `MSY Data - Ingredient.csv` - Recipe matrix
- `MSY Data - Shipment.csv` - Shipment frequency data
- Monthly Excel matrices (May-October) - Transaction data

To download the latest MSY data:

```bash
python download_msy_data.py
```

## 🛠️ Development

### Running in Development Mode

```bash
streamlit run app.py
```

The app will automatically reload when you make changes to the code.

### Key Components

- **DataLoader** (`src/data_loader.py`) - Loads and cleans CSV/Excel data files
- **InventoryAnalytics** (`src/analytics.py`) - Inventory calculations, forecasting, trend analysis
- **Chatbot** (`src/chatbot.py`) - AI-powered inventory assistant
- **Dashboard** (`app.py`) - Main Streamlit application with interactive visualizations

## 🐛 Troubleshooting

**Dashboard won't start:**
- Ensure virtual environment is activated: `which python` should show `.../msy/bin/python`
- Check that port 8501 is not in use
- Verify all dependencies are installed: `pip install -r requirements.txt`

**No data showing:**
- Verify data files exist in `data/` directory
- Run `python download_msy_data.py` to download sample data
- Check that data files have correct format

**Missing columns error:**
- Ensure CSV files have required columns (ingredient, date, quantity, etc.)
- The DataLoader automatically handles common column name variations

**Forecast not available:**
- Ensure you have sufficient historical usage data (at least 7 days) for the ingredient

**Performance issues:**
- Reduce the date range in data files
- Use data aggregation for large datasets
- Streamlit caching is already implemented

## 📝 Data Format Requirements

### Ingredients CSV
- Required: `ingredient`, `min_stock_level`, `max_stock_level`
- Optional: `unit`, `category`, `shelf_life_days`

### Purchases CSV
- Required: `date`, `ingredient`, `quantity`, `total_cost`
- Optional: `supplier`, `cost_per_unit`

### Shipments CSV
- Required: `date`, `ingredient`
- Optional: `expected_date`, `status`, `quantity`, `supplier`

### Sales CSV
- Required: `date`, `menu_item`
- Optional: `quantity_sold`, `revenue`, `price`

### Usage CSV
- Required: `date`, `ingredient`, `quantity_used`
- Optional: `menu_item`

## 🎯 Features

✅ **Interactive Visualizations** - Engaging Plotly charts  
✅ **Smart Analytics** - Trends, predictions, and actionable insights  
✅ **Actionability** - Reorder alerts, forecasts, risk alerts  
✅ **Functionality** - Fully functional dashboard with multiple data sources  
✅ **Data Handling** - Robust data cleaning and analysis  
✅ **Usability** - Intuitive interface with organized navigation  
✅ **Performance** - Efficient data handling with caching  
✅ **Predictive Features** - Multiple forecasting methods  
✅ **AI Chatbot** - Interactive assistant for queries

## 📄 License

This project is part of the Mai Shan Yun Inventory Intelligence Challenge.
