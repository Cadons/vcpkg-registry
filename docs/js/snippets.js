import { REPO_URL } from "./config.js";

export function configSnippet(pkg) {
  return `{
  "default-registry": {
    "kind": "builtin",
    "baseline": "<your-vcpkg-baseline-sha>"
  },
  "registries": [
    {
      "kind": "git",
      "repository": "${REPO_URL}",
      "baseline": "<commit-sha-of-this-repo>",
      "packages": ["${pkg.name}"]
    }
  ]
}`;
}

export function depsSnippet(pkg) {
  return `{
  "dependencies": ["${pkg.name}"]
}`;
}
