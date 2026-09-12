import { render, screen, fireEvent } from '@testing-library/react';
import OnboardingModal from './OnboardingModal';
import { describe, it, expect, vi } from 'vitest';

// Mock AuthContext
vi.mock('../context/AuthContext', () => ({
  useAuth: () => ({
    token: 'mock-token',
    user: { id: 'user1', name: 'Explorer' }
  })
}));

describe('OnboardingModal Component', () => {
  it('does not render when isOpen is false', () => {
    const { container } = render(
      <OnboardingModal isOpen={false} onClose={() => {}} onComplete={() => {}} />
    );
    expect(container.firstChild).toBeNull();
  });

  it('renders Step 1 with interests when isOpen is true', () => {
    render(
      <OnboardingModal isOpen={true} onClose={() => {}} onComplete={() => {}} />
    );

    expect(screen.getByText('What are your main interests?')).toBeTruthy();
    expect(screen.getByText('History')).toBeTruthy();
    expect(screen.getByText('Nature')).toBeTruthy();
    expect(screen.getByText('Next Step →')).toBeTruthy();
  });

  it('toggles interests and navigates to Step 2', () => {
    render(
      <OnboardingModal isOpen={true} onClose={() => {}} onComplete={() => {}} />
    );

    const historyBtn = screen.getByText('History');
    fireEvent.click(historyBtn);

    const nextBtn = screen.getByText('Next Step →');
    fireEvent.click(nextBtn);

    // Step 2 should now be visible
    expect(screen.getByText('What is your typical travel style?')).toBeTruthy();
    expect(screen.getByText('Solo Explorer')).toBeTruthy();
    expect(screen.getByText('Complete Setup')).toBeTruthy();
  });
});
