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

type AuthState = {
  token: string | null;
  user: User | null;
  balance: Balance | null;
  setAuth: (payload: { token: string; user: User; balance: Balance }) => void;
};

export const useAuthStore = create<AuthState>((set) => ({
  token: null,
  user: null,
  balance: null,
  setAuth: (payload) => set(payload),
}));

