"use client"

import { useState } from "react"
import { ChevronDown } from "lucide-react"

interface SidebarItem {
  label: string
  href: string
}

interface SidebarSection {
  title: string
  items: SidebarItem[]
}

interface MCPSidebarProps {
  sections: SidebarSection[]
}

export function MCPSidebar({ sections }: MCPSidebarProps) {
  const [openSections, setOpenSections] = useState<Record<string, boolean>>({
    "Getting Started": true,
    "Command Reference": true,
  })

  const toggleSection = (title: string) => {
    setOpenSections((prev) => ({
      ...prev,
      [title]: !prev[title],
    }))
  }

  const handleClick = (href: string) => {
    const element = document.querySelector(href)
    if (element) {
      element.scrollIntoView({ behavior: "smooth", block: "start" })
    }
  }

  return (
    <aside className="w-64 shrink-0 border-r bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60">
      <nav className="sticky top-24 h-[calc(100vh-6rem)] overflow-y-auto px-4 py-6">
        <div className="space-y-4">
          {sections.map((section) => (
            <div key={section.title}>
              <button
                onClick={() => toggleSection(section.title)}
                className="flex w-full items-center justify-between text-sm font-semibold text-foreground hover:text-brand transition-colors"
              >
                {section.title}
                {section.items.length > 0 && (
                  <ChevronDown
                    className={`h-4 w-4 transition-transform ${openSections[section.title] ? "rotate-180" : ""}`}
                  />
                )}
              </button>
              {openSections[section.title] && section.items.length > 0 && (
                <ul className="mt-2 space-y-2 pl-4">
                  {section.items.map((item) => (
                    <li key={item.href}>
                      <button
                        onClick={() => handleClick(item.href)}
                        className="text-sm text-muted-foreground hover:text-brand transition-colors text-left w-full"
                      >
                        {item.label}
                      </button>
                    </li>
                  ))}
                </ul>
              )}
            </div>
          ))}
        </div>
      </nav>
    </aside>
  )
}
