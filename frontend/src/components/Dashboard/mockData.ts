import type { ActiveModel, DashboardPatientRow, RecentModel } from "./types"

export const MOCK_ACTIVE_MODEL: ActiveModel = {
  id: "model-current-1",
  version: "v1.8.3",
  trainingDate: "2026-03-05T10:15:00Z",
  datasetSize: 12348,
  metrics: {
    accuracy: 0.941,
    precision: 0.917,
    recall: 0.902,
    f1: 0.909,
    oobScore: 0.934,
  },
}

export const MOCK_RECENT_MODELS: RecentModel[] = [
  {
    id: "model-v1-8-3",
    version: "v1.8.3",
    trainingDate: "2026-03-05T10:15:00Z",
    f1: 0.909,
  },
  {
    id: "model-v1-8-2",
    version: "v1.8.2",
    trainingDate: "2026-02-26T15:42:00Z",
    f1: 0.897,
  },
  {
    id: "model-v1-8-1",
    version: "v1.8.1",
    trainingDate: "2026-02-18T09:04:00Z",
    f1: 0.884,
  },
]

const PATIENT_ID_START = 10001
const PATIENT_COUNT = 100
const LAST_UPDATE_BASE_TIME_UTC = Date.UTC(2026, 2, 12, 18, 30, 0)

function seededUnit(seed: number, salt: number) {
  const value = Math.sin(seed * 12.9898 + salt * 78.233) * 43758.5453
  return value - Math.floor(value)
}

function toFixedNumber(value: number, decimals: number) {
  return Number(value.toFixed(decimals))
}

function buildPatientRow(patientId: number): DashboardPatientRow {
  const volatility = seededUnit(patientId, 1)
  const trend = seededUnit(patientId, 2)
  const noise = seededUnit(patientId, 3)
  const batteryDrift = seededUnit(patientId, 4)

  const riskScore = toFixedNumber(
    0.08 + 0.9 * (0.55 * volatility + 0.35 * trend + 0.1 * noise),
    2,
  )
  const leadImpedance = Math.round(780 + riskScore * 760 + noise * 140)
  const captureThreshold = toFixedNumber(0.6 + riskScore * 2 + trend * 0.35, 2)
  const batteryVoltage = toFixedNumber(
    Math.max(2.55, 3.15 - riskScore * 0.55 - batteryDrift * 0.07),
    2,
  )

  const impedanceBias3d = (seededUnit(patientId, 7) - 0.5) * 0.06
  const impedanceBias7d = (seededUnit(patientId, 8) - 0.5) * 0.04
  const thresholdBias3d = (seededUnit(patientId, 9) - 0.5) * 0.08
  const thresholdBias7d = (seededUnit(patientId, 10) - 0.5) * 0.06

  const leadImpedanceRollingMean3d = toFixedNumber(
    leadImpedance * (1 + impedanceBias3d),
    1,
  )
  const leadImpedanceRollingMean7d = toFixedNumber(
    leadImpedance * (1 + impedanceBias7d),
    1,
  )
  const captureThresholdRollingMean3d = toFixedNumber(
    captureThreshold * (1 + thresholdBias3d),
    3,
  )
  const captureThresholdRollingMean7d = toFixedNumber(
    captureThreshold * (1 + thresholdBias7d),
    3,
  )

  const leadImpedanceDeltaPerDay3d = toFixedNumber(
    ((leadImpedanceRollingMean3d - leadImpedanceRollingMean7d) / 4) *
      (0.9 + riskScore * 0.3),
    2,
  )
  const leadImpedanceDeltaPerDay7d = toFixedNumber(
    ((leadImpedance - leadImpedanceRollingMean7d) / 7) * (0.85 + trend * 0.3),
    2,
  )
  const captureThresholdDeltaPerDay3d = toFixedNumber(
    ((captureThresholdRollingMean3d - captureThresholdRollingMean7d) / 4) *
      (0.85 + riskScore * 0.35),
    3,
  )
  const captureThresholdDeltaPerDay7d = toFixedNumber(
    ((captureThreshold - captureThresholdRollingMean7d) / 7) *
      (0.85 + noise * 0.35),
    3,
  )

  const minutesAgo = Math.floor(6 + seededUnit(patientId, 5) * 60 * 24 * 3)
  const lastUpdate = new Date(
    LAST_UPDATE_BASE_TIME_UTC - minutesAgo * 60_000,
  ).toISOString()

  const alertsSent =
    riskScore >= 0.7 || (riskScore >= 0.55 && seededUnit(patientId, 6) > 0.62)

  return {
    patientId,
    riskScore,
    leadImpedance,
    captureThreshold,
    batteryVoltage,
    leadImpedanceRollingMean3d,
    leadImpedanceRollingMean7d,
    captureThresholdRollingMean3d,
    captureThresholdRollingMean7d,
    leadImpedanceDeltaPerDay3d,
    leadImpedanceDeltaPerDay7d,
    captureThresholdDeltaPerDay3d,
    captureThresholdDeltaPerDay7d,
    lastUpdate,
    alertsSent,
  }
}

export const MOCK_PATIENTS: DashboardPatientRow[] = Array.from(
  { length: PATIENT_COUNT },
  (_, index) => buildPatientRow(PATIENT_ID_START + index),
).sort((left, right) => right.riskScore - left.riskScore)
