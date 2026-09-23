import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import { BrowserRouter } from "react-router-dom";
import { describe, it, expect, vi, beforeEach } from "vitest";
import ClusteredMapView from "./ClusteredMapView";
import * as googlePlacesApi from "../services/googlePlacesApi";

// Mock AuthContext
vi.mock("../context/AuthContext", () => ({
  useAuth: () => ({
    token: "mock-token-123",
    user: { id: "1", name: "Tester" },
  }),
}));

const mockLayerGroup = {
  addTo: vi.fn().mockReturnThis(),
  clearLayers: vi.fn().mockReturnThis(),
  addLayer: vi.fn().mockReturnThis(),
};

const mockMap = {
  setView: vi.fn().mockReturnThis(),
  panTo: vi.fn().mockReturnThis(),
  fitBounds: vi.fn().mockReturnThis(),
  remove: vi.fn(),
};

// Mock Leaflet
vi.mock("leaflet", () => {
  const markerMock = {
    on: vi.fn().mockReturnThis(),
    bindPopup: vi.fn().mockReturnThis(),
    addTo: vi.fn().mockReturnThis(),
  };

  const tileLayerMock = {
    addTo: vi.fn().mockReturnThis(),
  };

  const controlMock = {
    addTo: vi.fn().mockReturnThis(),
  };

  return {
    default: {
      map: vi.fn(() => mockMap),
      layerGroup: vi.fn(() => mockLayerGroup),
      marker: vi.fn(() => markerMock),
      tileLayer: vi.fn(() => tileLayerMock),
      divIcon: vi.fn((opts) => opts),
      latLngBounds: vi.fn(() => ({
        isValid: () => true,
        extend: vi.fn(),
      })),
      control: {
        zoom: vi.fn(() => controlMock),
      },
      Icon: {
        Default: {
          prototype: {},
          mergeOptions: vi.fn(),
        },
      },
    },
  };
});

describe("ClusteredMapView (Bug #10)", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("renders without requiring VITE_GOOGLE_MAPS_API_KEY", () => {
    render(
      <BrowserRouter>
        <ClusteredMapView />
      </BrowserRouter>
    );

    // Header exists
    expect(screen.getAllByText(/AI Cluster Map/i).length).toBeGreaterThan(0);
    expect(screen.getByPlaceholderText(/Search city or destination/i)).toBeTruthy();

    // No error about missing VITE_GOOGLE_MAPS_API_KEY is shown
    expect(
      screen.queryByText(/VITE_GOOGLE_MAPS_API_KEY is not set/i)
    ).toBeNull();
    expect(
      screen.queryByText(/Google Maps Unavailable/i)
    ).toBeNull();
  });

  it("displays cluster filters and travel cluster range", () => {
    render(
      <BrowserRouter>
        <ClusteredMapView />
      </BrowserRouter>
    );

    expect(screen.getByText(/Travel Clusters/i)).toBeTruthy();
    expect(screen.getByText(/Distance/i)).toBeTruthy();
    expect(screen.getByText(/Category/i)).toBeTruthy();
  });

  it("initializes Leaflet and renders welcome state", () => {
    render(
      <BrowserRouter>
        <ClusteredMapView />
      </BrowserRouter>
    );

    expect(screen.getAllByText(/Explore India/i).length).toBeGreaterThan(0);
  });

  it("searches places, clusters them, and adds markers to Leaflet map", async () => {
    const mockPlaces = [
      {
        id: "p1",
        name: "Gateway of India",
        latitude: 18.922,
        longitude: 72.8347,
        category_name: "heritage",
        address: "Apollo Bandar, Mumbai",
      },
      {
        id: "p2",
        name: "Marine Drive",
        latitude: 18.944,
        longitude: 72.823,
        category_name: "nature",
        address: "Netaji Subhash Chandra Bose Rd, Mumbai",
      },
    ];

    const mockClusters = {
      k: 2,
      clusters: [
        {
          cluster_id: 0,
          centroid: [18.933, 72.828],
          places: mockPlaces,
        },
      ],
    };

    vi.spyOn(googlePlacesApi, "searchByText").mockResolvedValueOnce(mockPlaces);
    vi.spyOn(googlePlacesApi, "clusterPlaces").mockResolvedValueOnce(mockClusters);

    render(
      <BrowserRouter>
        <ClusteredMapView />
      </BrowserRouter>
    );

    const input = screen.getByPlaceholderText(/Search city or destination/i);
    fireEvent.change(input, { target: { value: "Mumbai" } });

    const submitButtons = screen.getAllByRole("button", { type: "submit" });
    fireEvent.click(submitButtons[0]);

    await waitFor(() => {
      expect(googlePlacesApi.searchByText).toHaveBeenCalledWith(
        expect.objectContaining({ query: "Mumbai" })
      );
      expect(googlePlacesApi.clusterPlaces).toHaveBeenCalledWith(
        expect.objectContaining({ places: mockPlaces })
      );
    });
  });
});
