"use client";

import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { toast } from "sonner";
import { Clock, AlertTriangle, CalendarDays, Timer } from "lucide-react";

interface DayRecord {
  date: string;
  status: string;
  check_in?: string;
  check_out?: string;
  work_hours?: number;
}

interface MonthlySummary {
  work_days?: number;
  late_days?: number;
  leave_days?: number;
  total_hours?: number;
  records?: DayRecord[];
}

const statusColors: Record<string, string> = {
  normal: "bg-green-500",
  정상: "bg-green-500",
  late: "bg-yellow-500",
  지각: "bg-yellow-500",
  absent: "bg-red-500",
  결근: "bg-red-500",
  leave: "bg-blue-500",
  휴가: "bg-blue-500",
  holiday: "bg-gray-300",
};

export default function AttendancePage() {
  const [data, setData] = useState<MonthlySummary | null>(null);
  const [loading, setLoading] = useState(true);
  const [currentMonth, setCurrentMonth] = useState(() => {
    const now = new Date();
    return `${now.getFullYear()}-${String(now.getMonth() + 1).padStart(2, "0")}`;
  });

  useEffect(() => {
    async function fetchData() {
      setLoading(true);
      try {
        const result = await api.get(
          `/attendance/monthly?month=${currentMonth}`
        );
        setData(result);
      } catch (err) {
        toast.error(
          err instanceof Error
            ? err.message
            : "출퇴근 데이터를 불러오는데 실패했습니다."
        );
      } finally {
        setLoading(false);
      }
    }
    fetchData();
  }, [currentMonth]);

  const handleMonthChange = (direction: number) => {
    const [year, month] = currentMonth.split("-").map(Number);
    const date = new Date(year, month - 1 + direction, 1);
    setCurrentMonth(
      `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, "0")}`
    );
  };

  // Build calendar grid
  const buildCalendar = () => {
    const [year, month] = currentMonth.split("-").map(Number);
    const firstDay = new Date(year, month - 1, 1).getDay();
    const daysInMonth = new Date(year, month, 0).getDate();
    const records = data?.records || [];

    const recordMap: Record<string, DayRecord> = {};
    records.forEach((r) => {
      const dayKey = r.date.split("T")[0];
      recordMap[dayKey] = r;
    });

    const weeks: (null | { day: number; record?: DayRecord })[][] = [];
    let currentWeek: (null | { day: number; record?: DayRecord })[] = [];

    for (let i = 0; i < firstDay; i++) {
      currentWeek.push(null);
    }

    for (let day = 1; day <= daysInMonth; day++) {
      const dateStr = `${year}-${String(month).padStart(2, "0")}-${String(day).padStart(2, "0")}`;
      currentWeek.push({ day, record: recordMap[dateStr] });
      if (currentWeek.length === 7) {
        weeks.push(currentWeek);
        currentWeek = [];
      }
    }
    if (currentWeek.length > 0) {
      while (currentWeek.length < 7) currentWeek.push(null);
      weeks.push(currentWeek);
    }

    return weeks;
  };

  if (loading) {
    return (
      <div className="space-y-6">
        <h1 className="text-2xl font-bold">출퇴근</h1>
        <div className="grid gap-4 md:grid-cols-4">
          {Array.from({ length: 4 }).map((_, i) => (
            <Skeleton key={i} className="h-24 w-full" />
          ))}
        </div>
        <Skeleton className="h-96 w-full" />
      </div>
    );
  }

  const weeks = buildCalendar();
  const dayLabels = ["일", "월", "화", "수", "목", "금", "토"];

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold">출퇴근</h1>

      {/* Summary Cards */}
      <div className="grid gap-4 md:grid-cols-4">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-medium">출근일수</CardTitle>
            <Clock className="size-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{data?.work_days ?? 0}일</div>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-medium">지각</CardTitle>
            <AlertTriangle className="size-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{data?.late_days ?? 0}일</div>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-medium">연차</CardTitle>
            <CalendarDays className="size-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{data?.leave_days ?? 0}일</div>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-medium">총근무시간</CardTitle>
            <Timer className="size-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {data?.total_hours ?? 0}시간
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Calendar */}
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <button
              className="text-sm text-muted-foreground hover:text-foreground"
              onClick={() => handleMonthChange(-1)}
            >
              &lt; 이전
            </button>
            <CardTitle className="text-base">
              {currentMonth.replace("-", "년 ")}월
            </CardTitle>
            <button
              className="text-sm text-muted-foreground hover:text-foreground"
              onClick={() => handleMonthChange(1)}
            >
              다음 &gt;
            </button>
          </div>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-7 gap-1">
            {dayLabels.map((label) => (
              <div
                key={label}
                className="py-2 text-center text-xs font-medium text-muted-foreground"
              >
                {label}
              </div>
            ))}
            {weeks.flat().map((cell, i) => (
              <div
                key={i}
                className="flex min-h-[3rem] flex-col items-center gap-1 rounded-md border p-1 text-xs"
              >
                {cell && (
                  <>
                    <span className="text-muted-foreground">{cell.day}</span>
                    {cell.record && (
                      <div
                        className={`size-2 rounded-full ${statusColors[cell.record.status] || "bg-gray-300"}`}
                        title={cell.record.status}
                      />
                    )}
                  </>
                )}
              </div>
            ))}
          </div>

          {/* Legend */}
          <div className="mt-4 flex items-center gap-4 text-xs text-muted-foreground">
            <span className="flex items-center gap-1">
              <div className="size-2 rounded-full bg-green-500" /> 정상
            </span>
            <span className="flex items-center gap-1">
              <div className="size-2 rounded-full bg-yellow-500" /> 지각
            </span>
            <span className="flex items-center gap-1">
              <div className="size-2 rounded-full bg-red-500" /> 결근
            </span>
            <span className="flex items-center gap-1">
              <div className="size-2 rounded-full bg-blue-500" /> 휴가
            </span>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
