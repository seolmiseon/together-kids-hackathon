import Header from '@/components/layout/Header';
import React from 'react';

export default function MainLayout({
    children,
}: {
    children: React.ReactNode;
}) {
    return (
        <div className="min-h-screen bg-gray-50">
            <Header />
            <main className="container mx-auto p-4 md:p-6">{children}</main>
        </div>
    );
}
