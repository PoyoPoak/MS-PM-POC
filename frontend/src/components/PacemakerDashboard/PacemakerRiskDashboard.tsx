import {
  AlertCircle,
  Clock3,
  Cpu,
  Heart,
  Play,
  RefreshCw,
  Search,
  Settings,
  Upload,
} from "lucide-react"
import { useMemo, useRef, useState } from "react"

import type { ModelArtifactPublic } from "@/client"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import { LoadingButton } from "@/components/ui/loading-button"
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table"
import { usePacemakerDashboard } from "@/hooks/usePacemakerDashboard"

function toPercent(value: unknown): string {
  if (typeof value === "number" && Number.isFinite(value)) {
    const normalized = value <= 1 ? value * 100 : value
    return `${normalized.toFixed(1)}%`
  }
  return "—"
}

function getWeightedAverageMetric(
  metrics: Record<string, unknown>,
  metricKey: string,
): number | null {
  const classificationReport = metrics.classification_report
  if (
    typeof classificationReport !== "object" ||
    classificationReport === null
  ) {
    return null
  }

  const weightedAverage = (classificationReport as Record<string, unknown>)[
    "weighted avg"
  ]
  if (typeof weightedAverage !== "object" || weightedAverage === null) {
    return null
  }

  const value = (weightedAverage as Record<string, unknown>)[metricKey]
  if (typeof value === "number" && Number.isFinite(value)) {
    return value
  }

  return null
}

function toMetric(
  metrics: Record<string, unknown>,
  keys: string[],
  weightedAverageKey?: string,
): string {
  const metric = keys.find((key) => typeof metrics[key] === "number")
  if (metric) {
    return toPercent(metrics[metric])
  }

  if (weightedAverageKey) {
    const weightedAverageMetric = getWeightedAverageMetric(
      metrics,
      weightedAverageKey,
    )
    if (weightedAverageMetric !== null) {
      return toPercent(weightedAverageMetric)
    }
  }

  return "—"
}

function toDate(value?: string | null): string {
  if (!value) {
    return "—"
  }
  const date = new Date(value)
  if (Number.isNaN(date.getTime())) {
    return "—"
  }
  return date.toLocaleString("en-US", {
    dateStyle: "medium",
    timeStyle: "short",
    hour12: false,
    timeZone: "UTC",
  })
}

function riskBadgeVariant(
  level: string,
): "destructive" | "secondary" | "outline" {
  if (level === "HIGH") {
    return "destructive"
  }
  if (level === "MED") {
    return "secondary"
  }
  return "outline"
}

function getDatasetValue(
  model: ModelArtifactPublic | undefined,
  key: string,
): string {
  if (!model) {
    return "—"
  }
  const value = model.dataset_info[key]
  if (typeof value === "number") {
    return value.toLocaleString("en-US")
  }
  if (typeof value === "string") {
    return value
  }
  return "—"
}

export default function PacemakerRiskDashboard() {
  const [search, setSearch] = useState("")
  const fileInputRef = useRef<HTMLInputElement | null>(null)

  const {
    activeModelQuery,
    modelListQuery,
    riskTableQuery,
    trainMutation,
    inferenceMutation,
    activateModelMutation,
    deleteModelMutation,
    uploadModelMutation,
  } = usePacemakerDashboard(search)

  const activeModel = activeModelQuery.data
  const recentModels = modelListQuery.data?.data ?? []
  const riskRows = riskTableQuery.data?.data ?? []

  const metrics = useMemo(
    () => (activeModel?.metrics as Record<string, unknown> | undefined) ?? {},
    [activeModel?.metrics],
  )

  const has403Error =
    String(activeModelQuery.error ?? "").includes("403") ||
    String(modelListQuery.error ?? "").includes("403") ||
    String(riskTableQuery.error ?? "").includes("403")

  const refreshedAt = toDate(riskTableQuery.data?.refreshed_at)

  return (
    <div className="flex w-full flex-col gap-6">
      <div className="flex flex-wrap items-center justify-between gap-4 rounded-xl border bg-card px-4 py-4 shadow-sm">
        <div className="flex items-center gap-3">
          <div className="rounded-lg border bg-rose-50 p-2 text-rose-700">
            <Heart className="size-5" />
          </div>
          <h1 className="text-2xl font-semibold tracking-tight">
            Pacemaker Risk Dashboard
          </h1>
        </div>
        <div className="flex items-center gap-2 text-sm text-muted-foreground">
          <Clock3 className="size-4" />
          <span>Last refresh: {refreshedAt}</span>
        </div>
      </div>

      {has403Error ? (
        <Card>
          <CardHeader>
            <CardTitle>
              Dashboard access requires superuser privileges
            </CardTitle>
            <CardDescription>
              Log in as the configured superuser to load telemetry risk and
              model management data.
            </CardDescription>
          </CardHeader>
        </Card>
      ) : null}

      <div className="grid gap-6 xl:grid-cols-[360px_minmax(0,1fr)]">
        <div className="flex flex-col gap-6">
          <Card>
            <CardHeader className="flex flex-row items-center justify-between gap-4 space-y-0">
              <div className="flex items-center gap-3">
                <div className="rounded-lg border bg-sky-50 p-2 text-sky-700">
                  <Cpu className="size-4" />
                </div>
                <CardTitle>Active Model</CardTitle>
              </div>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid gap-2 text-sm">
                <div className="flex items-center justify-between">
                  <span className="text-muted-foreground">Version</span>
                  <span className="font-medium">
                    {activeModel?.client_version_id ?? "—"}
                  </span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-muted-foreground">Trained At</span>
                  <span className="font-medium">
                    {toDate(activeModel?.trained_at_utc)}
                  </span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-muted-foreground">Dataset Size</span>
                  <span className="font-medium">
                    {getDatasetValue(activeModel, "train_rows")}
                  </span>
                </div>
              </div>

              <div className="grid grid-cols-2 gap-2 border-t pt-4">
                <div className="rounded-md border bg-muted/40 px-3 py-2 text-center">
                  <div className="text-xs text-muted-foreground">Accuracy</div>
                  <div className="text-sm font-semibold">
                    {toMetric(metrics, ["accuracy", "test_accuracy"])}
                  </div>
                </div>
                <div className="rounded-md border bg-muted/40 px-3 py-2 text-center">
                  <div className="text-xs text-muted-foreground">Precision</div>
                  <div className="text-sm font-semibold">
                    {toMetric(
                      metrics,
                      ["precision", "test_precision"],
                      "precision",
                    )}
                  </div>
                </div>
                <div className="rounded-md border bg-emerald-50 px-3 py-2 text-center text-emerald-800">
                  <div className="text-xs">Recall</div>
                  <div className="text-sm font-semibold">
                    {toMetric(metrics, ["recall", "test_recall"], "recall")}
                  </div>
                </div>
                <div className="rounded-md border bg-emerald-50 px-3 py-2 text-center text-emerald-800">
                  <div className="text-xs">F1 Score</div>
                  <div className="text-sm font-semibold">
                    {toMetric(
                      metrics,
                      ["f1", "f1_score", "test_f1"],
                      "f1-score",
                    )}
                  </div>
                </div>
              </div>

              <div className="flex items-center justify-between rounded-md border bg-muted/40 px-3 py-2 text-sm">
                <span className="text-muted-foreground">OOB Score</span>
                <span className="font-semibold">
                  {toMetric(metrics, ["oob_score", "oob"])}
                </span>
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="flex flex-row items-center gap-3 space-y-0">
              <div className="rounded-lg border bg-muted p-2 text-muted-foreground">
                <Settings className="size-4" />
              </div>
              <CardTitle>Model Management</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="flex flex-col gap-2">
                <LoadingButton
                  loading={trainMutation.isPending}
                  onClick={() => trainMutation.mutate()}
                  className="w-full"
                >
                  <Play className="size-4" />
                  Train New Model
                </LoadingButton>
                <LoadingButton
                  loading={inferenceMutation.isPending}
                  onClick={() => inferenceMutation.mutate()}
                  variant="secondary"
                  className="w-full"
                >
                  <RefreshCw className="size-4" />
                  Run Inference
                </LoadingButton>
                <LoadingButton
                  loading={uploadModelMutation.isPending}
                  variant="outline"
                  onClick={() => fileInputRef.current?.click()}
                  className="w-full"
                >
                  <Upload className="size-4" />
                  Upload Model
                </LoadingButton>
                <input
                  ref={fileInputRef}
                  type="file"
                  accept=".joblib,.pkl,.bin,.model"
                  className="hidden"
                  onChange={(event) => {
                    const file = event.target.files?.[0]
                    if (file) {
                      uploadModelMutation.mutate(file)
                    }
                    event.currentTarget.value = ""
                  }}
                />
              </div>

              <div className="space-y-2 border-t pt-4">
                <p className="text-sm font-medium text-muted-foreground">
                  Recent models
                </p>
                {recentModels.length === 0 ? (
                  <p className="text-sm text-muted-foreground">
                    No models available.
                  </p>
                ) : (
                  recentModels.map((model) => {
                    const recall = toMetric(
                      (model.metrics as Record<string, unknown>) ?? {},
                      ["recall", "test_recall"],
                    )
                    return (
                      <div
                        key={model.id}
                        className="flex items-center justify-between rounded-md border px-3 py-2"
                      >
                        <div className="min-w-0">
                          <p className="truncate text-sm font-medium">
                            {model.client_version_id ?? model.id.slice(0, 8)}
                          </p>
                          <p className="text-xs text-muted-foreground">
                            {recall}
                          </p>
                        </div>
                        <div className="flex items-center gap-1">
                          {model.is_active ? (
                            <Badge variant="secondary">Active</Badge>
                          ) : (
                            <Button
                              size="sm"
                              variant="outline"
                              onClick={() =>
                                activateModelMutation.mutate(model.id)
                              }
                              disabled={activateModelMutation.isPending}
                            >
                              Activate
                            </Button>
                          )}
                          <Button
                            size="icon-sm"
                            variant="ghost"
                            onClick={() => deleteModelMutation.mutate(model.id)}
                            disabled={
                              deleteModelMutation.isPending || model.is_active
                            }
                            aria-label="Delete model"
                          >
                            <AlertCircle className="size-4" />
                          </Button>
                        </div>
                      </div>
                    )
                  })
                )}
              </div>
            </CardContent>
          </Card>
        </div>

        <Card>
          <CardHeader className="flex flex-row flex-wrap items-center justify-between gap-3 space-y-0">
            <div className="flex items-center gap-3">
              <div className="rounded-lg border bg-rose-50 p-2 text-rose-700">
                <AlertCircle className="size-4" />
              </div>
              <CardTitle>At-Risk Patients</CardTitle>
            </div>
            <div className="relative w-full max-w-xs">
              <Search className="absolute left-2 top-1/2 size-4 -translate-y-1/2 text-muted-foreground" />
              <Input
                className="pl-8"
                placeholder="Search patients"
                value={search}
                onChange={(event) => setSearch(event.target.value)}
              />
            </div>
          </CardHeader>
          <CardContent>
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Patient ID</TableHead>
                  <TableHead>Risk Score</TableHead>
                  <TableHead>Level</TableHead>
                  <TableHead>Battery</TableHead>
                  <TableHead>Impedance</TableHead>
                  <TableHead>Threshold</TableHead>
                  <TableHead>Last Update</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {riskRows.length === 0 ? (
                  <TableRow>
                    <TableCell
                      colSpan={7}
                      className="text-center text-muted-foreground"
                    >
                      No patient rows available.
                    </TableCell>
                  </TableRow>
                ) : (
                  riskRows.map((row) => (
                    <TableRow key={`${row.patient_id}-${row.timestamp}`}>
                      <TableCell className="font-medium">
                        PAT-{row.patient_id}
                      </TableCell>
                      <TableCell className="font-semibold">
                        {row.fail_probability.toFixed(2)}
                      </TableCell>
                      <TableCell>
                        <Badge variant={riskBadgeVariant(row.risk_level)}>
                          {row.risk_level}
                        </Badge>
                      </TableCell>
                      <TableCell>{row.battery_voltage_v.toFixed(2)}V</TableCell>
                      <TableCell>
                        {Math.round(row.lead_impedance_ohms)}Ω
                      </TableCell>
                      <TableCell>
                        {row.capture_threshold_v.toFixed(1)}V
                      </TableCell>
                      <TableCell>{toDate(row.timestamp)}</TableCell>
                    </TableRow>
                  ))
                )}
              </TableBody>
            </Table>
            <div className="mt-3 text-sm text-muted-foreground">
              Showing {riskRows.length} of {riskTableQuery.data?.count ?? 0}{" "}
              patients
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  )
}
