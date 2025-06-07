import { OpenAIStream, StreamingTextResponse } from "ai";
import { NextRequest } from "next/server";
import OpenAI from "openai";

const openai = new OpenAI({
  apiKey: process.env.OPENAI_API_KEY,
});

export async function GET() {
  return new Response(`Hello OPEN AI! your key is: ${openai.apiKey}`);
}

export async function POST(req: NextRequest) {

  const { messages } = await req.json();
  const response = await openai.chat.completions.create({
    model: "gpt-4o-mini",
    stream: true,
    temperature: 0.7,
    messages,
  });
  const stream = OpenAIStream(response);
  return new StreamingTextResponse(stream);
}