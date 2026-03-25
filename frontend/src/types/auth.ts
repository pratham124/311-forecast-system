export type AuthenticatedUser = {
  userAccountId: string;
  email: string;
  roles: string[];
};

export type AuthResponse = {
  accessToken: string;
  tokenType: 'bearer';
  user: AuthenticatedUser;
};

export type AuthSession = {
  accessToken: string;
  user: AuthenticatedUser;
};
