FLT_EPSILON = 1e-6

# Fixed camera intrinsics (Brown-Conrady / plumb_bob model)
CAMERA_INTRINSICS = {
    "fx": 643.4216918945312,
    "fy": 642.5718994140625,
    "ppx": 638.689453125,
    "ppy": 383.8777160644531,
}

# Brown-Conrady distortion coefficients [k1, k2, p1, p2, k3]
DISTORTION_COEFFS = [
    -0.05599868297576904,
    0.06472615152597427,
    -8.93151736818254e-05,
    -7.332695531658828e-05,
    -0.020574895665049553,
]


def _is_distortion_zero(coeffs: list[float]) -> bool:
    return all(abs(c) < FLT_EPSILON for c in coeffs)


def deproject_pixel_to_point(pixel: list[float], depth: float) -> list[float]:
    """Deproject a 2D pixel coordinate to a 3D point using Brown-Conrady distortion model.

    Re-implemented from https://github.com/realsenseai/librealsense/blob/78cb605b11f5ba80176e7b8d70292f76ba625565/src/rs.cpp#L4273
    """
    x = (pixel[0] - CAMERA_INTRINSICS["ppx"]) / CAMERA_INTRINSICS["fx"]
    y = (pixel[1] - CAMERA_INTRINSICS["ppy"]) / CAMERA_INTRINSICS["fy"]

    xo = x
    yo = y

    if not _is_distortion_zero(DISTORTION_COEFFS):
        for _ in range(10):
            r2 = x * x + y * y
            icdist = 1.0 / (
                1
                + (
                    (DISTORTION_COEFFS[4] * r2 + DISTORTION_COEFFS[1]) * r2
                    + DISTORTION_COEFFS[0]
                )
                * r2
            )
            delta_x = 2 * DISTORTION_COEFFS[2] * x * y + DISTORTION_COEFFS[3] * (
                r2 + 2 * x * x
            )
            delta_y = 2 * DISTORTION_COEFFS[3] * x * y + DISTORTION_COEFFS[2] * (
                r2 + 2 * y * y
            )
            x = (xo - delta_x) * icdist
            y = (yo - delta_y) * icdist

    return [depth * x, depth * y, depth]
