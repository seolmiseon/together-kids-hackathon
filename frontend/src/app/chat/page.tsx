'use client';

import { useState, useEffect, useRef } from 'react';
import { useRouter } from 'next/navigation';
import Image from 'next/image';
import { getAuth } from 'firebase/auth';
import { useUserStore } from '@/store/userStore';
import CloseButton from '@/components/ui/CloseButton';

interface Message {
    id: string;
    type: 'ai' | 'user';
    content: string;
    timestamp: Date;
}

export default function ChatPage() {
    const router = useRouter();
    const { isLoggedIn, user } = useUserStore();
    const [messages, setMessages] = useState<Message[]>([
        {
            id: '1',
            type: 'ai',
            content: '안녕하세요! 함께키즈 AI 도우미입니다. 육아 고민이나 궁금한 점이 있으시면 언제든 말씀해주세요! 😊',
            timestamp: new Date(),
        },
    ]);
    const [inputMessage, setInputMessage] = useState('');
    const [isAiResponding, setIsAiResponding] = useState(false);
    const messagesEndRef = useRef<HTMLDivElement>(null);

    // 자동 스크롤
    useEffect(() => {
        messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
    }, [messages]);

    // 로그인 체크
    useEffect(() => {
        if (!isLoggedIn) {
            router.push('/auth/login');
        }
    }, [isLoggedIn, router]);

    const sendMessage = async () => {
        if (!inputMessage.trim() || isAiResponding) return;

        const newMessage: Message = {
            id: Date.now().toString(),
            type: 'user',
            content: inputMessage,
            timestamp: new Date(),
        };
        
        setMessages(prev => [...prev, newMessage]);
        const userMessage = inputMessage;
        setInputMessage('');
        setIsAiResponding(true);

        try {
            const auth = getAuth();
            const currentUser = auth.currentUser;
            if (!currentUser) throw new Error('로그인이 필요합니다.');
            
            const token = await currentUser.getIdToken();
            const apiUrl = process.env.NEXT_PUBLIC_API_URL;
            
            const params = new URLSearchParams({
                message: userMessage,
                mode: 'auto',
            });
            
            const response = await fetch(`${apiUrl}/ai/chat?${params.toString()}`, {
                method: 'POST',
                headers: {
                    Authorization: `Bearer ${token}`,
                },
            });

            if (!response.ok) throw new Error('AI 응답 실패');

            const aiData = await response.json();
            const aiResponse: Message = {
                id: (Date.now() + 1).toString(),
                type: 'ai',
                content: aiData.message || aiData.response || '응답을 처리할 수 없습니다.',
                timestamp: new Date(),
            };
            
            setMessages(prev => [...prev, aiResponse]);
        } catch (error) {
            console.error('AI 응답 오류:', error);
            const errorResponse: Message = {
                id: (Date.now() + 1).toString(),
                type: 'ai',
                content: '죄송합니다. 응답을 생성하는 중 오류가 발생했습니다.',
                timestamp: new Date(),
            };
            setMessages(prev => [...prev, errorResponse]);
        } finally {
            setIsAiResponding(false);
        }
    };

    if (!isLoggedIn) {
        return (
            <div className="flex items-center justify-center min-h-screen">
                <div className="animate-spin rounded-full h-32 w-32 border-b-2 border-blue-600 mx-auto"></div>
            </div>
        );
    }

    return (
        <div className="min-h-screen bg-gray-50 flex flex-col">
            {/* 헤더 */}
            <header className="bg-blue-600 text-white p-4 flex items-center justify-between">
                <div className="flex items-center space-x-3">
                    <Image
                        src="/images/logo/logosymbol.png"
                        alt="함께키즈"
                        width={32}
                        height={32}
                        className="w-8 h-8"
                    />
                    <div>
                        <h1 className="font-bold text-lg">함께키즈 AI 채팅</h1>
                        <p className="text-sm opacity-80">24시간 육아 도우미</p>
                    </div>
                </div>
                <CloseButton 
                    onClick={() => router.push('/dashboard')}
                    variant="dark"
                    size="md"
                    ariaLabel="채팅 닫기"
                />
            </header>

            {/* 메시지 영역 */}
            <div className="flex-1 overflow-y-auto p-4 space-y-4">
                {messages.map((message) => (
                    <div
                        key={message.id}
                        className={`flex items-end gap-3 ${
                            message.type === 'user' ? 'justify-end' : 'justify-start'
                        }`}
                    >
                        {message.type === 'ai' && (
                            <Image
                                src="/images/logo/logosymbol.png"
                                alt="AI"
                                width={32}
                                height={32}
                                className="w-8 h-8 rounded-full"
                            />
                        )}
                        <div
                            className={`max-w-md px-4 py-3 rounded-2xl ${
                                message.type === 'user'
                                    ? 'bg-blue-600 text-white rounded-br-sm'
                                    : 'bg-white text-gray-800 rounded-bl-sm shadow-sm'
                            }`}
                        >
                            <p className="text-sm whitespace-pre-wrap">{message.content}</p>
                            <p className="text-xs opacity-70 mt-1">
                                {message.timestamp.toLocaleTimeString()}
                            </p>
                        </div>
                    </div>
                ))}
                {isAiResponding && (
                    <div className="flex items-end gap-3 justify-start">
                        <Image
                            src="/images/logo/logosymbol.png"
                            alt="AI"
                            width={32}
                            height={32}
                            className="w-8 h-8 rounded-full"
                        />
                        <div className="bg-white text-gray-800 rounded-2xl rounded-bl-sm shadow-sm px-4 py-3">
                            <p className="text-sm animate-pulse">답변을 생성하고 있어요...</p>
                        </div>
                    </div>
                )}
                <div ref={messagesEndRef} />
            </div>

            {/* 입력 영역 */}
            <div className="bg-white border-t p-4">
                <div className="flex space-x-3">
                    <input
                        type="text"
                        value={inputMessage}
                        onChange={(e) => setInputMessage(e.target.value)}
                        onKeyPress={(e) => e.key === 'Enter' && sendMessage()}
                        placeholder="메시지를 입력하세요..."
                        className="flex-1 px-4 py-3 border border-gray-300 rounded-full focus:outline-none focus:ring-2 focus:ring-blue-500"
                        disabled={isAiResponding}
                    />
                    <button
                        onClick={sendMessage}
                        className="bg-blue-600 hover:bg-blue-700 text-white px-6 py-3 rounded-full transition-colors disabled:bg-gray-300 disabled:cursor-not-allowed"
                        disabled={isAiResponding || !inputMessage.trim()}
                    >
                        전송
                    </button>
                </div>
            </div>
        </div>
    );
            }
       