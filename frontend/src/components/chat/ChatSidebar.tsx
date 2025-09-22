'use client';
import { useState, useEffect, useRef, Dispatch, SetStateAction } from 'react';
import Image from 'next/image';
import { useUserStore } from '@/store/userStore';
import CloseButton from '@/components/ui/CloseButton';
import { ChatMessage } from './ChatMessage';
import type { Message } from './ChatMessage';
import { ChatInput } from './ChatInput';
import { chatService } from '@/lib/chatService';
// --- 타입 정의 ---

interface ChatSidebarProps {
    isOpen: boolean;
    setIsOpen: Dispatch<SetStateAction<boolean>>;
}

export default function ChatSidebar({
    isOpen,
    setIsOpen,
}: ChatSidebarProps) {
    const [messages, setMessages] = useState<Message[]>([]);
    const [inputMessage, setInputMessage] = useState('');
    const [isAiResponding, setIsAiResponding] = useState(false);
    const [urgency, setUrgency] = useState<'low' | 'medium' | 'high'>('low');

    const { user, isLoggedIn } = useUserStore();

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

        try {
            // ChatService를 사용해 메시지 전송
            const aiData = await chatService.sendMessage(userMessage);
            const processedResponse = chatService.processAiResponse(aiData);
            
            const aiResponse: Message = {
                id: Date.now() + 1,
                type: 'ai',
                content: processedResponse.content,
                timestamp: new Date(),
            };
            
            setMessages((prev) => [...prev, aiResponse]);

            // 장소 정보가 있으면 지도에 표시
            if (processedResponse.places) {
                chatService.handleMapDisplay(processedResponse.places);
            }

            // 긴급도 설정
            if (processedResponse.urgency) {
                setUrgency(processedResponse.urgency);
            }
        } catch (error) {
            const errorMessage = chatService.createErrorMessage(error as Error);
            setMessages((prev) => [...prev, errorMessage]);
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
                    <CloseButton 
                        onClick={() => setIsOpen(false)}
                        variant="dark"
                        size="md"
                        ariaLabel="챗봇 닫기"
                    />
                </div>

                <div className="flex-1 overflow-y-auto p-4 space-y-4 bg-gray-50">
                    {messages.map((message) => (
                        <ChatMessage key={message.id} message={message} />
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

                <ChatInput
                    inputMessage={inputMessage}
                    setInputMessage={setInputMessage}
                    onSendMessage={sendMessage}
                    isAiResponding={isAiResponding}
                    isLoggedIn={isLoggedIn}
                />
            </div>
        </>
    );
}
