// Conventional Commits validation config, used by the "Conventional Commits"
// GitHub Actions workflow (wagoid/commitlint-github-action). There is no need
// to install Node.js or commitlint locally — validation happens in CI.
export default {
  extends: ['@commitlint/config-conventional'],
};
