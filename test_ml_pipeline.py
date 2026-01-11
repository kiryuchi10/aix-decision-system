#!/usr/bin/env python3
"""
AiX Decision System - ML Pipeline Test Script
Tests the automated ML pipeline with model comparisons
"""

import asyncio
import requests
import json
import time
from datetime import datetime

BASE_URL = "http://localhost:8000"

def test_api_connection():
    """Test basic API connection"""
    print("🔍 Testing API connection...")
    try:
        response = requests.get(f"{BASE_URL}/health")
        if response.status_code == 200:
            print("✅ API connection successful")
            print(f"   Status: {response.json()}")
            return True
        else:
            print(f"❌ API connection failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ API connection error: {e}")
        return False

def test_available_models():
    """Test available models endpoint"""
    print("\n🤖 Testing available models...")
    try:
        response = requests.get(f"{BASE_URL}/api/v1/ml-pipeline/available-models")
        if response.status_code == 200:
            models = response.json()["models"]
            print(f"✅ Found {len(models)} available models:")
            for model in models:
                uncertainty = "🎯" if model["provides_uncertainty"] else "📊"
                print(f"   {uncertainty} {model['name']} ({model['type']})")
                print(f"      {model['description']}")
            return True
        else:
            print(f"❌ Failed to get models: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Error getting models: {e}")
        return False

def test_automated_pipeline():
    """Test the automated ML pipeline"""
    print("\n🚀 Testing automated ML pipeline...")
    
    # Start pipeline
    pipeline_request = {
        "experiment_id": "EXP-TEST-001",
        "min_models": 2,
        "max_models": 4
    }
    
    try:
        print("   Starting pipeline...")
        response = requests.post(
            f"{BASE_URL}/api/v1/ml-pipeline/run-automated-pipeline",
            json=pipeline_request
        )
        
        if response.status_code != 200:
            print(f"❌ Failed to start pipeline: {response.status_code}")
            print(f"   Response: {response.text}")
            return False
        
        result = response.json()
        pipeline_id = result["pipeline_id"]
        print(f"✅ Pipeline started: {pipeline_id}")
        
        # Monitor pipeline status
        print("   Monitoring pipeline progress...")
        max_wait = 300  # 5 minutes max
        start_time = time.time()
        
        while time.time() - start_time < max_wait:
            status_response = requests.get(
                f"{BASE_URL}/api/v1/ml-pipeline/pipeline-status/{pipeline_id}"
            )
            
            if status_response.status_code == 200:
                status_data = status_response.json()
                status = status_data["status"]
                progress = status_data.get("progress", 0)
                
                print(f"   Status: {status} ({progress}%)")
                
                if status == "completed":
                    print("✅ Pipeline completed successfully!")
                    return test_pipeline_results(pipeline_id)
                elif status == "failed":
                    error = status_data.get("error", "Unknown error")
                    print(f"❌ Pipeline failed: {error}")
                    return False
                
                time.sleep(5)  # Wait 5 seconds before next check
            else:
                print(f"❌ Failed to get status: {status_response.status_code}")
                return False
        
        print("❌ Pipeline timeout (5 minutes)")
        return False
        
    except Exception as e:
        print(f"❌ Pipeline test error: {e}")
        return False

def test_pipeline_results(pipeline_id):
    """Test pipeline results retrieval"""
    print(f"\n📊 Testing pipeline results for {pipeline_id}...")
    
    try:
        response = requests.get(
            f"{BASE_URL}/api/v1/ml-pipeline/pipeline-results/{pipeline_id}"
        )
        
        if response.status_code != 200:
            print(f"❌ Failed to get results: {response.status_code}")
            return False
        
        results = response.json()
        
        print("✅ Pipeline results retrieved:")
        print(f"   Experiment ID: {results['experiment_id']}")
        print(f"   Total combinations: {results['total_combinations']}")
        print(f"   Successful evaluations: {results['successful_evaluations']}")
        
        # Show top 3 combinations
        ranked_results = results["ranked_results"][:3]
        print(f"\n🏆 Top 3 Model Combinations:")
        
        for i, combo in enumerate(ranked_results, 1):
            print(f"   {i}. {' + '.join(combo['combination'])}")
            print(f"      Score: {combo['score']:.3f}")
            print(f"      R²: {combo['ensemble_r2']:.3f}")
            print(f"      MAE: {combo['ensemble_mae']:.2f}%")
            print(f"      Strategy: {combo['best_ensemble_strategy']}")
            print(f"      Uncertainty: {'Yes' if combo['has_uncertainty'] else 'No'}")
            print()
        
        # Test model selection
        return test_model_selection(pipeline_id)
        
    except Exception as e:
        print(f"❌ Results test error: {e}")
        return False

def test_model_selection(pipeline_id):
    """Test best model selection"""
    print(f"🎯 Testing model selection for {pipeline_id}...")
    
    try:
        response = requests.post(
            f"{BASE_URL}/api/v1/ml-pipeline/select-best-combination/{pipeline_id}"
        )
        
        if response.status_code != 200:
            print(f"❌ Failed to select model: {response.status_code}")
            return False
        
        result = response.json()
        
        print("✅ Best model selected:")
        print(f"   Model ID: {result['model_id']}")
        print(f"   Combination: {' + '.join(result['combination'])}")
        print(f"   Performance:")
        print(f"     R²: {result['performance']['r2']:.3f}")
        print(f"     MAE: {result['performance']['mae']:.2f}%")
        print(f"     RMSE: {result['performance']['rmse']:.2f}%")
        print(f"   Strategy: {result['ensemble_strategy']}")
        
        return True
        
    except Exception as e:
        print(f"❌ Model selection error: {e}")
        return False

def test_model_comparison():
    """Test model comparison endpoint"""
    print("\n📈 Testing model comparison...")
    
    try:
        response = requests.get(
            f"{BASE_URL}/api/v1/ml-pipeline/model-comparison/EXP-TEST-001"
        )
        
        if response.status_code == 200:
            comparison = response.json()
            print(f"✅ Model comparison retrieved:")
            print(f"   Experiment: {comparison['experiment_id']}")
            print(f"   Total comparisons: {comparison['total_comparisons']}")
            
            if comparison['comparisons']:
                print("   Top combinations:")
                for i, comp in enumerate(comparison['comparisons'][:3], 1):
                    print(f"     {i}. {' + '.join(comp['combination'])} (Score: {comp['score']:.3f})")
            
            return True
        else:
            print(f"❌ Model comparison failed: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Model comparison error: {e}")
        return False

def main():
    """Run all tests"""
    print("🧪 AiX Decision System - ML Pipeline Test Suite")
    print("=" * 60)
    
    tests = [
        ("API Connection", test_api_connection),
        ("Available Models", test_available_models),
        ("Automated Pipeline", test_automated_pipeline),
        ("Model Comparison", test_model_comparison),
    ]
    
    results = []
    
    for test_name, test_func in tests:
        print(f"\n{'='*20} {test_name} {'='*20}")
        try:
            success = test_func()
            results.append((test_name, success))
        except Exception as e:
            print(f"❌ {test_name} failed with exception: {e}")
            results.append((test_name, False))
    
    # Summary
    print(f"\n{'='*60}")
    print("📋 Test Summary:")
    print("=" * 60)
    
    passed = 0
    for test_name, success in results:
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"   {status} {test_name}")
        if success:
            passed += 1
    
    print(f"\nResults: {passed}/{len(results)} tests passed")
    
    if passed == len(results):
        print("🎉 All tests passed! ML Pipeline is working correctly.")
    else:
        print("⚠️  Some tests failed. Check the logs above.")
    
    return passed == len(results)

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)