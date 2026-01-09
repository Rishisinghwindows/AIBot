"use client"

import { useState, useRef, useEffect } from "react"
import Image from "next/image"
import Link from "next/link"
import { motion, useScroll, useTransform, useInView, useMotionValue, useSpring, AnimatePresence } from "framer-motion"

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

const founders = [
  { name: "Naseer", role: "Co-Founder & CEO", twitter: "#", linkedin: "#" },
  { name: "Pawan", role: "Co-Founder & CPO", twitter: "#", linkedin: "https://www.linkedin.com/in/pawan-k-singh-119b8a20/" },
  { name: "Rishi", role: "Co-Founder & CTO", twitter: "https://x.com/RishiSi92580328", linkedin: "https://www.linkedin.com/in/rishi-kumar-5878742a/" }
]

// ============== LANGUAGE MARQUEE ==============
function LanguageMarquee() {
  return (
    <div className="relative w-full overflow-hidden py-8 bg-black/50 backdrop-blur-sm border-y border-white/5">
      <div className="absolute left-0 top-0 bottom-0 w-32 bg-gradient-to-r from-black to-transparent z-10" />
      <div className="absolute right-0 top-0 bottom-0 w-32 bg-gradient-to-l from-black to-transparent z-10" />
      <div className="flex animate-marquee whitespace-nowrap">
        {[...marqueeLanguages, ...marqueeLanguages, ...marqueeLanguages].map((lang, i) => (
          <span key={`${lang.code}-${i}`} className="mx-8 md:mx-12 text-2xl md:text-4xl font-medium text-zinc-400 hover:text-white transition-colors cursor-default select-none">
            {lang.name}
          </span>
        ))}
      </div>
      <div className="flex animate-marquee-reverse whitespace-nowrap mt-4">
        {[...marqueeLanguages, ...marqueeLanguages, ...marqueeLanguages].reverse().map((lang, i) => (
          <span key={`reverse-${lang.code}-${i}`} className="mx-8 md:mx-12 text-xl md:text-3xl font-medium text-zinc-500/60 hover:text-zinc-300 transition-colors cursor-default select-none">
            {lang.english}
          </span>
        ))}
      </div>
    </div>
  )
}

// ============== MAGNETIC BUTTON (CSS-only) ==============
function MagneticButton({ children, className = "" }: { children: React.ReactNode; className?: string }) {
  return (
    <div className={cn("relative transition-transform duration-200 hover:scale-105", className)}>
      {children}
    </div>
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
    <motion.div ref={ref} onMouseMove={handleMouse} onMouseLeave={reset} style={{ rotateX, rotateY, transformStyle: "preserve-3d", position: "relative" }} className={className}>
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
      <motion.span initial={{ y: "100%" }} animate={isInView ? { y: 0 } : {}} transition={{ duration: 0.8, ease: [0.22, 1, 0.36, 1] }} className="inline-block">
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
    <motion.div ref={ref} initial="hidden" animate={isInView ? "visible" : "hidden"} variants={{ visible: { transition: { staggerChildren: 0.1 } } }} className={className}>
      {children}
    </motion.div>
  )
}

function StaggerItem({ children, className = "" }: { children: React.ReactNode; className?: string }) {
  return (
    <motion.div variants={{ hidden: { opacity: 0, y: 30 }, visible: { opacity: 1, y: 0, transition: { duration: 0.6, ease: [0.22, 1, 0.36, 1] } } }} className={className}>
      {children}
    </motion.div>
  )
}

// ============== GRADIENT TEXT ==============
function GradientText({ children, className = "" }: { children: React.ReactNode; className?: string }) {
  return (
    <span className={cn("bg-gradient-to-r from-violet-400 via-fuchsia-400 to-pink-400 bg-clip-text text-transparent", className)}>
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
      <motion.span key={index} initial={{ opacity: 0, y: 30, rotateX: -90 }} animate={{ opacity: 1, y: 0, rotateX: 0 }} exit={{ opacity: 0, y: -30, rotateX: 90 }} transition={{ duration: 0.5, ease: [0.22, 1, 0.36, 1] }} className="inline-block">
        <GradientText>{words[index]}</GradientText>
      </motion.span>
    </AnimatePresence>
  )
}

// ============== GRADIENT BORDER CARD ==============
function GradientBorderCard({ children, className = "" }: { children: React.ReactNode; className?: string }) {
  return (
    <div className={cn("relative p-[1px] rounded-2xl overflow-hidden group", className)}>
      <motion.div animate={{ rotate: 360 }} transition={{ duration: 8, repeat: Infinity, ease: "linear" }} className="absolute inset-0 bg-gradient-to-r from-violet-500 via-fuchsia-500 to-pink-500 opacity-50 group-hover:opacity-100 transition-opacity" style={{ filter: "blur(8px)" }} />
      <div className="absolute inset-0 bg-gradient-to-r from-violet-500 via-fuchsia-500 to-pink-500 rounded-2xl" />
      <div className="relative bg-black rounded-2xl">{children}</div>
    </div>
  )
}

// ============== ANIMATED COUNTER ==============
function AnimatedCounter({ value, suffix = "" }: { value: number; suffix?: string }) {
  const [count, setCount] = useState(0)
  const ref = useRef(null)
  const isInView = useInView(ref, { once: true })

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

// ============== PHONE CHAT MESSAGES DATA ==============
const phoneChatMessages = [
  // Hindi - Weather
  { type: "user", lang: "hi", text: "मुझे आज का मौसम बताओ 🌤️" },
  { type: "bot", lang: "hi", content: (
    <div>
      <p className="text-xs text-zinc-400 mb-1">🇮🇳 दिल्ली</p>
      <p>🌡️ <span className="font-semibold">32°C</span> • साफ आसमान</p>
      <p className="text-zinc-400 text-xs mt-1">💧 नमी: 45% | 💨 हवा: 12 km/h</p>
    </div>
  )},
  // Tamil - Horoscope
  { type: "user", lang: "ta", text: "இன்றைய ராசிபலன் ♌" },
  { type: "bot", lang: "ta", content: (
    <div>
      <p className="text-xs text-violet-400 mb-1">♌ சிம்மம் ராசி</p>
      <p className="text-xs">இன்று காலை 9-11 மணி சிறந்த நேரம். புதிய வாய்ப்புகள் வரும். ⭐⭐⭐⭐</p>
    </div>
  )},
  // English - Image
  { type: "user", lang: "en", text: "Generate a sunset image 🎨" },
  { type: "bot", lang: "en", content: (
    <div>
      <div className="w-full h-20 rounded-lg mb-2 overflow-hidden">
        <img src="/puch/features/salman-1.webp" alt="AI Generated" className="w-full h-full object-cover" />
      </div>
      <p className="text-xs text-zinc-400">Here's your AI-generated image! 🌅</p>
    </div>
  )},
  // Telugu - Sticker
  { type: "user", lang: "te", text: "స్టికర్ చేయి 🎭" },
  { type: "bot", lang: "te", content: (
    <div>
      <div className="w-16 h-16 rounded-xl mb-1 overflow-hidden">
        <img src="/puch/features/dragon-1.webp" alt="Sticker" className="w-full h-full object-cover" />
      </div>
      <p className="text-xs text-zinc-400">మీ స్టికర్ సిద్ధంగా ఉంది! 🎉</p>
    </div>
  )},
  // Bengali - News
  { type: "user", lang: "bn", text: "আজকের খবর 📰" },
  { type: "bot", lang: "bn", content: (
    <div>
      <p className="text-xs text-cyan-400 mb-1">📰 শীর্ষ সংবাদ</p>
      <p className="text-xs">ভারত বনাম অস্ট্রেলিয়া ম্যাচে ভারত ৭ উইকেটে জয়ী! 🏏🇮🇳</p>
    </div>
  )},
  // Kannada - Game
  { type: "user", lang: "kn", text: "ವರ್ಡ್ಲ್ ಆಟ ಆಡೋಣ 🎮" },
  { type: "bot", lang: "kn", content: (
    <div>
      <div className="flex gap-1 mb-1">
        <span className="w-6 h-6 bg-green-500 rounded text-white text-xs flex items-center justify-center font-bold">ಕ</span>
        <span className="w-6 h-6 bg-yellow-500 rounded text-white text-xs flex items-center justify-center font-bold">ನ</span>
        <span className="w-6 h-6 bg-zinc-600 rounded text-white text-xs flex items-center justify-center font-bold">್ನ</span>
        <span className="w-6 h-6 bg-green-500 rounded text-white text-xs flex items-center justify-center font-bold">ಡ</span>
      </div>
      <p className="text-xs text-zinc-400">ಅದ್ಭುತ! 3/6 ಪ್ರಯತ್ನಗಳಲ್ಲಿ! 🎯</p>
    </div>
  )},
  // Gujarati - Panchang
  { type: "user", lang: "gu", text: "આજનું પંચાંગ 🕉️" },
  { type: "bot", lang: "gu", content: (
    <div>
      <p className="text-xs text-amber-400 mb-1">🕉️ પંચાંગ</p>
      <p className="text-xs">તિથિ: શુક્લ એકાદશી</p>
      <p className="text-xs text-zinc-400">નક્ષત્ર: રોહિણી | યોગ: શુભ</p>
    </div>
  )},
  // Malayalam - Recipe
  { type: "user", lang: "ml", text: "ബിരിയാണി റെസിപ്പി 🍚" },
  { type: "bot", lang: "ml", content: (
    <div>
      <p className="text-xs text-orange-400 mb-1">🍚 മലബാർ ബിരിയാണി</p>
      <p className="text-xs">ചേരുവകൾ: ബസ്മതി അരി, ചിക്കൻ, മസാല...</p>
      <p className="text-xs text-zinc-400 mt-1">⏱️ സമയം: 45 മിനിറ്റ്</p>
    </div>
  )},
  // Marathi - Joke
  { type: "user", lang: "mr", text: "एक विनोद सांग 😄" },
  { type: "bot", lang: "mr", content: (
    <div>
      <p className="text-xs">शिक्षक: तुझा होमवर्क कुठे आहे?</p>
      <p className="text-xs">विद्यार्थी: कुत्र्याने खाल्ला सर! 🐕</p>
      <p className="text-xs mt-1">😂😂😂</p>
    </div>
  )},
  // Punjabi - Voice
  { type: "user", lang: "pa", text: "🎤 ਵੌਇਸ ਮੈਸੇਜ 0:05", isVoice: true },
  { type: "bot", lang: "pa", content: (
    <div>
      <p className="text-xs text-green-400 mb-1">🎤 ਵੌਇਸ ਟ੍ਰਾਂਸਕ੍ਰਿਪਟ</p>
      <p className="text-xs">"ਸਤ ਸ੍ਰੀ ਅਕਾਲ ਜੀ! ਮੈਂ ਠੀਕ ਹਾਂ"</p>
    </div>
  )},
  // Odia - Weather
  { type: "user", lang: "or", text: "ଆଜି ପାଣିପାଗ କେମିତି? ☀️" },
  { type: "bot", lang: "or", content: (
    <div>
      <p className="text-xs text-zinc-400 mb-1">🇮🇳 ଭୁବନେଶ୍ୱର</p>
      <p>🌡️ <span className="font-semibold">28°C</span> • ଆଂଶିକ ମେଘୁଆ</p>
      <p className="text-zinc-400 text-xs mt-1">💧 ଆର୍ଦ୍ରତା: 65%</p>
    </div>
  )},
  // Hindi - Kundli
  { type: "user", lang: "hi", text: "मेरी कुंडली बनाओ 🌟" },
  { type: "bot", lang: "hi", content: (
    <div>
      <p className="text-xs text-purple-400 mb-1">🌟 जन्म कुंडली</p>
      <div className="grid grid-cols-3 gap-0.5 mb-1">
        <span className="w-5 h-5 bg-violet-600/50 rounded text-[8px] flex items-center justify-center">शु</span>
        <span className="w-5 h-5 bg-zinc-700 rounded text-[8px] flex items-center justify-center">रा</span>
        <span className="w-5 h-5 bg-orange-600/50 rounded text-[8px] flex items-center justify-center">सू</span>
        <span className="w-5 h-5 bg-zinc-700 rounded text-[8px] flex items-center justify-center">के</span>
        <span className="w-5 h-5 bg-red-600/50 rounded text-[8px] flex items-center justify-center">मं</span>
        <span className="w-5 h-5 bg-zinc-700 rounded text-[8px] flex items-center justify-center">बु</span>
      </div>
      <p className="text-xs text-zinc-400">लग्न: वृषभ | चंद्र: कर्क</p>
    </div>
  )},
  // Tamil - Train Status
  { type: "user", lang: "ta", text: "PNR நிலை 2847593021 🚂" },
  { type: "bot", lang: "ta", content: (
    <div>
      <p className="text-xs text-blue-400 mb-1">🚂 ரயில் நிலை</p>
      <p className="text-xs">சென்னை → மும்பை எக்ஸ்பிரஸ்</p>
      <p className="text-xs text-green-400 mt-1">✅ உறுதி - S4/32</p>
    </div>
  )},
  // Telugu - Translate
  { type: "user", lang: "te", text: "Hello అనువదించు 🌐" },
  { type: "bot", lang: "te", content: (
    <div>
      <p className="text-xs text-blue-400 mb-1">🌐 అనువాదం</p>
      <p className="text-xs">English: Hello</p>
      <p className="text-xs text-violet-400">తెలుగు: హలో / నమస్కారం</p>
    </div>
  )},
  // Bengali - Fact Check
  { type: "user", lang: "bn", text: "এই খবরটি সত্য? 🔍" },
  { type: "bot", lang: "bn", content: (
    <div>
      <p className="text-xs text-red-400 mb-1">❌ ভুয়া খবর সতর্কতা</p>
      <p className="text-xs">এই দাবিটি মিথ্যা প্রমাণিত হয়েছে।</p>
      <p className="text-xs text-zinc-400 mt-1">📊 বিশ্বাসযোগ্যতা: 12%</p>
    </div>
  )},
  // Kannada - Birthday
  { type: "user", lang: "kn", text: "ಜನ್ಮದಿನದ ಶುಭಾಶಯ ಚಿತ್ರ 🎂" },
  { type: "bot", lang: "kn", content: (
    <div>
      <div className="w-full h-16 rounded-lg mb-1 overflow-hidden">
        <img src="/puch/features/salman-2.webp" alt="Birthday" className="w-full h-full object-cover" />
      </div>
      <p className="text-xs text-zinc-400">ಹುಟ್ಟುಹಬ್ಬದ ಶುಭಾಶಯಗಳು! 🥳</p>
    </div>
  )},
  // Gujarati - Cricket
  { type: "user", lang: "gu", text: "ક્રિકેટ સ્કોર 🏏" },
  { type: "bot", lang: "gu", content: (
    <div>
      <p className="text-xs text-green-400 mb-1">🏏 લાઈવ સ્કોર</p>
      <p className="text-xs font-semibold">IND 🇮🇳 284/3 (45 ov)</p>
      <p className="text-xs text-zinc-400">vs AUS 🇦🇺 | કોહલી 89*</p>
    </div>
  )},
  // Malayalam - Movie
  { type: "user", lang: "ml", text: "പുതിയ സിനിമ 🎬" },
  { type: "bot", lang: "ml", content: (
    <div>
      <p className="text-xs text-yellow-400 mb-1">🎬 ഈ ആഴ്ച റിലീസ്</p>
      <p className="text-xs">മഞ്ജുമ്മൽ ബോയ്സ് ⭐ 9.2</p>
      <p className="text-xs text-zinc-400 mt-1">തിയേറ്ററുകളിൽ ഇപ്പോൾ!</p>
    </div>
  )},
  // Marathi - Quote
  { type: "user", lang: "mr", text: "प्रेरणादायी विचार 💭" },
  { type: "bot", lang: "mr", content: (
    <div>
      <p className="text-xs text-amber-400 mb-1">💭 आजचा विचार</p>
      <p className="text-xs italic">"यश म्हणजे पडणे आणि पुन्हा उठणे"</p>
      <p className="text-xs text-zinc-400 mt-1">- स्वामी विवेकानंद</p>
    </div>
  )},
  // Hindi - Reminder
  { type: "user", lang: "hi", text: "याद दिलाओ सुबह 8 बजे 🔔" },
  { type: "bot", lang: "hi", content: (
    <div>
      <p className="text-xs text-green-400 mb-1">✅ रिमाइंडर सेट</p>
      <p className="text-xs">⏰ सुबह 8:00 बजे</p>
      <p className="text-xs text-zinc-400 mt-1">मैं आपको याद दिलाऊंगा!</p>
    </div>
  )},
  // English - Shinchanify
  { type: "user", lang: "en", text: "Shinchanify my photo 😜" },
  { type: "bot", lang: "en", content: (
    <div>
      <div className="w-16 h-16 rounded-xl mb-1 overflow-hidden">
        <img src="/puch/features/siddarth-shinchanified.png" alt="Shinchanified" className="w-full h-full object-cover" />
      </div>
      <p className="text-xs text-zinc-400">Your Shinchan avatar is ready! 🖼️</p>
    </div>
  )},
]

// ============== PHONE MOCKUP COMPONENT ==============
function PhoneMockup() {
  const scrollRef = useRef<HTMLDivElement>(null)
  const [isHovered, setIsHovered] = useState(false)

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
    <motion.div initial={{ opacity: 0, x: 50, rotateY: -15 }} animate={{ opacity: 1, x: 0, rotateY: 0 }} transition={{ delay: 0.5, duration: 0.8 }} className="relative flex justify-center">
      <div className="relative">
        <div className="absolute inset-0 bg-gradient-to-r from-violet-500/30 via-fuchsia-500/30 to-pink-500/30 rounded-[3rem] blur-3xl scale-110" />
        <TiltCard>
          <div className="relative w-[280px] sm:w-[320px] h-[560px] sm:h-[640px] bg-zinc-900 rounded-[2.5rem] p-2 border border-zinc-800 shadow-2xl">
            <div className="absolute top-0 left-1/2 -translate-x-1/2 w-32 h-7 bg-black rounded-b-2xl z-20" />
            <div className="w-full h-full bg-gradient-to-b from-zinc-900 to-black rounded-[2rem] overflow-hidden flex flex-col">
              {/* Header */}
              <div className="bg-gradient-to-r from-violet-600 to-fuchsia-600 px-4 py-4 pt-10 flex items-center gap-3 flex-shrink-0">
                <div className="w-10 h-10 rounded-full bg-white/20 flex items-center justify-center"><Sparkles className="w-5 h-5 text-white" /></div>
                <div>
                  <p className="text-white font-semibold">D23 AI</p>
                  <p className="text-white/70 text-xs flex items-center gap-1"><span className="w-1.5 h-1.5 rounded-full bg-green-400 animate-pulse" />Online • 11+ Languages</p>
                </div>
              </div>

              {/* Scrollable Chat Content */}
              <div
                ref={scrollRef}
                onMouseEnter={() => setIsHovered(true)}
                onMouseLeave={() => setIsHovered(false)}
                className="flex-1 overflow-y-auto p-3 space-y-3 scrollbar-thin scrollbar-thumb-violet-500/30 scrollbar-track-transparent"
                style={{ scrollBehavior: isHovered ? 'smooth' : 'auto' }}
              >
                {phoneChatMessages.map((msg, i) => (
                  <motion.div
                    key={i}
                    initial={{ opacity: 0, x: msg.type === 'user' ? 20 : -20 }}
                    animate={{ opacity: 1, x: 0 }}
                    transition={{ delay: 0.5 + i * 0.1 }}
                    className={`flex ${msg.type === 'user' ? 'justify-end' : 'justify-start'}`}
                  >
                    {msg.type === 'user' ? (
                      <div className={`max-w-[80%] bg-violet-600 text-white text-sm px-3 py-2 rounded-2xl rounded-br-md ${(msg as any).isVoice ? 'flex items-center gap-2' : ''}`}>
                        {(msg as any).isVoice && <Mic className="w-4 h-4" />}
                        {msg.text}
                      </div>
                    ) : (
                      <div className="max-w-[85%] bg-zinc-800 text-white text-sm px-3 py-2 rounded-2xl rounded-bl-md border border-zinc-700/50">
                        {(msg as any).content}
                      </div>
                    )}
                  </motion.div>
                ))}

                {/* Duplicate messages for seamless scroll loop */}
                {phoneChatMessages.map((msg, i) => (
                  <div
                    key={`dup-${i}`}
                    className={`flex ${msg.type === 'user' ? 'justify-end' : 'justify-start'}`}
                  >
                    {msg.type === 'user' ? (
                      <div className={`max-w-[80%] bg-violet-600 text-white text-sm px-3 py-2 rounded-2xl rounded-br-md ${(msg as any).isVoice ? 'flex items-center gap-2' : ''}`}>
                        {(msg as any).isVoice && <Mic className="w-4 h-4" />}
                        {msg.text}
                      </div>
                    ) : (
                      <div className="max-w-[85%] bg-zinc-800 text-white text-sm px-3 py-2 rounded-2xl rounded-bl-md border border-zinc-700/50">
                        {(msg as any).content}
                      </div>
                    )}
                  </div>
                ))}
              </div>

              {/* Gradient overlays */}
              <div className="absolute top-[76px] left-2 right-2 h-6 bg-gradient-to-b from-zinc-900 to-transparent pointer-events-none z-10 rounded-t-2xl" />
              <div className="absolute bottom-[60px] left-2 right-2 h-6 bg-gradient-to-t from-black to-transparent pointer-events-none z-10" />

              {/* Fixed Input Bar */}
              <div className="flex-shrink-0 p-3 bg-black">
                <div className="flex items-center gap-2 bg-zinc-800/80 rounded-full px-4 py-2.5 border border-zinc-700/50">
                  <span className="text-zinc-500 text-sm">Type a message...</span>
                  <div className="ml-auto flex items-center gap-2"><Mic className="w-5 h-5 text-zinc-500" /></div>
                </div>
              </div>
            </div>
          </div>
        </TiltCard>
        <motion.div animate={{ y: [0, -10, 0] }} transition={{ duration: 3, repeat: Infinity }} className="absolute -top-4 -right-4 w-16 h-16 rounded-2xl bg-gradient-to-br from-green-400 to-emerald-600 flex items-center justify-center shadow-xl shadow-green-500/30">
          <MessageCircle className="w-8 h-8 text-white" />
        </motion.div>
        <motion.div animate={{ y: [0, 10, 0] }} transition={{ duration: 4, repeat: Infinity, delay: 1 }} className="absolute -bottom-2 -left-6 w-14 h-14 rounded-xl bg-gradient-to-br from-violet-500 to-purple-600 flex items-center justify-center shadow-xl shadow-violet-500/30">
          <Languages className="w-7 h-7 text-white" />
        </motion.div>
      </div>
    </motion.div>
  )
}

// ============== FLOATING PARTICLES ==============
function FloatingParticles() {
  const [particles, setParticles] = useState<{ x: number; y: number; delay: number; duration: number }[]>([])

  useEffect(() => {
    setParticles(
      [...Array(20)].map(() => ({
        x: Math.random() * 1000,
        y: Math.random() * 800,
        delay: Math.random() * 5,
        duration: Math.random() * 10 + 10,
      }))
    )
  }, [])

  return (
    <div className="absolute inset-0 overflow-hidden pointer-events-none">
      {particles.map((particle, i) => (
        <motion.div key={i} className="absolute w-1 h-1 bg-violet-400/30 rounded-full" initial={{ x: particle.x, y: particle.y }} animate={{ y: [null, -200], opacity: [0, 1, 0] }} transition={{ duration: particle.duration, repeat: Infinity, delay: particle.delay }} />
      ))}
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
    <header className={cn("fixed top-0 left-0 right-0 z-50 transition-all duration-500", scrolled ? "bg-black/70 backdrop-blur-xl border-b border-white/10" : "")}>
      <div className="max-w-7xl mx-auto px-6 py-4">
        <div className="flex items-center justify-between">
          <Link href="/" scroll={true} className="flex items-center gap-2 cursor-pointer z-10">
            <Image src="/d23ai-logo-v7.svg" alt="D23" width={40} height={40} className="cursor-pointer hover:scale-110 transition-transform" priority />
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
              <Link href="https://wa.me/918548819349?text=Hey%20D23%20AI%21%20What%20can%20you%20do%3F" target="_blank" className="flex items-center gap-2 px-5 py-2.5 rounded-full bg-gradient-to-r from-violet-600 to-fuchsia-600 text-white text-sm font-medium shadow-lg shadow-violet-500/25 hover:shadow-violet-500/40 transition-shadow">
                <Zap className="h-4 w-4" />
                {t.nav.getStarted}
              </Link>
            </MagneticButton>
          </div>
        </div>
      </div>
    </header>
  )
}

// ============== REDESIGNED HERO SECTION ==============
function HeroSection() {
  const ref = useRef(null)
  const { scrollYProgress } = useScroll({ target: ref, offset: ["start start", "end start"] })
  const y = useTransform(scrollYProgress, [0, 1], [0, 200])
  const opacity = useTransform(scrollYProgress, [0, 0.5], [1, 0])
  const scale = useTransform(scrollYProgress, [0, 0.5], [1, 0.95])
  const t = useTranslations()

  const stats = [
    { value: 5000, suffix: "+", label: t.stats.users, icon: "👥" },
    { value: 11, suffix: "+", label: t.stats.languages, icon: "🌐" },
    { value: 24, suffix: "/7", label: t.stats.available, icon: "⚡" },
    { value: 2, suffix: "s", prefix: "<", label: t.stats.response, icon: "🚀" },
  ]

  return (
    <section ref={ref} className="relative min-h-screen flex items-center justify-center overflow-hidden">
      {/* Aurora Background */}
      <div className="absolute inset-0 bg-black">
        <div className="absolute inset-0 opacity-30">
          <div className="absolute inset-0 bg-[radial-gradient(ellipse_80%_80%_at_50%_-20%,rgba(120,119,198,0.3),rgba(255,255,255,0))]" />
        </div>
        <div className="absolute top-20 left-[10%] w-[500px] h-[500px] bg-gradient-to-r from-violet-600/40 to-fuchsia-600/40 rounded-full blur-[100px] animate-[float1_20s_ease-in-out_infinite]" />
        <div className="absolute bottom-20 right-[10%] w-[400px] h-[400px] bg-gradient-to-r from-cyan-500/30 to-blue-600/30 rounded-full blur-[100px] animate-[float2_15s_ease-in-out_infinite]" />
        <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[600px] h-[600px] bg-gradient-to-r from-pink-500/20 via-violet-500/20 to-cyan-500/20 rounded-full blur-[120px] animate-[spin_25s_linear_infinite]" />
        <div className="absolute inset-0 opacity-[0.015] bg-[url('data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHdpZHRoPSIzMDAiIGhlaWdodD0iMzAwIj48ZmlsdGVyIGlkPSJhIiB4PSIwIiB5PSIwIj48ZmVUdXJidWxlbmNlIGJhc2VGcmVxdWVuY3k9Ii43NSIgc3RpdGNoVGlsZXM9InN0aXRjaCIgdHlwZT0iZnJhY3RhbE5vaXNlIi8+PGZlQ29sb3JNYXRyaXggdHlwZT0ic2F0dXJhdGUiIHZhbHVlcz0iMCIvPjwvZmlsdGVyPjxwYXRoIGQ9Ik0wIDBoMzAwdjMwMEgweiIgZmlsdGVyPSJ1cmwoI2EpIiBvcGFjaXR5PSIuMDUiLz48L3N2Zz4=')]" />
        <div className="absolute inset-0 bg-[linear-gradient(rgba(139,92,246,0.03)_1px,transparent_1px),linear-gradient(90deg,rgba(139,92,246,0.03)_1px,transparent_1px)] bg-[size:60px_60px] animate-[pulse_4s_ease-in-out_infinite]" />
        <FloatingParticles />
      </div>

      <motion.div style={{ y, opacity, scale }} className="relative z-10 w-full max-w-7xl mx-auto px-6 pt-28 pb-12">
        <div className="grid lg:grid-cols-2 gap-8 lg:gap-4 items-center">
          {/* Left Content */}
          <div className="text-center lg:text-left">
            <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.2 }} className="inline-flex items-center gap-2 px-4 py-2 rounded-full border border-violet-500/30 bg-gradient-to-r from-violet-500/10 to-fuchsia-500/10 backdrop-blur-sm mb-6">
              <motion.div animate={{ scale: [1, 1.3, 1] }} transition={{ duration: 2, repeat: Infinity }} className="relative">
                <span className="flex h-2 w-2 rounded-full bg-green-400" />
                <span className="absolute inset-0 h-2 w-2 rounded-full bg-green-400 animate-ping" />
              </motion.div>
              <span className="text-sm font-medium bg-gradient-to-r from-violet-300 to-fuchsia-300 bg-clip-text text-transparent">{t.hero.badge}</span>
            </motion.div>

            <h1 className="text-4xl sm:text-5xl md:text-6xl lg:text-7xl font-bold text-white mb-6 leading-[1.1] tracking-tight">
              <span className="whitespace-nowrap"><TextReveal>{t.hero.headline1}</TextReveal></span>
              <br />
              <span className="relative">
                <span className="text-zinc-500">{t.hero.headline2} </span>
                <span className="relative">
                  <RotatingWord words={rotatingWords} />
                  <motion.span className="absolute -bottom-2 left-0 right-0 h-1 bg-gradient-to-r from-violet-500 via-fuchsia-500 to-pink-500 rounded-full" initial={{ scaleX: 0 }} animate={{ scaleX: 1 }} transition={{ delay: 1, duration: 0.8 }} />
                </span>
              </span>
            </h1>

            <motion.p initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.6 }} className="text-lg md:text-xl text-zinc-400 max-w-xl mx-auto lg:mx-0 mb-8">{t.hero.subtitle}</motion.p>

            <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.8 }} className="flex flex-wrap items-center justify-center lg:justify-start gap-4 mb-8">
              <MagneticButton>
                <Link href="https://wa.me/918548819349?text=Hey%20D23%20AI%21%20What%20can%20you%20do%3F" target="_blank" className="group relative flex items-center gap-3 px-8 py-4 rounded-2xl bg-gradient-to-r from-violet-600 via-fuchsia-600 to-pink-600 text-white font-semibold overflow-hidden">
                  <span className="absolute inset-0 bg-gradient-to-r from-violet-400 via-fuchsia-400 to-pink-400 opacity-0 group-hover:opacity-100 transition-opacity duration-300" />
                  <span className="absolute inset-0 shadow-[inset_0_1px_1px_rgba(255,255,255,0.3)]" />
                  <MessageCircle className="h-5 w-5 relative z-10" />
                  <span className="relative z-10">{t.hero.ctaWhatsapp}</span>
                  <ArrowRight className="h-5 w-5 relative z-10 group-hover:translate-x-1 transition-transform" />
                </Link>
              </MagneticButton>
              <MagneticButton>
                <Link href="/chat" className="group flex items-center gap-3 px-8 py-4 rounded-2xl border border-white/20 text-white font-semibold hover:bg-white/5 hover:border-white/30 transition-all backdrop-blur-sm">
                  <Play className="h-4 w-4 group-hover:scale-110 transition-transform" />
                  {t.hero.ctaWeb}
                </Link>
              </MagneticButton>
            </motion.div>

            <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 1 }} className="flex flex-wrap items-center justify-center lg:justify-start gap-3">
              <div className="relative group cursor-pointer">
                <div className="flex items-center gap-3 px-5 py-2.5 rounded-xl bg-white/5 border border-white/10 hover:border-white/20 hover:bg-white/10 transition-all backdrop-blur-sm">
                  <svg className="w-7 h-7 text-white" viewBox="0 0 24 24" fill="currentColor"><path d="M18.71 19.5c-.83 1.24-1.71 2.45-3.05 2.47-1.34.03-1.77-.79-3.29-.79-1.53 0-2 .77-3.27.82-1.31.05-2.3-1.32-3.14-2.53C4.25 17 2.94 12.45 4.7 9.39c.87-1.52 2.43-2.48 4.12-2.51 1.28-.02 2.5.87 3.29.87.78 0 2.26-1.07 3.81-.91.65.03 2.47.26 3.64 1.98-.09.06-2.17 1.28-2.15 3.81.03 3.02 2.65 4.03 2.68 4.04-.03.07-.42 1.44-1.38 2.83M13 3.5c.73-.83 1.94-1.46 2.94-1.5.13 1.17-.34 2.35-1.04 3.19-.69.85-1.83 1.51-2.95 1.42-.15-1.15.41-2.35 1.05-3.11z"/></svg>
                  <div className="text-left">
                    <p className="text-[9px] text-zinc-500 uppercase tracking-wider">{t.hero.comingSoon}</p>
                    <p className="text-white font-medium text-sm">{t.hero.appStore}</p>
                  </div>
                </div>
                <span className="absolute -top-1.5 -right-1.5 px-2 py-0.5 rounded-full bg-gradient-to-r from-violet-500 to-fuchsia-500 text-[9px] text-white font-bold shadow-lg">{t.hero.soon}</span>
              </div>
              <div className="relative group cursor-pointer">
                <div className="flex items-center gap-3 px-5 py-2.5 rounded-xl bg-white/5 border border-white/10 hover:border-white/20 hover:bg-white/10 transition-all backdrop-blur-sm">
                  <svg className="w-7 h-7 text-white" viewBox="0 0 24 24" fill="currentColor"><path d="M3.609 1.814L13.792 12 3.61 22.186a.996.996 0 0 1-.61-.92V2.734a1 1 0 0 1 .609-.92zm10.89 10.893l2.302 2.302-10.937 6.333 8.635-8.635zm3.199-3.198l2.807 1.626a1 1 0 0 1 0 1.73l-2.808 1.626L15.206 12l2.492-2.491zM5.864 2.658L16.8 8.99l-2.302 2.302-8.634-8.634z"/></svg>
                  <div className="text-left">
                    <p className="text-[9px] text-zinc-500 uppercase tracking-wider">{t.hero.comingSoon}</p>
                    <p className="text-white font-medium text-sm">{t.hero.playStore}</p>
                  </div>
                </div>
                <span className="absolute -top-1.5 -right-1.5 px-2 py-0.5 rounded-full bg-gradient-to-r from-violet-500 to-fuchsia-500 text-[9px] text-white font-bold shadow-lg">{t.hero.soon}</span>
              </div>
            </motion.div>
          </div>

          {/* Right Content - Phone Mockup */}
          <PhoneMockup />
        </div>

        {/* Stats - Bento Style */}
        <motion.div initial={{ opacity: 0, y: 40 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 1.2 }} className="grid grid-cols-2 md:grid-cols-4 gap-4 mt-16">
          {stats.map((stat, i) => (
            <motion.div key={stat.label} initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 1.3 + i * 0.1 }} whileHover={{ scale: 1.02, y: -2 }} className="relative group">
              <div className="absolute inset-0 bg-gradient-to-r from-violet-500/20 to-fuchsia-500/20 rounded-2xl blur-xl opacity-0 group-hover:opacity-100 transition-opacity" />
              <div className="relative p-6 rounded-2xl bg-white/[0.03] border border-white/10 backdrop-blur-sm hover:border-violet-500/30 transition-colors">
                <span className="text-2xl mb-2 block">{stat.icon}</span>
                <div className="text-3xl md:text-4xl font-bold text-white mb-1">{stat.prefix || ""}<AnimatedCounter value={stat.value} suffix={stat.suffix} /></div>
                <div className="text-sm text-zinc-500">{stat.label}</div>
              </div>
            </motion.div>
          ))}
        </motion.div>
      </motion.div>

      <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ delay: 1.5 }} className="absolute bottom-8 left-1/2 -translate-x-1/2">
        <motion.div animate={{ y: [0, 8, 0] }} transition={{ duration: 1.5, repeat: Infinity }} className="flex flex-col items-center gap-2">
          <span className="text-xs text-zinc-500 uppercase tracking-widest">Scroll</span>
          <ChevronDown className="h-5 w-5 text-zinc-500" />
        </motion.div>
      </motion.div>
    </section>
  )
}

// ============== ANIMATED DEMO SHOWCASE ==============
const demoConversations = [
  {
    id: "weather",
    icon: "🌤️",
    title: "Weather",
    color: "from-sky-500 to-blue-600",
    conversation: [
      { type: "user", text: "आज दिल्ली का मौसम कैसा है?", lang: "हिंदी" },
      { type: "bot", text: "दिल्ली में आज:\n🌡️ 28°C\n☀️ साफ आसमान\n💨 हवा: 12 km/h\n💧 नमी: 45%", lang: "हिंदी" },
    ],
  },
  {
    id: "image",
    icon: "🎨",
    title: "AI Images",
    color: "from-orange-500 to-pink-600",
    conversation: [
      { type: "user", text: "Generate a sunset over mountains", lang: "English" },
      { type: "bot", text: "Creating your image...", lang: "English", isImage: true },
    ],
  },
  {
    id: "translate",
    icon: "🌐",
    title: "Translate",
    color: "from-emerald-500 to-teal-600",
    conversation: [
      { type: "user", text: "How do you say 'thank you' in Tamil?", lang: "English" },
      { type: "bot", text: "நன்றி (Nandri)\n\nUsage: நன்றி சொல்கிறேன் 🙏", lang: "தமிழ்" },
    ],
  },
  {
    id: "factcheck",
    icon: "🔍",
    title: "Fact Check",
    color: "from-red-500 to-rose-600",
    conversation: [
      { type: "user", text: "Is this news real? [forwarded message]", lang: "English" },
      { type: "bot", text: "⚠️ MISLEADING\n\nThis claim is partially false. Here's what we found...", lang: "English" },
    ],
  },
  {
    id: "games",
    icon: "🎮",
    title: "Games",
    color: "from-violet-500 to-purple-600",
    conversation: [
      { type: "user", text: "ಪದ ಆಟ ಆಡೋಣ!", lang: "ಕನ್ನಡ" },
      { type: "bot", text: "🟩🟨🟩🟩🟩\n\nಅದ್ಭುತ! 3/6 ಪ್ರಯತ್ನಗಳಲ್ಲಿ ಗೆದ್ದಿರಿ! 🎉", lang: "ಕನ್ನಡ", isGame: true },
    ],
  },
  {
    id: "stickers",
    icon: "🎭",
    title: "Stickers",
    color: "from-amber-500 to-yellow-600",
    conversation: [
      { type: "user", text: "Make me a sticker of a happy dog", lang: "English" },
      { type: "bot", text: "Here's your custom sticker! 🐕", lang: "English", isSticker: true },
    ],
  },
]

const languageFlags = [
  { lang: "हिंदी", flag: "🇮🇳" },
  { lang: "தமிழ்", flag: "🇮🇳" },
  { lang: "తెలుగు", flag: "🇮🇳" },
  { lang: "ಕನ್ನಡ", flag: "🇮🇳" },
  { lang: "മലയാളം", flag: "🇮🇳" },
  { lang: "বাংলা", flag: "🇮🇳" },
  { lang: "मराठी", flag: "🇮🇳" },
  { lang: "ગુજરાતી", flag: "🇮🇳" },
  { lang: "ਪੰਜਾਬੀ", flag: "🇮🇳" },
  { lang: "ଓଡ଼ିଆ", flag: "🇮🇳" },
  { lang: "English", flag: "🌐" },
]

function AnimatedDemoShowcase() {
  const [activeDemo, setActiveDemo] = useState(0)
  const [isTyping, setIsTyping] = useState(false)
  const [showResponse, setShowResponse] = useState(false)
  const ref = useRef(null)
  const isInView = useInView(ref, { once: true, margin: "-100px" })

  // Auto-rotate demos
  useEffect(() => {
    if (!isInView) return
    const interval = setInterval(() => {
      setShowResponse(false)
      setIsTyping(false)
      setTimeout(() => {
        setActiveDemo((prev) => (prev + 1) % demoConversations.length)
      }, 300)
    }, 5000)
    return () => clearInterval(interval)
  }, [isInView])

  // Simulate typing effect
  useEffect(() => {
    if (!isInView) return
    setIsTyping(true)
    const timer = setTimeout(() => {
      setIsTyping(false)
      setShowResponse(true)
    }, 1200)
    return () => clearTimeout(timer)
  }, [activeDemo, isInView])

  const currentDemo = demoConversations[activeDemo]

  return (
    <section ref={ref} className="py-24 px-6 overflow-hidden relative">
      {/* Background Elements */}
      <div className="absolute inset-0 overflow-hidden">
        <motion.div
          animate={{ rotate: 360 }}
          transition={{ duration: 60, repeat: Infinity, ease: "linear" }}
          className="absolute -top-1/2 -right-1/2 w-full h-full bg-gradient-conic from-violet-500/10 via-transparent to-fuchsia-500/10 blur-3xl"
        />
      </div>

      <div className="max-w-6xl mx-auto relative z-10">
        {/* Header */}
        <StaggerContainer className="text-center mb-16">
          <StaggerItem>
            <motion.div
              initial={{ scale: 0 }}
              animate={isInView ? { scale: 1 } : {}}
              className="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-violet-500/10 border border-violet-500/20 mb-4"
            >
              <motion.div
                animate={{ rotate: [0, 360] }}
                transition={{ duration: 3, repeat: Infinity, ease: "linear" }}
              >
                <Sparkles className="w-4 h-4 text-violet-400" />
              </motion.div>
              <span className="text-violet-400 text-sm font-medium">Interactive Demo</span>
            </motion.div>
          </StaggerItem>
          <StaggerItem>
            <h2 className="text-4xl md:text-6xl font-bold text-white mt-3">
              Try D23 AI <GradientText>Features</GradientText>
            </h2>
          </StaggerItem>
          <StaggerItem>
            <p className="text-zinc-400 mt-4 max-w-xl mx-auto text-lg">
              Click on any feature to see how D23 AI responds in real-time
            </p>
          </StaggerItem>
        </StaggerContainer>

        {/* Main Demo Area */}
        <div className="grid lg:grid-cols-5 gap-8 items-start">
          {/* Feature Selector - Left */}
          <div className="lg:col-span-2 space-y-3">
            {demoConversations.map((demo, i) => (
              <motion.button
                key={demo.id}
                onClick={() => {
                  setShowResponse(false)
                  setIsTyping(false)
                  setActiveDemo(i)
                }}
                initial={{ opacity: 0, x: -30 }}
                animate={isInView ? { opacity: 1, x: 0 } : {}}
                transition={{ delay: i * 0.1 }}
                whileHover={{ x: 8 }}
                className={cn(
                  "w-full flex items-center gap-4 p-4 rounded-2xl border transition-all duration-300 text-left group",
                  i === activeDemo
                    ? "bg-gradient-to-r from-violet-500/20 to-fuchsia-500/20 border-violet-500/50 shadow-lg shadow-violet-500/10"
                    : "bg-white/[0.02] border-white/10 hover:border-white/20 hover:bg-white/[0.04]"
                )}
              >
                <div className={cn(
                  "w-14 h-14 rounded-xl flex items-center justify-center text-2xl transition-transform duration-300",
                  i === activeDemo ? `bg-gradient-to-br ${demo.color} shadow-lg` : "bg-zinc-800/80",
                  "group-hover:scale-110"
                )}>
                  {demo.icon}
                </div>
                <div className="flex-1">
                  <h3 className={cn(
                    "font-semibold transition-colors",
                    i === activeDemo ? "text-white" : "text-zinc-300"
                  )}>
                    {demo.title}
                  </h3>
                  <p className="text-xs text-zinc-500 mt-0.5">
                    {demo.conversation[0].text.slice(0, 30)}...
                  </p>
                </div>
                {i === activeDemo && (
                  <motion.div
                    layoutId="activeIndicator"
                    className="w-1.5 h-10 rounded-full bg-gradient-to-b from-violet-500 to-fuchsia-500"
                  />
                )}
              </motion.button>
            ))}
          </div>

          {/* Chat Preview - Right */}
          <motion.div
            initial={{ opacity: 0, y: 30 }}
            animate={isInView ? { opacity: 1, y: 0 } : {}}
            transition={{ delay: 0.3 }}
            className="lg:col-span-3"
          >
            <div className="relative">
              {/* Glow */}
              <motion.div
                key={activeDemo}
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                className={cn(
                  "absolute -inset-4 rounded-3xl blur-3xl opacity-30",
                  `bg-gradient-to-r ${currentDemo.color}`
                )}
              />

              {/* Chat Window */}
              <div className="relative bg-zinc-900/90 rounded-3xl border border-white/10 overflow-hidden backdrop-blur-xl shadow-2xl">
                {/* Header */}
                <div className={cn("p-4 flex items-center gap-3 bg-gradient-to-r", currentDemo.color)}>
                  <div className="w-12 h-12 rounded-full bg-white/20 flex items-center justify-center backdrop-blur-sm">
                    <span className="text-2xl">{currentDemo.icon}</span>
                  </div>
                  <div className="flex-1">
                    <h3 className="text-white font-bold text-lg">{currentDemo.title}</h3>
                    <div className="flex items-center gap-2">
                      <span className="w-2 h-2 rounded-full bg-green-400 animate-pulse" />
                      <span className="text-white/70 text-sm">D23 AI is ready</span>
                    </div>
                  </div>
                  <div className="flex gap-2">
                    <div className="w-3 h-3 rounded-full bg-white/20" />
                    <div className="w-3 h-3 rounded-full bg-white/20" />
                    <div className="w-3 h-3 rounded-full bg-white/20" />
                  </div>
                </div>

                {/* Messages */}
                <div className="p-6 min-h-[320px] space-y-4">
                  {/* User Message */}
                  <motion.div
                    key={`user-${activeDemo}`}
                    initial={{ opacity: 0, x: 30 }}
                    animate={{ opacity: 1, x: 0 }}
                    className="flex justify-end"
                  >
                    <div className="max-w-[80%]">
                      <div className="bg-violet-600 text-white px-4 py-3 rounded-2xl rounded-br-md shadow-lg">
                        <p className="text-sm">{currentDemo.conversation[0].text}</p>
                      </div>
                      <p className="text-xs text-zinc-500 mt-1 text-right">{currentDemo.conversation[0].lang}</p>
                    </div>
                  </motion.div>

                  {/* Bot Response */}
                  <AnimatePresence mode="wait">
                    {isTyping && (
                      <motion.div
                        initial={{ opacity: 0, y: 10 }}
                        animate={{ opacity: 1, y: 0 }}
                        exit={{ opacity: 0, y: -10 }}
                        className="flex justify-start"
                      >
                        <div className="bg-zinc-800 px-4 py-3 rounded-2xl rounded-bl-md border border-zinc-700">
                          <div className="flex gap-1.5">
                            <motion.span animate={{ y: [0, -5, 0] }} transition={{ duration: 0.5, repeat: Infinity, delay: 0 }} className="w-2 h-2 bg-zinc-500 rounded-full" />
                            <motion.span animate={{ y: [0, -5, 0] }} transition={{ duration: 0.5, repeat: Infinity, delay: 0.1 }} className="w-2 h-2 bg-zinc-500 rounded-full" />
                            <motion.span animate={{ y: [0, -5, 0] }} transition={{ duration: 0.5, repeat: Infinity, delay: 0.2 }} className="w-2 h-2 bg-zinc-500 rounded-full" />
                          </div>
                        </div>
                      </motion.div>
                    )}

                    {showResponse && (
                      <motion.div
                        key={`bot-${activeDemo}`}
                        initial={{ opacity: 0, y: 20, scale: 0.95 }}
                        animate={{ opacity: 1, y: 0, scale: 1 }}
                        className="flex justify-start"
                      >
                        <div className="max-w-[85%]">
                          <div className="bg-zinc-800 text-white px-4 py-3 rounded-2xl rounded-bl-md border border-zinc-700/50 shadow-lg">
                            {(currentDemo.conversation[1] as any).isImage && (
                              <div className="w-full h-40 rounded-xl mb-3 overflow-hidden bg-gradient-to-br from-orange-400 to-pink-600 flex items-center justify-center">
                                <motion.div
                                  initial={{ scale: 0 }}
                                  animate={{ scale: 1 }}
                                  transition={{ delay: 0.3, type: "spring" }}
                                >
                                  <ImageIcon className="w-12 h-12 text-white/80" />
                                </motion.div>
                              </div>
                            )}
                            {(currentDemo.conversation[1] as any).isGame && (
                              <div className="flex gap-1 mb-2">
                                {['🟩', '🟨', '🟩', '🟩', '🟩'].map((box, i) => (
                                  <motion.span
                                    key={i}
                                    initial={{ scale: 0, rotate: -180 }}
                                    animate={{ scale: 1, rotate: 0 }}
                                    transition={{ delay: 0.1 * i, type: "spring" }}
                                    className="w-8 h-8 flex items-center justify-center text-lg"
                                  >
                                    {box}
                                  </motion.span>
                                ))}
                              </div>
                            )}
                            {(currentDemo.conversation[1] as any).isSticker && (
                              <motion.div
                                initial={{ scale: 0, rotate: -20 }}
                                animate={{ scale: 1, rotate: 0 }}
                                transition={{ type: "spring" }}
                                className="w-24 h-24 bg-gradient-to-br from-amber-400 to-yellow-500 rounded-2xl mb-2 flex items-center justify-center text-5xl"
                              >
                                🐕
                              </motion.div>
                            )}
                            <p className="text-sm whitespace-pre-line">{currentDemo.conversation[1].text}</p>
                          </div>
                          <p className="text-xs text-zinc-500 mt-1">{currentDemo.conversation[1].lang}</p>
                        </div>
                      </motion.div>
                    )}
                  </AnimatePresence>
                </div>

                {/* Input */}
                <div className="p-4 border-t border-white/5 bg-black/30">
                  <div className="flex items-center gap-3 bg-zinc-800/50 rounded-full px-4 py-3 border border-zinc-700/50">
                    <input
                      type="text"
                      placeholder="Type a message in any language..."
                      className="flex-1 bg-transparent text-white placeholder-zinc-500 text-sm outline-none"
                      disabled
                    />
                    <div className="flex gap-2">
                      <div className="w-8 h-8 rounded-full bg-zinc-700/50 flex items-center justify-center">
                        <Mic className="w-4 h-4 text-zinc-400" />
                      </div>
                      <div className="w-8 h-8 rounded-full bg-gradient-to-r from-violet-500 to-fuchsia-500 flex items-center justify-center">
                        <ArrowRight className="w-4 h-4 text-white" />
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </div>

            {/* Languages */}
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={isInView ? { opacity: 1, y: 0 } : {}}
              transition={{ delay: 0.5 }}
              className="mt-6 p-4 rounded-2xl bg-white/[0.02] border border-white/10"
            >
              <p className="text-xs text-zinc-500 mb-3 uppercase tracking-wider text-center">Works in 11+ Indian Languages</p>
              <div className="flex flex-wrap justify-center gap-2">
                {languageFlags.map((item, i) => (
                  <motion.span
                    key={item.lang}
                    initial={{ opacity: 0, scale: 0 }}
                    animate={isInView ? { opacity: 1, scale: 1 } : {}}
                    transition={{ delay: 0.6 + i * 0.05 }}
                    whileHover={{ scale: 1.1, y: -2 }}
                    className="px-3 py-1.5 rounded-full bg-zinc-800/50 border border-zinc-700/50 text-xs text-white cursor-default flex items-center gap-1.5"
                  >
                    <span>{item.flag}</span>
                    <span>{item.lang}</span>
                  </motion.span>
                ))}
              </div>
            </motion.div>
          </motion.div>
        </div>

        {/* Bottom Stats */}
        <motion.div
          initial={{ opacity: 0, y: 30 }}
          animate={isInView ? { opacity: 1, y: 0 } : {}}
          transition={{ delay: 0.7 }}
          className="grid grid-cols-2 md:grid-cols-4 gap-4 mt-16"
        >
          {[
            { value: "5K+", label: "Active Users", icon: "👥" },
            { value: "50K+", label: "Messages/Day", icon: "💬" },
            { value: "<2s", label: "Response Time", icon: "⚡" },
            { value: "24/7", label: "Available", icon: "🌙" },
          ].map((stat, i) => (
            <motion.div
              key={stat.label}
              initial={{ opacity: 0, y: 20 }}
              animate={isInView ? { opacity: 1, y: 0 } : {}}
              transition={{ delay: 0.8 + i * 0.1 }}
              whileHover={{ y: -4, scale: 1.02 }}
              className="relative group"
            >
              <div className="absolute inset-0 bg-gradient-to-r from-violet-500/10 to-fuchsia-500/10 rounded-2xl blur-xl opacity-0 group-hover:opacity-100 transition-opacity" />
              <div className="relative p-6 rounded-2xl bg-white/[0.03] border border-white/10 text-center hover:border-violet-500/30 transition-colors">
                <span className="text-3xl mb-2 block">{stat.icon}</span>
                <p className="text-3xl font-bold text-white">{stat.value}</p>
                <p className="text-sm text-zinc-500">{stat.label}</p>
              </div>
            </motion.div>
          ))}
        </motion.div>
      </div>
    </section>
  )
}

// ============== FEATURES SECTION ==============
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
          <StaggerItem><span className="text-violet-400 text-sm font-semibold tracking-wider uppercase">{t.features.label}</span></StaggerItem>
          <StaggerItem><h2 className="text-4xl md:text-5xl font-bold text-white mt-3">{t.features.title1}<br /><GradientText>{t.features.title2}</GradientText></h2></StaggerItem>
        </StaggerContainer>
        <StaggerContainer className="grid md:grid-cols-2 lg:grid-cols-3 gap-6">
          {features.map((feature) => {
            const featureData = t.features[feature.titleKey as keyof typeof t.features] as { title: string; desc: string }
            return (
              <StaggerItem key={feature.id}>
                <TiltCard className="h-full">
                  <GradientBorderCard className="h-full">
                    <div className="p-6 h-full">
                      <motion.div whileHover={{ scale: 1.1, rotate: 5 }} className={cn("w-14 h-14 rounded-2xl flex items-center justify-center mb-5 bg-gradient-to-br", feature.color)}>{feature.icon}</motion.div>
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

// ============== CHAT SHOWCASE ==============
function ChatShowcase() {
  const scrollRef = useRef<HTMLDivElement>(null)
  const [isHovered, setIsHovered] = useState(false)
  const t = useTranslations()

  useEffect(() => {
    const container = scrollRef.current
    if (!container) return
    let animationId: number
    let scrollPosition = 0
    const autoScroll = () => {
      if (!isHovered && container) {
        scrollPosition += 0.5
        if (scrollPosition >= container.scrollHeight - container.clientHeight) scrollPosition = 0
        container.scrollTop = scrollPosition
      }
      animationId = requestAnimationFrame(autoScroll)
    }
    animationId = requestAnimationFrame(autoScroll)
    return () => cancelAnimationFrame(animationId)
  }, [isHovered])

  return (
    <motion.div initial={{ opacity: 0, x: 50 }} whileInView={{ opacity: 1, x: 0 }} viewport={{ once: true }} className="flex-shrink-0 w-80">
      <TiltCard>
        <GradientBorderCard className="group">
          <div className="aspect-[3/4] relative overflow-hidden rounded-xl bg-gradient-to-b from-zinc-900 to-black">
            <div className="sticky top-0 z-10 bg-gradient-to-r from-violet-600 to-fuchsia-600 px-4 py-3 flex items-center gap-3">
              <div className="w-10 h-10 rounded-full bg-white/20 flex items-center justify-center"><MessageCircle className="w-5 h-5 text-white" /></div>
              <div>
                <p className="text-white font-semibold text-sm">D23 AI</p>
                <p className="text-white/70 text-xs flex items-center gap-1"><span className="w-2 h-2 rounded-full bg-green-400 animate-pulse" />{t.showcase.languagesCount}</p>
              </div>
              <Languages className="w-5 h-5 text-white/70 ml-auto" />
            </div>
            <div ref={scrollRef} onMouseEnter={() => setIsHovered(true)} onMouseLeave={() => setIsHovered(false)} className="h-[calc(100%-60px)] overflow-y-auto px-3 py-3 space-y-3 scrollbar-thin scrollbar-thumb-violet-500/30 scrollbar-track-transparent" style={{ scrollBehavior: isHovered ? 'smooth' : 'auto' }}>
              {[...multilingualMessages, ...multilingualMessages].map((msg, i) => (
                <motion.div key={i} initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: i * 0.1 }} className="space-y-2">
                  <div className="flex items-center justify-center gap-1.5"><span className="text-xs">{msg.flag}</span><span className="text-[10px] text-zinc-500 font-medium uppercase tracking-wider">{msg.lang}</span></div>
                  <div className="flex justify-end"><div className="max-w-[85%] bg-violet-600 text-white text-xs px-3 py-2 rounded-2xl rounded-br-md shadow-lg">{msg.user}</div></div>
                  <div className="flex justify-start"><div className="max-w-[85%] bg-zinc-800 text-zinc-200 text-xs px-3 py-2 rounded-2xl rounded-bl-md shadow-lg border border-zinc-700/50">{msg.bot}</div></div>
                </motion.div>
              ))}
            </div>
            <div className="absolute top-[52px] left-0 right-0 h-8 bg-gradient-to-b from-zinc-900 to-transparent pointer-events-none z-[5]" />
            <div className="absolute bottom-0 left-0 right-0 h-8 bg-gradient-to-t from-black to-transparent pointer-events-none z-[5]" />
            <div className="absolute bottom-3 left-3 right-3 z-10">
              <span className="inline-block px-3 py-1 rounded-full bg-violet-500/20 border border-violet-500/30 text-violet-300 text-xs font-medium mb-2">{t.showcase.multilingual}</span>
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
          <StaggerItem><span className="text-violet-400 text-sm font-semibold tracking-wider uppercase">{t.showcase.label}</span></StaggerItem>
          <StaggerItem><h2 className="text-4xl md:text-5xl font-bold text-white mt-3">{t.showcase.title}</h2></StaggerItem>
        </StaggerContainer>
      </div>
      <div className="flex gap-6 px-6 overflow-x-auto pb-6 scrollbar-hide">
        <ChatShowcase />
        {showcaseItems.map((item, i) => (
          <motion.div key={item.title} initial={{ opacity: 0, x: 50 }} whileInView={{ opacity: 1, x: 0 }} transition={{ delay: (i + 1) * 0.1 }} viewport={{ once: true }} className="flex-shrink-0 w-72">
            <TiltCard>
              <GradientBorderCard className="group">
                <div className="aspect-[3/4] relative overflow-hidden rounded-xl">
                  <Image src={item.image} alt={item.title} fill className="object-cover transition-transform duration-700 group-hover:scale-110" />
                  <div className="absolute inset-0 bg-gradient-to-t from-black via-black/30 to-transparent" />
                  <div className="absolute bottom-4 left-4 right-4">
                    <span className="inline-block px-3 py-1 rounded-full bg-violet-500/20 border border-violet-500/30 text-violet-300 text-xs font-medium mb-2">{item.tag}</span>
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

// ============== ABOUT SECTION ==============
function AboutSection() {
  return (
    <section id="about" className="py-20 px-6 relative overflow-hidden">
      <div className="absolute inset-0 bg-gradient-to-b from-black via-violet-950/10 to-black" />
      <div className="max-w-6xl mx-auto relative z-10">
        <StaggerContainer className="text-center mb-12">
          <StaggerItem><span className="text-violet-400 text-sm font-semibold tracking-wider uppercase">About Us</span></StaggerItem>
          <StaggerItem><h2 className="text-3xl md:text-4xl font-bold text-white mt-3">Built for <GradientText>Bharat</GradientText></h2></StaggerItem>
        </StaggerContainer>
        <div className="grid md:grid-cols-2 gap-10 items-center">
          <StaggerContainer>
            <StaggerItem><p className="text-lg text-zinc-400 mb-6">D23 AI is India's first WhatsApp-native AI assistant designed specifically for Indian users. We understand that language should never be a barrier to accessing AI.</p></StaggerItem>
            <StaggerItem><p className="text-lg text-zinc-400 mb-6">Our mission is to make AI accessible to every Indian, in their own language. Whether you speak Hindi, Tamil, Telugu, Bengali, or any of the 11+ languages we support, D23 AI understands and responds naturally.</p></StaggerItem>
            <StaggerItem><p className="text-lg text-zinc-400">From fact-checking viral messages to generating images, from playing games to getting instant answers - D23 AI is your intelligent companion on WhatsApp.</p></StaggerItem>
          </StaggerContainer>
          <StaggerItem>
            <TiltCard>
              <GradientBorderCard>
                <div className="p-8 space-y-6">
                  <div className="flex items-center gap-4"><div className="w-12 h-12 rounded-xl bg-gradient-to-br from-violet-500 to-purple-500 flex items-center justify-center"><Globe className="h-6 w-6 text-white" /></div><div><p className="text-2xl font-bold text-white">11+</p><p className="text-zinc-500">Indian Languages</p></div></div>
                  <div className="flex items-center gap-4"><div className="w-12 h-12 rounded-xl bg-gradient-to-br from-fuchsia-500 to-pink-500 flex items-center justify-center"><MessageCircle className="h-6 w-6 text-white" /></div><div><p className="text-2xl font-bold text-white">WhatsApp</p><p className="text-zinc-500">Native Experience</p></div></div>
                  <div className="flex items-center gap-4"><div className="w-12 h-12 rounded-xl bg-gradient-to-br from-green-500 to-emerald-500 flex items-center justify-center"><Zap className="h-6 w-6 text-white" /></div><div><p className="text-2xl font-bold text-white">&lt;2 Seconds</p><p className="text-zinc-500">Response Time</p></div></div>
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
function FoundersSection() {
  return (
    <section className="py-16 px-6">
      <div className="max-w-4xl mx-auto">
        <StaggerContainer className="text-center mb-12">
          <StaggerItem><span className="text-violet-400 text-sm font-semibold tracking-wider uppercase">Our Team</span></StaggerItem>
          <StaggerItem><h2 className="text-3xl md:text-4xl font-bold text-white mt-3">Meet the <GradientText>Founders</GradientText></h2></StaggerItem>
          <StaggerItem><p className="text-zinc-400 mt-3 max-w-xl mx-auto">Passionate technologists on a mission to make AI accessible to every Indian.</p></StaggerItem>
        </StaggerContainer>
        <StaggerContainer className="flex flex-wrap justify-center gap-12">
          {founders.map((member) => (
            <StaggerItem key={member.name}>
              <motion.div whileHover={{ y: -5 }} className="text-center">
                <div className="relative w-32 h-32 mx-auto mb-4">
                  <div className="absolute inset-0 rounded-full bg-gradient-to-r from-violet-500 to-fuchsia-500 blur-md opacity-50" />
                  <div className="relative w-32 h-32 rounded-full bg-zinc-800 flex items-center justify-center border-2 border-violet-500/50 overflow-hidden"><span className="text-4xl font-bold text-white">{member.name[0]}</span></div>
                </div>
                <h3 className="text-xl font-semibold text-white">{member.name}</h3>
                <p className="text-sm text-zinc-400 mb-3">{member.role}</p>
                <div className="flex justify-center gap-3">
                  <a href={member.twitter} target="_blank" rel="noopener noreferrer" className="w-9 h-9 rounded-full bg-white/5 flex items-center justify-center text-zinc-400 hover:text-white hover:bg-white/10 transition-colors"><Twitter className="h-4 w-4" /></a>
                  <a href={member.linkedin} target="_blank" rel="noopener noreferrer" className="w-9 h-9 rounded-full bg-white/5 flex items-center justify-center text-zinc-400 hover:text-white hover:bg-white/10 transition-colors"><Linkedin className="h-4 w-4" /></a>
                </div>
              </motion.div>
            </StaggerItem>
          ))}
        </StaggerContainer>
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
          <StaggerItem><span className="text-violet-400 text-sm font-semibold tracking-wider uppercase">{t.faq.label}</span></StaggerItem>
          <StaggerItem><h2 className="text-3xl md:text-4xl font-bold text-white mt-3">{t.faq.title} <GradientText>{t.faq.titleHighlight}</GradientText></h2></StaggerItem>
        </StaggerContainer>
        <StaggerContainer className="space-y-4">
          {faqIds.map((id, i) => (
            <StaggerItem key={id}>
              <GradientBorderCard>
                <button onClick={() => setOpen(open === i ? null : i)} className="w-full flex items-center justify-between p-6 text-left">
                  <span className="text-lg font-medium text-white">{t.faq[id]}</span>
                  <motion.div animate={{ rotate: open === i ? 180 : 0 }} transition={{ duration: 0.3 }}><ChevronDown className="h-5 w-5 text-violet-400" /></motion.div>
                </button>
                <AnimatePresence>
                  {open === i && (
                    <motion.div initial={{ height: 0, opacity: 0 }} animate={{ height: "auto", opacity: 1 }} exit={{ height: 0, opacity: 0 }} transition={{ duration: 0.3 }}>
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

// ============== CONTACT SECTION ==============
function ContactSection() {
  return (
    <section id="contact" className="py-16 px-6">
      <div className="max-w-4xl mx-auto">
        <StaggerContainer className="text-center mb-12">
          <StaggerItem><span className="text-violet-400 text-sm font-semibold tracking-wider uppercase">Contact</span></StaggerItem>
          <StaggerItem><h2 className="text-4xl md:text-5xl font-bold text-white mt-3">Get in <GradientText>Touch</GradientText></h2></StaggerItem>
          <StaggerItem><p className="text-zinc-400 mt-4 max-w-xl mx-auto">Have questions or feedback? We'd love to hear from you. Reach out to us through any of these channels.</p></StaggerItem>
        </StaggerContainer>
        <StaggerContainer className="grid md:grid-cols-3 gap-6">
          <StaggerItem>
            <TiltCard className="h-full">
              <GradientBorderCard className="h-full">
                <div className="p-6 text-center">
                  <div className="w-14 h-14 rounded-2xl bg-gradient-to-br from-green-500 to-emerald-500 flex items-center justify-center mx-auto mb-4"><MessageCircle className="h-7 w-7 text-white" /></div>
                  <h3 className="text-lg font-semibold text-white mb-2">WhatsApp</h3>
                  <p className="text-zinc-400 text-sm mb-4">Chat with D23 AI directly</p>
                  <Link href="https://wa.me/918548819349" target="_blank" className="text-violet-400 hover:text-violet-300 text-sm font-medium">+91 85488 19349</Link>
                </div>
              </GradientBorderCard>
            </TiltCard>
          </StaggerItem>
          <StaggerItem>
            <TiltCard className="h-full">
              <GradientBorderCard className="h-full">
                <div className="p-6 text-center">
                  <div className="w-14 h-14 rounded-2xl bg-gradient-to-br from-violet-500 to-purple-500 flex items-center justify-center mx-auto mb-4"><svg className="h-7 w-7 text-white" fill="currentColor" viewBox="0 0 24 24"><path d="M20 4H4c-1.1 0-1.99.9-1.99 2L2 18c0 1.1.9 2 2 2h16c1.1 0 2-.9 2-2V6c0-1.1-.9-2-2-2zm0 4l-8 5-8-5V6l8 5 8-5v2z"/></svg></div>
                  <h3 className="text-lg font-semibold text-white mb-2">Email</h3>
                  <p className="text-zinc-400 text-sm mb-4">For business inquiries</p>
                  <Link href="mailto:hello@d23.ai" className="text-violet-400 hover:text-violet-300 text-sm font-medium">hello@d23.ai</Link>
                </div>
              </GradientBorderCard>
            </TiltCard>
          </StaggerItem>
          <StaggerItem>
            <TiltCard className="h-full">
              <GradientBorderCard className="h-full">
                <div className="p-6 text-center">
                  <div className="w-14 h-14 rounded-2xl bg-gradient-to-br from-fuchsia-500 to-pink-500 flex items-center justify-center mx-auto mb-4"><svg className="h-7 w-7 text-white" fill="currentColor" viewBox="0 0 24 24"><path d="M18.244 2.25h3.308l-7.227 8.26 8.502 11.24H16.17l-5.214-6.817L4.99 21.75H1.68l7.73-8.835L1.254 2.25H8.08l4.713 6.231zm-1.161 17.52h1.833L7.084 4.126H5.117z"/></svg></div>
                  <h3 className="text-lg font-semibold text-white mb-2">Twitter/X</h3>
                  <p className="text-zinc-400 text-sm mb-4">Follow us for updates</p>
                  <Link href="https://twitter.com/D23AI" target="_blank" className="text-violet-400 hover:text-violet-300 text-sm font-medium">@D23AI</Link>
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
            <motion.div animate={{ backgroundPosition: ["0% 50%", "100% 50%", "0% 50%"] }} transition={{ duration: 10, repeat: Infinity, ease: "linear" }} className="absolute inset-0 bg-gradient-to-r from-violet-600 via-fuchsia-600 to-pink-600 bg-[length:200%_auto]" />
            <div className="absolute inset-0 bg-[linear-gradient(rgba(255,255,255,0.1)_1px,transparent_1px),linear-gradient(90deg,rgba(255,255,255,0.1)_1px,transparent_1px)] bg-[size:40px_40px]" />
            <div className="relative z-10 p-12 md:p-20 text-center">
              <motion.h2 initial={{ opacity: 0, y: 20 }} whileInView={{ opacity: 1, y: 0 }} viewport={{ once: true }} className="text-4xl md:text-5xl font-bold text-white mb-6">{t.cta.title}</motion.h2>
              <motion.p initial={{ opacity: 0, y: 20 }} whileInView={{ opacity: 1, y: 0 }} transition={{ delay: 0.1 }} viewport={{ once: true }} className="text-white/80 text-lg mb-10 max-w-xl mx-auto">{t.cta.subtitle}</motion.p>
              <motion.div initial={{ opacity: 0, y: 20 }} whileInView={{ opacity: 1, y: 0 }} transition={{ delay: 0.2 }} viewport={{ once: true }} className="flex flex-wrap justify-center gap-4">
                <MagneticButton><Link href="https://wa.me/918548819349?text=Hey%20D23%20AI%21%20What%20can%20you%20do%3F" target="_blank" className="flex items-center gap-3 px-8 py-4 rounded-full bg-white text-violet-600 font-semibold shadow-2xl hover:bg-zinc-100 transition-colors"><MessageCircle className="h-5 w-5" />{t.cta.button1}</Link></MagneticButton>
                <MagneticButton><Link href="/chat" className="flex items-center gap-3 px-8 py-4 rounded-full border-2 border-white/30 text-white font-semibold hover:bg-white/10 transition-colors">{t.cta.button2}</Link></MagneticButton>
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
              <Image src="/d23ai-logo-v7.svg" alt="D23 AI" width={40} height={40} />
              <div><p className="text-lg font-bold text-white">D23 <GradientText>AI</GradientText></p><p className="text-sm text-zinc-500">{t.footer.tagline}</p></div>
            </div>
            <MagneticButton><Link href="https://wa.me/918548819349?text=Hey%20D23%20AI%21%20What%20can%20you%20do%3F" target="_blank" className="flex items-center gap-2 px-6 py-3 rounded-full bg-gradient-to-r from-violet-600 to-fuchsia-600 text-white font-medium shadow-lg shadow-violet-500/25">{t.footer.button}</Link></MagneticButton>
          </div>
          <div className="relative z-10 flex flex-col md:flex-row items-center justify-between gap-4 mt-8 pt-6 border-t border-white/10">
            <div className="flex items-center gap-4">
              {[{ icon: "X", href: "#" }, { icon: "IG", href: "#" }, { icon: "GH", href: "#" }].map((social) => (
                <Link key={social.icon} href={social.href} className="w-10 h-10 rounded-full bg-white/5 flex items-center justify-center text-zinc-400 hover:text-white hover:bg-white/10 transition-colors text-xs font-bold">{social.icon}</Link>
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

  if (!hydrated) {
    return (
      <div className="min-h-screen bg-black text-white flex items-center justify-center">
        <div className="animate-pulse"><Image src="/d23ai-logo-v7.svg" alt="D23" width={80} height={80} priority /></div>
      </div>
    )
  }

  return (
    <div className="relative min-h-screen bg-black text-white overflow-x-hidden">
      <div className="relative">
        <Header />
      </div>
      <main className="relative">
        <HeroSection />
        <LanguageMarquee />
        <AnimatedDemoShowcase />
        <FeaturesSection />
        <ShowcaseSection />
        <AboutSection />
        <FAQSection />
        <ContactSection />
        <CTASection />
      </main>
      <Footer />
    </div>
  )
}

// ============== MAIN PAGE ==============
export default function V7Page() {
  return (
    <LanguageProvider>
      <PageContent />
    </LanguageProvider>
  )
}
