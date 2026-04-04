# This is chosen by me (mercury), might need to change.
FLT_EPSILON = 1e-6

# Fixed camera intrinsics (Brown-Conrady / plumb_bob model)
# Values from: ros2 topic echo /camera/camera/color/camera_info (1280x720)
CAMERA_INTRINSICS = {
    'fx': 643.2360229492188,
    'fy': 642.1893920898438,
    'ppx': 661.8545532226562,
    'ppy': 365.9696044921875,
}

# Brown-Conrady distortion coefficients [k1, k2, p1, p2, k3]
# Values from: ros2 topic echo /camera/camera/color/camera_info (1280x720)
DISTORTION_COEFFS = [
    -0.05651168152689934,
    0.06660270690917969,
    -0.00015544862253591418,
    0.0008432056056335568,
    -0.02149238809943199,
]


def _is_distortion_zero(coeffs: list[float]) -> bool:
    return all(abs(c) < FLT_EPSILON for c in coeffs)


def deproject_pixel_to_point(
    pixel: list[float], depth: float) -> list[float]:
    """Deproject a 2D pixel coordinate to a 3D point using Brown-Conrady distortion model.

    Re-implemented from https://github.com/realsenseai/librealsense/blob/78cb605b11f5ba80176e7b8d70292f76ba625565/src/rs.cpp#L4273
    """
    fx = CAMERA_INTRINSICS["fx"]
    fy = CAMERA_INTRINSICS["fy"]
    ppx = CAMERA_INTRINSICS["ppx"]
    ppy = CAMERA_INTRINSICS["ppy"]
    coeffs = DISTORTION_COEFFS

    x = (pixel[0] - ppx) / fx
    y = (pixel[1] - ppy) / fy

    xo = x
    yo = y

    if not _is_distortion_zero(coeffs):
        for _ in range(10):
            r2 = x * x + y * y
            icdist = 1.0 / (
                1 + ((coeffs[4] * r2 + coeffs[1]) * r2 + coeffs[0]) * r2)
            delta_x = 2 * coeffs[2] * x * y + coeffs[3] * (r2 + 2 * x * x)
            delta_y = 2 * coeffs[3] * x * y + coeffs[2] * (r2 + 2 * y * y)
            x = (xo - delta_x) * icdist
            y = (yo - delta_y) * icdist

    return [depth * x, depth * y, depth]
