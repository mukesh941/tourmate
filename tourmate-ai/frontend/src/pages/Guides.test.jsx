import React from 'react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { BrowserRouter } from 'react-router-dom';
import Guides from './Guides';

// Mock AuthContext
vi.mock('../context/AuthContext', () => ({
  useAuth: () => ({
    token: 'mock-token',
    user: { name: 'Test User', email: 'test@example.com' }
  })
}));

// Mock axios properly
vi.mock('axios', () => {
  const mockAxiosInstance = {
    get: vi.fn(() => Promise.reject(new Error("Network Error"))),
    post: vi.fn(() => Promise.resolve({ data: { success: true, data: { id: "TM-TEST-01" } } })),
    interceptors: {
      request: { use: vi.fn(), eject: vi.fn() },
      response: { use: vi.fn(), eject: vi.fn() }
    }
  };
  return {
    default: {
      ...mockAxiosInstance,
      create: vi.fn(() => mockAxiosInstance)
    }
  };
});

const renderGuides = () => {
  return render(
    <BrowserRouter>
      <Guides />
    </BrowserRouter>
  );
};

describe('Guides Page', () => {
  beforeEach(() => {
    localStorage.clear();
    vi.clearAllMocks();
  });

  it('renders without crashing even when backend API is offline', async () => {
    renderGuides();
    expect(screen.getByText(/Hire a Local Guide/i)).toBeInTheDocument();
    
    // Should display curated guides
    await waitFor(() => {
      expect(screen.getByText(/Rajesh Kumar Sharma/i)).toBeInTheDocument();
      expect(screen.getByText(/Meenakshi Rathore/i)).toBeInTheDocument();
    });
  });

  it('filters guides by search text', async () => {
    renderGuides();
    await waitFor(() => {
      expect(screen.getByText(/Rajesh Kumar Sharma/i)).toBeInTheDocument();
    });

    const searchInput = screen.getByPlaceholderText(/Search by city, monument/i);
    fireEvent.change(searchInput, { target: { value: 'Jaipur' } });

    expect(screen.getByText(/Meenakshi Rathore/i)).toBeInTheDocument();
    expect(screen.queryByText(/Rajesh Kumar Sharma/i)).not.toBeInTheDocument();
  });

  it('opens booking modal and confirms booking locally when submitted', async () => {
    renderGuides();
    await waitFor(() => {
      expect(screen.getByText(/Rajesh Kumar Sharma/i)).toBeInTheDocument();
    });

    const bookButtons = screen.getAllByRole('button', { name: /Book Guided Tour/i });
    fireEvent.click(bookButtons[0]);

    // Modal should be open
    expect(screen.getByText(/Direct Expert Booking/i)).toBeInTheDocument();
    expect(screen.getByText(/Confirm Booking/i)).toBeInTheDocument();

    // Submit booking
    const confirmButton = screen.getByRole('button', { name: /Confirm Booking/i });
    fireEvent.click(confirmButton);

    await waitFor(() => {
      expect(screen.getByText(/Booking Confirmed/i)).toBeInTheDocument();
    });

    // Check localStorage
    const stored = JSON.parse(localStorage.getItem('tourmate_guide_bookings') || '[]');
    expect(stored.length).toBeGreaterThan(0);
    expect(stored[0].guide.name).toBe('Meenakshi Rathore');
  });

  it('allows switching to My Bookings tab', async () => {
    // Pre-populate a booking
    localStorage.setItem('tourmate_guide_bookings', JSON.stringify([
      {
        id: 'TM-PRE-01',
        guide: { name: 'Amanjot Singh Ahluwalia', location: 'New Delhi', hourly_rate: 700 },
        date: '2026-10-10',
        hours: 4,
        total_price: 2800,
        status: 'Confirmed'
      }
    ]));

    renderGuides();
    const myBookingsTab = screen.getByRole('button', { name: /My Bookings/i });
    fireEvent.click(myBookingsTab);

    expect(screen.getByText(/My Booked Guides/i)).toBeInTheDocument();
    expect(screen.getByText(/Amanjot Singh Ahluwalia/i)).toBeInTheDocument();
    expect(screen.getByText(/Booking ID: TM-PRE-01/i)).toBeInTheDocument();
  });
});
