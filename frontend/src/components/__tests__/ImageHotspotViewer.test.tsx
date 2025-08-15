import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { ImageHotspotViewer } from '../ImageHotspotViewer';
import type { Hotspot } from '../../types';

// Mock framer-motion
jest.mock('framer-motion', () => ({
  motion: {
    div: ({ children, ...props }: any) => <div {...props}>{children}</div>,
  },
  AnimatePresence: ({ children }: any) => children,
}));

const mockHotspots: Hotspot[] = [
  {
    id: '1',
    x: 25,
    y: 25,
    width: 10,
    height: 10,
    label: 'Heart',
    description: 'The heart muscle',
    correct: true,
  },
  {
    id: '2',
    x: 75,
    y: 75,
    width: 8,
    height: 8,
    label: 'Lung',
    description: 'Left lung',
    correct: true,
  },
  {
    id: '3',
    x: 50,
    y: 50,
    width: 5,
    height: 5,
    label: 'Distractor',
    description: 'This is not correct',
    correct: false,
  },
];

describe('ImageHotspotViewer', () => {
  const defaultProps = {
    imageSrc: '/test-image.jpg',
    hotspots: mockHotspots,
    mode: 'study' as const,
  };

  beforeEach(() => {
    // Mock getBoundingClientRect
    Element.prototype.getBoundingClientRect = jest.fn(() => ({
      width: 400,
      height: 300,
      top: 0,
      left: 0,
      bottom: 300,
      right: 400,
      x: 0,
      y: 0,
      toJSON: jest.fn(),
    }));
  });

  it('renders image and hotspots', () => {
    render(<ImageHotspotViewer {...defaultProps} />);
    
    expect(screen.getByRole('application')).toBeInTheDocument();
    expect(screen.getByRole('img')).toBeInTheDocument();
    expect(screen.getByLabelText(/Hotspot 1: Heart/)).toBeInTheDocument();
    expect(screen.getByLabelText(/Hotspot 2: Lung/)).toBeInTheDocument();
  });

  it('shows zoom controls', () => {
    render(<ImageHotspotViewer {...defaultProps} />);
    
    expect(screen.getByLabelText('Zoom in')).toBeInTheDocument();
    expect(screen.getByLabelText('Zoom out')).toBeInTheDocument();
    expect(screen.getByLabelText('Reset view')).toBeInTheDocument();
  });

  it('handles hotspot clicks in study mode', async () => {
    const onHotspotClick = jest.fn();
    const onValidationComplete = jest.fn();
    
    render(
      <ImageHotspotViewer
        {...defaultProps}
        onHotspotClick={onHotspotClick}
        onValidationComplete={onValidationComplete}
      />
    );

    const heartHotspot = screen.getByLabelText(/Hotspot 1: Heart/);
    await userEvent.click(heartHotspot);

    expect(onHotspotClick).toHaveBeenCalledWith(mockHotspots[0]);
    expect(heartHotspot).toHaveAttribute('aria-pressed', 'true');
  });

  it('validates when all correct hotspots are clicked', async () => {
    const onValidationComplete = jest.fn();
    
    render(
      <ImageHotspotViewer
        {...defaultProps}
        onValidationComplete={onValidationComplete}
      />
    );

    // Click both correct hotspots
    await userEvent.click(screen.getByLabelText(/Hotspot 1: Heart/));
    await userEvent.click(screen.getByLabelText(/Hotspot 2: Lung/));

    await waitFor(() => {
      expect(onValidationComplete).toHaveBeenCalledWith(
        true,
        expect.arrayContaining([
          expect.objectContaining({ id: '1' }),
          expect.objectContaining({ id: '2' }),
        ])
      );
    });
  });

  it('shows partial feedback when incorrect hotspots are also clicked', async () => {
    const onValidationComplete = jest.fn();
    
    render(
      <ImageHotspotViewer
        {...defaultProps}
        onValidationComplete={onValidationComplete}
      />
    );

    // Click correct and incorrect hotspots
    await userEvent.click(screen.getByLabelText(/Hotspot 1: Heart/));
    await userEvent.click(screen.getByLabelText(/Hotspot 2: Lung/));
    await userEvent.click(screen.getByLabelText(/Hotspot 3: Distractor/));

    await waitFor(() => {
      expect(onValidationComplete).toHaveBeenCalledWith(false, expect.any(Array));
    });
  });

  it('handles zoom controls', async () => {
    render(<ImageHotspotViewer {...defaultProps} />);
    
    const zoomInButton = screen.getByLabelText('Zoom in');
    const zoomOutButton = screen.getByLabelText('Zoom out');
    
    await userEvent.click(zoomInButton);
    expect(screen.getByText(/120%/)).toBeInTheDocument();
    
    await userEvent.click(zoomOutButton);
    expect(screen.getByText(/100%/)).toBeInTheDocument();
  });

  it('disables hotspots in answer mode', () => {
    render(<ImageHotspotViewer {...defaultProps} mode="answer" />);
    
    const hotspots = screen.getAllByRole('button').filter(button => 
      button.getAttribute('aria-label')?.includes('Hotspot')
    );
    
    hotspots.forEach(hotspot => {
      expect(hotspot).toBeDisabled();
    });
  });

  it('shows instructions in study mode', () => {
    render(<ImageHotspotViewer {...defaultProps} />);
    
    expect(screen.getByText(/Find 2 important areas/)).toBeInTheDocument();
    expect(screen.getByText(/Click to select areas/)).toBeInTheDocument();
  });

  it('shows answer info in answer mode', () => {
    render(<ImageHotspotViewer {...defaultProps} mode="answer" />);
    
    expect(screen.getByText('Answer revealed')).toBeInTheDocument();
    expect(screen.getByText(/Green areas were the targets/)).toBeInTheDocument();
  });

  it('handles keyboard controls when enabled', async () => {
    render(<ImageHotspotViewer {...defaultProps} enableKeyboardControls={true} />);
    
    const container = screen.getByRole('application');
    container.focus();
    
    // Test zoom in with + key
    fireEvent.keyDown(document, { key: '+' });
    await waitFor(() => {
      expect(screen.getByText(/120%/)).toBeInTheDocument();
    });
    
    // Test zoom out with - key
    fireEvent.keyDown(document, { key: '-' });
    await waitFor(() => {
      expect(screen.getByText(/100%/)).toBeInTheDocument();
    });
  });

  it('constrains zoom within min/max bounds', async () => {
    render(<ImageHotspotViewer {...defaultProps} minZoom={0.5} maxZoom={2} />);
    
    const zoomInButton = screen.getByLabelText('Zoom in');
    const zoomOutButton = screen.getByLabelText('Zoom out');
    
    // Zoom in to max
    await userEvent.click(zoomInButton);
    await userEvent.click(zoomInButton);
    
    expect(zoomInButton).toBeDisabled();
    expect(screen.getByText('200%')).toBeInTheDocument();
    
    // Zoom out to min
    await userEvent.click(zoomOutButton);
    await userEvent.click(zoomOutButton);
    await userEvent.click(zoomOutButton);
    
    expect(zoomOutButton).toBeDisabled();
    expect(screen.getByText('50%')).toBeInTheDocument();
  });

  it('handles image load error', () => {
    render(<ImageHotspotViewer {...defaultProps} imageSrc="/invalid-image.jpg" />);
    
    const image = screen.getByRole('img');
    fireEvent.error(image);
    
    expect(screen.getByText('Image not available')).toBeInTheDocument();
  });

  it('shows hover labels for hotspots', async () => {
    render(<ImageHotspotViewer {...defaultProps} />);
    
    const heartHotspot = screen.getByLabelText(/Hotspot 1: Heart/);
    await userEvent.hover(heartHotspot);
    
    expect(screen.getByText('Heart')).toBeInTheDocument();
    expect(screen.getByText('The heart muscle')).toBeInTheDocument();
  });
});