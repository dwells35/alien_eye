
def smooth_position(pos, smoothed, alpha=1/8):
    """
    Return 'smoothed' point based on previous points

    NOTE:
    Exponential smoothing (usually fastest when alpha=2^-N):
    s(0) = x(0)
    x(t) = alpha*x(t) + (1-alpha)*s(t)
    """
    x, y = pos
    x_s, y_s = smoothed
    return (alpha*x + (1-alpha)*x_s, alpha*y + (1-alpha)*y_s)