"""
Data Preprocessing Module
Centralized data cleaning, normalization, and validation for inventory management system
"""
import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
import warnings
warnings.filterwarnings('ignore')


class DataPreprocessor:
    """Centralized data preprocessing for inventory management"""
    
    def __init__(self):
        """Initialize preprocessor with canonical ingredient name mappings"""
        # Canonical ingredient name mappings (variations -> standard name)
        self.ingredient_mappings = {
            # Common variations
            'braised beef used (g)': 'Beef',
            'braised beef (g)': 'Beef',
            'Braised Beef(g)': 'Beef',  # Recipe matrix format
            'beef (g)': 'Beef',
            'braised chicken used (g)': 'Braised Chicken',
            'braised chicken (g)': 'Braised Chicken',
            'Braised Chicken(g)': 'Braised Chicken',  # Recipe matrix format
            'chicken (g)': 'Chicken',  # Keep raw chicken separate if it exists
            'braised pork used (g)': 'Braised Pork',
            'braised pork (g)': 'Braised Pork',
            'Braised Pork(g)': 'Braised Pork',  # Recipe matrix format
            'pork (g)': 'Pork',
            'boychoy(g)': 'Bokchoy',
            'Boychoy(g)': 'Bokchoy',  # Recipe matrix format
            'bokchoy (g)': 'Bokchoy',
            'bok choy (g)': 'Bokchoy',
            'pickle cabbage': 'Pickle Cabbage',
            'Pickle Cabbage': 'Pickle Cabbage',  # Recipe matrix format
            'pickled cabbage': 'Pickle Cabbage',
            'green onion': 'Green Onion',
            'Green Onion': 'Green Onion',  # Recipe matrix format
            'white onion': 'White Onion',
            'White onion': 'White Onion',  # Recipe matrix format
            # Carrot mappings (must come before combined mappings to avoid false matches)
            'Carrot(g)': 'Carrot',  # Recipe matrix format
            'carrot(g)': 'Carrot',
            'carrot': 'Carrot',  # Plain carrot
            # Peas mappings
            'Peas(g)': 'Peas',  # Recipe matrix format
            'peas(g)': 'Peas',
            'peas': 'Peas',  # Plain peas
            # Combined mappings (must come after individual mappings)
            'peas + carrot': 'Peas',  # Map combined purchases to Peas (will be split before normalization)
            'peas and carrot': 'Peas',
            'rice(g)': 'Rice',
            'Rice(g)': 'Rice',  # Recipe matrix format
            'rice noodles': 'Rice Noodles',
            'Rice Noodles(g)': 'Rice Noodles',  # Recipe matrix format
            'rice noodle': 'Rice Noodles',
            'ramen (count)': 'Ramen',
            'Ramen (count)': 'Ramen',  # Recipe matrix format
            'ramen (g)': 'Ramen',
            'ramen': 'Ramen',
            'egg (count)': 'Egg',
            'Egg(count)': 'Egg',  # Recipe matrix format
            'egg(count)': 'Egg',
            'eggs': 'Egg',
            'chicken wings': 'Chicken Wings',
            'Chicken Wings (pcs)': 'Chicken Wings',  # Recipe matrix format
            'chicken wings (pcs)': 'Chicken Wings',
            'wing': 'Chicken Wings',
            'wings': 'Chicken Wings',
            'chicken thigh (pcs)': 'Chicken Thigh',  # Recipe matrix format
            'chicken thigh': 'Chicken Thigh',
            'tapioca starch': 'Tapioca Starch',
            'Tapioca Starch': 'Tapioca Starch',  # Recipe matrix format
            'flour': 'Flour',
            'flour (g)': 'Flour',  # Recipe matrix format
        }
        
        # Count-based ingredient keywords
        self.count_keywords = ['wing', 'ramen', 'egg', 'count', 'pcs', 'piece', 'roll', 'whole', 'noodle']
        
        # Standard unit mappings
        self.unit_mappings = {
            'pound': 'lb',
            'pounds': 'lb',
            'lbs': 'lb',
            'ounce': 'oz',
            'ounces': 'oz',
            'gram': 'g',
            'grams': 'g',
            'kilogram': 'kg',
            'kilograms': 'kg',
            'unit': 'units',
            'units': 'units',
        }
    
    def normalize_ingredient_name(self, name: str) -> str:
        """
        Normalize ingredient name for consistent matching.
        
        Args:
            name: Raw ingredient name
            
        Returns:
            Normalized ingredient name
        """
        if pd.isna(name) or name == '':
            return ""
        
        name = str(name).strip()
        
        # Check canonical mappings first
        name_lower = name.lower()
        for variation, canonical in self.ingredient_mappings.items():
            variation_lower = variation.lower()
            # Exact match first (most precise)
            if name_lower == variation_lower:
                return canonical
            # For substring matching, only match if the variation is longer (to avoid false matches like "carrot" matching "peas + carrot")
            # This handles cases like "braised chicken (g)" matching "braised chicken"
            if len(variation_lower) > len(name_lower) and name_lower in variation_lower:
                return canonical
            # Also handle reverse: if name is longer and contains variation (e.g., "braised chicken used (g)" contains "braised chicken (g)")
            if len(name_lower) > len(variation_lower) and variation_lower in name_lower:
                return canonical
        
        # Remove common units and descriptors
        name_cleaned = name
        suffixes = [
            ' (g)', '(g)', ' (G)', '(G)',
            ' (count)', '(count)', ' (Count)', '(Count)',
            ' used', ' Used', ' USED',
            ' used (g)', ' Used (g)',
            ' (kg)', '(kg)', ' (KG)', '(KG)',
            ' (lb)', '(lb)', ' (LB)', '(LB)',
            ' (oz)', '(oz)', ' (OZ)', '(OZ)',
            ' (pcs)', '(pcs)', ' (PCS)', '(PCS)',
        ]
        for suffix in suffixes:
            name_cleaned = name_cleaned.replace(suffix, '')
        
        # Normalize compound names (handle "Peas + Carrot", "Peas and Carrot")
        name_cleaned = name_cleaned.replace(' and ', '+').replace(' And ', '+').replace(' AND ', '+')
        
        # Remove extra whitespace
        name_cleaned = ' '.join(name_cleaned.split())
        
        # Capitalize first letter of each word (title case)
        if name_cleaned:
            words = name_cleaned.split()
            name_cleaned = ' '.join(word.capitalize() for word in words)
        
        return name_cleaned if name_cleaned else name
    
    def is_count_based_ingredient(self, ingredient: str, unit: str = None) -> bool:
        """
        Check if ingredient is count-based (pieces, rolls, eggs, ramen, noodles) vs weight-based.
        
        Args:
            ingredient: Ingredient name
            unit: Unit string (optional)
            
        Returns:
            True if count-based, False if weight-based
        """
        ingredient_lower = str(ingredient).lower() if ingredient else ""
        unit_lower = str(unit).lower() if unit and pd.notna(unit) else ""
        
        # Check unit for count keywords
        if any(keyword in unit_lower for keyword in self.count_keywords):
            return True
        
        # Check ingredient name for count keywords
        count_ingredient_keywords = ['wing', 'ramen', 'egg', 'noodle']
        if any(keyword in ingredient_lower for keyword in count_ingredient_keywords):
            return True
        
        return False
    
    def detect_and_standardize_unit(self, ingredient: str, unit: str = None, column_name: str = None) -> str:
        """
        Detect and standardize unit for an ingredient.
        For count-based ingredients, override to 'count' even if column says '(g)'.
        
        Args:
            ingredient: Ingredient name
            unit: Current unit (optional)
            column_name: Column name that might contain unit info (optional)
            
        Returns:
            Standardized unit string
        """
        # Check if count-based first (this takes priority)
        if self.is_count_based_ingredient(ingredient, unit):
            return 'count'
        
        # Extract unit from column name if provided
        if column_name:
            col_lower = str(column_name).lower()
            if '(g)' in col_lower or ' (g)' in col_lower:
                unit = 'g'
            elif '(count)' in col_lower or ' (count)' in col_lower:
                unit = 'count'
            elif '(lb)' in col_lower or ' (lb)' in col_lower:
                unit = 'lb'
            elif '(oz)' in col_lower or ' (oz)' in col_lower:
                unit = 'oz'
            elif '(kg)' in col_lower or ' (kg)' in col_lower:
                unit = 'kg'
        
        # Standardize unit name
        if unit:
            unit_lower = str(unit).lower().strip()
            if unit_lower in self.unit_mappings:
                return self.unit_mappings[unit_lower]
            # Return as-is if already standard
            if unit_lower in ['g', 'kg', 'lb', 'oz', 'count', 'units']:
                return unit_lower
        
        # Default to 'units' if not count-based and no unit detected
        return 'units'
    
    def preprocess_purchases(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Preprocess purchases DataFrame.
        
        Args:
            df: Raw purchases DataFrame
            
        Returns:
            Cleaned purchases DataFrame
        """
        if df.empty:
            return df.copy()
        
        df = df.copy()
        
        # Normalize ingredient names
        if 'ingredient' in df.columns:
            # First, handle combined ingredients like "Peas+Carrot" by splitting them
            combined_rows = []
            rows_to_drop = []
            
            for idx, row in df.iterrows():
                ingredient = str(row.get('ingredient', '')).strip()
                ingredient_lower = ingredient.lower()
                
                # Check if this is a combined ingredient that should be split
                if 'peas' in ingredient_lower and 'carrot' in ingredient_lower:
                    # Split into separate Peas and Carrot rows
                    quantity = pd.to_numeric(row.get('quantity', 0), errors='coerce') or 0
                    # Split 50/50 (or we could use recipe proportions, but 50/50 is simplest)
                    peas_qty = quantity / 2
                    carrot_qty = quantity / 2
                    
                    # Create new rows for Peas and Carrot
                    peas_row = row.copy()
                    peas_row['ingredient'] = 'Peas'
                    peas_row['quantity'] = peas_qty
                    if 'total_cost' in row:
                        peas_row['total_cost'] = row.get('total_cost', 0) / 2
                    combined_rows.append(peas_row)
                    
                    carrot_row = row.copy()
                    carrot_row['ingredient'] = 'Carrot'
                    carrot_row['quantity'] = carrot_qty
                    if 'total_cost' in row:
                        carrot_row['total_cost'] = row.get('total_cost', 0) / 2
                    combined_rows.append(carrot_row)
                    
                    rows_to_drop.append(idx)
            
            # Add the split rows
            if combined_rows:
                split_df = pd.DataFrame(combined_rows)
                df = pd.concat([df, split_df], ignore_index=True)
                # Remove original combined rows
                if rows_to_drop:
                    df = df.drop(index=rows_to_drop).reset_index(drop=True)
            
            # Now normalize all ingredient names
            df['ingredient'] = df['ingredient'].apply(self.normalize_ingredient_name)
        
        # Ensure date is datetime
        if 'date' in df.columns:
            df['date'] = pd.to_datetime(df['date'], errors='coerce')
            # Remove rows with invalid dates
            df = df[df['date'].notna()]
        
        # Convert quantities to numeric
        if 'quantity' in df.columns:
            df['quantity'] = pd.to_numeric(df['quantity'], errors='coerce').fillna(0)
            # Round count-based ingredients to whole numbers
            if 'ingredient' in df.columns:
                df['quantity'] = df.apply(
                    lambda row: round(row['quantity']) if self.is_count_based_ingredient(row['ingredient']) else row['quantity'],
                    axis=1
                )
            # Remove rows with zero or negative quantities
            df = df[df['quantity'] > 0]
        
        # Handle costs
        if 'total_cost' in df.columns:
            df['total_cost'] = pd.to_numeric(df['total_cost'], errors='coerce').fillna(0)
            df['total_cost'] = df['total_cost'].clip(lower=0)  # Ensure non-negative
        
        # Normalize supplier names
        if 'supplier' in df.columns:
            df['supplier'] = df['supplier'].astype(str).str.strip()
        
        return df
    
    def preprocess_usage(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Preprocess usage DataFrame.
        
        Args:
            df: Raw usage DataFrame
            
        Returns:
            Cleaned usage DataFrame
        """
        if df.empty:
            return df.copy()
        
        df = df.copy()
        
        # Normalize ingredient names
        if 'ingredient' in df.columns:
            df['ingredient'] = df['ingredient'].apply(self.normalize_ingredient_name)
        
        # Ensure date is datetime
        if 'date' in df.columns:
            df['date'] = pd.to_datetime(df['date'], errors='coerce')
            df = df[df['date'].notna()]
        
        # Convert quantities to numeric
        if 'quantity_used' in df.columns:
            df['quantity_used'] = pd.to_numeric(df['quantity_used'], errors='coerce').fillna(0)
            # Round count-based ingredients to whole numbers
            if 'ingredient' in df.columns:
                df['quantity_used'] = df.apply(
                    lambda row: round(row['quantity_used']) if self.is_count_based_ingredient(row['ingredient']) else row['quantity_used'],
                    axis=1
                )
            # Remove rows with zero or negative quantities
            df = df[df['quantity_used'] > 0]
        
        # Normalize menu_item names (optional field)
        if 'menu_item' in df.columns:
            df['menu_item'] = df['menu_item'].astype(str).str.strip()
            df['menu_item'] = df['menu_item'].replace('nan', '')
        
        return df
    
    def preprocess_sales(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Preprocess sales DataFrame.
        
        Args:
            df: Raw sales DataFrame
            
        Returns:
            Cleaned sales DataFrame
        """
        if df.empty:
            return df.copy()
        
        df = df.copy()
        
        # Ensure date is datetime
        if 'date' in df.columns:
            df['date'] = pd.to_datetime(df['date'], errors='coerce')
            df = df[df['date'].notna()]
        
        # Normalize menu_item names
        if 'menu_item' in df.columns:
            df['menu_item'] = df['menu_item'].astype(str).str.strip()
            df['menu_item'] = df['menu_item'].replace('nan', '')
            # Remove rows with empty menu items
            df = df[df['menu_item'] != '']
        
        # Convert quantities to numeric
        if 'quantity_sold' in df.columns:
            df['quantity_sold'] = pd.to_numeric(df['quantity_sold'], errors='coerce').fillna(0)
            df['quantity_sold'] = df['quantity_sold'].round()  # Sales are always whole numbers
            df = df[df['quantity_sold'] > 0]
        
        # Handle revenue and price
        if 'revenue' in df.columns:
            df['revenue'] = pd.to_numeric(df['revenue'], errors='coerce').fillna(0)
            df['revenue'] = df['revenue'].clip(lower=0)
        
        if 'price' in df.columns:
            df['price'] = pd.to_numeric(df['price'], errors='coerce').fillna(0)
            df['price'] = df['price'].clip(lower=0)
        
        return df
    
    def preprocess_shipments(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Preprocess shipments DataFrame.
        
        Args:
            df: Raw shipments DataFrame
            
        Returns:
            Cleaned shipments DataFrame
        """
        if df.empty:
            return df.copy()
        
        df = df.copy()
        
        # Normalize ingredient names
        if 'ingredient' in df.columns:
            df['ingredient'] = df['ingredient'].apply(self.normalize_ingredient_name)
        
        # Handle date if present (shipments may be frequency-based)
        if 'date' in df.columns:
            df['date'] = pd.to_datetime(df['date'], errors='coerce')
            # Don't drop rows with missing dates (frequency-based shipments don't have dates)
        
        # Handle expected_date if present
        if 'expected_date' in df.columns:
            df['expected_date'] = pd.to_datetime(df['expected_date'], errors='coerce')
        
        # Convert quantities to numeric
        if 'quantity' in df.columns:
            df['quantity'] = pd.to_numeric(df['quantity'], errors='coerce').fillna(0)
            # Round count-based ingredients
            if 'ingredient' in df.columns:
                df['quantity'] = df.apply(
                    lambda row: round(row['quantity']) if self.is_count_based_ingredient(row['ingredient']) else row['quantity'],
                    axis=1
                )
        
        # Normalize frequency
        if 'frequency' in df.columns:
            df['frequency'] = df['frequency'].astype(str).str.strip().str.lower()
        
        # Normalize unit
        if 'Unit of shipment' in df.columns:
            df['Unit of shipment'] = df.apply(
                lambda row: self.detect_and_standardize_unit(
                    row.get('ingredient', ''),
                    row.get('Unit of shipment', '')
                ),
                axis=1
            )
        
        return df
    
    def preprocess_ingredients(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Preprocess ingredients DataFrame.
        
        Note: We do NOT normalize ingredient names here to preserve all unique ingredients.
        Normalization happens only when matching ingredients across DataFrames.
        
        Args:
            df: Raw ingredients DataFrame
            
        Returns:
            Cleaned ingredients DataFrame
        """
        if df.empty:
            return df.copy()
        
        df = df.copy()
        
        # Clean ingredient names (strip whitespace, but don't normalize to avoid merging distinct ingredients)
        if 'ingredient' in df.columns:
            df['ingredient'] = df['ingredient'].astype(str).str.strip()
            # Remove duplicates based on exact name match only (case-insensitive)
            # Create a temporary column for case-insensitive comparison
            df['_ingredient_lower'] = df['ingredient'].str.lower()
            df = df.drop_duplicates(subset=['_ingredient_lower'], keep='first', ignore_index=True)
            df = df.drop(columns=['_ingredient_lower'])
        
        # Standardize units
        if 'unit' in df.columns:
            df['unit'] = df.apply(
                lambda row: self.detect_and_standardize_unit(
                    row.get('ingredient', ''),
                    row.get('unit', '')
                ),
                axis=1
            )
        
        # Ensure numeric columns are numeric
        numeric_cols = ['min_stock_level', 'max_stock_level', 'shelf_life_days', 'storage_space_units']
        for col in numeric_cols:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce')
                if col in ['min_stock_level', 'max_stock_level', 'shelf_life_days']:
                    df[col] = df[col].fillna(20 if 'stock_level' in col else 14)
                    df[col] = df[col].clip(lower=0)
        
        return df
    
    def validate_data_quality(self, data: Dict[str, pd.DataFrame]) -> Dict[str, List[str]]:
        """
        Validate data quality and return warnings.
        
        Args:
            data: Dictionary of DataFrames
            
        Returns:
            Dictionary of warnings by DataFrame key
        """
        warnings = {}
        
        for key, df in data.items():
            if df.empty:
                continue
            
            df_warnings = []
            
            # Check required columns
            required_cols = {
                'purchases': ['date', 'ingredient', 'quantity'],
                'usage': ['date', 'ingredient', 'quantity_used'],
                'sales': ['date', 'menu_item', 'quantity_sold'],
                'shipments': ['ingredient'],
                'ingredients': ['ingredient'],
            }
            
            if key in required_cols:
                missing_cols = [col for col in required_cols[key] if col not in df.columns]
                if missing_cols:
                    df_warnings.append(f"Missing required columns: {', '.join(missing_cols)}")
            
            # Check for duplicate entries
            if 'date' in df.columns and 'ingredient' in df.columns:
                duplicates = df.duplicated(subset=['date', 'ingredient']).sum()
                if duplicates > 0:
                    df_warnings.append(f"Found {duplicates} duplicate date+ingredient entries")
            
            # Check date ranges
            if 'date' in df.columns:
                dates = pd.to_datetime(df['date'], errors='coerce')
                valid_dates = dates.dropna()
                if not valid_dates.empty:
                    max_date = valid_dates.max()
                    future_buffer = datetime.now() + timedelta(days=90)
                    if max_date > future_buffer:
                        df_warnings.append(f"Found dates beyond 90 days in future: {max_date.date()}")
            
            # Check for suspicious values
            if 'quantity' in df.columns:
                qty_col = pd.to_numeric(df['quantity'], errors='coerce')
                if qty_col.max() > 100000:
                    df_warnings.append(f"Suspiciously high quantity: {qty_col.max()}")
            
            if 'quantity_used' in df.columns:
                qty_col = pd.to_numeric(df['quantity_used'], errors='coerce')
                if qty_col.max() > 100000:
                    df_warnings.append(f"Suspiciously high quantity_used: {qty_col.max()}")
            
            if df_warnings:
                warnings[key] = df_warnings
        
        return warnings
    
    def preprocess_all(self, data: Dict[str, pd.DataFrame]) -> Dict[str, pd.DataFrame]:
        """
        Preprocess all DataFrames in the data dictionary.
        
        Args:
            data: Dictionary of DataFrames to preprocess
            
        Returns:
            Dictionary of preprocessed DataFrames
        """
        preprocessed = {}
        
        # Preprocess each DataFrame type
        if 'purchases' in data:
            preprocessed['purchases'] = self.preprocess_purchases(data['purchases'])
        
        if 'usage' in data:
            preprocessed['usage'] = self.preprocess_usage(data['usage'])
        
        if 'sales' in data:
            preprocessed['sales'] = self.preprocess_sales(data['sales'])
        
        if 'shipments' in data:
            preprocessed['shipments'] = self.preprocess_shipments(data['shipments'])
        
        if 'ingredients' in data:
            preprocessed['ingredients'] = self.preprocess_ingredients(data['ingredients'])
        
        # Keep other keys as-is
        for key, value in data.items():
            if key not in preprocessed:
                preprocessed[key] = value
        
        # Validate data quality
        quality_warnings = self.validate_data_quality(preprocessed)
        if quality_warnings:
            print("Data Quality Warnings:")
            for key, warnings in quality_warnings.items():
                print(f"  {key}: {', '.join(warnings)}")
        
        return preprocessed

