"use client"

import { useState } from "react"
import Image from "next/image"
import Link from "next/link"
import { motion } from "framer-motion"
import {
  Sparkles, Zap, Mail, MessageCircle, MapPin, Phone,
  Twitter, Instagram, Linkedin, Github, Send, ArrowRight
} from "lucide-react"
import { cn } from "@/lib/utils"

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
          <Link href="/v5" className="flex items-center gap-2">
            <Image src="/puch/logo.png" alt="D23" width={40} height={40} />
            <span className="text-xl font-bold text-white">D23<GradientText>.AI</GradientText></span>
          </Link>

          <nav className="hidden md:flex items-center gap-8">
            {["Integrations", "MCP", "About"].map((item) => (
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
            href="https://api.whatsapp.com/send/?phone=%2B919934438606&text=Hey+D23%21+What+can+you+do%3F&type=phone_number&app_absent=0"
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

// Contact Info
const contactInfo = [
  {
    icon: Mail,
    label: "Email",
    value: "hello@d23.ai",
    href: "mailto:hello@d23.ai",
    color: "from-violet-500 to-purple-500"
  },
  {
    icon: MessageCircle,
    label: "WhatsApp",
    value: "+91 99344 38606",
    href: "https://api.whatsapp.com/send/?phone=%2B919934438606&text=Hey+D23%21+What+can+you+do%3F&type=phone_number&app_absent=0",
    color: "from-green-500 to-emerald-500"
  },
  {
    icon: MapPin,
    label: "Location",
    value: "Bangalore, India",
    href: "#",
    color: "from-fuchsia-500 to-pink-500"
  }
]

// Social Links
const socialLinks = [
  { icon: Twitter, label: "Twitter", href: "#", color: "hover:bg-blue-500/20 hover:border-blue-500/50" },
  { icon: Instagram, label: "Instagram", href: "#", color: "hover:bg-pink-500/20 hover:border-pink-500/50" },
  { icon: Linkedin, label: "LinkedIn", href: "#", color: "hover:bg-blue-600/20 hover:border-blue-600/50" },
  { icon: Github, label: "GitHub", href: "#", color: "hover:bg-white/20 hover:border-white/50" }
]

export default function ContactPage() {
  const [formData, setFormData] = useState({
    name: "",
    email: "",
    subject: "",
    message: ""
  })
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [submitted, setSubmitted] = useState(false)

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setIsSubmitting(true)

    // Simulate form submission
    await new Promise(resolve => setTimeout(resolve, 1500))

    setSubmitted(true)
    setIsSubmitting(false)
  }

  return (
    <div className="min-h-screen bg-black text-white overflow-x-hidden">
      <Header />

      {/* Background */}
      <div className="fixed inset-0 pointer-events-none">
        <div className="absolute top-1/4 left-1/4 w-[600px] h-[600px] bg-violet-600/10 rounded-full blur-[120px]" />
        <div className="absolute bottom-1/4 right-1/4 w-[500px] h-[500px] bg-fuchsia-600/10 rounded-full blur-[120px]" />
        <div className="absolute inset-0 bg-[linear-gradient(rgba(255,255,255,0.02)_1px,transparent_1px),linear-gradient(90deg,rgba(255,255,255,0.02)_1px,transparent_1px)] bg-[size:50px_50px]" />
      </div>

      <main className="relative z-10 pt-32 pb-20">
        <div className="max-w-6xl mx-auto px-6">
          {/* Hero */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            className="text-center mb-16"
          >
            <div className="inline-flex items-center gap-2 px-4 py-2 rounded-full border border-violet-500/30 bg-violet-500/10 mb-6">
              <MessageCircle className="h-4 w-4 text-violet-400" />
              <span className="text-sm text-violet-300">Get in Touch</span>
            </div>

            <h1 className="text-4xl md:text-5xl lg:text-6xl font-bold text-white mb-4">
              Let's <GradientText>connect</GradientText>
            </h1>
            <p className="text-lg text-zinc-400 max-w-2xl mx-auto">
              Have questions, feedback, or partnership inquiries?
              We'd love to hear from you.
            </p>
          </motion.div>

          <div className="grid lg:grid-cols-2 gap-12">
            {/* Contact Info */}
            <motion.div
              initial={{ opacity: 0, x: -20 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ delay: 0.1 }}
            >
              <h2 className="text-2xl font-bold text-white mb-6">Contact Information</h2>

              <div className="space-y-4 mb-8">
                {contactInfo.map((info, i) => {
                  const Icon = info.icon
                  return (
                    <a
                      key={i}
                      href={info.href}
                      target={info.href.startsWith("http") ? "_blank" : undefined}
                      rel={info.href.startsWith("http") ? "noopener noreferrer" : undefined}
                      className="group flex items-center gap-4 p-4 rounded-xl bg-zinc-900 border border-zinc-800 hover:border-violet-500/30 transition-all"
                    >
                      <div className={cn(
                        "w-12 h-12 rounded-xl flex items-center justify-center bg-gradient-to-br",
                        info.color
                      )}>
                        <Icon className="h-6 w-6 text-white" />
                      </div>
                      <div>
                        <p className="text-xs text-zinc-500 uppercase tracking-wider">{info.label}</p>
                        <p className="text-white font-medium group-hover:text-violet-400 transition-colors">
                          {info.value}
                        </p>
                      </div>
                    </a>
                  )
                })}
              </div>

              {/* Social Links */}
              <h3 className="text-lg font-semibold text-white mb-4">Follow Us</h3>
              <div className="flex gap-3">
                {socialLinks.map((social, i) => {
                  const Icon = social.icon
                  return (
                    <a
                      key={i}
                      href={social.href}
                      target="_blank"
                      rel="noopener noreferrer"
                      className={cn(
                        "w-12 h-12 rounded-xl bg-zinc-900 border border-zinc-800 flex items-center justify-center text-zinc-400 hover:text-white transition-all",
                        social.color
                      )}
                      title={social.label}
                    >
                      <Icon className="h-5 w-5" />
                    </a>
                  )
                })}
              </div>

              {/* Quick CTA */}
              <div className="mt-8 p-6 rounded-xl bg-gradient-to-r from-violet-500/10 to-fuchsia-500/10 border border-violet-500/20">
                <h3 className="font-semibold text-white mb-2">Prefer WhatsApp?</h3>
                <p className="text-sm text-zinc-400 mb-4">
                  Chat with D23 AI directly on WhatsApp for instant responses.
                </p>
                <Link
                  href="https://api.whatsapp.com/send/?phone=%2B919934438606&text=Hey+D23%21+What+can+you+do%3F&type=phone_number&app_absent=0"
                  target="_blank"
                  className="inline-flex items-center gap-2 px-5 py-2.5 rounded-full bg-gradient-to-r from-violet-600 to-fuchsia-600 text-white text-sm font-medium"
                >
                  <MessageCircle className="h-4 w-4" />
                  Chat on WhatsApp
                  <ArrowRight className="h-4 w-4" />
                </Link>
              </div>
            </motion.div>

            {/* Contact Form */}
            <motion.div
              initial={{ opacity: 0, x: 20 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ delay: 0.2 }}
            >
              <div className="relative p-[1px] rounded-2xl overflow-hidden">
                <div className="absolute inset-0 bg-gradient-to-r from-violet-500 to-fuchsia-500 opacity-50" />
                <div className="relative bg-zinc-900 rounded-2xl p-8">
                  {submitted ? (
                    <div className="text-center py-12">
                      <div className="w-16 h-16 rounded-full bg-gradient-to-r from-green-500 to-emerald-500 flex items-center justify-center mx-auto mb-4">
                        <Sparkles className="h-8 w-8 text-white" />
                      </div>
                      <h3 className="text-2xl font-bold text-white mb-2">Message Sent!</h3>
                      <p className="text-zinc-400 mb-6">We'll get back to you as soon as possible.</p>
                      <button
                        onClick={() => {
                          setSubmitted(false)
                          setFormData({ name: "", email: "", subject: "", message: "" })
                        }}
                        className="text-violet-400 hover:text-violet-300 text-sm"
                      >
                        Send another message
                      </button>
                    </div>
                  ) : (
                    <>
                      <h2 className="text-2xl font-bold text-white mb-6">Send us a message</h2>

                      <form onSubmit={handleSubmit} className="space-y-5">
                        <div>
                          <label className="block text-sm text-zinc-400 mb-2">Name</label>
                          <input
                            type="text"
                            value={formData.name}
                            onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                            required
                            className="w-full px-4 py-3 rounded-xl bg-zinc-800 border border-zinc-700 text-white placeholder:text-zinc-500 focus:outline-none focus:border-violet-500 transition-colors"
                            placeholder="Your name"
                          />
                        </div>

                        <div>
                          <label className="block text-sm text-zinc-400 mb-2">Email</label>
                          <input
                            type="email"
                            value={formData.email}
                            onChange={(e) => setFormData({ ...formData, email: e.target.value })}
                            required
                            className="w-full px-4 py-3 rounded-xl bg-zinc-800 border border-zinc-700 text-white placeholder:text-zinc-500 focus:outline-none focus:border-violet-500 transition-colors"
                            placeholder="you@example.com"
                          />
                        </div>

                        <div>
                          <label className="block text-sm text-zinc-400 mb-2">Subject</label>
                          <input
                            type="text"
                            value={formData.subject}
                            onChange={(e) => setFormData({ ...formData, subject: e.target.value })}
                            required
                            className="w-full px-4 py-3 rounded-xl bg-zinc-800 border border-zinc-700 text-white placeholder:text-zinc-500 focus:outline-none focus:border-violet-500 transition-colors"
                            placeholder="What's this about?"
                          />
                        </div>

                        <div>
                          <label className="block text-sm text-zinc-400 mb-2">Message</label>
                          <textarea
                            value={formData.message}
                            onChange={(e) => setFormData({ ...formData, message: e.target.value })}
                            required
                            rows={5}
                            className="w-full px-4 py-3 rounded-xl bg-zinc-800 border border-zinc-700 text-white placeholder:text-zinc-500 focus:outline-none focus:border-violet-500 transition-colors resize-none"
                            placeholder="Tell us more..."
                          />
                        </div>

                        <button
                          type="submit"
                          disabled={isSubmitting}
                          className={cn(
                            "w-full flex items-center justify-center gap-2 px-6 py-4 rounded-xl font-semibold transition-all",
                            isSubmitting
                              ? "bg-zinc-800 text-zinc-500 cursor-not-allowed"
                              : "bg-gradient-to-r from-violet-600 to-fuchsia-600 text-white hover:shadow-lg hover:shadow-violet-500/25"
                          )}
                        >
                          {isSubmitting ? (
                            <>
                              <div className="w-5 h-5 border-2 border-zinc-500 border-t-transparent rounded-full animate-spin" />
                              Sending...
                            </>
                          ) : (
                            <>
                              <Send className="h-5 w-5" />
                              Send Message
                            </>
                          )}
                        </button>
                      </form>
                    </>
                  )}
                </div>
              </div>
            </motion.div>
          </div>
        </div>
      </main>

      {/* Footer */}
      <footer className="relative z-10 py-12 px-6 border-t border-white/10">
        <div className="max-w-6xl mx-auto">
          <div className="flex flex-col md:flex-row items-center justify-between gap-6">
            <div className="flex items-center gap-3">
              <Image src="/puch/logo.png" alt="D23 AI" width={40} height={40} />
              <div>
                <p className="text-lg font-bold text-white">D23<GradientText>.AI</GradientText></p>
                <p className="text-sm text-zinc-500">WhatsApp-native AI for Bharat.</p>
              </div>
            </div>
            <p className="text-sm text-zinc-500">© 2025 D23 AI. Built for every Indian language.</p>
          </div>
        </div>
      </footer>
    </div>
  )
}
