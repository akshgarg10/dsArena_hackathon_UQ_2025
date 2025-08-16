import React from "react";
import Editor from "@monaco-editor/react";

const API_URL =
  (typeof import.meta !== "undefined" && import.meta.env?.VITE_API_URL) ||
  "http://127.0.0.1:5000";

const CodeEditor = ({
  code,
  setCode,
  readonly = false,
  sessionId,
  playerId,
}) => {
  const runCode = async () => {
    // Local guards to avoid 400s
    if (!sessionId || !playerId) {
      alert("Join or create a session first (missing sessionId/playerId).");
      console.warn("runCode guard:", { sessionId, playerId });
      return;
    }
    if (!code || !code.trim()) {
      alert("Please enter some code before running.");
      return;
    }

    try {
      const res = await fetch(`${API_URL}/api/match/run`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ sessionId, playerId, code }),
      });

      // Parse raw text so we can show backend message even on 400
      const raw = await res.text();
      let data = null;
      try {
        data = JSON.parse(raw);
      } catch {}

      if (!res.ok) {
        // Show the server's message: prefer `error`, then `output`, then raw
        const msg =
          (data && (data.error || data.output)) ||
          raw ||
          `Run failed (${res.status})`;
        alert(msg);
        console.error("Run failed:", { status: res.status, data, raw });
        return;
      }

      const out = typeof data?.output === "string" ? data.output : "";
      alert("Output:\n" + (out || "<no output>"));
    } catch (err) {
      console.error(err);
      alert("Network error calling /api/match/run");
    }
  };

  return (
    <div>
      <Editor
        height="450px"
        defaultLanguage="python"
        value={code}
        onChange={(value) => {
          if (typeof value === "string") setCode(value);
        }}
        theme="vs-dark"
        options={{ readOnly: readonly }}
      />
      {!readonly && (
        <button
          onClick={runCode}
          className="mt-2 p-2 bg-blue-500 text-white rounded"
        >
          Run Code
        </button>
      )}
    </div>
  );
};

export default CodeEditor;
