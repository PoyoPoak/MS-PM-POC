import type { QuickStat } from "./types"

interface QuickStatsCardsProps {
  stats: QuickStat[]
}

export function QuickStatsCards({ stats }: QuickStatsCardsProps) {
  return (
    <div className="grid grid-cols-2 gap-3">
      {stats.map((stat) => (
        <div
          key={stat.title}
          className="h-full rounded-xl border bg-card px-5 py-4 shadow-sm transition-colors hover:bg-muted/20"
        >
          <div className="mb-2 flex items-center justify-between">
            <p className="text-xs uppercase tracking-wide text-muted-foreground">
              {stat.title}
            </p>
            <stat.icon className="size-4 text-muted-foreground" />
          </div>
          <p className="text-2xl font-semibold tracking-tight">{stat.value}</p>
        </div>
      ))}
    </div>
  )
}
