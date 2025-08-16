import React, { ReactElement } from 'react'
import { render, RenderOptions } from '@testing-library/react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { BrowserRouter } from 'react-router-dom'
import { vi } from 'vitest'

// Mock data generators
export const mockDocument = {
  id: '123e4567-e89b-12d3-a456-426614174000',
  filename: 'test-document.pdf',
  status: 'completed',
  chapter_count: 3,
  figure_count: 5,
  knowledge_count: 25,
  created_at: '2023-01-01T00:00:00Z',
}

export const mockChapter = {
  id: '123e4567-e89b-12d3-a456-426614174001',
  title: 'Chapter 1: Introduction',
  level: 1,
  figures: [],
  knowledge_count: 10,
}

export const mockCard = {
  id: '123e4567-e89b-12d3-a456-426614174002',
  card_type: 'qa',
  front: 'What is machine learning?',
  back: 'Machine learning is a subset of artificial intelligence...',
  difficulty: 0.5,
  due_date: '2023-12-01T00:00:00Z',
  metadata: {},
}

export const mockKnowledgePoint = {
  id: '123e4567-e89b-12d3-a456-426614174003',
  text: 'Machine learning is a method of data analysis...',
  kind: 'definition',
  entities: ['machine learning', 'data analysis'],
  anchors: { page: 1, chapter: 1, position: 100 },
}

export const mockSearchResult = {
  id: '123e4567-e89b-12d3-a456-426614174004',
  text: 'Neural networks are computing systems...',
  type: 'knowledge',
  score: 0.95,
  highlights: ['neural networks', 'computing systems'],
}

// Test wrapper component
interface AllTheProvidersProps {
  children: React.ReactNode
}

const AllTheProviders = ({ children }: AllTheProvidersProps) => {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: {
        retry: false,
      },
    },
  })

  return (
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        {children}
      </BrowserRouter>
    </QueryClientProvider>
  )
}

// Custom render function
const customRender = (
  ui: ReactElement,
  options?: Omit<RenderOptions, 'wrapper'>
) => render(ui, { wrapper: AllTheProviders, ...options })

export * from '@testing-library/react'
export { customRender as render }

// Mock API responses
export const mockApiResponses = {
  documents: [mockDocument],
  chapters: [mockChapter],
  cards: [mockCard],
  knowledge: [mockKnowledgePoint],
  searchResults: [mockSearchResult],
}

// Mock fetch function
export const mockFetch = (url: string, options?: RequestInit) => {
  const urlObj = new URL(url, 'http://localhost')
  const path = urlObj.pathname

  let response: any = {}

  if (path.includes('/documents')) {
    response = mockApiResponses.documents
  } else if (path.includes('/chapters')) {
    response = mockApiResponses.chapters
  } else if (path.includes('/cards')) {
    response = mockApiResponses.cards
  } else if (path.includes('/search')) {
    response = mockApiResponses.searchResults
  }

  return Promise.resolve({
    ok: true,
    status: 200,
    json: () => Promise.resolve(response),
  } as Response)
}

// Mock intersection observer
export const mockIntersectionObserver = () => {
  const mockIntersectionObserver = vi.fn()
  mockIntersectionObserver.mockReturnValue({
    observe: () => null,
    unobserve: () => null,
    disconnect: () => null,
  })
  window.IntersectionObserver = mockIntersectionObserver
}

// Mock resize observer
export const mockResizeObserver = () => {
  const mockResizeObserver = vi.fn()
  mockResizeObserver.mockReturnValue({
    observe: () => null,
    unobserve: () => null,
    disconnect: () => null,
  })
  window.ResizeObserver = mockResizeObserver
}

// Mock file upload
export const createMockFile = (name: string, size: number, type: string) => {
  const file = new File([''], name, { type })
  Object.defineProperty(file, 'size', {
    value: size,
    writable: false,
  })
  return file
}

// Mock drag and drop events
export const createMockDragEvent = (files: File[]) => {
  return {
    dataTransfer: {
      files,
      items: files.map(file => ({
        kind: 'file',
        type: file.type,
        getAsFile: () => file,
      })),
      types: ['Files'],
    },
    preventDefault: vi.fn(),
    stopPropagation: vi.fn(),
  }
}

// Performance testing utilities
export const measureRenderTime = async (renderFn: () => void) => {
  const start = performance.now()
  renderFn()
  const end = performance.now()
  return end - start
}

// Accessibility testing utilities
export const checkAccessibility = async (container: HTMLElement) => {
  const { axe } = await import('axe-core')
  const results = await axe.run(container)
  return results
}

// Wait for async operations
export const waitForLoadingToFinish = () => {
  return new Promise(resolve => setTimeout(resolve, 0))
}

// Mock local storage
export const mockLocalStorage = () => {
  const store: Record<string, string> = {}
  
  return {
    getItem: vi.fn((key: string) => store[key] || null),
    setItem: vi.fn((key: string, value: string) => {
      store[key] = value
    }),
    removeItem: vi.fn((key: string) => {
      delete store[key]
    }),
    clear: vi.fn(() => {
      Object.keys(store).forEach(key => delete store[key])
    }),
  }
}

// Mock session storage
export const mockSessionStorage = () => {
  const store: Record<string, string> = {}
  
  return {
    getItem: vi.fn((key: string) => store[key] || null),
    setItem: vi.fn((key: string, value: string) => {
      store[key] = value
    }),
    removeItem: vi.fn((key: string) => {
      delete store[key]
    }),
    clear: vi.fn(() => {
      Object.keys(store).forEach(key => delete store[key])
    }),
  }
}