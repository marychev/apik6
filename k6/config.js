import http from "k6/http";

export const BASE_URL = __ENV.BASE_URL || "http://localhost:8000";

export const headers = {
  "Content-Type": "application/json",
};

let counter = 0;

export function createUser() {
  counter++;
  const payload = JSON.stringify({
    name: `user_${counter}_${Date.now()}`,
    email: `user_${counter}_${Date.now()}@test.com`,
  });

  return http.post(`${BASE_URL}/users`, payload, { headers });
}

export function resetUsers() {
  http.post(`${BASE_URL}/users/reset`, null, { headers });
}
