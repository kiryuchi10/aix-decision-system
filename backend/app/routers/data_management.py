from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.orm import Session
from typing import List, Dict, Optional
from datetime import datetime
import json
import uuid

from ..core.database import get_db
from ..services.data_integration_service import DataIntegrationService
from pydantic import BaseModel

router = APIRouter(prefix="/data", tags=["Data Management"])

# Schemas
class RecipeCreate(BaseModel):
    name: str
    description: Optional[str] = None
    temperature_min: float = 840.0
    temperature_max: float = 860.0
    temperature_optimal: float = 850.0
    pressure_min: float = 2.3
    pressure_max: float = 2.7
    pressure_optimal: float = 2.5
    gas_flow_min: float = 90.0
    gas_flow_max: float = 110.0
    gas_flow_optimal: float = 100.0
    power_min: float = 1400.0
    power_max: float = 1600.0
    power_optimal: float = 1500.0

class ExperimentCreate(BaseModel):
    experiment_id: Optional[str] = None
    recipe_id: str
    name: Optional[str] = None
    description: Optional[str] = None
    objectives: List[str] = ["maximize_yield"]
    factors: Dict = {}
    constraints: Dict = {}
    parameters: Dict = {}
    estimated_duration: int = 120

class SensorDataBatch(BaseModel):
    experiment_id: Optional[str] = None
    recipe_id: Optional[str] = None
    data: List[Dict]

# === Recipe Management ===

@router.post("/recipes")
async def create_recipe(recipe: RecipeCreate, db: Session = Depends(get_db)):
    """Create a new process recipe"""
    data_service = DataIntegrationService(db)
    
    recipe_data = recipe.dict()
    recipe_data['id'] = f"RCP-{uuid.uuid4().hex[:8].upper()}"
    
    try:
        new_recipe = data_service.create_recipe(recipe_data)
        return {
            "status": "success",
            "recipe_id": new_recipe.id,
            "message": "Recipe created successfully"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create recipe: {str(e)}")

@router.get("/recipes")
async def list_recipes(db: Session = Depends(get_db)):
    """List all recipes"""
    from ..models.experiment import Recipe
    
    recipes = db.query(Recipe).filter(Recipe.is_active == True).all()
    
    return {
        "recipes": [
            {
                "id": recipe.id,
                "name": recipe.name,
                "description": recipe.description,
                "process_window": {
                    "temperature": {
                        "min": recipe.temperature_min,
                        "max": recipe.temperature_max,
                        "optimal": recipe.temperature_optimal
                    },
                    "pressure": {
                        "min": recipe.pressure_min,
                        "max": recipe.pressure_max,
                        "optimal": recipe.pressure_optimal
                    }
                },
                "created_at": recipe.created_at.isoformat() if recipe.created_at else None
            }
            for recipe in recipes
        ]
    }

@router.get("/recipes/{recipe_id}")
async def get_recipe(recipe_id: str, db: Session = Depends(get_db)):
    """Get recipe details"""
    data_service = DataIntegrationService(db)
    
    recipe = data_service.get_recipe(recipe_id)
    if not recipe:
        raise HTTPException(status_code=404, detail="Recipe not found")
    
    return {
        "id": recipe.id,
        "name": recipe.name,
        "description": recipe.description,
        "process_window": {
            "temperature": {
                "min": recipe.temperature_min,
                "max": recipe.temperature_max,
                "optimal": recipe.temperature_optimal
            },
            "pressure": {
                "min": recipe.pressure_min,
                "max": recipe.pressure_max,
                "optimal": recipe.pressure_optimal
            },
            "gas_flow": {
                "min": recipe.gas_flow_min,
                "max": recipe.gas_flow_max,
                "optimal": recipe.gas_flow_optimal
            },
            "power": {
                "min": recipe.power_min,
                "max": recipe.power_max,
                "optimal": recipe.power_optimal
            }
        },
        "created_at": recipe.created_at.isoformat() if recipe.created_at else None
    }

# === Experiment Management ===

@router.post("/experiments")
async def create_experiment(experiment: ExperimentCreate, db: Session = Depends(get_db)):
    """Create a new experiment"""
    data_service = DataIntegrationService(db)
    
    experiment_data = experiment.dict()
    if not experiment_data['experiment_id']:
        experiment_data['experiment_id'] = f"EXP-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
    
    try:
        new_experiment = data_service.create_experiment(experiment_data)
        return {
            "status": "success",
            "experiment_id": new_experiment.experiment_id,
            "internal_id": new_experiment.id,
            "message": "Experiment created successfully"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create experiment: {str(e)}")

@router.get("/experiments")
async def list_experiments(recipe_id: Optional[str] = None, db: Session = Depends(get_db)):
    """List experiments"""
    from ..models.experiment import Experiment
    
    query = db.query(Experiment)
    if recipe_id:
        query = query.filter(Experiment.recipe_id == recipe_id)
    
    experiments = query.order_by(Experiment.created_at.desc()).limit(50).all()
    
    return {
        "experiments": [
            {
                "id": exp.experiment_id,
                "name": exp.name,
                "recipe_id": exp.recipe_id,
                "status": exp.status,
                "objectives": exp.objectives,
                "yield_value": exp.yield_value,
                "created_at": exp.created_at.isoformat() if exp.created_at else None
            }
            for exp in experiments
        ]
    }

@router.get("/experiments/{experiment_id}")
async def get_experiment(experiment_id: str, db: Session = Depends(get_db)):
    """Get experiment details"""
    from ..models.experiment import Experiment
    
    experiment = db.query(Experiment).filter(
        Experiment.experiment_id == experiment_id
    ).first()
    
    if not experiment:
        raise HTTPException(status_code=404, detail="Experiment not found")
    
    return {
        "id": experiment.experiment_id,
        "name": experiment.name,
        "description": experiment.description,
        "recipe_id": experiment.recipe_id,
        "status": experiment.status,
        "objectives": experiment.objectives,
        "factors": experiment.factors,
        "parameters": experiment.parameters,
        "results": experiment.results,
        "yield_value": experiment.yield_value,
        "defect_rate": experiment.defect_rate,
        "created_at": experiment.created_at.isoformat() if experiment.created_at else None
    }

@router.put("/experiments/{experiment_id}/results")
async def update_experiment_results(
    experiment_id: str, 
    results: Dict, 
    db: Session = Depends(get_db)
):
    """Update experiment results"""
    data_service = DataIntegrationService(db)
    
    success = data_service.update_experiment_results(experiment_id, results)
    if not success:
        raise HTTPException(status_code=404, detail="Experiment not found")
    
    return {
        "status": "success",
        "message": "Experiment results updated successfully"
    }

# === Sensor Data Management ===

@router.post("/sensor-data/batch")
async def ingest_sensor_data_batch(
    sensor_batch: SensorDataBatch, 
    db: Session = Depends(get_db)
):
    """Ingest batch sensor data"""
    data_service = DataIntegrationService(db)
    
    # Prepare sensor data with metadata
    sensor_data_list = []
    for data_point in sensor_batch.data:
        data_point['experiment_id'] = sensor_batch.experiment_id
        data_point['recipe_id'] = sensor_batch.recipe_id
        
        # Parse timestamp if string
        if 'timestamp' in data_point and isinstance(data_point['timestamp'], str):
            data_point['timestamp'] = datetime.fromisoformat(data_point['timestamp'])
        elif 'timestamp' not in data_point:
            data_point['timestamp'] = datetime.utcnow()
        
        sensor_data_list.append(data_point)
    
    success = data_service.ingest_sensor_data(sensor_data_list)
    if not success:
        raise HTTPException(status_code=500, detail="Failed to ingest sensor data")
    
    return {
        "status": "success",
        "message": f"Ingested {len(sensor_data_list)} sensor data points"
    }

@router.get("/sensor-data/{experiment_id}")
async def get_sensor_data(
    experiment_id: str,
    start_time: Optional[str] = None,
    end_time: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Get sensor data for experiment"""
    data_service = DataIntegrationService(db)
    
    # Parse time parameters
    start_dt = datetime.fromisoformat(start_time) if start_time else None
    end_dt = datetime.fromisoformat(end_time) if end_time else None
    
    sensor_data = data_service.get_sensor_data_for_experiment(
        experiment_id, start_dt, end_dt
    )
    
    return {
        "experiment_id": experiment_id,
        "data_points": len(sensor_data),
        "sensor_data": [
            {
                "timestamp": sd.timestamp.isoformat(),
                "temperature": sd.temperature,
                "pressure": sd.pressure,
                "gas_flow": sd.gas_flow,
                "power": sd.power,
                "quality_score": sd.quality_score
            }
            for sd in sensor_data
        ]
    }

# === Data Import/Export ===

@router.get("/export/{experiment_id}")
async def export_experiment_data(experiment_id: str, db: Session = Depends(get_db)):
    """Export complete experiment data"""
    data_service = DataIntegrationService(db)
    
    export_data = data_service.export_experiment_data(experiment_id)
    if not export_data:
        raise HTTPException(status_code=404, detail="Experiment not found")
    
    return {
        "status": "success",
        "experiment_id": experiment_id,
        "export_timestamp": datetime.utcnow().isoformat(),
        "data": export_data
    }

@router.post("/import")
async def import_experiment_data(
    import_data: Dict,
    db: Session = Depends(get_db)
):
    """Import experiment data"""
    data_service = DataIntegrationService(db)
    
    success = data_service.import_experiment_data(import_data)
    if not success:
        raise HTTPException(status_code=500, detail="Failed to import experiment data")
    
    return {
        "status": "success",
        "message": "Experiment data imported successfully"
    }

@router.post("/import/file")
async def import_from_file(
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    """Import experiment data from JSON file"""
    if not file.filename.endswith('.json'):
        raise HTTPException(status_code=400, detail="Only JSON files are supported")
    
    try:
        content = await file.read()
        import_data = json.loads(content)
        
        data_service = DataIntegrationService(db)
        success = data_service.import_experiment_data(import_data)
        
        if not success:
            raise HTTPException(status_code=500, detail="Failed to import data from file")
        
        return {
            "status": "success",
            "filename": file.filename,
            "message": "Data imported successfully from file"
        }
        
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Invalid JSON file")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Import failed: {str(e)}")

# === Analytics ===

@router.get("/analytics/experiments")
async def get_experiment_analytics(recipe_id: Optional[str] = None, db: Session = Depends(get_db)):
    """Get experiment analytics"""
    data_service = DataIntegrationService(db)
    
    stats = data_service.get_experiment_statistics(recipe_id)
    
    return {
        "recipe_id": recipe_id,
        "statistics": stats,
        "generated_at": datetime.utcnow().isoformat()
    }

@router.get("/analytics/models")
async def get_model_analytics(limit: int = 10, db: Session = Depends(get_db)):
    """Get model performance analytics"""
    data_service = DataIntegrationService(db)
    
    model_history = data_service.get_model_performance_history(limit)
    
    return {
        "model_count": len(model_history),
        "models": model_history,
        "generated_at": datetime.utcnow().isoformat()
    }

# === Health Check ===

@router.get("/health")
async def data_health_check(db: Session = Depends(get_db)):
    """Data service health check"""
    try:
        # Test database connection
        from ..models.experiment import Recipe
        recipe_count = db.query(Recipe).count()
        
        return {
            "status": "healthy",
            "database": "connected",
            "recipe_count": recipe_count,
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat()
        }