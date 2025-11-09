import React from 'react'
import { Outlet } from 'react-router-dom'
import { Header } from './Header'
import { Sidebar } from './Sidebar'
import { ChatPanel } from './ChatPanel'
import { useUIStore } from '@/store/uiStore'
import { cn } from '@/lib/utils'

export const MainLayout: React.FC = () => {
  const { sidebarOpen, chatOpen } = useUIStore()

  return (
    <div className="min-h-screen bg-background relative">
      {/* Full-page food image background with overlay */}
      <div 
        className="fixed inset-0 z-0"
        style={{
          backgroundImage: 'url(/food-background.jpg)',
          backgroundSize: 'cover',
          backgroundPosition: 'center',
          backgroundAttachment: 'fixed',
        }}
      >
        <div className="absolute inset-0 bg-black/55 backdrop-blur-[1px]" />
      </div>
      
      {/* Content layer */}
      <div className="relative z-10">
        <Header />
        <div className="flex">
          <Sidebar />
          <main
            className={cn(
              'flex-1 transition-all duration-300',
              sidebarOpen ? 'md:ml-64' : 'md:ml-0',
              chatOpen && 'md:mr-96'
            )}
          >
            <div className="container mx-auto p-4 md:p-6 lg:p-8">
              <Outlet />
            </div>
          </main>
          <ChatPanel />
        </div>
      </div>
    </div>
  )
}

