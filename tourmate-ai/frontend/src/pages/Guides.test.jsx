import React from 'react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { BrowserRouter } from 'react-router-dom';
import Guides from './Guides';
import i18n from '../i18n';

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
  beforeEach(async () => {
    localStorage.clear();
    vi.clearAllMocks();
    await i18n.changeLanguage('en');
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

  it('translates content correctly when language is switched to Hindi, Kannada, Tamil, or Malayalam', async () => {
    const { unmount } = renderGuides();
    
    // Switch to Hindi
    await i18n.changeLanguage('hi');
    expect(screen.getByText(/स्थानीय गाइड बुक करें/i)).toBeInTheDocument();
    expect(screen.getByText(/मेरी बुकिंग/i)).toBeInTheDocument();
    expect(localStorage.getItem('tourmate_language')).toBe('hi');

    // Switch to Kannada
    await i18n.changeLanguage('kn');
    expect(screen.getByText(/ಸ್ಥಳೀಯ ಮಾರ್ಗದರ್ಶಿಯನ್ನು ನೇಮಿಸಿ/i)).toBeInTheDocument();
    expect(screen.getByText(/ನನ್ನ ಬುಕಿಂಗ್‌ಗಳು/i)).toBeInTheDocument();

    // Switch to Tamil
    await i18n.changeLanguage('ta');
    expect(screen.getByText(/உள்ளூர் வழிகாட்டியை அமர்த்தவும்/i)).toBeInTheDocument();
    expect(screen.getByText(/எனது முன்பதிவுகள்/i)).toBeInTheDocument();

    // Switch to Malayalam
    await i18n.changeLanguage('ml');
    expect(screen.getByText(/ഒരു പ്രാദേശിക ഗൈഡിനെ തിരഞ്ഞെടുക്കൂ/i)).toBeInTheDocument();
    expect(screen.getByText(/എന്റെ ബുക്കിംഗുകൾ/i)).toBeInTheDocument();

    unmount();
  });
});
