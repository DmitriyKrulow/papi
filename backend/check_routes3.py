import sys
sys.path.insert(0, 'backend')

try:
    from src.infrastructure.main import app
    
    print(f"Total routes: {len(app.routes)}")
    
    for r in app.routes:
        path = getattr(r, 'path', 'no path')
        print(f"  {path}")
        
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()
