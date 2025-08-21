import React from 'react';

export default function LoadingSkeleton() {
    return (
        <div className="min-h-screen bg-gray-50 animate-pulse">
            {/* 헤더 스켈레톤 */}
            <header className="bg-white shadow-sm">
                <div className="container mx-auto px-6 py-4 flex items-center justify-between">
                    <div className="h-10 w-32 bg-gray-200 rounded"></div>
                    <div className="flex items-center space-x-4">
                        <div className="h-6 w-6 bg-gray-200 rounded-full"></div>
                        <div className="h-9 w-24 bg-gray-200 rounded-lg"></div>
                    </div>
                </div>
            </header>
            {/* 대시보드 스켈레톤 */}
            <main className="container mx-auto p-6">
                <div className="h-8 w-1/3 bg-gray-200 rounded mb-6"></div>
                <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                    <div className="lg:col-span-2 space-y-6">
                        <div className="h-48 bg-white rounded-lg shadow p-6 space-y-4">
                            <div className="h-6 w-1/2 bg-gray-200 rounded"></div>
                            <div className="h-4 w-full bg-gray-200 rounded"></div>
                            <div className="h-4 w-3/4 bg-gray-200 rounded"></div>
                        </div>
                    </div>
                    <div className="lg:col-span-1">
                        <div className="h-48 bg-white rounded-lg shadow p-6 space-y-4">
                            <div className="h-6 w-1/2 bg-gray-200 rounded"></div>
                            <div className="h-4 w-full bg-gray-200 rounded"></div>
                            <div className="h-4 w-3/4 bg-gray-200 rounded"></div>
                        </div>
                    </div>
                </div>
            </main>
        </div>
    );
}
