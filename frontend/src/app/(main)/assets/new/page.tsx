"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { api } from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import {
  Card,
  CardContent,
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
import { toast } from "sonner";

export default function NewAssetPage() {
  const router = useRouter();
  const [submitting, setSubmitting] = useState(false);
  const [form, setForm] = useState({
    name: "",
    category: "",
    manufacturer: "",
    model: "",
    serial_number: "",
    purchase_date: "",
    purchase_price: "",
    warranty_end: "",
    description: "",
  });

  const update = (key: string, value: string) => {
    setForm((prev) => ({ ...prev, [key]: value }));
  };

  const handleSubmit = async () => {
    if (!form.name || !form.category) {
      toast.error("자산명과 분류를 입력해주세요.");
      return;
    }
    setSubmitting(true);
    try {
      await api.post("/assets", {
        ...form,
        purchase_price: form.purchase_price
          ? Number(form.purchase_price)
          : undefined,
      });
      toast.success("자산이 등록되었습니다.");
      router.push("/assets");
    } catch (err) {
      toast.error(
        err instanceof Error ? err.message : "등록에 실패했습니다."
      );
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="mx-auto max-w-2xl space-y-6">
      <h1 className="text-2xl font-bold">자산 등록</h1>

      <Card>
        <CardHeader>
          <CardTitle className="text-base">자산 정보</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="grid grid-cols-2 gap-4">
            <div className="space-y-2">
              <Label>자산명 *</Label>
              <Input
                value={form.name}
                onChange={(e) => update("name", e.target.value)}
                placeholder="예: MacBook Pro 16인치"
              />
            </div>
            <div className="space-y-2">
              <Label>분류 *</Label>
              <Select
                value={form.category}
                onValueChange={(v) => update("category", v)}
              >
                <SelectTrigger>
                  <SelectValue placeholder="분류 선택" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="컴퓨터">컴퓨터</SelectItem>
                  <SelectItem value="모니터">모니터</SelectItem>
                  <SelectItem value="주변기기">주변기기</SelectItem>
                  <SelectItem value="소프트웨어">소프트웨어</SelectItem>
                  <SelectItem value="가구">가구</SelectItem>
                  <SelectItem value="기타">기타</SelectItem>
                </SelectContent>
              </Select>
            </div>
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div className="space-y-2">
              <Label>제조사</Label>
              <Input
                value={form.manufacturer}
                onChange={(e) => update("manufacturer", e.target.value)}
                placeholder="예: Apple"
              />
            </div>
            <div className="space-y-2">
              <Label>모델</Label>
              <Input
                value={form.model}
                onChange={(e) => update("model", e.target.value)}
                placeholder="예: A2141"
              />
            </div>
          </div>

          <div className="space-y-2">
            <Label>시리얼 번호</Label>
            <Input
              value={form.serial_number}
              onChange={(e) => update("serial_number", e.target.value)}
              placeholder="시리얼 번호"
            />
          </div>

          <div className="grid grid-cols-3 gap-4">
            <div className="space-y-2">
              <Label>구매일</Label>
              <Input
                type="date"
                value={form.purchase_date}
                onChange={(e) => update("purchase_date", e.target.value)}
              />
            </div>
            <div className="space-y-2">
              <Label>구매가 (원)</Label>
              <Input
                type="number"
                value={form.purchase_price}
                onChange={(e) => update("purchase_price", e.target.value)}
                placeholder="0"
              />
            </div>
            <div className="space-y-2">
              <Label>보증만료일</Label>
              <Input
                type="date"
                value={form.warranty_end}
                onChange={(e) => update("warranty_end", e.target.value)}
              />
            </div>
          </div>

          <div className="space-y-2">
            <Label>비고</Label>
            <Textarea
              value={form.description}
              onChange={(e) => update("description", e.target.value)}
              placeholder="추가 설명"
              rows={3}
            />
          </div>
        </CardContent>
      </Card>

      <div className="flex justify-end gap-2">
        <Button variant="outline" onClick={() => router.back()}>
          취소
        </Button>
        <Button onClick={handleSubmit} disabled={submitting}>
          {submitting ? "등록 중..." : "등록"}
        </Button>
      </div>
    </div>
  );
}
