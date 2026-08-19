/**
 * Display-only money formatting. The authoritative amounts are always the
 * strings the backend computes (Decimal); this only formats them for the UI
 * and never re-derives cost math (ADR-009).
 */
export function formatMoney(amount: string, currency: string): string {
  const n = Number(amount);
  try {
    return new Intl.NumberFormat("es-AR", {
      style: "currency",
      currency,
      maximumFractionDigits: 2,
    }).format(n);
  } catch {
    return `${amount} ${currency}`;
  }
}
