/**
 * STACKUP wordmark + mark. Own visual identity (not derived from any
 * third-party brand). The mark is a stacked-layers glyph evoking a "stack"
 * of costs.
 */
export function BrandMark({ className }: { className?: string }) {
  return (
    <svg
      viewBox="0 0 24 24"
      fill="none"
      className={className}
      aria-hidden="true"
    >
      <path
        d="M12 3 21 8l-9 5-9-5 9-5Z"
        fill="var(--primary)"
        opacity="0.95"
      />
      <path
        d="m3 12 9 5 9-5"
        stroke="var(--primary)"
        strokeWidth="1.8"
        strokeLinejoin="round"
        strokeLinecap="round"
        opacity="0.6"
      />
      <path
        d="m3 16 9 5 9-5"
        stroke="var(--primary)"
        strokeWidth="1.8"
        strokeLinejoin="round"
        strokeLinecap="round"
        opacity="0.3"
      />
    </svg>
  );
}

export function BrandWordmark({ className }: { className?: string }) {
  return (
    <span className={`inline-flex items-center gap-2 ${className ?? ""}`}>
      <BrandMark className="h-6 w-6" />
      <span className="text-lg font-semibold tracking-tight">STACKUP</span>
    </span>
  );
}
