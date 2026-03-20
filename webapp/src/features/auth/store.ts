import { create } from "zustand";

type User = {
  id: string;
  telegram_id: number;
  first_name: string;
  username?: string | null;
  is_admin: boolean;
  referral_code: string;
};

type Balance = {
  available_requests: number;
  reserved_requests: number;
};

type AuthPayload = {
  token: string;
  user: User;
  balance: Balance;
};

type AuthState = {
  token: string | null;
  user: User | null;
  balance: Balance | null;
  isBootstrapping: boolean;
  error: string | null;
  setAuth: (payload: AuthPayload) => void;
  setBalance: (balance: Balance) => void;
  setBootstrapping: (value: boolean) => void;
  setError: (message: string | null) => void;
  clearAuth: () => void;
};

const STORAGE_KEY = "proofbot-auth";

function readStoredAuth(): Partial<AuthPayload> {
  if (typeof window === "undefined") {
    return {};
  }
  try {
    const raw = window.localStorage.getItem(STORAGE_KEY);
    return raw ? JSON.parse(raw) : {};
  } catch {
    return {};
  }
}

function writeStoredAuth(payload: AuthPayload | null) {
  if (typeof window === "undefined") {
    return;
  }
  if (!payload) {
    window.localStorage.removeItem(STORAGE_KEY);
    return;
  }
  window.localStorage.setItem(STORAGE_KEY, JSON.stringify(payload));
}

const stored = readStoredAuth();

export const useAuthStore = create<AuthState>((set) => ({
  token: stored.token ?? null,
  user: stored.user ?? null,
  balance: stored.balance ?? null,
  isBootstrapping: true,
  error: null,
  setAuth: (payload) => {
    writeStoredAuth(payload);
    set({ ...payload, error: null, isBootstrapping: false });
  },
  setBalance: (balance) =>
    set((state) => {
      const payload =
        state.token && state.user
          ? { token: state.token, user: state.user, balance }
          : null;
      writeStoredAuth(payload);
      return { balance };
    }),
  setBootstrapping: (value) => set({ isBootstrapping: value }),
  setError: (message) => set({ error: message, isBootstrapping: false }),
  clearAuth: () => {
    writeStoredAuth(null);
    set({ token: null, user: null, balance: null, error: null, isBootstrapping: false });
  },
}));
