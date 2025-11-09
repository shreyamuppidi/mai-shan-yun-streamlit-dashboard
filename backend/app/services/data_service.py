"""
Data Service - Handles data loading and caching
"""
import pandas as pd
from pathlib import Path
from typing import Dict, Optional, Tuple, Any
import sys
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.data_loader import DataLoader

class DataService:
    """Service for loading and managing data"""
    
    def __init__(self, data_dir: str = "data"):
        self.data_dir = data_dir
        self._data_cache: Optional[Dict[str, pd.DataFrame]] = None
        self._loader = None
    
    def get_data_loader(self) -> DataLoader:
        """Get or create data loader"""
        if self._loader is None:
            self._loader = DataLoader(data_dir=self.data_dir)
        return self._loader
    
    def load_all_data(self, force_reload: bool = False) -> Dict[str, pd.DataFrame]:
        """Load all data files, with caching"""
        if self._data_cache is None or force_reload:
            loader = self.get_data_loader()
            self._data_cache = loader.load_all_data()
        return self._data_cache
    
    def get_data(self) -> Dict[str, pd.DataFrame]:
        """Get cached data or load if not available"""
        if self._data_cache is None:
            return self.load_all_data()
        return self._data_cache
    
    def clear_cache(self):
        """Clear data cache"""
        self._data_cache = None
    
    def merge_new_data(self, new_file_path: Path) -> Dict[str, Any]:
        """
        Merge new data from uploaded file with existing data.
        Appends new transactions and deduplicates based on date + ingredient/item.
        
        Returns:
            Dict with merge statistics (new_records, duplicates_skipped, etc.)
        """
        # Load existing data
        existing_data = self.get_data()
        
        # Load new data from the uploaded file
        # Use the same loader logic to parse the new file
        loader = self.get_data_loader()
        
        # Temporarily add the new file to data directory and reload
        # We'll parse it using MSYDataLoader if available
        try:
            from src.msy_data_loader import MSYDataLoader
            # MSYDataLoader expects the data directory path
            data_dir_path = Path(self.data_dir)
            msy_loader = MSYDataLoader(data_dir=str(data_dir_path))
            
            # Create a temporary loader with just this file
            # We need to parse it using the same logic as monthly matrices
            new_data = self._parse_uploaded_file(new_file_path, msy_loader)
        except ImportError:
            # Fallback to basic parsing
            new_data = self._parse_uploaded_file_basic(new_file_path)
        
        # Merge statistics
        merge_stats = {
            'purchases': {'new': 0, 'duplicates': 0},
            'sales': {'new': 0, 'duplicates': 0},
            'usage': {'new': 0, 'duplicates': 0}
        }
        
        # Merge purchases
        if 'purchases' in new_data and not new_data['purchases'].empty:
            existing_purchases = existing_data.get('purchases', pd.DataFrame())
            if existing_purchases.empty:
                existing_data['purchases'] = new_data['purchases']
                merge_stats['purchases']['new'] = len(new_data['purchases'])
            else:
                merged_purchases, stats = self._merge_dataframes(
                    existing_purchases, 
                    new_data['purchases'],
                    key_columns=['date', 'ingredient']
                )
                existing_data['purchases'] = merged_purchases
                merge_stats['purchases'] = stats
        
        # Merge sales
        if 'sales' in new_data and not new_data['sales'].empty:
            existing_sales = existing_data.get('sales', pd.DataFrame())
            if existing_sales.empty:
                existing_data['sales'] = new_data['sales']
                merge_stats['sales']['new'] = len(new_data['sales'])
            else:
                merged_sales, stats = self._merge_dataframes(
                    existing_sales,
                    new_data['sales'],
                    key_columns=['date', 'menu_item']
                )
                existing_data['sales'] = merged_sales
                merge_stats['sales'] = stats
        
        # Merge usage
        if 'usage' in new_data and not new_data['usage'].empty:
            existing_usage = existing_data.get('usage', pd.DataFrame())
            if existing_usage.empty:
                existing_data['usage'] = new_data['usage']
                merge_stats['usage']['new'] = len(new_data['usage'])
            else:
                merged_usage, stats = self._merge_dataframes(
                    existing_usage,
                    new_data['usage'],
                    key_columns=['date', 'ingredient', 'menu_item']
                )
                existing_data['usage'] = merged_usage
                merge_stats['usage'] = stats
        
        # Update cache
        self._data_cache = existing_data
        
        return {
            'success': True,
            'stats': merge_stats,
            'total_new_records': (
                merge_stats['purchases']['new'] +
                merge_stats['sales']['new'] +
                merge_stats['usage']['new']
            ),
            'total_duplicates': (
                merge_stats['purchases']['duplicates'] +
                merge_stats['sales']['duplicates'] +
                merge_stats['usage']['duplicates']
            )
        }
    
    def _parse_uploaded_file(self, file_path: Path, msy_loader) -> Dict[str, pd.DataFrame]:
        """Parse uploaded file using MSY loader logic"""
        result = {
            'purchases': pd.DataFrame(),
            'sales': pd.DataFrame(),
            'usage': pd.DataFrame()
        }
        
        if file_path.suffix.lower() == '.xlsx':
            # Parse as Excel file similar to monthly matrices
            try:
                xls = pd.ExcelFile(str(file_path))
                month_year = msy_loader._extract_month_year_from_filename(file_path.name)
                
                for sheet_name in xls.sheet_names:
                    try:
                        df = pd.read_excel(str(file_path), sheet_name=sheet_name, header=None)
                        
                        # Try matrix parsing
                        parsed_data = msy_loader._parse_matrix_sheet(df, sheet_name, month_year, file_path.stem)
                        if parsed_data:
                            if 'purchases' in parsed_data and parsed_data['purchases']:
                                result['purchases'] = pd.concat([result['purchases'], pd.DataFrame(parsed_data['purchases'])], ignore_index=True)
                            if 'sales' in parsed_data and parsed_data['sales']:
                                result['sales'] = pd.concat([result['sales'], pd.DataFrame(parsed_data['sales'])], ignore_index=True)
                            if 'usage' in parsed_data and parsed_data['usage']:
                                result['usage'] = pd.concat([result['usage'], pd.DataFrame(parsed_data['usage'])], ignore_index=True)
                        
                        # Try standard parsers
                        purchases = msy_loader._parse_purchase_sheet(df, file_path.stem)
                        if purchases is not None and not purchases.empty:
                            result['purchases'] = pd.concat([result['purchases'], purchases], ignore_index=True)
                        
                        sales = msy_loader._parse_sales_sheet(df, file_path.stem, month_year)
                        if sales is not None and not sales.empty:
                            result['sales'] = pd.concat([result['sales'], sales], ignore_index=True)
                        
                        usage = msy_loader._parse_usage_sheet(df, file_path.stem)
                        if usage is not None and not usage.empty:
                            result['usage'] = pd.concat([result['usage'], usage], ignore_index=True)
                    except Exception as e:
                        print(f"Warning: Could not parse sheet {sheet_name}: {str(e)}")
                        continue
            except Exception as e:
                print(f"Error parsing Excel file: {str(e)}")
        elif file_path.suffix.lower() == '.csv':
            # Try to parse as CSV (could be purchases, sales, or usage)
            try:
                df = pd.read_csv(str(file_path))
                # Try to infer type based on columns
                if 'ingredient' in df.columns and 'quantity' in df.columns:
                    if 'total_cost' in df.columns or 'cost' in df.columns:
                        result['purchases'] = df
                    elif 'quantity_used' in df.columns or 'used' in df.columns:
                        result['usage'] = df
                elif 'menu_item' in df.columns or 'item' in df.columns:
                    result['sales'] = df
            except Exception as e:
                print(f"Error parsing CSV file: {str(e)}")
        
        return result
    
    def _parse_uploaded_file_basic(self, file_path: Path) -> Dict[str, pd.DataFrame]:
        """Basic file parsing fallback"""
        result = {
            'purchases': pd.DataFrame(),
            'sales': pd.DataFrame(),
            'usage': pd.DataFrame()
        }
        
        try:
            if file_path.suffix.lower() == '.xlsx':
                df = pd.read_excel(str(file_path))
            elif file_path.suffix.lower() == '.csv':
                df = pd.read_csv(str(file_path))
            else:
                return result
            
            # Basic inference based on columns
            if 'ingredient' in df.columns and 'quantity' in df.columns:
                if 'total_cost' in df.columns or 'cost' in df.columns:
                    result['purchases'] = df
                else:
                    result['usage'] = df
            elif 'menu_item' in df.columns:
                result['sales'] = df
        except Exception as e:
            print(f"Error in basic parsing: {str(e)}")
        
        return result
    
    def _merge_dataframes(self, existing: pd.DataFrame, new: pd.DataFrame, key_columns: list) -> Tuple[pd.DataFrame, Dict]:
        """
        Merge two dataframes, deduplicating based on key columns.
        Returns merged dataframe and statistics.
        """
        if new.empty:
            return existing, {'new': 0, 'duplicates': 0}
        
        if existing.empty:
            return new, {'new': len(new), 'duplicates': 0}
        
        # Ensure key columns exist in both dataframes
        existing_keys = [col for col in key_columns if col in existing.columns]
        new_keys = [col for col in key_columns if col in new.columns]
        
        if not existing_keys or not new_keys:
            # If key columns don't match, just append
            merged = pd.concat([existing, new], ignore_index=True)
            return merged, {'new': len(new), 'duplicates': 0}
        
        # Create copies to avoid modifying originals
        existing_copy = existing.copy()
        new_copy = new.copy()
        
        # Normalize dates for comparison
        if 'date' in existing_keys and 'date' in new_copy.columns:
            existing_copy['date'] = pd.to_datetime(existing_copy['date']).dt.date
            new_copy['date'] = pd.to_datetime(new_copy['date']).dt.date
        
        # Create composite keys for deduplication
        existing_copy['_merge_key'] = existing_copy[existing_keys].apply(
            lambda row: '|'.join([str(row[col]) for col in existing_keys]), axis=1
        )
        new_copy['_merge_key'] = new_copy[new_keys].apply(
            lambda row: '|'.join([str(row[col]) for col in new_keys]), axis=1
        )
        
        # Find duplicates
        duplicates = new_copy[new_copy['_merge_key'].isin(existing_copy['_merge_key'])]
        new_records = new_copy[~new_copy['_merge_key'].isin(existing_copy['_merge_key'])]
        
        # Remove temporary key column from new_records
        if '_merge_key' in new_records.columns:
            new_records = new_records.drop(columns=['_merge_key'])
        
        # Merge
        merged = pd.concat([existing, new_records], ignore_index=True)
        
        stats = {
            'new': len(new_records),
            'duplicates': len(duplicates)
        }
        
        return merged, stats

