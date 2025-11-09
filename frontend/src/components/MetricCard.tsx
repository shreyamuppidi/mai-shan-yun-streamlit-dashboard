import React from 'react'
import { motion } from 'framer-motion'
import { Card, CardContent, CardHeader, CardTitle } from './ui/card'
import { cn } from '@/lib/utils'
import { TrendingUp, TrendingDown, Minus } from 'lucide-react'

interface MetricCardProps {
  title: string
  value: string | number
  delta?: number | string | null
  deltaType?: 'increase' | 'decrease' | 'neutral'
  help?: string
  className?: string
  animationDelay?: number
  gradient?: 'blue' | 'purple' | 'green' | 'orange' | 'red'
}

export const MetricCard: React.FC<MetricCardProps> = ({
  title,
  value,
  delta,
  deltaType,
  help,
  className,
  animationDelay = 0,
  gradient = 'blue',
}) => {
  const getDeltaIcon = () => {
    if (deltaType === 'increase') return <TrendingUp className="h-4 w-4" />
    if (deltaType === 'decrease') return <TrendingDown className="h-4 w-4" />
    return <Minus className="h-4 w-4" />
  }

  const getDeltaColor = () => {
    if (deltaType === 'increase') return 'text-green-400'
    if (deltaType === 'decrease') return 'text-red-400'
    return 'text-gray-400'
  }

  const gradientClasses = {
    blue: 'from-blue-500/20 via-blue-600/10 to-transparent border-blue-500/30',
    purple: 'from-purple-500/20 via-purple-600/10 to-transparent border-purple-500/30',
    green: 'from-green-500/20 via-green-600/10 to-transparent border-green-500/30',
    orange: 'from-orange-500/20 via-orange-600/10 to-transparent border-orange-500/30',
    red: 'from-red-500/20 via-red-600/10 to-transparent border-red-500/30',
  }

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ 
        duration: 0.4, 
        delay: animationDelay,
        ease: [0.25, 0.1, 0.25, 1]
      }}
      whileHover={{ y: -6, scale: 1.02 }}
      className="h-full"
    >
      <Card className={cn(
        'h-full transition-all duration-300 relative overflow-hidden',
        'bg-gradient-to-br',
        gradientClasses[gradient],
        'border-2 shadow-lg shadow-black/20',
        'hover:shadow-xl hover:shadow-black/30',
        className
      )}>
        {/* Animated background gradient */}
        <div className="absolute inset-0 bg-gradient-to-br from-white/5 to-transparent opacity-0 hover:opacity-100 transition-opacity duration-300" />
        
        <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-3 relative z-10">
          <CardTitle className="text-sm font-semibold text-white/90 tracking-wide">
            {title}
          </CardTitle>
          {help && (
            <span className="text-xs text-white/60 hover:text-white/80 transition-colors cursor-help" title={help}>
              ℹ️
            </span>
          )}
        </CardHeader>
        <CardContent className="relative z-10">
          <div className="text-3xl font-bold text-white mb-2 tracking-tight">
            {value}
          </div>
          {delta !== null && delta !== undefined && (
            <div className={cn('flex items-center text-xs mt-2 font-medium', getDeltaColor())}>
              {getDeltaIcon()}
              <span className="ml-1.5">{delta}</span>
            </div>
          )}
        </CardContent>
        
        {/* Decorative corner accent */}
        <div className="absolute top-0 right-0 w-20 h-20 bg-gradient-to-br from-white/10 to-transparent rounded-bl-full" />
      </Card>
    </motion.div>
  )
}

