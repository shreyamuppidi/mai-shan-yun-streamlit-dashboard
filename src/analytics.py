"""
Analytics and Predictive Modeling Module
Provides inventory forecasting and trend analysis
"""
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional
from sklearn.linear_model import LinearRegression
from sklearn.preprocessing import StandardScaler
import warnings
import holidays
warnings.filterwarnings('ignore')

# Try to import DataPreprocessor
try:
    from .data_preprocessor import DataPreprocessor
except ImportError:
    try:
        from data_preprocessor import DataPreprocessor
    except ImportError:
        DataPreprocessor = None


class InventoryAnalytics:
    """Analytics and forecasting for inventory management"""
    
    def __init__(self, data: Dict[str, pd.DataFrame]):
        self.data = data
        self.forecast_cache = {}
        # Initialize preprocessor if available
        if DataPreprocessor is not None:
            self.preprocessor = DataPreprocessor()
        else:
            self.preprocessor = None
    
    def calculate_inventory_levels(self, current_date: Optional[datetime] = None) -> pd.DataFrame:
        """Calculate current inventory levels based on purchases and usage"""
        if current_date is None:
            current_date = datetime.now()
        
        purchases = self.data.get('purchases', pd.DataFrame())
        usage = self.data.get('usage', pd.DataFrame())
        ingredients = self.data.get('ingredients', pd.DataFrame())
        
        if purchases.empty or usage.empty:
            return pd.DataFrame()
        
        # Filter data up to current date
        purchases = purchases[purchases['date'] <= current_date].copy()
        usage = usage[usage['date'] <= current_date].copy()
        
        # Aggregate purchases by ingredient
        purchase_agg = purchases.groupby('ingredient').agg({
            'quantity': 'sum'
        }).reset_index()
        purchase_agg.columns = ['ingredient', 'total_purchased']
        
        # Aggregate usage by ingredient
        usage_agg = usage.groupby('ingredient').agg({
            'quantity_used': 'sum'
        }).reset_index()
        usage_agg.columns = ['ingredient', 'total_used']
        
        # Merge and calculate current inventory
        inventory = purchase_agg.merge(usage_agg, on='ingredient', how='outer').fillna(0)
        inventory['current_stock'] = inventory['total_purchased'] - inventory['total_used']
        # Ensure current_stock is never negative (cap at 0)
        inventory['current_stock'] = inventory['current_stock'].apply(lambda x: max(0, float(x)) if pd.notna(x) else 0)
        
        # Merge with ingredient master for min/max levels
        if not ingredients.empty and 'ingredient' in ingredients.columns:
            inventory = inventory.merge(
                ingredients[['ingredient', 'min_stock_level', 'max_stock_level']],
                on='ingredient',
                how='left'
            )
            inventory['min_stock_level'] = inventory['min_stock_level'].fillna(20)
            inventory['max_stock_level'] = inventory['max_stock_level'].fillna(200)
        else:
            inventory['min_stock_level'] = 20
            inventory['max_stock_level'] = 200
        
        # Calculate stock status
        inventory['stock_status'] = inventory.apply(
            lambda row: 'Low' if row['current_stock'] < row['min_stock_level']
            else 'High' if row['current_stock'] > row['max_stock_level']
            else 'Normal',
            axis=1
        )
        
        inventory['reorder_needed'] = inventory['current_stock'] < inventory['min_stock_level']
        inventory['days_until_stockout'] = inventory.apply(
            lambda row: self._estimate_days_until_stockout(row['ingredient'], row['current_stock'])
            if row['current_stock'] > 0 else 0,
            axis=1
        )
        
        return inventory
    
    def _estimate_days_until_stockout(self, ingredient: str, current_stock: float) -> int:
        """Estimate days until stockout based on historical usage"""
        usage = self.data.get('usage', pd.DataFrame())
        if usage.empty or current_stock <= 0:
            return 0  # Out of stock
        
        # Normalize ingredient name for matching
        if self.preprocessor:
            normalize_ingredient_name = lambda name: self.preprocessor.normalize_ingredient_name(name).lower()
        else:
            def normalize_ingredient_name(name):
                if pd.isna(name):
                    return ""
                name = str(name).strip().lower()
                for suffix in [' (g)', '(g)', ' used', ' used (g)', ' (kg)', '(kg)', ' (oz)', '(oz)', 
                              ' (count)', '(count)', ' (pcs)', '(pcs)', ' (lb)', '(lb)', ' braised', 'braised ']:
                    name = name.replace(suffix, '')
                name = ' '.join(name.split())
                return name
        
        # Try exact match first
        ingredient_usage = usage[usage['ingredient'] == ingredient].copy()
        
        # If no exact match, try normalized matching
        if ingredient_usage.empty:
            ingredient_norm = normalize_ingredient_name(ingredient)
            usage['ingredient_normalized'] = usage['ingredient'].apply(normalize_ingredient_name)
            
            # Find best match
            exact_match = usage[usage['ingredient_normalized'] == ingredient_norm]
            if not exact_match.empty:
                ingredient_usage = exact_match.copy()
            else:
                # Try partial match
                partial_matches = usage[usage['ingredient_normalized'].str.contains(ingredient_norm, na=False, regex=False)]
                if not partial_matches.empty:
                    # Take the most specific match (shortest name)
                    best_match_name = partial_matches.loc[partial_matches['ingredient_normalized'].str.len().idxmin(), 'ingredient']
                    ingredient_usage = usage[usage['ingredient'] == best_match_name].copy()
        
        if ingredient_usage.empty:
            return 30  # Default if no usage data found
        
        # Calculate average daily usage over last 30 days
        recent_date = datetime.now() - timedelta(days=30)
        recent_usage = ingredient_usage[ingredient_usage['date'] >= recent_date]
        
        if recent_usage.empty:
            # Use overall average
            avg_daily = ingredient_usage['quantity_used'].mean()
        else:
            days_span = (recent_usage['date'].max() - recent_usage['date'].min()).days + 1
            total_usage = recent_usage['quantity_used'].sum()
            avg_daily = total_usage / days_span if days_span > 0 else ingredient_usage['quantity_used'].mean()
        
        if avg_daily <= 0:
            return 999  # No usage
        
        days_until_stockout = int(current_stock / avg_daily) if avg_daily > 0 else 999
        return max(0, min(days_until_stockout, 365))
    
    def forecast_demand(self, ingredient: str, days_ahead: int = 30, 
                       method: str = 'moving_average') -> pd.DataFrame:
        """Forecast future ingredient demand"""
        usage = self.data.get('usage', pd.DataFrame())
        if usage.empty:
            return pd.DataFrame()
        
        # Try exact match first
        ingredient_usage = usage[usage['ingredient'] == ingredient].copy()
        
        # If no exact match, try normalized matching (same as reorder recommendations)
        if ingredient_usage.empty:
            if self.preprocessor:
                normalize_ingredient_name = lambda name: self.preprocessor.normalize_ingredient_name(name).lower()
                ingredient_norm = normalize_ingredient_name(ingredient)
            else:
                def normalize_ingredient_name(name):
                    if pd.isna(name):
                        return ""
                    name = str(name).strip().lower()
                    for suffix in [' (g)', '(g)', ' used', ' used (g)', ' (kg)', '(kg)', ' (oz)', '(oz)', 
                                  ' (count)', '(count)', ' (pcs)', '(pcs)', ' (lb)', '(lb)', ' braised', 'braised ']:
                        name = name.replace(suffix, '')
                    name = ' '.join(name.split())
                    return name
                ingredient_norm = normalize_ingredient_name(ingredient)
            usage['ingredient_normalized'] = usage['ingredient'].apply(normalize_ingredient_name)
            
            # Try normalized match
            exact_match = usage[usage['ingredient_normalized'] == ingredient_norm]
            if not exact_match.empty:
                ingredient_usage = exact_match.copy()
            else:
                # Try partial match
                partial_matches = usage[usage['ingredient_normalized'].str.contains(ingredient_norm, na=False, regex=False)]
                if not partial_matches.empty:
                    # Take the best match (shortest name, most specific)
                    best_match_name = partial_matches.loc[partial_matches['ingredient_normalized'].str.len().idxmin(), 'ingredient']
                    ingredient_usage = usage[usage['ingredient'] == best_match_name].copy()
        
        if ingredient_usage.empty:
            return pd.DataFrame()
        
        # Aggregate by date
        daily_usage = ingredient_usage.groupby('date').agg({
            'quantity_used': 'sum'
        }).reset_index()
        daily_usage = daily_usage.sort_values('date')
        
        if method == 'moving_average':
            return self._forecast_moving_average(daily_usage, days_ahead)
        elif method == 'linear_trend':
            return self._forecast_linear_trend(daily_usage, days_ahead)
        else:
            return self._forecast_moving_average(daily_usage, days_ahead)
    
    def _forecast_moving_average(self, daily_usage: pd.DataFrame, days_ahead: int) -> pd.DataFrame:
        """Forecast using moving average"""
        # Calculate 7-day and 30-day moving averages
        daily_usage['ma_7'] = daily_usage['quantity_used'].rolling(window=7, min_periods=1).mean()
        daily_usage['ma_30'] = daily_usage['quantity_used'].rolling(window=30, min_periods=1).mean()
        
        # Use weighted average of recent moving averages
        recent_ma7 = daily_usage['ma_7'].iloc[-7:].mean()
        recent_ma30 = daily_usage['ma_30'].iloc[-30:].mean() if len(daily_usage) >= 30 else recent_ma7
        
        forecast_value = (recent_ma7 * 0.6 + recent_ma30 * 0.4)
        
        # Generate forecast dates
        last_date = daily_usage['date'].max()
        forecast_dates = pd.date_range(
            start=last_date + timedelta(days=1),
            periods=days_ahead,
            freq='D'
        )
        
        forecast_df = pd.DataFrame({
            'date': forecast_dates,
            'forecasted_usage': forecast_value,
            'confidence_low': forecast_value * 0.8,
            'confidence_high': forecast_value * 1.2
        })
        
        return forecast_df
    
    def _forecast_linear_trend(self, daily_usage: pd.DataFrame, days_ahead: int) -> pd.DataFrame:
        """Forecast using linear regression trend"""
        if len(daily_usage) < 7:
            return self._forecast_moving_average(daily_usage, days_ahead)
        
        # Prepare data for regression
        daily_usage = daily_usage.copy()
        daily_usage['days'] = (daily_usage['date'] - daily_usage['date'].min()).dt.days
        
        X = daily_usage[['days']].values
        y = daily_usage['quantity_used'].values
        
        # Fit linear model
        model = LinearRegression()
        model.fit(X, y)
        
        # Generate forecast
        last_date = daily_usage['date'].max()
        last_days = daily_usage['days'].max()
        forecast_dates = pd.date_range(
            start=last_date + timedelta(days=1),
            periods=days_ahead,
            freq='D'
        )
        
        forecast_days = np.array([last_days + i + 1 for i in range(days_ahead)])
        forecast_values = model.predict(forecast_days.reshape(-1, 1))
        
        # Ensure non-negative
        forecast_values = np.maximum(forecast_values, 0)
        
        # Calculate confidence intervals (simple std-based)
        residuals = y - model.predict(X)
        std_error = np.std(residuals)
        
        forecast_df = pd.DataFrame({
            'date': forecast_dates,
            'forecasted_usage': forecast_values,
            'confidence_low': forecast_values - 1.96 * std_error,
            'confidence_high': forecast_values + 1.96 * std_error
        })
        
        forecast_df['confidence_low'] = forecast_df['confidence_low'].clip(lower=0)
        
        return forecast_df
    
    def get_usage_trends(self, ingredient: Optional[str] = None, 
                        period: str = 'monthly') -> pd.DataFrame:
        """Get usage trends over time"""
        usage = self.data.get('usage', pd.DataFrame())
        if usage.empty:
            return pd.DataFrame()
        
        usage_df = usage.copy()
        
        if ingredient:
            usage_df = usage_df[usage_df['ingredient'] == ingredient]
        
        usage_df['year'] = usage_df['date'].dt.year.astype(int)
        usage_df['month'] = usage_df['date'].dt.month.astype(int)
        usage_df['week'] = usage_df['date'].dt.isocalendar().week.astype(int)
        usage_df['day_of_week'] = usage_df['date'].dt.dayofweek.astype(int)
        
        if period == 'monthly':
            trends = usage_df.groupby(['year', 'month']).agg({
                'quantity_used': 'sum'
            }).reset_index()
            trends['period'] = pd.to_datetime(
                trends[['year', 'month']].assign(day=1)
            )
        elif period == 'weekly':
            trends = usage_df.groupby(['year', 'week']).agg({
                'quantity_used': 'sum'
            }).reset_index()
            trends['period'] = trends.apply(
                lambda row: pd.Timestamp.fromisocalendar(int(row['year']), int(row['week']), 1),
                axis=1
            )
        else:  # daily
            trends = usage_df.groupby('date').agg({
                'quantity_used': 'sum'
            }).reset_index()
            trends['period'] = trends['date']
        
        return trends.sort_values('period')
    
    def get_top_ingredients(self, metric: str = 'usage', limit: int = 10, 
                           period_days: int = 30) -> pd.DataFrame:
        """Get top ingredients by usage or cost"""
        cutoff_date = datetime.now() - timedelta(days=period_days)
        
        if metric == 'usage':
            usage = self.data.get('usage', pd.DataFrame())
            if usage.empty:
                return pd.DataFrame()
            
            # Filter by date, but if no data in last period_days, use most recent data available
            recent_usage = usage[usage['date'] >= cutoff_date]
            
            # If no data in the requested period, use the most recent period_days worth of data
            if recent_usage.empty:
                # Get the most recent date in the data
                max_date = usage['date'].max()
                if pd.notna(max_date):
                    # Use data from the most recent period_days
                    min_date = max_date - timedelta(days=period_days)
                    recent_usage = usage[usage['date'] >= min_date]
            
            if recent_usage.empty:
                return pd.DataFrame()
            
            top = recent_usage.groupby('ingredient').agg({
                'quantity_used': 'sum'
            }).reset_index().sort_values('quantity_used', ascending=False).head(limit)
            top.columns = ['ingredient', 'value']
            top['metric'] = 'Usage'
            
        elif metric == 'cost':
            purchases = self.data.get('purchases', pd.DataFrame())
            if purchases.empty:
                return pd.DataFrame()
            
            # Filter by date, but if no data in last period_days, use most recent data available
            recent_purchases = purchases[purchases['date'] >= cutoff_date].copy()
            
            # If no data in the requested period, use the most recent period_days worth of data
            if recent_purchases.empty:
                # Get the most recent date in the data
                max_date = purchases['date'].max()
                if pd.notna(max_date):
                    # Use data from the most recent period_days
                    min_date = max_date - timedelta(days=period_days)
                    recent_purchases = purchases[purchases['date'] >= min_date].copy()
            
            if recent_purchases.empty:
                return pd.DataFrame()
            
            # Estimate missing costs
            recent_purchases = self._estimate_missing_costs(recent_purchases)
            
            top = recent_purchases.groupby('ingredient').agg({
                'total_cost': 'sum'
            }).reset_index().sort_values('total_cost', ascending=False).head(limit)
            top.columns = ['ingredient', 'value']
            top['metric'] = 'Cost'
        
        else:
            return pd.DataFrame()
        
        return top
    
    def analyze_shipment_delays(self) -> pd.DataFrame:
        """Analyze shipment delay patterns"""
        shipments = self.data.get('shipments', pd.DataFrame())
        if shipments.empty:
            return pd.DataFrame()
        
        # Check if we have date information for delay analysis
        has_date_info = False
        shipments_copy = shipments.copy()
        
        if 'delay_days' in shipments_copy.columns:
            has_date_info = True
        elif 'expected_date' in shipments_copy.columns and 'date' in shipments_copy.columns:
            shipments_copy['delay_days'] = (
                pd.to_datetime(shipments_copy['date'], errors='coerce') - 
                pd.to_datetime(shipments_copy['expected_date'], errors='coerce')
            ).dt.days
            has_date_info = True
        elif 'date' in shipments_copy.columns:
            # If we only have date, we can't calculate delays but can still show shipment info
            # Return empty to indicate delay analysis not possible
            return pd.DataFrame()
        
        if not has_date_info:
            return pd.DataFrame()
        
        delay_analysis = shipments_copy.groupby('ingredient').agg({
            'delay_days': ['mean', 'max', 'count'],
            'status': lambda x: (x == 'Delayed').sum() if 'status' in shipments_copy.columns else pd.Series([0] * len(x))
        }).reset_index()
        
        delay_analysis.columns = ['ingredient', 'avg_delay', 'max_delay', 'total_shipments', 'delayed_count']
        delay_analysis['delay_rate'] = delay_analysis['delayed_count'] / delay_analysis['total_shipments']
        
        return delay_analysis.sort_values('avg_delay', ascending=False)
    
    def _estimate_missing_costs(self, purchases: pd.DataFrame) -> pd.DataFrame:
        """Estimate costs for purchases that have zero or missing cost data"""
        purchases = purchases.copy()
        
        if 'total_cost' not in purchases.columns:
            purchases['total_cost'] = 0
        
        if 'quantity' not in purchases.columns:
            purchases['quantity'] = 0
        
        # Check if we have any purchases with actual cost data
        purchases_with_cost = purchases[
            (purchases['total_cost'] > 0) & 
            (purchases['quantity'] > 0)
        ]
        
        if not purchases_with_cost.empty:
            # Calculate average unit cost per ingredient from purchases with cost data
            avg_unit_costs = purchases_with_cost.groupby('ingredient').apply(
                lambda x: (x['total_cost'].sum() / x['quantity'].sum()) if x['quantity'].sum() > 0 else 0
            ).to_dict()
            
            # Estimate costs for purchases with zero or missing costs
            for idx, row in purchases.iterrows():
                if row['total_cost'] == 0 and row['quantity'] > 0:
                    ingredient = row['ingredient']
                    if ingredient in avg_unit_costs and avg_unit_costs[ingredient] > 0:
                        purchases.at[idx, 'total_cost'] = row['quantity'] * avg_unit_costs[ingredient]
        else:
            # No cost data available - use estimated unit costs based on ingredient types
            def estimate_unit_cost(ingredient: str, quantity: float) -> float:
                """Estimate unit cost based on ingredient type"""
                ingredient_lower = str(ingredient).lower()
                
                # Meat products (higher cost)
                if any(word in ingredient_lower for word in ['beef', 'chicken', 'pork', 'meat', 'braised']):
                    return 8.0  # $8 per unit (e.g., per 100g)
                
                # Seafood
                elif any(word in ingredient_lower for word in ['fish', 'shrimp', 'seafood']):
                    return 12.0
                
                # Vegetables (medium cost)
                elif any(word in ingredient_lower for word in ['onion', 'cabbage', 'carrot', 'peas', 'boychoy', 'cilantro', 'green']):
                    return 2.0
                
                # Staple items (lower cost)
                elif any(word in ingredient_lower for word in ['rice', 'noodle', 'flour', 'starch']):
                    return 1.5
                
                # Eggs and dairy
                elif any(word in ingredient_lower for word in ['egg', 'milk', 'dairy']):
                    return 0.5
                
                # Sauces and condiments
                elif any(word in ingredient_lower for word in ['sauce', 'oil', 'vinegar', 'soy', 'pickle']):
                    return 3.0
                
                # Default estimate
                else:
                    return 2.5
            
            # Apply estimates
            for idx, row in purchases.iterrows():
                if row['total_cost'] == 0 and row['quantity'] > 0:
                    unit_cost = estimate_unit_cost(row['ingredient'], row['quantity'])
                    purchases.at[idx, 'total_cost'] = row['quantity'] * unit_cost
        
        return purchases
    
    def get_cost_analysis(self, period_days: int = 30) -> Dict:
        """Analyze costs and spending patterns"""
        purchases = self.data.get('purchases', pd.DataFrame())
        if purchases.empty:
            return {}
        
        cutoff_date = datetime.now() - timedelta(days=period_days)
        recent_purchases = purchases[purchases['date'] >= cutoff_date].copy()
        
        if recent_purchases.empty:
            return {}
        
        # Estimate missing costs
        recent_purchases = self._estimate_missing_costs(recent_purchases)
        
        # Calculate metrics
        total_spending = recent_purchases['total_cost'].sum() if 'total_cost' in recent_purchases.columns else 0
        
        # Calculate average daily spending
        if 'date' in recent_purchases.columns and 'total_cost' in recent_purchases.columns:
            daily_spending = recent_purchases.groupby('date')['total_cost'].sum()
            avg_daily_spending = daily_spending.mean() if not daily_spending.empty else 0
        else:
            avg_daily_spending = 0
        
        # Spending trend
        if 'date' in recent_purchases.columns and 'total_cost' in recent_purchases.columns:
            spending_trend = recent_purchases.groupby('date')['total_cost'].sum().reset_index()
            spending_trend.columns = ['date', 'total_cost']
        else:
            spending_trend = pd.DataFrame()
        
        # Spending by supplier
        if 'supplier' in recent_purchases.columns and 'total_cost' in recent_purchases.columns:
            spending_by_supplier = recent_purchases.groupby('supplier')['total_cost'].sum().to_dict()
        else:
            spending_by_supplier = {}
        
        analysis = {
            'total_spending': total_spending,
            'avg_daily_spending': avg_daily_spending,
            'top_spending_ingredients': self.get_top_ingredients('cost', 10, period_days),
            'spending_by_supplier': spending_by_supplier,
            'spending_trend': spending_trend
        }
        
        return analysis
    
    def calculate_reorder_recommendations(self, current_date: Optional[datetime] = None, 
                                         include_seasonality: bool = True) -> pd.DataFrame:
        """Calculate reorder recommendations based on current stock and forecasted demand"""
        if current_date is None:
            current_date = datetime.now()
            
        inventory = self.calculate_inventory_levels(current_date)
        
        if inventory.empty:
            return pd.DataFrame()
        
        usage = self.data.get('usage', pd.DataFrame())
        purchases = self.data.get('purchases', pd.DataFrame())
        shipments = self.data.get('shipments', pd.DataFrame())
        
        recommendations = []
        
        for _, row in inventory.iterrows():
            ingredient = row['ingredient']
            current_stock = row['current_stock']
            min_stock = row['min_stock_level']
            max_stock = row.get('max_stock_level', min_stock * 10)
            days_until_stockout = row['days_until_stockout']
            
            # Show items that need reordering: below min stock OR will run out within 30 days
            # This ensures we show items with different urgency levels (not just Critical)
            if current_stock >= min_stock and days_until_stockout > 30:
                continue  # Skip items that are well-stocked for more than 30 days
            
            # Calculate forecasted demand for next 30 days
            # Try to get forecast, but use historical average if forecast fails
            forecasted_demand_30d = 0
            has_forecast_data = False
            
            # Get unit information for this ingredient FIRST (needed for conversion)
            ingredient_unit = None
            if not shipments.empty and 'ingredient' in shipments.columns:
                ingredient_shipments = shipments[shipments['ingredient'] == ingredient]
                if not ingredient_shipments.empty:
                    if 'unit' in shipments.columns:
                        ingredient_unit = ingredient_shipments.iloc[0].get('unit', '')
                    elif 'Unit of shipment' in shipments.columns:
                        ingredient_unit = ingredient_shipments.iloc[0].get('Unit of shipment', '')
            
            # Check if ingredient is count-based
            def is_count_based(ingredient_name, unit=None):
                """Check if ingredient is count-based (pieces, rolls, eggs) vs weight-based"""
                ingredient_lower = str(ingredient_name).lower()
                unit_lower = str(unit).lower() if unit and pd.notna(unit) else ""
                count_keywords = ['wing', 'ramen', 'egg', 'count', 'pcs', 'piece', 'roll', 'whole']
                if any(keyword in unit_lower for keyword in count_keywords):
                    return True
                if any(keyword in ingredient_lower for keyword in ['wing', 'ramen', 'egg']):
                    return True
                return False
            
            is_count_based_ingredient = is_count_based(ingredient, ingredient_unit)
            
            # Try forecast first, but validate and convert the results
            try:
                forecast = self.forecast_demand(ingredient, days_ahead=30)
                if include_seasonality and not forecast.empty:
                    forecast = self.adjust_forecast_for_events(ingredient, forecast)
                
                if not forecast.empty and 'forecasted_usage' in forecast.columns:
                    forecasted_demand_30d = forecast['forecasted_usage'].sum()
                    
                    # Convert forecast to match inventory unit (usage is in grams, need to convert)
                    # Usage data from recipes is always in grams, so we always need to convert
                    if is_count_based_ingredient:
                        # For count-based items, convert grams to count
                        # Always convert for count-based items (usage is in grams, inventory is in count)
                        estimated_weight_per_unit = 50  # Default
                        if 'ramen' in ingredient.lower():
                            estimated_weight_per_unit = 100  # Ramen ~100g per pack
                        elif 'egg' in ingredient.lower():
                            estimated_weight_per_unit = 50  # Egg ~50g
                        elif 'wing' in ingredient.lower():
                            estimated_weight_per_unit = 30  # Wing ~30g per piece
                        forecasted_demand_30d = forecasted_demand_30d / estimated_weight_per_unit
                    else:
                        # For weight-based items, convert grams to purchase unit
                        # Always convert for weight-based items (usage is in grams, purchase unit is likely lbs/oz)
                        if ingredient_unit:
                            unit_lower = str(ingredient_unit).lower()
                            G_TO_LB = 1 / 453.592
                            G_TO_OZ = 1 / 28.3495
                            G_TO_KG = 1 / 1000
                            
                            if 'lb' in unit_lower or 'pound' in unit_lower:
                                forecasted_demand_30d = forecasted_demand_30d * G_TO_LB
                            elif 'oz' in unit_lower or 'ounce' in unit_lower:
                                forecasted_demand_30d = forecasted_demand_30d * G_TO_OZ
                            elif 'kg' in unit_lower or 'kilogram' in unit_lower:
                                forecasted_demand_30d = forecasted_demand_30d * G_TO_KG
                            # If unit is 'g' or 'gram', keep as is (already in grams)
                        else:
                            # No unit specified, convert to lbs for readability (most ingredients purchased in lbs)
                            forecasted_demand_30d = forecasted_demand_30d * (1 / 453.592)
                    
                    # Validate forecast - if still unreasonable, skip it
                    if forecasted_demand_30d > max_stock * 10:
                        # Forecast is still unreasonable, will use historical average instead
                        has_forecast_data = False
                    else:
                        has_forecast_data = True
                else:
                    has_forecast_data = False
            except:
                has_forecast_data = False
            
            # Track if we found usage data
            found_usage_data = False
            
            # If no forecast, use historical average daily usage
            if not has_forecast_data and not usage.empty:
                # Normalize ingredient name for matching (same as waste analysis)
                if self.preprocessor:
                    normalize_ingredient_name = lambda name: self.preprocessor.normalize_ingredient_name(name).lower()
                else:
                    def normalize_ingredient_name(name):
                        if pd.isna(name):
                            return ""
                        name = str(name).strip().lower()
                        for suffix in [' (g)', '(g)', ' used', ' used (g)', ' (kg)', '(kg)', ' (oz)', '(oz)', 
                                      ' (count)', '(count)', ' (pcs)', '(pcs)', ' (lb)', '(lb)', ' braised', 'braised ']:
                            name = name.replace(suffix, '')
                        name = ' '.join(name.split())
                        return name
                
                # Get usage data and match ingredients - use robust matching like waste analysis
                recent_usage = usage[usage['date'] >= (current_date - timedelta(days=30))].copy()
                if not recent_usage.empty:
                    # Aggregate usage by ingredient
                    usage_totals = recent_usage.groupby('ingredient')['quantity_used'].sum().reset_index()
                    usage_totals['ingredient_normalized'] = usage_totals['ingredient'].apply(normalize_ingredient_name)
                    
                    ingredient_norm = normalize_ingredient_name(ingredient)
                    
                    # Multi-strategy matching - find the BEST match, not all matches
                    # Strategy 1: Exact normalized match
                    exact_match = usage_totals[usage_totals['ingredient_normalized'] == ingredient_norm]
                    if not exact_match.empty:
                        matched_usage = exact_match.iloc[0]  # Take first exact match
                    else:
                        # Strategy 2: Partial match (ingredient name contains normalized name)
                        partial_matches = usage_totals[
                            usage_totals['ingredient_normalized'].str.contains(ingredient_norm, na=False, regex=False)
                        ]
                        if not partial_matches.empty:
                            # Take the best match (shortest name, most specific)
                            matched_usage = partial_matches.loc[partial_matches['ingredient_normalized'].str.len().idxmin()]
                        else:
                            # Strategy 3: Reverse partial match (normalized name contains usage ingredient)
                            reverse_matches = usage_totals[
                                usage_totals['ingredient_normalized'].apply(
                                    lambda x: ingredient_norm in str(x) if pd.notna(x) else False
                                )
                            ]
                            if not reverse_matches.empty:
                                matched_usage = reverse_matches.iloc[0]
                            else:
                                matched_usage = None
                    
                    if matched_usage is not None:
                        # Handle Series access (from .iloc[0])
                        if isinstance(matched_usage, pd.Series):
                            total_usage = matched_usage['quantity_used'] if 'quantity_used' in matched_usage.index else 0
                        else:
                            total_usage = 0
                        
                        if not pd.isna(total_usage) and total_usage > 0:
                            days_in_period = max(1, (recent_usage['date'].max() - recent_usage['date'].min()).days + 1)
                            avg_daily_usage = total_usage / days_in_period
                            
                            # Convert usage to match inventory/purchase unit
                            # Usage from recipes is always in grams, so we always need to convert
                            if is_count_based_ingredient:
                                # For count-based items (Ramen, Egg, Wings), convert grams to count
                                # Always convert for count-based items (usage is in grams, inventory is in count)
                                estimated_weight_per_unit = 50  # Default estimate (grams per unit)
                                if 'ramen' in ingredient.lower():
                                    estimated_weight_per_unit = 100  # Ramen ~100g per pack
                                elif 'egg' in ingredient.lower():
                                    estimated_weight_per_unit = 50  # Egg ~50g
                                elif 'wing' in ingredient.lower():
                                    estimated_weight_per_unit = 30  # Wing ~30g per piece
                                
                                # Convert grams to estimated count
                                avg_daily_usage = avg_daily_usage / estimated_weight_per_unit
                            else:
                                # For weight-based items, convert from grams to purchase unit
                                # Always convert for weight-based items (usage is in grams, purchase unit is likely lbs/oz)
                                if ingredient_unit:
                                    unit_lower = str(ingredient_unit).lower()
                                    # Conversion factors
                                    G_TO_LB = 1 / 453.592
                                    G_TO_OZ = 1 / 28.3495
                                    G_TO_KG = 1 / 1000
                                    
                                    if 'lb' in unit_lower or 'pound' in unit_lower:
                                        # Convert grams to pounds
                                        avg_daily_usage = avg_daily_usage * G_TO_LB
                                    elif 'oz' in unit_lower or 'ounce' in unit_lower:
                                        # Convert grams to ounces
                                        avg_daily_usage = avg_daily_usage * G_TO_OZ
                                    elif 'kg' in unit_lower or 'kilogram' in unit_lower:
                                        # Convert grams to kilograms
                                        avg_daily_usage = avg_daily_usage * G_TO_KG
                                    # If unit is 'g' or 'gram', keep as is (already in grams)
                                else:
                                    # No unit specified, convert to lbs for readability (most ingredients purchased in lbs)
                                    avg_daily_usage = avg_daily_usage * (1 / 453.592)  # Convert to lbs
                            
                            forecasted_demand_30d = avg_daily_usage * 30
                            
                            # Cap unreasonable forecasts - if forecast > 5x max_stock, likely unit mismatch
                            # Use a much more conservative estimate
                            if forecasted_demand_30d > max_stock * 5:
                                # Likely unit mismatch (grams vs count) - use conservative estimate
                                if days_until_stockout > 0 and current_stock > 0:
                                    # Use current stock consumption rate
                                    forecasted_demand_30d = (current_stock / days_until_stockout) * 30
                                elif min_stock > 0:
                                    # Use min_stock as conservative monthly estimate
                                    forecasted_demand_30d = min_stock * 3  # 3x min stock as conservative estimate
                                else:
                                    forecasted_demand_30d = 20  # Very conservative default
                                found_usage_data = False  # Mark as limited since we had to cap it
                            else:
                                found_usage_data = True
                    elif days_until_stockout > 0 and current_stock > 0:
                        # Fallback: estimate from current stock and days until stockout
                        avg_daily_usage = current_stock / days_until_stockout
                        forecasted_demand_30d = avg_daily_usage * 30
                        found_usage_data = False  # Using fallback, not real usage data
                    else:
                        # No usage data and no stock - use a conservative default
                        # Estimate based on min_stock (assume we need min_stock per month)
                        forecasted_demand_30d = min_stock * 1.5  # 1.5x min stock as conservative estimate
                        found_usage_data = False
            
            # Calculate recommended order quantity
            # Formula: (30-day demand + safety buffer) - current stock
            # Safety buffer = minimum stock level (ensures we don't go below min)
            safety_buffer = min_stock
            
            # If forecast is very high or unavailable, use a conservative estimate
            if forecasted_demand_30d > max_stock * 2:
                # Forecast seems unreasonable - use conservative approach
                # Order enough to reach min_stock + some buffer
                target_stock = min_stock * 2  # Order 2x min_stock as conservative estimate
            else:
                # Use forecast + safety buffer
                target_stock = forecasted_demand_30d + safety_buffer
            
            # Calculate recommended order: target_stock - current_stock
            # But don't exceed max_stock (unless we're below min_stock, then order at least min_stock)
            if current_stock < min_stock:
                # Below min stock - order at least enough to reach min_stock
                min_order = min_stock - current_stock
                recommended_order = max(min_order, min(target_stock - current_stock, max_stock - current_stock))
            else:
                # Above min stock - order based on forecast, but cap at max_stock
                recommended_order = max(0, min(target_stock - current_stock, max_stock - current_stock))
            
            # Round to reasonable values (no decimal places for most items)
            recommended_order = round(recommended_order, 0)
            
            # Only include items that need reordering
            if recommended_order <= 0:
                continue
            
            # Get lead time from shipment frequency
            lead_time = 7  # Default
            if not shipments.empty and 'ingredient' in shipments.columns:
                ingredient_shipments = shipments[shipments['ingredient'] == ingredient]
                if not ingredient_shipments.empty:
                    # Get frequency and estimate lead time
                    freq_col = None
                    for col in shipments.columns:
                        if 'frequency' in str(col).lower():
                            freq_col = col
                            break
                    
                    if freq_col:
                        frequency = str(ingredient_shipments.iloc[0].get(freq_col, 'weekly')).lower()
                        if 'weekly' in frequency:
                            lead_time = 7
                        elif 'biweekly' in frequency or 'bi-weekly' in frequency:
                            lead_time = 14
                        elif 'monthly' in frequency:
                            lead_time = 30
                        else:
                            lead_time = 7
            
            # Determine urgency based on days until stockout and current stock level
            # Consider both stock level and time until stockout
            if current_stock <= 0:
                urgency = 'Critical'  # Out of stock
            elif current_stock < min_stock:
                # Below minimum stock - urgency based on days until stockout
                if days_until_stockout <= 0:
                    urgency = 'Critical'
                elif days_until_stockout < 3:
                    urgency = 'Critical'
                elif days_until_stockout < 7:
                    urgency = 'High'
                elif days_until_stockout < 14:
                    urgency = 'Medium'
                else:
                    urgency = 'Low'
            else:
                # Above min stock but will run out - lower urgency
                if days_until_stockout < 7:
                    urgency = 'High'
                elif days_until_stockout < 14:
                    urgency = 'Medium'
                else:
                    urgency = 'Low'
            
            # Calculate recommended reorder date (order before we run out, accounting for lead time)
            if days_until_stockout > 0:
                reorder_days_ahead = max(0, days_until_stockout - lead_time - 2)  # Add 2 day buffer
            else:
                reorder_days_ahead = 0  # Order immediately if already out of stock
            
            reorder_date = current_date + timedelta(days=reorder_days_ahead)
            
            # Simple data quality indicator (not a filter)
            # Based on whether we have good usage data
            if has_forecast_data:
                usage_data_quality = 'Good'
            elif found_usage_data:
                usage_data_quality = 'Good'
            else:
                usage_data_quality = 'Limited'
            
            recommendations.append({
                'ingredient': ingredient,
                'current_stock': round(current_stock, 2),
                'min_stock_level': round(min_stock, 2),
                'days_until_stockout': round(days_until_stockout, 1),
                'forecasted_demand_30d': int(forecasted_demand_30d),  # Floor to whole numbers
                'recommended_order_quantity': recommended_order,
                'urgency': urgency,
                'estimated_lead_time_days': lead_time,
                'reorder_date': reorder_date,
                'data_quality': usage_data_quality
            })
        
        if not recommendations:
            return pd.DataFrame()
        
        df = pd.DataFrame(recommendations)
        # Sort by urgency (Critical first) and days until stockout
        urgency_order = {'Critical': 0, 'High': 1, 'Medium': 2, 'Low': 3}
        df['urgency_order'] = df['urgency'].map(urgency_order)
        df = df.sort_values(['urgency_order', 'days_until_stockout'], ascending=[True, True])
        df = df.drop(columns=['urgency_order'])
        
        return df
    
    # ========== NEW FEATURES ==========
    
    def calculate_risk_alerts(self, current_date: Optional[datetime] = None) -> pd.DataFrame:
        """Calculate real-time inventory risk alerts based on usage velocity"""
        if current_date is None:
            current_date = datetime.now()
        
        inventory = self.calculate_inventory_levels(current_date)
        if inventory.empty:
            return pd.DataFrame()
        
        usage = self.data.get('usage', pd.DataFrame())
        if usage.empty:
            return inventory
        
        risk_alerts = []
        
        for _, row in inventory.iterrows():
            ingredient = row['ingredient']
            current_stock = row['current_stock']
            min_stock = row['min_stock_level']
            max_stock = row['max_stock_level']
            
            # Calculate usage velocity (daily consumption rate)
            ingredient_usage = usage[usage['ingredient'] == ingredient].copy()
            if not ingredient_usage.empty:
                # Last 7 days velocity
                recent_date = current_date - timedelta(days=7)
                recent_usage = ingredient_usage[ingredient_usage['date'] >= recent_date]
                if not recent_usage.empty:
                    days_span = (recent_usage['date'].max() - recent_usage['date'].min()).days + 1
                    total_usage_7d = recent_usage['quantity_used'].sum()
                    velocity_7d = total_usage_7d / max(days_span, 1)
                    
                    # Last 30 days velocity for comparison
                    recent_30d_date = current_date - timedelta(days=30)
                    recent_30d_usage = ingredient_usage[ingredient_usage['date'] >= recent_30d_date]
                    if not recent_30d_usage.empty:
                        days_span_30d = (recent_30d_usage['date'].max() - recent_30d_usage['date'].min()).days + 1
                        total_usage_30d = recent_30d_usage['quantity_used'].sum()
                        velocity_30d = total_usage_30d / max(days_span_30d, 1)
                    else:
                        velocity_30d = velocity_7d
                else:
                    velocity_7d = 0
                    velocity_30d = 0
            else:
                velocity_7d = 0
                velocity_30d = 0
            
            # Calculate days until stockout based on velocity
            if velocity_7d > 0:
                days_until_stockout_velocity = current_stock / velocity_7d
            else:
                days_until_stockout_velocity = 999
            
            # Risk assessment
            risk_score = 0
            risk_type = 'Normal'
            
            # Shortage risk
            if current_stock < min_stock:
                risk_score += 50
                risk_type = 'Shortage Risk'
            elif days_until_stockout_velocity < 7:
                risk_score += 40
                risk_type = 'Critical Shortage Risk'
            elif days_until_stockout_velocity < 14:
                risk_score += 25
                risk_type = 'High Shortage Risk'
            elif days_until_stockout_velocity < 30:
                risk_score += 10
                risk_type = 'Moderate Shortage Risk'
            
            # Overstock risk
            if current_stock > max_stock * 1.2:
                risk_score += 30
                if risk_type == 'Normal':
                    risk_type = 'Overstock Risk'
                else:
                    risk_type = f'{risk_type} / Overstock'
            elif current_stock > max_stock:
                risk_score += 15
                if risk_type == 'Normal':
                    risk_type = 'Moderate Overstock'
            
            # Velocity spike detection
            if velocity_30d > 0 and velocity_7d > velocity_30d * 1.5:
                risk_score += 20
                if 'Velocity Spike' not in risk_type:
                    risk_type = f'{risk_type} (Velocity Spike)' if risk_type != 'Normal' else 'Velocity Spike'
            
            risk_score = min(100, risk_score)
            
            risk_alerts.append({
                'ingredient': ingredient,
                'current_stock': current_stock,
                'min_stock_level': min_stock,
                'max_stock_level': max_stock,
                'usage_velocity_7d': round(velocity_7d, 2),
                'usage_velocity_30d': round(velocity_30d, 2),
                'days_until_stockout': round(days_until_stockout_velocity, 1),
                'risk_score': risk_score,
                'risk_type': risk_type,
                'needs_reorder': days_until_stockout_velocity < 14 or current_stock < min_stock
            })
        
        risk_df = pd.DataFrame(risk_alerts)
        return risk_df.sort_values('risk_score', ascending=False)
    
    def track_shelf_life(self, current_date: Optional[datetime] = None) -> pd.DataFrame:
        """Track ingredient shelf life and expiration dates"""
        if current_date is None:
            current_date = datetime.now()
        
        purchases = self.data.get('purchases', pd.DataFrame())
        ingredients = self.data.get('ingredients', pd.DataFrame())
        usage = self.data.get('usage', pd.DataFrame())
        
        if purchases.empty or ingredients.empty:
            return pd.DataFrame()
        
        # Get shelf life data
        if 'shelf_life_days' not in ingredients.columns:
            ingredients['shelf_life_days'] = 14  # Default
        
        # Merge purchases with ingredient shelf life
        purchases_with_shelf = purchases.merge(
            ingredients[['ingredient', 'shelf_life_days']],
            on='ingredient',
            how='left'
        )
        purchases_with_shelf['shelf_life_days'] = purchases_with_shelf['shelf_life_days'].fillna(14)
        
        # Calculate expiration dates
        purchases_with_shelf['expiration_date'] = purchases_with_shelf['date'] + pd.to_timedelta(
            purchases_with_shelf['shelf_life_days'], unit='D'
        )
        
        # Track remaining quantity per purchase (simplified - assume FIFO)
        shelf_life_tracking = []
        for ingredient in purchases_with_shelf['ingredient'].unique():
            ing_purchases = purchases_with_shelf[purchases_with_shelf['ingredient'] == ingredient].sort_values('date')
            ing_usage = usage[usage['ingredient'] == ingredient].copy() if not usage.empty else pd.DataFrame()
            
            remaining_qty = 0
            for _, purchase in ing_purchases.iterrows():
                purchase_qty = purchase['quantity']
                purchase_date = purchase['date']
                expiration_date = purchase['expiration_date']
                shelf_life = purchase['shelf_life_days']
                
                # Calculate usage since purchase
                if not ing_usage.empty:
                    usage_since_purchase = ing_usage[
                        (ing_usage['date'] >= purchase_date) & 
                        (ing_usage['date'] < current_date)
                    ]['quantity_used'].sum()
                    remaining_qty += max(0, purchase_qty - usage_since_purchase)
                else:
                    remaining_qty += purchase_qty
                
                # Days until expiration
                days_until_expiration = (expiration_date - current_date).days
                
                if remaining_qty > 0 and days_until_expiration >= 0:
                    expiration_status = 'Good'
                    if days_until_expiration <= 7:
                        expiration_status = 'Expiring Soon (7 days)'
                    elif days_until_expiration <= 14:
                        expiration_status = 'Expiring Soon (14 days)'
                    elif days_until_expiration <= 30:
                        expiration_status = 'Expiring Soon (30 days)'
                    
                    shelf_life_tracking.append({
                        'ingredient': ingredient,
                        'purchase_date': purchase_date,
                        'expiration_date': expiration_date,
                        'remaining_quantity': remaining_qty,
                        'days_until_expiration': days_until_expiration,
                        'expiration_status': expiration_status,
                        'shelf_life_days': shelf_life
                    })
        
        if not shelf_life_tracking:
            return pd.DataFrame()
        
        shelf_life_df = pd.DataFrame(shelf_life_tracking)
        return shelf_life_df.sort_values('days_until_expiration')
    
    def get_expiring_ingredients(self, days_ahead: int = 7, current_date: Optional[datetime] = None) -> pd.DataFrame:
        """Get ingredients expiring within specified days"""
        shelf_life = self.track_shelf_life(current_date)
        if shelf_life.empty:
            return pd.DataFrame()
        
        expiring = shelf_life[
            (shelf_life['days_until_expiration'] >= 0) & 
            (shelf_life['days_until_expiration'] <= days_ahead)
        ].copy()
        
        return expiring.sort_values('days_until_expiration')
    
    def get_use_it_now_recipes(self, expiring_ingredients: List[str]) -> pd.DataFrame:
        """Get recipe suggestions for expiring ingredients"""
        usage = self.data.get('usage', pd.DataFrame())
        sales = self.data.get('sales', pd.DataFrame())
        
        if usage.empty or 'menu_item' not in usage.columns:
            return pd.DataFrame()
        
        # Find menu items that use expiring ingredients
        recipes = usage[usage['ingredient'].isin(expiring_ingredients)].copy()
        if recipes.empty:
            return pd.DataFrame()
        
        # Get menu items and their usage of expiring ingredients
        recipe_suggestions = recipes.groupby('menu_item').agg({
            'ingredient': lambda x: ', '.join(x.unique()),
            'quantity_used': 'sum'
        }).reset_index()
        recipe_suggestions.columns = ['menu_item', 'expiring_ingredients', 'total_usage']
        
        # Add popularity from sales if available
        if not sales.empty and 'menu_item' in sales.columns:
            recent_sales = sales[sales['date'] >= datetime.now() - timedelta(days=30)]
            menu_popularity = recent_sales.groupby('menu_item')['quantity_sold'].sum().reset_index()
            menu_popularity.columns = ['menu_item', 'sales_count']
            recipe_suggestions = recipe_suggestions.merge(menu_popularity, on='menu_item', how='left')
            recipe_suggestions['sales_count'] = recipe_suggestions['sales_count'].fillna(0)
            recipe_suggestions = recipe_suggestions.sort_values('sales_count', ascending=False)
        else:
            recipe_suggestions['sales_count'] = 0
        
        return recipe_suggestions
    
    def _calculate_ingredient_per_serving(self, ingredient: str, menu_items: List[str] = None) -> Dict[str, Tuple[float, str]]:
        """
        Calculate ingredient usage per serving for each menu item.
        Returns a dictionary mapping menu_item -> (usage_per_serving, unit)
        """
        usage = self.data.get('usage', pd.DataFrame())
        sales = self.data.get('sales', pd.DataFrame())
        
        if usage.empty or 'menu_item' not in usage.columns:
            return {}
        
        # Filter for the specific ingredient and menu items
        filtered_usage = usage[usage['ingredient'] == ingredient].copy()
        if menu_items:
            filtered_usage = filtered_usage[filtered_usage['menu_item'].isin(menu_items)]
        
        if filtered_usage.empty:
            return {}
        
        # Helper function to check if ingredient is count-based
        def is_count_based_ingredient(ingredient_name, unit=None):
            """Check if ingredient is count-based (pieces, rolls, eggs, ramen, noodles) vs weight-based"""
            ingredient_lower = str(ingredient_name).lower()
            unit_lower = str(unit).lower() if unit and pd.notna(unit) else ""
            count_keywords = ['wing', 'ramen', 'egg', 'count', 'pcs', 'piece', 'roll', 'whole', 'noodle']
            if any(keyword in unit_lower for keyword in count_keywords):
                return True
            if any(keyword in ingredient_lower for keyword in ['wing', 'ramen', 'egg', 'noodle']):
                return True
            return False
        
        # Method 1: Try to get from recipe matrix directly (most accurate)
        recipe_per_serving = {}
        ingredient_unit_from_recipe = None
        try:
            from pathlib import Path
            recipe_file = Path("data") / "MSY Data - Ingredient.csv"
            if recipe_file.exists():
                recipe_matrix = pd.read_csv(recipe_file)
                if not recipe_matrix.empty and 'Item name' in recipe_matrix.columns:
                    menu_item_col = 'Item name'
                    ingredient_cols = [col for col in recipe_matrix.columns if col != menu_item_col]
                    
                    # Find the ingredient column (normalize names for matching)
                    def normalize_name(name):
                        if pd.isna(name):
                            return ""
                        # Remove units and descriptors for matching
                        name = str(name).strip().lower()
                        # Remove units: (g), (count), (pcs), etc.
                        name = name.replace(' (g)', '').replace('(g)', '')
                        name = name.replace(' (count)', '').replace('(count)', '')
                        name = name.replace(' (pcs)', '').replace('(pcs)', '')
                        name = name.replace(' used', '')
                        name = name.replace(' ', '')  # Remove spaces for better matching
                        return name
                    
                    ingredient_norm = normalize_name(ingredient)
                    matching_col = None
                    # Try to find best match: exact match first, then partial match
                    best_match_score = 0
                    for col in ingredient_cols:
                        col_norm = normalize_name(col)
                        # Exact match (highest priority) - after normalization
                        if col_norm == ingredient_norm:
                            matching_col = col
                            break
                        # Check if ingredient name is contained in column name (or vice versa)
                        # This handles "Ramen" matching "Ramen (count)"
                        if ingredient_norm in col_norm or col_norm in ingredient_norm:
                            # Prefer exact matches and shorter column names (more specific)
                            match_score = 1.0 / (len(col_norm) + 1)
                            if match_score > best_match_score:
                                best_match_score = match_score
                                matching_col = col
                    # If no exact match found, use the best partial match
                    if not matching_col and best_match_score > 0:
                        # matching_col already set in the loop above
                        pass
                    
                    if matching_col:
                        # Extract unit from column name if present
                        original_col = matching_col
                        unit = 'units'  # Default
                        if '(g)' in original_col or ' (g)' in original_col:
                            unit = 'g'
                        elif '(count)' in original_col or ' (count)' in original_col:
                            unit = 'count'
                        elif '(lb)' in original_col or ' (lb)' in original_col:
                            unit = 'lb'
                        elif '(oz)' in original_col or ' (oz)' in original_col:
                            unit = 'oz'
                        
                        # Check if this is a count-based ingredient FIRST
                        # For count-based ingredients, override unit detection (e.g., Ramen should be count, not g)
                        is_count_based = is_count_based_ingredient(ingredient, unit)
                        if is_count_based:
                            # Override unit to 'count' for count-based ingredients, regardless of column name
                            unit = 'count'
                            ingredient_unit_from_recipe = unit
                        else:
                            ingredient_unit_from_recipe = unit
                        
                        # Get values for each menu item (each dish can have different amounts)
                        for _, row in recipe_matrix.iterrows():
                            menu_item = str(row[menu_item_col]).strip()
                            qty = pd.to_numeric(row[matching_col], errors='coerce')
                            if pd.notna(qty) and qty > 0:
                                # Round to whole number if count-based
                                if is_count_based:
                                    qty = round(qty)
                                recipe_per_serving[menu_item] = (qty, unit)
        except Exception:
            pass
        
        # Method 2: Calculate from usage and sales data (divide total usage by quantity sold)
        per_serving_dict = {}
        
        if not sales.empty and 'quantity_sold' in sales.columns:
            try:
                # Merge usage with sales to get quantity_sold
                usage_with_sales = filtered_usage.merge(
                    sales[['date', 'menu_item', 'quantity_sold']],
                    on=['date', 'menu_item'],
                    how='left'
                )
                
                # Filter valid rows
                usage_with_sales = usage_with_sales[
                    (usage_with_sales['quantity_sold'].notna()) & 
                    (usage_with_sales['quantity_sold'] > 0) &
                    (usage_with_sales['quantity_used'] > 0)
                ].copy()
                
                if not usage_with_sales.empty:
                    # Calculate per-serving: quantity_used / quantity_sold
                    # Note: usage data is typically in grams, so we need to convert to count for count-based items
                    usage_with_sales['per_serving'] = (
                        usage_with_sales['quantity_used'] / usage_with_sales['quantity_sold']
                    )
                    
                    # Filter reasonable values
                    usage_with_sales = usage_with_sales[
                        (usage_with_sales['per_serving'] > 0.001) & 
                        (usage_with_sales['per_serving'] < 10000)
                    ]
                    
                    if not usage_with_sales.empty:
                        # Get average per serving per menu item
                        per_serving_avg = usage_with_sales.groupby('menu_item')['per_serving'].mean().to_dict()
                        # Use unit from recipe if available, otherwise infer from ingredient name
                        unit = ingredient_unit_from_recipe if ingredient_unit_from_recipe else 'units'
                        
                        # Check if this is a count-based ingredient
                        # For count-based ingredients, override unit to 'count' regardless of what was detected
                        is_count_based = is_count_based_ingredient(ingredient, unit)
                        if is_count_based:
                            unit = 'count'  # Override to 'count' for count-based items
                            # Convert from grams to count (usage data is in grams)
                            estimated_weight_per_unit = 50  # Default
                            ingredient_lower = str(ingredient).lower()
                            if 'ramen' in ingredient_lower:
                                estimated_weight_per_unit = 100  # Ramen ~100g per pack
                            elif 'egg' in ingredient_lower:
                                estimated_weight_per_unit = 50  # Egg ~50g
                            elif 'wing' in ingredient_lower:
                                estimated_weight_per_unit = 30  # Wing ~30g per piece
                            elif 'noodle' in ingredient_lower:
                                estimated_weight_per_unit = 100  # Noodles ~100g per pack
                            
                            # Convert per_serving values from grams to count
                            for menu_item in per_serving_avg:
                                if per_serving_avg[menu_item] > 5:  # If > 5, likely in grams
                                    per_serving_avg[menu_item] = per_serving_avg[menu_item] / estimated_weight_per_unit
                        
                        for menu_item, qty in per_serving_avg.items():
                            # Round to whole number if count-based
                            if is_count_based:
                                qty = round(qty)
                            per_serving_dict[menu_item] = (qty, unit)
            except Exception:
                pass
        
        # ALWAYS prioritize recipe matrix values (Method 1) - they're the source of truth
        # Only use calculated values (Method 2) if recipe matrix doesn't have the menu item
        result = {}
        for menu_item in filtered_usage['menu_item'].unique():
            # Priority 1: Recipe matrix (most accurate)
            if menu_item in recipe_per_serving:
                result[menu_item] = recipe_per_serving[menu_item]
            # Priority 2: Calculated from usage/sales (fallback only)
            elif menu_item in per_serving_dict:
                result[menu_item] = per_serving_dict[menu_item]
        
        return result
    
    def forecast_by_menu_trends(self, ingredient: str, days_ahead: int = 30) -> pd.DataFrame:
        """
        Forecast ingredient demand based on menu item sales trends.
        
        How it works:
        1. Finds menu items that use this ingredient
        2. Forecasts sales for each menu item based on historical trends
        3. Calculates ingredient usage per serving for each menu item
        4. Forecasts total ingredient demand = sum(daily_sales × usage_per_serving) for all menu items
        """
        usage = self.data.get('usage', pd.DataFrame())
        sales = self.data.get('sales', pd.DataFrame())
        
        if usage.empty or sales.empty:
            return pd.DataFrame()
        
        # Check if menu_item column exists in usage
        if 'menu_item' not in usage.columns:
            return pd.DataFrame()
        
        # Get menu items that use this ingredient
        menu_items = usage[usage['ingredient'] == ingredient]['menu_item'].unique().tolist()
        if len(menu_items) == 0:
            return pd.DataFrame()
        
        # Forecast sales for each menu item
        menu_forecasts = []
        for menu_item in menu_items:
            menu_sales = sales[sales['menu_item'] == menu_item].copy()
            if menu_sales.empty:
                continue
            
            # Aggregate daily sales
            daily_sales = menu_sales.groupby('date').agg({
                'quantity_sold': 'sum'
            }).reset_index()
            daily_sales = daily_sales.sort_values('date')
            
            # Check if we have enough data points
            if len(daily_sales) < 2:
                continue
            
            # Calculate average sales per period (day/month)
            # Check if data is daily or monthly by looking at date differences
            if len(daily_sales) > 1:
                date_diff = (daily_sales['date'].max() - daily_sales['date'].min()).days
                # If we have <= 12 data points and they span > 60 days, likely monthly data
                if len(daily_sales) <= 12 and date_diff > 60:
                    avg_sales = daily_sales['quantity_sold'].mean()
                    avg_daily_sales = avg_sales / 30.0  # Scale monthly to daily average
                else:
                    # For daily data, use moving average of last 30 days (or all if less)
                    window = min(30, len(daily_sales))
                    avg_daily_sales = daily_sales['quantity_sold'].tail(window).mean()
            else:
                avg_daily_sales = daily_sales['quantity_sold'].mean() if not daily_sales.empty else 0
            
            menu_forecasts.append({
                'menu_item': menu_item,
                'daily_avg_sales': avg_daily_sales
            })
        
        if not menu_forecasts:
            return pd.DataFrame()
        
        # Calculate ingredient usage per serving for each menu item
        ingredient_usage_per_serving = self._calculate_ingredient_per_serving(ingredient, menu_items)
        
        # Check if ingredient is count-based
        if self.preprocessor:
            is_count_based = self.preprocessor.is_count_based_ingredient(ingredient)
        else:
            # Fallback check
            ingredient_lower = str(ingredient).lower()
            is_count_based = any(keyword in ingredient_lower for keyword in ['wing', 'ramen', 'egg', 'noodle'])
        
        # Calculate daily ingredient demand (sum across all menu items)
        # Formula: For each menu item: daily_sales × ingredient_usage_per_serving
        daily_ingredient_demand = 0
        original_units_from_recipe = []  # Track original units before override
        for forecast in menu_forecasts:
            menu_item = forecast['menu_item']
            daily_sales = forecast['daily_avg_sales']
            usage_data = ingredient_usage_per_serving.get(menu_item)
            if usage_data:
                usage_per_serving, unit = usage_data  # Extract value and unit from tuple
                original_units_from_recipe.append((usage_per_serving, unit))
            else:
                usage_per_serving = 0
                unit = None
            
            if usage_per_serving > 0:
                # Daily ingredient demand = daily sales × ingredient usage per serving
                daily_ingredient_demand += daily_sales * usage_per_serving
        
        if daily_ingredient_demand <= 0:
            return pd.DataFrame()
        
        # Convert to count if ingredient is count-based and value is in grams
        if is_count_based:
            # For count-based ingredients, usage_per_serving from recipe matrix is often in grams
            # We need to convert the total demand from grams to count
            # Estimate weight per unit for conversion
            estimated_weight_per_unit = 50  # Default: 50g per unit
            ingredient_lower = str(ingredient).lower()
            if 'ramen' in ingredient_lower:
                estimated_weight_per_unit = 100  # Ramen ~100g per pack
            elif 'egg' in ingredient_lower:
                estimated_weight_per_unit = 50  # Egg ~50g
            elif 'wing' in ingredient_lower:
                estimated_weight_per_unit = 30  # Wing ~30g per piece
            elif 'noodle' in ingredient_lower:
                estimated_weight_per_unit = 100  # Noodles ~100g per pack
            
            # For count-based ingredients, recipe matrix values are often in grams even if we override unit to 'count'
            # Check if usage_per_serving values suggest grams (values > 5 typically indicate grams for count-based items)
            # The recipe matrix often has count-based ingredients in grams (e.g., "Ramen (g)" = 909g means 909g, not 909 packs)
            # Count-based items typically use 1-2 units per serving, not 900+
            needs_conversion = False
            if original_units_from_recipe:
                # Check original values - if any value > 5, it's likely in grams (not count)
                for usage_value, usage_unit in original_units_from_recipe:
                    # If unit is 'g' or value is suspiciously large (> 5 for count-based items), convert
                    if usage_unit == 'g' or (usage_value > 5):
                        needs_conversion = True
                        break
            # For count-based ingredients, ALWAYS convert if value is suspiciously large
            # Reasonable count-based daily demand is typically < 1000 units
            # If we see values > 100, it's almost certainly in grams and needs conversion
            if daily_ingredient_demand > 100:
                needs_conversion = True
            
            # Convert from grams to count if needed
            if needs_conversion and estimated_weight_per_unit > 0:
                daily_ingredient_demand = daily_ingredient_demand / estimated_weight_per_unit
            
            # Round to whole number for count-based items
            daily_ingredient_demand = round(daily_ingredient_demand)
        
        # Generate forecast DataFrame with daily values
        last_date = sales['date'].max()
        forecast_dates = pd.date_range(
            start=last_date + timedelta(days=1),
            periods=days_ahead,
            freq='D'
        )
        
        # Each day has the same daily forecast (flat forecast based on average)
        forecast_df = pd.DataFrame({
            'date': forecast_dates,
            'forecasted_usage': daily_ingredient_demand,  # Daily amount (same for each day), in count for count-based items
            'confidence_low': max(0, round(daily_ingredient_demand * 0.8)) if is_count_based else daily_ingredient_demand * 0.8,
            'confidence_high': round(daily_ingredient_demand * 1.2) if is_count_based else daily_ingredient_demand * 1.2
        })
        
        return forecast_df
    
    def calculate_ingredient_impact_score(self) -> pd.DataFrame:
        """
        Calculate ingredient impact score per menu item.
        
        Impact score shows which menu items drive the most usage of each ingredient.
        Formula: Impact Score = Menu Popularity × Normalized Ingredient Usage
        
        Returns DataFrame with columns: menu_item, ingredient, usage_per_serving, popularity_score, impact_score
        """
        usage = self.data.get('usage', pd.DataFrame())
        sales = self.data.get('sales', pd.DataFrame())
        
        if usage.empty or sales.empty or 'menu_item' not in usage.columns:
            return pd.DataFrame()
        
        # Get sales popularity - use most recent 30 days of data available
        cutoff_date = datetime.now() - timedelta(days=30)
        recent_sales = sales[sales['date'] >= cutoff_date]
        
        # If no data in last 30 days, use most recent 30 days available
        if recent_sales.empty:
            max_date = sales['date'].max()
            if pd.notna(max_date):
                min_date = max_date - timedelta(days=30)
                recent_sales = sales[sales['date'] >= min_date]
        
        if recent_sales.empty:
            return pd.DataFrame()
        
        menu_popularity = recent_sales.groupby('menu_item')['quantity_sold'].sum().reset_index()
        menu_popularity.columns = ['menu_item', 'total_sales']
        
        if menu_popularity.empty or menu_popularity['total_sales'].max() == 0:
            return pd.DataFrame()
        
        max_sales = menu_popularity['total_sales'].max()
        menu_popularity['popularity_score'] = (menu_popularity['total_sales'] / max_sales * 100).round(2)
        
        # Get all unique ingredients
        all_ingredients = usage['ingredient'].unique()
        
        # Calculate impact score for each ingredient
        impact_scores = []
        for ingredient in all_ingredients:
            # Get menu items that use this ingredient
            menu_items = usage[usage['ingredient'] == ingredient]['menu_item'].unique().tolist()
            if not menu_items:
                continue
            
            # Calculate ingredient usage per serving for each menu item
            ingredient_usage_per_serving = self._calculate_ingredient_per_serving(ingredient, menu_items)
            
            if not ingredient_usage_per_serving:
                continue
            
            # Get max usage for normalization (extract values from tuples)
            usage_values = [val[0] for val in ingredient_usage_per_serving.values() if val]
            max_usage = max(usage_values) if usage_values else 1
            
            # Get unit (should be same for all menu items, use first one)
            unit = None
            if ingredient_usage_per_serving:
                first_value = next(iter(ingredient_usage_per_serving.values()))
                if first_value:
                    _, unit = first_value
            
            # Calculate impact score for each menu item
            for menu_item in menu_items:
                if menu_item not in menu_popularity['menu_item'].values:
                    continue
                
                popularity = menu_popularity[menu_popularity['menu_item'] == menu_item]['popularity_score'].iloc[0]
                usage_data = ingredient_usage_per_serving.get(menu_item)
                if usage_data:
                    usage_per_serving, usage_unit = usage_data
                    if not unit:
                        unit = usage_unit
                else:
                    usage_per_serving = 0
                
                if usage_per_serving <= 0:
                    continue
                
                # Impact score = popularity × normalized usage
                normalized_usage = (usage_per_serving / max_usage * 100) if max_usage > 0 else 0
                impact_score = (popularity * normalized_usage / 100).round(2)
                
                impact_scores.append({
                    'menu_item': menu_item,
                    'ingredient': ingredient,
                    'usage_per_serving': round(usage_per_serving, 2),  # Per serving, not total
                    'usage_unit': unit or 'units',  # Store unit for display
                    'popularity_score': popularity,
                    'impact_score': impact_score
                })
        
        if not impact_scores:
            return pd.DataFrame()
        
        impact_df = pd.DataFrame(impact_scores)
        return impact_df.sort_values('impact_score', ascending=False)
    
    def detect_seasonality(self, ingredient: str) -> Dict:
        """Detect seasonal patterns in ingredient usage"""
        usage = self.data.get('usage', pd.DataFrame())
        if usage.empty:
            return {}
        
        ingredient_usage = usage[usage['ingredient'] == ingredient].copy()
        if ingredient_usage.empty:
            return {}
        
        # Aggregate by month
        ingredient_usage['year'] = ingredient_usage['date'].dt.year
        ingredient_usage['month'] = ingredient_usage['date'].dt.month
        
        monthly_usage = ingredient_usage.groupby(['year', 'month']).agg({
            'quantity_used': 'sum'
        }).reset_index()
        
        # Calculate average usage per month
        monthly_avg = monthly_usage.groupby('month')['quantity_used'].mean().to_dict()
        overall_avg = monthly_usage['quantity_used'].mean()
        
        # Calculate seasonal factors
        seasonal_factors = {month: (avg / overall_avg) if overall_avg > 0 else 1.0 
                           for month, avg in monthly_avg.items()}
        
        # Detect peak and low seasons
        peak_month = max(seasonal_factors, key=seasonal_factors.get)
        low_month = min(seasonal_factors, key=seasonal_factors.get)
        
        return {
            'seasonal_factors': seasonal_factors,
            'peak_month': peak_month,
            'low_month': low_month,
            'peak_factor': seasonal_factors[peak_month],
            'low_factor': seasonal_factors[low_month],
            'has_seasonality': abs(seasonal_factors[peak_month] - seasonal_factors[low_month]) > 0.2
        }
    
    def adjust_forecast_for_events(self, ingredient: str, forecast: pd.DataFrame, 
                                   country: str = 'US') -> pd.DataFrame:
        """Adjust forecast for holidays and events"""
        if forecast.empty or 'date' not in forecast.columns:
            return forecast
        
        try:
            # Get US holidays
            years = forecast['date'].dt.year.unique().tolist()
            if not years:
                return forecast
            us_holidays = holidays.UnitedStates(years=years)
        except Exception as e:
            # If holidays fails, continue without holiday adjustments
            print(f"Warning: Could not load holidays: {str(e)}")
            us_holidays = {}
        
        # Get current month for seasonality
        current_month = datetime.now().month
        seasonality = self.detect_seasonality(ingredient)
        
        adjusted_forecast = forecast.copy()
        
        # Apply seasonal adjustments
        if seasonality.get('has_seasonality', False):
            seasonal_factors = seasonality.get('seasonal_factors', {})
            adjusted_forecast['month'] = adjusted_forecast['date'].dt.month
            adjusted_forecast['seasonal_factor'] = adjusted_forecast['month'].map(seasonal_factors).fillna(1.0)
            adjusted_forecast['forecasted_usage'] = adjusted_forecast['forecasted_usage'] * adjusted_forecast['seasonal_factor']
            adjusted_forecast['confidence_low'] = adjusted_forecast['confidence_low'] * adjusted_forecast['seasonal_factor']
            adjusted_forecast['confidence_high'] = adjusted_forecast['confidence_high'] * adjusted_forecast['seasonal_factor']
        
        # Apply holiday adjustments (increase demand by 20% on holidays)
        try:
            # Convert dates to date objects for holiday checking
            adjusted_forecast['date_only'] = adjusted_forecast['date'].dt.date
            adjusted_forecast['is_holiday'] = adjusted_forecast['date_only'].isin(us_holidays)
            holiday_factor = 1.2
            adjusted_forecast.loc[adjusted_forecast['is_holiday'], 'forecasted_usage'] *= holiday_factor
            adjusted_forecast.loc[adjusted_forecast['is_holiday'], 'confidence_high'] *= holiday_factor
            adjusted_forecast = adjusted_forecast.drop(columns=['date_only'], errors='ignore')
        except Exception as e:
            # If holiday checking fails, continue without holiday adjustments
            print(f"Warning: Could not apply holiday adjustments: {str(e)}")
        
        # Drop temporary columns
        adjusted_forecast = adjusted_forecast.drop(columns=['month', 'seasonal_factor', 'is_holiday'], errors='ignore')
        
        return adjusted_forecast
    
    def calculate_waste_analysis(self, period_days: int = 30) -> pd.DataFrame:
        """Calculate waste analysis - overstock that goes unused"""
        purchases = self.data.get('purchases', pd.DataFrame())
        usage = self.data.get('usage', pd.DataFrame())
        ingredients = self.data.get('ingredients', pd.DataFrame())
        
        if purchases.empty or usage.empty:
            return pd.DataFrame()
        
        cutoff_date = datetime.now() - timedelta(days=period_days)
        
        # Get purchases and usage in period
        recent_purchases = purchases[purchases['date'] >= cutoff_date].copy()
        recent_usage = usage[usage['date'] >= cutoff_date].copy()
        
        # Estimate missing costs for purchases
        if not recent_purchases.empty:
            recent_purchases = self._estimate_missing_costs(recent_purchases)
        
        # Unit conversion helper
        def convert_to_grams(quantity, ingredient_name, unit=None):
            """Convert quantity to grams based on ingredient and unit"""
            if pd.isna(quantity) or quantity <= 0:
                return 0
            
            ingredient_lower = str(ingredient_name).lower()
            unit_lower = str(unit).lower() if unit and pd.notna(unit) else ""
            
            # Conversion factors
            LBS_TO_G = 453.592
            OZ_TO_G = 28.3495
            KG_TO_G = 1000
            
            # Check unit first, then ingredient type
            if 'lb' in unit_lower or 'pound' in unit_lower:
                return quantity * LBS_TO_G
            elif 'oz' in unit_lower or 'ounce' in unit_lower:
                return quantity * OZ_TO_G
            elif 'kg' in unit_lower or 'kilogram' in unit_lower:
                return quantity * KG_TO_G
            elif 'g' in unit_lower or 'gram' in unit_lower:
                return quantity
            elif 'count' in unit_lower or 'pcs' in unit_lower or 'piece' in unit_lower or 'roll' in unit_lower or 'egg' in unit_lower:
                # For count-based items, assume they're already in the correct unit
                # Don't convert count/pieces to grams
                return quantity
            elif 'whole' in unit_lower or 'onion' in unit_lower:
                # For whole items like onions, estimate weight
                if 'onion' in ingredient_lower:
                    return quantity * 150  # Average onion ~150g
                return quantity * 100  # Default estimate
            
            # If no unit specified, infer from ingredient name
            if any(word in ingredient_lower for word in ['beef', 'chicken', 'pork', 'meat']):
                # Assume lbs if meat
                return quantity * LBS_TO_G
            elif any(word in ingredient_lower for word in ['rice', 'noodle', 'flour', 'starch']):
                # Assume lbs for dry goods
                return quantity * LBS_TO_G
            elif 'egg' in ingredient_lower:
                # Eggs are counted, not weighed
                return quantity
            elif 'onion' in ingredient_lower or 'cilantro' in ingredient_lower or 'green onion' in ingredient_lower:
                # Vegetables might be in lbs
                return quantity * LBS_TO_G
            elif 'wing' in ingredient_lower or 'ramen' in ingredient_lower:
                # Pieces/count items
                return quantity
            
            # Default: assume grams
            return quantity
        
        # Normalize ingredient names for matching
        if self.preprocessor:
            normalize_ingredient_name = lambda name: self.preprocessor.normalize_ingredient_name(name).lower()
        else:
            def normalize_ingredient_name(name):
                """Normalize ingredient name for matching"""
                if pd.isna(name):
                    return ""
                name = str(name).strip().lower()
                # Remove common units and descriptors
                for suffix in [' (g)', '(g)', ' used', ' used (g)', ' (kg)', '(kg)', ' (oz)', '(oz)', 
                              ' (count)', '(count)', ' (pcs)', '(pcs)', ' (lb)', '(lb)', ' braised', 'braised ']:
                    name = name.replace(suffix, '')
                # Remove extra whitespace
                name = ' '.join(name.split())
                return name
        
        def extract_base_ingredient(name):
            """Extract base ingredient name, handling compound names"""
            if pd.isna(name):
                return []
            name = str(name).strip().lower()
            # Remove units and descriptors
            for suffix in [' (g)', '(g)', ' used', ' used (g)', ' (kg)', '(kg)', ' (oz)', '(oz)', 
                          ' (count)', '(count)', ' (pcs)', '(pcs)', ' (lb)', '(lb)', ' braised', 'braised ']:
                name = name.replace(suffix, '')
            name = ' '.join(name.split())
            
            # Handle compound ingredients like "Peas + Carrot" or "Peas(g)" and "Carrot(g)"
            if '+' in name or ' and ' in name:
                parts = [p.strip() for p in name.replace(' and ', '+').split('+')]
                return [p for p in parts if p]
            return [name]
        
        # Get unit information from shipments if available
        shipments = self.data.get('shipments', pd.DataFrame())
        unit_map = {}
        if not shipments.empty and 'ingredient' in shipments.columns:
            if 'unit' in shipments.columns:
                for _, row in shipments.iterrows():
                    ingredient = row['ingredient']
                    unit = row.get('unit', '')
                    if ingredient and unit:
                        unit_map[ingredient] = str(unit).strip()
            elif 'Unit of shipment' in shipments.columns:
                for _, row in shipments.iterrows():
                    ingredient = row['ingredient']
                    unit = row.get('Unit of shipment', '')
                    if ingredient and unit:
                        unit_map[ingredient] = str(unit).strip()
        
        # Calculate total purchased and used per ingredient
        purchase_totals = recent_purchases.groupby('ingredient').agg({
            'quantity': 'sum',
            'total_cost': 'sum'
        }).reset_index()
        purchase_totals.columns = ['ingredient', 'total_purchased', 'total_cost']
        purchase_totals['ingredient_normalized'] = purchase_totals['ingredient'].apply(normalize_ingredient_name)
        purchase_totals['base_ingredients'] = purchase_totals['ingredient'].apply(extract_base_ingredient)
        
        # Determine if ingredient is count-based or weight-based, and convert purchases to grams
        def is_count_based(ingredient_name, unit=None):
            """Check if ingredient is count-based (pieces, rolls, eggs) vs weight-based"""
            ingredient_lower = str(ingredient_name).lower()
            unit_lower = str(unit).lower() if unit and pd.notna(unit) else ""
            
            count_keywords = ['wing', 'ramen', 'egg', 'count', 'pcs', 'piece', 'roll', 'whole']
            if any(keyword in unit_lower for keyword in count_keywords):
                return True
            if any(keyword in ingredient_lower for keyword in ['wing', 'ramen', 'egg']):
                return True
            return False
        
        # Convert purchase quantities to grams (for weight-based) or keep as-is (for count-based)
        purchase_totals['unit'] = purchase_totals['ingredient'].map(unit_map)
        purchase_totals['is_count_based'] = purchase_totals.apply(
            lambda row: is_count_based(row['ingredient'], row.get('unit', '')), axis=1
        )
        purchase_totals['total_purchased_grams'] = purchase_totals.apply(
            lambda row: row['total_purchased'] if row['is_count_based'] 
            else convert_to_grams(row['total_purchased'], row['ingredient'], row.get('unit', '')),
            axis=1
        )
        
        usage_totals = recent_usage.groupby('ingredient')['quantity_used'].sum().reset_index()
        usage_totals.columns = ['ingredient', 'total_used']
        usage_totals['ingredient_normalized'] = usage_totals['ingredient'].apply(normalize_ingredient_name)
        usage_totals['base_ingredients'] = usage_totals['ingredient'].apply(extract_base_ingredient)
        
        # Determine if usage ingredient is count-based
        usage_totals['is_count_based'] = usage_totals['ingredient'].apply(
            lambda x: is_count_based(x, None)
        )
        # Usage from recipes is already in grams for weight-based, count for count-based
        usage_totals['total_used_grams'] = usage_totals.apply(
            lambda row: row['total_used'] if row['is_count_based'] else row['total_used'],
            axis=1
        )
        
        # Create a mapping from normalized names and base ingredients to original purchase ingredient names
        purchase_map = {}
        purchase_base_map = {}  # Map base ingredients to purchase ingredients
        
        for _, row in purchase_totals.iterrows():
            norm_name = row['ingredient_normalized']
            purchase_ingredient = row['ingredient']
            
            # Add to normalized name map
            if norm_name not in purchase_map:
                purchase_map[norm_name] = []
            purchase_map[norm_name].append(purchase_ingredient)
            
            # Add to base ingredient map (for compound ingredients)
            for base_ing in row['base_ingredients']:
                if base_ing not in purchase_base_map:
                    purchase_base_map[base_ing] = []
                purchase_base_map[base_ing].append(purchase_ingredient)
        
        # Match usage ingredients to purchase ingredients - improved matching
        matched_usage = []
        for _, usage_row in usage_totals.iterrows():
            norm_usage = usage_row['ingredient_normalized']
            usage_base_ingredients = usage_row['base_ingredients']
            usage_ingredient_orig = usage_row['ingredient']
            matched_purchases = set()
            
            # Strategy 1: Try exact normalized match
            if norm_usage and norm_usage in purchase_map:
                for purchase_ingredient in purchase_map[norm_usage]:
                    matched_purchases.add(purchase_ingredient)
            
            # Strategy 2: Try partial match (one contains the other) - more aggressive
            if not matched_purchases and norm_usage:
                for norm_purchase, purchase_ingredients in purchase_map.items():
                    if norm_purchase:
                        # Check if one contains the other (but not too short to avoid false matches)
                        if len(norm_usage) >= 2 and len(norm_purchase) >= 2:
                            if norm_usage in norm_purchase or norm_purchase in norm_usage:
                                for purchase_ingredient in purchase_ingredients:
                                    matched_purchases.add(purchase_ingredient)
            
            # Strategy 3: Match by base ingredients (for compound ingredients like Peas + Carrot)
            if not matched_purchases:
                for base_ing in usage_base_ingredients:
                    if base_ing and base_ing in purchase_base_map:
                        for purchase_ingredient in purchase_base_map[base_ing]:
                            matched_purchases.add(purchase_ingredient)
            
            # Strategy 4: Try word-by-word matching
            if not matched_purchases and norm_usage:
                usage_words = set(norm_usage.split())
                for norm_purchase, purchase_ingredients in purchase_map.items():
                    if norm_purchase:
                        purchase_words = set(norm_purchase.split())
                        # If there's word overlap, consider it a match
                        if usage_words and purchase_words:
                            overlap = len(usage_words & purchase_words)
                            # Match if at least one significant word overlaps
                            if overlap > 0:
                                for purchase_ingredient in purchase_ingredients:
                                    matched_purchases.add(purchase_ingredient)
            
            # Strategy 5: Direct ingredient name matching (fallback)
            if not matched_purchases:
                usage_lower = str(usage_ingredient_orig).lower()
                for purchase_ingredient in purchase_totals['ingredient'].unique():
                    purchase_lower = str(purchase_ingredient).lower()
                    # Remove units and check if core names match
                    for suffix in [' (g)', '(g)', ' used', ' used (g)', ' (pcs)', '(pcs)', ' (count)', '(count)']:
                        usage_lower_clean = usage_lower.replace(suffix, '')
                        purchase_lower_clean = purchase_lower.replace(suffix, '')
                        if usage_lower_clean in purchase_lower_clean or purchase_lower_clean in usage_lower_clean:
                            if len(usage_lower_clean) >= 3 and len(purchase_lower_clean) >= 3:
                                matched_purchases.add(purchase_ingredient)
                                break
            
            # Add all matched purchases with proper unit handling
            for purchase_ingredient in matched_purchases:
                purchase_row = purchase_totals[purchase_totals['ingredient'] == purchase_ingredient]
                if not purchase_row.empty:
                    purchase_is_count = purchase_row.iloc[0]['is_count_based']
                    usage_is_count = usage_row['is_count_based']
                    
                    # Determine the usage value to use
                    if purchase_is_count and usage_is_count:
                        # Both count-based: use original units (pieces/rolls/eggs)
                        usage_value = usage_row['total_used']
                    elif not purchase_is_count and not usage_is_count:
                        # Both weight-based: use grams
                        usage_value = usage_row['total_used']  # Already in grams from recipe
                    else:
                        # Mixed: if purchase is weight-based, convert usage to grams (already is)
                        # If purchase is count-based but usage is weight-based, skip (shouldn't happen)
                        usage_value = usage_row['total_used'] if purchase_is_count else usage_row['total_used']
                    
                    matched_usage.append({
                        'purchase_ingredient': purchase_ingredient,
                        'usage_ingredient': usage_ingredient_orig,
                        'total_used': usage_value,
                        'total_used_grams': usage_value if not purchase_is_count else usage_value
                    })
        
        # Aggregate usage by purchase ingredient - use appropriate units
        if matched_usage:
            matched_df = pd.DataFrame(matched_usage)
            # Group by purchase ingredient and sum usage
            usage_by_purchase = matched_df.groupby('purchase_ingredient').agg({
                'total_used': 'sum',
                'total_used_grams': 'sum'
            }).reset_index()
            usage_by_purchase.columns = ['ingredient', 'total_used_original', 'total_used_grams']
        else:
            usage_by_purchase = pd.DataFrame(columns=['ingredient', 'total_used_original', 'total_used_grams'])
        
        # Merge purchases with matched usage
        waste_analysis = purchase_totals[['ingredient', 'total_purchased', 'total_purchased_grams', 'total_cost', 'is_count_based', 'unit']].merge(
            usage_by_purchase, on='ingredient', how='left'
        ).fillna(0)
        
        # Ensure numeric types
        waste_analysis['total_purchased'] = pd.to_numeric(waste_analysis['total_purchased'], errors='coerce').fillna(0)
        waste_analysis['total_purchased_grams'] = pd.to_numeric(waste_analysis['total_purchased_grams'], errors='coerce').fillna(0)
        waste_analysis['total_used_original'] = pd.to_numeric(waste_analysis['total_used_original'], errors='coerce').fillna(0)
        waste_analysis['total_used_grams'] = pd.to_numeric(waste_analysis['total_used_grams'], errors='coerce').fillna(0)
        waste_analysis['total_cost'] = pd.to_numeric(waste_analysis['total_cost'], errors='coerce').fillna(0)
        
        # Set total_used based on whether item is count-based or weight-based
        # For display: show in original purchase units
        waste_analysis['total_used'] = waste_analysis.apply(
            lambda row: row['total_used_original'] if row['is_count_based'] else row['total_used_grams'],
            axis=1
        )
        
        # Calculate waste in the same units as purchases (for display)
        # Count-based: waste in pieces/rolls/eggs
        # Weight-based: waste in grams (but we'll convert back to original units for display if needed)
        waste_analysis['waste'] = waste_analysis.apply(
            lambda row: max(0, row['total_purchased'] - row['total_used_original']) if row['is_count_based']
            else max(0, row['total_purchased_grams'] - row['total_used_grams']),
            axis=1
        )
        
        # For weight-based items, convert waste back to original purchase units for display
        # But keep grams for calculations
        def convert_grams_to_original(grams, ingredient_name, unit):
            """Convert grams back to original purchase unit"""
            if pd.isna(grams) or grams <= 0:
                return 0
            LBS_TO_G = 453.592
            unit_lower = str(unit).lower() if unit and pd.notna(unit) else ""
            if 'lb' in unit_lower or 'pound' in unit_lower:
                return grams / LBS_TO_G
            return grams  # Keep in grams if unit unknown
        
        waste_analysis['waste_display'] = waste_analysis.apply(
            lambda row: row['waste'] if row['is_count_based']
            else convert_grams_to_original(row['waste'], row['ingredient'], row.get('unit', '')),
            axis=1
        )
        
        # Calculate waste percentage using display units
        waste_analysis['waste_percentage'] = waste_analysis.apply(
            lambda row: (row['waste_display'] / row['total_purchased'] * 100) if row['total_purchased'] > 0
            else 0,
            axis=1
        ).round(2)
        waste_analysis['waste_percentage'] = waste_analysis['waste_percentage'].clip(lower=0, upper=100)
        
        # Calculate waste cost (proportional cost of wasted items)
        # Use display waste for cost calculation
        waste_analysis['waste_cost'] = waste_analysis.apply(
            lambda row: (row['waste_display'] / row['total_purchased'] * row['total_cost']) if row['total_purchased'] > 0 and row['waste_display'] > 0
            else 0,
            axis=1
        ).round(2)
        waste_analysis['waste_cost'] = waste_analysis['waste_cost'].clip(lower=0)
        
        # Use waste_display as the main waste column for output
        waste_analysis['waste'] = waste_analysis['waste_display']
        
        # Get max stock levels for context
        if not ingredients.empty and 'max_stock_level' in ingredients.columns:
            waste_analysis = waste_analysis.merge(
                ingredients[['ingredient', 'max_stock_level']],
                on='ingredient',
                how='left'
            )
            waste_analysis['max_stock_level'] = pd.to_numeric(waste_analysis['max_stock_level'], errors='coerce').fillna(200)
        else:
            waste_analysis['max_stock_level'] = 200
        
        # Filter out items with no purchases (can't calculate waste without purchases)
        waste_analysis = waste_analysis[waste_analysis['total_purchased'] > 0]
        
        return waste_analysis.sort_values('waste_cost', ascending=False)
    
    def get_cost_waste_heatmap_data(self, period_days: int = 30) -> pd.DataFrame:
        """Get data for cost vs waste heatmap"""
        waste_analysis = self.calculate_waste_analysis(period_days)
        if waste_analysis.empty:
            return pd.DataFrame()
        
        # Clean and ensure numeric columns
        heatmap_data = waste_analysis.copy()
        heatmap_data['total_cost'] = pd.to_numeric(heatmap_data['total_cost'], errors='coerce').fillna(0)
        heatmap_data['waste'] = pd.to_numeric(heatmap_data['waste'], errors='coerce').fillna(0)
        heatmap_data['waste_cost'] = pd.to_numeric(heatmap_data['waste_cost'], errors='coerce').fillna(0)
        
        # Only include items with purchases (total_cost > 0 or total_purchased > 0)
        # This ensures we show all items that were purchased, even if they have no waste
        heatmap_data = heatmap_data[heatmap_data['total_purchased'] > 0]
        
        if heatmap_data.empty:
            return pd.DataFrame()
        
        # Normalize cost and waste for heatmap
        max_cost = heatmap_data['total_cost'].max()
        max_waste = heatmap_data['waste'].max()
        
        if max_cost > 0:
            heatmap_data['cost_normalized'] = (heatmap_data['total_cost'] / max_cost * 100).round(2)
        else:
            heatmap_data['cost_normalized'] = 0
        
        if max_waste > 0:
            heatmap_data['waste_normalized'] = (heatmap_data['waste'] / max_waste * 100).round(2)
        else:
            heatmap_data['waste_normalized'] = 0
        
        # Calculate risk level based on normalized cost and waste
        heatmap_data['risk_level'] = heatmap_data.apply(
            lambda row: 'High Risk' if row['cost_normalized'] > 50 and row['waste_normalized'] > 50
            else 'Medium Risk' if row['cost_normalized'] > 30 or row['waste_normalized'] > 30
            else 'Low Risk',
            axis=1
        )
        
        return heatmap_data
    
    def estimate_storage_load(self, current_date: Optional[datetime] = None, 
                             days_ahead: int = 7) -> pd.DataFrame:
        """Estimate storage load for cold storage based on projected inventory"""
        if current_date is None:
            current_date = datetime.now()
        
        ingredients = self.data.get('ingredients', pd.DataFrame())
        purchases = self.data.get('purchases', pd.DataFrame())
        usage = self.data.get('usage', pd.DataFrame())
        
        if ingredients.empty:
            return pd.DataFrame()
        
        # Get storage type and space requirements
        if 'storage_type' not in ingredients.columns:
            return pd.DataFrame()
        
        if 'storage_space_units' not in ingredients.columns:
            ingredients['storage_space_units'] = 1.0  # Default
        
        # Calculate current inventory
        current_inventory = self.calculate_inventory_levels(current_date)
        if current_inventory.empty:
            return pd.DataFrame()
        
        # Merge current inventory with storage info
        current_storage_data = current_inventory.merge(
            ingredients[['ingredient', 'storage_type', 'storage_space_units']],
            on='ingredient',
            how='left'
        )
        
        # Project future inventory: current + expected purchases - expected usage
        future_date = current_date + timedelta(days=days_ahead)
        
        # Get expected purchases in the next days_ahead days
        expected_purchases = pd.DataFrame()
        if not purchases.empty and 'date' in purchases.columns:
            # First, try to get future purchases from existing purchase data
            future_purchases = purchases[
                (purchases['date'] > current_date) & 
                (purchases['date'] <= future_date)
            ].copy()
            
            if not future_purchases.empty:
                expected_purchases = future_purchases.groupby('ingredient')['quantity'].sum().reset_index()
                expected_purchases.columns = ['ingredient', 'expected_purchase_qty']
        else:
                # No future purchases in data - generate them based on shipment frequency
                shipments = self.data.get('shipments', pd.DataFrame())
                if not shipments.empty:
                    # Check for frequency column (could be 'frequency' or 'Frequency')
                    freq_col = None
                    for col in shipments.columns:
                        if 'frequency' in str(col).lower():
                            freq_col = col
                            break
                    
                    qty_col = None
                    for col in shipments.columns:
                        if 'quantity' in str(col).lower() or 'qty' in str(col).lower():
                            qty_col = col
                            break
                    
                    if freq_col and qty_col:
                        future_purchase_list = []
                        for _, row in shipments.iterrows():
                            ingredient = row.get('ingredient', '')
                            if pd.isna(ingredient) or not ingredient:
                                continue
                                
                            qty_per_shipment = pd.to_numeric(row.get(qty_col, 0), errors='coerce') or 0
                            frequency = str(row.get(freq_col, 'weekly')).lower()
                            
                            if qty_per_shipment <= 0:
                                continue
                            
                            # Calculate days between shipments
                            if 'weekly' in frequency:
                                days_between = 7
                            elif 'biweekly' in frequency or 'bi-weekly' in frequency:
                                days_between = 14
                            elif 'monthly' in frequency:
                                days_between = 30
                            else:
                                days_between = 7  # Default to weekly
                            
                            # Generate purchase dates in the future
                            # Start from the next expected shipment date
                            purchase_date = current_date + timedelta(days=days_between)
                            purchase_count = 0
                            max_purchases = int(days_ahead / days_between) + 2  # Add buffer
                            
                            while purchase_date <= future_date and purchase_count < max_purchases:
                                future_purchase_list.append({
                                    'ingredient': str(ingredient).strip(),
                                    'quantity': qty_per_shipment
                                })
                                purchase_date += timedelta(days=days_between)
                                purchase_count += 1
                        
                        if future_purchase_list:
                            future_purchases_df = pd.DataFrame(future_purchase_list)
                            expected_purchases = future_purchases_df.groupby('ingredient')['quantity'].sum().reset_index()
                            expected_purchases.columns = ['ingredient', 'expected_purchase_qty']
        
        # Get expected usage in the next days_ahead days (based on historical average)
        expected_usage = pd.DataFrame()
        if not usage.empty and 'date' in usage.columns:
            # Calculate average daily usage for each ingredient
            historical_usage = usage[usage['date'] <= current_date].copy()
            if not historical_usage.empty:
                # Get last 30 days of usage for average
                cutoff = current_date - timedelta(days=30)
                recent_usage = historical_usage[historical_usage['date'] >= cutoff]
                
                if not recent_usage.empty:
                    # Normalize ingredient names for matching (same as waste analysis)
                    if self.preprocessor:
                        normalize_ingredient_name = lambda name: self.preprocessor.normalize_ingredient_name(name).lower()
                    else:
                        def normalize_ingredient_name(name):
                            if pd.isna(name):
                                return ""
                            name = str(name).strip().lower()
                            for suffix in [' (g)', '(g)', ' used', ' used (g)', ' (kg)', '(kg)', ' (oz)', '(oz)', 
                                          ' (count)', '(count)', ' (pcs)', '(pcs)', ' (lb)', '(lb)', ' braised', 'braised ']:
                                name = name.replace(suffix, '')
                            name = ' '.join(name.split())
                            return name
                    
                    # Calculate average daily usage by ingredient
                    usage_totals = recent_usage.groupby('ingredient')['quantity_used'].sum().reset_index()
                    usage_totals.columns = ['ingredient', 'total_usage']
                    usage_totals['ingredient_normalized'] = usage_totals['ingredient'].apply(normalize_ingredient_name)
                    
                    # Match usage ingredients to inventory ingredients
                    inventory_ingredients = current_inventory['ingredient'].unique()
                    inventory_normalized = {normalize_ingredient_name(ing): ing for ing in inventory_ingredients}
                    
                    matched_usage_list = []
                    # Calculate actual days in the recent usage period
                    if len(recent_usage) > 0:
                        date_range = (recent_usage['date'].max() - recent_usage['date'].min()).days + 1
                        days_in_period = max(1, date_range)
                    else:
                        days_in_period = 30  # Default to 30 days if no data
                    
                    for _, usage_row in usage_totals.iterrows():
                        norm_name = usage_row['ingredient_normalized']
                        total_usage = usage_row['total_usage']
                        avg_daily = total_usage / days_in_period if days_in_period > 0 else 0
                        
                        # Try to match to inventory ingredient
                        matched = False
                        if norm_name in inventory_normalized:
                            matched_usage_list.append({
                                'ingredient': inventory_normalized[norm_name],
                                'avg_daily_usage': avg_daily
                            })
                            matched = True
                        else:
                            # Try partial match
                            for inv_norm, inv_ing in inventory_normalized.items():
                                if norm_name and inv_norm:
                                    if (norm_name in inv_norm or inv_norm in norm_name) and len(norm_name) >= 3:
                                        matched_usage_list.append({
                                            'ingredient': inv_ing,
                                            'avg_daily_usage': avg_daily
                                        })
                                        matched = True
                                        break
                    
                    if matched_usage_list:
                        matched_usage_df = pd.DataFrame(matched_usage_list)
                        # Aggregate by ingredient (in case multiple usage ingredients match one inventory ingredient)
                        avg_daily_usage = matched_usage_df.groupby('ingredient')['avg_daily_usage'].sum().reset_index()
                        # Project usage for days_ahead
                        avg_daily_usage['expected_usage_qty'] = avg_daily_usage['avg_daily_usage'] * days_ahead
                        expected_usage = avg_daily_usage[['ingredient', 'expected_usage_qty']]
        
        # Calculate projected inventory for each ingredient
        projected_inventory = current_inventory[['ingredient', 'current_stock']].copy()
        projected_inventory.columns = ['ingredient', 'projected_stock']
        
        # Add expected purchases
        if not expected_purchases.empty:
            projected_inventory = projected_inventory.merge(
                expected_purchases, on='ingredient', how='left'
            ).fillna(0)
            projected_inventory['projected_stock'] = projected_inventory['projected_stock'] + projected_inventory['expected_purchase_qty']
        else:
            projected_inventory['expected_purchase_qty'] = 0
        
        # Subtract expected usage
        if not expected_usage.empty:
            projected_inventory = projected_inventory.merge(
                expected_usage, on='ingredient', how='left'
            ).fillna(0)
            projected_inventory['projected_stock'] = projected_inventory.apply(
                lambda row: max(0, row['projected_stock'] - row['expected_usage_qty']), axis=1
            )
        else:
            projected_inventory['expected_usage_qty'] = 0
        
        # Merge with storage info
        projected_storage_data = projected_inventory.merge(
            ingredients[['ingredient', 'storage_type', 'storage_space_units']],
            on='ingredient',
            how='left'
        )
        
        # Calculate storage load by type
        storage_load = []
        for storage_type in ['refrigerated', 'frozen', 'shelf']:
            # Current load
            current_stock = current_storage_data[current_storage_data['storage_type'] == storage_type]
            current_load = (current_stock['current_stock'] * current_stock['storage_space_units']).sum()
            
            # Projected load (after days_ahead)
            projected_stock = projected_storage_data[projected_storage_data['storage_type'] == storage_type]
            projected_load = (projected_stock['projected_stock'] * projected_stock['storage_space_units']).sum()
            
            # Incoming load (purchases in next days_ahead)
            incoming_load = 0
            if not expected_purchases.empty:
                incoming = expected_purchases.merge(
                    ingredients[['ingredient', 'storage_type', 'storage_space_units']],
                    on='ingredient',
                    how='left'
                )
                incoming_for_type = incoming[incoming['storage_type'] == storage_type]
                incoming_load = (incoming_for_type['expected_purchase_qty'] * incoming_for_type['storage_space_units']).sum()
            
            # Estimate capacity (assume 2x current max as capacity, or use a reasonable default)
            estimated_capacity = max(current_load * 2, 1000) if current_load > 0 else 1000
            
            # Total load is the projected load after days_ahead
            total_load = projected_load
            
            storage_load.append({
                'storage_type': storage_type,
                'current_load': round(current_load, 2),
                'incoming_load': round(incoming_load, 2),
                'total_load': round(total_load, 2),
                'estimated_capacity': round(estimated_capacity, 2),
                'utilization_percentage': round((total_load / estimated_capacity * 100) if estimated_capacity > 0 else 0, 2),
                'is_overloaded': total_load > estimated_capacity
            })
        
        return pd.DataFrame(storage_load)
    
    def track_supplier_reliability(self) -> pd.DataFrame:
        """Track supplier reliability scores"""
        shipments = self.data.get('shipments', pd.DataFrame())
        purchases = self.data.get('purchases', pd.DataFrame())
        
        if shipments.empty:
            return pd.DataFrame()
        
        if 'supplier' not in shipments.columns:
            return pd.DataFrame()
        
        # Calculate delay metrics
        if 'delay_days' not in shipments.columns:
            if 'expected_date' in shipments.columns and 'date' in shipments.columns:
                shipments['delay_days'] = (
                    pd.to_datetime(shipments['date']) - 
                    pd.to_datetime(shipments['expected_date'])
                ).dt.days
            else:
                shipments['delay_days'] = 0
        
        # Supplier analysis
        supplier_metrics = shipments.groupby('supplier').agg({
            'delay_days': ['mean', 'max', 'count'],
            'status': lambda x: (x == 'Delayed').sum()
        }).reset_index()
        
        supplier_metrics.columns = ['supplier', 'avg_delay', 'max_delay', 'total_shipments', 'delayed_count']
        supplier_metrics['delay_rate'] = (supplier_metrics['delayed_count'] / supplier_metrics['total_shipments'] * 100).round(2)
        supplier_metrics['on_time_rate'] = (100 - supplier_metrics['delay_rate']).round(2)
        
        # Calculate fulfillment accuracy (if we have purchase data)
        if not purchases.empty and 'supplier' in purchases.columns:
            # Match purchases to shipments (simplified - by ingredient and date proximity)
            purchase_totals = purchases.groupby(['supplier', 'ingredient'])['quantity'].sum().reset_index()
            shipment_totals = shipments.groupby(['supplier', 'ingredient'])['quantity'].sum().reset_index()
            
            fulfillment = purchase_totals.merge(
                shipment_totals,
                on=['supplier', 'ingredient'],
                how='left',
                suffixes=('_ordered', '_received')
            ).fillna(0)
            
            fulfillment['fulfillment_rate'] = (
                fulfillment['quantity_received'] / fulfillment['quantity_ordered'] * 100
            ).round(2)
            fulfillment['fulfillment_rate'] = fulfillment['fulfillment_rate'].clip(upper=100)
            
            supplier_fulfillment = fulfillment.groupby('supplier')['fulfillment_rate'].mean().reset_index()
            supplier_metrics = supplier_metrics.merge(supplier_fulfillment, on='supplier', how='left')
            supplier_metrics['fulfillment_rate'] = supplier_metrics['fulfillment_rate'].fillna(100)
        else:
            supplier_metrics['fulfillment_rate'] = 100
        
        # Calculate reliability score (0-100)
        supplier_metrics['reliability_score'] = (
            supplier_metrics['on_time_rate'] * 0.5 +
            supplier_metrics['fulfillment_rate'] * 0.5
        ).round(2)
        
        # Get spending per supplier
        if not purchases.empty and 'supplier' in purchases.columns:
            supplier_spending = purchases.groupby('supplier')['total_cost'].sum().reset_index()
            supplier_spending.columns = ['supplier', 'total_spending']
            supplier_metrics = supplier_metrics.merge(supplier_spending, on='supplier', how='left')
            supplier_metrics['total_spending'] = supplier_metrics['total_spending'].fillna(0)
        else:
            supplier_metrics['total_spending'] = 0
        
        return supplier_metrics.sort_values('reliability_score', ascending=False)
    
    def get_alternative_suppliers(self, ingredient: str, current_supplier: str = None) -> pd.DataFrame:
        """Get alternative suppliers for an ingredient based on reliability"""
        supplier_reliability = self.track_supplier_reliability()
        purchases = self.data.get('purchases', pd.DataFrame())
        
        if supplier_reliability.empty:
            return pd.DataFrame()
        
        # Get suppliers that supply this ingredient
        if not purchases.empty and 'supplier' in purchases.columns:
            ingredient_suppliers = purchases[purchases['ingredient'] == ingredient]['supplier'].unique()
            alternative_suppliers = supplier_reliability[
                supplier_reliability['supplier'].isin(ingredient_suppliers)
            ].copy()
            
            if current_supplier:
                alternative_suppliers = alternative_suppliers[
                    alternative_suppliers['supplier'] != current_supplier
                ]
            
            return alternative_suppliers.sort_values('reliability_score', ascending=False)
        
        return pd.DataFrame()
    
    def map_recipes_to_inventory(self, current_date: Optional[datetime] = None) -> pd.DataFrame:
        """Map menu items to ingredients and calculate servings possible"""
        if current_date is None:
            current_date = datetime.now()
        
        usage = self.data.get('usage', pd.DataFrame())
        inventory = self.calculate_inventory_levels(current_date)
        sales = self.data.get('sales', pd.DataFrame())
        
        if usage.empty or 'menu_item' not in usage.columns:
            return pd.DataFrame()
        
        # If inventory is empty, create a minimal inventory with zero stock for all ingredients
        # This allows us to still show which dishes cannot be made
        if inventory.empty:
            # Get unique ingredients from usage
            all_ingredients = usage['ingredient'].unique()
            inventory = pd.DataFrame({
                'ingredient': all_ingredients,
                'current_stock': 0,
                'total_purchased': 0,
                'total_used': 0,
                'min_stock_level': 20,
                'max_stock_level': 200
            })
        
        # Calculate ingredient per serving correctly
        # quantity_used in usage data is total usage (quantity_sold × recipe_amount)
        # We need to divide by quantity_sold to get per-serving amounts
        
        recipe_map = None
        
        # Method 1: Try to load recipe matrix directly FIRST (most reliable source of truth)
        try:
            from pathlib import Path
            recipe_file = Path("data") / "MSY Data - Ingredient.csv"
            if recipe_file.exists():
                recipe_matrix = pd.read_csv(recipe_file)
                if not recipe_matrix.empty and 'Item name' in recipe_matrix.columns:
                    # Convert recipe matrix to long format
                    recipe_list = []
                    menu_item_col = 'Item name'
                    ingredient_cols = [col for col in recipe_matrix.columns if col != menu_item_col]
                    
                    for _, row in recipe_matrix.iterrows():
                        menu_item = str(row[menu_item_col]).strip()
                        for ingredient in ingredient_cols:
                            qty = pd.to_numeric(row[ingredient], errors='coerce')
                            if pd.notna(qty) and qty > 0:
                                recipe_list.append({
                                    'menu_item': menu_item,
                                    'ingredient': str(ingredient).strip(),
                                    'avg_ingredient_per_serving': qty
                                })
                    
                    if recipe_list:
                        recipe_map = pd.DataFrame(recipe_list)
        except Exception as e:
            # If recipe matrix load fails, fall through to next method
            pass
        
        # Method 2: Use sales data to calculate per-serving (accurate if recipe matrix not available)
        if (recipe_map is None or recipe_map.empty) and not sales.empty and 'quantity_sold' in sales.columns and 'menu_item' in sales.columns:
            try:
                # Merge usage with sales on date and menu_item
                usage_with_sales = usage.merge(
                    sales[['date', 'menu_item', 'quantity_sold']],
                    on=['date', 'menu_item'],
                    how='left'
                )
                
                # Filter out rows where quantity_sold is missing or 0
                usage_with_sales = usage_with_sales[
                    (usage_with_sales['quantity_sold'].notna()) & 
                    (usage_with_sales['quantity_sold'] > 0)
                ].copy()
                
                if not usage_with_sales.empty:
                    # Calculate per-serving: divide total usage by quantity sold
                    usage_with_sales['per_serving'] = (
                        usage_with_sales['quantity_used'] / usage_with_sales['quantity_sold']
                    )
                    
                    # Filter out unreasonable values (too small or too large)
                    # Per-serving should be reasonable (e.g., between 0.001 and 10000)
                    usage_with_sales = usage_with_sales[
                        (usage_with_sales['per_serving'] > 0.001) & 
                        (usage_with_sales['per_serving'] < 10000)
                    ].copy()
                    
                    if not usage_with_sales.empty:
                        # Get average ingredient usage per menu item (per serving)
                        recipe_map = usage_with_sales.groupby(['menu_item', 'ingredient']).agg({
                            'per_serving': 'mean'
                        }).reset_index()
                        recipe_map.columns = ['menu_item', 'ingredient', 'avg_ingredient_per_serving']
                        
                        # Ensure all values are reasonable
                        recipe_map = recipe_map[
                            (recipe_map['avg_ingredient_per_serving'] > 0.001) & 
                            (recipe_map['avg_ingredient_per_serving'] < 10000)
                        ]
            except Exception as e:
                # If merge fails, fall through to next method
                pass
        
        # Method 3: Fallback - use minimum quantity_used per date+menu_item as proxy for per-serving
        # This assumes the minimum usage represents a single serving
        if recipe_map is None or recipe_map.empty:
            try:
                # Group by date and menu_item, take minimum as proxy for single serving
                usage_by_transaction = usage.groupby(['date', 'menu_item', 'ingredient']).agg({
                    'quantity_used': 'sum'
                }).reset_index()
                
                # For each menu_item+ingredient, use the minimum as proxy for per-serving
                # This works if there are some single-serving transactions
                recipe_map = usage_by_transaction.groupby(['menu_item', 'ingredient']).agg({
                    'quantity_used': lambda x: x.min() if len(x) > 0 else 0
                }).reset_index()
                recipe_map.columns = ['menu_item', 'ingredient', 'avg_ingredient_per_serving']
                
                # If minimum is still too high (likely multi-serving), try median divided by typical serving count
                # Estimate typical servings per transaction
                transaction_sizes = usage_by_transaction.groupby(['date', 'menu_item']).size()
                if not transaction_sizes.empty:
                    typical_servings = max(1, int(transaction_sizes.median()))
                    recipe_map['avg_ingredient_per_serving'] = (
                        recipe_map['avg_ingredient_per_serving'] / typical_servings
                    )
            except Exception as e:
                # Last resort: use mean divided by estimated serving count
                recipe_map = usage.groupby(['menu_item', 'ingredient']).agg({
                    'quantity_used': 'mean'
                }).reset_index()
                recipe_map.columns = ['menu_item', 'ingredient', 'avg_ingredient_per_serving']
                # Divide by estimated average servings (heuristic: assume 2-3 servings per transaction)
                recipe_map['avg_ingredient_per_serving'] = recipe_map['avg_ingredient_per_serving'] / 2.5
        
        if recipe_map is None or recipe_map.empty:
            return pd.DataFrame()
        
        # Create a comprehensive ingredient matching function
        if self.preprocessor:
            normalize_ingredient_name = lambda name: self.preprocessor.normalize_ingredient_name(name).lower()
        else:
            def normalize_ingredient_name(name):
                """Normalize ingredient name for matching"""
                if pd.isna(name):
                    return ""
                name = str(name).strip().lower()
                # Remove common units and descriptors
                for suffix in [' (g)', '(g)', ' used', ' used (g)', ' (kg)', '(kg)', ' (oz)', '(oz)', ' (count)', '(count)', ' (pcs)', '(pcs)']:
                    name = name.replace(suffix, '')
                # Remove extra whitespace
                name = ' '.join(name.split())
                return name
        
        # Create ingredient mapping dictionary for better matching
        recipe_map_normalized = recipe_map.copy()
        recipe_map_normalized['ingredient_normalized'] = recipe_map_normalized['ingredient'].apply(normalize_ingredient_name)
        
        inventory_normalized = inventory.copy()
        inventory_normalized['ingredient_normalized'] = inventory_normalized['ingredient'].apply(normalize_ingredient_name)
        
        # Create a mapping of recipe ingredient names to inventory ingredient names
        ingredient_mapping = {}
        for recipe_ing_norm in recipe_map_normalized['ingredient_normalized'].unique():
            if not recipe_ing_norm:  # Skip empty names
                continue
            
            # Get the original recipe ingredient name
            recipe_ing_original = recipe_map_normalized[recipe_map_normalized['ingredient_normalized'] == recipe_ing_norm]['ingredient'].iloc[0]
            
            # Strategy 1: Exact normalized match
            exact_match = inventory_normalized[inventory_normalized['ingredient_normalized'] == recipe_ing_norm]
            if not exact_match.empty:
                ingredient_mapping[recipe_ing_original] = exact_match['ingredient'].iloc[0]
                continue
            
            # Strategy 2: Partial match (one contains the other)
            best_match = None
            best_match_score = 0
            for inv_ing_norm in inventory_normalized['ingredient_normalized'].unique():
                if not inv_ing_norm:
                    continue
                # Check if one contains the other (but not too short to avoid false matches)
                if len(recipe_ing_norm) >= 3 and len(inv_ing_norm) >= 3:
                    if recipe_ing_norm in inv_ing_norm or inv_ing_norm in recipe_ing_norm:
                        # Prefer longer matches
                        match_score = min(len(recipe_ing_norm), len(inv_ing_norm))
                        if match_score > best_match_score:
                            best_match_score = match_score
                            best_match = inventory_normalized[inventory_normalized['ingredient_normalized'] == inv_ing_norm]['ingredient'].iloc[0]
            
            if best_match:
                ingredient_mapping[recipe_ing_original] = best_match
        
        # Update recipe_map with matched ingredient names
        if ingredient_mapping:
            recipe_map['ingredient'] = recipe_map['ingredient'].map(ingredient_mapping).fillna(recipe_map['ingredient'])
        
        # Calculate servings possible for each menu item
        menu_viability = []
        for menu_item in recipe_map['menu_item'].unique():
            menu_recipe = recipe_map[recipe_map['menu_item'] == menu_item]
            
            servings_possible = []
            missing_ingredients = []
            invalid_ingredients = []
            
            # Process each ingredient for this menu item
            for _, recipe_row in menu_recipe.iterrows():
                ingredient = str(recipe_row['ingredient']).strip()
                required_per_serving = recipe_row['avg_ingredient_per_serving']
                
                # Validate required_per_serving is reasonable (not too small or negative)
                if pd.isna(required_per_serving) or required_per_serving <= 0:
                    # Track invalid ingredients but don't skip the menu item
                    invalid_ingredients.append(ingredient)
                    continue
                
                # Get current stock - use normalized matching
                ingredient_normalized = normalize_ingredient_name(ingredient)
                
                # Try to find matching inventory ingredient
                stock_row = pd.DataFrame()
                
                # Strategy 1: Exact match (case-sensitive)
                stock_row = inventory[inventory['ingredient'].astype(str).str.strip() == str(ingredient).strip()]
                
                # Strategy 2: Case-insensitive exact match
                if stock_row.empty:
                    inventory_ingredients_normalized = inventory['ingredient'].apply(normalize_ingredient_name)
                    stock_row = inventory[inventory_ingredients_normalized == ingredient_normalized]
                
                # Strategy 3: Partial match (contains) - only if normalized name is meaningful
                if stock_row.empty and len(ingredient_normalized) >= 3:
                    inventory_ingredients_normalized = inventory['ingredient'].apply(normalize_ingredient_name)
                    for idx, inv_ing_norm in inventory_ingredients_normalized.items():
                        if len(inv_ing_norm) >= 3:
                            if ingredient_normalized in inv_ing_norm or inv_ing_norm in ingredient_normalized:
                                stock_row = inventory[inventory.index == idx]
                                break
                
                if not stock_row.empty:
                    current_stock = stock_row['current_stock'].iloc[0]
                    
                    # Ensure current_stock is not NaN
                    if pd.isna(current_stock):
                        missing_ingredients.append(ingredient)
                        servings_possible.append(0)
                        continue
                    
                    # Calculate servings - ensure no negative values
                    if required_per_serving > 0:
                        # If stock is negative or zero, ingredient is missing/out of stock
                        if current_stock <= 0:
                            # Use the actual inventory ingredient name for clarity
                            inv_ing_name = stock_row['ingredient'].iloc[0]
                            missing_ingredients.append(f"{inv_ing_name} (out of stock: {max(0, current_stock):.1f})")
                            servings_possible.append(0)
                        else:
                            # Calculate servings and ensure it's never negative
                            servings = current_stock / required_per_serving
                            servings = max(0, int(servings))  # Ensure non-negative integer
                            servings_possible.append(servings)
                    else:
                        # If required_per_serving is 0 or invalid, treat as can make many
                        servings_possible.append(999)
                else:
                    # Ingredient not found in inventory at all
                    missing_ingredients.append(f"{ingredient} (not in inventory)")
                    servings_possible.append(0)
            
            # If we have no valid ingredients processed, mark as cannot make
            if len(servings_possible) == 0:
                if invalid_ingredients:
                    min_servings = 0
                    viability_status = 'Cannot Make (Invalid Recipe Data)'
                    can_make = False
                    missing_ingredients = invalid_ingredients
                else:
                    min_servings = 0
                    viability_status = 'Cannot Make (No Recipe Data)'
                    can_make = False
            elif missing_ingredients:
                min_servings = 0
                viability_status = 'Cannot Make'
                can_make = False
            else:
                min_servings = min(servings_possible) if servings_possible else 0
                # Ensure min_servings is never negative
                min_servings = max(0, int(min_servings))
                
                if min_servings > 0:
                    can_make = True
                    if min_servings >= 50:
                        viability_status = 'High Viability'
                    elif min_servings >= 20:
                        viability_status = 'Medium Viability'
                    else:
                        viability_status = 'Low Viability'
                else:
                    can_make = False
                    viability_status = 'Cannot Make'
            
            # Format missing ingredients nicely - extract only ingredient names
            if missing_ingredients:
                def extract_ingredient_name(ing_str):
                    """Extract just the ingredient name, removing (out of stock: X) or (not in inventory)"""
                    if isinstance(ing_str, str):
                        # Remove "(out of stock: X.X)" pattern
                        ing_str = ing_str.split(' (out of stock:')[0]
                        # Remove "(not in inventory)" pattern
                        ing_str = ing_str.split(' (not in inventory)')[0]
                        return ing_str.strip()
                    return str(ing_str)
                
                if isinstance(missing_ingredients, list):
                    cleaned_ingredients = [extract_ingredient_name(ing) for ing in missing_ingredients]
                    missing_str = '; '.join(cleaned_ingredients)
                else:
                    missing_str = extract_ingredient_name(missing_ingredients)
            else:
                missing_str = None
            
            menu_viability.append({
                'menu_item': menu_item,
                'servings_possible': min_servings,
                'viability_status': viability_status,
                'can_make': can_make,
                'missing_ingredients': missing_str
            })
        
        return pd.DataFrame(menu_viability).sort_values('servings_possible', ascending=False)
    
    def calculate_menu_viability_score(self, current_date: Optional[datetime] = None) -> float:
        """Calculate overall menu viability score (0-100)"""
        menu_viability = self.map_recipes_to_inventory(current_date)
        if menu_viability.empty:
            return 0
        
        # Count viable menu items
        total_items = len(menu_viability)
        viable_items = len(menu_viability[menu_viability['servings_possible'] > 0])
        
        if total_items == 0:
            return 0.0
        
        viability_score = (viable_items / total_items * 100)
        return round(float(viability_score), 2)
    
    def simulate_scenario(self, scenario: Dict, current_date: Optional[datetime] = None) -> pd.DataFrame:
        """Simulate a scenario and show inventory impact"""
        if current_date is None:
            current_date = datetime.now()
        
        # Get base inventory
        base_inventory = self.calculate_inventory_levels(current_date)
        if base_inventory.empty:
            return pd.DataFrame()
        
        # Create simulated data
        simulated_data = self.data.copy()
        
        # Apply scenario changes
        sales_multiplier = scenario.get('sales_multiplier', 1.0)
        price_multiplier = scenario.get('price_multiplier', 1.0)
        supplier_delay_days = scenario.get('supplier_delay_days', 0)
        menu_item_changes = scenario.get('menu_item_changes', {})
        
        # Simulate sales changes
        if sales_multiplier != 1.0 and 'sales' in simulated_data and not simulated_data['sales'].empty:
            simulated_sales = simulated_data['sales'].copy()
            simulated_sales['quantity_sold'] = simulated_sales['quantity_sold'] * sales_multiplier
            simulated_data['sales'] = simulated_sales
        
        # Simulate usage changes based on sales
        if 'usage' in simulated_data and not simulated_data['usage'].empty and 'menu_item' in simulated_data['usage'].columns:
            simulated_usage = simulated_data['usage'].copy()
            
            # Apply menu item specific changes
            for menu_item, multiplier in menu_item_changes.items():
                mask = simulated_usage['menu_item'] == menu_item
                simulated_usage.loc[mask, 'quantity_used'] = simulated_usage.loc[mask, 'quantity_used'] * multiplier
            
            # Apply overall sales multiplier
            if sales_multiplier != 1.0:
                simulated_usage['quantity_used'] = simulated_usage['quantity_used'] * sales_multiplier
            
            simulated_data['usage'] = simulated_usage
        
        # Simulate supplier delays
        # Note: Shipments data might be frequency-based (no dates) or have dates
        # Only simulate delays if shipments have date information
        if supplier_delay_days > 0 and 'shipments' in simulated_data and not simulated_data['shipments'].empty:
            simulated_shipments = simulated_data['shipments'].copy()
            
            # Check if shipments have date column
            if 'date' in simulated_shipments.columns:
                # Convert date column to datetime if needed
                simulated_shipments['date'] = pd.to_datetime(simulated_shipments['date'], errors='coerce')
                
                # Filter future shipments
            future_shipments = simulated_shipments[simulated_shipments['date'] > current_date].copy()
            if not future_shipments.empty:
                    # Add delay to future shipment dates
                simulated_shipments.loc[simulated_shipments['date'] > current_date, 'date'] = (
                    simulated_shipments.loc[simulated_shipments['date'] > current_date, 'date'] + 
                    pd.to_timedelta(supplier_delay_days, unit='D')
                )
                simulated_data['shipments'] = simulated_shipments
            # If shipments don't have dates (frequency-based), delays are simulated through purchases
            # The delay will affect future purchases generated from shipment frequency
        
        # Calculate simulated inventory
        simulated_analytics = InventoryAnalytics(simulated_data)
        simulated_inventory = simulated_analytics.calculate_inventory_levels(current_date)
        
        # Compare with base
        comparison = base_inventory.merge(
            simulated_inventory[['ingredient', 'current_stock', 'days_until_stockout']],
            on='ingredient',
            how='outer',
            suffixes=('_base', '_simulated')
        ).fillna(0)
        
        comparison['stock_change'] = comparison['current_stock_simulated'] - comparison['current_stock_base']
        comparison['stock_change_percentage'] = (
            (comparison['stock_change'] / comparison['current_stock_base'] * 100)
            .replace([np.inf, -np.inf], 0)
            .fillna(0)
            .round(2)
        )
        comparison['days_change'] = comparison['days_until_stockout_simulated'] - comparison['days_until_stockout_base']
        
        return comparison

