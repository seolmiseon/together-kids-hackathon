import NextAuth from 'next-auth';
import GoogleProvider from 'next-auth/providers/google';
import KakaoProvider from 'next-auth/providers/kakao';
import NaverProvider from 'next-auth/providers/naver';
import { JWT } from 'next-auth/jwt';

declare module 'next-auth' {
    interface Session {
        accessToken?: string;
        refreshToken?: string;
        error?: string;
    }
}

declare module 'next-auth/jwt' {
    interface JWT {
        accessToken?: string;
        refreshToken?: string;
        accessTokenExpires?: number;
        provider?: string;
    }
}

interface BackendTokens {
    access_token: string;
    refresh_token: string;
    expires_in: number;
}

// --- 백엔드 통신 함수 ---
async function exchangeTokenWithBackend(
    provider: string,
    account: any
): Promise<BackendTokens> {
    const apiUrl = process.env.NEXT_PUBLIC_API_URL;
    try {
        const response = await fetch(`${apiUrl}/auth/${provider}/callback`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                access_token: account.access_token,
                id_token: account.id_token,
            }),
        });
        if (!response.ok) {
            const errorData = await response.json();
            throw new Error(errorData.detail || '백엔드 토큰 교환 실패');
        }
        return await response.json();
    } catch (error) {
        console.error(`${provider} 토큰 교환 오류:`, error);
        throw new Error('인증 처리 중 오류 발생');
    }
}

async function refreshAccessToken(token: JWT): Promise<JWT> {
    try {
        const apiUrl = process.env.NEXT_PUBLIC_API_URL;
        const response = await fetch(`${apiUrl}/auth/refresh`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ refreshToken: token.refreshToken }),
        });

        const refreshedTokens = await response.json();

        if (!response.ok) {
            throw refreshedTokens;
        }

        // 새로 발급받은 토큰으로 업데이트
        return {
            ...token,
            accessToken: refreshedTokens.access_token,
            accessTokenExpires: Date.now() + refreshedTokens.expires_in * 1000,
        };
    } catch (error) {
        console.error('Access Token 갱신 오류:', error);
        return {
            ...token,
            error: 'RefreshAccessTokenError',
        };
    }
}

const handler = NextAuth({
    providers: [
        GoogleProvider({
            clientId: process.env.GOOGLE_CLIENT_ID!,
            clientSecret: process.env.GOOGLE_CLIENT_SECRET!,
        }),
        KakaoProvider({
            clientId: process.env.KAKAO_CLIENT_ID!,
            clientSecret: process.env.KAKAO_CLIENT_SECRET!,
        }),
        NaverProvider({
            clientId: process.env.NAVER_CLIENT_ID!,
            clientSecret: process.env.NAVER_CLIENT_SECRET!,
        }),
    ],
    callbacks: {
        async jwt({ token, user, account }) {
            // 첫 로그인
            if (account && user) {
                try {
                    const backendTokens = await exchangeTokenWithBackend(
                        account.provider,
                        account
                    );
                    token.accessToken = backendTokens.access_token;
                    token.refreshToken = backendTokens.refresh_token;
                    token.accessTokenExpires =
                        Date.now() + backendTokens.expires_in * 1000;
                    token.provider = account.provider;
                } catch (error) {
                    token.error = 'RefreshAccessTokenError';
                }
                return token;
            }

            // Access Token이 만료되지 않았을 때
            if (Date.now() < (token.accessTokenExpires as number)) {
                return token;
            }

            // Access Token이 만료되었을 때 갱신 시도
            return refreshAccessToken(token);
        },

        async session({ session, token }) {
            session.accessToken = token.accessToken;
            session.refreshToken = token.refreshToken;
            session.error =
                typeof token.error === 'string' ? token.error : undefined;
            return session;
        },
    },
    pages: {
        signIn: '/auth/login',
    },
    secret: process.env.NEXTAUTH_SECRET,
});

export { handler as GET, handler as POST };
