"use client"

import * as React from "react"

import {
  SidebarMenu,
  SidebarMenuButton,
  SidebarMenuItem,
  useSidebar,
} from "@/components/ui/sidebar"
import { GalleryVerticalEnd } from "lucide-react"

export function TeamSwitcher({
  teams,
}: {
  teams: {
    name: string
    logo: React.ReactNode
    plan: string
  }[]
}) {
  const { isMobile, state } = useSidebar()
  const [activeTeam, setActiveTeam] = React.useState(teams[0])
  const isCollapsed = state === "collapsed"

  if (!activeTeam) {
    return null
  }

  return (
    <SidebarMenu>
      <SidebarMenuItem>
        <SidebarMenuButton
          size="lg"
          className="flex items-center justify-between px-3 h-auto py-3"
        >
          <a href="#" className="flex items-center gap-3 flex-1">
            <div className="flex aspect-square size-8 items-center justify-center rounded-full bg-sidebar-primary text-sidebar-primary-foreground shrink-0">
              {activeTeam.logo}
            </div>
            {/* Collapse to logo only when sidebar is collapsed */}
            <div
              className={`flex flex-col gap-1 leading-none overflow-hidden transition-all duration-200 ${
                isCollapsed
                  ? "max-w-0 opacity-0"
                  : "max-w-xs opacity-100"
              }`}
            >
              <span className="text-base font-bold whitespace-nowrap">
                {activeTeam.name}
              </span>
              <span className="text-xs text-muted-foreground whitespace-nowrap">
                {activeTeam.plan}
              </span>
            </div>
          </a>
        </SidebarMenuButton>
      </SidebarMenuItem>
    </SidebarMenu>
  )
}
