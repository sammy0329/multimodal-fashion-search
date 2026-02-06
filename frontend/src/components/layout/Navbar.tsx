"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useState } from "react";

const CATEGORIES = [
  { name: "상의", href: "/results?category=상의" },
  { name: "하의", href: "/results?category=하의" },
  { name: "아우터", href: "/results?category=아우터" },
  { name: "원피스", href: "/results?category=원피스" },
];

export default function Navbar() {
  const router = useRouter();
  const [isMenuOpen, setIsMenuOpen] = useState(false);

  return (
    <nav className="sticky top-0 z-50 bg-white border-b border-gray-200">
      <div className="max-w-7xl mx-auto px-4">
        <div className="flex items-center justify-between h-16">
          <Link href="/" className="text-xl font-bold text-gray-900">
            STYLE MATCHER
          </Link>

          <div className="hidden md:flex items-center gap-8">
            {CATEGORIES.map((cat) => (
              <Link
                key={cat.name}
                href={cat.href}
                className="text-gray-600 hover:text-gray-900 transition-colors"
              >
                {cat.name}
              </Link>
            ))}
          </div>

          <div className="flex items-center gap-2">
            <button
              onClick={() => router.push("/results")}
              className="p-2 hover:bg-gray-100 rounded-full transition-colors"
              aria-label="검색"
            >
              <svg
                className="w-5 h-5 text-gray-600"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"
                />
              </svg>
            </button>
            <button
              className="p-2 hover:bg-gray-100 rounded-full transition-colors md:hidden"
              onClick={() => setIsMenuOpen(!isMenuOpen)}
              aria-label="메뉴"
            >
              <svg
                className="w-5 h-5 text-gray-600"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M4 6h16M4 12h16M4 18h16"
                />
              </svg>
            </button>
          </div>
        </div>

        {isMenuOpen && (
          <div className="md:hidden py-4 border-t border-gray-100">
            {CATEGORIES.map((cat) => (
              <Link
                key={cat.name}
                href={cat.href}
                className="block py-3 text-gray-600 hover:text-gray-900"
                onClick={() => setIsMenuOpen(false)}
              >
                {cat.name}
              </Link>
            ))}
          </div>
        )}
      </div>
    </nav>
  );
}
