import Link from "next/link";
import { GoogleAuthButton } from "@/components/GoogleAuthButton";

export default function LoginPage() {
  return (
    <main className="auth-page">
      <div className="auth-card card">
        <h1>Log in</h1>
        <p>Sign in with Google through Supabase to access your briefs, runs, and provenance history.</p>
        <GoogleAuthButton label="Sign in with Google" callbackUrl="/dashboard" />
        <p className="auth-footer">
          New to AdProof? <Link href="/signup">Create an account</Link>
        </p>
      </div>
    </main>
  );
}
