// Conventional Commits validation config, used by the "Conventional Commits"
// GitHub Actions workflow (wagoid/commitlint-github-action). There is no need
// to install Node.js or commitlint locally — validation happens in CI.
export default {
  extends: ['@commitlint/config-conventional'],
  rules: {
    // PRs are squash-merged with the PR body as the commit body; PR bodies
    // routinely exceed 100-character lines, so don't fail on body length.
    'body-max-line-length': [0, 'always', 100],
    'footer-max-line-length': [0, 'always', 100],
  },
};
