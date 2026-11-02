"use client";

import { useState, type FormEvent } from "react";

import { parseLoginInput, requestLoginToken } from "../../lib/auth";
import { saveSessionToken } from "../../lib/session";

const GENERIC_ERROR_MESSAGE = "Đăng nhập thất bại, vui lòng thử lại";

export interface LoginFormProps {
  onLoggedIn: (token: string) => void;
}

function describeError(error: unknown): string {
  return error instanceof Error ? error.message : GENERIC_ERROR_MESSAGE;
}

export function LoginForm({ onLoggedIn }: LoginFormProps) {
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const form = new FormData(event.currentTarget);
    const parsed = parseLoginInput({
      email: form.get("email"),
      password: form.get("password"),
    });
    if (!parsed.success) {
      setErrorMessage(parsed.error.issues[0]?.message ?? GENERIC_ERROR_MESSAGE);
      return;
    }

    setErrorMessage(null);
    setSubmitting(true);
    try {
      const token = await requestLoginToken(parsed.data);
      saveSessionToken(token);
      onLoggedIn(token);
    } catch (error: unknown) {
      setErrorMessage(describeError(error));
      setSubmitting(false);
    }
  }

  return (
    <form onSubmit={handleSubmit} noValidate className="flex flex-col gap-5">
      <label className="flex flex-col gap-1.5 text-sm text-neutral-700">
        Email
        <input
          type="email"
          name="email"
          autoComplete="username"
          required
          className="rounded border border-neutral-300 px-3 py-2 text-base text-neutral-900"
        />
      </label>
      <label className="flex flex-col gap-1.5 text-sm text-neutral-700">
        Mật khẩu
        <input
          type="password"
          name="password"
          autoComplete="current-password"
          required
          className="rounded border border-neutral-300 px-3 py-2 text-base text-neutral-900"
        />
      </label>
      {errorMessage !== null && (
        <p role="alert" className="text-sm text-red-700">
          {errorMessage}
        </p>
      )}
      <button
        type="submit"
        disabled={submitting}
        className="rounded bg-neutral-900 px-4 py-2.5 text-base font-semibold text-white disabled:opacity-60"
      >
        {submitting ? "Đang đăng nhập…" : "Đăng nhập"}
      </button>
    </form>
  );
}
