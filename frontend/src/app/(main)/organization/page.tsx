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
import { ChevronDown, ChevronRight, Users, User } from "lucide-react";

interface Member {
  id: number;
  name: string;
  position?: string;
  title?: string;
  email?: string;
}

interface Department {
  id: number;
  name: string;
  parent_id?: number;
  members?: Member[];
  children?: Department[];
}

function DepartmentNode({ dept, level = 0 }: { dept: Department; level?: number }) {
  const [expanded, setExpanded] = useState(level < 2);
  const hasChildren =
    (dept.children && dept.children.length > 0) ||
    (dept.members && dept.members.length > 0);

  return (
    <div className={level > 0 ? "ml-4 border-l pl-4" : ""}>
      <button
        className="flex w-full items-center gap-2 rounded-md p-2 text-left hover:bg-accent"
        onClick={() => setExpanded(!expanded)}
      >
        {hasChildren ? (
          expanded ? (
            <ChevronDown className="size-4 text-muted-foreground" />
          ) : (
            <ChevronRight className="size-4 text-muted-foreground" />
          )
        ) : (
          <div className="size-4" />
        )}
        <Users className="size-4 text-primary" />
        <span className="font-medium text-sm">{dept.name}</span>
        {dept.members && (
          <span className="text-xs text-muted-foreground">
            ({dept.members.length}명)
          </span>
        )}
      </button>

      {expanded && (
        <div className="mt-1">
          {/* Members */}
          {dept.members &&
            dept.members.map((member) => (
              <div
                key={member.id}
                className="ml-6 flex items-center gap-2 rounded-md p-2 text-sm"
              >
                <User className="size-4 text-muted-foreground" />
                <span>{member.name}</span>
                {member.position && (
                  <span className="text-xs text-muted-foreground">
                    {member.position}
                  </span>
                )}
                {member.title && (
                  <span className="text-xs text-muted-foreground">
                    / {member.title}
                  </span>
                )}
              </div>
            ))}

          {/* Child Departments */}
          {dept.children &&
            dept.children.map((child) => (
              <DepartmentNode key={child.id} dept={child} level={level + 1} />
            ))}
        </div>
      )}
    </div>
  );
}

export default function OrganizationPage() {
  const [departments, setDepartments] = useState<Department[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function fetchData() {
      try {
        const data = await api.get("/org-chart");
        const depts = data.departments || data.items || data || [];
        setDepartments(Array.isArray(depts) ? depts : [depts]);
      } catch (err) {
        toast.error(
          err instanceof Error
            ? err.message
            : "조직도를 불러오는데 실패했습니다."
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
        <h1 className="text-2xl font-bold">조직도</h1>
        <Skeleton className="h-96 w-full" />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold">조직도</h1>

      <Card>
        <CardHeader>
          <CardTitle className="text-base">부서 및 구성원</CardTitle>
        </CardHeader>
        <CardContent>
          {departments.length === 0 ? (
            <div className="py-12 text-center text-sm text-muted-foreground">
              조직 정보가 없습니다.
            </div>
          ) : (
            <div className="space-y-1">
              {departments.map((dept) => (
                <DepartmentNode key={dept.id} dept={dept} />
              ))}
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
