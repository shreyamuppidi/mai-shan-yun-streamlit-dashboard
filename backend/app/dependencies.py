"""
Dependencies for FastAPI routes
"""
from pathlib import Path
from app.services.analytics_service import AnalyticsService
from app.services.data_service import DataService
from app.services.chatbot_service import ChatbotService

# Get the project root directory (parent of backend/)
# backend/app/dependencies.py -> backend/ -> project root
backend_dir = Path(__file__).parent.parent
project_root = backend_dir.parent
data_dir = str(project_root / "data")

# Initialize services with correct data directory
data_service = DataService(data_dir=data_dir)
analytics_service = AnalyticsService(data_service)
chatbot_service = ChatbotService(analytics_service)

