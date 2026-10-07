import { render, screen, fireEvent } from '@testing-library/react';
import PaymentSuspended from './PaymentSuspended';
import { describe, it, expect, vi } from 'vitest';

describe('PaymentSuspended Page', () => {
  it('renders the suspension warning and reason', () => {
    render(<PaymentSuspended />);

    expect(screen.getByText(/Service Suspended/i)).toBeTruthy();
    expect(screen.getByText(/TourMate is Temporarily On Hold/i)).toBeTruthy();
    expect(screen.getByText(/CRITICAL NOTICE/i)).toBeTruthy();
    expect(screen.getByText(/Reason for Suspension/i)).toBeTruthy();
  });

  it('displays the Telegram contact button pointing to @unknownman59', () => {
    render(<PaymentSuspended />);

    const telegramLink = screen.getByRole('link', { name: /Open Telegram @unknownman59/i });
    expect(telegramLink).toBeTruthy();
    expect(telegramLink.getAttribute('href')).toBe('https://t.me/unknownman59');
  });

  it('allows copying the Telegram handle', () => {
    const writeTextMock = vi.fn().mockResolvedValue(undefined);
    Object.assign(navigator, {
      clipboard: {
        writeText: writeTextMock,
      },
    });

    render(<PaymentSuspended />);

    const copyBtn = screen.getByRole('button', { name: /Copy Username/i });
    expect(copyBtn).toBeTruthy();

    fireEvent.click(copyBtn);

    expect(writeTextMock).toHaveBeenCalledWith('@unknownman59');
    expect(screen.getByText('Copied!')).toBeTruthy();
  });
});
