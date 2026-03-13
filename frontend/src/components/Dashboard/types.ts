import type { LucideIcon } from "lucide-react"

export type DashboardPatientRow = {
  patientId: number
  riskScore: number | null
  leadImpedance: number
  captureThreshold: number
  batteryVoltage: number
  leadImpedanceRollingMean3d: number
  leadImpedanceRollingMean7d: number
  captureThresholdRollingMean3d: number
  captureThresholdRollingMean7d: number
  leadImpedanceDeltaPerDay3d: number
  leadImpedanceDeltaPerDay7d: number
  captureThresholdDeltaPerDay3d: number
  captureThresholdDeltaPerDay7d: number
  lastUpdate: string
  alertsSent: boolean
}

export type ActiveModelMetrics = {
  accuracy: number
  precision: number
  recall: number
  f1: number
  oobScore: number
}

export type ActiveModel = {
  id: string
  version: string
  trainingDate: string
  datasetSize: number
  metrics: ActiveModelMetrics
}

export type RecentModel = {
  id: string
  version: string
  trainingDate: string
  f1: number
}

export type QuickStat = {
  title: string
  value: string
  helper: string
  icon: LucideIcon
}
