interface Place {
    name: string;
    address: string;
}

interface LocationButtonsProps {
    message: string;
}

export function LocationButtons({ message }: LocationButtonsProps) {
    // 네이버 지도용 텍스트 정제 함수
    const cleanSearchQuery = (text: string): string => {
        let cleanName = text.trim();
        
        // 패턴 1: "OO 놀이공원 에서는..." → "OO 놀이공원"
        if (cleanName.includes(' 에서는') || cleanName.includes(' 에서')) {
            cleanName = cleanName.split(/ 에서[는]?/)[0];
        }
        
        // 패턴 2: "OO 어린이공원은 넓은..." → "OO 어린이공원"
        if (cleanName.includes(' 은 ') || cleanName.includes(' 는 ')) {
            cleanName = cleanName.split(/ [은는] /)[0];
        }
        
        // 패턴 3: "이곳은 넓은 잔디밭과..." 같은 시작 제거
        if (cleanName.startsWith('이곳은 ')) {
            // "이곳은"으로 시작하면 전체 텍스트에서 장소명 추출 시도
            const placeMatch = cleanName.match(/([가-힣\w\s]+(?:공원|놀이터|키즈카페|수영장|체육관|도서관|박물관|마트|병원))/);
            if (placeMatch) {
                cleanName = placeMatch[1];
            }
        }
        
        // 패턴 4: 긴 설명문에서 핵심 키워드만 추출
        const keywordMatch = cleanName.match(/([가-힣\w\s]{2,15}(?:공원|놀이터|키즈카페|어린이|수영장|체육관|도서관|박물관|마트|병원|센터|카페|식당))/);
        if (keywordMatch && keywordMatch[1].length < cleanName.length) {
            cleanName = keywordMatch[1];
        }
        
        // 최종 정제: 특수문자 제거 및 공백 정리
        cleanName = cleanName.replace(/[^\w가-힣\s]/g, '').replace(/\s+/g, ' ').trim();
        
        return cleanName || text; // 정제 실패 시 원본 반환
    };

    // 메시지에서 장소 정보 추출하는 함수
    const extractPlaces = (message: string): Place[] => {
        const places: Place[] = [];
        
        // 정규식 패턴: 장소명과 주소를 추출
        // 예: "서울시 강남구 역삼동의 카페 A"나 "부산 해운대구의 레스토랑 B" 등
        const placeRegex = /([가-힣\w\s]+(?:카페|레스토랑|식당|병원|학교|공원|마트|상가|센터|빌딩|타워|플라자|몰|점|관))\s*(?:[@\-\s]*([가-힣\w\s]+(?:구|동|로|길|번길|대로)\s*[\d\-가-힣\w\s]*)|.*?([가-힣\w\s]+(?:시|구|동|읍|면)\s*[가-힣\w\s]*))(?=[.,\s]|$)/g;
        
        let match;
        
        while ((match = placeRegex.exec(message)) !== null) {
            places.push({
                name: match[1].trim(),
                address: match[2] || match[3] || ''
            });
        }
        
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