/**
 * StatusCard - Reusable card component for displaying metrics
 */
export function StatusCard({ title, value, subtitle, icon, className = '' }) {
  return (
    <div className={`bg-card rounded-lg p-6 border border-border ${className}`}>
      <div className="flex items-start justify-between">
        <div>
          <p className="text-sm font-medium text-muted-foreground uppercase tracking-wide">
            {title}
          </p>
          <p className="text-3xl font-bold text-foreground mt-2">{value}</p>
          {subtitle && (
            <p className="text-sm text-muted-foreground mt-1">{subtitle}</p>
          )}
        </div>
        {icon && <div className="text-muted-foreground">{icon}</div>}
      </div>
    </div>
  );
}
