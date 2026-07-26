import sys
sys.path.insert(0, 'backend')

try:
    from fastapi import FastAPI
    
    app = FastAPI(title="PAPI Backend")
    
    from src.presentation.http.routers.repairs import router as repairs_router
    
    print(f"Repairs router: {repairs_router}")
    print(f"Repairs router prefix: {repairs_router.prefix}")
    print(f"Repairs router routes: {len(repairs_router.routes)}")
    
    app.include_router(repairs_router, prefix="/api")
    
    print(f"\nTotal routes in app: {len(app.routes)}")
    
    for r in app.routes:
        path = getattr(r, 'path', 'no path')
        if 'repair' in str(path).lower():
            print(f"  {path}")
        
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()
