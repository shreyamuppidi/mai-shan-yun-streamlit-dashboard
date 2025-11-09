import React, { useState, useRef, useEffect } from 'react'
import { useMutation } from '@tanstack/react-query'
import { useUIStore } from '@/store/uiStore'
import { Button } from './ui/button'
import { Input } from './ui/input'
import { Card, CardContent, CardHeader, CardTitle } from './ui/card'
import { X, Send, Loader2, MessageSquare } from 'lucide-react'
import { apiEndpoints } from '@/services/api'
import { cn } from '@/lib/utils'
import { PlotlyChart } from './PlotlyChart'

interface ChatMessage {
  role: 'user' | 'assistant'
  content: string
  chart_info?: any
}

export const ChatPanel: React.FC = () => {
  const { chatOpen, setChatOpen } = useUIStore()
  const [messages, setMessages] = useState<ChatMessage[]>([])
  const [input, setInput] = useState('')
  const messagesEndRef = useRef<HTMLDivElement>(null)

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }

  useEffect(() => {
    scrollToBottom()
  }, [messages])

  const chatMutation = useMutation({
    mutationFn: (query: string) => apiEndpoints.chat(query),
    onSuccess: (response) => {
      const newMessage: ChatMessage = {
        role: 'assistant',
        content: response.data.response,
        chart_info: response.data.chart_info,
      }
      setMessages((prev) => [...prev, newMessage])
    },
    onError: (error: any) => {
      const errorMessage: ChatMessage = {
        role: 'assistant',
        content: `Error: ${error.response?.data?.detail || error.message || 'Failed to get response'}`,
      }
      setMessages((prev) => [...prev, errorMessage])
    },
  })

  const clearChatMutation = useMutation({
    mutationFn: () => apiEndpoints.clearChat(),
    onSuccess: () => {
      setMessages([])
    },
  })

  const handleSend = () => {
    if (!input.trim() || chatMutation.isPending) return

    const userMessage: ChatMessage = {
      role: 'user',
      content: input,
    }
    setMessages((prev) => [...prev, userMessage])
    setInput('')
    chatMutation.mutate(input)
  }

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSend()
    }
  }

  if (!chatOpen) return null

  return (
    <div
      className="fixed right-0 top-16 z-40 h-[calc(100vh-4rem)] w-full max-w-md border-l border-white/20 bg-black/50 backdrop-blur-md shadow-lg md:w-96"
    >
        <Card className="h-full flex flex-col border-0 rounded-none bg-transparent">
          <CardHeader className="flex flex-row items-center justify-between border-b border-white/20">
            <CardTitle className="text-lg text-white">Yun Chef</CardTitle>
            <div className="flex items-center gap-2">
              <Button
                variant="ghost"
                size="icon"
                onClick={() => clearChatMutation.mutate()}
                disabled={messages.length === 0}
              >
                <X className="h-4 w-4" />
              </Button>
              <Button
                variant="ghost"
                size="icon"
                onClick={() => setChatOpen(false)}
              >
                <X className="h-4 w-4" />
              </Button>
            </div>
          </CardHeader>
          <CardContent className="flex-1 flex flex-col overflow-hidden p-0">
            <div className="flex-1 overflow-y-auto p-4 space-y-4">
              {messages.length === 0 && (
                <div className="flex flex-col items-center justify-center h-full py-8 px-4">
                  <div className="bg-white/10 backdrop-blur-sm rounded-2xl p-6 max-w-md w-full border border-white/20 shadow-lg">
                    <div className="flex items-center gap-3 mb-4">
                      <div className="h-10 w-10 rounded-full bg-gradient-to-br from-primary to-primary/70 flex items-center justify-center">
                        <MessageSquare className="h-5 w-5 text-white" />
                      </div>
                      <div>
                        <h3 className="text-lg font-semibold text-white">Yun Chef</h3>
                        <p className="text-xs text-white/60">AI Assistant • Ready to help</p>
                      </div>
                    </div>
                    <p className="text-white/90 mb-4 text-sm leading-relaxed">
                      👋 Hi! I can help you with:
                    </p>
                    <div className="grid grid-cols-1 gap-2">
                      {[
                        'Most used/wasted ingredients',
                        'Revenue by dish',
                        'Inventory status',
                        'Cost analysis',
                        'Menu viability',
                        'Reorder recommendations'
                      ].map((item, idx) => (
                        <div
                          key={idx}
                          className="flex items-center gap-2 px-3 py-2 rounded-lg bg-white/5 hover:bg-white/10 transition-colors border border-white/10"
                        >
                          <div className="h-1.5 w-1.5 rounded-full bg-primary flex-shrink-0" />
                          <span className="text-sm text-white/80">{item}</span>
                        </div>
                      ))}
                    </div>
                    <div className="mt-4 pt-4 border-t border-white/10">
                      <p className="text-xs text-white/50 text-center">
                        Ask me anything about your inventory
                      </p>
                    </div>
                  </div>
                </div>
              )}
              {messages.map((message, idx) => (
                <div
                  key={idx}
                  className={cn(
                    'flex',
                    message.role === 'user' ? 'justify-end' : 'justify-start'
                  )}
                >
                  <div
                    className={cn(
                      'max-w-[80%] rounded-lg px-4 py-2',
                      message.role === 'user'
                        ? 'bg-primary text-white'
                        : 'bg-white/10 text-white'
                    )}
                  >
                    <p className="text-sm whitespace-pre-wrap">{message.content}</p>
                    {message.chart_info && 
                     message.chart_info.type && 
                     message.chart_info.data && 
                     (() => {
                       // Check if data is not empty
                       const data = message.chart_info.data
                       const hasData = Array.isArray(data) 
                         ? data.length > 0 
                         : (typeof data === 'object' && data !== null && Object.keys(data).length > 0)
                       return hasData
                     })() && (
                      <div className="mt-2">
                        <PlotlyChart
                          data={message.chart_info.data || []}
                          layout={message.chart_info.layout || { title: message.chart_info.title || '' }}
                        />
                      </div>
                    )}
                  </div>
                </div>
              ))}
              {chatMutation.isPending && (
                <div className="flex justify-start">
                  <div className="bg-white/10 text-white rounded-lg px-4 py-2 flex items-center gap-2">
                    <Loader2 className="h-4 w-4 animate-spin" />
                    <span className="text-sm">Cooking...</span>
                  </div>
                </div>
              )}
              <div ref={messagesEndRef} />
            </div>
            <div className="border-t border-white/20 p-4">
              <div className="flex gap-2">
                <Input
                  value={input}
                  onChange={(e) => setInput(e.target.value)}
                  onKeyPress={handleKeyPress}
                  placeholder="Ask a question about your inventory..."
                  disabled={chatMutation.isPending}
                />
                <Button
                  onClick={handleSend}
                  disabled={!input.trim() || chatMutation.isPending}
                  size="icon"
                >
                  {chatMutation.isPending ? (
                    <Loader2 className="h-4 w-4 animate-spin" />
                  ) : (
                    <Send className="h-4 w-4" />
                  )}
                </Button>
              </div>
            </div>
          </CardContent>
        </Card>
    </div>
  )
}

