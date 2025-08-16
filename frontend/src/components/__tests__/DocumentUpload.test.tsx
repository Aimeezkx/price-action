import { describe, it, expect, vi, beforeEach } from 'vitest'
import { screen, fireEvent, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { render, mockFetch, createMockFile, createMockDragEvent } from '../../test/utils'
import DocumentUpload from '../DocumentUpload'

// Mock the API
global.fetch = vi.fn()

describe('DocumentUpload', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    global.fetch = vi.fn().mockImplementation(mockFetch)
  })

  it('renders upload interface', () => {
    render(<DocumentUpload />)
    
    expect(screen.getByText(/upload document/i)).toBeInTheDocument()
    expect(screen.getByText(/drag and drop/i)).toBeInTheDocument()
  })

  it('handles file selection via input', async () => {
    const user = userEvent.setup()
    render(<DocumentUpload />)
    
    const file = createMockFile('test.pdf', 1024, 'application/pdf')
    const input = screen.getByLabelText(/choose file/i)
    
    await user.upload(input, file)
    
    expect(screen.getByText('test.pdf')).toBeInTheDocument()
  })

  it('handles drag and drop', async () => {
    render(<DocumentUpload />)
    
    const file = createMockFile('test.pdf', 1024, 'application/pdf')
    const dropZone = screen.getByTestId('drop-zone')
    
    const dragEvent = createMockDragEvent([file])
    
    fireEvent.dragOver(dropZone, dragEvent)
    expect(dropZone).toHaveClass('drag-over')
    
    fireEvent.drop(dropZone, dragEvent)
    
    await waitFor(() => {
      expect(screen.getByText('test.pdf')).toBeInTheDocument()
    })
  })

  it('validates file types', async () => {
    const user = userEvent.setup()
    render(<DocumentUpload />)
    
    const invalidFile = createMockFile('test.txt', 1024, 'text/plain')
    const input = screen.getByLabelText(/choose file/i)
    
    await user.upload(input, invalidFile)
    
    expect(screen.getByText(/unsupported file type/i)).toBeInTheDocument()
  })

  it('validates file size', async () => {
    const user = userEvent.setup()
    render(<DocumentUpload />)
    
    const largeFile = createMockFile('large.pdf', 100 * 1024 * 1024, 'application/pdf') // 100MB
    const input = screen.getByLabelText(/choose file/i)
    
    await user.upload(input, largeFile)
    
    expect(screen.getByText(/file too large/i)).toBeInTheDocument()
  })

  it('uploads file successfully', async () => {
    const user = userEvent.setup()
    
    // Mock successful upload response
    global.fetch = vi.fn().mockResolvedValue({
      ok: true,
      json: () => Promise.resolve({ id: '123', status: 'uploaded' })
    })
    
    render(<DocumentUpload />)
    
    const file = createMockFile('test.pdf', 1024, 'application/pdf')
    const input = screen.getByLabelText(/choose file/i)
    
    await user.upload(input, file)
    
    const uploadButton = screen.getByRole('button', { name: /upload/i })
    await user.click(uploadButton)
    
    await waitFor(() => {
      expect(screen.getByText(/upload successful/i)).toBeInTheDocument()
    })
    
    expect(global.fetch).toHaveBeenCalledWith(
      expect.stringContaining('/api/documents/upload'),
      expect.objectContaining({
        method: 'POST',
        body: expect.any(FormData)
      })
    )
  })

  it('handles upload errors', async () => {
    const user = userEvent.setup()
    
    // Mock failed upload response
    global.fetch = vi.fn().mockResolvedValue({
      ok: false,
      status: 400,
      json: () => Promise.resolve({ detail: 'Upload failed' })
    })
    
    render(<DocumentUpload />)
    
    const file = createMockFile('test.pdf', 1024, 'application/pdf')
    const input = screen.getByLabelText(/choose file/i)
    
    await user.upload(input, file)
    
    const uploadButton = screen.getByRole('button', { name: /upload/i })
    await user.click(uploadButton)
    
    await waitFor(() => {
      expect(screen.getByText(/upload failed/i)).toBeInTheDocument()
    })
  })

  it('shows upload progress', async () => {
    const user = userEvent.setup()
    
    // Mock upload with progress
    const mockXHR = {
      open: vi.fn(),
      send: vi.fn(),
      setRequestHeader: vi.fn(),
      upload: {
        addEventListener: vi.fn((event, callback) => {
          if (event === 'progress') {
            // Simulate progress
            setTimeout(() => callback({ loaded: 50, total: 100 }), 100)
            setTimeout(() => callback({ loaded: 100, total: 100 }), 200)
          }
        })
      },
      addEventListener: vi.fn((event, callback) => {
        if (event === 'load') {
          setTimeout(() => callback({
            target: {
              status: 200,
              responseText: JSON.stringify({ id: '123', status: 'uploaded' })
            }
          }), 300)
        }
      })
    }
    
    global.XMLHttpRequest = vi.fn(() => mockXHR)
    
    render(<DocumentUpload />)
    
    const file = createMockFile('test.pdf', 1024, 'application/pdf')
    const input = screen.getByLabelText(/choose file/i)
    
    await user.upload(input, file)
    
    const uploadButton = screen.getByRole('button', { name: /upload/i })
    await user.click(uploadButton)
    
    // Should show progress
    await waitFor(() => {
      expect(screen.getByRole('progressbar')).toBeInTheDocument()
    })
    
    // Should complete
    await waitFor(() => {
      expect(screen.getByText(/upload successful/i)).toBeInTheDocument()
    }, { timeout: 1000 })
  })

  it('supports multiple file selection', async () => {
    const user = userEvent.setup()
    render(<DocumentUpload multiple />)
    
    const files = [
      createMockFile('test1.pdf', 1024, 'application/pdf'),
      createMockFile('test2.pdf', 2048, 'application/pdf')
    ]
    
    const input = screen.getByLabelText(/choose files/i)
    await user.upload(input, files)
    
    expect(screen.getByText('test1.pdf')).toBeInTheDocument()
    expect(screen.getByText('test2.pdf')).toBeInTheDocument()
  })

  it('allows file removal before upload', async () => {
    const user = userEvent.setup()
    render(<DocumentUpload />)
    
    const file = createMockFile('test.pdf', 1024, 'application/pdf')
    const input = screen.getByLabelText(/choose file/i)
    
    await user.upload(input, file)
    
    expect(screen.getByText('test.pdf')).toBeInTheDocument()
    
    const removeButton = screen.getByRole('button', { name: /remove/i })
    await user.click(removeButton)
    
    expect(screen.queryByText('test.pdf')).not.toBeInTheDocument()
  })

  it('is accessible', async () => {
    const { container } = render(<DocumentUpload />)
    
    // Check for proper ARIA labels
    expect(screen.getByLabelText(/choose file/i)).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /upload/i })).toBeInTheDocument()
    
    // Check for keyboard navigation
    const input = screen.getByLabelText(/choose file/i)
    expect(input).toHaveAttribute('tabindex', '0')
    
    // Check for screen reader support
    const dropZone = screen.getByTestId('drop-zone')
    expect(dropZone).toHaveAttribute('aria-label')
  })
})