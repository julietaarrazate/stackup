import { ImageResponse } from "next/og";

export const size = { width: 512, height: 512 };
export const contentType = "image/png";

/** Generated app icon — the STACKUP mark on the brand background. */
export default function Icon() {
  return new ImageResponse(
    (
      <div
        style={{
          width: "100%",
          height: "100%",
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          background: "#0b0c10",
        }}
      >
        <svg width="320" height="320" viewBox="0 0 24 24" fill="none">
          <path d="M12 3 21 8l-9 5-9-5 9-5Z" fill="#8b5cf6" />
          <path
            d="m3 12 9 5 9-5"
            stroke="#8b5cf6"
            strokeWidth="1.8"
            strokeLinejoin="round"
            strokeLinecap="round"
            opacity="0.6"
          />
          <path
            d="m3 16 9 5 9-5"
            stroke="#8b5cf6"
            strokeWidth="1.8"
            strokeLinejoin="round"
            strokeLinecap="round"
            opacity="0.3"
          />
        </svg>
      </div>
    ),
    size,
  );
}
