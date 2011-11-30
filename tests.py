import numpy as np

water = np.ones((6, 6), float)
collab = np.ones((6, 6), float)
collab[3, 4] = .8

#noinspection PyArgumentEqualDefault
def fastroll(array, shift, axis):
    prefix = [slice(None)] * axis
    shift %= array.shape[axis]
    ret = np.empty_like(array)
    ret[prefix + [slice(shift, None)]] = array[prefix + [slice(None, -shift)]]
    ret[prefix + [slice(0, shift)]] = array[prefix + [slice(-shift, None)]]
    return ret

def diffuse(arr):
    arr += 0.2 * fastroll(arr,shift=1,axis=1) * water
    arr += 0.2 * fastroll(arr,shift=-1,axis=1) * water
    arr += 0.2 * fastroll(arr,shift=1,axis=0) * water
    arr += 0.2 * fastroll(arr,shift=-1,axis=0) * water
    return arr

m = np.zeros((6, 6), float)
m[3, 3] = 1000



for i in range(3):
    collab = diffuse(collab)
    print(collab)
    raw_input()