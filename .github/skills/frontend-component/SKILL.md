---
name: frontend-component
description: Frontend component development guide for creating React components, UI pages, forms, data tables, dialogs, and modifying the frontend interface. Use when creating React components, TanStack Router pages, forms, data tables, dialogs, UI components, or implementing frontend features with React 19, TypeScript, TanStack Query, shadcn/ui, and Tailwind CSS.
---

# Frontend Component Skill

This skill guides you through creating React components and pages for this frontend application built with React 19, TypeScript, TanStack Router, TanStack Query, shadcn/ui, and Tailwind CSS 4.

## When to Use This Skill

- Creating new React components
- Building UI pages with file-based routing
- Implementing forms and data tables
- Creating dialogs and modals
- Integrating with backend API endpoints
- Implementing data fetching and mutations
- Building responsive layouts

## Technology Stack

- **React**: 19 (with Suspense and Server Components patterns)
- **TypeScript**: Strict mode enabled
- **Router**: TanStack Router (file-based routing)
- **Data Fetching**: TanStack Query (React Query v5)
- **UI Components**: shadcn/ui (Radix UI primitives)
- **Styling**: Tailwind CSS 4
- **Linter/Formatter**: Biome
- **Build Tool**: Vite 7
- **Package Manager**: bun

**Reference**: `.github/copilot-instructions.md` lines 9-10

## File-Based Routing with TanStack Router

### Creating a New Page Route

Routes are defined in `frontend/src/routes/` using TanStack Router's file-based routing:

```typescript
// frontend/src/routes/_layout/{things}.tsx
import { useSuspenseQuery } from "@tanstack/react-query"
import { createFileRoute } from "@tanstack/router-router"
import { Suspense } from "react"

import { {Thing}sService } from "@/client"
import { DataTable } from "@/components/Common/DataTable"
import Add{Thing} from "@/components/{Thing}s/Add{Thing}"
import { columns } from "@/components/{Thing}s/columns"
import Pending{Thing}s from "@/components/Pending/Pending{Thing}s"

function get{Thing}sQueryOptions() {
  return {
    queryFn: () => {Thing}sService.read{Thing}s({ skip: 0, limit: 100 }),
    queryKey: ["{things}"],
  }
}

export const Route = createFileRoute("/_layout/{things}")({
  component: {Thing}s,
  head: () => ({
    meta: [
      {
        title: "{Thing}s - FastAPI Cloud",
      },
    ],
  }),
})

function {Thing}sTableContent() {
  const { data: {things} } = useSuspenseQuery(get{Thing}sQueryOptions())

  if ({things}.data.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center text-center py-12">
        <div className="rounded-full bg-muted p-4 mb-4">
          <Search className="h-8 w-8 text-muted-foreground" />
        </div>
        <h3 className="text-lg font-semibold">You don't have any {things} yet</h3>
        <p className="text-muted-foreground">Add a new {thing} to get started</p>
      </div>
    )
  }

  return <DataTable columns={columns} data={{things}.data} />
}

function {Thing}sTable() {
  return (
    <Suspense fallback={<Pending{Thing}s />}>
      <{Thing}sTableContent />
    </Suspense>
  )
}

function {Thing}s() {
  return (
    <div className="flex flex-col gap-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold tracking-tight">{Thing}s</h1>
          <p className="text-muted-foreground">Create and manage your {things}</p>
        </div>
        <Add{Thing} />
      </div>
      <{Thing}sTable />
    </div>
  )
}
```

**Key patterns**:
- `createFileRoute` defines the route configuration
- `useSuspenseQuery` for data fetching (requires `<Suspense>` boundary)
- Separate content component for suspense boundary
- Empty state handling
- `head` function for meta tags

**Reference**: `frontend/src/routes/_layout/items.tsx`

### Route File Naming

- `_layout/*.tsx` - Pages within authenticated layout
- `login.tsx` - Public pages (no underscore prefix)
- `_layout.tsx` - Layout wrapper component

Routes are automatically generated - check `frontend/src/routeTree.gen.ts` (DO NOT edit manually).

**Reference**: memory: auto-generated files

## Data Fetching with TanStack Query

### Query Pattern (useSuspenseQuery)

For data fetching with automatic suspense:

```typescript
import { useSuspenseQuery } from "@tanstack/react-query"
import { {Thing}sService } from "@/client"

function get{Thing}sQueryOptions() {
  return {
    queryFn: () => {Thing}sService.read{Thing}s({ skip: 0, limit: 100 }),
    queryKey: ["{things}"],
  }
}

function Component() {
  const { data: {things} } = useSuspenseQuery(get{Thing}sQueryOptions())

  return <div>{things}.data.map(...)</div>
}
```

**Important**:
- Must be wrapped in `<Suspense>` boundary
- Automatically suspends during loading
- No need for loading state management

### Query Pattern (useQuery)

For optional data fetching:

```typescript
import { useQuery } from "@tanstack/react-query"

function Component() {
  const { data: user } = useQuery({
    queryKey: ["currentUser"],
    queryFn: UsersService.readUserMe,
    enabled: isLoggedIn(),  // Conditional fetching
  })

  if (!user) return null

  return <div>{user.full_name}</div>
}
```

**Reference**: `frontend/src/hooks/useAuth.ts` lines 23-27

## Mutation Pattern with Query Invalidation

For create, update, delete operations:

```typescript
import { useMutation, useQueryClient } from "@tanstack/react-query"
import { {Thing}sService, type {Thing}Create } from "@/client"
import { handleError } from "@/utils"
import useCustomToast from "@/hooks/useCustomToast"

function use{Thing}Mutations() {
  const queryClient = useQueryClient()
  const { showErrorToast } = useCustomToast()

  const createMutation = useMutation({
    mutationFn: (data: {Thing}Create) =>
      {Thing}sService.create{Thing}({ requestBody: data }),
    onError: handleError.bind(showErrorToast),
    onSettled: () => {
      queryClient.invalidateQueries({ queryKey: ["{things}"] })
    },
  })

  const updateMutation = useMutation({
    mutationFn: ({ id, data }: { id: string; data: {Thing}Update }) =>
      {Thing}sService.update{Thing}({ id, requestBody: data }),
    onError: handleError.bind(showErrorToast),
    onSettled: () => {
      queryClient.invalidateQueries({ queryKey: ["{things}"] })
    },
  })

  const deleteMutation = useMutation({
    mutationFn: (id: string) =>
      {Thing}sService.delete{Thing}({ id }),
    onError: handleError.bind(showErrorToast),
    onSettled: () => {
      queryClient.invalidateQueries({ queryKey: ["{things}"] })
    },
  })

  return { createMutation, updateMutation, deleteMutation }
}
```

**Key points**:
- Use `onSettled` (NOT `onSuccess`) for query invalidation - ensures it runs even on error
- Use `handleError.bind(showErrorToast)` for consistent error handling
- Invalidate queries to trigger refetch and update UI

**Reference**: `frontend/src/hooks/useAuth.ts` lines 29-39

## Component Organization

For each feature, create these components in `frontend/src/components/{Thing}s/`:

### 1. Add{Thing}.tsx - Creation Dialog

```typescript
import { useMutation, useQueryClient } from "@tanstack/react-query"
import { useState } from "react"

import { {Thing}sService, type {Thing}Create } from "@/client"
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { handleError } from "@/utils"
import useCustomToast from "@/hooks/useCustomToast"

export default function Add{Thing}() {
  const [open, setOpen] = useState(false)
  const queryClient = useQueryClient()
  const { showSuccessToast, showErrorToast } = useCustomToast()

  const mutation = useMutation({
    mutationFn: (data: {Thing}Create) =>
      {Thing}sService.create{Thing}({ requestBody: data }),
    onSuccess: () => {
      showSuccessToast("{Thing} created successfully")
      setOpen(false)
    },
    onError: handleError.bind(showErrorToast),
    onSettled: () => {
      queryClient.invalidateQueries({ queryKey: ["{things}"] })
    },
  })

  const handleSubmit = (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault()
    const formData = new FormData(e.currentTarget)
    const data = {
      field1: formData.get("field1") as string,
      field2: formData.get("field2") as string,
    }
    mutation.mutate(data)
  }

  return (
    <Dialog open={open} onOpenChange={setOpen}>
      <DialogTrigger asChild>
        <Button>Add {Thing}</Button>
      </DialogTrigger>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>Add {Thing}</DialogTitle>
        </DialogHeader>
        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <Label htmlFor="field1">Field 1</Label>
            <Input id="field1" name="field1" required />
          </div>
          <div>
            <Label htmlFor="field2">Field 2</Label>
            <Input id="field2" name="field2" />
          </div>
          <Button type="submit" disabled={mutation.isPending}>
            {mutation.isPending ? "Creating..." : "Create"}
          </Button>
        </form>
      </DialogContent>
    </Dialog>
  )
}
```

### 2. Edit{Thing}.tsx - Edit Dialog

Similar pattern to Add, but receives existing data as props:

```typescript
interface Edit{Thing}Props {
  {thing}: {Thing}Public
}

export default function Edit{Thing}({ {thing} }: Edit{Thing}Props) {
  // Similar to Add, but pre-populate form with {thing} data
  // Use updateMutation instead of createMutation
}
```

### 3. Delete{Thing}.tsx - Delete Confirmation Dialog

```typescript
import { useMutation, useQueryClient } from "@tanstack/react-query"
import { {Thing}sService } from "@/client"
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from "@/components/ui/alert-dialog"

interface Delete{Thing}Props {
  id: string
  open: boolean
  onOpenChange: (open: boolean) => void
}

export default function Delete{Thing}({ id, open, onOpenChange }: Delete{Thing}Props) {
  const queryClient = useQueryClient()

  const mutation = useMutation({
    mutationFn: (id: string) => {Thing}sService.delete{Thing}({ id }),
    onSettled: () => {
      queryClient.invalidateQueries({ queryKey: ["{things}"] })
      onOpenChange(false)
    },
  })

  return (
    <AlertDialog open={open} onOpenChange={onOpenChange}>
      <AlertDialogContent>
        <AlertDialogHeader>
          <AlertDialogTitle>Are you sure?</AlertDialogTitle>
          <AlertDialogDescription>
            This action cannot be undone.
          </AlertDialogDescription>
        </AlertDialogHeader>
        <AlertDialogFooter>
          <AlertDialogCancel>Cancel</AlertDialogCancel>
          <AlertDialogAction onClick={() => mutation.mutate(id)}>
            Delete
          </AlertDialogAction>
        </AlertDialogFooter>
      </AlertDialogContent>
    </AlertDialog>
  )
}
```

### 4. columns.tsx - DataTable Column Definitions

```typescript
import { type ColumnDef } from "@tanstack/react-table"
import { type {Thing}Public } from "@/client"
import ActionsMenu from "@/components/Common/ActionsMenu"

export const columns: ColumnDef<{Thing}Public>[] = [
  {
    accessorKey: "field1",
    header: "Field 1",
  },
  {
    accessorKey: "field2",
    header: "Field 2",
  },
  {
    accessorKey: "created_at",
    header: "Created At",
    cell: ({ row }) => {
      const date = new Date(row.getValue("created_at"))
      return date.toLocaleDateString()
    },
  },
  {
    id: "actions",
    cell: ({ row }) => {
      const {thing} = row.original
      return <ActionsMenu {thing}={{thing}} />
    },
  },
]
```

## Existing Hooks

Leverage these custom hooks from `frontend/src/hooks/`:

### useAuth

```typescript
import useAuth from "@/hooks/useAuth"

function Component() {
  const { user, logout } = useAuth()

  return <div>{user?.full_name}</div>
}
```

**Provides**: `user`, `loginMutation`, `signUpMutation`, `logout`

**Reference**: `frontend/src/hooks/useAuth.ts`

### useCustomToast

```typescript
import useCustomToast from "@/hooks/useCustomToast"

function Component() {
  const { showSuccessToast, showErrorToast } = useCustomToast()

  showSuccessToast("Operation successful")
  showErrorToast("Operation failed")
}
```

### useCopyToClipboard

```typescript
import useCopyToClipboard from "@/hooks/useCopyToClipboard"

function Component() {
  const { copyToClipboard } = useCopyToClipboard()

  const handleCopy = () => {
    copyToClipboard("text to copy")
  }
}
```

### useMobile

```typescript
import { useMobile } from "@/hooks/useMobile"

function Component() {
  const isMobile = useMobile()

  return isMobile ? <MobileView /> : <DesktopView />
}
```

## Auto-Generated Files (DO NOT EDIT)

These files are managed by tools and must NOT be manually edited:

### frontend/src/client/**

Generated by openapi-ts from backend OpenAPI spec. Regenerate with:

```bash
bash ./scripts/generate-client.sh
```

Contains:
- API service classes (`ItemsService`, `UsersService`, etc.)
- TypeScript types (`ItemPublic`, `UserPublic`, etc.)
- API client configuration

**Reference**: memory: auto-generated files

### frontend/src/components/ui/**

Managed by shadcn/ui. Add components with:

```bash
cd frontend
bunx shadcn@latest add button
cd ..
```

**Reference**: memory: auto-generated files

### frontend/src/routeTree.gen.ts

Generated by TanStack Router plugin during build. Do not edit.

**Reference**: memory: auto-generated files

## Styling with Tailwind CSS 4

### Utility-First Approach

```typescript
<div className="flex flex-col gap-6">
  <h1 className="text-2xl font-bold tracking-tight">Title</h1>
  <p className="text-muted-foreground">Description</p>
</div>
```

### Responsive Design

```typescript
<div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
  {/* Responsive grid */}
</div>
```

### Theme Variables

Use semantic color classes:

- `bg-background` / `text-foreground` - Base colors
- `bg-muted` / `text-muted-foreground` - Muted variants
- `bg-primary` / `text-primary-foreground` - Primary colors
- `bg-destructive` - Destructive actions
- `border` - Border color

## Biome Conventions

The codebase uses Biome for linting and formatting:

- **Quotes**: Double quotes (`"`)
- **Indentation**: Spaces (2 spaces)
- **Semicolons**: Only as needed (ASI-safe)
- **Line width**: 100 characters

**Auto-format**:

```bash
bun run lint
```

**Reference**: `.github/copilot-instructions.md` line 182, memory: linting tools

## TypeScript Best Practices

### Import Types

```typescript
import { type ItemPublic, type ItemCreate } from "@/client"
```

Use `type` keyword when importing only types.

### Component Props

```typescript
interface {Thing}FormProps {
  {thing}?: {Thing}Public
  onSubmit: (data: {Thing}Create) => void
}

export default function {Thing}Form({ {thing}, onSubmit }: {Thing}FormProps) {
  // Component implementation
}
```

### Event Handlers

```typescript
const handleSubmit = (e: React.FormEvent<HTMLFormElement>) => {
  e.preventDefault()
  // Handle form submission
}

const handleClick = (e: React.MouseEvent<HTMLButtonElement>) => {
  // Handle click
}
```

## Building and Linting

### Lint Frontend

```bash
bun run lint
```

Runs Biome linter and formatter (auto-fixes issues).

**Reference**: `.github/copilot-instructions.md` line 108, memory: linting tools

### Build Frontend

```bash
cd frontend && bun run build && cd ..
```

Runs TypeScript check + Vite build.

**Reference**: `.github/copilot-instructions.md` lines 111-112

### Run E2E Tests (Optional)

```bash
docker compose up -d --wait backend
cd frontend && bunx playwright test && cd ..
```

**Reference**: `.github/copilot-instructions.md` lines 114-116

## Common Pitfalls

- **Editing auto-generated files** - Never manually edit `src/client/**`, `src/components/ui/**`, `routeTree.gen.ts`
- **Using single quotes** - Biome enforces double quotes
- **Forgetting Suspense boundary** - `useSuspenseQuery` requires `<Suspense>` wrapper
- **Using `onSuccess` for invalidation** - Use `onSettled` to ensure it runs even on error
- **Not using path aliases** - Use `@/` instead of relative imports (e.g., `@/client`, `@/components`)
- **Hardcoded API calls** - Always use generated service classes from `@/client`
- **Missing TypeScript types** - Leverage generated types from `@/client`
- **Not binding error handler** - Use `handleError.bind(showErrorToast)`, not `(err) => handleError(err, showErrorToast)`

## Component Checklist

- [ ] Created route file in `frontend/src/routes/_layout/{things}.tsx`
- [ ] Used `createFileRoute` for route definition
- [ ] Used `useSuspenseQuery` with `<Suspense>` boundary
- [ ] Created query options function (`get{Thing}sQueryOptions`)
- [ ] Implemented empty state handling
- [ ] Created component directory `frontend/src/components/{Thing}s/`
- [ ] Created `Add{Thing}.tsx` with mutation and form
- [ ] Created `Edit{Thing}.tsx` with mutation and pre-populated form
- [ ] Created `Delete{Thing}.tsx` with confirmation dialog
- [ ] Created `columns.tsx` with DataTable column definitions
- [ ] Used `onSettled` for query invalidation in mutations
- [ ] Used `handleError.bind(showErrorToast)` for error handling
- [ ] Used generated types and services from `@/client`
- [ ] Used path aliases (`@/`) for imports
- [ ] Followed Biome conventions (double quotes, spaces)
- [ ] Ran `bun run lint` and fixed all issues
- [ ] Ran `cd frontend && bun run build` to verify TypeScript compilation
- [ ] Did NOT manually edit `src/client/**`, `src/components/ui/**`, or `routeTree.gen.ts`
