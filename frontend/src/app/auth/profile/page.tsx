'use client';

import { useState, ChangeEvent, FormEvent, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import Image from 'next/image';
import { getAuth, onAuthStateChanged } from 'firebase/auth';
import { useUserStore } from '@/store/userStore';

interface ChildInfo {
    id: number;
    name: string;
    age: string;
    school: string;
    imageFile: File | null;
    imageUrl: string | null;
}

export default function ProfileSetupPage() {
    const router = useRouter();
    const [parentName, setParentName] = useState('');
    const [apartment, setApartment] = useState('');
    const [children, setChildren] = useState<ChildInfo[]>([
        {
            id: 1,
            name: '',
            age: '',
            school: '',
            imageFile: null,
            imageUrl: null,
        },
    ]);
    const [isSubmitting, setIsSubmitting] = useState(false);
    const [isAuthenticated, setIsAuthenticated] = useState(false);
    
    // 🚀 Zustand 함수 가져오기
    const { handleProfileSetupComplete } = useUserStore();

    useEffect(() => {
        const initAuth = async () => {
            try {
                const auth = getAuth();
                const unsubscribe = onAuthStateChanged(auth, (user) => {
                    if (user) {
                        setIsAuthenticated(true);
                        setParentName(user.displayName || '');
                    } else {
                        setIsAuthenticated(false);
                        router.replace('/auth/login');
                    }
                });
                return () => unsubscribe();
            } catch (error) {
                console.error('Firebase Auth 초기화 오류:', error);
                setTimeout(() => {
                    router.replace('/auth/login');
                }, 1000);
            }
        };

        initAuth();
    }, [router]);

    const handleChildChange = (index: number, e: ChangeEvent<HTMLInputElement>) => {
        const { name, value } = e.target;
        const newChildren = [...children];
        newChildren[index] = { ...newChildren[index], [name]: value };
        setChildren(newChildren);
    };

    const handleImageChange = (index: number, e: ChangeEvent<HTMLInputElement>) => {
        if (e.target.files && e.target.files[0]) {
            const file = e.target.files[0];
            const newChildren = [...children];
            newChildren[index].imageFile = file;
            newChildren[index].imageUrl = URL.createObjectURL(file);
            setChildren(newChildren);
        }
    };

    const addChild = () => {
        setChildren([
            ...children,
            {
                id: Date.now(),
                name: '',
                age: '',
                school: '',
                imageFile: null,
                imageUrl: null,
            },
        ]);
    };

    const removeChild = (index: number) => {
        const newChildren = children.filter((_, i) => i !== index);
        setChildren(newChildren);
    };

    const handleSubmit = async (e: FormEvent) => {
        e.preventDefault();
        setIsSubmitting(true);

        try {
            let auth, currentUser, token;

            try {
                auth = getAuth();
                currentUser = auth.currentUser;
                if (!currentUser) {
                    throw new Error('로그인 정보가 유효하지 않습니다. 다시 로그인해주세요.');
                }
                token = await currentUser.getIdToken();
            } catch (authError) {
                console.error('Firebase Auth 오류:', authError);
                throw new Error('인증 상태를 확인할 수 없습니다. 다시 로그인해주세요.');
            }

            const apiUrl = process.env.NEXT_PUBLIC_API_URL;

            // 1. 보호자 정보 업데이트
            const userResponse = await fetch(`${apiUrl}/users/profile`, {
                method: 'PUT',
                headers: {
                    'Content-Type': 'application/json',
                    Authorization: `Bearer ${token}`,
                },
                body: JSON.stringify({
                    full_name: parentName,
                    apartment_complex: apartment,
                }),
            });
            if (!userResponse.ok) throw new Error('보호자 정보 저장에 실패했습니다.');

            // 2. 각 자녀 정보 등록
            for (const child of children) {
                const childFormData = new FormData();
                childFormData.append('name', child.name);
                childFormData.append('age', child.age);
                childFormData.append('school_name', child.school);
                if (child.imageFile) {
                    childFormData.append('image', child.imageFile);
                }

                const childResponse = await fetch(`${apiUrl}/children/`, {
                    method: 'POST',
                    headers: { Authorization: `Bearer ${token}` },
                    body: childFormData,
                });
                if (!childResponse.ok) throw new Error(`${child.name} 정보 저장에 실패했습니다.`);
            }

            alert('프로필이 성공적으로 저장되었습니다!');
            
            // 🚀 Zustand 공통 처리
            await handleProfileSetupComplete(router);
            
        } catch (error) {
            console.error('프로필 저장 오류:', error);
            if (error instanceof Error) {
                alert(`프로필 저장 중 오류가 발생했습니다: ${error.message}`);
            } else {
                alert('프로필 저장 중 알 수 없는 오류가 발생했습니다.');
            }
        } finally {
            setIsSubmitting(false);
        }
    };

    if (!isAuthenticated) {
        return (
            <div className="flex items-center justify-center min-h-screen">
                로딩 중...
            </div>
        );
    }

    return (
        <div className="min-h-screen bg-gray-50 flex items-center justify-center p-4 sm:p-6 lg:p-8">
            <div className="w-full max-w-2xl mx-auto bg-white p-8 rounded-lg shadow-md">
                <div className="text-center mb-8">
                    <Image
                        src="/images/logo/logowide.png"
                        alt="함께 키즈 로고"
                        width={150}
                        height={50}
                        className="mx-auto mb-4"
                    />
                    <h1 className="text-2xl font-bold text-gray-800">프로필 설정</h1>
                    <p className="text-gray-500">공동육아 시작을 위해 정보를 입력해주세요.</p>
                </div>

                <form onSubmit={handleSubmit} className="space-y-6">
                    {/* 부모 정보 섹션 */}
                    <div className="space-y-4 p-4 border rounded-lg">
                        <h2 className="text-lg font-semibold text-gray-700">보호자 정보</h2>
                        <div>
                            <label className="block text-sm font-medium text-gray-600">이름</label>
                            <input
                                type="text"
                                value={parentName}
                                onChange={(e) => setParentName(e.target.value)}
                                required
                                className="mt-1 block w-full px-3 py-2 bg-white border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500"
                            />
                        </div>
                        <div>
                            <label className="block text-sm font-medium text-gray-600">아파트 단지</label>
                            <input
                                type="text"
                                value={apartment}
                                onChange={(e) => setApartment(e.target.value)}
                                required
                                className="mt-1 block w-full px-3 py-2 bg-white border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500"
                            />
                        </div>
                    </div>

                    {/* 아이 정보 섹션 */}
                    <div className="space-y-4">
                        <h2 className="text-lg font-semibold text-gray-700">자녀 정보</h2>
                        {children.map((child, index) => (
                            <div key={child.id} className="p-4 border rounded-lg space-y-4 relative">
                                {children.length > 1 && (
                                    <button
                                        type="button"
                                        onClick={() => removeChild(index)}
                                        className="absolute top-2 right-2 text-gray-400 hover:text-red-500"
                                    >
                                        &times;
                                    </button>
                                )}
                                <div className="flex items-center space-x-4">
                                    <div className="w-24 h-24 bg-gray-100 rounded-full flex items-center justify-center overflow-hidden">
                                        {child.imageUrl ? (
                                            <Image
                                                src={child.imageUrl}
                                                alt="프로필 미리보기"
                                                width={96}
                                                height={96}
                                                className="w-full h-full object-cover"
                                            />
                                        ) : (
                                            <span className="text-gray-400 text-xs">사진 등록</span>
                                        )}
                                    </div>
                                    <div className="flex-1">
                                        <label className="block text-sm font-medium text-gray-600">프로필 사진</label>
                                        <input
                                            type="file"
                                            accept="image/*"
                                            onChange={(e) => handleImageChange(index, e)}
                                            className="mt-1 block w-full text-sm text-gray-500 file:mr-4 file:py-2 file:px-4 file:rounded-full file:border-0 file:text-sm file:font-semibold file:bg-blue-50 file:text-blue-700 hover:file:bg-blue-100"
                                        />
                                    </div>
                                </div>
                                <div>
                                    <label className="block text-sm font-medium text-gray-600">이름</label>
                                    <input
                                        type="text"
                                        name="name"
                                        value={child.name}
                                        onChange={(e) => handleChildChange(index, e)}
                                        required
                                        className="mt-1 block w-full px-3 py-2 border rounded-md"
                                    />
                                </div>
                                <div className="grid grid-cols-2 gap-4">
                                    <div>
                                        <label className="block text-sm font-medium text-gray-600">나이</label>
                                        <input
                                            type="number"
                                            name="age"
                                            value={child.age}
                                            onChange={(e) => handleChildChange(index, e)}
                                            required
                                            className="mt-1 block w-full px-3 py-2 border rounded-md"
                                        />
                                    </div>
                                    <div>
                                        <label className="block text-sm font-medium text-gray-600">어린이집/학교</label>
                                        <input
                                            type="text"
                                            name="school"
                                            value={child.school}
                                            onChange={(e) => handleChildChange(index, e)}
                                            required
                                            className="mt-1 block w-full px-3 py-2 border rounded-md"
                                        />
                                    </div>
                                </div>
                            </div>
                        ))}
                        <button
                            type="button"
                            onClick={addChild}
                            className="w-full py-2 px-4 border-2 border-dashed border-gray-300 rounded-lg text-sm font-semibold text-gray-600 hover:bg-gray-50"
                        >
                            + 자녀 추가하기
                        </button>
                    </div>

                    <div className="pt-4">
                        <button
                            type="submit"
                            disabled={isSubmitting || !isAuthenticated}
                            className="w-full py-3 px-4 bg-blue-600 hover:bg-blue-700 text-white font-bold rounded-lg transition-colors disabled:bg-gray-400"
                        >
                            {isSubmitting ? '저장하는 중...' : '저장하고 시작하기'}
                        </button>
                    </div>
                </form>
            </div>
        </div>
    );
}
