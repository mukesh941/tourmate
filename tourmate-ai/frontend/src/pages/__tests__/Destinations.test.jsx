import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { BrowserRouter } from 'react-router-dom';
import Destinations from '../Destinations';
import * as placesApi from '../../api/places';

jest.mock('../../api/places');

const mockDestinations = {
  page: 1,
  page_size: 24,
  total: 7586,
  total_pages: 317,
  results: [
    { id: "1", name: "Agra", state: "UP", country: "India", description: "Taj Mahal", cover_image: "https://images.unsplash.com/photo" },
    { id: "2", name: "4 Arm (Kharwali)", state: "Rajasthan", country: "India", description: "", cover_image: "data:image/svg+xml;charset=UTF-8,..." },
  ]
};

const mockSearchDestinations = {
  page: 1,
  page_size: 24,
  total: 1,
  total_pages: 1,
  results: [
    { id: "2", name: "4 Arm (Kharwali)", state: "Rajasthan", country: "India", description: "", cover_image: "data:image/svg+xml;charset=UTF-8,..." },
  ]
};

describe('Destinations Page', () => {
  beforeEach(() => {
    placesApi.getDestinations.mockResolvedValue(mockDestinations);
  });

  test('renders popular destinations and handles missing images gracefully', async () => {
    render(<BrowserRouter><Destinations /></BrowserRouter>);
    
    expect(screen.getByText(/Explore Destinations/i)).toBeInTheDocument();
    
    await waitFor(() => {
      expect(screen.getByText('Agra')).toBeInTheDocument();
      expect(screen.getByText('4 Arm (Kharwali)')).toBeInTheDocument();
    });
    
    // Verify cover images are assigned properly
    const images = screen.getAllByRole('img');
    expect(images[0]).toHaveAttribute('src', 'https://images.unsplash.com/photo');
  });

  test('search finds obscure destinations', async () => {
    render(<BrowserRouter><Destinations /></BrowserRouter>);
    
    placesApi.getDestinations.mockResolvedValueOnce(mockSearchDestinations);
    
    const searchInput = screen.getByPlaceholderText(/Search destinations/i);
    fireEvent.change(searchInput, { target: { value: '4 Arm' } });
    
    const searchForm = searchInput.closest('form');
    fireEvent.submit(searchForm);
    
    await waitFor(() => {
      expect(placesApi.getDestinations).toHaveBeenCalledWith({ page: 1, page_size: 24, search: '4 Arm' });
    });
  });

  test('pagination load more works', async () => {
    render(<BrowserRouter><Destinations /></BrowserRouter>);
    
    await waitFor(() => {
      expect(screen.getByText('Load More Destinations')).toBeInTheDocument();
    });
    
    placesApi.getDestinations.mockResolvedValueOnce(mockDestinations);
    
    fireEvent.click(screen.getByText('Load More Destinations'));
    
    await waitFor(() => {
      expect(placesApi.getDestinations).toHaveBeenCalledWith({ page: 2, page_size: 24, search: '' });
    });
  });
});
