'use client';

import { useEffect, useState, useRef } from 'react';
import socket from '@/lib/socket';

interface Message {
    id: string;
    text: string;
    sender: string;
    timestamp: Date;
    room: string;
}

export default function ChatPage() {
    // 페이지 컴포넌트는 props를 받을 수 없으므로 기본값 사용
    const room = 'general';
    const currentUser = 'user';
    const [messages, setMessages] = useState<Message[]>([]);
    const [inputText, setInputText] = useState<string>('');
    const [isConnected, setIsConnected] = useState<boolean>(false);
    const [isTyping, setIsTyping] = useState<boolean>(false);
    const messagesEndRef = useRef<HTMLDivElement>(null);

    // 자동 스크롤 함수
    const scrollToBottom = () => {
        messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
    };

    // 메시지가 업데이트될 때마다 자동 스크롤
    useEffect(() => {
        scrollToBottom();
    }, [messages]);

    useEffect(() => {
        // 연결 상태 관리
        socket.on('connect', () => setIsConnected(true));
        socket.on('disconnect', () => setIsConnected(false));

        // 메시지 수신 - ID 생성 로직 추가
        socket.on('message', (newMessage: Omit<Message, 'id'>) => {
            const messageWithId: Message = {
                ...newMessage,
                id: `${Date.now()}-${Math.random().toString(36).substr(2, 9)}`, // 고유 ID 생성
                timestamp: new Date(newMessage.timestamp), // Date 객체로 변환
            };

            setMessages((prev) => [...prev, messageWithId]);
        });

        // 타이핑 상태 관리
        socket.on('typing', (data: { user: string; isTyping: boolean }) => {
            if (data.user !== currentUser) {
                setIsTyping(data.isTyping);
            }
        });

        // 방 참여
        socket.emit('join_room', { room, parent: currentUser });

        // 기존 메시지 로드 (선택사항)
        socket.emit('load_messages', { room });
        socket.on('previous_messages', (previousMessages: Message[]) => {
            setMessages(previousMessages);
        });

        return () => {
            socket.off('connect');
            socket.off('disconnect');
            socket.off('message');
            socket.off('typing');
            socket.off('previous_messages');
        };
    }, [room, currentUser]);

    const sendMessage = () => {
        if (!inputText.trim()) return;

        const messageData: Omit<Message, 'id'> = {
            text: inputText,
            sender: currentUser,
            timestamp: new Date(),
            room,
        };

        // 즉시 UI에 메시지 추가 (낙관적 업데이트)
        const optimisticMessage: Message = {
            ...messageData,
            id: `temp-${Date.now()}`,
        };
        setMessages((prev) => [...prev, optimisticMessage]);

        // 서버로 메시지 전송
        socket.emit('message', messageData);

        // 입력창 초기화
        setInputText('');

        // 타이핑 상태 중지
        socket.emit('stop_typing', { room, user: currentUser });
    };

    // 입력 중 타이핑 상태 전송
    const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
        setInputText(e.target.value);

        // 타이핑 상태 전송 (디바운싱)
        socket.emit('typing', { room, user: currentUser, isTyping: true });

        // 3초 후 타이핑 중지
        setTimeout(() => {
            socket.emit('typing', { room, user: currentUser, isTyping: false });
        }, 3000);
    };

    const handleKeyPress = (e: React.KeyboardEvent<HTMLInputElement>) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            sendMessage();
        }
    };

    // 네이버 네비게이션 열기
    const openNavigation = (placeName: string, lat?: number, lng?: number) => {
        console.log('🚗 네비 실행:', placeName, lat, lng);

        // 모바일 여부 체크
        const isMobile =
            /Android|iPhone|iPad|iPod|BlackBerry|IEMobile|Opera Mini/i.test(
                navigator.userAgent
            );

        if (isMobile) {
            // 모바일: 네이버 앱으로 연결
            if (lat && lng) {
                const naviUrl = `navi://destination?lat=${lat}&lng=${lng}&name=${encodeURIComponent(
                    placeName
                )}&appname=함께키즈`;
                console.log('� 모바일 네비 URL:', naviUrl);
                window.location.href = naviUrl;
            } else {
                const mapUrl = `nmap://search?query=${encodeURIComponent(
                    placeName
                )}&appname=함께키즈`;
                console.log('� 모바일 지도 URL:', mapUrl);
                window.location.href = mapUrl;
            }
        } else {
            // 데스크톱: 웹 네이버 지도로 연결
            const webMapUrl =
                lat && lng
                    ? `https://map.naver.com/v5/search/${encodeURIComponent(
                          placeName
                      )}/place?c=${lng},${lat},15,0,0,0,dh`
                    : `https://map.naver.com/v5/search/${encodeURIComponent(
                          placeName
                      )}`;
            console.log('💻 데스크톱 지도 URL:', webMapUrl);
            window.open(webMapUrl, '_blank');
        }
    };

    // 메시지에서 장소명을 찾아 클릭 가능하게 만들기 (대폭 개선)
    const renderMessageWithNavigation = (text: string) => {
        // 다양한 장소명 및 주소 패턴 매칭
        const patterns = [
            // 상호명 + 업종
            /([가-힣\w\s]+(?:카페|커피|스타벅스|이디야|빽다방|할리스))/g,
            /([가-힣\w\s]+(?:병원|의원|클리닉|약국))/g,
            /([가-힣\w\s]+(?:놀이터|키즈카페|어린이집|유치원))/g,
            /([가-힣\w\s]+(?:수영장|헬스장|체육관|골프장))/g,
            /([가-힣\w\s]+(?:극장|영화관|공연장|뮤지컬|연극))/g,
            /([가-힣\w\s]+(?:공원|산|해변|호수))/g,
            /([가-힣\w\s]+(?:마트|편의점|쇼핑몰|백화점|아울렛))/g,
            /([가-힣\w\s]+(?:학교|도서관|미술관|박물관))/g,
            /([가-힣\w\s]+(?:레스토랑|음식점|식당|맛집|치킨|피자))/g,
            
            // 주소 패턴
            /([가-힣]+(?:시|구|군)\s+[가-힣]+(?:동|로|길)\s*\d*-?\d*)/g,
            /([가-힣]+(?:시|도)\s+[가-힣]+(?:시|구|군)\s+[가-힣]+(?:동|면|읍))/g,
            
            // 유명 장소명
            /([가-힣]+(?:타워|센터|플라자|빌딩|몰|파크|랜드))/g,
        ];

        let processedText = text;
        const clickableSpans: { text: string; start: number; end: number }[] = [];

        // 모든 패턴을 찾아서 저장
        patterns.forEach(pattern => {
            let match;
            while ((match = pattern.exec(text)) !== null) {
                const matchText = match[1] || match[0];
                if (matchText.trim().length > 1) { // 너무 짧은 매치 제외
                    clickableSpans.push({
                        text: matchText.trim(),
                        start: match.index,
                        end: match.index + matchText.length
                    });
                }
            }
        });

        // 겹치는 영역 제거 및 정렬
        const uniqueSpans = clickableSpans
            .filter((span, index, arr) => 
                !arr.some((other, otherIndex) => 
                    otherIndex !== index && 
                    other.start <= span.start && 
                    other.end >= span.end
                )
            )
            .sort((a, b) => a.start - b.start);

        if (uniqueSpans.length === 0) {
            return <span>{text}</span>;
        }

        // 텍스트를 분할하여 렌더링
        const parts = [];
        let lastEnd = 0;

        uniqueSpans.forEach((span, index) => {
            // 클릭 가능한 부분 이전의 일반 텍스트
            if (span.start > lastEnd) {
                parts.push(
                    <span key={`text-${index}`}>
                        {text.substring(lastEnd, span.start)}
                    </span>
                );
            }

            // 클릭 가능한 부분
            parts.push(
                <span
                    key={`link-${index}`}
                    className="text-blue-600 underline cursor-pointer hover:text-blue-800 font-medium bg-blue-50 px-1 rounded"
                    onClick={() => openNavigation(span.text)}
                    title={`"${span.text}" 네이버 지도에서 검색`}
                >
                    {span.text}
                </span>
            );

            lastEnd = span.end;
        });

        // 마지막 남은 텍스트
        if (lastEnd < text.length) {
            parts.push(
                <span key="text-end">
                    {text.substring(lastEnd)}
                </span>
            );
        }

        return <>{parts}</>;
    };

    return (
        <div className="flex flex-col h-[600px] bg-white rounded-lg shadow-lg max-w-4xl mx-auto">
            {/* 헤더 */}
            <div className="bg-blue-600 text-white p-6 rounded-t-lg flex justify-between items-start">
                <div>
                    <h3 className="font-bold text-lg">함께키즈 AI 어시스턴트</h3>
                    <p className="text-sm opacity-80 flex items-center mt-1">
                        {isConnected ? (
                            <>
                                <span className="w-2 h-2 bg-green-400 rounded-full mr-2"></span>
                                연결됨
                            </>
                        ) : (
                            <>
                                <span className="w-2 h-2 bg-red-400 rounded-full mr-2"></span>
                                연결 중...
                            </>
                        )}
                    </p>
                </div>
                <button
                    onClick={() => window.history.back()}
                    className="text-white hover:text-gray-200 transition-colors p-1"
                    title="닫기"
                >
                    <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                    </svg>
                </button>
            </div>

            {/* 메시지 영역 */}
            <div className="flex-1 overflow-y-auto p-6 space-y-4 bg-gray-50">
                {messages.length === 0 ? (
                    <div className="text-center text-gray-500 mt-12">
                        <div className="bg-blue-100 rounded-lg p-6 inline-block">
                            <p className="text-lg mb-2">👋 안녕하세요!</p>
                            <p className="text-base mb-1">
                                아이 돌봄에 대해 무엇이든 물어보세요.
                            </p>
                            <p className="text-sm text-gray-600">
                                놀이터, 카페, 병원 추천부터 육아 상담까지!
                            </p>
                        </div>
                    </div>
                ) : (
                    messages.map((msg) => (
                        <div
                            key={msg.id}
                            className={`flex ${
                                msg.sender === currentUser
                                    ? 'justify-end'
                                    : 'justify-start'
                            }`}
                        >
                            <div
                                className={`p-4 rounded-lg max-w-2xl ${
                                    msg.sender === currentUser
                                        ? 'bg-blue-500 text-white'
                                        : 'bg-white text-gray-800 shadow-sm border'
                                }`}
                            >
                                <p className="text-base leading-relaxed whitespace-pre-wrap">
                                    {msg.sender === currentUser
                                        ? msg.text
                                        : renderMessageWithNavigation(msg.text)}
                                </p>
                                <p className="text-xs opacity-70 mt-2">
                                    {msg.sender === currentUser
                                        ? '나'
                                        : 'AI 어시스턴트'}{' '}
                                    •{' '}
                                    {new Date(msg.timestamp).toLocaleTimeString(
                                        'ko-KR',
                                        {
                                            hour: '2-digit',
                                            minute: '2-digit',
                                        }
                                    )}
                                </p>
                            </div>
                        </div>
                    ))
                )}

                {/* 타이핑 인디케이터 */}
                {isTyping && (
                    <div className="bg-gray-100 text-gray-600 p-2 rounded-lg max-w-xs text-sm">
                        <div className="flex items-center">
                            <div className="typing-dots flex space-x-1">
                                <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce"></div>
                                <div
                                    className="w-2 h-2 bg-gray-400 rounded-full animate-bounce"
                                    style={{ animationDelay: '0.1s' }}
                                ></div>
                                <div
                                    className="w-2 h-2 bg-gray-400 rounded-full animate-bounce"
                                    style={{ animationDelay: '0.2s' }}
                                ></div>
                            </div>
                            <span className="ml-2">입력 중...</span>
                        </div>
                    </div>
                )}

                {/* 자동 스크롤을 위한 참조점 */}
                <div ref={messagesEndRef} />
            </div>

            {/* 입력 영역 */}
            <div className="p-6 border-t bg-white rounded-b-lg">
                <div className="flex space-x-3">
                    <input
                        type="text"
                        value={inputText}
                        onChange={handleInputChange}
                        onKeyPress={handleKeyPress}
                        placeholder="아이 돌봄에 대해 무엇이든 물어보세요... (예: 놀이터 추천, 뮤지컬 공연장)"
                        disabled={!isConnected}
                        className="flex-1 p-4 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 disabled:bg-gray-100 disabled:cursor-not-allowed text-base"
                    />
                    <button
                        onClick={sendMessage}
                        disabled={!inputText.trim() || !isConnected}
                        className="bg-blue-600 text-white px-6 py-4 rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors font-medium"
                    >
                        전송
                    </button>
                </div>

                {/* 연결 상태 메시지 */}
                {!isConnected && (
                    <p className="text-xs text-red-500 mt-3 text-center">
                        서버 연결이 끊어졌습니다. 재연결 중...
                    </p>
                )}
            </div>
        </div>
    );
}
