import axios from 'axios';

const BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000/api/v1';

const api = axios.create({ baseURL: BASE_URL });

export const fetchPods = (namespace) =>
  api.get('/cluster/pods', { params: namespace ? { namespace } : {} }).then((r) => r.data);

export const fetchClusterStatus = () =>
  api.get('/cluster/status').then((r) => r.data);

export const diagnosePod = (podName, namespace = 'default') =>
  api.post(`/diagnose/${podName}`, { namespace }).then((r) => r.data);

export const scanYaml = (yamlContent, filename = 'manifest.yaml') =>
  api.post('/yaml/scan', { yaml_content: yamlContent, filename }).then((r) => r.data);

export const fetchDiagnoseHistory = () =>
  api.get('/diagnose/history').then((r) => r.data);

export default api;
