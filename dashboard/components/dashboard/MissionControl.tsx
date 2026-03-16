"use client"

import { useState, useEffect, useRef } from "react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { ScrollArea } from "@/components/ui/scroll-area"
import { Terminal, Check, X } from "lucide-react"
import Cookies from "js-cookie"

interface AuditLog {
    id: string
    timestamp: string
    agent_name: string
    tool_name: string
    tool_args: string
    status: "PENDING" | "SUCCESS" | "FAILURE" | "INFO"
    result?: string
    error_message?: string
}

interface MissionControlProps {
    sessionId: string
    clusterId: string
}

export function MissionControl({ sessionId, clusterId }: MissionControlProps) {
    const [logs, setLogs] = useState<AuditLog[]>([])
    const [status, setStatus] = useState<string>("UNKNOWN")
    const [loading, setLoading] = useState(false)
    const scrollRef = useRef<HTMLDivElement>(null)

    useEffect(() => {
        if (!sessionId) return

        const fetchState = async () => {
            try {
                const token = Cookies.get("token")
                const res = await fetch(`/agent/state/${sessionId}`, {
                    headers: { Authorization: `Bearer ${token}` },
                })
                if (!res.ok) return
                const data = await res.json()
                setStatus(data.status || "UNKNOWN")
                if (data.logs && Array.isArray(data.logs)) {
                    setLogs(data.logs)
                }
            } catch (error) {
                console.error("Failed to fetch agent state:", error)
            }
        }

        fetchState()
        const interval = setInterval(fetchState, 3000)
        return () => clearInterval(interval)
    }, [sessionId])

    useEffect(() => {
        scrollRef.current?.scrollIntoView({ behavior: "smooth" })
    }, [logs])

    const handleApprove = async () => {
        setLoading(true)
        try {
            const token = Cookies.get("token")
            await fetch(`/approve/${sessionId}`, {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                    Authorization: `Bearer ${token}`,
                },
            })
        } catch (error) {
            console.error("Failed to approve remediation:", error)
        } finally {
            setLoading(false)
        }
    }

    return (
        <Card className="bg-black border-zinc-800">
            <CardHeader className="py-3 border-b border-zinc-800">
                <div className="flex items-center gap-2">
                    <Terminal className="h-4 w-4 text-green-500" />
                    <CardTitle className="text-sm font-mono text-zinc-400">
                        MISSION CONTROL — {status}
                    </CardTitle>
                </div>
            </CardHeader>
            <CardContent className="p-0">
                <ScrollArea className="h-[400px] p-4 font-mono text-xs text-zinc-300 space-y-1">
                    {logs.map((log) => (
                        <div key={log.id} className="group flex gap-2 font-mono">
                            <span className="text-zinc-600 shrink-0 select-none w-[85px]">
                                {log.timestamp
                                    ? new Date(log.timestamp).toLocaleTimeString([], { hour12: false })
                                    : "[--:--:--]"}
                            </span>

                            {log.status === "INFO" ? (
                                <div className="flex-1 flex gap-2">
                                    <span className="text-blue-400 font-bold shrink-0 w-24 truncate text-right">
                                        {log.agent_name}
                                    </span>
                                    <span className="text-zinc-400">{log.tool_args}</span>
                                </div>
                            ) : (
                                <>
                                    <span className="text-emerald-500 font-bold shrink-0 w-24 truncate text-right">
                                        {log.agent_name}
                                    </span>
                                    <div className="flex-1 break-words">
                                        <span className="text-zinc-300">
                                            Executing{" "}
                                            <span className="text-yellow-200">{log.tool_name}</span>
                                        </span>
                                        <span className="text-zinc-500 ml-2 truncate inline-block max-w-[200px]">
                                            {log.tool_args}
                                        </span>

                                        <div className="mt-1 pl-4 border-l-2 border-zinc-800">
                                            {log.status === "PENDING" && (
                                                <span className="text-yellow-500 flex items-center gap-1 text-xs">
                                                    <span className="animate-spin">&#x27F3;</span> Executing...
                                                </span>
                                            )}
                                            {log.status === "SUCCESS" && (
                                                <span className="text-zinc-400 flex items-center gap-1 text-xs">
                                                    <span className="text-emerald-500">&#x2713;</span> Result:{" "}
                                                    <span className="text-zinc-500 truncate max-w-md">
                                                        {log.result?.slice(0, 100)}...
                                                    </span>
                                                </span>
                                            )}
                                            {log.status === "FAILURE" && (
                                                <span className="text-red-500 flex items-center gap-1 text-xs">
                                                    &#x26A0; Error: {log.error_message}
                                                </span>
                                            )}
                                        </div>
                                    </div>
                                </>
                            )}
                        </div>
                    ))}
                    <div ref={scrollRef} />

                    {status === "WAITING_APPROVAL" && (
                        <div className="mt-8 border-t border-dashed border-zinc-700 pt-4">
                            <p className="text-yellow-400 animate-pulse mb-4">
                                &gt;_ SYSTEM PAUSED via Policy Gate (Revert Commit Detected).
                                <br />
                                &gt;_ AWAITING HUMAN AUTHORIZATION...
                            </p>
                            <div className="flex gap-4">
                                <Button
                                    onClick={handleApprove}
                                    disabled={loading}
                                    className="bg-emerald-600 hover:bg-emerald-700 text-white border-none"
                                >
                                    <Check className="mr-2 h-4 w-4" />
                                    AUTHORIZE EXECUTION
                                </Button>
                                <Button
                                    variant="outline"
                                    disabled={loading}
                                    className="border-red-800 text-red-500 hover:bg-red-950 hover:text-red-400"
                                >
                                    <X className="mr-2 h-4 w-4" />
                                    ABORT MISSION
                                </Button>
                            </div>
                        </div>
                    )}
                </ScrollArea>
            </CardContent>
        </Card>
    )
}
