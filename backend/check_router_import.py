import sys
sys.path.insert(0, 'backend')

print("Step 1: Importing routers module...")

try:
    from src.presentation.http.routers.repairs import router as repairs_router
    print(f"Step 2: Repairs router imported: {repairs_router}")
    print(f"Routes: {len(repairs_router.routes)}")
    
    for route in repairs_router.routes:
        path = getattr(route, 'path', 'no path')
        print(f"  {path}")
        
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()
