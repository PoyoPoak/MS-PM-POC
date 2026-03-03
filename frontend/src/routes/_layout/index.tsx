import { createFileRoute } from "@tanstack/react-router"

import PacemakerRiskDashboard from "@/components/PacemakerDashboard/PacemakerRiskDashboard"

export const Route = createFileRoute("/_layout/")({
  component: Dashboard,
  head: () => ({
    meta: [
      {
        title: "Pacemaker Risk Dashboard",
      },
    ],
  }),
})

function Dashboard() {
  return <PacemakerRiskDashboard />
}
