from typing import List, Dict, Optional, Tuple
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, desc
import json
import uuid

from ..models.experiment import (
    Recipe, Experiment, SensorData, Alarm, 
    ModelRegistry, Recommendation, ProcessWindow, MLPipeline
)
from ..core.database import get_db

class DataIntegrationService:
    """
    Real data integration service for AiX Decision System
    Handles experiment data, sensor data, and ML pipeline integration
    """
    
    def __init__(self, db: Session):
        self.db = db
    
    # === Recipe Management ===
    
    def create_recipe(self, recipe_data: Dict) -> Recipe:
        """Create a new process recipe"""
        recipe = Recipe(
            id=recipe_data.get('id', f"RCP-{uuid.uuid4().hex[:8].upper()}"),
            name=recipe_data['name'],
            description=recipe_data.get('description'),
            temperature_min=recipe_data.get('temperature_min', 840.0),
            temperature_max=recipe_data.get('temperature_max', 860.0),
            temperature_optimal=recipe_data.get('temperature_optimal', 850.0),
            pressure_min=recipe_data.get('pressure_min', 2.3),
            pressure_max=recipe_data.get('pressure_max', 2.7),
            pressure_optimal=recipe_data.get('pressure_optimal', 2.5),
            gas_flow_min=recipe_data.get('gas_flow_min', 90.0),
            gas_flow_max=recipe_data.get('gas_flow_max', 110.0),
            gas_flow_optimal=recipe_data.get('gas_flow_optimal', 100.0),
            power_min=recipe_data.get('power_min', 1400.0),
            power_max=recipe_data.get('power_max', 1600.0),
            power_optimal=recipe_data.get('power_optimal', 1500.0)
        )
        
        self.db.add(recipe)
        self.db.commit()
        self.db.refresh(recipe)
        return recipe
    
    def get_recipe(self, recipe_id: str) -> Optional[Recipe]:
        """Get recipe by ID"""
        return self.db.query(Recipe).filter(Recipe.id == recipe_id).first()
    
    # === Experiment Management ===
    
    def create_experiment(self, experiment_data: Dict) -> Experiment:
        """Create a new DoE experiment"""
        experiment = Experiment(
            id=f"EXP-{uuid.uuid4().hex[:8].upper()}",
            experiment_id=experiment_data.get('experiment_id', f"EXP-{datetime.now().strftime('%Y%m%d-%H%M%S')}"),
            recipe_id=experiment_data['recipe_id'],
            name=experiment_data.get('name'),
            description=experiment_data.get('description'),
            objectives=experiment_data.get('objectives', ['maximize_yield']),
            factors=experiment_data.get('factors', {}),
            constraints=experiment_data.get('constraints', {}),
            parameters=experiment_data.get('parameters', {}),
            status=experiment_data.get('status', 'PLANNED'),
            estimated_duration=experiment_data.get('estimated_duration', 120),
            created_by=experiment_data.get('created_by', 'system')
        )
        
        self.db.add(experiment)
        self.db.commit()
        self.db.refresh(experiment)
        return experiment
    
    def update_experiment_results(self, experiment_id: str, results: Dict) -> bool:
        """Update experiment with results"""
        experiment = self.db.query(Experiment).filter(
            Experiment.experiment_id == experiment_id
        ).first()
        
        if not experiment:
            return False
        
        experiment.results = results
        experiment.yield_value = results.get('yield', 0.0)
        experiment.defect_rate = results.get('defect_rate', 0.0)
        experiment.status = 'COMPLETED'
        experiment.actual_end = datetime.utcnow()
        experiment.updated_at = datetime.utcnow()
        
        self.db.commit()
        return True
    
    def get_experiment_data_for_ml(self, experiment_id: str) -> Tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
        """
        Prepare experiment data for ML pipeline
        Returns: X_train, y_train, X_test, y_test
        """
        experiment = self.db.query(Experiment).filter(
            Experiment.experiment_id == experiment_id
        ).first()
        
        if not experiment or not experiment.results:
            # Generate synthetic data for demo
            return self._generate_synthetic_data()
        
        # Get related experiments for the same recipe
        related_experiments = self.db.query(Experiment).filter(
            and_(
                Experiment.recipe_id == experiment.recipe_id,
                Experiment.status == 'COMPLETED',
                Experiment.results.isnot(None)
            )
        ).all()
        
        if len(related_experiments) < 10:
            # Not enough data, supplement with synthetic
            return self._generate_synthetic_data()
        
        # Extract features and targets
        X = []
        y = []
        
        for exp in related_experiments:
            if exp.parameters and exp.results:
                features = []
                
                # Extract parameter values
                params = exp.parameters
                features.extend([
                    params.get('temperature', 850.0),
                    params.get('pressure', 2.5),
                    params.get('gas_flow', 100.0),
                    params.get('power', 1500.0)
                ])
                
                X.append(features)
                y.append(exp.yield_value or exp.results.get('yield', 90.0))
        
        X = np.array(X)
        y = np.array(y)
        
        # Train/test split (80/20)
        split_idx = int(len(X) * 0.8)
        
        X_train = X[:split_idx]
        y_train = y[:split_idx]
        X_test = X[split_idx:]
        y_test = y[split_idx:]
        
        return X_train, y_train, X_test, y_test
    
    def _generate_synthetic_data(self) -> Tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
        """Generate synthetic experiment data for demo"""
        np.random.seed(42)
        
        n_samples = 100
        n_features = 4  # temperature, pressure, gas_flow, power
        
        # Generate features with realistic ranges
        X = np.random.normal(0, 1, (n_samples, n_features))
        
        # Add realistic scaling
        X[:, 0] = 850 + X[:, 0] * 5    # temperature: 845-855
        X[:, 1] = 2.5 + X[:, 1] * 0.1  # pressure: 2.4-2.6
        X[:, 2] = 100 + X[:, 2] * 5    # gas_flow: 95-105
        X[:, 3] = 1500 + X[:, 3] * 50  # power: 1450-1550
        
        # Generate target with realistic relationship
        y = (
            85 +  # baseline yield
            0.3 * (X[:, 0] - 850) / 5 +      # temperature effect
            0.2 * (X[:, 1] - 2.5) / 0.1 +    # pressure effect
            0.1 * (X[:, 2] - 100) / 5 +      # gas flow effect
            0.15 * (X[:, 3] - 1500) / 50 +   # power effect
            0.1 * (X[:, 0] - 850) * (X[:, 1] - 2.5) / (5 * 0.1) +  # interaction
            np.random.normal(0, 1, n_samples)  # noise
        )
        
        # Ensure yield is in reasonable range
        y = np.clip(y, 80, 95)
        
        # Train/test split
        split_idx = int(len(X) * 0.8)
        
        return X[:split_idx], y[:split_idx], X[split_idx:], y[split_idx:]
    
    # === Sensor Data Management ===
    
    def ingest_sensor_data(self, sensor_data_list: List[Dict]) -> bool:
        """Ingest batch sensor data"""
        try:
            sensor_records = []
            
            for data in sensor_data_list:
                sensor_record = SensorData(
                    experiment_id=data.get('experiment_id'),
                    recipe_id=data.get('recipe_id'),
                    timestamp=data.get('timestamp', datetime.utcnow()),
                    temperature=data.get('temperature'),
                    pressure=data.get('pressure'),
                    gas_flow=data.get('gas_flow'),
                    power=data.get('power'),
                    chamber_pressure=data.get('chamber_pressure'),
                    rf_power=data.get('rf_power'),
                    gas_flow_ar=data.get('gas_flow_ar'),
                    gas_flow_n2=data.get('gas_flow_n2'),
                    substrate_temperature=data.get('substrate_temperature'),
                    is_valid=data.get('is_valid', True),
                    quality_score=data.get('quality_score', 1.0)
                )
                sensor_records.append(sensor_record)
            
            self.db.add_all(sensor_records)
            self.db.commit()
            return True
            
        except Exception as e:
            self.db.rollback()
            print(f"Error ingesting sensor data: {e}")
            return False
    
    def get_sensor_data_for_experiment(self, experiment_id: str, 
                                     start_time: Optional[datetime] = None,
                                     end_time: Optional[datetime] = None) -> List[SensorData]:
        """Get sensor data for specific experiment"""
        query = self.db.query(SensorData).filter(
            SensorData.experiment_id == experiment_id
        )
        
        if start_time:
            query = query.filter(SensorData.timestamp >= start_time)
        if end_time:
            query = query.filter(SensorData.timestamp <= end_time)
        
        return query.order_by(SensorData.timestamp).all()
    
    # === ML Pipeline Integration ===
    
    def create_ml_pipeline_record(self, pipeline_data: Dict) -> MLPipeline:
        """Create ML pipeline execution record"""
        pipeline = MLPipeline(
            id=f"PIP-{uuid.uuid4().hex[:8].upper()}",
            pipeline_id=pipeline_data['pipeline_id'],
            experiment_id=pipeline_data.get('experiment_id'),
            config=pipeline_data.get('config', {}),
            models_tested=pipeline_data.get('models_tested', []),
            ensemble_strategies=pipeline_data.get('ensemble_strategies', []),
            status='RUNNING',
            started_at=datetime.utcnow(),
            created_by=pipeline_data.get('created_by', 'system')
        )
        
        self.db.add(pipeline)
        self.db.commit()
        self.db.refresh(pipeline)
        return pipeline
    
    def update_ml_pipeline_results(self, pipeline_id: str, results: Dict) -> bool:
        """Update ML pipeline with results"""
        pipeline = self.db.query(MLPipeline).filter(
            MLPipeline.pipeline_id == pipeline_id
        ).first()
        
        if not pipeline:
            return False
        
        pipeline.results = results
        pipeline.status = 'COMPLETED'
        pipeline.progress = 100
        pipeline.completed_at = datetime.utcnow()
        pipeline.duration_seconds = int((datetime.utcnow() - pipeline.started_at).total_seconds())
        
        # Extract best model info
        if 'best_combination' in results:
            best = results['best_combination']
            pipeline.best_model_id = f"MODEL-{uuid.uuid4().hex[:8].upper()}"
            pipeline.performance_summary = {
                'r2': best.get('ensemble_r2'),
                'mae': best.get('ensemble_mae'),
                'rmse': best.get('ensemble_rmse'),
                'strategy': best.get('best_ensemble_strategy')
            }
        
        self.db.commit()
        return True
    
    def save_best_model_to_registry(self, pipeline_id: str, model_data: Dict) -> ModelRegistry:
        """Save best model to model registry"""
        model = ModelRegistry(
            id=f"MDL-{uuid.uuid4().hex[:8].upper()}",
            model_id=model_data['model_id'],
            experiment_id=model_data.get('experiment_id'),
            name=f"Ensemble Model - {model_data['model_id']}",
            model_type='ensemble',
            algorithm='ensemble',
            model_version='v1.0',
            model_path=model_data.get('model_path'),
            r2_score=model_data['performance']['r2'],
            mae=model_data['performance']['mae'],
            rmse=model_data['performance']['rmse'],
            is_ensemble=True,
            ensemble_strategy=model_data['ensemble_strategy'],
            ensemble_models=model_data['combination'],
            is_active=True,
            created_by=model_data.get('created_by', 'system')
        )
        
        self.db.add(model)
        self.db.commit()
        self.db.refresh(model)
        return model
    
    # === Data Export/Import ===
    
    def export_experiment_data(self, experiment_id: str) -> Dict:
        """Export complete experiment data"""
        experiment = self.db.query(Experiment).filter(
            Experiment.experiment_id == experiment_id
        ).first()
        
        if not experiment:
            return {}
        
        # Get related data
        sensor_data = self.get_sensor_data_for_experiment(experiment_id)
        alarms = self.db.query(Alarm).filter(
            Alarm.experiment_id == experiment.id
        ).all()
        
        return {
            'experiment': {
                'id': experiment.experiment_id,
                'name': experiment.name,
                'description': experiment.description,
                'recipe_id': experiment.recipe_id,
                'objectives': experiment.objectives,
                'factors': experiment.factors,
                'parameters': experiment.parameters,
                'results': experiment.results,
                'status': experiment.status,
                'created_at': experiment.created_at.isoformat() if experiment.created_at else None
            },
            'sensor_data': [
                {
                    'timestamp': sd.timestamp.isoformat(),
                    'temperature': sd.temperature,
                    'pressure': sd.pressure,
                    'gas_flow': sd.gas_flow,
                    'power': sd.power
                }
                for sd in sensor_data
            ],
            'alarms': [
                {
                    'id': alarm.id,
                    'timestamp': alarm.timestamp.isoformat(),
                    'parameter': alarm.parameter,
                    'type': alarm.alarm_type,
                    'severity': alarm.severity,
                    'current_value': alarm.current_value,
                    'sigma_distance': alarm.sigma_distance
                }
                for alarm in alarms
            ]
        }
    
    def import_experiment_data(self, data: Dict) -> bool:
        """Import experiment data from external source"""
        try:
            # Create experiment
            exp_data = data['experiment']
            experiment = self.create_experiment(exp_data)
            
            # Import sensor data
            if 'sensor_data' in data:
                sensor_data_list = []
                for sd in data['sensor_data']:
                    sd['experiment_id'] = experiment.id
                    sd['recipe_id'] = experiment.recipe_id
                    if isinstance(sd['timestamp'], str):
                        sd['timestamp'] = datetime.fromisoformat(sd['timestamp'])
                    sensor_data_list.append(sd)
                
                self.ingest_sensor_data(sensor_data_list)
            
            # Import alarms
            if 'alarms' in data:
                for alarm_data in data['alarms']:
                    alarm = Alarm(
                        id=alarm_data.get('id', f"ALM-{uuid.uuid4().hex[:8].upper()}"),
                        experiment_id=experiment.id,
                        timestamp=datetime.fromisoformat(alarm_data['timestamp']),
                        parameter=alarm_data['parameter'],
                        alarm_type=alarm_data['type'],
                        severity=alarm_data['severity'],
                        current_value=alarm_data['current_value'],
                        sigma_distance=alarm_data.get('sigma_distance', 0.0)
                    )
                    self.db.add(alarm)
            
            self.db.commit()
            return True
            
        except Exception as e:
            self.db.rollback()
            print(f"Error importing experiment data: {e}")
            return False
    
    # === Analytics and Reporting ===
    
    def get_experiment_statistics(self, recipe_id: Optional[str] = None) -> Dict:
        """Get experiment statistics"""
        query = self.db.query(Experiment)
        
        if recipe_id:
            query = query.filter(Experiment.recipe_id == recipe_id)
        
        experiments = query.all()
        
        total_experiments = len(experiments)
        completed_experiments = len([e for e in experiments if e.status == 'COMPLETED'])
        avg_yield = np.mean([e.yield_value for e in experiments if e.yield_value is not None])
        
        return {
            'total_experiments': total_experiments,
            'completed_experiments': completed_experiments,
            'completion_rate': completed_experiments / total_experiments if total_experiments > 0 else 0,
            'average_yield': float(avg_yield) if not np.isnan(avg_yield) else 0.0,
            'active_experiments': len([e for e in experiments if e.status in ['PLANNED', 'RUNNING']])
        }
    
    def get_model_performance_history(self, limit: int = 10) -> List[Dict]:
        """Get recent model performance history"""
        models = self.db.query(ModelRegistry).filter(
            ModelRegistry.is_active == True
        ).order_by(desc(ModelRegistry.created_at)).limit(limit).all()
        
        return [
            {
                'model_id': model.model_id,
                'name': model.name,
                'algorithm': model.algorithm,
                'r2_score': model.r2_score,
                'mae': model.mae,
                'is_ensemble': model.is_ensemble,
                'ensemble_strategy': model.ensemble_strategy,
                'created_at': model.created_at.isoformat() if model.created_at else None
            }
            for model in models
        ]