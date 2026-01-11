from typing import List, Dict, Tuple, Optional
import numpy as np
from sklearn.gaussian_process import GaussianProcessRegressor
from sklearn.gaussian_process.kernels import RBF, ConstantKernel, Matern, WhiteKernel, RationalQuadratic
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor, ExtraTreesRegressor, AdaBoostRegressor
from sklearn.svm import SVR
from sklearn.neural_network import MLPRegressor
from sklearn.linear_model import Ridge, ElasticNet, BayesianRidge
from sklearn.neighbors import KNeighborsRegressor
from xgboost import XGBRegressor
try:
    from lightgbm import LGBMRegressor
    LIGHTGBM_AVAILABLE = True
except ImportError:
    LIGHTGBM_AVAILABLE = False
try:
    from catboost import CatBoostRegressor
    CATBOOST_AVAILABLE = True
except ImportError:
    CATBOOST_AVAILABLE = False
from sklearn.model_selection import cross_val_score, KFold
from sklearn.metrics import mean_absolute_error, r2_score, mean_squared_error
import json
from datetime import datetime
import joblib
import itertools
import os

class MLEnsembleService:
    """
    ML/DL 모델 앙상블 서비스
    - 여러 모델 조합을 자동으로 생성
    - 성능 비교 및 최적 조합 선택
    - 앙상블 전략: Voting, Stacking, Weighted Average
    """
    
    def __init__(self):
        self.model_registry = {}
        self.ensemble_results = []
    
    def get_available_models(self) -> Dict[str, Dict]:
        """사용 가능한 모델 정의 - Extended Model Registry"""
        models = {
            # === Probabilistic Models (Uncertainty Quantification) ===
            'gaussian_process_rbf': {
                'model': GaussianProcessRegressor(
                    kernel=ConstantKernel(1.0) * RBF(length_scale=1.0),
                    n_restarts_optimizer=10,
                    alpha=1e-6
                ),
                'type': 'probabilistic',
                'provides_uncertainty': True,
                'description': 'Gaussian Process with RBF kernel - best for uncertainty quantification'
            },
            'gaussian_process_matern': {
                'model': GaussianProcessRegressor(
                    kernel=ConstantKernel(1.0) * Matern(length_scale=1.0, nu=1.5),
                    n_restarts_optimizer=10,
                    alpha=1e-6
                ),
                'type': 'probabilistic',
                'provides_uncertainty': True,
                'description': 'Gaussian Process with Matern kernel - smoother predictions'
            },
            'gaussian_process_rq': {
                'model': GaussianProcessRegressor(
                    kernel=ConstantKernel(1.0) * RationalQuadratic(length_scale=1.0, alpha=1.0),
                    n_restarts_optimizer=10,
                    alpha=1e-6
                ),
                'type': 'probabilistic',
                'provides_uncertainty': True,
                'description': 'Gaussian Process with Rational Quadratic kernel - multi-scale patterns'
            },
            'bayesian_ridge': {
                'model': BayesianRidge(
                    alpha_1=1e-6,
                    alpha_2=1e-6,
                    lambda_1=1e-6,
                    lambda_2=1e-6
                ),
                'type': 'probabilistic',
                'provides_uncertainty': True,
                'description': 'Bayesian Ridge Regression - linear with uncertainty'
            },
            
            # === Ensemble Models (Robust Performance) ===
            'random_forest': {
                'model': RandomForestRegressor(
                    n_estimators=100,
                    max_depth=10,
                    min_samples_split=2,
                    random_state=42
                ),
                'type': 'ensemble',
                'provides_uncertainty': False,
                'description': 'Random Forest - robust to outliers, handles non-linearity'
            },
            'extra_trees': {
                'model': ExtraTreesRegressor(
                    n_estimators=100,
                    max_depth=10,
                    min_samples_split=2,
                    random_state=42
                ),
                'type': 'ensemble',
                'provides_uncertainty': False,
                'description': 'Extra Trees - faster than RF, good for high-dimensional data'
            },
            'ada_boost': {
                'model': AdaBoostRegressor(
                    n_estimators=100,
                    learning_rate=0.1,
                    random_state=42
                ),
                'type': 'ensemble',
                'provides_uncertainty': False,
                'description': 'AdaBoost - adaptive boosting for weak learners'
            },
            
            # === Gradient Boosting Models (High Performance) ===
            'xgboost': {
                'model': XGBRegressor(
                    n_estimators=100,
                    max_depth=6,
                    learning_rate=0.1,
                    random_state=42,
                    verbosity=0
                ),
                'type': 'boosting',
                'provides_uncertainty': False,
                'description': 'XGBoost - high performance, handles complex patterns'
            },
            'gradient_boosting': {
                'model': GradientBoostingRegressor(
                    n_estimators=100,
                    max_depth=5,
                    learning_rate=0.1,
                    random_state=42
                ),
                'type': 'boosting',
                'provides_uncertainty': False,
                'description': 'Gradient Boosting - good generalization'
            },
            
            # === Neural Networks (Deep Learning) ===
            'neural_network_small': {
                'model': MLPRegressor(
                    hidden_layer_sizes=(50, 25),
                    activation='relu',
                    solver='adam',
                    alpha=0.001,
                    max_iter=500,
                    random_state=42
                ),
                'type': 'neural_network',
                'provides_uncertainty': False,
                'description': 'Small Neural Network - fast training, good for simple patterns'
            },
            'neural_network_deep': {
                'model': MLPRegressor(
                    hidden_layer_sizes=(100, 50, 25),
                    activation='relu',
                    solver='adam',
                    alpha=0.001,
                    max_iter=1000,
                    random_state=42
                ),
                'type': 'neural_network',
                'provides_uncertainty': False,
                'description': 'Deep Neural Network - complex pattern recognition'
            },
            
            # === Support Vector Machines ===
            'svr_rbf': {
                'model': SVR(
                    kernel='rbf',
                    C=1.0,
                    gamma='scale',
                    epsilon=0.1
                ),
                'type': 'kernel',
                'provides_uncertainty': False,
                'description': 'Support Vector Regression with RBF kernel - non-linear patterns'
            },
            'svr_poly': {
                'model': SVR(
                    kernel='poly',
                    degree=3,
                    C=1.0,
                    gamma='scale',
                    epsilon=0.1
                ),
                'type': 'kernel',
                'provides_uncertainty': False,
                'description': 'Support Vector Regression with Polynomial kernel'
            },
            
            # === Linear Models (Interpretable) ===
            'ridge': {
                'model': Ridge(
                    alpha=1.0,
                    random_state=42
                ),
                'type': 'linear',
                'provides_uncertainty': False,
                'description': 'Ridge Regression - L2 regularization, interpretable'
            },
            'elastic_net': {
                'model': ElasticNet(
                    alpha=1.0,
                    l1_ratio=0.5,
                    random_state=42
                ),
                'type': 'linear',
                'provides_uncertainty': False,
                'description': 'Elastic Net - L1+L2 regularization, feature selection'
            },
            
            # === Instance-based Models ===
            'knn': {
                'model': KNeighborsRegressor(
                    n_neighbors=5,
                    weights='distance'
                ),
                'type': 'instance_based',
                'provides_uncertainty': False,
                'description': 'K-Nearest Neighbors - local patterns, non-parametric'
            }
        }
        
        # Add LightGBM if available
        if LIGHTGBM_AVAILABLE:
            models['lightgbm'] = {
                'model': LGBMRegressor(
                    n_estimators=100,
                    max_depth=6,
                    learning_rate=0.1,
                    random_state=42,
                    verbosity=-1
                ),
                'type': 'boosting',
                'provides_uncertainty': False,
                'description': 'LightGBM - fast gradient boosting, memory efficient'
            }
        
        # Add CatBoost if available
        if CATBOOST_AVAILABLE:
            models['catboost'] = {
                'model': CatBoostRegressor(
                    iterations=100,
                    depth=6,
                    learning_rate=0.1,
                    random_seed=42,
                    verbose=False
                ),
                'type': 'boosting',
                'provides_uncertainty': False,
                'description': 'CatBoost - handles categorical features, robust to overfitting'
            }
        
        return models
    
    def generate_model_combinations(self, min_models: int = 2, max_models: int = 4) -> List[List[str]]:
        """
        자동으로 여러 모델 조합 생성
        
        전략:
        - 확률적 모델 최소 1개 포함 (uncertainty 제공)
        - 다양한 타입 조합 (probabilistic + ensemble + boosting)
        """
        available_models = self.get_available_models()
        model_names = list(available_models.keys())
        
        probabilistic_models = [name for name, info in available_models.items() 
                               if info['provides_uncertainty']]
        other_models = [name for name, info in available_models.items() 
                       if not info['provides_uncertainty']]
        
        combinations = []
        
        # Strategy 1: All probabilistic (for uncertainty)
        combinations.append(probabilistic_models)
        
        # Strategy 2: 1 probabilistic + 2-3 others
        for prob_model in probabilistic_models:
            for r in range(1, min(len(other_models), max_models - 1) + 1):
                for combo in itertools.combinations(other_models, r):
                    combinations.append([prob_model] + list(combo))
        
        # Strategy 3: All ensemble/boosting (for performance)
        if len(other_models) >= min_models:
            combinations.append(other_models)
        
        # Strategy 4: Diverse mix
        for r in range(min_models, min(len(model_names), max_models) + 1):
            for combo in itertools.combinations(model_names, r):
                if combo not in combinations:
                    combinations.append(list(combo))
        
        # Limit combinations
        return combinations[:20]  # Top 20 combinations
    
    def train_and_evaluate_combination(
        self,
        model_names: List[str],
        X_train: np.ndarray,
        y_train: np.ndarray,
        X_test: np.ndarray,
        y_test: np.ndarray,
        cv_folds: int = 5
    ) -> Dict:
        """
        모델 조합 학습 및 평가
        """
        available_models = self.get_available_models()
        trained_models = []
        individual_scores = []
        
        # Train individual models
        for model_name in model_names:
            model_info = available_models[model_name]
            model = model_info['model']
            
            # Train
            model.fit(X_train, y_train)
            
            # Evaluate
            y_pred = model.predict(X_test)
            mae = mean_absolute_error(y_test, y_pred)
            r2 = r2_score(y_test, y_pred)
            rmse = np.sqrt(mean_squared_error(y_test, y_pred))
            
            # Cross-validation score
            cv_scores = cross_val_score(
                model, X_train, y_train, 
                cv=KFold(n_splits=cv_folds, shuffle=True, random_state=42),
                scoring='r2'
            )
            
            trained_models.append({
                'name': model_name,
                'model': model,
                'info': model_info
            })
            
            individual_scores.append({
                'name': model_name,
                'mae': float(mae),
                'r2': float(r2),
                'rmse': float(rmse),
                'cv_mean': float(cv_scores.mean()),
                'cv_std': float(cv_scores.std())
            })
        
        # Ensemble predictions
        ensemble_results = self._create_ensemble_predictions(
            trained_models, X_test, y_test
        )
        
        return {
            'combination': model_names,
            'individual_scores': individual_scores,
            'ensemble_results': ensemble_results,
            'trained_models': trained_models
        }
    
    def _create_ensemble_predictions(
        self,
        trained_models: List[Dict],
        X_test: np.ndarray,
        y_test: np.ndarray
    ) -> Dict:
        """
        앙상블 예측 생성 (다양한 전략)
        """
        predictions = []
        uncertainties = []
        
        # Get predictions from all models
        for model_data in trained_models:
            model = model_data['model']
            pred = model.predict(X_test)
            predictions.append(pred)
            
            # Get uncertainty if available
            if model_data['info']['provides_uncertainty']:
                try:
                    _, std = model.predict(X_test, return_std=True)
                    uncertainties.append(std)
                except:
                    pass
        
        predictions = np.array(predictions)
        
        ensemble_strategies = {}
        
        # Strategy 1: Simple Average
        avg_pred = np.mean(predictions, axis=0)
        ensemble_strategies['average'] = {
            'predictions': avg_pred,
            'mae': float(mean_absolute_error(y_test, avg_pred)),
            'r2': float(r2_score(y_test, avg_pred)),
            'rmse': float(np.sqrt(mean_squared_error(y_test, avg_pred))),
            'description': 'Simple average of all model predictions'
        }
        
        # Strategy 2: Median (robust to outliers)
        median_pred = np.median(predictions, axis=0)
        ensemble_strategies['median'] = {
            'predictions': median_pred,
            'mae': float(mean_absolute_error(y_test, median_pred)),
            'r2': float(r2_score(y_test, median_pred)),
            'rmse': float(np.sqrt(mean_squared_error(y_test, median_pred))),
            'description': 'Median of all predictions - robust to outliers'
        }
        
        # Strategy 3: Weighted Average (by inverse MAE)
        weights = []
        for pred in predictions:
            mae = mean_absolute_error(y_test, pred)
            weights.append(1.0 / (mae + 1e-6))
        weights = np.array(weights)
        weights = weights / weights.sum()
        
        weighted_pred = np.average(predictions, axis=0, weights=weights)
        ensemble_strategies['weighted_mae'] = {
            'predictions': weighted_pred,
            'weights': weights.tolist(),
            'mae': float(mean_absolute_error(y_test, weighted_pred)),
            'r2': float(r2_score(y_test, weighted_pred)),
            'rmse': float(np.sqrt(mean_squared_error(y_test, weighted_pred))),
            'description': 'Weighted average by inverse MAE'
        }
        
        # Strategy 4: Weighted Average (by R2)
        weights_r2 = []
        for pred in predictions:
            r2 = r2_score(y_test, pred)
            weights_r2.append(max(r2, 0))  # Clip negative R2
        weights_r2 = np.array(weights_r2)
        if weights_r2.sum() > 0:
            weights_r2 = weights_r2 / weights_r2.sum()
            
            weighted_r2_pred = np.average(predictions, axis=0, weights=weights_r2)
            ensemble_strategies['weighted_r2'] = {
                'predictions': weighted_r2_pred,
                'weights': weights_r2.tolist(),
                'mae': float(mean_absolute_error(y_test, weighted_r2_pred)),
                'r2': float(r2_score(y_test, weighted_r2_pred)),
                'rmse': float(np.sqrt(mean_squared_error(y_test, weighted_r2_pred))),
                'description': 'Weighted average by R2 score'
            }
        
        # Strategy 5: Voting (majority for classification-like approach)
        # For regression, use "soft voting" - round and vote
        rounded_predictions = np.round(predictions, 1)
        voted_pred = []
        for i in range(len(y_test)):
            votes = rounded_predictions[:, i]
            # Use most common prediction
            unique, counts = np.unique(votes, return_counts=True)
            voted_pred.append(unique[np.argmax(counts)])
        voted_pred = np.array(voted_pred)
        
        ensemble_strategies['voting'] = {
            'predictions': voted_pred,
            'mae': float(mean_absolute_error(y_test, voted_pred)),
            'r2': float(r2_score(y_test, voted_pred)),
            'rmse': float(np.sqrt(mean_squared_error(y_test, voted_pred))),
            'description': 'Voting-based ensemble (soft voting)'
        }
        
        # Strategy 6: Uncertainty-weighted (if available)
        if len(uncertainties) > 0:
            uncertainties = np.array(uncertainties)
            # Weight by inverse uncertainty
            unc_weights = 1.0 / (uncertainties + 1e-6)
            unc_weights = unc_weights / unc_weights.sum(axis=0)
            
            unc_pred = np.sum(predictions[:len(uncertainties)] * unc_weights, axis=0)
            ensemble_strategies['uncertainty_weighted'] = {
                'predictions': unc_pred,
                'mae': float(mean_absolute_error(y_test, unc_pred)),
                'r2': float(r2_score(y_test, unc_pred)),
                'rmse': float(np.sqrt(mean_squared_error(y_test, unc_pred))),
                'description': 'Weighted by inverse uncertainty from probabilistic models',
                'avg_uncertainty': float(np.mean(uncertainties))
            }
        
        # Strategy 7: Dynamic Weighted Average (performance-based)
        dynamic_weights = []
        for pred in predictions:
            # Calculate multiple metrics
            mae = mean_absolute_error(y_test, pred)
            r2 = r2_score(y_test, pred)
            rmse = np.sqrt(mean_squared_error(y_test, pred))
            
            # Combined score (higher is better)
            combined_score = r2 - (mae / 100.0) - (rmse / 100.0)
            dynamic_weights.append(max(combined_score, 0))
        
        dynamic_weights = np.array(dynamic_weights)
        if dynamic_weights.sum() > 0:
            dynamic_weights = dynamic_weights / dynamic_weights.sum()
            
            dynamic_pred = np.average(predictions, axis=0, weights=dynamic_weights)
            ensemble_strategies['dynamic_weighted'] = {
                'predictions': dynamic_pred,
                'weights': dynamic_weights.tolist(),
                'mae': float(mean_absolute_error(y_test, dynamic_pred)),
                'r2': float(r2_score(y_test, dynamic_pred)),
                'rmse': float(np.sqrt(mean_squared_error(y_test, dynamic_pred))),
                'description': 'Dynamic weighting based on combined performance metrics'
            }
        
        # Strategy 8: Trimmed Mean (remove outliers)
        if len(predictions) >= 3:
            # Remove top and bottom 20% of predictions for each sample
            trim_percent = 0.2
            trim_count = max(1, int(len(predictions) * trim_percent))
            
            trimmed_pred = []
            for i in range(len(y_test)):
                sample_preds = predictions[:, i]
                sorted_preds = np.sort(sample_preds)
                trimmed = sorted_preds[trim_count:-trim_count] if trim_count < len(sorted_preds)//2 else sorted_preds
                trimmed_pred.append(np.mean(trimmed))
            
            trimmed_pred = np.array(trimmed_pred)
            ensemble_strategies['trimmed_mean'] = {
                'predictions': trimmed_pred,
                'mae': float(mean_absolute_error(y_test, trimmed_pred)),
                'r2': float(r2_score(y_test, trimmed_pred)),
                'rmse': float(np.sqrt(mean_squared_error(y_test, trimmed_pred))),
                'description': f'Trimmed mean (remove {trim_percent*100}% outliers)'
            }
        
        # Strategy 9: Stacking-like approach (simple meta-learner)
        if len(predictions) >= 2:
            # Use simple linear combination as meta-learner
            from sklearn.linear_model import LinearRegression
            
            try:
                # Prepare meta-features (predictions as features)
                meta_X = predictions.T  # Shape: (n_samples, n_models)
                
                # Train simple meta-learner
                meta_learner = LinearRegression()
                meta_learner.fit(meta_X, y_test)
                
                # Get stacked predictions
                stacked_pred = meta_learner.predict(meta_X)
                
                ensemble_strategies['stacking_linear'] = {
                    'predictions': stacked_pred,
                    'mae': float(mean_absolute_error(y_test, stacked_pred)),
                    'r2': float(r2_score(y_test, stacked_pred)),
                    'rmse': float(np.sqrt(mean_squared_error(y_test, stacked_pred))),
                    'description': 'Linear stacking with meta-learner',
                    'meta_weights': meta_learner.coef_.tolist()
                }
            except Exception as e:
                print(f"Stacking strategy failed: {e}")
        
        # Strategy 10: Confidence-weighted ensemble
        confidence_weights = []
        for i, pred in enumerate(predictions):
            # Calculate confidence based on prediction consistency
            pred_std = np.std(pred)
            confidence = 1.0 / (pred_std + 1e-6)  # Higher confidence for lower variance
            confidence_weights.append(confidence)
        
        confidence_weights = np.array(confidence_weights)
        confidence_weights = confidence_weights / confidence_weights.sum()
        
        confidence_pred = np.average(predictions, axis=0, weights=confidence_weights)
        ensemble_strategies['confidence_weighted'] = {
            'predictions': confidence_pred,
            'weights': confidence_weights.tolist(),
            'mae': float(mean_absolute_error(y_test, confidence_pred)),
            'r2': float(r2_score(y_test, confidence_pred)),
            'rmse': float(np.sqrt(mean_squared_error(y_test, confidence_pred))),
            'description': 'Weighted by prediction confidence (inverse variance)'
        }
        
        return ensemble_strategies
    
    def run_automated_pipeline(
        self,
        X_train: np.ndarray,
        y_train: np.ndarray,
        X_test: np.ndarray,
        y_test: np.ndarray,
        experiment_id: str
    ) -> Dict:
        """
        자동화된 ML 파이프라인 실행
        - 모든 조합 생성
        - 각 조합 학습 및 평가
        - 최적 조합 선택
        """
        print(f"Starting automated ML pipeline for experiment {experiment_id}")
        
        # Generate combinations
        combinations = self.generate_model_combinations()
        print(f"Generated {len(combinations)} model combinations")
        
        results = []
        
        # Evaluate each combination
        for i, combo in enumerate(combinations):
            print(f"Evaluating combination {i+1}/{len(combinations)}: {combo}")
            
            try:
                result = self.train_and_evaluate_combination(
                    combo, X_train, y_train, X_test, y_test
                )
                results.append(result)
            except Exception as e:
                print(f"Error evaluating combination {combo}: {str(e)}")
                continue
        
        # Rank combinations
        ranked_results = self._rank_combinations(results)
        
        # Select best combination
        best_combination = ranked_results[0] if ranked_results else None
        
        # Save results
        pipeline_results = {
            'experiment_id': experiment_id,
            'timestamp': datetime.utcnow().isoformat(),
            'total_combinations': len(combinations),
            'successful_evaluations': len(results),
            'ranked_results': ranked_results,
            'best_combination': best_combination,
            'recommendations': self._generate_recommendations(ranked_results)
        }
        
        self.ensemble_results.append(pipeline_results)
        
        return pipeline_results
    
    def _rank_combinations(self, results: List[Dict]) -> List[Dict]:
        """
        조합 순위 매기기
        
        평가 기준:
        1. 앙상블 R2 (40%)
        2. 앙상블 MAE (30%)
        3. 개별 모델 평균 성능 (20%)
        4. 불확실성 제공 여부 (10%)
        """
        ranked = []
        
        for result in results:
            # Get best ensemble strategy
            ensemble_results = result['ensemble_results']
            best_ensemble = max(
                ensemble_results.items(),
                key=lambda x: x[1]['r2']
            )
            
            # Calculate score
            r2_score_val = best_ensemble[1]['r2']
            mae_score = 1.0 / (best_ensemble[1]['mae'] + 1e-6)
            
            # Average individual model performance
            avg_individual_r2 = np.mean([s['r2'] for s in result['individual_scores']])
            
            # Uncertainty bonus
            has_uncertainty = any(
                m['info']['provides_uncertainty'] 
                for m in result['trained_models']
            )
            uncertainty_bonus = 0.1 if has_uncertainty else 0
            
            # Weighted score
            score = (
                0.4 * r2_score_val +
                0.3 * min(mae_score / 10.0, 1.0) +  # Normalize MAE
                0.2 * avg_individual_r2 +
                uncertainty_bonus
            )
            
            ranked.append({
                'combination': result['combination'],
                'score': float(score),
                'best_ensemble_strategy': best_ensemble[0],
                'ensemble_r2': float(best_ensemble[1]['r2']),
                'ensemble_mae': float(best_ensemble[1]['mae']),
                'ensemble_rmse': float(best_ensemble[1]['rmse']),
                'individual_scores': result['individual_scores'],
                'ensemble_results': result['ensemble_results'],
                'has_uncertainty': has_uncertainty
            })
        
        # Sort by score
        ranked.sort(key=lambda x: x['score'], reverse=True)
        
        return ranked
    
    def _generate_recommendations(self, ranked_results: List[Dict]) -> Dict:
        """
        사용자를 위한 추천 생성
        """
        if not ranked_results:
            return {'message': 'No successful combinations evaluated'}
        
        best = ranked_results[0]
        
        recommendations = {
            'best_combination': best['combination'],
            'expected_performance': {
                'r2': best['ensemble_r2'],
                'mae': best['ensemble_mae'],
                'rmse': best['ensemble_rmse']
            },
            'ensemble_strategy': best['best_ensemble_strategy'],
            'confidence_level': 'high' if best['score'] > 0.8 else 'medium' if best['score'] > 0.6 else 'low',
            'use_cases': []
        }
        
        # Use case recommendations
        if best['has_uncertainty']:
            recommendations['use_cases'].append({
                'scenario': 'Production deployment',
                'reason': 'Provides uncertainty estimates for risk assessment'
            })
        
        if best['ensemble_mae'] < 2.0:
            recommendations['use_cases'].append({
                'scenario': 'High-precision requirements',
                'reason': f'Low MAE ({best["ensemble_mae"]:.2f}%) ensures accurate predictions'
            })
        
        if len(best['combination']) >= 3:
            recommendations['use_cases'].append({
                'scenario': 'Robust predictions',
                'reason': 'Multiple models reduce overfitting risk'
            })
        
        # Alternative combinations
        recommendations['alternatives'] = [
            {
                'rank': i + 2,
                'combination': r['combination'],
                'r2': r['ensemble_r2'],
                'reason': self._explain_alternative(r, best)
            }
            for i, r in enumerate(ranked_results[1:4])  # Top 3 alternatives
        ]
        
        return recommendations
    
    def _explain_alternative(self, alternative: Dict, best: Dict) -> str:
        """대안 조합에 대한 설명"""
        if alternative['has_uncertainty'] and not best['has_uncertainty']:
            return "Better uncertainty quantification"
        elif len(alternative['combination']) < len(best['combination']):
            return "Simpler model, faster inference"
        elif alternative['ensemble_mae'] < best['ensemble_mae']:
            return "Lower prediction error"
        else:
            return "Different model diversity"
    
    def save_best_model(
        self,
        pipeline_results: Dict,
        save_path: str
    ) -> str:
        """
        최적 모델 조합 저장
        """
        best = pipeline_results['best_combination']
        
        model_package = {
            'combination': best['combination'],
            'ensemble_strategy': best['best_ensemble_strategy'],
            'metadata': {
                'experiment_id': pipeline_results['experiment_id'],
                'timestamp': pipeline_results['timestamp'],
                'performance': {
                    'r2': best['ensemble_r2'],
                    'mae': best['ensemble_mae'],
                    'rmse': best['ensemble_rmse']
                }
            }
        }
        
        # Save to file
        os.makedirs(save_path, exist_ok=True)
        
        model_file = os.path.join(
            save_path,
            f"ensemble_model_{pipeline_results['experiment_id']}.pkl"
        )
        
        joblib.dump(model_package, model_file)
        
        # Save metadata as JSON
        metadata_file = os.path.join(
            save_path,
            f"ensemble_metadata_{pipeline_results['experiment_id']}.json"
        )
        
        with open(metadata_file, 'w') as f:
            json.dump(model_package['metadata'], f, indent=2)
        
        return model_file