# Waypoint-Routes Integration Specification

## Overview
This document describes the integration between the frontend waypoint management system and the backend routes system. The goal is to unify the local waypoint queue with persistent backend routes while maintaining a clear separation between route storage and drone mission posting.

## Current State

### Two Separate Systems
1. **Local Queue** (`appSlice.queuedWaypoints`)
   - Client-side staging area
   - localStorage persistence
   - Used for creating/editing waypoints
   - Posted to drone via "GCOM POST"

2. **Backend Routes** (`dataSlice.currentRoute`)
   - Persistent Django models (Route, OrderedWaypoint)
   - REST API for CRUD operations
   - Currently disconnected from waypoint workflow

### The Problem
These systems don't communicate - users can't save their waypoint work as routes, and routes can't be loaded into the working area.

## Desired State

### Unified System: Current Route as Working State

Remove the separation between local queue and current route:
- `dataSlice.currentRoute.waypoints` becomes the single source of truth for what the user is working on
- All waypoint operations (create, edit, delete, reorder) work directly on `currentRoute.waypoints`
- Changes propagate to backend via explicit "Save to Backend" button
- The `appSlice.queuedWaypoints` can be deprecated/removed

### Key Architectural Decisions

#### 1. Route Selection & Loading
**Behavior**: When user selects a route from dropdown:
- **Replace entirely** - local working state is replaced with selected route's waypoints
- No unsaved changes issue - all changes are saved before switching routes (via "Save to Backend" button)
- Selection loads route into `dataSlice.currentRoute`

**Implementation**:
- RouteSelector dropdown triggers `switchToRoute(id)` thunk
- Thunk fetches route from backend, dispatches `setCurrentRoute`
- Working area immediately reflects new route's waypoints

#### 2. Saving Changes to Backend
**Behavior**: Manual save via button click
- User clicks "Save to Backend" button
- All changes (waypoint edits, additions, deletions, reorders, route name) POST to backend
- Initially: one button for all saves
- Future: could be automatic on blur/form submission

**Implementation**:
- Add "Save to Backend" button in WaypointStatusCard
- Button triggers save operation that:
  - Updates route name if changed: `PUT /api/route/{id}/`
  - Syncs waypoints: `POST /api/waypoint/` for new waypoints, `PUT /api/waypoint/{id}/` for edits
  - Reorders waypoints: `POST /api/route/{id}/reorder-waypoints/`
- Could batch these into a single operation or make sequential calls

#### 3. Creating New Routes
**Behavior**: Create empty route immediately when user clicks "New Route"
- Route created in backend with user-provided name
- New empty route becomes `currentRoute`
- User can then add waypoints to it

**Implementation**:
- RouteSelector "New Route" dialog already exists
- `createNewRoute` thunk already POSTs to backend
- After creation, automatically set as current route

#### 4. Route Name Editing
**Behavior**: Route name can be edited in frontend
- Changes saved when user clicks "Save to Backend"
- Name is part of route data, not separate save operation

**Implementation**:
- Could add inline edit to RouteSelector showing current route name
- Or just rely on "Save to Backend" to push name changes
- Updates `currentRoute.name` locally, saved with waypoint changes

#### 5. Posting to Drone
**Behavior**: "Post Route to Drone" button sends waypoints to mission-planner
- Posts whatever is in `currentRoute.waypoints` (local state)
- Goes to `/api/drone/queue` endpoint
- Backend forwards to mission-planner (DroneApiClient)
- **No connection to backend Route models** - purely a drone operation

**Implementation**:
- Rename "GCOM POST" button to "Post Route to Drone" for clarity
- Update to use `selectCurrentRouteWaypoints` instead of `selectQueuedWaypoints`
- Endpoint remains `/api/drone/queue` (no backend changes needed)
- No backend tracking of "which route is on drone"

#### 6. Waypoint Operations
**Behavior**: All waypoint CRUD operations work on `currentRoute.waypoints`

**Implementation Changes Needed**:
- WaypointForm: Instead of `addToQueuedWaypoints`, update `currentRoute.waypoints`
  - Add action: `addWaypointToCurrentRoute(waypoint)`
  - Edit action: `editWaypointInCurrentRoute(index, waypoint)`
- WaypointStatusCard: Instead of `selectQueuedWaypoints`, use `selectCurrentRouteWaypoints`
- WaypointCreationMap: Same change, use current route waypoints
- All map views already updated to use `selectCurrentRouteWaypoints`

## Implementation Plan

### Phase 1: State Management Changes
**Files**:
- `projects/web-frontend/src/store/slices/dataSlice.ts`

**Changes**:
- Add actions: `addWaypointToCurrentRoute`, `editWaypointInCurrentRoute`, `deleteWaypointFromCurrentRoute`
- These actions modify `currentRoute.waypoints` in-place
- Keep waypoints in sync between `currentRoute` and `availableRoutes` array

### Phase 2: Component Refactoring
**Files**:
- `projects/web-frontend/src/components/WaypointStatusCard.tsx`
- `projects/web-frontend/src/components/WaypointStatus/WaypointForm.tsx`
- `projects/web-frontend/src/components/Map/WaypointCreationMap.tsx`

**Changes**:
- Replace all uses of `selectQueuedWaypoints` with `selectCurrentRouteWaypoints`
- Replace `addToQueuedWaypoints` with `addWaypointToCurrentRoute`
- Replace `editWaypointAtIndex` with `editWaypointInCurrentRoute`
- Replace `removeOneFromWaypoints` with `deleteWaypointFromCurrentRoute`
- Keep local editing logic the same, just change what state it operates on

### Phase 3: Save to Backend
**Files**:
- `projects/web-frontend/src/store/thunks/dataThunks.ts` (new thunk)
- `projects/web-frontend/src/components/WaypointStatusCard.tsx` (add button)

**Changes**:
- Create `saveCurrentRouteToBackend` thunk that:
  - Syncs waypoints to backend
  - Handles new waypoints (no id) vs existing (has id)
  - Calls reorder endpoint if needed
  - Updates route name if changed
- Add "Save to Backend" button in WaypointStatusCard
- Remove or repurpose "Delete ALL Queued Waypoints" button

### Phase 4: Post to Drone Update
**Files**:
- `projects/web-frontend/src/components/WaypointStatusCard.tsx`

**Changes**:
- Rename "GCOM POST" to "Post Route to Drone"
- Use `selectCurrentRouteWaypoints` instead of `selectQueuedWaypoints`
- Remove auto-clear functionality (not relevant with backend-synced routes)

### Phase 5: Cleanup
**Files**:
- `projects/web-frontend/src/store/slices/appSlice.ts`

**Changes**:
- Remove or deprecate `queuedWaypoints` and related actions
- Remove localStorage persistence of waypoint queue
- Keep other app state (theme, settings, etc.)

## User Flow

### Creating and Working with Routes

1. User navigates to Queue page
2. Clicks "New Route" button
3. Enters route name → Route created in backend, set as current
4. User adds waypoints via WaypointForm or map
   - Waypoints stored in `currentRoute.waypoints`
   - Changes are local only
5. User clicks "Save to Backend" → waypoints persisted to database
6. User can continue editing, click "Save to Backend" again
7. User clicks "Post Route to Drone" → sends waypoints to mission-planner

### Switching Routes

1. User has Route A loaded with unsaved changes
2. User clicks "Save to Backend" to persist changes
3. User selects Route B from dropdown
4. Route A is no longer active
5. Route B's waypoints load into working area
6. User can edit Route B

### Posting to Drone

1. User has route loaded with waypoints
2. User clicks "Post Route to Drone"
3. Frontend POSTs waypoints to `/api/drone/queue`
4. Backend forwards to mission-planner
5. Drone receives mission
6. **Route remains in backend unchanged** - this is just drone communication

## Future Enhancements

1. **Auto-save on blur**: Replace "Save to Backend" button with auto-save when form fields blur
2. **Optimistic updates**: Show waypoint changes immediately, sync in background
3. **Conflict detection**: Detect if route was modified elsewhere
4. **Save indicators**: Show "Saved" / "Saving..." / "Unsaved changes" status
5. **Route history**: Track which route was last posted to drone
6. **Validation**: Ensure route has at least one waypoint before posting to drone

## Backend Considerations

### No Changes Required for MVP
The existing backend API already supports everything we need:
- `/api/route/` - CRUD for routes
- `/api/waypoint/` - CRUD for waypoints
- `/api/route/{id}/reorder-waypoints/` - Reordering
- `/api/drone/queue` - Drone posting (separate from routes)

### Potential Future Backend Enhancements
1. Batch waypoint update endpoint (reduce API calls)
2. Route versioning/history
3. Track "active mission" relationship between route and drone
4. Validation rules (e.g., min waypoints, coordinate bounds)

## Migration Notes

### Breaking Changes
- Components that relied on `appSlice.queuedWaypoints` will need updates
- localStorage key `appSlice.queuedWaypoints` will be unused

### Non-Breaking
- Backend API unchanged
- Drone posting endpoint unchanged
- Route management API already implemented

## Testing Checklist

- [ ] Create new route → appears in backend
- [ ] Add waypoints to route → visible locally
- [ ] Click "Save to Backend" → waypoints persist in database
- [ ] Switch routes → loads correct waypoints
- [ ] Edit waypoints → changes reflected after save
- [ ] Reorder waypoints → order persists after save
- [ ] Delete waypoints → deletion persists after save
- [ ] Edit route name → name updates in backend
- [ ] Post route to drone → waypoints sent to mission-planner
- [ ] Delete route → removed from backend and frontend
- [ ] No route selected → appropriate empty state
