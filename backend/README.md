# Mai Shan Yun Dashboard - FastAPI Backend

FastAPI backend for the Mai Shan Yun Inventory Intelligence Dashboard.

## Setup

1. Create virtual environment:
```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Set environment variables:
```bash
export OPENROUTER_API_KEY=your_key_here
```

4. Run the server:
```bash
cd backend
python -m app.main
```

Or using uvicorn directly:
```bash
uvicorn app.main:app --reload --port 8000
```

The API will be available at http://localhost:8000

## API Documentation

Once the server is running, visit:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## Endpoints

All endpoints are prefixed with `/api`:
- `/api/overview` - Overview dashboard data
- `/api/inventory` - Inventory levels
- `/api/risk-alerts` - Risk alerts
- `/api/usage-trends` - Usage trends
- `/api/forecast` - Demand forecasting
- `/api/menu-forecast` - Menu-driven forecasting
- `/api/recipe-mapper` - Recipe mapper
- `/api/shipments` - Shipment analysis
- `/api/cost-analysis` - Cost analysis
- `/api/waste` - Waste analysis
- `/api/storage` - Storage estimator
- `/api/reorder` - Reorder recommendations
- `/api/simulate` - What-if simulator
- `/api/chat` - Chatbot endpoint

