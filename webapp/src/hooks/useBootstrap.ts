import { useEffect } from "react";
import { apiFetch } from "../lib/api";
import { getTelegramWebApp } from "../lib/telegram";
import { useAuthStore } from "../features/auth/store";

export function useBootstrap() {
  const setAuth = useAuthStore((state) => state.setAuth);

  useEffect(() => {
    const webApp = getTelegramWebApp();
    webApp?.ready();
    webApp?.expand();
    const initData = webApp?.initData;
    if (!initData) {
      return;
    }
    apiFetch<{ token: string; user: any; balance: any }>("/api/twa/auth/validate", undefined, {
      method: "POST",
      body: JSON.stringify({ init_data_raw: initData }),
    })
      .then((data) => setAuth(data))
      .catch(() => undefined);
  }, [setAuth]);
}

