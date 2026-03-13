import {
  type ColumnDef,
  flexRender,
  getCoreRowModel,
  getPaginationRowModel,
  getSortedRowModel,
  type SortingState,
  useReactTable,
} from "@tanstack/react-table"
import { ArrowUpDown, Search, TriangleAlert } from "lucide-react"
import { useMemo, useState } from "react"
import { Button } from "@/components/ui/button"
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select"
import { Skeleton } from "@/components/ui/skeleton"
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table"
import { cn } from "@/lib/utils"
import type { DashboardPatientRow } from "./types"

interface PatientListTableProps {
  data: DashboardPatientRow[]
  isLoading: boolean
  usingFallback: boolean
}

type RiskFilter = "all" | "high" | "medium" | "low"
type AlertFilter = "all" | "sent" | "none"

const RISK_THRESHOLDS = {
  high: 0.7,
  medium: 0.4,
}

function formatTimestamp(value: string) {
  return new Date(value).toLocaleString([], {
    year: "numeric",
    month: "2-digit",
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
    second: "2-digit",
  })
}

function formatRiskScorePercentage(riskScore: number | null) {
  if (riskScore === null) {
    return "--"
  }

  return `${(riskScore * 100).toLocaleString([], {
    maximumFractionDigits: 3,
  })}%`
}

function getRiskLabel(riskScore: number | null) {
  if (riskScore === null) {
    return {
      label: "Unscored",
      className: "bg-zinc-100 text-zinc-800 border-zinc-200",
    }
  }

  if (riskScore >= RISK_THRESHOLDS.high) {
    return {
      label: "High",
      className: "bg-red-100 text-red-900 border-red-200",
    }
  }

  if (riskScore >= RISK_THRESHOLDS.medium) {
    return {
      label: "Medium",
      className: "bg-amber-100 text-amber-900 border-amber-200",
    }
  }

  return {
    label: "Low",
    className: "bg-emerald-100 text-emerald-900 border-emerald-200",
  }
}

function PatientTableSkeleton() {
  const skeletonRows = [
    "row-1",
    "row-2",
    "row-3",
    "row-4",
    "row-5",
    "row-6",
    "row-7",
  ]

  return (
    <div className="space-y-3">
      <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
        <Skeleton className="h-9" />
        <Skeleton className="h-9" />
        <Skeleton className="h-9" />
        <Skeleton className="h-9" />
      </div>
      <div className="space-y-2 rounded-lg border p-3">
        {skeletonRows.map((rowKey) => (
          <Skeleton key={rowKey} className="h-8 w-full" />
        ))}
      </div>
    </div>
  )
}

function SortableHeader({
  title,
  onClick,
}: {
  title: string
  onClick: () => void
}) {
  return (
    <Button variant="ghost" className="-ml-3 h-8 px-3" onClick={onClick}>
      {title}
      <ArrowUpDown className="size-3.5" />
    </Button>
  )
}

function formatOhms(value: number) {
  return `${value.toFixed(1)} Ω`
}

function formatVoltage(value: number) {
  return `${value.toFixed(3)} V`
}

function formatOhmsDelta(value: number) {
  return `${value.toFixed(2)} Ω/day`
}

function formatVoltageDelta(value: number) {
  return `${value.toFixed(3)} V/day`
}

export function PatientListTable({
  data,
  isLoading,
  usingFallback,
}: PatientListTableProps) {
  const [sorting, setSorting] = useState<SortingState>([
    { id: "riskScore", desc: true },
  ])
  const [searchText, setSearchText] = useState("")
  const [riskFilter, setRiskFilter] = useState<RiskFilter>("all")
  const [alertFilter, setAlertFilter] = useState<AlertFilter>("all")

  const filteredData = useMemo(() => {
    return data.filter((row) => {
      const searchMatch = row.patientId
        .toString()
        .toLowerCase()
        .includes(searchText.trim().toLowerCase())

      const riskMatch =
        riskFilter === "all" ||
        (riskFilter === "high" &&
          row.riskScore !== null &&
          row.riskScore >= RISK_THRESHOLDS.high) ||
        (riskFilter === "medium" &&
          row.riskScore !== null &&
          row.riskScore >= RISK_THRESHOLDS.medium &&
          row.riskScore < RISK_THRESHOLDS.high) ||
        (riskFilter === "low" &&
          (row.riskScore === null || row.riskScore < RISK_THRESHOLDS.medium))

      const alertMatch =
        alertFilter === "all" ||
        (alertFilter === "sent" && row.alertsSent) ||
        (alertFilter === "none" && !row.alertsSent)

      return searchMatch && riskMatch && alertMatch
    })
  }, [data, searchText, riskFilter, alertFilter])

  const columns = useMemo<ColumnDef<DashboardPatientRow>[]>(
    () => [
      {
        accessorKey: "patientId",
        header: ({ column }) => (
          <SortableHeader
            title="Patient ID"
            onClick={() => column.toggleSorting(column.getIsSorted() === "asc")}
          />
        ),
        cell: ({ row }) => (
          <span className="font-medium tabular-nums">
            #{row.original.patientId}
          </span>
        ),
      },
      {
        accessorKey: "riskScore",
        header: ({ column }) => (
          <SortableHeader
            title="Risk Score"
            onClick={() => column.toggleSorting(column.getIsSorted() === "asc")}
          />
        ),
        sortingFn: "basic",
        cell: ({ row }) => {
          const risk = getRiskLabel(row.original.riskScore)
          return (
            <div className="flex items-center gap-2">
              <span className="font-semibold tabular-nums">
                {formatRiskScorePercentage(row.original.riskScore)}
              </span>
              <span
                className={cn(
                  "rounded-full border px-2 py-0.5 text-[11px] font-medium",
                  risk.className,
                )}
              >
                {risk.label}
              </span>
            </div>
          )
        },
      },
      {
        accessorKey: "leadImpedance",
        header: ({ column }) => (
          <SortableHeader
            title="Lead Impedance"
            onClick={() => column.toggleSorting(column.getIsSorted() === "asc")}
          />
        ),
        cell: ({ row }) => (
          <span className="tabular-nums">
            {formatOhms(row.original.leadImpedance)}
          </span>
        ),
      },
      {
        id: "leadImpedanceMeanCombined",
        accessorFn: (row) =>
          (row.leadImpedanceRollingMean3d + row.leadImpedanceRollingMean7d) / 2,
        header: ({ column }) => (
          <SortableHeader
            title="Lead Ω Mean (3d/7d)"
            onClick={() => column.toggleSorting(column.getIsSorted() === "asc")}
          />
        ),
        cell: ({ row }) => (
          <div className="space-y-0.5 text-xs tabular-nums leading-tight">
            <div>3d: {formatOhms(row.original.leadImpedanceRollingMean3d)}</div>
            <div>7d: {formatOhms(row.original.leadImpedanceRollingMean7d)}</div>
          </div>
        ),
      },
      {
        id: "leadImpedanceDeltaCombined",
        accessorFn: (row) =>
          (row.leadImpedanceDeltaPerDay3d + row.leadImpedanceDeltaPerDay7d) / 2,
        header: ({ column }) => (
          <SortableHeader
            title="Lead Δ/day (3d/7d)"
            onClick={() => column.toggleSorting(column.getIsSorted() === "asc")}
          />
        ),
        cell: ({ row }) => (
          <div className="space-y-0.5 text-xs tabular-nums leading-tight">
            <div>
              3d: {formatOhmsDelta(row.original.leadImpedanceDeltaPerDay3d)}
            </div>
            <div>
              7d: {formatOhmsDelta(row.original.leadImpedanceDeltaPerDay7d)}
            </div>
          </div>
        ),
      },
      {
        accessorKey: "captureThreshold",
        header: ({ column }) => (
          <SortableHeader
            title="Capture Threshold"
            onClick={() => column.toggleSorting(column.getIsSorted() === "asc")}
          />
        ),
        cell: ({ row }) => (
          <span className="tabular-nums">
            {row.original.captureThreshold.toFixed(2)} V
          </span>
        ),
      },
      {
        id: "captureThresholdMeanCombined",
        accessorFn: (row) =>
          (row.captureThresholdRollingMean3d +
            row.captureThresholdRollingMean7d) /
          2,
        header: ({ column }) => (
          <SortableHeader
            title="Capture V Mean (3d/7d)"
            onClick={() => column.toggleSorting(column.getIsSorted() === "asc")}
          />
        ),
        cell: ({ row }) => (
          <div className="space-y-0.5 text-xs tabular-nums leading-tight">
            <div>
              3d: {formatVoltage(row.original.captureThresholdRollingMean3d)}
            </div>
            <div>
              7d: {formatVoltage(row.original.captureThresholdRollingMean7d)}
            </div>
          </div>
        ),
      },
      {
        id: "captureThresholdDeltaCombined",
        accessorFn: (row) =>
          (row.captureThresholdDeltaPerDay3d +
            row.captureThresholdDeltaPerDay7d) /
          2,
        header: ({ column }) => (
          <SortableHeader
            title="Capture Δ/day (3d/7d)"
            onClick={() => column.toggleSorting(column.getIsSorted() === "asc")}
          />
        ),
        cell: ({ row }) => (
          <div className="space-y-0.5 text-xs tabular-nums leading-tight">
            <div>
              3d:{" "}
              {formatVoltageDelta(row.original.captureThresholdDeltaPerDay3d)}
            </div>
            <div>
              7d:{" "}
              {formatVoltageDelta(row.original.captureThresholdDeltaPerDay7d)}
            </div>
          </div>
        ),
      },
      {
        accessorKey: "batteryVoltage",
        header: ({ column }) => (
          <SortableHeader
            title="Battery Voltage"
            onClick={() => column.toggleSorting(column.getIsSorted() === "asc")}
          />
        ),
        cell: ({ row }) => (
          <span className="tabular-nums">
            {row.original.batteryVoltage.toFixed(2)} V
          </span>
        ),
      },
      {
        accessorKey: "lastUpdate",
        header: ({ column }) => (
          <SortableHeader
            title="Last Update"
            onClick={() => column.toggleSorting(column.getIsSorted() === "asc")}
          />
        ),
        cell: ({ row }) => (
          <span className="text-sm text-muted-foreground">
            {formatTimestamp(row.original.lastUpdate)}
          </span>
        ),
      },
    ],
    [],
  )

  const table = useReactTable({
    data: filteredData,
    columns,
    state: {
      sorting,
    },
    onSortingChange: setSorting,
    getCoreRowModel: getCoreRowModel(),
    getSortedRowModel: getSortedRowModel(),
    getPaginationRowModel: getPaginationRowModel(),
    initialState: {
      pagination: {
        pageSize: 15,
      },
    },
  })

  return (
    <Card className="h-full min-h-0 gap-4 py-5">
      <CardHeader className="gap-1 border-b pb-4">
        <div className="flex flex-wrap items-center justify-between gap-2">
          <CardTitle className="flex items-center gap-2 text-base">
            <TriangleAlert className="size-4 text-primary" />
            Patient List
          </CardTitle>
          {usingFallback ? (
            <span className="rounded-full border border-amber-300 bg-amber-50 px-2 py-1 text-xs text-amber-900">
              Showing fallback data
            </span>
          ) : null}
        </div>
        <CardDescription>
          Track patient risk, telemetry signal quality, and latest updates
        </CardDescription>
      </CardHeader>

      <CardContent className="flex min-h-0 flex-1 flex-col space-y-4">
        {isLoading ? (
          <PatientTableSkeleton />
        ) : (
          <div className="flex min-h-0 flex-1 flex-col gap-4">
            <div className="flex flex-col gap-2 lg:flex-row lg:items-center">
              <div className="relative w-full lg:max-w-xs">
                <Search className="pointer-events-none absolute left-2.5 top-2.5 size-4 text-muted-foreground" />
                <Input
                  placeholder="Search patient ID"
                  className="pl-8"
                  value={searchText}
                  onChange={(event) => setSearchText(event.target.value)}
                />
              </div>

              <div className="flex w-full flex-col gap-2 sm:flex-row lg:ml-auto lg:w-auto">
                <Select
                  value={riskFilter}
                  onValueChange={(value) => setRiskFilter(value as RiskFilter)}
                >
                  <SelectTrigger className="w-full sm:w-44">
                    <SelectValue placeholder="Filter by risk" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="all">All risk levels</SelectItem>
                    <SelectItem value="high">High risk</SelectItem>
                    <SelectItem value="medium">Medium risk</SelectItem>
                    <SelectItem value="low">Low risk</SelectItem>
                  </SelectContent>
                </Select>

                <Select
                  value={alertFilter}
                  onValueChange={(value) =>
                    setAlertFilter(value as AlertFilter)
                  }
                >
                  <SelectTrigger className="w-full sm:w-44">
                    <SelectValue placeholder="Filter by alerts" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="all">All alert states</SelectItem>
                    <SelectItem value="sent">Alerts sent</SelectItem>
                    <SelectItem value="none">No alerts sent</SelectItem>
                  </SelectContent>
                </Select>
              </div>
            </div>

            <div className="min-h-0 flex-1 overflow-hidden rounded-lg border">
              <div className="h-full overflow-y-auto">
                <Table className="w-full">
                  <TableHeader>
                    {table.getHeaderGroups().map((headerGroup) => (
                      <TableRow
                        key={headerGroup.id}
                        className="hover:bg-transparent"
                      >
                        {headerGroup.headers.map((header) => (
                          <TableHead key={header.id}>
                            {header.isPlaceholder
                              ? null
                              : flexRender(
                                  header.column.columnDef.header,
                                  header.getContext(),
                                )}
                          </TableHead>
                        ))}
                      </TableRow>
                    ))}
                  </TableHeader>

                  <TableBody>
                    {table.getRowModel().rows.length > 0 ? (
                      table.getRowModel().rows.map((row) => (
                        <TableRow key={row.id}>
                          {row.getVisibleCells().map((cell) => (
                            <TableCell key={cell.id}>
                              {flexRender(
                                cell.column.columnDef.cell,
                                cell.getContext(),
                              )}
                            </TableCell>
                          ))}
                        </TableRow>
                      ))
                    ) : (
                      <TableRow className="hover:bg-transparent">
                        <TableCell
                          colSpan={columns.length}
                          className="h-20 text-center text-muted-foreground"
                        >
                          No patients match the current search and filters.
                        </TableCell>
                      </TableRow>
                    )}
                  </TableBody>
                </Table>
              </div>
            </div>

            <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
              <p className="text-sm text-muted-foreground">
                Showing{" "}
                <span className="font-medium text-foreground">
                  {table.getRowModel().rows.length}
                </span>{" "}
                patients on page {table.getState().pagination.pageIndex + 1} of{" "}
                {Math.max(1, table.getPageCount())}
              </p>
              <div className="flex items-center gap-2">
                <Select
                  value={`${table.getState().pagination.pageSize}`}
                  onValueChange={(value) => table.setPageSize(Number(value))}
                >
                  <SelectTrigger className="h-8 w-32">
                    <SelectValue placeholder="Rows" />
                  </SelectTrigger>
                  <SelectContent side="top">
                    {[15, 30, 50].map((pageSize) => (
                      <SelectItem key={pageSize} value={`${pageSize}`}>
                        {pageSize} rows
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
                <Button
                  variant="outline"
                  size="sm"
                  disabled={!table.getCanPreviousPage()}
                  onClick={() => table.previousPage()}
                >
                  Previous
                </Button>
                <Button
                  variant="outline"
                  size="sm"
                  disabled={!table.getCanNextPage()}
                  onClick={() => table.nextPage()}
                >
                  Next
                </Button>
              </div>
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  )
}
