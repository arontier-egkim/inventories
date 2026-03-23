"use client";

import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import { Badge } from "@/components/ui/badge";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { toast } from "sonner";
import { Shield } from "lucide-react";

interface Role {
  id: number;
  name: string;
  description?: string;
  permissions?: string[];
  permission_count?: number;
  user_count?: number;
}

export default function RolesSettingsPage() {
  const [roles, setRoles] = useState<Role[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function fetchData() {
      try {
        const data = await api.get("/roles");
        setRoles(data.items || data.results || data || []);
      } catch (err) {
        toast.error(
          err instanceof Error
            ? err.message
            : "역할 목록을 불러오는데 실패했습니다."
        );
      } finally {
        setLoading(false);
      }
    }
    fetchData();
  }, []);

  if (loading) {
    return (
      <div className="space-y-6">
        <h1 className="text-2xl font-bold">역할관리</h1>
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
          {Array.from({ length: 3 }).map((_, i) => (
            <Skeleton key={i} className="h-36 w-full" />
          ))}
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold">역할관리</h1>

      {roles.length === 0 ? (
        <div className="py-12 text-center text-sm text-muted-foreground">
          등록된 역할이 없습니다.
        </div>
      ) : (
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
          {roles.map((role) => (
            <Card key={role.id}>
              <CardHeader>
                <div className="flex items-center gap-2">
                  <Shield className="size-5 text-primary" />
                  <CardTitle className="text-base">{role.name}</CardTitle>
                </div>
                {role.description && (
                  <CardDescription>{role.description}</CardDescription>
                )}
              </CardHeader>
              <CardContent>
                <div className="flex items-center gap-4 text-sm text-muted-foreground">
                  <span>
                    권한:{" "}
                    {role.permission_count ??
                      role.permissions?.length ??
                      0}
                    개
                  </span>
                  {role.user_count !== undefined && (
                    <span>사용자: {role.user_count}명</span>
                  )}
                </div>
                {role.permissions && role.permissions.length > 0 && (
                  <div className="mt-3 flex flex-wrap gap-1">
                    {role.permissions.slice(0, 6).map((perm) => (
                      <Badge
                        key={perm}
                        variant="outline"
                        className="text-xs"
                      >
                        {perm}
                      </Badge>
                    ))}
                    {role.permissions.length > 6 && (
                      <Badge variant="outline" className="text-xs">
                        +{role.permissions.length - 6}
                      </Badge>
                    )}
                  </div>
                )}
              </CardContent>
            </Card>
          ))}
        </div>
      )}
    </div>
  );
}
