interface Place {
    name: string;
    address: string;
}

interface LocationButtonsProps {
    message: string;
}

export function LocationButtons({ message }: LocationButtonsProps) {
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
                            onClick={() => window.open(`https://maps.google.com/maps?q=${encodeURIComponent(place.name + ' ' + place.address)}`, '_blank')}
                            className="px-2 py-1 bg-green-500 text-white text-xs rounded hover:bg-green-600 transition-colors"
                        >
                            구글맵
                        </button>
                        <button
                            onClick={() => window.open(`https://map.kakao.com/link/search/${encodeURIComponent(place.name + ' ' + place.address)}`, '_blank')}
                            className="px-2 py-1 bg-yellow-500 text-white text-xs rounded hover:bg-yellow-600 transition-colors"
                        >
                            카카오맵
                        </button>
                        <button
                            onClick={() => window.open(`https://map.naver.com/v5/search/${encodeURIComponent(place.name + ' ' + place.address)}`, '_blank')}
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