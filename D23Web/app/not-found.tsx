import Link from 'next/link'
import { Button } from '@/components/ui/button'
import { Home, Search, MessageCircle } from 'lucide-react'

/**
 * Custom 404 Not Found page.
 * Displayed when a user navigates to a non-existent route.
 */
export default function NotFound() {
  return (
    <div className="min-h-screen flex items-center justify-center bg-background px-4">
      <div className="max-w-md w-full text-center space-y-6">
        {/* 404 Illustration */}
        <div className="space-y-2">
          <h1 className="text-8xl font-bold text-primary/20">404</h1>
          <h2 className="text-2xl font-bold text-foreground">
            Page Not Found
          </h2>
          <p className="text-muted-foreground">
            The page you&apos;re looking for doesn&apos;t exist or has been moved.
          </p>
        </div>

        {/* Quick Links */}
        <div className="flex flex-col sm:flex-row gap-3 justify-center">
          <Button asChild variant="default" className="gap-2">
            <Link href="/">
              <Home className="h-4 w-4" />
              Go Home
            </Link>
          </Button>
          <Button asChild variant="outline" className="gap-2">
            <Link href="/chat">
              <MessageCircle className="h-4 w-4" />
              Start Chat
            </Link>
          </Button>
        </div>

        {/* Helpful Links */}
        <div className="pt-6 border-t border-border">
          <p className="text-sm text-muted-foreground mb-4">
            Here are some helpful links:
          </p>
          <div className="flex flex-wrap gap-2 justify-center text-sm">
            <Link href="/about" className="text-primary hover:underline">
              About Us
            </Link>
            <span className="text-muted-foreground">|</span>
            <Link href="/integrations" className="text-primary hover:underline">
              Integrations
            </Link>
            <span className="text-muted-foreground">|</span>
            <Link href="/contact" className="text-primary hover:underline">
              Contact
            </Link>
            <span className="text-muted-foreground">|</span>
            <Link href="/mcp" className="text-primary hover:underline">
              MCP Docs
            </Link>
          </div>
        </div>
      </div>
    </div>
  )
}
