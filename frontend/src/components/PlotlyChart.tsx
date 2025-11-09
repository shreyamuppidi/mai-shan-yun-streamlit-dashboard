import React from 'react'
import Plot from 'react-plotly.js'
import { motion } from 'framer-motion'
import { cn } from '@/lib/utils'

interface PlotlyChartProps {
  data: any
  layout?: any
  config?: any
  className?: string
  style?: React.CSSProperties
  animationDelay?: number
}

export const PlotlyChart: React.FC<PlotlyChartProps> = ({
  data,
  layout = {},
  config = { responsive: true, displayModeBar: true, displaylogo: false },
  className,
  style,
  animationDelay = 0,
}) => {
  // Enhanced default layout with sophisticated styling
  const defaultLayout = {
    autosize: true,
    margin: { l: 60, r: 40, t: 40, b: 60 },
    paper_bgcolor: 'rgba(255, 255, 255, 0.05)',
    plot_bgcolor: 'rgba(255, 255, 255, 0.05)',
    font: { 
      family: 'system-ui, -apple-system, sans-serif', 
      size: 13,
      color: 'rgba(255, 255, 255, 0.9)'
    },
    xaxis: {
      gridcolor: 'rgba(255, 255, 255, 0.1)',
      gridwidth: 1,
      showgrid: true,
      zeroline: false,
      linecolor: 'rgba(255, 255, 255, 0.3)',
      tickfont: { color: 'rgba(255, 255, 255, 0.8)' },
      titlefont: { color: 'rgba(255, 255, 255, 0.9)', size: 14 },
      ...layout.xaxis,
    },
    yaxis: {
      gridcolor: 'rgba(255, 255, 255, 0.1)',
      gridwidth: 1,
      showgrid: true,
      zeroline: false,
      linecolor: 'rgba(255, 255, 255, 0.3)',
      tickfont: { color: 'rgba(255, 255, 255, 0.8)' },
      titlefont: { color: 'rgba(255, 255, 255, 0.9)', size: 14 },
      ...layout.yaxis,
    },
    legend: {
      bgcolor: 'rgba(0, 0, 0, 0.3)',
      bordercolor: 'rgba(255, 255, 255, 0.2)',
      borderwidth: 1,
      font: { color: 'rgba(255, 255, 255, 0.9)', size: 12 },
      ...layout.legend,
    },
    hovermode: 'closest' as const,
    hoverlabel: {
      bgcolor: 'rgba(0, 0, 0, 0.8)',
      bordercolor: 'rgba(255, 255, 255, 0.3)',
      font: { color: 'rgba(255, 255, 255, 0.95)', size: 12 },
    },
    ...layout,
  }

  return (
    <motion.div
      initial={{ opacity: 0, scale: 0.95 }}
      animate={{ opacity: 1, scale: 1 }}
      transition={{ 
        duration: 0.5, 
        delay: animationDelay,
        ease: [0.25, 0.1, 0.25, 1]
      }}
      className={cn('w-full', className)}
      style={style}
    >
      <Plot
        data={data}
        layout={defaultLayout}
        config={config}
        style={{ width: '100%', height: '100%' }}
        useResizeHandler={true}
      />
    </motion.div>
  )
}

