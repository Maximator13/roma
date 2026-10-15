import heapq
import math

import numpy as np
from mathutils import Vector

STEPS = [(-1, -1), (-1, 0), (-1, 1), (0, -1), (0, 1), (1, -1), (1, 0), (1, 1)]


class Planner:
    def __init__(self, field, allowed):
        self.field = field
        self.allowed = allowed
        self.spacing = field.spacing

    def cell(self, point):
        row = int(round((point[1] - self.field.y0) / self.spacing))
        column = int(round((point[0] - self.field.x0) / self.spacing))
        return (min(max(row, 0), self.field.rows - 1), min(max(column, 0), self.field.columns - 1))

    def position(self, row, column):
        return Vector((self.field.x0 + column * self.spacing, self.field.y0 + row * self.spacing))

    def snap(self, point, max_slope, reach=30.0):
        row, column = self.cell(point)
        span = int(reach / self.spacing)
        r0, r1 = max(row - span, 1), min(row + span, self.field.rows - 2)
        c0, c1 = max(column - span, 1), min(column + span, self.field.columns - 2)
        slope = self.field.slope()[r0:r1 + 1, c0:c1 + 1]
        ok = self.allowed[r0:r1 + 1, c0:c1 + 1] & (slope <= max_slope)
        if ok[row - r0, column - c0]:
            return Vector(point)
        rows, columns = np.nonzero(ok)
        if len(rows) == 0:
            return Vector(point)
        distance = (rows + r0 - row) ** 2 + (columns + c0 - column) ** 2
        best = int(np.argmin(distance))
        return self.position(rows[best] + r0, columns[best] + c0)

    def leg(self, start, goal, max_grade, margin=70.0):
        (r0, c0), (r1, c1) = self.cell(start), self.cell(goal)
        pad = int(margin / self.spacing)
        top, bottom = max(min(r0, r1) - pad, 0), min(max(r0, r1) + pad, self.field.rows - 1)
        left, right = max(min(c0, c1) - pad, 0), min(max(c0, c1) + pad, self.field.columns - 1)
        heights = self.field.heights[top:bottom + 1, left:right + 1].tolist()
        allowed = self.allowed[top:bottom + 1, left:right + 1].copy()
        allowed[r0 - top, c0 - left] = True
        allowed[r1 - top, c1 - left] = True
        allowed = allowed.tolist()
        rows, columns = len(heights), len(heights[0])
        source, target = (r0 - top, c0 - left), (r1 - top, c1 - left)
        distance = {source: 0.0}
        previous = {}
        heap = [(0.0, 0.0, source)]
        spacing = self.spacing
        while heap:
            _, cost, node = heapq.heappop(heap)
            if node == target:
                break
            if cost > distance.get(node, math.inf):
                continue
            row, column = node
            here = heights[row][column]
            for dr, dc in STEPS:
                nr, nc = row + dr, column + dc
                if nr < 0 or nc < 0 or nr >= rows or nc >= columns or not allowed[nr][nc]:
                    continue
                length = spacing * (1.41421356 if dr and dc else 1.0)
                grade = abs(heights[nr][nc] - here) / length
                if grade > max_grade:
                    continue
                total = cost + length * (1.0 + 5.0 * grade)
                if total < distance.get((nr, nc), math.inf):
                    distance[(nr, nc)] = total
                    previous[(nr, nc)] = node
                    remaining = math.hypot(nr - target[0], nc - target[1]) * spacing
                    heapq.heappush(heap, (total + remaining, total, (nr, nc)))
        if target not in previous and target != source:
            return None
        path = [target]
        while path[-1] != source:
            path.append(previous[path[-1]])
        path.reverse()
        points = [self.position(r + top, c + left) for r, c in path]
        points[0] = Vector(start)
        points[-1] = Vector(goal)
        return points

    def clear(self, a, b, max_grade):
        length = (b - a).length
        count = max(1, int(math.ceil(length / 0.8)))
        previous = None
        for k in range(count + 1):
            p = a + (b - a) * (k / count)
            row, column = self.cell(p)
            if 0 < k < count and not self.allowed[row, column]:
                return False
            z = self.field.sample(p.x, p.y)
            if previous is not None and abs(z - previous) / (length / count) > max_grade:
                return False
            previous = z
        return True

    def straighten(self, points, max_grade):
        result = [points[0]]
        index = 0
        while index < len(points) - 1:
            best = index + 1
            for candidate in range(min(len(points) - 1, index + 40), index + 1, -1):
                if self.clear(points[index], points[candidate], max_grade):
                    best = candidate
                    break
            result.append(points[best])
            index = best
        return result

    def route(self, waypoints, max_grade=0.2, max_slope=0.6):
        snapped = [self.snap(p, max_slope) for p in waypoints]
        result = [snapped[0]]
        for a, b in zip(snapped[:-1], snapped[1:]):
            points = None
            for grade in (max_grade, max_grade + 0.02, max_grade + 0.04):
                points = self.leg(a, b, grade)
                if points is not None:
                    break
            if points is None:
                raise RuntimeError(f"no walkable path from {tuple(a)} to {tuple(b)}")
            result.extend(self.straighten(points, max_grade + 0.02)[1:])
        return result


def densify(points, step=2.0):
    dense = [points[0]]
    for a, b in zip(points[:-1], points[1:]):
        count = max(1, int(math.ceil((b - a).length / step)))
        dense.extend(a + (b - a) * (k / count) for k in range(1, count + 1))
    return dense


def chaikin(points, passes=2):
    for _ in range(passes):
        smoothed = [points[0]]
        for a, b in zip(points[:-1], points[1:]):
            smoothed.append(a * 0.75 + b * 0.25)
            smoothed.append(a * 0.25 + b * 0.75)
        smoothed.append(points[-1])
        points = smoothed
    return points


def grades(ground, points):
    heights = [ground.height(p.x, p.y) for p in points]
    worst = (0.0, None)
    for (p, z), (q, zq) in zip(zip(points[:-1], heights[:-1]), zip(points[1:], heights[1:])):
        run = (q - p).length
        if run > 1e-3 and abs(zq - z) / run > worst[0]:
            worst = (abs(zq - z) / run, (round(p.x, 1), round(p.y, 1)))
    return worst, heights
