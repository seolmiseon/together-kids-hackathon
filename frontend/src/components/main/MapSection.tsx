'use client';
import { useState, useEffect } from 'react';
import {
    Container as MapDiv,
    NaverMap,
    Marker,
    useNavermaps,
} from 'react-naver-maps';
import { useSession } from 'next-auth/react';
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
    const { data: session, status } = useSession();
    const [children, setChildren] = useState<Child[]>([]);
    const [isLoading, setIsLoading] = useState(true);
    const [mapError, setMapError] = useState(false);
    const navermaps = useNavermaps();
    // [수정] isTrackingTime의 기본값을 true로 변경하여 항상 마커가 보이도록
    const [isTrackingTime, setIsTrackingTime] = useState(true);

    useEffect(() => {
        const fetchData = async () => {
            setIsLoading(true);
            if (status === 'authenticated') {
                try {
                    const apiUrl = process.env.NEXT_PUBLIC_API_URL;
                    const response = await fetch(`${apiUrl}/children`, {
                        headers: {
                            Authorization: `Bearer ${session.accessToken}`,
                        },
                    });
                    if (!response.ok) throw new Error('데이터 로딩 실패');
                    const data = await response.json();
                    setChildren(data);
                } catch (error) {
                    console.error(error);
                }
            } else if (status === 'unauthenticated') {
                const demoData: Child[] = [
                    {
                        id: 1,
                        name: '데모 아이',
                        lat: 37.566826,
                        lng: 126.9786567,
                        status: 'safe',
                        guardian: '함께키즈',
                        imageUrl: '/images/logo/logosymbol.png',
                    },
                ];
                setChildren(demoData);
            }
            setIsLoading(false);
        };
        fetchData();
    }, [status, session]);

    /*
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

    useEffect(() => {
        const timer = setTimeout(() => {
            if (!navermaps) {
                setMapError(true);
                console.error('Naver Maps script loading timed out.');
            }
        }, 5000);
        return () => clearTimeout(timer);
    }, [navermaps]);

    if (isLoading) {
        return (
            <div
                className="w-full flex items-center justify-center"
                style={{ height: 'calc(100vh - 5rem)' }}
            >
                <p className="text-center pt-10">지도 로딩 중...</p>
            </div>
        );
    }

    return (
        <div
            className="relative w-full"
            style={{ height: 'calc(100vh - 5rem)' }}
        >
            {mapError ? (
                <div className="w-full h-full flex items-center justify-center bg-gray-200">
                    <div className="text-center">
                        <p className="text-red-500 font-semibold mb-2">
                            지도 로딩에 실패했습니다.
                        </p>
                        <p className="text-gray-600 text-sm">
                            네이버 지도 Client ID 또는 도메인 등록을
                            확인해주세요.
                        </p>
                    </div>
                </div>
            ) : (
                <NaverMap
                    defaultCenter={new navermaps.LatLng(37.566826, 126.9786567)}
                    defaultZoom={15}
                >
                    {isTrackingTime &&
                        children.map((child) => (
                            <Marker
                                key={child.id}
                                position={
                                    new navermaps.LatLng(child.lat, child.lng)
                                }
                                title={child.name}
                                icon={{
                                    content: `<div style="width:48px;height:48px;border-radius:50%;overflow:hidden;border:3px solid ${
                                        child.status === 'safe'
                                            ? '#10B981'
                                            : '#3B82F6'
                                    };box-shadow: 0 0 0 2px white;"><img src="${
                                        child.imageUrl
                                    }" style="width:100%;height:100%;object-fit:cover;" alt="${
                                        child.name
                                    }"/></div>`,
                                    anchor: new navermaps.Point(24, 48),
                                }}
                            />
                        ))}
                </NaverMap>
            )}
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
                                            : 'bg-blue-500'
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
