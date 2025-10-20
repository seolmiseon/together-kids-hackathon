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

    // 빠른 질문 버튼들
    const quickQuestions = [
        "근처 놀이터 찾아줘",
        "가까운 병원 알려줘", 
        "주변 식당 추천해줘",
        "이 근처 어린이집은?",
    ];

    const handleQuickQuestion = (question: string) => {
        setInputMessage(question);
        // 자동 전송은 하지 않고 사용자가 수정할 기회 제공
    };

    return (
        <div className="p-4 border-t bg-white flex-shrink-0 space-y-3">
            {/* 빠른 질문 버튼들 */}
            {!isAiResponding && isLoggedIn && (
                <div className="grid grid-cols-2 gap-2">
                    {quickQuestions.map((question, index) => (
                        <button
                            key={index}
                            onClick={() => handleQuickQuestion(question)}
                            className="px-3 py-2 bg-gray-100 hover:bg-gray-200 text-gray-700 rounded-lg text-xs transition-colors border"
                            disabled={isAiResponding}
                        >
                            {question}
                        </button>
                    ))}
                </div>
            )}
            
            {/* 메인 입력 영역 */}
            <div className="flex space-x-2">
                <input
                    type="text"
                    value={inputMessage}
                    onChange={(e) => setInputMessage(e.target.value)}
                    onKeyPress={handleKeyPress}
                    placeholder="메시지를 입력하거나 지도를 클릭하세요..."
                    className="flex-1 px-4 py-2 border border-gray-300 rounded-full focus:outline-none focus:ring-2 focus:ring-blue-500 text-sm"
                    disabled={isAiResponding || !isLoggedIn}
                />
                <button
                    onClick={onSendMessage}
                    className="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-full transition-colors disabled:bg-gray-300 touch-target"
                    disabled={isAiResponding || !isLoggedIn}
                >
                    전송
                </button>
            </div>
            
            {/* 도움말 텍스트 */}
            {!isAiResponding && isLoggedIn && (
                <p className="text-xs text-gray-500 text-center">
                    💡 팁: 지도에서 위치를 클릭하면 해당 지역 정보를 자동으로 받아볼 수 있어요!
                </p>
            )}
        </div>
    );
}