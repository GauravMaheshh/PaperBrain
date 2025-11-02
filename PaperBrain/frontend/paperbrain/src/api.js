const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:5000';

export async function apiUpload(answerKeys, answerSheets, relatedDocs = []) {
  const formData = new FormData();
  
  // Add answer keys
  answerKeys.forEach(file => {
    formData.append('answer_key[]', file);
  });
  
  // Add answer sheets (can be single file or array)
  const sheets = Array.isArray(answerSheets) ? answerSheets : [answerSheets];
  sheets.forEach(file => {
    if (file) {
      formData.append('answer_sheet[]', file);
    }
  });
  
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

export async function apiSaveStudentInfo(studentInfo) {
  const resp = await fetch(`${API_BASE}/api/student-info`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ student_info: studentInfo })
  });
  const data = await resp.json().catch(() => ({}));
  if (!resp.ok) throw new Error(data.error || `Save failed (${resp.status})`);
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

export async function apiGetQuestionsForReference() {
  const resp = await fetch(`${API_BASE}/api/reference-answers/questions`);
  const data = await resp.json().catch(() => ({}));
  if (!resp.ok) throw new Error(data.error || `Failed to get questions (${resp.status})`);
  return data;
}

export async function apiGetReferenceAnswers() {
  const resp = await fetch(`${API_BASE}/api/reference-answers`);
  const data = await resp.json().catch(() => ({}));
  if (!resp.ok) throw new Error(data.error || `Failed to get reference answers (${resp.status})`);
  return data;
}

export async function apiUpdateReferenceAnswers(answers) {
  const resp = await fetch(`${API_BASE}/api/reference-answers/update`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ answers })
  });
  const data = await resp.json().catch(() => ({}));
  if (!resp.ok) throw new Error(data.error || `Update failed (${resp.status})`);
  return data;
}

export async function apiCloseSession() {
  try {
    const resp = await fetch(`${API_BASE}/api/session/close`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' }
    });
    const data = await resp.json().catch(() => ({}));
    if (!resp.ok) throw new Error(data.error || `Session close failed (${resp.status})`);
    return data;
  } catch (err) {
    // Silently fail on cleanup to avoid blocking page navigation
    console.log('Session cleanup failed (non-critical):', err.message);
    return { status: 'error', message: err.message };
  }
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