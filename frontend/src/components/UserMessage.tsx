interface UserMessageProps {
  text: string;
  queryImage?: { name: string };
}

export default function UserMessage({ text, queryImage }: UserMessageProps) {
  return (
    <div className="flex justify-end px-4 py-2">
      <div className="max-w-[75%] space-y-2">
        {/* Visual search image pill */}
        {queryImage && (
          <div className="flex justify-end">
            <span className="inline-flex items-center gap-1 bg-blue-100 text-blue-700 text-xs px-3 py-1 rounded-full border border-blue-200">
              🖼 {queryImage.name}
            </span>
          </div>
        )}

        {/* Message bubble */}
        {text && (
          <div className="bg-blue-600 text-white rounded-2xl rounded-tr-sm px-4 py-3 text-sm leading-relaxed">
            {text}
          </div>
        )}
      </div>
    </div>
  );
}
