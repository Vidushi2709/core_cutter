import { useState } from 'react';
import { useSystemStatus } from './hooks/useSystemStatus';
import { useSwitchHistory } from './hooks/useSwitchHistory';
import { StatusCard } from './components/StatusCard';
import { PhaseCard } from './components/PhaseCard';
import { HouseCard } from './components/HouseCard';
import { SwitchActivityItem } from './components/SwitchActivityItem';
import { SystemAlert } from './components/SystemAlert';
import { LoadingSpinner } from './components/LoadingSpinner';
import { formatRelativeTime, getPhaseDisplayName } from './utils/helpers';

function App() {
  const { status, loading, error } = useSystemStatus(2000); // Faster refresh - 2 seconds
  const { history } = useSwitchHistory(2000, 5); // Only last 5 switches, refresh every 2 seconds
  const [selectedHouse, setSelectedHouse] = useState(null);

  if (loading) {
    return (
      <div className="min-h-screen bg-background flex items-center justify-center">
        <LoadingSpinner size="lg" />
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-screen bg-background flex items-center justify-center p-4">
        <div className="max-w-md w-full">
          <SystemAlert
            type="error"
            title="Connection Error"
            message={error}
          />
        </div>
      </div>
    );
  }

  if (!status) return null;

  // Calculate statistics
  const totalHouses = status.phases.reduce((sum, p) => sum + p.house_count, 0);
  const switchesToday = history.length;
  const totalPower = status.phases.reduce((sum, p) => sum + p.total_power_kw, 0);

  // Get phase distribution
  const phaseDistribution = status.phases.map(p => ({
    phase: getPhaseDisplayName(p.phase),
    power: p.total_power_kw,
    houses: p.house_count,
    color: p.phase === 'L1' ? 'phase-r' : p.phase === 'L2' ? 'phase-y' : 'phase-b',
  }));

  // Detect issues
  const hasImbalanceIssue = status.imbalance_kw > 0.6;
  const hasVoltageIssue = Object.keys(status.phase_issues).length > 0;
  const hasPowerIssue = Object.keys(status.power_issues).length > 0;

  return (
    <div className="min-h-screen bg-background">
      {/* Header */}
      <header className="bg-card text-foreground shadow-lg sticky top-0 z-50 border-b border-border">
        <div className="container mx-auto px-6 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 bg-primary rounded-lg flex items-center justify-center">
                <svg className="w-6 h-6 text-white" fill="currentColor" viewBox="0 0 20 20">
                  <path fillRule="evenodd" d="M11.3 1.046A1 1 0 0112 2v5h4a1 1 0 01.82 1.573l-7 10A1 1 0 018 18v-5H4a1 1 0 01-.82-1.573l7-10a1 1 0 011.12-.38z" clipRule="evenodd" />
                </svg>
              </div>
              <h1 className="text-2xl font-bold">Phase Balancing Controller</h1>
            </div>
            <button className="px-4 py-2 bg-primary hover:bg-primary/90 rounded-lg font-medium transition-colors text-white">
              Live Dashboard
            </button>
          </div>
        </div>
      </header>

      <main className="container mx-auto px-6 py-8 max-w-[1920px]">
        {/* Top Stats */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
          <StatusCard
            title="System Mode"
            value={
              <span className="flex items-center gap-2">
                {status.mode}
                <span className={`w-3 h-3 rounded-full ${status.mode === 'CONSUME' ? 'bg-mode-consume' : 'bg-mode-export'} animate-pulse`} />
              </span>
            }
          />
          <StatusCard
            title="Imbalance"
            value={`${status.imbalance_kw.toFixed(1)} kW`}
            subtitle={
              <div className="flex items-center gap-2">
                <div className={`w-full h-2 bg-muted rounded-full overflow-hidden`}>
                  <div
                    className={`h-full ${hasImbalanceIssue ? 'bg-destructive' : 'bg-mode-consume'}`}
                    style={{ width: `${Math.min((status.imbalance_kw / 1.0) * 100, 100)}%` }}
                  />
                </div>
              </div>
            }
          />
          <StatusCard
            title="Total Houses"
            value={totalHouses}
            subtitle="All Connected"
          />
          <StatusCard
            title="Switches Today"
            value={switchesToday}
            subtitle={history[0] ? `Last ${formatRelativeTime(history[0].timestamp)}` : 'No recent activity'}
          />
        </div>

        {/* Phase Distribution */}
        <div className="mb-8">
          <h2 className="text-xl font-bold text-foreground mb-4">Phase Distribution</h2>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            {phaseDistribution.map((phase) => (
              <div key={phase.phase} className={`bg-${phase.color} rounded-lg p-6 text-white`}>
                <div className="flex items-center justify-between mb-4">
                  <h3 className="text-2xl font-bold">{phase.phase}</h3>
                  <div className="text-right">
                    <p className="text-3xl font-bold">{phase.power.toFixed(1)} kW</p>
                    <p className="text-sm opacity-80">{phase.houses} houses</p>
                  </div>
                </div>
                <div className="w-full h-2 bg-white/20 rounded-full overflow-hidden">
                  <div
                    className="h-full bg-white rounded-full transition-all duration-500"
                    style={{ width: `${(phase.power / Math.max(totalPower, 1)) * 100}%` }}
                  />
                </div>
              </div>
            ))}
          </div>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          {/* Left Column - Phase Details */}
          <div className="lg:col-span-2 space-y-8">
            {/* Phase Details */}
            <section>
              <h2 className="text-xl font-bold text-foreground mb-4">Phase Details</h2>
              <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                {status.phases.map((phase) => (
                  <PhaseCard
                    key={phase.phase}
                    phase={phase.phase}
                    totalPowerKw={phase.total_power_kw}
                    avgVoltage={phase.avg_voltage}
                    houseCount={phase.house_count}
                    status={status.phase_issues[phase.phase] ? 'Issue' : 'Normal'}
                  />
                ))}
              </div>
            </section>

            {/* All Houses */}
            <section>
              <div className="flex items-center justify-between mb-4">
                <h2 className="text-xl font-bold text-foreground">All Houses</h2>
                <p className="text-sm text-muted-foreground">Click to view details</p>
              </div>
              <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 xl:grid-cols-5 gap-4">
                {status.phases.flatMap(phase => phase.houses).map((house) => (
                  <HouseCard
                    key={house.house_id}
                    house={house}
                    onClick={() => setSelectedHouse(house)}
                  />
                ))}
              </div>
            </section>
          </div>

          {/* Right Column - Activity & Alerts */}
          <div className="space-y-6">
            {/* System Alerts */}
            <section>
              <h2 className="text-xl font-bold text-foreground mb-4">System Alerts</h2>
              <div className="space-y-3">
                {hasImbalanceIssue && (
                  <SystemAlert
                    type="warning"
                    title="Phase Imbalance"
                    message={`Phase ${getPhaseDisplayName(status.phases.reduce((max, p) => p.total_power_kw > max.total_power_kw ? p : max).phase)} is ${status.imbalance_kw.toFixed(1)} kW higher than Phase ${getPhaseDisplayName(status.phases.reduce((min, p) => p.total_power_kw < min.total_power_kw ? p : min).phase)}`}
                  />
                )}
                {hasVoltageIssue && Object.entries(status.phase_issues).map(([phase, issue]) => (
                  <SystemAlert
                    key={phase}
                    type="error"
                    title={`Phase ${getPhaseDisplayName(phase)} Voltage Issue`}
                    message={issue}
                  />
                ))}
                {!hasImbalanceIssue && !hasVoltageIssue && !hasPowerIssue && (
                  <SystemAlert
                    type="success"
                    title="✓ All Systems Normal"
                    message="Voltage levels within acceptable range"
                  />
                )}
              </div>
            </section>

            {/* Recent Switch Activity */}
            <section>
              <h2 className="text-xl font-bold text-foreground mb-4">Recent Switch Activity</h2>
              <div className="bg-card rounded-lg border border-border p-4 max-h-[600px] overflow-y-auto">
                {history.length > 0 ? (
                  <div className="space-y-2">
                    {history.slice(0, 10).map((switchEvent, index) => (
                      <SwitchActivityItem key={index} switchEvent={switchEvent} />
                    ))}
                  </div>
                ) : (
                  <p className="text-center text-muted-foreground py-8">No recent switch activity</p>
                )}
              </div>
            </section>
          </div>
        </div>

        {/* Footer */}
        <footer className="mt-12 py-6 border-t border-border">
          <div className="text-center text-sm text-muted-foreground">
            <p>Last updated: {formatRelativeTime(status.timestamp)}</p>
            <p className="mt-1">Phase Balancing Controller v2.0</p>
          </div>
        </footer>
      </main>

      {/* House Details Modal */}
      {selectedHouse && (
        <div
          className="fixed inset-0 bg-black/70 flex items-center justify-center p-4 z-50 backdrop-blur-sm"
          onClick={() => setSelectedHouse(null)}
        >
          <div
            className="bg-card rounded-lg p-6 max-w-md w-full shadow-xl border border-border"
            onClick={(e) => e.stopPropagation()}
          >
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-xl font-bold text-foreground">{selectedHouse.house_id}</h3>
              <button
                onClick={() => setSelectedHouse(null)}
                className="text-muted-foreground hover:text-foreground"
              >
                <svg className="w-6 h-6" fill="currentColor" viewBox="0 0 20 20">
                  <path fillRule="evenodd" d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z" clipRule="evenodd" />
                </svg>
              </button>
            </div>
            <div className="space-y-4">
              <div>
                <p className="text-sm text-muted-foreground mb-1">Phase</p>
                <p className="text-lg font-semibold text-foreground">
                  {getPhaseDisplayName(selectedHouse.phase)}
                </p>
              </div>
              <div>
                <p className="text-sm text-muted-foreground mb-1">Power</p>
                <p className="text-lg font-semibold text-foreground">
                  {selectedHouse.power_kw.toFixed(3)} kW
                </p>
              </div>
              <div>
                <p className="text-sm text-muted-foreground mb-1">Voltage</p>
                <p className="text-lg font-semibold text-foreground">
                  {selectedHouse.voltage.toFixed(1)} V
                </p>
              </div>
              <div>
                <p className="text-sm text-muted-foreground mb-1">Current</p>
                <p className="text-lg font-semibold text-foreground">
                  {selectedHouse.current.toFixed(2)} A
                </p>
              </div>
              <div>
                <p className="text-sm text-muted-foreground mb-1">Mode</p>
                <p className="text-lg font-semibold text-foreground">
                  {selectedHouse.mode_reading}
                </p>
              </div>
              <div>
                <p className="text-sm text-muted-foreground mb-1">Last Updated</p>
                <p className="text-lg font-semibold text-foreground">
                  {formatRelativeTime(selectedHouse.timestamp)}
                </p>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

export default App;
