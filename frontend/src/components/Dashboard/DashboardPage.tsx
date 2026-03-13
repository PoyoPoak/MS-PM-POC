import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query"
import { Activity, BellRing, Clock4, UsersRound } from "lucide-react"
import { useMemo, useState } from "react"

import { type PacemakerTelemetryPublic, TrainingService } from "@/client"
import useCustomToast from "@/hooks/useCustomToast"
import { handleError } from "@/utils"
import { ActiveModelPanel } from "./ActiveModelPanel"
import { ModelManagementPanel } from "./ModelManagementPanel"
import {
  MOCK_ACTIVE_MODEL,
  MOCK_PATIENTS,
  MOCK_RECENT_MODELS,
} from "./mockData"
import { PatientListTable } from "./PatientListTable"
import { QuickStatsCards } from "./QuickStatsCards"
import type {
  ActiveModel,
  DashboardPatientRow,
  QuickStat,
  RecentModel,
} from "./types"

function deriveRiskScore(row: PacemakerTelemetryPublic): number {
  if (typeof row.target_fail_next_7d === "number") {
    return Math.max(0, Math.min(1, row.target_fail_next_7d))
  }

  const leadScore = Math.min(
    1,
    Math.max(0, (row.lead_impedance_ohms - 1000) / 600),
  )
  const thresholdScore = Math.min(
    1,
    Math.max(0, (row.capture_threshold_v - 0.8) / 1.8),
  )
  const batteryScore = Math.min(
    1,
    Math.max(0, (3.05 - row.battery_voltage_v) / 0.55),
  )

  return Number(
    (0.4 * leadScore + 0.4 * thresholdScore + 0.2 * batteryScore).toFixed(4),
  )
}

function toPatientRows(
  rows: PacemakerTelemetryPublic[],
): DashboardPatientRow[] {
  const byPatient = new Map<number, PacemakerTelemetryPublic>()

  rows.forEach((row) => {
    const current = byPatient.get(row.patient_id)
    if (!current) {
      byPatient.set(row.patient_id, row)
      return
    }

    if (
      new Date(row.timestamp).getTime() > new Date(current.timestamp).getTime()
    ) {
      byPatient.set(row.patient_id, row)
    }
  })

  return Array.from(byPatient.values())
    .map((row) => {
      const riskScore = deriveRiskScore(row)
      const leadImpedanceRollingMean3d =
        row.lead_impedance_ohms_rolling_mean_3d ??
        Number(
          (row.lead_impedance_ohms * (1 + (riskScore - 0.5) * 0.04)).toFixed(1),
        )
      const leadImpedanceRollingMean7d =
        row.lead_impedance_ohms_rolling_mean_7d ??
        Number(
          (row.lead_impedance_ohms * (1 + (riskScore - 0.5) * 0.025)).toFixed(
            1,
          ),
        )
      const captureThresholdRollingMean3d =
        row.capture_threshold_v_rolling_mean_3d ??
        Number(
          (row.capture_threshold_v * (1 + (riskScore - 0.5) * 0.05)).toFixed(3),
        )
      const captureThresholdRollingMean7d =
        row.capture_threshold_v_rolling_mean_7d ??
        Number(
          (row.capture_threshold_v * (1 + (riskScore - 0.5) * 0.03)).toFixed(3),
        )

      const leadImpedanceDeltaPerDay3d =
        row.lead_impedance_ohms_delta_per_day_3d ??
        Number(
          (
            ((leadImpedanceRollingMean3d - leadImpedanceRollingMean7d) / 4) *
            (0.85 + riskScore * 0.3)
          ).toFixed(2),
        )
      const leadImpedanceDeltaPerDay7d =
        row.lead_impedance_ohms_delta_per_day_7d ??
        Number(
          (
            ((row.lead_impedance_ohms - leadImpedanceRollingMean7d) / 7) *
            (0.8 + riskScore * 0.25)
          ).toFixed(2),
        )
      const captureThresholdDeltaPerDay3d =
        row.capture_threshold_v_delta_per_day_3d ??
        Number(
          (
            ((captureThresholdRollingMean3d - captureThresholdRollingMean7d) /
              4) *
            (0.85 + riskScore * 0.25)
          ).toFixed(3),
        )
      const captureThresholdDeltaPerDay7d =
        row.capture_threshold_v_delta_per_day_7d ??
        Number(
          (
            ((row.capture_threshold_v - captureThresholdRollingMean7d) / 7) *
            (0.8 + riskScore * 0.2)
          ).toFixed(3),
        )

      return {
        patientId: row.patient_id,
        riskScore,
        leadImpedance: row.lead_impedance_ohms,
        captureThreshold: row.capture_threshold_v,
        batteryVoltage: row.battery_voltage_v,
        leadImpedanceRollingMean3d,
        leadImpedanceRollingMean7d,
        captureThresholdRollingMean3d,
        captureThresholdRollingMean7d,
        leadImpedanceDeltaPerDay3d,
        leadImpedanceDeltaPerDay7d,
        captureThresholdDeltaPerDay3d,
        captureThresholdDeltaPerDay7d,
        lastUpdate: row.timestamp,
        alertsSent: riskScore >= 0.75,
      }
    })
    .sort((a, b) => b.riskScore - a.riskScore)
}

function buildStats(patients: DashboardPatientRow[]): QuickStat[] {
  const highRiskCount = patients.filter(
    (patient) => patient.riskScore >= 0.7,
  ).length
  const alertsCount = patients.filter((patient) => patient.alertsSent).length
  const lastUpdateValue =
    patients.length === 0
      ? "N/A"
      : new Date(
          patients.reduce((latest, row) => {
            return new Date(row.lastUpdate).getTime() >
              new Date(latest).getTime()
              ? row.lastUpdate
              : latest
          }, patients[0].lastUpdate),
        ).toLocaleTimeString([], {
          hour: "2-digit",
          minute: "2-digit",
        })

  return [
    {
      title: "Total Patients",
      value: patients.length.toLocaleString(),
      helper: "Current monitored population",
      icon: UsersRound,
    },
    {
      title: "High Risk",
      value: highRiskCount.toString(),
      helper: "Patients needing urgent review",
      icon: Activity,
    },
    {
      title: "Alerts Sent",
      value: alertsCount.toString(),
      helper: "Notification activity",
      icon: BellRing,
    },
    {
      title: "Last Update",
      value: lastUpdateValue,
      helper: "Latest telemetry refresh",
      icon: Clock4,
    },
  ]
}

export function DashboardPage() {
  const [activeModel, setActiveModel] = useState<ActiveModel>(MOCK_ACTIVE_MODEL)
  const [recentModels] = useState<RecentModel[]>(MOCK_RECENT_MODELS)
  const [inferenceRecommended, setInferenceRecommended] = useState(false)
  const queryClient = useQueryClient()
  const { showSuccessToast, showErrorToast } = useCustomToast()

  const telemetryQuery = useQuery({
    queryKey: ["dashboard", "training-data"],
    queryFn: () => TrainingService.downloadTrainingData({ newestLocalTs: 0 }),
    staleTime: 30_000,
  })

  const trainModelMutation = useMutation({
    mutationFn: () => TrainingService.createTrainingJobRequest(),
    onSuccess: (response) => {
      showSuccessToast(
        `Training request queued (${response.id.slice(0, 8)}). The next available trainer will claim it.`,
      )
    },
    onError: handleError.bind(showErrorToast),
  })

  const runInferenceMutation = useMutation({
    mutationFn: () => TrainingService.refreshPatientLatestPredictions(),
    onSuccess: async (response) => {
      showSuccessToast(
        `Inference completed. ${response.rows_scored} rows scored and ${response.rows_upserted} rows refreshed.`,
      )
      setInferenceRecommended(false)
      await queryClient.invalidateQueries({
        queryKey: ["dashboard", "training-data"],
      })
    },
    onError: handleError.bind(showErrorToast),
  })

  const patients = useMemo(() => {
    if (!telemetryQuery.data?.rows || telemetryQuery.data.rows.length === 0) {
      return MOCK_PATIENTS
    }
    return toPatientRows(telemetryQuery.data.rows)
  }, [telemetryQuery.data?.rows])

  const usingFallback =
    telemetryQuery.isError ||
    !telemetryQuery.data ||
    telemetryQuery.data.rows.length === 0

  const quickStats = useMemo(() => buildStats(patients), [patients])

  return (
    <div className="h-full min-h-0">
      <div className="grid h-full min-h-0 grid-cols-1 gap-6 xl:grid-cols-[minmax(360px,420px)_minmax(0,1fr)]">
        <div className="space-y-6">
          <section aria-label="Operational quick stats">
            <QuickStatsCards stats={quickStats} />
          </section>

          <section aria-label="Active model summary">
            <ActiveModelPanel
              model={activeModel}
              inferenceRecommended={inferenceRecommended}
            />
          </section>

          <section aria-label="Model management actions">
            <ModelManagementPanel
              models={recentModels}
              activeModelId={activeModel.id}
              trainPending={trainModelMutation.isPending}
              inferencePending={runInferenceMutation.isPending}
              onTrainNewModel={() => trainModelMutation.mutate()}
              onRunInference={() => runInferenceMutation.mutate()}
              onUploadModel={() => {
                showErrorToast(
                  "Upload flow is not yet wired in this dashboard. Use the model artifact upload endpoint workflow for now.",
                )
              }}
              onDeployModel={(model) => {
                setActiveModel((previous) => ({
                  ...previous,
                  id: model.id,
                  version: model.version,
                  trainingDate: model.trainingDate,
                  metrics: {
                    ...previous.metrics,
                    f1: model.f1,
                  },
                }))
                setInferenceRecommended(true)
                showSuccessToast(
                  `${model.version} deployed locally as active model. Run inference to refresh patient risk scores.`,
                )
              }}
            />
          </section>
        </div>

        <div className="min-h-0 space-y-6">
          <section
            aria-label="Operational telemetry and patient list"
            className="h-full"
          >
            <PatientListTable
              data={patients}
              isLoading={telemetryQuery.isLoading}
              usingFallback={usingFallback}
            />
          </section>
        </div>
      </div>
    </div>
  )
}
