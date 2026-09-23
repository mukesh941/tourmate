import { render, screen, fireEvent, act } from '@testing-library/react';
import ChatbotWidget from './ChatbotWidget';
import { describe, it, expect, vi, beforeEach } from 'vitest';

// Mock scrollIntoView for jsdom
window.HTMLElement.prototype.scrollIntoView = vi.fn();
window.HTMLElement.prototype.setPointerCapture = vi.fn();
window.HTMLElement.prototype.releasePointerCapture = vi.fn();

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

// Mock localStorage for jsdom
const localStorageMock = (() => {
  let store = {};
  return {
    getItem: (key) => store[key] || null,
    setItem: (key, value) => {
      store[key] = String(value);
    },
    removeItem: (key) => {
      delete store[key];
    },
    clear: () => {
      store = {};
    },
  };
})();
Object.defineProperty(window, 'localStorage', { value: localStorageMock, writable: true });

describe('ChatbotWidget Component', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    window.localStorage.clear();
    // Default desktop dimensions
    window.innerWidth = 1024;
    window.innerHeight = 768;
  });

  it('renders the floating open chat button with accessibility attributes', () => {
    render(<ChatbotWidget />);
    const openBtn = screen.getByRole('button', { name: /Open TourMate AI Guide/i });
    expect(openBtn).toBeTruthy();
    expect(openBtn.getAttribute('aria-expanded')).toBe('false');
  });

  it('opens and closes chat window when tapped/clicked', () => {
    render(<ChatbotWidget />);
    const openBtn = screen.getByRole('button', { name: /Open TourMate AI Guide/i });
    
    // Tap to open
    fireEvent.click(openBtn);
    expect(screen.getByText('TourMate Guide')).toBeTruthy();
    expect(screen.getByPlaceholderText('Ask about places, tips...')).toBeTruthy();

    // Close button
    const closeBtn = screen.getByRole('button', { name: /Close TourMate Guide/i });
    fireEvent.click(closeBtn);
    expect(screen.queryByText('TourMate Guide')).toBeNull();
  });

  it('allows user to type into the message input', () => {
    render(<ChatbotWidget />);
    const openBtn = screen.getByRole('button', { name: /Open TourMate AI Guide/i });
    fireEvent.click(openBtn);

    const input = screen.getByPlaceholderText('Ask about places, tips...');
    fireEvent.change(input, { target: { value: 'Recommend places in Jaipur' } });
    expect(input.value).toBe('Recommend places in Jaipur');
  });

  it('positions safely above bottom navigation on mobile screen sizes', () => {
    // Mobile viewport (e.g. 390 x 844 iPhone 12/13/14)
    window.innerWidth = 390;
    window.innerHeight = 844;

    const { container } = render(<ChatbotWidget />);
    const wrapper = container.querySelector('.z-\\[50\\]');
    expect(wrapper).toBeTruthy();
    
    // Expected default top: 844 - 56 - 80 = 708px
    expect(wrapper.style.top).toBe('708px');
    // Expected default left: 390 - 56 - 16 = 318px
    expect(wrapper.style.left).toBe('318px');
  });

  it('drags using pointer events and does not trigger open on drag release', () => {
    window.innerWidth = 390;
    window.innerHeight = 844;

    const { container } = render(<ChatbotWidget />);
    const openBtn = screen.getByRole('button', { name: /Open TourMate AI Guide/i });
    const wrapper = container.querySelector('.z-\\[50\\]');

    // Initial position: 318, 708
    expect(wrapper.style.left).toBe('318px');
    expect(wrapper.style.top).toBe('708px');

    // Pointer down at (320, 710)
    fireEvent.pointerDown(openBtn, { clientX: 320, clientY: 710, pointerId: 1, button: 0 });

    // Move pointer by 50px right, 40px down
    fireEvent.pointerMove(window, { clientX: 370, clientY: 750 });

    // Pointer up
    fireEvent.pointerUp(window, { clientX: 370, clientY: 750, pointerId: 1 });

    // Simulated click on drag release must be suppressed
    fireEvent.click(openBtn);

    // Chat should NOT be open
    expect(screen.queryByText('TourMate Guide')).toBeNull();

    // Position should be updated and clamped
    // 318 + 50 = 368, but max is 390 - 56 - 12 = 322px
    expect(parseInt(wrapper.style.left)).toBeLessThanOrEqual(322);
  });

  it('persists and restores valid custom position from localStorage', () => {
    localStorage.setItem('tourmate_chatbot_pos_v2', JSON.stringify({ x: 100, y: 200 }));
    
    const { container } = render(<ChatbotWidget />);
    const wrapper = container.querySelector('.z-\\[50\\]');
    expect(wrapper.style.left).toBe('100px');
    expect(wrapper.style.top).toBe('200px');
  });

  it('gracefully handles corrupted localStorage data', () => {
    localStorage.setItem('tourmate_chatbot_pos_v2', '{ corrupt json');
    
    const { container } = render(<ChatbotWidget />);
    const wrapper = container.querySelector('.z-\\[50\\]');
    expect(wrapper).toBeTruthy();
    expect(wrapper.style.left).toBeTruthy();
    expect(wrapper.style.top).toBeTruthy();
  });

  it('supports keyboard navigation (Enter/Space)', () => {
    render(<ChatbotWidget />);
    const openBtn = screen.getByRole('button', { name: /Open TourMate AI Guide/i });

    // Press Enter to open
    fireEvent.keyDown(openBtn, { key: 'Enter', code: 'Enter' });
    expect(screen.getByText('TourMate Guide')).toBeTruthy();

    // Press Space to toggle/close
    fireEvent.keyDown(openBtn, { key: ' ', code: 'Space' });
    expect(screen.queryByText('TourMate Guide')).toBeNull();
  });

  it('re-clamps position on window resize and orientation change', () => {
    window.innerWidth = 1024;
    window.innerHeight = 768;

    const { container } = render(<ChatbotWidget />);
    const wrapper = container.querySelector('.z-\\[50\\]');

    // Now resize to small screen 375x667
    act(() => {
      window.innerWidth = 375;
      window.innerHeight = 667;
      window.dispatchEvent(new Event('resize'));
    });

    // Max X is 375 - 56 - 12 = 307px
    // Max Y is 667 - 56 - 76 = 535px
    expect(parseInt(wrapper.style.left)).toBeLessThanOrEqual(307);
    expect(parseInt(wrapper.style.top)).toBeLessThanOrEqual(535);
  });
});
