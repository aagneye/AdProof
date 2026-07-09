import Link from "next/link";
import { GoogleAuthButton } from "@/components/GoogleAuthButton";

export default function SignupPage() {
  return (
    <main className="auth-page">
      <div className="auth-card card">
        <h1>Sign up</h1>
        <p>
          Create your AdProof account with Google. Your briefs and pipeline history stay private
          to your account.
        </p>
        <GoogleAuthButton label="Sign up with Google" callbackUrl="/dashboard" />
        <p className="auth-footer">
          Already have an account? <Link href="/login">Log in</Link>
        </p>
      </div>
    </main>
  );
}
