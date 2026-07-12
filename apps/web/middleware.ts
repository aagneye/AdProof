import { NextResponse, type NextRequest } from "next/server";

export function middleware(request: NextRequest) {
  const token = request.cookies.get("adproof_token")?.value;

  // Allow Supabase OAuth callbacks to pass through so SessionProvider
  // can exchange the token and set the cookie before we check auth.
  // Supabase appends #access_token or ?code= to the callback URL.
  const { searchParams } = request.nextUrl;
  const hasOAuthParams =
    searchParams.has("code") ||
    searchParams.has("access_token") ||
    request.nextUrl.hash?.includes("access_token");

  if (!token && !hasOAuthParams) {
    const loginUrl = new URL("/login", request.url);
    loginUrl.searchParams.set("callbackUrl", request.nextUrl.pathname);
    return NextResponse.redirect(loginUrl);
  }

  return NextResponse.next();
}

export const config = {
  matcher: ["/dashboard/:path*", "/brief/:path*", "/library/:path*", "/run/:path*"],
};
