import axios from 'axios';

const BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000/api/v1';

const api = axios.create({ baseURL: BASE_URL, timeout: 30000 });

api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.data) {
      const data = error.response.data;
      const message =
        data.detail ||
        data.message ||
        data.error ||
        (typeof data === 'string' ? data : null) ||
        `Server error (${error.response.status})`;
      return Promise.reject(new Error(message));
    }
    if (error.request) {
      return Promise.reject(new Error('Cannot reach server. Check that the backend is running.'));
    }
    return Promise.reject(error);
  }
);

export const fetchPods = (namespace) =>
  api.get('/cluster/pods', { params: namespace ? { namespace } : {} }).then((r) => r.data);

export const fetchClusterStatus = () =>
  api.get('/cluster/status').then((r) => r.data);

export const diagnosePod = (podName, namespace = 'default') =>
  api.post(`/diagnose/${podName}`, { namespace }).then((r) => r.data);

export const scanYaml = (yamlContent, filename = 'manifest.yaml') =>
  api.post('/yaml/scan', { yaml_content: yamlContent, filename }).then((r) => r.data);

export const fetchDiagnoseHistory = (limit = 50) =>
  api.get('/diagnose/history', { params: { limit } }).then((r) => r.data);

export const fetchPodDiagnoseHistory = (podName) =>
  api.get(`/diagnose/history/${podName}`).then((r) => r.data);

export const diffYaml = (yamlA, yamlB) =>
  api.post('/yaml/diff', { yaml_a: yamlA, yaml_b: yamlB }).then((r) => r.data);

export default api;
