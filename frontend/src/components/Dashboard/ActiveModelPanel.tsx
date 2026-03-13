import { BrainCircuit } from "lucide-react"

import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card"
import type { ActiveModel } from "./types"

interface ActiveModelPanelProps {
  model: ActiveModel
  inferenceRecommended: boolean
}

function formatDate(value: string) {
  return new Date(value).toLocaleDateString(undefined, {
    year: "numeric",
    month: "short",
    day: "numeric",
  })
}

function formatMetric(value: number) {
  return `${(value * 100).toFixed(1)}%`
}

export function ActiveModelPanel({ model }: ActiveModelPanelProps) {
  const metrics = [
    { label: "Accuracy", value: model.metrics.accuracy },
    { label: "Precision", value: model.metrics.precision },
    { label: "Recall", value: model.metrics.recall },
    { label: "F1", value: model.metrics.f1 },
  ]

  return (
    <Card className="gap-4 border-primary/15 bg-gradient-to-b from-card to-card/95 py-5">
      <CardHeader className="gap-1 border-b pb-4">
        <div className="flex items-center gap-2">
          <CardTitle className="flex items-center gap-2 text-base">
            <BrainCircuit className="size-4 text-primary" />
            Active Model
          </CardTitle>
        </div>
        <CardDescription>Current production model performance</CardDescription>
      </CardHeader>

      <CardContent className="space-y-4">
        <div className="grid grid-cols-1 gap-3 text-sm sm:grid-cols-3">
          <div>
            <p className="text-muted-foreground">Version</p>
            <p className="font-medium">{model.version}</p>
          </div>
          <div>
            <p className="text-muted-foreground">Training Date</p>
            <p className="font-medium">{formatDate(model.trainingDate)}</p>
          </div>
          <div>
            <p className="text-muted-foreground">Dataset Size</p>
            <p className="font-medium">
              {model.datasetSize.toLocaleString()} samples
            </p>
          </div>
        </div>

        <div className="grid grid-cols-2 gap-3">
          {metrics.map((metric) => (
            <div
              key={metric.label}
              className="rounded-lg border bg-muted/30 px-3 py-2.5"
            >
              <p className="text-xs text-muted-foreground">{metric.label}</p>
              <p className="text-base font-semibold">
                {formatMetric(metric.value)}
              </p>
            </div>
          ))}
        </div>

        <div className="rounded-lg border bg-muted/20 px-3 py-2.5">
          <p className="text-xs text-muted-foreground">Out-of-Bag Score</p>
          <p className="text-base font-semibold">
            {formatMetric(model.metrics.oobScore)}
          </p>
        </div>
      </CardContent>
    </Card>
  )
}
