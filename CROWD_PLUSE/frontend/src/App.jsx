import { useState, useEffect } from 'react';
import axios from 'axios';
import { io } from 'socket.io-client';
import './App.css';
import LoginPage from './loginpage';
import LandingPage from './LandingPage';

const API_URL = 'http://127.0.0.1:5000';

// --- Main App Component ---
function App() {
  const [appState, setAppState] = useState('landing'); // 'landing', 'login', 'dashboard'

  const handleLoginSuccess = () => {
    setAppState('dashboard');
  };

  const handleLogout = () => {
    setAppState('landing');
  };

  // The main dashboard layout
  if (appState === 'dashboard') {
    return (
      <div className="app-container">
        <Dashboard onLogout={handleLogout} />
      </div>
    );
  }

  // The landing page (manages its own full-screen layout)
  if (appState === 'landing') {
    return <LandingPage onGetStarted={() => setAppState('login')} />;
  }

  // The login page (needs to be centered)
  if (appState === 'login') {
    return (
      <div className="fullscreen-container">
        <LoginPage onLoginSuccess={handleLoginSuccess} />
      </div>
    );
  }

  return null; 
}


const Dashboard = ({ onLogout }) => {
  const [task, setTask] = useState(null);
  const [analytics, setAnalytics] = useState(null);
  const [liveCount, setLiveCount] = useState(0);

  // Poll for status and fetch analytics when complete
  useEffect(() => {
    if (task && task.status === 'processing') {
      const interval = setInterval(async () => {
        try {
          const statusRes = await axios.get(`${API_URL}/api/status/${task.id}`);
          if (statusRes.data.status === 'complete') {
            setTask(statusRes.data);
            const analyticsRes = await axios.get(`${API_URL}/api/analytics/${task.id}`);
            setAnalytics(analyticsRes.data);
            clearInterval(interval);
          } else if (statusRes.data.status === 'failed') {
            setTask(statusRes.data);
            clearInterval(interval);
          }
        } catch (error) {
          console.error("Error polling for status:", error);
          setTask({ status: 'failed' });
          clearInterval(interval);
        }
      }, 3000);
      return () => clearInterval(interval);
    }
  }, [task]);

  // Connect to WebSocket for live updates
  useEffect(() => {
    const socket = io(API_URL);
    socket.on('live_update', (data) => setLiveCount(data.count));
    return () => socket.disconnect();
  }, []);

  const handleNewTask = (newTask) => {
    setTask(newTask);
    setAnalytics(null);
    setLiveCount(0);
  };

  const handleReset = () => {
    setTask(null);
    setAnalytics(null);
    setLiveCount(0);
  };

  return (
    <>
      <Navbar onReset={handleReset}  onLogout={onLogout}/>
      <main className="main-content">
        <section className="video-section">
          {!task || task.status !== 'complete' ? (
            <FileUpload onNewTask={handleNewTask} taskStatus={task?.status} />
          ) : (
            <VideoPlayer videoPath={task.result_path} onReset={handleReset} />
          )}
        </section>
        <aside className="analytics-sidebar">
          <AnalyticsPanel analytics={analytics} liveCount={liveCount} taskStatus={task?.status} onReset={handleReset}/>
        </aside>
      </main>
    </>
  );
};

const Navbar = ({ onReset, onLogout }) => {
  const [showLogoutModal, setShowLogoutModal] = useState(false);

  return (
    <>
      <header className="navbar">
        <span onClick={onReset} style={{ cursor: 'pointer' }}>Dashboard</span>
        <div className="user-icon-container" onClick={() => setShowLogoutModal(true)}>
          <svg className="user-icon" xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24"><path d="M12 12c2.21 0 4-1.79 4-4s-1.79-4-4-4-4 1.79-4 4 1.79 4 4 4zm0 2c-2.67 0-8 1.34-8 4v2h16v-2c0-2.66-5.33-4-8-4z"/></svg>
        </div>
      </header>
      {showLogoutModal && (
        <LogoutModal onConfirm={onLogout} onCancel={() => setShowLogoutModal(false)} />
      )}
    </>
  );
};

const LogoutModal = ({ onConfirm, onCancel }) => {
  return (
    <div className="modal-overlay">
      <div className="modal-box">
        <h2>Confirm Logout</h2>
        <p>Are you sure you want to log out of the current session?</p>
        <div className="modal-buttons">
          <button className="modal-button cancel" onClick={onCancel}>Cancel</button>
          <button className="modal-button confirm" onClick={onConfirm}>Logout</button>
        </div>
      </div>
    </div>
  );
};

const FileUpload = ({ onNewTask, taskStatus }) => {
  const [selectedFile, setSelectedFile] = useState(null);

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!selectedFile) return;
    const formData = new FormData();
    formData.append('video', selectedFile);
    try {
      const res = await axios.post(`${API_URL}/api/upload`, formData);
      onNewTask({ id: res.data.task_id, status: 'processing' });
    } catch (error) { console.error("Error uploading file:", error); }
  };

  return (
    <div className="upload-box">
      <h2>Analyze a New Video</h2>
      <form onSubmit={handleSubmit}>
        <input type="file" onChange={(e) => setSelectedFile(e.target.files[0])} accept="video/*" />
        <button type="submit">Upload & Analyze</button>
      </form>
      {taskStatus === 'processing' && <p>Processing, please wait... Live count is in the sidebar.</p>}
      {taskStatus === 'failed' && <p className="error-message">Processing failed. Please try another video.</p>}
    </div>
  );
};

const VideoPlayer = ({ videoPath, onReset }) => (
  <div className="video-player-box">
    <video className="video-player" controls autoPlay muted loop>
      <source src={`${API_URL}/static/${videoPath}`} type="video/mp4" />
    </video>
  </div>
);

const AnalyticsPanel = ({ analytics, liveCount, taskStatus, onReset }) => (
  <div className="analytics-box">
    {taskStatus === 'complete' ? (
      <div className="analysis-complete-section">
        <h2>Analysis Complete</h2>
        <button className="reset-button" onClick={onReset}>Analyze Another Video</button>
      </div>
    ) : (
      <h2>Video Analytics</h2>
    )}
    <MetricCard title="Live Crowd Count" value={liveCount} />
    {analytics ? (
      <>
        <MetricCard title="Peak Crowd Count" value={analytics.peak_count} />
        <MetricCard title="Average Crowd Count" value={analytics.average_count} />
      </>
    ) : (
      <p className="placeholder-text">Final analytics will appear here after processing is complete.</p>
    )}
  </div>
);

const MetricCard = ({ title, value }) => (
  <div className="metric-card">
    <h3>{title}</h3>
    <p>{value}</p>
  </div>
);

export default App;