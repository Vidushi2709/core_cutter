import { formatRelativeTime, getPhaseColor, getPhaseDisplayName } from '../utils/helpers';

/**
 * SwitchActivityItem - Displays a single switch event in the activity feed
 */
export function SwitchActivityItem({ switchEvent }) {
  const fromColor = getPhaseColor(switchEvent.from_phase);
  const toColor = getPhaseColor(switchEvent.to_phase);
  const fromDisplay = getPhaseDisplayName(switchEvent.from_phase);
  const toDisplay = getPhaseDisplayName(switchEvent.to_phase);
  
  // Determine icon based on reason
  const getIcon = (reason) => {
    if (reason.toLowerCase().includes('balance')) {
      return (
        <div className="w-8 h-8 rounded-full bg-mode-consume flex items-center justify-center">
          <svg className="w-4 h-4 text-white" fill="currentColor" viewBox="0 0 20 20">
            <path d="M10 12a2 2 0 100-4 2 2 0 000 4z" />
            <path fillRule="evenodd" d="M.458 10C1.732 5.943 5.522 3 10 3s8.268 2.943 9.542 7c-1.274 4.057-5.064 7-9.542 7S1.732 14.057.458 10zM14 10a4 4 0 11-8 0 4 4 0 018 0z" clipRule="evenodd" />
          </svg>
        </div>
      );
    }
    if (reason.toLowerCase().includes('voltage')) {
      return (
        <div className="w-8 h-8 rounded-full bg-phase-y flex items-center justify-center">
          <svg className="w-4 h-4 text-white" fill="currentColor" viewBox="0 0 20 20">
            <path fillRule="evenodd" d="M11.3 1.046A1 1 0 0112 2v5h4a1 1 0 01.82 1.573l-7 10A1 1 0 018 18v-5H4a1 1 0 01-.82-1.573l7-10a1 1 0 011.12-.38z" clipRule="evenodd" />
          </svg>
        </div>
      );
    }
    return (
      <div className="w-8 h-8 rounded-full bg-primary flex items-center justify-center">
        <svg className="w-4 h-4 text-white" fill="currentColor" viewBox="0 0 20 20">
          <path fillRule="evenodd" d="M4 2a1 1 0 011 1v2.101a7.002 7.002 0 0111.601 2.566 1 1 0 11-1.885.666A5.002 5.002 0 005.999 7H9a1 1 0 010 2H4a1 1 0 01-1-1V3a1 1 0 011-1zm.008 9.057a1 1 0 011.276.61A5.002 5.002 0 0014.001 13H11a1 1 0 110-2h5a1 1 0 011 1v5a1 1 0 11-2 0v-2.101a7.002 7.002 0 01-11.601-2.566 1 1 0 01.61-1.276z" clipRule="evenodd" />
        </svg>
      </div>
    );
  };

  return (
    <div className="flex gap-3 p-3 rounded-lg hover:bg-muted/50 transition-colors">
      {getIcon(switchEvent.reason)}
      
      <div className="flex-1 min-w-0">
        <div className="flex items-center gap-2 flex-wrap">
          <span className="font-semibold text-foreground">{switchEvent.house_id}</span>
          <span className={`inline-flex items-center px-1.5 py-0.5 rounded text-xs font-medium bg-${fromColor} text-white`}>
            {fromDisplay}
          </span>
          <svg className="w-4 h-4 text-muted-foreground" fill="currentColor" viewBox="0 0 20 20">
            <path fillRule="evenodd" d="M10.293 3.293a1 1 0 011.414 0l6 6a1 1 0 010 1.414l-6 6a1 1 0 01-1.414-1.414L14.586 11H3a1 1 0 110-2h11.586l-4.293-4.293a1 1 0 010-1.414z" clipRule="evenodd" />
          </svg>
          <span className={`inline-flex items-center px-1.5 py-0.5 rounded text-xs font-medium bg-${toColor} text-white`}>
            {toDisplay}
          </span>
        </div>
        <p className="text-xs text-muted-foreground mt-1 truncate">{switchEvent.reason}</p>
      </div>
      
      <div className="text-xs text-muted-foreground whitespace-nowrap">
        {formatRelativeTime(switchEvent.timestamp)}
      </div>
    </div>
  );
}
