import React from 'react';

interface CloseButtonProps {
  onClick: () => void;
  className?: string;
  size?: 'sm' | 'md' | 'lg';
  variant?: 'default' | 'dark' | 'light' | 'danger';
  ariaLabel?: string;
}

export default function CloseButton({ 
  onClick, 
  className = '', 
  size = 'md',
  variant = 'default',
  ariaLabel = '닫기'
}: CloseButtonProps) {
  
  // 크기별 스타일
  const sizeStyles = {
    sm: 'w-4 h-4 p-1',
    md: 'w-6 h-6 p-1',
    lg: 'w-8 h-8 p-2'
  };

  // 색상별 스타일
  const variantStyles = {
    default: 'text-gray-500 hover:text-gray-700 hover:bg-gray-100',
    dark: 'text-white hover:text-gray-200 hover:bg-white/20',
    light: 'text-gray-400 hover:text-gray-600 hover:bg-gray-50',
    danger: 'text-red-500 hover:text-red-700 hover:bg-red-50'
  };

  // 아이콘 크기
  const iconSizes = {
    sm: '12',
    md: '16', 
    lg: '20'
  };

  return (
    <button
      onClick={onClick}
      className={`
        ${sizeStyles[size]}
        ${variantStyles[variant]}
        rounded-full transition-all duration-200 
        flex items-center justify-center
        ${className}
      `}
      aria-label={ariaLabel}
    >
      <svg 
        width={iconSizes[size]} 
        height={iconSizes[size]} 
        viewBox="0 0 24 24" 
        fill="none" 
        stroke="currentColor" 
        strokeWidth="2"
        strokeLinecap="round" 
        strokeLinejoin="round"
      >
        <path d="M18 6L6 18M6 6l12 12" />
      </svg>
    </button>
  );
}