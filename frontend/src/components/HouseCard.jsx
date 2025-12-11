import { getPhaseColor, getPhaseDisplayName, formatPower, isExporting } from '../utils/helpers';

/**
 * HouseCard - Displays information about a single house
 */
export function HouseCard({ house, onClick }) {
  const phaseColor = getPhaseColor(house.phase);
  const phaseDisplay = getPhaseDisplayName(house.phase);
  const exporting = isExporting(house);
  
  return (
    <div
      onClick={onClick}
      className="bg-card rounded-lg p-4 border-2 border-border hover:border-primary hover:shadow-lg hover:shadow-primary/20 transition-all cursor-pointer relative"
    >
      {/* Status indicator */}
      <div className="absolute top-3 right-3">
        <div className={`w-3 h-3 rounded-full ${exporting ? 'bg-mode-export' : 'bg-mode-consume'} animate-pulse shadow-lg ${exporting ? 'shadow-mode-export/50' : 'shadow-mode-consume/50'}`} />
      </div>

      <div className="mb-3">
        <h4 className="font-semibold text-foreground text-lg">{house.house_id}</h4>
        <div className="flex items-center gap-2 mt-1">
          <span className={`inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-${phaseColor} text-white`}>
            {phaseDisplay}
          </span>
          {exporting && (
            <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-mode-export text-white">
              EXPORT
            </span>
          )}
        </div>
      </div>

      <div className="space-y-1.5">
        <div className="flex justify-between text-sm">
          <span className="text-muted-foreground">Power</span>
          <span className="font-semibold text-foreground">{formatPower(house.power_kw)}</span>
        </div>
        <div className="flex justify-between text-sm">
          <span className="text-muted-foreground">Voltage</span>
          <span className="font-medium text-foreground">{house.voltage.toFixed(1)} V</span>
        </div>
      </div>
    </div>
  );
}
