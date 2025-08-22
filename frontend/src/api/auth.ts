import api from "./client";

export type LoginResponse = {
  status?: string;
  token: string;
  user?: any;
  message?: string;
};

export async function login(identifier: string, password: string): Promise<LoginResponse> {
  const payload = identifier.includes("@")
    ? { email: identifier, password }
    : { documento: identifier, password };
  const { data } = await api.post("/users/login", payload);
  return data;
}
