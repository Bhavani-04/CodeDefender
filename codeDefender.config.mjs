import js from '@eslint/js';

export default [
  js.configs.recommended,
  {
    files: ['**/*.js'],
    rules: {
      'no-eval': 'error',
      'no-unused-vars': 'warn',
      'eqeqeq': 'error',
      'no-console': 'warn'
    }
  }
];