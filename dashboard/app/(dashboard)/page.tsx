"use client"

import { useEffect, useState } from "react"
import Link from "next/link"
import { Plus, Server, Copy, Check, Settings } from "lucide-react"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import {
    Dialog,
    DialogContent,
    DialogDescription,
    DialogFooter,
    DialogHeader,
    DialogTitle,
    DialogTrigger,
} from "@/components/ui/dialog"
import { useAuth, api } from "@/lib/auth-context"

interface Cluster {
    id: string
    name: string
    status: string
    last_heartbeat: string
}

export default function DashboardHome() {
    const [clusters, setClusters] = useState<Cluster[]>([])
    const [loading, setLoading] = useState(true)
    const [open, setOpen] = useState(false)
    const [newClusterName, setNewClusterName] = useState("")
    const [createdClusterToken, setCreatedClusterToken] = useState<string | null>(null)
    const [copied, setCopied] = useState(false)
    const { user } = useAuth()

    const [configOpen, setConfigOpen] = useState(false)
    const [selectedClusterId, setSelectedClusterId] = useState<string | null>(null)
    const [kubeconfig, setKubeconfig] = useState("")
    const [configStatus, setConfigStatus] = useState<"idle" | "submitting" | "success" | "error">("idle")

    const handleConfigureCluster = async () => {
        if (!selectedClusterId) return
        setConfigStatus("submitting")
        try {
            await api.post(`/clusters/${selectedClusterId}/jobs/trigger`, {
                job_type: "configure_cluster",
                payload: { kubeconfig }
            })
            setConfigStatus("success")
            setTimeout(() => {
                setConfigOpen(false)
                setConfigStatus("idle")
                setKubeconfig("")
            }, 2000)
        } catch (e) {
            console.error("Failed to configure cluster", e)
            setConfigStatus("error")
        }
    }

    const openConfigModal = (clusterId: string) => {
        setSelectedClusterId(clusterId)
        setConfigOpen(true)
    }

    // Fetch Clusters (Periodic Refresh)
    useEffect(() => {
        fetchClusters()
        const interval = setInterval(fetchClusters, 5000) // Poll every 5s
        return () => clearInterval(interval)
    }, [])

    const fetchClusters = async () => {
        try {
            const res = await api.get("/clusters")
            setClusters(res.data)
        } catch (e) {
            console.error("Failed to fetch clusters", e)
        } finally {
            setLoading(false)
        }
    }

    const handleCreateCluster = async () => {
        try {
            const res = await api.post("/clusters", { name: newClusterName })
            if (res.status === 200) {
                setCreatedClusterToken(res.data.token) // Token is returned only once
                fetchClusters()
            }
        } catch (e) {
            console.error("Failed to create cluster", e)
        }
    }

    const copyToClipboard = () => {
        if (createdClusterToken) {
            navigator.clipboard.writeText(`docker run -e CLUSTER_TOKEN=${createdClusterToken} sre-agent`)
            setCopied(true)
            setTimeout(() => setCopied(false), 2000)
        }
    }

    const resetModal = () => {
        setOpen(false)
        setCreatedClusterToken(null)
        setNewClusterName("")
        setCopied(false)
    }

    return (
        <div className="space-y-6">
            <div className="flex justify-between items-center">
                <h1 className="text-3xl font-bold tracking-tight">Clusters</h1>

                <Dialog open={open} onOpenChange={setOpen}>
                    <DialogTrigger asChild>
                        <Button onClick={() => setCreatedClusterToken(null)}>
                            <Plus className="mr-2 h-4 w-4" /> Connect Cluster
                        </Button>
                    </DialogTrigger>
                    <DialogContent className="sm:max-w-[500px]">
                        <DialogHeader>
                            <DialogTitle>Connect a New Cluster</DialogTitle>
                            <DialogDescription>
                                Create a cluster to generate an access token for your agent.
                            </DialogDescription>
                        </DialogHeader>

                        {!createdClusterToken ? (
                            <div className="grid gap-4 py-4">
                                <div className="grid grid-cols-4 items-center gap-4">
                                    <Label htmlFor="name" className="text-right">
                                        Name
                                    </Label>
                                    <Input
                                        id="name"
                                        value={newClusterName}
                                        onChange={(e) => setNewClusterName(e.target.value)}
                                        placeholder="Production US-East"
                                        className="col-span-3"
                                    />
                                </div>
                            </div>
                        ) : (
                            <div className="space-y-4 py-4">
                                <div className="p-4 bg-green-50 dark:bg-green-900/20 text-green-700 dark:text-green-300 rounded-md border border-green-200 dark:border-green-800">
                                    <h4 className="font-semibold flex items-center gap-2">
                                        <Check className="h-4 w-4" /> Cluster Created Successfully
                                    </h4>
                                    <p className="text-sm mt-1">Run this command on your edge server:</p>
                                </div>
                                <div className="relative">
                                    <pre className="bg-slate-950 text-slate-50 p-4 rounded-lg text-xs overflow-x-auto">
                                        <code>docker run -e CLUSTER_TOKEN={createdClusterToken} sre-agent</code>
                                    </pre>
                                    <Button
                                        size="icon"
                                        variant="ghost"
                                        className="absolute top-2 right-2 hover:bg-slate-800 text-slate-400"
                                        onClick={copyToClipboard}
                                    >
                                        {copied ? <Check className="h-4 w-4 text-green-500" /> : <Copy className="h-4 w-4" />}
                                    </Button>
                                </div>
                                <p className="text-xs text-muted-foreground text-center">
                                    This token will not be shown again. Save it securely.
                                </p>
                            </div>
                        )}

                        <DialogFooter>
                            {!createdClusterToken ? (
                                <Button onClick={handleCreateCluster} disabled={!newClusterName}>Create Cluster</Button>
                            ) : (
                                <Button onClick={resetModal}>Done</Button>
                            )}
                        </DialogFooter>
                    </DialogContent>
                </Dialog>
            </div>

            {loading ? (
                <div>Loading clusters...</div>
            ) : (
                <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
                    {clusters.map((cluster) => {
                        // Calculate status based on heartbeat (30s threshold)
                        const lastHeartbeat = cluster.last_heartbeat ? new Date(cluster.last_heartbeat).getTime() : 0
                        const timeSinceHeartbeat = Date.now() - lastHeartbeat
                        const isOnline = lastHeartbeat > 0 && timeSinceHeartbeat < 30000 // 30 seconds

                        return (
                            <Card key={cluster.id} className={isOnline ? "border-green-500/50" : "border-red-200 dark:border-red-900/30"}>
                                <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                                    <CardTitle className="text-sm font-medium">
                                        {cluster.name}
                                    </CardTitle>
                                    <Badge variant={isOnline ? "default" : "destructive"} className={isOnline ? "bg-green-500 hover:bg-green-600" : "bg-red-500 hover:bg-red-600"}>
                                        {isOnline ? "🟢 Online" : "🔴 Offline"}
                                    </Badge>
                                </CardHeader>
                                <CardContent>
                                    <div className="text-2xl font-bold">
                                        <Server className={`inline-block mr-2 ${isOnline ? "text-green-500" : "text-gray-400"}`} />
                                    </div>
                                    <p className="text-xs text-muted-foreground mt-2">
                                        Last heartbeat: {cluster.last_heartbeat ? new Date(cluster.last_heartbeat).toLocaleString() : "Never"}
                                    </p>
                                </CardContent>
                                <CardFooter className="flex gap-2">
                                    <Link href={`/clusters/${cluster.id}`} className="flex-1">
                                        <Button variant="outline" className="w-full">View Details</Button>
                                    </Link>
                                    <Button variant="ghost" size="icon" onClick={() => openConfigModal(cluster.id)}>
                                        <Settings className="h-4 w-4" />
                                    </Button>
                                </CardFooter>
                            </Card>
                        )
                    })}

                    {/* Configuration Modal */}
                    <Dialog open={configOpen} onOpenChange={setConfigOpen}>
                        <DialogContent className="sm:max-w-[600px]">
                            <DialogHeader>
                                <DialogTitle>Configure Cluster Connection</DialogTitle>
                                <DialogDescription>
                                    Paste your <code>kubeconfig</code> YAML below to allow the agent to manage this cluster.
                                </DialogDescription>
                            </DialogHeader>
                            <div className="grid gap-4 py-4">
                                <Label htmlFor="kubeconfig">Kubeconfig YAML</Label>
                                <textarea
                                    id="kubeconfig"
                                    className="min-h-[300px] font-mono text-xs p-4 rounded-md border bg-slate-950 text-slate-50"
                                    placeholder="apiVersion: v1..."
                                    value={kubeconfig}
                                    onChange={(e) => setKubeconfig(e.target.value)}
                                />
                            </div>
                            <DialogFooter>
                                <Button onClick={handleConfigureCluster} disabled={!kubeconfig || configStatus === "submitting"}>
                                    {configStatus === "submitting" ? "Configuring..." :
                                        configStatus === "success" ? "Configured!" : "Update Configuration"}
                                </Button>
                            </DialogFooter>
                        </DialogContent>
                    </Dialog>

                    {clusters.length === 0 && (
                        <div className="col-span-full text-center p-10 text-gray-500 border-2 border-dashed rounded-lg">
                            No clusters found. Click "Connect Cluster" to get started.
                        </div>
                    )}
                </div>
            )}
        </div>
    )
}
