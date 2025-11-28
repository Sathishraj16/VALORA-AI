declare module 'ogl' {
  export class Renderer {
    constructor(options?: {
      alpha?: boolean;
      premultipliedAlpha?: boolean;
      antialias?: boolean;
      depth?: boolean;
      stencil?: boolean;
      preserveDrawingBuffer?: boolean;
      powerPreference?: string;
      autoClear?: boolean;
      webgl?: number;
    });
    gl: WebGLRenderingContext & {
      canvas: HTMLCanvasElement;
    };
    setSize(width: number, height: number): void;
    render(options: { scene: Mesh | any }): void;
  }

  export class Program {
    constructor(
      gl: WebGLRenderingContext,
      options: {
        vertex: string;
        fragment: string;
        uniforms?: Record<string, { value: any }>;
        transparent?: boolean;
        cullFace?: boolean;
        frontFace?: number;
        depthTest?: boolean;
        depthWrite?: boolean;
        depthFunc?: number;
      }
    );
    uniforms: Record<string, { value: any }>;
  }

  export class Mesh {
    constructor(
      gl: WebGLRenderingContext,
      options: {
        geometry: Triangle | any;
        program: Program;
      }
    );
  }

  export class Triangle {
    constructor(gl: WebGLRenderingContext);
  }

  export class Vec2 {
    constructor(x?: number, y?: number);
    set(x: number, y: number): this;
  }

  export class Color {
    constructor(color?: string | number | number[]);
    r: number;
    g: number;
    b: number;
  }
}
