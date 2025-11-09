# 🍜 Mai Shan Yun Inventory Intelligence Dashboard

An interactive, data-powered inventory management dashboard that helps restaurant managers optimize inventory levels, minimize waste, avoid shortages, and predict restocking needs.

## 🎯 Overview

The Mai Shan Yun Inventory Intelligence Dashboard transforms raw restaurant data into actionable insights. Built with React and FastAPI, it provides:

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

- **Node.js** 18+ and npm (for React frontend)
- **Python** 3.8+ (for FastAPI backend)
- **pip** package manager

### Quick Start

#### 1. Clone the Repository

```bash
git clone https://github.com/shreyamuppidi/mai-shan-yun-streamlit-dashboard.git
cd mai-shan-yun-dashboard
git checkout react/app
```

#### 2. Backend Setup

```bash
# Create virtual environment (recommended)
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install Python dependencies
pip install -r requirements.txt
```

#### 3. Frontend Setup

```bash
cd frontend
npm install
cd ..
```

#### 4. Start the Application

**Option 1: Using startup scripts (Recommended)**

```bash
# Terminal 1: Start backend
./start_backend.sh

# Terminal 2: Start frontend
./start_frontend.sh
```

**Option 2: Manual start**

```bash
# Terminal 1: Start backend
cd backend
uvicorn app.main:app --reload --port 8000

# Terminal 2: Start frontend
cd frontend
npm run dev
```

The application will be available at:
- **Frontend**: http://localhost:5173
- **Backend API**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs

### Environment Variables

Create a `.env` file in the `frontend/` directory (optional):

```env
VITE_API_URL=http://localhost:8000
```

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
├── frontend/              # React frontend application
│   ├── src/
│   │   ├── components/    # React components
│   │   ├── pages/        # Page components
│   │   ├── services/     # API client
│   │   └── ...
│   ├── package.json
│   └── vite.config.ts
├── backend/              # FastAPI backend
│   ├── app/
│   │   ├── api/         # API routes
│   │   ├── services/    # Business logic
│   │   └── main.py      # FastAPI app
│   └── ...
├── src/                  # Shared Python modules
│   ├── analytics.py     # Analytics engine
│   ├── chatbot.py       # Chatbot logic
│   ├── data_loader.py   # Data loading
│   └── ...
├── data/                 # Data files (Excel, CSV)
├── requirements.txt      # Python dependencies
└── README.md
```

## 🔧 Technical Stack

- **Frontend**: React 18, TypeScript, Vite, Tailwind CSS
- **Backend**: FastAPI, Python 3.8+
- **Data Processing**: Pandas, NumPy
- **Visualization**: Plotly.js
- **Analytics**: scikit-learn
- **State Management**: Zustand, React Query

## 📊 Data Setup

The dashboard requires MSY data files in the `data/` directory. The repository includes sample data files:

- `MSY Data - Ingredient.csv` - Recipe matrix
- `MSY Data - Shipment.csv` - Shipment frequency data
- Monthly Excel matrices (May-October) - Transaction data

To download the latest MSY data:

```bash
python download_msy_data.py
```
We use the dataset provided in the https://github.com/tamu-datathon-org/mai-shen-yun repo.

## 🛠️ Development

### Backend Development

```bash
cd backend
uvicorn app.main:app --reload --port 8000
```

API documentation available at http://localhost:8000/docs

### Frontend Development

```bash
cd frontend
npm run dev
```

### Building for Production

```bash
# Build frontend
cd frontend
npm run build

# The built files will be in frontend/dist/
```

## 🐛 Troubleshooting

**Backend won't start:**
- Ensure virtual environment is activated
- Check that port 8000 is not in use
- Verify all dependencies are installed: `pip install -r requirements.txt`

**Frontend won't start:**
- Ensure Node.js 18+ is installed
- Run `npm install` in the frontend directory
- Check that port 5173 is not in use

**API connection errors:**
- Verify backend is running on http://localhost:8000
- Check CORS settings in `backend/app/main.py`
- Ensure `VITE_API_URL` in frontend `.env` matches backend URL

**No data showing:**
- Verify data files exist in `data/` directory
- Check backend logs for data loading errors
- Ensure data files have correct format (see data format requirements)

## 📝 API Endpoints

All endpoints are prefixed with `/api`:

- `GET /api/overview` - Overview dashboard data
- `GET /api/inventory` - Inventory levels
- `GET /api/risk-alerts` - Risk alerts
- `GET /api/usage-trends` - Usage trends
- `GET /api/forecast` - Demand forecasting
- `GET /api/menu-forecast` - Menu-driven forecasting
- `GET /api/recipe-mapper` - Recipe mapper
- `GET /api/shipments` - Shipment analysis
- `GET /api/cost-analysis` - Cost analysis
- `GET /api/waste` - Waste analysis
- `GET /api/storage` - Storage estimator
- `GET /api/reorder` - Reorder recommendations
- `POST /api/simulate` - What-if simulator
- `POST /api/chat` - Chatbot endpoint
- `POST /api/upload` - Upload new data files

See http://localhost:8000/docs for full API documentation.

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
