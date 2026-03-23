"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { api } from "@/lib/api";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { Badge } from "@/components/ui/badge";
import { toast } from "sonner";
import { Clock, FileCheck, CalendarDays, Megaphone } from "lucide-react";

interface AttendanceStatus {
  check_in?: string;
  check_out?: string;
  work_duration?: string;
}

interface ApprovalSummary {
  pending_count?: number;
}

interface LeaveBalance {
  total?: number;
  used?: number;
  remaining?: number;
}

interface Notice {
  id: number;
  title: string;
  created_at: string;
  category?: string;
}

export default function DashboardPage() {
  const [attendance, setAttendance] = useState<AttendanceStatus | null>(null);
  const [approvalSummary, setApprovalSummary] =
    useState<ApprovalSummary | null>(null);
  const [leaveBalance, setLeaveBalance] = useState<LeaveBalance | null>(null);
  const [notices, setNotices] = useState<Notice[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function fetchData() {
      try {
        const [att, appr, leave, noticeRes] = await Promise.allSettled([
          api.get("/attendance/today"),
          api.get("/approvals/dashboard/summary"),
          api.get("/leaves/balance"),
          api.get("/notices?size=5"),
        ]);
        if (att.status === "fulfilled") setAttendance(att.value);
        if (appr.status === "fulfilled") setApprovalSummary(appr.value);
        if (leave.status === "fulfilled") setLeaveBalance(leave.value);
        if (noticeRes.status === "fulfilled") {
          const data = noticeRes.value;
          setNotices(data.items || data.results || data || []);
        }
      } catch {
        toast.error("데이터를 불러오는데 실패했습니다.");
      } finally {
        setLoading(false);
      }
    }
    fetchData();
  }, []);

  const handleCheckIn = async () => {
    try {
      const result = await api.post("/attendance/check-in");
      setAttendance(result);
      toast.success("출근이 기록되었습니다.");
    } catch (err) {
      toast.error(
        err instanceof Error ? err.message : "출근 기록에 실패했습니다."
      );
    }
  };

  const handleCheckOut = async () => {
    try {
      const result = await api.post("/attendance/check-out");
      setAttendance(result);
      toast.success("퇴근이 기록되었습니다.");
    } catch (err) {
      toast.error(
        err instanceof Error ? err.message : "퇴근 기록에 실패했습니다."
      );
    }
  };

  if (loading) {
    return (
      <div className="space-y-6">
        <h1 className="text-2xl font-bold">대시보드</h1>
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
          {Array.from({ length: 4 }).map((_, i) => (
            <Card key={i}>
              <CardHeader>
                <Skeleton className="h-5 w-24" />
              </CardHeader>
              <CardContent>
                <Skeleton className="h-8 w-full" />
              </CardContent>
            </Card>
          ))}
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold">대시보드</h1>

      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        {/* Attendance Card */}
        <Card>
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-medium">출퇴근</CardTitle>
            <Clock className="size-4 text-muted-foreground" />
          </CardHeader>
          <CardContent className="space-y-3">
            <div className="text-xs text-muted-foreground space-y-1">
              <div>
                출근:{" "}
                {attendance?.check_in
                  ? new Date(attendance.check_in).toLocaleTimeString("ko-KR")
                  : "미기록"}
              </div>
              <div>
                퇴근:{" "}
                {attendance?.check_out
                  ? new Date(attendance.check_out).toLocaleTimeString("ko-KR")
                  : "미기록"}
              </div>
              {attendance?.work_duration && (
                <div>근무시간: {attendance.work_duration}</div>
              )}
            </div>
            <div className="flex gap-2">
              {!attendance?.check_in ? (
                <Button size="sm" onClick={handleCheckIn} className="w-full">
                  출근
                </Button>
              ) : !attendance?.check_out ? (
                <Button
                  size="sm"
                  variant="outline"
                  onClick={handleCheckOut}
                  className="w-full"
                >
                  퇴근
                </Button>
              ) : (
                <Badge variant="secondary" className="w-full justify-center">
                  근무 완료
                </Badge>
              )}
            </div>
          </CardContent>
        </Card>

        {/* Pending Approvals Card */}
        <Card>
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-medium">결재 대기</CardTitle>
            <FileCheck className="size-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {approvalSummary?.pending_count ?? 0}
            </div>
            <CardDescription>건의 결재가 대기중입니다</CardDescription>
            <Link href="/approvals">
              <Button variant="link" className="mt-2 h-auto p-0 text-xs">
                결재함 바로가기
              </Button>
            </Link>
          </CardContent>
        </Card>

        {/* Leave Balance Card */}
        <Card>
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-medium">잔여 연차</CardTitle>
            <CalendarDays className="size-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {leaveBalance?.remaining ?? 0}
              <span className="text-sm font-normal text-muted-foreground">
                {" "}
                / {leaveBalance?.total ?? 0}일
              </span>
            </div>
            <CardDescription>
              사용: {leaveBalance?.used ?? 0}일
            </CardDescription>
            <Link href="/leaves">
              <Button variant="link" className="mt-2 h-auto p-0 text-xs">
                휴가관리 바로가기
              </Button>
            </Link>
          </CardContent>
        </Card>

        {/* Notices Card */}
        <Card>
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-medium">공지사항</CardTitle>
            <Megaphone className="size-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            {notices.length === 0 ? (
              <p className="text-sm text-muted-foreground">
                새로운 공지가 없습니다.
              </p>
            ) : (
              <ul className="space-y-1">
                {notices.map((notice) => (
                  <li key={notice.id}>
                    <Link
                      href={`/notices/${notice.id}`}
                      className="block truncate text-xs hover:underline"
                    >
                      {notice.title}
                    </Link>
                  </li>
                ))}
              </ul>
            )}
            <Link href="/notices">
              <Button variant="link" className="mt-2 h-auto p-0 text-xs">
                전체보기
              </Button>
            </Link>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
