export interface OverviewData {
  metrics: {
    total_ingredients: number
    low_stock: number
    high_stock: number
    reorder_count: number
    menu_viability: number | null
  }
  status_distribution: Record<string, number>
  critical_stockout: any[]
  top_stock: any[]
  top_risks: any[]
  recent_purchases: any[]
  recent_usage: any[]
}

export interface InventoryItem {
  ingredient: string
  current_stock: number
  min_stock_level: number
  max_stock_level: number
  stock_status: 'Low' | 'Normal' | 'High'
  days_until_stockout: number
  reorder_needed: boolean
}

export interface RiskAlert {
  ingredient: string
  current_stock: number
  min_stock_level: number
  max_stock_level: number
  usage_velocity_7d: number
  days_until_stockout: number
  risk_score: number
  risk_type: string
  needs_reorder: boolean
}

export interface ForecastData {
  date: string
  forecasted_usage: number
  confidence_low: number
  confidence_high: number
}

export interface MenuViability {
  viability_score: number
  data: any[]
  can_make_count: number
  cannot_make_count: number
}

export interface ChatMessage {
  role: 'user' | 'assistant'
  content: string
  chart_info?: any
}

