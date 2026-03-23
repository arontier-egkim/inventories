"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { api } from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { Skeleton } from "@/components/ui/skeleton";
import { toast } from "sonner";
import { Plus, Pin } from "lucide-react";

interface Notice {
  id: number;
  title: string;
  category?: string;
  author_name?: string;
  created_at: string;
  view_count?: number;
  is_pinned?: boolean;
}

const categoryColors: Record<string, string> = {
  공지: "bg-blue-100 text-blue-800",
  안내: "bg-green-100 text-green-800",
  인사: "bg-purple-100 text-purple-800",
  일반: "bg-gray-100 text-gray-800",
};

export default function NoticesPage() {
  const [notices, setNotices] = useState<Notice[]>([]);
  const [loading, setLoading] = useState(true);
  const [page, setPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [categoryFilter, setCategoryFilter] = useState<string>("");

  useEffect(() => {
    async function fetchData() {
      setLoading(true);
      try {
        let path = `/notices?page=${page}&size=20`;
        if (categoryFilter) path += `&category=${categoryFilter}`;
        const data = await api.get(path);
        setNotices(data.items || data.results || data || []);
        setTotalPages(data.total_pages || data.pages || 1);
      } catch (err) {
        toast.error(
          err instanceof Error
            ? err.message
            : "공지사항을 불러오는데 실패했습니다."
        );
      } finally {
        setLoading(false);
      }
    }
    fetchData();
  }, [page, categoryFilter]);

  const categories = ["", "공지", "안내", "인사", "일반"];

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold">공지사항</h1>
        <Link href="/notices/new">
          <Button>
            <Plus className="mr-1 size-4" />
            글쓰기
          </Button>
        </Link>
      </div>

      {/* Category Filter */}
      <div className="flex gap-2">
        {categories.map((cat) => (
          <Badge
            key={cat || "all"}
            variant={categoryFilter === cat ? "default" : "outline"}
            className="cursor-pointer"
            onClick={() => {
              setCategoryFilter(cat);
              setPage(1);
            }}
          >
            {cat || "전체"}
          </Badge>
        ))}
      </div>

      {loading ? (
        <div className="space-y-2">
          {Array.from({ length: 10 }).map((_, i) => (
            <Skeleton key={i} className="h-10 w-full" />
          ))}
        </div>
      ) : notices.length === 0 ? (
        <div className="py-12 text-center text-sm text-muted-foreground">
          공지사항이 없습니다.
        </div>
      ) : (
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead className="w-16"></TableHead>
              <TableHead className="w-20">분류</TableHead>
              <TableHead>제목</TableHead>
              <TableHead className="w-24">작성자</TableHead>
              <TableHead className="w-28">작성일</TableHead>
              <TableHead className="w-16 text-right">조회</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {notices.map((notice) => (
              <TableRow
                key={notice.id}
                className={notice.is_pinned ? "bg-muted/50" : ""}
              >
                <TableCell>
                  {notice.is_pinned && (
                    <Pin className="size-3 text-orange-500" />
                  )}
                </TableCell>
                <TableCell>
                  {notice.category && (
                    <span
                      className={`inline-flex items-center rounded px-1.5 py-0.5 text-xs font-medium ${categoryColors[notice.category] || categoryColors["일반"]}`}
                    >
                      {notice.category}
                    </span>
                  )}
                </TableCell>
                <TableCell>
                  <Link
                    href={`/notices/${notice.id}`}
                    className="hover:underline font-medium"
                  >
                    {notice.title}
                  </Link>
                </TableCell>
                <TableCell className="text-sm">
                  {notice.author_name || "-"}
                </TableCell>
                <TableCell className="text-xs text-muted-foreground">
                  {new Date(notice.created_at).toLocaleDateString("ko-KR")}
                </TableCell>
                <TableCell className="text-right text-xs text-muted-foreground">
                  {notice.view_count ?? 0}
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      )}

      {/* Pagination */}
      {totalPages > 1 && (
        <div className="flex items-center justify-center gap-2">
          <Button
            variant="outline"
            size="sm"
            disabled={page <= 1}
            onClick={() => setPage((p) => p - 1)}
          >
            이전
          </Button>
          <span className="text-sm text-muted-foreground">
            {page} / {totalPages}
          </span>
          <Button
            variant="outline"
            size="sm"
            disabled={page >= totalPages}
            onClick={() => setPage((p) => p + 1)}
          >
            다음
          </Button>
        </div>
      )}
    </div>
  );
}
