import numpy as np
from skimage.transform import rescale


def mse(ch1, ch2):
    return np.average((ch1 - ch2)**2)


def channel_crop(camera):
    height, width = camera.shape
    height //= 3

    cut = 0.15
    hcut, wcut = int(height * cut), int(width * cut)

    frames = []
    for i in range(3):
        hfrom, hto = height * i + hcut, height * (i + 1) - hcut
        wfrom, wto = wcut, width - wcut

        # cut image from borders
        frame = camera[hfrom:hto, wfrom:wto]
        frames.insert(0, frame)

    return np.dstack(frames)


def channel_split(img):
    return [img[:, :, i] for i in range(3)]


def shift(img, offset):
    r, g, b = channel_split(img)
    height, width = r.shape

    i, j, k, h = offset

    r = np.roll(r, (i, j), axis=(1, 0))
    b = np.roll(b, (k, h), axis=(1, 0))

    hfrom, hto = max(j, h, 0), min(height, height + j, height + h)
    wfrom, wto = max(i, k, 0), min(width, width + i, width + k)

    return np.dstack([layer[hfrom:hto, wfrom:wto] for layer in [r, g, b]])


def channel_shift(ch1, ch2, offset):
    height, width = ch2.shape
    x, y = offset

    if x >= 0:
        if y >= 0:
            return ch1[y:, x:], ch2[:height-y, :width-x]
        else:
            return ch1[:height+y, x:], ch2[-y:, :width-x]
    else:
        if y >= 0:
            return ch1[y:, :width+x], ch2[:height-y, -x:]
        else:
            return ch1[:height+y, :width+x], ch2[-y:, -x:]


def channel_surface_search(ch1, ch2, metric, bounds):
    opt_offset = np.zeros(2, dtype=np.int64)

    min_metric = None
    for x_offset in range(*bounds):
        sch1, sch2 = channel_shift(ch1, ch2, (x_offset, 0))
        current_metric = metric(sch1, sch2)

        if min_metric is None or current_metric < min_metric:
            min_metric = current_metric
            opt_offset[0] = x_offset

    for y_offset in range(*bounds):
        sch1, sch2 = channel_shift(ch1, ch2, (opt_offset[0], y_offset))
        current_metric = metric(sch1, sch2)

        if current_metric < min_metric:
            min_metric = current_metric
            opt_offset[1] = y_offset

    return opt_offset


def channel_pyramid_search(ch1, ch2, metric, bounds, depth):
    offset = np.zeros(2, dtype=np.int64)
    for i in range(depth-1, -1, -1):
        sch1, sch2 = [rescale(ch, 0.5 ** i, mode='reflect') for ch in channel_shift(ch1, ch2, offset)]
        offset += (2**i) * channel_surface_search(sch1, sch2, metric, bounds)

    return offset
