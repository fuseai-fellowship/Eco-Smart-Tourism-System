import React from "react";

const ItineraryCard = ({ dayPlan }) => {
  return (
    <div className="itinerary-card">
      <h4>Day {dayPlan.day}: {dayPlan.title}</h4>
      <ul>
        {dayPlan.activities.map((act, idx) => (
          <li key={idx}>{act}</li>
        ))}
      </ul>
    </div>
  );
};

export default ItineraryCard;
