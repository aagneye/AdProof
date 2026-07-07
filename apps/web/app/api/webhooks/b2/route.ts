import { NextRequest, NextResponse } from "next/server";

export async function POST(request: NextRequest) {
  const body = await request.json();
  // TODO: handle B2 event notification on variants/*/final.mp4 PUT
  // Update brief status, broadcast SSE
  console.log("B2 webhook received:", body);
  return NextResponse.json({ received: true });
}
