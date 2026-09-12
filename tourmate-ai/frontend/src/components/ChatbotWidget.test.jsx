import { render, screen, fireEvent } from '@testing-library/react';
import ChatbotWidget from './ChatbotWidget';
import { describe, it, expect, vi, beforeEach } from 'vitest';

// Mock scrollIntoView for jsdom
window.HTMLElement.prototype.scrollIntoView = vi.fn();

// Mock AuthContext
vi.mock('../context/AuthContext', () => ({
  useAuth: () => ({
    token: 'mock-token',
    user: { id: 'user1', name: 'Alice Explorer' }
  })
}));

// Mock react-router-dom
vi.mock('react-router-dom', () => ({
  useLocation: () => ({ pathname: '/dashboard' })
}));

// Mock react-i18next
vi.mock('react-i18next', () => ({
  useTranslation: () => ({
    i18n: { language: 'en' }
  })
}));

describe('ChatbotWidget Component', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders the floating open chat button initially', () => {
    render(<ChatbotWidget />);
    const openBtn = screen.getByRole('button');
    expect(openBtn).toBeTruthy();
  });

  it('opens chat window and renders greeting when clicked', () => {
    render(<ChatbotWidget />);
    const openBtn = screen.getByRole('button');
    fireEvent.click(openBtn);

    // Chat header should show TourMate Guide
    expect(screen.getByText('TourMate Guide')).toBeTruthy();
    // Input placeholder
    expect(screen.getByPlaceholderText('Ask about places, tips...')).toBeTruthy();
  });

  it('allows user to type into the message input', () => {
    render(<ChatbotWidget />);
    const openBtn = screen.getByRole('button');
    fireEvent.click(openBtn);

    const input = screen.getByPlaceholderText('Ask about places, tips...');
    fireEvent.change(input, { target: { value: 'Recommend places in Jaipur' } });
    expect(input.value).toBe('Recommend places in Jaipur');
  });
});
