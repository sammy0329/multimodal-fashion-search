import SearchBar from "@/components/SearchBar";

export default function Home() {
  return (
    <div className="min-h-screen flex flex-col items-center justify-center p-8">
      <main className="w-full max-w-2xl flex flex-col items-center gap-8">
        <h1 className="text-4xl font-bold tracking-tight">Style Matcher</h1>
        <p className="text-lg text-gray-600 text-center">
          사진 한 장 또는 자연어 설명으로 원하는 스타일의 옷을 찾아보세요
        </p>
        <SearchBar />
      </main>
    </div>
  );
}
