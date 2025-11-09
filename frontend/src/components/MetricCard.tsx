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
}

export const MetricCard: React.FC<MetricCardProps> = ({
  title,
  value,
  delta,
  deltaType,
  help,
  className,
  animationDelay = 0,
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

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ 
        duration: 0.4, 
        delay: animationDelay,
        ease: [0.25, 0.1, 0.25, 1]
      }}
      whileHover={{ y: -4 }}
      className="h-full"
    >
      <Card className={cn('h-full transition-all duration-300', className)}>
        <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
          <CardTitle className="text-sm font-medium">{title}</CardTitle>
          {help && (
            <span className="text-xs text-muted-foreground" title={help}>
              ℹ️
            </span>
          )}
        </CardHeader>
        <CardContent>
          <div className="text-2xl font-bold">{value}</div>
          {delta !== null && delta !== undefined && (
            <div className={cn('flex items-center text-xs mt-1', getDeltaColor())}>
              {getDeltaIcon()}
              <span className="ml-1">{delta}</span>
            </div>
          )}
        </CardContent>
      </Card>
    </motion.div>
  )
}

