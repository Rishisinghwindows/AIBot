const authFetch = async (url: string, options: RequestInit = {}, token?: string | null) => {
  // Prefer access_token (JWT from our backend) over firebase_id_token
  // access_token is what the backend API expects for authenticated requests
  const authToken = token ?? (typeof window !== 'undefined'
    ? (localStorage.getItem("access_token") || localStorage.getItem("firebase_id_token"))
    : null);

  if (authToken) {
    options.headers = {
      ...options.headers,
      Authorization: `Bearer ${authToken}`,
      "Content-Type": "application/json",
    };
  }

  const response = await fetch(url, options);

  if (response.status === 401) {
    console.error("Unauthorized access");
  }

  return response;
};

export default authFetch;
