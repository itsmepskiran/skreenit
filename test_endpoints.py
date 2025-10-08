#!/usr/bin/env python3
"""
Quick test script to verify Skreenit backend endpoints
"""
import requests
import json

BASE_URL = "http://localhost:8000"

def test_health():
    """Test health endpoint"""
    try:
        response = requests.get(f"{BASE_URL}/health")
        print(f"✅ Health Check: {response.status_code} - {response.json()}")
        return True
    except Exception as e:
        print(f"❌ Health Check Failed: {e}")
        return False

def test_auth_endpoints():
    """Test authentication endpoints"""
    endpoints = [
        "/auth/register",
        "/auth/login", 
        "/auth/password-updated"
    ]
    
    for endpoint in endpoints:
        try:
            # Test OPTIONS request (CORS preflight)
            response = requests.options(f"{BASE_URL}{endpoint}")
            print(f"✅ CORS {endpoint}: {response.status_code}")
        except Exception as e:
            print(f"❌ CORS {endpoint} Failed: {e}")

def test_other_endpoints():
    """Test other router endpoints"""
    routers = [
        "/applicant",
        "/recruiter", 
        "/dashboard",
        "/analytics",
        "/notification",
        "/video"
    ]
    
    for router in routers:
        try:
            # Test OPTIONS request (CORS preflight)
            response = requests.options(f"{BASE_URL}{router}/")
            print(f"✅ Router {router}: {response.status_code}")
        except Exception as e:
            print(f"❌ Router {router} Failed: {e}")

def main():
    print("🚀 Testing Skreenit Backend Endpoints\n")
    
    # Test health first
    if not test_health():
        print("❌ Backend is not running. Please start the backend server first.")
        return
    
    print("\n📡 Testing CORS Configuration...")
    test_auth_endpoints()
    
    print("\n🔗 Testing Router Endpoints...")
    test_other_endpoints()
    
    print("\n✅ Backend testing completed!")
    print("\n📋 Next Steps:")
    print("1. Test frontend by visiting http://localhost:3000")
    print("2. Try registration flow at http://localhost:3000/auth/registration.html")
    print("3. Test login at http://localhost:3000/login/login.html")

if __name__ == "__main__":
    main()
