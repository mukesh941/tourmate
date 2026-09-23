import { render, screen, fireEvent } from '@testing-library/react';
import { describe, it, expect, vi } from 'vitest';
import React from 'react';
import FullTripBudgetModal from './FullTripBudgetModal';

describe('FullTripBudgetModal Component', () => {
  const sampleItinerary = {
    route_name: 'Balanced',
    transportation: {
      mode: 'flight',
      estimated_distance_km: 480,
      estimated_cost_min: 2500,
      estimated_cost_max: 5000,
      recommendation_note: 'Fastest transit option'
    },
    schedule: [
      {
        day: 1,
        activities: [
          { name: 'Taj Mahal', estimated_cost: 250, activity_type: 'Sightseeing', entryFee: '₹250' },
          { name: 'Agra Fort', estimated_cost: 250, activity_type: 'Monument', entryFee: '₹250' },
        ]
      },
      {
        day: 2,
        activities: [
          { name: 'Mehtab Bagh', estimated_cost: 50, activity_type: 'Garden', entryFee: '₹50' },
          { name: 'Fatehpur Sikri', estimated_cost: 250, activity_type: 'Heritage', entryFee: '₹250' },
        ]
      }
    ]
  };

  const sampleHotel = {
    id: 'hotel-123',
    name: 'ITC Mughal Resort & Spa',
    city: 'Agra',
    price_per_night: 6500,
    rating: 4.8
  };

  it('renders transparent full trip budget when open', () => {
    render(
      <FullTripBudgetModal 
        isOpen={true}
        onClose={vi.fn()}
        itinerary={sampleItinerary}
        destinationName="Agra"
        days={2}
        travelType="Couple"
        selectedHotel={sampleHotel}
        transportationMode="flight"
        originName="New Delhi"
      />
    );

    expect(screen.getByText(/Agra Full Trip Budget/i)).toBeInTheDocument();
    expect(screen.getByText(/2 Days \(1 Nights\)/i)).toBeInTheDocument();
    expect(screen.getByText('ITC Mughal Resort & Spa')).toBeInTheDocument();
    // 6500 * 1 night = 6500
    expect(screen.getByText(/₹6,500\/night × 1 night/i)).toBeInTheDocument();
    expect(screen.getByText(/₹800/i)).toBeInTheDocument(); // Attraction entry fees: 250 + 250 + 50 + 250 = 800
  });

  it('handles missing accommodation price safely without fake values', () => {
    const hotelWithoutPrice = {
      id: 'hotel-456',
      name: 'Boutique Heritage Haveli',
      city: 'Agra',
      price_per_night: null,
    };

    render(
      <FullTripBudgetModal 
        isOpen={true}
        onClose={vi.fn()}
        itinerary={sampleItinerary}
        destinationName="Agra"
        days={3}
        travelType="Solo"
        selectedHotel={hotelWithoutPrice}
      />
    );

    expect(screen.getByText('Boutique Heritage Haveli')).toBeInTheDocument();
    expect(screen.getByText(/Price unavailable/i)).toBeInTheDocument();
  });

  it('handles no hotel selected state gracefully', () => {
    render(
      <FullTripBudgetModal 
        isOpen={true}
        onClose={vi.fn()}
        itinerary={sampleItinerary}
        destinationName="Agra"
        days={1}
        selectedHotel={null}
      />
    );

    expect(screen.getByText(/No hotel selected yet/i)).toBeInTheDocument();
    expect(screen.getByText(/Not included/i)).toBeInTheDocument();
  });

  it('calls onClose when close button is clicked', () => {
    const handleClose = vi.fn();
    render(
      <FullTripBudgetModal 
        isOpen={true}
        onClose={handleClose}
        itinerary={sampleItinerary}
        destinationName="Agra"
        days={2}
      />
    );

    const closeBtn = screen.getByRole('button', { name: /Close Budget Details/i });
    fireEvent.click(closeBtn);
    expect(handleClose).toHaveBeenCalledTimes(1);
  });
});
