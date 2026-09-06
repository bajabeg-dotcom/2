#!/usr/bin/env python3
"""
FACTORY VELOCITY CALIBRATION 10.00 - KORIGIRANO I BAZDARENO
PHASE 5 & 6: Factory Velocity Calibration

FACTORY koristiti prvenstveno za određivanje:
- prirodnog velocity raspona
- osnovne krive
- family behaviour
- instrument class behaviour
- drum-element behaviour
- accent behaviour
- dynamic ceiling
- dynamic floor
- inter-note velocity relation

NE koristiti sirovu velocity vrijednost iz originalnog korisničkog MIDI-a kao authority.

Svaki instrument: 7-point curve na intensity 0/17/33/50/67/83/100
"""

import json
import math
from pathlib import Path
from typing import Dict, List, Tuple
from collections import defaultdict

DATA_DIR = Path(__file__).parent / "data"
CALIBRATION_DIR = Path(__file__).parent / "calibration"

CURVE_ANCHORS = [
    (0, "floor"),
    (17, "soft"),
    (33, "lowMid"),
    (50, "optimal"),
    (67, "highMid"),
    (83, "strong"),
    (100, "ceiling")
]

class FactoryVelocityCalibrated:
    """Korigirani Factory velocity engine - 100% Factory authority"""
    
    def __init__(self):
        self.profiles = self._load_profiles()
        self.catalog = self._load_catalog()
        self.calibrated_curves = {}
        
        # Role-specific velocity rules from general-rules
        self.velocity_rules = self._load_velocity_rules()
    
    def _load_profiles(self) -> List[dict]:
        path = DATA_DIR / "factory-velocity-profiles.json"
        if path.exists():
            data = json.loads(path.read_text(encoding='utf-8'))
            return data.get("profiles", [])
        return []
    
    def _load_catalog(self) -> dict:
        path = DATA_DIR / "factory-velocity-catalog-9.30.json"
        if path.exists():
            return json.loads(path.read_text(encoding='utf-8'))
        return {}
    
    def _load_velocity_rules(self) -> dict:
        path = DATA_DIR / "general-rules-9.30.json"
        if path.exists():
            data = json.loads(path.read_text(encoding='utf-8'))
            return data.get("velocityRules", {})
        return {}
    
    def _percentile(self, data: List[int], p: float) -> int:
        if not data:
            return 0
        s = sorted(data)
        idx = int(len(s) * p / 100)
        return s[min(idx, len(s)-1)]
    
    def build_7point_curve(self, velocity_values: List[int], optimal: int = None) -> dict:
        """
        Izgradnja 7-point monotone Factory curve
        Input: instrument family, role, phrase position, note position, pitch register, articulation, intensity, accent state, rhythmic density
        Output: target velocity
        Range mora biti Korg-realistic
        """
        if not velocity_values:
            velocity_values = [64, 80, 96]
        
        # Clean values 1-127
        clean = [max(1, min(127, int(v))) for v in velocity_values]
        clean.sort()
        
        if optimal is None:
            optimal = clean[len(clean)//2]
        
        optimal = max(clean[0], min(clean[-1], int(optimal)))
        floor = clean[0]
        ceiling = clean[-1]
        
        # Quantiles
        soft = min(optimal, self._percentile(clean, 10))
        low_mid = min(optimal, max(soft, self._percentile(clean, 25)))
        high_mid = max(optimal, self._percentile(clean, 75))
        strong = max(high_mid, self._percentile(clean, 90))
        
        # Ensure monotone
        soft = max(floor, soft)
        low_mid = max(soft, low_mid)
        high_mid = max(low_mid, high_mid)
        strong = max(high_mid, strong)
        ceiling = max(strong, ceiling)
        
        curve_values = {
            "floor": floor,
            "soft": soft,
            "lowMid": low_mid,
            "optimal": optimal,
            "highMid": high_mid,
            "strong": strong,
            "ceiling": ceiling
        }
        
        points = [
            {"intensity": intensity, "label": label, "velocity": curve_values[label]}
            for intensity, label in CURVE_ANCHORS
        ]
        
        # Quantiles for detailed analysis
        quantiles = {
            "p05": self._percentile(clean, 5),
            "p10": self._percentile(clean, 10),
            "p25": self._percentile(clean, 25),
            "p50": self._percentile(clean, 50),
            "p75": self._percentile(clean, 75),
            "p90": self._percentile(clean, 90),
            "p95": self._percentile(clean, 95),
            "p99": self._percentile(clean, 99)
        }
        
        # Confidence based on sample count
        n = len(clean)
        confidence = min(0.99, 0.1 + 0.9 * (1 - math.exp(-n/50)))
        
        return {
            "method": "factory-quantiles-plus-mode-monotone-v10-calibrated",
            "points": points,
            "values": curve_values,
            "quantiles": quantiles,
            "allowedRange": [floor, ceiling],
            "sampleCount": n,
            "confidence": round(confidence, 4),
            "goldAffectsDynamics": False,  # FACTORY ONLY
            "korgRealistic": self._is_korg_realistic(curve_values),
            "source": "FACTORY"
        }
    
    def _is_korg_realistic(self, values: dict) -> bool:
        """Provjeri da li je range Korg-realistic"""
        checks = [
            values["floor"] >= 1,
            values["ceiling"] <= 127,
            values["floor"] <= values["soft"] <= values["lowMid"] <= values["optimal"] <= values["highMid"] <= values["strong"] <= values["ceiling"],
            values["ceiling"] > values["floor"],
            values["floor"] <= values["optimal"] <= values["ceiling"]
        ]
        return all(checks)
    
    def calibrate_all_roles(self) -> dict:
        """Kalibriraj sve role po Factory podacima"""
        print("🔧 Calibrating Factory velocity for all roles...")
        
        # Group by role
        by_role = defaultdict(list)
        for p in self.profiles:
            role = p.get("role", "unknown")
            by_role[role].append(p)
        
        # Also group by instrument for detailed calibration
        by_instrument = defaultdict(list)
        for p in self.profiles:
            inst = p.get("instrument", "unknown")
            by_instrument[inst].append(p)
        
        calibrated = {}
        
        for role, profiles in by_role.items():
            # Extract all velocity values for this role
            all_velocities = []
            for prof in profiles:
                vel = prof.get("velocity", {})
                if vel:
                    # Use optimal as representative, but also include min/max for range
                    all_velocities.append(vel.get("optimal", vel.get("optimum", 80)))
                    # Include some min/max for broader range
                    if vel.get("min"):
                        all_velocities.append(vel.get("min"))
                    if vel.get("max"):
                        all_velocities.append(vel.get("max"))
            
            if not all_velocities:
                all_velocities = [60, 80, 100]
            
            # Build curve
            curve = self.build_7point_curve(all_velocities)
            
            # Role-specific adjustments from velocity rules
            category = self._map_role_to_category(role)
            vel_rule = self.velocity_rules.get(category, {})
            
            # Apply ppp floor if exists
            if vel_rule and vel_rule.get("ppp"):
                ppp_floor = vel_rule["ppp"]
                if curve["values"]["floor"] < ppp_floor:
                    # Clamp floor to ppp for audibility (e.g., bass needs min 65)
                    curve["values"]["floor"] = max(curve["values"]["floor"], ppp_floor)
                    curve["points"][0]["velocity"] = curve["values"]["floor"]
            
            calibrated[role] = {
                "role": role,
                "profile_count": len(profiles),
                "sample_count": len(all_velocities),
                "curve": curve,
                "velocity_rule": vel_rule,
                "korg_realistic": curve["korgRealistic"],
                "confidence": curve["confidence"],
                "transformation": {
                    "source_evidence": f"{len(profiles)} Factory profiles, {len(all_velocities)} velocity samples",
                    "musical_purpose": vel_rule.get("reason", f"Natural velocity range for {role}"),
                    "target_profile": f"Range {curve['values']['floor']}-{curve['values']['ceiling']}, optimal {curve['values']['optimal']}",
                    "constraints": f"Korg: 1-127, {category} ppp={vel_rule.get('ppp', 1)}",
                    "transformation_rule": f"Intensity 0-100 -> Velocity {curve['values']['floor']}-{curve['values']['ceiling']} via 7-point Factory curve",
                    "before_metric": "Original velocity random/uncontrolled",
                    "after_metric": f"Factory calibrated {curve['values']['floor']}-{curve['values']['ceiling']}, mean {curve['values']['optimal']}",
                    "pass_fail": "PASS" if curve["korgRealistic"] else "FAIL",
                    "explanation": f"Factory daje prirodni velocity raspon za {role}, Gold ne utječe na velocity"
                }
            }
            
            self.calibrated_curves[role] = curve
        
        # Save
        output = {
            "version": "10.00-calibrated",
            "timestamp": __import__('datetime').datetime.now().isoformat(),
            "authority": "FACTORY_ONLY",
            "total_roles": len(calibrated),
            "total_factory_profiles": len(self.profiles),
            "calibrations": calibrated
        }
        
        path = CALIBRATION_DIR / "factory_velocity_v10_calibrated.json"
        path.write_text(json.dumps(output, indent=2, ensure_ascii=False), encoding='utf-8')
        
        print(f"✅ Calibrated {len(calibrated)} roles, {len(self.profiles)} factory profiles")
        for role, cal in calibrated.items():
            print(f"   {role}: {cal['curve']['values']['floor']}-{cal['curve']['values']['ceiling']} (optimal {cal['curve']['values']['optimal']}) confidence {cal['confidence']:.2f}")
        
        return output
    
    def velocity_at_intensity(self, role: str, intensity: float) -> int:
        """Get target velocity for given intensity (0-100) using calibrated curve"""
        curve = self.calibrated_curves.get(role)
        if not curve:
            # Fallback
            return int(1 + (intensity / 100) * 126)
        
        points = sorted(curve["points"], key=lambda x: x["intensity"])
        intensity = max(0, min(100, intensity))
        
        # Find surrounding points
        for i in range(len(points)-1):
            left = points[i]
            right = points[i+1]
            if left["intensity"] <= intensity <= right["intensity"]:
                # Linear interpolation
                span = right["intensity"] - left["intensity"]
                if span == 0:
                    return left["velocity"]
                ratio = (intensity - left["intensity"]) / span
                vel = left["velocity"] + (right["velocity"] - left["velocity"]) * ratio
                return max(1, min(127, int(round(vel))))
        
        # Edge cases
        if intensity <= points[0]["intensity"]:
            return points[0]["velocity"]
        else:
            return points[-1]["velocity"]
    
    def _map_role_to_category(self, role: str) -> str:
        mapping = {
            "bass": "bass",
            "drums": "drums",
            "percussion": "perc",
            "rhythm_guitar": "guitar",
            "solo_guitar": "guitar",
            "piano": "piano",
            "organ": "organ",
            "strings": "strings",
            "brass": "brass",
            "sax": "reed",
            "clarinet": "reed",
            "woodwind": "pipe",
            "violin": "strings",
            "synth_lead": "synth",
            "pad": "synth",
            "choir": "ensemble",
            "mallet": "perc",
            "fx": "sfx",
            "accompaniment": "chords",
            "melody": "melody",
            "chords": "chords"
        }
        return mapping.get(role, "chords")

# Test and calibrate
if __name__ == "__main__":
    engine = FactoryVelocityCalibrated()
    result = engine.calibrate_all_roles()
    
    # Test velocity_at
    print("\n--- Test velocity_at ---")
    for role in ["bass", "drums", "rhythm_guitar", "piano"]:
        if role in engine.calibrated_curves:
            for intensity in [0, 25, 50, 75, 100]:
                vel = engine.velocity_at_intensity(role, intensity)
                print(f"{role} intensity {intensity} -> velocity {vel}")
