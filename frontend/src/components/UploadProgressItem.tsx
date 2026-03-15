import type { UploadItem } from '@/types';

interface UploadProgressItemProps {
  item: UploadItem;
}

function StatusIcon({ status }: { status: UploadItem['status'] }) {
  if (status === 'uploading') {
    return (
      <span className="w-4 h-4 rounded-full border-2 border-blue-400 border-t-transparent animate-spin inline-block flex-shrink-0" />
    );
  }
  if (status === 'processing') {
    return (
      <span className="w-4 h-4 rounded-full border-2 border-amber-400 border-t-transparent animate-spin inline-block flex-shrink-0" />
    );
  }
  if (status === 'indexed') {
    return <span className="text-emerald-500 flex-shrink-0">✓</span>;
  }
  return <span className="text-red-500 flex-shrink-0" title="Failed">✕</span>;
}

export default function UploadProgressItem({ item }: UploadProgressItemProps) {
  return (
    <div className="flex items-center gap-2 px-4 py-2 text-sm">
      <StatusIcon status={item.status} />
      <div className="flex-1 min-w-0">
        <p className="truncate text-gray-700" title={item.filename}>{item.filename}</p>
        {(item.status === 'uploading' || item.status === 'processing') && (
          <div className="mt-1 h-1.5 bg-gray-200 rounded-full overflow-hidden">
            <div
              className="h-full bg-blue-500 rounded-full transition-all duration-300"
              style={{ width: `${item.progress}%` }}
            />
          </div>
        )}
        {item.status === 'failed' && item.error && (
          <p className="text-xs text-red-500 truncate" title={item.error}>{item.error}</p>
        )}
      </div>
      <span className="text-xs text-gray-400 flex-shrink-0 capitalize">{item.status}</span>
    </div>
  );
}
