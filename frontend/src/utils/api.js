/**
 * API utility functions for communicating with the Phase Balancing Controller backend
 */

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

/**
 * Fetch system status including all phases, houses, mode, and imbalance
 */
export async function getSystemStatus() {
  const response = await fetch(`${API_BASE_URL}/analytics/status`);
  if (!response.ok) {
    throw new Error('Failed to fetch system status');
  }
  return response.json();
}

/**
 * Fetch all houses with current readings
 */
export async function getAllHouses() {
  const response = await fetch(`${API_BASE_URL}/analytics/houses`);
  if (!response.ok) {
    throw new Error('Failed to fetch houses');
  }
  return response.json();
}

/**
 * Fetch switch history
 */
export async function getSwitchHistory(limit = 50) {
  const response = await fetch(`${API_BASE_URL}/analytics/switches?limit=${limit}`);
  if (!response.ok) {
    throw new Error('Failed to fetch switch history');
  }
  return response.json();
}

/**
 * Fetch details for a specific phase
 */
export async function getPhaseDetails(phase) {
  const response = await fetch(`${API_BASE_URL}/analytics/phase/${phase}`);
  if (!response.ok) {
    throw new Error(`Failed to fetch phase ${phase} details`);
  }
  return response.json();
}

/**
 * Health check
 */
export async function checkHealth() {
  const response = await fetch(`${API_BASE_URL}/health`);
  if (!response.ok) {
    throw new Error('Health check failed');
  }
  return response.json();
}
