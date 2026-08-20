const PALETTE = [
  "#8b5cf6",
  "#22b8cf",
  "#f7a53b",
  "#35c17f",
  "#f06a7e",
  "#6d3bef",
  "#3b82f6",
];

function colorFor(name: string): string {
  let hash = 0;
  for (let i = 0; i < name.length; i++) {
    hash = (hash << 5) - hash + name.charCodeAt(i);
    hash |= 0;
  }
  return PALETTE[Math.abs(hash) % PALETTE.length]!;
}

export function EntityIcon({
  name,
  size = "md",
}: {
  name: string;
  size?: "sm" | "md";
}) {
  const dim = size === "sm" ? "h-7 w-7 text-xs" : "h-9 w-9 text-sm";
  return (
    <span
      aria-hidden="true"
      className={`inline-flex shrink-0 items-center justify-center rounded-lg font-semibold text-white ${dim}`}
      style={{ background: colorFor(name || "?") }}
    >
      {(name || "?").trim().charAt(0).toUpperCase()}
    </span>
  );
}
