import { ImageResponse } from "next/og"

export const runtime = "edge"

export const alt = "D23 AI - Bharat's WhatsApp AI Assistant"
export const size = {
  width: 1200,
  height: 630,
}
export const contentType = "image/png"

export default async function Image() {
  return new ImageResponse(
    (
      <div
        style={{
          height: "100%",
          width: "100%",
          display: "flex",
          flexDirection: "column",
          alignItems: "center",
          justifyContent: "center",
          backgroundColor: "#000",
          backgroundImage: "linear-gradient(135deg, #1a1a2e 0%, #0a0a0a 100%)",
          position: "relative",
        }}
      >
        {/* Gradient blobs */}
        <div
          style={{
            position: "absolute",
            top: -100,
            left: -100,
            width: 400,
            height: 400,
            borderRadius: "50%",
            background: "radial-gradient(circle, rgba(139,92,246,0.3) 0%, transparent 70%)",
            filter: "blur(60px)",
          }}
        />
        <div
          style={{
            position: "absolute",
            bottom: -100,
            right: -100,
            width: 500,
            height: 500,
            borderRadius: "50%",
            background: "radial-gradient(circle, rgba(236,72,153,0.2) 0%, transparent 70%)",
            filter: "blur(80px)",
          }}
        />

        {/* Main content */}
        <div
          style={{
            display: "flex",
            flexDirection: "column",
            alignItems: "center",
            justifyContent: "center",
            zIndex: 10,
          }}
        >
          {/* Logo */}
          <div
            style={{
              display: "flex",
              alignItems: "baseline",
              marginBottom: 20,
            }}
          >
            <span
              style={{
                fontSize: 160,
                fontWeight: 700,
                color: "white",
                letterSpacing: "-0.02em",
              }}
            >
              D23
            </span>
            <span
              style={{
                fontSize: 160,
                fontWeight: 700,
                background: "linear-gradient(90deg, #8B5CF6 0%, #D946EF 50%, #EC4899 100%)",
                backgroundClip: "text",
                color: "transparent",
                letterSpacing: "-0.02em",
              }}
            >
              .AI
            </span>
          </div>

          {/* Tagline */}
          <p
            style={{
              fontSize: 40,
              color: "#a1a1aa",
              marginTop: 10,
              marginBottom: 16,
            }}
          >
            Bharat's First WhatsApp AI Assistant
          </p>

          {/* Features */}
          <p
            style={{
              fontSize: 28,
              color: "#71717a",
            }}
          >
            11+ Indian Languages | Voice | Images | Games
          </p>
        </div>
      </div>
    ),
    {
      ...size,
    }
  )
}
