import { createFileRoute } from "@tanstack/react-router"

import { DashboardPage } from "@/components/Dashboard/DashboardPage"

export const Route = createFileRoute("/_layout/")({
  component: Dashboard,
  head: () => ({
    meta: [
      {
        title: "Dashboard - Pacemaker Telemetry",
      },
    ],
  }),
})

function Dashboard() {
  return <DashboardPage />
}
