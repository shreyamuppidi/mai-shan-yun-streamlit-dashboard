import * as React from "react"
import { cn } from "@/lib/utils"

export interface BadgeProps extends React.HTMLAttributes<HTMLDivElement> {
  variant?: "default" | "secondary" | "destructive" | "outline"
}

function Badge({ className, variant = "default", ...props }: BadgeProps) {
  return (
    <div
      className={cn(
        "inline-flex items-center rounded-full border px-2.5 py-0.5 text-xs font-semibold transition-colors focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2",
        {
          "border-transparent bg-green-600 text-white hover:bg-green-700": variant === "default",
          "border-transparent bg-yellow-500 text-gray-900 hover:bg-yellow-600": variant === "secondary",
          "border-transparent bg-red-600 text-white hover:bg-red-700": variant === "destructive",
          "border-orange-500 bg-orange-500/20 text-orange-400 hover:bg-orange-500/30": variant === "outline",
        },
        className
      )}
      {...props}
    />
  )
}

export { Badge }

