# Design Specification for Altostrat Elevate-HR UI (Stitch Prototype)

This design document outlines the UI layout, component hierarchies, and backend integration hooks for the Altostrat Elevate-HR Virtual Assistant. You can use these specifications inside **Google Stitch** to generate the high-fidelity UI mockup and frontend code.

---

## 1. Design System & Style Guide

To maintain consistency with the Altostrat theme, use the following variables in the design system configuration:

*   **Background (Dark Theme):** `#121212` (slate background)
*   **Surface / Cards:** `#1e1e1e` (slightly lighter charcoal grey)
*   **Primary Accent:** `#7cc4ff` (light sky blue for buttons, active tabs, and primary actions)
*   **Secondary Accent:** `#b5c9e2` (muted grey-blue for secondary text, labels, and borders)
*   **Text (Primary):** `#ffffff` (pure white)
*   **Text (Muted):** `#a0a0a0` (light grey)
*   **Alert / Green:** `#81c784` (success/submitted state)
*   **Alert / Red:** `#e57373` (denied/insufficient balance state)

---

## 2. Page Layout: Master Dashboard Layout

The interface is structured as a single-page app (SPA) with a **Sidebar Navigation** and a **Main Content viewport**.

```
+--------------------------------------------------------------------------+
|  Altostrat Elevate-HR   |                                                |
|  --------------------   |  Header: Active Employee Context (EmpID: E1209)|
|  [💬 Chat Assistant]     |  --------------------------------------------  |
|  [📅 Leave Dashboard]   |                                                |
|  [🎫 Ticket Portal]      |  Main Content Viewport                         |
|  [🖥️ Procurement]       |  (Renders active selected page/dashboard)      |
|                         |                                                |
+--------------------------------------------------------------------------+
```

### Tailwind Shell Layout
```html
<div class="flex h-screen bg-[#121212] text-white">
  <!-- Sidebar Navigation -->
  <aside class="w-64 bg-[#1e1e1e] border-r border-[#3a485a] flex flex-col">
    <div class="p-6 border-b border-[#3a485a]">
      <h1 class="text-xl font-bold text-[#7cc4ff]">Altostrat Elevate</h1>
    </div>
    <nav class="flex-1 p-4 space-y-2">
      <button class="w-full text-left py-2.5 px-4 rounded bg-[#3a485a] text-[#7cc4ff]">💬 Chat Assistant</button>
      <button class="w-full text-left py-2.5 px-4 rounded text-gray-300 hover:bg-[#203246]">📅 Leave Dashboard</button>
      <button class="w-full text-left py-2.5 px-4 rounded text-gray-300 hover:bg-[#203246]">🎫 Ticket Portal</button>
      <button class="w-full text-left py-2.5 px-4 rounded text-gray-300 hover:bg-[#203246]">🖥️ Procurement</button>
    </nav>
  </aside>
  
  <!-- Content Space -->
  <div class="flex-1 flex flex-col overflow-hidden">
    <!-- Header -->
    <header class="h-16 bg-[#1e1e1e] border-b border-[#3a485a] flex items-center justify-between px-8">
      <div class="text-sm text-[#b5c9e2]">Active Context: <span class="text-white font-semibold">E1209 (Knowledge Worker)</span></div>
      <div class="w-8 h-8 rounded-full bg-[#7cc4ff] flex items-center justify-center text-[#003366] font-bold">AJ</div>
    </header>
    <!-- Viewport -->
    <main class="flex-1 overflow-y-auto p-8">
      <!-- Active screen content goes here -->
    </main>
  </div>
</div>
```

---

## 3. Screen Designs & Components

### Screen 1: 💬 Chat Assistant (Conversational View)
A split-screen view: the left side handles the active chatbot thread, and the right side displays a "Grounding Vault" showing policy citations dynamically parsed.

*   **Left Column (Chat Container):**
    *   Scrollable message log.
    *   Input message bar with attachment and submit button.
*   **Right Column (Grounding Panel):**
    *   Displays current source documents, sections, and trust score (e.g. `Trust Score: 95%`).
    *   Clickable external link pointing to the full policy page (e.g., `Leave_Policy_2026.pdf#sec4.2`).

```html
<div class="grid grid-cols-3 gap-8 h-full">
  <!-- Chat Feed -->
  <div class="col-span-2 bg-[#1e1e1e] rounded-lg border border-[#3a485a] flex flex-col h-[70vh]">
    <div class="flex-1 p-6 space-y-4 overflow-y-auto">
      <div class="flex items-start gap-3">
        <div class="w-8 h-8 rounded bg-[#7cc4ff] text-[#003366] flex items-center justify-center font-bold">Bot</div>
        <div class="bg-[#3a485a] p-3 rounded-lg max-w-[80%] text-sm">
          Hello! How can I help you manage your leave or raise IT support requests today?
        </div>
      </div>
    </div>
    <div class="p-4 border-t border-[#3a485a] flex gap-3">
      <input type="text" placeholder="Type your message..." class="flex-1 bg-[#121212] border border-[#3a485a] rounded px-4 py-2 text-sm focus:outline-none focus:border-[#7cc4ff]" />
      <button class="bg-[#7cc4ff] text-[#003366] px-5 py-2 rounded text-sm font-semibold hover:bg-opacity-90">Send</button>
    </div>
  </div>
  
  <!-- Grounding Panel -->
  <div class="bg-[#1e1e1e] rounded-lg border border-[#3a485a] p-6 flex flex-col">
    <h3 class="text-[#7cc4ff] font-semibold mb-4 text-sm uppercase tracking-wider">Grounding Evidence</h3>
    <div class="flex-1 space-y-4">
      <div class="bg-[#121212] p-4 rounded border border-green-500/30">
        <div class="flex justify-between text-xs text-[#b5c9e2] mb-2">
          <span>Leave_Policy_2026.pdf</span>
          <span class="text-green-400 font-bold">Attribution: 94%</span>
        </div>
        <p class="text-xs text-gray-300 italic">"Employees are eligible for up to 5 days of paid bereavement leave..."</p>
      </div>
    </div>
  </div>
</div>
```

---

### Screen 2: 📅 Leave Dashboard (WorkWeek Integration)
Allows checking balances, submitting time-off, and listing active requests.

*   **Metric Cards (Top):** Accrued Vacation, Remaining Vacation, Sick Leave.
*   **Request Time Off Form:** Input fields for start date, end date, leave type (Vacation/Sick), and a submit button.
*   **Leave History Table:** Shows request list with status badges (`Pending`, `Approved`) and actions (Cancel).

```html
<div class="space-y-8">
  <!-- Leave Balances -->
  <div class="grid grid-cols-3 gap-6">
    <div class="bg-[#1e1e1e] p-6 rounded-lg border border-[#3a485a]">
      <div class="text-xs text-[#b5c9e2] mb-1">Accrued Vacation</div>
      <div class="text-3xl font-bold text-white">16.0 hrs <span class="text-sm font-normal text-gray-400">(2 days)</span></div>
    </div>
    <div class="bg-[#1e1e1e] p-6 rounded-lg border border-[#3a485a]">
      <div class="text-xs text-[#b5c9e2] mb-1">Remaining Vacation</div>
      <div class="text-3xl font-bold text-[#7cc4ff]">16.0 hrs</div>
    </div>
    <div class="bg-[#1e1e1e] p-6 rounded-lg border border-[#3a485a]">
      <div class="text-xs text-[#b5c9e2] mb-1">Used Sick Leave</div>
      <div class="text-3xl font-bold text-white">0.0 hrs</div>
    </div>
  </div>

  <!-- Booking Form & History -->
  <div class="grid grid-cols-2 gap-8">
    <div class="bg-[#1e1e1e] p-6 rounded-lg border border-[#3a485a]">
      <h3 class="text-lg font-semibold mb-4 text-[#7cc4ff]">Submit Leave Request</h3>
      <form class="space-y-4">
        <div>
          <label class="block text-xs text-[#b5c9e2] mb-1">Leave Type</label>
          <select class="w-full bg-[#121212] border border-[#3a485a] rounded px-3 py-2 text-sm text-white">
            <option>Vacation</option>
            <option>Sick Leave</option>
          </select>
        </div>
        <div class="grid grid-cols-2 gap-4">
          <div>
            <label class="block text-xs text-[#b5c9e2] mb-1">Start Date</label>
            <input type="date" class="w-full bg-[#121212] border border-[#3a485a] rounded px-3 py-2 text-sm text-white" />
          </div>
          <div>
            <label class="block text-xs text-[#b5c9e2] mb-1">End Date</label>
            <input type="date" class="w-full bg-[#121212] border border-[#3a485a] rounded px-3 py-2 text-sm text-white" />
          </div>
        </div>
        <button type="submit" class="w-full bg-[#7cc4ff] text-[#003366] font-bold py-2 rounded text-sm hover:bg-opacity-90">Submit Request</button>
      </form>
    </div>
    
    <div class="bg-[#1e1e1e] p-6 rounded-lg border border-[#3a485a] flex flex-col">
      <h3 class="text-lg font-semibold mb-4 text-white">Request History</h3>
      <div class="flex-1 overflow-x-auto text-sm">
        <table class="w-full text-left">
          <thead>
            <tr class="border-b border-[#3a485a] text-[#b5c9e2] text-xs">
              <th class="pb-2">ID</th>
              <th class="pb-2">Dates</th>
              <th class="pb-2">Status</th>
              <th class="pb-2">Actions</th>
            </tr>
          </thead>
          <tbody>
            <tr class="border-b border-[#3a485a]/40 text-xs">
              <td class="py-3">LV-99201</td>
              <td>08/20 - 08/21</td>
              <td><span class="bg-green-500/20 text-green-400 px-2 py-0.5 rounded">Submitted</span></td>
              <td><button class="text-red-400 hover:underline">Cancel</button></td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  </div>
</div>
```

---

### Screen 3: 🎫 Ticket Portal (ServiceImmediately Integration)
Displays open tickets, creation dialog, and activity comments timeline.

```html
<div class="space-y-6">
  <div class="flex justify-between items-center">
    <h2 class="text-xl font-bold">IT Support Tickets</h2>
    <button class="bg-[#7cc4ff] text-[#003366] px-4 py-2 rounded text-sm font-semibold hover:bg-opacity-90">Create Ticket</button>
  </div>
  
  <div class="grid grid-cols-3 gap-8">
    <!-- Active Tickets list -->
    <div class="col-span-1 bg-[#1e1e1e] rounded-lg border border-[#3a485a] p-4 space-y-3">
      <div class="p-3 bg-[#121212] rounded border-l-4 border-yellow-400">
        <div class="flex justify-between text-xs text-[#b5c9e2] mb-1">
          <span>INC0049281</span>
          <span>Moderate</span>
        </div>
        <h4 class="font-semibold text-sm">VPN connection dropping</h4>
        <span class="text-xs text-yellow-400">In Progress</span>
      </div>
    </div>
    
    <!-- Ticket Details & Activity Comments Timeline -->
    <div class="col-span-2 bg-[#1e1e1e] rounded-lg border border-[#3a485a] p-6 flex flex-col h-[60vh]">
      <div class="border-b border-[#3a485a] pb-4 mb-4">
        <h3 class="text-lg font-semibold">INC0049281: VPN connection dropping</h3>
        <p class="text-xs text-[#b5c9e2] mt-1">Requested by: E1209 | Assigned to: Network Operations</p>
      </div>
      <div class="flex-1 overflow-y-auto space-y-4 pr-2">
        <div class="bg-[#121212] p-3 rounded text-xs">
          <div class="text-[#7cc4ff] font-bold mb-1">Network Tech <span class="text-[10px] text-gray-500 font-normal">2 hrs ago</span></div>
          We are investigating a routing issue in the Austin GFE region.
        </div>
      </div>
      <div class="mt-4 pt-4 border-t border-[#3a485a] flex gap-2">
        <input type="text" placeholder="Add comment..." class="flex-1 bg-[#121212] border border-[#3a485a] rounded px-3 py-2 text-xs text-white" />
        <button class="bg-[#7cc4ff] text-[#003366] px-4 py-2 rounded text-xs font-semibold">Post</button>
      </div>
    </div>
  </div>
</div>
```

---

## 4. Integration Hooks (Connecting Stitch to ADK Backend)

When you export the layout from Google Stitch, link the UI actions to the running ADK agent's **A2A Server Endpoints** using standard HTTP `fetch` requests:

### A2A Configuration
*   **Base URL:** `http://127.0.0.1:8080` (or the deployed Cloud Run service URL)
*   **Chat POST Endpoint:** `/a2a/app/chat`
    *   **Body Schema:**
        ```json
        {
          "message": "User query text here",
          "session_id": "optional-session-id"
        }
        ```
*   **Response Handling:**
    The response contains the model's text response and tool execution traces:
    ```javascript
    fetch("http://127.0.0.1:8080/a2a/app/chat", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ message: "What is my leave balance?" })
    })
    .then(res => res.json())
    .then(data => {
      // 1. Render message: data.response
      // 2. Refresh dashboard if leave balances tool was called
    });
    ```
