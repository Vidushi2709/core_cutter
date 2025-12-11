/**
 * LoadingSpinner - Simple loading spinner component
 */
export function LoadingSpinner({ size = 'md' }) {
  const sizes = {
    sm: 'w-4 h-4',
    md: 'w-8 h-8',
    lg: 'w-12 h-12',
  };

  return (
    <div className="flex items-center justify-center p-8">
      <div className={`${sizes[size]} border-4 border-muted border-t-primary rounded-full animate-spin`} />
    </div>
  );
}
