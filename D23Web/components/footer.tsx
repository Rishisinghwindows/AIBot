import type React from "react"
import Image from "next/image"
import Link from "next/link"
import { Mail, Github, Instagram } from "lucide-react"

import { Button } from "@/components/ui/button"
import footerData from "@/data/footer.json"

const iconMap = {
  twitter: (props: React.SVGProps<SVGSVGElement>) => (
    <svg fill="currentColor" viewBox="0 0 24 24" {...props}>
      <path d="M18.244 2.25h3.308l-7.227 8.26 8.502 11.24H16.17l-5.214-6.817L4.99 21.75H1.68l7.73-8.835L1.254 2.25H8.08l4.713 6.231zm-1.161 17.52h1.833L7.084 4.126H5.117z" />
    </svg>
  ),
  instagram: Instagram,
  github: Github,
  mail: Mail,
}

export function Footer() {
  return (
    <footer className="mt-20 border-t border-border/60 bg-white">
      <div className="mx-auto max-w-6xl space-y-6 px-4 py-12">
        <div className="flex flex-col items-start gap-6 md:flex-row md:items-center md:justify-between">
          <div className="flex items-center gap-3">
            <Image src="/puch/logo.png" alt="D23 AI" width={40} height={40} className="h-10 w-10" />
            <div>
              <p className="text-lg font-semibold text-foreground">{footerData.logo}</p>
              <p className="text-sm text-foreground/60">WhatsApp-native AI for Bharat.</p>
            </div>
          </div>
          <Button
            asChild
            className="gap-2 rounded-md bg-primary px-4 py-2 text-sm text-white shadow-md transition hover:-translate-y-0.5 hover:bg-primary/90"
          >
            <Link href="https://api.whatsapp.com/send/?phone=%2B919934438606&text=Hey+D23%21+What+can+you+do%3F&type=phone_number&app_absent=0" target="_blank" rel="noreferrer">
              <svg height="1em" preserveAspectRatio="xMidYMid" viewBox="0 0 256 259" width="1em" xmlns="http://www.w3.org/2000/svg" className="h-4 w-4">
                <path
                  d="m67.663 221.823 4.185 2.093c17.44 10.463 36.971 15.346 56.503 15.346 61.385 0 111.609-50.224 111.609-111.609 0-29.297-11.859-57.897-32.785-78.824-20.927-20.927-48.83-32.785-78.824-32.785-61.385 0-111.61 50.224-110.912 112.307 0 20.926 6.278 41.156 16.741 58.594l2.79 4.186-11.16 41.156 41.853-10.464Z"
                  fill="#00E676"
                ></path>
                <path
                  d="M219.033 37.668C195.316 13.254 162.531 0 129.048 0 57.898 0 .698 57.897 1.395 128.35c0 22.322 6.278 43.947 16.742 63.478L0 258.096l67.663-17.439c18.834 10.464 39.76 15.347 60.688 15.347 70.453 0 127.653-57.898 127.653-128.35 0-34.181-13.254-66.269-36.97-89.986ZM129.048 234.38c-18.834 0-37.668-4.882-53.712-14.648l-4.185-2.093-40.458 10.463 10.463-39.76-2.79-4.186C7.673 134.63 22.322 69.058 72.546 38.365c50.224-30.692 115.097-16.043 145.79 34.181 30.692 50.224 16.043 115.097-34.18 145.79-16.045 10.463-35.576 16.043-55.108 16.043Zm61.385-77.428-7.673-3.488s-11.16-4.883-18.136-8.371c-.698 0-1.395-.698-2.093-.698-2.093 0-3.488.698-4.883 1.396 0 0-.697.697-10.463 11.858-.698 1.395-2.093 2.093-3.488 2.093h-.698c-.697 0-2.092-.698-2.79-1.395l-3.488-1.395c-7.673-3.488-14.648-7.674-20.229-13.254-1.395-1.395-3.488-2.79-4.883-4.185-4.883-4.883-9.766-10.464-13.253-16.742l-.698-1.395c-.697-.698-.697-1.395-1.395-2.79 0-1.395 0-2.79.698-3.488 0 0 2.79-3.488 4.882-5.58 1.396-1.396 2.093-3.488 3.488-4.883 1.395-2.093 2.093-4.883 1.395-6.976-.697-3.488-9.068-22.322-11.16-26.507-1.396-2.093-2.79-2.79-4.883-3.488H83.01c-1.396 0-2.79.698-4.186.698l-.698.697c-1.395.698-2.79 2.093-4.185 2.79-1.395 1.396-2.093 2.79-3.488 4.186-4.883 6.278-7.673 13.951-7.673 21.624 0 5.58 1.395 11.161 3.488 16.044l.698 2.093c6.278 13.253 14.648 25.112 25.81 35.575l2.79 2.79c2.092 2.093 4.185 3.488 5.58 5.58 14.649 12.557 31.39 21.625 50.224 26.508 2.093.697 4.883.697 6.976 1.395h6.975c3.488 0 7.673-1.395 10.464-2.79 2.092-1.395 3.487-1.395 4.882-2.79l1.396-1.396c1.395-1.395 2.79-2.092 4.185-3.487 1.395-1.395 2.79-2.79 3.488-4.186 1.395-2.79 2.092-6.278 2.79-9.765v-4.883s-.698-.698-2.093-1.395Z"
                  fill="#FFF"
                ></path>
              </svg>
              Talk to D23 AI
            </Link>
          </Button>
        </div>
        <div className="flex flex-col gap-4 border-t border-border/50 pt-6 md:flex-row md:items-center md:justify-between">
          <div className="flex items-center gap-4">
            {footerData.socialLinks.map((link) => {
              const Icon = iconMap[link.icon as keyof typeof iconMap]
              return (
                <Link
                  key={link.platform}
                  href={link.href}
                  className="text-muted-foreground transition-colors hover:text-foreground"
                  target="_blank"
                  rel="noopener noreferrer"
                >
                  <Icon className="h-5 w-5" />
                </Link>
              )
            })}
          </div>
          <p className="text-sm text-muted-foreground">{footerData.copyright}</p>
        </div>
      </div>
    </footer>
  )
}
