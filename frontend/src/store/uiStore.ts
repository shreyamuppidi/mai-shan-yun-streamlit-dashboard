import { create } from 'zustand'

interface UIState {
  sidebarOpen: boolean
  chatOpen: boolean
  setSidebarOpen: (open: boolean) => void
  setChatOpen: (open: boolean) => void
  toggleSidebar: () => void
  toggleChat: () => void
}

export const useUIStore = create<UIState>((set) => ({
  sidebarOpen: true,
  chatOpen: false,
  setSidebarOpen: (open) => set({ sidebarOpen: open }),
  setChatOpen: (open) => set({ chatOpen: open }),
  toggleSidebar: () => set((state) => ({ sidebarOpen: !state.sidebarOpen })),
  toggleChat: () => set((state) => ({ chatOpen: !state.chatOpen })),
}))

