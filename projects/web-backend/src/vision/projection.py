import math

def project_point_to_pixel(intrinsics: dict, point: list[float]) -> list[float]:
    """Re-implemented from https://github.com/realsenseai/librealsense/blob/78cb605b11f5ba80176e7b8d70292f76ba625565/src/rs.cpp#L4202-L4264"""

    FLT_EPSILON = 1e-6 # defining here for now, can't find in the repository
    x = point[0] / point[2]
    y = point[1] / point[2]
    
    model = intrinsics['model']
    coeffs = intrinsics['coeffs']

    r2 = x * x + y * y
    r = math.sqrt(r2)

    if (model == 'RS2_DISTORTION_MODIFIED_BROWN_CONRADY') or (model == 'RS2_DISTORTION_INVERSE_BROWN_CONRADY'):
        f = 1 + coeffs[0] * r2 + coeffs[1] * r2 * r2 + coeffs[4] * r2 * r2 * r2
        
        x *= f
        y *= f

        dx = x + 2 * coeffs[2] * x * y + coeffs[3] * (r2 + 2 * x * x)
        dy = y + 2 * coeffs[3] * x * y + coeffs[2] * (r2 + 2 * y * y)

        x = dx
        y = dy

    elif (model == 'RS2_DISTORTION_BROWN_CONRADY'):
        f = 1 + coeffs[0] * r2 + coeffs[1] * r2 * r2 + coeffs[4] * r2 * r2 * r2

        xf = x * f
        yf = y * f

        dx = xf + 2 * coeffs[2] * x * y + coeffs[3] * (r2 + 2 * x * x)
        dy = yf + 2 * coeffs[3] * x * y + coeffs[2] * (r2 + 2 * y * y)

        x = dx
        y = dy
        
    elif (model == 'RS2_DISTORTION_FTHETA'):
        r = max(r, FLT_EPSILON)

        rd = (1.0 / coeffs[0] * math.atan(2 * r * math.tan(coeffs[0] / 2.0)))
        x *= rd / r
        y *= rd / r

    elif (model == 'RS2_DISTORTION_KANNALA_BRANDT4'):
        r = max(r, FLT_EPSILON)

        theta = math.atan(r)
        theta2 = theta * theta 
        series = 1 + theta2 * (coeffs[0] + theta2 * (coeffs[1] + theta2 * (coeffs[2] + theta2 * coeffs[3])))
        rd = theta * series
        x *= rd / r
        y *= rd / r

    new_pixel = [x * intrinsics['fx'] + intrinsics['ppx'], y * intrinsics['fy'] + intrinsics['ppy']]
    return new_pixel