import TodayScheduleCard from '@/components/dashboard/TodayScheduleCard';
import RecentActivityFeed from '@/components/dashboard/RecentActivityFeed';

export default function DashboardPage() {
    return (
        <div className="space-y-6">
            <h1 className="text-3xl font-bold text-gray-800">
                오늘의 대시보드
            </h1>
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                <div className="lg:col-span-2 space-y-6">
                    <TodayScheduleCard />
                    <RecentActivityFeed />
                </div>
                {/* ... */}
            </div>
        </div>
    );
}
