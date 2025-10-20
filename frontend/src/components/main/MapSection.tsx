'use client';

import { useEffect, useState, useRef, useLayoutEffect } from 'react';
import { getAuth } from 'firebase/auth';
import { useUserStore } from '@/store/userStore';
import LoadingSkeleton from '@/components/ui/LoadingSkeleton';

// 자녀 데이터 타입 정의
interface Child {
    id: string;
    name: string;
    school: string;
    grade: number;
    location?: {
        lat: number;
        lng: number;
        address?: string;
        last_updated?: string;
    };
}

// 부모 위치 데이터 타입 정의
interface ParentLocation {
    uid: string;
    full_name: string;
    location: {
        lat: number;
        lng: number;
        address?: string;
        last_updated?: string;
    };
}

// AI 검색 결과 장소 타입 정의
interface SearchPlace {
    id: string;
    name: string;
    address: string;
    lat: number;
    lng: number;
    category?: string;
    phone?: string;
    description?: string;
}

// Naver Maps 타입 선언
declare global {
    interface Window {
        naver: any;
    }
}

const MapSection = () => {
    const { user } = useUserStore();
    const [children, setChildren] = useState<Child[]>([]);
    const [nearbyParents, setNearbyParents] = useState<ParentLocation[]>([]);
    const [searchPlaces, setSearchPlaces] = useState<SearchPlace[]>([]); // AI 검색 결과 장소들
    const [currentUserLocation, setCurrentUserLocation] = useState<{
        lat: number;
        lng: number;
        address?: string;
    } | null>(null);
    const [markers, setMarkers] = useState<any[]>([]);
    const [isLoading, setIsLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);
    const [locationPermission, setLocationPermission] = useState<
        'granted' | 'denied' | 'prompt' | null
    >(null);
    const [isTrackingLocation, setIsTrackingLocation] = useState(false);
    const [isMapReady, setIsMapReady] = useState(false); // 🚀 현업 스타일: 지도 준비 상태 추가

    // 현업 스타일: ref로 DOM 참조 (RAG의 VectorDB 같은 역할!)
    const mapContainerRef = useRef<HTMLDivElement>(null);
    const mapInstanceRef = useRef<any>(null);
    const watchIdRef = useRef<number | null>(null);
    const retryCountRef = useRef(0); // 🚀 현업 스타일: 재시도 카운터

    // 간단한 Naver Maps API 로드
    useEffect(() => {
        if (window.naver?.maps) {
            setIsLoading(false);
            return;
        }

        const script = document.createElement('script');
        // 새로운 네이버 클라우드 플랫폼 Maps API URL
        const apiUrl = `https://oapi.map.naver.com/openapi/v3/maps.js?ncpKeyId=${process.env.NEXT_PUBLIC_NAVER_MAP_CLIENT_ID}`;
        console.log('🌐 Maps API URL:', apiUrl);

        script.src = apiUrl;
        script.onload = () => {
            console.log('✅ API 로드 성공');
            setIsLoading(false);
        };
        script.onerror = (e) => {
            console.error('❌ API 로드 실패:', e);
            setError('지도 API 로드 실패');
        };

        document.head.appendChild(script);
    }, []);

    // 현업 스타일: 간단하고 확실한 지도 초기화
    useLayoutEffect(() => {
        // 조건이 모두 충족될 때까지 기다림
        if (
            !user ||
            isLoading ||
            !window.naver?.maps ||
            !mapContainerRef.current ||
            mapInstanceRef.current
        ) {
            return;
        }

        console.log('🗺️ 지도 생성 시작');

        // 컨테이너 크기 확인
        const containerRect = mapContainerRef.current.getBoundingClientRect();
        console.log('📦 지도 컨테이너 크기:', {
            width: containerRect.width,
            height: containerRect.height,
            offsetWidth: mapContainerRef.current.offsetWidth,
            offsetHeight: mapContainerRef.current.offsetHeight,
        });

        // 네이버 클라우드 플랫폼 - Client ID와 함께 지도 생성
        mapInstanceRef.current = new window.naver.maps.Map(
            mapContainerRef.current,
            {
                center: new window.naver.maps.LatLng(37.5665, 126.978),
                zoom: 10,
                mapTypeControl: true,
                scaleControl: false,
                logoControl: false,
                zoomControl: true,
            }
        );

        console.log('✅ 지도 생성 완료');

        // 지도 크기 강제 조정
        setTimeout(() => {
            if (mapInstanceRef.current) {
                window.naver.maps.Event.trigger(
                    mapInstanceRef.current,
                    'resize'
                );
                console.log('🔄 지도 크기 조정 완료');
            }
        }, 100);
    }, [user, isLoading]); // 간단한 의존성

    // 자녀 데이터 로드
    useEffect(() => {
        if (!user?.id) {
            setChildren([]);
            return;
        }

        const fetchChildren = async () => {
            try {
                const auth = getAuth();
                const token = await auth.currentUser?.getIdToken();
                if (!token) return;

                const response = await fetch(
                    `${process.env.NEXT_PUBLIC_API_URL}/children/`,
                    {
                        headers: {
                            Authorization: `Bearer ${token}`,
                            'Content-Type': 'application/json',
                        },
                    }
                );

                if (response.ok) {
                    const data = await response.json();
                    setChildren(data.children || []);
                }
            } catch (error) {
                console.error('❌ 자녀 데이터 로드 실패:', error);
            }
        };

        fetchChildren();
    }, [user?.id]);

    // 위치 권한 확인 및 추적 시작
    useEffect(() => {
        if (!user?.id || !navigator.geolocation) return;

        // 위치 권한 상태 확인
        if ('permissions' in navigator) {
            navigator.permissions
                .query({ name: 'geolocation' })
                .then((result) => {
                    setLocationPermission(result.state as any);

                    result.addEventListener('change', () => {
                        setLocationPermission(result.state as any);
                    });
                });
        }
    }, [user?.id]);

    // 위치 추적 시작/중지
    const toggleLocationTracking = async () => {
        if (!navigator.geolocation) {
            alert('이 브라우저는 위치 서비스를 지원하지 않습니다.');
            return;
        }

        if (isTrackingLocation) {
            // 추적 중지
            if (watchIdRef.current !== null) {
                navigator.geolocation.clearWatch(watchIdRef.current);
                watchIdRef.current = null;
            }
            setIsTrackingLocation(false);
            console.log('📍 위치 추적 중지');
        } else {
            // 추적 시작
            setIsTrackingLocation(true);
            console.log('📍 위치 추적 시작');

            const options = {
                enableHighAccuracy: true,
                timeout: 10000,
                maximumAge: 60000, // 1분
            };

            // 즉시 현재 위치 가져오기
            navigator.geolocation.getCurrentPosition(
                (position) => updateLocationToServer(position),
                (error) => {
                    console.error('❌ 현재 위치 가져오기 실패:', error);
                    setIsTrackingLocation(false);
                },
                options
            );

            // 지속적 위치 추적
            watchIdRef.current = navigator.geolocation.watchPosition(
                (position) => updateLocationToServer(position),
                (error) => {
                    console.error('❌ 위치 추적 오류:', error);
                    setIsTrackingLocation(false);
                },
                options
            );
        }
    };

    // 🔍 AI 검색 결과를 지도에 표시하는 함수
    const displaySearchResults = (places: SearchPlace[]) => {
        console.log('🔍 AI 검색 결과를 지도에 표시:', places);
        setSearchPlaces(places);

        // 검색 결과가 있으면 해당 지역으로 지도 이동
        if (places.length > 0 && mapInstanceRef.current) {
            const firstPlace = places[0];
            const bounds = new window.naver.maps.LatLngBounds();

            // 검색된 장소들을 모두 포함하는 범위 계산
            places.forEach((place) => {
                bounds.extend(
                    new window.naver.maps.LatLng(place.lat, place.lng)
                );
            });

            // 내 위치도 포함
            if (currentUserLocation) {
                bounds.extend(
                    new window.naver.maps.LatLng(
                        currentUserLocation.lat,
                        currentUserLocation.lng
                    )
                );
            }

            mapInstanceRef.current.fitBounds(bounds, {
                top: 60,
                right: 60,
                bottom: 60,
                left: 60,
            });
        }
    };

    // 📍 현재 위치 즉시 가져오기 (마커 표시용)
    const getCurrentLocation = () => {
        if (!navigator.geolocation) {
            alert('이 브라우저는 위치 서비스를 지원하지 않습니다.');
            return;
        }

        navigator.geolocation.getCurrentPosition(
            (position) => {
                const { latitude, longitude } = position.coords;
                console.log('📍 현재 위치 획득:', latitude, longitude);

                setCurrentUserLocation({
                    lat: latitude,
                    lng: longitude,
                    address: undefined,
                });

                // 지도 중심을 현재 위치로 이동
                if (mapInstanceRef.current) {
                    mapInstanceRef.current.setCenter(
                        new window.naver.maps.LatLng(latitude, longitude)
                    );
                    mapInstanceRef.current.setZoom(15);
                }
            },
            (error) => {
                console.error('❌ 현재 위치 가져오기 실패:', error);
                alert(
                    '현재 위치를 가져올 수 없습니다. 위치 권한을 확인해주세요.'
                );
            },
            {
                enableHighAccuracy: true,
                timeout: 10000,
                maximumAge: 60000,
            }
        );
    };

    // MapSection 컴포넌트를 전역에서 접근 가능하게 함 (AI 검색 결과 표시용)
    useEffect(() => {
        if (typeof window !== 'undefined') {
            (window as any).displaySearchResults = displaySearchResults;
        }

        return () => {
            if (typeof window !== 'undefined') {
                delete (window as any).displaySearchResults;
            }
        };
    }, [currentUserLocation]);

    // 서버에 위치 업데이트
    const updateLocationToServer = async (position: GeolocationPosition) => {
        try {
            const auth = getAuth();
            const token = await auth.currentUser?.getIdToken();
            if (!token) return;

            const { latitude, longitude } = position.coords;

            // 역지오코딩으로 주소 가져오기 (선택사항)
            let address = '';
            try {
                if (window.naver?.maps?.Service) {
                    window.naver.maps.Service.reverseGeocode(
                        {
                            coords: new window.naver.maps.LatLng(
                                latitude,
                                longitude
                            ),
                        },
                        (status: any, response: any) => {
                            if (
                                status === window.naver.maps.Service.Status.OK
                            ) {
                                const result = response.v2;
                                if (result.address) {
                                    address =
                                        result.address.jibunAddress ||
                                        result.address.roadAddress ||
                                        '';
                                }
                            }
                        }
                    );
                }
            } catch (e) {
                console.log('역지오코딩 실패, 좌표만 저장');
            }

            const locationData = {
                lat: latitude,
                lng: longitude,
                address: address,
            };

            const response = await fetch(
                `${process.env.NEXT_PUBLIC_API_URL}/users/location`,
                {
                    method: 'PUT',
                    headers: {
                        Authorization: `Bearer ${token}`,
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify(locationData),
                }
            );

            if (response.ok) {
                console.log('✅ 위치 업데이트 성공:', locationData);

                // 현재 사용자 위치 상태 업데이트
                setCurrentUserLocation({
                    lat: latitude,
                    lng: longitude,
                    address: address || undefined,
                });

                // 다른 부모들 위치도 새로 가져오기
                fetchNearbyParents();
            }
        } catch (error) {
            console.error('❌ 위치 업데이트 실패:', error);
        }
    };

    // 근처 부모들 위치 가져오기
    const fetchNearbyParents = async () => {
        try {
            const auth = getAuth();
            const token = await auth.currentUser?.getIdToken();
            if (!token) return;

            const response = await fetch(
                `${process.env.NEXT_PUBLIC_API_URL}/users/nearby-parents`,
                {
                    headers: {
                        Authorization: `Bearer ${token}`,
                        'Content-Type': 'application/json',
                    },
                }
            );

            if (response.ok) {
                const data = await response.json();
                setNearbyParents(data.nearby_parents || []);
            }
        } catch (error) {
            console.error('❌ 근처 부모 데이터 로드 실패:', error);
        }
    };

    // 컴포넌트 언마운트 시 위치 추적 정리
    useEffect(() => {
        return () => {
            if (watchIdRef.current !== null) {
                navigator.geolocation.clearWatch(watchIdRef.current);
            }
        };
    }, []);

    // 마커 업데이트 (자녀 + 부모)
    useEffect(() => {
        if (!mapInstanceRef.current || !window.naver?.maps) return;

        // 기존 마커 제거
        markers.forEach((marker) => marker?.setMap?.(null));
        setMarkers([]);

        const newMarkers: any[] = [];

        // 🔥 내 위치 마커 생성 (최우선!)
        if (currentUserLocation?.lat && currentUserLocation?.lng) {
            console.log('🔥 내 위치 마커 생성 시작:', currentUserLocation);
            console.log('🔥 지도 인스턴스:', mapInstanceRef.current);
            console.log('🔥 네이버 지도 API:', window.naver?.maps);

            // 🔥 기본 마커로도 테스트
            const basicMarker = new window.naver.maps.Marker({
                position: new window.naver.maps.LatLng(
                    currentUserLocation.lat,
                    currentUserLocation.lng
                ),
                map: mapInstanceRef.current,
                title: '내 위치 (기본 마커)',
            });

            console.log('🔥 기본 마커도 생성:', basicMarker);
            newMarkers.push(basicMarker);

            const myLocationMarker = new window.naver.maps.Marker({
                position: new window.naver.maps.LatLng(
                    currentUserLocation.lat,
                    currentUserLocation.lng
                ),
                map: mapInstanceRef.current,
                title: '내 위치',
                zIndex: 1000, // 다른 마커보다 위에 표시
                icon: {
                    content: `
                        <div style="
                            width: 20px;
                            height: 20px;
                            background: #ef4444;
                            border: 3px solid white;
                            border-radius: 50%;
                            box-shadow: 0 2px 4px rgba(0,0,0,0.3);
                        "></div>
                    `,
                    size: new window.naver.maps.Size(20, 20),
                    anchor: new window.naver.maps.Point(10, 10),
                },
            });

            console.log('🔥 마커 생성됨:', myLocationMarker);

            // 마커 위치로 지도 중심 이동
            mapInstanceRef.current.setCenter(
                new window.naver.maps.LatLng(
                    currentUserLocation.lat,
                    currentUserLocation.lng
                )
            );
            mapInstanceRef.current.setZoom(15);

            // 내 위치 정보창
            const myInfoWindow = new window.naver.maps.InfoWindow({
                content: `
                    <div style="padding: 12px; max-width: 220px;">
                        <h4 style="margin: 0 0 8px 0; color: #ef4444; font-weight: bold;">📍 내 현재 위치</h4>
                        <p style="margin: 0; font-size: 13px; color: #666;">
                            ${user?.name || '사용자'}님의 위치
                        </p>
                        ${
                            currentUserLocation.address
                                ? `
                            <p style="margin: 8px 0 0 0; font-size: 12px; color: #888; line-height: 1.4;">
                                📍 ${currentUserLocation.address}
                            </p>
                        `
                                : ''
                        }
                    </div>
                `,
            });

            window.naver.maps.Event.addListener(
                myLocationMarker,
                'click',
                () => {
                    myInfoWindow.open(mapInstanceRef.current, myLocationMarker);
                }
            );

            newMarkers.push(myLocationMarker);
        }

        // 자녀 마커 생성
        children
            .filter((child) => child.location?.lat && child.location?.lng)
            .forEach((child) => {
                const marker = new window.naver.maps.Marker({
                    position: new window.naver.maps.LatLng(
                        child.location!.lat,
                        child.location!.lng
                    ),
                    map: mapInstanceRef.current,
                    title: child.name,
                    icon: {
                        content: `
                            <div style="
                                background: #3b82f6;
                                color: white;
                                padding: 4px 8px;
                                border-radius: 20px;
                                font-size: 12px;
                                font-weight: bold;
                                border: 2px solid white;
                                box-shadow: 0 2px 4px rgba(0,0,0,0.2);
                                white-space: nowrap;
                            ">
                                👶 ${child.name}
                            </div>
                        `,
                        size: new window.naver.maps.Size(22, 35),
                        anchor: new window.naver.maps.Point(11, 35),
                    },
                });

                // 자녀 정보창
                const infoWindow = new window.naver.maps.InfoWindow({
                    content: `
                        <div style="padding: 10px; max-width: 200px;">
                            <h4 style="margin: 0 0 5px 0; color: #333;">👶 ${
                                child.name
                            }</h4>
                            <p style="margin: 0; font-size: 12px; color: #666;">
                                ${child.school} ${child.grade}학년
                            </p>
                            ${
                                child.location?.address
                                    ? `
                                <p style="margin: 5px 0 0 0; font-size: 11px; color: #888;">
                                    ${child.location.address}
                                </p>
                            `
                                    : ''
                            }
                        </div>
                    `,
                });

                window.naver.maps.Event.addListener(marker, 'click', () => {
                    infoWindow.open(mapInstanceRef.current, marker);
                });

                newMarkers.push(marker);
            });

        // 부모 마커 생성
        nearbyParents.forEach((parent) => {
            const marker = new window.naver.maps.Marker({
                position: new window.naver.maps.LatLng(
                    parent.location.lat,
                    parent.location.lng
                ),
                map: mapInstanceRef.current,
                title: parent.full_name,
                icon: {
                    content: `
                        <div style="
                            background: #10b981;
                            color: white;
                            padding: 4px 8px;
                            border-radius: 20px;
                            font-size: 12px;
                            font-weight: bold;
                            border: 2px solid white;
                            box-shadow: 0 2px 4px rgba(0,0,0,0.2);
                            white-space: nowrap;
                        ">
                            👩‍👧‍👦 ${parent.full_name}
                        </div>
                    `,
                    size: new window.naver.maps.Size(22, 35),
                    anchor: new window.naver.maps.Point(11, 35),
                },
            });

            // 부모 정보창
            const infoWindow = new window.naver.maps.InfoWindow({
                content: `
                    <div style="padding: 10px; max-width: 200px;">
                        <h4 style="margin: 0 0 5px 0; color: #333;">👩‍👧‍👦 ${
                            parent.full_name
                        }</h4>
                        <p style="margin: 0; font-size: 12px; color: #666;">
                            근처에 있는 부모님
                        </p>
                        ${
                            parent.location?.address
                                ? `
                            <p style="margin: 5px 0 0 0; font-size: 11px; color: #888;">
                                ${parent.location.address}
                            </p>
                        `
                                : ''
                        }
                        <p style="margin: 5px 0 0 0; font-size: 10px; color: #999;">
                            ${new Date(
                                parent.location.last_updated || ''
                            ).toLocaleString()}
                        </p>
                    </div>
                `,
            });

            window.naver.maps.Event.addListener(marker, 'click', () => {
                infoWindow.open(mapInstanceRef.current, marker);
            });

            newMarkers.push(marker);
        });

        // 🔍 AI 검색 결과 장소 마커 생성
        searchPlaces.forEach((place) => {
            const marker = new window.naver.maps.Marker({
                position: new window.naver.maps.LatLng(place.lat, place.lng),
                map: mapInstanceRef.current,
                title: place.name,
                icon: {
                    content: `
                        <div style="
                            background: #f59e0b;
                            color: white;
                            padding: 6px 10px;
                            border-radius: 20px;
                            font-size: 12px;
                            font-weight: bold;
                            border: 2px solid white;
                            box-shadow: 0 3px 6px rgba(0,0,0,0.3);
                            white-space: nowrap;
                        ">
                            🔍 ${place.name}
                        </div>
                    `,
                    size: new window.naver.maps.Size(22, 35),
                    anchor: new window.naver.maps.Point(11, 35),
                },
            });

            // 장소 정보창
            const infoWindow = new window.naver.maps.InfoWindow({
                content: `
                    <div style="padding: 12px; max-width: 240px;">
                        <h4 style="margin: 0 0 8px 0; color: #f59e0b; font-weight: bold;">🔍 ${
                            place.name
                        }</h4>
                        <p style="margin: 0 0 6px 0; font-size: 13px; color: #333;">
                            ${place.category || '장소'}
                        </p>
                        <p style="margin: 0 0 8px 0; font-size: 12px; color: #666; line-height: 1.4;">
                            📍 ${place.address}
                        </p>
                        ${
                            place.phone
                                ? `
                            <p style="margin: 0 0 8px 0; font-size: 12px; color: #666;">
                                📞 ${place.phone}
                            </p>
                        `
                                : ''
                        }
                        ${
                            place.description
                                ? `
                            <p style="margin: 0 0 8px 0; font-size: 12px; color: #888; line-height: 1.3;">
                                ${place.description}
                            </p>
                        `
                                : ''
                        }
                        <div style="margin-top: 10px; display: flex; gap: 6px;">
                            <button onclick="
                                // 🔧 강력한 장소명 정제 로직
                                let searchTerm = '${place.name}';
                                console.log('🔍 네이버지도 검색 원본:', searchTerm);
                                
                                // 패턴 매칭으로 실제 장소명만 추출
                                if (searchTerm.includes(' 에서는') || searchTerm.includes(' 에서')) {
                                    searchTerm = searchTerm.split(/ 에서[는]?/)[0];
                                }
                                if (searchTerm.includes('는 ') || searchTerm.includes('은 ')) {
                                    searchTerm = searchTerm.split(/[는은] /)[0];
                                }
                                if (searchTerm.includes('이 ') || searchTerm.includes('가 ')) {
                                    searchTerm = searchTerm.split(/[이가] /)[0];
                                }
                                
                                // 특수문자 제거 및 길이 제한
                                searchTerm = searchTerm.replace(/[^가-힣a-zA-Z0-9\\s]/g, '').trim();
                                const words = searchTerm.split(' ').filter(w => w.length > 0);
                                if (words.length > 2) {
                                    searchTerm = words.slice(0, 2).join(' '); // 최대 2단어
                                }
                                
                                console.log('✅ 네이버지도 검색 정제됨:', searchTerm);
                                window.open('https://map.naver.com/p/search/' + encodeURIComponent(searchTerm));
                            " 
                                style="background: #03C75A; color: white; border: none; padding: 6px 12px; border-radius: 15px; font-size: 11px; cursor: pointer;">
                                네이버지도
                            </button>
                            <button onclick="navigator.clipboard?.writeText('${
                                place.address
                            }').then(() => alert('주소가 복사되었습니다!'))" 
                                style="background: #6b7280; color: white; border: none; padding: 6px 12px; border-radius: 15px; font-size: 11px; cursor: pointer;">
                                주소복사
                            </button>
                        </div>
                    </div>
                `,
            });

            window.naver.maps.Event.addListener(marker, 'click', () => {
                infoWindow.open(mapInstanceRef.current, marker);
            });

            newMarkers.push(marker);
        });

        setMarkers(newMarkers);

        // 지도 범위 조정
        if (newMarkers.length > 0) {
            const bounds = new window.naver.maps.LatLngBounds();

            children.forEach((child) => {
                if (child.location?.lat && child.location?.lng) {
                    bounds.extend(
                        new window.naver.maps.LatLng(
                            child.location.lat,
                            child.location.lng
                        )
                    );
                }
            });

            nearbyParents.forEach((parent) => {
                bounds.extend(
                    new window.naver.maps.LatLng(
                        parent.location.lat,
                        parent.location.lng
                    )
                );
            });

            // AI 검색 결과 장소들도 범위에 포함
            searchPlaces.forEach((place) => {
                bounds.extend(
                    new window.naver.maps.LatLng(place.lat, place.lng)
                );
            });

            mapInstanceRef.current.fitBounds(bounds, {
                top: 50,
                right: 50,
                bottom: 50,
                left: 50,
            });
        }
    }, [children, nearbyParents, searchPlaces]); // searchPlaces 의존성 추가

    // 🔥 지도 클릭 이벤트 추가 - UX 개선
    useEffect(() => {
        if (!mapInstanceRef.current || !window.naver?.maps) return;

        // 지도 클릭 이벤트 리스너
        const mapClickListener = window.naver.maps.Event.addListener(
            mapInstanceRef.current,
            'click',
            (e: any) => {
                const clickedLatLng = e.coord || e.latlng;
                if (!clickedLatLng) return;

                const lat = clickedLatLng.lat();
                const lng = clickedLatLng.lng();
                
                console.log('🗺️ 지도 클릭됨:', { lat, lng });

                // 역지오코딩으로 주소 가져오기
                if (window.naver?.maps?.Service) {
                    window.naver.maps.Service.reverseGeocode(
                        {
                            coords: new window.naver.maps.LatLng(lat, lng),
                        },
                        (status: any, response: any) => {
                            let address = '';
                            if (status === window.naver.maps.Service.Status.OK) {
                                const result = response.v2;
                                if (result.address) {
                                    address = result.address.jibunAddress || 
                                             result.address.roadAddress || 
                                             `위도: ${lat.toFixed(4)}, 경도: ${lng.toFixed(4)}`;
                                }
                            } else {
                                address = `위도: ${lat.toFixed(4)}, 경도: ${lng.toFixed(4)}`;
                            }

                            // 클릭 위치에 임시 마커 표시
                            const clickMarker = new window.naver.maps.Marker({
                                position: new window.naver.maps.LatLng(lat, lng),
                                map: mapInstanceRef.current,
                                title: '클릭한 위치',
                                icon: {
                                    content: `
                                        <div style="
                                            width: 12px;
                                            height: 12px;
                                            background: #ef4444;
                                            border: 2px solid white;
                                            border-radius: 50%;
                                            box-shadow: 0 2px 4px rgba(0,0,0,0.3);
                                            animation: pulse 2s infinite;
                                        "></div>
                                        <style>
                                            @keyframes pulse {
                                                0% { transform: scale(1); opacity: 1; }
                                                50% { transform: scale(1.2); opacity: 0.7; }
                                                100% { transform: scale(1); opacity: 1; }
                                            }
                                        </style>
                                    `,
                                    size: new window.naver.maps.Size(12, 12),
                                    anchor: new window.naver.maps.Point(6, 6),
                                },
                            });

                            // 클릭 정보를 채팅으로 전달
                            const clickInfo = {
                                type: 'map_click',
                                lat,
                                lng,
                                address,
                                timestamp: new Date().toISOString(),
                            };

                            // 전역 이벤트로 채팅 컴포넌트에 전달
                            if (typeof window !== 'undefined') {
                                (window as any).lastMapClick = clickInfo;
                                
                                // 커스텀 이벤트 발송
                                const mapClickEvent = new CustomEvent('mapClick', {
                                    detail: clickInfo
                                });
                                window.dispatchEvent(mapClickEvent);
                            }

                            console.log('🎯 지도 클릭 정보 전달:', clickInfo);

                            // 3초 후 임시 마커 제거
                            setTimeout(() => {
                                clickMarker.setMap(null);
                            }, 3000);
                        }
                    );
                }
            }
        );

        // 컴포넌트 언마운트 시 이벤트 리스너 제거
        return () => {
            if (mapClickListener) {
                window.naver.maps.Event.removeListener(mapClickListener);
            }
        };
    }, [mapInstanceRef.current]);

    // 로그인 필요
    if (!user) {
        return (
            <div className="flex items-center justify-center h-full bg-gray-50">
                <div className="text-center">
                    <p className="text-gray-600 mb-4">
                        지도를 보려면 로그인이 필요합니다
                    </p>
                    <button
                        onClick={() => (window.location.href = '/auth/login')}
                        className="bg-blue-500 text-white px-6 py-2 rounded-lg hover:bg-blue-600 transition-colors"
                    >
                        로그인하기
                    </button>
                </div>
            </div>
        );
    }

    // 에러 상태
    if (error) {
        return (
            <div className="flex items-center justify-center h-full bg-red-50">
                <div className="text-center">
                    <p className="text-red-600 mb-2">
                        지도 로드 중 오류가 발생했습니다
                    </p>
                    <p className="text-sm text-red-500">{error}</p>
                    <button
                        onClick={() => window.location.reload()}
                        className="mt-4 bg-red-500 text-white px-4 py-2 rounded hover:bg-red-600 transition-colors"
                    >
                        새로고침
                    </button>
                </div>
            </div>
        );
    }

    // 로딩 상태 - LoadingSkeleton 사용
    if (isLoading) {
        return <LoadingSkeleton />;
    }

    // 메인 렌더링 - 현업 스타일: ref 사용
    return (
        <div
            className="relative w-full"
            style={{ height: 'calc(100vh - 5rem)' }}
        >
            {/* 위치 추적 제어 버튼 */}
            <div className="absolute top-4 right-4 z-10 space-y-2">
                {/* 🔥 의정부 테스트 버튼 */}
                {process.env.NODE_ENV === 'development' && (
                    <button
                        onClick={() => {
                            const testLocation = {
                                lat: 37.7379,
                                lng: 127.0477,
                                address: '의정부 (테스트)',
                            };
                            setCurrentUserLocation(testLocation);
                            console.log(
                                '🧪 의정부 테스트 위치 설정:',
                                testLocation
                            );
                        }}
                        className="bg-purple-500 hover:bg-purple-600 text-white px-3 py-1.5 rounded-lg font-medium text-xs shadow-lg transition-all block w-full"
                    >
                        🌳 의정부 테스트
                    </button>
                )}

                {/* 위치 추적 토글 버튼 */}
                <button
                    onClick={toggleLocationTracking}
                    disabled={locationPermission === 'denied'}
                    className={`
                        px-4 py-2 rounded-lg font-medium text-sm shadow-lg transition-all
                        ${
                            isTrackingLocation
                                ? 'bg-red-500 hover:bg-red-600 text-white'
                                : 'bg-green-500 hover:bg-green-600 text-white'
                        }
                        ${
                            locationPermission === 'denied'
                                ? 'opacity-50 cursor-not-allowed'
                                : ''
                        }
                    `}
                >
                    {isTrackingLocation ? '📍 추적 중지' : '📍 위치 추적'}
                </button>

                {/* 내 위치 즉시 표시 버튼 */}
                <button
                    onClick={getCurrentLocation}
                    className="px-4 py-2 bg-blue-500 hover:bg-blue-600 text-white rounded-lg font-medium text-sm shadow-lg transition-colors"
                >
                    📍 내 위치 표시
                </button>

                {/* 근처 부모 새로고침 버튼 */}
                <button
                    onClick={fetchNearbyParents}
                    className="block w-full px-4 py-2 bg-blue-500 hover:bg-blue-600 text-white rounded-lg font-medium text-sm shadow-lg transition-colors"
                >
                    🔄 근처 부모 찾기
                </button>

                {/* 위치 권한 상태 표시 */}
                {locationPermission === 'denied' && (
                    <div className="bg-red-100 border border-red-400 text-red-700 px-3 py-2 rounded text-xs">
                        위치 권한이 거부되었습니다
                    </div>
                )}
            </div>

            {/* 범례 */}
            <div className="absolute bottom-4 left-4 z-10 bg-white p-3 rounded-lg shadow-lg">
                <h4 className="font-medium text-sm mb-2">범례</h4>
                <div className="space-y-1 text-xs">
                    <div className="flex items-center">
                        <div className="w-4 h-4 bg-red-500 rounded mr-2"></div>
                        <span>
                            📍 내 위치 {currentUserLocation ? '✅' : '❌'}
                        </span>
                    </div>
                    <div className="flex items-center">
                        <div className="w-4 h-4 bg-blue-500 rounded mr-2"></div>
                        <span>👶 우리 아이</span>
                    </div>
                    <div className="flex items-center">
                        <div className="w-4 h-4 bg-green-500 rounded mr-2"></div>
                        <span>👩‍👧‍👦 근처 부모</span>
                    </div>
                    <div className="flex items-center">
                        <div className="w-4 h-4 bg-orange-500 rounded mr-2"></div>
                        <span>🔍 검색 장소</span>
                    </div>
                </div>
                <div className="mt-2 pt-2 border-t text-xs text-gray-600">
                    총 {children.length}명의 아이, {nearbyParents.length}명의
                    부모
                    {currentUserLocation && (
                        <div className="text-green-600 mt-1">
                            📍 위치: {currentUserLocation.lat.toFixed(4)},{' '}
                            {currentUserLocation.lng.toFixed(4)}
                        </div>
                    )}
                    {!currentUserLocation && (
                        <div className="text-red-600 mt-1">
                            📍 위치 추적 안됨 - 위치 추적 버튼을 눌러주세요
                        </div>
                    )}
                </div>
            </div>

            <div
                ref={mapContainerRef}
                className="w-full h-full bg-gray-200"
                style={{
                    minHeight: '500px',
                    height: '100%',
                    width: '100%',
                    position: 'relative',
                    zIndex: 1,
                }}
            />

            {children.length === 0 && nearbyParents.length === 0 && (
                <div className="absolute inset-0 flex items-center justify-center bg-white bg-opacity-90 pointer-events-none">
                    <div className="text-center">
                        <p className="text-gray-600 mb-2">
                            표시할 위치가 없습니다
                        </p>
                        <p className="text-sm text-gray-500">
                            자녀를 등록하고 위치 추적을 시작해보세요
                        </p>
                    </div>
                </div>
            )}
        </div>
    );
};

export default MapSection;
