import React from 'react';
import './LandingPage.css';
import logo from './assets/logo.jpg'; 

// Using a placeholder URL for the logo to resolve asset path issues.


const LandingPage = ({ onGetStarted }) => {
  return (
    <div className="landing-container">
      <header className="landing-header">
        <img src={logo} alt="Crowd Pulse Logo" className="logo" />
        <h1 className="main-title">Crowd Pulse</h1>
      </header>

      <main className="landing-main">
        <section className="features-section">
          <h2>Key Features</h2>
          <div className="features-grid">
            <div className="feature-card">
              <h3>Live Video Analysis</h3>
              <p>Monitor live feeds from webcams or CCTV for instant crowd counting and tracking.</p>
            </div>
            <div className="feature-card">
              <h3>Upload & Process</h3>
              <p>Analyze pre-recorded video files to extract detailed crowd analytics and insights.</p>
            </div>
            <div className="feature-card">
              <h3>Intelligent Insights</h3>
              <p>Get key metrics like peak and average crowd sizes to make informed decisions.</p>
            </div>
          </div>
        </section>

        <section className="cta-section">
          <button className="cta-button" onClick={onGetStarted}>
            Get Started
          </button>
        </section>
      </main>

      <footer className="landing-footer">
        <p>&copy; 2025 Crowd Pulse. All Rights Reserved.</p>
      </footer> 
    </div>
  );
};

export default LandingPage;