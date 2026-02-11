"use client"

import { useState } from "react"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { ScrollArea } from "@/components/ui/scroll-area"
import { Terminal, Shield, Check, X, AlertOctagon, Play } from "lucide-react"
import Cookies from "js-cookie"

interface Job {
    id: string
    status: string
    logs: string | null
    result: string | null
}

interface IncidentCommandCenterProps {
    job: Job
    onRefresh: () => void
}

export function IncidentCommandCenter({ job, onRefresh }: IncidentCommandCenterProps) {
    const [actionLoading, setActionLoading] = useState(false)

    const handleApproval = async (approved: boolean) => {
        setActionLoading(true)
        try {
            const token = Cookies.get("token")
            await fetch(`/api/v1/jobs/${job.id}/approve`, {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                    "Authorization": `Bearer ${token}`
                },
                body: JSON.stringify({ approved })
            })
            onRefresh()
        } catch (error) {
            console.error("Failed to submit approval", error)
        } finally {
            setActionLoading(false)
        }
    }

    return (
        <div className="grid gap-4 md:grid-cols-12 h-[500px]">
            {/* Left: Incident Context */}
            <Card className="md:col-span-3 flex flex-col">
                <CardHeader>
                    <CardTitle className="text-sm font-medium text-muted-foreground">INCIDENT CONTEXT</CardTitle>
                    <div className="flex items-center gap-2">
                        <Badge variant="outline" className="animate-pulse border-red-500 text-red-500">
                            Critical
                        </Badge>
                        <span className="text-xl font-bold tracking-tight">high_latency</span>
                    </div>
                </CardHeader>
                <CardContent className="space-y-4">
                    <div>
                        <p className="text-xs text-muted-foreground uppercase">Hypothesis</p>
                        <p className="text-sm">
                            Commit <code className="bg-muted px-1 py-0.5 rounded">a1b2c</code> introduced a 5s sleep in checkout flow.
                        </p>
                    </div>
                    <div>
                        <p className="text-xs text-muted-foreground uppercase">Duration</p>
                        <p className="font-mono text-lg">12m 30s</p>
                    </div>
                </CardContent>
            </Card>

            {/* Center: Live Terminal */}
            <Card className="md:col-span-6 flex flex-col bg-black border-zinc-800">
                <CardHeader className="py-3 border-b border-zinc-800">
                    <div className="flex items-center gap-2">
                        <Terminal className="h-4 w-4 text-green-500" />
                        <CardTitle className="text-sm font-mono text-zinc-400">AGENT_TERMINAL_OUTPUT</CardTitle>
                    </div>
                </CardHeader>
                <CardContent className="flex-1 p-0 overflow-hidden relative">
                    <ScrollArea className="h-full w-full p-4 font-mono text-xs text-zinc-300">
                        {job.logs ? (
                            job.logs.split('\n').map((line, i) => (
                                <div key={i} className="py-0.5 border-l-2 border-transparent hover:border-zinc-700 pl-2">
                                    <span className="text-zinc-500 mr-2">
                                        {new Date().toLocaleTimeString().split(' ')[0]}
                                    </span>
                                    {line}
                                </div>
                            ))
                        ) : (
                            <div className="flex flex-col items-center justify-center h-full text-zinc-600 gap-2">
                                <Loader2 className="h-8 w-8 animate-spin" />
                                <p>Initializing Agent Runtime...</p>
                            </div>
                        )}
                        {/* Auto-scroll anchor */}
                        <div id="terminal-end" />
                    </ScrollArea>
                </CardContent>
            </Card>

            {/* Right: Action Deck */}
            <Card className="md:col-span-3 flex flex-col bg-slate-900/50 border-slate-800">
                <CardHeader>
                    <CardTitle className="text-sm font-medium text-slate-400">ACTION DECK</CardTitle>
                </CardHeader>
                <CardContent className="flex-1 flex flex-col justify-between">
                    <div className="space-y-4">
                        <div className="p-3 bg-slate-900 rounded border border-slate-700">
                            <div className="flex items-center gap-2 text-blue-400 mb-2">
                                <Shield className="h-4 w-4" />
                                <span className="text-xs font-bold uppercase">Proposed Plan</span>
                            </div>
                            <ul className="text-xs space-y-2 text-slate-300">
                                <li className="flex gap-2">
                                    <span className="text-slate-500">1.</span>
                                    <span>Restart Deployment</span>
                                </li>
                                <li className="flex gap-2">
                                    <span className="text-slate-500">2.</span>
                                    <span>Revert Commit <code className="text-xs">a1b2c</code></span>
                                </li>
                            </ul>
                        </div>
                    </div>

                    <div className="space-y-2 mt-4">
                        {job.status === 'wait_approval' ? (
                            <>
                                <Button
                                    className="w-full bg-green-600 hover:bg-green-700 text-white"
                                    onClick={() => handleApproval(true)}
                                    disabled={actionLoading}
                                >
                                    <Check className="mr-2 h-4 w-4" />
                                    APPROVE PLAN
                                </Button>
                                <Button
                                    variant="outline"
                                    className="w-full border-red-900 text-red-500 hover:bg-red-950 hover:text-red-400"
                                    onClick={() => handleApproval(false)}
                                    disabled={actionLoading}
                                >
                                    <X className="mr-2 h-4 w-4" />
                                    REJECT
                                </Button>
                            </>
                        ) : (
                            <Button variant="ghost" className="w-full text-slate-500 cursor-default" disabled>
                                {job.status === 'running' ? (
                                    <span className="flex items-center animate-pulse">
                                        <Play className="mr-2 h-3 w-3" /> AGENT RUNNING
                                    </span>
                                ) : (
                                    "NO PENDING ACTIONS"
                                )}
                            </Button>
                        )}
                    </div>
                </CardContent>
            </Card>
        </div>
    )
}

function Loader2(props: any) {
    return (
        <svg
            {...props}
            xmlns="http://www.w3.org/2000/svg"
            width="24"
            height="24"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            strokeWidth="2"
            strokeLinecap="round"
            strokeLinejoin="round"
        >
            <path d="M21 12a9 9 0 1 1-6.219-8.56" />
        </svg>
    )
}
