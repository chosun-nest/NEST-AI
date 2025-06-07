'use client'

import { useTheme } from "next-themes"
import { useState, CSSProperties } from "react";
import { MemoizedReactMarkdown } from "@/components/shared/Markdown";
import ScaleLoader from "react-spinners/ScaleLoader";

type Chat = {
    role: "user" | "assistant";
    content: string;
}

const override: CSSProperties = {
    display: "block",
    margin: "0 auto",
    height: "20px",
};

export default function Home() {
    const { theme, setTheme } = useTheme();
    const [question, setQuestion] = useState("");
    const [messages, setMessages] = useState<Chat[]>([]);
    const [loading, setLoading] = useState(false);
    const [color] = useState("#ffffff");

    function handleQuestion(e: React.ChangeEvent<HTMLInputElement>) {
        setQuestion(e.target.value);
    }

    function postChatAPI() {
        setLoading(true);

        (async () => {
            const response = await fetch("/api/chat", {
                method: "POST",
                body: JSON.stringify({
                    messages: [
                        ...messages,
                        {
                            role: 'user',
                            content: question,
                        }
                    ],
                }),
            });

            const reader = response.body?.getReader();
            const decoder = new TextDecoder();
            let content = "";
            if (!reader) return;

            while (true) {
                setQuestion("");
                setLoading(false);

                const { done, value } = await reader.read();

                if (done) break;

                const decodedValue = decoder.decode(value);
                content += decodedValue;

                setMessages([
                    ...messages,
                    { role: 'user', content: question },
                    { role: 'assistant', content: content }
                ]);
            }
        })()
    }

    return (
        <div className="py-3 px-5" style={{ fontFamily: "'Gowun Dodum', sans-serif" }}>
            <div className="flex py-4 w-full">
                <h3 className="text-2xl flex-grow">챗봇 위닛(WitN)에게 질문해보세요!</h3>
                <button
                    className="bg-gray-800 dark:bg-gray-100 dark:text-gray-800 px-3 py-2 text-sm font-semibold text-white shadow-sm rounded-md"
                    onClick={() => setTheme(theme === "dark" ? "light" : "dark")}
                >
                    {theme === "dark" ? "🌞 light모드로 변환" : "🌚 dark모드로 변환"}
                </button>
            </div>

            <div className="flex w-full">
                <input
                    className="px-3 py-2 text-sm shadow-sm rounded-md flex-grow ring-gray-300 dark:ring-gray-900 ring-1 ring-inset disabled:cursor-not-allowed"
                    placeholder="질문을 입력해주세요."
                    onChange={handleQuestion}
                    value={question}
                    disabled={loading}
                />
                <button
                    className="w-20 mx-1 bg-indigo-600 px-3 py-2 text-sm font-semibold text-white shadow-sm rounded-md disabled:bg-gray-300 dark:disabled:bg-gray-700 disabled:cursor-not-allowed"
                    onClick={postChatAPI}
                    disabled={!question || loading}
                >
                    <ScaleLoader
                        color={color}
                        loading={loading}
                        cssOverride={override}
                        height={15}
                        aria-label="Loading Spinner"
                    />
                    {!loading && "질문하기"}
                </button>
            </div>

            <div className="my-3 flex flex-col space-y-2">
                {messages.map((message, index) => {
                    const isUser = message.role === "user";
                    const displayName = isUser ? "me" : "위닛";
                    const bgColor = isUser ? "#e0f7ff" : "#007acc";
                    const textColor = isUser ? "#000000" : "#ffffff";
                    return (
                        <div key={index} className="flex border-t border-gray-200 dark:border-gray-700 py-3">
                            <p className="w-1/6 py-2 px-3 font-semibold">{displayName}</p>
                            <div
                                className="w-5/6 px-4 py-3 rounded-2xl shadow-md"
                                style={{
                                    backgroundColor: bgColor,
                                    color: textColor,
                                    whiteSpace: "pre-wrap"
                                }}
                            >
                                <MemoizedReactMarkdown key={index}>{message.content}</MemoizedReactMarkdown>
                            </div>
                        </div>
                    );
                })}
            </div>
        </div>
    );
}
