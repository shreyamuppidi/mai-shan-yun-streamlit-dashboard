"""
API Routes for Mai Shan Yun Dashboard
"""
from fastapi import APIRouter, HTTPException, Query, Body, UploadFile, File
from fastapi.responses import JSONResponse
from typing import Optional, Dict, Any
import pandas as pd
import json
from pathlib import Path
from datetime import datetime
import os

from app.dependencies import analytics_service, data_service, chatbot_service

router = APIRouter()

def dataframe_to_dict(df: pd.DataFrame) -> list:
    """Convert DataFrame to list of dicts, handling datetime and NaN"""
    if df.empty:
        return []
    
    # Convert datetime columns to strings
    df = df.copy()
    for col in df.columns:
        if pd.api.types.is_datetime64_any_dtype(df[col]):
            df[col] = df[col].dt.strftime('%Y-%m-%d')
    
    # Replace NaN with None
    df = df.where(pd.notnull(df), None)
    
    return df.to_dict('records')

@router.get("/overview")
async def get_overview():
    """Get overview dashboard data"""
    try:
        analytics = analytics_service.get_analytics()
        data = analytics_service.get_data()
        
        inventory = analytics.calculate_inventory_levels()
        
        # Handle empty inventory
        if inventory.empty or 'stock_status' not in inventory.columns:
            return {
                "metrics": {
                    "total_ingredients": 0,
                    "low_stock": 0,
                    "high_stock": 0,
                    "reorder_count": 0,
                    "menu_viability": None
                },
                "status_distribution": {},
                "critical_stockout": [],
                "top_stock": [],
                "top_risks": [],
                "recent_purchases": [],
                "recent_usage": []
            }
        
        # Calculate metrics
        total_ingredients = len(inventory)
        low_stock = len(inventory[inventory['stock_status'] == 'Low']) if 'stock_status' in inventory.columns else 0
        high_stock = len(inventory[inventory['stock_status'] == 'High']) if 'stock_status' in inventory.columns else 0
        reorder_count = int(inventory['reorder_needed'].sum()) if 'reorder_needed' in inventory.columns else 0
        
        try:
            menu_viability = analytics.calculate_menu_viability_score()
        except:
            menu_viability = None
        
        # Status distribution
        status_counts = inventory['stock_status'].value_counts().to_dict() if 'stock_status' in inventory.columns else {}
        
        # Critical stockout items
        critical_stockout = pd.DataFrame()
        if 'days_until_stockout' in inventory.columns:
            critical_stockout = inventory[inventory['days_until_stockout'] < 30].copy()
            if not critical_stockout.empty:
                critical_stockout = critical_stockout.sort_values('days_until_stockout').head(10)
        
        # Top stock items
        top_stock = pd.DataFrame()
        if 'current_stock' in inventory.columns:
            top_stock = inventory.nlargest(10, 'current_stock')
            if 'stock_status' in top_stock.columns:
                top_stock = top_stock[['ingredient', 'current_stock', 'stock_status']]
            else:
                top_stock = top_stock[['ingredient', 'current_stock']] if 'ingredient' in top_stock.columns else pd.DataFrame()
        
        # Risk alerts preview
        try:
            risk_alerts = analytics.calculate_risk_alerts()
            top_risks = risk_alerts.head(10) if not risk_alerts.empty else pd.DataFrame()
        except:
            top_risks = pd.DataFrame()
        
        # Recent purchases
        recent_purchases = pd.DataFrame()
        if 'purchases' in data and not data['purchases'].empty and 'date' in data['purchases'].columns:
            recent_purchases = data['purchases'].nlargest(10, 'date').copy()
            # Estimate missing costs if total_cost is 0
            if 'total_cost' in recent_purchases.columns:
                recent_purchases = analytics._estimate_missing_costs(recent_purchases)
            if all(col in recent_purchases.columns for col in ['date', 'ingredient', 'quantity', 'total_cost']):
                recent_purchases = recent_purchases[['date', 'ingredient', 'quantity', 'total_cost']].copy()
        
        # Recent usage
        recent_usage = pd.DataFrame()
        if 'usage' in data and not data['usage'].empty and 'date' in data['usage'].columns:
            recent_usage = data['usage'].nlargest(10, 'date')
            if 'menu_item' in recent_usage.columns:
                if all(col in recent_usage.columns for col in ['date', 'ingredient', 'quantity_used', 'menu_item']):
                    recent_usage = recent_usage[['date', 'ingredient', 'quantity_used', 'menu_item']].copy()
            else:
                if all(col in recent_usage.columns for col in ['date', 'ingredient', 'quantity_used']):
                    recent_usage = recent_usage[['date', 'ingredient', 'quantity_used']].copy()
        
        return {
            "metrics": {
                "total_ingredients": total_ingredients,
                "low_stock": low_stock,
                "high_stock": high_stock,
                "reorder_count": reorder_count,
                "menu_viability": menu_viability
            },
            "status_distribution": status_counts,
            "critical_stockout": dataframe_to_dict(critical_stockout),
            "top_stock": dataframe_to_dict(top_stock),
            "top_risks": dataframe_to_dict(top_risks),
            "recent_purchases": dataframe_to_dict(recent_purchases),
            "recent_usage": dataframe_to_dict(recent_usage)
        }
    except Exception as e:
        import traceback
        error_detail = f"{str(e)}\n{traceback.format_exc()}"
        raise HTTPException(status_code=500, detail=error_detail)

@router.get("/inventory")
async def get_inventory():
    """Get inventory levels"""
    try:
        analytics = analytics_service.get_analytics()
        inventory = analytics.calculate_inventory_levels()
        return {"data": dataframe_to_dict(inventory)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/risk-alerts")
async def get_risk_alerts():
    """Get risk alerts"""
    try:
        analytics = analytics_service.get_analytics()
        risk_alerts = analytics.calculate_risk_alerts()
        
        if risk_alerts.empty:
            return {"data": [], "summary": {}}
        
        high_risk = len(risk_alerts[risk_alerts['risk_score'] >= 50])
        needs_reorder = int(risk_alerts['needs_reorder'].sum())
        overstock = len(risk_alerts[risk_alerts['risk_type'].str.contains('Overstock', na=False)])
        avg_risk_score = float(risk_alerts['risk_score'].mean())
        
        return {
            "data": dataframe_to_dict(risk_alerts),
            "summary": {
                "high_risk_items": high_risk,
                "needs_reorder": needs_reorder,
                "overstocked_items": overstock,
                "avg_risk_score": avg_risk_score
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/usage-trends")
async def get_usage_trends(
    ingredient: Optional[str] = Query(None),
    period: str = Query("monthly", regex="^(daily|weekly|monthly)$")
):
    """Get usage trends"""
    try:
        analytics = analytics_service.get_analytics()
        trends = analytics.get_usage_trends(ingredient=ingredient, period=period)
        
        # Get top ingredients
        top_usage = analytics.get_top_ingredients(metric='usage', limit=10, period_days=30)
        
        return {
            "trends": dataframe_to_dict(trends),
            "top_ingredients": dataframe_to_dict(top_usage)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/forecast")
async def get_forecast(
    ingredient: str = Query(...),
    days_ahead: int = Query(30, ge=7, le=90),
    method: str = Query("moving_average", regex="^(moving_average|linear_trend)$"),
    include_seasonality: bool = Query(True),
    include_holidays: bool = Query(True)
):
    """Get demand forecast"""
    try:
        analytics = analytics_service.get_analytics()
        forecast = analytics.forecast_demand(ingredient, days_ahead=days_ahead, method=method)
        
        if include_seasonality or include_holidays:
            forecast = analytics.adjust_forecast_for_events(ingredient, forecast)
        
        # Get historical trends
        trends = analytics.get_usage_trends(ingredient=ingredient, period='daily')
        
        # Seasonality info
        seasonality_info = None
        if include_seasonality:
            try:
                seasonality = analytics.detect_seasonality(ingredient)
                if seasonality and seasonality.get('has_seasonality', False):
                    # Convert numpy types to Python types for JSON serialization
                    seasonality_info = {
                        'seasonal_factors': {int(k): float(v) for k, v in seasonality.get('seasonal_factors', {}).items()},
                        'peak_month': int(seasonality.get('peak_month', 0)),
                        'low_month': int(seasonality.get('low_month', 0)),
                        'peak_factor': float(seasonality.get('peak_factor', 1.0)),
                        'low_factor': float(seasonality.get('low_factor', 1.0)),
                        'has_seasonality': bool(seasonality.get('has_seasonality', False))
                    }
            except Exception as e:
                # If seasonality detection fails, continue without it
                print(f"Warning: Could not get seasonality info: {str(e)}")
                seasonality_info = None
        
        return {
            "forecast": dataframe_to_dict(forecast),
            "historical": dataframe_to_dict(trends),
            "seasonality": seasonality_info,
            "summary": {
                "avg_forecast": float(forecast['forecasted_usage'].mean()) if not forecast.empty else 0,
                "total_forecast": float(forecast['forecasted_usage'].sum()) if not forecast.empty else 0,
                "max_forecast": float(forecast['forecasted_usage'].max()) if not forecast.empty else 0
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/menu-forecast")
async def get_menu_forecast(
    ingredient: str = Query(...),
    days_ahead: int = Query(30, ge=7, le=90)
):
    """Get menu-driven forecast"""
    try:
        analytics = analytics_service.get_analytics()
        forecast = analytics.forecast_by_menu_trends(ingredient, days_ahead=days_ahead)
        
        # Get impact scores
        impact_scores = analytics.calculate_ingredient_impact_score()
        ingredient_impact = impact_scores[impact_scores['ingredient'] == ingredient].copy() if not impact_scores.empty else pd.DataFrame()
        ingredient_impact = ingredient_impact.sort_values('impact_score', ascending=False)
        
        # Determine if ingredient is count-based
        from src.data_preprocessor import DataPreprocessor
        preprocessor = DataPreprocessor()
        is_count_based = preprocessor.is_count_based_ingredient(ingredient)
        unit = 'count' if is_count_based else 'g'  # Default to grams for weight-based
        
        return {
            "forecast": dataframe_to_dict(forecast),
            "unit": unit,
            "is_count_based": is_count_based,
            "impact_scores": dataframe_to_dict(ingredient_impact),
            "summary": {
                "daily_forecast": float(forecast['forecasted_usage'].iloc[0]) if not forecast.empty else 0,
                "total_forecast": float(forecast['forecasted_usage'].sum()) if not forecast.empty else 0,
                "avg_forecast": float(forecast['forecasted_usage'].mean()) if not forecast.empty else 0
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/recipe-mapper")
async def get_recipe_mapper():
    """Get recipe mapper data"""
    try:
        analytics = analytics_service.get_analytics()
        menu_viability = analytics.map_recipes_to_inventory()
        menu_viability_score = analytics.calculate_menu_viability_score()
        
        can_make = menu_viability[menu_viability['servings_possible'] > 0] if not menu_viability.empty else pd.DataFrame()
        cannot_make = menu_viability[menu_viability['servings_possible'] == 0] if not menu_viability.empty else pd.DataFrame()
        
        return {
            "viability_score": menu_viability_score,
            "data": dataframe_to_dict(menu_viability),
            "can_make_count": len(can_make),
            "cannot_make_count": len(cannot_make)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/shipments")
async def get_shipments():
    """Get shipment analysis"""
    try:
        analytics = analytics_service.get_analytics()
        data = analytics_service.get_data()
        
        delay_analysis = analytics.analyze_shipment_delays()
        supplier_reliability = analytics.track_supplier_reliability()
        
        shipments = data.get('shipments', pd.DataFrame())
        
        return {
            "delay_analysis": dataframe_to_dict(delay_analysis),
            "supplier_reliability": dataframe_to_dict(supplier_reliability),
            "shipments": dataframe_to_dict(shipments)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/cost-analysis")
async def get_cost_analysis(period_days: int = Query(30, ge=7, le=365)):
    """Get cost analysis"""
    try:
        analytics = analytics_service.get_analytics()
        cost_analysis = analytics.get_cost_analysis(period_days=period_days)
        
        top_cost = analytics.get_top_ingredients(metric='cost', limit=15, period_days=period_days)
        
        return {
            "summary": cost_analysis,
            "top_ingredients": dataframe_to_dict(top_cost)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/waste")
async def get_waste(period_days: int = Query(30, ge=7, le=365)):
    """Get waste analysis"""
    try:
        analytics = analytics_service.get_analytics()
        waste_analysis = analytics.calculate_waste_analysis(period_days=period_days)
        heatmap_data = analytics.get_cost_waste_heatmap_data(period_days=period_days)
        
        return {
            "waste_analysis": dataframe_to_dict(waste_analysis),
            "heatmap_data": dataframe_to_dict(heatmap_data)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/storage")
async def get_storage(days_ahead: int = Query(7, ge=1, le=30)):
    """Get storage estimator"""
    try:
        analytics = analytics_service.get_analytics()
        storage_load = analytics.estimate_storage_load(days_ahead=days_ahead)
        
        return {
            "data": dataframe_to_dict(storage_load),
            "summary": {
                "total_current_load": float(storage_load['current_load'].sum()) if not storage_load.empty else 0,
                "total_incoming_load": float(storage_load['incoming_load'].sum()) if not storage_load.empty else 0,
                "overloaded_count": int(storage_load['is_overloaded'].sum()) if not storage_load.empty else 0
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/reorder")
async def get_reorder(include_seasonality: bool = Query(True)):
    """Get reorder recommendations"""
    try:
        analytics = analytics_service.get_analytics()
        recommendations = analytics.calculate_reorder_recommendations(include_seasonality=include_seasonality)
        
        if recommendations.empty:
            return {"data": [], "summary": {}}
        
        critical = len(recommendations[recommendations['urgency'] == 'Critical'])
        high = len(recommendations[recommendations['urgency'] == 'High'])
        medium = len(recommendations[recommendations['urgency'] == 'Medium'])
        total_reorder = float(recommendations['recommended_order_quantity'].sum())
        
        return {
            "data": dataframe_to_dict(recommendations),
            "summary": {
                "critical": critical,
                "high": high,
                "medium": medium,
                "total_recommended_order": total_reorder
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/simulate")
async def simulate_scenario(scenario: Dict[str, Any] = Body(...)):
    """Run what-if simulation"""
    try:
        analytics = analytics_service.get_analytics()
        simulation_results = analytics.simulate_scenario(scenario)
        
        if simulation_results.empty:
            return {"data": [], "summary": {}}
        
        # Check if required columns exist before accessing them
        if 'stock_change' not in simulation_results.columns:
            return {"data": dataframe_to_dict(simulation_results), "summary": {}}
        
        avg_stock_change = float(simulation_results['stock_change'].mean()) if 'stock_change' in simulation_results.columns else 0.0
        items_affected = len(simulation_results[simulation_results['stock_change'] != 0]) if 'stock_change' in simulation_results.columns else 0
        items_low_stock = len(simulation_results[simulation_results['days_until_stockout_simulated'] < 7]) if 'days_until_stockout_simulated' in simulation_results.columns else 0
        avg_days_change = float(simulation_results['days_change'].mean()) if 'days_change' in simulation_results.columns else 0.0
        
        return {
            "data": dataframe_to_dict(simulation_results),
            "summary": {
                "avg_stock_change": avg_stock_change,
                "items_affected": items_affected,
                "items_low_stock": items_low_stock,
                "avg_days_change": avg_days_change
            }
        }
    except Exception as e:
        import traceback
        error_detail = f"{str(e)}\n{traceback.format_exc()}"
        raise HTTPException(status_code=500, detail=error_detail)

@router.get("/ingredients")
async def get_ingredients():
    """Get list of all available ingredients"""
    try:
        analytics = analytics_service.get_analytics()
        data = analytics_service.get_data()
        
        # Get ingredients from inventory levels
        inventory = analytics.calculate_inventory_levels()
        ingredients = []
        
        if not inventory.empty and 'ingredient' in inventory.columns:
            ingredients = sorted(inventory['ingredient'].unique().tolist())
        elif 'ingredients' in data and not data['ingredients'].empty:
            if 'ingredient' in data['ingredients'].columns:
                ingredients = sorted(data['ingredients']['ingredient'].unique().tolist())
        elif 'usage' in data and not data['usage'].empty and 'ingredient' in data['usage'].columns:
            ingredients = sorted(data['usage']['ingredient'].unique().tolist())
        elif 'purchases' in data and not data['purchases'].empty and 'ingredient' in data['purchases'].columns:
            ingredients = sorted(data['purchases']['ingredient'].unique().tolist())
        
        return {"ingredients": ingredients}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/menu-items")
async def get_menu_items():
    """Get list of all available menu items"""
    try:
        data = analytics_service.get_data()
        menu_items = []
        
        # Try to get from recipe matrix first
        if 'ingredients' in data and not data['ingredients'].empty:
            # Check if it's a recipe matrix (first column is menu items)
            df = data['ingredients']
            if 'Item name' in df.columns:
                menu_items = sorted(df['Item name'].dropna().unique().tolist())
        
        # Fall back to usage data
        if not menu_items and 'usage' in data and not data['usage'].empty:
            if 'menu_item' in data['usage'].columns:
                menu_items = sorted(data['usage']['menu_item'].dropna().unique().tolist())
        
        # Fall back to sales data
        if not menu_items and 'sales' in data and not data['sales'].empty:
            if 'menu_item' in data['sales'].columns:
                menu_items = sorted(data['sales']['menu_item'].dropna().unique().tolist())
            elif 'item_name' in data['sales'].columns:
                menu_items = sorted(data['sales']['item_name'].dropna().unique().tolist())
        
        return {"menu_items": menu_items}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/chat")
async def chat(query: Dict[str, str] = Body(...)):
    """Chatbot endpoint"""
    try:
        user_query = query.get("query", "")
        if not user_query:
            raise HTTPException(status_code=400, detail="Query is required")
        
        response_text, chart_info = chatbot_service.ask(user_query)
        
        return {
            "response": response_text,
            "chart_info": chart_info
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/chat/clear")
async def clear_chat():
    """Clear chatbot history"""
    try:
        chatbot_service.clear_history()
        return {"status": "cleared"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/reload")
async def reload_data():
    """Reload data and analytics"""
    try:
        analytics_service.reload_analytics()
        return {"status": "reloaded"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/upload-data")
async def upload_data(file: UploadFile = File(...)):
    """Upload and merge new data file"""
    try:
        # Validate file type
        file_ext = Path(file.filename).suffix.lower()
        if file_ext not in ['.xlsx', '.csv']:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid file type. Only .xlsx and .csv files are allowed. Got: {file_ext}"
            )
        
        # Validate file size (max 50MB)
        file_content = await file.read()
        file_size_mb = len(file_content) / (1024 * 1024)
        if file_size_mb > 50:
            raise HTTPException(
                status_code=400,
                detail=f"File too large. Maximum size is 50MB. Got: {file_size_mb:.2f}MB"
            )
        
        # Generate timestamped filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        original_name = Path(file.filename).stem
        new_filename = f"{original_name}_{timestamp}{file_ext}"
        
        # Save file to data directory
        data_dir = Path(data_service.data_dir)
        data_dir.mkdir(parents=True, exist_ok=True)
        file_path = data_dir / new_filename
        
        with open(file_path, 'wb') as f:
            f.write(file_content)
        
        # Merge new data with existing data
        try:
            merge_result = data_service.merge_new_data(file_path)
            
            # Update analytics with merged data (don't reload from files to avoid duplicates)
            # The merge already updated the cache, so we just need to recreate analytics
            analytics_service.update_analytics()
            
            # Reload chatbot to ensure it has access to the new data
            chatbot_service.reload_chatbot()
            
            # Get file stats
            file_stats = {
                'filename': new_filename,
                'original_filename': file.filename,
                'size_bytes': len(file_content),
                'size_mb': round(file_size_mb, 2),
                'uploaded_at': datetime.now().isoformat()
            }
            
            return {
                "status": "success",
                "message": "File uploaded and data merged successfully",
                "file": file_stats,
                "merge_stats": merge_result
            }
        except Exception as merge_error:
            # If merge fails, delete the uploaded file
            if file_path.exists():
                file_path.unlink()
            raise HTTPException(
                status_code=500,
                detail=f"Error merging data: {str(merge_error)}"
            )
    
    except HTTPException:
        raise
    except Exception as e:
        import traceback
        error_detail = f"{str(e)}\n{traceback.format_exc()}"
        raise HTTPException(status_code=500, detail=error_detail)

@router.get("/upload-history")
async def get_upload_history():
    """Get list of uploaded data files with metadata"""
    try:
        data_dir = Path(data_service.data_dir)
        
        if not data_dir.exists():
            return {"files": []}
        
        # Get all Excel and CSV files
        excel_files = list(data_dir.glob("*.xlsx"))
        csv_files = list(data_dir.glob("*.csv"))
        all_files = excel_files + csv_files
        
        files_info = []
        for file_path in sorted(all_files, key=lambda p: p.stat().st_mtime, reverse=True):
            try:
                stat = file_path.stat()
                file_info = {
                    'filename': file_path.name,
                    'size_bytes': stat.st_size,
                    'size_mb': round(stat.st_size / (1024 * 1024), 2),
                    'uploaded_at': datetime.fromtimestamp(stat.st_mtime).isoformat(),
                    'modified_at': datetime.fromtimestamp(stat.st_mtime).isoformat()
                }
                
                # Try to get record counts if possible (optional, might be slow)
                try:
                    if file_path.suffix.lower() == '.xlsx':
                        df = pd.read_excel(str(file_path), nrows=0)  # Just read headers
                        file_info['columns'] = list(df.columns) if not df.empty else []
                    elif file_path.suffix.lower() == '.csv':
                        df = pd.read_csv(str(file_path), nrows=0)
                        file_info['columns'] = list(df.columns) if not df.empty else []
                except:
                    file_info['columns'] = []
                
                files_info.append(file_info)
            except Exception as e:
                # Skip files that can't be read
                print(f"Warning: Could not read file {file_path}: {str(e)}")
                continue
        
        return {"files": files_info}
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

