import cv2

def add_center_point(pos_list, center):
    pos_list.append(center)
    pos_list.pop(0)
    return pos_list

def avg_center(pos, smoothed, alpha=1/8):
    """
    Exponential smoothing (usually fastest when alpha=2^-N):
    s(0) = x(0)
    x(t) = alpha*x(t) + (1-alpha)*s(t)
    """
    x, y = pos
    x_s, y_s = smoothed
    return (alpha*x + (1-alpha)*x_s, alpha*y + (1-alpha)*y_s)

    xs = 0
    ys = 0
    for x, y in pos_list:
        xs += x
        ys += y
    avgx = xs/len(pos_list)
    avgy = ys/len(pos_list)

    return (int(avgx), int(avgy))

def get_roi(left, right, bottom, top, eye, background):
    eye_width = int(eye.shape[1])
    eye_height = int(eye.shape[0])
    background_width = int(background.shape[1])
    background_height = int(background.shape[0])

    if left < 0:
        left = 0
        right = eye_width
    if bottom < 0:
        bottom = 0
        top = eye_height
    if right > background_width:
        right = background_width
        left = background_width - eye_width
    if top > background_height:
        top = background_height
        bottom = background_height - eye_height
    return (left, right, bottom, top)

