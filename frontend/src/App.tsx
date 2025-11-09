import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import { ErrorBoundary } from './components/ErrorBoundary'
import { MainLayout } from './components/MainLayout'
import { Overview } from './pages/Overview'
import { Inventory } from './pages/Inventory'
import { RiskAlerts } from './pages/RiskAlerts'
import { UsageTrends } from './pages/UsageTrends'
import { Forecasting } from './pages/Forecasting'
import { MenuForecasting } from './pages/MenuForecasting'
import { RecipeMapper } from './pages/RecipeMapper'
import { Shipments } from './pages/Shipments'
import { CostAnalysis } from './pages/CostAnalysis'
import { CostWaste } from './pages/CostWaste'
import { Storage } from './pages/Storage'
import { Reorder } from './pages/Reorder'
import { Simulator } from './pages/Simulator'
import { DataManagement } from './pages/DataManagement'

function App() {
  console.log('📱 App component rendering...')
  try {
    return (
      <ErrorBoundary>
        <BrowserRouter future={{ v7_startTransition: true, v7_relativeSplatPath: true }}>
          <Routes>
            <Route path="/" element={<MainLayout />}>
              <Route index element={<Navigate to="/overview" replace />} />
              <Route path="overview" element={<Overview />} />
              <Route path="inventory" element={<Inventory />} />
              <Route path="risk-alerts" element={<RiskAlerts />} />
              <Route path="usage-trends" element={<UsageTrends />} />
              <Route path="forecasting" element={<Forecasting />} />
              <Route path="menu-forecasting" element={<MenuForecasting />} />
              <Route path="recipe-mapper" element={<RecipeMapper />} />
              <Route path="shipments" element={<Shipments />} />
              <Route path="cost-analysis" element={<CostAnalysis />} />
              <Route path="cost-waste" element={<CostWaste />} />
              <Route path="storage" element={<Storage />} />
              <Route path="reorder" element={<Reorder />} />
              <Route path="simulator" element={<Simulator />} />
              <Route path="data-management" element={<DataManagement />} />
            </Route>
          </Routes>
        </BrowserRouter>
      </ErrorBoundary>
    )
  } catch (error) {
    console.error('❌ Error in App component:', error)
    return (
      <div style={{ padding: '20px', color: 'red' }}>
        <h1>Error in App Component</h1>
        <p>{error instanceof Error ? error.message : String(error)}</p>
      </div>
    )
  }
}

export default App

