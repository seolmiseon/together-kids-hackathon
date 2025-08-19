import React from 'react';

export default function RecentActivityFeed() {
    return (
        <div className="bg-white p-6 rounded-lg shadow">
            <h2 className="text-xl font-bold text-gray-800 mb-4">최근 활동</h2>
            <ul className="space-y-4">
                <li className="flex items-start">
                    <div className="w-10 h-10 bg-gray-200 rounded-full mr-4"></div>
                    <div className="flex-grow">
                        <p className="font-medium text-gray-800">
                            김지연 님이 '주말 놀이터 모임'에 참여했습니다.
                        </p>
                        <p className="text-sm text-gray-400">2시간 전</p>
                    </div>
                </li>
                <li className="flex items-start">
                    <div className="w-10 h-10 bg-gray-200 rounded-full mr-4"></div>
                    <div className="flex-grow">
                        <p className="font-medium text-gray-800">
                            박서준 님이 '내일 하원 도움'을 요청했습니다.
                        </p>
                        <p className="text-sm text-gray-400">5시간 전</p>
                    </div>
                </li>
            </ul>
        </div>
    );
}
