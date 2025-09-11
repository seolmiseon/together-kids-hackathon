// GPS 위치 추적을 위한 TypeScript 유틸리티
// 프론트엔드에서 사용자 위치를 가져오는 함수들

// 타입 정의
export interface LocationData {
    latitude: number;
    longitude: number;
    accuracy: number;
    timestamp: Date;
}

export interface LocationPermissionState {
    state: 'granted' | 'denied' | 'prompt';
}

/**
 * 사용자의 현재 GPS 위치를 가져옵니다
 * @returns {Promise<LocationData>} 위치 데이터
 */
export async function getCurrentLocation(): Promise<LocationData> {
    return new Promise((resolve, reject) => {
        // GPS 지원 여부 확인
        if (!navigator.geolocation) {
            reject(
                new Error('이 브라우저는 GPS 위치 서비스를 지원하지 않습니다.')
            );
            return;
        }

        // GPS 옵션 설정
        const options: PositionOptions = {
            enableHighAccuracy: true, // 높은 정확도 요청
            timeout: 10000, // 10초 타임아웃
            maximumAge: 300000, // 5분 캐시 허용
        };

        navigator.geolocation.getCurrentPosition(
            (position: GeolocationPosition) => {
                const { latitude, longitude, accuracy } = position.coords;

                console.log(
                    `📍 GPS 위치 획득: ${latitude}, ${longitude} (정확도: ${accuracy}m)`
                );

                resolve({
                    latitude,
                    longitude,
                    accuracy,
                    timestamp: new Date(),
                });
            },
            (error: GeolocationPositionError) => {
                let errorMessage = '';

                switch (error.code) {
                    case error.PERMISSION_DENIED:
                        errorMessage =
                            '위치 접근이 거부되었습니다. 브라우저 설정에서 위치 권한을 허용해주세요.';
                        break;
                    case error.POSITION_UNAVAILABLE:
                        errorMessage = '위치 정보를 사용할 수 없습니다.';
                        break;
                    case error.TIMEOUT:
                        errorMessage = '위치 요청 시간이 초과되었습니다.';
                        break;
                    default:
                        errorMessage =
                            '위치를 가져오는 중 오류가 발생했습니다.';
                        break;
                }

                console.error('GPS 오류:', errorMessage);
                reject(new Error(errorMessage));
            },
            options
        );
    });
}

/**
 * 지속적으로 위치를 추적합니다 (실시간 위치)
 * @param onLocationUpdate - 위치 업데이트 콜백
 * @param onError - 오류 콜백
 * @returns watchId - 추적 중단을 위한 ID
 */
export function watchLocation(
    onLocationUpdate: (location: LocationData) => void,
    onError: (error: GeolocationPositionError) => void
): number | null {
    if (!navigator.geolocation) {
        onError(
            new GeolocationPositionError() // TypeScript 호환
        );
        return null;
    }

    const options: PositionOptions = {
        enableHighAccuracy: true,
        timeout: 10000,
        maximumAge: 60000, // 1분 캐시
    };

    const watchId = navigator.geolocation.watchPosition(
        (position: GeolocationPosition) => {
            const { latitude, longitude, accuracy } = position.coords;

            onLocationUpdate({
                latitude,
                longitude,
                accuracy,
                timestamp: new Date(),
            });
        },
        (error: GeolocationPositionError) => {
            onError(error);
        },
        options
    );

    return watchId;
}

/**
 * 위치 추적을 중단합니다
 * @param watchId - watchLocation에서 반환된 ID
 */
export function stopWatchingLocation(watchId: number | null): void {
    if (watchId && navigator.geolocation) {
        navigator.geolocation.clearWatch(watchId);
        console.log('📍 GPS 위치 추적 중단됨');
    }
}

/**
 * 사용자에게 위치 권한 요청
 * @returns 권한 허용 여부
 */
export async function requestLocationPermission(): Promise<boolean> {
    try {
        // 권한 API 지원 여부 확인
        if ('permissions' in navigator) {
            const permission = await navigator.permissions.query({
                name: 'geolocation',
            });

            if (permission.state === 'granted') {
                return true;
            } else if (permission.state === 'prompt') {
                // 사용자에게 권한 요청
                const location = await getCurrentLocation();
                return !!location;
            } else {
                return false;
            }
        } else {
            // 권한 API 미지원 시 직접 위치 요청
            const location = await getCurrentLocation();
            return !!location;
        }
    } catch (error) {
        console.error('위치 권한 요청 오류:', error);
        return false;
    }
}

/**
 * 두 GPS 좌표 간의 거리를 계산합니다 (하버사인 공식)
 * @param lat1 - 첫 번째 위도
 * @param lon1 - 첫 번째 경도
 * @param lat2 - 두 번째 위도
 * @param lon2 - 두 번째 경도
 * @returns 거리 (미터)
 */
export function calculateDistance(
    lat1: number,
    lon1: number,
    lat2: number,
    lon2: number
): number {
    const R = 6371000; // 지구 반지름 (미터)

    const lat1Rad = (lat1 * Math.PI) / 180;
    const lat2Rad = (lat2 * Math.PI) / 180;
    const deltaLatRad = ((lat2 - lat1) * Math.PI) / 180;
    const deltaLonRad = ((lon2 - lon1) * Math.PI) / 180;

    const a =
        Math.sin(deltaLatRad / 2) * Math.sin(deltaLatRad / 2) +
        Math.cos(lat1Rad) *
            Math.cos(lat2Rad) *
            Math.sin(deltaLonRad / 2) *
            Math.sin(deltaLonRad / 2);

    const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a));

    return R * c; // 거리 (미터)
}

/**
 * 거리를 사람이 읽기 쉬운 형태로 변환
 * @param meters - 거리 (미터)
 * @returns 형식화된 거리 문자열
 */
export function formatDistance(meters: number): string {
    if (meters < 1000) {
        return `${Math.round(meters)}m`;
    } else {
        return `${(meters / 1000).toFixed(1)}km`;
    }
}

/**
 * 도보 시간 계산
 * @param meters - 거리 (미터)
 * @returns 도보 시간 (분)
 */
export function calculateWalkingTime(meters: number): number {
    const walkingSpeedMPerMin = 67; // 평균 도보 속도 67m/분 (4km/h)
    return Math.round(meters / walkingSpeedMPerMin);
}

/**
 * 차량 이동 시간 계산
 * @param meters - 거리 (미터)
 * @returns 차량 이동 시간 (분)
 */
export function calculateDrivingTime(meters: number): number {
    const drivingSpeedMPerMin = 500; // 시내 평균 속도 500m/분 (30km/h)
    return Math.round(meters / drivingSpeedMPerMin);
}

/**
 * 두 위치가 지정된 거리 내에 있는지 확인
 * @param lat1 - 첫 번째 위도
 * @param lon1 - 첫 번째 경도
 * @param lat2 - 두 번째 위도
 * @param lon2 - 두 번째 경도
 * @param maxDistance - 최대 거리 (미터)
 * @returns 거리 내 위치 여부
 */
export function isWithinDistance(
    lat1: number,
    lon1: number,
    lat2: number,
    lon2: number,
    maxDistance: number
): boolean {
    const distance = calculateDistance(lat1, lon1, lat2, lon2);
    return distance <= maxDistance;
}

// 사용 예제 (TypeScript)
/*
import { 
    getCurrentLocation, 
    calculateDistance, 
    formatDistance,
    LocationData 
} from '@/utils/gpsUtils';

const LocationComponent: React.FC = () => {
    const [location, setLocation] = useState<LocationData | null>(null);
    const [loading, setLoading] = useState<boolean>(false);
    const [error, setError] = useState<string | null>(null);

    const getLocation = async (): Promise<void> => {
        setLoading(true);
        setError(null);
        
        try {
            const currentLocation = await getCurrentLocation();
            setLocation(currentLocation);
            
            // 거리 계산 예제
            const distance = calculateDistance(
                currentLocation.latitude,
                currentLocation.longitude,
                37.5663, // 서울시청
                126.9779
            );
            
            console.log(`거리: ${formatDistance(distance)}`);
        } catch (err) {
            setError(err instanceof Error ? err.message : '오류 발생');
        } finally {
            setLoading(false);
        }
    };

    return (
        <div>
            <button onClick={getLocation} disabled={loading}>
                {loading ? '위치 가져오는 중...' : '내 위치 찾기'}
            </button>
            
            {location && (
                <div>
                    <p>위도: {location.latitude}</p>
                    <p>경도: {location.longitude}</p>
                    <p>정확도: {location.accuracy}m</p>
                </div>
            )}
            
            {error && <p style={{color: 'red'}}>오류: {error}</p>}
        </div>
    );
};
*/
