import { FlaskConical, RefreshCcw, Rocket, Upload } from "lucide-react"
import { useState } from "react"

import { Button } from "@/components/ui/button"
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card"
import {
  Dialog,
  DialogClose,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog"
import { LoadingButton } from "@/components/ui/loading-button"
import type { RecentModel } from "./types"

interface ModelManagementPanelProps {
  models: RecentModel[]
  activeModelId: string
  trainPending: boolean
  inferencePending: boolean
  onTrainNewModel: () => void
  onRunInference: () => void
  onUploadModel: () => void
  onDeployModel: (model: RecentModel) => void
}

function formatDate(value: string) {
  return new Date(value).toLocaleDateString(undefined, {
    year: "numeric",
    month: "short",
    day: "numeric",
  })
}

export function ModelManagementPanel({
  models,
  activeModelId,
  trainPending,
  inferencePending,
  onTrainNewModel,
  onRunInference,
  onUploadModel,
  onDeployModel,
}: ModelManagementPanelProps) {
  const [selectedModel, setSelectedModel] = useState<RecentModel | null>(null)

  return (
    <>
      <Card className="gap-4 py-5">
        <CardHeader className="gap-1 border-b pb-4">
          <CardTitle className="flex items-center gap-2 text-base">
            <FlaskConical className="size-4 text-primary" />
            Model Management
          </CardTitle>
          <CardDescription>
            Trigger training, refresh predictions, and deploy model revisions
          </CardDescription>
        </CardHeader>

        <CardContent className="space-y-4">
          <div className="flex flex-col gap-2">
            <LoadingButton
              size="sm"
              loading={trainPending}
              onClick={onTrainNewModel}
              className="w-full justify-start"
            >
              <FlaskConical className="size-4" />
              Train New Model
            </LoadingButton>

            <LoadingButton
              size="sm"
              variant="outline"
              loading={inferencePending}
              onClick={onRunInference}
              className="w-full justify-start"
            >
              <RefreshCcw className="size-4" />
              Run Inference
            </LoadingButton>

            <Button
              size="sm"
              variant="secondary"
              onClick={onUploadModel}
              className="w-full justify-start"
            >
              <Upload className="size-4" />
              Upload Model
            </Button>
          </div>

          <div className="space-y-2">
            <p className="text-xs font-medium uppercase tracking-wide text-muted-foreground">
              Recent Models
            </p>
            {models.map((model) => (
              <div
                key={model.id}
                className="flex items-center justify-between gap-2 rounded-lg border bg-muted/20 px-3 py-2.5"
              >
                <div className="min-w-0 flex-1">
                  <p className="truncate text-sm font-medium">
                    {model.version}
                  </p>
                  <p className="text-xs text-muted-foreground">
                    {formatDate(model.trainingDate)} · F1{" "}
                    {(model.f1 * 100).toFixed(1)}%
                  </p>
                </div>
                <Button
                  size="sm"
                  variant={model.id === activeModelId ? "secondary" : "outline"}
                  disabled={model.id === activeModelId}
                  onClick={() => setSelectedModel(model)}
                >
                  <Rocket className="size-4" />
                  {model.id === activeModelId ? "Active" : "Deploy"}
                </Button>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>

      <Dialog
        open={selectedModel !== null}
        onOpenChange={(isOpen) => {
          if (!isOpen) {
            setSelectedModel(null)
          }
        }}
      >
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Deploy {selectedModel?.version}?</DialogTitle>
            <DialogDescription>
              This updates the active model selection and marks patient
              inference as needing a rerun.
            </DialogDescription>
          </DialogHeader>
          <DialogFooter>
            <DialogClose asChild>
              <Button variant="outline">Cancel</Button>
            </DialogClose>
            <Button
              onClick={() => {
                if (selectedModel) {
                  onDeployModel(selectedModel)
                }
                setSelectedModel(null)
              }}
            >
              Confirm Deploy
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </>
  )
}
