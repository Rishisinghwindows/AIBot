import type React from "react"
import type { Metadata } from "next"
import { Geist, Geist_Mono } from "next/font/google"
import { AuthProvider } from "@/context/AuthContext"
import "./globals.css"

const _geist = Geist({ subsets: ["latin"] })
const _geistMono = Geist_Mono({ subsets: ["latin"] })

export const metadata: Metadata = {
  title: "D23 AI | Bharat's WhatsApp AI",
  description: "Meet Bharat's first WhatsApp-native AI assistant for every language and every question.",
  generator: "d23.ai",
  metadataBase: new URL("https://d23ai.in"),
  icons: {
    icon: "/d23ai-logo-v7.svg",
    apple: "/apple-icon.png",
  },
  openGraph: {
    title: "D23 AI | Bharat's WhatsApp AI",
    description: "Meet Bharat's first WhatsApp-native AI assistant for every language and every question.",
    url: "https://d23ai.in",
    siteName: "D23 AI",
    locale: "en_IN",
    type: "website",
    images: [
      {
        url: "/d23-og.png",
        width: 1200,
        height: 630,
        alt: "D23 AI - Bharat's WhatsApp AI Assistant",
      },
    ],
  },
  twitter: {
    card: "summary_large_image",
    title: "D23 AI | Bharat's WhatsApp AI",
    description: "Meet Bharat's first WhatsApp-native AI assistant for every language and every question.",
    images: ["/d23-og.png"],
  },
}

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode
}>) {
  return (
    <html lang="en">
      <body className={`font-sans antialiased`}>
        <AuthProvider>
          {children}
        </AuthProvider>
      </body>
    </html>
  )
}
