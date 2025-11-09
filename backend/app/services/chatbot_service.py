"""
Chatbot Service - Wraps InventoryChatbot for API use
"""
import os
from typing import Optional
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.chatbot import InventoryChatbot
from app.services.analytics_service import AnalyticsService

class ChatbotService:
    """Service for chatbot operations"""
    
    def __init__(self, analytics_service: AnalyticsService):
        self.analytics_service = analytics_service
        self._chatbot: Optional[InventoryChatbot] = None
    
    def get_chatbot(self, force_reload: bool = False) -> Optional[InventoryChatbot]:
        """Get or create chatbot instance
        
        Args:
            force_reload: If True, recreate chatbot with fresh analytics data
        """
        if self._chatbot is None or force_reload:
            try:
                # Always get fresh analytics to ensure we have latest data including uploaded files
                analytics = self.analytics_service.get_analytics()
                api_key = os.getenv('OPENROUTER_API_KEY')
                if api_key:
                    self._chatbot = InventoryChatbot(analytics, api_key=api_key)
            except Exception as e:
                print(f"Chatbot initialization error: {e}")
                return None
        return self._chatbot
    
    def ask(self, query: str) -> tuple:
        """Process a chat query"""
        # Always get fresh analytics to ensure we have latest data including uploaded files
        # The analytics service will return fresh data from cache
        chatbot = self.get_chatbot(force_reload=False)
        if chatbot is None:
            return ("Chatbot is not available. Please set OPENROUTER_API_KEY environment variable.", None)
        
        # Update chatbot's analytics reference to ensure it has latest data
        # This is important after data uploads
        try:
            fresh_analytics = self.analytics_service.get_analytics()
            chatbot.analytics = fresh_analytics
        except:
            pass  # If update fails, continue with existing analytics
        
        return chatbot.ask(query)
    
    def reload_chatbot(self):
        """Reload chatbot with fresh analytics data (call after data uploads)"""
        self._chatbot = None
        return self.get_chatbot(force_reload=True)
    
    def clear_history(self):
        """Clear chatbot conversation history"""
        chatbot = self.get_chatbot()
        if chatbot:
            chatbot.clear_history()

