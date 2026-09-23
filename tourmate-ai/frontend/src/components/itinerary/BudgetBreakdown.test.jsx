import { render, screen, fireEvent } from '@testing-library/react';
import { describe, it, expect, vi } from 'vitest';
import React from 'react';
import BudgetBreakdown from './BudgetBreakdown';

describe('BudgetBreakdown Component', () => {
  const sampleDayPlan = {
    day: 1,
    activities: [
      { name: 'Taj Mahal', estimated_cost: 250, activity_type: 'Sightseeing', category: 'Attraction' },
      { name: 'Lunch at Local Diner', estimated_cost: 400, activity_type: 'Meal', category: 'Food' },
      { name: 'Taxi across city', estimated_cost: 150, activity_type: 'Transit', category: 'Transport' },
      { name: 'Souvenir shopping', estimated_cost: 200, activity_type: 'Shopping', category: 'Other' },
    ]
  };

  it('renders daily cost breakdown accurately with transparent categories', () => {
    render(<BudgetBreakdown dayPlan={sampleDayPlan} onViewFullBudget={vi.fn()} />);

    expect(screen.getByText(/Day 1 Cost Breakdown/i)).toBeInTheDocument();
    expect(screen.getByText('₹250')).toBeInTheDocument();
    expect(screen.getByText('₹400')).toBeInTheDocument();
    expect(screen.getByText('₹150')).toBeInTheDocument();
    expect(screen.getByText('₹200')).toBeInTheDocument();
    expect(screen.getByText('₹1,000')).toBeInTheDocument(); // Total: 250 + 400 + 150 + 200 = 1000
  });

  it('calls onViewFullBudget when View Full Trip Budget button is clicked', () => {
    const handleViewFullBudget = vi.fn();
    render(<BudgetBreakdown dayPlan={sampleDayPlan} onViewFullBudget={handleViewFullBudget} />);

    const button = screen.getByRole('button', { name: /View Full Trip Budget/i });
    expect(button).toBeInTheDocument();
    fireEvent.click(button);

    expect(handleViewFullBudget).toHaveBeenCalledTimes(1);
  });

  it('handles empty or zero-cost activities safely without NaN', () => {
    const freeDayPlan = {
      day: 2,
      activities: [
        { name: 'Mehtab Bagh sunset view', estimated_cost: 0, activity_type: 'Sightseeing' },
      ]
    };
    render(<BudgetBreakdown dayPlan={freeDayPlan} onViewFullBudget={vi.fn()} />);

    expect(screen.getByText(/Day 2 Cost Breakdown/i)).toBeInTheDocument();
    expect(screen.getAllByText('₹0').length).toBeGreaterThanOrEqual(1);
  });
});
