"use client"

import { useState, useEffect, useRef } from "react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { ScrollArea } from "@/components/ui/scroll-area"
import { Terminal, Play, Pause, AlertTriangle, Check, X } from "lucide-react"
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

// ... (keep intervening code)

{
    logs.map((log) => (
        <div key={log.id} className="group flex gap-2 font-mono">
            <span className="text-zinc-600 shrink-0 select-none w-[85px]">
                {log.timestamp ? new Date(log.timestamp).toLocaleTimeString([], { hour12: false }) : "[--:--:--]"}
            </span>

            {log.status === "INFO" ? (
                <div className="flex-1 flex gap-2">
                    <span className="text-blue-400 font-bold shrink-0 w-24 truncate text-right">
                        {log.agent_name}
                    </span>
                    <span className="text-zinc-400">
                        {log.tool_args}
                    </span>
                </div>
            ) : (
                <>
                    <span className="text-emerald-500 font-bold shrink-0 w-24 truncate text-right">
                        {log.agent_name}
                    </span>
                    <div className="flex-1 break-words">
                        <span className="text-zinc-300">
                            Executing <span className="text-yellow-200">{log.tool_name}</span>
                        </span>
                        <span className="text-zinc-500 ml-2 truncate inline-block max-w-[200px]">
                            {log.tool_args}
                        </span>

                        {/* Status Indicator */}
                        <div className="mt-1 pl-4 border-l-2 border-zinc-800">
                            {log.status === "PENDING" && (
                                <span className="text-yellow-500 flex items-center gap-1 text-xs">
                                    <span className="animate-spin">⟳</span> Executing...
                                </span>
                            )}
                            {log.status === "SUCCESS" && (
                                <span className="text-zinc-400 flex items-center gap-1 text-xs">
                                    <span className="text-emerald-500">✓</span> Result: <span className="text-zinc-500 truncate max-w-md">{log.result?.slice(0, 100)}...</span>
                                </span>
                            )}
                            {log.status === "FAILURE" && (
                                <span className="text-red-500 flex items-center gap-1 text-xs">
                                    ⚠ Error: {log.error_message}
                                </span>
                            )}
                        </div>
                    </div>
                </>
            )}
        </div>
    ))
}
<div ref={scrollRef} />

{/* Approval Prompt */ }
{
    status === "WAITING_APPROVAL" && (
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
    )
}
                    </div >
                </ScrollArea >
            </CardContent >
        </Card >
    )
}
