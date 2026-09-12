/**
 * TourMate Offline Storage & Export Service
 * Fulfills VTU Major Project Synopsis Slide 20 Non-Functional Requirement #3:
 * "Offline mode (downloaded tours) is highly desirable for low-network areas"
 */

const OFFLINE_KEY = "tourmate_offline_itineraries";

export function getOfflineItineraries() {
  try {
    const raw = localStorage.getItem(OFFLINE_KEY);
    return raw ? JSON.parse(raw) : [];
  } catch (err) {
    console.error("Error reading offline itineraries:", err);
    return [];
  }
}

export function isItineraryOffline(id) {
  const items = getOfflineItineraries();
  return items.some(item => item.id === id);
}

export function saveItineraryOffline(itinerary) {
  try {
    const items = getOfflineItineraries();
    const existingIndex = items.findIndex(item => item.id === itinerary.id);
    const enriched = {
      ...itinerary,
      savedOfflineAt: new Date().toISOString(),
      offlineReady: true
    };

    if (existingIndex >= 0) {
      items[existingIndex] = enriched;
    } else {
      items.unshift(enriched);
    }

    localStorage.setItem(OFFLINE_KEY, JSON.stringify(items));
    return true;
  } catch (err) {
    console.error("Failed to save itinerary offline:", err);
    return false;
  }
}

export function removeOfflineItinerary(id) {
  try {
    const items = getOfflineItineraries();
    const filtered = items.filter(item => item.id !== id);
    localStorage.setItem(OFFLINE_KEY, JSON.stringify(filtered));
    return true;
  } catch (err) {
    console.error("Failed to remove offline itinerary:", err);
    return false;
  }
}

export function exportItineraryJSON(itinerary) {
  try {
    const dataStr = "data:text/json;charset=utf-8," + encodeURIComponent(JSON.stringify(itinerary, null, 2));
    const downloadAnchor = document.createElement("a");
    const safeTitle = (itinerary.title || "tourmate_trip").replace(/[^a-zA-Z0-9_-]/g, "_");
    downloadAnchor.setAttribute("href", dataStr);
    downloadAnchor.setAttribute("download", `${safeTitle}_offline_tour.json`);
    document.body.appendChild(downloadAnchor);
    downloadAnchor.click();
    downloadAnchor.remove();
    return true;
  } catch (err) {
    console.error("Failed to export JSON:", err);
    return false;
  }
}

export function printItineraryDocument(itinerary) {
  const win = window.open("", "_blank", "width=850,height=900");
  if (!win) {
    alert("Please allow popups to generate your printable/PDF offline tour.");
    return;
  }

  const daysHtml = (itinerary.schedule || []).map(day => `
    <div style="margin-bottom: 24px; page-break-inside: avoid; border: 1px solid #e2e8f0; border-radius: 12px; padding: 18px; background: #ffffff;">
      <h3 style="margin: 0 0 12px 0; color: #0d9488; font-size: 18px; font-weight: 700; border-bottom: 2px solid #f1f5f9; padding-bottom: 6px;">
        📅 Day ${day.day} ${day.title ? `— ${day.title}` : ""}
      </h3>
      <div style="display: flex; flex-direction: column; gap: 10px;">
        ${(day.activities || []).map(act => `
          <div style="display: flex; gap: 14px; align-items: flex-start;">
            <span style="font-weight: 700; color: #475569; font-size: 13px; min-width: 70px; background: #f8fafc; padding: 2px 8px; border-radius: 6px; border: 1px solid #cbd5e1;">${act.time || "--:--"}</span>
            <div>
              <div style="font-weight: 600; color: #0f172a; font-size: 15px;">${act.name}</div>
              ${act.description ? `<div style="color: #64748b; font-size: 13px; margin-top: 2px;">${act.description}</div>` : ""}
            </div>
          </div>
        `).join("")}
      </div>
    </div>
  `).join("");

  win.document.write(`
    <!DOCTYPE html>
    <html>
      <head>
        <title>TourMate — ${itinerary.title} (Offline Travel Pass)</title>
        <meta charset="utf-8" />
        <style>
          body {
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
            color: #1e293b;
            margin: 0;
            padding: 36px;
            background: #f8fafc;
          }
          .container {
            max-width: 760px;
            margin: 0 auto;
            background: #ffffff;
            padding: 32px;
            border-radius: 16px;
            box-shadow: 0 4px 12px rgba(0,0,0,0.05);
          }
          .header {
            border-bottom: 3px solid #0d9488;
            padding-bottom: 20px;
            margin-bottom: 24px;
            display: flex;
            justify-content: space-between;
            align-items: flex-start;
          }
          .helpline-box {
            background: #ecfdf5;
            border: 1px solid #a7f3d0;
            border-radius: 8px;
            padding: 12px 16px;
            margin-bottom: 24px;
            font-size: 12px;
            color: #065f46;
          }
          @media print {
            body { padding: 0; background: #ffffff; }
            .container { box-shadow: none; padding: 0; }
            .no-print { display: none !important; }
          }
        </style>
      </head>
      <body>
        <div class="container">
          <div class="no-print" style="margin-bottom: 20px; display: flex; justify-content: flex-end; gap: 10px;">
            <button onclick="window.print()" style="background: #0d9488; color: white; border: none; padding: 10px 20px; border-radius: 8px; font-weight: 600; cursor: pointer;">🖨️ Print / Save as PDF</button>
            <button onclick="window.close()" style="background: #e2e8f0; color: #475569; border: none; padding: 10px 16px; border-radius: 8px; font-weight: 600; cursor: pointer;">Close</button>
          </div>

          <div class="header">
            <div>
              <div style="font-size: 12px; font-weight: 800; color: #0d9488; letter-spacing: 1.5px; text-transform: uppercase;">TOURMATE OFFLINE TRAVEL PASS</div>
              <h1 style="margin: 6px 0 0 0; font-size: 26px; color: #0f172a;">${itinerary.title}</h1>
              <div style="color: #64748b; font-size: 13px; margin-top: 4px;">Duration: <strong>${itinerary.days} Days</strong> • Generated with TourMate AI</div>
            </div>
            <div style="text-align: right; font-size: 12px; color: #94a3b8;">
              <div>Offline Version</div>
              <div>${new Date().toLocaleDateString()}</div>
            </div>
          </div>

          <div class="helpline-box">
            <strong>🆘 Emergency & Tourist Helplines (All India):</strong><br/>
            Tourist Police & Multi-Language Helpline: <strong>1363</strong> • National Emergency: <strong>112</strong> • Ambulance: <strong>102</strong>
          </div>

          <div>
            ${daysHtml}
          </div>

          <div style="margin-top: 32px; padding-top: 16px; border-top: 1px solid #e2e8f0; font-size: 11px; color: #94a3b8; text-align: center;">
            TourMate Virtual Tour Guide • Offline Guide for Low-Network Tourism Areas • Dept of CSE Major Project
          </div>
        </div>
      </body>
    </html>
  `);
  win.document.close();
}
