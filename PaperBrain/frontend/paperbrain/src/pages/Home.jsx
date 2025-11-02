import { useState, useEffect, useRef } from 'react';

function DotGrid({ 
  dotSize = 16, 
  gap = 32, 
  baseColor = '#5227FF', 
  activeColor = '#5227FF',
  proximity = 150,
  speedTrigger = 100,
  shockRadius = 250,
  shockStrength = 5,
  maxSpeed = 5000,
  resistance = 750,
  returnDuration = 1.5
}) {
  const canvasRef = useRef(null);
  const [dimensions, setDimensions] = useState({ width: 0, height: 0 });
  const mousePos = useRef({ x: -1000, y: -1000 });
  const prevMousePos = useRef({ x: -1000, y: -1000 });
  const mouseVelocity = useRef({ x: 0, y: 0 });
  const animationRef = useRef(null);
  const dotsRef = useRef([]);
  const lastClickPos = useRef({ x: 0, y: 0, time: 0 });

  useEffect(() => {
    const updateDimensions = () => {
      if (canvasRef.current) {
        setDimensions({
          width: window.innerWidth,
          height: window.innerHeight
        });
      }
    };

    updateDimensions();
    window.addEventListener('resize', updateDimensions);
    return () => window.removeEventListener('resize', updateDimensions);
  }, []);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas || !dimensions.width) return;

    const ctx = canvas.getContext('2d');
    const cols = Math.ceil(dimensions.width / gap);
    const rows = Math.ceil(dimensions.height / gap);

    // Initialize dots
    dotsRef.current = [];
    for (let i = 0; i < cols; i++) {
      for (let j = 0; j < rows; j++) {
        dotsRef.current.push({
          x: i * gap,
          y: j * gap,
          originalX: i * gap,
          originalY: j * gap,
          vx: 0,
          vy: 0
        });
      }
    }

    const handleMouseMove = (e) => {
      prevMousePos.current = { ...mousePos.current };
      mousePos.current = { x: e.clientX, y: e.clientY };
      
      const dx = mousePos.current.x - prevMousePos.current.x;
      const dy = mousePos.current.y - prevMousePos.current.y;
      mouseVelocity.current = { x: dx, y: dy };
    };

    const handleMouseLeave = () => {
      mousePos.current = { x: -1000, y: -1000 };
      mouseVelocity.current = { x: 0, y: 0 };
    };

    const handleClick = (e) => {
      lastClickPos.current = { x: e.clientX, y: e.clientY, time: Date.now() };
    };

    window.addEventListener('mousemove', handleMouseMove);
    window.addEventListener('mouseleave', handleMouseLeave);
    window.addEventListener('click', handleClick);

    const hexToRgb = (hex) => {
      const result = /^#?([a-f\d]{2})([a-f\d]{2})([a-f\d]{2})$/i.exec(hex);
      return result ? {
        r: parseInt(result[1], 16),
        g: parseInt(result[2], 16),
        b: parseInt(result[3], 16)
      } : { r: 82, g: 39, b: 255 };
    };

    const baseRgb = hexToRgb(baseColor);
    const activeRgb = hexToRgb(activeColor);

    const draw = () => {
      ctx.clearRect(0, 0, dimensions.width, dimensions.height);

      const speed = Math.sqrt(mouseVelocity.current.x ** 2 + mouseVelocity.current.y ** 2);
      const isInertia = speed > speedTrigger;
      
      const timeSinceClick = Date.now() - lastClickPos.current.time;
      const shockwave = timeSinceClick < 1000;

      dotsRef.current.forEach(dot => {
        const distToMouse = Math.sqrt(
          Math.pow(dot.x - mousePos.current.x, 2) + 
          Math.pow(dot.y - mousePos.current.y, 2)
        );

        // Shockwave effect
        if (shockwave) {
          const distToClick = Math.sqrt(
            Math.pow(dot.originalX - lastClickPos.current.x, 2) + 
            Math.pow(dot.originalY - lastClickPos.current.y, 2)
          );
          
          if (distToClick < shockRadius) {
            const angle = Math.atan2(
              dot.originalY - lastClickPos.current.y,
              dot.originalX - lastClickPos.current.x
            );
            const force = (1 - distToClick / shockRadius) * shockStrength;
            dot.vx += Math.cos(angle) * force;
            dot.vy += Math.sin(angle) * force;
          }
        }

        // Inertia effect
        if (isInertia && distToMouse < proximity) {
          const factor = 1 - (distToMouse / proximity);
          const angle = Math.atan2(
            dot.y - mousePos.current.y,
            dot.x - mousePos.current.x
          );
          const force = Math.min(speed / maxSpeed, 1) * factor * 2;
          dot.vx += Math.cos(angle) * force;
          dot.vy += Math.sin(angle) * force;
        }

        // Apply resistance
        dot.vx *= (1 - 1 / resistance);
        dot.vy *= (1 - 1 / resistance);

        // Return to original position
        const dx = dot.originalX - dot.x;
        const dy = dot.originalY - dot.y;
        dot.vx += dx / (returnDuration * 60);
        dot.vy += dy / (returnDuration * 60);

        // Update position
        dot.x += dot.vx;
        dot.y += dot.vy;

        // Draw dot
        let opacity = 0.3;
        let size = dotSize;
        let color = baseRgb;

        if (distToMouse < proximity) {
          const factor = 1 - (distToMouse / proximity);
          opacity = 0.3 + (factor * 0.7);
          size = dotSize + (factor * 4);
          color = {
            r: Math.round(baseRgb.r + (activeRgb.r - baseRgb.r) * factor),
            g: Math.round(baseRgb.g + (activeRgb.g - baseRgb.g) * factor),
            b: Math.round(baseRgb.b + (activeRgb.b - baseRgb.b) * factor)
          };
        }

        ctx.fillStyle = `rgba(${color.r}, ${color.g}, ${color.b}, ${opacity})`;
        ctx.beginPath();
        ctx.arc(dot.x, dot.y, size / 2, 0, Math.PI * 2);
        ctx.fill();
      });

      animationRef.current = requestAnimationFrame(draw);
    };

    draw();

    return () => {
      window.removeEventListener('mousemove', handleMouseMove);
      window.removeEventListener('mouseleave', handleMouseLeave);
      window.removeEventListener('click', handleClick);
      if (animationRef.current) {
        cancelAnimationFrame(animationRef.current);
      }
    };
  }, [dimensions, dotSize, gap, baseColor, activeColor, proximity, speedTrigger, shockRadius, shockStrength, maxSpeed, resistance, returnDuration]);

  return (
    <canvas
      ref={canvasRef}
      width={dimensions.width}
      height={dimensions.height}
      style={{
        position: 'fixed',
        top: 0,
        left: 0,
        width: '100%',
        height: '100%',
        zIndex: 0,
        pointerEvents: 'none'
      }}
    />
  );
}

export default function Home() {
  return (
    <div style={{
      minHeight: '100vh',
      backgroundColor: '#000000',
      color: 'white',
      fontFamily: '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif',
      position: 'relative'
    }}>
      <DotGrid dotSize={3} gap={40} />
      
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
        maxWidth: '1200px',
        margin: '0 auto'
      }}>
        {/* Hero Section */}
        <div style={{
          textAlign: 'center',
          marginBottom: '4rem'
        }}>
          <h1 style={{
            fontSize: 'clamp(2.5rem, 8vw, 4.5rem)',
            fontWeight: 700,
            lineHeight: 1.1,
            marginBottom: '1.5rem',
            maxWidth: '900px',
            margin: '0 auto 1.5rem'
          }}>
            AI-Powered Automated Exam Evaluation System
          </h1>

          <p style={{
            fontSize: 'clamp(1rem, 2vw, 1.25rem)',
            color: 'rgba(255, 255, 255, 0.7)',
            marginBottom: '2.5rem',
            maxWidth: '700px',
            margin: '0 auto 2.5rem',
            lineHeight: 1.6
          }}>
            Transform your grading workflow with intelligent image processing, 
            optical character recognition, and AI-powered evaluation.
          </p>

          <div style={{
            display: 'flex',
            gap: '1rem',
            flexWrap: 'wrap',
            justifyContent: 'center'
          }}>
            <a href="/dashboard" style={{
              padding: '1rem 2.5rem',
              fontSize: '1rem',
              fontWeight: 600,
              backgroundColor: 'white',
              color: '#0b0f19',
              border: 'none',
              borderRadius: '100px',
              cursor: 'pointer',
              textDecoration: 'none',
              display: 'inline-block',
              transition: 'all 0.3s ease'
            }}>
              Get Started
            </a>
            <a href="/outputs" style={{
              padding: '1rem 2.5rem',
              fontSize: '1rem',
              fontWeight: 600,
              backgroundColor: 'transparent',
              color: 'rgba(255, 255, 255, 0.7)',
              border: '1px solid rgba(255, 255, 255, 0.2)',
              borderRadius: '100px',
              cursor: 'pointer',
              textDecoration: 'none',
              display: 'inline-block',
              transition: 'all 0.3s ease'
            }}>
              View Results
            </a>
          </div>
        </div>

        {/* Features */}
        <div style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(auto-fit, minmax(265px, 1fr))',
            gap: '1.5rem',
            marginBottom: '4rem'
          }}>
            {[
              { 
                icon: <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <circle cx="11" cy="11" r="8"/>
                  <path d="m21 21-4.35-4.35"/>
                </svg>,
                title: 'Smart Recognition', 
                desc: 'Advanced OCR technology extracts answers with precision' 
              },
              { 
                icon: <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <path d="M13 2L3 14h9l-1 8 10-12h-9l1-8z"/>
                </svg>,
                title: 'Lightning Fast', 
                desc: 'Process multiple exams in minutes, not hours' 
              },
              { 
                icon: <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <circle cx="12" cy="12" r="10"/>
                  <path d="M12 6v6l4 2"/>
                </svg>,
                title: 'AI-Powered', 
                desc: 'Intelligent evaluation with contextual understanding' 
              },
              { 
                icon: <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <polyline points="22 12 18 12 15 21 9 3 6 12 2 12"/>
                </svg>,
                title: 'Analytics', 
                desc: 'Comprehensive performance insights and visualizations' 
              }
            ].map((feature, i) => (
              <div key={i} style={{
                padding: '2rem',
                backgroundColor: 'rgba(17, 24, 39, 0.6)',
                backdropFilter: 'blur(10px)',
                border: '1px solid rgba(255, 255, 255, 0.1)',
                borderRadius: '16px',
                transition: 'all 0.3s ease'
              }}>
                <div style={{
                  width: '48px',
                  height: '48px',
                  marginBottom: '1rem',
                  color: '#5227FF'
                }}>
                  {feature.icon}
                </div>
                <h3 style={{
                  fontSize: '1.25rem',
                  fontWeight: 600,
                  marginBottom: '0.75rem'
                }}>{feature.title}</h3>
                <p style={{
                  color: 'rgba(255, 255, 255, 0.6)',
                  fontSize: '0.95rem',
                  lineHeight: 1.5
                }}>{feature.desc}</p>
              </div>
            ))}
          </div>

        {/* CTA */}
        <div style={{
            textAlign: 'center',
            padding: '3rem 2rem',
            backgroundColor: 'rgba(17, 24, 39, 0.4)',
            backdropFilter: 'blur(10px)',
            border: '1px solid rgba(255, 255, 255, 0.1)',
            borderRadius: '20px'
          }}>
            <h2 style={{
              fontSize: 'clamp(1.5rem, 4vw, 2rem)',
              fontWeight: 600,
              marginBottom: '1.5rem'
            }}>Ready to revolutionize exam grading?</h2>
            <a href="/dashboard" style={{
              padding: '1rem 2.5rem',
              fontSize: '1rem',
              fontWeight: 600,
              backgroundColor: 'white',
              color: '#0b0f19',
              border: 'none',
              borderRadius: '100px',
              cursor: 'pointer',
              textDecoration: 'none',
              display: 'inline-block',
              transition: 'all 0.3s ease'
            }}>
          Start Grading Now
        </a>
      </div>
      </div>

      {/* Copyright */}
      <div style={{
        position: 'absolute',
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