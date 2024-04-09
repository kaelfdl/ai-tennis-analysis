def get_center_of_bbox(bbox):
    x1, y1, x2, y2 = bbox
    center_x = int((x1 + x2) / 2)
    center_y = int((y1 + y2) / 2)
    return (center_x, center_y)

def measure_distance(p1, p2):
    return ((p1[0] - p2[0])**2 + (p1[1] - p2[1])**2)**0.5

def get_foot_position(bbox):
    x1, y1, x2, y2 = bbox
    return (int((x1 + x2) / 2), y2)

def get_closest_kp_index(point, kps, kp_indices):
    closest_distance = float('inf')
    kp_idx = kp_indices[0]
    for kp_index in kp_indices:
        kp = kps[kp_index*2], kps[kp_index*2 + 1]
        distance = abs(point[1] - kp[1])

        if distance < closest_distance:
            closest_distance = distance
            kp_idx = kp_index
    return kp_idx

def get_height_of_bbox(bbox):
    return bbox[3] - bbox[1]

def measure_xy_distance(p1, p2):
    return  abs(p1[0] - p2[0]), abs(p1[1] - p2[1])