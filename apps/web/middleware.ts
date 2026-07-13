import { NextResponse, type NextRequest } from "next/server";

export function middleware(request: NextRequest) {
  const token = request.cookies.get("adproof_token")?.value;

  // /auth/callback handles Supabase OAuth redirect and doesn't need auth
  // The SessionProvider will set the cookie after syncing with the worker
  if (request.nextUrl.pathname === "/auth/callback") {
    return NextResponse.next();
  }

  if (!token) {
    const loginUrl = new URL("/login", request.url);
    loginUrl.searchParams.set("callbackUrl", request.nextUrl.pathname);
    return NextResponse.redirect(loginUrl);
  }

  return NextResponse.next();
}

export const config = {
  matcher: ["/dashboard/:path*", "/brief/:path*", "/library/:path*", "/run/:path*"],
};
