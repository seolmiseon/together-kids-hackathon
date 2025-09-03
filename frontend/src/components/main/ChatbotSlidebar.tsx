'use client';
import { useState, Dispatch, SetStateAction, useEffect, useRef } from 'react';
import Image from 'next/image';
import { getAuth } from 'firebase/auth';
import { useUserStore } from '@/store/userStore';
// --- 타입 정의 ---
interface Message {
    id: number;
    type: 'ai' | 'user';
    content: string;
    timestamp: Date;
}

interface ChatbotSidebarProps {
    isOpen: boolean;
    setIsOpen: Dispatch<SetStateAction<boolean>>;
}

export default function ChatbotSidebar({
    isOpen,
    setIsOpen,
}: ChatbotSidebarProps) {
    const [messages, setMessages] = useState<Message[]>([
        {
            id: 1,
            type: 'ai',
            content:
                '안녕하세요! 함께 키즈 AI 도우미입니다. 등하원 일정 조율이나 궁금한 점이 있으시면 언제든 말씀해주세요! 😊',
            timestamp: new Date(),
        },
    ]);
    const [inputMessage, setInputMessage] = useState('');
    const [isAiResponding, setIsAiResponding] = useState(false);
    const [urgency, setUrgency] = useState<'low' | 'medium' | 'high'>('low');

    const { isLoggedIn } = useUserStore();

    const messagesEndRef = useRef<HTMLDivElement>(null);
    useEffect(() => {
        messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
    }, [messages]);

    const sendMessage = async () => {
        if (!inputMessage.trim() || isAiResponding) return;

        const newMessage: Message = {
            id: Date.now(),
            type: 'user',
            content: inputMessage,
            timestamp: new Date(),
        };
        setMessages((prev) => [...prev, newMessage]);
        const userMessage = inputMessage;
        setInputMessage('');
        setIsAiResponding(true);
        setUrgency('low');

        const apiUrl = process.env.NEXT_PUBLIC_API_URL;
        try {
            const auth = getAuth();
            const currentUser = auth.currentUser;
            if (!currentUser) {
                throw new Error('로그인이 필요합니다.');
            }
            const token = await currentUser.getIdToken();

            const params = new URLSearchParams({
                message: userMessage,
                mode: 'auto',
            });
            const requestUrl = `${apiUrl}/ai/chat?${params.toString()}`;

            const response = await fetch(requestUrl, {
                method: 'POST',
                headers: {
                    Authorization: `Bearer ${token}`,
                },
            });

            if (!response.ok) throw new Error('AI 응답 실패');

            const aiData = await response.json();
            const aiContent =
                aiData.message ||
                aiData.response ||
                aiData.coordination_result ||
                '응답을 처리할 수 없습니다.';
            const aiResponse: Message = {
                id: Date.now() + 1,
                type: 'ai',
                content: aiContent,
                timestamp: new Date(),
            };
            setMessages((prev) => [...prev, aiResponse]);

            if (aiData.urgency) {
                setUrgency(aiData.urgency);
            }
        } catch (error) {
            console.error(error);
            const errorResponse: Message = {
                id: Date.now() + 1,
                type: 'ai',
                content: '죄송해요, 지금은 답변을 드릴 수 없어요.',
                timestamp: new Date(),
            };
            setMessages((prev) => [...prev, errorResponse]);
        } finally {
            setIsAiResponding(false);
        }
    };

    const urgencyClasses = {
        low: { header: 'bg-blue-600', border: 'border-transparent' },
        medium: { header: 'bg-yellow-500', border: 'border-yellow-500' },
        high: { header: 'bg-red-600', border: 'border-red-600' },
    };

    return (
        <>
            {!isOpen && (
                // [모바일 최적화] 모바일에서는 버튼 위치를 조금 더 안쪽으로 조정합니다.
                <button
                    onClick={() => setIsOpen(true)}
                    className="fixed right-4 bottom-4 sm:right-6 sm:bottom-6 bg-blue-600 hover:bg-blue-700 text-white p-4 rounded-full shadow-lg transition-all duration-300 z-50 animate-bounce"
                    aria-label="AI 도우미 열기"
                >
                    <Image
                        src="/images/logo/logosymbol.png"
                        alt="함께키즈 AI"
                        width={32}
                        height={32}
                    />
                </button>
            )}

            {/* [모바일 최적화] 모바일에서는 화면 전체 너비를 사용하고, 데스크탑에서는 최대 너비를 지정합니다. */}
            <div
                className={`fixed right-0 top-0 h-full w-full sm:w-96 sm:max-w-md bg-white shadow-2xl transform transition-transform duration-300 z-40 flex flex-col border-l-4 ${
                    isOpen ? 'translate-x-0' : 'translate-x-full'
                } ${urgencyClasses[urgency].border}`}
            >
                <div
                    className={`text-white p-4 flex items-center justify-between flex-shrink-0 transition-colors ${urgencyClasses[urgency].header}`}
                >
                    <div className="flex items-center space-x-3">
                        <Image
                            src="/images/logo/logosymbol.png"
                            alt="함께키즈"
                            width={32}
                            height={32}
                            className="w-8 h-8"
                        />
                        <div>
                            <h3 className="font-bold">함께키즈 AI</h3>
                            <p className="text-xs opacity-80">
                                일정조율 도우미
                            </p>
                        </div>
                    </div>
                    <button
                        onClick={() => setIsOpen(false)}
                        className="p-2 rounded-full hover:bg-white/20 transition-colors"
                    >
                        <svg
                            width="20"
                            height="20"
                            viewBox="0 0 24 24"
                            fill="none"
                        >
                            <path
                                d="M6 18L18 6M6 6l12 12"
                                stroke="currentColor"
                                strokeWidth="2"
                            />
                        </svg>
                    </button>
                </div>

                <div className="flex-1 overflow-y-auto p-4 space-y-4 bg-gray-50">
                    {messages.map((message) => (
                        <div
                            key={message.id}
                            className={`flex items-end gap-2 ${
                                message.type === 'user'
                                    ? 'justify-end'
                                    : 'justify-start'
                            }`}
                        >
                            {message.type === 'ai' && (
                                <Image
                                    src="/images/logo/logosymbol.png"
                                    alt="AI"
                                    width={24}
                                    height={24}
                                    className="w-6 h-6 rounded-full self-start"
                                />
                            )}
                            <div
                                className={`max-w-xs px-4 py-2 rounded-2xl ${
                                    message.type === 'user'
                                        ? 'bg-blue-600 text-white rounded-br-none'
                                        : 'bg-gray-200 text-gray-800 rounded-bl-none'
                                }`}
                            >
                                <p className="text-sm">{message.content}</p>
                            </div>
                        </div>
                    ))}
                    {isAiResponding && (
                        <div className="flex items-end gap-2 justify-start">
                            <Image
                                src="/images/logo/logosymbol.png"
                                alt="AI"
                                width={24}
                                height={24}
                                className="w-6 h-6 rounded-full self-start"
                            />
                            <div className="max-w-xs px-4 py-2 rounded-2xl bg-gray-200 text-gray-800 rounded-bl-none">
                                <p className="text-sm animate-pulse">
                                    답변을 생각하고 있어요...
                                </p>
                            </div>
                        </div>
                    )}
                    <div ref={messagesEndRef} />
                </div>

                <div className="p-4 border-t bg-white flex-shrink-0">
                    <div className="flex space-x-2">
                        <input
                            type="text"
                            value={inputMessage}
                            onChange={(e) => setInputMessage(e.target.value)}
                            onKeyPress={(e) =>
                                e.key === 'Enter' && sendMessage()
                            }
                            placeholder="메시지를 입력하세요..."
                            className="flex-1 px-4 py-2 border border-gray-300 rounded-full focus:outline-none focus:ring-2 focus:ring-blue-500 text-sm"
                            disabled={isAiResponding || !isLoggedIn}
                        />
                        <button
                            onClick={sendMessage}
                            className="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-full transition-colors disabled:bg-gray-300"
                            disabled={isAiResponding || !isLoggedIn}
                        >
                            전송
                        </button>
                    </div>
                </div>
            </div>
        </>
    );
}
