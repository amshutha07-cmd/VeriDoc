/* The mark: a V bracket (a claim coming down to its source) with a cobalt square at its point (the page it is anchored to). */
export default function LogoMark({ size = 32, className = "" }: { size?: number; className?: string }) {
  return (
    <svg width={size} height={size} viewBox="0 0 64 64" role="img" aria-label="VeriDoc Nexus" className={className}>
      <rect width="64" height="64" fill="#17181C" />
      <polyline points="12,14 32,50 52,14" fill="none" stroke="#D4F25C" strokeWidth="9" strokeLinejoin="miter" strokeLinecap="butt" />
      <rect x="26" y="44" width="12" height="12" fill="#1E3BFF" />
    </svg>
  );
}
