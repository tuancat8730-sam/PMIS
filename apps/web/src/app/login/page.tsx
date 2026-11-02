"use client";

import { useRouter } from "next/navigation";

import { LoginForm } from "@/components/login/login-form";

export const COMMAND_CENTER_HREF = "/command-center";

export default function LoginPage() {
  const router = useRouter();

  return (
    <main className="mx-auto flex min-h-screen max-w-sm flex-col justify-center gap-8 px-6 py-16">
      <header className="flex flex-col gap-2">
        <p className="text-sm font-medium uppercase tracking-widest text-neutral-500">
          PMIS · Đầu tư công
        </p>
        <h1 className="text-3xl font-semibold text-neutral-900">Đăng nhập</h1>
      </header>
      <LoginForm onLoggedIn={() => router.replace(COMMAND_CENTER_HREF)} />
    </main>
  );
}
