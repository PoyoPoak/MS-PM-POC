"use client";

import React from "react";
import { Badge } from "@/ui/components/Badge";
import { Button } from "@/ui/components/Button";
import { IconButton } from "@/ui/components/IconButton";
import { IconWithBackground } from "@/ui/components/IconWithBackground";
import { TextField } from "@/ui/components/TextField";
import { FeatherAlertCircle } from "@subframe/core";
import { FeatherCheck } from "@subframe/core";
import { FeatherCheckCircle } from "@subframe/core";
import { FeatherChevronRight } from "@subframe/core";
import { FeatherClock } from "@subframe/core";
import { FeatherCpu } from "@subframe/core";
import { FeatherEye } from "@subframe/core";
import { FeatherHeart } from "@subframe/core";
import { FeatherMail } from "@subframe/core";
import { FeatherMinus } from "@subframe/core";
import { FeatherPlay } from "@subframe/core";
import { FeatherRefreshCw } from "@subframe/core";
import { FeatherSearch } from "@subframe/core";
import { FeatherSettings } from "@subframe/core";
import { FeatherTrendingDown } from "@subframe/core";
import { FeatherTrendingUp } from "@subframe/core";
import { FeatherUpload } from "@subframe/core";

function PacemakerRiskDashboard() {
  return (
    <div className="container max-w-none flex h-full w-full flex-col items-start bg-neutral-50 overflow-auto">
      <div className="flex w-full items-center justify-center gap-4 border-b border-solid border-neutral-300 bg-neutral-0 px-4 py-4 shadow-sm sticky top-0 z-10">
        <div className="flex grow shrink-0 basis-0 items-center justify-center gap-4 mobile:flex-row mobile:flex-wrap mobile:gap-4">
          <div className="flex items-center gap-4">
            <IconWithBackground
              variant="error"
              size="medium"
              icon={<FeatherHeart />}
              square={true}
            />
            <span className="text-heading-2 font-heading-2 text-default-font mobile:text-heading-3 mobile:font-heading-3">
              Pacemaker Risk Dashboard
            </span>
          </div>
          <div className="flex grow shrink-0 basis-0 items-center justify-end gap-2">
            <div className="flex items-center gap-2 mobile:hidden">
              <FeatherClock className="text-caption font-caption text-subtext-color" />
              <span className="text-caption font-caption text-subtext-color">
                Last refresh: 2024-01-15 14:32 UTC
              </span>
            </div>
          </div>
        </div>
      </div>
      <div className="flex w-full flex-col items-start gap-6 px-6 py-6">
        <div className="flex w-full items-start gap-6 mobile:flex-col mobile:flex-nowrap mobile:gap-6">
          <div className="flex w-96 flex-none flex-col items-start gap-6 self-stretch mobile:w-full mobile:grow mobile:shrink-0 mobile:basis-0">
            <div className="flex w-full flex-col items-start gap-4 rounded-lg border border-solid border-neutral-300 bg-neutral-0 px-4 py-4 shadow-sm">
              <div className="flex w-full items-center gap-4">
                <IconWithBackground
                  variant="brand"
                  size="medium"
                  icon={<FeatherCpu />}
                  square={true}
                />
                <span className="grow shrink-0 basis-0 text-heading-3 font-heading-3 text-default-font">
                  Active Model
                </span>
                <Badge variant="success" icon={<FeatherCheck />}>
                  Active
                </Badge>
              </div>
              <div className="flex w-full flex-col items-start gap-3">
                <div className="flex w-full items-center justify-between">
                  <span className="text-caption font-caption text-neutral-700">
                    Version
                  </span>
                  <span className="text-body-bold font-body-bold text-neutral-900">
                    v2.4.1
                  </span>
                </div>
                <div className="flex w-full items-center justify-between">
                  <span className="text-caption font-caption text-neutral-700">
                    Trained At
                  </span>
                  <span className="text-body font-body text-neutral-900">
                    2024-01-10 08:00 UTC
                  </span>
                </div>
                <div className="flex w-full items-center justify-between">
                  <span className="text-caption font-caption text-neutral-700">
                    Dataset Window
                  </span>
                  <span className="text-body font-body text-neutral-900">
                    90 days
                  </span>
                </div>
                <div className="flex w-full items-center justify-between">
                  <span className="text-caption font-caption text-neutral-700">
                    Dataset Size
                  </span>
                  <span className="text-body font-body text-neutral-900">
                    1.2M records
                  </span>
                </div>
              </div>
              <div className="flex h-px w-full flex-none flex-col items-center gap-2 bg-neutral-300" />
              <div className="flex w-full flex-col items-start gap-2">
                <span className="text-caption-bold font-caption-bold text-neutral-700">
                  Performance Metrics
                </span>
                <div className="flex w-full items-start gap-4">
                  <div className="flex grow shrink-0 basis-0 flex-col items-center gap-1 rounded-md bg-neutral-50 px-3 py-3">
                    <span className="text-caption font-caption text-neutral-700">
                      Accuracy
                    </span>
                    <span className="text-body-bold font-body-bold text-neutral-900">
                      93.4%
                    </span>
                  </div>
                  <div className="flex grow shrink-0 basis-0 flex-col items-center gap-1 rounded-md bg-neutral-50 px-3 py-3">
                    <span className="text-caption font-caption text-neutral-700">
                      Precision
                    </span>
                    <span className="text-body-bold font-body-bold text-neutral-900">
                      89.7%
                    </span>
                  </div>
                </div>
                <div className="flex w-full items-start gap-4">
                  <div className="flex grow shrink-0 basis-0 flex-col items-center gap-1 rounded-md bg-success-50 px-3 py-3">
                    <span className="text-caption font-caption text-success-600">
                      Recall
                    </span>
                    <span className="text-body-bold font-body-bold text-success-700">
                      94.2%
                    </span>
                  </div>
                  <div className="flex grow shrink-0 basis-0 flex-col items-center gap-1 rounded-md bg-success-50 px-3 py-3">
                    <span className="text-caption font-caption text-success-600">
                      F1 Score
                    </span>
                    <span className="text-body-bold font-body-bold text-success-700">
                      91.8%
                    </span>
                  </div>
                </div>
                <div className="flex w-full items-center justify-between rounded-md bg-neutral-50 px-3 py-2">
                  <span className="text-caption font-caption text-neutral-700">
                    OOB Score
                  </span>
                  <span className="text-body-bold font-body-bold text-neutral-900">
                    92.1%
                  </span>
                </div>
              </div>
            </div>
            <div className="flex w-full flex-col items-start gap-4 rounded-lg border border-solid border-neutral-300 bg-neutral-0 px-4 py-4 shadow-sm">
              <div className="flex w-full items-center gap-4">
                <IconWithBackground
                  variant="neutral"
                  size="medium"
                  icon={<FeatherSettings />}
                  square={true}
                />
                <span className="grow shrink-0 basis-0 text-heading-3 font-heading-3 text-default-font">
                  Model Management
                </span>
              </div>
              <div className="flex w-full flex-col items-start gap-2">
                <Button
                  className="h-12 w-full flex-none"
                  variant="brand-secondary"
                  size="large"
                  icon={<FeatherPlay />}
                  onClick={(event: React.MouseEvent<HTMLButtonElement>) => {}}
                >
                  Train New Model
                </Button>
                <Button
                  className="h-12 w-full flex-none"
                  variant="neutral-secondary"
                  size="large"
                  icon={<FeatherRefreshCw />}
                  onClick={(event: React.MouseEvent<HTMLButtonElement>) => {}}
                >
                  Run Inference
                </Button>
                <div className="flex w-full items-center gap-2">
                  <Button
                    className="h-12 grow shrink-0 basis-0"
                    variant="neutral-secondary"
                    size="large"
                    icon={<FeatherUpload />}
                    onClick={(event: React.MouseEvent<HTMLButtonElement>) => {}}
                  >
                    Upload Model
                  </Button>
                </div>
              </div>
              <div className="flex h-px w-full flex-none flex-col items-center gap-2 bg-neutral-300" />
              <div className="flex w-full flex-col items-start gap-2">
                <span className="text-caption-bold font-caption-bold text-neutral-700">
                  Recent models
                </span>
                <div className="flex w-full items-center gap-2 rounded-md bg-brand-50 px-3 py-2">
                  <span className="grow shrink-0 basis-0 text-body-bold font-body-bold text-neutral-900">
                    v2.4.1
                  </span>
                  <Badge variant="success">94.2%</Badge>
                </div>
                <div className="flex w-full items-center gap-2 rounded-md bg-neutral-50 px-3 py-2">
                  <span className="grow shrink-0 basis-0 text-body font-body text-neutral-900">
                    v2.4.0
                  </span>
                  <Badge variant="neutral">92.8%</Badge>
                </div>
                <div className="flex w-full items-center gap-2 rounded-md bg-neutral-50 px-3 py-2">
                  <span className="grow shrink-0 basis-0 text-body font-body text-neutral-900">
                    v2.3.2
                  </span>
                  <Badge variant="neutral">91.5%</Badge>
                </div>
              </div>
            </div>
          </div>
          <div className="flex grow shrink-0 basis-0 flex-col items-start gap-6 self-stretch">
            <div className="flex w-full grow shrink-0 basis-0 flex-col items-start gap-4 rounded-lg border border-solid border-neutral-300 bg-neutral-0 px-4 py-4 shadow-sm">
              <div className="flex w-full items-center gap-4">
                <IconWithBackground
                  variant="error"
                  size="medium"
                  icon={<FeatherAlertCircle />}
                  square={true}
                />
                <span className="grow shrink-0 basis-0 text-heading-3 font-heading-3 text-neutral-900">
                  At-Risk Patients
                </span>
                <TextField
                  className="h-auto w-64 flex-none"
                  label=""
                  helpText=""
                  icon={<FeatherSearch />}
                >
                  <TextField.Input
                    placeholder="Search patients"
                    value=""
                    onChange={(
                      event: React.ChangeEvent<HTMLInputElement>
                    ) => {}}
                  />
                </TextField>
              </div>
              <div className="flex w-full flex-col items-start overflow-auto">
                <div className="flex w-full items-center gap-4 border-b-2 border-solid border-neutral-300 bg-neutral-100 px-4 py-2">
                  <span className="w-24 flex-none text-caption-bold font-caption-bold text-neutral-900">
                    Patient ID
                  </span>
                  <span className="w-20 flex-none text-caption-bold font-caption-bold text-neutral-900">
                    Risk Score
                  </span>
                  <span className="w-16 flex-none text-caption-bold font-caption-bold text-neutral-900">
                    Level
                  </span>
                  <span className="w-16 flex-none text-caption-bold font-caption-bold text-neutral-900">
                    Battery
                  </span>
                  <span className="w-20 flex-none text-caption-bold font-caption-bold text-neutral-900">
                    Impedance
                  </span>
                  <span className="w-20 flex-none text-caption-bold font-caption-bold text-neutral-900">
                    Threshold
                  </span>
                  <span className="grow shrink-0 basis-0 text-caption-bold font-caption-bold text-neutral-900">
                    Last Update
                  </span>
                  <span className="w-32 flex-none text-caption-bold font-caption-bold text-neutral-900 text-right">
                    Actions
                  </span>
                </div>
                <div className="flex w-full items-center gap-4 border-b border-solid border-neutral-300 px-4 py-3 hover:bg-neutral-100">
                  <span className="w-24 flex-none text-body-bold font-body-bold text-neutral-900">
                    PAT-2847
                  </span>
                  <span className="w-20 flex-none text-body-bold font-body-bold text-error-700">
                    0.94
                  </span>
                  <div className="flex w-16 flex-none items-start">
                    <Badge variant="error">HIGH</Badge>
                  </div>
                  <span className="w-16 flex-none text-caption font-caption text-warning-800">
                    2.65V
                  </span>
                  <div className="flex w-20 flex-none items-center gap-1">
                    <span className="text-caption font-caption text-error-700">
                      1250Ω
                    </span>
                    <FeatherTrendingUp className="text-caption font-caption text-error-700" />
                  </div>
                  <div className="flex w-20 flex-none items-center gap-1">
                    <span className="text-caption font-caption text-neutral-900">
                      2.1V
                    </span>
                    <FeatherMinus className="text-caption font-caption text-neutral-600" />
                  </div>
                  <span className="grow shrink-0 basis-0 text-caption font-caption text-neutral-700">
                    2 min ago
                  </span>
                  <div className="flex w-32 flex-none items-center justify-end gap-1">
                    <IconButton
                      size="small"
                      icon={<FeatherEye />}
                      onClick={(
                        event: React.MouseEvent<HTMLButtonElement>
                      ) => {}}
                    />
                    <IconButton
                      size="small"
                      icon={<FeatherCheckCircle />}
                      onClick={(
                        event: React.MouseEvent<HTMLButtonElement>
                      ) => {}}
                    />
                    <IconButton
                      size="small"
                      icon={<FeatherMail />}
                      onClick={(
                        event: React.MouseEvent<HTMLButtonElement>
                      ) => {}}
                    />
                  </div>
                </div>
                <div className="flex w-full items-center gap-4 border-b border-solid border-neutral-300 px-4 py-3 hover:bg-neutral-100">
                  <span className="w-24 flex-none text-body-bold font-body-bold text-neutral-900">
                    PAT-1923
                  </span>
                  <span className="w-20 flex-none text-body-bold font-body-bold text-error-700">
                    0.87
                  </span>
                  <div className="flex w-16 flex-none items-start">
                    <Badge variant="error">HIGH</Badge>
                  </div>
                  <span className="w-16 flex-none text-caption font-caption text-neutral-900">
                    2.78V
                  </span>
                  <div className="flex w-20 flex-none items-center gap-1">
                    <span className="text-caption font-caption text-neutral-900">
                      520Ω
                    </span>
                    <FeatherMinus className="text-caption font-caption text-neutral-600" />
                  </div>
                  <div className="flex w-20 flex-none items-center gap-1">
                    <span className="text-caption font-caption text-warning-800">
                      3.2V
                    </span>
                    <FeatherTrendingUp className="text-caption font-caption text-warning-800" />
                  </div>
                  <span className="grow shrink-0 basis-0 text-caption font-caption text-neutral-700">
                    5 min ago
                  </span>
                  <div className="flex w-32 flex-none items-center justify-end gap-1">
                    <IconButton
                      size="small"
                      icon={<FeatherEye />}
                      onClick={(
                        event: React.MouseEvent<HTMLButtonElement>
                      ) => {}}
                    />
                    <IconButton
                      size="small"
                      icon={<FeatherCheckCircle />}
                      onClick={(
                        event: React.MouseEvent<HTMLButtonElement>
                      ) => {}}
                    />
                    <IconButton
                      size="small"
                      icon={<FeatherMail />}
                      onClick={(
                        event: React.MouseEvent<HTMLButtonElement>
                      ) => {}}
                    />
                  </div>
                </div>
                <div className="flex w-full items-center gap-4 border-b border-solid border-neutral-300 px-4 py-3 hover:bg-neutral-100">
                  <span className="w-24 flex-none text-body-bold font-body-bold text-neutral-900">
                    PAT-5721
                  </span>
                  <span className="w-20 flex-none text-body-bold font-body-bold text-warning-800">
                    0.72
                  </span>
                  <div className="flex w-16 flex-none items-start">
                    <Badge variant="warning">MED</Badge>
                  </div>
                  <span className="w-16 flex-none text-caption font-caption text-neutral-900">
                    2.71V
                  </span>
                  <div className="flex w-20 flex-none items-center gap-1">
                    <span className="text-caption font-caption text-neutral-900">
                      580Ω
                    </span>
                    <FeatherMinus className="text-caption font-caption text-neutral-600" />
                  </div>
                  <div className="flex w-20 flex-none items-center gap-1">
                    <span className="text-caption font-caption text-neutral-900">
                      2.4V
                    </span>
                    <FeatherMinus className="text-caption font-caption text-neutral-600" />
                  </div>
                  <span className="grow shrink-0 basis-0 text-caption font-caption text-neutral-700">
                    8 min ago
                  </span>
                  <div className="flex w-32 flex-none items-center justify-end gap-1">
                    <IconButton
                      size="small"
                      icon={<FeatherEye />}
                      onClick={(
                        event: React.MouseEvent<HTMLButtonElement>
                      ) => {}}
                    />
                    <IconButton
                      size="small"
                      icon={<FeatherCheckCircle />}
                      onClick={(
                        event: React.MouseEvent<HTMLButtonElement>
                      ) => {}}
                    />
                    <IconButton
                      size="small"
                      icon={<FeatherMail />}
                      onClick={(
                        event: React.MouseEvent<HTMLButtonElement>
                      ) => {}}
                    />
                  </div>
                </div>
                <div className="flex w-full items-center gap-4 border-b border-solid border-neutral-300 px-4 py-3 hover:bg-neutral-100">
                  <span className="w-24 flex-none text-body-bold font-body-bold text-neutral-900">
                    PAT-3294
                  </span>
                  <span className="w-20 flex-none text-body-bold font-body-bold text-warning-800">
                    0.68
                  </span>
                  <div className="flex w-16 flex-none items-start">
                    <Badge variant="warning">MED</Badge>
                  </div>
                  <span className="w-16 flex-none text-caption font-caption text-warning-800">
                    2.68V
                  </span>
                  <div className="flex w-20 flex-none items-center gap-1">
                    <span className="text-caption font-caption text-neutral-900">
                      495Ω
                    </span>
                    <FeatherMinus className="text-caption font-caption text-neutral-600" />
                  </div>
                  <div className="flex w-20 flex-none items-center gap-1">
                    <span className="text-caption font-caption text-neutral-900">
                      1.9V
                    </span>
                    <FeatherMinus className="text-caption font-caption text-neutral-600" />
                  </div>
                  <span className="grow shrink-0 basis-0 text-caption font-caption text-neutral-700">
                    12 min ago
                  </span>
                  <div className="flex w-32 flex-none items-center justify-end gap-1">
                    <IconButton
                      size="small"
                      icon={<FeatherEye />}
                      onClick={(
                        event: React.MouseEvent<HTMLButtonElement>
                      ) => {}}
                    />
                    <IconButton
                      size="small"
                      icon={<FeatherCheckCircle />}
                      onClick={(
                        event: React.MouseEvent<HTMLButtonElement>
                      ) => {}}
                    />
                    <IconButton
                      size="small"
                      icon={<FeatherMail />}
                      onClick={(
                        event: React.MouseEvent<HTMLButtonElement>
                      ) => {}}
                    />
                  </div>
                </div>
                <div className="flex w-full items-center gap-4 px-4 py-3 hover:bg-neutral-100">
                  <span className="w-24 flex-none text-body-bold font-body-bold text-neutral-900">
                    PAT-8472
                  </span>
                  <span className="w-20 flex-none text-body-bold font-body-bold text-warning-800">
                    0.61
                  </span>
                  <div className="flex w-16 flex-none items-start">
                    <Badge variant="warning">MED</Badge>
                  </div>
                  <span className="w-16 flex-none text-caption font-caption text-neutral-900">
                    2.79V
                  </span>
                  <div className="flex w-20 flex-none items-center gap-1">
                    <span className="text-caption font-caption text-neutral-900">
                      510Ω
                    </span>
                    <FeatherTrendingDown className="text-caption font-caption text-success-600" />
                  </div>
                  <div className="flex w-20 flex-none items-center gap-1">
                    <span className="text-caption font-caption text-neutral-900">
                      2.0V
                    </span>
                    <FeatherMinus className="text-caption font-caption text-neutral-600" />
                  </div>
                  <span className="grow shrink-0 basis-0 text-caption font-caption text-neutral-700">
                    15 min ago
                  </span>
                  <div className="flex w-32 flex-none items-center justify-end gap-1">
                    <IconButton
                      size="small"
                      icon={<FeatherEye />}
                      onClick={(
                        event: React.MouseEvent<HTMLButtonElement>
                      ) => {}}
                    />
                    <IconButton
                      size="small"
                      icon={<FeatherCheckCircle />}
                      onClick={(
                        event: React.MouseEvent<HTMLButtonElement>
                      ) => {}}
                    />
                    <IconButton
                      size="small"
                      icon={<FeatherMail />}
                      onClick={(
                        event: React.MouseEvent<HTMLButtonElement>
                      ) => {}}
                    />
                  </div>
                </div>
              </div>
              <Button
                variant="brand-tertiary"
                size="small"
                iconRight={<FeatherChevronRight />}
                onClick={(event: React.MouseEvent<HTMLButtonElement>) => {}}
              >
                View all 23 high-risk patients
              </Button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

export default PacemakerRiskDashboard;
