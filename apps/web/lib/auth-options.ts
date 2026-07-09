import type { NextAuthOptions } from "next-auth";
import GoogleProvider from "next-auth/providers/google";
import { syncGoogleUser } from "./sync-user";

export const authOptions: NextAuthOptions = {
  providers: [
    GoogleProvider({
      clientId: process.env.GOOGLE_CLIENT_ID || "",
      clientSecret: process.env.GOOGLE_CLIENT_SECRET || "",
    }),
  ],
  pages: {
    signIn: "/login",
  },
  session: {
    strategy: "jwt",
  },
  callbacks: {
    async jwt({ token, account, profile }) {
      if (account?.provider === "google" && profile?.email) {
        const googleProfile = profile as {
          email?: string;
          name?: string;
          picture?: string;
          sub?: string;
        };
        const synced = await syncGoogleUser({
          email: googleProfile.email!,
          google_id: googleProfile.sub || account.providerAccountId,
          name: googleProfile.name,
          picture: googleProfile.picture,
        });
        token.accessToken = synced.access_token;
        token.userId = synced.user_id;
        token.email = synced.email;
        token.name = synced.name || googleProfile.name;
        token.picture = synced.avatar_url || googleProfile.picture;
      }
      return token;
    },
    async session({ session, token }) {
      if (token.accessToken) {
        session.accessToken = token.accessToken as string;
      }
      if (token.userId) {
        session.userId = token.userId as string;
      }
      if (session.user) {
        session.user.id = token.userId as string | undefined;
        session.user.email = token.email as string | undefined;
        session.user.name = token.name as string | undefined;
        session.user.image = token.picture as string | undefined;
      }
      return session;
    },
  },
  secret: process.env.NEXTAUTH_SECRET,
};
