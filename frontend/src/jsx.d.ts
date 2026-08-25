// Minimal JSX namespace declaration to satisfy the TS compiler in this scaffold
declare namespace JSX {
  type Element = any
  interface IntrinsicElements {
    [elemName: string]: any
  }
}
