'use client';
import { useState, useEffect } from 'react';
import { Map, MapMarker } from 'react-kakao-maps-sdk';
import Script from 'next/script';

interface Child {
    id: number;
    name: string;
    lat: number;
    lng: number;
    status: 'safe' | 'moving' | 'alert';
    guardian: string;
    imageUrl: string;
}

export default function MapSection() {
    const [children, setChildren] = useState<Child[]>([]);
    const [isLoading, setIsLoading] = useState(true);
    // [수정] isTrackingTime의 기본값을 true로 변경하여 항상 마커가 보이도록
    const [isTrackingTime, setIsTrackingTime] = useState(true);

    useEffect(() => {
        const fetchChildrenData = async () => {
            try {
                const apiUrl = process.env.NEXT_PUBLIC_API_URL;
                const response = await fetch(`${apiUrl}/children`);

                if (!response.ok) {
                    throw new Error(
                        '서버에서 데이터를 가져오는 데 실패했습니다.'
                    );
                }

                const data: Child[] = await response.json();
                setChildren(data);
            } catch (error) {
                console.error('아이 정보를 불러오는 데 실패했습니다:', error);
                // 테스트를 위해 에러 발생 시에도 임시 데이터를 보여줍니다.
                const mockData: Child[] = [
                    {
                        id: 1,
                        name: '김지연',
                        lat: 37.5665,
                        lng: 126.978,
                        status: 'safe',
                        guardian: '변우석엄마',
                        imageUrl: '/images/children/child_profile_1.png',
                    },
                    {
                        id: 2,
                        name: '박민준',
                        lat: 37.5675,
                        lng: 126.9785,
                        status: 'moving',
                        guardian: '박민준엄마',
                        imageUrl: '/images/children/child_profile_2.png',
                    },
                ];
                setChildren(mockData);
            } finally {
                setIsLoading(false);
            }
        };

        fetchChildrenData();
    }, []);

    /*
    // [주석 처리] 테스트 중에는 시간 제한 로직을 사용하지 않습니다.
    // 나중에 실제 서비스 운영 시 이 주석을 다시 해제하면 됩니다.
    useEffect(() => {
        const checkTrackingTime = () => {
            const now = new Date();
            const currentHour = now.getHours();

            const isMorningRush = currentHour >= 8 && currentHour < 9;
            const isAfternoonRush = currentHour >= 15 && currentHour < 16;

            setIsTrackingTime(isMorningRush || isAfternoonRush);
        };

        const interval = setInterval(checkTrackingTime, 60000);
        checkTrackingTime();

        return () => clearInterval(interval);
    }, []);
    */

    const KAKAO_MAP_KEY = process.env.NEXT_PUBLIC_KAKAO_MAP_KEY;

    if (isLoading) {
        return (
            <div
                className="flex-1 relative bg-gray-100 flex items-center justify-center"
                style={{ height: 'calc(100vh - 80px)' }}
            >
                <p className="text-gray-500">
                    아이들 위치 정보를 불러오는 중...
                </p>
            </div>
        );
    }

    return (
        <div
            className="flex-1 relative bg-gray-100"
            style={{ height: 'calc(100vh - 80px)' }}
        >
            <Script
                src={`//dapi.kakao.com/v2/maps/sdk.js?appkey=${KAKAO_MAP_KEY}&autoload=false`}
                strategy="beforeInteractive"
            />
            <Map
                center={{ lat: 37.5665, lng: 126.978 }}
                style={{ width: '100%', height: '100%' }}
                level={4}
            >
                {isTrackingTime &&
                    children.map((child) => (
                        <MapMarker
                            key={child.id}
                            position={{ lat: child.lat, lng: child.lng }}
                            title={child.name}
                            image={{
                                src: child.imageUrl,
                                size: { width: 48, height: 48 },
                                options: {
                                    offset: { x: 24, y: 48 },
                                },
                            }}
                        />
                    ))}
            </Map>

            <div className="absolute top-4 left-4 bg-white rounded-lg shadow-lg p-4 z-30">
                <h3 className="text-lg font-bold text-gray-800 mb-2">
                    실시간 위치 현황
                </h3>
                {isTrackingTime ? (
                    <div className="space-y-2">
                        {children.map((child) => (
                            <div
                                key={child.id}
                                className="flex items-center space-x-2 text-sm"
                            >
                                <div
                                    className={`w-3 h-3 rounded-full ${
                                        child.status === 'safe'
                                            ? 'bg-green-500'
                                            : child.status === 'moving'
                                            ? 'bg-blue-500'
                                            : 'bg-red-500'
                                    }`}
                                ></div>
                                <span className="text-gray-800">
                                    {child.name}
                                </span>
                                <span className="text-gray-600">
                                    ({child.guardian})
                                </span>
                            </div>
                        ))}
                    </div>
                ) : (
                    <p className="text-sm text-gray-500">
                        현재는 등하원 추적 시간이 아닙니다.
                    </p>
                )}
            </div>
        </div>
    );
}
