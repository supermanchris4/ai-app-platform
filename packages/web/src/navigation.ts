/** Full-page navigation, kept in one object so tests can replace it. */
export const navigation = {
  assign(url: string): void {
    window.location.assign(url);
  },
  currentPath(): string {
    return window.location.pathname + window.location.search + window.location.hash;
  },
};

/** The API's sign-in address, returning to `returnTo` afterwards (specs/50-auth.md). */
export function signInAddress(returnTo: string): string {
  return `/api/auth/login?provider=internal&return_to=${encodeURIComponent(returnTo)}`;
}

/** Send the person to sign in, returning to where they are now. */
export function signIn(): void {
  navigation.assign(signInAddress(navigation.currentPath()));
}
