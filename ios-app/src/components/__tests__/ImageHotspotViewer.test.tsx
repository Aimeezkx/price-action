import React from 'react';
import { render, fireEvent } from '@testing-library/react-native';
import { ImageHotspotViewer } from '../ImageHotspotViewer';

const mockHotspots = [
  { x: 100, y: 100, width: 50, height: 50, label: 'Feature A' },
  { x: 200, y: 150, width: 60, height: 40, label: 'Feature B' },
];

describe('ImageHotspotViewer', () => {
  const mockOnHotspotPress = jest.fn();

  beforeEach(() => {
    mockOnHotspotPress.mockClear();
  });

  it('renders image with hotspots', () => {
    const { getByTestId } = render(
      <ImageHotspotViewer
        imageUri="test-image.jpg"
        hotspots={mockHotspots}
        onHotspotPress={mockOnHotspotPress}
      />
    );
    
    const imageContainer = getByTestId('image-hotspot-container');
    expect(imageContainer).toBeTruthy();
  });

  it('renders correct number of hotspots', () => {
    const { getAllByTestId } = render(
      <ImageHotspotViewer
        imageUri="test-image.jpg"
        hotspots={mockHotspots}
        onHotspotPress={mockOnHotspotPress}
      />
    );
    
    const hotspotElements = getAllByTestId(/hotspot-\d+/);
    expect(hotspotElements).toHaveLength(mockHotspots.length);
  });

  it('calls onHotspotPress when hotspot is tapped', () => {
    const { getByTestId } = render(
      <ImageHotspotViewer
        imageUri="test-image.jpg"
        hotspots={mockHotspots}
        onHotspotPress={mockOnHotspotPress}
      />
    );
    
    const firstHotspot = getByTestId('hotspot-0');
    fireEvent.press(firstHotspot);
    
    expect(mockOnHotspotPress).toHaveBeenCalledWith(mockHotspots[0], 0);
  });

  it('supports zoom and pan gestures', () => {
    const { getByTestId } = render(
      <ImageHotspotViewer
        imageUri="test-image.jpg"
        hotspots={mockHotspots}
        onHotspotPress={mockOnHotspotPress}
        enableZoom={true}
      />
    );
    
    const zoomContainer = getByTestId('zoom-container');
    expect(zoomContainer).toBeTruthy();
  });

  it('positions hotspots correctly based on coordinates', () => {
    const { getByTestId } = render(
      <ImageHotspotViewer
        imageUri="test-image.jpg"
        hotspots={mockHotspots}
        onHotspotPress={mockOnHotspotPress}
      />
    );
    
    const firstHotspot = getByTestId('hotspot-0');
    const hotspotStyle = firstHotspot.props.style;
    
    expect(hotspotStyle).toMatchObject(
      expect.objectContaining({
        position: 'absolute',
        left: expect.any(Number),
        top: expect.any(Number),
      })
    );
  });

  it('shows hotspot labels when enabled', () => {
    const { getByText } = render(
      <ImageHotspotViewer
        imageUri="test-image.jpg"
        hotspots={mockHotspots}
        onHotspotPress={mockOnHotspotPress}
        showLabels={true}
      />
    );
    
    expect(getByText('Feature A')).toBeTruthy();
    expect(getByText('Feature B')).toBeTruthy();
  });

  it('handles empty hotspots array', () => {
    const { getByTestId, queryAllByTestId } = render(
      <ImageHotspotViewer
        imageUri="test-image.jpg"
        hotspots={[]}
        onHotspotPress={mockOnHotspotPress}
      />
    );
    
    const imageContainer = getByTestId('image-hotspot-container');
    expect(imageContainer).toBeTruthy();
    
    const hotspotElements = queryAllByTestId(/hotspot-\d+/);
    expect(hotspotElements).toHaveLength(0);
  });

  it('applies correct accessibility properties', () => {
    const { getByTestId } = render(
      <ImageHotspotViewer
        imageUri="test-image.jpg"
        hotspots={mockHotspots}
        onHotspotPress={mockOnHotspotPress}
      />
    );
    
    const firstHotspot = getByTestId('hotspot-0');
    expect(firstHotspot.props.accessible).toBe(true);
    expect(firstHotspot.props.accessibilityRole).toBe('button');
    expect(firstHotspot.props.accessibilityLabel).toContain('Feature A');
  });

  it('handles image loading states', () => {
    const { getByTestId } = render(
      <ImageHotspotViewer
        imageUri="test-image.jpg"
        hotspots={mockHotspots}
        onHotspotPress={mockOnHotspotPress}
      />
    );
    
    const imageElement = getByTestId('hotspot-image');
    expect(imageElement).toBeTruthy();
  });
});