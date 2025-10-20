import { io, Socket } from 'socket.io-client';

let socket: Socket | null = null;

export const initializeSocket = (url: string = process.env.NEXT_PUBLIC_SOCKET_URL || 'http://localhost:3000') => {
    if (!socket) {
        socket = io(url, {
            autoConnect: false,
            transports: ['websocket', 'polling'],
        });
    }
    return socket;
};

export const getSocket = () => {
    if (!socket) {
        return initializeSocket();
    }
    return socket;
};

export const disconnectSocket = () => {
    if (socket) {
        socket.disconnect();
        socket = null;
    }
};

export default {
    initialize: initializeSocket,
    get: getSocket,
    disconnect: disconnectSocket,
};