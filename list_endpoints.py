#!/usr/bin/env python3
"""
Quick API endpoints listing for CommunityExpress
"""

import re
from pathlib import Path

def extract_routes_from_file(file_path):
    """Extract routes from a router file"""
    try:
        with open(file_path, 'r') as f:
            content = f.read()
        
        routes = []
        
        # Find router prefix
        prefix_match = re.search(r'router = APIRouter\(prefix="([^"]*)"', content)
        prefix = prefix_match.group(1) if prefix_match else ""
        
        # Find all route decorators
        route_pattern = r'@router\.(get|post|put|delete)\("([^"]*)"'
        matches = re.findall(route_pattern, content)
        
        for method, path in matches:
            full_path = f"{prefix}{path}" if path != "/" else prefix + "/"
            routes.append((method.upper(), full_path))
        
        return routes
    except Exception as e:
        print(f"Error reading {file_path}: {e}")
        return []

def main():
    """List all API endpoints"""
    router_dir = Path("/Users/harsha/CommunityExpress/backend/app/routers")
    
    print("🚀 CommunityExpress API Endpoints")
    print("=" * 50)
    
    all_routes = []
    
    for router_file in sorted(router_dir.glob("*.py")):
        if router_file.name == "__init__.py":
            continue
        
        routes = extract_routes_from_file(router_file)
        if routes:
            print(f"\n📁 {router_file.stem}.py:")
            for method, path in routes:
                print(f"  {method:<6} {path}")
                all_routes.append((method, path))
    
    print(f"\n📊 Summary: {len(all_routes)} total endpoints")
    
    # Group by method
    methods = {}
    for method, path in all_routes:
        if method not in methods:
            methods[method] = []
        methods[method].append(path)
    
    print(f"\nBy Method:")
    for method in sorted(methods.keys()):
        print(f"  {method}: {len(methods[method])} endpoints")

if __name__ == "__main__":
    main()
