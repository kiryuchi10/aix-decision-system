# ML Ensemble Service - handles missing optional dependencies gracefully
try:
    from xgboost import XGBRegressor
    XGBOOST_AVAILABLE = True
except ImportError:
    XGBOOST_AVAILABLE = False
    # Create a dummy class for type hints
    class XGBRegressor:
        def __init__(self, *args, **kwargs):
            raise ImportError("xgboost is not installed. Install with: pip install xgboost")

from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
from sklearn.neural_network import MLPRegressor
from sklearn.svm import SVR
import numpy as np
from typing import Dict, List, Any, Optional

class MLEnsembleService:
    """ML Ensemble service with graceful handling of missing dependencies"""
    
    def __init__(self):
        self.available_models = self._get_available_models()
    
    def _get_available_models(self) -> Dict[str, Any]:
        """Get available models, skipping ones with missing dependencies"""
        models = {
            'random_forest': {
                'model': RandomForestRegressor,
                'type': 'ensemble',
                'provides_uncertainty': False,
                'description': 'Random Forest Regressor'
            },
            'gradient_boosting': {
                'model': GradientBoostingRegressor,
                'type': 'ensemble',
                'provides_uncertainty': False,
                'description': 'Gradient Boosting Regressor'
            },
            'svm': {
                'model': SVR,
                'type': 'regressor',
                'provides_uncertainty': False,
                'description': 'Support Vector Regressor'
            },
            'neural_network': {
                'model': MLPRegressor,
                'type': 'neural',
                'provides_uncertainty': False,
                'description': 'Multi-layer Perceptron Regressor'
            }
        }
        
        # Add XGBoost only if available
        if XGBOOST_AVAILABLE:
            models['xgboost'] = {
                'model': XGBRegressor,
                'type': 'ensemble',
                'provides_uncertainty': False,
                'description': 'XGBoost Regressor'
            }
        
        return models
    
    def get_available_models(self) -> Dict[str, Any]:
        """Get list of available models"""
        return {
            name: {
                'type': info['type'],
                'provides_uncertainty': info['provides_uncertainty'],
                'description': info['description']
            }
            for name, info in self.available_models.items()
        }
    
    def create_model(self, model_name: str, **kwargs):
        """Create a model instance"""
        if model_name not in self.available_models:
            raise ValueError(f"Model '{model_name}' not available")
        
        model_class = self.available_models[model_name]['model']
        return model_class(**kwargs)
    
    def train_model(self, model, X: np.ndarray, y: np.ndarray):
        """Train a model"""
        return model.fit(X, y)
    
    def predict(self, model, X: np.ndarray) -> np.ndarray:
        """Make predictions"""
        return model.predict(X)
