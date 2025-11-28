'use client';

import { useEffect, useRef } from 'react';

const CustomCursor = () => {
  const dotRef = useRef<HTMLDivElement>(null);
  const ringRef = useRef<HTMLDivElement>(null);
  const mousePos = useRef({ x: 0, y: 0 });
  const isPointer = useRef(false);
  const isClicking = useRef(false);

  useEffect(() => {
    // Hide on touch devices
    const isTouchDevice = 'ontouchstart' in window || navigator.maxTouchPoints > 0;
    if (isTouchDevice) return;

    const dot = dotRef.current;
    const ring = ringRef.current;
    if (!dot || !ring) return;

    const handleMouseMove = (e: MouseEvent) => {
      mousePos.current = { x: e.clientX, y: e.clientY };
      
      // Direct DOM manipulation - no React re-renders
      dot.style.transform = `translate(${e.clientX}px, ${e.clientY}px) translate(-50%, -50%)`;
      ring.style.transform = `translate(${e.clientX}px, ${e.clientY}px) translate(-50%, -50%)`;

      // Check if hovering clickable element
      const el = e.target as HTMLElement;
      const clickable = el.closest('button, a, [role="button"], input, select, textarea, label');
      const newIsPointer = !!clickable;
      
      if (newIsPointer !== isPointer.current) {
        isPointer.current = newIsPointer;
        updateCursorStyle();
      }
    };

    const handleMouseDown = () => {
      isClicking.current = true;
      updateCursorStyle();
    };

    const handleMouseUp = () => {
      isClicking.current = false;
      updateCursorStyle();
    };

    const handleMouseLeave = () => {
      dot.style.opacity = '0';
      ring.style.opacity = '0';
    };

    const handleMouseEnter = () => {
      dot.style.opacity = '1';
      ring.style.opacity = '1';
    };

    const updateCursorStyle = () => {
      if (!dot || !ring) return;
      
      const dotSize = isClicking.current ? 6 : isPointer.current ? 8 : 10;
      const ringSize = isClicking.current ? 24 : isPointer.current ? 40 : 32;
      
      dot.style.width = `${dotSize}px`;
      dot.style.height = `${dotSize}px`;
      
      ring.style.width = `${ringSize}px`;
      ring.style.height = `${ringSize}px`;
      ring.style.borderColor = isPointer.current ? 'rgba(96, 165, 250, 0.8)' : 'rgba(255, 255, 255, 0.5)';
    };

    window.addEventListener('mousemove', handleMouseMove, { passive: true });
    window.addEventListener('mousedown', handleMouseDown);
    window.addEventListener('mouseup', handleMouseUp);
    document.addEventListener('mouseleave', handleMouseLeave);
    document.addEventListener('mouseenter', handleMouseEnter);

    return () => {
      window.removeEventListener('mousemove', handleMouseMove);
      window.removeEventListener('mousedown', handleMouseDown);
      window.removeEventListener('mouseup', handleMouseUp);
      document.removeEventListener('mouseleave', handleMouseLeave);
      document.removeEventListener('mouseenter', handleMouseEnter);
    };
  }, []);

  return (
    <>
      {/* Main cursor dot */}
      <div
        ref={dotRef}
        style={{
          position: 'fixed',
          top: 0,
          left: 0,
          width: 10,
          height: 10,
          backgroundColor: '#fff',
          borderRadius: '50%',
          pointerEvents: 'none',
          zIndex: 99999,
          mixBlendMode: 'difference',
          willChange: 'transform',
        }}
      />

      {/* Outer ring */}
      <div
        ref={ringRef}
        style={{
          position: 'fixed',
          top: 0,
          left: 0,
          width: 32,
          height: 32,
          border: '2px solid rgba(255, 255, 255, 0.5)',
          borderRadius: '50%',
          pointerEvents: 'none',
          zIndex: 99998,
          transition: 'width 0.15s, height 0.15s, border-color 0.15s',
          willChange: 'transform',
        }}
      />

      {/* Global style to hide default cursor */}
      <style jsx global>{`
        * {
          cursor: none !important;
        }
      `}</style>
    </>
  );
};

export default CustomCursor;
