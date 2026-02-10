# Design Document

## Overview

The AiX Decision System is designed as a microservices-based architecture that integrates FDC (Fault Detection and Classification) Drift Sentinel with Adaptive DoE (Design of Experiments) Planner. The system employs a modern tech stack with FastAPI backend, React frontend, and sophisticated ML pipeline automation to provide real-time process monitoring and intelligent decision-making capabilities.

## Architecture

### High-Level Architecture

```mermaid
graph TB
    subgraph "Frontend Layer"
        UI[React Dashboard]
        WS[WebSocket Client]
    end
    
    subgraph "API Gateway"
        GW[FastAPI Gateway]
    end
    
    subgraph "Core Services"
        FDC[FDC Service]
        DOE[DoE Service]
        ML[ML Pipeline Service]
        REC[Recommendation Engine]
        COUP[Coupling Service]
    end
    
    subgraph "Data Layer"
        MYSQL[(MySQL)]
        REDIS[(Redis Cache)]
        TSDB[(InfluxDB)]
    end
    
    subgraph "External Systems"
        SENSORS[Manufacturing Sensors]
        MES[MES System]
    end
    
    UI --> GW
    WS --> GW
    GW --> FDC
    GW --> DOE
    GW --> ML
    GW --> REC
    GW --> COUP
    
    FDC --> MYSQL
    FDC --> REDIS
    FDC --> TSDB
    DOE --> MYSQL
    ML --> MYSQL
    REC --> REDIS
    COUP --> MYSQL
    
    SENSORS --> FDC
    MES --> DOE
```

### System Components

#### 1. Frontend Architecture (React + TypeScript)

**Component Hierarchy:**
```
App
├── Dashboard
│   ├── KPICards
│   ├── SensorMonitoring
│   ├── ActiveAlarms
│   ├── AIRecommendations
│   └── DoEStatus
├── MLPipeline
│   ├── ModelComparison
│   ├── EnsembleConfiguration
│   └── PipelineStatus
└── SystemSettings
    ├── ProcessWindows
    ├── AlarmThresholds
    └── UserManagement
```

**State Management:**
- Redux Toolkit for global state management
- React Query for server state and caching
- WebSocket integration for real-time updates

**Real-time Communication:**
- WebSocket connection for live sensor data
- Server-Sent Events for system notifications
- Automatic reconnection and error handling

#### 2. Backend Architecture (FastAPI)

**Service Layer Design:**

```python
# Core service interfaces
class FDCService:
    - detect_drift(sensor_data: SensorData) -> DriftDetection
    - classify_anomaly(drift: DriftDetection) -> AlarmType
    - calculate_process_capability(data: List[float]) -> ProcessCapability
    
class DoEService:
    - generate_experiment_plan(objectives: List[str]) -> ExperimentPlan
    - update_surrogate_model(results: ExperimentResults) -> ModelUpdate
    - recommend_next_experiments(n: int) -> List[Experiment]
    
class MLPipelineService:
    - train_model_combinations() -> List[ModelResult]
    - create_ensemble(models: List[Model]) -> EnsembleModel
    - evaluate_performance(model: Model, data: TestData) -> Metrics
    
class RecommendationEngine:
    - generate_recovery_action(alarm: Alarm) -> RecoveryRecommendation
    - suggest_validation_experiments(uncertainty: float) -> List[Experiment]
    - assess_risk(recommendation: Recommendation) -> RiskAssessment
    
class CouplingService:
    - coordinate_fdc_doe(fdc_result: FDCResult) -> CouplingAction
    - execute_closed_loop_action(action: CouplingAction) -> ExecutionResult
    - manage_approval_workflow(recommendation: Recommendation) -> ApprovalStatus
```

**API Router Structure:**
```
/api/v1/
├── /fdc/
│   ├── /sensors/data
│   ├── /alarms/active
│   ├── /drift/detection
│   └── /process/capability
├── /doe/
│   ├── /experiments/active
│   ├── /experiments/plan
│   ├── /models/surrogate
│   └── /recommendations/next
├── /ml/
│   ├── /pipeline/status
│   ├── /models/comparison
│   ├── /ensemble/create
│   └── /performance/metrics
├── /recommendations/
│   ├── /recovery/actions
│   ├── /validation/experiments
│   └── /risk/assessment
└── /coupling/
    ├── /status
    ├── /actions/execute
    └── /approvals/workflow
```

## Components and Interfaces

### 1. Data Models

**Core Entities:**

```python
# Sensor Data Model
class SensorReading(BaseModel):
    sensor_id: str
    timestamp: datetime
    temperature: float
    pressure: float
    gas_flow: float
    power: float
    recipe_id: str

# Alarm Model
class Alarm(BaseModel):
    id: str
    timestamp: datetime
    severity: AlarmSeverity
    type: AlarmType  # GRADUAL_DRIFT, STEP_CHANGE, INTERMITTENT
    parameter: str
    current_value: float
    threshold_value: float
    sigma_distance: float
    yield_impact: float
    status: AlarmStatus

# Experiment Model
class Experiment(BaseModel):
    id: str
    parameters: Dict[str, float]
    objectives: List[str]
    status: ExperimentStatus
    results: Optional[ExperimentResults]
    information_gain: float
    estimated_duration: timedelta

# Recommendation Model
class Recommendation(BaseModel):
    id: str
    type: RecommendationType
    priority: Priority
    confidence: float
    expected_improvement: float
    risk_level: RiskLevel
    requires_approval: bool
    parameters: Dict[str, Any]
```

### 2. ML Pipeline Components

**Model Registry:**
```python
class ModelRegistry:
    algorithms = {
        'random_forest': RandomForestRegressor,
        'svm': SVR,
        'neural_network': MLPRegressor,
        'xgboost': XGBRegressor,
        'gradient_boosting': GradientBoostingRegressor
    }
    
    ensemble_methods = {
        'voting': VotingRegressor,
        'stacking': StackingRegressor,
        'blending': BlendingEnsemble
    }
```

**Pipeline Configuration:**
```python
class MLPipelineConfig:
    cross_validation_folds: int = 5
    test_size: float = 0.2
    random_state: int = 42
    
    hyperparameter_grids = {
        'random_forest': {
            'n_estimators': [100, 200, 300],
            'max_depth': [10, 20, None],
            'min_samples_split': [2, 5, 10]
        },
        # ... other algorithms
    }
    
    evaluation_metrics = [
        'mean_squared_error',
        'mean_absolute_error',
        'r2_score',
        'explained_variance_score'
    ]
```

### 3. Real-time Data Processing

**Stream Processing Architecture:**
```python
class StreamProcessor:
    def __init__(self):
        self.redis_client = Redis()
        self.websocket_manager = WebSocketManager()
        
    async def process_sensor_stream(self, sensor_data: SensorReading):
        # 1. Store in time-series database
        await self.store_sensor_data(sensor_data)
        
        # 2. Run FDC analysis
        drift_result = await self.fdc_service.detect_drift(sensor_data)
        
        # 3. Update real-time cache
        await self.update_realtime_cache(sensor_data)
        
        # 4. Broadcast to connected clients
        await self.websocket_manager.broadcast(sensor_data)
        
        # 5. Trigger coupling if anomaly detected
        if drift_result.is_anomaly:
            await self.coupling_service.handle_anomaly(drift_result)
```

## Data Models

### Database Schema Design

**MySQL Tables:**

```sql
-- Recipes and Process Windows
CREATE TABLE recipes (
    id VARCHAR(50) PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    temperature_min DECIMAL(8,2),
    temperature_max DECIMAL(8,2),
    temperature_optimal DECIMAL(8,2),
    pressure_min DECIMAL(8,2),
    pressure_max DECIMAL(8,2),
    pressure_optimal DECIMAL(8,2),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Experiments
CREATE TABLE experiments (
    id VARCHAR(50) PRIMARY KEY,
    recipe_id VARCHAR(50),
    status ENUM('PLANNED', 'RUNNING', 'COMPLETED', 'FAILED'),
    parameters JSON,
    objectives JSON,
    results JSON,
    information_gain DECIMAL(10,6),
    estimated_duration INT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (recipe_id) REFERENCES recipes(id)
);

-- Alarms
CREATE TABLE alarms (
    id VARCHAR(50) PRIMARY KEY,
    sensor_id VARCHAR(50),
    severity ENUM('LOW', 'MEDIUM', 'HIGH'),
    type ENUM('GRADUAL_DRIFT', 'STEP_CHANGE', 'INTERMITTENT'),
    parameter VARCHAR(50),
    current_value DECIMAL(12,6),
    threshold_value DECIMAL(12,6),
    sigma_distance DECIMAL(8,4),
    yield_impact DECIMAL(8,4),
    status ENUM('ACTIVE', 'ACKNOWLEDGED', 'RESOLVED'),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ML Models
CREATE TABLE ml_models (
    id VARCHAR(50) PRIMARY KEY,
    name VARCHAR(100),
    algorithm VARCHAR(50),
    hyperparameters JSON,
    performance_metrics JSON,
    is_ensemble BOOLEAN DEFAULT FALSE,
    ensemble_config JSON,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Recommendations
CREATE TABLE recommendations (
    id VARCHAR(50) PRIMARY KEY,
    type ENUM('RECOVERY_ACTION', 'VALIDATION_EXPERIMENT'),
    priority ENUM('LOW', 'MEDIUM', 'HIGH', 'URGENT'),
    confidence DECIMAL(4,3),
    expected_improvement DECIMAL(8,4),
    risk_level ENUM('LOW', 'MEDIUM', 'HIGH'),
    requires_approval BOOLEAN,
    parameters JSON,
    status ENUM('PENDING', 'APPROVED', 'REJECTED', 'EXECUTED'),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

**InfluxDB Schema (Time-series data):**

```sql
-- Sensor measurements
CREATE MEASUREMENT sensor_data (
    time TIMESTAMP,
    sensor_id TAG,
    recipe_id TAG,
    temperature FIELD,
    pressure FIELD,
    gas_flow FIELD,
    power FIELD
);

-- Process capability metrics
CREATE MEASUREMENT process_metrics (
    time TIMESTAMP,
    recipe_id TAG,
    cpk FIELD,
    cp FIELD,
    drift_rate FIELD,
    yield_estimate FIELD
);
```

## Error Handling

### Error Classification and Response Strategy

```python
class ErrorHandler:
    error_categories = {
        'sensor_communication': {
            'retry_attempts': 3,
            'fallback_strategy': 'use_cached_data',
            'alert_threshold': 5
        },
        'model_prediction': {
            'retry_attempts': 1,
            'fallback_strategy': 'use_baseline_model',
            'alert_threshold': 1
        },
        'database_connection': {
            'retry_attempts': 5,
            'fallback_strategy': 'queue_operations',
            'alert_threshold': 3
        }
    }
    
    async def handle_error(self, error: Exception, context: str):
        error_type = self.classify_error(error)
        strategy = self.error_categories.get(error_type)
        
        if strategy:
            await self.execute_fallback_strategy(strategy, context)
            await self.log_error_with_context(error, context)
            
        if self.should_alert(error_type):
            await self.send_alert(error, context)
```

### Graceful Degradation

```python
class GracefulDegradation:
    service_priorities = {
        'sensor_monitoring': 1,  # Critical
        'alarm_generation': 1,   # Critical
        'recommendations': 2,   # Important
        'ml_pipeline': 3,        # Nice to have
        'historical_analysis': 4 # Optional
    }
    
    async def handle_resource_constraint(self, available_resources: float):
        if available_resources < 0.5:
            await self.disable_services_by_priority(threshold=3)
        elif available_resources < 0.7:
            await self.reduce_service_frequency(services=['ml_pipeline'])
```

## Testing Strategy

### Testing Pyramid

**Unit Tests (70%):**
- Individual service methods
- Data model validation
- Utility functions
- ML algorithm components

**Integration Tests (20%):**
- API endpoint testing
- Database operations
- Service-to-service communication
- WebSocket connections

**End-to-End Tests (10%):**
- Complete user workflows
- Real-time data processing
- ML pipeline execution
- System performance under load

### Test Implementation

```python
# Example unit test
class TestFDCService:
    def test_drift_detection_gradual(self):
        service = FDCService()
        sensor_data = generate_gradual_drift_data()
        result = service.detect_drift(sensor_data)
        assert result.type == AlarmType.GRADUAL_DRIFT
        assert result.confidence > 0.8

# Example integration test
class TestAPIIntegration:
    async def test_sensor_data_to_alarm_workflow(self):
        # Send sensor data
        response = await client.post("/api/v1/fdc/sensors/data", json=sensor_data)
        assert response.status_code == 200
        
        # Check alarm generation
        alarms = await client.get("/api/v1/fdc/alarms/active")
        assert len(alarms.json()) > 0

# Example E2E test
class TestSystemWorkflow:
    async def test_complete_anomaly_detection_and_recommendation(self):
        # Simulate sensor anomaly
        await simulate_sensor_anomaly()
        
        # Verify alarm generation
        await verify_alarm_created()
        
        # Verify recommendation generation
        await verify_recommendation_created()
        
        # Verify coupling action
        await verify_coupling_triggered()
```

### Performance Testing

```python
class PerformanceTests:
    async def test_sensor_data_throughput(self):
        # Test 1000 data points per second
        start_time = time.time()
        await send_concurrent_sensor_data(count=10000)
        duration = time.time() - start_time
        assert duration < 10  # Should process 10k points in under 10 seconds
    
    async def test_concurrent_user_load(self):
        # Test 50 concurrent dashboard users
        tasks = [simulate_user_session() for _ in range(50)]
        results = await asyncio.gather(*tasks)
        assert all(result.response_time < 2.0 for result in results)
```

## Deployment Architecture

### Container Strategy

```dockerfile
# Backend Dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]

# Frontend Dockerfile
FROM node:18-alpine AS builder
WORKDIR /app
COPY package*.json ./
RUN npm ci
COPY . .
RUN npm run build

FROM nginx:alpine
COPY --from=builder /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/nginx.conf
EXPOSE 80
```

### Docker Compose Configuration

```yaml
version: '3.8'
services:
  backend:
    build: ./backend
    environment:
      - DATABASE_URL=mysql://user:pass@mysql:3306/aixdb
      - REDIS_URL=redis://redis:6379
      - INFLUXDB_URL=http://influxdb:8086
    depends_on:
      - mysql
      - redis
      - influxdb
    
  frontend:
    build: ./frontend
    ports:
      - "80:80"
    depends_on:
      - backend
    
  mysql:
    image: mysql:8.0
    environment:
      MYSQL_ROOT_PASSWORD: rootpass
      MYSQL_DATABASE: aixdb
    volumes:
      - mysql_data:/var/lib/mysql
    
  redis:
    image: redis:7-alpine
    volumes:
      - redis_data:/data
    
  influxdb:
    image: influxdb:2.0
    environment:
      INFLUXDB_DB: sensor_data
    volumes:
      - influx_data:/var/lib/influxdb2

volumes:
  mysql_data:
  redis_data:
  influx_data:
```

### Kubernetes Deployment (Production)

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: aix-backend
spec:
  replicas: 3
  selector:
    matchLabels:
      app: aix-backend
  template:
    metadata:
      labels:
        app: aix-backend
    spec:
      containers:
      - name: backend
        image: aix-decision-system/backend:latest
        ports:
        - containerPort: 8000
        env:
        - name: DATABASE_URL
          valueFrom:
            secretKeyRef:
              name: aix-secrets
              key: database-url
        resources:
          requests:
            memory: "512Mi"
            cpu: "250m"
          limits:
            memory: "1Gi"
            cpu: "500m"
        livenessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /ready
            port: 8000
          initialDelaySeconds: 5
          periodSeconds: 5
```

This comprehensive design provides a robust foundation for implementing the AiX Decision System with all the required features including real-time monitoring, AI recommendations, ML pipeline automation, and seamless FDC-DoE integration.
