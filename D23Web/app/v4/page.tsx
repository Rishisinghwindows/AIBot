"use client"

import { useRef, useState, useEffect } from "react"
import Image from "next/image"
import Link from "next/link"
import { motion, useScroll, useTransform, useSpring, useInView, AnimatePresence } from "framer-motion"
import { ArrowRight, ArrowUpRight, Check, ChevronRight, Globe, MessageCircle, Sparkles, Zap } from "lucide-react"
import { cn } from "@/lib/utils"

// ============== MARQUEE COMPONENT ==============
function Marquee({ children, speed = 30, direction = "left" }: { children: React.ReactNode; speed?: number; direction?: "left" | "right" }) {
  return (
    <div className="overflow-hidden whitespace-nowrap">
      <motion.div
        animate={{ x: direction === "left" ? "-50%" : "0%" }}
        initial={{ x: direction === "left" ? "0%" : "-50%" }}
        transition={{ duration: speed, repeat: Infinity, ease: "linear" }}
        className="inline-flex"
      >
        {children}
        {children}
      </motion.div>
    </div>
  )
}

// ============== SPOTLIGHT CARD ==============
function SpotlightCard({ children, className = "" }: { children: React.ReactNode; className?: string }) {
  const divRef = useRef<HTMLDivElement>(null)
  const [position, setPosition] = useState({ x: 0, y: 0 })
  const [opacity, setOpacity] = useState(0)

  const handleMouseMove = (e: React.MouseEvent<HTMLDivElement>) => {
    if (!divRef.current) return
    const rect = divRef.current.getBoundingClientRect()
    setPosition({ x: e.clientX - rect.left, y: e.clientY - rect.top })
  }

  return (
    <div
      ref={divRef}
      onMouseMove={handleMouseMove}
      onMouseEnter={() => setOpacity(1)}
      onMouseLeave={() => setOpacity(0)}
      className={cn("relative overflow-hidden rounded-2xl border border-white/10 bg-white/[0.02]", className)}
    >
      <div
        className="pointer-events-none absolute -inset-px opacity-0 transition-opacity duration-500"
        style={{
          opacity,
          background: `radial-gradient(400px circle at ${position.x}px ${position.y}px, rgba(34,197,94,0.15), transparent 40%)`,
        }}
      />
      {children}
    </div>
  )
}

// ============== ANIMATED COUNTER ==============
function AnimatedCounter({ value, suffix = "" }: { value: number; suffix?: string }) {
  const ref = useRef(null)
  const isInView = useInView(ref, { once: true })
  const [count, setCount] = useState(0)

  useEffect(() => {
    if (isInView) {
      const duration = 2000
      const steps = 60
      const increment = value / steps
      let current = 0
      const timer = setInterval(() => {
        current += increment
        if (current >= value) {
          setCount(value)
          clearInterval(timer)
        } else {
          setCount(Math.floor(current))
        }
      }, duration / steps)
      return () => clearInterval(timer)
    }
  }, [isInView, value])

  return <span ref={ref}>{count}{suffix}</span>
}

// ============== FADE IN COMPONENT ==============
function FadeIn({ children, delay = 0, className = "" }: { children: React.ReactNode; delay?: number; className?: string }) {
  const ref = useRef(null)
  const isInView = useInView(ref, { once: true, margin: "-100px" })

  return (
    <motion.div
      ref={ref}
      initial={{ opacity: 0, y: 30 }}
      animate={isInView ? { opacity: 1, y: 0 } : {}}
      transition={{ duration: 0.8, delay, ease: [0.25, 0.4, 0.25, 1] }}
      className={className}
    >
      {children}
    </motion.div>
  )
}

// ============== HEADER ==============
function Header() {
  const { scrollY } = useScroll()
  const headerBg = useTransform(scrollY, [0, 100], ["rgba(0,0,0,0)", "rgba(0,0,0,0.8)"])
  const headerBlur = useTransform(scrollY, [0, 100], ["blur(0px)", "blur(12px)"])

  return (
    <motion.header
      style={{ backgroundColor: headerBg, backdropFilter: headerBlur }}
      className="fixed top-0 left-0 right-0 z-50 border-b border-transparent"
    >
      <div className="max-w-7xl mx-auto px-6">
        <div className="flex items-center justify-between h-16">
          <Link href="/v4" className="flex items-center gap-2">
            <Image src="/puch/logo.png" alt="D23" width={32} height={32} />
            <span className="font-semibold text-white">D23.AI</span>
          </Link>

          <nav className="hidden md:flex items-center gap-8">
            {["Features", "Pricing", "About"].map((item) => (
              <Link
                key={item}
                href={`/${item.toLowerCase()}`}
                className="text-sm text-zinc-400 hover:text-white transition-colors"
              >
                {item}
              </Link>
            ))}
          </nav>

          <div className="flex items-center gap-3">
            <Link href="/chat" className="text-sm text-zinc-400 hover:text-white transition-colors">
              Web Chat
            </Link>
            <Link
              href="https://api.whatsapp.com/send/?phone=%2B919934438606&text=Hey+D23%21+What+can+you+do%3F&type=phone_number&app_absent=0"
              target="_blank"
              className="flex items-center gap-2 px-4 py-2 rounded-full bg-white text-black text-sm font-medium hover:bg-zinc-200 transition-colors"
            >
              Get Started
              <ArrowRight className="h-4 w-4" />
            </Link>
          </div>
        </div>
      </div>
    </motion.header>
  )
}

// ============== HERO ==============
function HeroSection() {
  const ref = useRef(null)
  const { scrollYProgress } = useScroll({ target: ref, offset: ["start start", "end start"] })
  const y = useTransform(scrollYProgress, [0, 1], [0, 300])
  const scale = useTransform(scrollYProgress, [0, 1], [1, 0.8])
  const opacity = useTransform(scrollYProgress, [0, 0.5], [1, 0])

  return (
    <section ref={ref} className="relative min-h-[100vh] flex items-center justify-center overflow-hidden">
      {/* Gradient Mesh Background */}
      <div className="absolute inset-0">
        <div className="absolute inset-0 bg-black" />
        <div className="absolute top-0 left-1/4 w-[600px] h-[600px] bg-green-500/30 rounded-full blur-[128px]" />
        <div className="absolute bottom-0 right-1/4 w-[500px] h-[500px] bg-emerald-500/20 rounded-full blur-[128px]" />
        <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[800px] h-[800px] bg-teal-500/10 rounded-full blur-[128px]" />
      </div>

      <motion.div style={{ y, scale, opacity }} className="relative z-10 max-w-5xl mx-auto px-6 text-center pt-32">
        {/* Announcement Badge */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6 }}
          className="inline-flex items-center gap-2 px-4 py-1.5 rounded-full border border-zinc-800 bg-zinc-900/50 backdrop-blur-sm mb-8"
        >
          <span className="flex h-2 w-2 rounded-full bg-green-500 animate-pulse" />
          <span className="text-sm text-zinc-300">Now supporting 11+ Indian languages</span>
          <ChevronRight className="h-4 w-4 text-zinc-500" />
        </motion.div>

        {/* Main Headline */}
        <motion.h1
          initial={{ opacity: 0, y: 30 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.8, delay: 0.1 }}
          className="text-5xl sm:text-6xl md:text-7xl lg:text-8xl font-bold tracking-tight text-white mb-6"
        >
          AI that speaks
          <br />
          <span className="bg-gradient-to-r from-green-400 via-emerald-400 to-teal-400 bg-clip-text text-transparent">
            your language
          </span>
        </motion.h1>

        {/* Subtitle */}
        <motion.p
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.8, delay: 0.2 }}
          className="text-lg md:text-xl text-zinc-400 max-w-2xl mx-auto mb-10"
        >
          D23 AI is your intelligent WhatsApp assistant. Get instant answers in Hindi, Tamil, Telugu, Bengali & more.
        </motion.p>

        {/* CTA Buttons */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.8, delay: 0.3 }}
          className="flex flex-col sm:flex-row items-center justify-center gap-4"
        >
          <Link
            href="https://api.whatsapp.com/send/?phone=%2B919934438606&text=Hey+D23%21+What+can+you+do%3F&type=phone_number&app_absent=0"
            target="_blank"
            className="group flex items-center gap-3 px-8 py-4 rounded-full bg-white text-black font-medium hover:bg-zinc-100 transition-all"
          >
            Start Free on WhatsApp
            <ArrowRight className="h-5 w-5 group-hover:translate-x-1 transition-transform" />
          </Link>
          <Link
            href="/chat"
            className="flex items-center gap-3 px-8 py-4 rounded-full border border-zinc-800 text-white font-medium hover:bg-zinc-900 transition-colors"
          >
            <Globe className="h-5 w-5" />
            Try Web Version
          </Link>
        </motion.div>

        {/* Trusted By */}
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ duration: 1, delay: 0.5 }}
          className="mt-20"
        >
          <p className="text-sm text-zinc-500 mb-6">Trusted by thousands across India</p>
          <div className="flex items-center justify-center gap-12">
            {[
              { value: 5000, suffix: "+", label: "Users" },
              { value: 11, suffix: "+", label: "Languages" },
              { value: 24, suffix: "/7", label: "Available" },
            ].map((stat) => (
              <div key={stat.label} className="text-center">
                <div className="text-3xl font-bold text-white">
                  <AnimatedCounter value={stat.value} suffix={stat.suffix} />
                </div>
                <div className="text-sm text-zinc-500">{stat.label}</div>
              </div>
            ))}
          </div>
        </motion.div>
      </motion.div>

      {/* Scroll Indicator */}
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ delay: 1 }}
        className="absolute bottom-10 left-1/2 -translate-x-1/2"
      >
        <motion.div
          animate={{ y: [0, 8, 0] }}
          transition={{ duration: 2, repeat: Infinity }}
          className="w-6 h-10 rounded-full border-2 border-zinc-700 flex justify-center pt-2"
        >
          <motion.div className="w-1 h-2 rounded-full bg-white" />
        </motion.div>
      </motion.div>
    </section>
  )
}

// ============== MARQUEE SECTION ==============
function MarqueeSection() {
  const languages = ["हिंदी", "தமிழ்", "తెలుగు", "বাংলা", "मराठी", "ગુજરાતી", "ಕನ್ನಡ", "മലയാളം", "ਪੰਜਾਬੀ", "ଓଡ଼ିଆ", "English"]

  return (
    <section className="py-20 border-y border-zinc-800 bg-black overflow-hidden">
      <Marquee speed={40}>
        <div className="flex items-center gap-12 px-6">
          {languages.map((lang, i) => (
            <span key={`${lang}-${i}`} className="text-4xl md:text-6xl font-bold text-zinc-800 hover:text-white transition-colors cursor-default whitespace-nowrap">
              {lang}
            </span>
          ))}
        </div>
      </Marquee>
    </section>
  )
}

// ============== FEATURES SECTION ==============
const features = [
  {
    icon: <MessageCircle className="h-6 w-6" />,
    title: "WhatsApp Native",
    description: "Works inside WhatsApp. No app download, no signup. Just start chatting.",
  },
  {
    icon: <Globe className="h-6 w-6" />,
    title: "11+ Languages",
    description: "Speak naturally in Hindi, Tamil, Telugu, Bengali, Marathi & more regional languages.",
  },
  {
    icon: <Zap className="h-6 w-6" />,
    title: "Instant Responses",
    description: "Get answers in under 2 seconds. Always available, 24/7.",
  },
  {
    icon: <Sparkles className="h-6 w-6" />,
    title: "AI Image Generation",
    description: "Create stunning images from text prompts. Just describe what you want.",
  },
]

function FeaturesSection() {
  return (
    <section className="py-32 px-6">
      <div className="max-w-6xl mx-auto">
        <FadeIn className="text-center mb-20">
          <p className="text-green-400 text-sm font-medium tracking-wider uppercase mb-4">Features</p>
          <h2 className="text-4xl md:text-5xl lg:text-6xl font-bold text-white">
            Everything you need
          </h2>
        </FadeIn>

        <div className="grid md:grid-cols-2 gap-6">
          {features.map((feature, i) => (
            <FadeIn key={feature.title} delay={i * 0.1}>
              <SpotlightCard className="h-full">
                <div className="p-8">
                  <div className="w-12 h-12 rounded-xl bg-gradient-to-br from-green-500/20 to-emerald-500/20 flex items-center justify-center text-green-400 mb-6">
                    {feature.icon}
                  </div>
                  <h3 className="text-xl font-semibold text-white mb-3">{feature.title}</h3>
                  <p className="text-zinc-400 leading-relaxed">{feature.description}</p>
                </div>
              </SpotlightCard>
            </FadeIn>
          ))}
        </div>
      </div>
    </section>
  )
}

// ============== HORIZONTAL SCROLL SHOWCASE ==============
function HorizontalShowcase() {
  const containerRef = useRef<HTMLDivElement>(null)
  const { scrollYProgress } = useScroll({ target: containerRef, offset: ["start end", "end start"] })
  const x = useTransform(scrollYProgress, [0, 1], ["0%", "-30%"])

  const showcaseItems = [
    { title: "Image Generation", image: "/puch/features/siddarth-shinchanified.png", tag: "AI Art" },
    { title: "Voice Assistant", image: "/puch/features/salman-3.webp", tag: "Voice" },
    { title: "Fact Checker", image: "/puch/features/salman-1.webp", tag: "Verify" },
    { title: "Custom Stickers", image: "/puch/features/dragon.png", tag: "Creative" },
    { title: "Games", image: "/puch/assets/wordle/wordlewin.jpeg", tag: "Fun" },
  ]

  return (
    <section ref={containerRef} className="py-32 overflow-hidden">
      <div className="max-w-7xl mx-auto px-6 mb-16">
        <FadeIn>
          <p className="text-green-400 text-sm font-medium tracking-wider uppercase mb-4">Showcase</p>
          <h2 className="text-4xl md:text-5xl font-bold text-white">See what&apos;s possible</h2>
        </FadeIn>
      </div>

      <motion.div style={{ x }} className="flex gap-6 pl-6">
        {showcaseItems.map((item, i) => (
          <motion.div
            key={item.title}
            initial={{ opacity: 0, scale: 0.9 }}
            whileInView={{ opacity: 1, scale: 1 }}
            transition={{ delay: i * 0.1 }}
            viewport={{ once: true }}
            className="flex-shrink-0 w-80 md:w-96"
          >
            <SpotlightCard className="group cursor-pointer">
              <div className="aspect-[4/5] relative overflow-hidden rounded-t-2xl">
                <Image
                  src={item.image}
                  alt={item.title}
                  fill
                  className="object-cover transition-transform duration-700 group-hover:scale-110"
                />
                <div className="absolute inset-0 bg-gradient-to-t from-black via-black/20 to-transparent" />
                <div className="absolute bottom-4 left-4 right-4">
                  <span className="inline-block px-3 py-1 rounded-full bg-white/10 backdrop-blur-sm text-xs text-white mb-2">
                    {item.tag}
                  </span>
                  <h3 className="text-xl font-semibold text-white">{item.title}</h3>
                </div>
              </div>
            </SpotlightCard>
          </motion.div>
        ))}
      </motion.div>
    </section>
  )
}

// ============== HOW IT WORKS ==============
function HowItWorks() {
  const steps = [
    { step: "01", title: "Save the number", description: "Add D23 AI to your WhatsApp contacts" },
    { step: "02", title: "Send a message", description: "Start chatting in any Indian language" },
    { step: "03", title: "Get instant help", description: "Receive AI-powered answers in seconds" },
  ]

  return (
    <section className="py-32 px-6 border-t border-zinc-800">
      <div className="max-w-6xl mx-auto">
        <FadeIn className="text-center mb-20">
          <p className="text-green-400 text-sm font-medium tracking-wider uppercase mb-4">How it works</p>
          <h2 className="text-4xl md:text-5xl font-bold text-white">Three simple steps</h2>
        </FadeIn>

        <div className="grid md:grid-cols-3 gap-8">
          {steps.map((step, i) => (
            <FadeIn key={step.step} delay={i * 0.15}>
              <div className="relative">
                {i < steps.length - 1 && (
                  <div className="hidden md:block absolute top-8 left-full w-full h-px bg-gradient-to-r from-zinc-800 to-transparent -translate-x-8" />
                )}
                <div className="text-6xl font-bold text-zinc-800 mb-4">{step.step}</div>
                <h3 className="text-xl font-semibold text-white mb-2">{step.title}</h3>
                <p className="text-zinc-400">{step.description}</p>
              </div>
            </FadeIn>
          ))}
        </div>
      </div>
    </section>
  )
}

// ============== TESTIMONIALS ==============
function TestimonialsSection() {
  const testimonials = [
    { text: "Finally an AI that understands Hindi perfectly! Game changer for my daily queries.", author: "Rahul S.", location: "Delhi" },
    { text: "The fact-checking feature saved me from sharing fake news. Highly recommended!", author: "Priya M.", location: "Mumbai" },
    { text: "Love the sticker creation feature. My WhatsApp groups are so much fun now!", author: "Arjun K.", location: "Bangalore" },
  ]

  return (
    <section className="py-32 px-6 bg-zinc-950">
      <div className="max-w-6xl mx-auto">
        <FadeIn className="text-center mb-16">
          <p className="text-green-400 text-sm font-medium tracking-wider uppercase mb-4">Testimonials</p>
          <h2 className="text-4xl md:text-5xl font-bold text-white">Loved by users</h2>
        </FadeIn>

        <div className="grid md:grid-cols-3 gap-6">
          {testimonials.map((testimonial, i) => (
            <FadeIn key={i} delay={i * 0.1}>
              <SpotlightCard className="h-full">
                <div className="p-8">
                  <div className="flex gap-1 mb-6">
                    {[...Array(5)].map((_, j) => (
                      <svg key={j} className="w-5 h-5 text-yellow-500" fill="currentColor" viewBox="0 0 20 20">
                        <path d="M9.049 2.927c.3-.921 1.603-.921 1.902 0l1.07 3.292a1 1 0 00.95.69h3.462c.969 0 1.371 1.24.588 1.81l-2.8 2.034a1 1 0 00-.364 1.118l1.07 3.292c.3.921-.755 1.688-1.54 1.118l-2.8-2.034a1 1 0 00-1.175 0l-2.8 2.034c-.784.57-1.838-.197-1.539-1.118l1.07-3.292a1 1 0 00-.364-1.118L2.98 8.72c-.783-.57-.38-1.81.588-1.81h3.461a1 1 0 00.951-.69l1.07-3.292z" />
                      </svg>
                    ))}
                  </div>
                  <p className="text-white mb-6">&quot;{testimonial.text}&quot;</p>
                  <div>
                    <p className="font-medium text-white">{testimonial.author}</p>
                    <p className="text-sm text-zinc-500">{testimonial.location}</p>
                  </div>
                </div>
              </SpotlightCard>
            </FadeIn>
          ))}
        </div>
      </div>
    </section>
  )
}

// ============== PRICING ==============
function PricingSection() {
  return (
    <section className="py-32 px-6 border-t border-zinc-800">
      <div className="max-w-4xl mx-auto text-center">
        <FadeIn>
          <p className="text-green-400 text-sm font-medium tracking-wider uppercase mb-4">Pricing</p>
          <h2 className="text-4xl md:text-5xl font-bold text-white mb-6">
            Free to start,<br />powerful for everyone
          </h2>
          <p className="text-xl text-zinc-400 mb-12">
            No credit card required. Just start chatting.
          </p>
        </FadeIn>

        <FadeIn delay={0.2}>
          <SpotlightCard className="max-w-md mx-auto">
            <div className="p-8">
              <div className="text-green-400 text-sm font-medium mb-2">FREE FOREVER</div>
              <div className="flex items-baseline gap-2 mb-6">
                <span className="text-5xl font-bold text-white">₹0</span>
                <span className="text-zinc-400">/month</span>
              </div>
              <ul className="space-y-4 mb-8 text-left">
                {["Unlimited messages", "11+ languages", "Image generation", "Voice assistant", "Fact checking", "Custom stickers", "Games & more"].map((item) => (
                  <li key={item} className="flex items-center gap-3 text-zinc-300">
                    <Check className="h-5 w-5 text-green-400 flex-shrink-0" />
                    {item}
                  </li>
                ))}
              </ul>
              <Link
                href="https://api.whatsapp.com/send/?phone=%2B919934438606&text=Hey+D23%21+What+can+you+do%3F&type=phone_number&app_absent=0"
                target="_blank"
                className="block w-full py-4 rounded-full bg-white text-black font-medium text-center hover:bg-zinc-200 transition-colors"
              >
                Get Started Free
              </Link>
            </div>
          </SpotlightCard>
        </FadeIn>
      </div>
    </section>
  )
}

// ============== CTA ==============
function CTASection() {
  return (
    <section className="py-32 px-6">
      <FadeIn>
        <div className="max-w-4xl mx-auto text-center">
          <h2 className="text-4xl md:text-6xl font-bold text-white mb-6">
            Ready to get started?
          </h2>
          <p className="text-xl text-zinc-400 mb-10">
            Join thousands of Indians using D23 AI every day.
          </p>
          <div className="flex flex-col sm:flex-row items-center justify-center gap-4">
            <Link
              href="https://api.whatsapp.com/send/?phone=%2B919934438606&text=Hey+D23%21+What+can+you+do%3F&type=phone_number&app_absent=0"
              target="_blank"
              className="group flex items-center gap-3 px-8 py-4 rounded-full bg-gradient-to-r from-green-500 to-emerald-600 text-white font-medium hover:opacity-90 transition-opacity"
            >
              Start on WhatsApp
              <ArrowUpRight className="h-5 w-5 group-hover:translate-x-0.5 group-hover:-translate-y-0.5 transition-transform" />
            </Link>
            <Link
              href="/chat"
              className="flex items-center gap-3 px-8 py-4 rounded-full border border-zinc-700 text-white font-medium hover:bg-zinc-900 transition-colors"
            >
              Try Web Chat
            </Link>
          </div>
        </div>
      </FadeIn>
    </section>
  )
}

// ============== FOOTER ==============
function Footer() {
  return (
    <footer className="py-12 px-6 border-t border-zinc-800">
      <div className="max-w-6xl mx-auto">
        <div className="flex flex-col md:flex-row items-center justify-between gap-6">
          <div className="flex items-center gap-2">
            <Image src="/puch/logo.png" alt="D23" width={24} height={24} />
            <span className="text-white font-medium">D23.AI</span>
          </div>
          <p className="text-zinc-500 text-sm">© 2025 D23 AI. Built for every Indian language.</p>
          <div className="flex items-center gap-6">
            <Link href="#" className="text-zinc-500 hover:text-white text-sm transition-colors">Twitter</Link>
            <Link href="#" className="text-zinc-500 hover:text-white text-sm transition-colors">Instagram</Link>
            <Link href="#" className="text-zinc-500 hover:text-white text-sm transition-colors">GitHub</Link>
          </div>
        </div>
      </div>
    </footer>
  )
}

// ============== MAIN ==============
export default function V4Page() {
  return (
    <div className="min-h-screen bg-black text-white overflow-x-hidden">
      <Header />
      <main>
        <HeroSection />
        <MarqueeSection />
        <FeaturesSection />
        <HorizontalShowcase />
        <HowItWorks />
        <TestimonialsSection />
        <PricingSection />
        <CTASection />
      </main>
      <Footer />
    </div>
  )
}
