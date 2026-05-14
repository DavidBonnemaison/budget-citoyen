// webapp/src/__tests__/components/LeverSlider.test.tsx
//
// Vitest component smoke test for LeverSlider (A11Y-05).
// Decision: verifies component renders with all expected output elements.
// React Aria uses dynamic IDs; tests target stable text and element counts.

import { describe, it, expect, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import '@testing-library/jest-dom/vitest';
import { LeverSlider } from '../../components/LeverSlider';

describe('LeverSlider', () => {
  const defaultProps = {
    label: 'IR ménages',
    minValue: -30,
    maxValue: 30,
    step: 1,
    defaultValue: 0,
    onValueChange: vi.fn(),
    onDragEnd: vi.fn(),
  };

  it('renders label text', () => {
    render(<LeverSlider {...defaultProps} />);
    expect(screen.getByText('IR ménages')).toBeInTheDocument();
  });

  it('displays Actuel baseline label', () => {
    render(<LeverSlider {...defaultProps} />);
    const labels = screen.getAllByText('Actuel');
    expect(labels.length).toBeGreaterThanOrEqual(1);
  });

  it('renders a group container', () => {
    render(<LeverSlider {...defaultProps} />);
    const containers = screen.getAllByRole('group');
    expect(containers.length).toBeGreaterThanOrEqual(1);
  });

  it('renders a hidden range input for screen readers', () => {
    render(<LeverSlider {...defaultProps} />);
    const inputs = document.querySelectorAll('input[type="range"]');
    expect(inputs.length).toBeGreaterThanOrEqual(1);
  });

  it('renders an output element for the value label', () => {
    render(<LeverSlider {...defaultProps} />);
    const outputs = document.querySelectorAll('output');
    expect(outputs.length).toBeGreaterThanOrEqual(1);
  });

  it('renders without error when disabled', () => {
    render(<LeverSlider {...defaultProps} disabled={true} />);
    const labels = screen.getAllByText('Actuel');
    expect(labels.length).toBeGreaterThanOrEqual(1);
  });

  it('renders with a non-zero default value without error', () => {
    render(<LeverSlider {...defaultProps} defaultValue={5} />);
    const labels = screen.getAllByText('IR ménages');
    expect(labels.length).toBeGreaterThanOrEqual(1);
  });
});
