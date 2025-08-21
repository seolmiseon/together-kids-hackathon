'use client';
import { useState } from 'react';
import Image from 'next/image';

interface ChatbotSidebarProps {
    isOpen: boolean;
    setIsOpen: (open: boolean) => void;
}

export default function ChatbotSidebar({
    isOpen,
    setIsOpen,
}: ChatbotSidebarProps) {
    const [messages, setMessages] = useState([
        {
            id: 1,
            type: 'ai',
            content:
                '안녕하세요! 함께 키즈 AI 도우미입니다. 등하원 일정 조율이나 궁금한 점이 있으시면 언제든 말씀해주세요! 😊',
            timestamp: new Date(),
        },
    ]);
    const [inputMessage, setInputMessage] = useState('');

    const sendMessage = () => {
        if (!inputMessage.trim()) return;

        const newMessage = {
            id: Date.now(),
            type: 'user',
            content: inputMessage,
            timestamp: new Date(),
        };

        setMessages((prev) => [...prev, newMessage]);
        setInputMessage('');

        // AI 응답 시뮬레이션
        setTimeout(() => {
            const aiResponse = {
                id: Date.now() + 1,
                type: 'ai',
                content:
                    '네, 말씀해주신 내용을 확인했습니다. 어떤 도움이 필요하신지 자세히 알려주시면 최적의 해결책을 제안해드리겠습니다!',
                timestamp: new Date(),
            };
            setMessages((prev) => [...prev, aiResponse]);
        }, 1000);
    };

    return (
        <>
            {/* 챗봇 토글 버튼 */}
            {!isOpen && (
                <button
                    onClick={() => setIsOpen(true)}
                    className="fixed right-4 sm:right-6 bottom-4 sm:bottom-6 bg-blue-600 hover:bg-blue-700 text-white p-3 sm:p-4 rounded-full shadow-lg transition-all duration-300 z-50"
                >
                    <svg width="24" height="24" viewBox="0 0 24 24" fill="none">
                        <path
                            d="M12 2C6.48 2 2 6.48 2 12c0 1.54.36 3.04 1.05 4.35L2 22l5.65-1.05C9.96 21.64 11.46 22 13 22h7c1.1 0 2-.9 2-2V12c0-5.52-4.48-10-10-10z"
                            stroke="currentColor"
                            strokeWidth="2"
                        />
                    </svg>
                </button>
            )}

            {/* 챗봇 사이드바 */}
            <div
                className={`fixed right-0 top-0 h-full w-full sm:w-96 bg-white shadow-2xl transform transition-transform duration-300 z-40 ${
                    isOpen ? 'translate-x-0' : 'translate-x-full'
                }`}
            >
                <div className="bg-blue-600 text-white p-4 flex items-center justify-between">
                    <div className="flex items-center space-x-3">
                        <Image
                            src="/images/logo/logosymbol.png"
                            alt="함께키즈"
                            className="w-8 h-8"
                            width={32}
                            height={32}
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
                        className="text-white hover:text-gray-200 transition-colors"
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
                {/* 메시지 영역 */}
                <div className="flex-1 overflow-y-auto p-4 space-y-4 h-[calc(100vh-140px)]">
                    {messages.map((message) => (
                        <div
                            key={message.id}
                            className={`flex ${
                                message.type === 'user'
                                    ? 'justify-end'
                                    : 'justify-start'
                            }`}
                        >
                            <div
                                className={`max-w-xs px-4 py-2 rounded-lg ${
                                    message.type === 'user'
                                        ? 'bg-blue-600 text-white'
                                        : 'bg-gray-100 text-gray-800'
                                }`}
                            >
                                <p className="text-sm">{message.content}</p>
                            </div>
                        </div>
                    ))}
                </div>

                {/* 입력 영역 */}
                <div className="p-4 border-t bg-gray-50">
                    <div className="flex space-x-2">
                        <input
                            type="text"
                            value={inputMessage}
                            onChange={(e) => setInputMessage(e.target.value)}
                            onKeyPress={(e) =>
                                e.key === 'Enter' && sendMessage()
                            }
                            placeholder="메시지를 입력하세요..."
                            className="flex-1 px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 text-sm"
                        />
                        <button
                            onClick={sendMessage}
                            className="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-lg transition-colors"
                        >
                            전송
                        </button>
                    </div>
                </div>
            </div>
        </>
    );
}
