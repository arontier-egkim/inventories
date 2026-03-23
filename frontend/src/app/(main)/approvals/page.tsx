"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { api } from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
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
import { Plus } from "lucide-react";

interface Approval {
  id: number;
  document_number?: string;
  title: string;
  template_name?: string;
  status: string;
  drafter_name?: string;
  created_at: string;
}

function statusBadge(status: string) {
  const map: Record<string, { label: string; variant: "default" | "secondary" | "destructive" | "outline" }> = {
    pending: { label: "대기", variant: "secondary" },
    in_progress: { label: "진행중", variant: "secondary" },
    approved: { label: "승인", variant: "default" },
    rejected: { label: "반려", variant: "destructive" },
    cancelled: { label: "취소", variant: "outline" },
    drafted: { label: "임시저장", variant: "outline" },
  };
  const info = map[status] || { label: status, variant: "outline" as const };
  return <Badge variant={info.variant}>{info.label}</Badge>;
}

function ApprovalsTable({
  items,
  loading,
}: {
  items: Approval[];
  loading: boolean;
}) {
  if (loading) {
    return (
      <div className="space-y-2">
        {Array.from({ length: 5 }).map((_, i) => (
          <Skeleton key={i} className="h-10 w-full" />
        ))}
      </div>
    );
  }

  if (items.length === 0) {
    return (
      <div className="py-12 text-center text-sm text-muted-foreground">
        문서가 없습니다.
      </div>
    );
  }

  return (
    <Table>
      <TableHeader>
        <TableRow>
          <TableHead className="w-32">문서번호</TableHead>
          <TableHead>제목</TableHead>
          <TableHead className="w-24">양식</TableHead>
          <TableHead className="w-20">상태</TableHead>
          <TableHead className="w-24">기안자</TableHead>
          <TableHead className="w-28">상신일</TableHead>
        </TableRow>
      </TableHeader>
      <TableBody>
        {items.map((item) => (
          <TableRow key={item.id}>
            <TableCell className="text-xs text-muted-foreground">
              {item.document_number || "-"}
            </TableCell>
            <TableCell>
              <Link
                href={`/approvals/${item.id}`}
                className="hover:underline font-medium"
              >
                {item.title}
              </Link>
            </TableCell>
            <TableCell className="text-xs">
              {item.template_name || "-"}
            </TableCell>
            <TableCell>{statusBadge(item.status)}</TableCell>
            <TableCell className="text-sm">
              {item.drafter_name || "-"}
            </TableCell>
            <TableCell className="text-xs text-muted-foreground">
              {new Date(item.created_at).toLocaleDateString("ko-KR")}
            </TableCell>
          </TableRow>
        ))}
      </TableBody>
    </Table>
  );
}

export default function ApprovalsPage() {
  const [tab, setTab] = useState("drafted");
  const [items, setItems] = useState<Approval[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function fetchData() {
      setLoading(true);
      try {
        let path = "/approvals/drafted";
        if (tab === "pending") path = "/approvals/pending";
        if (tab === "completed") path = "/approvals/completed";
        const data = await api.get(path);
        setItems(data.items || data.results || data || []);
      } catch (err) {
        toast.error(
          err instanceof Error ? err.message : "데이터를 불러오는데 실패했습니다."
        );
      } finally {
        setLoading(false);
      }
    }
    fetchData();
  }, [tab]);

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold">전자결재</h1>
        <Link href="/approvals/new">
          <Button>
            <Plus className="mr-1 size-4" />새 기안
          </Button>
        </Link>
      </div>

      <Tabs value={tab} onValueChange={setTab}>
        <TabsList>
          <TabsTrigger value="drafted">기안함</TabsTrigger>
          <TabsTrigger value="pending">결재대기</TabsTrigger>
          <TabsTrigger value="completed">결재완료</TabsTrigger>
        </TabsList>
        <TabsContent value={tab} className="mt-4">
          <ApprovalsTable items={items} loading={loading} />
        </TabsContent>
      </Tabs>
    </div>
  );
}
