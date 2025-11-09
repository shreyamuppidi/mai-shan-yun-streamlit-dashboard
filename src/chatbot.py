"""
AI Chatbot for Inventory Analytics
Provides natural language querying of inventory data using OpenRouter API
"""
import os
import json
from typing import Dict, List, Optional, Tuple, Any
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta

try:
    import openai
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False
    openai = None

class InventoryChatbot:
    """AI chatbot for querying inventory analytics"""
    
    def __init__(self, analytics, api_key: Optional[str] = None, model: str = "openai/gpt-4o-mini"):
        """
        Initialize chatbot
        
        Args:
            analytics: InventoryAnalytics instance
            api_key: OpenRouter API key (if None, tries to get from env or Streamlit secrets)
            model: Model to use (default: gpt-4o-mini). See https://openrouter.ai/models
        """
        self.analytics = analytics
        self.model = model
        self.api_key = api_key or os.getenv('OPENROUTER_API_KEY')
        
        if not OPENAI_AVAILABLE:
            raise ImportError("openai package not installed. Install with: pip install openai")
        
        if not self.api_key:
            # Try to get from Streamlit secrets if available
            try:
                import streamlit as st
                if hasattr(st, 'secrets') and 'OPENROUTER_API_KEY' in st.secrets:
                    self.api_key = st.secrets['OPENROUTER_API_KEY']
            except:
                pass
        
        if not self.api_key:
            raise ValueError("OpenRouter API key not found. Set OPENROUTER_API_KEY environment variable or in Streamlit secrets.")
        
        # Initialize OpenAI client with OpenRouter endpoint
        self.client = openai.OpenAI(
            api_key=self.api_key,
            base_url="https://openrouter.ai/api/v1"
        )
        self.conversation_history = []
        
        # System prompt describing available functions
        self.system_prompt = """You are Yun Chef, an AI assistant for a restaurant inventory management system. 
You help users understand their inventory data, costs, waste, usage patterns, and menu viability.

Your name is Yun Chef, but you can also be called "Yun". When users address you as "Yun" or "Yun Chef", respond naturally to that name.

Your capabilities:
1. **Data Analysis**: Answer questions about inventory, usage, costs, waste, revenue, and menu viability
2. **Recipe Generation**: Create step-by-step cooking instructions based on ingredient lists
3. **Recommendations**: Provide actionable advice
4. **Natural Language**: Understand and respond to questions in a conversational, helpful way
5. **Follow-up Questions**: Maintain conversation context to answer follow-up questions naturally

When answering questions:
- Be conversational, friendly, and helpful
- Keep responses concise and direct - ONLY answer what was asked, nothing more
- Do NOT provide extra information that wasn't requested
- Do NOT mention things that can't be done unless specifically asked
- Use specific numbers and data when available
- For recipes: You will receive ingredient lists with quantities. Generate clear, step-by-step cooking instructions even if you don't have the exact recipe. Use your knowledge of cooking techniques to create reasonable instructions.
- For data questions: Use the provided data to give accurate, specific answers - don't add extra information unless relevant
- For "what can I make" questions: ONLY list dishes that can be made with their serving counts - do NOT mention dishes that can't be made
- For follow-up questions: Use conversation history to understand context (e.g., if user previously asked about dishes, a follow-up "what about that one?" refers to a previously mentioned dish)
- Be creative when appropriate (e.g., generating recipes, providing cooking tips)
- If data is unavailable, explain why briefly and suggest alternatives
- Format numbers clearly (e.g., $1,234.56, 1,234 units)
- Optionally end responses with 1-2 brief, helpful follow-up suggestions - but keep them as suggestions, not required information

When asked for recipes or cooking instructions:
- List all ingredients with their quantities first
- Then provide numbered, step-by-step cooking instructions
- Include helpful tips (cooking temperatures, times, techniques) based on the dish type
- Be creative and practical - you're helping a restaurant kitchen!

When asked "what can I make" or similar questions:
- ONLY list dishes that CAN be made with current inventory
- Include the number of servings possible for each dish
- Keep it simple and direct - ONLY answer what was asked
- DO NOT mention dishes that cannot be made
- DO NOT list missing ingredients for dishes that can't be made
- DO NOT say "however" or "but" followed by information about dishes that can't be made
- DO NOT provide examples of dishes that can't be made
- If asked "what can I make", respond ONLY with dishes that can be made and their serving counts
- Optionally end with 1-2 brief follow-up suggestions (e.g., "Would you like cooking instructions?" or "Need help with anything else?")
- Keep the response focused and concise

Remember: You are Yun Chef, an AI assistant that can generate creative content like recipes and cooking instructions, not just format data. Maintain conversation context to answer follow-up questions naturally."""
    
    def _get_top_ingredients(self, metric: str = 'usage', limit: int = 10, period_days: int = 30) -> Dict:
        """Get top ingredients by usage, cost, or waste"""
        try:
            if metric == 'waste':
                waste_analysis = self.analytics.calculate_waste_analysis(period_days=period_days)
                if waste_analysis.empty:
                    return {'error': 'No waste data available'}
                top = waste_analysis.nlargest(limit, 'waste')
                return {
                    'metric': 'waste',
                    'data': top[['ingredient', 'waste', 'waste_cost', 'waste_percentage']].to_dict('records')
                }
            else:
                top_df = self.analytics.get_top_ingredients(metric=metric, limit=limit, period_days=period_days)
                if top_df.empty:
                    return {'error': f'No {metric} data available'}
                return {
                    'metric': metric,
                    'data': top_df.to_dict('records')
                }
        except Exception as e:
            return {'error': str(e)}
    
    def _extract_month_year(self, query: str) -> tuple:
        """Extract month and year from query. If year not specified, uses most recent year with data."""
        import re
        query_lower = query.lower()
        
        month_map = {
            'january': 1, 'jan': 1,
            'february': 2, 'feb': 2,
            'march': 3, 'mar': 3,
            'april': 4, 'apr': 4,
            'may': 5,
            'june': 6, 'jun': 6,
            'july': 7, 'jul': 7,
            'august': 8, 'aug': 8,
            'september': 9, 'sep': 9, 'sept': 9,
            'october': 10, 'oct': 10,
            'november': 11, 'nov': 11,
            'december': 12, 'dec': 12
        }
        
        month = None
        year = None
        
        # Extract month name (check longer names first to avoid partial matches)
        for month_name, month_num in sorted(month_map.items(), key=lambda x: len(x[0]), reverse=True):
            # Use word boundaries to avoid partial matches
            pattern = r'\b' + re.escape(month_name) + r'\b'
            if re.search(pattern, query_lower):
                month = month_num
                break
        
        # Extract year (4 digits)
        year_match = re.search(r'\b(20\d{2})\b', query)
        if year_match:
            year = int(year_match.group(1))
        else:
            # If year not specified, find the most recent year with data for this month
            if month is not None:
                try:
                    sales = self.analytics.data.get('sales', pd.DataFrame())
                    if not sales.empty and 'date' in sales.columns:
                        sales = sales.copy()
                        sales['date'] = pd.to_datetime(sales['date'], errors='coerce')
                        sales = sales[sales['date'].notna()]
                        # Filter to the requested month
                        month_sales = sales[sales['date'].dt.month == month]
                        if not month_sales.empty:
                            # Get the most recent year for this month
                            year = int(month_sales['date'].dt.year.max())
                        else:
                            # No data for this month, use current year
                            year = datetime.now().year
                    else:
                        year = datetime.now().year
                except:
                    year = datetime.now().year
            else:
                # No month specified, use current year
                year = datetime.now().year
        
        return month, year
    
    def _get_revenue_by_dish(self, period_days: int = None, month: int = None, year: int = None) -> Dict:
        """Calculate revenue by menu item
        
        Args:
            period_days: Filter by last N days (if provided)
            month: Filter by specific month (1-12)
            year: Filter by specific year (defaults to current year)
        """
        try:
            sales = self.analytics.data.get('sales', pd.DataFrame())
            if sales.empty:
                return {'error': 'No sales data available'}
            
            # Ensure date column is datetime
            if 'date' not in sales.columns:
                return {'error': 'Sales data missing date column'}
            
            sales = sales.copy()
            sales['date'] = pd.to_datetime(sales['date'], errors='coerce')
            sales = sales[sales['date'].notna()]
            
            if sales.empty:
                return {'error': 'No valid sales data with dates'}
            
            # Filter by month/year if specified
            if month is not None:
                if year is None:
                    year = datetime.now().year
                # Filter to specific month
                filtered_sales = sales[
                    (sales['date'].dt.month == month) & 
                    (sales['date'].dt.year == year)
                ].copy()
                period_note = f"{datetime(year, month, 1).strftime('%B %Y')}"
            elif period_days is not None:
                # Filter by last N days
                cutoff_date = datetime.now() - timedelta(days=period_days)
                filtered_sales = sales[sales['date'] >= cutoff_date].copy()
                period_note = f"last {period_days} days"
            else:
                # Use all available data
                filtered_sales = sales.copy()
                period_note = "all available"
            
            # If no data in the requested period, return error with helpful message
            if filtered_sales.empty:
                if month is not None:
                    month_name = datetime(year if year else datetime.now().year, month, 1).strftime('%B')
                    available_months = sorted(sales['date'].dt.to_period('M').unique().astype(str).tolist())
                    return {'error': f'No sales data available for {month_name} {year if year else datetime.now().year}. Available months: {", ".join(available_months)}'}
                else:
                    return {'error': 'No sales data available for the requested period'}
            
            # Calculate revenue (quantity_sold * price if price column exists, else use revenue column, else estimate)
            if 'revenue' in filtered_sales.columns and filtered_sales['revenue'].sum() > 0:
                # Use existing revenue column
                filtered_sales['calculated_revenue'] = filtered_sales['revenue']
            elif 'price' in filtered_sales.columns:
                # Calculate from price * quantity
                filtered_sales['calculated_revenue'] = filtered_sales['quantity_sold'] * filtered_sales['price']
            else:
                # Estimate revenue if price not available (use quantity as proxy)
                filtered_sales['calculated_revenue'] = filtered_sales['quantity_sold']
            
            revenue_by_dish = filtered_sales.groupby('menu_item').agg({
                'calculated_revenue': 'sum',
                'quantity_sold': 'sum'
            }).reset_index()
            revenue_by_dish.columns = ['menu_item', 'revenue', 'quantity_sold']
            revenue_by_dish = revenue_by_dish.sort_values('revenue', ascending=False)
            
            return {
                'data': revenue_by_dish.to_dict('records'),
                'total_revenue': revenue_by_dish['revenue'].sum(),
                'period_note': period_note,  # Note about which period was used
                'month': month,  # Include month for debugging
                'year': year  # Include year for debugging
            }
        except Exception as e:
            return {'error': str(e)}
    
    def _get_waste_analysis(self, period_days: int = 30, limit: int = 10) -> Dict:
        """Get waste analysis"""
        try:
            waste_df = self.analytics.calculate_waste_analysis(period_days=period_days)
            if waste_df.empty:
                return {'error': 'No waste data available'}
            
            top_waste = waste_df.nlargest(limit, 'waste_cost')
            return {
                'data': top_waste[['ingredient', 'total_purchased', 'total_used', 'waste', 
                                  'waste_percentage', 'waste_cost']].to_dict('records'),
                'total_waste_cost': waste_df['waste_cost'].sum()
            }
        except Exception as e:
            return {'error': str(e)}
    
    def _get_inventory_status(self) -> Dict:
        """Get current inventory status"""
        try:
            inventory = self.analytics.calculate_inventory_levels()
            if inventory.empty:
                return {'error': 'No inventory data available'}
            
            low_stock = inventory[inventory['stock_status'] == 'Low']
            reorder_needed = inventory[inventory['reorder_needed'] == True]
            
            return {
                'total_ingredients': len(inventory),
                'low_stock_count': len(low_stock),
                'reorder_needed_count': len(reorder_needed),
                'low_stock_items': low_stock[['ingredient', 'current_stock', 'min_stock_level', 
                                              'days_until_stockout']].to_dict('records'),
                'reorder_items': reorder_needed[['ingredient', 'current_stock', 'days_until_stockout']].to_dict('records')
            }
        except Exception as e:
            return {'error': str(e)}
    
    def _get_cost_analysis(self, period_days: int = 30) -> Dict:
        """Get cost analysis"""
        try:
            cost_analysis = self.analytics.get_cost_analysis(period_days=period_days)
            return cost_analysis
        except Exception as e:
            return {'error': str(e)}
    
    def _get_reorder_recommendations(self) -> Dict:
        """Get reorder recommendations"""
        try:
            recommendations = self.analytics.calculate_reorder_recommendations()
            if recommendations.empty:
                return {'error': 'No reorder recommendations available'}
            
            return {
                'data': recommendations.to_dict('records'),
                'total_items': len(recommendations)
            }
        except Exception as e:
            return {'error': str(e)}
    
    def _get_menu_viability(self) -> Dict:
        """Get menu viability information"""
        try:
            viability_df = self.analytics.map_recipes_to_inventory()
            if viability_df.empty:
                return {'error': 'No menu viability data available'}
            
            can_make = viability_df[viability_df['servings_possible'] > 0]
            cannot_make = viability_df[viability_df['servings_possible'] == 0]
            viability_score = self.analytics.calculate_menu_viability_score()
            
            # Get dishes that can be made with their details
            can_make_items = []
            if not can_make.empty:
                # Include menu_item and servings_possible
                for _, row in can_make.iterrows():
                    item_info = {
                        'menu_item': row.get('menu_item', 'Unknown'),
                        'servings_possible': int(row.get('servings_possible', 0))
                    }
                    can_make_items.append(item_info)
            
            # Get recipe information for dishes that can be made
            recipe_info = {}
            if not can_make.empty and len(can_make_items) > 0:
                # Try to get recipe matrix to provide recipe details
                try:
                    recipe_file = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data', 'MSY Data - Ingredient.csv')
                    if os.path.exists(recipe_file):
                        recipe_matrix = pd.read_csv(recipe_file)
                        for item in can_make_items:
                            menu_item = item['menu_item']
                            recipe_row = recipe_matrix[recipe_matrix['Item name'] == menu_item]
                            if not recipe_row.empty:
                                # Get all ingredients with quantities
                                ingredients = {}
                                for col in recipe_matrix.columns:
                                    if col != 'Item name':
                                        qty = recipe_row[col].iloc[0] if len(recipe_row) > 0 else None
                                        if pd.notna(qty) and qty > 0:
                                            ingredients[col] = float(qty)
                                if ingredients:
                                    recipe_info[menu_item] = ingredients
                except Exception:
                    pass  # If recipe file not available, continue without recipe details
            
            return {
                'viability_score': viability_score,
                'total_dishes': len(viability_df),
                'can_make_count': len(can_make),
                'can_make_items': can_make_items,  # Now includes actual dish names!
                'recipes': recipe_info  # Include recipe information
            }
        except Exception as e:
            return {'error': str(e)}
    
    def _get_recipe_for_dish(self, dish_name: str) -> Dict:
        """Get recipe for a specific dish"""
        try:
            recipe_file = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data', 'MSY Data - Ingredient.csv')
            if not os.path.exists(recipe_file):
                return {'error': 'Recipe data file not found'}
            
            recipe_matrix = pd.read_csv(recipe_file)
            
            # Try to find the dish (exact match first, then case-insensitive, then partial)
            dish_row = None
            
            # Exact match
            dish_row = recipe_matrix[recipe_matrix['Item name'] == dish_name]
            
            # Case-insensitive match
            if dish_row.empty:
                dish_row = recipe_matrix[recipe_matrix['Item name'].str.lower() == dish_name.lower()]
            
            # Partial match
            if dish_row.empty:
                dish_row = recipe_matrix[recipe_matrix['Item name'].str.lower().str.contains(dish_name.lower(), na=False)]
            
            if dish_row.empty:
                return {'error': f'Recipe not found for "{dish_name}". Available dishes: {", ".join(recipe_matrix["Item name"].tolist()[:10])}'}
            
            # Get the first match
            menu_item = dish_row['Item name'].iloc[0]
            recipe_row = dish_row.iloc[0]
            
            # Get all ingredients with quantities
            ingredients = {}
            for col in recipe_matrix.columns:
                if col != 'Item name':
                    qty = recipe_row[col]
                    if pd.notna(qty) and qty > 0:
                        ingredients[col] = float(qty)
            
            return {
                'menu_item': menu_item,
                'ingredients': ingredients,
                'ingredient_count': len(ingredients)
            }
        except Exception as e:
            return {'error': str(e)}
    
    def _extract_dish_from_context(self, current_query: str) -> Optional[str]:
        """Extract dish name from current query or conversation history"""
        query_lower = current_query.lower()
        
        # Check if query explicitly mentions a dish name
        # Look for patterns like "recipe for X", "how to make X", "ingredients for X"
        import re
        
        # Pattern: "recipe for [dish]" or "recipe to make [dish]"
        patterns = [
            r'recipe\s+(?:for|to\s+make|of)\s+([^?]+)',
            r'how\s+to\s+make\s+([^?]+)',
            r'ingredients\s+(?:for|to\s+make)\s+([^?]+)',
            r'what\s+(?:do\s+i\s+need|ingredients)\s+(?:to\s+make|for)\s+([^?]+)',
            r'recipe\s+to\s+make\s+([^?]+)',
            r'what\s+is\s+the\s+recipe\s+to\s+make\s+([^?]+)',
            r'step\s+by\s+step\s+(?:procedure|instructions)\s+(?:to\s+make|for)\s+([^?]+)',
            r'procedure\s+to\s+make\s+([^?]+)',
            r'instructions\s+(?:to\s+make|for)\s+([^?]+)',
            r'how\s+do\s+(?:i|you)\s+make\s+([^?]+)',
            r'can\s+you\s+give\s+me\s+(?:the\s+)?(?:step\s+by\s+step\s+)?(?:procedure|instructions|recipe)\s+(?:to\s+make|for)\s+([^?]+)'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, query_lower)
            if match:
                dish_name = match.group(1).strip()
                # Clean up common prefixes that might be captured
                dish_name = re.sub(r'^(to\s+make|for)\s+', '', dish_name, flags=re.IGNORECASE).strip()
                if dish_name and len(dish_name) > 2:
                    return dish_name
        
        # Check conversation history for recently mentioned dishes
        if len(self.conversation_history) > 0:
            # Look at last few messages for dish names
            for msg in reversed(self.conversation_history[-4:]):
                content = msg.get('content', '')
                # Check if previous response mentioned a dish
                # Look for common dish patterns
                dish_keywords = ['dish', 'menu item', 'can make', 'brings in the most']
                if any(keyword in content.lower() for keyword in dish_keywords):
                    # Try to extract dish name from previous response
                    # Look for capitalized words or quoted text
                    words = content.split()
                    for i, word in enumerate(words):
                        if word and word[0].isupper() and len(word) > 3:
                            # Check if it's likely a dish name (not a common word)
                            if word.lower() not in ['the', 'this', 'that', 'which', 'what', 'dish', 'item']:
                                # Check next few words
                                potential_dish = ' '.join(words[i:i+3]).strip('.,!?;:')
                                if len(potential_dish) > 5:
                                    return potential_dish
        
        # If query is just "it" or "that", check last response for dish name
        if query_lower in ['it', 'that', 'this', 'the recipe', 'recipe'] or 'recipe to make it' in query_lower or 'recipe to make that' in query_lower:
            if len(self.conversation_history) >= 2:
                last_response = self.conversation_history[-1].get('content', '')
                # Try to find dish name in last response
                # Look for patterns like "dish X" or quoted names
                import re
                # Look for quoted text
                quoted = re.findall(r'"([^"]+)"', last_response)
                if quoted:
                    return quoted[0]
                # Look for "dish [name]" pattern - fix regex to avoid multiple repeat
                dish_match = re.search(r'dish[:\s]+([A-Z][a-zA-Z\s]{2,})', last_response)
                if dish_match:
                    return dish_match.group(1).strip()
                # Look for capitalized words that might be dish names
                words = last_response.split()
                for i, word in enumerate(words):
                    if word and word[0].isupper() and len(word) > 4:
                        if i + 1 < len(words) and words[i+1][0].isupper():
                            return f"{word} {words[i+1]}"
                        return word
                # Also check previous user messages for dish names
                for msg in reversed(self.conversation_history[-4:]):
                    if msg.get('role') == 'user':
                        user_content = msg.get('content', '')
                        # Extract dish name from user's previous question
                        for pattern in patterns:
                            match = re.search(pattern, user_content.lower())
                            if match:
                                dish_name = match.group(1).strip()
                                if dish_name and len(dish_name) > 2 and dish_name.lower() not in ['it', 'that', 'this']:
                                    return dish_name
        
        return None
    
    def _generate_chart(self, chart_type: str, data: Dict, title: str = "") -> Optional[str]:
        """Generate a chart and return chart info for Streamlit rendering"""
        try:
            # This will be handled in the UI layer
            # Return chart specification as JSON string
            chart_spec = {
                'type': chart_type,
                'data': data,
                'title': title
            }
            return json.dumps(chart_spec)
        except Exception as e:
            return None
    
    def _query_analytics(self, query_type: str, **kwargs) -> Dict:
        """Route query to appropriate analytics function"""
        query_map = {
            'top_ingredients': self._get_top_ingredients,
            'revenue_by_dish': self._get_revenue_by_dish,
            'waste_analysis': self._get_waste_analysis,
            'inventory_status': self._get_inventory_status,
            'cost_analysis': self._get_cost_analysis,
            'reorder_recommendations': self._get_reorder_recommendations,
            'menu_viability': self._get_menu_viability
        }
        
        if query_type not in query_map:
            return {'error': f'Unknown query type: {query_type}'}
        
        try:
            return query_map[query_type](**kwargs)
        except Exception as e:
            return {'error': str(e)}
    
    def ask(self, user_query: str) -> Tuple[str, Optional[Dict]]:
        """
        Process user query and return response
        
        Returns:
            Tuple of (response_text, chart_info_dict)
        """
        # Determine what data to fetch based on query intent
        query_lower = user_query.lower()
        chart_info = None
        result = None
        data_fetched = False
        
        # Check if user explicitly asked for a chart/graph/visualization
        # Only create charts if explicitly requested with strong keywords
        chart_keywords = ['show me a', 'display a', 'create a', 'generate a', 'draw a', 'make a', 'plot a', 'graph of', 'chart of', 'visualize', 'visualization']
        user_wants_chart = any(keyword in query_lower for keyword in chart_keywords)
        
        # Check for month-only queries first (follow-up questions)
        month, year = self._extract_month_year(user_query)
        is_followup_month_query = False
        
        # If user just says a month name (or "what about [month]"), check if previous query was about sales
        if month is not None and len(query_lower.strip().split()) <= 3:  # Short query like "November?" or "what about November"
            # Check conversation history for context
            for msg in reversed(self.conversation_history[-4:]):
                prev_content = msg.get('content', '').lower()
                # Check if previous query was about sales/revenue
                if any(word in prev_content for word in ['sales', 'revenue', 'selling', 'top selling', 'top items', 'items', 'dish', 'money', 'best selling']):
                    is_followup_month_query = True
                    break
                # Check if previous response mentioned sales data
                if msg.get('role') == 'assistant':
                    if any(word in prev_content for word in ['revenue', 'sold', 'items', 'top selling', 'sales']):
                        is_followup_month_query = True
                        break
        
        # Query routing logic - fetch relevant data
        if any(word in query_lower for word in ['most used', 'highest usage', 'top ingredient', 'ingredient used', 'which ingredient is used', 'ingredient is used', 'used the most']):
            result = self._get_top_ingredients(metric='usage', limit=10, period_days=180)
            # Only create chart if explicitly requested
            if 'error' not in result and user_wants_chart:
                chart_info = {'type': 'bar', 'data': result, 'title': 'Top Ingredients by Usage'}
            data_fetched = True
        
        elif any(word in query_lower for word in ['most wasted', 'highest waste', 'waste', 'wasted ingredient', 'which ingredient is being wasted']):
            result = self._get_waste_analysis(period_days=30, limit=10)
            # Only create chart if explicitly requested
            if 'error' not in result and user_wants_chart:
                chart_info = {'type': 'bar', 'data': result, 'title': 'Top Wasted Ingredients'}
            data_fetched = True
        
        elif is_followup_month_query or \
             any(word in query_lower for word in ['most money', 'revenue', 'highest revenue', 'best selling', 'top dish', 'which dish brings', 'brings in the most', 'top selling', 'selling items', 'sales', 'same for', 'what about']) or \
             (month is not None and any(word in query_lower for word in ['top', 'items', 'selling', 'sales'])):
            # Sales/revenue query - check if user specified a month
            # IMPORTANT: Extract month FIRST before checking "same for" logic
            # This ensures "show me the same for november" correctly extracts November
            if month is None:
                # Try to extract month again (might have been missed)
                month, year = self._extract_month_year(user_query)
            
            # Handle "same for" or "what about" queries - ONLY if no month was found in current query
            # This prevents "same for november" from using previous month
            if month is None and ('same for' in query_lower or 'same' in query_lower or 'what about' in query_lower):
                # Look for month in previous conversation ONLY if current query has no month
                for msg in reversed(self.conversation_history[-4:]):
                    prev_content = msg.get('content', '').lower()
                    prev_month, prev_year = self._extract_month_year(prev_content)
                    if prev_month is not None:
                        month, year = prev_month, prev_year
                        break
            
            if month is not None:
                # User asked for specific month - ensure we have the right year
                if year is None:
                    # Get most recent year with data for this month
                    try:
                        sales = self.analytics.data.get('sales', pd.DataFrame())
                        if not sales.empty and 'date' in sales.columns:
                            sales = sales.copy()
                            sales['date'] = pd.to_datetime(sales['date'], errors='coerce')
                            sales = sales[sales['date'].notna()]
                            month_sales = sales[sales['date'].dt.month == month]
                            if not month_sales.empty:
                                year = int(month_sales['date'].dt.year.max())
                            else:
                                year = datetime.now().year
                        else:
                            year = datetime.now().year
                    except:
                        year = datetime.now().year
                
                # User asked for specific month
                result = self._get_revenue_by_dish(month=month, year=year)
            else:
                # Default to last 30 days or all data
                result = self._get_revenue_by_dish(period_days=30)
            # Only create chart if explicitly requested
            if 'error' not in result and user_wants_chart:
                chart_info = {'type': 'bar', 'data': result, 'title': 'Revenue by Dish'}
            data_fetched = True
        
        elif any(word in query_lower for word in ['reorder', 'need to order', 'low stock', 'stockout', 'reorder recommendation']):
            result = self._get_reorder_recommendations()
            # Only create chart if explicitly requested
            if 'error' not in result and user_wants_chart:
                chart_info = {'type': 'table', 'data': result}
            data_fetched = True
        
        elif any(word in query_lower for word in ['inventory', 'current stock', 'stock level', 'inventory status']):
            result = self._get_inventory_status()
            # Only create chart if explicitly requested
            if 'error' not in result and user_wants_chart:
                chart_info = {'type': 'table', 'data': result}
            data_fetched = True
        
        elif any(word in query_lower for word in ['cost', 'spending', 'expense', 'total spending']):
            result = self._get_cost_analysis(period_days=30)
            # Only create chart if explicitly requested
            if 'error' not in result and user_wants_chart:
                chart_info = {'type': 'bar', 'data': result, 'title': 'Cost Analysis'}
            data_fetched = True
        
        elif any(word in query_lower for word in ['menu', 'dish', 'viability', 'menu viability']) or \
             'can make' in query_lower or 'can i make' in query_lower or 'what can' in query_lower or \
             'what dishes' in query_lower or 'available dishes' in query_lower:
            result = self._get_menu_viability()
            # Only create chart if explicitly requested
            if 'error' not in result and user_wants_chart:
                chart_info = {'type': 'table', 'data': result}
            data_fetched = True
        
        elif any(word in query_lower for word in ['recipe', 'how to make', 'ingredients for', 'what do i need', 'step by step', 'procedure', 'instructions', 'how do i make', 'how do you make']):
            # Recipe query - check conversation history for dish name
            dish_name = self._extract_dish_from_context(user_query)
            if dish_name:
                result = self._get_recipe_for_dish(dish_name)
                if 'error' not in result:
                    # Always mark as needing instructions - LLM will generate them
                    result['needs_instructions'] = True
                    data_fetched = True
            else:
                # If no dish name found, get menu viability to show available dishes
                result = self._get_menu_viability()
                if 'error' not in result:
                    result['info'] = 'recipe_query_no_dish'
        
        else:
            # Generic query - let LLM handle it
            greeting_words = ['hey', 'hi', 'hello', 'help', 'what can you do', 'what do you do']
            if any(word in query_lower for word in greeting_words):
                result = {'info': 'greeting'}
            else:
                # For unclear queries, let LLM try to understand and help
                result = {'info': 'general_query'}
        
        # Use LLM to generate response - it will handle both data formatting and creative content
        if result and 'error' not in result:
            if result.get('info') == 'greeting' or result.get('info') == 'help':
                # Use template for greetings/help
                response_text = self._format_response(user_query, result)
            else:
                # Use LLM for everything else - it will generate natural, creative responses
                response_text = self._generate_llm_response(user_query, result, data_fetched)
        elif result and 'error' in result:
            # Use LLM even for errors to provide helpful context
            response_text = self._generate_llm_response(user_query, result, False)
        else:
            # Unknown query - let LLM handle it with available context
            response_text = self._generate_llm_response(user_query, {'info': 'general_query'}, False)
        
        # Add messages to history
        self.conversation_history.append({"role": "user", "content": user_query})
        self.conversation_history.append({"role": "assistant", "content": response_text})
        
        return response_text, chart_info
    
    def _generate_llm_response(self, user_query: str, data_result: Dict, has_data: bool = True) -> str:
        """Generate natural language response using OpenRouter API"""
        try:
            # Build the prompt based on what data we have
            if data_result.get('info') == 'general_query':
                # No specific data - let LLM answer based on its knowledge and context
                user_content = f"""User question: {user_query}

You are helping with a restaurant inventory management system. Answer the user's question helpfully and naturally. If you need specific data that wasn't provided, explain what information would be helpful."""
            
            elif 'menu_item' in data_result and 'ingredients' in data_result:
                # Recipe query - provide ingredients and ask LLM to generate cooking instructions
                dish_name = data_result.get('menu_item', 'Unknown')
                ingredients = data_result.get('ingredients', {})
                
                user_content = f"""User is asking about making {dish_name}. Here are the ingredients available:

"""
                for ingredient, quantity in ingredients.items():
                    # Clean ingredient name
                    ing_name = ingredient.split('(')[0].strip()
                    unit = ''
                    if '(' in ingredient and ')' in ingredient:
                        unit = ingredient[ingredient.find('(')+1:ingredient.find(')')]
                    if unit:
                        user_content += f"- {ing_name}: {quantity} {unit}\n"
                    else:
                        user_content += f"- {ing_name}: {quantity}\n"
                
                user_content += f"""
Based on these ingredients, please provide:
1. A clear list of all ingredients with their quantities
2. Step-by-step cooking instructions for making {dish_name}
3. Any helpful cooking tips (temperature, timing, techniques) based on the dish type

Be creative and practical - generate reasonable cooking instructions even if you don't have the exact recipe. Use your knowledge of cooking techniques."""
            
            elif 'can_make_items' in data_result or 'viability_score' in data_result:
                # Menu viability query - format specially for "what can I make" questions
                can_make = data_result.get('can_make_items', [])
                viability_score = data_result.get('viability_score', 0)
                
                user_content = f"""User question: {user_query}

Based on current inventory, here is what can be made:

Dishes that CAN be made ({len(can_make)} dishes):"""
                
                if can_make:
                    for item in can_make:
                        servings = item.get('servings_possible', 0)
                        dish_name = item.get('menu_item', 'Unknown')
                        user_content += f"\n- {dish_name}: {servings} servings possible"
                else:
                    user_content += "\n- None (no dishes can be made with current inventory)"
                
                user_content += f"""

CRITICAL INSTRUCTIONS:
- The user asked "what can I make" - they ONLY want to know what dishes they CAN make
- List ONLY the dishes shown above (the ones that CAN be made) with their serving counts
- DO NOT mention dishes that cannot be made
- DO NOT say "however", "but", "unfortunately", or "there are X dishes you can't make"
- DO NOT list missing ingredients
- DO NOT provide examples of dishes that can't be made
- DO NOT mention the number of dishes that can't be made
- Keep your response focused ONLY on dishes that CAN be made
- Be concise and direct
- Optionally end with a brief follow-up suggestion like "Would you like cooking instructions?" or "Need help with anything else?"

Your response should start directly with the dishes that can be made, nothing else."""
            
            elif has_data:
                # Data-driven query - provide data and ask for natural response
                data_summary = json.dumps(data_result, indent=2, default=str)
                period_info = data_result.get('period_note', '')
                
                # Check if there's an error
                if 'error' in data_result:
                    error_msg = data_result.get('error', 'Unknown error')
                    user_content = f"""User question: {user_query}

I tried to retrieve the data but encountered: {error_msg}

Please provide a helpful response explaining that the data might not be available for the requested period, and suggest checking if the data has been uploaded or if a different time period might work."""
                else:
                    user_content = f"""User question: {user_query}

Here is the relevant data for {period_info}:
{data_summary}

CRITICAL INSTRUCTIONS:
- Use ONLY the data provided above - do NOT use data from previous conversation history
- The period is: {period_info}
- List the top selling items (menu items) with their revenue and quantities sold from the data above
- Total revenue for {period_info} is shown in the data
- Be specific with numbers - use the EXACT revenue and quantity values from the data provided above
- If the data shows items like "All Day Menu", "Ramen", etc., these are the actual menu items/categories
- Do NOT repeat information from previous messages - use ONLY the current data provided
- The user asked about {period_info} - make sure your answer reflects the data for that specific period"""
            
            else:
                # Error or no data
                error_msg = data_result.get('error', 'No data available')
                user_content = f"""User question: {user_query}

I encountered an issue: {error_msg}

Please provide a helpful response explaining the situation and suggesting what the user might try instead."""
            
            # Build messages for the API
            messages = [
                {"role": "system", "content": self.system_prompt},
                *self.conversation_history[-6:],  # Include last 3 exchanges for context
                {
                    "role": "user", 
                    "content": user_content
                }
            ]
            
            # Call OpenRouter API with higher token limit for creative content
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=0.8,  # Slightly higher for more creative responses
                max_tokens=800  # More tokens for recipes and detailed instructions
            )
            
            response_text = response.choices[0].message.content.strip()
            
            # Post-process to remove unwanted information about dishes that can't be made
            if 'can_make_items' in data_result:
                response_text = self._filter_unwanted_content(response_text)
            
            return response_text
            
        except Exception as e:
            # Fallback to template response if LLM fails
            error_msg = f"Error generating response: {str(e)}"
            if has_data:
                return self._format_response(user_query, data_result)
            else:
                return f"I apologize, but I encountered an error: {error_msg}. Please try rephrasing your question."
    
    def _filter_unwanted_content(self, text: str) -> str:
        """Filter out unwanted information about dishes that can't be made"""
        import re
        
        # Split by common phrases that introduce unwanted information
        unwanted_patterns = [
            r'However.*?\.',
            r'But.*?\.',
            r'Unfortunately.*?\.',
            r'However,.*?\.',
            r'However it.*?\.',
            r'However, it.*?\.',
            r'However there.*?\.',
            r'However, there.*?\.',
            r'However, it seems.*?\.',
            r'However, it looks.*?\.',
            r'However, there are.*?\.',
            r'However there are.*?\.',
            r'However, it appears.*?\.',
            r'However it appears.*?\.',
        ]
        
        # Remove sentences that contain unwanted information
        lines = text.split('\n')
        filtered_lines = []
        skip_next = False
        
        for line in lines:
            # Check if line contains unwanted patterns
            contains_unwanted = False
            for pattern in unwanted_patterns:
                if re.search(pattern, line, re.IGNORECASE):
                    contains_unwanted = True
                    break
            
            # Check for phrases that indicate unwanted content
            unwanted_phrases = [
                'dishes you can\'t make',
                'dishes you cannot make',
                'dishes that can\'t be made',
                'dishes that cannot be made',
                'can\'t make right now',
                'cannot make right now',
                'due to missing ingredients',
                'missing ingredients',
                'can\'t make',
                'cannot make',
                'other dishes',
                'few examples',
                'some dishes',
            ]
            
            for phrase in unwanted_phrases:
                if phrase.lower() in line.lower():
                    contains_unwanted = True
                    break
            
            # Skip lines with unwanted content
            if contains_unwanted:
                continue
            
            # Skip list items that mention missing ingredients
            if line.strip().startswith('-') and ('missing:' in line.lower() or 'missing ' in line.lower()):
                continue
            
            filtered_lines.append(line)
        
        return '\n'.join(filtered_lines).strip()
    
    def _format_response(self, query: str, result: Dict) -> str:
        """Format analytics result into natural language response"""
        if 'error' in result:
            return f"I couldn't retrieve that information: {result['error']}"
        
        # Handle greeting/help messages
        if 'info' in result:
            if result['info'] == 'greeting':
                return """Welcome! I'm Yun Chef, your intelligent inventory management assistant. I'm here to help you make data-driven decisions for your restaurant operations.

I can provide insights on:

• **Ingredient Analytics** - Track usage patterns and identify waste
• **Revenue Intelligence** - Analyze which dishes drive profitability
• **Inventory Status** - Monitor stock levels and identify critical items
• **Cost Analysis** - Understand spending patterns and optimize expenses
• **Menu Viability** - Determine what you can prepare with current inventory
• **Smart Reordering** - Get AI-powered recommendations for restocking

Simply ask me anything about your inventory, or click on any of the suggestions above to get started!"""
            elif result['info'] == 'help':
                return """I can help you with questions about your inventory! Try asking:

• "What ingredient is used the most?"
• "Which dish brings in the most money?"
• "Which ingredient is being wasted the most?"
• "Show me items that need reordering"
• "What's the current inventory status?"
• "Which dishes can't be made right now?"

What would you like to know?"""
            elif result['info'] == 'recipe_query_no_dish':
                # User asked for recipe but didn't specify dish - show available dishes
                can_make = result.get('can_make_items', [])
                if can_make:
                    dish_list = ', '.join([item['menu_item'] for item in can_make[:5]])
                    return f"""I'd be happy to provide a recipe! However, I need to know which dish you'd like the recipe for.

Here are some dishes you can make: {dish_list}

Please ask: What is the recipe for [dish name]? or How do I make [dish name]?

For example: What is the recipe for {can_make[0]['menu_item']}?"""
                else:
                    return """I'd be happy to provide a recipe! However, I need to know which dish you'd like the recipe for.

Please ask: What is the recipe for [dish name]? or How do I make [dish name]?"""
        
        query_lower = query.lower()
        
        # Format based on result type
        if 'metric' in result and result['metric'] == 'usage':
            data = result.get('data', [])
            if not data:
                return "No usage data available."
            top_item = data[0]
            response = f"The most used ingredient is **{top_item['ingredient']}** with {top_item.get('value', 0):,.0f} units used.\n\n"
            response += "Top 5 ingredients by usage:\n"
            for i, item in enumerate(data[:5], 1):
                response += f"{i}. {item['ingredient']}: {item.get('value', 0):,.0f} units\n"
            response += "\n*Would you like to see a chart?*"
            return response
        
        elif 'metric' in result and result['metric'] == 'waste':
            data = result.get('data', [])
            if not data:
                return "No waste data available."
            top_item = data[0]
            response = f"The most wasted ingredient is **{top_item['ingredient']}** with {top_item.get('waste', 0):,.0f} units wasted "
            response += f"(${top_item.get('waste_cost', 0):,.2f} cost).\n\n"
            response += "Top 5 wasted ingredients:\n"
            for i, item in enumerate(data[:5], 1):
                response += f"{i}. {item['ingredient']}: {item.get('waste', 0):,.0f} units (${item.get('waste_cost', 0):,.2f})\n"
            response += "\n*Would you like to see a chart?*"
            return response
        
        elif 'total_revenue' in result:
            data = result.get('data', [])
            if not data:
                return "No revenue data available."
            top_dish = data[0]
            total = result.get('total_revenue', 0)
            response = f"The dish that brings in the most money is **{top_dish['menu_item']}** "
            response += f"with ${top_dish.get('revenue', 0):,.2f} in revenue.\n\n"
            response += f"Total revenue: ${total:,.2f}\n\n"
            response += "Top 5 dishes by revenue:\n"
            for i, item in enumerate(data[:5], 1):
                response += f"{i}. {item['menu_item']}: ${item.get('revenue', 0):,.2f} ({item.get('quantity_sold', 0):,.0f} sold)\n"
            response += "\n*Would you like to see a chart?*"
            return response
        
        elif 'viability_score' in result:
            score = result.get('viability_score', 0)
            can_make = result.get('can_make_count', 0)
            can_make_items = result.get('can_make_items', [])
            response = f"Menu viability score: **{score:.1f}%**\n\n"
            response += f"Dishes you can make ({can_make} dishes):\n"
            for item in can_make_items:
                dish_name = item.get('menu_item', 'Unknown')
                servings = item.get('servings_possible', 0)
                response += f"- {dish_name}: {servings} servings\n"
            return response
        
        elif 'total_waste_cost' in result:
            data = result.get('data', [])
            total_cost = result.get('total_waste_cost', 0)
            response = f"Total waste cost: **${total_cost:,.2f}**\n\n"
            response += "Top wasted ingredients:\n"
            for i, item in enumerate(data[:5], 1):
                response += f"{i}. {item['ingredient']}: {item.get('waste', 0):,.0f} units (${item.get('waste_cost', 0):,.2f})\n"
            return response
        
        elif 'low_stock_count' in result:
            low_stock = result.get('low_stock_count', 0)
            reorder = result.get('reorder_needed_count', 0)
            response = f"Current inventory status:\n\n"
            response += f"- Total ingredients: {result.get('total_ingredients', 0)}\n"
            response += f"- Low stock items: {low_stock}\n"
            response += f"- Items needing reorder: {reorder}\n"
            if low_stock > 0:
                low_items = result.get('low_stock_items', [])
                response += "\nLow stock items:\n"
                for item in low_items[:5]:
                    response += f"- {item['ingredient']}: {item.get('current_stock', 0):,.0f} (min: {item.get('min_stock_level', 0):,.0f})\n"
            return response
        
        elif 'total_spending' in result:
            total = result.get('total_spending', 0)
            avg_daily = result.get('avg_daily_spending', 0)
            response = f"Cost analysis:\n\n"
            response += f"- Total spending: **${total:,.2f}**\n"
            response += f"- Average daily spending: **${avg_daily:,.2f}**\n"
            top_ingredients = result.get('top_spending_ingredients', pd.DataFrame())
            if not top_ingredients.empty:
                response += "\nTop spending ingredients:\n"
                for i, row in top_ingredients.head(5).iterrows():
                    response += f"- {row.get('ingredient', 'Unknown')}: ${row.get('value', 0):,.2f}\n"
            return response
        
        elif 'total_items' in result:
            data = result.get('data', [])
            response = f"Reorder recommendations: **{result.get('total_items', 0)} items** need reordering.\n\n"
            for i, item in enumerate(data[:5], 1):
                urgency = item.get('urgency', 'Unknown')
                ingredient = item.get('ingredient', 'Unknown')
                response += f"{i}. {ingredient} ({urgency} urgency)\n"
            return response
        
        elif 'menu_item' in result and 'ingredients' in result:
            # Recipe response
            menu_item = result.get('menu_item', 'Unknown Dish')
            ingredients = result.get('ingredients', {})
            ingredient_count = result.get('ingredient_count', 0)
            
            response = f"**Recipe for {menu_item}**\n\n"
            response += f"Ingredients needed ({ingredient_count} total):\n\n"
            
            for ingredient, quantity in ingredients.items():
                # Format ingredient name (remove units if in parentheses)
                ing_name = ingredient.split('(')[0].strip()
                unit = ''
                if '(' in ingredient and ')' in ingredient:
                    unit = ingredient[ingredient.find('('):ingredient.find(')')+1]
                
                if unit:
                    response += f"• {ing_name}: {quantity} {unit}\n"
                else:
                    response += f"• {ing_name}: {quantity}\n"
            
            return response
        
        else:
            # Generic response
            return "I retrieved the information, but I'm not sure how to format it. Here's the raw data:\n\n" + str(result)
    
    def clear_history(self):
        """Clear conversation history"""
        self.conversation_history = []

