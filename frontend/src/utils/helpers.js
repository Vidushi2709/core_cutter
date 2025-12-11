/**
 * Helper utility functions
 */

/**
 * Format timestamp to relative time (e.g., "5 min ago")
 */
export function formatRelativeTime(timestamp) {
  const now = new Date();
  const past = new Date(timestamp);
  const diffInSeconds = Math.floor((now - past) / 1000);

  if (diffInSeconds < 60) {
    return `${diffInSeconds} sec ago`;
  }
  
  const diffInMinutes = Math.floor(diffInSeconds / 60);
  if (diffInMinutes < 60) {
    return `${diffInMinutes} min ago`;
  }
  
  const diffInHours = Math.floor(diffInMinutes / 60);
  if (diffInHours < 24) {
    return `${diffInHours} hour${diffInHours > 1 ? 's' : ''} ago`;
  }
  
  const diffInDays = Math.floor(diffInHours / 24);
  return `${diffInDays} day${diffInDays > 1 ? 's' : ''} ago`;
}

/**
 * Get phase color based on phase name
 */
export function getPhaseColor(phase) {
  const colors = {
    'L1': 'phase-r',
    'R': 'phase-r',
    'L2': 'phase-y',
    'Y': 'phase-y',
    'L3': 'phase-b',
    'B': 'phase-b',
  };
  return colors[phase] || 'gray-500';
}

/**
 * Get phase display name
 */
export function getPhaseDisplayName(phase) {
  const names = {
    'L1': 'R',
    'L2': 'Y',
    'L3': 'B',
  };
  return names[phase] || phase;
}

/**
 * Format power value
 */
export function formatPower(powerKw) {
  return `${Math.abs(powerKw).toFixed(1)} kW`;
}

/**
 * Format voltage value
 */
export function formatVoltage(voltage) {
  return `${voltage.toFixed(1)} V`;
}

/**
 * Get status color based on value and thresholds
 */
export function getStatusColor(value, type = 'voltage') {
  if (type === 'voltage') {
    if (value < 200) return 'destructive';
    if (value > 250) return 'destructive';
    return 'mode-consume';
  }
  
  if (type === 'imbalance') {
    if (value > 0.6) return 'destructive';
    if (value > 0.15) return 'phase-y';
    return 'mode-consume';
  }
  
  return 'mode-consume';
}

/**
 * Check if a house is exporting
 */
export function isExporting(house) {
  return house.mode_reading === 'EXPORT' || house.power_kw < 0;
}
