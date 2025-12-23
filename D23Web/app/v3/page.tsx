"use client"

import { useState, useRef, useEffect } from "react"
import Image from "next/image"
import Link from "next/link"
import { motion, useScroll, useTransform, useInView, AnimatePresence } from "framer-motion"
import { Sparkles, Mic, ShieldCheck, Sticker, Gamepad2, MessageCircle, ChevronDown, ArrowRight, Play, Globe, Zap, Languages } from "lucide-react"
import { cn } from "@/lib/utils"

// ============== DATA ==============
const rotatingWords = ["पूछो", "વિચારો", "ಪ್ರಶ್ನಿಸಿ", "विचारा", "అడుగు", "D23"]

const bentoFeatures = [
  {
    title: "11+ Languages",
    description: "Hindi, Tamil, Telugu, Bengali, Marathi & more",
    icon: <Languages className="h-6 w-6" />,
    gradient: "from-blue-500 to-cyan-400",
    size: "col-span-2 row-span-1",
  },
  {
    title: "Voice AI",
    description: "Speak naturally, get voice replies",
    icon: <Mic className="h-6 w-6" />,
    gradient: "from-purple-500 to-pink-500",
    size: "col-span-1 row-span-2",
    image: "/puch/features/salman-3.webp",
  },
  {
    title: "AI Images",
    description: "Generate stunning visuals instantly",
    icon: <Sparkles className="h-6 w-6" />,
    gradient: "from-orange-500 to-red-500",
    size: "col-span-1 row-span-1",
  },
  {
    title: "Fact Check",
    description: "Verify any message instantly",
    icon: <ShieldCheck className="h-6 w-6" />,
    gradient: "from-green-500 to-emerald-400",
    size: "col-span-1 row-span-1",
  },
  {
    title: "Stickers",
    description: "Create custom WhatsApp stickers",
    icon: <Sticker className="h-6 w-6" />,
    gradient: "from-yellow-500 to-orange-400",
    size: "col-span-1 row-span-1",
    image: "/puch/features/dragon.png",
  },
  {
    title: "Games",
    description: "Play Wordle & more in WhatsApp",
    icon: <Gamepad2 className="h-6 w-6" />,
    gradient: "from-indigo-500 to-purple-500",
    size: "col-span-1 row-span-1",
  },
]

const stats = [
  { value: "5000+", label: "Users", icon: "👥" },
  { value: "11+", label: "Languages", icon: "🌍" },
  { value: "24/7", label: "Available", icon: "⚡" },
  { value: "<2s", label: "Response", icon: "🚀" },
]

const faqs = [
  { question: "What is D23 AI?", answer: "An intelligent WhatsApp bot specializing in Indic languages for instant answers." },
  { question: "Which languages are supported?", answer: "Hindi, Marathi, Bengali, Tamil, Telugu, Kannada, Malayalam, Gujarati, Punjabi, Oriya and more." },
  { question: "Is it free to use?", answer: "Yes! You can start chatting without paying anything." },
  { question: "Can it fact-check messages?", answer: "Forward any message for verification. D23 AI searches reliable sources to detect misinformation." },
]

const showcaseItems = [
  { title: "Shinchanify", image: "/puch/features/siddarth-shinchanified.png", tag: "Fun" },
  { title: "Image Gen", image: "/puch/features/salman.png", tag: "Creative" },
  { title: "Stickers", image: "/puch/features/dragon.png", tag: "Custom" },
]

// ============== ANIMATION HELPERS ==============
function FadeUp({ children, delay = 0, className = "" }: { children: React.ReactNode; delay?: number; className?: string }) {
  const ref = useRef(null)
  const isInView = useInView(ref, { once: true, margin: "-50px" })

  return (
    <motion.div
      ref={ref}
      initial={{ opacity: 0, y: 40 }}
      animate={isInView ? { opacity: 1, y: 0 } : {}}
      transition={{ duration: 0.6, delay, ease: [0.22, 1, 0.36, 1] }}
      className={className}
    >
      {children}
    </motion.div>
  )
}

// Rotating Word Component
function RotatingWord({ words }: { words: string[] }) {
  const [index, setIndex] = useState(0)

  useEffect(() => {
    const interval = setInterval(() => setIndex((i) => (i + 1) % words.length), 2000)
    return () => clearInterval(interval)
  }, [words.length])

  return (
    <AnimatePresence mode="wait">
      <motion.span
        key={index}
        initial={{ opacity: 0, y: 20, filter: "blur(8px)" }}
        animate={{ opacity: 1, y: 0, filter: "blur(0px)" }}
        exit={{ opacity: 0, y: -20, filter: "blur(8px)" }}
        transition={{ duration: 0.4 }}
        className="inline-block text-transparent bg-clip-text bg-gradient-to-r from-green-400 via-emerald-400 to-teal-400"
      >
        {words[index]}
      </motion.span>
    </AnimatePresence>
  )
}

// Glow Effect Component
function GlowCard({ children, className = "", glowColor = "green" }: { children: React.ReactNode; className?: string; glowColor?: string }) {
  const glowStyles: Record<string, string> = {
    green: "before:bg-green-500/20 hover:before:bg-green-500/30",
    purple: "before:bg-purple-500/20 hover:before:bg-purple-500/30",
    blue: "before:bg-blue-500/20 hover:before:bg-blue-500/30",
  }

  return (
    <div className={cn(
      "relative group rounded-2xl bg-gray-900/80 border border-gray-800 backdrop-blur-xl overflow-hidden transition-all duration-500",
      "before:absolute before:inset-0 before:rounded-2xl before:transition-all before:duration-500 before:blur-xl before:-z-10",
      glowStyles[glowColor] || glowStyles.green,
      className
    )}>
      {children}
    </div>
  )
}

// ============== HEADER ==============
function Header() {
  const [scrolled, setScrolled] = useState(false)

  useEffect(() => {
    const handleScroll = () => setScrolled(window.scrollY > 50)
    window.addEventListener("scroll", handleScroll)
    return () => window.removeEventListener("scroll", handleScroll)
  }, [])

  return (
    <motion.header
      initial={{ y: -100 }}
      animate={{ y: 0 }}
      transition={{ duration: 0.6 }}
      className={cn(
        "fixed top-0 left-0 right-0 z-50 transition-all duration-300",
        scrolled ? "bg-black/80 backdrop-blur-xl border-b border-gray-800" : ""
      )}
    >
      <div className="max-w-7xl mx-auto px-6 py-4">
        <div className="flex items-center justify-between">
          <Link href="/v3" className="flex items-center gap-3">
            <div className="relative">
              <div className="absolute inset-0 bg-green-500/50 blur-xl rounded-full" />
              <Image src="/puch/logo.png" alt="D23" width={40} height={40} className="relative" />
            </div>
            <span className="text-xl font-bold text-white">D23<span className="text-green-400">.AI</span></span>
          </Link>

          <nav className="hidden md:flex items-center gap-8">
            {["Features", "About", "Contact"].map((item) => (
              <Link key={item} href={`/${item.toLowerCase()}`} className="text-gray-400 hover:text-white transition-colors text-sm">
                {item}
              </Link>
            ))}
          </nav>

          <motion.div whileHover={{ scale: 1.05 }} whileTap={{ scale: 0.95 }}>
            <Link
              href="https://api.whatsapp.com/send/?phone=%2B919934438606&text=Hey+D23%21+What+can+you+do%3F&type=phone_number&app_absent=0"
              target="_blank"
              className="flex items-center gap-2 px-5 py-2.5 rounded-full bg-gradient-to-r from-green-500 to-emerald-600 text-white text-sm font-medium shadow-lg shadow-green-500/25"
            >
              <Zap className="h-4 w-4" />
              Start Free
            </Link>
          </motion.div>
        </div>
      </div>
    </motion.header>
  )
}

// ============== HERO SECTION ==============
function HeroSection() {
  const ref = useRef(null)
  const { scrollYProgress } = useScroll({ target: ref, offset: ["start start", "end start"] })
  const y = useTransform(scrollYProgress, [0, 1], [0, 200])
  const opacity = useTransform(scrollYProgress, [0, 0.8], [1, 0])

  return (
    <section ref={ref} className="relative min-h-screen flex items-center justify-center overflow-hidden pt-20">
      {/* Animated Background */}
      <div className="absolute inset-0">
        <div className="absolute inset-0 bg-[radial-gradient(ellipse_at_center,_var(--tw-gradient-stops))] from-green-900/20 via-gray-950 to-gray-950" />
        <motion.div
          animate={{ rotate: 360 }}
          transition={{ duration: 50, repeat: Infinity, ease: "linear" }}
          className="absolute top-1/4 left-1/4 w-96 h-96 bg-gradient-to-r from-green-500/10 to-emerald-500/10 rounded-full blur-3xl"
        />
        <motion.div
          animate={{ rotate: -360 }}
          transition={{ duration: 60, repeat: Infinity, ease: "linear" }}
          className="absolute bottom-1/4 right-1/4 w-80 h-80 bg-gradient-to-r from-blue-500/10 to-purple-500/10 rounded-full blur-3xl"
        />
        {/* Grid Pattern */}
        <div className="absolute inset-0 bg-[linear-gradient(rgba(255,255,255,0.02)_1px,transparent_1px),linear-gradient(90deg,rgba(255,255,255,0.02)_1px,transparent_1px)] bg-[size:64px_64px]" />
      </div>

      <motion.div style={{ y, opacity }} className="relative z-10 max-w-5xl mx-auto px-6 text-center">
        {/* Badge */}
        <motion.div
          initial={{ opacity: 0, scale: 0.8 }}
          animate={{ opacity: 1, scale: 1 }}
          transition={{ duration: 0.5 }}
          className="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-gray-800/50 border border-gray-700 mb-8"
        >
          <span className="relative flex h-2 w-2">
            <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-green-400 opacity-75" />
            <span className="relative inline-flex rounded-full h-2 w-2 bg-green-500" />
          </span>
          <span className="text-sm text-gray-300">India's #1 AI on WhatsApp</span>
        </motion.div>

        {/* Main Heading */}
        <motion.h1
          initial={{ opacity: 0, y: 30 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6, delay: 0.2 }}
          className="text-5xl md:text-7xl lg:text-8xl font-bold text-white mb-6 leading-tight"
        >
          Kuch bhi ho
          <br />
          <span className="text-gray-500">bas</span> <RotatingWord words={rotatingWords} />
        </motion.h1>

        {/* Subtitle */}
        <motion.p
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6, delay: 0.4 }}
          className="text-lg md:text-xl text-gray-400 max-w-2xl mx-auto mb-10"
        >
          Your AI assistant that speaks your language. Get instant answers in Hindi, Tamil, Telugu & 11+ Indian languages.
        </motion.p>

        {/* CTA Buttons */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6, delay: 0.6 }}
          className="flex flex-wrap items-center justify-center gap-4"
        >
          <motion.div whileHover={{ scale: 1.05 }} whileTap={{ scale: 0.95 }}>
            <Link
              href="https://api.whatsapp.com/send/?phone=%2B919934438606&text=Hey+D23%21+What+can+you+do%3F&type=phone_number&app_absent=0"
              target="_blank"
              className="group flex items-center gap-3 px-8 py-4 rounded-full bg-gradient-to-r from-green-500 to-emerald-600 text-white font-semibold shadow-2xl shadow-green-500/30 hover:shadow-green-500/50 transition-shadow"
            >
              <svg height="24" width="24" viewBox="0 0 256 259" xmlns="http://www.w3.org/2000/svg">
                <path d="m67.663 221.823 4.185 2.093c17.44 10.463 36.971 15.346 56.503 15.346 61.385 0 111.609-50.224 111.609-111.609 0-29.297-11.859-57.897-32.785-78.824-20.927-20.927-48.83-32.785-78.824-32.785-61.385 0-111.61 50.224-110.912 112.307 0 20.926 6.278 41.156 16.741 58.594l2.79 4.186-11.16 41.156 41.853-10.464Z" fill="#fff"/>
              </svg>
              Start on WhatsApp
              <ArrowRight className="h-5 w-5 group-hover:translate-x-1 transition-transform" />
            </Link>
          </motion.div>

          <motion.div whileHover={{ scale: 1.05 }} whileTap={{ scale: 0.95 }}>
            <Link
              href="/chat"
              className="flex items-center gap-3 px-8 py-4 rounded-full bg-gray-800 border border-gray-700 text-white font-semibold hover:bg-gray-700 transition-colors"
            >
              <Globe className="h-5 w-5" />
              Try Web Chat
            </Link>
          </motion.div>
        </motion.div>

        {/* Stats Row */}
        <motion.div
          initial={{ opacity: 0, y: 30 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6, delay: 0.8 }}
          className="flex items-center justify-center gap-8 md:gap-16 mt-16"
        >
          {stats.map((stat, i) => (
            <div key={stat.label} className="text-center">
              <div className="text-2xl md:text-3xl font-bold text-white">{stat.value}</div>
              <div className="text-sm text-gray-500">{stat.label}</div>
            </div>
          ))}
        </motion.div>
      </motion.div>

      {/* Scroll Indicator */}
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ delay: 1.5 }}
        className="absolute bottom-8 left-1/2 -translate-x-1/2"
      >
        <motion.div animate={{ y: [0, 8, 0] }} transition={{ duration: 1.5, repeat: Infinity }} className="text-gray-500">
          <ChevronDown className="h-6 w-6" />
        </motion.div>
      </motion.div>
    </section>
  )
}

// ============== VIDEO SECTION ==============
function VideoSection() {
  return (
    <section className="py-20 px-6">
      <div className="max-w-5xl mx-auto">
        <FadeUp>
          <GlowCard className="p-2">
            <div className="relative rounded-xl overflow-hidden group cursor-pointer">
              <video
                className="w-full aspect-video object-cover"
                src="/puch/Puch_AI_Launch.mp4"
                autoPlay
                loop
                muted
                playsInline
              />
              <div className="absolute inset-0 bg-black/60 flex items-center justify-center opacity-100 group-hover:opacity-0 transition-opacity duration-500">
                <div className="flex items-center gap-4">
                  <motion.div
                    animate={{ scale: [1, 1.2, 1] }}
                    transition={{ duration: 2, repeat: Infinity }}
                    className="w-20 h-20 rounded-full bg-white/10 backdrop-blur-sm flex items-center justify-center border border-white/20"
                  >
                    <Play className="h-8 w-8 text-white ml-1" fill="white" />
                  </motion.div>
                  <div className="text-left">
                    <p className="text-white font-semibold text-xl">D23 AI</p>
                    <p className="text-gray-400 text-sm">Watch Launch Video</p>
                  </div>
                </div>
              </div>
            </div>
          </GlowCard>
        </FadeUp>
      </div>
    </section>
  )
}

// ============== BENTO GRID ==============
function BentoSection() {
  return (
    <section className="py-20 px-6">
      <div className="max-w-6xl mx-auto">
        <FadeUp className="text-center mb-16">
          <span className="text-green-400 text-sm font-semibold tracking-wider uppercase">Features</span>
          <h2 className="text-4xl md:text-5xl font-bold text-white mt-3">
            Everything you need,<br />
            <span className="text-gray-500">in your language</span>
          </h2>
        </FadeUp>

        <div className="grid grid-cols-2 md:grid-cols-3 gap-4 md:gap-6 auto-rows-[180px]">
          {bentoFeatures.map((feature, i) => (
            <FadeUp key={feature.title} delay={i * 0.1} className={feature.size}>
              <motion.div
                whileHover={{ scale: 1.02, y: -5 }}
                transition={{ duration: 0.3 }}
                className="h-full"
              >
                <GlowCard className="h-full p-6 flex flex-col justify-between">
                  {feature.image && (
                    <div className="absolute inset-0 opacity-30">
                      <Image src={feature.image} alt="" fill className="object-cover" />
                      <div className="absolute inset-0 bg-gradient-to-t from-gray-900 via-gray-900/80 to-transparent" />
                    </div>
                  )}
                  <div className="relative z-10">
                    <div className={cn(
                      "w-12 h-12 rounded-xl flex items-center justify-center mb-4",
                      `bg-gradient-to-br ${feature.gradient}`
                    )}>
                      {feature.icon}
                    </div>
                    <h3 className="text-xl font-bold text-white mb-2">{feature.title}</h3>
                    <p className="text-gray-400 text-sm">{feature.description}</p>
                  </div>
                </GlowCard>
              </motion.div>
            </FadeUp>
          ))}
        </div>
      </div>
    </section>
  )
}

// ============== SHOWCASE SECTION ==============
function ShowcaseSection() {
  return (
    <section className="py-20 px-6">
      <div className="max-w-6xl mx-auto">
        <FadeUp className="text-center mb-16">
          <span className="text-green-400 text-sm font-semibold tracking-wider uppercase">Showcase</span>
          <h2 className="text-4xl md:text-5xl font-bold text-white mt-3">See what's possible</h2>
        </FadeUp>

        <div className="grid md:grid-cols-3 gap-6">
          {showcaseItems.map((item, i) => (
            <FadeUp key={item.title} delay={i * 0.15}>
              <motion.div
                whileHover={{ y: -10 }}
                transition={{ duration: 0.3 }}
                className="group"
              >
                <GlowCard className="overflow-hidden">
                  <div className="relative aspect-square overflow-hidden">
                    <Image
                      src={item.image}
                      alt={item.title}
                      fill
                      className="object-cover transition-transform duration-500 group-hover:scale-110"
                    />
                    <div className="absolute inset-0 bg-gradient-to-t from-gray-900 via-transparent to-transparent" />
                    <div className="absolute bottom-4 left-4 right-4">
                      <span className="inline-block px-3 py-1 rounded-full bg-green-500/20 border border-green-500/30 text-green-400 text-xs font-medium mb-2">
                        {item.tag}
                      </span>
                      <h3 className="text-xl font-bold text-white">{item.title}</h3>
                    </div>
                  </div>
                </GlowCard>
              </motion.div>
            </FadeUp>
          ))}
        </div>
      </div>
    </section>
  )
}

// ============== PHONE MOCKUP SECTION ==============
function PhoneMockupSection() {
  return (
    <section className="py-20 px-6 overflow-hidden">
      <div className="max-w-6xl mx-auto">
        <div className="grid lg:grid-cols-2 gap-12 items-center">
          <FadeUp>
            <span className="text-green-400 text-sm font-semibold tracking-wider uppercase">WhatsApp Native</span>
            <h2 className="text-4xl md:text-5xl font-bold text-white mt-3 mb-6">
              No app needed.<br />
              <span className="text-gray-500">Just WhatsApp.</span>
            </h2>
            <p className="text-gray-400 text-lg mb-8">
              D23 AI works right inside WhatsApp - the app you already use daily. No downloads, no signups. Just start chatting.
            </p>
            <ul className="space-y-4">
              {["Send a message to start", "Ask in any Indian language", "Get instant, helpful replies"].map((item, i) => (
                <motion.li
                  key={item}
                  initial={{ opacity: 0, x: -20 }}
                  whileInView={{ opacity: 1, x: 0 }}
                  transition={{ delay: i * 0.1 }}
                  viewport={{ once: true }}
                  className="flex items-center gap-3 text-gray-300"
                >
                  <div className="w-6 h-6 rounded-full bg-green-500/20 flex items-center justify-center">
                    <svg className="w-3 h-3 text-green-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={3} d="M5 13l4 4L19 7" />
                    </svg>
                  </div>
                  {item}
                </motion.li>
              ))}
            </ul>
          </FadeUp>

          <FadeUp delay={0.2} className="relative">
            <motion.div
              animate={{ y: [0, -10, 0] }}
              transition={{ duration: 4, repeat: Infinity }}
              className="relative mx-auto w-72"
            >
              {/* Phone Frame */}
              <div className="relative rounded-[3rem] bg-gray-900 p-3 border border-gray-700 shadow-2xl">
                <div className="rounded-[2.5rem] overflow-hidden bg-[#0b1014]">
                  {/* Status Bar */}
                  <div className="flex items-center justify-between px-6 py-2 bg-[#0b1014]">
                    <span className="text-white text-xs">9:41</span>
                    <div className="flex items-center gap-1">
                      <div className="w-4 h-2 bg-white/60 rounded-sm" />
                    </div>
                  </div>
                  {/* Chat Header */}
                  <div className="flex items-center gap-3 px-4 py-3 bg-[#1f272a] border-b border-white/10">
                    <Image src="/puch/logo.png" alt="D23" width={40} height={40} className="rounded-full" />
                    <div>
                      <p className="text-white font-semibold">D23 AI</p>
                      <p className="text-green-400 text-xs">Online</p>
                    </div>
                  </div>
                  {/* Chat Messages */}
                  <div className="p-4 space-y-3 h-80 overflow-hidden">
                    <div className="bg-[#1f272a] rounded-lg px-3 py-2 max-w-[85%]">
                      <p className="text-white text-sm">नमस्ते! मैं D23 AI हूं। आज मैं आपकी क्या मदद कर सकता हूं? 🙏</p>
                    </div>
                    <div className="bg-green-900/40 rounded-lg px-3 py-2 max-w-[85%] ml-auto">
                      <p className="text-white text-sm">आज दिल्ली का मौसम कैसा है?</p>
                    </div>
                    <div className="bg-[#1f272a] rounded-lg px-3 py-2 max-w-[85%]">
                      <p className="text-white text-sm">दिल्ली में आज 28°C तापमान है। 🌤️ आसमान साफ है और शाम को हल्की बारिश की संभावना है।</p>
                    </div>
                    <div className="bg-green-900/40 rounded-lg px-3 py-2 max-w-[85%] ml-auto">
                      <p className="text-white text-sm">Thanks! 👍</p>
                    </div>
                  </div>
                </div>
              </div>
              {/* Glow Effect */}
              <div className="absolute -inset-4 bg-gradient-to-r from-green-500/20 to-emerald-500/20 rounded-[4rem] blur-2xl -z-10" />
            </motion.div>
          </FadeUp>
        </div>
      </div>
    </section>
  )
}

// ============== FAQ SECTION ==============
function FAQSection() {
  const [open, setOpen] = useState<number | null>(null)

  return (
    <section className="py-20 px-6">
      <div className="max-w-3xl mx-auto">
        <FadeUp className="text-center mb-16">
          <span className="text-green-400 text-sm font-semibold tracking-wider uppercase">FAQ</span>
          <h2 className="text-4xl md:text-5xl font-bold text-white mt-3">Questions?</h2>
        </FadeUp>

        <div className="space-y-4">
          {faqs.map((faq, i) => (
            <FadeUp key={i} delay={i * 0.1}>
              <GlowCard className="overflow-hidden" glowColor="green">
                <button
                  onClick={() => setOpen(open === i ? null : i)}
                  className="w-full flex items-center justify-between p-6 text-left"
                >
                  <span className="text-lg font-medium text-white">{faq.question}</span>
                  <motion.div animate={{ rotate: open === i ? 180 : 0 }} transition={{ duration: 0.3 }}>
                    <ChevronDown className="h-5 w-5 text-gray-400" />
                  </motion.div>
                </button>
                <AnimatePresence>
                  {open === i && (
                    <motion.div
                      initial={{ height: 0, opacity: 0 }}
                      animate={{ height: "auto", opacity: 1 }}
                      exit={{ height: 0, opacity: 0 }}
                      transition={{ duration: 0.3 }}
                    >
                      <p className="px-6 pb-6 text-gray-400">{faq.answer}</p>
                    </motion.div>
                  )}
                </AnimatePresence>
              </GlowCard>
            </FadeUp>
          ))}
        </div>
      </div>
    </section>
  )
}

// ============== CTA SECTION ==============
function CTASection() {
  return (
    <section className="py-20 px-6">
      <FadeUp>
        <div className="max-w-4xl mx-auto relative">
          <div className="absolute inset-0 bg-gradient-to-r from-green-500/20 via-emerald-500/20 to-teal-500/20 rounded-3xl blur-3xl" />
          <div className="relative rounded-3xl border border-gray-800 bg-gray-900/80 backdrop-blur-xl p-12 md:p-16 text-center overflow-hidden">
            {/* Grid Pattern */}
            <div className="absolute inset-0 bg-[linear-gradient(rgba(255,255,255,0.02)_1px,transparent_1px),linear-gradient(90deg,rgba(255,255,255,0.02)_1px,transparent_1px)] bg-[size:32px_32px]" />

            <div className="relative z-10">
              <h2 className="text-4xl md:text-5xl font-bold text-white mb-4">
                Ready to try D23?
              </h2>
              <p className="text-gray-400 text-lg mb-10 max-w-xl mx-auto">
                Join 5000+ Indians already using D23 AI for instant answers in their language.
              </p>

              <div className="flex flex-wrap justify-center gap-4">
                <motion.div whileHover={{ scale: 1.05 }} whileTap={{ scale: 0.95 }}>
                  <Link
                    href="https://api.whatsapp.com/send/?phone=%2B919934438606&text=Hey+D23%21+What+can+you+do%3F&type=phone_number&app_absent=0"
                    target="_blank"
                    className="inline-flex items-center gap-3 px-8 py-4 rounded-full bg-gradient-to-r from-green-500 to-emerald-600 text-white font-semibold shadow-2xl shadow-green-500/30"
                  >
                    <MessageCircle className="h-5 w-5" />
                    Start on WhatsApp
                  </Link>
                </motion.div>
                <motion.div whileHover={{ scale: 1.05 }} whileTap={{ scale: 0.95 }}>
                  <Link
                    href="/chat"
                    className="inline-flex items-center gap-3 px-8 py-4 rounded-full bg-gray-800 border border-gray-700 text-white font-semibold hover:bg-gray-700 transition-colors"
                  >
                    Try Web Version
                  </Link>
                </motion.div>
              </div>
            </div>
          </div>
        </div>
      </FadeUp>
    </section>
  )
}

// ============== FOOTER ==============
function Footer() {
  return (
    <footer className="py-12 px-6 border-t border-gray-800">
      <div className="max-w-6xl mx-auto">
        <div className="flex flex-col md:flex-row items-center justify-between gap-6">
          <div className="flex items-center gap-3">
            <Image src="/puch/logo.png" alt="D23" width={32} height={32} />
            <span className="text-white font-semibold">D23.AI</span>
          </div>
          <p className="text-gray-500 text-sm">© 2025 D23 AI. Built for every Indian language.</p>
          <div className="flex items-center gap-4">
            {["twitter", "instagram", "github"].map((social) => (
              <Link key={social} href="#" className="text-gray-500 hover:text-white transition-colors">
                <div className="w-8 h-8 rounded-full bg-gray-800 flex items-center justify-center">
                  <span className="text-xs">{social[0].toUpperCase()}</span>
                </div>
              </Link>
            ))}
          </div>
        </div>
      </div>
    </footer>
  )
}

// ============== MAIN PAGE ==============
export default function V3Page() {
  return (
    <div className="min-h-screen bg-gray-950 text-white overflow-x-hidden">
      <Header />
      <main>
        <HeroSection />
        <VideoSection />
        <BentoSection />
        <ShowcaseSection />
        <PhoneMockupSection />
        <FAQSection />
        <CTASection />
      </main>
      <Footer />
    </div>
  )
}
