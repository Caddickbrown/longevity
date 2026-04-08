import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { Dashboard } from '@/pages/Dashboard'
import { Protocols } from '@/pages/Protocols'
import { Checklist } from '@/pages/Checklist'
import { Correlation } from '@/pages/Correlation'
import { Research } from '@/pages/Research'
import { BloodPanel } from '@/pages/BloodPanel'
import { Journal } from '@/pages/Journal'
import { Beliefs } from '@/pages/Beliefs'
import { Teaching } from '@/pages/Teaching'
import { Chat } from '@/pages/Chat'

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
            <TabsTrigger value="correlation">Correlation</TabsTrigger>
            <TabsTrigger value="research">Research</TabsTrigger>
            <TabsTrigger value="blood-panel">Blood Panel</TabsTrigger>
            <TabsTrigger value="journal">Journal</TabsTrigger>
            <TabsTrigger value="beliefs">Beliefs</TabsTrigger>
            <TabsTrigger value="teaching">Teaching</TabsTrigger>
            <TabsTrigger value="chat">Chat</TabsTrigger>
          </TabsList>
          <TabsContent value="dashboard"><Dashboard /></TabsContent>
          <TabsContent value="checklist"><Checklist /></TabsContent>
          <TabsContent value="protocols"><Protocols /></TabsContent>
          <TabsContent value="correlation"><Correlation /></TabsContent>
          <TabsContent value="research"><Research /></TabsContent>
          <TabsContent value="blood-panel"><BloodPanel /></TabsContent>
          <TabsContent value="journal"><Journal /></TabsContent>
          <TabsContent value="beliefs"><Beliefs /></TabsContent>
          <TabsContent value="teaching"><Teaching /></TabsContent>
          <TabsContent value="chat"><Chat /></TabsContent>
        </Tabs>
      </main>
    </div>
  )
}
