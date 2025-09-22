import Image from 'next/image';
import { LocationButtons } from './LocationButtons';

export interface Message {
    id: number;
    type: 'user' | 'ai';
    content: string;
    timestamp: Date;
}

interface ChatMessageProps {
    message: Message;
}

export function ChatMessage({ message }: ChatMessageProps) {
    return (
        <div
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
                <p className="text-sm whitespace-pre-wrap">{message.content}</p>
                {/* 장소 정보 네비게이션 버튼 - AI 메시지에만 표시 */}
                {message.type === 'ai' && (
                    <LocationButtons message={message.content} />
                )}
            </div>
        </div>
    );
}
