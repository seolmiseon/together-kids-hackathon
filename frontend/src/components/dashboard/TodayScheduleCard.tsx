import React from 'react';

const SunIcon = () => (
    <svg
        xmlns="http://www.w3.org/2000/svg"
        className="h-6 w-6 text-yellow-500"
        fill="none"
        viewBox="0 0 24 24"
        stroke="currentColor"
    >
        <path
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeWidth={2}
            d="M12 3v1m0 16v1m9-9h-1M4 12H3m15.364 6.364l-.707-.707M6.343 6.343l-.707-.707m12.728 0l-.707.707M6.343 17.657l-.707.707M16 12a4 4 0 11-8 0 4 4 0 018 0z"
        />
    </svg>
);
const MoonIcon = () => (
    <svg
        xmlns="http://www.w3.org/2000/svg"
        className="h-6 w-6 text-indigo-500"
        fill="none"
        viewBox="0 0 24 24"
        stroke="currentColor"
    >
        <path
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeWidth={2}
            d="M20.354 15.354A9 9 0 018.646 3.646 9.003 9.003 0 0012 21a9.003 9.003 0 008.354-5.646z"
        />
    </svg>
);

export default function TodayScheduleCard() {
    return (
        <div className="bg-white p-6 rounded-lg shadow">
            <div className="flex justify-between items-center mb-4">
                <h2 className="text-xl font-bold text-gray-800">
                    오늘의 등하원 일정
                </h2>
                <span className="text-sm font-medium text-gray-500">
                    50% 완료
                </span>
            </div>
            <div className="w-full bg-gray-200 rounded-full h-2 mb-4">
                <div
                    className="bg-blue-600 h-2 rounded-full"
                    style={{ width: '50%' }}
                ></div>
            </div>
            <div className="space-y-4">
                <div className="flex items-center p-4 bg-gray-50 rounded-lg">
                    <div className="mr-4">
                        <SunIcon />
                    </div>
                    <div className="flex-grow">
                        <p className="font-bold text-gray-700">등원 (08:30)</p>
                        <p className="text-sm text-gray-500">
                            담당자: 김지연 님
                        </p>
                    </div>
                    <span className="text-sm font-bold text-green-600 bg-green-100 px-3 py-1 rounded-full">
                        완료
                    </span>
                </div>
                <div className="flex items-center p-4 bg-blue-50 rounded-lg border-l-4 border-blue-500">
                    <div className="mr-4">
                        <MoonIcon />
                    </div>
                    <div className="flex-grow">
                        <p className="font-bold text-gray-700">하원 (16:00)</p>
                        <p className="text-sm text-gray-500">
                            담당자: 박서준 님
                        </p>
                    </div>
                    <span className="text-sm font-bold text-blue-600 bg-blue-100 px-3 py-1 rounded-full">
                        진행 예정
                    </span>
                </div>
            </div>
        </div>
    );
}
