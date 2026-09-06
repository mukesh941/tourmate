import { render, screen } from '@testing-library/react';
import { BrowserRouter } from 'react-router-dom';
import { AuthProvider } from '../context/AuthContext';
import Navbar from './Navbar';
import { describe, it, expect, vi } from 'vitest';

// Mock translation hook
vi.mock('react-i18next', () => ({
  useTranslation: () => ({
    t: (str) => str,
    i18n: {
      changeLanguage: () => new Promise(() => {}),
      language: 'en'
    }
  })
}));

describe('Navbar Component', () => {
  it('renders the brand name', () => {
    render(
      <BrowserRouter>
        <AuthProvider>
          <Navbar toggleDarkMode={() => {}} darkMode={false} />
        </AuthProvider>
      </BrowserRouter>
    );
    
    // Using string matching for the brand name
    expect(screen.getByText('TourMate AI')).toBeTruthy();
  });
});
