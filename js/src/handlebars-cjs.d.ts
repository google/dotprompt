// Type declarations for handlebars/dist/cjs/handlebars.js
// This simply maps the CJS dist path to the official handlebars types
declare module 'handlebars/dist/cjs/handlebars.js' {
  // Import and re-export everything from the main handlebars package
  // This leverages the official types from node_modules/handlebars/types/index.d.ts
  export * from 'handlebars';
  import handlebars from 'handlebars';
  export default handlebars;
}