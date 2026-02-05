"use client";

interface AICommentProps {
  comment: string | null;
  isLoading: boolean;
}

export default function AIComment({ comment, isLoading }: AICommentProps) {
  if (!comment && !isLoading) {
    return null;
  }

  return (
    <div className="w-full rounded-lg border border-gray-200 bg-gray-50 p-4">
      <h3 className="text-sm font-semibold mb-2">AI 스타일리스트</h3>
      {isLoading ? (
        <div className="animate-pulse space-y-2">
          <div className="h-4 bg-gray-200 rounded w-3/4" />
          <div className="h-4 bg-gray-200 rounded w-1/2" />
        </div>
      ) : (
        <p className="text-sm text-gray-700">{comment}</p>
      )}
    </div>
  );
}
