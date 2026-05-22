"use client"

import * as React from "react"

import { NavMain } from "@/components/nav-main"
import { NavProjects } from "@/components/nav-projects"
import { NavUser } from "@/components/nav-user"
import { TeamSwitcher } from "@/components/team-switcher"
import {
  Sidebar,
  SidebarContent,
  SidebarFooter,
  SidebarHeader,
  SidebarRail,
} from "@/components/ui/sidebar"
import { RowsIcon, WaveformIcon, CommandIcon, TerminalIcon, RobotIcon, BookOpenIcon, GearIcon, CropIcon, ChartPieIcon, MapTrifoldIcon } from "@phosphor-icons/react"
import { HomeIcon } from "lucide-react"

// This is sample data.
const data = {
  user: {
    name: "shadcn",
    email: "m@example.com",
    avatar: "/avatars/shadcn.jpg",
  },
  instansi: [
    {
      name: "Kementerian Pertahanan",
      logo: (
        <RowsIcon
        />
      ),
      plan: "Enterprise",
    },
  ],
  navMain: [
    {
      title: "Home",
      url: "/",
      icon: (
        <HomeIcon
        />
      ),
      isActive: true,
    },
    {
      title: "Monitor",
      url: "/monitor/overview",
      icon: (
        <RobotIcon
        />
      ),
      items: [
        {
          title: "Overview",
          url: "/monitor/overview",
        },
        {
          title: "Table View",
          url: "/monitor/table",
        },
        {
          title: "Statistics",
          url: "/monitor/statistics",
        },
      ],
    },
    {
      title: "Reports",
      url: "/reports",
      icon: (
        <RobotIcon
        />
      ),
    },
    {
      title: "Settings",
      url: "/settings",
      icon: (
        <GearIcon
        />
      ),
      
    },
  ],
}

export function AppSidebar({ ...props }: React.ComponentProps<typeof Sidebar>) {
  return (
    <Sidebar collapsible="icon" {...props}>
      <SidebarHeader>
        <TeamSwitcher teams={data.instansi} />
      </SidebarHeader>
      <SidebarContent>
        <NavMain items={data.navMain} />
      </SidebarContent>
      <SidebarFooter>
        <NavUser user={data.user} />
      </SidebarFooter>
      <SidebarRail />
    </Sidebar>
  )
}
