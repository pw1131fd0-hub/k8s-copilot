from fastapi import FastAPI
import uvicorn

app = FastAPI(title='Lobster K8s Copilot API')

@app.get('/')
async def root():
    return {'message': 'Lobster K8s Copilot API is running'}

@app.get('/api/v1/cluster/status')
async def get_cluster_status():
    return {'status': 'connected', 'clusters': ['local-dev']}

if __name__ == '__main__':
    uvicorn.run(app, host='0.0.0.0', port=8000)
