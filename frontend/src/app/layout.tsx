import type { Metadata } from 'next';
import { Toaster } from 'react-hot-toast';
import { ChatProvider } from '@/contexts/ChatContext';
import { UploadProvider } from '@/contexts/UploadContext';
import './globals.css';

export const metadata: Metadata = {
  title: 'Multimodal RAG',
  description: 'Chat with your images, videos, and documents — powered by GPT-4',
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body className="bg-gray-50 text-gray-900">
        <UploadProvider>
          <ChatProvider>
            {children}
            <Toaster
              position="bottom-right"
              toastOptions={{
                style: {
                  background: '#fff',
                  color: '#111827',
                  border: '1px solid #e5e7eb',
                  borderRadius: '0.5rem',
                  boxShadow: '0 4px 6px -1px rgb(0 0 0 / 0.1)',
                },
              }}
            />
          </ChatProvider>
        </UploadProvider>
      </body>
    </html>
  );
}
