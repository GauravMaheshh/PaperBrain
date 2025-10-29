const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:5000';

export async function apiUpload(answerKeys, answerSheet, relatedDocs = []) {
  const formData = new FormData();
  
  // Add answer keys
  answerKeys.forEach(file => {
    formData.append('answer_key[]', file);
  });
  
  // Add answer sheet
  formData.append('answer_sheet', answerSheet);
  
  // Add related docs (optional)
  relatedDocs.forEach(file => {
    formData.append('related_docs[]', file);
  });

  const resp = await fetch(`${API_BASE}/api/upload`, {
    method: 'POST',
    body: formData
  });
  
  const data = await resp.json().catch(() => ({}));
  if (!resp.ok) throw new Error(data.error || `Upload failed (${resp.status})`);
  return data;
}

export async function apiRunPipeline() {
  const resp = await fetch(`${API_BASE}/api/run`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({})
  });
  
  const data = await resp.json().catch(() => ({}));
  if (!resp.ok) throw new Error(data.error || `Pipeline failed (${resp.status})`);
  return data;
}

export async function apiCurrentStudent() {
  const resp = await fetch(`${API_BASE}/api/results/current-student`);
  const data = await resp.json().catch(() => ({}));
  if (!resp.ok) throw new Error(data.error || `Not found (${resp.status})`);
  return data;
}

export async function apiOutputsList() {
  const resp = await fetch(`${API_BASE}/api/outputs/list`);
  const data = await resp.json().catch(() => ({}));
  if (!resp.ok) throw new Error(`Failed to load outputs (${resp.status})`);
  return data;
}

export async function apiEvaluationResults() {
  const resp = await fetch(`${API_BASE}/api/results/evaluation`);
  const data = await resp.json().catch(() => ({}));
  if (!resp.ok) throw new Error(data.error || `Not found (${resp.status})`);
  return data;
}

export async function apiAllStudentsResults() {
  const resp = await fetch(`${API_BASE}/api/results/all-students`);
  const data = await resp.json().catch(() => ({}));
  if (!resp.ok) throw new Error(data.error || `Not found (${resp.status})`);
  return data;
}

export function getImageUrl(type, filename) {
  const paths = {
    preprocessor: `/api/outputs/preprocessor/${filename}`,
    'text-recognition': `/api/outputs/text-recognition/${filename}`,
    'region-selector': `/api/outputs/region-selector/${filename}`,
    visualizations: `/api/outputs/visualizations/${filename}`
  };
  return `${API_BASE}${paths[type] || ''}`;
}

export { API_BASE };