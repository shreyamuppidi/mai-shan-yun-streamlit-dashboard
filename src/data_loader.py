"""
Data Loading and Processing Module
Handles loading and preprocessing of restaurant inventory data
"""
import pandas as pd
import numpy as np
from pathlib import Path
from typing import Dict, List, Optional
import warnings
warnings.filterwarnings('ignore')

# Try to import MSY loader
try:
    from .msy_data_loader import MSYDataLoader
    MSY_LOADER_AVAILABLE = True
except ImportError:
    try:
        from msy_data_loader import MSYDataLoader
        MSY_LOADER_AVAILABLE = True
    except ImportError:
        MSY_LOADER_AVAILABLE = False

# Try to import DataPreprocessor
try:
    from .data_preprocessor import DataPreprocessor
    PREPROCESSOR_AVAILABLE = True
except ImportError:
    try:
        from data_preprocessor import DataPreprocessor
        PREPROCESSOR_AVAILABLE = True
    except ImportError:
        PREPROCESSOR_AVAILABLE = False
        DataPreprocessor = None


class DataLoader:
    """Load and process restaurant inventory data"""
    
    def __init__(self, data_dir: str = "data"):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(exist_ok=True)
        # Initialize preprocessor if available
        if PREPROCESSOR_AVAILABLE:
            self.preprocessor = DataPreprocessor()
        else:
            self.preprocessor = None
        
    def load_purchases(self, file_path: Optional[str] = None) -> pd.DataFrame:
        """Load monthly purchase logs"""
        if file_path:
            df = pd.read_csv(file_path)
        else:
            # Try to find purchase file
            purchase_file = self.data_dir / "purchases.csv"
            if purchase_file.exists():
                df = pd.read_csv(purchase_file)
            else:
                return None
        return self._clean_purchases(df)
    
    def load_shipments(self, file_path: Optional[str] = None) -> pd.DataFrame:
        """Load shipment details"""
        if file_path:
            df = pd.read_csv(file_path)
        else:
            shipment_file = self.data_dir / "shipments.csv"
            if shipment_file.exists():
                df = pd.read_csv(shipment_file)
            else:
                return None
        return self._clean_shipments(df)
    
    def load_ingredients(self, file_path: Optional[str] = None) -> pd.DataFrame:
        """Load ingredient master list"""
        if file_path:
            df = pd.read_csv(file_path)
        else:
            ingredient_file = self.data_dir / "ingredients.csv"
            if ingredient_file.exists():
                df = pd.read_csv(ingredient_file)
            else:
                return None
        return self._clean_ingredients(df)
    
    def load_sales(self, file_path: Optional[str] = None) -> pd.DataFrame:
        """Load menu item sales data"""
        if file_path:
            df = pd.read_csv(file_path)
        else:
            sales_file = self.data_dir / "sales.csv"
            if sales_file.exists():
                df = pd.read_csv(sales_file)
            else:
                return None
        return self._clean_sales(df)
    
    def load_usage(self, file_path: Optional[str] = None) -> pd.DataFrame:
        """Load ingredient usage data"""
        if file_path:
            df = pd.read_csv(file_path)
        else:
            usage_file = self.data_dir / "usage.csv"
            if usage_file.exists():
                df = pd.read_csv(usage_file)
            else:
                return None
        return self._clean_usage(df)
    
    def _clean_purchases(self, df: pd.DataFrame) -> pd.DataFrame:
        """Clean purchase data"""
        # Standardize date column
        date_cols = ['date', 'purchase_date', 'Date', 'Purchase Date']
        for col in date_cols:
            if col in df.columns:
                df['date'] = pd.to_datetime(df[col], errors='coerce')
                break
        
        # Standardize quantity and cost columns
        if 'quantity' not in df.columns:
            qty_cols = ['qty', 'Quantity', 'Qty', 'amount']
            for col in qty_cols:
                if col in df.columns:
                    df['quantity'] = pd.to_numeric(df[col], errors='coerce')
                    break
        
        # Handle cost columns - prioritize total_cost
        if 'total_cost' not in df.columns:
            cost_cols = ['total_cost', 'Total Cost', 'cost', 'Cost', 'price', 'Price']
            cost_found = False
            for col in cost_cols:
                if col in df.columns:
                    df['total_cost'] = pd.to_numeric(df[col], errors='coerce')
                    cost_found = True
                    break
            
            # If we have cost_per_unit and quantity, calculate total_cost
            if not cost_found and 'cost_per_unit' in df.columns and 'quantity' in df.columns:
                df['total_cost'] = pd.to_numeric(df['cost_per_unit'], errors='coerce') * pd.to_numeric(df['quantity'], errors='coerce')
            elif not cost_found and 'price' in df.columns and 'quantity' in df.columns:
                df['total_cost'] = pd.to_numeric(df['price'], errors='coerce') * pd.to_numeric(df['quantity'], errors='coerce')
        
        # Ensure we have ingredient column
        if 'ingredient' not in df.columns:
            ing_cols = ['ingredient', 'Ingredient', 'ingredient_name', 'item']
            for col in ing_cols:
                if col in df.columns:
                    df['ingredient'] = df[col]
                    break
        
        df = df.dropna(subset=['date'])
        
        # Apply preprocessor if available
        if self.preprocessor is not None:
            df = self.preprocessor.preprocess_purchases(df)
        
        return df
    
    def _clean_shipments(self, df: pd.DataFrame) -> pd.DataFrame:
        """Clean shipment data"""
        date_cols = ['date', 'ship_date', 'Date', 'Ship Date', 'expected_date', 'Expected Date']
        for col in date_cols:
            if col in df.columns:
                df['date'] = pd.to_datetime(df[col], errors='coerce')
                break
        
        # Handle delay calculations
        if 'expected_date' in df.columns or 'Expected Date' in df.columns:
            exp_col = 'expected_date' if 'expected_date' in df.columns else 'Expected Date'
            df['expected_date'] = pd.to_datetime(df[exp_col], errors='coerce')
            df['delay_days'] = (df['date'] - df['expected_date']).dt.days
        
        df = df.dropna(subset=['date'])
        
        # Apply preprocessor if available
        if self.preprocessor is not None:
            df = self.preprocessor.preprocess_shipments(df)
        
        return df
    
    def _clean_ingredients(self, df: pd.DataFrame) -> pd.DataFrame:
        """Clean ingredient data"""
        # Ensure we have ingredient names and units
        if 'ingredient' not in df.columns:
            name_cols = ['name', 'Name', 'ingredient_name', 'Ingredient Name']
            for col in name_cols:
                if col in df.columns:
                    df['ingredient'] = df[col]
                    break
        
        # Apply preprocessor if available
        if self.preprocessor is not None:
            df = self.preprocessor.preprocess_ingredients(df)
        
        return df
    
    def _clean_sales(self, df: pd.DataFrame) -> pd.DataFrame:
        """Clean sales data"""
        date_cols = ['date', 'sale_date', 'Date', 'Sale Date']
        for col in date_cols:
            if col in df.columns:
                df['date'] = pd.to_datetime(df[col], errors='coerce')
                break
        
        df = df.dropna(subset=['date'])
        
        # Apply preprocessor if available
        if self.preprocessor is not None:
            df = self.preprocessor.preprocess_sales(df)
        
        return df
    
    def _clean_usage(self, df: pd.DataFrame) -> pd.DataFrame:
        """Clean usage data"""
        date_cols = ['date', 'usage_date', 'Date', 'Usage Date']
        for col in date_cols:
            if col in df.columns:
                df['date'] = pd.to_datetime(df[col], errors='coerce')
                break
        
        # Ensure menu_item column is preserved if it exists
        # Standardize menu_item column names
        menu_item_cols = ['menu_item', 'Menu Item', 'menuItem', 'dish', 'Dish']
        for col in menu_item_cols:
            if col in df.columns and col != 'menu_item':
                df['menu_item'] = df[col]
                break
        
        df = df.dropna(subset=['date'])
        
        # Apply preprocessor if available
        if self.preprocessor is not None:
            df = self.preprocessor.preprocess_usage(df)
        
        return df
    
    def load_all_data(self) -> Dict[str, pd.DataFrame]:
        """Load all available data files, prioritizing MSY format"""
        data = {}
        
        # Always try MSY loader first if available
        if MSY_LOADER_AVAILABLE:
            try:
                msy_loader = MSYDataLoader(data_dir=str(self.data_dir))
                msy_data = msy_loader.load_all_data()
                
                # Use MSY data if it has any content
                if msy_data:
                    # Check if we have meaningful data (at least one non-empty DataFrame)
                    has_data = any(
                        (isinstance(df, pd.DataFrame) and not df.empty) 
                        for df in msy_data.values()
                    )
                    if has_data:
                        data.update(msy_data)
                        # Ensure all required keys exist
                        required_keys = ['purchases', 'shipments', 'ingredients', 'sales', 'usage']
                        for key in required_keys:
                            if key not in data:
                                data[key] = pd.DataFrame()
                        
                        # Apply preprocessing to all data (especially shipments for unit standardization)
                        if self.preprocessor:
                            if 'shipments' in data and not data['shipments'].empty:
                                data['shipments'] = self.preprocessor.preprocess_shipments(data['shipments'])
                            if 'purchases' in data and not data['purchases'].empty:
                                data['purchases'] = self.preprocessor.preprocess_purchases(data['purchases'])
                            if 'usage' in data and not data['usage'].empty:
                                data['usage'] = self.preprocessor.preprocess_usage(data['usage'])
                            if 'sales' in data and not data['sales'].empty:
                                data['sales'] = self.preprocessor.preprocess_sales(data['sales'])
                            if 'ingredients' in data and not data['ingredients'].empty:
                                data['ingredients'] = self.preprocessor.preprocess_ingredients(data['ingredients'])
                        
                        return data
            except Exception as e:
                # Log error but continue to standard loader
                print(f"Warning: MSY loader encountered an error: {str(e)}")
                import traceback
                traceback.print_exc()
        
        # Fall back to standard loading only if MSY loader not available or failed completely
        # This handles cases where user has standard CSV files instead of MSY format
        purchases = self.load_purchases()
        if purchases is not None and not purchases.empty:
            data['purchases'] = purchases
        else:
            data['purchases'] = pd.DataFrame()
        
        shipments = self.load_shipments()
        if shipments is not None and not shipments.empty:
            data['shipments'] = shipments
        else:
            data['shipments'] = pd.DataFrame()
        
        ingredients = self.load_ingredients()
        if ingredients is not None and not ingredients.empty:
            data['ingredients'] = ingredients
        else:
            data['ingredients'] = pd.DataFrame()
        
        sales = self.load_sales()
        if sales is not None and not sales.empty:
            data['sales'] = sales
        else:
            data['sales'] = pd.DataFrame()
        
        usage = self.load_usage()
        if usage is not None and not usage.empty:
            data['usage'] = usage
        else:
            data['usage'] = pd.DataFrame()
        
        return data

