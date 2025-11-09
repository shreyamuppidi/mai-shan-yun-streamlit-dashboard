"""
Analytics Service - Wraps InventoryAnalytics for API use
"""
from typing import Dict, Optional
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.analytics import InventoryAnalytics
from app.services.data_service import DataService

class AnalyticsService:
    """Service for analytics operations"""
    
    def __init__(self, data_service: DataService):
        self.data_service = data_service
        self._analytics: Optional[InventoryAnalytics] = None
    
    def get_analytics(self) -> InventoryAnalytics:
        """Get or create analytics instance"""
        if self._analytics is None:
            data = self.data_service.get_data()
            self._analytics = InventoryAnalytics(data)
        return self._analytics
    
    def reload_analytics(self):
        """Reload analytics with fresh data"""
        self.data_service.clear_cache()
        data = self.data_service.load_all_data(force_reload=True)
        self._analytics = InventoryAnalytics(data)
    
    def update_analytics(self):
        """Update analytics with current cached data (without reloading from files)"""
        data = self.data_service.get_data()
        self._analytics = InventoryAnalytics(data)
    
    def get_data(self) -> Dict:
        """Get current data"""
        return self.data_service.get_data()

