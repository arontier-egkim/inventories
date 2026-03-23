"use client";

import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog";
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
import { Plus } from "lucide-react";

interface LeaveBalance {
  total: number;
  used: number;
  remaining: number;
}

interface LeaveRequest {
  id: number;
  leave_type?: string;
  start_date: string;
  end_date: string;
  days?: number;
  reason?: string;
  status: string;
  created_at: string;
}

function statusBadge(status: string) {
  const map: Record<string, { label: string; variant: "default" | "secondary" | "destructive" | "outline" }> = {
    pending: { label: "대기", variant: "secondary" },
    approved: { label: "승인", variant: "default" },
    rejected: { label: "반려", variant: "destructive" },
    cancelled: { label: "취소", variant: "outline" },
  };
  const info = map[status] || { label: status, variant: "outline" as const };
  return <Badge variant={info.variant}>{info.label}</Badge>;
}

export default function LeavesPage() {
  const [balance, setBalance] = useState<LeaveBalance | null>(null);
  const [requests, setRequests] = useState<LeaveRequest[]>([]);
  const [loading, setLoading] = useState(true);
  const [dialogOpen, setDialogOpen] = useState(false);

  // Form state
  const [leaveType, setLeaveType] = useState("연차");
  const [startDate, setStartDate] = useState("");
  const [endDate, setEndDate] = useState("");
  const [reason, setReason] = useState("");
  const [submitting, setSubmitting] = useState(false);

  const fetchData = async () => {
    setLoading(true);
    try {
      const [bal, reqs] = await Promise.allSettled([
        api.get("/leaves/balance"),
        api.get("/leaves/requests"),
      ]);
      if (bal.status === "fulfilled") setBalance(bal.value);
      if (reqs.status === "fulfilled") {
        const data = reqs.value;
        setRequests(data.items || data.results || data || []);
      }
    } catch (err) {
      toast.error(
        err instanceof Error ? err.message : "데이터를 불러오는데 실패했습니다."
      );
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, []);

  const handleSubmit = async () => {
    if (!startDate || !endDate) {
      toast.error("날짜를 입력해주세요.");
      return;
    }
    setSubmitting(true);
    try {
      await api.post("/leaves/requests", {
        leave_type: leaveType,
        start_date: startDate,
        end_date: endDate,
        reason,
      });
      toast.success("휴가 신청이 완료되었습니다.");
      setDialogOpen(false);
      setLeaveType("연차");
      setStartDate("");
      setEndDate("");
      setReason("");
      fetchData();
    } catch (err) {
      toast.error(
        err instanceof Error ? err.message : "휴가 신청에 실패했습니다."
      );
    } finally {
      setSubmitting(false);
    }
  };

  if (loading) {
    return (
      <div className="space-y-6">
        <h1 className="text-2xl font-bold">휴가관리</h1>
        <Skeleton className="h-28 w-full" />
        <Skeleton className="h-64 w-full" />
      </div>
    );
  }

  const usagePercent = balance
    ? Math.round((balance.used / Math.max(balance.total, 1)) * 100)
    : 0;

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold">휴가관리</h1>
        <Dialog open={dialogOpen} onOpenChange={setDialogOpen}>
          <DialogTrigger asChild>
            <Button>
              <Plus className="mr-1 size-4" />
              휴가 신청
            </Button>
          </DialogTrigger>
          <DialogContent>
            <DialogHeader>
              <DialogTitle>휴가 신청</DialogTitle>
              <DialogDescription>
                휴가 종류와 기간을 입력하세요.
              </DialogDescription>
            </DialogHeader>
            <div className="space-y-4">
              <div className="space-y-2">
                <Label>휴가 종류</Label>
                <Select value={leaveType} onValueChange={setLeaveType}>
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="연차">연차</SelectItem>
                    <SelectItem value="반차(오전)">반차(오전)</SelectItem>
                    <SelectItem value="반차(오후)">반차(오후)</SelectItem>
                    <SelectItem value="병가">병가</SelectItem>
                    <SelectItem value="경조사">경조사</SelectItem>
                    <SelectItem value="기타">기타</SelectItem>
                  </SelectContent>
                </Select>
              </div>
              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label>시작일</Label>
                  <Input
                    type="date"
                    value={startDate}
                    onChange={(e) => setStartDate(e.target.value)}
                  />
                </div>
                <div className="space-y-2">
                  <Label>종료일</Label>
                  <Input
                    type="date"
                    value={endDate}
                    onChange={(e) => setEndDate(e.target.value)}
                  />
                </div>
              </div>
              <div className="space-y-2">
                <Label>사유</Label>
                <Textarea
                  value={reason}
                  onChange={(e) => setReason(e.target.value)}
                  placeholder="휴가 사유를 입력하세요"
                  rows={3}
                />
              </div>
            </div>
            <DialogFooter>
              <Button
                variant="outline"
                onClick={() => setDialogOpen(false)}
              >
                취소
              </Button>
              <Button onClick={handleSubmit} disabled={submitting}>
                {submitting ? "신청 중..." : "신청"}
              </Button>
            </DialogFooter>
          </DialogContent>
        </Dialog>
      </div>

      {/* Balance Card */}
      <Card>
        <CardHeader>
          <CardTitle className="text-base">연차 현황</CardTitle>
          <CardDescription>
            총 {balance?.total ?? 0}일 중 {balance?.used ?? 0}일 사용
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-3">
          <div className="flex items-center justify-between text-sm">
            <span>잔여: {balance?.remaining ?? 0}일</span>
            <span className="text-muted-foreground">{usagePercent}% 사용</span>
          </div>
          <div className="h-3 w-full rounded-full bg-muted">
            <div
              className="h-3 rounded-full bg-primary transition-all"
              style={{ width: `${usagePercent}%` }}
            />
          </div>
        </CardContent>
      </Card>

      {/* Requests Table */}
      <Card>
        <CardHeader>
          <CardTitle className="text-base">휴가 신청 내역</CardTitle>
        </CardHeader>
        <CardContent>
          {requests.length === 0 ? (
            <div className="py-8 text-center text-sm text-muted-foreground">
              휴가 신청 내역이 없습니다.
            </div>
          ) : (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>종류</TableHead>
                  <TableHead>기간</TableHead>
                  <TableHead className="w-16">일수</TableHead>
                  <TableHead>사유</TableHead>
                  <TableHead className="w-20">상태</TableHead>
                  <TableHead className="w-28">신청일</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {requests.map((req) => (
                  <TableRow key={req.id}>
                    <TableCell className="text-sm">
                      {req.leave_type || "연차"}
                    </TableCell>
                    <TableCell className="text-xs">
                      {new Date(req.start_date).toLocaleDateString("ko-KR")} ~{" "}
                      {new Date(req.end_date).toLocaleDateString("ko-KR")}
                    </TableCell>
                    <TableCell className="text-sm">{req.days ?? "-"}</TableCell>
                    <TableCell className="text-xs text-muted-foreground truncate max-w-[200px]">
                      {req.reason || "-"}
                    </TableCell>
                    <TableCell>{statusBadge(req.status)}</TableCell>
                    <TableCell className="text-xs text-muted-foreground">
                      {new Date(req.created_at).toLocaleDateString("ko-KR")}
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
