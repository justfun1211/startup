declare global {
  interface Window {
    Telegram?: {
      WebApp?: {
        ready(): void;
        expand(): void;
        initData: string;
        initDataUnsafe?: { start_param?: string };
        themeParams?: Record<string, string>;
        openTelegramLink(url: string): void;
      };
    };
  }
}

export function getTelegramWebApp() {
  return window.Telegram?.WebApp;
}

