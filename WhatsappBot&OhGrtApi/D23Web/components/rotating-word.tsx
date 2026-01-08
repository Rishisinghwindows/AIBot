"use client"

import { useEffect, useState } from "react"

import { cn } from "@/lib/utils"

type RotatingWordProps = {
  words: string[]
  interval?: number
  className?: string
}

export function RotatingWord({ words, interval = 1600, className }: RotatingWordProps) {
  const [index, setIndex] = useState(0)

  useEffect(() => {
    if (words.length <= 1) return
    const id = setInterval(() => {
      setIndex((prev) => (prev + 1) % words.length)
    }, interval)
    return () => clearInterval(id)
  }, [interval, words.length])

  return (
    <span
      className={cn(
        "inline-flex min-w-[5ch] items-center justify-start text-primary transition-all duration-500",
        className,
      )}
    >
      {words[index]}
    </span>
  )
}
