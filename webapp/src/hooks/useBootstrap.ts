import { useEffect } from "react";

import { useAuthStore } from "../features/auth/store";
import { apiFetch } from "../lib/api";
import { getTelegramWebApp } from "../lib/telegram";

export function useBootstrap() {
  const token = useAuthStore((state) => state.token);
  const setAuth = useAuthStore((state) => state.setAuth);
  const setBootstrapping = useAuthStore((state) => state.setBootstrapping);
  const setError = useAuthStore((state) => state.setError);
  const clearAuth = useAuthStore((state) => state.clearAuth);

  useEffect(() => {
    const webApp = getTelegramWebApp();
    webApp?.ready();
    webApp?.expand();

    const initData = webApp?.initData;
    if (initData) {
      apiFetch<{ token: string; user: any; balance: any }>("/api/twa/auth/validate", undefined, {
        method: "POST",
        body: JSON.stringify({ init_data_raw: initData }),
      })
        .then((data) => setAuth(data))
        .catch((error: Error) => setError(error.message || "Не удалось авторизоваться в Mini App."));
      return;
    }

    if (token) {
      Promise.all([apiFetch<any>("/api/me", token), apiFetch<any>("/api/me/balance", token)])
        .then(([user, balance]) => setAuth({ token, user, balance }))
        .catch(() => {
          clearAuth();
          setError("Сессия Mini App истекла. Откройте приложение снова из Telegram.");
        });
      return;
    }

    setBootstrapping(false);
    setError("Mini App открыт без Telegram-сессии. Откройте его через кнопку в боте.");
  }, [clearAuth, setAuth, setBootstrapping, setError, token]);

  useEffect(() => {
    if (!token) {
      return;
    }

    let isRefreshing = false;

    const refresh = async () => {
      if (isRefreshing) {
        return;
      }
      isRefreshing = true;
      try {
        const [user, balance] = await Promise.all([apiFetch<any>("/api/me", token), apiFetch<any>("/api/me/balance", token)]);
        setAuth({ token, user, balance });
      } catch {
        clearAuth();
        setError("Сессия Mini App истекла. Откройте приложение снова из Telegram.");
      } finally {
        isRefreshing = false;
      }
    };

    const handleVisibility = () => {
      if (document.visibilityState === "visible") {
        void refresh();
      }
    };

    window.addEventListener("focus", handleVisibility);
    document.addEventListener("visibilitychange", handleVisibility);
    const intervalId = window.setInterval(() => {
      if (document.visibilityState === "visible") {
        void refresh();
      }
    }, 30000);

    return () => {
      window.removeEventListener("focus", handleVisibility);
      document.removeEventListener("visibilitychange", handleVisibility);
      window.clearInterval(intervalId);
    };
  }, [clearAuth, setAuth, setError, token]);
}
