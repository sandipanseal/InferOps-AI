const BROWSER_API_BASE =
  process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8000";

const SERVER_API_BASE =
  process.env.INTERNAL_API_BASE_URL || "http://backend:8000";

export function getApiBase() {
  // In the browser, `window` exists → use the public URL.
  // During SSR inside Docker, fall back to the internal service name.
  if (typeof window !== "undefined") return BROWSER_API_BASE;
  return SERVER_API_BASE;
}

export async function apiGet(path: string) {
  const base = getApiBase();

  const res = await fetch(`${base}${path}`, {
    method: "GET",
    cache: "no-store",
  });

  if (!res.ok) {
    const text = await res.text();
    throw new Error(`GET ${path} failed with status ${res.status}: ${text}`);
  }

  return res.json();
}

export async function apiPost(path: string, body: unknown) {
  const base = getApiBase();

  const res = await fetch(`${base}${path}`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(body),
  });

  if (!res.ok) {
    const text = await res.text();
    throw new Error(`POST ${path} failed with status ${res.status}: ${text}`);
  }

  return res.json();
}

export async function apiDelete<T>(path: string): Promise<T> {
  const base = getApiBase();

  const res = await fetch(`${base}${path}`, {
    method: "DELETE",
  });

  if (!res.ok) {
    let message = `${path} failed with status ${res.status}`;

    try {
      const errorBody = await res.json();
      message = errorBody.detail || message;
    } catch {
      // keep fallback message
    }

    throw new Error(message);
  }

  return res.json();
}

export async function apiUploadFile<T>(
  path: string,
  formData: FormData
): Promise<T> {
  const base = getApiBase();

  const res = await fetch(`${base}${path}`, {
    method: "POST",
    body: formData,
  });

  if (!res.ok) {
    let message = `${path} failed with status ${res.status}`;

    try {
      const errorBody = await res.json();
      message = errorBody.detail || message;
    } catch {
      // keep fallback message
    }

    throw new Error(message);
  }

  return res.json();
}