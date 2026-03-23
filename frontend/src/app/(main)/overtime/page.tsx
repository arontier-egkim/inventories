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

interface WeeklySummary {
  current_hours?: number;
  max_hours?: number;
  overtime_hours?: number;
}

interface OvertimeRequest {
  id: number;
  date: string;
  start_time?: string;
  end_time?: string;
  hours?: number;
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

export default function OvertimePage() {
  const [summary, setSummary] = useState<WeeklySummary | null>(null);
  const [requests, setRequests] = useState<OvertimeRequest[]>([]);
  const [loading, setLoading] = useState(true);
  const [dialogOpen, setDialogOpen] = useState(false);

  // Form state
  const [date, setDate] = useState("");
  const [startTime, setStartTime] = useState("");
  const [endTime, setEndTime] = useState("");
  const [reason, setReason] = useState("");
  const [submitting, setSubmitting] = useState(false);

  const fetchData = async () => {
    setLoading(true);
    try {
      const [sum, reqs] = await Promise.allSettled([
        api.get("/overtime/weekly-summary"),
        api.get("/overtime/requests"),
      ]);
      if (sum.status === "fulfilled") setSummary(sum.value);
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
    if (!date || !startTime || !endTime) {
      toast.error("날짜와 시간을 입력해주세요.");
      return;
    }
    setSubmitting(true);
    try {
      await api.post("/overtime/requests", {
        date,
        start_time: startTime,
        end_time: endTime,
        reason,
      });
      toast.success("초과근무 신청이 완료되었습니다.");
      setDialogOpen(false);
      setDate("");
      setStartTime("");
      setEndTime("");
      setReason("");
      fetchData();
    } catch (err) {
      toast.error(
        err instanceof Error ? err.message : "신청에 실패했습니다."
      );
    } finally {
      setSubmitting(false);
    }
  };

  if (loading) {
    return (
      <div className="space-y-6">
        <h1 className="text-2xl font-bold">초과근무</h1>
        <Skeleton className="h-28 w-full" />
        <Skeleton className="h-64 w-full" />
      </div>
    );
  }

  const maxHours = summary?.max_hours ?? 52;
  const currentHours = summary?.current_hours ?? 0;
  const usagePercent = Math.round((currentHours / maxHours) * 100);

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold">초과근무</h1>
        <Dialog open={dialogOpen} onOpenChange={setDialogOpen}>
          <DialogTrigger asChild>
            <Button>
              <Plus className="mr-1 size-4" />
              초과근무 신청
            </Button>
          </DialogTrigger>
          <DialogContent>
            <DialogHeader>
              <DialogTitle>초과근무 신청</DialogTitle>
              <DialogDescription>
                초과근무 일시와 사유를 입력하세요.
              </DialogDescription>
            </DialogHeader>
            <div className="space-y-4">
              <div className="space-y-2">
                <Label>날짜</Label>
                <Input
                  type="date"
                  value={date}
                  onChange={(e) => setDate(e.target.value)}
                />
              </div>
              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label>시작 시간</Label>
                  <Input
                    type="time"
                    value={startTime}
                    onChange={(e) => setStartTime(e.target.value)}
                  />
                </div>
                <div className="space-y-2">
                  <Label>종료 시간</Label>
                  <Input
                    type="time"
                    value={endTime}
                    onChange={(e) => setEndTime(e.target.value)}
                  />
                </div>
              </div>
              <div className="space-y-2">
                <Label>사유</Label>
                <Textarea
                  value={reason}
                  onChange={(e) => setReason(e.target.value)}
                  placeholder="초과근무 사유를 입력하세요"
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

      {/* Weekly Summary */}
      <Card>
        <CardHeader>
          <CardTitle className="text-base">주간 근무 현황</CardTitle>
          <CardDescription>
            법정 최대 {maxHours}시간 중 {currentHours}시간 근무
            {summary?.overtime_hours
              ? ` (초과: ${summary.overtime_hours}시간)`
              : ""}
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-3">
          <div className="flex items-center justify-between text-sm">
            <span>{currentHours}시간</span>
            <span className="text-muted-foreground">{maxHours}시간</span>
          </div>
          <div className="h-3 w-full rounded-full bg-muted">
            <div
              className={`h-3 rounded-full transition-all ${usagePercent > 90 ? "bg-red-500" : usagePercent > 75 ? "bg-yellow-500" : "bg-primary"}`}
              style={{ width: `${Math.min(usagePercent, 100)}%` }}
            />
          </div>
          <p className="text-xs text-muted-foreground">
            {usagePercent}% ({maxHours - currentHours}시간 여유)
          </p>
        </CardContent>
      </Card>

      {/* Requests Table */}
      <Card>
        <CardHeader>
          <CardTitle className="text-base">초과근무 신청 내역</CardTitle>
        </CardHeader>
        <CardContent>
          {requests.length === 0 ? (
            <div className="py-8 text-center text-sm text-muted-foreground">
              초과근무 신청 내역이 없습니다.
            </div>
          ) : (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>날짜</TableHead>
                  <TableHead>시간</TableHead>
                  <TableHead className="w-16">시간</TableHead>
                  <TableHead>사유</TableHead>
                  <TableHead className="w-20">상태</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {requests.map((req) => (
                  <TableRow key={req.id}>
                    <TableCell className="text-sm">
                      {new Date(req.date).toLocaleDateString("ko-KR")}
                    </TableCell>
                    <TableCell className="text-xs">
                      {req.start_time || "-"} ~ {req.end_time || "-"}
                    </TableCell>
                    <TableCell className="text-sm">
                      {req.hours ?? "-"}h
                    </TableCell>
                    <TableCell className="text-xs text-muted-foreground truncate max-w-[200px]">
                      {req.reason || "-"}
                    </TableCell>
                    <TableCell>{statusBadge(req.status)}</TableCell>
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
