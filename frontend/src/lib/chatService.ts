import { getAuth } from 'firebase/auth';
import type { Message } from '@/components/chat/ChatMessage';

export interface ChatResponse {
    message?: string;
    response?: string;
    coordination_result?: string;
    places?: any[];
    urgency?: 'low' | 'medium' | 'high';
}

export class ChatService {
    private apiUrl: string;

    constructor() {
        this.apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
    }

    async sendMessage(message: string): Promise<ChatResponse> {
        const auth = getAuth();
        const currentUser = auth.currentUser;
        
        if (!currentUser) {
            throw new Error('로그인이 필요합니다.');
        }

        const token = await currentUser.getIdToken();
        const params = new URLSearchParams({
            message,
            mode: 'auto',
        });
        const requestUrl = `${this.apiUrl}/chat?${params.toString()}`;

        const response = await fetch(requestUrl, {
            method: 'POST',
            headers: {
                Authorization: `Bearer ${token}`,
            },
        });

        if (!response.ok) {
            throw new Error('AI 응답 실패');
        }

        return await response.json();
    }

    processAiResponse(aiData: ChatResponse): {
        content: string;
        places?: any[];
        urgency?: 'low' | 'medium' | 'high';
    } {
        const content = aiData.message || 
                       aiData.response || 
                       aiData.coordination_result || 
                       '응답을 처리할 수 없습니다.';

        return {
            content,
            places: aiData.places,
            urgency: aiData.urgency
        };
    }

    handleMapDisplay(places: any[]) {
        if (!places || !Array.isArray(places) || places.length === 0) {
            return;
        }

        console.log('🔍 AI 응답에서 장소 정보 발견:', places);

        // 장소 정보를 SearchPlace 형태로 변환
        const searchPlaces = places.map((place: any, index: number) => ({
            id: place.id || `place_${index}`,
            name: place.name || place.title || '알 수 없는 장소',
            address: place.address || place.roadAddress || '',
            lat: parseFloat(place.lat || place.mapx) / (place.mapx ? 10000000 : 1),
            lng: parseFloat(place.lng || place.mapy) / (place.mapy ? 10000000 : 1),
            category: place.category || '',
            phone: place.phone || place.telephone || '',
            description: place.description || '',
        }));

        // 지도에 장소 표시 (전역 함수 호출)
        if (typeof window !== 'undefined' && (window as any).displaySearchResults) {
            (window as any).displaySearchResults(searchPlaces);
        }
    }

    createErrorMessage(error: Error): Message {
        console.error('Chat service error:', error);
        return {
            id: Date.now(),
            type: 'ai',
            content: '죄송해요, 지금은 답변을 드릴 수 없어요.',
            timestamp: new Date(),
        };
    }
}

// 싱글톤 인스턴스 제공
export const chatService = new ChatService();
