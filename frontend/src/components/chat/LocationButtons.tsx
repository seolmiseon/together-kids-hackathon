interface Place {
    name: string;
    address: string;
}

interface LocationButtonsProps {
    message: string;
}

export function LocationButtons({ message }: LocationButtonsProps) {
    // 네이버 지도용 강화된 텍스트 정제 함수
    const cleanSearchQuery = (text: string): string => {
        let cleanName = text.trim();
        
        console.log('🔍 정제 전 텍스트:', cleanName);
        
        // 패턴 0: "OO 어린이 공원" 패턴 직접 처리
        if (cleanName.startsWith('OO ')) {
            // OO를 실제 지역명으로 대체하려고 시도
            const placeMatch = cleanName.match(/OO\s*(.+?)(?:\s+이곳은|\s+여기는|$)/);
            if (placeMatch) {
                cleanName = '서울' + placeMatch[1]; // 기본적으로 서울로 설정
            }
        }
        
        // 패턴 1: "어린이 공원 이곳은..." → "어린이 공원"
        if (cleanName.includes(' 이곳은')) {
            cleanName = cleanName.split(' 이곳은')[0];
        }
        
        // 패턴 2: "놀이공원 에서는..." → "놀이공원"
        if (cleanName.includes(' 에서는') || cleanName.includes(' 에서') || cleanName.includes(' 에 가')) {
            cleanName = cleanName.split(/ (?:에서[는]?|에 가)/)[0];
        }
        
        // 패턴 3: "어린이공원은 넓은..." → "어린이공원"
        if (cleanName.includes('은 ') || cleanName.includes('는 ')) {
            cleanName = cleanName.split(/[은는] /)[0];
        }
        
        // 패턴 4: "이곳은 다양한..." → 키워드 추출
        if (cleanName.startsWith('이곳은 ')) {
            const placeMatch = cleanName.match(/([가-힣\w\s]*(?:공원|놀이터|키즈카페|수영장|체육관|도서관|박물관|마트|병원|센터))/);
            if (placeMatch) {
                cleanName = placeMatch[1];
            }
        }
        
        // 패턴 5: "체험관 에 가보시는" → "체험관"
        if (cleanName.includes(' 에 가보시는') || cleanName.includes(' 가보시는')) {
            cleanName = cleanName.split(/ (?:에 )?가보시는/)[0];
        }
        
        // 패턴 6: "추천드려요" "어떠세요" 같은 끝 제거
        cleanName = cleanName.replace(/ (?:추천드려요|어떠세요|좋을 것 같아요|괜찮을 것 같아요).*$/g, '');
        
        // 패턴 7: 긴 설명문에서 첫 번째 장소명만 추출
        const keywordMatch = cleanName.match(/^([가-힣\w\s]{2,20}(?:공원|놀이터|키즈카페|어린이|수영장|체육관|도서관|박물관|마트|병원|센터|카페|식당|체험관))/);
        if (keywordMatch) {
            cleanName = keywordMatch[1];
        }
        
        // 최종 정제: 특수문자 제거 및 공백 정리
        cleanName = cleanName.replace(/[^\w가-힣\s]/g, '').replace(/\s+/g, ' ').trim();
        
        console.log('🔍 정제 후 텍스트:', cleanName);
        
        return cleanName || '공원'; // 정제 실패 시 기본값 반환
    };

    // 메시지에서 장소 정보 추출하는 함수 - 강화된 버전
    const extractPlaces = (message: string): Place[] => {
        console.log('🔍 AI 메시지 원본:', message);
        
        const places: Place[] = [];
        
        // 1단계: 간단한 장소 키워드 추출 (더 관대한 패턴)
        const simpleKeywords = ['공원', '놀이터', '키즈카페', '어린이', '수영장', '체육관', '도서관', '박물관', '마트', '병원', '센터', '카페', '식당'];
        
        for (const keyword of simpleKeywords) {
            if (message.includes(keyword)) {
                // 해당 키워드 주변 텍스트 추출
                const keywordRegex = new RegExp(`([가-힣\\w\\s]{0,10}${keyword}[가-힣\\w\\s]{0,10})`, 'g');
                let match;
                
                while ((match = keywordRegex.exec(message)) !== null) {
                    const extracted = match[1].trim();
                    // 너무 긴 텍스트는 제외
                    if (extracted.length <= 30) {
                        places.push({
                            name: extracted,
                            address: ''
                        });
                        console.log('🔍 키워드로 추출된 장소:', extracted);
                    }
                }
            }
        }
        
        // 2단계: 기존 정규식도 시도 (백업)
        if (places.length === 0) {
            const placeRegex = /([가-힣\w\s]+(?:카페|레스토랑|식당|병원|학교|공원|마트|상가|센터|빌딩|타워|플라자|몰|점|관))\s*(?:[@\-\s]*([가-힣\w\s]+(?:구|동|로|길|번길|대로)\s*[\d\-가-힣\w\s]*)|.*?([가-힣\w\s]+(?:시|구|동|읍|면)\s*[가-힣\w\s]*))(?=[.,\s]|$)/g;
            
            let match;
            
            while ((match = placeRegex.exec(message)) !== null) {
                places.push({
                    name: match[1].trim(),
                    address: match[2] || match[3] || ''
                });
            }
        }
        
        // 3단계: 아무것도 찾지 못했으면 전체 메시지를 하나의 장소로 처리 (마지막 수단)
        if (places.length === 0) {
            places.push({
                name: message.trim(),
                address: ''
            });
            console.log('🔍 전체 메시지를 장소로 처리:', message.trim());
        }
        
        console.log('🔍 최종 추출된 장소들:', places);
        
        return places;
    };

    const places = extractPlaces(message);
    
    if (places.length === 0) return null;
    
    return (
        <div className="mt-2 space-y-2">
            {places.map((place, index) => (
                <div key={index} className="border-t pt-2 mt-2">
                    <p className="text-xs font-semibold text-gray-600 mb-1">📍 {place.name}</p>
                    <div className="flex gap-1 flex-wrap">
                        <button
                            onClick={() => {
                                const cleanedName = cleanSearchQuery(place.name);
                                const searchQuery = cleanedName + (place.address ? ' ' + place.address : '');
                                window.open(`https://maps.google.com/maps?q=${encodeURIComponent(searchQuery)}`, '_blank');
                            }}
                            className="px-2 py-1 bg-green-500 text-white text-xs rounded hover:bg-green-600 transition-colors"
                        >
                            구글맵
                        </button>
                        <button
                            onClick={() => {
                                const cleanedName = cleanSearchQuery(place.name);
                                const searchQuery = cleanedName + (place.address ? ' ' + place.address : '');
                                window.open(`https://map.kakao.com/link/search/${encodeURIComponent(searchQuery)}`, '_blank');
                            }}
                            className="px-2 py-1 bg-yellow-500 text-white text-xs rounded hover:bg-yellow-600 transition-colors"
                        >
                            카카오맵
                        </button>
                        <button
                            onClick={() => {
                                const cleanedName = cleanSearchQuery(place.name);
                                const searchQuery = cleanedName + (place.address ? ' ' + place.address : '');
                                console.log('🗺️ 네이버 지도 검색:', { 원본: place.name, 정제: cleanedName, 최종: searchQuery });
                                window.open(`https://map.naver.com/v5/search/${encodeURIComponent(searchQuery)}`, '_blank');
                            }}
                            className="px-2 py-1 bg-green-600 text-white text-xs rounded hover:bg-green-700 transition-colors"
                        >
                            네이버맵
                        </button>
                    </div>
                </div>
            ))}
        </div>
    );
}