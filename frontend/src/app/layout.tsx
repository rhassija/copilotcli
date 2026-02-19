import type { Metadata } from 'next'
import './globals.css'

export const metadata: Metadata = {
  title: 'Copilot CLI - Web UI',
  description: 'Modern web interface for GitHub Copilot CLI',
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en">
      <body className="antialiased">{children}</body>
    </html>
  )
}
