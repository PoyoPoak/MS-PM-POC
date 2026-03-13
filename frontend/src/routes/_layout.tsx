import { createFileRoute, Outlet, redirect } from "@tanstack/react-router"
import { Activity, Clock3 } from "lucide-react"

import { Footer } from "@/components/Common/Footer"
import AppSidebar from "@/components/Sidebar/AppSidebar"
import {
  SidebarInset,
  SidebarProvider,
  SidebarTrigger,
} from "@/components/ui/sidebar"
import { isLoggedIn } from "@/hooks/useAuth"

export const Route = createFileRoute("/_layout")({
  component: Layout,
  beforeLoad: async () => {
    if (!isLoggedIn()) {
      throw redirect({
        to: "/login",
      })
    }
  },
})

function Layout() {
  const nowLabel = new Date().toLocaleString(undefined, {
    month: "short",
    day: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  })

  return (
    <SidebarProvider>
      <AppSidebar />
      <SidebarInset className="h-svh overflow-hidden">
        <header className="sticky top-0 z-10 flex h-16 shrink-0 items-center gap-2 border-b border-zinc-300/90 bg-zinc-100/95 px-4 shadow-sm backdrop-blur dark:border-zinc-700/80 dark:bg-zinc-900/95">
          <SidebarTrigger className="-ml-1 text-muted-foreground" />
          <div className="ml-2 flex min-w-0 items-center gap-2">
            <Activity className="size-4 text-primary" />
            <div className="min-w-0">
              <p className="truncate text-sm font-semibold">
                Clinical Risk Dashboard
              </p>
              <p className="truncate text-xs text-muted-foreground">
                Pacemaker telemetry monitoring and model operations
              </p>
            </div>
          </div>
          <div className="ml-auto hidden items-center gap-2 rounded-full border border-zinc-300/80 bg-white/85 px-3 py-1 text-xs text-muted-foreground sm:flex dark:border-zinc-700/70 dark:bg-zinc-800/80">
            <Clock3 className="size-3.5" />
            Updated {nowLabel}
          </div>
        </header>
        <main className="flex-1 min-h-0 overflow-auto p-6 md:p-8">
          <div className="w-full">
            <Outlet />
          </div>
        </main>
        <Footer />
      </SidebarInset>
    </SidebarProvider>
  )
}

export default Layout
