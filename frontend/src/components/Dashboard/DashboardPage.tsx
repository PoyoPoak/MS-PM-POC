import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query"
import { Activity, Clock4, Database, UsersRound } from "lucide-react"
import { useEffect, useMemo, useState } from "react"

import {
  DashboardService,
  type ModelArtifactPublic,
  ModelsService,
  type PatientLatestTelemetryPublic,
  PatientsService,
  TrainingService,
} from "@/client"
import useCustomToast from "@/hooks/useCustomToast"
import { handleError } from "@/utils"
import { ActiveModelPanel } from "./ActiveModelPanel"
import { ModelManagementPanel } from "./ModelManagementPanel"
import { PatientListTable } from "./PatientListTable"
import { QuickStatsCards } from "./QuickStatsCards"
import type {
  ActiveModel,
  DashboardPatientRow,
  QuickStat,
  RecentModel,
} from "./types"

function getMetricValue(
  metrics: Record<string, unknown>,
  keys: string[],
): number {
  for (const key of keys) {
    const value = metrics[key]
    if (typeof value === "number") {
      return value
    }
  }
  return 0
}

function deriveRiskScore(row: PatientLatestTelemetryPublic): number | null {
  if (typeof row.fail_probability === "number") {
    return Math.max(0, Math.min(1, row.fail_probability))
  }

  return null
}

function toActiveModel(
  model: ModelArtifactPublic | null | undefined,
): ActiveModel | null {
  if (!model) {
    return null
  }

  const metrics = model.metrics as Record<string, unknown>
  const datasetInfo = model.dataset_info as Record<string, unknown>
  const datasetSizeRaw = datasetInfo.train_rows
  const datasetSize = typeof datasetSizeRaw === "number" ? datasetSizeRaw : 0

  return {
    id: model.id,
    version:
      model.client_version_id ??
      model.source_run_id ??
      `model-${model.id.slice(0, 8)}`,
    trainingDate:
      model.trained_at_utc ?? model.created_at ?? new Date().toISOString(),
    datasetSize,
    metrics: {
      accuracy: getMetricValue(metrics, ["accuracy", "test_accuracy"]),
      precision: getMetricValue(metrics, ["precision", "precision_score"]),
      recall: getMetricValue(metrics, ["recall", "recall_score"]),
      f1: getMetricValue(metrics, ["f1", "f1_score"]),
      oobScore: getMetricValue(metrics, ["oob_score", "oobScore"]),
    },
  }
}

function toRecentModel(model: ModelArtifactPublic): RecentModel {
  const metrics = model.metrics as Record<string, unknown>

  return {
    id: model.id,
    version:
      model.client_version_id ??
      model.source_run_id ??
      `model-${model.id.slice(0, 8)}`,
    trainingDate:
      model.trained_at_utc ?? model.created_at ?? new Date().toISOString(),
    f1: getMetricValue(metrics, ["f1", "f1_score"]),
  }
}

function toPatientRows(
  rows: PatientLatestTelemetryPublic[],
): DashboardPatientRow[] {
  return rows
    .map((row) => {
      const riskScore = deriveRiskScore(row)

      const leadImpedanceRollingMean3d =
        row.lead_impedance_ohms_rolling_mean_3d ?? row.lead_impedance_ohms
      const leadImpedanceRollingMean7d =
        row.lead_impedance_ohms_rolling_mean_7d ?? row.lead_impedance_ohms
      const captureThresholdRollingMean3d =
        row.capture_threshold_v_rolling_mean_3d ?? row.capture_threshold_v
      const captureThresholdRollingMean7d =
        row.capture_threshold_v_rolling_mean_7d ?? row.capture_threshold_v

      const leadImpedanceDeltaPerDay3d =
        row.lead_impedance_ohms_delta_per_day_3d ??
        Number(
          (
            (leadImpedanceRollingMean3d - leadImpedanceRollingMean7d) /
            4
          ).toFixed(2),
        )
      const leadImpedanceDeltaPerDay7d =
        row.lead_impedance_ohms_delta_per_day_7d ??
        Number(
          ((row.lead_impedance_ohms - leadImpedanceRollingMean7d) / 7).toFixed(
            2,
          ),
        )
      const captureThresholdDeltaPerDay3d =
        row.capture_threshold_v_delta_per_day_3d ??
        Number(
          (
            (captureThresholdRollingMean3d - captureThresholdRollingMean7d) /
            4
          ).toFixed(3),
        )
      const captureThresholdDeltaPerDay7d =
        row.capture_threshold_v_delta_per_day_7d ??
        Number(
          (
            (row.capture_threshold_v - captureThresholdRollingMean7d) /
            7
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
        alertsSent: (riskScore ?? 0) >= 0.75,
      }
    })
    .sort((a, b) => (b.riskScore ?? -1) - (a.riskScore ?? -1))
}

function buildStats(
  totalPatients: number,
  highRiskCount: number,
  totalTelemetryDatapoints: number,
  lastUpdate: string | null,
): QuickStat[] {
  const lastUpdateValue = lastUpdate
    ? new Date(lastUpdate).toLocaleTimeString([], {
        hour: "2-digit",
        minute: "2-digit",
      })
    : "N/A"

  return [
    {
      title: "Total Patients",
      value: totalPatients.toLocaleString(),
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
      title: "Total Telemetry Datapoints",
      value: totalTelemetryDatapoints.toLocaleString(),
      helper: "Rows currently loaded in dashboard",
      icon: Database,
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
  const [inferenceRecommended, setInferenceRecommended] = useState(false)
  const [frozenTelemetryDatapoints, setFrozenTelemetryDatapoints] = useState<
    number | null
  >(null)
  const queryClient = useQueryClient()
  const { showSuccessToast, showErrorToast } = useCustomToast()

  const summaryQuery = useQuery({
    queryKey: ["dashboard", "summary"],
    queryFn: () => DashboardService.getDashboardSummary(),
    staleTime: 30_000,
  })

  const modelsQuery = useQuery({
    queryKey: ["dashboard", "models"],
    queryFn: () => ModelsService.listModelArtifacts({ skip: 0, limit: 25 }),
    staleTime: 30_000,
  })

  const activeModelQuery = useQuery({
    queryKey: ["dashboard", "active-model"],
    queryFn: () => ModelsService.getActiveModelArtifact(),
    staleTime: 30_000,
  })

  const patientsQuery = useQuery({
    queryKey: ["dashboard", "patients", "latest"],
    queryFn: () =>
      PatientsService.listLatestPatientTelemetry({
        skip: 0,
        limit: 1000,
        sortBy: "risk_score",
        sortOrder: "desc",
      }),
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
      await Promise.all([
        queryClient.invalidateQueries({ queryKey: ["dashboard", "summary"] }),
        queryClient.invalidateQueries({ queryKey: ["dashboard", "models"] }),
        queryClient.invalidateQueries({
          queryKey: ["dashboard", "active-model"],
        }),
        queryClient.invalidateQueries({
          queryKey: ["dashboard", "patients", "latest"],
        }),
      ])
    },
    onError: handleError.bind(showErrorToast),
  })

  const deployModelMutation = useMutation({
    mutationFn: (model: RecentModel) =>
      ModelsService.activateModelArtifact({ modelId: model.id }),
    onSuccess: async (_response, model) => {
      setInferenceRecommended(true)
      showSuccessToast(
        `${model.version} is now active. Run inference to refresh patient risk scores.`,
      )
      await Promise.all([
        queryClient.invalidateQueries({ queryKey: ["dashboard", "summary"] }),
        queryClient.invalidateQueries({ queryKey: ["dashboard", "models"] }),
        queryClient.invalidateQueries({
          queryKey: ["dashboard", "active-model"],
        }),
      ])
    },
    onError: handleError.bind(showErrorToast),
  })

  const patients = useMemo(
    () => toPatientRows(patientsQuery.data?.data ?? []),
    [patientsQuery.data?.data],
  )

  const activeModel = useMemo(
    () => toActiveModel(activeModelQuery.data?.data),
    [activeModelQuery.data?.data],
  )

  const recentModels = useMemo<RecentModel[]>(
    () => (modelsQuery.data?.data ?? []).slice(0, 3).map(toRecentModel),
    [modelsQuery.data?.data],
  )

  const summary = summaryQuery.data
  const liveTelemetryDatapoints = patientsQuery.data?.count ?? patients.length

  useEffect(() => {
    if (frozenTelemetryDatapoints === null && patientsQuery.isSuccess) {
      setFrozenTelemetryDatapoints(liveTelemetryDatapoints)
    }
  }, [
    frozenTelemetryDatapoints,
    liveTelemetryDatapoints,
    patientsQuery.isSuccess,
  ])

  const quickStats = useMemo(
    () =>
      buildStats(
        summary?.total_patients ?? patients.length,
        summary?.high_risk_patients ??
          patients.filter((row) => (row.riskScore ?? 0) >= 0.7).length,
        frozenTelemetryDatapoints ?? liveTelemetryDatapoints,
        summary?.last_update ?? null,
      ),
    [
      frozenTelemetryDatapoints,
      summary?.high_risk_patients,
      summary?.last_update,
      summary?.total_patients,
      liveTelemetryDatapoints,
      patients,
    ],
  )

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
              activeModelId={activeModel?.id ?? ""}
              trainPending={trainModelMutation.isPending}
              inferencePending={
                runInferenceMutation.isPending || deployModelMutation.isPending
              }
              onTrainNewModel={() => trainModelMutation.mutate()}
              onRunInference={() => runInferenceMutation.mutate()}
              onUploadModel={() => {
                showErrorToast(
                  "Upload flow is not yet wired in this dashboard. Use the model artifact upload endpoint workflow for now.",
                )
              }}
              onDeployModel={(model) => deployModelMutation.mutate(model)}
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
              isLoading={patientsQuery.isLoading}
              usingFallback={false}
            />
          </section>
        </div>
      </div>
    </div>
  )
}
