import { useEffect, useState } from "react";
import { useAppDispatch, useAppSelector } from "../store/store";
import { selectAvailableRoutes, selectCurrentRoute } from "../store/slices/dataSlice";
import { fetchAllRoutes, switchToRoute, createNewRoute, deleteRouteById } from "../store/thunks/dataThunks";

export const RouteSelector = () => {
    const dispatch = useAppDispatch();
    const availableRoutes = useAppSelector(selectAvailableRoutes);
    const currentRoute = useAppSelector(selectCurrentRoute);
    const [showCreateDialog, setShowCreateDialog] = useState(false);
    const [newRouteName, setNewRouteName] = useState("");
    const [showDeleteConfirm, setShowDeleteConfirm] = useState(false);
    const [routeToDelete, setRouteToDelete] = useState<number | null>(null);

    useEffect(() => {
        void dispatch(fetchAllRoutes() as any);
    }, [dispatch]);

    const handleRouteChange = (routeId: number) => {
        void dispatch(switchToRoute(routeId) as any);
    };

    const handleCreateRoute = async () => {
        if (newRouteName.trim()) {
            await dispatch(createNewRoute(newRouteName.trim()) as any);
            setNewRouteName("");
            setShowCreateDialog(false);
        }
    };

    const handleDeleteClick = (routeId: number) => {
        setRouteToDelete(routeId);
        setShowDeleteConfirm(true);
    };

    const handleConfirmDelete = async () => {
        if (routeToDelete !== null) {
            await dispatch(deleteRouteById(routeToDelete) as any);
            setRouteToDelete(null);
            setShowDeleteConfirm(false);
        }
    };

    return (
        <div className="route-selector">
            <div className="route-selector-header">
                <h3>Routes</h3>
                <button className="btn-create-route" onClick={() => setShowCreateDialog(true)}>
                    + New Route
                </button>
            </div>

            <div className="route-list">
                {availableRoutes.length === 0 ? (
                    <p className="no-routes">No routes available. Create one to get started.</p>
                ) : (
                    <select
                        value={currentRoute?.id ?? ""}
                        onChange={(e) => handleRouteChange(Number(e.target.value))}
                        className="route-dropdown"
                    >
                        <option value="" disabled>
                            Select a route
                        </option>
                        {availableRoutes.map((route) => (
                            <option key={route.id} value={route.id}>
                                {route.name} ({route.waypoints.length} waypoints)
                            </option>
                        ))}
                    </select>
                )}

                {currentRoute && (
                    <div className="current-route-info">
                        <span className="current-route-name">Active: {currentRoute.name}</span>
                        <button className="btn-delete-route" onClick={() => handleDeleteClick(currentRoute.id)}>
                            Delete
                        </button>
                    </div>
                )}
            </div>

            {showCreateDialog && (
                <div className="dialog-overlay">
                    <div className="dialog">
                        <h4>Create New Route</h4>
                        <input
                            type="text"
                            value={newRouteName}
                            onChange={(e) => setNewRouteName(e.target.value)}
                            placeholder="Enter route name"
                            autoFocus
                            onKeyPress={(e) => {
                                if (e.key === "Enter") {
                                    handleCreateRoute();
                                }
                            }}
                        />
                        <div className="dialog-actions">
                            <button onClick={() => setShowCreateDialog(false)}>Cancel</button>
                            <button onClick={handleCreateRoute} disabled={!newRouteName.trim()}>
                                Create
                            </button>
                        </div>
                    </div>
                </div>
            )}

            {showDeleteConfirm && (
                <div className="dialog-overlay">
                    <div className="dialog">
                        <h4>Confirm Delete</h4>
                        <p>Are you sure you want to delete this route? This action cannot be undone.</p>
                        <div className="dialog-actions">
                            <button onClick={() => setShowDeleteConfirm(false)}>Cancel</button>
                            <button onClick={handleConfirmDelete} className="btn-danger">
                                Delete
                            </button>
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
};
