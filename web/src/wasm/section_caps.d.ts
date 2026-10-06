/* tslint:disable */
/* eslint-disable */

/**
 * Flattened mesh-local XYZ positions, optional triangle indices (empty means
 * non-indexed), and crease threshold in degrees. Returns flattened XYZ line
 * endpoints in input traversal order. Incomplete or invalid triangles are
 * skipped, preserving valid borders elsewhere in the mesh.
 */
export function cad_outline(positions: Float64Array, indices: Uint32Array, threshold_angle: number): Float32Array;

/**
 * The WASM/native entry point. `positions` are flattened mesh-local XYZ;
 * `indices` are triangle indices (empty means non-indexed triangles), and
 * `matrix` is a nonsingular, column-major affine world transform.
 *
 * The returned array contains all XYZ positions followed by all XYZ normals
 * (equal-size halves, total length = 6 * vertex count). An empty array means
 * there is no cap, or the input is invalid/open/non-manifold. No JavaScript
 * objects, renderer state, network requests, or global geometry caches are used.
 */
export function section_cap(positions: Float64Array, indices: Uint32Array, matrix: Float64Array, world_height: number): Float32Array;

export type InitInput = RequestInfo | URL | Response | BufferSource | WebAssembly.Module;

export interface InitOutput {
    readonly memory: WebAssembly.Memory;
    readonly cad_outline: (a: number, b: number, c: number, d: number, e: number) => [number, number];
    readonly section_cap: (a: number, b: number, c: number, d: number, e: number, f: number, g: number) => [number, number];
    readonly __wbindgen_externrefs: WebAssembly.Table;
    readonly __wbindgen_malloc: (a: number, b: number) => number;
    readonly __wbindgen_free: (a: number, b: number, c: number) => void;
    readonly __wbindgen_start: () => void;
}

export type SyncInitInput = BufferSource | WebAssembly.Module;

/**
 * Instantiates the given `module`, which can either be bytes or
 * a precompiled `WebAssembly.Module`.
 *
 * @param {{ module: SyncInitInput }} module - Passing `SyncInitInput` directly is deprecated.
 *
 * @returns {InitOutput}
 */
export function initSync(module: { module: SyncInitInput } | SyncInitInput): InitOutput;

/**
 * If `module_or_path` is {RequestInfo} or {URL}, makes a request and
 * for everything else, calls `WebAssembly.instantiate` directly.
 *
 * @param {{ module_or_path: InitInput | Promise<InitInput> }} module_or_path - Passing `InitInput` directly is deprecated.
 *
 * @returns {Promise<InitOutput>}
 */
export default function __wbg_init (module_or_path?: { module_or_path: InitInput | Promise<InitInput> } | InitInput | Promise<InitInput>): Promise<InitOutput>;
