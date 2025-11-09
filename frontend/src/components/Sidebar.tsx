import React from 'react'
import { Link, useLocation } from 'react-router-dom'
import { cn } from '@/lib/utils'
import { useUIStore } from '@/store/uiStore'
import {
  Home,
  Package,
  AlertTriangle,
  TrendingUp,
  Sparkles,
  UtensilsCrossed,
  FileText,
  Truck,
  DollarSign,
  Trash2,
  Snowflake,
  ShoppingCart,
  FlaskConical,
} from 'lucide-react'

const navigation = [
  { name: 'Overview', href: '/overview', icon: Home },
  { name: 'Inventory Levels', href: '/inventory', icon: Package },
  { name: 'Risk Alerts', href: '/risk-alerts', icon: AlertTriangle },
  { name: 'Usage Trends', href: '/usage-trends', icon: TrendingUp },
  { name: 'Demand Forecasting', href: '/forecasting', icon: Sparkles },
  { name: 'Menu Forecasting', href: '/menu-forecasting', icon: UtensilsCrossed },
  { name: 'Recipe Mapper', href: '/recipe-mapper', icon: FileText },
  { name: 'Shipment Analysis', href: '/shipments', icon: Truck },
  { name: 'Cost Analysis', href: '/cost-analysis', icon: DollarSign },
  { name: 'Cost vs Waste', href: '/cost-waste', icon: Trash2 },
  { name: 'Storage Estimator', href: '/storage', icon: Snowflake },
  { name: 'Reorder Recommendations', href: '/reorder', icon: ShoppingCart },
  { name: 'What-If Simulator', href: '/simulator', icon: FlaskConical },
]

export const Sidebar: React.FC = () => {
  const location = useLocation()
  const { sidebarOpen, setSidebarOpen } = useUIStore()

  return (
    <>
      {/* Mobile overlay */}
      {sidebarOpen && (
        <div
          className="fixed inset-0 z-40 bg-black/50 md:hidden"
          onClick={() => setSidebarOpen(false)}
        />
      )}

      {/* Sidebar */}
      <aside
        className={cn(
          'fixed left-0 top-16 z-40 h-[calc(100vh-4rem)] w-64 border-r border-white/20 bg-black/50 backdrop-blur-md transition-transform duration-300 md:translate-x-0',
          sidebarOpen ? 'translate-x-0' : '-translate-x-full'
        )}
      >
        <div className="flex h-full flex-col overflow-y-auto p-4">
          <nav className="space-y-1">
            {navigation.map((item) => {
              const Icon = item.icon
              const isActive = location.pathname === item.href

              return (
                <Link
                  key={item.name}
                  to={item.href}
                  onClick={() => {
                    // Close sidebar on mobile when navigating
                    if (window.innerWidth < 768) {
                      setSidebarOpen(false)
                    }
                  }}
                  className={cn(
                    'flex items-center gap-3 rounded-lg px-3 py-2 text-sm font-medium transition-colors',
                    isActive
                      ? 'bg-primary text-white'
                      : 'text-white/80 hover:bg-white/10 hover:text-white'
                  )}
                >
                  <Icon className="h-5 w-5" />
                  {item.name}
                </Link>
              )
            })}
          </nav>
        </div>
      </aside>
    </>
  )
}

