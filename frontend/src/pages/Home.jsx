import React, { useState, useEffect } from "react";
import CodeEditor from "./CodeEditor";

const API_URL =
  (typeof import.meta !== "undefined" && import.meta.env?.VITE_API_URL) ||
  "http://127.0.0.1:5000";

const Home = () => {
  const [sessionId, setSessionId] = useState(
    localStorage.getItem("sessionId") || ""
  );
  const [playerId, setPlayerId] = useState(
    localStorage.getItem("playerId") || ""
  );
  const [playerName, setPlayerName] = useState("");
  const [player1Code, setPlayer1Code] = useState("# Player 1 code here");
  const [player2Code, setPlayer2Code] = useState("# Player 2 code here");
  const [joined, setJoined] = useState(false); // <- start on landing screen
  const [waiting, setWaiting] = useState(false);
  const [player1Name, setPlayer1Name] = useState("");
  const [player2Name, setPlayer2Name] = useState("");
  const [gameStatus, setGameStatus] = useState("active"); // "active" | "ended"
  const [winnerId, setWinnerId] = useState(null);
  const [round, setRound] = useState(1);
  const [liveRemaining, setLiveRemaining] = useState(0); // <— ADD: seconds shown on screen
  const [targetTs, setTargetTs] = useState(null);
  const mm = String(Math.floor(liveRemaining / 60)).padStart(2, "0");
  const ss = String(liveRemaining % 60).padStart(2, "0");

  // Create a new session (Player 1)
  const createSession = () => {
    if (!playerName.trim()) return alert("Enter your name");

    fetch(`${API_URL}/api/match/create`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ player1: playerName.trim() }),
    })
      .then((res) => res.json())
      .then((data) => {
        if (data.success) {
          setSessionId(data.sessionId);
          const player = (data.players || []).find(
            (p) => p?.name === playerName.trim()
          );
          if (player?.id) {
            setPlayerId(player.id);
            localStorage.setItem("sessionId", data.sessionId);
            localStorage.setItem("playerId", player.id);
          }
          setPlayer1Name(playerName.trim());
          setJoined(true);
          setWaiting(true); // P1 waits for P2
        } else if (data.error) {
          alert(data.error);
        }
      })
      .catch((err) => {
        console.error(err);
        alert("Failed to create session.");
      });
  };

  // Join an existing session (Player 2, via prompt as you had it)
  const joinSession = () => {
    if (!playerName.trim()) return alert("Enter your name");

    const id = prompt("Enter session ID to join:");
    if (!id) return;

    fetch(`${API_URL}/api/match/join`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        sessionId: id.trim(),
        playerName: playerName.trim(),
      }),
    })
      .then((res) => res.json())
      .then((data) => {
        if (data.success) {
          setSessionId(id.trim());
          setPlayerId(data.playerId);
          localStorage.setItem("sessionId", id.trim());
          localStorage.setItem("playerId", data.playerId);
          setPlayer2Name(playerName.trim());
          setJoined(true);
          setWaiting(false); // P2 is not waiting
        } else if (data.error) {
          alert(data.error);
        }
      })
      .catch((err) => {
        console.error(err);
        alert("Failed to join session. Try again.");
      });
  };

  const [roundsTotal, setRoundsTotal] = useState(5);
  const [problemMeta, setProblemMeta] = useState(null);
  const [championId, setChampionId] = useState(null);
  // Poll while joined (update names and P2 panel; clear waiting once P2 present)
  useEffect(() => {
    if (!sessionId || !joined) return;

    const interval = setInterval(() => {
      fetch(`${API_URL}/api/match/${sessionId}`)
        .then((res) => res.json())
        .then((data) => {
          const players = data?.players || [];
          const p1 = players[0];
          const p2 = players[1];

          // names
          setPlayer1Name(p1?.name || "");
          setPlayer2Name(p2?.name || "");

          // P2 code mirror + waiting state
          if (p2?.name) {
            setPlayer2Code(
              typeof p2?.code === "string" ? p2.code : "# Player 2 code here"
            );
            setWaiting(false);
          } else {
            setWaiting(true);
          }

          // status / winner / round / totals
          if (data?.status) setGameStatus(data.status);
          setWinnerId(data?.winnerId ?? null);
          setRound(data?.round ?? 1);
          setRoundsTotal(data?.roundsTotal ?? 5);
          setChampionId(data?.championId ?? null);

          // problem info (title/signature/statement/starter)
          if (data?.problem) {
            setProblemMeta(data.problem);
            // Seed starter code only when round is active AND your editor still has placeholder/empty
            if (data.status === "active" && data.problem.starter) {
              setPlayer1Code((prev) =>
                prev === "# Player 1 code here" || prev.trim() === ""
                  ? data.problem.starter
                  : prev
              );
            }
          }

          // timer sync
          if (data?.status === "active") {
            const rem = Number.isFinite(data?.remaining) ? data.remaining : 0;
            setLiveRemaining(rem);
            setTargetTs(Date.now() + rem * 1000); // smooth ticking between polls
          } else {
            setTargetTs(null);
            setLiveRemaining(0);
          }
        })
        .catch((err) => console.error(err));
    }, 1500);

    return () => clearInterval(interval);
  }, [sessionId, joined]);

  useEffect(() => {
    if (!joined || gameStatus !== "active" || !targetTs) return;
    const id = setInterval(() => {
      const secs = Math.max(0, Math.floor((targetTs - Date.now()) / 1000));
      setLiveRemaining(secs);
    }, 1000);
    return () => clearInterval(id);
  }, [joined, gameStatus, targetTs]);

  // LANDING: name + buttons (your original UX)
  if (!joined) {
    return (
      <div className="flex flex-col items-center justify-center min-h-screen space-y-4 p-4">
        <h1 className="text-3xl font-bold">Welcome to DSArena</h1>
        <input
          placeholder="Enter your name"
          value={playerName}
          onChange={(e) => setPlayerName(e.target.value)}
          className="p-2 border rounded w-full max-w-md"
        />
        <div className="flex gap-2">
          <button
            onClick={createSession}
            className="p-2 bg-blue-500 text-white rounded"
          >
            Create Session
          </button>
          <button
            onClick={joinSession}
            className="p-2 bg-green-500 text-white rounded"
          >
            Join Session
          </button>
        </div>
      </div>
    );
  }

  // WAITING screen (as you had it)
  if (joined && waiting) {
    return (
      <div className="flex flex-col items-center justify-center min-h-screen space-y-4">
        <h1 className="text-2xl font-bold">Waiting for Player 2 to join...</h1>
        <p>
          Share session ID: <span className="font-mono">{sessionId}</span>
        </p>
      </div>
    );
  }

  // MATCH COMPLETED screen (after round 5)
  if (joined && gameStatus === "completed") {
    const iAmChampion = championId && championId === playerId;
    return (
      <div className="flex flex-col items-center justify-center min-h-screen space-y-4 p-6">
        <h1
          className={`text-4xl font-extrabold ${
            iAmChampion ? "text-green-600" : "text-blue-600"
          }`}
        >
          Match Over –{" "}
          {iAmChampion ? "You’re the Champion! 🏆" : "Champion decided"}
        </h1>
        <div className="text-lg">Rounds: {roundsTotal}</div>
        <div className="text-sm text-gray-600">
          Session: <span className="font-mono">{sessionId}</span>
        </div>
        <button
          className="mt-4 px-4 py-2 border rounded"
          onClick={() => window.location.reload()}
        >
          Play Again (new session)
        </button>
      </div>
    );
  }

  // ROUND ENDED screen (between rounds 1..(total-1))
  if (joined && gameStatus === "ended") {
    const iWon = winnerId && winnerId === playerId;
    const isLastRound = round >= roundsTotal;

    const handleNextRound = () => {
      fetch(`${API_URL}/api/match/next-round`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ sessionId, playerId }),
      })
        .then((r) => r.json())
        .then((data) => {
          if (data.success) {
            // optimistic – poll will confirm
            setGameStatus("active");
            setWinnerId(null);
            setRound(data.round || round + 1);
            setPlayer1Code("# Player 1 code here");
            setPlayer2Code("# Player 2 code here");
          } else if (data.error) {
            alert(data.error);
          }
        })
        .catch(() => alert("Failed to start next round"));
    };

    return (
      <div className="flex flex-col items-center justify-center min-h-screen space-y-4 p-6">
        <h1
          className={`text-4xl font-extrabold ${
            iWon ? "text-green-600" : "text-red-600"
          }`}
        >
          {iWon ? "You Win! 🎉" : "You Lose 😔"}
        </h1>
        <div className="text-lg">
          Round {round} of {roundsTotal} finished.
        </div>
        <div className="text-sm text-gray-500">
          Session: <span className="font-mono">{sessionId}</span>
        </div>

        {!isLastRound ? (
          <button
            onClick={handleNextRound}
            className="mt-4 px-4 py-2 bg-blue-600 text-white rounded"
          >
            Start Next Round
          </button>
        ) : (
          <div className="mt-4 text-sm text-gray-600">
            Last round complete — awaiting final result…
          </div>
        )}
      </div>
    );
  }

  // MAIN ARENA (your original structure)
  return (
    <>
      <div className="border min-h-screen w-screen flex flex-col items-center p-4 space-y-6">
        <h1 className="text-3xl font-bold border-2 p-4 rounded">
          Welcome to DSArena!
        </h1>

        <div className="flex w-1/2 justify-between">
          <div className="flex-1 border-2 p-4 m-2 text-center rounded bg-blue-500 text-white">
            {player1Name || "Player 1"}
          </div>

          <div className="flex-1 border-2 p-4 m-2 text-center rounded bg-green-500 text-white">
            {player2Name || "Player 2"}
          </div>
        </div>

        {/* Round & Problem header */}
        <div className="w-full max-w-4xl space-y-2">
          <div className="flex items-center justify-between">
            <h2 className="text-xl font-semibold">
              Round {round} / {roundsTotal}
            </h2>
            {/* Live timer */}
            <div className="text-lg font-medium border-2 p-2 rounded">
              {(() => {
                const mm = String(Math.floor(liveRemaining / 60)).padStart(
                  2, 
                  "0"
                );
                const ss = String(liveRemaining % 60).padStart(2, "0");
                return `Timer: ${
                  gameStatus === "active" ? `${mm}:${ss}` : "00:00"
                }`;
              })()}
            </div>
          </div>
          {problemMeta && (
            <div className="border rounded p-3 text-left bg-gray-50">
              <div className="font-semibold">{problemMeta.title}</div>
              <div className="text-sm text-gray-700 mt-1">
                {problemMeta.statement}
              </div>
              <div className="text-sm font-mono mt-2">
                {problemMeta.signature}
              </div>
            </div>
          )}
        </div>

        <div className="flex w-full text-center border-2 justify-center">
          <div className="m-2 w-2/4">
            <CodeEditor
              code={player1Code}
              setCode={setPlayer1Code}
              sessionId={sessionId}
              playerId={playerId}
            />
          </div>
          <div className="m-2 w-2/4">
            <CodeEditor
              code={player2Code}
              setCode={() => {}}
              readonly={true}
              sessionId={sessionId}
              playerId={playerId}
            />
          </div>
        </div>
      </div>
    </>
  );
};

export default Home;
