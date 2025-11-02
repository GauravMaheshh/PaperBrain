import { useState } from 'react';

export default function PipelineOutputs({ outputs }) {
  const [selectedImage, setSelectedImage] = useState(null);
  const [zoom, setZoom] = useState(1);
  const [position, setPosition] = useState({ x: 0, y: 0 });

  if (!outputs) {
    return (
      <div style={{
        padding: '3rem',
        textAlign: 'center',
        backgroundColor: 'rgba(17, 24, 39, 0.4)',
        backdropFilter: 'blur(10px)',
        border: '1px solid rgba(255, 255, 255, 0.1)',
        borderRadius: '16px',
        color: 'rgba(255, 255, 255, 0.6)'
      }}>
        No outputs available
      </div>
    );
  }

  const { preprocessor, region_selector, text_recognition, evaluator } = outputs;

  const getImageUrl = (stage, filename) => {
    return `/api/outputs/${stage}/${filename}`;
  };

  const handleImageClick = (stage, filename) => {
    setSelectedImage({ stage, filename, url: getImageUrl(stage, filename) });
    setZoom(1);
    setPosition({ x: 0, y: 0 });
  };

  const closeImageViewer = () => {
    setSelectedImage(null);
    setZoom(1);
    setPosition({ x: 0, y: 0 });
  };

  const handleZoomIn = () => setZoom(Math.min(zoom + 0.25, 3));
  const handleZoomOut = () => setZoom(Math.max(zoom - 0.25, 0.5));
  const handleResetZoom = () => {
    setZoom(1);
    setPosition({ x: 0, y: 0 });
  };

  const Section = ({ title, description, count, images, stage }) => (
    <section style={{
      marginBottom: '3rem',
      padding: '2rem',
      backgroundColor: 'rgba(17, 24, 39, 0.4)',
      backdropFilter: 'blur(10px)',
      border: '1px solid rgba(255, 255, 255, 0.1)',
      borderRadius: '16px'
    }}>
      <h2 style={{
        fontSize: '1.5rem',
        fontWeight: 600,
        marginBottom: '0.5rem'
      }}>
        {title} ({count})
      </h2>
      <p style={{
        color: 'rgba(255, 255, 255, 0.6)',
        marginBottom: '1.5rem',
        fontSize: '0.95rem'
      }}>
        {description}
      </p>
      <div style={{
        display: 'grid',
        gridTemplateColumns: 'repeat(auto-fill, minmax(250px, 1fr))',
        gap: '1.5rem'
      }}>
        {images.map((img, idx) => (
          <div key={idx} style={{
            backgroundColor: 'rgba(17, 24, 39, 0.6)',
            border: '1px solid rgba(255, 255, 255, 0.1)',
            borderRadius: '12px',
            overflow: 'hidden',
            transition: 'all 0.3s ease'
          }}
          onMouseEnter={(e) => {
            e.currentTarget.style.transform = 'translateY(-4px)';
            e.currentTarget.style.borderColor = 'rgba(82, 39, 255, 0.4)';
          }}
          onMouseLeave={(e) => {
            e.currentTarget.style.transform = 'translateY(0)';
            e.currentTarget.style.borderColor = 'rgba(255, 255, 255, 0.1)';
          }}
          >
            <img 
              src={getImageUrl(stage, img)} 
              alt={img}
              loading="lazy"
              onClick={() => handleImageClick(stage, img)}
              style={{
                width: '100%',
                height: '200px',
                objectFit: 'cover',
                display: 'block',
                cursor: 'pointer',
                transition: 'all 0.2s ease'
              }}
              onMouseEnter={(e) => {
                e.currentTarget.style.opacity = '0.8';
              }}
              onMouseLeave={(e) => {
                e.currentTarget.style.opacity = '1';
              }}
            />
            <div style={{
              padding: '0.75rem',
              fontSize: '0.85rem',
              color: 'rgba(255, 255, 255, 0.7)',
              overflow: 'hidden',
              textOverflow: 'ellipsis',
              whiteSpace: 'nowrap'
            }}>
              {img}
            </div>
          </div>
        ))}
      </div>
    </section>
  );

  return (
    <div>
      {preprocessor && preprocessor.count > 0 && (
        <Section
          title="Preprocessor - Aligned Outputs"
          description="Images after alignment processing to match the template format."
          count={preprocessor.count}
          images={preprocessor.images}
          stage="preprocessor"
        />
      )}

      {region_selector && region_selector.count > 0 && (
        <Section
          title="Region Selector - Evaluation Results"
          description="Processed images showing selected regions for text recognition."
          count={region_selector.count}
          images={region_selector.images}
          stage="region-selector"
        />
      )}

      {text_recognition && text_recognition.count > 0 && (
        <Section
          title="Text Recognition - Debug Crops"
          description="Cropped regions extracted for OCR processing."
          count={text_recognition.count}
          images={text_recognition.debug_crops}
          stage="text-recognition"
        />
      )}

      {text_recognition && text_recognition.json_exists && text_recognition.json_data && (
        <section style={{
          marginBottom: '3rem',
          padding: '2rem',
          backgroundColor: 'rgba(17, 24, 39, 0.4)',
          backdropFilter: 'blur(10px)',
          border: '1px solid rgba(255, 255, 255, 0.1)',
          borderRadius: '16px'
        }}>
          <h2 style={{
            fontSize: '1.5rem',
            fontWeight: 600,
            marginBottom: '0.5rem'
          }}>
            Text Recognition - Extracted Answers
          </h2>
          <p style={{
            color: 'rgba(255, 255, 255, 0.6)',
            marginBottom: '1.5rem',
            fontSize: '0.95rem'
          }}>
            Student answers extracted from the answer sheet via OCR.
          </p>
          
          <div style={{
            backgroundColor: 'rgba(17, 24, 39, 0.6)',
            border: '1px solid rgba(255, 255, 255, 0.1)',
            borderRadius: '12px',
            padding: '1.5rem'
          }}>
            <h3 style={{ fontSize: '1.25rem', marginBottom: '1rem', fontWeight: 600 }}>Student Information</h3>
            <div style={{
              display: 'grid',
              gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))',
              gap: '1rem',
              marginBottom: '2rem'
            }}>
              <div>
                <span style={{ color: 'rgba(255, 255, 255, 0.6)', fontSize: '0.9rem' }}>Name:</span>
                <div style={{ fontSize: '1.1rem', marginTop: '0.25rem' }}>
                  {text_recognition.json_data.student_info?.name || 'N/A'}
                </div>
              </div>
              <div>
                <span style={{ color: 'rgba(255, 255, 255, 0.6)', fontSize: '0.9rem' }}>Roll No:</span>
                <div style={{ fontSize: '1.1rem', marginTop: '0.25rem' }}>
                  {text_recognition.json_data.student_info?.roll_no || 'N/A'}
                </div>
              </div>
            </div>
            
            <h3 style={{ fontSize: '1.25rem', marginBottom: '1rem', fontWeight: 600 }}>Extracted Answers</h3>
            <div style={{
              display: 'grid',
              gridTemplateColumns: 'repeat(auto-fill, minmax(150px, 1fr))',
              gap: '1rem'
            }}>
              {text_recognition.json_data.answers && Object.entries(text_recognition.json_data.answers)
                .sort(([a], [b]) => {
                  // Sort questions numerically (Q1, Q2, Q10 instead of Q1, Q10, Q2)
                  const numA = parseInt(a.replace(/\D/g, '')) || 0;
                  const numB = parseInt(b.replace(/\D/g, '')) || 0;
                  return numA - numB;
                })
                .map(([question, answer]) => (
                <div key={question} style={{
                  padding: '1rem',
                  backgroundColor: 'rgba(82, 39, 255, 0.15)',
                  border: '2px solid rgba(82, 39, 255, 0.4)',
                  borderRadius: '12px',
                  transition: 'all 0.3s ease',
                  cursor: 'default'
                }}
                onMouseEnter={(e) => {
                  e.currentTarget.style.transform = 'translateY(-2px)';
                  e.currentTarget.style.borderColor = 'rgba(82, 39, 255, 0.6)';
                  e.currentTarget.style.backgroundColor = 'rgba(82, 39, 255, 0.25)';
                }}
                onMouseLeave={(e) => {
                  e.currentTarget.style.transform = 'translateY(0)';
                  e.currentTarget.style.borderColor = 'rgba(82, 39, 255, 0.4)';
                  e.currentTarget.style.backgroundColor = 'rgba(82, 39, 255, 0.15)';
                }}>
                  <div style={{
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'space-between',
                    marginBottom: '0.5rem'
                  }}>
                    <span style={{
                      color: '#5227FF',
                      fontSize: '0.9rem',
                      fontWeight: 700,
                      textTransform: 'uppercase',
                      letterSpacing: '0.05em'
                    }}>
                      {question}
                    </span>
                    <div style={{
                      width: '8px',
                      height: '8px',
                      borderRadius: '50%',
                      backgroundColor: '#5227FF',
                      opacity: 0.6
                    }}></div>
                  </div>
                  <div style={{
                    fontSize: '1.5rem',
                    color: '#fff',
                    fontWeight: 700,
                    textAlign: 'center',
                    padding: '0.5rem',
                    backgroundColor: 'rgba(82, 39, 255, 0.2)',
                    borderRadius: '8px',
                    minHeight: '50px',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center'
                  }}>
                    {answer || 'N/A'}
                  </div>
                </div>
              ))}
            </div>
          </div>
        </section>
      )}

      {evaluator && evaluator.current_student_data && evaluator.current_student_file && (
        <section style={{
          marginBottom: '3rem',
          padding: '2rem',
          backgroundColor: 'rgba(16, 185, 129, 0.1)',
          backdropFilter: 'blur(10px)',
          border: '1px solid rgba(16, 185, 129, 0.4)',
          borderRadius: '16px'
        }}>
          <h2 style={{
            fontSize: '1.5rem',
            fontWeight: 600,
            marginBottom: '0.5rem',
            color: '#10b981'
          }}>
            Current Student Evaluation Results
          </h2>
          <p style={{
            color: 'rgba(255, 255, 255, 0.6)',
            marginBottom: '1.5rem',
            fontSize: '0.95rem'
          }}>
            Evaluation results for the most recently processed student.
          </p>
          
          <div style={{
            backgroundColor: 'rgba(17, 24, 39, 0.6)',
            border: '1px solid rgba(255, 255, 255, 0.1)',
            borderRadius: '12px',
            padding: '1.5rem'
          }}>
            {/* Student Info */}
            {evaluator.current_student_data.student_info && (
              <div style={{ marginBottom: '1.5rem' }}>
                <h3 style={{ fontSize: '1.25rem', marginBottom: '1rem', fontWeight: 600 }}>Student Information</h3>
                <div style={{
                  display: 'grid',
                  gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))',
                  gap: '1rem'
                }}>
                  <div>
                    <span style={{ color: 'rgba(255, 255, 255, 0.6)', fontSize: '0.9rem' }}>Name:</span>
                    <div style={{ fontSize: '1.1rem', marginTop: '0.25rem', fontWeight: 600 }}>
                      {evaluator.current_student_data.student_info?.name || 'N/A'}
                    </div>
                  </div>
                  <div>
                    <span style={{ color: 'rgba(255, 255, 255, 0.6)', fontSize: '0.9rem' }}>Roll No:</span>
                    <div style={{ fontSize: '1.1rem', marginTop: '0.25rem', fontWeight: 600 }}>
                      {evaluator.current_student_data.student_info?.roll_no || 'N/A'}
                    </div>
                  </div>
                </div>
              </div>
            )}

            {/* Score Summary */}
            {(evaluator.current_student_data.total_awarded_marks !== undefined || 
              evaluator.current_student_data.total_possible_marks !== undefined) && (
              <div style={{ marginBottom: '1.5rem' }}>
                <h3 style={{ fontSize: '1.25rem', marginBottom: '1rem', fontWeight: 600 }}>Score Summary</h3>
                <div style={{
                  display: 'grid',
                  gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))',
                  gap: '1rem'
                }}>
                  {evaluator.current_student_data.total_awarded_marks !== undefined && (
                    <div style={{
                      padding: '1rem',
                      backgroundColor: 'rgba(16, 185, 129, 0.15)',
                      border: '2px solid rgba(16, 185, 129, 0.4)',
                      borderRadius: '12px'
                    }}>
                      <span style={{ color: 'rgba(255, 255, 255, 0.6)', fontSize: '0.9rem', display: 'block', marginBottom: '0.5rem' }}>
                        Total Awarded Marks
                      </span>
                      <span style={{ color: '#10b981', fontSize: '1.5rem', fontWeight: 700 }}>
                        {evaluator.current_student_data.total_awarded_marks}
                      </span>
                    </div>
                  )}
                  {evaluator.current_student_data.total_possible_marks !== undefined && (
                    <div style={{
                      padding: '1rem',
                      backgroundColor: 'rgba(16, 185, 129, 0.15)',
                      border: '2px solid rgba(16, 185, 129, 0.4)',
                      borderRadius: '12px'
                    }}>
                      <span style={{ color: 'rgba(255, 255, 255, 0.6)', fontSize: '0.9rem', display: 'block', marginBottom: '0.5rem' }}>
                        Total Possible Marks
                      </span>
                      <span style={{ color: '#10b981', fontSize: '1.5rem', fontWeight: 700 }}>
                        {evaluator.current_student_data.total_possible_marks}
                      </span>
                    </div>
                  )}
                  {evaluator.current_student_data.total_awarded_marks !== undefined && 
                   evaluator.current_student_data.total_possible_marks !== undefined && (
                    <div style={{
                      padding: '1rem',
                      backgroundColor: 'rgba(16, 185, 129, 0.15)',
                      border: '2px solid rgba(16, 185, 129, 0.4)',
                      borderRadius: '12px'
                    }}>
                      <span style={{ color: 'rgba(255, 255, 255, 0.6)', fontSize: '0.9rem', display: 'block', marginBottom: '0.5rem' }}>
                        Percentage
                      </span>
                      <span style={{ color: '#10b981', fontSize: '1.5rem', fontWeight: 700 }}>
                        {((evaluator.current_student_data.total_awarded_marks / evaluator.current_student_data.total_possible_marks) * 100).toFixed(2)}%
                      </span>
                    </div>
                  )}
                </div>
              </div>
            )}

            {/* Question-wise Answers */}
            {evaluator.current_student_data.answers && 
             typeof evaluator.current_student_data.answers === 'object' && 
             Object.keys(evaluator.current_student_data.answers).length > 0 && (
              <div>
                <h3 style={{ fontSize: '1.25rem', marginBottom: '1rem', fontWeight: 600 }}>Question-wise Evaluation</h3>
                <div style={{
                  display: 'grid',
                  gridTemplateColumns: 'repeat(auto-fill, minmax(180px, 1fr))',
                  gap: '1rem'
                }}>
                  {Object.entries(evaluator.current_student_data.answers)
                    .sort(([a], [b]) => {
                      const numA = parseInt(a.replace(/\D/g, '')) || 0;
                      const numB = parseInt(b.replace(/\D/g, '')) || 0;
                      return numA - numB;
                    })
                    .map(([question, qData]) => (
                    <div key={question} style={{
                      padding: '1rem',
                      backgroundColor: qData.awarded_marks > 0 ? 'rgba(16, 185, 129, 0.15)' : 'rgba(239, 68, 68, 0.15)',
                      border: `2px solid ${qData.awarded_marks > 0 ? 'rgba(16, 185, 129, 0.4)' : 'rgba(239, 68, 68, 0.4)'}`,
                      borderRadius: '12px',
                      transition: 'all 0.3s ease'
                    }}
                    onMouseEnter={(e) => {
                      e.currentTarget.style.transform = 'translateY(-2px)';
                    }}
                    onMouseLeave={(e) => {
                      e.currentTarget.style.transform = 'translateY(0)';
                    }}>
                      <div style={{
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'space-between',
                        marginBottom: '0.5rem'
                      }}>
                        <span style={{
                          color: qData.awarded_marks > 0 ? '#10b981' : '#ef4444',
                          fontSize: '0.9rem',
                          fontWeight: 700,
                          textTransform: 'uppercase'
                        }}>
                          {question}
                        </span>
                        <span style={{
                          padding: '0.25rem 0.5rem',
                          borderRadius: '100px',
                          fontSize: '0.75rem',
                          fontWeight: 600,
                          backgroundColor: qData.awarded_marks > 0 ? 'rgba(16, 185, 129, 0.3)' : 'rgba(239, 68, 68, 0.3)',
                          color: qData.awarded_marks > 0 ? '#10b981' : '#ef4444'
                        }}>
                          {qData.awarded_marks} / {qData.max_marks}
                        </span>
                      </div>
                      <div style={{
                        fontSize: '1.25rem',
                        color: '#fff',
                        fontWeight: 700,
                        textAlign: 'center',
                        padding: '0.5rem',
                        backgroundColor: 'rgba(0, 0, 0, 0.2)',
                        borderRadius: '8px',
                        marginBottom: '0.5rem'
                      }}>
                        {qData.answer || 'N/A'}
                      </div>
                      {qData.feedback && (
                        <div style={{
                          fontSize: '0.85rem',
                          color: 'rgba(255, 255, 255, 0.7)',
                          fontStyle: 'italic',
                          padding: '0.5rem',
                          backgroundColor: 'rgba(0, 0, 0, 0.1)',
                          borderRadius: '6px'
                        }}>
                          {qData.feedback}
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        </section>
      )}

      {evaluator && evaluator.count > 0 && (
        <>
          <Section
            title="Evaluation Visualizations - Whole Class"
            description="Charts and visualizations showing evaluation results and statistics from all students in the CSV."
            count={evaluator.count}
            images={evaluator.visualizations.filter(img => img !== 'current_student_performance.png')}
            stage="visualizations"
          />
          {evaluator.visualizations.includes('current_student_performance.png') && (
            <Section
              title="Evaluation Visualizations - Current Student"
              description="Performance visualization for the most recently processed student."
              count={1}
              images={['current_student_performance.png']}
              stage="visualizations"
            />
          )}
        </>
      )}

      {(!preprocessor || preprocessor.count === 0) && 
       (!region_selector || region_selector.count === 0) &&
       (!text_recognition || text_recognition.count === 0) && 
       (!evaluator || evaluator.count === 0) && (
        <div style={{
          padding: '3rem',
          textAlign: 'center',
          backgroundColor: 'rgba(17, 24, 39, 0.4)',
          backdropFilter: 'blur(10px)',
          border: '1px solid rgba(255, 255, 255, 0.1)',
          borderRadius: '16px',
          color: 'rgba(255, 255, 255, 0.6)'
        }}>
          <p>No pipeline outputs yet. Upload files and run the pipeline first.</p>
        </div>
      )}

      {/* Image Viewer Modal with Zoom */}
      {selectedImage && (
        <div
          onClick={closeImageViewer}
          style={{
            position: 'fixed',
            inset: 0,
            backgroundColor: 'rgba(0, 0, 0, 0.95)',
            zIndex: 9999,
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            padding: '2rem'
          }}
        >
          {/* Zoom Controls */}
          <div style={{
            position: 'absolute',
            top: '2rem',
            right: '2rem',
            display: 'flex',
            gap: '0.5rem',
            zIndex: 10000
          }}>
            <button onClick={(e) => { e.stopPropagation(); handleZoomIn(); }} style={{ padding: '0.75rem', backgroundColor: '#5227FF', color: 'white', border: 'none', borderRadius: '8px', cursor: 'pointer', fontSize: '1.25rem', fontWeight: 600 }}>+</button>
            <button onClick={(e) => { e.stopPropagation(); handleZoomOut(); }} style={{ padding: '0.75rem', backgroundColor: '#5227FF', color: 'white', border: 'none', borderRadius: '8px', cursor: 'pointer', fontSize: '1.25rem', fontWeight: 600 }}>-</button>
            <button onClick={(e) => { e.stopPropagation(); handleResetZoom(); }} style={{ padding: '0.75rem 1rem', backgroundColor: '#5227FF', color: 'white', border: 'none', borderRadius: '8px', cursor: 'pointer', fontSize: '0.9rem' }}>Reset</button>
            <button onClick={(e) => { e.stopPropagation(); closeImageViewer(); }} style={{ padding: '0.75rem 1.5rem', backgroundColor: '#ef4444', color: 'white', border: 'none', borderRadius: '8px', cursor: 'pointer' }}>Close</button>
          </div>

          {/* Image Display */}
          <div onClick={(e) => e.stopPropagation()} style={{ maxWidth: '95vw', maxHeight: '95vh', overflow: 'auto' }}>
            <img src={selectedImage.url} alt={selectedImage.filename} style={{ width: '100%', height: 'auto', transform: `scale(${zoom})`, transformOrigin: 'center', transition: 'transform 0.3s ease' }} />
          </div>

          {/* Filename Display */}
          <div style={{ position: 'absolute', bottom: '2rem', left: '50%', transform: 'translateX(-50%)', backgroundColor: 'rgba(17, 24, 39, 0.9)', padding: '0.75rem 1.5rem', borderRadius: '8px', color: 'white', fontSize: '0.9rem' }}>
            {selectedImage.filename}
          </div>
        </div>
      )}
    </div>
  );
}