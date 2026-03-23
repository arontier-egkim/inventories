"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  LayoutDashboard,
  FileCheck,
  MessageSquare,
  Clock,
  CalendarDays,
  Timer,
  Monitor,
  Users,
  UserCog,
  Shield,
} from "lucide-react";

import {
  Sidebar,
  SidebarContent,
  SidebarGroup,
  SidebarGroupContent,
  SidebarGroupLabel,
  SidebarHeader,
  SidebarMenu,
  SidebarMenuButton,
  SidebarMenuItem,
  SidebarMenuSub,
  SidebarMenuSubButton,
  SidebarMenuSubItem,
} from "@/components/ui/sidebar";

const menuGroups = [
  {
    label: "메인",
    items: [
      { title: "대시보드", href: "/dashboard", icon: LayoutDashboard },
    ],
  },
  {
    label: "업무",
    items: [
      { title: "전자결재", href: "/approvals", icon: FileCheck },
      {
        title: "게시판",
        icon: MessageSquare,
        children: [
          { title: "공지사항", href: "/notices" },
          { title: "자유게시판", href: "/boards" },
        ],
      },
    ],
  },
  {
    label: "근태",
    items: [
      { title: "출퇴근", href: "/attendance", icon: Clock },
      { title: "휴가관리", href: "/leaves", icon: CalendarDays },
      { title: "초과근무", href: "/overtime", icon: Timer },
    ],
  },
  {
    label: "자산",
    items: [{ title: "자산관리", href: "/assets", icon: Monitor }],
  },
  {
    label: "조직",
    items: [{ title: "조직도", href: "/organization", icon: Users }],
  },
  {
    label: "설정",
    items: [
      { title: "사용자관리", href: "/settings/users", icon: UserCog },
      { title: "역할관리", href: "/settings/roles", icon: Shield },
    ],
  },
];

export function AppSidebar() {
  const pathname = usePathname();

  return (
    <Sidebar>
      <SidebarHeader className="border-b px-4 py-3">
        <Link href="/dashboard" className="flex items-center gap-2">
          <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-primary text-primary-foreground text-sm font-bold">
            AT
          </div>
          <span className="text-base font-semibold">아론티어 그룹웨어</span>
        </Link>
      </SidebarHeader>
      <SidebarContent>
        {menuGroups.map((group) => (
          <SidebarGroup key={group.label}>
            <SidebarGroupLabel>{group.label}</SidebarGroupLabel>
            <SidebarGroupContent>
              <SidebarMenu>
                {group.items.map((item) => {
                  if (item.children) {
                    const isGroupActive = item.children.some((c) =>
                      pathname.startsWith(c.href)
                    );
                    return (
                      <SidebarMenuItem key={item.title}>
                        <SidebarMenuButton isActive={isGroupActive}>
                          {item.icon && <item.icon className="size-4" />}
                          <span>{item.title}</span>
                        </SidebarMenuButton>
                        <SidebarMenuSub>
                          {item.children.map((child) => (
                            <SidebarMenuSubItem key={child.href}>
                              <SidebarMenuSubButton
                                render={<Link href={child.href} />}
                                isActive={pathname.startsWith(child.href)}
                              >
                                <span>{child.title}</span>
                              </SidebarMenuSubButton>
                            </SidebarMenuSubItem>
                          ))}
                        </SidebarMenuSub>
                      </SidebarMenuItem>
                    );
                  }

                  return (
                    <SidebarMenuItem key={item.title}>
                      <SidebarMenuButton
                        render={<Link href={item.href!} />}
                        isActive={pathname.startsWith(item.href!)}
                      >
                        {item.icon && <item.icon className="size-4" />}
                        <span>{item.title}</span>
                      </SidebarMenuButton>
                    </SidebarMenuItem>
                  );
                })}
              </SidebarMenu>
            </SidebarGroupContent>
          </SidebarGroup>
        ))}
      </SidebarContent>
    </Sidebar>
  );
}
