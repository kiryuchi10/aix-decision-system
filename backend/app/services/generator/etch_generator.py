"""
Etch process data generator
Based on dry_etch.csv structure and Etch process requirements
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional
from datetime import datetime, timedelta
import random

class EtchDataGenerator:
    """Generate synthetic Etch process data with realistic patterns"""
    
    # Etch process column definitions
    CORE_COLUMNS = [
        "timestamp", "tool_id", "chamber_id", "sensor_id",
        "recipe_id", "step_id", "lot_id", "wafer_id"
    ]
    
    PROCESS_VARIABLES = [
        "pressure_torr", "source_power_w", "bias_power_w",
        "gas_flow_sccm_cf4", "gas_flow_sccm_o2", "gas_flow_sccm_cl2",
        "chuck_temp_c", "throttle_valve_pct", "endpoint_signal", "dc_bias_v"
    ]
    
    METROLOGY_COLUMNS = [
        "etch_rate_nm_min", "cd_nm", "profile_angle_deg",
        "uniformity_pct", "defect_density", "yield_estimate"
    ]
    
    LABEL_COLUMNS = [
        "alarm_type", "alarm_severity", "maintenance_event", "operator_action"
    ]
    
    def __init__(self, seed: int = 42):
        self.seed = seed
        np.random.seed(seed)
        random.seed(seed)
    
    def generate_etch_schema(self) -> Dict:
        """Generate Etch data schema template"""
        return {
            "process_type": "etch",
            "columns": {
                "core": self.CORE_COLUMNS,
                "process_variables": self.PROCESS_VARIABLES,
                "metrology": self.METROLOGY_COLUMNS,
                "labels": self.LABEL_COLUMNS
            },
            "column_types": {
                "timestamp": "datetime64[ns]",
                "tool_id": "string",
                "chamber_id": "string",
                "sensor_id": "string",
                "recipe_id": "string",
                "step_id": "int",
                "lot_id": "string",
                "wafer_id": "string",
                "pressure_torr": "float64",
                "source_power_w": "float64",
                "bias_power_w": "float64",
                "gas_flow_sccm_cf4": "float64",
                "gas_flow_sccm_o2": "float64",
                "gas_flow_sccm_cl2": "float64",
                "chuck_temp_c": "float64",
                "throttle_valve_pct": "float64",
                "endpoint_signal": "float64",
                "dc_bias_v": "float64",
                "etch_rate_nm_min": "float64",
                "cd_nm": "float64",
                "profile_angle_deg": "float64",
                "uniformity_pct": "float64",
                "defect_density": "float64",
                "yield_estimate": "float64",
                "alarm_type": "string",
                "alarm_severity": "string",
                "maintenance_event": "string",
                "operator_action": "string"
            }
        }
    
    def generate_dataset(
        self,
        n_runs: int = 100,
        recipes: Optional[List[str]] = None,
        include_drift: bool = False,
        include_step_change: bool = False,
        include_intermittent: bool = False,
        start_time: Optional[datetime] = None
    ) -> pd.DataFrame:
        """Generate Etch process dataset"""
        if recipes is None:
            recipes = ["recipe1", "recipe2", "recipe3", "recipe4", "recipe5"]
        
        if start_time is None:
            start_time = datetime.utcnow() - timedelta(days=7)
        
        data = []
        
        for i in range(n_runs):
            recipe_id = random.choice(recipes)
            timestamp = start_time + timedelta(minutes=i * 30)
            
            # Base values based on recipe
            base_pressure = self._get_recipe_pressure(recipe_id)
            base_cf4 = self._get_recipe_cf4(recipe_id)
            base_o2 = self._get_recipe_o2(recipe_id)
            
            # Generate process variables with realistic variation
            pressure = base_pressure + np.random.normal(0, 2)
            
            # Add drift if requested
            if include_drift and i > n_runs * 0.3:
                drift_factor = (i - n_runs * 0.3) / (n_runs * 0.7) * 5
                pressure += drift_factor
            
            # Add step change if requested
            if include_step_change and i == n_runs // 2:
                pressure += 10
            
            source_power = 2000 + np.random.normal(0, 50)
            bias_power = 500 + np.random.normal(0, 20)
            gas_cf4 = base_cf4 + np.random.normal(0, 50)
            gas_o2 = base_o2 + np.random.normal(0, 20)
            gas_cl2 = 0  # Optional
            chuck_temp = 20 + np.random.normal(0, 1)
            throttle_valve = 50 + np.random.normal(0, 5)
            endpoint_signal = 0.5 + np.random.normal(0, 0.1)
            dc_bias = -200 + np.random.normal(0, 10)
            
            # Generate metrology (correlated with process)
            etch_rate = 100 + (pressure - 50) * 0.5 + np.random.normal(0, 5)
            cd = 3.0 + (pressure - 50) * 0.01 + np.random.normal(0, 0.1)
            profile_angle = 88 + np.random.normal(0, 1)
            uniformity = 95 + np.random.normal(0, 2)
            defect_density = max(0, 0.1 + np.random.normal(0, 0.05))
            yield_estimate = max(0, min(100, 95 + np.random.normal(0, 3)))
            
            # Generate labels
            alarm_type = "none"
            alarm_severity = "none"
            if include_drift and i > n_runs * 0.7:
                alarm_type = "gradual"
                alarm_severity = "medium"
            elif include_step_change and i == n_runs // 2:
                alarm_type = "step"
                alarm_severity = "high"
            elif include_intermittent and random.random() < 0.1:
                alarm_type = "intermittent"
                alarm_severity = "low"
            
            row = {
                "timestamp": timestamp,
                "tool_id": f"TOOL-{random.randint(1, 3)}",
                "chamber_id": f"CHAMBER-{random.randint(1, 2)}",
                "sensor_id": f"SENSOR-{random.randint(1, 5)}",
                "recipe_id": recipe_id,
                "step_id": random.randint(1, 5),
                "lot_id": f"LOT-{random.randint(1, 10)}",
                "wafer_id": f"WAFER-{random.randint(1, 25)}",
                "pressure_torr": round(pressure, 2),
                "source_power_w": round(source_power, 1),
                "bias_power_w": round(bias_power, 1),
                "gas_flow_sccm_cf4": round(gas_cf4, 1),
                "gas_flow_sccm_o2": round(gas_o2, 1),
                "gas_flow_sccm_cl2": round(gas_cl2, 1),
                "chuck_temp_c": round(chuck_temp, 1),
                "throttle_valve_pct": round(throttle_valve, 1),
                "endpoint_signal": round(endpoint_signal, 3),
                "dc_bias_v": round(dc_bias, 1),
                "etch_rate_nm_min": round(etch_rate, 2),
                "cd_nm": round(cd, 2),
                "profile_angle_deg": round(profile_angle, 1),
                "uniformity_pct": round(uniformity, 2),
                "defect_density": round(defect_density, 3),
                "yield_estimate": round(yield_estimate, 2),
                "alarm_type": alarm_type,
                "alarm_severity": alarm_severity,
                "maintenance_event": "" if random.random() > 0.05 else "cleaning",
                "operator_action": "" if random.random() > 0.1 else "manual_adjust"
            }
            
            data.append(row)
        
        return pd.DataFrame(data)
    
    def _get_recipe_pressure(self, recipe_id: str) -> float:
        """Get base pressure for recipe"""
        recipe_map = {
            "recipe1": 50,
            "recipe2": 80,
            "recipe3": 125,
            "recipe4": 80,
            "recipe5": 80
        }
        return recipe_map.get(recipe_id, 80)
    
    def _get_recipe_cf4(self, recipe_id: str) -> float:
        """Get base CF4 flow for recipe"""
        recipe_map = {
            "recipe1": 2000,
            "recipe2": 2000,
            "recipe3": 2000,
            "recipe4": 1000,
            "recipe5": 1000
        }
        return recipe_map.get(recipe_id, 2000)
    
    def _get_recipe_o2(self, recipe_id: str) -> float:
        """Get base O2 flow for recipe"""
        recipe_map = {
            "recipe1": 500,
            "recipe2": 500,
            "recipe3": 500,
            "recipe4": 1000,
            "recipe5": 1000
        }
        return recipe_map.get(recipe_id, 500)
