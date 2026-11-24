// UI-настройки в localStorage (как dd-theme): читаются синхронно при
// старте, меняются на вкладке «Настройки» и применяются сразу.
const K = "dd-ui-";

export function uiSetting<T>(key: string, def: T): T {
  try {
    const v = localStorage.getItem(K + key);
    return v === null ? def : (JSON.parse(v) as T);
  } catch {
    return def;
  }
}

export function setUiSetting(key: string, v: unknown) {
  localStorage.setItem(K + key, JSON.stringify(v));
}
