/**
 * Maps ODLC image color_detection [r,g,b] to a stable group key and display label.
 * For now: each distinct RGB tuple is its own group.
 * Later: replace with range-based logic (e.g. map RGB ranges to "Red", "Yellow") in this file only.
 */

export type RGB = [number, number, number];

/**
 * Returns a stable key for grouping. One dropdown per unique key.
 * Current: exact RGB tuple. Later: can return range-based key (e.g. "red", "yellow").
 */
export function getColorGroupKey(rgb: RGB): string {
    const [r, g, b] = rgb;
    return `${r},${g},${b}`;
}

/**
 * Returns the display label for a color group in the UI.
 * Current: "R, G, B". Later: can return "Red", "Yellow", etc. from ranges.
 */
export function getColorGroupLabel(rgb: RGB): string {
    const [r, g, b] = rgb;
    return `${r}, ${g}, ${b}`;
}
