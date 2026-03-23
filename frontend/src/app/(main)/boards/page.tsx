"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { api } from "@/lib/api";
import {
  Card,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { toast } from "sonner";
import { MessageSquare } from "lucide-react";

interface Board {
  id: number;
  name: string;
  description?: string;
  post_count?: number;
}

export default function BoardsPage() {
  const [boards, setBoards] = useState<Board[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function fetchData() {
      try {
        const data = await api.get("/boards");
        setBoards(data.items || data.results || data || []);
      } catch (err) {
        toast.error(
          err instanceof Error
            ? err.message
            : "게시판을 불러오는데 실패했습니다."
        );
      } finally {
        setLoading(false);
      }
    }
    fetchData();
  }, []);

  if (loading) {
    return (
      <div className="space-y-6">
        <h1 className="text-2xl font-bold">게시판</h1>
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
          {Array.from({ length: 3 }).map((_, i) => (
            <Skeleton key={i} className="h-28 w-full" />
          ))}
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold">게시판</h1>

      {boards.length === 0 ? (
        <div className="py-12 text-center text-sm text-muted-foreground">
          등록된 게시판이 없습니다.
        </div>
      ) : (
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
          {boards.map((board) => (
            <Link key={board.id} href={`/boards/${board.id}`}>
              <Card className="transition-shadow hover:shadow-md cursor-pointer">
                <CardHeader>
                  <div className="flex items-center gap-2">
                    <MessageSquare className="size-5 text-muted-foreground" />
                    <CardTitle className="text-base">{board.name}</CardTitle>
                  </div>
                  {board.description && (
                    <CardDescription>{board.description}</CardDescription>
                  )}
                  {board.post_count !== undefined && (
                    <p className="text-xs text-muted-foreground">
                      게시글 {board.post_count}개
                    </p>
                  )}
                </CardHeader>
              </Card>
            </Link>
          ))}
        </div>
      )}
    </div>
  );
}
