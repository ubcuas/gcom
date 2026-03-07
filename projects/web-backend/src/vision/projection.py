import math

FLT_EPSILON = 1e-6


def _is_distortion_zero(coeffs: list[float]) -> bool:
    return all(abs(c) < FLT_EPSILON for c in coeffs)


def deproject_pixel_to_point(intrinsics: dict, pixel: list[float], depth: float) -> list[float]:
    """Re-implemented from https://github.com/realsenseai/librealsense/blob/78cb605b11f5ba80176e7b8d70292f76ba625565/src/rs.cpp#L4273"""

    model = intrinsics['model']
    coeffs = intrinsics['coeffs']

    if model == 'RS2_DISTORTION_MODIFIED_BROWN_CONRADY':
        raise ValueError("Cannot deproject from a forward-distorted image")

    x = (pixel[0] - intrinsics['ppx']) / intrinsics['fx']
    y = (pixel[1] - intrinsics['ppy']) / intrinsics['fy']

    xo = x
    yo = y

    if not _is_distortion_zero(coeffs):
        if model == 'RS2_DISTORTION_INVERSE_BROWN_CONRADY':
            for _ in range(10):
                r2 = x * x + y * y
                icdist = 1.0 / (1 + ((coeffs[4] * r2 + coeffs[1]) * r2 + coeffs[0]) * r2)
                xq = x / icdist
                yq = y / icdist
                delta_x = 2 * coeffs[2] * xq * yq + coeffs[3] * (r2 + 2 * xq * xq)
                delta_y = 2 * coeffs[3] * xq * yq + coeffs[2] * (r2 + 2 * yq * yq)
                x = (xo - delta_x) * icdist
                y = (yo - delta_y) * icdist

        if model == 'RS2_DISTORTION_BROWN_CONRADY':
            for _ in range(10):
                r2 = x * x + y * y
                icdist = 1.0 / (1 + ((coeffs[4] * r2 + coeffs[1]) * r2 + coeffs[0]) * r2)
                delta_x = 2 * coeffs[2] * x * y + coeffs[3] * (r2 + 2 * x * x)
                delta_y = 2 * coeffs[3] * x * y + coeffs[2] * (r2 + 2 * y * y)
                x = (xo - delta_x) * icdist
                y = (yo - delta_y) * icdist

    if model == 'RS2_DISTORTION_KANNALA_BRANDT4':
        rd = math.sqrt(x * x + y * y)
        rd = max(rd, FLT_EPSILON)

        theta = rd
        theta2 = rd * rd
        for _ in range(4):
            f = theta * (1 + theta2 * (coeffs[0] + theta2 * (coeffs[1] + theta2 * (coeffs[2] + theta2 * coeffs[3])))) - rd
            if abs(f) < FLT_EPSILON:
                break
            df = 1 + theta2 * (3 * coeffs[0] + theta2 * (5 * coeffs[1] + theta2 * (7 * coeffs[2] + 9 * theta2 * coeffs[3])))
            theta -= f / df
            theta2 = theta * theta
        r = math.tan(theta)
        x *= r / rd
        y *= r / rd

    if model == 'RS2_DISTORTION_FTHETA':
        rd = math.sqrt(x * x + y * y)
        rd = max(rd, FLT_EPSILON)
        r = 0.0 if abs(coeffs[0]) < FLT_EPSILON else math.tan(coeffs[0] * rd) / math.atan(2 * math.tan(coeffs[0] / 2.0))
        x *= r / rd
        y *= r / rd

    return [depth * x, depth * y, depth]