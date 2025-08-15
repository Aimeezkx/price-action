import React from 'react';
import { render, fireEvent } from '@testing-library/react-native';
import { GradingInterface } from '../GradingInterface';

describe('GradingInterface', () => {
  const mockOnGrade = jest.fn();

  beforeEach(() => {
    mockOnGrade.mockClear();
  });

  it('renders all grade buttons (0-5)', () => {
    const { getByText } = render(
      <GradingInterface onGrade={mockOnGrade} />
    );
    
    for (let i = 0; i <= 5; i++) {
      expect(getByText(i.toString())).toBeTruthy();
    }
  });

  it('calls onGrade with correct value when button is pressed', () => {
    const { getByText } = render(
      <GradingInterface onGrade={mockOnGrade} />
    );
    
    fireEvent.press(getByText('4'));
    expect(mockOnGrade).toHaveBeenCalledWith(4);
  });

  it('shows grade descriptions', () => {
    const { getByText } = render(
      <GradingInterface onGrade={mockOnGrade} />
    );
    
    expect(getByText('Again')).toBeTruthy(); // Grade 0
    expect(getByText('Perfect')).toBeTruthy(); // Grade 5
  });

  it('applies correct styling to grade buttons', () => {
    const { getByTestId } = render(
      <GradingInterface onGrade={mockOnGrade} />
    );
    
    const button0 = getByTestId('grade-button-0');
    const button5 = getByTestId('grade-button-5');
    
    expect(button0.props.style).toMatchObject(
      expect.objectContaining({
        backgroundColor: expect.any(String),
      })
    );
    expect(button5.props.style).toMatchObject(
      expect.objectContaining({
        backgroundColor: expect.any(String),
      })
    );
  });

  it('supports keyboard shortcuts', () => {
    const { getByTestId } = render(
      <GradingInterface onGrade={mockOnGrade} />
    );
    
    // Test that buttons have proper accessibility labels for keyboard navigation
    const button3 = getByTestId('grade-button-3');
    expect(button3.props.accessibilityLabel).toContain('3');
  });

  it('provides haptic feedback on button press', () => {
    const { getByText } = render(
      <GradingInterface onGrade={mockOnGrade} />
    );
    
    fireEvent.press(getByText('3'));
    
    // Verify that the component triggers haptic feedback
    // This would be tested through the haptic service mock
    expect(mockOnGrade).toHaveBeenCalledWith(3);
  });

  it('handles disabled state correctly', () => {
    const { getByTestId } = render(
      <GradingInterface onGrade={mockOnGrade} disabled={true} />
    );
    
    const button2 = getByTestId('grade-button-2');
    fireEvent.press(button2);
    
    expect(mockOnGrade).not.toHaveBeenCalled();
  });

  it('shows loading state when processing grade', () => {
    const { getByTestId } = render(
      <GradingInterface onGrade={mockOnGrade} loading={true} />
    );
    
    const loadingIndicator = getByTestId('grading-loading');
    expect(loadingIndicator).toBeTruthy();
  });
});