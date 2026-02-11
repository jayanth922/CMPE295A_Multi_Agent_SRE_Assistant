"use client"

import { useEffect, useState } from "react"
import { useRouter } from "next/navigation"
import Cookies from "js-cookie"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from "@/components/ui/card"
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Plus, Server, LogOut, Loader2, Trash2 } from "lucide-react"

interface Cluster {
  id: string
  name: string
  status: string
  created_at: string
}

export default function DashboardPage() {
  const router = useRouter()
  const [clusters, setClusters] = useState<Cluster[]>([])
  const [loading, setLoading] = useState(true)
  const [createOpen, setCreateOpen] = useState(false)
  const [newClusterName, setNewClusterName] = useState("")
  const [createdToken, setCreatedToken] = useState("")
  const [createLoading, setCreateLoading] = useState(false)
  const [deleteLoading, setDeleteLoading] = useState<string | null>(null)

  useEffect(() => {
    fetchClusters()
    const interval = setInterval(fetchClusters, 5000) // Poll every 5s
    return () => clearInterval(interval)
  }, [])

  const fetchClusters = async () => {
    try {
      const token = Cookies.get("token")
      const res = await fetch("/api/v1/clusters", {
        headers: {
          "Authorization": `Bearer ${token}`
        }
      })
      if (res.status === 401) {
        router.push("/login")
        return
      }
      if (res.ok) {
        const data = await res.json()
        setClusters(data)
      }
    } catch (error) {
      console.error("Failed to fetch clusters", error)
    } finally {
      setLoading(false)
    }
  }

  const handleCreateCluster = async (e: React.FormEvent) => {
    e.preventDefault()
    setCreateLoading(true)
    try {
      const token = Cookies.get("token")
      const res = await fetch("/api/v1/clusters", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "Authorization": `Bearer ${token}`
        },
        body: JSON.stringify({ name: newClusterName }),
      })
      if (res.ok) {
        const data = await res.json()
        setCreatedToken(data.token) // API returns token on creation
        fetchClusters() // Refresh list
      }
    } catch (error) {
      console.error("Failed to create cluster", error)
    } finally {
      setCreateLoading(false)
      setNewClusterName("")
    }
  }

  const handleDeleteCluster = async (clusterId: string) => {
    if (!confirm("Are you sure you want to delete this cluster?")) return
    setDeleteLoading(clusterId)
    try {
      const token = Cookies.get("token")
      const res = await fetch(`/api/v1/clusters/${clusterId}`, {
        method: "DELETE",
        headers: { "Authorization": `Bearer ${token}` }
      })
      if (res.ok) {
        fetchClusters()
      } else {
        alert("Failed to delete cluster")
      }
    } catch (error) {
      console.error("Failed to delete cluster", error)
    } finally {
      setDeleteLoading(null)
    }
  }

  const handleLogout = async () => {
    try {
      const token = Cookies.get("token")
      await fetch("/auth/logout", {
        method: "POST",
        headers: { "Authorization": `Bearer ${token}` }
      })
    } catch (e) {
      // Ignore error
    }
    Cookies.remove("token")
    router.push("/login")
  }

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900">
      {/* Header */}
      <header className="bg-white dark:bg-gray-800 shadow">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4 flex justify-between items-center">
          <h1 className="text-2xl font-bold text-gray-900 dark:text-white">SRE Platform Dashboard</h1>
          <Button variant="ghost" onClick={handleLogout}>
            <LogOut className="mr-2 h-4 w-4" /> Logout
          </Button>
        </div>
      </header>

      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Actions */}
        <div className="flex justify-between items-center mb-6">
          <h2 className="text-xl font-semibold text-gray-800 dark:text-gray-200">Your Clusters</h2>
          <Dialog open={createOpen} onOpenChange={setCreateOpen}>
            <DialogTrigger asChild>
              <Button className="bg-blue-600 hover:bg-blue-700">
                <Plus className="mr-2 h-4 w-4" /> Add Cluster
              </Button>
            </DialogTrigger>
            <DialogContent>
              <DialogHeader>
                <DialogTitle>Add New Kubernetes Cluster</DialogTitle>
                <DialogDescription>
                  Create a new cluster to generate an onboarding token.
                </DialogDescription>
              </DialogHeader>

              {!createdToken ? (
                <form onSubmit={handleCreateCluster}>
                  <div className="grid gap-4 py-4">
                    <div className="grid grid-cols-4 items-center gap-4">
                      <Label htmlFor="name" className="text-right">
                        Name
                      </Label>
                      <Input
                        id="name"
                        value={newClusterName}
                        onChange={(e) => setNewClusterName(e.target.value)}
                        className="col-span-3"
                        placeholder="e.g. Production US-East"
                        required
                      />
                    </div>
                  </div>
                  <DialogFooter>
                    <Button type="submit" disabled={createLoading}>
                      {createLoading ? <Loader2 className="mr-2 h-4 w-4 animate-spin" /> : null}
                      Create Cluster
                    </Button>
                  </DialogFooter>
                </form>
              ) : (
                <div className="space-y-4 py-4">
                  <div className="bg-green-50 p-4 rounded-md border border-green-200">
                    <p className="text-green-800 font-medium mb-2">Cluster Created Successfully!</p>
                    <p className="text-sm text-green-700 mb-4">
                      Run the following command on your cluster to connect it:
                    </p>
                    <div className="bg-gray-900 text-gray-100 p-3 rounded font-mono text-sm break-all">
                      helm install sre-agent ./charts/sre-agent --set token={createdToken}
                    </div>
                  </div>
                  <DialogFooter>
                    <Button onClick={() => { setCreateOpen(false); setCreatedToken(""); }}>
                      Done
                    </Button>
                  </DialogFooter>
                </div>
              )}
            </DialogContent>
          </Dialog>
        </div>

        {/* Cluster List */}
        {loading ? (
          <div className="flex justify-center py-12">
            <Loader2 className="h-8 w-8 animate-spin text-gray-400" />
          </div>
        ) : clusters.length === 0 ? (
          <div className="text-center py-12 bg-white dark:bg-gray-800 rounded-lg shadow border border-dashed border-gray-300">
            <Server className="mx-auto h-12 w-12 text-gray-400" />
            <h3 className="mt-2 text-sm font-semibold text-gray-900 dark:text-gray-100">No clusters</h3>
            <p className="mt-1 text-sm text-gray-500">Get started by creating a new cluster.</p>
          </div>
        ) : (
          <div className="grid grid-cols-1 gap-6 sm:grid-cols-2 lg:grid-cols-3">
            {clusters.map((cluster) => (
              <Card key={cluster.id} className="hover:shadow-md transition-shadow">
                <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                  <CardTitle className="text-sm font-medium">
                    {cluster.name}
                  </CardTitle>
                  <div className="flex items-center space-x-2">
                    <Server className={`h-4 w-4 ${cluster.status === 'online' ? 'text-green-500' : 'text-gray-500'}`} />
                    <Button variant="ghost" size="icon" className="h-6 w-6 text-red-500 hover:text-red-700 hover:bg-red-50" onClick={() => handleDeleteCluster(cluster.id)} disabled={deleteLoading === cluster.id}>
                      {deleteLoading === cluster.id ? <Loader2 className="h-3 w-3 animate-spin" /> : <Trash2 className="h-3 w-3" />}
                    </Button>
                  </div>
                </CardHeader>
                <CardContent>
                  <div className={`text-2xl font-bold capitalize ${cluster.status === 'online' ? 'text-green-600' : 'text-gray-600'}`}>
                    {cluster.status}
                  </div>
                  <p className="text-xs text-muted-foreground mt-1">
                    ID: {cluster.id.substring(0, 8)}...
                  </p>
                  <div className="mt-4">
                    <Button variant="outline" size="sm" className="w-full" onClick={() => router.push(`/clusters/${cluster.id}`)}>
                      View Details
                    </Button>
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        )}
      </main>
    </div>
  )
}
