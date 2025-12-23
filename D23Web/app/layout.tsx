import type React from "react"
import type { Metadata } from "next"
import { Geist, Geist_Mono } from "next/font/google"
import { Analytics } from "@vercel/analytics/next"
import { AuthProvider } from "@/context/AuthContext"
import "./globals.css"

const _geist = Geist({ subsets: ["latin"] })
const _geistMono = Geist_Mono({ subsets: ["latin"] })

export const metadata: Metadata = {
  title: "D23 AI | Bharat's WhatsApp AI",
  description: "Meet Bharat's first WhatsApp-native AI assistant for every language and every question.",
  generator: "d23.ai recreation",
  icons: {
    icon: [
      {
        url: "/puch/puch_ai.png",
      },
      {
        url: "/puch/logo.png",
      },
    ],
    apple: "/puch/puch_ai.png",
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
        <Analytics />
      </body>
    </html>
  )
}
