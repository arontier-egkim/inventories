"use client";

import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import { Badge } from "@/components/ui/badge";
import { Input } from "@/components/ui/input";
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
import { Search } from "lucide-react";

interface User {
  id: number;
  email: string;
  name: string;
  department?: string;
  position?: string;
  role?: string;
  is_active?: boolean;
  status?: string;
  created_at?: string;
}

function statusBadge(user: User) {
  const active = user.is_active !== false && user.status !== "inactive";
  return (
    <Badge variant={active ? "default" : "outline"}>
      {active ? "활성" : "비활성"}
    </Badge>
  );
}

export default function UsersSettingsPage() {
  const [users, setUsers] = useState<User[]>([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState("");

  useEffect(() => {
    async function fetchData() {
      setLoading(true);
      try {
        let path = "/users";
        if (search) path += `?search=${encodeURIComponent(search)}`;
        const data = await api.get(path);
        setUsers(data.items || data.results || data || []);
      } catch (err) {
        toast.error(
          err instanceof Error
            ? err.message
            : "사용자 목록을 불러오는데 실패했습니다."
        );
      } finally {
        setLoading(false);
      }
    }
    fetchData();
  }, [search]);

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold">사용자관리</h1>

      <div className="relative max-w-sm">
        <Search className="absolute left-3 top-1/2 size-4 -translate-y-1/2 text-muted-foreground" />
        <Input
          placeholder="이름, 이메일 검색..."
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          className="pl-9"
        />
      </div>

      {loading ? (
        <div className="space-y-2">
          {Array.from({ length: 8 }).map((_, i) => (
            <Skeleton key={i} className="h-10 w-full" />
          ))}
        </div>
      ) : users.length === 0 ? (
        <div className="py-12 text-center text-sm text-muted-foreground">
          사용자가 없습니다.
        </div>
      ) : (
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>이름</TableHead>
              <TableHead>이메일</TableHead>
              <TableHead>부서</TableHead>
              <TableHead>직위</TableHead>
              <TableHead className="w-20">역할</TableHead>
              <TableHead className="w-20">상태</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {users.map((user) => (
              <TableRow key={user.id}>
                <TableCell className="font-medium">{user.name}</TableCell>
                <TableCell className="text-sm text-muted-foreground">
                  {user.email}
                </TableCell>
                <TableCell className="text-sm">
                  {user.department || "-"}
                </TableCell>
                <TableCell className="text-sm">
                  {user.position || "-"}
                </TableCell>
                <TableCell>
                  <Badge variant="secondary">{user.role || "사용자"}</Badge>
                </TableCell>
                <TableCell>{statusBadge(user)}</TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      )}
    </div>
  );
}
