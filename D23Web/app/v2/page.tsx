"use client"

import { useState, useRef, useEffect } from "react"
import Image from "next/image"
import Link from "next/link"
import { motion, useScroll, useTransform, useInView, AnimatePresence } from "framer-motion"
import { Sparkles, Mic, ShieldCheck, Sticker, Gamepad2, MessageCircle, ChevronDown } from "lucide-react"
import { cn } from "@/lib/utils"

// ============== DATA ==============
const rotatingWords = ["पूछो", "વિચારો", "ಪ್ರಶ್ನಿಸಿ", "विचारा", "D23 AI"]

const featureCards = [
  {
    title: "Multi-Language Support",
    highlights: ["Hindi, Marathi, Tamil", "regional"],
    description: "Connect naturally in your mother tongue. D23 AI responds fluently in Hindi, Marathi, Tamil, and more.",
    tags: ["Multi-Language", "Regional", "Natural"],
  },
  {
    title: "Voice Assistant",
    highlights: ["authentic regional voices", "hands-free access"],
    description: "Hear answers in authentic regional voices. Enjoy hands-free access to news, facts, and everyday help.",
    tags: ["Voice", "Natural", "Accessible"],
  },
  {
    title: "Instant Fact Checker",
    highlights: ["instant verification", "detect misinformation"],
    description: "Forward any message and get instant verification. D23 AI checks trusted sources to detect misinformation.",
    tags: ["Instant", "Fact-Checking", "Reliable"],
  },
  {
    title: "AI Image Generation",
    highlights: ["stunning visuals", "any style"],
    description: "Create stunning visuals from a simple prompt. Generate images in any style instantly.",
    tags: ["Creative", "AI Art", "Instant"],
  },
  {
    title: "Create custom stickers",
    highlights: ["/sticker", "unique stickers"],
    description: "Transform any image into a custom sticker. Send /sticker with an image and let D23 AI craft unique stickers.",
    tags: ["AI-Powered", "Custom Design", "Instant"],
  },
  {
    title: "Shinchanify your images",
    highlights: ["/shinchan", "converts your photos"],
    description: "Turn any photo into Shin-chan style artwork. Send /shinchan with an image and get adorable anime vibes.",
    tags: ["Anime Style", "Instant", "Fun"],
  },
]

const stats = [
  { value: "5000+", title: "users already talking", highlight: "D23 AI" },
  { value: "Real-time", title: "Instant Responses", highlight: "instantly" },
  { value: "24/7", title: "AI Availability", highlight: "24/7" },
  { value: "11", title: "languages supported", highlight: "regional languages" },
]

const faqs = [
  { question: "What is D23 AI?", answer: "An intelligent WhatsApp bot specializing in Indic languages for instant answers." },
  {
    question: "Which languages does D23 AI support?",
    answer: "Hindi, Marathi, Bengali, Tamil, Telugu, Kannada, Malayalam, Gujarati, Punjabi, Oriya and more regional languages.",
  },
  { question: "Is D23 AI free to use?", answer: "Yes! You can start chatting without paying anything." },
  {
    question: "Can D23 AI fact-check information?",
    answer: "Forward any message for verification. D23 AI searches reliable sources, but remember online info can have biases.",
  },
]

const capabilityShowcases = [
  {
    title: "Image Generation",
    description: "Create stunning visuals from prompts. Pick styles and get instant renders you can share.",
    icon: <Sparkles className="h-5 w-5" />,
    image: "/puch/features/siddarth-shinchanified.png",
    label: "AI Images",
  },
  {
    title: "Voice Assistant",
    description: "Ask in your voice, hear replies in authentic regional tones. Hands-free answers, always on.",
    icon: <Mic className="h-5 w-5" />,
    image: "/puch/puch_ai.png",
    label: "Voice",
  },
  {
    title: "Fact Check",
    description: "Forward any message for instant verification. Stay safe from misinformation in any language.",
    icon: <ShieldCheck className="h-5 w-5" />,
    image: "/puch/features/salman-3.webp",
    label: "Verify",
  },
  {
    title: "Stickers",
    description: "Send /sticker with a photo to get a full sticker pack, auto-cropped and ready to drop.",
    icon: <Sticker className="h-5 w-5" />,
    image: "/puch/features/dragon.png",
    label: "Stickers",
  },
  {
    title: "Games",
    description: "Play Wordle and more inside WhatsApp. Invite friends and keep the fun in-chat.",
    icon: <Gamepad2 className="h-5 w-5" />,
    image: "/puch/assets/wordle/wordlewin.jpeg",
    label: "Games",
  },
]

const phoneTabs = [
  { label: "Multi-Language Support", image: "/puch/assets/wordle/wordlewin.jpeg" },
  { label: "Image Generation", image: "/puch/features/salman.png" },
  { label: "Video Generation", image: "/puch/features/salman-6.webp" },
  { label: "Voice Assistant", image: "/puch/features/salman-3.webp" },
  { label: "Shinchanify", image: "/puch/features/siddarth-shinchanified.png" },
  { label: "Fact Check", image: "/puch/features/salman-1.webp" },
  { label: "Stickers", image: "/puch/features/dragon.png" },
  { label: "Games", image: "/puch/assets/wordle/wordlewin.jpeg" },
]

// ============== ANIMATION COMPONENTS ==============
function FadeInOnScroll({ children, className = "", delay = 0 }: { children: React.ReactNode; className?: string; delay?: number }) {
  const ref = useRef(null)
  const isInView = useInView(ref, { once: true, margin: "-100px" })

  return (
    <motion.div
      ref={ref}
      initial={{ opacity: 0, y: 60 }}
      animate={isInView ? { opacity: 1, y: 0 } : { opacity: 0, y: 60 }}
      transition={{ duration: 0.8, delay, ease: [0.21, 0.47, 0.32, 0.98] }}
      className={className}
    >
      {children}
    </motion.div>
  )
}

function ScaleOnScroll({ children, className = "" }: { children: React.ReactNode; className?: string }) {
  const ref = useRef(null)
  const isInView = useInView(ref, { once: true, margin: "-50px" })

  return (
    <motion.div
      ref={ref}
      initial={{ opacity: 0, scale: 0.9 }}
      animate={isInView ? { opacity: 1, scale: 1 } : { opacity: 0, scale: 0.9 }}
      transition={{ duration: 0.6, ease: [0.21, 0.47, 0.32, 0.98] }}
      className={className}
    >
      {children}
    </motion.div>
  )
}

// Glass Card Component
function GlassCard({ children, className = "", hover = true }: { children: React.ReactNode; className?: string; hover?: boolean }) {
  return (
    <motion.div
      whileHover={hover ? { scale: 1.02, y: -5 } : {}}
      transition={{ duration: 0.3 }}
      className={`relative overflow-hidden rounded-2xl border border-white/30 bg-white/40 backdrop-blur-xl shadow-[0_8px_32px_rgba(0,0,0,0.08)] ${className}`}
    >
      <div className="absolute inset-0 bg-gradient-to-br from-white/50 via-transparent to-transparent pointer-events-none" />
      <div className="relative z-10">{children}</div>
    </motion.div>
  )
}

// Floating Orbs Background
function FloatingOrbs() {
  return (
    <div className="fixed inset-0 overflow-hidden pointer-events-none z-0">
      <motion.div
        animate={{ x: [0, 100, 0], y: [0, -50, 0] }}
        transition={{ duration: 20, repeat: Infinity, ease: "linear" }}
        className="absolute top-20 left-10 w-72 h-72 bg-gradient-to-r from-green-400/20 to-emerald-400/20 rounded-full blur-3xl"
      />
      <motion.div
        animate={{ x: [0, -80, 0], y: [0, 100, 0] }}
        transition={{ duration: 25, repeat: Infinity, ease: "linear" }}
        className="absolute top-40 right-20 w-96 h-96 bg-gradient-to-r from-blue-400/15 to-purple-400/15 rounded-full blur-3xl"
      />
      <motion.div
        animate={{ x: [0, 60, 0], y: [0, -80, 0] }}
        transition={{ duration: 18, repeat: Infinity, ease: "linear" }}
        className="absolute bottom-20 left-1/3 w-80 h-80 bg-gradient-to-r from-pink-400/15 to-orange-400/15 rounded-full blur-3xl"
      />
    </div>
  )
}

// Rotating Word Component
function RotatingWord({ words, className = "" }: { words: string[]; className?: string }) {
  const [index, setIndex] = useState(0)

  useEffect(() => {
    const interval = setInterval(() => {
      setIndex((prev) => (prev + 1) % words.length)
    }, 2000)
    return () => clearInterval(interval)
  }, [words.length])

  return (
    <span className={`inline-block relative ${className}`}>
      <AnimatePresence mode="wait">
        <motion.span
          key={index}
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          exit={{ opacity: 0, y: -20 }}
          transition={{ duration: 0.4 }}
          className="inline-block bg-gradient-to-r from-green-500 to-emerald-600 bg-clip-text text-transparent"
        >
          {words[index]}
        </motion.span>
      </AnimatePresence>
    </span>
  )
}

// ============== HEADER ==============
function Header() {
  return (
    <motion.header
      initial={{ y: -100, opacity: 0 }}
      animate={{ y: 0, opacity: 1 }}
      transition={{ duration: 0.8, ease: [0.21, 0.47, 0.32, 0.98] }}
      className="fixed top-4 left-0 right-0 z-50 px-4"
    >
      <div className="mx-auto max-w-6xl">
        <GlassCard className="px-4 py-3" hover={false}>
          <div className="flex items-center justify-between">
            <Link href="/v2" className="flex items-center gap-2">
              <Image src="/puch/logo.png" alt="D23 AI" width={36} height={36} className="h-9 w-9" />
              <span className="text-lg font-bold bg-gradient-to-r from-green-600 to-emerald-600 bg-clip-text text-transparent">D23 AI</span>
            </Link>
            <nav className="hidden md:flex items-center gap-6">
              {["Chat", "Integrations", "MCP", "About", "Contact"].map((item) => (
                <Link
                  key={item}
                  href={`/${item.toLowerCase()}`}
                  className="text-sm font-medium text-gray-600 hover:text-green-600 transition-colors"
                >
                  {item}
                </Link>
              ))}
            </nav>
            <div className="flex items-center gap-2">
              <button className="hidden md:flex h-9 items-center gap-1 rounded-lg border border-gray-200 bg-white/50 px-3 text-sm font-medium text-gray-600 hover:bg-white/80 transition">
                English
                <ChevronDown className="h-4 w-4 opacity-60" />
              </button>
              <motion.div whileHover={{ scale: 1.05 }} whileTap={{ scale: 0.95 }}>
                <Link
                  href="https://api.whatsapp.com/send/?phone=%2B919934438606&text=Hey+D23%21+What+can+you+do%3F&type=phone_number&app_absent=0"
                  target="_blank"
                  className="flex items-center gap-2 rounded-xl bg-gradient-to-r from-green-500 to-emerald-600 px-4 py-2 text-sm font-semibold text-white shadow-lg shadow-green-500/25"
                >
                  <MessageCircle className="h-4 w-4" />
                  Try Now
                </Link>
              </motion.div>
            </div>
          </div>
        </GlassCard>
      </div>
    </motion.header>
  )
}

// ============== HERO SECTION ==============
function HeroSection() {
  const ref = useRef(null)
  const { scrollYProgress } = useScroll({ target: ref, offset: ["start start", "end start"] })
  const y = useTransform(scrollYProgress, [0, 1], [0, 150])
  const opacity = useTransform(scrollYProgress, [0, 0.5], [1, 0])

  return (
    <section ref={ref} className="relative pt-32 pb-16 overflow-hidden">
      <motion.div style={{ y, opacity }} className="relative z-10">
        <div className="flex flex-col items-center gap-5 text-center px-4">
          {/* Badge */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6 }}
          >
            <GlassCard className="inline-flex items-center gap-2 px-4 py-2" hover={false}>
              <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" fill="currentColor" viewBox="0 0 256 256" className="text-yellow-500">
                <path d="M234.29,114.85l-45,38.83L203,211.75a16.4,16.4,0,0,1-24.5,17.82L128,198.49,77.47,229.57A16.4,16.4,0,0,1,53,211.75l13.76-58.07-45-38.83A16.46,16.46,0,0,1,31.08,86l59-4.76,22.76-55.08a16.36,16.36,0,0,1,30.27,0l22.75,55.08,59,4.76a16.46,16.46,0,0,1,9.37,28.86Z" />
              </svg>
              <span className="text-sm font-medium text-gray-700">WhatsApp in your native language</span>
            </GlassCard>
          </motion.div>

          {/* Title with Rotating Words */}
          <motion.div
            initial={{ opacity: 0, y: 30 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.8, delay: 0.2 }}
            className="space-y-3"
          >
            <h1 className="text-4xl sm:text-5xl md:text-6xl font-medium leading-tight text-gray-900">
              <span>Kuch bhi ho, </span>
              <span>bas <RotatingWord words={rotatingWords} className="font-semibold min-w-[120px]" /></span>
            </h1>
            <p className="text-base sm:text-lg text-gray-600 max-w-2xl mx-auto">
              India&apos;s first AI assistant jo har samay aapki sewa mein hai. D23 AI hai har sawaal ka smart jawaab.
            </p>
          </motion.div>

          {/* Tags */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6, delay: 0.4 }}
            className="flex flex-wrap items-center justify-center gap-3"
          >
            {["Aapka Dost", "Aapka Assistant", "Aapka AI"].map((item, i) => (
              <motion.span
                key={item}
                initial={{ opacity: 0, scale: 0.8 }}
                animate={{ opacity: 1, scale: 1 }}
                transition={{ delay: 0.5 + i * 0.1 }}
                whileHover={{ scale: 1.05, y: -2 }}
                className="rounded-full border border-green-200 bg-white/80 backdrop-blur-sm px-4 py-2 text-sm font-semibold text-green-700 shadow-sm"
              >
                {item}
              </motion.span>
            ))}
          </motion.div>

          {/* Buttons */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6, delay: 0.6 }}
            className="flex flex-wrap items-center justify-center gap-3"
          >
            <motion.div whileHover={{ scale: 1.05, y: -2 }} whileTap={{ scale: 0.95 }}>
              <Link
                href="https://api.whatsapp.com/send/?phone=%2B919934438606&text=Hey+D23%21+What+can+you+do%3F&type=phone_number&app_absent=0"
                target="_blank"
                className="flex items-center gap-2 rounded-xl bg-gradient-to-r from-green-500 to-green-600 px-6 py-3 text-sm font-semibold text-white shadow-lg shadow-green-500/30"
              >
                <Image src="/puch/puch_ai.png" alt="WhatsApp" width={20} height={20} className="h-5 w-5" />
                WhatsApp
              </Link>
            </motion.div>
            <motion.div whileHover={{ scale: 1.05, y: -2 }} whileTap={{ scale: 0.95 }}>
              <Link
                href="/chat"
                className="flex items-center gap-2 rounded-xl bg-gradient-to-r from-gray-800 to-gray-900 px-6 py-3 text-sm font-semibold text-white shadow-lg"
              >
                <svg className="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z" />
                </svg>
                Try Web Chat
              </Link>
            </motion.div>
          </motion.div>

          <motion.p
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ delay: 0.8 }}
            className="text-sm text-gray-500"
          >
            Also available on iOS App Store (Coming Soon)
          </motion.p>
        </div>

        {/* Hero Video */}
        <motion.div
          initial={{ opacity: 0, y: 40 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.8, delay: 0.4 }}
          className="mt-12 px-4"
        >
          <HeroVideo />
        </motion.div>
      </motion.div>
    </section>
  )
}

function HeroVideo() {
  return (
    <div className="group relative mx-auto w-full max-w-4xl overflow-hidden rounded-2xl shadow-2xl">
      <GlassCard className="p-1" hover={false}>
        <div className="relative rounded-xl overflow-hidden">
          <video
            className="h-full w-full object-cover rounded-xl"
            src="/puch/Puch_AI_Launch.mp4"
            autoPlay
            loop
            muted
            playsInline
            controls={false}
          />
          <div className="pointer-events-none absolute inset-0 flex items-center justify-center bg-white/90 backdrop-blur-sm transition duration-500 group-hover:opacity-0">
            <div className="relative flex items-center gap-3 rounded-full bg-white/80 backdrop-blur-sm px-5 py-3 shadow-xl border border-white/50">
              <Image src="/puch/logo.png" alt="D23 AI logo" width={48} height={48} className="h-12 w-12" />
              <div className="text-left">
                <p className="text-xl font-semibold text-gray-900">D23 AI</p>
                <p className="text-sm text-gray-500">Launch reel</p>
              </div>
              <motion.div
                animate={{ scale: [1, 1.1, 1] }}
                transition={{ duration: 2, repeat: Infinity }}
                className="flex h-12 w-12 items-center justify-center rounded-full bg-gradient-to-r from-green-500 to-emerald-600 text-white shadow-lg"
              >
                <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" fill="currentColor" viewBox="0 0 256 256">
                  <path d="M240,128a15.74,15.74,0,0,1-7.6,13.51L88.32,229.65a16,16,0,0,1-16.2.3A15.86,15.86,0,0,1,64,216.13V39.87a15.86,15.86,0,0,1,8.12-13.82,16,16,0,0,1,16.2.3L232.4,114.49A15.74,15.74,0,0,1,240,128Z" />
                </svg>
              </motion.div>
            </div>
          </div>
        </div>
      </GlassCard>
    </div>
  )
}

// ============== PHONE WALL ==============
function PhoneWall() {
  const [active, setActive] = useState(0)
  const prevIndex = (active - 1 + phoneTabs.length) % phoneTabs.length
  const nextIndex = (active + 1) % phoneTabs.length

  return (
    <section className="py-20 px-4">
      <FadeInOnScroll className="text-center mb-8">
        <GlassCard className="inline-flex items-center gap-2 px-5 py-2 mb-6" hover={false}>
          <Sparkles className="h-4 w-4 text-green-500" />
          <span className="text-sm font-medium text-gray-700">Features</span>
        </GlassCard>
        <h2 className="text-3xl sm:text-4xl font-medium text-gray-900">
          D23 AI is faster, smarter, and always ready.
        </h2>
      </FadeInOnScroll>

      {/* Tabs */}
      <FadeInOnScroll delay={0.2}>
        <div className="flex flex-wrap justify-center gap-2 mb-8">
          {phoneTabs.map((tab, idx) => (
            <motion.button
              key={tab.label}
              onClick={() => setActive(idx)}
              whileHover={{ scale: 1.05 }}
              whileTap={{ scale: 0.95 }}
              className={cn(
                "rounded-xl border px-4 py-2 text-sm font-medium transition-all backdrop-blur-sm",
                active === idx
                  ? "border-green-400 bg-gradient-to-r from-green-100 to-emerald-100 text-green-700 shadow-md"
                  : "border-gray-200 bg-white/50 text-gray-600 hover:bg-white/80"
              )}
            >
              {tab.label}
            </motion.button>
          ))}
        </div>
      </FadeInOnScroll>

      {/* Phone Mockups */}
      <div className="relative flex items-end justify-center gap-4 md:gap-8 overflow-hidden py-4">
        {[prevIndex, active, nextIndex].map((idx, pos) => {
          const tab = phoneTabs[idx]
          const isActive = idx === active

          return (
            <motion.div
              key={`${tab.label}-${idx}-${pos}`}
              onClick={() => setActive(idx)}
              initial={false}
              animate={{
                scale: isActive ? 1.05 : 0.9,
                opacity: isActive ? 1 : 0.4,
                x: pos === 0 ? -20 : pos === 2 ? 20 : 0,
              }}
              transition={{ duration: 0.4, ease: "easeOut" }}
              className={cn(
                "relative cursor-pointer overflow-hidden rounded-[32px] border bg-[#0b1014] shadow-2xl",
                isActive ? "h-[520px] w-[260px] z-20 border-green-500/50" : "h-[460px] w-[220px] z-10 border-white/10"
              )}
            >
              {isActive && (
                <motion.div
                  className="absolute inset-0 rounded-[32px]"
                  animate={{ boxShadow: ["0 0 20px rgba(34,197,94,0.3)", "0 0 40px rgba(34,197,94,0.5)", "0 0 20px rgba(34,197,94,0.3)"] }}
                  transition={{ duration: 2, repeat: Infinity }}
                />
              )}
              <div className="absolute inset-0">
                <Image src="/puch/features/wtsp-bg.png" alt="" fill className="object-cover opacity-15" />
              </div>
              <div className="relative flex h-full flex-col">
                <div className="flex items-center justify-between px-4 py-3">
                  <div className="flex items-center gap-2 text-white">
                    <span className="text-lg font-semibold">D23</span>
                    <span className="text-sm font-medium opacity-70">AI</span>
                  </div>
                  <span className="text-xs text-white/60">{tab.label}</span>
                </div>
                <div className="relative m-3 flex-1 overflow-hidden rounded-2xl border border-white/10 bg-black/40">
                  {tab.label === "Multi-Language Support" ? (
                    <MultiLanguageMock muted={!isActive} />
                  ) : (
                    <>
                      <Image src={tab.image} alt={tab.label} fill className="object-cover" />
                      {!isActive && <div className="absolute inset-0 bg-black/40 backdrop-blur-[2px]" />}
                    </>
                  )}
                </div>
              </div>
            </motion.div>
          )
        })}
      </div>
    </section>
  )
}

function MultiLanguageMock({ muted }: { muted: boolean }) {
  return (
    <div className="relative h-full w-full overflow-hidden bg-[#0b1014] text-white">
      <div className="absolute inset-0">
        <Image src="/puch/features/wtsp-bg.png" alt="" fill className="object-cover opacity-10" />
      </div>
      <div className="relative flex h-full flex-col gap-3 overflow-y-auto p-4 text-sm leading-relaxed">
        <div className="rounded-lg bg-[#1f272a] px-3 py-2 shadow-sm">
          <p className="font-semibold text-emerald-400">You</p>
          <p className="text-white">आज के मुख्य समाचार बताओ।</p>
        </div>
        <div className="rounded-lg bg-[#0d1417] px-3 py-2 shadow-sm ring-1 ring-white/5">
          <p className="font-semibold text-[#e94f4f]">D23 AI</p>
          <ul className="mt-1 space-y-1 text-sm text-white">
            <li>🔹 मौसम: दिल्ली में आज तेज़ बारिश की संभावना।</li>
            <li>🔹 राजनीति: संसद का मानसून सत्र आज से शुरू।</li>
            <li>🔹 खेल: विराट कोहली ने लगाया शतक।</li>
          </ul>
          <p className="mt-2 text-xs text-white/60">10:02 AM</p>
        </div>
        <div className="rounded-lg bg-emerald-900/40 px-3 py-2 shadow-sm ring-1 ring-emerald-400/30">
          <p className="text-white">આજના સમાચાર આપો.</p>
          <p className="mt-2 text-xs text-white/70">10:03 AM</p>
        </div>
        <div className="rounded-lg bg-[#0d1417] px-3 py-2 shadow-sm ring-1 ring-white/5">
          <p className="font-semibold text-[#e94f4f]">D23 AI</p>
          <ul className="mt-1 space-y-1 text-sm text-white">
            <li>🔹 અમદાવાદમાં ભારે વરસાદની આગાહી</li>
            <li>🔹 વડાપ્રધાન નવી યોજનાઓ શરૂ</li>
            <li>🔹 ક્રિકેટ: ભારત જીત્યું</li>
          </ul>
          <p className="mt-2 text-xs text-white/60">10:05 AM</p>
        </div>
        <div className="rounded-lg bg-[#1f272a] px-3 py-2 shadow-sm">
          <p className="font-semibold text-emerald-400">You</p>
          <p className="text-white">আগামীকালের আবহাওয়া কেমন হবে?</p>
        </div>
        <div className="rounded-lg bg-[#0d1417] px-3 py-2 shadow-sm ring-1 ring-white/5">
          <p className="font-semibold text-[#e94f4f]">D23 AI</p>
          <p className="text-white">🌧️ কলকাতায় কাল মেঘলা আকাশ ও বৃষ্টির সম্ভাবনা।🌡️ সর্বোচ্চ: 31°C</p>
        </div>
      </div>
      {muted && <div className="absolute inset-0 bg-black/40 backdrop-blur-[2px]" />}
    </div>
  )
}

// ============== FEATURE GRID ==============
function FeatureGrid() {
  return (
    <section className="py-20 px-4">
      <FadeInOnScroll className="text-center mb-10">
        <GlassCard className="inline-flex items-center gap-2 px-5 py-2 mb-6" hover={false}>
          <Sparkles className="h-4 w-4 text-green-500" />
          <span className="text-sm font-medium text-gray-700">Capabilities</span>
        </GlassCard>
      </FadeInOnScroll>

      <div className="max-w-6xl mx-auto grid gap-6 md:grid-cols-2">
        {featureCards.map((card, i) => (
          <FadeInOnScroll key={card.title} delay={i * 0.1}>
            <GlassCard className="p-6 h-full">
              <div className="flex items-center gap-2 mb-3">
                <span className="h-2 w-2 rounded-full bg-gradient-to-r from-green-500 to-emerald-500" />
                <p className="text-sm font-semibold uppercase tracking-wide text-green-600">{card.tags[0]}</p>
              </div>
              <h3 className="text-xl font-semibold text-gray-900 mb-2">{card.title}</h3>
              <p className="text-sm leading-relaxed text-gray-600 mb-4">{card.description}</p>
              <div className="flex flex-wrap gap-2">
                {card.highlights.map((text) => (
                  <span key={text} className="rounded-full border border-green-200 bg-green-50 px-3 py-1 text-xs font-semibold text-green-700">
                    {text}
                  </span>
                ))}
                {card.tags.map((tag) => (
                  <span key={tag} className="rounded-full bg-gray-100 px-3 py-1 text-xs font-semibold text-gray-600">
                    {tag}
                  </span>
                ))}
              </div>
            </GlassCard>
          </FadeInOnScroll>
        ))}
      </div>
    </section>
  )
}

// ============== CAPABILITY SHOWCASES ==============
function CapabilityShowcases() {
  return (
    <section className="py-20 px-4">
      <FadeInOnScroll className="text-center mb-10">
        <GlassCard className="inline-flex items-center gap-2 px-5 py-2" hover={false}>
          <span className="text-sm font-medium text-gray-700">Image • Voice • Fact Check • Stickers • Games</span>
        </GlassCard>
      </FadeInOnScroll>

      <div className="max-w-6xl mx-auto grid gap-6 md:grid-cols-2 lg:grid-cols-3">
        {capabilityShowcases.map((capability, i) => (
          <FadeInOnScroll key={capability.title} delay={i * 0.1}>
            <GlassCard className="overflow-hidden h-full">
              <div className="p-5">
                <div className="flex items-center gap-3 mb-3">
                  <span className="flex h-10 w-10 items-center justify-center rounded-xl bg-gradient-to-r from-green-500 to-emerald-500 text-white shadow-lg">
                    {capability.icon}
                  </span>
                  <div>
                    <p className="text-xs font-semibold uppercase tracking-wide text-green-600">{capability.label}</p>
                    <h4 className="text-lg font-semibold text-gray-900">{capability.title}</h4>
                  </div>
                </div>
                <p className="text-sm leading-relaxed text-gray-600 mb-4">{capability.description}</p>
                <div className="overflow-hidden rounded-xl border border-gray-100">
                  <Image
                    src={capability.image}
                    alt={capability.title}
                    width={600}
                    height={400}
                    className="h-48 w-full object-cover transition duration-300 hover:scale-105"
                  />
                </div>
              </div>
            </GlassCard>
          </FadeInOnScroll>
        ))}
      </div>
    </section>
  )
}

// ============== STATS SECTION ==============
function StatsSection() {
  return (
    <section className="py-20 px-4">
      <FadeInOnScroll className="text-center mb-10">
        <p className="text-lg font-semibold bg-gradient-to-r from-green-500 to-emerald-500 bg-clip-text text-transparent">Trusted</p>
        <h3 className="text-3xl font-medium text-gray-900">by thousands of users across India</h3>
      </FadeInOnScroll>

      <div className="max-w-6xl mx-auto grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        {stats.map((item, i) => (
          <FadeInOnScroll key={item.title} delay={i * 0.1}>
            <GlassCard className="p-6">
              <div className="text-3xl font-bold bg-gradient-to-r from-green-500 to-emerald-500 bg-clip-text text-transparent mb-2">
                {item.value}
              </div>
              <div className="text-sm font-medium text-gray-900 mb-1">{item.title}</div>
              <p className="text-sm text-gray-600">
                Always-on help with <span className="font-semibold text-gray-900">{item.highlight}</span>.
              </p>
            </GlassCard>
          </FadeInOnScroll>
        ))}
      </div>
    </section>
  )
}

// ============== FAQ SECTION ==============
function FAQSection() {
  const [openIndex, setOpenIndex] = useState<number | null>(null)

  return (
    <section className="py-20 px-4">
      <FadeInOnScroll className="text-center mb-10">
        <h3 className="text-3xl font-semibold text-gray-900">
          Frequently Asked <span className="bg-gradient-to-r from-green-500 to-emerald-500 bg-clip-text text-transparent">Questions</span>
        </h3>
        <p className="text-sm text-gray-500 mt-2">Everything you need to know before you use D23 AI.</p>
      </FadeInOnScroll>

      <div className="max-w-3xl mx-auto space-y-3">
        {faqs.map((faq, idx) => (
          <FadeInOnScroll key={idx} delay={idx * 0.1}>
            <GlassCard className="overflow-hidden" hover={false}>
              <button
                onClick={() => setOpenIndex(openIndex === idx ? null : idx)}
                className="w-full flex items-center justify-between p-5 text-left"
              >
                <span className="text-base font-medium text-gray-900">{faq.question}</span>
                <motion.div
                  animate={{ rotate: openIndex === idx ? 180 : 0 }}
                  transition={{ duration: 0.3 }}
                >
                  <ChevronDown className="h-5 w-5 text-gray-500" />
                </motion.div>
              </button>
              <AnimatePresence>
                {openIndex === idx && (
                  <motion.div
                    initial={{ height: 0, opacity: 0 }}
                    animate={{ height: "auto", opacity: 1 }}
                    exit={{ height: 0, opacity: 0 }}
                    transition={{ duration: 0.3 }}
                    className="overflow-hidden"
                  >
                    <p className="px-5 pb-5 text-sm leading-relaxed text-gray-600">{faq.answer}</p>
                  </motion.div>
                )}
              </AnimatePresence>
            </GlassCard>
          </FadeInOnScroll>
        ))}
      </div>
    </section>
  )
}

// ============== CTA SECTION ==============
function CTASection() {
  return (
    <section className="py-20 px-4">
      <ScaleOnScroll>
        <div className="max-w-4xl mx-auto">
          <GlassCard className="p-10 overflow-hidden" hover={false}>
            <div className="absolute inset-0 bg-gradient-to-r from-green-500/10 via-transparent to-emerald-500/10" />
            <div className="relative z-10 flex flex-col items-center gap-6 text-center">
              <div>
                <p className="text-sm font-semibold uppercase tracking-wide bg-gradient-to-r from-green-500 to-emerald-500 bg-clip-text text-transparent">Get Started</p>
                <h3 className="text-3xl font-semibold text-gray-900 mt-1">Choose Your Platform</h3>
                <p className="text-sm text-gray-500 mt-2">D23 AI is available on multiple platforms. Pick your favorite!</p>
              </div>

              {/* Platform Cards */}
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4 w-full max-w-3xl">
                {/* WhatsApp */}
                <motion.div whileHover={{ scale: 1.03, y: -5 }} className="flex flex-col items-center gap-3 p-5 rounded-xl border border-green-200 bg-white/80 backdrop-blur-sm shadow-sm">
                  <div className="w-12 h-12 rounded-full bg-gradient-to-r from-green-400 to-green-500 flex items-center justify-center shadow-lg">
                    <Image src="/puch/puch_ai.png" alt="WhatsApp" width={28} height={28} />
                  </div>
                  <div className="text-center">
                    <h4 className="font-semibold text-gray-900">WhatsApp</h4>
                    <p className="text-xs text-gray-500">Chat on your favorite app</p>
                  </div>
                  <Link
                    href="https://api.whatsapp.com/send/?phone=%2B919934438606&text=Hey+D23%21+What+can+you+do%3F&type=phone_number&app_absent=0"
                    target="_blank"
                    className="w-full text-center py-2 rounded-lg bg-gradient-to-r from-green-500 to-green-600 text-white text-sm font-semibold shadow-md"
                  >
                    Open WhatsApp
                  </Link>
                </motion.div>

                {/* Web Chat */}
                <motion.div whileHover={{ scale: 1.03, y: -5 }} className="flex flex-col items-center gap-3 p-5 rounded-xl border border-gray-200 bg-white/80 backdrop-blur-sm shadow-sm">
                  <div className="w-12 h-12 rounded-full bg-gradient-to-r from-gray-700 to-gray-800 flex items-center justify-center shadow-lg">
                    <svg className="w-6 h-6 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z" />
                    </svg>
                  </div>
                  <div className="text-center">
                    <h4 className="font-semibold text-gray-900">Web Chat</h4>
                    <p className="text-xs text-gray-500">Chat directly in browser</p>
                  </div>
                  <Link
                    href="/chat"
                    className="w-full text-center py-2 rounded-lg bg-gradient-to-r from-gray-700 to-gray-800 text-white text-sm font-semibold shadow-md"
                  >
                    Try Now
                  </Link>
                </motion.div>

                {/* iOS App */}
                <motion.div className="flex flex-col items-center gap-3 p-5 rounded-xl border border-gray-200 bg-white/60 backdrop-blur-sm shadow-sm opacity-75">
                  <div className="w-12 h-12 rounded-full bg-gray-200 flex items-center justify-center">
                    <svg aria-hidden="true" width="24" height="24" viewBox="0 0 384 512" className="text-gray-500">
                      <path fill="currentColor" d="M318.7 268.7c-.3-36.7 16-64.4 49-84.8-18.4-26.7-46.2-41.6-83.1-44.5-34.8-2.8-73.1 20.3-87.1 20.3-14.4 0-47.6-19.4-73.6-19.4C77.5 141.4 9 184 9 285.5c0 25.9 4.8 52.5 14.5 79.9 12.9 36.7 59.4 126.6 108.1 125 25.4-.6 43.3-17.9 76.2-17.9 32.4 0 49.4 17.9 76.7 17.9 49.1-.7 90.8-82.7 102.9-119.7-65.1-30.7-68.7-90-68.7-101zM258.5 78.3C283.2 50.2 280.9 25 280 16c-21.2 1.3-45.6 14.1-60.1 30.8-13 15-23.9 38.8-20.9 61.5 22.9 1.8 46.4-10.5 59.5-30z" />
                    </svg>
                  </div>
                  <div className="text-center">
                    <h4 className="font-semibold text-gray-900">iOS App</h4>
                    <p className="text-xs text-gray-500">Native iPhone experience</p>
                  </div>
                  <button disabled className="w-full text-center py-2 rounded-lg border border-gray-300 bg-gray-100 text-gray-500 text-sm font-semibold cursor-not-allowed">
                    Coming Soon
                  </button>
                </motion.div>
              </div>

              <p className="text-xs text-gray-400 mt-2">
                All platforms support 22+ Indian languages including Hindi, Marathi, Tamil, Telugu, and more.
              </p>
            </div>
          </GlassCard>
        </div>
      </ScaleOnScroll>
    </section>
  )
}

// ============== FOOTER ==============
function Footer() {
  return (
    <footer className="py-12 px-4 border-t border-gray-100">
      <div className="max-w-6xl mx-auto">
        <FadeInOnScroll>
          <GlassCard className="p-8" hover={false}>
            <div className="flex flex-col md:flex-row items-center justify-between gap-6">
              <div className="flex items-center gap-3">
                <Image src="/puch/logo.png" alt="D23 AI" width={40} height={40} />
                <div>
                  <p className="text-lg font-bold bg-gradient-to-r from-green-600 to-emerald-600 bg-clip-text text-transparent">D23 AI</p>
                  <p className="text-sm text-gray-500">WhatsApp-native AI for Bharat.</p>
                </div>
              </div>
              <motion.div whileHover={{ scale: 1.05 }} whileTap={{ scale: 0.95 }}>
                <Link
                  href="https://api.whatsapp.com/send/?phone=%2B919934438606&text=Hey+D23%21+What+can+you+do%3F&type=phone_number&app_absent=0"
                  target="_blank"
                  className="flex items-center gap-2 rounded-xl bg-gradient-to-r from-green-500 to-emerald-600 px-6 py-3 text-sm font-semibold text-white shadow-lg"
                >
                  Talk to D23 AI
                </Link>
              </motion.div>
            </div>
            <div className="flex flex-col md:flex-row items-center justify-between gap-4 mt-8 pt-6 border-t border-gray-100">
              <div className="flex items-center gap-4">
                <Link href="#" className="text-gray-400 hover:text-green-500 transition-colors">
                  <svg className="h-5 w-5" fill="currentColor" viewBox="0 0 24 24">
                    <path d="M18.244 2.25h3.308l-7.227 8.26 8.502 11.24H16.17l-5.214-6.817L4.99 21.75H1.68l7.73-8.835L1.254 2.25H8.08l4.713 6.231zm-1.161 17.52h1.833L7.084 4.126H5.117z" />
                  </svg>
                </Link>
                <Link href="#" className="text-gray-400 hover:text-green-500 transition-colors">
                  <svg className="h-5 w-5" fill="currentColor" viewBox="0 0 24 24">
                    <path d="M12 2.163c3.204 0 3.584.012 4.85.07 3.252.148 4.771 1.691 4.919 4.919.058 1.265.069 1.645.069 4.849 0 3.205-.012 3.584-.069 4.849-.149 3.225-1.664 4.771-4.919 4.919-1.266.058-1.644.07-4.85.07-3.204 0-3.584-.012-4.849-.07-3.26-.149-4.771-1.699-4.919-4.92-.058-1.265-.07-1.644-.07-4.849 0-3.204.013-3.583.07-4.849.149-3.227 1.664-4.771 4.919-4.919 1.266-.057 1.645-.069 4.849-.069z" />
                  </svg>
                </Link>
                <Link href="#" className="text-gray-400 hover:text-green-500 transition-colors">
                  <svg className="h-5 w-5" fill="currentColor" viewBox="0 0 24 24">
                    <path d="M12 0c-6.626 0-12 5.373-12 12 0 5.302 3.438 9.8 8.207 11.387.599.111.793-.261.793-.577v-2.234c-3.338.726-4.033-1.416-4.033-1.416-.546-1.387-1.333-1.756-1.333-1.756-1.089-.745.083-.729.083-.729 1.205.084 1.839 1.237 1.839 1.237 1.07 1.834 2.807 1.304 3.492.997.107-.775.418-1.305.762-1.604-2.665-.305-5.467-1.334-5.467-5.931 0-1.311.469-2.381 1.236-3.221-.124-.303-.535-1.524.117-3.176 0 0 1.008-.322 3.301 1.23.957-.266 1.983-.399 3.003-.404 1.02.005 2.047.138 3.006.404 2.291-1.552 3.297-1.23 3.297-1.23.653 1.653.242 2.874.118 3.176.77.84 1.235 1.911 1.235 3.221 0 4.609-2.807 5.624-5.479 5.921.43.372.823 1.102.823 2.222v3.293c0 .319.192.694.801.576 4.765-1.589 8.199-6.086 8.199-11.386 0-6.627-5.373-12-12-12z" />
                  </svg>
                </Link>
              </div>
              <p className="text-sm text-gray-500">© 2025 D23 AI. Built for every Indian language.</p>
            </div>
          </GlassCard>
        </FadeInOnScroll>
      </div>
    </footer>
  )
}

// ============== MAIN PAGE ==============
export default function V2Page() {
  return (
    <div className="min-h-screen bg-gradient-to-b from-gray-50 via-white to-gray-50 overflow-x-hidden">
      <FloatingOrbs />
      <Header />
      <main className="relative z-10 max-w-6xl mx-auto">
        <HeroSection />
        <PhoneWall />
        <FeatureGrid />
        <CapabilityShowcases />
        <StatsSection />
        <FAQSection />
        <CTASection />
      </main>
      <Footer />
    </div>
  )
}
