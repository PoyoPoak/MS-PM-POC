export function Footer() {
  const currentYear = new Date().getFullYear()
  const repositoryUrl =
    import.meta.env.VITE_REPOSITORY_URL ??
    "https://github.com/PoyoPoak/MS-PM-POC"
  const rawCommitHash =
    import.meta.env.VITE_GIT_SHA ??
    import.meta.env.VITE_COMMIT_HASH ??
    "local-dev"
  const commitHash = rawCommitHash.slice(0, 7)

  return (
    <footer className="border-t py-4 px-6">
      <div className="flex flex-col items-center justify-between gap-4 sm:flex-row">
        <p className="text-muted-foreground text-sm">
          Pacemaker Telemetry Risk Monitoring Platform - {currentYear}
        </p>
        <div className="flex items-center gap-3 text-sm">
          <a
            href={repositoryUrl}
            target="_blank"
            rel="noopener noreferrer"
            className="font-medium text-muted-foreground transition-colors hover:text-foreground"
          >
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
