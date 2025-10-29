import { useState, useEffect } from 'react';
import { apiUpload, apiRunPipeline, apiOutputsList, apiCurrentStudent } from '../api';
import ImageGrid from '../components/ImageGrid';
import UploadPanel from '../components/UploadPanel';
import PipelineOutputs from '../components/PipelineOutputs';

// DotGrid Component
function DotGrid({ 
  dotSize = 3, 
  gap = 40, 
  baseColor = '#5227FF', 
  activeColor = '#5227FF'
}) {
  return (
    <div style={{
      position: 'fixed',
      inset: 0,
      zIndex: 0,
      pointerEvents: 'none',
      backgroundImage: `radial-gradient(circle, ${baseColor} 1px, transparent 1px)`,
      backgroundSize: `${gap}px ${gap}px`,
      opacity: 0.3
    }} />
  );
}

export default function Dashboard() {
  const [answerKeys, setAnswerKeys] = useState([]);
  const [answerSheet, setAnswerSheet] = useState(null);
  const [relatedDocs, setRelatedDocs] = useState([]);
  const [uploading, setUploading] = useState(false);
  const [running, setRunning] = useState(false);
  const [message, setMessage] = useState('');
  const [messageType, setMessageType] = useState('info');
  const [uploaded, setUploaded] = useState(false);
  const [pipelineOutputs, setPipelineOutputs] = useState(null);
  const [studentResults, setStudentResults] = useState(null);
  const [showResults, setShowResults] = useState(false);
  const [uploadProgress, setUploadProgress] = useState(0);

  // Load upload status and files from sessionStorage on mount
  useEffect(() => {
    const isUploaded = sessionStorage.getItem('uploaded') === 'true';
    setUploaded(isUploaded);
    
    // Load persisted files from sessionStorage if they exist
    try {
      const savedAnswerKeys = sessionStorage.getItem('answerKeys');
      const savedAnswerSheet = sessionStorage.getItem('answerSheet');
      const savedRelatedDocs = sessionStorage.getItem('relatedDocs');
      
      if (savedAnswerKeys) {
        const files = JSON.parse(savedAnswerKeys);
        // Create File objects from the saved data
        const fileObjects = files.map(f => new File([], f.name, { type: f.type }));
        setAnswerKeys(fileObjects);
      }
      
      if (savedAnswerSheet) {
        const file = JSON.parse(savedAnswerSheet);
        setAnswerSheet(new File([], file.name, { type: file.type }));
      }
      
      if (savedRelatedDocs) {
        const files = JSON.parse(savedRelatedDocs);
        const fileObjects = files.map(f => new File([], f.name, { type: f.type }));
        setRelatedDocs(fileObjects);
      }
    } catch (e) {
      console.error('Error loading saved files:', e);
    }
  }, []);

  const showMessage = (msg, type = 'info') => {
    setMessage(msg);
    setMessageType(type);
    setTimeout(() => setMessage(''), 5000);
  };

  const getMessageStyle = () => {
    const baseStyle = {
      padding: '1rem 1.5rem',
      borderRadius: '12px',
      marginBottom: '2rem',
      fontWeight: 500,
      display: message ? 'block' : 'none'
    };
    
    switch(messageType) {
      case 'success':
        return { ...baseStyle, backgroundColor: 'rgba(16, 185, 129, 0.2)', border: '1px solid rgba(16, 185, 129, 0.4)', color: '#10b981' };
      case 'error':
        return { ...baseStyle, backgroundColor: 'rgba(239, 68, 68, 0.2)', border: '1px solid rgba(239, 68, 68, 0.4)', color: '#ef4444' };
      case 'warning':
        return { ...baseStyle, backgroundColor: 'rgba(251, 191, 36, 0.2)', border: '1px solid rgba(251, 191, 36, 0.4)', color: '#fbbf24' };
      default:
        return { ...baseStyle, backgroundColor: 'rgba(59, 130, 246, 0.2)', border: '1px solid rgba(59, 130, 246, 0.4)', color: '#3b82f6' };
    }
  };

  // Save files to sessionStorage whenever they change
  useEffect(() => {
    if (answerKeys.length > 0) {
      sessionStorage.setItem('answerKeys', JSON.stringify(answerKeys.map(f => ({ name: f.name, type: f.type }))));
    }
  }, [answerKeys]);
  
  useEffect(() => {
    if (answerSheet) {
      sessionStorage.setItem('answerSheet', JSON.stringify({ name: answerSheet.name, type: answerSheet.type }));
    }
  }, [answerSheet]);
  
  useEffect(() => {
    if (relatedDocs.length > 0) {
      sessionStorage.setItem('relatedDocs', JSON.stringify(relatedDocs.map(f => ({ name: f.name, type: f.type }))));
    }
  }, [relatedDocs]);

  async function handleUpload() {
    if (answerKeys.length === 0 || !answerSheet) {
      showMessage('Please upload answer keys and answer sheet', 'warning');
      return;
    }

    setUploading(true);
    setMessage('');
    setUploadProgress(0);
    
    try {
      setUploadProgress(50);
      const response = await apiUpload(answerKeys, answerSheet, relatedDocs);
      setUploadProgress(100);
      setUploaded(true);
      sessionStorage.setItem('uploaded', 'true');
      showMessage(`✅ Files uploaded successfully! ${answerKeys.length} answer key(s), 1 answer sheet, ${relatedDocs.length} related doc(s)`, 'success');
      
      // Clear progress after 1 second
      setTimeout(() => setUploadProgress(0), 1000);
    } catch (err) {
      setUploadProgress(0);
      showMessage(`❌ Upload failed: ${err.message}`, 'error');
    } finally {
      setUploading(false);
    }
  }

  async function handleRunPipeline() {
    if (!uploaded) {
      showMessage('Please upload files first', 'warning');
      return;
    }

    setRunning(true);
    setMessage('🔄 Starting pipeline...');
    setShowResults(false);
    
    try {
      // Run the pipeline
      setMessage('🔄 Running preprocessor...');
      await apiRunPipeline();
      setMessage('✅ Pipeline completed! Fetching results...');
      
      // Get the outputs
      try {
        const outputs = await apiOutputsList();
        setPipelineOutputs(outputs);
      } catch (e) {
        console.error('Could not fetch outputs:', e);
      }
      
      // Get current student results
      try {
        const student = await apiCurrentStudent();
        setStudentResults(student);
      } catch (e) {
        console.error('Could not fetch student results:', e);
      }
      
      setShowResults(true);
      showMessage('✅ Pipeline completed successfully! Check the results below.', 'success');
    } catch (err) {
      showMessage(`❌ Pipeline failed: ${err.message}`, 'error');
    } finally {
      setRunning(false);
    }
  }

  return (
    <div style={{
      minHeight: '100vh',
      backgroundColor: '#000000',
      color: 'white',
      fontFamily: '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif',
      position: 'relative'
    }}>
      <DotGrid />
      
      {/* Navigation */}
      <nav style={{
        position: 'fixed',
        top: '2rem',
        left: '50%',
        transform: 'translateX(-50%)',
        zIndex: 1000,
        display: 'flex',
        alignItems: 'center',
        gap: '2rem',
        padding: '0.75rem 2rem',
        backgroundColor: 'rgba(17, 24, 39, 0.8)',
        backdropFilter: 'blur(10px)',
        borderRadius: '100px',
        border: '1px solid rgba(255, 255, 255, 0.1)'
      }}>
        <div style={{
          display: 'flex',
          alignItems: 'center',
          gap: '0.5rem',
          fontSize: '1.25rem',
          fontWeight: 600
        }}>
          <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/>
            <polyline points="14 2 14 8 20 8"/>
            <line x1="16" y1="13" x2="8" y2="13"/>
            <line x1="16" y1="17" x2="8" y2="17"/>
            <polyline points="10 9 9 9 8 9"/>
          </svg>
          PaperBrain
        </div>
        <div style={{ display: 'flex', gap: '1.5rem', fontSize: '0.95rem' }}>
          <a href="/" style={{ color: 'white', textDecoration: 'none', opacity: 0.9 }}>Home</a>
          <a href="/dashboard" style={{ color: 'white', textDecoration: 'none', opacity: 1, fontWeight: 600 }}>Dashboard</a>
          <a href="/outputs" style={{ color: 'white', textDecoration: 'none', opacity: 0.9 }}>Outputs</a>
          <a href="/student" style={{ color: 'white', textDecoration: 'none', opacity: 0.9 }}>Student</a>
        </div>
      </nav>

      {/* Main Content */}
      <div style={{
        position: 'relative',
        zIndex: 1,
        padding: '8rem 2rem 4rem',
        maxWidth: '1400px',
        margin: '0 auto'
      }}>
        <h1 style={{
          fontSize: '2.5rem',
          marginBottom: '0.5rem',
          fontWeight: 700
        }}>Dashboard</h1>
        <p style={{
          fontSize: '1.1rem',
          color: 'rgba(255, 255, 255, 0.6)',
          marginBottom: '3rem'
        }}>Upload and process exam papers with AI-powered evaluation</p>

        {/* Message Display */}
        <div style={getMessageStyle()}>{message}</div>

        {/* Demo sections */}
        <div style={{
          display: 'grid',
          gap: '2rem'
        }}>
          {/* Answer Keys Section */}
          <section style={{
            padding: '2rem',
            backgroundColor: 'rgba(17, 24, 39, 0.6)',
            backdropFilter: 'blur(10px)',
            border: '1px solid rgba(255, 255, 255, 0.1)',
            borderRadius: '16px'
          }}>
            <h2 style={{ fontSize: '1.5rem', marginBottom: '1rem', fontWeight: 600 }}>Answer Keys (Required)</h2>
            <p style={{ color: 'rgba(255, 255, 255, 0.6)', marginBottom: '1.5rem', fontSize: '0.95rem' }}>
              Upload the answer key images for evaluation
            </p>
            <UploadPanel
              label="Choose Answer Keys"
              accept="image/*"
              multiple={true}
              onChange={setAnswerKeys}
            />
            {answerKeys.length > 0 && (
              <ImageGrid 
                images={answerKeys} 
                onRemove={(idx) => setAnswerKeys(answerKeys.filter((_, i) => i !== idx))}
              />
            )}
          </section>

          {/* Answer Sheet Section */}
          <section style={{
            padding: '2rem',
            backgroundColor: 'rgba(17, 24, 39, 0.6)',
            backdropFilter: 'blur(10px)',
            border: '1px solid rgba(255, 255, 255, 0.1)',
            borderRadius: '16px'
          }}>
            <h2 style={{ fontSize: '1.5rem', marginBottom: '1rem', fontWeight: 600 }}>Answer Sheet (Required)</h2>
            <p style={{ color: 'rgba(255, 255, 255, 0.6)', marginBottom: '1.5rem', fontSize: '0.95rem' }}>
              Upload the student's answer sheet for processing
            </p>
            <UploadPanel
              label="Choose Answer Sheet"
              accept="image/*"
              multiple={false}
              onChange={(files) => setAnswerSheet(files[0])}
            />
            {answerSheet && (
              <ImageGrid 
                images={[answerSheet]} 
                onRemove={() => setAnswerSheet(null)}
              />
            )}
          </section>

          {/* Related Documents Section */}
          <section style={{
            padding: '2rem',
            backgroundColor: 'rgba(17, 24, 39, 0.6)',
            backdropFilter: 'blur(10px)',
            border: '1px solid rgba(255, 255, 255, 0.1)',
            borderRadius: '16px'
          }}>
            <h2 style={{ fontSize: '1.5rem', marginBottom: '1rem', fontWeight: 600 }}>Related Documents (Optional)</h2>
            <p style={{ color: 'rgba(255, 255, 255, 0.6)', marginBottom: '1.5rem', fontSize: '0.95rem' }}>
              Add any additional reference materials or context documents
            </p>
            <UploadPanel
              label="Choose Related Docs"
              accept="image/*,.txt,.pdf,.doc,.docx"
              multiple={true}
              onChange={setRelatedDocs}
            />
            {relatedDocs.length > 0 && (
              <ImageGrid 
                images={relatedDocs} 
                onRemove={(idx) => setRelatedDocs(relatedDocs.filter((_, i) => i !== idx))}
              />
            )}
          </section>

          {/* Action Buttons */}
          <div style={{
            display: 'flex',
            gap: '1rem',
            flexWrap: 'wrap',
            marginTop: '1rem'
          }}>
            <button 
              onClick={handleUpload}
              disabled={uploading || answerKeys.length === 0 || !answerSheet}
              style={{
                padding: '1rem 2.5rem',
                fontSize: '1rem',
                fontWeight: 600,
                backgroundColor: uploading ? 'rgba(255, 255, 255, 0.5)' : 'white',
                color: '#000000',
                border: 'none',
                borderRadius: '100px',
                cursor: uploading ? 'not-allowed' : 'pointer',
                transition: 'all 0.3s ease'
              }}
            >
              {uploading ? 'Uploading...' : uploaded ? 'Upload New Files' : 'Upload Files'}
            </button>
            <button 
              onClick={handleRunPipeline}
              disabled={running || !uploaded}
              style={{
                padding: '1rem 2.5rem',
                fontSize: '1rem',
                fontWeight: 600,
                backgroundColor: running ? 'rgba(82, 39, 255, 0.5)' : '#5227FF',
                color: 'white',
                border: 'none',
                borderRadius: '100px',
                cursor: running ? 'not-allowed' : 'pointer',
                transition: 'all 0.3s ease'
              }}
            >
              {running ? 'Running Pipeline...' : 'Run Pipeline'}
            </button>
          </div>
        </div>

        {/* Results Section */}
        {showResults && (pipelineOutputs || studentResults) && (
          <div style={{ marginTop: '3rem' }}>
            {studentResults && (
              <section style={{
                padding: '2rem',
                backgroundColor: 'rgba(16, 185, 129, 0.1)',
                backdropFilter: 'blur(10px)',
                border: '2px solid rgba(16, 185, 129, 0.4)',
                borderRadius: '16px',
                marginBottom: '2rem'
              }}>
                <h2 style={{ fontSize: '1.75rem', marginBottom: '1.5rem', fontWeight: 600, color: '#10b981' }}>
                  Student Evaluation Results
                </h2>
                
                {/* Student Info */}
                {(studentResults.student_id || studentResults.name || studentResults.student_name) && (
                  <div style={{ marginBottom: '1.5rem' }}>
                    <p style={{ color: 'rgba(255, 255, 255, 0.6)', fontSize: '0.95rem' }}>Student ID:</p>
                    <p style={{ fontSize: '1.25rem', fontWeight: 600 }}>
                      {studentResults.student_id || studentResults.id || studentResults.name || studentResults.student_name}
                    </p>
                  </div>
                )}

                {/* Score */}
                {(studentResults.total_score !== undefined || studentResults.score !== undefined) && (
                  <div style={{
                    display: 'flex',
                    alignItems: 'center',
                    gap: '1rem',
                    marginBottom: '1.5rem',
                    padding: '1rem',
                    backgroundColor: 'rgba(17, 24, 39, 0.4)',
                    borderRadius: '12px'
                  }}>
                    <div>
                      <p style={{ color: 'rgba(255, 255, 255, 0.6)', fontSize: '0.9rem', marginBottom: '0.25rem' }}>Total Score</p>
                      <p style={{ fontSize: '2rem', fontWeight: 700, color: '#10b981' }}>
                        {studentResults.total_score || studentResults.score}
                        {studentResults.max_score && ` / ${studentResults.max_score}`}
                      </p>
                    </div>
                    {studentResults.percentage !== undefined && (
                      <div style={{ marginLeft: 'auto', textAlign: 'right' }}>
                        <p style={{ color: 'rgba(255, 255, 255, 0.6)', fontSize: '0.9rem', marginBottom: '0.25rem' }}>Percentage</p>
                        <p style={{ fontSize: '1.75rem', fontWeight: 700, color: '#3b82f6' }}>
                          {studentResults.percentage.toFixed(2)}%
                        </p>
                      </div>
                    )}
                  </div>
                )}

                {/* Question-wise Results */}
                {studentResults.question_results && Array.isArray(studentResults.question_results) && (
                  <div>
                    <h3 style={{ fontSize: '1.25rem', marginBottom: '1rem', fontWeight: 600 }}>Question Breakdown</h3>
                    <div style={{
                      display: 'grid',
                      gridTemplateColumns: 'repeat(auto-fill, minmax(60px, 1fr))',
                      gap: '0.75rem'
                    }}>
                      {studentResults.question_results.map((result, idx) => (
                        <div key={idx} style={{
                          padding: '0.75rem',
                          backgroundColor: result.is_correct ? 'rgba(16, 185, 129, 0.2)' : 'rgba(239, 68, 68, 0.2)',
                          border: `2px solid ${result.is_correct ? 'rgba(16, 185, 129, 0.6)' : 'rgba(239, 68, 68, 0.6)'}`,
                          borderRadius: '8px',
                          textAlign: 'center'
                        }}>
                          <div style={{ fontSize: '0.8rem', color: 'rgba(255, 255, 255, 0.7)' }}>Q{result.question_number || idx + 1}</div>
                          <div style={{ fontSize: '1.5rem', fontWeight: 700, color: result.is_correct ? '#10b981' : '#ef4444' }}>
                            {result.is_correct ? '●' : '○'}
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </section>
            )}

            {pipelineOutputs && <PipelineOutputs outputs={pipelineOutputs} />}
          </div>
        )}
      </div>

      {/* Copyright */}
      <div style={{
        position: 'fixed',
        bottom: '2rem',
        left: '50%',
        transform: 'translateX(-50%)',
        zIndex: 1000,
        fontSize: '0.85rem',
        color: 'rgba(255, 255, 255, 0.4)',
        textAlign: 'center'
      }}>
        © 2024 PaperBrain. All rights reserved.
      </div>
    </div>
  );
}
