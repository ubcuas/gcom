# Multi-Routes Frontend Integration Plan

## Overview
Integrate the frontend with the backend's multi-route functionality. Frontend will maintain a single active route at a time, with UI for switching between routes and managing the route list.

## Architecture Decision
- **State Management**: Option B - Keep single active route with list of available routes
- **Backend**: No concept of "active route" - user responsibility to track
- **WebSocket**: Not part of this implementation

## Implementation Tasks

### Phase 1: Type System & Models
- [x] Update frontend Route type to include `name` field
- [x] Ensure Waypoint type matches backend OrderedWaypoint structure
- [x] Add proper typing for route-related API responses

### Phase 2: API Layer
- [x] Fix `getRoute()` to properly use `/api/route/{id}/` endpoint
- [x] Add `listRoutes()` API call
- [x] Add `getRouteById(id)` API call
- [x] Add `createRoute(name)` API call
- [x] Add `deleteRoute(id)` API call
- [x] Add `updateRouteName(id, name)` API call
- [x] Add `addWaypointToRoute(routeId, waypoint)` API call
- [x] Add `reorderWaypoints(routeId, waypointIds)` API call

### Phase 3: Redux State Management
- [x] Update DataState interface to include `availableRoutes` array
- [x] Rename `route` to `currentRoute` for clarity
- [x] Add `loadAvailableRoutes` action
- [x] Add `setCurrentRoute` action
- [x] Add `addRoute` action
- [x] Add `removeRoute` action
- [x] Add `updateCurrentRouteName` action
- [x] Add `updateCurrentRouteWaypoints` action
- [x] Add corresponding selectors
- [x] Update initialState with proper structure

### Phase 4: Redux Thunks
- [x] Create `fetchAllRoutes` thunk
- [x] Create `fetchRouteById` thunk
- [x] Create `createNewRoute` thunk
- [x] Create `deleteRouteById` thunk
- [x] Create `switchToRoute` thunk

### Phase 5: UI Components
- [x] Create RouteSelector component (dropdown/list for switching routes)
- [x] Create CreateRouteDialog component (integrated into RouteSelector)
- [x] Create DeleteRouteConfirmation component (integrated into RouteSelector)
- [x] Update Queue page to include RouteSelector
- [x] Add route management section to Queue page

### Phase 6: Integration & Testing
- [x] Update existing MapView to use `selectCurrentRouteWaypoints`
- [x] Fixed MPSControlSection to work with new route system (commented out legacy code)
- [x] TypeScript compilation successful
- [ ] Manual integration testing with backend
- [ ] Test route CRUD operations end-to-end
- [ ] Test route switching with waypoints
- [ ] Update waypoint creation flow to associate with current route

## Technical Notes

### Type Changes
```typescript
// Route type needs name field
type Route = {
    id: number;
    name: string;
    waypoints: Waypoint[];
};

// DataState structure
type DataState = {
    aircraftStatus: AircraftStatus;
    availableRoutes: Route[];
    currentRoute: Route | null;
};
```

### API Endpoints
- List: `GET /api/route/`
- Retrieve: `GET /api/route/{id}/`
- Create: `POST /api/route/` with `{name: string}`
- Update: `PUT /api/route/{id}/` with `{name: string}`
- Delete: `DELETE /api/route/{id}/`
- Add waypoint: `POST /api/waypoint/` with waypoint data + route FK
- Reorder: `POST /api/route/{id}/reorder-waypoints/` with waypoint ID array

### User Flow
1. User sees list of available routes on load
2. User can create new route with name
3. User selects a route from dropdown - becomes currentRoute
4. All waypoint operations apply to currentRoute
5. User can switch between routes
6. User can delete routes (with confirmation)
7. Current route name displayed prominently

## Success Criteria
- [ ] Can fetch and display all routes from backend
- [ ] Can create new routes with custom names
- [ ] Can switch between routes and see different waypoint lists
- [ ] Can delete routes
- [ ] Waypoint operations properly associate with current route
- [ ] UI clearly shows which route is active
- [ ] No breaking changes to existing functionality

## Implementation Summary

### Completed
1. **Type System**: Updated `Route` type to include `name` field
2. **API Layer**: Added complete REST API integration for routes (list, get, create, delete, update, add waypoints, reorder)
3. **Redux State**: Refactored from single route to `availableRoutes` + `currentRoute` pattern with corresponding actions and selectors
4. **Redux Thunks**: Created async thunks for all route operations
5. **UI Components**: Built `RouteSelector` component with integrated create/delete dialogs
6. **Integration**: Integrated RouteSelector into Queue page, updated MapView to use current route waypoints
7. **Build**: Successfully compiles with TypeScript

### Known Issues & Next Steps
1. **MPSControlSection**: "Fetch MPS Data" button temporarily disabled (needs route integration)
2. **Waypoint Creation**: Current waypoint creation flow uses local queue (`appSlice.queuedWaypoints`), not yet integrated with backend routes
3. **Testing Required**:
   - Backend integration testing
   - Route CRUD operations
   - Waypoint association with routes
   - Route switching behavior

### Architecture Notes
- Frontend maintains single active route (`currentRoute`) with list of available routes
- Backend has no concept of "active route" - purely client-side responsibility
- Waypoint operations should target `currentRoute.id` when posting to backend
- Current implementation keeps legacy local waypoint queue separate from backend routes (needs integration)
