import { createAsyncThunk } from "@reduxjs/toolkit";
import {
    listRoutes,
    getRouteById,
    createRoute as apiCreateRoute,
    deleteRoute as apiDeleteRoute,
} from "../../api/endpoints";
import { loadAvailableRoutes, setCurrentRoute, addRoute, removeRoute } from "../slices/dataSlice";

export const fetchAllRoutes = createAsyncThunk("data/fetchAllRoutes", async (_, { dispatch }) => {
    const routes = await listRoutes();
    dispatch(loadAvailableRoutes(routes));
    return routes;
});

export const fetchRouteById = createAsyncThunk("data/fetchRouteById", async (id: number, { dispatch }) => {
    const route = await getRouteById(id);
    dispatch(setCurrentRoute(route));
    return route;
});

export const createNewRoute = createAsyncThunk("data/createNewRoute", async (name: string, { dispatch }) => {
    const route = await apiCreateRoute(name);
    dispatch(addRoute(route));
    return route;
});

export const deleteRouteById = createAsyncThunk("data/deleteRouteById", async (id: number, { dispatch }) => {
    await apiDeleteRoute(id);
    dispatch(removeRoute(id));
});

export const switchToRoute = createAsyncThunk("data/switchToRoute", async (id: number, { dispatch }) => {
    const route = await getRouteById(id);
    dispatch(setCurrentRoute(route));
    return route;
});
