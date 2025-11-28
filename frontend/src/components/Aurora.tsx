"use client";

import React, { useEffect, useRef } from "react";

const vertexShader = `
attribute vec2 uv;
attribute vec2 position;
varying vec2 vUv;
void main() {
    vUv = uv;
    gl_Position = vec4(position, 0, 1);
}
`;

const fragmentShader = `
precision highp float;

uniform float uTime;
uniform float uAmplitude;
uniform vec3 uColorStops[3];
uniform vec2 uResolution;
uniform float uBlend;

varying vec2 vUv;

vec3 permute(vec3 x) {
    return mod(((x * 34.0) + 1.0) * x, 289.0);
}

float snoise(vec2 v) {
    vec4 C = vec4(0.211324865405187, 0.366025403784439, -0.577350269189626, 0.024390243902439);
    vec2 i = floor(v + dot(v, C.yy));
    vec2 x0 = v - i + dot(i, C.xx);
    vec2 i1 = (x0.x > x0.y) ? vec2(1.0, 0.0) : vec2(0.0, 1.0);
    vec4 x12 = x0.xyxy + C.xxzz;
    x12.xy -= i1;
    i = mod(i, 289.0);
    vec3 p = permute(permute(i.y + vec3(0.0, i1.y, 1.0)) + i.x + vec3(0.0, i1.x, 1.0));
    vec3 m = max(0.5 - vec3(dot(x0, x0), dot(x12.xy, x12.xy), dot(x12.zw, x12.zw)), 0.0);
    m = m * m;
    m = m * m;
    vec3 x = 2.0 * fract(p * C.www) - 1.0;
    vec3 h = abs(x) - 0.5;
    vec3 ox = floor(x + 0.5);
    vec3 a0 = x - ox;
    m *= 1.79284291400159 - 0.85373472095314 * (a0 * a0 + h * h);
    vec3 g;
    g.x = a0.x * x0.x + h.x * x0.y;
    g.yz = a0.yz * x12.xz + h.yz * x12.yw;
    return 130.0 * dot(m, g);
}

void main() {
    vec2 uv = gl_FragCoord.xy / uResolution.xy;
    
    float t = uTime;
    
    // Multiple flowing noise layers
    float n1 = snoise(vec2(uv.x * 1.5 + t * 0.15, uv.y * 1.0 + t * 0.1));
    float n2 = snoise(vec2(uv.x * 2.0 - t * 0.12, uv.y * 1.5 + t * 0.08));
    float n3 = snoise(vec2(uv.x * 3.0 + t * 0.1, uv.y * 2.0 - t * 0.15));
    float n4 = snoise(vec2(uv.x * 0.8 - t * 0.08, uv.y * 0.5 + t * 0.12));
    
    float noise = n1 * 0.4 + n2 * 0.3 + n3 * 0.2 + n4 * 0.1;
    noise = (noise + 1.0) * 0.5;
    
    // Flowing wave effect
    float wave1 = sin(uv.x * 3.0 + t * 0.8 + noise * 2.0) * 0.15;
    float wave2 = sin(uv.x * 5.0 - t * 0.6) * 0.1;
    float wave3 = cos(uv.x * 2.0 + t * 0.4) * 0.1;
    
    float flow = uv.y + wave1 + wave2 + wave3 + noise * uAmplitude * 0.5;
    float factor = smoothstep(0.0, 1.0, flow * 0.8);
    factor = clamp(factor, 0.0, 1.0);
    
    // Color mixing
    vec3 c1 = uColorStops[0];
    vec3 c2 = uColorStops[1];
    vec3 c3 = uColorStops[2];
    
    vec3 color;
    if (factor < 0.5) {
        color = mix(c1, c2, factor * 2.0);
    } else {
        color = mix(c2, c3, (factor - 0.5) * 2.0);
    }
    
    // Pulsing brightness
    float pulse = 1.0 + sin(t * 0.5) * 0.1 + sin(t * 0.8 + uv.x * 2.0) * 0.05;
    color *= pulse;

    // Alpha with movement
    float alphaNoise = snoise(vec2(uv.x * 2.0 + t * 0.2, uv.y * 1.5 - t * 0.1));
    float alpha = smoothstep(0.0, 0.4, uv.y + alphaNoise * 0.2);
    alpha *= smoothstep(1.0, 0.6, uv.y - alphaNoise * 0.1);
    alpha *= uBlend;
    
    gl_FragColor = vec4(color, alpha);
}
`;

interface AuroraProps {
  colorStops?: string[];
  amplitude?: number;
  blend?: number;
  speed?: number;
}

function hexToRgb(hex: string): [number, number, number] {
  const result = /^#?([a-f\d]{2})([a-f\d]{2})([a-f\d]{2})$/i.exec(hex);
  return result
    ? [
        parseInt(result[1], 16) / 255,
        parseInt(result[2], 16) / 255,
        parseInt(result[3], 16) / 255,
      ]
    : [0, 0, 0];
}

const Aurora: React.FC<AuroraProps> = ({
  colorStops = ["#1e3a5f", "#3d5a80", "#293241"],
  amplitude = 0.5,
  blend = 0.8,
  speed = 1.0,
}) => {
  const containerRef = useRef<HTMLDivElement | null>(null);
  const rendererRef = useRef<any>(null);
  const programRef = useRef<any>(null);
  const animationRef = useRef<number>(0);
  const startTimeRef = useRef<number>(0);

  useEffect(() => {
    if (!containerRef.current || typeof window === "undefined") return;

    let mounted = true;

    const init = async () => {
      try {
        const OGL = await import("ogl");
        if (!mounted || !containerRef.current) return;

        const container = containerRef.current;

        const renderer = new OGL.Renderer({
          alpha: true,
          antialias: true,
        });
        rendererRef.current = renderer;

        const gl = renderer.gl;
        const canvas = gl.canvas as HTMLCanvasElement;
        canvas.style.cssText = "position:absolute;top:0;left:0;width:100%;height:100%;";
        container.appendChild(canvas);

        const geometry = new OGL.Triangle(gl);
        const colors = colorStops.flatMap(hexToRgb);

        const program = new OGL.Program(gl, {
          vertex: vertexShader,
          fragment: fragmentShader,
          uniforms: {
            uTime: { value: 0 },
            uAmplitude: { value: amplitude },
            uColorStops: { value: colors },
            uResolution: { value: new OGL.Vec2(1, 1) },
            uBlend: { value: blend },
          },
          transparent: true,
          depthTest: false,
          depthWrite: false,
        });
        programRef.current = program;

        const mesh = new OGL.Mesh(gl, { geometry, program });

        const resize = () => {
          const w = container.clientWidth;
          const h = container.clientHeight;
          if (w > 0 && h > 0) {
            renderer.setSize(w, h);
            program.uniforms.uResolution.value.set(w, h);
          }
        };

        window.addEventListener("resize", resize);
        resize();

        startTimeRef.current = performance.now();

        const animate = () => {
          if (!mounted) return;
          
          const elapsed = (performance.now() - startTimeRef.current) / 1000;
          program.uniforms.uTime.value = elapsed * speed;
          
          renderer.render({ scene: mesh });
          animationRef.current = requestAnimationFrame(animate);
        };

        animate();

        return () => {
          window.removeEventListener("resize", resize);
        };
      } catch (e) {
        console.error("Aurora error:", e);
      }
    };

    init();

    return () => {
      mounted = false;
      if (animationRef.current) {
        cancelAnimationFrame(animationRef.current);
      }
      if (rendererRef.current && containerRef.current) {
        const canvas = containerRef.current.querySelector("canvas");
        if (canvas) {
          containerRef.current.removeChild(canvas);
        }
      }
    };
  }, [colorStops, amplitude, blend, speed]);

  return (
    <div
      ref={containerRef}
      style={{
        position: "absolute",
        inset: 0,
        overflow: "hidden",
      }}
    />
  );
};

export default Aurora;
