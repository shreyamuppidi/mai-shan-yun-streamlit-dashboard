"""
MSY Real Data Loader
Handles loading and processing of real Mai Shan Yun restaurant data
including Excel monthly matrices from the GitHub repository
"""
import pandas as pd
import numpy as np
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import warnings
import glob
import re
from datetime import datetime, timedelta
warnings.filterwarnings('ignore')

# Try to import DataPreprocessor
try:
    from .data_preprocessor import DataPreprocessor
except ImportError:
    try:
        from data_preprocessor import DataPreprocessor
    except ImportError:
        DataPreprocessor = None


class MSYDataLoader:
    """Load and process real MSY restaurant inventory data"""
    
    def __init__(self, data_dir: str = "data"):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(exist_ok=True)
        self.recipe_matrix = None
    
    def load_recipe_matrix(self) -> pd.DataFrame:
        """Load recipe matrix from MSY Data - Ingredient.csv"""
        msy_file = self.data_dir / "MSY Data - Ingredient.csv"
        if not msy_file.exists():
            return pd.DataFrame()
        
        try:
            df = pd.read_csv(msy_file)
            # First column is menu items (Item name), rest are ingredients
            if df.empty:
                return pd.DataFrame()
            
            # Store recipe matrix
            self.recipe_matrix = df
            return df
        except Exception as e:
            print(f"Warning: Could not load recipe matrix: {str(e)}")
            return pd.DataFrame()
    
    def load_msy_ingredients(self, file_path: Optional[str] = None) -> pd.DataFrame:
        """Create ingredient master list from recipe matrix and shipment data"""
        # Load recipe matrix to get ingredient list
        if self.recipe_matrix is None:
            self.load_recipe_matrix()
        
        ingredients_list = []
        
        # Get ingredients from recipe matrix (all columns except first)
        if self.recipe_matrix is not None and not self.recipe_matrix.empty:
            ingredient_cols = [col for col in self.recipe_matrix.columns if col != 'Item name']
            ingredients_list.extend(ingredient_cols)
        
        # Get ingredients from shipment data
        shipments = self.load_msy_shipments()
        if shipments is not None and not shipments.empty and 'ingredient' in shipments.columns:
            ingredients_list.extend(shipments['ingredient'].unique().tolist())
        
        # Remove duplicates and create ingredient master list
        unique_ingredients = list(set(ingredients_list))
        
        if not unique_ingredients:
            return pd.DataFrame()
        
        # Create ingredient DataFrame with defaults
        ingredients_df = pd.DataFrame({
            'ingredient': unique_ingredients
        })
        
        # Add default values
        ingredients_df['min_stock_level'] = 20
        ingredients_df['max_stock_level'] = 200
        ingredients_df['shelf_life_days'] = 14
        ingredients_df['unit'] = 'units'
        ingredients_df['category'] = 'Other'
        
        # Infer storage type
        ingredients_df['storage_type'] = ingredients_df['ingredient'].apply(self._infer_storage_type_from_name)
        ingredients_df['storage_space_units'] = 1.0
        
        # Update from shipment data if available
        if shipments is not None and not shipments.empty and 'ingredient' in shipments.columns:
            # Extract units from shipment data
            if 'Unit of shipment' in shipments.columns:
                unit_map = shipments.set_index('ingredient')['Unit of shipment'].to_dict()
                ingredients_df['unit'] = ingredients_df['ingredient'].map(unit_map).fillna('units')
        
        return ingredients_df
    
    def _infer_storage_type_from_name(self, ingredient_name: str) -> str:
        """Infer storage type from ingredient name"""
        ingredient = str(ingredient_name).lower()
        
        if any(word in ingredient for word in ['frozen', 'ice']):
            return 'frozen'
        elif any(word in ingredient for word in ['chicken', 'pork', 'beef', 'shrimp', 'tofu', 'egg', 'braised']):
            return 'refrigerated'
        elif any(word in ingredient for word in ['onion', 'cilantro', 'cabbage', 'carrot', 'boychoy', 'peas']):
            return 'refrigerated'
        else:
            return 'shelf'
    
    def load_msy_shipments(self, file_path: Optional[str] = None) -> pd.DataFrame:
        """Load MSY shipment data"""
        if file_path:
            df = pd.read_csv(file_path)
        else:
            msy_file = self.data_dir / "MSY Data - Shipment.csv"
            if msy_file.exists():
                df = pd.read_csv(msy_file)
            else:
                shipment_file = self.data_dir / "shipments.csv"
                if shipment_file.exists():
                    df = pd.read_csv(shipment_file)
                else:
                    return None
        
        # Standardize column names
        column_mapping = {
            'Ingredient': 'ingredient',
            'Ingredient Name': 'ingredient',
            'Quantity per shipment': 'quantity',
            'Unit of shipment': 'unit',
            'Number of shipments': 'num_shipments',
            'frequency': 'frequency'
        }
        
        df = df.rename(columns=column_mapping)
        
        # Ensure ingredient column exists
        if 'ingredient' not in df.columns:
            return None
        
        # If this is frequency-based data (no dates), we'll handle it separately
        # For now, return the shipment data as-is for reference
        # Purchase generation from frequency will be done in load_all_data
        return df
    
    def generate_purchases_from_shipments(self, shipments_df: pd.DataFrame) -> pd.DataFrame:
        """Generate purchase data from shipment frequency information"""
        if shipments_df.empty or 'frequency' not in shipments_df.columns:
            return pd.DataFrame()
        
        purchases_list = []
        # Generate purchase dates based on frequency for the last 6 months
        start_date = datetime.now() - timedelta(days=180)
        end_date = datetime.now()
        
        for _, row in shipments_df.iterrows():
            ingredient = row['ingredient']
            qty_per_shipment = pd.to_numeric(row.get('quantity', 0), errors='coerce') or 0
            num_shipments = pd.to_numeric(row.get('num_shipments', 0), errors='coerce') or 0
            frequency = str(row.get('frequency', 'weekly')).lower()
            
            if qty_per_shipment <= 0:
                continue
            
            # Calculate shipment dates based on frequency
            if 'weekly' in frequency:
                days_between = 7
            elif 'biweekly' in frequency:
                days_between = 14
            elif 'monthly' in frequency:
                days_between = 30
            else:
                days_between = 7  # Default to weekly
            
            # Generate purchase dates
            current_date = start_date
            purchase_count = 0
            max_purchases = max(num_shipments, 24)  # At least generate some purchases
            
            while current_date <= end_date and purchase_count < max_purchases:
                purchases_list.append({
                    'date': current_date,
                    'ingredient': ingredient,
                    'quantity': qty_per_shipment,
                    'total_cost': 0,  # Cost not available in shipment data
                    'supplier': 'Unknown'
                })
                current_date += timedelta(days=days_between)
                purchase_count += 1
        
        if purchases_list:
            return pd.DataFrame(purchases_list)
        return pd.DataFrame()
    
    def load_monthly_matrices(self) -> Dict[str, pd.DataFrame]:
        """Load monthly data matrices from Excel files"""
        monthly_data = {
            'purchases': [],
            'sales': [],
            'usage': []
        }
        
        # Find all Excel files matching monthly pattern
        excel_files = glob.glob(str(self.data_dir / "*_Data_Matrix*.xlsx")) + \
                     glob.glob(str(self.data_dir / "*Data_Matrix*.xlsx"))
        
        if not excel_files:
            excel_files = list(self.data_dir.glob("*.xlsx"))
        
        for excel_file in excel_files:
            try:
                # Convert to Path if it's a string
                if isinstance(excel_file, str):
                    excel_file = Path(excel_file)
                
                # Extract month/year from filename
                month_year = self._extract_month_year_from_filename(excel_file.name)
                
                # Read all sheets
                xls = pd.ExcelFile(excel_file)
                
                for sheet_name in xls.sheet_names:
                    try:
                        df = pd.read_excel(str(excel_file), sheet_name=sheet_name, header=None)
                        
                        # Try different parsing strategies
                        # Strategy 1: Matrix format (dates in first column/row, ingredients/menu items in columns/rows)
                        parsed_data = self._parse_matrix_sheet(df, sheet_name, month_year, excel_file.stem)
                        
                        if parsed_data:
                            if 'purchases' in parsed_data:
                                monthly_data['purchases'].extend(parsed_data['purchases'])
                            if 'sales' in parsed_data:
                                monthly_data['sales'].extend(parsed_data['sales'])
                            if 'usage' in parsed_data:
                                monthly_data['usage'].extend(parsed_data['usage'])
                        
                        # Strategy 2: Standard format (try existing parsers)
                        purchases = self._parse_purchase_sheet(df, excel_file.stem)
                        if purchases is not None and not purchases.empty:
                            monthly_data['purchases'].append(purchases)
                        
                        sales = self._parse_sales_sheet(df, excel_file.stem, month_year)
                        if sales is not None and not sales.empty:
                            monthly_data['sales'].append(sales)
                        
                        usage = self._parse_usage_sheet(df, excel_file.stem)
                        if usage is not None and not usage.empty:
                            monthly_data['usage'].append(usage)
                    
                    except Exception as e:
                        print(f"Warning: Could not parse sheet {sheet_name} in {excel_file}: {str(e)}")
                        continue
            
            except Exception as e:
                print(f"Warning: Could not parse {excel_file}: {str(e)}")
                continue
        
        # Combine all monthly data
        result = {}
        for key, data_list in monthly_data.items():
            if data_list:
                result[key] = pd.concat(data_list, ignore_index=True)
            else:
                result[key] = pd.DataFrame()
        
        return result
    
    def _extract_month_year_from_filename(self, filename: str) -> Tuple[Optional[int], Optional[int]]:
        """Extract month and year from filename"""
        # Try to extract month name and year
        month_map = {
            'january': 1, 'february': 2, 'march': 3, 'april': 4,
            'may': 5, 'june': 6, 'july': 7, 'august': 8,
            'september': 9, 'october': 10, 'november': 11, 'december': 12
        }
        
        filename_lower = filename.lower()
        year = None
        month = None
        
        # Extract year (4 digits)
        year_match = re.search(r'20\d{2}', filename)
        if year_match:
            year = int(year_match.group())
        
        # Extract month
        for month_name, month_num in month_map.items():
            if month_name in filename_lower:
                month = month_num
                break
        
        # If no year found, assume current year
        if year is None:
            year = datetime.now().year
        
        # If no month found, try to extract from numeric patterns
        if month is None:
            month_match = re.search(r'\b(0?[1-9]|1[0-2])\b', filename)
            if month_match:
                month = int(month_match.group())
        
        return month, year
    
    def _parse_matrix_sheet(self, df: pd.DataFrame, sheet_name: str, 
                           month_year: Tuple[Optional[int], Optional[int]], 
                           source: str) -> Optional[Dict]:
        """Parse matrix-style sheet (dates in rows/columns, items in columns/rows)"""
        if df.empty or df.shape[0] < 2 or df.shape[1] < 2:
            return None
        
        result = {'purchases': [], 'sales': [], 'usage': []}
        month, year = month_year
        
        # Try to identify if first row/column contains dates
        first_col = df.iloc[:, 0].astype(str)
        first_row = df.iloc[0, :].astype(str)
        
        # Check if first column contains dates
        date_col_indices = []
        for idx, val in enumerate(first_col):
            try:
                pd.to_datetime(val, errors='raise')
                date_col_indices.append(idx)
            except:
                pass
        
        # Check if first row contains dates
        date_row_indices = []
        for idx, val in enumerate(first_row):
            try:
                pd.to_datetime(val, errors='raise')
                date_row_indices.append(idx)
            except:
                pass
        
        # If we found dates, parse as matrix
        if date_col_indices or date_row_indices:
            # Assume dates are in first column, items in first row (after header)
            if date_col_indices:
                # Dates in rows, items in columns
                dates = []
                for idx in date_col_indices:
                    try:
                        date_val = pd.to_datetime(first_col.iloc[idx])
                        # If only month/year provided, use day 1
                        if month and year and pd.isna(date_val):
                            date_val = datetime(year, month, 1)
                        dates.append(date_val)
                    except:
                        if month and year:
                            dates.append(datetime(year, month, 1))
                
                # Get item names from header row (skip first column)
                items = df.iloc[0, 1:].astype(str).tolist()
                
                # Parse data
                for date_idx, date_val in enumerate(date_col_indices):
                    if date_idx >= len(dates):
                        continue
                    date = dates[date_idx]
                    row_data = df.iloc[date_val, 1:]
                    
                    for item_idx, item_name in enumerate(items):
                        if item_idx >= len(row_data):
                            continue
                        value = pd.to_numeric(row_data.iloc[item_idx], errors='coerce')
                        if pd.notna(value) and value > 0:
                            # Determine if this is sales (menu item) or usage (ingredient)
                            if self._is_menu_item(item_name):
                                result['sales'].append({
                                    'date': date,
                                    'menu_item': item_name,
                                    'quantity_sold': value,
                                    'revenue': 0,
                                    'price': 0
                                })
                            else:
                                result['usage'].append({
                                    'date': date,
                                    'ingredient': item_name,
                                    'quantity_used': value,
                                    'menu_item': 'Unknown'
                                })
        
        # Return result if we found data
        if any(result.values()):
            return result
        return None
    
    def _is_menu_item(self, name: str) -> bool:
        """Check if a name is a menu item based on recipe matrix"""
        if self.recipe_matrix is None:
            self.load_recipe_matrix()
        
        if self.recipe_matrix is not None and not self.recipe_matrix.empty:
            menu_items = self.recipe_matrix['Item name'].astype(str).str.lower().tolist()
            return str(name).lower() in menu_items
        
        # Heuristic: menu items often contain words like "ramen", "rice", "noodles", "fried"
        menu_keywords = ['ramen', 'rice', 'noodle', 'fried', 'soup', 'tossed', 'cutlet', 'wings']
        name_lower = str(name).lower()
        return any(keyword in name_lower for keyword in menu_keywords)
    
    def _parse_purchase_sheet(self, df: pd.DataFrame, source: str) -> Optional[pd.DataFrame]:
        """Parse purchase data from a sheet"""
        # Reset index if needed
        if df.empty:
            return None
        
        # Try with header
        df_with_header = df.copy()
        if df.shape[0] > 0:
            df_with_header.columns = df.iloc[0] if df.shape[0] > 0 else df.columns
            df_with_header = df_with_header.iloc[1:]
        
        # Look for date, ingredient, quantity, cost columns
        date_cols = [col for col in df_with_header.columns if 'date' in str(col).lower() or 'time' in str(col).lower()]
        ingredient_cols = [col for col in df_with_header.columns if 'ingredient' in str(col).lower() or 'item' in str(col).lower()]
        qty_cols = [col for col in df_with_header.columns if 'qty' in str(col).lower() or 'quantity' in str(col).lower() or 'amount' in str(col).lower()]
        cost_cols = [col for col in df_with_header.columns if 'cost' in str(col).lower() or 'price' in str(col).lower() or 'total' in str(col).lower()]
        
        if not date_cols or not ingredient_cols:
            return None
        
        result = pd.DataFrame()
        result['date'] = pd.to_datetime(df_with_header[date_cols[0]], errors='coerce')
        result['ingredient'] = df_with_header[ingredient_cols[0]].astype(str)
        
        if qty_cols:
            result['quantity'] = pd.to_numeric(df_with_header[qty_cols[0]], errors='coerce')
        else:
            result['quantity'] = 0
        
        if cost_cols:
            result['total_cost'] = pd.to_numeric(df_with_header[cost_cols[0]], errors='coerce')
        else:
            result['total_cost'] = 0
        
        # Try to find supplier column
        supplier_cols = [col for col in df_with_header.columns if 'supplier' in str(col).lower() or 'vendor' in str(col).lower()]
        if supplier_cols:
            result['supplier'] = df_with_header[supplier_cols[0]].astype(str)
        else:
            result['supplier'] = 'Unknown'
        
        # Ensure required columns exist
        if 'date' not in result.columns or 'ingredient' not in result.columns:
            return None
        
        result = result.dropna(subset=['date', 'ingredient'])
        if result.empty:
            return None
        return result
    
    def _parse_sales_sheet(self, df: pd.DataFrame, source: str, month_year: Tuple[Optional[int], Optional[int]] = (None, None)) -> Optional[pd.DataFrame]:
        """Parse sales data from a sheet"""
        if df.empty:
            return None
        
        # Use first row as header if it looks like headers
        df_with_header = df.copy()
        if df.shape[0] > 0:
            # Check if first row looks like data or headers
            first_row_str = [str(x).lower() for x in df.iloc[0]]
            if any(keyword in ' '.join(first_row_str) for keyword in ['category', 'group', 'count', 'amount', 'menu', 'item']):
                df_with_header.columns = df.iloc[0]
                df_with_header = df_with_header.iloc[1:]
        
        # Look for menu item columns (Category, Group, Menu Item, Dish, Item)
        menu_cols = [col for col in df_with_header.columns if any(keyword in str(col).lower() for keyword in ['category', 'group', 'menu', 'dish', 'item'])]
        qty_cols = [col for col in df_with_header.columns if any(keyword in str(col).lower() for keyword in ['count', 'qty', 'quantity', 'sold'])]
        revenue_cols = [col for col in df_with_header.columns if any(keyword in str(col).lower() for keyword in ['amount', 'revenue', 'price', 'total', 'cost'])]
        date_cols = [col for col in df_with_header.columns if 'date' in str(col).lower() or 'time' in str(col).lower()]
        
        # Need at least menu item column
        if not menu_cols:
            return None
        
        result = pd.DataFrame()
        result['menu_item'] = df_with_header[menu_cols[0]].astype(str)
        
        # Quantity
        if qty_cols:
            # Remove commas and convert to numeric
            qty_data = df_with_header[qty_cols[0]].astype(str).str.replace(',', '').str.replace('$', '')
            result['quantity_sold'] = pd.to_numeric(qty_data, errors='coerce').fillna(0)
        else:
            result['quantity_sold'] = 1
        
        # Revenue
        if revenue_cols:
            # Remove $ and commas, convert to numeric
            revenue_data = df_with_header[revenue_cols[0]].astype(str).str.replace('$', '').str.replace(',', '')
            result['revenue'] = pd.to_numeric(revenue_data, errors='coerce').fillna(0)
            result['price'] = result['revenue'] / result['quantity_sold'].replace(0, 1)
        else:
            result['revenue'] = 0
            result['price'] = 0
        
        # Date - infer from filename if not in data
        if date_cols:
            result['date'] = pd.to_datetime(df_with_header[date_cols[0]], errors='coerce')
        else:
            # Infer date from month_year or use current date
            month, year = month_year
            if month and year:
                # Use first day of month as default
                result['date'] = datetime(year, month, 1)
            else:
                # Extract from source filename
                month, year = self._extract_month_year_from_filename(source)
                if month and year:
                    result['date'] = datetime(year, month, 1)
                else:
                    result['date'] = datetime.now()
        
        # Filter out invalid rows
        result = result[result['menu_item'].notna()]
        result = result[result['menu_item'] != '']
        result = result[result['quantity_sold'] > 0]
        
        if result.empty:
            return None
        
        return result
    
    def _parse_usage_sheet(self, df: pd.DataFrame, source: str) -> Optional[pd.DataFrame]:
        """Parse usage data from a sheet"""
        if df.empty:
            return None
        
        # Try with header
        df_with_header = df.copy()
        if df.shape[0] > 0:
            df_with_header.columns = df.iloc[0] if df.shape[0] > 0 else df.columns
            df_with_header = df_with_header.iloc[1:]
        
        # Look for date, ingredient, quantity used, menu item columns
        date_cols = [col for col in df_with_header.columns if 'date' in str(col).lower() or 'time' in str(col).lower()]
        ingredient_cols = [col for col in df_with_header.columns if 'ingredient' in str(col).lower()]
        menu_cols = [col for col in df_with_header.columns if 'menu' in str(col).lower() or 'dish' in str(col).lower()]
        qty_cols = [col for col in df_with_header.columns if 'qty' in str(col).lower() or 'quantity' in str(col).lower() or 'used' in str(col).lower()]
        
        if not date_cols or not ingredient_cols:
            return None
        
        result = pd.DataFrame()
        result['date'] = pd.to_datetime(df_with_header[date_cols[0]], errors='coerce')
        result['ingredient'] = df_with_header[ingredient_cols[0]].astype(str)
        
        if menu_cols:
            result['menu_item'] = df_with_header[menu_cols[0]].astype(str)
        else:
            result['menu_item'] = 'Unknown'
        
        if qty_cols:
            result['quantity_used'] = pd.to_numeric(df_with_header[qty_cols[0]], errors='coerce').fillna(0)
        else:
            result['quantity_used'] = 0
        
        # Ensure required columns exist
        if 'date' not in result.columns or 'ingredient' not in result.columns:
            return None
        
        result = result.dropna(subset=['date', 'ingredient'])
        if result.empty:
            return None
        return result
    
    def generate_usage_from_sales_and_recipes(self, sales_df: pd.DataFrame) -> pd.DataFrame:
        """Generate usage data from sales and recipe matrix"""
        if self.recipe_matrix is None:
            self.load_recipe_matrix()
        
        if self.recipe_matrix is None or self.recipe_matrix.empty or sales_df.empty:
            return pd.DataFrame()
        
        usage_list = []
        
        # Create a mapping of menu item names (normalized) to recipe rows
        recipe_map = {}
        for idx, row in self.recipe_matrix.iterrows():
            item_name = str(row['Item name']).strip()
            # Store both exact and normalized versions
            recipe_map[item_name.lower()] = row
            recipe_map[item_name] = row
        
        # Iterate through sales
        for _, sale in sales_df.iterrows():
            menu_item = str(sale.get('menu_item', '')).strip()
            quantity_sold = pd.to_numeric(sale.get('quantity_sold', 0), errors='coerce') or 0
            date = sale.get('date', datetime.now())
            
            if not menu_item or quantity_sold <= 0 or pd.isna(quantity_sold):
                continue
            
            # Find recipe for this menu item (try normalized first)
            recipe_row = None
            menu_item_lower = menu_item.lower()
            
            # Try exact match (case-insensitive)
            if menu_item_lower in recipe_map:
                recipe_row = recipe_map[menu_item_lower]
            else:
                # Try partial match
                for key, row in recipe_map.items():
                    if menu_item_lower in key.lower() or key.lower() in menu_item_lower:
                        recipe_row = row
                        break
            
            if recipe_row is None:
                # Skip if no recipe found
                continue
            
            # Get ingredients from recipe (all columns except 'Item name')
            ingredient_cols = [col for col in self.recipe_matrix.columns if col != 'Item name']
            
            for ingredient in ingredient_cols:
                ingredient_qty = pd.to_numeric(recipe_row[ingredient], errors='coerce')
                if pd.notna(ingredient_qty) and ingredient_qty > 0:
                    # Calculate total usage for this sale
                    total_usage = ingredient_qty * quantity_sold
                    
                    usage_list.append({
                        'date': pd.to_datetime(date),
                        'ingredient': str(ingredient).strip(),
                        'menu_item': menu_item,
                        'quantity_used': total_usage
                    })
        
        if usage_list:
            return pd.DataFrame(usage_list)
        return pd.DataFrame()
    
    def load_all_data(self) -> Dict[str, pd.DataFrame]:
        """Load all available MSY data"""
        data = {}
        
        # Load recipe matrix first
        self.load_recipe_matrix()
        
        # Load ingredients (created from recipe matrix and shipments)
        ingredients = self.load_msy_ingredients()
        if ingredients is not None and not ingredients.empty:
            data['ingredients'] = ingredients
        
        # Load shipments
        shipments = self.load_msy_shipments()
        if shipments is not None and not shipments.empty:
            data['shipments'] = shipments
            
            # Generate purchases from shipment frequency data
            purchases_from_shipments = self.generate_purchases_from_shipments(shipments)
            if not purchases_from_shipments.empty:
                # Store for combination later
                data['_purchases_from_shipments'] = purchases_from_shipments
        
        # Load monthly matrices
        monthly_data = self.load_monthly_matrices()
        
        # Combine purchases
        purchases_list = []
        if '_purchases_from_shipments' in data:
            purchases_list.append(data['_purchases_from_shipments'])
            del data['_purchases_from_shipments']
        if 'purchases' in monthly_data and not monthly_data['purchases'].empty:
            purchases_list.append(monthly_data['purchases'])
        if purchases_list:
            data['purchases'] = pd.concat(purchases_list, ignore_index=True) if len(purchases_list) > 1 else purchases_list[0]
        else:
            data['purchases'] = pd.DataFrame()
        
        # Combine sales
        if 'sales' in monthly_data and not monthly_data['sales'].empty:
            data['sales'] = monthly_data['sales']
        else:
            data['sales'] = pd.DataFrame()
        
        # Combine usage
        usage_list = []
        if 'usage' in monthly_data and not monthly_data['usage'].empty:
            usage_list.append(monthly_data['usage'])
        
        # Generate usage from sales if we have sales and recipe matrix
        if not data['sales'].empty and self.recipe_matrix is not None:
            usage_from_sales = self.generate_usage_from_sales_and_recipes(data['sales'])
            if not usage_from_sales.empty:
                usage_list.append(usage_from_sales)
        
        if usage_list:
            data['usage'] = pd.concat(usage_list, ignore_index=True) if len(usage_list) > 1 else usage_list[0]
        else:
            data['usage'] = pd.DataFrame()
        
        # Ensure all required DataFrames exist
        if 'ingredients' not in data:
            data['ingredients'] = pd.DataFrame()
        if 'shipments' not in data:
            data['shipments'] = pd.DataFrame()
        
        # Collect ALL unique ingredients from all data sources (before preprocessing)
        # This ensures we don't lose ingredients that exist in purchases/usage but not in recipe matrix
        all_ingredient_names = set()
        
        # Add ingredients from existing ingredients DataFrame
        if not data['ingredients'].empty and 'ingredient' in data['ingredients'].columns:
            all_ingredient_names.update(data['ingredients']['ingredient'].astype(str).str.strip())
        
        # Add ingredients from purchases
        if not data['purchases'].empty and 'ingredient' in data['purchases'].columns:
            all_ingredient_names.update(data['purchases']['ingredient'].astype(str).str.strip())
        
        # Add ingredients from usage
        if not data['usage'].empty and 'ingredient' in data['usage'].columns:
            all_ingredient_names.update(data['usage']['ingredient'].astype(str).str.strip())
        
        # Add ingredients from shipments
        if not data['shipments'].empty and 'ingredient' in data['shipments'].columns:
            all_ingredient_names.update(data['shipments']['ingredient'].astype(str).str.strip())
        
        # Remove empty strings and update ingredients DataFrame
        all_ingredient_names = {name for name in all_ingredient_names if name and name != 'nan' and str(name).strip() != ''}
        
        if all_ingredient_names:
            # Create or update ingredients DataFrame with all found ingredients
            if data['ingredients'].empty:
                # Create new DataFrame
                ingredients_df = pd.DataFrame({
                    'ingredient': sorted(list(all_ingredient_names))
                })
                ingredients_df['min_stock_level'] = 20
                ingredients_df['max_stock_level'] = 200
                ingredients_df['shelf_life_days'] = 14
                ingredients_df['unit'] = 'units'
                ingredients_df['category'] = 'Other'
                ingredients_df['storage_type'] = ingredients_df['ingredient'].apply(self._infer_storage_type_from_name)
                ingredients_df['storage_space_units'] = 1.0
                data['ingredients'] = ingredients_df
            else:
                # Add missing ingredients to existing DataFrame
                existing_ingredients = set(data['ingredients']['ingredient'].astype(str).str.strip())
                new_ingredients = all_ingredient_names - existing_ingredients
                if new_ingredients:
                    new_rows = pd.DataFrame({
                        'ingredient': sorted(list(new_ingredients))
                    })
                    new_rows['min_stock_level'] = 20
                    new_rows['max_stock_level'] = 200
                    new_rows['shelf_life_days'] = 14
                    new_rows['unit'] = 'units'
                    new_rows['category'] = 'Other'
                    new_rows['storage_type'] = new_rows['ingredient'].apply(self._infer_storage_type_from_name)
                    new_rows['storage_space_units'] = 1.0
                    data['ingredients'] = pd.concat([data['ingredients'], new_rows], ignore_index=True)
        
        # Apply preprocessing pipeline using DataPreprocessor
        if DataPreprocessor is not None:
            preprocessor = DataPreprocessor()
            data = preprocessor.preprocess_all(data)
            
            # Normalize ingredient names in the master list to match normalized purchases/usage
            if not data['ingredients'].empty and 'ingredient' in data['ingredients'].columns:
                data['ingredients']['ingredient'] = data['ingredients']['ingredient'].apply(
                    preprocessor.normalize_ingredient_name
                )
                # Remove duplicates after normalization
                data['ingredients'] = data['ingredients'].drop_duplicates(subset=['ingredient'], keep='first').reset_index(drop=True)
        else:
            # Fallback to basic normalization if preprocessor not available
            if not data['ingredients'].empty and 'ingredient' in data['ingredients'].columns:
                # Create a mapping of normalized names
                ingredient_master = data['ingredients']['ingredient'].str.strip().str.lower()
                
                # Normalize ingredient names in other dataframes
                for key in ['purchases', 'usage', 'shipments']:
                    if key in data and not data[key].empty and 'ingredient' in data[key].columns:
                        # Strip whitespace
                        data[key]['ingredient'] = data[key]['ingredient'].astype(str).str.strip()
                        
                        # Try to match ingredient names (case-insensitive, handle variations)
                        # Create a mapping for common variations
                        normalized = data[key]['ingredient'].str.lower()
                        
                        # Try to find matches in ingredient master list
                        # This helps with slight variations in naming
                        for idx, ing in enumerate(normalized):
                            # Check for exact match
                            if ing in ingredient_master.values:
                                continue
                            # Check for partial matches (e.g., "beef" matches "braised beef used (g)")
                            matches = ingredient_master[ingredient_master.str.contains(ing, na=False, case=False)]
                            if len(matches) > 0:
                                # Use the first match
                                data[key].iloc[idx, data[key].columns.get_loc('ingredient')] = matches.iloc[0]
        
        return data
