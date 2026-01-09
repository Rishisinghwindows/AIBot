"use client"

import { useState, useRef } from "react"
import Image from "next/image"
import Link from "next/link"
import { motion, useInView } from "framer-motion"
import {
  MessageCircle, Search, Gamepad2, Train, Sparkles, ArrowRight,
  Zap, Globe, Bot, Languages, ImageIcon, Mic, ChevronDown
} from "lucide-react"
import { cn } from "@/lib/utils"

// Integration Data
const integrations = [
  {
    id: "conversational-ai",
    icon: MessageCircle,
    title: "Conversational AI",
    description: "General chat, Q&A, explanations, brainstorming, and task assistance.",
    details: "Engage in natural conversations for questions, answers, explanations, brainstorming, and task assistance.",
    howToUse: "Ask questions or give instructions. Add context, constraints, or examples for better results.",
    image: "/puch/features/salman-1.webp",
    color: "from-violet-500 to-purple-500",
    tags: ["Chat", "Q&A", "Tasks", "Ideas"]
  },
  {
    id: "multilingual",
    icon: Languages,
    title: "11+ Indian Languages",
    description: "Speak in Hindi, Tamil, Telugu, Bengali, Marathi, Gujarati & more.",
    details: "Full support for Hindi, Tamil, Telugu, Bengali, Marathi, Gujarati, Kannada, Malayalam, Punjabi, Odia and English.",
    howToUse: "Just type or speak in your preferred language. D23 AI automatically detects and responds in the same language.",
    image: "/puch/features/siddarth-shinchanified.png",
    color: "from-fuchsia-500 to-pink-500",
    tags: ["Hindi", "Tamil", "Telugu", "Bengali", "+7 more"]
  },
  {
    id: "search",
    icon: Search,
    title: "Web Search",
    description: "Search the internet for real-time information and news.",
    details: "Enables real-time internet search for information that may be outside the model's knowledge, or that is evolving.",
    howToUse: "Ask any question about current events, news, or information. D23 will search and summarize for you.",
    image: "/puch/features/salman-2.webp",
    color: "from-cyan-500 to-blue-500",
    tags: ["Web", "News", "Real-time"]
  },
  {
    id: "image-gen",
    icon: ImageIcon,
    title: "AI Image Generation",
    description: "Generate stunning AI images from text descriptions.",
    details: "Create beautiful, unique images using AI. Perfect for social media, creative projects, or just for fun.",
    howToUse: "Describe the image you want, e.g., 'Generate an image of a sunset over the Himalayas'",
    image: "/puch/features/salman.png",
    color: "from-orange-500 to-red-500",
    tags: ["Creative", "Art", "Design"]
  },
  {
    id: "voice",
    icon: Mic,
    title: "Voice Messages",
    description: "Send voice messages and get voice replies.",
    details: "Speak naturally in any supported language. D23 AI understands your voice and can respond with audio.",
    howToUse: "Send a voice message on WhatsApp. D23 AI will transcribe, understand, and respond.",
    image: "/puch/features/salman-3.webp",
    color: "from-green-500 to-emerald-500",
    tags: ["Voice", "Audio", "Speech"]
  },
  {
    id: "games",
    icon: Gamepad2,
    title: "Games & Quizzes",
    description: "Play Wordle, quizzes, and other fun games.",
    details: "Play quizzes on any topic, Wordle, and other interactive games right in WhatsApp.",
    howToUse: "Type 'play wordle' or 'start quiz on cricket' to begin.",
    image: "/puch/assets/wordle/wordlewin.jpeg",
    color: "from-amber-500 to-yellow-500",
    tags: ["Wordle", "Quiz", "Fun"]
  },
  {
    id: "train",
    icon: Train,
    title: "Train & PNR Status",
    description: "Check live train status, schedules, and PNR information.",
    details: "Get real-time train running status, check PNR status, find trains between stations, and more.",
    howToUse: "Type 'PNR 1234567890' or 'Live status for 12954' or 'Trains from Delhi to Mumbai'",
    image: "/puch/assets/wordle/wordle1.jpeg",
    color: "from-rose-500 to-pink-500",
    tags: ["Live Status", "PNR", "Schedule"]
  },
]

// Gradient Text Component
function GradientText({ children, className = "" }: { children: React.ReactNode; className?: string }) {
  return (
    <span className={cn(
      "bg-gradient-to-r from-violet-400 via-fuchsia-400 to-pink-400 bg-clip-text text-transparent",
      className
    )}>
      {children}
    </span>
  )
}

// Header Component
function Header() {
  return (
    <header className="fixed top-0 left-0 right-0 z-50 bg-black/70 backdrop-blur-xl border-b border-white/10">
      <div className="max-w-7xl mx-auto px-6 py-4">
        <div className="flex items-center justify-between">
          <Link href="/" className="flex items-center gap-2">
            <Image src="/d23ai-logo-v8.svg" alt="D23" width={40} height={40} />
          </Link>

          <nav className="hidden md:flex items-center gap-8">
            {["Features", "About", "Contact"].map((item) => (
              <Link
                key={item}
                href={`/${item.toLowerCase()}`}
                className="text-sm text-zinc-400 hover:text-white transition-colors"
              >
                {item}
              </Link>
            ))}
          </nav>

          <Link
            href="https://wa.me/918548819349?text=Hey%20D23%20AI%21%20What%20can%20you%20do%3F"
            target="_blank"
            className="flex items-center gap-2 px-5 py-2.5 rounded-full bg-gradient-to-r from-violet-600 to-fuchsia-600 text-white text-sm font-medium"
          >
            <Zap className="h-4 w-4" />
            Try Now
          </Link>
        </div>
      </div>
    </header>
  )
}

// Hero Section
function HeroSection() {
  return (
    <section className="relative pt-32 pb-20 overflow-hidden">
      {/* Background */}
      <div className="absolute inset-0">
        <div className="absolute top-1/4 left-1/4 w-[600px] h-[600px] bg-violet-600/20 rounded-full blur-[120px]" />
        <div className="absolute bottom-1/4 right-1/4 w-[500px] h-[500px] bg-fuchsia-600/20 rounded-full blur-[120px]" />
        <div className="absolute inset-0 bg-[linear-gradient(rgba(255,255,255,0.02)_1px,transparent_1px),linear-gradient(90deg,rgba(255,255,255,0.02)_1px,transparent_1px)] bg-[size:50px_50px]" />
      </div>

      <div className="relative z-10 max-w-5xl mx-auto px-6 text-center">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="inline-flex items-center gap-2 px-4 py-2 rounded-full border border-violet-500/30 bg-violet-500/10 mb-8"
        >
          <Sparkles className="h-4 w-4 text-violet-400" />
          <span className="text-sm text-violet-300">Powerful Integrations</span>
        </motion.div>

        <motion.h1
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.1 }}
          className="text-5xl md:text-6xl lg:text-7xl font-bold text-white mb-6"
        >
          Everything D23 AI
          <br />
          <GradientText>can do for you</GradientText>
        </motion.h1>

        <motion.p
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.2 }}
          className="text-lg md:text-xl text-zinc-400 max-w-2xl mx-auto mb-10"
        >
          Discover the power of AI-driven conversations with seamless integrations
          across platforms, services, and tools that matter to you.
        </motion.p>

        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.3 }}
          className="flex flex-wrap justify-center gap-4"
        >
          <Link
            href="https://wa.me/918548819349?text=Hey%20D23%20AI%21%20What%20can%20you%20do%3F"
            target="_blank"
            className="flex items-center gap-2 px-8 py-4 rounded-full bg-gradient-to-r from-violet-600 to-fuchsia-600 text-white font-semibold shadow-lg shadow-violet-500/25"
          >
            <MessageCircle className="h-5 w-5" />
            Try on WhatsApp
            <ArrowRight className="h-5 w-5" />
          </Link>
          <Link
            href="/chat"
            className="flex items-center gap-2 px-8 py-4 rounded-full border border-white/20 text-white font-semibold hover:bg-white/5 transition-colors"
          >
            Try Web Chat
          </Link>
        </motion.div>
      </div>
    </section>
  )
}

// Integration Card
function IntegrationCard({ integration, index }: { integration: typeof integrations[0]; index: number }) {
  const ref = useRef(null)
  const isInView = useInView(ref, { once: true, margin: "-100px" })
  const Icon = integration.icon

  return (
    <motion.div
      ref={ref}
      initial={{ opacity: 0, y: 50 }}
      animate={isInView ? { opacity: 1, y: 0 } : {}}
      transition={{ delay: index * 0.1 }}
      className="group relative"
    >
      <div className="relative p-[1px] rounded-2xl overflow-hidden">
        <div className="absolute inset-0 bg-gradient-to-r from-violet-500 via-fuchsia-500 to-pink-500 opacity-0 group-hover:opacity-100 transition-opacity duration-500" />
        <div className="absolute inset-0 bg-zinc-800" />

        <div className="relative bg-zinc-900 rounded-2xl overflow-hidden">
          {/* Image */}
          <div className="relative h-48 overflow-hidden">
            <Image
              src={integration.image}
              alt={integration.title}
              fill
              className="object-cover transition-transform duration-700 group-hover:scale-110"
            />
            <div className="absolute inset-0 bg-gradient-to-t from-zinc-900 via-zinc-900/50 to-transparent" />

            {/* Icon Badge */}
            <div className={cn(
              "absolute top-4 left-4 w-12 h-12 rounded-xl flex items-center justify-center bg-gradient-to-br shadow-lg",
              integration.color
            )}>
              <Icon className="w-6 h-6 text-white" />
            </div>
          </div>

          {/* Content */}
          <div className="p-6">
            <h3 className="text-xl font-bold text-white mb-2">{integration.title}</h3>
            <p className="text-zinc-400 text-sm mb-4">{integration.description}</p>

            {/* Tags */}
            <div className="flex flex-wrap gap-2 mb-4">
              {integration.tags.map((tag) => (
                <span
                  key={tag}
                  className="px-3 py-1 rounded-full bg-white/5 border border-white/10 text-xs text-zinc-400"
                >
                  {tag}
                </span>
              ))}
            </div>

            {/* How to Use */}
            <div className="pt-4 border-t border-white/10">
              <p className="text-xs text-zinc-500 mb-1">How to use:</p>
              <p className="text-sm text-zinc-300">{integration.howToUse}</p>
            </div>
          </div>
        </div>
      </div>
    </motion.div>
  )
}

// Integrations Grid
function IntegrationsGrid() {
  return (
    <section className="py-20 px-6">
      <div className="max-w-7xl mx-auto">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          className="text-center mb-16"
        >
          <span className="text-violet-400 text-sm font-semibold tracking-wider uppercase">Capabilities</span>
          <h2 className="text-4xl md:text-5xl font-bold text-white mt-3">
            Explore all <GradientText>integrations</GradientText>
          </h2>
        </motion.div>

        <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6">
          {integrations.map((integration, i) => (
            <IntegrationCard key={integration.id} integration={integration} index={i} />
          ))}
        </div>
      </div>
    </section>
  )
}

// CTA Section
function CTASection() {
  return (
    <section className="py-20 px-6">
      <div className="max-w-4xl mx-auto">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          className="relative rounded-3xl overflow-hidden"
        >
          <div className="absolute inset-0 bg-gradient-to-r from-violet-600 via-fuchsia-600 to-pink-600" />
          <div className="absolute inset-0 bg-[linear-gradient(rgba(255,255,255,0.1)_1px,transparent_1px),linear-gradient(90deg,rgba(255,255,255,0.1)_1px,transparent_1px)] bg-[size:40px_40px]" />

          <div className="relative z-10 p-12 md:p-20 text-center">
            <h2 className="text-4xl md:text-5xl font-bold text-white mb-6">
              Ready to get started?
            </h2>
            <p className="text-white/80 text-lg mb-10 max-w-xl mx-auto">
              Try D23 AI now and experience the power of AI in your language.
            </p>

            <div className="flex flex-wrap justify-center gap-4">
              <Link
                href="https://wa.me/918548819349?text=Hey%20D23%20AI%21%20What%20can%20you%20do%3F"
                target="_blank"
                className="flex items-center gap-2 px-8 py-4 rounded-full bg-white text-violet-600 font-semibold shadow-2xl hover:bg-zinc-100 transition-colors"
              >
                <MessageCircle className="h-5 w-5" />
                Start on WhatsApp
              </Link>
            </div>
          </div>
        </motion.div>
      </div>
    </section>
  )
}

// Footer
function Footer() {
  return (
    <footer className="py-12 px-6 border-t border-white/10">
      <div className="max-w-6xl mx-auto">
        <div className="flex flex-col md:flex-row items-center justify-between gap-6">
          <div className="flex items-center gap-3">
            <Image src="/puch/logo.png" alt="D23 AI" width={40} height={40} />
            <div>
              <p className="text-lg font-bold text-white">D23 <GradientText>AI</GradientText></p>
              <p className="text-sm text-zinc-500">WhatsApp-native AI for Bharat.</p>
            </div>
          </div>

          <p className="text-sm text-zinc-500">© 2025 D23 AI. Built for every Indian language.</p>
        </div>
      </div>
    </footer>
  )
}

// Main Page
export default function IntegrationsPage() {
  return (
    <div className="min-h-screen bg-black text-white overflow-x-hidden">
      <Header />
      <main>
        <HeroSection />
        <IntegrationsGrid />
        <CTASection />
      </main>
      <Footer />
    </div>
  )
}
