import React, { useState, useRef, useEffect } from "react";
import ChatMessage from "./ChatMessage";
import ItineraryCard from "./ItineraryCard";

const Chat = () => {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const chatWindowRef = useRef(null);

  // Scroll to bottom whenever messages change
  useEffect(() => {
    if (chatWindowRef.current) {
      chatWindowRef.current.scrollTop = chatWindowRef.current.scrollHeight;
    }
  }, [messages]);

  const handleSend = async () => {
    if (!input.trim()) return;

    const userMessage = input.trim();
    setMessages([...messages, { message: userMessage, isUser: true }]);
    setInput("");
    setLoading(true);

    try {
      const response = await fetch("http://127.0.0.1:8000/api/predict/", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ user_input: userMessage }),
      });
      const data = await response.json();
      const itinerary = data.itinerary;

      if (itinerary) {
        const formattedMessage = (
          <div className="itinerary">
            <h3>{itinerary.result.itinerary.summary}</h3>
            <p><strong>Duration:</strong> {itinerary.result.itinerary.duration}</p>
            <p><strong>Destinations:</strong> {itinerary.result.itinerary.destinations.join(", ")}</p>

            <h4>Daily Plan:</h4>
            {itinerary.result.itinerary.daily_plan.map((dayPlan) => (
              <ItineraryCard key={dayPlan.day} dayPlan={dayPlan} />
            ))}

            <h4>Budget:</h4>
            <p>{itinerary.result.itinerary.budget.description} ({itinerary.result.itinerary.budget.total})</p>

            <h4>Travel Tips:</h4>
            <ul>
              {itinerary.result.itinerary.travel_tips.map((tip, idx) => <li key={idx}>{tip}</li>)}
            </ul>

            <h4>Recommendations:</h4>
            <ul>
              {itinerary.result.itinerary.recommendations.map((rec, idx) => <li key={idx}>{rec}</li>)}
            </ul>
          </div>
        );

        setMessages((prev) => [...prev, { message: formattedMessage, isUser: false }]);
      } else {
        setMessages((prev) => [...prev, { message: "No itinerary generated.", isUser: false }]);
      }

    } catch (err) {
      setMessages((prev) => [...prev, { message: "Error connecting to server", isUser: false }]);
      console.error(err);
    }

    setLoading(false);
  };

  const handleKeyPress = (e) => {
    if (e.key === "Enter") handleSend();
  };

  return (
    <div className="chat-container">
      <div className="chat-window" ref={chatWindowRef}>
        {messages.map((msg, idx) => (
          <ChatMessage key={idx} message={msg.message} isUser={msg.isUser} />
        ))}
        {loading && <div className="message bot">Loading...</div>}
      </div>
      <div className="chat-input">
        <input
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyPress={handleKeyPress}
          placeholder="Ask for a travel itinerary..."
        />
        <button onClick={handleSend}>Send</button>
      </div>
    </div>
  );
};

export default Chat;
