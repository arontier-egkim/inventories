"use client";

import { useEffect, useState, use } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { api } from "@/lib/api";
import { Button } from "@/components/ui/button";
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
import { ArrowLeft } from "lucide-react";

interface Post {
  id: number;
  title: string;
  author_name?: string;
  created_at: string;
  view_count?: number;
  comment_count?: number;
}

interface BoardInfo {
  id: number;
  name: string;
}

export default function BoardPostsPage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const { id } = use(params);
  const router = useRouter();
  const [board, setBoard] = useState<BoardInfo | null>(null);
  const [posts, setPosts] = useState<Post[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function fetchData() {
      try {
        const [boardData, postsData] = await Promise.all([
          api.get(`/boards/${id}`),
          api.get(`/boards/${id}/posts`),
        ]);
        setBoard(boardData);
        setPosts(postsData.items || postsData.results || postsData || []);
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
  }, [id]);

  if (loading) {
    return (
      <div className="space-y-6">
        <Skeleton className="h-8 w-48" />
        <div className="space-y-2">
          {Array.from({ length: 5 }).map((_, i) => (
            <Skeleton key={i} className="h-10 w-full" />
          ))}
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center gap-4">
        <Button variant="ghost" size="sm" onClick={() => router.back()}>
          <ArrowLeft className="mr-1 size-4" />
          뒤로
        </Button>
        <h1 className="text-2xl font-bold">{board?.name || "게시판"}</h1>
      </div>

      {posts.length === 0 ? (
        <div className="py-12 text-center text-sm text-muted-foreground">
          게시글이 없습니다.
        </div>
      ) : (
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>제목</TableHead>
              <TableHead className="w-24">작성자</TableHead>
              <TableHead className="w-28">작성일</TableHead>
              <TableHead className="w-16 text-right">조회</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {posts.map((post) => (
              <TableRow key={post.id}>
                <TableCell>
                  <Link
                    href={`/boards/${id}/${post.id}`}
                    className="hover:underline font-medium"
                  >
                    {post.title}
                    {post.comment_count ? (
                      <span className="ml-1 text-xs text-blue-500">
                        [{post.comment_count}]
                      </span>
                    ) : null}
                  </Link>
                </TableCell>
                <TableCell className="text-sm">
                  {post.author_name || "-"}
                </TableCell>
                <TableCell className="text-xs text-muted-foreground">
                  {new Date(post.created_at).toLocaleDateString("ko-KR")}
                </TableCell>
                <TableCell className="text-right text-xs text-muted-foreground">
                  {post.view_count ?? 0}
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      )}
    </div>
  );
}
