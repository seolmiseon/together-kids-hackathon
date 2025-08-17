import React from 'react';

interface BellIconProps {
    size?: 'sm' | 'md' | 'lg';
    hasNotification?: boolean;
    count?: number;
    className?: string;
    onClick?: () => void;
}

export default function BellIcon({
    size = 'md',
    className = '',
    hasNotification = false,
    count = 0,
    onClick,
}: BellIconProps) {
    const sizeClasses = {
        sm: 'w-4 h-4',
        md: 'w-6 h-6',
        lg: 'w-8 h-8',
    };

    return (
        <div className="relative">
            <svg
                width="24"
                height="24"
                viewBox="0 0 24 24"
                fill="none"
                className="text-gray-600 hover:text-blue-600 transition-colors cursor-pointer"
            >
                <path
                    d="M18 8A6 6 0 0 0 6 8c0 7-3 9-3 9h18s-3-2-3-9"
                    stroke="currentColor"
                    strokeWidth="2"
                    strokeLinecap="round"
                    strokeLinejoin="round"
                />
                <path
                    d="M13.73 21a2 2 0 0 1-3.46 0"
                    stroke="currentColor"
                    strokeWidth="2"
                    strokeLinecap="round"
                    strokeLinejoin="round"
                />
            </svg>

            {/* 알림 배지 */}
            {hasNotification && (
                <span className="absolute -top-2 -right-2 bg-red-500 text-white text-xs font-bold rounded-full min-w-[20px] h-5 flex items-center justify-center px-1">
                    {count > 99 ? '99+' : count}
                </span>
            )}
        </div>
    );
}
