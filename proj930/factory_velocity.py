#!/usr/bin/env python3
"""Factory-only sedmerotočkaste velocity krivulje.

Modul nema GOLD ulaz. Sve vrijednosti moraju nastati iz Factory uzoraka ili
iz eksplicitno označenog Factory fallback profila.
"""

from __future__ import annotations

from bisect import bisect_right
import math
import statistics
from collections import Counter


CURVE_ANCHORS = (
    (0, "floor"),
    (17, "soft"),
    (33, "lowMid"),
    (50, "optimal"),
    (67, "highMid"),
    (83, "strong"),
    (100, "ceiling"),
)


def nearest_percentile(ordered, amount):
    if not ordered:
        raise ValueError("Velocity profil nema Factory uzorke")
    return int(ordered[round((len(ordered) - 1) * amount)])


def build_velocity_curve(values, optimal):
    ordered = sorted(max(1, min(127, int(value))) for value in values)
    if not ordered:
        raise ValueError("Velocity profil nema Factory uzorke")
    optimal = max(ordered[0], min(ordered[-1], int(optimal)))
    floor, ceiling = ordered[0], ordered[-1]
    soft = min(optimal, nearest_percentile(ordered, .10))
    low_mid = min(optimal, max(soft, nearest_percentile(ordered, .25)))
    high_mid = max(optimal, nearest_percentile(ordered, .75))
    strong = max(high_mid, nearest_percentile(ordered, .90))
    curve_values = {
        "floor": floor,
        "soft": soft,
        "lowMid": low_mid,
        "optimal": optimal,
        "highMid": high_mid,
        "strong": strong,
        "ceiling": ceiling,
    }
    points = [
        {"intensity": intensity, "label": label, "velocity": curve_values[label]}
        for intensity, label in CURVE_ANCHORS
    ]
    quantiles = {
        "p05": nearest_percentile(ordered, .05),
        "p10": nearest_percentile(ordered, .10),
        "p25": nearest_percentile(ordered, .25),
        "p50": nearest_percentile(ordered, .50),
        "p75": nearest_percentile(ordered, .75),
        "p90": nearest_percentile(ordered, .90),
        "p95": nearest_percentile(ordered, .95),
    }
    return {
        "method": "factory-quantiles-plus-mode-monotone-v1",
        "points": points,
        "values": curve_values,
        "quantiles": quantiles,
        "allowedRange": [floor, ceiling],
        "sampleCount": len(ordered),
        "goldAffectsDynamics": False,
    }


def build_controller_profile(values):
    ordered = sorted(max(0, min(127, int(value))) for value in values)
    if not ordered:
        return None
    counts = Counter(ordered)
    median = statistics.median(ordered)
    highest = max(counts.values())
    optimal = min((value for value, count in counts.items() if count == highest),
                  key=lambda value: abs(value - median))
    soft = min(optimal, nearest_percentile(ordered, .10))
    low_mid = min(optimal, max(soft, nearest_percentile(ordered, .25)))
    high_mid = max(optimal, nearest_percentile(ordered, .75))
    strong = max(high_mid, nearest_percentile(ordered, .90))
    curve_values = {
        "floor": ordered[0], "soft": soft, "lowMid": low_mid,
        "optimal": optimal, "highMid": high_mid, "strong": strong,
        "ceiling": ordered[-1],
    }
    sample_count = len(ordered)
    confidence = round(min(1.0, math.log2(sample_count + 1) / 8), 3)
    return {
        "method": "factory-controller-quantiles-plus-mode-v1",
        "points": [{"intensity": intensity, "label": label, "value": curve_values[label]}
                   for intensity, label in CURVE_ANCHORS],
        "values": curve_values,
        "quantiles": {
            "p05": nearest_percentile(ordered, .05), "p10": nearest_percentile(ordered, .10),
            "p25": nearest_percentile(ordered, .25), "p50": nearest_percentile(ordered, .50),
            "p75": nearest_percentile(ordered, .75), "p90": nearest_percentile(ordered, .90),
            "p95": nearest_percentile(ordered, .95),
        },
        "allowedRange": [ordered[0], ordered[-1]],
        "sampleCount": sample_count, "confidence": confidence,
        "goldAffectsMixer": False,
    }


def _profile_points(profile):
    curve = profile.get("velocityCurve") or profile.get("velocity_curve")
    if isinstance(curve, dict) and isinstance(curve.get("points"), list) and len(curve["points"]) >= 2:
        return sorted(
            ((float(item["intensity"]), int(item["velocity"])) for item in curve["points"]),
            key=lambda item: item[0],
        )
    values = profile.get("velocity", {"min": 64, "optimal": 96, "max": 112})
    return [(0.0, int(values["min"])), (50.0, int(values["optimal"])), (100.0, int(values["max"]))]


def velocity_at(profile, intensity):
    points = _profile_points(profile)
    amount = max(0.0, min(100.0, float(intensity)))
    positions = [item[0] for item in points]
    right = bisect_right(positions, amount)
    if right == 0:
        return max(1, min(127, points[0][1]))
    if right >= len(points):
        return max(1, min(127, points[-1][1]))
    left_point, right_point = points[right - 1], points[right]
    span = max(1e-9, right_point[0] - left_point[0])
    ratio = (amount - left_point[0]) / span
    value = round(left_point[1] + (right_point[1] - left_point[1]) * ratio)
    return max(1, min(127, value))


def controller_at(controller_profile, intensity):
    if not controller_profile:
        return None
    points = sorted(((float(item["intensity"]), int(item["value"]))
                     for item in controller_profile.get("points", [])), key=lambda item: item[0])
    if not points:
        return None
    amount = max(0.0, min(100.0, float(intensity)))
    positions = [item[0] for item in points]
    right = bisect_right(positions, amount)
    if right == 0:
        return max(0, min(127, points[0][1]))
    if right >= len(points):
        return max(0, min(127, points[-1][1]))
    left_point, right_point = points[right - 1], points[right]
    ratio = (amount - left_point[0]) / max(1e-9, right_point[0] - left_point[0])
    return max(0, min(127, round(left_point[1] + (right_point[1] - left_point[1]) * ratio)))


def remap_velocity(profile, source_velocity, strength=100):
    source = max(1, min(127, int(source_velocity)))
    intensity = (source - 1) * 100 / 126
    target = velocity_at(profile, intensity)
    ratio = max(0, min(100, int(strength))) / 100
    result = round(source + (target - source) * ratio)
    values = profile.get("velocity", {})
    low = int(values.get("min", values.get("floor", 1)))
    high = int(values.get("max", values.get("ceiling", 127)))
    return max(low, min(high, result))