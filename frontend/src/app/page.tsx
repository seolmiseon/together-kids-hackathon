'use client';

import { useSession } from 'next-auth/react';
import { useRouter } from 'next/navigation';
import { useEffect } from 'react';
import LoadingSkeleton from '@/components/ui/LoadingSkeleton';

export default function GatekeeperPage() {
    const { data: session, status } = useSession();
    const router = useRouter();

    useEffect(() => {
        if (status === 'loading') {
            return;
        }

        if (status === 'authenticated') {
            router.replace('/dashboard');
        }

        if (status === 'unauthenticated') {
            router.replace('/auth/login');
        }
    }, [status, router]);

    return <LoadingSkeleton />;
}
