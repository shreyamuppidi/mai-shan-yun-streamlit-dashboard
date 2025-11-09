import React from 'react'
import { useNavigate, useLocation } from 'react-router-dom'
import { Button } from './ui/button'
import { useUIStore } from '@/store/uiStore'
import { Menu, MessageSquare, X, Upload } from 'lucide-react'
import { cn } from '@/lib/utils'

export const Header: React.FC = () => {
  const { sidebarOpen, chatOpen, toggleSidebar, toggleChat } = useUIStore()
  const navigate = useNavigate()
  const location = useLocation()
  const isDataManagementActive = location.pathname === '/data-management'

  return (
    <header className="sticky top-0 z-50 w-full border-b border-white/20 bg-black/40 backdrop-blur-md supports-[backdrop-filter]:bg-black/30">
      <div className="flex h-16 items-center justify-between px-4 md:px-6 lg:px-8">
        <div className="flex items-center gap-4">
          <Button
            variant="ghost"
            size="icon"
            onClick={toggleSidebar}
            className="md:hidden"
          >
            {sidebarOpen ? <X className="h-5 w-5" /> : <Menu className="h-5 w-5" />}
          </Button>
          <div className="flex items-center gap-2">
            <img
              src="/logo1.png"
              alt="Mai Shan Yun"
              className="h-10 w-10 object-contain"
              onError={(e) => {
                console.error('Logo failed to load:', e)
                // Fallback if logo doesn't exist - hide the image but keep spacing
                e.currentTarget.style.display = 'none'
              }}
            />
            <h1 className="text-xl font-bold text-white">Mai Shan Yun</h1>
          </div>
        </div>
        <div className="flex items-center gap-4">
          {/* Data Management Button */}
          <Button
            variant={isDataManagementActive ? "default" : "outline"}
            onClick={() => navigate('/data-management')}
            className={cn(
              "relative transition-all duration-300 overflow-visible group flex items-center gap-2 px-4",
              !isDataManagementActive && "data-management-button-pulse bg-gradient-to-br from-blue-500/20 to-cyan-500/10 border-blue-500/50 hover:from-blue-500/30 hover:to-cyan-500/20 hover:border-blue-500/70 text-white",
              isDataManagementActive && "bg-gradient-to-br from-blue-500 to-cyan-500 text-white shadow-lg shadow-blue-500/50"
            )}
          >
            <Upload className={cn(
              "h-4 w-4 transition-all duration-300",
              !isDataManagementActive && "group-hover:scale-110 group-hover:rotate-12"
            )} />
            <span className="text-sm font-medium">Upload Data</span>
            {!isDataManagementActive && (
              <>
                {/* Pulsing notification dot */}
                <span className="absolute -top-1 -right-1 h-3 w-3 rounded-full bg-blue-500 animate-ping" />
                <span className="absolute -top-1 -right-1 h-3 w-3 rounded-full bg-blue-500" />
                {/* Glow effect */}
                <span className="absolute inset-0 rounded-md bg-blue-500/20 animate-pulse" />
                {/* Shimmer effect */}
                <span className="absolute inset-0 rounded-md bg-gradient-to-r from-transparent via-white/10 to-transparent -translate-x-full group-hover:translate-x-full transition-transform duration-1000" />
              </>
            )}
            {isDataManagementActive && (
              <span className="absolute -top-1 -right-1 h-3 w-3 rounded-full bg-cyan-400 shadow-lg shadow-cyan-400/50" />
            )}
          </Button>
          
          {/* Chatbot Button */}
          <Button
            variant={chatOpen ? "default" : "outline"}
            onClick={toggleChat}
            className={cn(
              "relative transition-all duration-300 overflow-visible group flex items-center gap-2 px-4",
              !chatOpen && "chatbot-button-pulse bg-gradient-to-br from-primary/20 to-primary/10 border-primary/50 hover:from-primary/30 hover:to-primary/20 text-white",
              chatOpen && "bg-primary text-white shadow-lg shadow-primary/50"
            )}
          >
            <MessageSquare className={cn(
              "h-4 w-4 transition-all duration-300",
              !chatOpen && "animate-bounce-subtle"
            )} />
            <span className="text-sm font-medium">Chef Yun</span>
            {!chatOpen && (
              <>
                {/* Pulsing notification dot */}
                <span className="absolute -top-1 -right-1 h-3 w-3 rounded-full bg-primary animate-ping" />
                <span className="absolute -top-1 -right-1 h-3 w-3 rounded-full bg-primary" />
                {/* Glow effect */}
                <span className="absolute inset-0 rounded-md bg-primary/20 animate-pulse" />
              </>
            )}
            {chatOpen && (
              <span className="absolute -top-1 -right-1 h-3 w-3 rounded-full bg-green-400 shadow-lg shadow-green-400/50" />
            )}
          </Button>
        </div>
      </div>
    </header>
  )
}

