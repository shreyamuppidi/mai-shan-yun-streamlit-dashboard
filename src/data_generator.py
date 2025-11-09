"""
Sample Data Generator
Creates realistic sample data for testing and demonstration
"""
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import random


class SampleDataGenerator:
    """Generate sample restaurant inventory data"""
    
    def __init__(self):
        self.ingredients = [
            'Rice', 'Soy Sauce', 'Ginger', 'Garlic', 'Green Onions',
            'Sesame Oil', 'Chicken Breast', 'Pork Belly', 'Tofu', 'Noodles',
            'Bok Choy', 'Carrots', 'Broccoli', 'Mushrooms', 'Bell Peppers',
            'Chili Peppers', 'Scallions', 'Cilantro', 'Bean Sprouts', 'Cabbage',
            'Eggs', 'Shrimp', 'Beef', 'Fish Sauce', 'Oyster Sauce',
            'Shaoxing Wine', 'Cornstarch', 'Sugar', 'Salt', 'Pepper'
        ]
        
        self.menu_items = [
            'Kung Pao Chicken', 'Mapo Tofu', 'Sweet and Sour Pork',
            'General Tso Chicken', 'Beef and Broccoli', 'Hunan Beef',
            'Szechuan Shrimp', 'Vegetable Lo Mein', 'Fried Rice',
            'Hot and Sour Soup', 'Egg Drop Soup', 'Wonton Soup',
            'Peking Duck', 'Orange Chicken', 'Honey Walnut Shrimp'
        ]
        
        # Menu item to ingredient mappings (simplified)
        self.menu_ingredients = {
            'Kung Pao Chicken': ['Chicken Breast', 'Peanuts', 'Chili Peppers', 'Soy Sauce', 'Ginger', 'Garlic'],
            'Mapo Tofu': ['Tofu', 'Ground Pork', 'Sichuan Peppercorns', 'Garlic', 'Ginger', 'Soy Sauce'],
            'Sweet and Sour Pork': ['Pork Belly', 'Bell Peppers', 'Pineapple', 'Sugar', 'Vinegar', 'Soy Sauce'],
            'General Tso Chicken': ['Chicken Breast', 'Chili Peppers', 'Ginger', 'Garlic', 'Soy Sauce', 'Sugar'],
            'Beef and Broccoli': ['Beef', 'Broccoli', 'Garlic', 'Ginger', 'Soy Sauce', 'Oyster Sauce'],
            'Vegetable Lo Mein': ['Noodles', 'Carrots', 'Bell Peppers', 'Broccoli', 'Soy Sauce', 'Sesame Oil'],
            'Fried Rice': ['Rice', 'Eggs', 'Green Onions', 'Soy Sauce', 'Sesame Oil', 'Carrots'],
            'Hot and Sour Soup': ['Mushrooms', 'Tofu', 'Vinegar', 'Soy Sauce', 'White Pepper', 'Cornstarch'],
        }
    
    def generate_ingredients(self, n: int = 30) -> pd.DataFrame:
        """Generate ingredient master list"""
        # Define storage types for ingredients
        storage_types = ['refrigerated', 'frozen', 'shelf']
        ingredient_storage_map = {
            'Rice': 'shelf', 'Soy Sauce': 'shelf', 'Ginger': 'refrigerated', 
            'Garlic': 'shelf', 'Green Onions': 'refrigerated', 'Sesame Oil': 'shelf',
            'Chicken Breast': 'refrigerated', 'Pork Belly': 'refrigerated', 'Tofu': 'refrigerated',
            'Noodles': 'shelf', 'Bok Choy': 'refrigerated', 'Carrots': 'refrigerated',
            'Broccoli': 'refrigerated', 'Mushrooms': 'refrigerated', 'Bell Peppers': 'refrigerated',
            'Chili Peppers': 'refrigerated', 'Scallions': 'refrigerated', 'Cilantro': 'refrigerated',
            'Bean Sprouts': 'refrigerated', 'Cabbage': 'refrigerated', 'Eggs': 'refrigerated',
            'Shrimp': 'frozen', 'Beef': 'refrigerated', 'Fish Sauce': 'shelf',
            'Oyster Sauce': 'shelf', 'Shaoxing Wine': 'shelf', 'Cornstarch': 'shelf',
            'Sugar': 'shelf', 'Salt': 'shelf', 'Pepper': 'shelf'
        }
        
        data = {
            'ingredient': self.ingredients[:n],
            'unit': ['lb', 'oz', 'lb', 'oz', 'bunch', 'oz', 'lb', 'lb', 'lb', 'lb',
                    'bunch', 'lb', 'lb', 'lb', 'lb', 'oz', 'bunch', 'bunch', 'lb', 'lb',
                    'dozen', 'lb', 'lb', 'oz', 'oz', 'oz', 'oz', 'lb', 'oz', 'oz'][:n],
            'category': ['Grain', 'Sauce', 'Vegetable', 'Vegetable', 'Vegetable', 'Oil', 'Protein', 'Protein',
                        'Protein', 'Grain', 'Vegetable', 'Vegetable', 'Vegetable', 'Vegetable', 'Vegetable',
                        'Vegetable', 'Vegetable', 'Vegetable', 'Vegetable', 'Vegetable', 'Protein', 'Protein',
                        'Protein', 'Sauce', 'Sauce', 'Sauce', 'Starch', 'Spice', 'Spice', 'Spice'][:n],
            'shelf_life_days': np.random.randint(3, 30, n),
            'min_stock_level': np.random.randint(10, 50, n),
            'max_stock_level': np.random.randint(100, 500, n),
            'storage_type': [ingredient_storage_map.get(ing, random.choice(storage_types)) for ing in self.ingredients[:n]],
            'storage_space_units': np.random.uniform(0.1, 2.0, n).round(2)  # cubic feet
        }
        return pd.DataFrame(data)
    
    def generate_purchases(self, start_date: datetime, days: int = 365) -> pd.DataFrame:
        """Generate purchase logs"""
        dates = pd.date_range(start_date, periods=days, freq='D')
        purchases = []
        
        for date in dates:
            # Random number of purchases per day (1-5)
            n_purchases = np.random.randint(1, 6)
            
            for _ in range(n_purchases):
                ingredient = random.choice(self.ingredients)
                quantity = np.random.uniform(5, 100)
                cost_per_unit = np.random.uniform(0.5, 15.0)
                total_cost = quantity * cost_per_unit
                
                purchases.append({
                    'date': date,
                    'ingredient': ingredient,
                    'quantity': round(quantity, 2),
                    'unit': 'lb' if quantity > 10 else 'oz',
                    'cost_per_unit': round(cost_per_unit, 2),
                    'total_cost': round(total_cost, 2),
                    'supplier': random.choice(['Supplier A', 'Supplier B', 'Supplier C', 'Local Market'])
                })
        
        return pd.DataFrame(purchases)
    
    def generate_shipments(self, start_date: datetime, days: int = 365) -> pd.DataFrame:
        """Generate shipment data"""
        dates = pd.date_range(start_date, periods=days, freq='D')
        shipments = []
        
        for date in dates:
            # Random shipments per day (0-3)
            n_shipments = np.random.randint(0, 4)
            
            for _ in range(n_shipments):
                ingredient = random.choice(self.ingredients)
                expected_date = date - timedelta(days=np.random.randint(1, 8))
                actual_date = date
                delay = (actual_date - expected_date).days if actual_date > expected_date else 0
                
                quantity = np.random.uniform(10, 200)
                status = random.choice(['Delivered', 'In Transit', 'Delayed'])
                
                shipments.append({
                    'date': actual_date,
                    'expected_date': expected_date,
                    'ingredient': ingredient,
                    'quantity': round(quantity, 2),
                    'status': status,
                    'delay_days': delay if status == 'Delayed' else 0,
                    'supplier': random.choice(['Supplier A', 'Supplier B', 'Supplier C'])
                })
        
        return pd.DataFrame(shipments)
    
    def generate_sales(self, start_date: datetime, days: int = 365) -> pd.DataFrame:
        """Generate menu item sales data"""
        dates = pd.date_range(start_date, periods=days, freq='D')
        sales = []
        
        for date in dates:
            # Sales vary by day of week
            day_of_week = date.weekday()
            base_sales = 50 if day_of_week < 5 else 80  # More on weekends
            
            # Generate sales for each menu item
            for item in self.menu_items:
                # Random sales per item with some items being more popular
                popularity = np.random.uniform(0.3, 1.5)
                qty_sold = int(base_sales * popularity * np.random.uniform(0.5, 1.5))
                
                if qty_sold > 0:
                    price = np.random.uniform(8.99, 18.99)
                    sales.append({
                        'date': date,
                        'menu_item': item,
                        'quantity_sold': qty_sold,
                        'revenue': round(qty_sold * price, 2),
                        'price': round(price, 2)
                    })
        
        return pd.DataFrame(sales)
    
    def generate_usage(self, start_date: datetime, days: int = 365) -> pd.DataFrame:
        """Generate ingredient usage data"""
        dates = pd.date_range(start_date, periods=days, freq='D')
        usage = []
        
        # Get sales data to calculate usage
        sales = self.generate_sales(start_date, days)
        
        for _, sale in sales.iterrows():
            menu_item = sale['menu_item']
            date = sale['date']
            qty_sold = sale['quantity_sold']
            
            # Get ingredients for this menu item
            if menu_item in self.menu_ingredients:
                ingredients = self.menu_ingredients[menu_item]
            else:
                # Default ingredients if not in mapping
                ingredients = random.sample(self.ingredients, 4)
            
            # Calculate usage per dish
            for ingredient in ingredients:
                usage_per_dish = np.random.uniform(0.1, 2.0)
                total_usage = qty_sold * usage_per_dish
                
                usage.append({
                    'date': date,
                    'ingredient': ingredient,
                    'menu_item': menu_item,
                    'quantity_used': round(total_usage, 2),
                    'unit': 'lb' if total_usage > 1 else 'oz'
                })
        
        # Create usage DataFrame - preserve menu_item for recipe mapping
        usage_df = pd.DataFrame(usage)
        
        # Also create aggregated version for backward compatibility
        # But return the detailed version with menu_item
        if not usage_df.empty:
            # Ensure menu_item is preserved
            if 'menu_item' not in usage_df.columns:
                # If menu_item was lost, we need to recreate it from the original data
                pass
        
        return usage_df
    
    def generate_all_sample_data(self, output_dir: str = "data"):
        """Generate all sample data files"""
        from pathlib import Path
        output_path = Path(output_dir)
        output_path.mkdir(exist_ok=True)
        
        start_date = datetime.now() - timedelta(days=365)
        
        print("Generating sample data...")
        
        ingredients = self.generate_ingredients()
        ingredients.to_csv(output_path / "ingredients.csv", index=False)
        print(f"✓ Generated ingredients.csv ({len(ingredients)} ingredients)")
        
        purchases = self.generate_purchases(start_date)
        purchases.to_csv(output_path / "purchases.csv", index=False)
        print(f"✓ Generated purchases.csv ({len(purchases)} records)")
        
        shipments = self.generate_shipments(start_date)
        shipments.to_csv(output_path / "shipments.csv", index=False)
        print(f"✓ Generated shipments.csv ({len(shipments)} records)")
        
        sales = self.generate_sales(start_date)
        sales.to_csv(output_path / "sales.csv", index=False)
        print(f"✓ Generated sales.csv ({len(sales)} records)")
        
        usage = self.generate_usage(start_date)
        usage.to_csv(output_path / "usage.csv", index=False)
        print(f"✓ Generated usage.csv ({len(usage)} records)")
        
        print("\n✅ All sample data generated successfully!")


if __name__ == "__main__":
    generator = SampleDataGenerator()
    generator.generate_all_sample_data()

