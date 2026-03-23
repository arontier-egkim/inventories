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
import { ArrowLeft } from "lucide-react";

interface HistoryEntry {
  id: number;
  action: string;
  description?: string;
  actor_name?: string;
  created_at: string;
}

interface AssetDetail {
  id: number;
  name: string;
  category?: string;
  manufacturer?: string;
  model?: string;
  serial_number?: string;
  status: string;
  assigned_to?: string;
  assigned_to_name?: string;
  assigned_department?: string;
  purchase_date?: string;
  purchase_price?: number;
  warranty_end?: string;
  description?: string;
  history?: HistoryEntry[];
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

export default function AssetDetailPage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const { id } = use(params);
  const router = useRouter();
  const [asset, setAsset] = useState<AssetDetail | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function fetchData() {
      try {
        const data = await api.get(`/assets/${id}`);
        setAsset(data);
      } catch (err) {
        toast.error(
          err instanceof Error
            ? err.message
            : "자산 정보를 불러오는데 실패했습니다."
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

  if (!asset) {
    return (
      <div className="py-12 text-center text-muted-foreground">
        자산을 찾을 수 없습니다.
      </div>
    );
  }

  return (
    <div className="mx-auto max-w-2xl space-y-6">
      <Button variant="ghost" size="sm" onClick={() => router.back()}>
        <ArrowLeft className="mr-1 size-4" />
        목록으로
      </Button>

      {/* Asset Info */}
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <CardTitle>{asset.name}</CardTitle>
            {statusBadge(asset.status)}
          </div>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-2 gap-4 text-sm">
            <div>
              <span className="text-muted-foreground">분류:</span>{" "}
              {asset.category || "-"}
            </div>
            <div>
              <span className="text-muted-foreground">제조사:</span>{" "}
              {asset.manufacturer || "-"}
            </div>
            <div>
              <span className="text-muted-foreground">모델:</span>{" "}
              {asset.model || "-"}
            </div>
            <div>
              <span className="text-muted-foreground">시리얼:</span>{" "}
              <span className="font-mono">{asset.serial_number || "-"}</span>
            </div>
            <div>
              <span className="text-muted-foreground">구매일:</span>{" "}
              {asset.purchase_date
                ? new Date(asset.purchase_date).toLocaleDateString("ko-KR")
                : "-"}
            </div>
            <div>
              <span className="text-muted-foreground">구매가:</span>{" "}
              {asset.purchase_price
                ? `${asset.purchase_price.toLocaleString()}원`
                : "-"}
            </div>
            <div>
              <span className="text-muted-foreground">보증만료:</span>{" "}
              {asset.warranty_end
                ? new Date(asset.warranty_end).toLocaleDateString("ko-KR")
                : "-"}
            </div>
          </div>
          {asset.description && (
            <>
              <Separator className="my-4" />
              <p className="text-sm text-muted-foreground">
                {asset.description}
              </p>
            </>
          )}
        </CardContent>
      </Card>

      {/* Assignment Info */}
      {(asset.assigned_to_name || asset.assigned_to) && (
        <Card>
          <CardHeader>
            <CardTitle className="text-base">배정 정보</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-2 gap-4 text-sm">
              <div>
                <span className="text-muted-foreground">사용자:</span>{" "}
                {asset.assigned_to_name || asset.assigned_to}
              </div>
              {asset.assigned_department && (
                <div>
                  <span className="text-muted-foreground">부서:</span>{" "}
                  {asset.assigned_department}
                </div>
              )}
            </div>
          </CardContent>
        </Card>
      )}

      {/* History */}
      {asset.history && asset.history.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle className="text-base">이력</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="relative space-y-4 pl-6 before:absolute before:left-2 before:top-1 before:h-[calc(100%-8px)] before:w-px before:bg-border">
              {asset.history.map((entry) => (
                <div key={entry.id} className="relative">
                  <div className="absolute -left-[1.15rem] top-1.5 size-2 rounded-full bg-primary" />
                  <div className="text-sm font-medium">{entry.action}</div>
                  {entry.description && (
                    <p className="text-xs text-muted-foreground">
                      {entry.description}
                    </p>
                  )}
                  <div className="mt-1 flex items-center gap-2 text-xs text-muted-foreground">
                    {entry.actor_name && <span>{entry.actor_name}</span>}
                    <span>
                      {new Date(entry.created_at).toLocaleDateString("ko-KR")}
                    </span>
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
}
