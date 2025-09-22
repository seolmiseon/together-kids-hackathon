interface ChatInputProps {
    inputMessage: string;
    setInputMessage: (message: string) => void;
    onSendMessage: () => void;
    isAiResponding: boolean;
    isLoggedIn: boolean;
}

export function ChatInput({
    inputMessage,
    setInputMessage,
    onSendMessage,
    isAiResponding,
    isLoggedIn,
}: ChatInputProps) {
    const handleKeyPress = (e: React.KeyboardEvent<HTMLInputElement>) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            onSendMessage();
        }
    };

    return (
        <div className="p-4 border-t bg-white flex-shrink-0">
            <div className="flex space-x-2">
                <input
                    type="text"
                    value={inputMessage}
                    onChange={(e) => setInputMessage(e.target.value)}
                    onKeyPress={handleKeyPress}
                    placeholder="메시지를 입력하세요..."
                    className="flex-1 px-4 py-2 border border-gray-300 rounded-full focus:outline-none focus:ring-2 focus:ring-blue-500 text-sm"
                    disabled={isAiResponding || !isLoggedIn}
                />
                <button
                    onClick={onSendMessage}
                    className="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-full transition-colors disabled:bg-gray-300"
                    disabled={isAiResponding || !isLoggedIn}
                >
                    전송
                </button>
            </div>
        </div>
    );
}