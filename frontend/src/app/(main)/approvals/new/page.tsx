"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { api } from "@/lib/api";
import { Button } from "@/components/ui/button";
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
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import { toast } from "sonner";
import { X } from "lucide-react";

interface Template {
  id: number;
  name: string;
  description?: string;
}

interface UserOption {
  id: number;
  name: string;
  department?: string;
  position?: string;
}

export default function NewApprovalPage() {
  const router = useRouter();
  const [templates, setTemplates] = useState<Template[]>([]);
  const [selectedTemplate, setSelectedTemplate] = useState("");
  const [title, setTitle] = useState("");
  const [content, setContent] = useState("");
  const [approvers, setApprovers] = useState<UserOption[]>([]);
  const [userSearch, setUserSearch] = useState("");
  const [searchResults, setSearchResults] = useState<UserOption[]>([]);
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);

  useEffect(() => {
    async function fetchTemplates() {
      try {
        const data = await api.get("/templates");
        setTemplates(data.items || data.results || data || []);
      } catch (err) {
        toast.error(
          err instanceof Error
            ? err.message
            : "양식을 불러오는데 실패했습니다."
        );
      } finally {
        setLoading(false);
      }
    }
    fetchTemplates();
  }, []);

  const searchUsers = async (query: string) => {
    setUserSearch(query);
    if (query.length < 2) {
      setSearchResults([]);
      return;
    }
    try {
      const data = await api.get(`/users?search=${encodeURIComponent(query)}`);
      const users = data.items || data.results || data || [];
      setSearchResults(
        users.filter(
          (u: UserOption) => !approvers.some((a) => a.id === u.id)
        )
      );
    } catch {
      // ignore search errors
    }
  };

  const addApprover = (user: UserOption) => {
    setApprovers((prev) => [...prev, user]);
    setSearchResults([]);
    setUserSearch("");
  };

  const removeApprover = (userId: number) => {
    setApprovers((prev) => prev.filter((a) => a.id !== userId));
  };

  const handleSubmit = async () => {
    if (!selectedTemplate || !title) {
      toast.error("양식과 제목을 입력해주세요.");
      return;
    }
    if (approvers.length === 0) {
      toast.error("결재자를 한 명 이상 추가해주세요.");
      return;
    }

    setSubmitting(true);
    try {
      const approval = await api.post("/approvals", {
        template_id: Number(selectedTemplate),
        title,
        content,
        approver_ids: approvers.map((a) => a.id),
      });
      await api.put(`/approvals/${approval.id}/submit`);
      toast.success("기안이 상신되었습니다.");
      router.push("/approvals");
    } catch (err) {
      toast.error(
        err instanceof Error ? err.message : "기안 상신에 실패했습니다."
      );
    } finally {
      setSubmitting(false);
    }
  };

  if (loading) {
    return (
      <div className="space-y-6">
        <h1 className="text-2xl font-bold">새 기안</h1>
        <Skeleton className="h-64 w-full" />
      </div>
    );
  }

  return (
    <div className="mx-auto max-w-2xl space-y-6">
      <h1 className="text-2xl font-bold">새 기안</h1>

      {/* Step 1: Template */}
      <Card>
        <CardHeader>
          <CardTitle className="text-base">1. 양식 선택</CardTitle>
          <CardDescription>결재 양식을 선택하세요</CardDescription>
        </CardHeader>
        <CardContent>
          <Select value={selectedTemplate} onValueChange={setSelectedTemplate}>
            <SelectTrigger>
              <SelectValue placeholder="양식을 선택하세요" />
            </SelectTrigger>
            <SelectContent>
              {templates.map((t) => (
                <SelectItem key={t.id} value={String(t.id)}>
                  {t.name}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </CardContent>
      </Card>

      {/* Step 2: Content */}
      <Card>
        <CardHeader>
          <CardTitle className="text-base">2. 내용 작성</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="space-y-2">
            <Label htmlFor="title">제목</Label>
            <Input
              id="title"
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              placeholder="기안 제목"
            />
          </div>
          <div className="space-y-2">
            <Label htmlFor="content">내용</Label>
            <Textarea
              id="content"
              value={content}
              onChange={(e) => setContent(e.target.value)}
              placeholder="기안 내용을 작성하세요"
              rows={8}
            />
          </div>
        </CardContent>
      </Card>

      {/* Step 3: Approval Line */}
      <Card>
        <CardHeader>
          <CardTitle className="text-base">3. 결재선 설정</CardTitle>
          <CardDescription>결재자를 검색하여 추가하세요</CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="relative">
            <Input
              value={userSearch}
              onChange={(e) => searchUsers(e.target.value)}
              placeholder="이름으로 검색..."
            />
            {searchResults.length > 0 && (
              <div className="absolute top-full left-0 right-0 z-10 mt-1 rounded-md border bg-popover shadow-md">
                {searchResults.map((user) => (
                  <button
                    key={user.id}
                    className="flex w-full items-center gap-2 px-3 py-2 text-sm hover:bg-accent"
                    onClick={() => addApprover(user)}
                  >
                    <span className="font-medium">{user.name}</span>
                    {user.department && (
                      <span className="text-muted-foreground">
                        {user.department}
                      </span>
                    )}
                    {user.position && (
                      <span className="text-muted-foreground">
                        {user.position}
                      </span>
                    )}
                  </button>
                ))}
              </div>
            )}
          </div>

          {approvers.length > 0 && (
            <div className="space-y-2">
              {approvers.map((approver, idx) => (
                <div
                  key={approver.id}
                  className="flex items-center gap-2 rounded-md border p-2"
                >
                  <Badge variant="outline">{idx + 1}</Badge>
                  <span className="text-sm font-medium">{approver.name}</span>
                  {approver.department && (
                    <span className="text-xs text-muted-foreground">
                      {approver.department}
                    </span>
                  )}
                  <button
                    className="ml-auto text-muted-foreground hover:text-foreground"
                    onClick={() => removeApprover(approver.id)}
                  >
                    <X className="size-4" />
                  </button>
                </div>
              ))}
            </div>
          )}
        </CardContent>
      </Card>

      <div className="flex justify-end gap-2">
        <Button variant="outline" onClick={() => router.back()}>
          취소
        </Button>
        <Button onClick={handleSubmit} disabled={submitting}>
          {submitting ? "상신 중..." : "상신"}
        </Button>
      </div>
    </div>
  );
}
