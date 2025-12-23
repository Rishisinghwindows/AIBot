"use client"

import { useState, useRef, useEffect } from "react"
import Image from "next/image"
import Link from "next/link"
import { motion, useScroll, useTransform, useInView, useMotionValue, useSpring, AnimatePresence } from "framer-motion"

// Fix for hydration mismatch with framer-motion
const useHydrated = () => {
  const [hydrated, setHydrated] = useState(false)
  useEffect(() => {
    setHydrated(true)
  }, [])
  return hydrated
}
import { Sparkles, Mic, ShieldCheck, Sticker, Gamepad2, MessageCircle, ChevronDown, ArrowRight, Play, Languages, ImageIcon, Zap, Globe, Twitter, Linkedin } from "lucide-react"
import { cn } from "@/lib/utils"
import { LanguageProvider, useLanguage, useTranslations, languages as supportedLanguages } from "@/lib/i18n/LanguageContext"
import { LanguageSwitcher, LanguageBar } from "@/components/LanguageSwitcher"

// ============== DATA ==============
const rotatingWords = ["पूछो", "કહો", "ಕೇಳಿ", "అడుగు", "D23"]

// Languages for the marquee - in their native scripts
const marqueeLanguages = [
  { name: "हिंदी", code: "hi", english: "Hindi" },
  { name: "தமிழ்", code: "ta", english: "Tamil" },
  { name: "తెలుగు", code: "te", english: "Telugu" },
  { name: "ಕನ್ನಡ", code: "kn", english: "Kannada" },
  { name: "മലയാളം", code: "ml", english: "Malayalam" },
  { name: "ગુજરાતી", code: "gu", english: "Gujarati" },
  { name: "मराठी", code: "mr", english: "Marathi" },
  { name: "বাংলা", code: "bn", english: "Bengali" },
  { name: "ਪੰਜਾਬੀ", code: "pa", english: "Punjabi" },
  { name: "ଓଡ଼ିଆ", code: "or", english: "Odia" },
  { name: "English", code: "en", english: "English" },
]

// ============== LANGUAGE MARQUEE ==============
function LanguageMarquee() {
  return (
    <div className="relative w-full overflow-hidden py-8 bg-black/50 backdrop-blur-sm border-y border-white/5">
      {/* Gradient Overlays */}
      <div className="absolute left-0 top-0 bottom-0 w-32 bg-gradient-to-r from-black to-transparent z-10" />
      <div className="absolute right-0 top-0 bottom-0 w-32 bg-gradient-to-l from-black to-transparent z-10" />

      {/* First Row - Moving Right */}
      <div className="flex animate-marquee whitespace-nowrap">
        {[...marqueeLanguages, ...marqueeLanguages, ...marqueeLanguages].map((lang, i) => (
          <span
            key={`${lang.code}-${i}`}
            className="mx-8 md:mx-12 text-2xl md:text-4xl font-medium text-zinc-400 hover:text-white transition-colors cursor-default select-none"
          >
            {lang.name}
          </span>
        ))}
      </div>

      {/* Second Row - Moving Left (Reverse) */}
      <div className="flex animate-marquee-reverse whitespace-nowrap mt-4">
        {[...marqueeLanguages, ...marqueeLanguages, ...marqueeLanguages].reverse().map((lang, i) => (
          <span
            key={`reverse-${lang.code}-${i}`}
            className="mx-8 md:mx-12 text-xl md:text-3xl font-medium text-zinc-500/60 hover:text-zinc-300 transition-colors cursor-default select-none"
          >
            {lang.english}
          </span>
        ))}
      </div>
    </div>
  )
}

// ============== MAGNETIC BUTTON ==============
function MagneticButton({ children, className = "" }: { children: React.ReactNode; className?: string }) {
  const ref = useRef<HTMLDivElement>(null)
  const x = useMotionValue(0)
  const y = useMotionValue(0)
  const springX = useSpring(x, { stiffness: 300, damping: 20 })
  const springY = useSpring(y, { stiffness: 300, damping: 20 })

  const handleMouse = (e: React.MouseEvent) => {
    if (!ref.current) return
    const rect = ref.current.getBoundingClientRect()
    const centerX = rect.left + rect.width / 2
    const centerY = rect.top + rect.height / 2
    x.set((e.clientX - centerX) * 0.2)
    y.set((e.clientY - centerY) * 0.2)
  }

  const reset = () => { x.set(0); y.set(0) }

  return (
    <motion.div
      ref={ref}
      onMouseMove={handleMouse}
      onMouseLeave={reset}
      style={{ x: springX, y: springY }}
      className={className}
    >
      {children}
    </motion.div>
  )
}

// ============== 3D TILT CARD ==============
function TiltCard({ children, className = "" }: { children: React.ReactNode; className?: string }) {
  const ref = useRef<HTMLDivElement>(null)
  const x = useMotionValue(0)
  const y = useMotionValue(0)
  const rotateX = useSpring(useTransform(y, [-0.5, 0.5], [10, -10]), { stiffness: 300, damping: 30 })
  const rotateY = useSpring(useTransform(x, [-0.5, 0.5], [-10, 10]), { stiffness: 300, damping: 30 })

  const handleMouse = (e: React.MouseEvent) => {
    if (!ref.current) return
    const rect = ref.current.getBoundingClientRect()
    x.set((e.clientX - rect.left) / rect.width - 0.5)
    y.set((e.clientY - rect.top) / rect.height - 0.5)
  }

  const reset = () => { x.set(0); y.set(0) }

  return (
    <motion.div
      ref={ref}
      onMouseMove={handleMouse}
      onMouseLeave={reset}
      style={{ rotateX, rotateY, transformStyle: "preserve-3d" }}
      className={className}
    >
      {children}
    </motion.div>
  )
}

// ============== TEXT REVEAL ==============
function TextReveal({ children, className = "" }: { children: string; className?: string }) {
  const ref = useRef(null)
  const isInView = useInView(ref, { once: true, margin: "-100px" })

  return (
    <span ref={ref} className={cn("inline-block overflow-hidden", className)}>
      <motion.span
        initial={{ y: "100%" }}
        animate={isInView ? { y: 0 } : {}}
        transition={{ duration: 0.8, ease: [0.22, 1, 0.36, 1] }}
        className="inline-block"
      >
        {children}
      </motion.span>
    </span>
  )
}

// ============== STAGGER CONTAINER ==============
function StaggerContainer({ children, className = "" }: { children: React.ReactNode; className?: string }) {
  const ref = useRef(null)
  const isInView = useInView(ref, { once: true, margin: "-50px" })

  return (
    <motion.div
      ref={ref}
      initial="hidden"
      animate={isInView ? "visible" : "hidden"}
      variants={{ visible: { transition: { staggerChildren: 0.1 } } }}
      className={className}
    >
      {children}
    </motion.div>
  )
}

function StaggerItem({ children, className = "" }: { children: React.ReactNode; className?: string }) {
  return (
    <motion.div
      variants={{
        hidden: { opacity: 0, y: 30 },
        visible: { opacity: 1, y: 0, transition: { duration: 0.6, ease: [0.22, 1, 0.36, 1] } }
      }}
      className={className}
    >
      {children}
    </motion.div>
  )
}

// ============== GRADIENT TEXT ==============
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

// ============== ROTATING WORD ==============
function RotatingWord({ words }: { words: string[] }) {
  const [index, setIndex] = useState(0)

  useEffect(() => {
    const interval = setInterval(() => setIndex((i) => (i + 1) % words.length), 2500)
    return () => clearInterval(interval)
  }, [words.length])

  return (
    <AnimatePresence mode="wait">
      <motion.span
        key={index}
        initial={{ opacity: 0, y: 30, rotateX: -90 }}
        animate={{ opacity: 1, y: 0, rotateX: 0 }}
        exit={{ opacity: 0, y: -30, rotateX: 90 }}
        transition={{ duration: 0.5, ease: [0.22, 1, 0.36, 1] }}
        className="inline-block"
      >
        <GradientText>{words[index]}</GradientText>
      </motion.span>
    </AnimatePresence>
  )
}

// ============== ANIMATED GRADIENT BORDER ==============
function GradientBorderCard({ children, className = "" }: { children: React.ReactNode; className?: string }) {
  return (
    <div className={cn("relative p-[1px] rounded-2xl overflow-hidden group", className)}>
      <motion.div
        animate={{ rotate: 360 }}
        transition={{ duration: 8, repeat: Infinity, ease: "linear" }}
        className="absolute inset-0 bg-gradient-to-r from-violet-500 via-fuchsia-500 to-pink-500 opacity-50 group-hover:opacity-100 transition-opacity"
        style={{ filter: "blur(8px)" }}
      />
      <div className="absolute inset-0 bg-gradient-to-r from-violet-500 via-fuchsia-500 to-pink-500 rounded-2xl" />
      <div className="relative bg-black rounded-2xl">{children}</div>
    </div>
  )
}

// ============== HEADER ==============
function Header() {
  const [scrolled, setScrolled] = useState(false)
  const t = useTranslations()

  useEffect(() => {
    const handleScroll = () => setScrolled(window.scrollY > 50)
    window.addEventListener("scroll", handleScroll)
    return () => window.removeEventListener("scroll", handleScroll)
  }, [])

  return (
    <motion.header
      initial={{ y: -100 }}
      animate={{ y: 0 }}
      transition={{ duration: 0.8, ease: [0.22, 1, 0.36, 1] }}
      className={cn(
        "fixed top-0 left-0 right-0 z-50 transition-all duration-500",
        scrolled ? "bg-black/70 backdrop-blur-xl border-b border-white/10" : ""
      )}
    >
      <div className="max-w-7xl mx-auto px-6 py-4">
        <div className="flex items-center justify-between">
          <Link href="/" className="flex items-center gap-2">
            <motion.div whileHover={{ rotate: 360 }} transition={{ duration: 0.5 }}>
              <Image src="/puch/logo.png" alt="D23" width={40} height={40} />
            </motion.div>
            <span className="text-xl font-bold text-white">D23<GradientText>.AI</GradientText></span>
          </Link>

          <nav className="hidden md:flex items-center gap-8">
            <Link href="#features" className="relative text-sm text-zinc-400 hover:text-white transition-colors group">
              {t.nav.features}
              <span className="absolute -bottom-1 left-0 w-0 h-0.5 bg-gradient-to-r from-violet-500 to-pink-500 group-hover:w-full transition-all duration-300" />
            </Link>
            <Link href="/about" className="relative text-sm text-zinc-400 hover:text-white transition-colors group">
              {t.nav.about}
              <span className="absolute -bottom-1 left-0 w-0 h-0.5 bg-gradient-to-r from-violet-500 to-pink-500 group-hover:w-full transition-all duration-300" />
            </Link>
            <Link href="#contact" className="relative text-sm text-zinc-400 hover:text-white transition-colors group">
              {t.nav.contact}
              <span className="absolute -bottom-1 left-0 w-0 h-0.5 bg-gradient-to-r from-violet-500 to-pink-500 group-hover:w-full transition-all duration-300" />
            </Link>
          </nav>

          <div className="flex items-center gap-4">
            <LanguageSwitcher variant="pill" />
            <MagneticButton>
              <Link
                href="https://api.whatsapp.com/send/?phone=%2B919934438606&text=Hey+D23%21+What+can+you+do%3F&type=phone_number&app_absent=0"
                target="_blank"
                className="flex items-center gap-2 px-5 py-2.5 rounded-full bg-gradient-to-r from-violet-600 to-fuchsia-600 text-white text-sm font-medium shadow-lg shadow-violet-500/25 hover:shadow-violet-500/40 transition-shadow"
              >
                <Zap className="h-4 w-4" />
                {t.nav.getStarted}
              </Link>
            </MagneticButton>
          </div>
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
  const opacity = useTransform(scrollYProgress, [0, 0.5], [1, 0])
  const scale = useTransform(scrollYProgress, [0, 0.5], [1, 0.95])
  const t = useTranslations()

  const stats = [
    { value: "5000+", label: t.stats.users },
    { value: "11+", label: t.stats.languages },
    { value: "24/7", label: t.stats.available },
    { value: "<2s", label: t.stats.response },
  ]

  return (
    <section ref={ref} className="relative min-h-screen flex items-center justify-center overflow-hidden">
      {/* Animated Background */}
      <div className="absolute inset-0 bg-black">
        <motion.div
          animate={{ scale: [1, 1.2, 1], opacity: [0.3, 0.5, 0.3] }}
          transition={{ duration: 8, repeat: Infinity }}
          className="absolute top-1/4 left-1/4 w-[600px] h-[600px] bg-violet-600/30 rounded-full blur-[120px]"
        />
        <motion.div
          animate={{ scale: [1.2, 1, 1.2], opacity: [0.3, 0.5, 0.3] }}
          transition={{ duration: 10, repeat: Infinity }}
          className="absolute bottom-1/4 right-1/4 w-[500px] h-[500px] bg-fuchsia-600/30 rounded-full blur-[120px]"
        />
        <motion.div
          animate={{ scale: [1, 1.3, 1], opacity: [0.2, 0.4, 0.2] }}
          transition={{ duration: 12, repeat: Infinity }}
          className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[700px] h-[700px] bg-pink-600/20 rounded-full blur-[150px]"
        />
        {/* Grid Overlay */}
        <div className="absolute inset-0 bg-[linear-gradient(rgba(255,255,255,0.03)_1px,transparent_1px),linear-gradient(90deg,rgba(255,255,255,0.03)_1px,transparent_1px)] bg-[size:50px_50px]" />
      </div>

      <motion.div style={{ y, opacity, scale }} className="relative z-10 max-w-5xl mx-auto px-6 text-center pt-24">
        {/* Badge */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.2 }}
          className="inline-flex items-center gap-2 px-4 py-2 rounded-full border border-violet-500/30 bg-violet-500/10 backdrop-blur-sm mb-8"
        >
          <motion.span
            animate={{ scale: [1, 1.2, 1] }}
            transition={{ duration: 2, repeat: Infinity }}
            className="flex h-2 w-2 rounded-full bg-violet-400"
          />
          <span className="text-sm text-violet-300">{t.hero.badge}</span>
        </motion.div>

        {/* Headline */}
        <h1 className="text-5xl sm:text-6xl md:text-7xl lg:text-8xl font-bold text-white mb-6 leading-[1.1]">
          <TextReveal>{t.hero.headline1}</TextReveal>
          <br />
          <span className="text-zinc-500">{t.hero.headline2} </span>
          <RotatingWord words={rotatingWords} />
        </h1>

        {/* Subtitle */}
        <motion.p
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.6 }}
          className="text-lg md:text-xl text-zinc-400 max-w-2xl mx-auto mb-10"
        >
          {t.hero.subtitle}
        </motion.p>

        {/* CTA Buttons */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.8 }}
          className="flex flex-wrap items-center justify-center gap-4"
        >
          <MagneticButton>
            <Link
              href="https://api.whatsapp.com/send/?phone=%2B919934438606&text=Hey+D23%21+What+can+you+do%3F&type=phone_number&app_absent=0"
              target="_blank"
              className="group flex items-center gap-3 px-8 py-4 rounded-full bg-gradient-to-r from-violet-600 via-fuchsia-600 to-pink-600 text-white font-semibold shadow-2xl shadow-violet-500/30 hover:shadow-violet-500/50 transition-all"
            >
              <MessageCircle className="h-5 w-5" />
              {t.hero.ctaWhatsapp}
              <ArrowRight className="h-5 w-5 group-hover:translate-x-1 transition-transform" />
            </Link>
          </MagneticButton>
          <MagneticButton>
            <Link
              href="/chat"
              className="flex items-center gap-3 px-8 py-4 rounded-full border border-white/20 text-white font-semibold hover:bg-white/5 transition-colors"
            >
              {t.hero.ctaWeb}
            </Link>
          </MagneticButton>
        </motion.div>

        {/* App Store Buttons */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 1 }}
          className="flex flex-wrap items-center justify-center gap-4 mt-6"
        >
          <div className="relative group cursor-pointer">
            <div className="flex items-center gap-3 px-6 py-3 rounded-xl bg-zinc-900 border border-zinc-800 hover:border-zinc-700 transition-colors">
              <svg className="w-8 h-8 text-white" viewBox="0 0 24 24" fill="currentColor">
                <path d="M18.71 19.5c-.83 1.24-1.71 2.45-3.05 2.47-1.34.03-1.77-.79-3.29-.79-1.53 0-2 .77-3.27.82-1.31.05-2.3-1.32-3.14-2.53C4.25 17 2.94 12.45 4.7 9.39c.87-1.52 2.43-2.48 4.12-2.51 1.28-.02 2.5.87 3.29.87.78 0 2.26-1.07 3.81-.91.65.03 2.47.26 3.64 1.98-.09.06-2.17 1.28-2.15 3.81.03 3.02 2.65 4.03 2.68 4.04-.03.07-.42 1.44-1.38 2.83M13 3.5c.73-.83 1.94-1.46 2.94-1.5.13 1.17-.34 2.35-1.04 3.19-.69.85-1.83 1.51-2.95 1.42-.15-1.15.41-2.35 1.05-3.11z"/>
              </svg>
              <div className="text-left">
                <p className="text-[10px] text-zinc-500 uppercase tracking-wider">{t.hero.comingSoon}</p>
                <p className="text-white font-semibold text-sm">{t.hero.appStore}</p>
              </div>
            </div>
            <div className="absolute -top-2 -right-2 px-2 py-0.5 rounded-full bg-gradient-to-r from-violet-500 to-fuchsia-500 text-[10px] text-white font-semibold">
              {t.hero.soon}
            </div>
          </div>

          <div className="relative group cursor-pointer">
            <div className="flex items-center gap-3 px-6 py-3 rounded-xl bg-zinc-900 border border-zinc-800 hover:border-zinc-700 transition-colors">
              <svg className="w-8 h-8 text-white" viewBox="0 0 24 24" fill="currentColor">
                <path d="M3.609 1.814L13.792 12 3.61 22.186a.996.996 0 0 1-.61-.92V2.734a1 1 0 0 1 .609-.92zm10.89 10.893l2.302 2.302-10.937 6.333 8.635-8.635zm3.199-3.198l2.807 1.626a1 1 0 0 1 0 1.73l-2.808 1.626L15.206 12l2.492-2.491zM5.864 2.658L16.8 8.99l-2.302 2.302-8.634-8.634z"/>
              </svg>
              <div className="text-left">
                <p className="text-[10px] text-zinc-500 uppercase tracking-wider">{t.hero.comingSoon}</p>
                <p className="text-white font-semibold text-sm">{t.hero.playStore}</p>
              </div>
            </div>
            <div className="absolute -top-2 -right-2 px-2 py-0.5 rounded-full bg-gradient-to-r from-violet-500 to-fuchsia-500 text-[10px] text-white font-semibold">
              {t.hero.soon}
            </div>
          </div>
        </motion.div>

        {/* Stats */}
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 1.2 }}
          className="flex items-center justify-center gap-8 md:gap-16 mt-16"
        >
          {stats.map((stat) => (
            <div key={stat.label} className="text-center">
              <div className="text-2xl md:text-3xl font-bold text-white">{stat.value}</div>
              <div className="text-sm text-zinc-500">{stat.label}</div>
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
        <motion.div animate={{ y: [0, 10, 0] }} transition={{ duration: 2, repeat: Infinity }}>
          <ChevronDown className="h-6 w-6 text-zinc-500" />
        </motion.div>
      </motion.div>
    </section>
  )
}

// ============== VIDEO SECTION ==============
function VideoSection() {
  const t = useTranslations()

  return (
    <section className="py-16 px-6">
      <div className="max-w-5xl mx-auto">
        <StaggerContainer className="text-center mb-12">
          <StaggerItem>
            <span className="text-violet-400 text-sm font-semibold tracking-wider uppercase">{t.video.label}</span>
          </StaggerItem>
          <StaggerItem>
            <h2 className="text-4xl md:text-5xl font-bold text-white mt-3">{t.video.title}</h2>
          </StaggerItem>
        </StaggerContainer>

        <StaggerItem>
          <TiltCard className="perspective-1000">
            <GradientBorderCard>
              <div className="p-2">
                <div className="group relative rounded-xl overflow-hidden cursor-pointer">
                  <video
                    className="w-full aspect-video object-cover rounded-xl"
                    src="/puch/Puch_AI_Launch.mp4"
                    autoPlay
                    loop
                    muted
                    playsInline
                  />
                  <div className="absolute inset-0 bg-black/60 flex items-center justify-center opacity-100 group-hover:opacity-0 transition-opacity duration-500">
                    <div className="flex items-center gap-4">
                      <motion.div
                        animate={{ scale: [1, 1.1, 1] }}
                        transition={{ duration: 2, repeat: Infinity }}
                        className="w-20 h-20 rounded-full bg-gradient-to-r from-violet-500 to-fuchsia-500 flex items-center justify-center shadow-2xl shadow-violet-500/50"
                      >
                        <Play className="h-8 w-8 text-white ml-1" fill="white" />
                      </motion.div>
                      <div className="text-left">
                        <p className="text-white font-semibold text-xl">{t.video.videoTitle}</p>
                        <p className="text-zinc-400 text-sm">{t.video.videoSubtitle}</p>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </GradientBorderCard>
          </TiltCard>
        </StaggerItem>
      </div>
    </section>
  )
}

// ============== FEATURES GRID ==============
function FeaturesSection() {
  const t = useTranslations()

  const features = [
    { id: "languages", icon: <Languages className="h-6 w-6" />, titleKey: "languages", color: "from-violet-500 to-purple-500" },
    { id: "voice", icon: <Mic className="h-6 w-6" />, titleKey: "voice", color: "from-fuchsia-500 to-pink-500" },
    { id: "images", icon: <ImageIcon className="h-6 w-6" />, titleKey: "images", color: "from-orange-500 to-red-500" },
    { id: "factCheck", icon: <ShieldCheck className="h-6 w-6" />, titleKey: "factCheck", color: "from-cyan-500 to-blue-500" },
    { id: "stickers", icon: <Sticker className="h-6 w-6" />, titleKey: "stickers", color: "from-green-500 to-emerald-500" },
    { id: "games", icon: <Gamepad2 className="h-6 w-6" />, titleKey: "games", color: "from-amber-500 to-yellow-500" },
  ]

  return (
    <section id="features" className="py-24 px-6">
      <div className="max-w-6xl mx-auto">
        <StaggerContainer className="text-center mb-16">
          <StaggerItem>
            <span className="text-violet-400 text-sm font-semibold tracking-wider uppercase">{t.features.label}</span>
          </StaggerItem>
          <StaggerItem>
            <h2 className="text-4xl md:text-5xl font-bold text-white mt-3">
              {t.features.title1}
              <br />
              <GradientText>{t.features.title2}</GradientText>
            </h2>
          </StaggerItem>
        </StaggerContainer>

        <StaggerContainer className="grid md:grid-cols-2 lg:grid-cols-3 gap-6">
          {features.map((feature) => {
            const featureData = t.features[feature.titleKey as keyof typeof t.features] as { title: string; desc: string }
            return (
              <StaggerItem key={feature.id}>
                <TiltCard className="h-full">
                  <GradientBorderCard className="h-full">
                    <div className="p-6 h-full">
                      <motion.div
                        whileHover={{ scale: 1.1, rotate: 5 }}
                        className={cn(
                          "w-14 h-14 rounded-2xl flex items-center justify-center mb-5 bg-gradient-to-br",
                          feature.color
                        )}
                      >
                        {feature.icon}
                      </motion.div>
                      <h3 className="text-xl font-semibold text-white mb-2">{featureData?.title}</h3>
                      <p className="text-zinc-400">{featureData?.desc}</p>
                    </div>
                  </GradientBorderCard>
                </TiltCard>
              </StaggerItem>
            )
          })}
        </StaggerContainer>
      </div>
    </section>
  )
}

// ============== MULTILINGUAL CHAT MESSAGES ==============
const multilingualMessages = [
  { lang: "Hindi", langCode: "hi", user: "मुझे आज का मौसम बताओ", bot: "दिल्ली में आज 32°C है, धूप और साफ आसमान। शाम को हल्की बारिश की संभावना है।", flag: "🇮🇳" },
  { lang: "Tamil", langCode: "ta", user: "இன்றைய செய்தி என்ன?", bot: "இந்தியா vs ஆஸ்திரேலியா கிரிக்கெட் போட்டியில் இந்தியா 7 விக்கெட் வித்தியாசத்தில் வெற்றி பெற்றது!", flag: "🇮🇳" },
  { lang: "Telugu", langCode: "te", user: "నాకు ఒక జోక్ చెప్పు", bot: "టీచర్: నువ్వు హోమ్‌వర్క్ ఎందుకు చేయలేదు? స్టూడెంట్: మా ఇంట్లో లైట్ పోయింది సార్! 😄", flag: "🇮🇳" },
  { lang: "Bengali", langCode: "bn", user: "একটি রেসিপি বলুন", bot: "মাছের ঝোল: সরিষার তেলে মাছ ভাজুন, পেঁয়াজ-রসুন বাটা দিন, হলুদ-লংকা মেশান।", flag: "🇮🇳" },
  { lang: "Marathi", langCode: "mr", user: "आज कोणता सण आहे?", bot: "आज गणेश चतुर्थी आहे! गणपती बाप्पा मोरया! 🙏", flag: "🇮🇳" },
  { lang: "Gujarati", langCode: "gu", user: "મને એક વાર્તા કહો", bot: "એક સમયે એક ડાહ્યો કાગડો હતો. તે પાણી માટે ઘડામાં કાંકરા નાખીને પાણી ઉપર લાવ્યો! 🪨", flag: "🇮🇳" },
  { lang: "Kannada", langCode: "kn", user: "ಇಂದು ಯಾವ ದಿನ?", bot: "ಇಂದು ಶುಕ್ರವಾರ, ಡಿಸೆಂಬರ್ 18, 2025. ಶುಭ ದಿನ! ✨", flag: "🇮🇳" },
  { lang: "Malayalam", langCode: "ml", user: "ഒരു ചിത്രം ഉണ്ടാക്കൂ", bot: "ശരി! ഞാൻ നിങ്ങൾക്കായി ഒരു മനോഹരമായ കേരള ബാക്ക്‌വാട്ടർ ചിത്രം ഉണ്ടാക്കുന്നു... 🎨", flag: "🇮🇳" },
  { lang: "Punjabi", langCode: "pa", user: "ਮੈਨੂੰ ਗਾਣਾ ਸੁਣਾਓ", bot: "ਬੱਲੇ ਬੱਲੇ! ਤੁਸੀਂ ਕਿਹੜਾ ਗਾਣਾ ਸੁਣਨਾ ਚਾਹੁੰਦੇ ਹੋ? 🎵", flag: "🇮🇳" },
  { lang: "Odia", langCode: "or", user: "ଆଜି ପାଣିପାଗ କେମିତି?", bot: "ଭୁବନେଶ୍ୱରରେ ଆଜି 28°C, ଆଂଶିକ ମେଘୁଆ ଆକାଶ। ☀️", flag: "🇮🇳" },
  { lang: "English", langCode: "en", user: "Tell me a fact", bot: "Did you know? India has 22 official languages and over 19,500 dialects! 🌍", flag: "🇬🇧" },
]

// ============== CHAT MESSAGE SHOWCASE ==============
function ChatShowcase() {
  const scrollRef = useRef<HTMLDivElement>(null)
  const [isHovered, setIsHovered] = useState(false)
  const t = useTranslations()

  useEffect(() => {
    const container = scrollRef.current
    if (!container) return

    let animationId: number
    let scrollPosition = 0
    const scrollSpeed = 0.5

    const autoScroll = () => {
      if (!isHovered && container) {
        scrollPosition += scrollSpeed
        if (scrollPosition >= container.scrollHeight - container.clientHeight) {
          scrollPosition = 0
        }
        container.scrollTop = scrollPosition
      }
      animationId = requestAnimationFrame(autoScroll)
    }

    animationId = requestAnimationFrame(autoScroll)
    return () => cancelAnimationFrame(animationId)
  }, [isHovered])

  return (
    <motion.div
      initial={{ opacity: 0, x: 50 }}
      whileInView={{ opacity: 1, x: 0 }}
      viewport={{ once: true }}
      className="flex-shrink-0 w-80"
    >
      <TiltCard>
        <GradientBorderCard className="group">
          <div className="aspect-[3/4] relative overflow-hidden rounded-xl bg-gradient-to-b from-zinc-900 to-black">
            {/* Chat Header */}
            <div className="sticky top-0 z-10 bg-gradient-to-r from-violet-600 to-fuchsia-600 px-4 py-3 flex items-center gap-3">
              <div className="w-10 h-10 rounded-full bg-white/20 flex items-center justify-center">
                <MessageCircle className="w-5 h-5 text-white" />
              </div>
              <div>
                <p className="text-white font-semibold text-sm">D23 AI</p>
                <p className="text-white/70 text-xs flex items-center gap-1">
                  <span className="w-2 h-2 rounded-full bg-green-400 animate-pulse" />
                  {t.showcase.languagesCount}
                </p>
              </div>
              <Languages className="w-5 h-5 text-white/70 ml-auto" />
            </div>

            {/* Scrollable Messages */}
            <div
              ref={scrollRef}
              onMouseEnter={() => setIsHovered(true)}
              onMouseLeave={() => setIsHovered(false)}
              className="h-[calc(100%-60px)] overflow-y-auto px-3 py-3 space-y-3 scrollbar-thin scrollbar-thumb-violet-500/30 scrollbar-track-transparent"
              style={{ scrollBehavior: isHovered ? 'smooth' : 'auto' }}
            >
              {multilingualMessages.map((msg, i) => (
                <motion.div
                  key={i}
                  initial={{ opacity: 0, y: 10 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: i * 0.1 }}
                  className="space-y-2"
                >
                  <div className="flex items-center justify-center gap-1.5">
                    <span className="text-xs">{msg.flag}</span>
                    <span className="text-[10px] text-zinc-500 font-medium uppercase tracking-wider">{msg.lang}</span>
                  </div>
                  <div className="flex justify-end">
                    <div className="max-w-[85%] bg-violet-600 text-white text-xs px-3 py-2 rounded-2xl rounded-br-md shadow-lg">
                      {msg.user}
                    </div>
                  </div>
                  <div className="flex justify-start">
                    <div className="max-w-[85%] bg-zinc-800 text-zinc-200 text-xs px-3 py-2 rounded-2xl rounded-bl-md shadow-lg border border-zinc-700/50">
                      {msg.bot}
                    </div>
                  </div>
                </motion.div>
              ))}
              {multilingualMessages.map((msg, i) => (
                <motion.div key={`repeat-${i}`} className="space-y-2">
                  <div className="flex items-center justify-center gap-1.5">
                    <span className="text-xs">{msg.flag}</span>
                    <span className="text-[10px] text-zinc-500 font-medium uppercase tracking-wider">{msg.lang}</span>
                  </div>
                  <div className="flex justify-end">
                    <div className="max-w-[85%] bg-violet-600 text-white text-xs px-3 py-2 rounded-2xl rounded-br-md shadow-lg">
                      {msg.user}
                    </div>
                  </div>
                  <div className="flex justify-start">
                    <div className="max-w-[85%] bg-zinc-800 text-zinc-200 text-xs px-3 py-2 rounded-2xl rounded-bl-md shadow-lg border border-zinc-700/50">
                      {msg.bot}
                    </div>
                  </div>
                </motion.div>
              ))}
            </div>

            <div className="absolute top-[52px] left-0 right-0 h-8 bg-gradient-to-b from-zinc-900 to-transparent pointer-events-none z-[5]" />
            <div className="absolute bottom-0 left-0 right-0 h-8 bg-gradient-to-t from-black to-transparent pointer-events-none z-[5]" />

            <div className="absolute bottom-3 left-3 right-3 z-10">
              <span className="inline-block px-3 py-1 rounded-full bg-violet-500/20 border border-violet-500/30 text-violet-300 text-xs font-medium mb-2">
                {t.showcase.multilingual}
              </span>
              <h3 className="text-xl font-bold text-white">{t.showcase.languagesCount}</h3>
            </div>
          </div>
        </GradientBorderCard>
      </TiltCard>
    </motion.div>
  )
}

// ============== SHOWCASE SECTION ==============
function ShowcaseSection() {
  const t = useTranslations()

  const showcaseItems = [
    { title: "Shinchanify", image: "/puch/features/siddarth-shinchanified.png", tag: "Fun" },
    { title: "Image Gen", image: "/puch/features/salman.png", tag: "Creative" },
    { title: "Stickers", image: "/puch/features/dragon.png", tag: "Custom" },
    { title: "Voice", image: "/puch/features/salman-3.webp", tag: "Voice" },
    { title: "Games", image: "/puch/assets/wordle/wordlewin.jpeg", tag: "Play" },
  ]

  return (
    <section className="py-20 overflow-hidden">
      <div className="max-w-7xl mx-auto px-6 mb-12">
        <StaggerContainer>
          <StaggerItem>
            <span className="text-violet-400 text-sm font-semibold tracking-wider uppercase">{t.showcase.label}</span>
          </StaggerItem>
          <StaggerItem>
            <h2 className="text-4xl md:text-5xl font-bold text-white mt-3">{t.showcase.title}</h2>
          </StaggerItem>
        </StaggerContainer>
      </div>

      <div className="flex gap-6 px-6 overflow-x-auto pb-6 scrollbar-hide">
        <ChatShowcase />
        {showcaseItems.map((item, i) => (
          <motion.div
            key={item.title}
            initial={{ opacity: 0, x: 50 }}
            whileInView={{ opacity: 1, x: 0 }}
            transition={{ delay: (i + 1) * 0.1 }}
            viewport={{ once: true }}
            className="flex-shrink-0 w-72"
          >
            <TiltCard>
              <GradientBorderCard className="group">
                <div className="aspect-[3/4] relative overflow-hidden rounded-xl">
                  <Image src={item.image} alt={item.title} fill className="object-cover transition-transform duration-700 group-hover:scale-110" />
                  <div className="absolute inset-0 bg-gradient-to-t from-black via-black/30 to-transparent" />
                  <div className="absolute bottom-4 left-4 right-4">
                    <span className="inline-block px-3 py-1 rounded-full bg-violet-500/20 border border-violet-500/30 text-violet-300 text-xs font-medium mb-2">
                      {item.tag}
                    </span>
                    <h3 className="text-xl font-bold text-white">{item.title}</h3>
                  </div>
                </div>
              </GradientBorderCard>
            </TiltCard>
          </motion.div>
        ))}
      </div>
    </section>
  )
}

// ============== FAQ SECTION ==============
function FAQSection() {
  const [open, setOpen] = useState<number | null>(null)
  const t = useTranslations()

  const faqIds = ["q1", "q2", "q3", "q4"] as const

  return (
    <section className="py-20 px-6">
      <div className="max-w-3xl mx-auto">
        <StaggerContainer className="text-center mb-12">
          <StaggerItem>
            <span className="text-violet-400 text-sm font-semibold tracking-wider uppercase">{t.faq.label}</span>
          </StaggerItem>
          <StaggerItem>
            <h2 className="text-3xl md:text-4xl font-bold text-white mt-3">
              {t.faq.title} <GradientText>{t.faq.titleHighlight}</GradientText>
            </h2>
          </StaggerItem>
        </StaggerContainer>

        <StaggerContainer className="space-y-4">
          {faqIds.map((id, i) => (
            <StaggerItem key={id}>
              <GradientBorderCard>
                <button
                  onClick={() => setOpen(open === i ? null : i)}
                  className="w-full flex items-center justify-between p-6 text-left"
                >
                  <span className="text-lg font-medium text-white">{t.faq[id]}</span>
                  <motion.div animate={{ rotate: open === i ? 180 : 0 }} transition={{ duration: 0.3 }}>
                    <ChevronDown className="h-5 w-5 text-violet-400" />
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
                      <p className="px-6 pb-6 text-zinc-400">{t.faq[`a${i + 1}` as keyof typeof t.faq]}</p>
                    </motion.div>
                  )}
                </AnimatePresence>
              </GradientBorderCard>
            </StaggerItem>
          ))}
        </StaggerContainer>
      </div>
    </section>
  )
}

// ============== ABOUT SECTION ==============
function AboutSection() {
  return (
    <section id="about" className="py-20 px-6 relative overflow-hidden">
      <div className="absolute inset-0 bg-gradient-to-b from-black via-violet-950/10 to-black" />

      <div className="max-w-6xl mx-auto relative z-10">
        <StaggerContainer className="text-center mb-12">
          <StaggerItem>
            <span className="text-violet-400 text-sm font-semibold tracking-wider uppercase">About Us</span>
          </StaggerItem>
          <StaggerItem>
            <h2 className="text-3xl md:text-4xl font-bold text-white mt-3">
              Built for <GradientText>Bharat</GradientText>
            </h2>
          </StaggerItem>
        </StaggerContainer>

        <div className="grid md:grid-cols-2 gap-10 items-center">
          <StaggerContainer>
            <StaggerItem>
              <p className="text-lg text-zinc-400 mb-6">
                D23 AI is India's first WhatsApp-native AI assistant designed specifically for Indian users. We understand that language should never be a barrier to accessing AI.
              </p>
            </StaggerItem>
            <StaggerItem>
              <p className="text-lg text-zinc-400 mb-6">
                Our mission is to make AI accessible to every Indian, in their own language. Whether you speak Hindi, Tamil, Telugu, Bengali, or any of the 11+ languages we support, D23 AI understands and responds naturally.
              </p>
            </StaggerItem>
            <StaggerItem>
              <p className="text-lg text-zinc-400">
                From fact-checking viral messages to generating images, from playing games to getting instant answers - D23 AI is your intelligent companion on WhatsApp.
              </p>
            </StaggerItem>
          </StaggerContainer>

          <StaggerItem>
            <TiltCard>
              <GradientBorderCard>
                <div className="p-8 space-y-6">
                  <div className="flex items-center gap-4">
                    <div className="w-12 h-12 rounded-xl bg-gradient-to-br from-violet-500 to-purple-500 flex items-center justify-center">
                      <Globe className="h-6 w-6 text-white" />
                    </div>
                    <div>
                      <p className="text-2xl font-bold text-white">11+</p>
                      <p className="text-zinc-500">Indian Languages</p>
                    </div>
                  </div>
                  <div className="flex items-center gap-4">
                    <div className="w-12 h-12 rounded-xl bg-gradient-to-br from-fuchsia-500 to-pink-500 flex items-center justify-center">
                      <MessageCircle className="h-6 w-6 text-white" />
                    </div>
                    <div>
                      <p className="text-2xl font-bold text-white">WhatsApp</p>
                      <p className="text-zinc-500">Native Experience</p>
                    </div>
                  </div>
                  <div className="flex items-center gap-4">
                    <div className="w-12 h-12 rounded-xl bg-gradient-to-br from-green-500 to-emerald-500 flex items-center justify-center">
                      <Zap className="h-6 w-6 text-white" />
                    </div>
                    <div>
                      <p className="text-2xl font-bold text-white">&lt;2 Seconds</p>
                      <p className="text-zinc-500">Response Time</p>
                    </div>
                  </div>
                </div>
              </GradientBorderCard>
            </TiltCard>
          </StaggerItem>
        </div>
      </div>
    </section>
  )
}

// ============== FOUNDERS SECTION ==============
const founders = [
  {
    name: "Naseer",
    role: "Co-Founder & CEO",
    twitter: "#",
    linkedin: "#"
  },
  {
    name: "Pawan",
    role: "Co-Founder & CPO",
    twitter: "#",
    linkedin: "https://www.linkedin.com/in/pawan-k-singh-119b8a20/"
  },
  {
    name: "Rishi",
    role: "Co-Founder & CTO",
    twitter: "https://x.com/RishiSi92580328",
    linkedin: "https://www.linkedin.com/in/rishi-kumar-5878742a/"
  }
]

function FoundersSection() {
  return (
    <section className="py-16 px-6">
      <div className="max-w-4xl mx-auto">
        <StaggerContainer className="text-center mb-12">
          <StaggerItem>
            <span className="text-violet-400 text-sm font-semibold tracking-wider uppercase">Our Team</span>
          </StaggerItem>
          <StaggerItem>
            <h2 className="text-3xl md:text-4xl font-bold text-white mt-3">
              Meet the <GradientText>Founders</GradientText>
            </h2>
          </StaggerItem>
          <StaggerItem>
            <p className="text-zinc-400 mt-3 max-w-xl mx-auto">
              Passionate technologists on a mission to make AI accessible to every Indian.
            </p>
          </StaggerItem>
        </StaggerContainer>

        <StaggerContainer className="flex flex-wrap justify-center gap-12">
          {founders.map((member) => (
            <StaggerItem key={member.name}>
              <motion.div
                whileHover={{ y: -5 }}
                className="text-center"
              >
                <div className="relative w-32 h-32 mx-auto mb-4">
                  <div className="absolute inset-0 rounded-full bg-gradient-to-r from-violet-500 to-fuchsia-500 blur-md opacity-50" />
                  <div className="relative w-32 h-32 rounded-full bg-zinc-800 flex items-center justify-center border-2 border-violet-500/50 overflow-hidden">
                    <span className="text-4xl font-bold text-white">{member.name[0]}</span>
                  </div>
                </div>
                <h3 className="text-xl font-semibold text-white">{member.name}</h3>
                <p className="text-sm text-zinc-400 mb-3">{member.role}</p>
                <div className="flex justify-center gap-3">
                  <a
                    href={member.twitter}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="w-9 h-9 rounded-full bg-white/5 flex items-center justify-center text-zinc-400 hover:text-white hover:bg-white/10 transition-colors"
                  >
                    <Twitter className="h-4 w-4" />
                  </a>
                  <a
                    href={member.linkedin}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="w-9 h-9 rounded-full bg-white/5 flex items-center justify-center text-zinc-400 hover:text-white hover:bg-white/10 transition-colors"
                  >
                    <Linkedin className="h-4 w-4" />
                  </a>
                </div>
              </motion.div>
            </StaggerItem>
          ))}
        </StaggerContainer>
      </div>
    </section>
  )
}

// ============== CONTACT SECTION ==============
function ContactSection() {
  return (
    <section id="contact" className="py-16 px-6">
      <div className="max-w-4xl mx-auto">
        <StaggerContainer className="text-center mb-12">
          <StaggerItem>
            <span className="text-violet-400 text-sm font-semibold tracking-wider uppercase">Contact</span>
          </StaggerItem>
          <StaggerItem>
            <h2 className="text-4xl md:text-5xl font-bold text-white mt-3">
              Get in <GradientText>Touch</GradientText>
            </h2>
          </StaggerItem>
          <StaggerItem>
            <p className="text-zinc-400 mt-4 max-w-xl mx-auto">
              Have questions or feedback? We'd love to hear from you. Reach out to us through any of these channels.
            </p>
          </StaggerItem>
        </StaggerContainer>

        <StaggerContainer className="grid md:grid-cols-3 gap-6">
          <StaggerItem>
            <TiltCard className="h-full">
              <GradientBorderCard className="h-full">
                <div className="p-6 text-center">
                  <div className="w-14 h-14 rounded-2xl bg-gradient-to-br from-green-500 to-emerald-500 flex items-center justify-center mx-auto mb-4">
                    <MessageCircle className="h-7 w-7 text-white" />
                  </div>
                  <h3 className="text-lg font-semibold text-white mb-2">WhatsApp</h3>
                  <p className="text-zinc-400 text-sm mb-4">Chat with D23 AI directly</p>
                  <Link
                    href="https://api.whatsapp.com/send/?phone=%2B919934438606&text=Hey+D23%21+What+can+you+do%3F&type=phone_number&app_absent=0"
                    target="_blank"
                    className="text-violet-400 hover:text-violet-300 text-sm font-medium"
                  >
                    +91 99344 38606
                  </Link>
                </div>
              </GradientBorderCard>
            </TiltCard>
          </StaggerItem>

          <StaggerItem>
            <TiltCard className="h-full">
              <GradientBorderCard className="h-full">
                <div className="p-6 text-center">
                  <div className="w-14 h-14 rounded-2xl bg-gradient-to-br from-violet-500 to-purple-500 flex items-center justify-center mx-auto mb-4">
                    <svg className="h-7 w-7 text-white" fill="currentColor" viewBox="0 0 24 24">
                      <path d="M20 4H4c-1.1 0-1.99.9-1.99 2L2 18c0 1.1.9 2 2 2h16c1.1 0 2-.9 2-2V6c0-1.1-.9-2-2-2zm0 4l-8 5-8-5V6l8 5 8-5v2z"/>
                    </svg>
                  </div>
                  <h3 className="text-lg font-semibold text-white mb-2">Email</h3>
                  <p className="text-zinc-400 text-sm mb-4">For business inquiries</p>
                  <Link
                    href="mailto:hello@d23.ai"
                    className="text-violet-400 hover:text-violet-300 text-sm font-medium"
                  >
                    hello@d23.ai
                  </Link>
                </div>
              </GradientBorderCard>
            </TiltCard>
          </StaggerItem>

          <StaggerItem>
            <TiltCard className="h-full">
              <GradientBorderCard className="h-full">
                <div className="p-6 text-center">
                  <div className="w-14 h-14 rounded-2xl bg-gradient-to-br from-fuchsia-500 to-pink-500 flex items-center justify-center mx-auto mb-4">
                    <svg className="h-7 w-7 text-white" fill="currentColor" viewBox="0 0 24 24">
                      <path d="M18.244 2.25h3.308l-7.227 8.26 8.502 11.24H16.17l-5.214-6.817L4.99 21.75H1.68l7.73-8.835L1.254 2.25H8.08l4.713 6.231zm-1.161 17.52h1.833L7.084 4.126H5.117z"/>
                    </svg>
                  </div>
                  <h3 className="text-lg font-semibold text-white mb-2">Twitter/X</h3>
                  <p className="text-zinc-400 text-sm mb-4">Follow us for updates</p>
                  <Link
                    href="https://twitter.com/D23AI"
                    target="_blank"
                    className="text-violet-400 hover:text-violet-300 text-sm font-medium"
                  >
                    @D23AI
                  </Link>
                </div>
              </GradientBorderCard>
            </TiltCard>
          </StaggerItem>
        </StaggerContainer>
      </div>
    </section>
  )
}

// ============== CTA SECTION ==============
function CTASection() {
  const t = useTranslations()

  return (
    <section className="py-20 px-6">
      <div className="max-w-4xl mx-auto">
        <TiltCard>
          <div className="relative rounded-3xl overflow-hidden">
            <motion.div
              animate={{ backgroundPosition: ["0% 50%", "100% 50%", "0% 50%"] }}
              transition={{ duration: 10, repeat: Infinity, ease: "linear" }}
              className="absolute inset-0 bg-gradient-to-r from-violet-600 via-fuchsia-600 to-pink-600 bg-[length:200%_auto]"
            />
            <div className="absolute inset-0 bg-[linear-gradient(rgba(255,255,255,0.1)_1px,transparent_1px),linear-gradient(90deg,rgba(255,255,255,0.1)_1px,transparent_1px)] bg-[size:40px_40px]" />

            <div className="relative z-10 p-12 md:p-20 text-center">
              <motion.h2
                initial={{ opacity: 0, y: 20 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true }}
                className="text-4xl md:text-5xl font-bold text-white mb-6"
              >
                {t.cta.title}
              </motion.h2>
              <motion.p
                initial={{ opacity: 0, y: 20 }}
                whileInView={{ opacity: 1, y: 0 }}
                transition={{ delay: 0.1 }}
                viewport={{ once: true }}
                className="text-white/80 text-lg mb-10 max-w-xl mx-auto"
              >
                {t.cta.subtitle}
              </motion.p>

              <motion.div
                initial={{ opacity: 0, y: 20 }}
                whileInView={{ opacity: 1, y: 0 }}
                transition={{ delay: 0.2 }}
                viewport={{ once: true }}
                className="flex flex-wrap justify-center gap-4"
              >
                <MagneticButton>
                  <Link
                    href="https://api.whatsapp.com/send/?phone=%2B919934438606&text=Hey+D23%21+What+can+you+do%3F&type=phone_number&app_absent=0"
                    target="_blank"
                    className="flex items-center gap-3 px-8 py-4 rounded-full bg-white text-violet-600 font-semibold shadow-2xl hover:bg-zinc-100 transition-colors"
                  >
                    <MessageCircle className="h-5 w-5" />
                    {t.cta.button1}
                  </Link>
                </MagneticButton>
                <MagneticButton>
                  <Link
                    href="/chat"
                    className="flex items-center gap-3 px-8 py-4 rounded-full border-2 border-white/30 text-white font-semibold hover:bg-white/10 transition-colors"
                  >
                    {t.cta.button2}
                  </Link>
                </MagneticButton>
              </motion.div>
            </div>
          </div>
        </TiltCard>
      </div>
    </section>
  )
}

// ============== FOOTER ==============
function Footer() {
  const t = useTranslations()

  return (
    <footer className="py-12 px-6 border-t border-white/10">
      <div className="max-w-6xl mx-auto">
        <div className="relative rounded-2xl border border-white/10 bg-white/[0.02] backdrop-blur-xl p-8 overflow-hidden">
          <div className="absolute top-0 left-1/4 w-64 h-64 bg-violet-500/10 rounded-full blur-3xl" />
          <div className="absolute bottom-0 right-1/4 w-64 h-64 bg-fuchsia-500/10 rounded-full blur-3xl" />

          <div className="relative z-10 flex flex-col md:flex-row items-center justify-between gap-6">
            <div className="flex items-center gap-3">
              <Image src="/puch/logo.png" alt="D23 AI" width={40} height={40} />
              <div>
                <p className="text-lg font-bold text-white">D23<GradientText>.AI</GradientText></p>
                <p className="text-sm text-zinc-500">{t.footer.tagline}</p>
              </div>
            </div>

            <MagneticButton>
              <Link
                href="https://api.whatsapp.com/send/?phone=%2B919934438606&text=Hey+D23%21+What+can+you+do%3F&type=phone_number&app_absent=0"
                target="_blank"
                className="flex items-center gap-2 px-6 py-3 rounded-full bg-gradient-to-r from-violet-600 to-fuchsia-600 text-white font-medium shadow-lg shadow-violet-500/25"
              >
                {t.footer.button}
              </Link>
            </MagneticButton>
          </div>

          <div className="relative z-10 flex flex-col md:flex-row items-center justify-between gap-4 mt-8 pt-6 border-t border-white/10">
            <div className="flex items-center gap-4">
              {[
                { icon: "X", href: "#" },
                { icon: "IG", href: "#" },
                { icon: "GH", href: "#" },
              ].map((social) => (
                <Link
                  key={social.icon}
                  href={social.href}
                  className="w-10 h-10 rounded-full bg-white/5 flex items-center justify-center text-zinc-400 hover:text-white hover:bg-white/10 transition-colors text-xs font-bold"
                >
                  {social.icon}
                </Link>
              ))}
            </div>
            <p className="text-sm text-zinc-500">{t.footer.copyright}</p>
          </div>
        </div>
      </div>
    </footer>
  )
}

// ============== PAGE CONTENT ==============
function PageContent() {
  const hydrated = useHydrated()

  // Show a simple loading state until hydrated to prevent flash of un-animated content
  if (!hydrated) {
    return (
      <div className="min-h-screen bg-black text-white flex items-center justify-center">
        <div className="animate-pulse">
          <Image src="/puch/logo.png" alt="D23" width={80} height={80} />
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-black text-white overflow-x-hidden">
      <Header />
      <main>
        <HeroSection />
        <LanguageMarquee />
        <VideoSection />
        <FeaturesSection />
        <ShowcaseSection />
        <AboutSection />
        <FoundersSection />
        <FAQSection />
        <ContactSection />
        <CTASection />
      </main>
      <Footer />
    </div>
  )
}

// ============== MAIN PAGE ==============
export default function HomePage() {
  return (
    <LanguageProvider>
      <PageContent />
    </LanguageProvider>
  )
}
