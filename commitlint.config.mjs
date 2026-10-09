// Conventional Commits validation config, used by the "Conventional Commits"
// GitHub Actions workflow, which runs commitlint under Node on pushes to main.
// There is no need to install Node.js or commitlint locally — validation
// happens in CI.
export default {
  extends: ['@commitlint/config-conventional'],
  rules: {
    // Squash commits carry the PR title only, but Release Please's own commits
    // have long changelog lines in their bodies, so don't fail on body length.
    'body-max-line-length': [0, 'always', 100],
    'footer-max-line-length': [0, 'always', 100],
  },
};
