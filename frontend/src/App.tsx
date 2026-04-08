import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { Dashboard } from '@/pages/Dashboard'
import { Protocols } from '@/pages/Protocols'
import { Checklist } from '@/pages/Checklist'

export default function App() {
  return (
    <div className="min-h-screen bg-background text-foreground">
      <header className="border-b px-6 py-4">
        <h1 className="text-xl font-semibold tracking-tight">Longevity OS</h1>
      </header>
      <main className="px-6 py-6">
        <Tabs defaultValue="dashboard">
          <TabsList className="mb-6">
            <TabsTrigger value="dashboard">Dashboard</TabsTrigger>
            <TabsTrigger value="checklist">Today</TabsTrigger>
            <TabsTrigger value="protocols">Protocols</TabsTrigger>
          </TabsList>
          <TabsContent value="dashboard"><Dashboard /></TabsContent>
          <TabsContent value="checklist"><Checklist /></TabsContent>
          <TabsContent value="protocols"><Protocols /></TabsContent>
        </Tabs>
      </main>
    </div>
  )
}
