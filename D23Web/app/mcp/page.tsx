"use client"

import { useState } from "react"
import Image from "next/image"
import Link from "next/link"
import { motion } from "framer-motion"
import {
  Sparkles, Zap, Server, Terminal, Code, CheckCircle2,
  XCircle, Play, HelpCircle, MessageCircle, ArrowRight, Copy, Check
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

// Code Block Component
function CodeBlock({ code, language = "bash" }: { code: string; language?: string }) {
  const [copied, setCopied] = useState(false)

  const handleCopy = () => {
    navigator.clipboard.writeText(code)
    setCopied(true)
    setTimeout(() => setCopied(false), 2000)
  }

  return (
    <div className="relative group">
      <div className="bg-zinc-900 border border-zinc-800 rounded-xl overflow-hidden">
        <div className="flex items-center justify-between px-4 py-2 border-b border-zinc-800 bg-zinc-900/50">
          <span className="text-xs text-zinc-500">{language}</span>
          <button
            onClick={handleCopy}
            className="flex items-center gap-1 text-xs text-zinc-500 hover:text-white transition-colors"
          >
            {copied ? <Check className="w-3 h-3" /> : <Copy className="w-3 h-3" />}
            {copied ? "Copied!" : "Copy"}
          </button>
        </div>
        <pre className="p-4 overflow-x-auto">
          <code className="text-sm text-violet-300 font-mono">{code}</code>
        </pre>
      </div>
    </div>
  )
}

// Header Component
function Header() {
  return (
    <header className="fixed top-0 left-0 right-0 z-50 bg-black/70 backdrop-blur-xl border-b border-white/10">
      <div className="max-w-7xl mx-auto px-6 py-4">
        <div className="flex items-center justify-between">
          <Link href="/" className="flex items-center gap-2">
            <Image src="/d23ai-logo-v7.svg" alt="D23" width={40} height={40} />
          </Link>

          <nav className="hidden md:flex items-center gap-8">
            {["Integrations", "About", "Contact"].map((item) => (
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

// MCP Data
const mcpFeatures = {
  supported: [
    "stdio transport for local servers",
    "SSE transport for remote servers",
    "Tool calls from MCP servers",
    "Sampling (prompts) from MCP servers"
  ],
  notSupported: [
    "Resources (files, data) from MCP servers",
    "MCP server management UI"
  ]
}

const commands = [
  {
    name: "Add MCP Server",
    command: "/mcp add <name> <command> [args...]",
    description: "Register a new MCP server with D23",
    example: "/mcp add filesystem npx -y @anthropic/mcp-filesystem /home/user"
  },
  {
    name: "Remove MCP Server",
    command: "/mcp remove <name>",
    description: "Unregister an MCP server",
    example: "/mcp remove filesystem"
  },
  {
    name: "List MCP Servers",
    command: "/mcp list",
    description: "Show all registered MCP servers and their status",
    example: "/mcp list"
  }
]

const requirements = [
  {
    title: "Node.js Environment",
    description: "MCP servers require Node.js 18+ installed on your system.",
    icon: Server
  },
  {
    title: "Valid MCP Server",
    description: "The server must implement the MCP protocol correctly.",
    icon: CheckCircle2
  },
  {
    title: "Network Access",
    description: "For SSE transport, ensure the server URL is accessible.",
    icon: Terminal
  }
]

export default function MCPPage() {
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
        <div className="max-w-4xl mx-auto px-6">
          {/* Hero */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            className="mb-16"
          >
            <div className="inline-flex items-center gap-2 px-4 py-2 rounded-full border border-violet-500/30 bg-violet-500/10 mb-6">
              <Server className="h-4 w-4 text-violet-400" />
              <span className="text-sm text-violet-300">MCP Integration</span>
            </div>

            <h1 className="text-4xl md:text-5xl font-bold text-white mb-4">
              Model Context Protocol
            </h1>
            <p className="text-lg text-zinc-400 mb-8">
              Extend <span className="text-white font-semibold">D23 AI</span> with custom tools and capabilities using the Model Context Protocol.
            </p>

            {/* Info Box */}
            <div className="relative p-[1px] rounded-xl overflow-hidden">
              <div className="absolute inset-0 bg-gradient-to-r from-violet-500 to-fuchsia-500" />
              <div className="relative bg-zinc-900 rounded-xl p-6">
                <div className="flex gap-4">
                  <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-full bg-gradient-to-br from-violet-500 to-fuchsia-500">
                    <Sparkles className="h-5 w-5 text-white" />
                  </div>
                  <div>
                    <h3 className="font-semibold text-white mb-2">What is MCP?</h3>
                    <p className="text-sm text-zinc-400">
                      The Model Context Protocol (MCP) allows you to connect external tools, databases, and services to D23 AI.
                      This enables D23 to access your files, query databases, call APIs, and more.
                    </p>
                  </div>
                </div>
              </div>
            </div>
          </motion.div>

          {/* Supported Features */}
          <motion.section
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            className="mb-16"
          >
            <h2 className="text-2xl font-bold text-white mb-6">Supported Features</h2>
            <div className="grid md:grid-cols-2 gap-6">
              <div className="bg-zinc-900 border border-zinc-800 rounded-xl p-6">
                <h3 className="flex items-center gap-2 text-green-400 font-semibold mb-4">
                  <CheckCircle2 className="h-5 w-5" />
                  Supported
                </h3>
                <ul className="space-y-3">
                  {mcpFeatures.supported.map((item, i) => (
                    <li key={i} className="flex items-start gap-2 text-sm text-zinc-300">
                      <CheckCircle2 className="h-4 w-4 text-green-500 mt-0.5 shrink-0" />
                      {item}
                    </li>
                  ))}
                </ul>
              </div>
              <div className="bg-zinc-900 border border-zinc-800 rounded-xl p-6">
                <h3 className="flex items-center gap-2 text-red-400 font-semibold mb-4">
                  <XCircle className="h-5 w-5" />
                  Not Yet Supported
                </h3>
                <ul className="space-y-3">
                  {mcpFeatures.notSupported.map((item, i) => (
                    <li key={i} className="flex items-start gap-2 text-sm text-zinc-400">
                      <XCircle className="h-4 w-4 text-red-500 mt-0.5 shrink-0" />
                      {item}
                    </li>
                  ))}
                </ul>
              </div>
            </div>
          </motion.section>

          {/* Getting Started */}
          <motion.section
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            className="mb-16"
          >
            <h2 className="text-2xl font-bold text-white mb-6">Getting Started</h2>

            <div className="space-y-6">
              <div className="bg-zinc-900 border border-zinc-800 rounded-xl p-6">
                <div className="flex items-start gap-4">
                  <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-gradient-to-br from-violet-500 to-fuchsia-500 text-white font-semibold">
                    1
                  </div>
                  <div className="flex-1">
                    <h3 className="font-semibold text-white mb-2">Install an MCP Server</h3>
                    <p className="text-sm text-zinc-400 mb-4">
                      First, install an MCP server package. For example, the filesystem server:
                    </p>
                    <CodeBlock code="npm install -g @anthropic/mcp-filesystem" />
                  </div>
                </div>
              </div>

              <div className="bg-zinc-900 border border-zinc-800 rounded-xl p-6">
                <div className="flex items-start gap-4">
                  <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-gradient-to-br from-violet-500 to-fuchsia-500 text-white font-semibold">
                    2
                  </div>
                  <div className="flex-1">
                    <h3 className="font-semibold text-white mb-2">Register with D23</h3>
                    <p className="text-sm text-zinc-400 mb-4">
                      Add the MCP server to D23 using the /mcp command:
                    </p>
                    <CodeBlock code="/mcp add filesystem npx @anthropic/mcp-filesystem /path/to/folder" />
                  </div>
                </div>
              </div>

              <div className="bg-zinc-900 border border-zinc-800 rounded-xl p-6">
                <div className="flex items-start gap-4">
                  <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-gradient-to-br from-violet-500 to-fuchsia-500 text-white font-semibold">
                    3
                  </div>
                  <div className="flex-1">
                    <h3 className="font-semibold text-white mb-2">Start Using</h3>
                    <p className="text-sm text-zinc-400">
                      D23 AI will automatically detect and use the tools provided by your MCP server.
                      Just ask naturally, e.g., "List all files in my documents folder".
                    </p>
                  </div>
                </div>
              </div>
            </div>
          </motion.section>

          {/* Command Reference */}
          <motion.section
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            className="mb-16"
          >
            <h2 className="text-2xl font-bold text-white mb-6">Command Reference</h2>

            <div className="space-y-4">
              {commands.map((cmd, i) => (
                <div key={i} className="bg-zinc-900 border border-zinc-800 rounded-xl p-6">
                  <h3 className="font-semibold text-white mb-2">{cmd.name}</h3>
                  <CodeBlock code={cmd.command} language="command" />
                  <p className="text-sm text-zinc-400 mt-3 mb-2">{cmd.description}</p>
                  <p className="text-xs text-zinc-500">
                    <span className="text-violet-400">Example:</span> {cmd.example}
                  </p>
                </div>
              ))}
            </div>
          </motion.section>

          {/* Requirements */}
          <motion.section
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            className="mb-16"
          >
            <h2 className="text-2xl font-bold text-white mb-6">Server Requirements</h2>

            <div className="grid md:grid-cols-3 gap-4">
              {requirements.map((req, i) => {
                const Icon = req.icon
                return (
                  <div key={i} className="bg-zinc-900 border border-zinc-800 rounded-xl p-6">
                    <div className="w-12 h-12 rounded-xl bg-gradient-to-br from-violet-500/20 to-fuchsia-500/20 flex items-center justify-center mb-4 border border-violet-500/20">
                      <Icon className="h-6 w-6 text-violet-400" />
                    </div>
                    <h3 className="font-semibold text-white mb-2">{req.title}</h3>
                    <p className="text-sm text-zinc-400">{req.description}</p>
                  </div>
                )
              })}
            </div>
          </motion.section>

          {/* Help Section */}
          <motion.section
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
          >
            <div className="relative rounded-2xl overflow-hidden">
              <div className="absolute inset-0 bg-gradient-to-r from-violet-600 via-fuchsia-600 to-pink-600" />
              <div className="absolute inset-0 bg-[linear-gradient(rgba(255,255,255,0.1)_1px,transparent_1px),linear-gradient(90deg,rgba(255,255,255,0.1)_1px,transparent_1px)] bg-[size:40px_40px]" />

              <div className="relative z-10 p-8 md:p-12 text-center">
                <HelpCircle className="h-12 w-12 text-white/80 mx-auto mb-4" />
                <h2 className="text-2xl font-bold text-white mb-3">Need Help?</h2>
                <p className="text-white/80 mb-6 max-w-md mx-auto">
                  Have questions about MCP integration? Join our community or reach out directly.
                </p>
                <Link
                  href="/contact"
                  className="inline-flex items-center gap-2 px-6 py-3 rounded-full bg-white text-violet-600 font-semibold hover:bg-zinc-100 transition-colors"
                >
                  <MessageCircle className="h-5 w-5" />
                  Contact Us
                </Link>
              </div>
            </div>
          </motion.section>
        </div>
      </main>

      {/* Footer */}
      <footer className="relative z-10 py-12 px-6 border-t border-white/10">
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
    </div>
  )
}
