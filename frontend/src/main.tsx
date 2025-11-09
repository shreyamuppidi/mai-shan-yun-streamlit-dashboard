import React from 'react'
import ReactDOM from 'react-dom/client'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import App from './App.tsx'
import './index.css'

// Polyfills for plotly.js (needed for Node.js compatibility in browser)
import { Buffer } from 'buffer'
;(window as any).Buffer = Buffer
;(window as any).global = window
;(window as any).process = { env: {} }

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      refetchOnWindowFocus: false,
      retry: 1,
      staleTime: 5 * 60 * 1000, // 5 minutes
    },
  },
})

console.log('🚀 Starting React app...')
console.log('Root element exists:', !!document.getElementById('root'))

// Add global error handler
window.addEventListener('error', (event) => {
  console.error('❌ Global error:', event.error)
  const root = document.getElementById('root')
  if (root && root.children.length === 0) {
    root.innerHTML = `
      <div style="padding: 20px; color: red; font-family: monospace;">
        <h1>JavaScript Error</h1>
        <p><strong>Error:</strong> ${event.message}</p>
        <p><strong>File:</strong> ${event.filename}:${event.lineno}</p>
        <p>Check the browser console for more details.</p>
      </div>
    `
  }
})

// Add unhandled promise rejection handler
window.addEventListener('unhandledrejection', (event) => {
  console.error('❌ Unhandled promise rejection:', event.reason)
})

const rootElement = document.getElementById('root')
if (!rootElement) {
  console.error('❌ Root element not found!')
  document.body.innerHTML = '<h1 style="color: red; padding: 20px;">Error: Root element not found!</h1>'
} else {
  console.log('✅ Root element found, rendering app...')
  
  try {
    const root = ReactDOM.createRoot(rootElement)
    // Don't clear innerHTML - React.createRoot handles this
    root.render(
      <QueryClientProvider client={queryClient}>
        <App />
      </QueryClientProvider>,
    )
    console.log('✅ App rendered successfully!')
  } catch (error) {
    console.error('❌ Error rendering app:', error)
    rootElement.innerHTML = `
      <div style="padding: 20px; color: red; font-family: monospace;">
        <h1>Error Loading App</h1>
        <p><strong>Error:</strong> ${error instanceof Error ? error.message : String(error)}</p>
        <p>Check the browser console (F12 or Cmd+Option+I) for more details.</p>
        <pre style="background: #f0f0f0; padding: 10px; margin-top: 10px; overflow: auto; max-height: 400px;">
${error instanceof Error ? error.stack : String(error)}
        </pre>
      </div>
    `
  }
}

