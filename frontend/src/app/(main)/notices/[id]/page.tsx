"use client";

import { useEffect, useState, use } from "react";
import { useRouter } from "next/navigation";
import { api } from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Separator } from "@/components/ui/separator";
import { Skeleton } from "@/components/ui/skeleton";
import { toast } from "sonner";
import { ArrowLeft, Eye, Paperclip, Calendar, User } from "lucide-react";

interface Attachment {
  id: number;
  filename: string;
  url: string;
  size?: number;
}

interface Comment {
  id: number;
  author_name: string;
  content: string;
  created_at: string;
}

interface NoticeDetail {
  id: number;
  title: string;
  content: string;
  category?: string;
  author_name?: string;
  created_at: string;
  view_count?: number;
  attachments?: Attachment[];
  comments?: Comment[];
}

export default function NoticeDetailPage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const { id } = use(params);
  const router = useRouter();
  const [notice, setNotice] = useState<NoticeDetail | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function fetchData() {
      try {
        const data = await api.get(`/notices/${id}`);
        setNotice(data);
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
  }, [id]);

  if (loading) {
    return (
      <div className="mx-auto max-w-2xl space-y-6">
        <Skeleton className="h-8 w-48" />
        <Skeleton className="h-64 w-full" />
      </div>
    );
  }

  if (!notice) {
    return (
      <div className="py-12 text-center text-muted-foreground">
        공지사항을 찾을 수 없습니다.
      </div>
    );
  }

  return (
    <div className="mx-auto max-w-2xl space-y-6">
      <Button variant="ghost" size="sm" onClick={() => router.back()}>
        <ArrowLeft className="mr-1 size-4" />
        목록으로
      </Button>

      <Card>
        <CardHeader>
          <div className="flex items-start justify-between">
            <div className="space-y-1">
              <CardTitle className="text-xl">{notice.title}</CardTitle>
              <div className="flex items-center gap-3 text-sm text-muted-foreground">
                <span className="flex items-center gap-1">
                  <User className="size-3" />
                  {notice.author_name || "관리자"}
                </span>
                <span className="flex items-center gap-1">
                  <Calendar className="size-3" />
                  {new Date(notice.created_at).toLocaleDateString("ko-KR")}
                </span>
                <span className="flex items-center gap-1">
                  <Eye className="size-3" />
                  {notice.view_count ?? 0}
                </span>
              </div>
            </div>
            {notice.category && (
              <Badge variant="secondary">{notice.category}</Badge>
            )}
          </div>
        </CardHeader>
        <Separator />
        <CardContent className="pt-6">
          <div className="whitespace-pre-wrap text-sm leading-relaxed">
            {notice.content}
          </div>
        </CardContent>
      </Card>

      {/* Attachments */}
      {notice.attachments && notice.attachments.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-base">
              <Paperclip className="size-4" />
              첨부파일 ({notice.attachments.length})
            </CardTitle>
          </CardHeader>
          <CardContent>
            <ul className="space-y-2">
              {notice.attachments.map((file) => (
                <li key={file.id}>
                  <a
                    href={file.url}
                    className="text-sm text-blue-600 hover:underline"
                    target="_blank"
                    rel="noopener noreferrer"
                  >
                    {file.filename}
                    {file.size && (
                      <span className="ml-2 text-xs text-muted-foreground">
                        ({(file.size / 1024).toFixed(1)} KB)
                      </span>
                    )}
                  </a>
                </li>
              ))}
            </ul>
          </CardContent>
        </Card>
      )}

      {/* Comments */}
      {notice.comments && notice.comments.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle className="text-base">
              댓글 ({notice.comments.length})
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              {notice.comments.map((comment) => (
                <div key={comment.id} className="space-y-1">
                  <div className="flex items-center gap-2">
                    <span className="text-sm font-medium">
                      {comment.author_name}
                    </span>
                    <span className="text-xs text-muted-foreground">
                      {new Date(comment.created_at).toLocaleDateString("ko-KR")}
                    </span>
                  </div>
                  <p className="text-sm text-muted-foreground">
                    {comment.content}
                  </p>
                  <Separator />
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
}
