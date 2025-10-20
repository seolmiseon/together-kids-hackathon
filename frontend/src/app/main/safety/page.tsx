'use client';

import { useEffect, useState } from 'react';
import socket from '@/lib/socket';

interface Location {
    lat: number;
    lng: number;
    timestamp: Date;
}

interface Parent {
    id: string;
    name: string;
    location: Location;
    isInSafeZone: boolean;
    children: string[];
}

export default function SafetyPage() {
    // 페이지 컴포넌트는 props를 받을 수 없으므로 기본값 사용
    const groupId = 'general';
    const currentParent = 'user';

    const [parents, setParents] = useState<Parent[]>([]);
    const [myLocation, setMyLocation] = useState<Location | null>(null);
    const [trackingEnabled, setTrackingEnabled] = useState<boolean>(false);

    useEffect(() => {
        if (!trackingEnabled) return;

        const watchId = navigator.geolocation.watchPosition(
            (position) => {
                const newLocation: Location = {
                    lat: position.coords.latitude,
                    lng: position.coords.longitude,
                    timestamp: new Date(),
                };

                setMyLocation(newLocation);

                // 등하원 시간대에만 위치 공유 (개인정보 보호)
                const hour = new Date().getHours();
                const isPickupTime =
                    (hour >= 7 && hour <= 9) || (hour >= 15 && hour <= 18);

                if (isPickupTime) {
                    const socketInstance = socket.get();
                    socketInstance.emit('location_update', {
                        groupId,
                        parent: currentParent,
                        location: newLocation,
                    });
                }
            },
            (error) => console.error('GPS 오류:', error),
            { enableHighAccuracy: true, maximumAge: 30000, timeout: 10000 }
        );

        const socketInstance = socket.get();
        socketInstance.on(
            'location_update',
            (data: {
                parent: string;
                location: Location;
                isInSafeZone: boolean;
            }) => {
                setParents((prev) =>
                    prev.map((p) =>
                        p.name === data.parent
                            ? {
                                  ...p,
                                  location: data.location,
                                  isInSafeZone: data.isInSafeZone,
                              }
                            : p
                    )
                );
            }
        );

        socketInstance.on(
            'safety_alert',
            (data: { parent: string; message: string }) => {
                if (data.parent !== currentParent) {
                    alert(`⚠️ 안전 알림: ${data.message}`);
                }
            }
        );

        return () => {
            navigator.geolocation.clearWatch(watchId);
            socketInstance.off('location_update');
            socketInstance.off('safety_alert');
        };
    }, [trackingEnabled, groupId, currentParent]);

    const toggleTracking = () => {
        setTrackingEnabled(!trackingEnabled);
    };

    return (
        <div className="bg-white rounded-lg shadow-lg p-6">
            <div className="flex justify-between items-center mb-4">
                <h3 className="text-lg font-bold text-gray-800">
                    GPS 안전 관리
                </h3>
                <button
                    onClick={toggleTracking}
                    className={`px-4 py-2 rounded-lg font-medium ${
                        trackingEnabled
                            ? 'bg-green-500 text-white hover:bg-green-600'
                            : 'bg-gray-300 text-gray-700 hover:bg-gray-400'
                    }`}
                >
                    {trackingEnabled ? '🟢 추적 중' : '⚪ 추적 중지'}
                </button>
            </div>

            <div className="text-sm text-gray-600 mb-4">
                <p>
                    🔒 개인정보 보호: 등하원 시간대(오전 7-9시, 오후 3-6시)에만
                    위치를 공유합니다
                </p>
            </div>

            {myLocation && (
                <div className="bg-blue-50 p-4 rounded-lg mb-4">
                    <h4 className="font-medium text-blue-800 mb-2">
                        내 현재 위치
                    </h4>
                    <p className="text-sm text-gray-700">
                        위도: {myLocation.lat.toFixed(6)}, 경도:{' '}
                        {myLocation.lng.toFixed(6)}
                    </p>
                    <p className="text-xs text-gray-500 mt-1">
                        업데이트: {myLocation.timestamp.toLocaleTimeString()}
                    </p>
                </div>
            )}

            <div className="space-y-2">
                <h4 className="font-medium text-gray-800">그룹 멤버 위치</h4>
                {parents.map((parent) => (
                    <div
                        key={parent.id}
                        className={`p-3 rounded-lg border ${
                            parent.isInSafeZone
                                ? 'border-green-200 bg-green-50'
                                : 'border-red-200 bg-red-50'
                        }`}
                    >
                        <div className="flex justify-between items-center">
                            <span className="font-medium">{parent.name}</span>
                            <span
                                className={`text-sm px-2 py-1 rounded ${
                                    parent.isInSafeZone
                                        ? 'bg-green-200 text-green-800'
                                        : 'bg-red-200 text-red-800'
                                }`}
                            >
                                {parent.isInSafeZone
                                    ? '✅ 안전 구역'
                                    : '⚠️ 경계 이탈'}
                            </span>
                        </div>
                        <p className="text-xs text-gray-600 mt-1">
                            아이들: {parent.children.join(', ')}
                        </p>
                    </div>
                ))}
            </div>
        </div>
    );
}
