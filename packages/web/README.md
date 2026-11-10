# ai-app-platform: the web platform

The platform code every React web interface built from the AI application template needs, as one npm package, `@supermanchris4/ai-app-platform-web`. It implements the browser's side of the template's `40-ui.md` and `50-auth.md`, and imports nothing of any application's.

| Export                                                                  | What it provides                                                                                                                                                                                                                                   |
| ----------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `platformFetch`, `apiRequest`, `ApiError`, `setCsrfToken`               | The API client: a correlation ID on every request, the CSRF token on state-changing ones, the session cookie, revalidated responses, and sign-in again on a 401. `platformFetch` is the `fetch` to give a generated client such as `openapi-fetch` |
| `SessionProvider`, `useSession`, `SessionContext`, `signOut`, `Session` | Reads who is signed in when the app starts, and ends the session                                                                                                                                                                                   |
| `RequireRoles`                                                          | Shows content only to a person holding one of the roles; the API still decides what is allowed                                                                                                                                                     |
| `navigation`, `signIn`, `signInAddress`                                 | Full-page navigation to the API's sign-in endpoint. Tests replace `navigation.assign`                                                                                                                                                              |
| `ErrorNotice`                                                           | An error with the API's message and the correlation ID for support                                                                                                                                                                                 |
| `EnvironmentBanner`, `loadConfig`, `AppConfig`                          | The environment's name on every page except production, from the deployed `config.json`                                                                                                                                                            |
| `LocalDate`                                                             | A UTC timestamp in the browser's time zone and locale                                                                                                                                                                                              |
| `NavLink`                                                               | A sidebar link, highlighted for the current section                                                                                                                                                                                                |

React and React Router are peer dependencies: the application provides them, so both share one copy.

## Installing it

The package is in GitHub Packages, whose npm registry needs a token to read even a public package. No token is ever written into the application's repository.

1. In the application's web folder, an `.npmrc` that says where the scope's packages come from:

   ```ini
   @supermanchris4:registry=https://npm.pkg.github.com
   ```

2. Then `npm install @supermanchris4/ai-app-platform-web@0.1.0 react react-router`.

**On a developer's machine,** sign in to the registry once with a personal access token (classic) that has only the `read:packages` scope. npm stores it in the user's own `~/.npmrc`, outside the repository:

```bash
npm login --scope=@supermanchris4 --auth-type=legacy --registry=https://npm.pkg.github.com
```

**In the application's pipelines,** the run's own token reads the package. The job needs `packages: read`, and `actions/setup-node` writes the registry setting:

```yaml
permissions:
  contents: read
  packages: read
steps:
  - uses: actions/setup-node@... # pinned
    with:
      node-version-file: apps/web/.nvmrc
      registry-url: https://npm.pkg.github.com
      scope: "@supermanchris4"
  - run: npm ci
    env:
      NODE_AUTH_TOKEN: ${{ github.token }}
```

If the package is private, the application's repository also needs read access in the package's settings, under "Manage Actions access". To upgrade, install the new version and read the [changelog](CHANGELOG.md).

## Using it

An application:

1. Wraps its routes in `SessionProvider`, and shows `EnvironmentBanner` with the environment from `loadConfig()`.
2. Calls the API through `platformFetch` or `apiRequest`, never `fetch` directly.
3. Styles the components with Tailwind CSS. The components use the template's theme colours (`accent`, `destructive`, `muted-foreground`), and the application's Tailwind `content` setting includes `node_modules/@supermanchris4/ai-app-platform-web/dist/**/*.js`, so their classes are generated.

## Developing

```bash
npm ci
npm run lint && npm run typecheck && npm test && npm run build
```

`npm test` runs the Vitest tests with coverage, which must reach 80%. `npm run build` writes the library and its type declarations to `dist/`.
