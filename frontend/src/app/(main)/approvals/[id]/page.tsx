"use client";

import { useEffect, useState, use } from "react";
import { useRouter } from "next/navigation";
import { api } from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Separator } from "@/components/ui/separator";
import { Skeleton } from "@/components/ui/skeleton";
import { Textarea } from "@/components/ui/textarea";
import { toast } from "sonner";
import { useAuth } from "@/lib/auth-context";
import { CheckCircle, XCircle, Clock, ArrowLeft } from "lucide-react";

interface ApprovalStep {
  id: number;
  approver_id: number;
  approver_name: string;
  order: number;
  status: string;
  comment?: string;
  acted_at?: string;
}

interface ApprovalDetail {
  id: number;
  document_number?: string;
  title: string;
  content?: string;
  template_name?: string;
  status: string;
  drafter_name?: string;
  drafter_department?: string;
  created_at: string;
  submitted_at?: string;
  steps?: ApprovalStep[];
  current_step?: number;
}

function stepStatusIcon(status: string) {
  if (status === "approved")
    return <CheckCircle className="size-5 text-green-600" />;
  if (status === "rejected")
    return <XCircle className="size-5 text-red-600" />;
  return <Clock className="size-5 text-yellow-600" />;
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

export default function ApprovalDetailPage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const { id } = use(params);
  const router = useRouter();
  const { user } = useAuth();
  const [approval, setApproval] = useState<ApprovalDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [comment, setComment] = useState("");
  const [acting, setActing] = useState(false);

  useEffect(() => {
    async function fetchData() {
      try {
        const data = await api.get(`/approvals/${id}`);
        setApproval(data);
      } catch (err) {
        toast.error(
          err instanceof Error
            ? err.message
            : "결재 문서를 불러오는데 실패했습니다."
        );
      } finally {
        setLoading(false);
      }
    }
    fetchData();
  }, [id]);

  const isCurrentApprover =
    approval?.steps?.some(
      (s) =>
        s.approver_id === user?.id &&
        s.status === "pending" &&
        s.order === approval.current_step
    ) ?? false;

  const handleAction = async (action: "approve" | "reject") => {
    setActing(true);
    try {
      await api.post(`/approvals/${id}/${action}`, { comment });
      toast.success(action === "approve" ? "승인되었습니다." : "반려되었습니다.");
      router.push("/approvals");
    } catch (err) {
      toast.error(
        err instanceof Error ? err.message : "처리에 실패했습니다."
      );
    } finally {
      setActing(false);
    }
  };

  if (loading) {
    return (
      <div className="mx-auto max-w-2xl space-y-6">
        <Skeleton className="h-8 w-48" />
        <Skeleton className="h-64 w-full" />
      </div>
    );
  }

  if (!approval) {
    return (
      <div className="py-12 text-center text-muted-foreground">
        문서를 찾을 수 없습니다.
      </div>
    );
  }

  return (
    <div className="mx-auto max-w-2xl space-y-6">
      <Button variant="ghost" size="sm" onClick={() => router.back()}>
        <ArrowLeft className="mr-1 size-4" />
        뒤로
      </Button>

      {/* Document Info */}
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <div>
              <CardTitle>{approval.title}</CardTitle>
              <CardDescription>
                {approval.document_number || `#${approval.id}`}
                {approval.template_name && ` | ${approval.template_name}`}
              </CardDescription>
            </div>
            {statusBadge(approval.status)}
          </div>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="grid grid-cols-2 gap-4 text-sm">
            <div>
              <span className="text-muted-foreground">기안자:</span>{" "}
              {approval.drafter_name}
              {approval.drafter_department &&
                ` (${approval.drafter_department})`}
            </div>
            <div>
              <span className="text-muted-foreground">상신일:</span>{" "}
              {approval.submitted_at
                ? new Date(approval.submitted_at).toLocaleDateString("ko-KR")
                : new Date(approval.created_at).toLocaleDateString("ko-KR")}
            </div>
          </div>
          <Separator />
          <div className="whitespace-pre-wrap text-sm">
            {approval.content || "(내용 없음)"}
          </div>
        </CardContent>
      </Card>

      {/* Approval Steps */}
      {approval.steps && approval.steps.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle className="text-base">결재선</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              {approval.steps.map((step) => (
                <div
                  key={step.id}
                  className="flex items-center gap-3 rounded-md border p-3"
                >
                  {stepStatusIcon(step.status)}
                  <div className="flex-1">
                    <div className="text-sm font-medium">
                      {step.order}차 결재 - {step.approver_name}
                    </div>
                    {step.comment && (
                      <div className="mt-1 text-xs text-muted-foreground">
                        {step.comment}
                      </div>
                    )}
                  </div>
                  {step.acted_at && (
                    <span className="text-xs text-muted-foreground">
                      {new Date(step.acted_at).toLocaleDateString("ko-KR")}
                    </span>
                  )}
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}

      {/* Approve / Reject */}
      {isCurrentApprover && (
        <Card>
          <CardHeader>
            <CardTitle className="text-base">결재 처리</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <Textarea
              placeholder="의견을 입력하세요 (선택)"
              value={comment}
              onChange={(e) => setComment(e.target.value)}
              rows={3}
            />
            <div className="flex gap-2 justify-end">
              <Button
                variant="destructive"
                onClick={() => handleAction("reject")}
                disabled={acting}
              >
                반려
              </Button>
              <Button
                onClick={() => handleAction("approve")}
                disabled={acting}
              >
                승인
              </Button>
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
}
