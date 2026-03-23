"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { api } from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Input } from "@/components/ui/input";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
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
import { Plus, Search } from "lucide-react";

interface Asset {
  id: number;
  name: string;
  category?: string;
  manufacturer?: string;
  model?: string;
  serial_number?: string;
  status: string;
  assigned_to?: string;
  purchase_date?: string;
}

function statusBadge(status: string) {
  const map: Record<string, { label: string; variant: "default" | "secondary" | "destructive" | "outline" }> = {
    in_use: { label: "사용중", variant: "default" },
    사용중: { label: "사용중", variant: "default" },
    available: { label: "사용가능", variant: "secondary" },
    사용가능: { label: "사용가능", variant: "secondary" },
    repair: { label: "수리중", variant: "destructive" },
    수리중: { label: "수리중", variant: "destructive" },
    disposed: { label: "폐기", variant: "outline" },
    폐기: { label: "폐기", variant: "outline" },
  };
  const info = map[status] || { label: status, variant: "outline" as const };
  return <Badge variant={info.variant}>{info.label}</Badge>;
}

export default function AssetsPage() {
  const [assets, setAssets] = useState<Asset[]>([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState("");
  const [categoryFilter, setCategoryFilter] = useState("all");
  const [statusFilter, setStatusFilter] = useState("all");

  useEffect(() => {
    async function fetchData() {
      setLoading(true);
      try {
        let path = "/assets?";
        if (search) path += `search=${encodeURIComponent(search)}&`;
        if (categoryFilter && categoryFilter !== "all")
          path += `category=${encodeURIComponent(categoryFilter)}&`;
        if (statusFilter && statusFilter !== "all")
          path += `status=${encodeURIComponent(statusFilter)}&`;
        const data = await api.get(path);
        setAssets(data.items || data.results || data || []);
      } catch (err) {
        toast.error(
          err instanceof Error
            ? err.message
            : "자산 목록을 불러오는데 실패했습니다."
        );
      } finally {
        setLoading(false);
      }
    }
    fetchData();
  }, [search, categoryFilter, statusFilter]);

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold">자산관리</h1>
        <Link href="/assets/new">
          <Button>
            <Plus className="mr-1 size-4" />
            자산 등록
          </Button>
        </Link>
      </div>

      {/* Filters */}
      <div className="flex flex-wrap items-center gap-3">
        <div className="relative flex-1 min-w-[200px] max-w-sm">
          <Search className="absolute left-3 top-1/2 size-4 -translate-y-1/2 text-muted-foreground" />
          <Input
            placeholder="자산명, 시리얼 검색..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="pl-9"
          />
        </div>
        <Select value={categoryFilter} onValueChange={setCategoryFilter}>
          <SelectTrigger className="w-[140px]">
            <SelectValue placeholder="분류" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">전체 분류</SelectItem>
            <SelectItem value="컴퓨터">컴퓨터</SelectItem>
            <SelectItem value="모니터">모니터</SelectItem>
            <SelectItem value="주변기기">주변기기</SelectItem>
            <SelectItem value="소프트웨어">소프트웨어</SelectItem>
            <SelectItem value="가구">가구</SelectItem>
            <SelectItem value="기타">기타</SelectItem>
          </SelectContent>
        </Select>
        <Select value={statusFilter} onValueChange={setStatusFilter}>
          <SelectTrigger className="w-[140px]">
            <SelectValue placeholder="상태" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">전체 상태</SelectItem>
            <SelectItem value="in_use">사용중</SelectItem>
            <SelectItem value="available">사용가능</SelectItem>
            <SelectItem value="repair">수리중</SelectItem>
            <SelectItem value="disposed">폐기</SelectItem>
          </SelectContent>
        </Select>
      </div>

      {loading ? (
        <div className="space-y-2">
          {Array.from({ length: 8 }).map((_, i) => (
            <Skeleton key={i} className="h-10 w-full" />
          ))}
        </div>
      ) : assets.length === 0 ? (
        <div className="py-12 text-center text-sm text-muted-foreground">
          등록된 자산이 없습니다.
        </div>
      ) : (
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>자산명</TableHead>
              <TableHead className="w-24">분류</TableHead>
              <TableHead>제조사</TableHead>
              <TableHead>모델</TableHead>
              <TableHead className="w-32">시리얼</TableHead>
              <TableHead className="w-20">상태</TableHead>
              <TableHead>사용자</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {assets.map((asset) => (
              <TableRow key={asset.id}>
                <TableCell>
                  <Link
                    href={`/assets/${asset.id}`}
                    className="hover:underline font-medium"
                  >
                    {asset.name}
                  </Link>
                </TableCell>
                <TableCell className="text-xs">
                  {asset.category || "-"}
                </TableCell>
                <TableCell className="text-sm">
                  {asset.manufacturer || "-"}
                </TableCell>
                <TableCell className="text-sm">{asset.model || "-"}</TableCell>
                <TableCell className="text-xs font-mono text-muted-foreground">
                  {asset.serial_number || "-"}
                </TableCell>
                <TableCell>{statusBadge(asset.status)}</TableCell>
                <TableCell className="text-sm">
                  {asset.assigned_to || "-"}
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      )}
    </div>
  );
}
