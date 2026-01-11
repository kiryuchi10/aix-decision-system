from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime
import numpy as np
import uuid

from ..core.database import get_db
from ..services.data_integration_service import DataIntegrationService
from ..services.ml_ensemble_service import MLEnsembleService
from pydantic import BaseModel

router = APIRouter(prefix="/ml-pipeline", tags=["ML Pipeline"])

# Schemas
class ModelCombinationRequest(BaseModel):
    experiment_id: str
    model_names: List[str]

class AutomatedPipelineRequest(BaseModel):
    experiment_id: str
    min_models: int = 2
    max_models: int = 4

class ModelComparisonResponse(BaseModel):
    combination: List[str]
    score: float
    ensemble_r2: float
    ensemble_mae: float
    ensemble_rmse: float
    best_ensemble_strategy: str
    individual_scores: List[dict]
    has_uncertainty: bool

# In-memory storage for pipeline results (should use DB in production)
pipeline_cache = {}

@router.get("/available-models")
def get_available_models():
    """Get list of available ML models"""
    service = MLEnsembleService()
    models = service.get_available_models()
    
    return {
        "models": [
            {
                "name": name,
                "type": info["type"],
                "provides_uncertainty": info["provides_uncertainty"],
                "description": info["description"]
            }
            for name, info in models.items()
        ]
    }

@router.post("/evaluate-combination")
async def evaluate_combination(
    request: ModelCombinationRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """
    특정 모델 조합 평가
    """
    # Generate mock training data for demo
    X_train, y_train, X_test, y_test = generate_mock_experiment_data()
    
    if len(X_train) < 10:
        raise HTTPException(status_code=400, detail="Insufficient training data (minimum 10 samples)")
    
    # Evaluate combination
    service = MLEnsembleService()
    
    try:
        result = service.train_and_evaluate_combination(
            request.model_names,
            X_train, y_train,
            X_test, y_test
        )
        
        return {
            "status": "success",
            "combination": result["combination"],
            "individual_scores": result["individual_scores"],
            "ensemble_results": result["ensemble_results"]
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Evaluation failed: {str(e)}")

@router.post("/run-automated-pipeline")
async def run_automated_pipeline(
    request: AutomatedPipelineRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """
    자동화된 ML 파이프라인 실행
    - 실제 실험 데이터 사용 또는 합성 데이터 생성
    - 모든 조합 생성 및 평가
    - 최적 조합 선택
    """
    # Generate pipeline ID
    pipeline_id = f"PIPELINE-{uuid.uuid4().hex[:8].upper()}"
    
    # Initialize data integration service
    data_service = DataIntegrationService(db)
    
    # Create pipeline record in database
    pipeline_data = {
        'pipeline_id': pipeline_id,
        'experiment_id': request.experiment_id,
        'config': {
            'min_models': request.min_models,
            'max_models': request.max_models
        }
    }
    data_service.create_ml_pipeline_record(pipeline_data)
    
    # Get experiment data (real or synthetic)
    try:
        X_train, y_train, X_test, y_test = data_service.get_experiment_data_for_ml(request.experiment_id)
    except Exception as e:
        print(f"Using synthetic data due to: {e}")
        X_train, y_train, X_test, y_test = generate_mock_experiment_data()
    
    if len(X_train) < 10:
        raise HTTPException(status_code=400, detail="Insufficient training data")
    
    # Run pipeline in background
    background_tasks.add_task(
        execute_pipeline_task,
        pipeline_id,
        request.experiment_id,
        X_train, y_train,
        X_test, y_test,
        db
    )
    
    return {
        "status": "started",
        "pipeline_id": pipeline_id,
        "message": "Pipeline execution started. Check status endpoint for progress.",
        "data_source": "real_experiment_data" if request.experiment_id.startswith("EXP-") else "synthetic_data"
    }

@router.get("/pipeline-status/{pipeline_id}")
def get_pipeline_status(pipeline_id: str):
    """파이프라인 실행 상태 확인"""
    if pipeline_id not in pipeline_cache:
        raise HTTPException(status_code=404, detail="Pipeline not found")
    
    return pipeline_cache[pipeline_id]

@router.get("/pipeline-results/{pipeline_id}")
def get_pipeline_results(pipeline_id: str):
    """파이프라인 전체 결과 조회"""
    if pipeline_id not in pipeline_cache:
        raise HTTPException(status_code=404, detail="Pipeline not found")
    
    results = pipeline_cache[pipeline_id]
    
    if results["status"] != "completed":
        return {
            "status": results["status"],
            "progress": results.get("progress", 0)
        }
    
    return results["results"]

@router.post("/select-best-combination/{pipeline_id}")
async def select_best_combination(
    pipeline_id: str,
    db: Session = Depends(get_db)
):
    """
    최적 조합 선택 및 모델 레지스트리에 저장
    """
    if pipeline_id not in pipeline_cache:
        raise HTTPException(status_code=404, detail="Pipeline not found")
    
    results = pipeline_cache[pipeline_id]
    
    if results["status"] != "completed":
        raise HTTPException(status_code=400, detail="Pipeline not completed yet")
    
    pipeline_results = results["results"]
    best_combination = pipeline_results["best_combination"]
    
    # For now, just return the selection (would save to DB in production)
    return {
        "status": "success",
        "model_id": f"MODEL-{uuid.uuid4().hex[:8].upper()}",
        "combination": best_combination["combination"],
        "performance": {
            "r2": best_combination["ensemble_r2"],
            "mae": best_combination["ensemble_mae"],
            "rmse": best_combination["ensemble_rmse"]
        },
        "ensemble_strategy": best_combination["best_ensemble_strategy"]
    }

@router.get("/model-comparison/{experiment_id}")
def get_model_comparison(experiment_id: str, db: Session = Depends(get_db)):
    """
    실험에 대한 모든 모델 비교 결과 조회
    """
    # Find all pipelines for this experiment
    experiment_pipelines = [
        results for results in pipeline_cache.values()
        if results.get("experiment_id") == experiment_id and results["status"] == "completed"
    ]
    
    if not experiment_pipelines:
        return {
            "experiment_id": experiment_id,
            "message": "No completed pipelines found for this experiment",
            "comparisons": []
        }
    
    # Extract comparison data
    comparisons = []
    for pipeline in experiment_pipelines:
        results = pipeline["results"]
        for ranked in results["ranked_results"][:5]:  # Top 5
            comparisons.append({
                "combination": ranked["combination"],
                "score": ranked["score"],
                "r2": ranked["ensemble_r2"],
                "mae": ranked["ensemble_mae"],
                "rmse": ranked["ensemble_rmse"],
                "strategy": ranked["best_ensemble_strategy"],
                "has_uncertainty": ranked["has_uncertainty"]
            })
    
    # Sort by score
    comparisons.sort(key=lambda x: x["score"], reverse=True)
    
    return {
        "experiment_id": experiment_id,
        "total_comparisons": len(comparisons),
        "comparisons": comparisons[:10]  # Top 10
    }

# Helper functions
def generate_mock_experiment_data() -> tuple:
    """Generate mock experiment data for demo purposes"""
    np.random.seed(42)
    
    # Generate synthetic DoE data
    n_samples = 100
    n_features = 4  # temperature, pressure, gas_flow, power
    
    # Features (process parameters)
    X = np.random.normal(0, 1, (n_samples, n_features))
    
    # Target (yield) - synthetic relationship
    y = (
        0.3 * X[:, 0] +  # temperature effect
        0.2 * X[:, 1] +  # pressure effect
        0.1 * X[:, 2] +  # gas flow effect
        0.15 * X[:, 3] + # power effect
        0.1 * X[:, 0] * X[:, 1] +  # interaction
        np.random.normal(0, 0.1, n_samples)  # noise
    )
    
    # Normalize yield to 0-100%
    y = 85 + 10 * (y - y.min()) / (y.max() - y.min())
    
    # Train/test split (80/20)
    split_idx = int(len(X) * 0.8)
    
    X_train = X[:split_idx]
    y_train = y[:split_idx]
    X_test = X[split_idx:]
    y_test = y[split_idx:]
    
    return X_train, y_train, X_test, y_test

def execute_pipeline_task(
    pipeline_id: str,
    experiment_id: str,
    X_train: np.ndarray,
    y_train: np.ndarray,
    X_test: np.ndarray,
    y_test: np.ndarray,
    db: Session
):
    """백그라운드에서 파이프라인 실행 - Database integrated"""
    
    # Initialize status
    pipeline_cache[pipeline_id] = {
        "pipeline_id": pipeline_id,
        "experiment_id": experiment_id,
        "status": "running",
        "progress": 0,
        "started_at": datetime.utcnow().isoformat()
    }
    
    try:
        # Initialize services
        service = MLEnsembleService()
        data_service = DataIntegrationService(db)
        
        # Run automated pipeline
        results = service.run_automated_pipeline(
            X_train, y_train,
            X_test, y_test,
            experiment_id
        )
        
        # Update database with results
        data_service.update_ml_pipeline_results(pipeline_id, results)
        
        # Save best model to registry
        if 'best_combination' in results:
            best = results['best_combination']
            model_data = {
                'model_id': f"MODEL-{uuid.uuid4().hex[:8].upper()}",
                'experiment_id': experiment_id,
                'combination': best['combination'],
                'ensemble_strategy': best['best_ensemble_strategy'],
                'performance': {
                    'r2': best['ensemble_r2'],
                    'mae': best['ensemble_mae'],
                    'rmse': best['ensemble_rmse']
                },
                'model_path': f"./models/{experiment_id}/ensemble_model_{pipeline_id}.pkl"
            }
            data_service.save_best_model_to_registry(pipeline_id, model_data)
        
        # Update cache
        pipeline_cache[pipeline_id] = {
            "pipeline_id": pipeline_id,
            "experiment_id": experiment_id,
            "status": "completed",
            "progress": 100,
            "started_at": pipeline_cache[pipeline_id]["started_at"],
            "completed_at": datetime.utcnow().isoformat(),
            "results": results
        }
        
        # Save best model files
        model_path = f"./models/{experiment_id}"
        service.save_best_model(results, model_path)
        
    except Exception as e:
        pipeline_cache[pipeline_id] = {
            "pipeline_id": pipeline_id,
            "experiment_id": experiment_id,
            "status": "failed",
            "error": str(e),
            "started_at": pipeline_cache[pipeline_id]["started_at"],
            "failed_at": datetime.utcnow().isoformat()
        }