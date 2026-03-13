import { Github } from "lucide-react"
import { useEffect, useState } from "react"

import { getLatestCommitHash } from "@/lib/github"

interface FooterProps {
  commitHash?: string
}

export function Footer({ commitHash: initialHash }: FooterProps) {
  const [commitHash, setCommitHash] = useState(initialHash || "------")
  const currentYear = new Date().getFullYear()
  const repositoryUrl =
    import.meta.env.VITE_REPOSITORY_URL ??
    "https://github.com/PoyoPoak/MS-PM-POC"

  useEffect(() => {
    async function fetchHash() {
      const hash = await getLatestCommitHash()
      if (hash) {
        setCommitHash(hash)
      }
    }

    void fetchHash()
  }, [])

  return (
    <footer className="border-t border-zinc-300/90 bg-zinc-100/95 px-6 py-4 dark:border-zinc-700/80 dark:bg-zinc-900/95">
      <div className="flex flex-col items-center justify-between gap-4 sm:flex-row">
        <p className="text-muted-foreground text-sm">
          Pacemaker Telemetry Risk Monitoring Platform - {currentYear}
        </p>
        <div className="flex items-center gap-3 text-sm">
          <a
            href={repositoryUrl}
            target="_blank"
            rel="noopener noreferrer"
            className="inline-flex items-center gap-1 font-medium text-muted-foreground transition-colors hover:text-foreground"
          >
            <Github className="h-3.5 w-3.5" aria-hidden="true" />
            Repository
          </a>
          <span className="text-muted-foreground/60">|</span>
          <span className="text-muted-foreground">
            Commit <span className="font-mono">{commitHash}</span>
          </span>
        </div>
      </div>
    </footer>
  )
}
