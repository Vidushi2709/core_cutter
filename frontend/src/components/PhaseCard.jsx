import { getPhaseColor, getPhaseDisplayName, formatPower, formatVoltage } from '../utils/helpers';

/**
 * PhaseCard - Displays detailed information about a single phase
 */
export function PhaseCard({ phase, totalPowerKw, avgVoltage, houseCount, status = 'Normal' }) {
  const phaseDisplay = getPhaseDisplayName(phase);
  const phaseColor = getPhaseColor(phase);
  
  const isNormal = status === 'Normal';
  
  return (
    <div className={`bg-${phaseColor} rounded-lg p-6 text-white relative overflow-hidden`}>
      {/* Background decoration */}
      <div className="absolute top-0 right-0 w-32 h-32 bg-white opacity-5 rounded-full -mr-16 -mt-16" />
      
      <div className="relative z-10">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-xl font-bold flex items-center gap-2">
            PHASE {phaseDisplay}
            {!isNormal && (
              <span className="w-3 h-3 bg-white rounded-full animate-pulse" />
            )}
          </h3>
          {isNormal ? (
            <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 20 20">
              <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
            </svg>
          ) : null}
        </div>

        <div className="space-y-3">
          <div>
            <p className="text-sm opacity-80">Total Power</p>
            <p className="text-2xl font-bold">{formatPower(totalPowerKw)}</p>
          </div>

          <div>
            <p className="text-sm opacity-80">Avg Voltage</p>
            <p className="text-xl font-semibold">{formatVoltage(avgVoltage)}</p>
          </div>

          <div>
            <p className="text-sm opacity-80">Houses</p>
            <p className="text-xl font-semibold">{houseCount}</p>
          </div>
        </div>
      </div>
    </div>
  );
}
