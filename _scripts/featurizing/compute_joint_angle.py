import numpy as np

def angle(record, end1, middle, end2): #two landmarks are ends and one is between
    seq = record["seq"]

    angles = []

    a = seq[:, end1, :3] #indices 0,1,2 for x,y,z
    b = seq[:, middle, :3]
    c = seq[:, end2, :3]

    v1 = a-b #array of vectors originating at b (middle) and ending at a
    v2 = c-b

    dot_product = np.sum(v1*v2, axis=1)
    norms = np.linalg.norm(v1, axis=1)*np.linalg.norm(v2, axis=1)
    theta = np.degrees(np.arccos(np.clip(dot_product/norms, -1.0, 1.0))) #np.clip safeguards against floating point division errors

    return theta


