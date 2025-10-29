import { useState, useEffect } from 'react';
import { apiCurrentStudent, apiAllStudentsResults } from '../api';

export default function Student() {
  const [student, setStudent] = useState(null);
  const [allStudents, setAllStudents] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [activeTab, setActiveTab] = useState('current');

  useEffect(() => {
    loadData();
  }, []);

  async function loadData() {
    setLoading(true);
    setError('');
    try {
      // Load current student
      try {
        const currentStudent = await apiCurrentStudent();
        console.log('Current student data received:', currentStudent);
        setStudent(currentStudent);
      } catch (err) {
        console.log('No current student data:', err.message);
      }

      // Load all students
      try {
        const allStudentsData = await apiAllStudentsResults();
        console.log('All students data received:', allStudentsData);
        setAllStudents(allStudentsData);
      } catch (err) {
        console.log('No all students data:', err.message);
      }
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
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
          <a href="/dashboard" style={{ color: 'white', textDecoration: 'none', opacity: 0.9 }}>Dashboard</a>
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
        <div className="page">
          <div className="page-header">
            <h1>Student Results</h1>
            <button onClick={loadData} className="btn btn-secondary" disabled={loading}>
              {loading ? 'Refreshing...' : 'Refresh'}
            </button>
          </div>

      {/* Tab Navigation */}
      <div className="tab-navigation">
        <button 
          className={`tab-btn ${activeTab === 'current' ? 'active' : ''}`}
          onClick={() => setActiveTab('current')}
        >
          Current Student
        </button>
        <button 
          className={`tab-btn ${activeTab === 'all' ? 'active' : ''}`}
          onClick={() => setActiveTab('all')}
        >
          All Students ({allStudents?.total_students || 0})
        </button>
      </div>

      {loading && <div className="loading">Loading student data...</div>}
      {error && (
        <div className="error-box">
          <p>{error}</p>
          <p className="hint">Make sure you've run the pipeline first to generate student results.</p>
        </div>
      )}
      
      {/* Current Student Tab */}
      {!loading && !error && activeTab === 'current' && student && (
        <div>
          <section style={{
            padding: '2rem',
            backgroundColor: 'rgba(16, 185, 129, 0.1)',
            backdropFilter: 'blur(10px)',
            border: '2px solid rgba(16, 185, 129, 0.4)',
            borderRadius: '16px'
          }}>
            <h2 style={{ fontSize: '1.75rem', marginBottom: '1.5rem', fontWeight: 600, color: '#10b981' }}>
              {student.name || student.student_name || student.student_id || 'Student Evaluation'}
            </h2>

            {/* Main Results */}
            <div style={{
              display: 'grid',
              gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))',
              gap: '1rem',
              marginBottom: '2rem'
            }}>
              {(student.student_id || student.id) && (
                <div className="result-item">
                  <span className="result-label">Student ID:</span>
                  <span className="result-value">{student.student_id || student.id}</span>
                </div>
              )}
              
              {student.total_score !== undefined && (
                <div className="result-item">
                  <span className="result-label">Total Score:</span>
                  <span className="result-value score-highlight">
                    {student.total_score} {student.max_score ? `/ ${student.max_score}` : ''}
                  </span>
                </div>
              )}

              {student.score !== undefined && (
                <div className="result-item">
                  <span className="result-label">Score:</span>
                  <span className="result-value score-highlight">{student.score}</span>
                </div>
              )}
              
              {student.total !== undefined && (
                <div className="result-item">
                  <span className="result-label">Total:</span>
                  <span className="result-value">{student.total}</span>
                </div>
              )}
              
              {student.percentage !== undefined && (
                <div className="result-item">
                  <span className="result-label">Percentage:</span>
                  <span className="result-value percentage-highlight">{student.percentage.toFixed(2)}%</span>
                </div>
              )}

              {student.correct_count !== undefined && (
                <div className="result-item">
                  <span className="result-label">Correct Answers:</span>
                  <span className="result-value score-highlight">{student.correct_count}</span>
                </div>
              )}

              {student.incorrect_count !== undefined && (
                <div className="result-item">
                  <span className="result-label">Incorrect Answers:</span>
                  <span className="result-value" style={{color: '#ef4444'}}>{student.incorrect_count}</span>
                </div>
              )}

              {student.total_questions !== undefined && (
                <div className="result-item">
                  <span className="result-label">Total Questions:</span>
                  <span className="result-value">{student.total_questions}</span>
                </div>
              )}
            </div>

            {/* Question-wise breakdown - Table Format */}
            {student.question_results && Array.isArray(student.question_results) && student.question_results.length > 0 && (
              <div style={{ marginTop: '2rem' }}>
                <h3 style={{ fontSize: '1.25rem', marginBottom: '1rem', fontWeight: 600 }}>Question-wise Marks</h3>
                
                {/* Table View */}
                <div style={{
                  backgroundColor: 'rgba(17, 24, 39, 0.6)',
                  border: '1px solid rgba(255, 255, 255, 0.1)',
                  borderRadius: '12px',
                  overflow: 'hidden'
                }}>
                  <table style={{ width: '100%', borderCollapse: 'collapse' }}>
                    <thead>
                      <tr style={{ backgroundColor: 'rgba(82, 39, 255, 0.2)' }}>
                        <th style={{ padding: '0.75rem 1rem', textAlign: 'left', color: 'rgba(255, 255, 255, 0.8)', fontSize: '0.9rem', fontWeight: 600 }}>Question</th>
                        <th style={{ padding: '0.75rem 1rem', textAlign: 'left', color: 'rgba(255, 255, 255, 0.8)', fontSize: '0.9rem', fontWeight: 600 }}>Status</th>
                        <th style={{ padding: '0.75rem 1rem', textAlign: 'left', color: 'rgba(255, 255, 255, 0.8)', fontSize: '0.9rem', fontWeight: 600 }}>Marks</th>
                        <th style={{ padding: '0.75rem 1rem', textAlign: 'left', color: 'rgba(255, 255, 255, 0.8)', fontSize: '0.9rem', fontWeight: 600 }}>Feedback</th>
                      </tr>
                    </thead>
                    <tbody>
                      {student.question_results.map((result, idx) => (
                        <tr key={idx} style={{ 
                          borderBottom: idx < student.question_results.length - 1 ? '1px solid rgba(255, 255, 255, 0.1)' : 'none'
                        }}>
                          <td style={{ padding: '1rem', color: 'rgba(255, 255, 255, 0.9)', fontWeight: 600 }}>Q{result.question_number || idx + 1}</td>
                          <td style={{ padding: '1rem' }}>
                            <span style={{
                              padding: '0.25rem 0.75rem',
                              borderRadius: '100px',
                              fontSize: '0.85rem',
                              fontWeight: 600,
                              backgroundColor: result.is_correct ? 'rgba(16, 185, 129, 0.2)' : 'rgba(239, 68, 68, 0.2)',
                              color: result.is_correct ? '#10b981' : '#ef4444',
                              border: `1px solid ${result.is_correct ? 'rgba(16, 185, 129, 0.4)' : 'rgba(239, 68, 68, 0.4)'}`
                            }}>
                              {result.is_correct ? 'Correct' : 'Incorrect'}
                            </span>
                          </td>
                          <td style={{ padding: '1rem', color: result.is_correct ? '#10b981' : '#ef4444', fontWeight: 600 }}>
                            {result.marks !== undefined ? `${result.marks} pts` : 'N/A'}
                          </td>
                          <td style={{ padding: '1rem', color: 'rgba(255, 255, 255, 0.7)', fontSize: '0.9rem' }}>
                            {result.feedback || '-'}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            )}

            {/* Alternative questions format */}
            {student.questions && typeof student.questions === 'object' && Object.keys(student.questions).length > 0 && (
              <div style={{ marginTop: '2rem' }}>
                <h3 style={{ fontSize: '1.25rem', marginBottom: '1rem', fontWeight: 600 }}>Question-wise Analysis</h3>
                <div style={{
                  display: 'grid',
                  gridTemplateColumns: 'repeat(auto-fill, minmax(60px, 1fr))',
                  gap: '0.75rem'
                }}>
                  {Object.entries(student.questions).map(([qNum, result]) => (
                    <div key={qNum} style={{
                      padding: '0.75rem',
                      backgroundColor: (result.correct || result.is_correct) ? 'rgba(16, 185, 129, 0.2)' : 'rgba(239, 68, 68, 0.2)',
                      border: `2px solid ${(result.correct || result.is_correct) ? 'rgba(16, 185, 129, 0.6)' : 'rgba(239, 68, 68, 0.6)'}`,
                      borderRadius: '8px',
                      textAlign: 'center'
                    }}>
                      <div style={{ fontSize: '0.8rem', color: 'rgba(255, 255, 255, 0.7)' }}>Q{qNum}</div>
                      <div style={{ fontSize: '1.5rem', fontWeight: 700, color: (result.correct || result.is_correct) ? '#10b981' : '#ef4444' }}>
                        {(result.correct || result.is_correct) ? '●' : '○'}
                      </div>
                      {result.marks && (
                        <div style={{ fontSize: '0.7rem', color: 'rgba(255, 255, 255, 0.6)' }}>{result.marks} pts</div>
                      )}
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Additional metadata */}
            {(student.date || student.timestamp || student.evaluated_at) && (
              <div className="metadata">
                <h4>Evaluation Details</h4>
                <div className="info-row">
                  <strong>Date:</strong>
                  <span>{student.date || student.timestamp || student.evaluated_at}</span>
                </div>
              </div>
            )}

            {/* Raw JSON Data */}
            <details style={{
              marginTop: '2rem',
              paddingTop: '1.5rem',
              borderTop: '1px solid rgba(255, 255, 255, 0.1)'
            }}>
              <summary style={{
                cursor: 'pointer',
                color: '#3b82f6',
                fontWeight: 600,
                padding: '0.5rem',
                userSelect: 'none'
              }}>View Raw JSON Data</summary>
              <pre style={{
                marginTop: '1rem',
                padding: '1rem',
                backgroundColor: 'rgba(0, 0, 0, 0.3)',
                border: '1px solid rgba(255, 255, 255, 0.1)',
                borderRadius: '6px',
                overflowX: 'auto',
                fontSize: '0.85rem',
                color: '#d1d5db'
              }}>{JSON.stringify(student, null, 2)}</pre>
            </details>
          </section>
        </div>
      )}

      {/* All Students Tab */}
      {!loading && !error && activeTab === 'all' && allStudents && allStudents.students && allStudents.students.length > 0 && (
        <div className="all-students-info">
          <div className="summary-stats">
            <div className="stat-item">
              <span className="stat-label">Total Students:</span>
              <span className="stat-value">{allStudents.total_students}</span>
            </div>
            <div className="stat-item">
              <span className="stat-label">Average Score:</span>
              <span className="stat-value">{allStudents.summary.average_score.toFixed(2)}</span>
            </div>
            <div className="stat-item">
              <span className="stat-label">Highest Score:</span>
              <span className="stat-value score-highlight">{allStudents.summary.highest_score}</span>
            </div>
            <div className="stat-item">
              <span className="stat-label">Lowest Score:</span>
              <span className="stat-value">{allStudents.summary.lowest_score}</span>
            </div>
          </div>
          
          <div className="students-grid">
            {allStudents.students.map((student, idx) => (
              <div key={idx} className="student-card">
                <div className="student-header">
                  <h4>{student.name || 'Unknown Student'}</h4>
                  <span className="student-id">{student.student_id}</span>
                </div>
                <div className="student-stats">
                  <div className="stat">
                    <span className="stat-label">Score:</span>
                    <span className="stat-value score-highlight">
                      {student.total_score} / {student.max_score}
                    </span>
                  </div>
                  <div className="stat">
                    <span className="stat-label">Percentage:</span>
                    <span className="stat-value percentage-highlight">
                      {student.percentage.toFixed(1)}%
                    </span>
                  </div>
                  <div className="stat">
                    <span className="stat-label">Correct:</span>
                    <span className="stat-value">{student.correct_count}</span>
                  </div>
                  <div className="stat">
                    <span className="stat-label">Incorrect:</span>
                    <span className="stat-value">{student.incorrect_count}</span>
                  </div>
                </div>
                {student.question_results && student.question_results.length > 0 && (
                  <div className="student-questions">
                    <div className="questions-mini-grid">
                      {student.question_results.map((result, qIdx) => (
                        <div key={qIdx} className={`mini-question ${result.is_correct ? 'correct' : 'incorrect'}`}>
                          <span className="mini-q-num">Q{result.question_number}</span>
                          <span className="mini-q-result">{result.is_correct ? '✓' : '✗'}</span>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>
      )}
      
      {/* No Data */}
      {!loading && !error && !student && !allStudents && (
        <div className="no-data">
          <p>No student data available yet.</p>
          <p className="hint">Run the pipeline from the Dashboard to generate evaluation results.</p>
        </div>
      )}
        </div>
      </div>
    </div>
  );
}