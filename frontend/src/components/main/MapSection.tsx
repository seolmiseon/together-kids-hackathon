'use client';
import { useState, useEffect } from 'react';

export default function MapSection() {
    const [children, setChildren] = useState([
        {
            id: 1,
            name: '김지연',
            lat: 37.5665,
            lng: 126.978,
            status: 'safe', // safe, moving, alert
            guardian: '변우석엄마',
        },
        {
            id: 2,
            name: '박민준',
            lat: 37.5675,
            lng: 126.9785,
            status: 'moving',
            guardian: '박민준엄마',
        },
    ]);

    return (
        <div className="flex-1 relative bg-gray-100">
            {/* 지도 영역 (전체 화면) */}
            <div className="absolute inset-0 bg-gradient-to-br from-blue-50 to-green-50 flex items-center justify-center">
                {/* 임시 지도 (실제로는 Google Maps나 Naver Maps API 사용) */}
                <div className="w-full h-full relative">
                    {/* 지도 배경 */}
                    <div className="absolute inset-0 bg-gray-200 opacity-50">
                        <div className="w-full h-full bg-gradient-to-br from-green-200 to-blue-200 relative">
                            {/* 가상의 도로와 건물들 */}
                            <div className="absolute top-1/4 left-1/4 w-1/2 h-2 bg-gray-400 opacity-60"></div>
                            <div className="absolute top-1/3 left-1/6 w-2 h-1/3 bg-gray-400 opacity-60"></div>
                            <div className="absolute top-1/2 left-1/3 w-16 h-16 bg-red-300 opacity-70 rounded-lg flex items-center justify-center text-xs font-bold">
                                어린이집
                            </div>
                        </div>
                    </div>

                    {/* 아이들 위치 마커 */}
                    {children.map((child) => (
                        <div
                            key={child.id}
                            className={`absolute transform -translate-x-1/2 -translate-y-1/2 z-20`}
                            style={{
                                left: `${(child.lng - 126.97) * 5000 + 50}%`,
                                top: `${(37.57 - child.lat) * 5000 + 40}%`,
                            }}
                        >
                            <div className={`relative`}>
                                {/* 안전 영역 표시 */}
                                <div
                                    className={`absolute -top-8 -left-8 w-16 h-16 rounded-full border-2 ${
                                        child.status === 'safe'
                                            ? 'border-green-400 bg-green-100'
                                            : child.status === 'moving'
                                            ? 'border-blue-400 bg-blue-100'
                                            : 'border-red-400 bg-red-100'
                                    } opacity-60`}
                                ></div>

                                {/* 아이 마커 */}
                                <div
                                    className={`w-8 h-8 rounded-full ${
                                        child.status === 'safe'
                                            ? 'bg-green-500'
                                            : child.status === 'moving'
                                            ? 'bg-blue-500'
                                            : 'bg-red-500'
                                    } border-2 border-white shadow-lg flex items-center justify-center text-white text-xs font-bold`}
                                >
                                    👶
                                </div>

                                {/* 아이 정보 툴팁 */}
                                <div className="absolute top-10 left-1/2 transform -translate-x-1/2 bg-white rounded-lg shadow-lg px-3 py-2 text-xs font-medium whitespace-nowrap z-30">
                                    <p className="text-gray-800">
                                        {child.name}
                                    </p>
                                    <p className="text-gray-600">
                                        {child.guardian}
                                    </p>
                                    <p
                                        className={`${
                                            child.status === 'safe'
                                                ? 'text-green-600'
                                                : child.status === 'moving'
                                                ? 'text-blue-600'
                                                : 'text-red-600'
                                        }`}
                                    >
                                        {child.status === 'safe'
                                            ? '안전'
                                            : child.status === 'moving'
                                            ? '이동 중'
                                            : '주의'}
                                    </p>
                                </div>
                            </div>
                        </div>
                    ))}

                    {/* 지도 컨트롤 */}
                    <div className="absolute top-4 left-4 bg-white rounded-lg shadow-lg p-4 z-30">
                        <h3 className="text-lg font-bold text-gray-800 mb-2">
                            실시간 위치 현황
                        </h3>
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
                    </div>
                </div>
            </div>
        </div>
    );
}
