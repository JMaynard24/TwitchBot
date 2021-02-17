def is_number(num):
    """Given string 'num', returns true if 'num' is numeric."""
    try:
        int(num)
        return True
    except ValueError:
        return False


# -----------------------------------------------------------------------------


def linearMap(val, min1, max1, min2, max2):
    ratio = (val - min1)/(max1 - min1)
    return (ratio * (max2 - min2)) + min2


# -----------------------------------------------------------------------------


def logMap(val, min1, max1, min2, max2):
    return linearMap(val, min1, max1, linearMap(val, min1, max1, min2, max2), max2)


# -----------------------------------------------------------------------------


def expMap(val, min1, max1, min2, max2):
    return linearMap(val, min1, max1, min2, linearMap(val, min1, max1, min2, max2))
