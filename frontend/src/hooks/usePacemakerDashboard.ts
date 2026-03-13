import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query"

import {
  type Body_models_upload_model_artifact,
  ModelsService,
  TrainingService,
} from "@/client"
import { handleError } from "@/utils"
import useCustomToast from "./useCustomToast"

export function usePacemakerDashboard(search: string) {
  const queryClient = useQueryClient()
  const { showErrorToast, showSuccessToast } = useCustomToast()

  const activeModelQuery = useQuery({
    queryKey: ["dashboard", "active-model"],
    queryFn: () => ModelsService.readActiveModelArtifact(),
    retry: false,
  })

  const modelListQuery = useQuery({
    queryKey: ["dashboard", "models"],
    queryFn: () => ModelsService.readModelArtifacts({ skip: 0, limit: 10 }),
    retry: false,
  })

  const riskTableQuery = useQuery({
    queryKey: ["dashboard", "risk-table", search],
    queryFn: () =>
      TrainingService.readAtRiskPatients({
        skip: 0,
        limit: 25,
        minRisk: 0,
        search: search.trim() === "" ? null : search.trim(),
      }),
    retry: false,
  })

  const trainMutation = useMutation({
    mutationFn: () => TrainingService.createTrainingJobRequest(),
    onSuccess: () => {
      showSuccessToast("Training request queued")
    },
    onError: handleError.bind(showErrorToast),
  })

  const inferenceMutation = useMutation({
    mutationFn: () => TrainingService.refreshPatientLatestPredictions(),
    onSuccess: () => {
      showSuccessToast("Inference completed")
      queryClient.invalidateQueries({ queryKey: ["dashboard", "risk-table"] })
    },
    onError: handleError.bind(showErrorToast),
  })

  const activateModelMutation = useMutation({
    mutationFn: (modelId: string) =>
      ModelsService.activateModelArtifact({ modelId }),
    onSuccess: () => {
      showSuccessToast("Active model updated")
      queryClient.invalidateQueries({ queryKey: ["dashboard", "active-model"] })
      queryClient.invalidateQueries({ queryKey: ["dashboard", "models"] })
    },
    onError: handleError.bind(showErrorToast),
  })

  const deleteModelMutation = useMutation({
    mutationFn: (modelId: string) =>
      ModelsService.deleteModelArtifact({ modelId }),
    onSuccess: () => {
      showSuccessToast("Model deleted")
      queryClient.invalidateQueries({ queryKey: ["dashboard", "active-model"] })
      queryClient.invalidateQueries({ queryKey: ["dashboard", "models"] })
    },
    onError: handleError.bind(showErrorToast),
  })

  const uploadModelMutation = useMutation({
    mutationFn: (file: File) => {
      const metadata = {
        algorithm: "UploadedModel",
        hyperparameters: {},
        metrics: {},
        dataset_info: {
          uploaded_filename: file.name,
        },
      }

      const formData: Body_models_upload_model_artifact = {
        model_file: file,
        metadata_json: JSON.stringify(metadata),
      }

      return ModelsService.uploadModelArtifact({ formData })
    },
    onSuccess: () => {
      showSuccessToast("Model uploaded")
      queryClient.invalidateQueries({ queryKey: ["dashboard", "active-model"] })
      queryClient.invalidateQueries({ queryKey: ["dashboard", "models"] })
    },
    onError: handleError.bind(showErrorToast),
  })

  return {
    activeModelQuery,
    modelListQuery,
    riskTableQuery,
    trainMutation,
    inferenceMutation,
    activateModelMutation,
    deleteModelMutation,
    uploadModelMutation,
  }
}
