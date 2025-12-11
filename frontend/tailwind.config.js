/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        // Primary Theme Colors - Darker
        background: '#0f1419',
        foreground: '#e8eaed',
        primary: '#5865f2',
        'primary-foreground': '#ffffff',
        
        // Secondary & Accent Colors - Darker
        secondary: '#1e2530',
        'secondary-foreground': '#b8bcc4',
        accent: '#2a3441',
        'accent-foreground': '#e8eaed',
        
        // UI Component Colors - Darker
        card: '#1a1f2e',
        'card-foreground': '#e8eaed',
        popover: '#1a1f2e',
        'popover-foreground': '#e8eaed',
        muted: '#252a36',
        'muted-foreground': '#8b8f98',
        
        // Utility & Form Colors - Darker
        border: '#2d3340',
        input: '#2d3340',
        ring: '#5865f2',
        
        // Status & Feedback Colors
        destructive: '#ed4245',
        'destructive-foreground': '#ffffff',
        
        // Chart & Visualization Colors - Consume (Green) / Export (Red)
        chart: {
          1: '#22c55e', // Green for consume
          2: '#16a34a',
          3: '#15803d',
          4: '#166534',
          5: '#14532d',
        },
        
        // Sidebar & Navigation Colors - Darker
        'sidebar-background': '#1a1f2e',
        'sidebar-foreground': '#e8eaed',
        'sidebar-primary': '#5865f2',
        'sidebar-primary-foreground': '#ffffff',
        'sidebar-accent': '#2a3441',
        'sidebar-accent-foreground': '#e8eaed',
        'sidebar-border': '#2d3340',
        'sidebar-ring': '#5865f2',
        
        // Phase Colors (Distinct colors for R, Y, B phases)
        'phase-r': '#f43f5e', // Rose/Pink for R phase
        'phase-y': '#38bdf8', // Light Blue/Sky for Y phase
        'phase-b': '#3b82f6', // Blue for B phase
        
        // Mode Colors (Consume/Export)
        'mode-consume': '#22c55e', // Green for consume
        'mode-export': '#ef4444',   // Red for export
      },
    },
  },
  plugins: [],
}

