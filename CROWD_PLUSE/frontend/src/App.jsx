import React, { useState, useEffect } from 'react';
import axios from 'axios';
import './App.css';

const API_URL = 'http://127.0.0.1:5000';

// --- Main App Component ---
function App() {
  const [task, setTask] = useState(null);
  const [analytics, setAnalytics] = useState(null);

  // Poll for status and fetch analytics when complete
  useEffect(() => {
    if (task && task.status === 'processing') {
      const interval = setInterval(async () => {
        try {
          const statusRes = await axios.get(`${API_URL}/api/status/${task.id}`);
          if (statusRes.data.status === 'complete') {
            setTask(statusRes.data);
            // Now fetch analytics data
            const analyticsRes = await axios.get(`${API_URL}/api/analytics/${task.id}`);
            setAnalytics(analyticsRes.data);
            clearInterval(interval);
          } else if (statusRes.data.status === 'failed') {
            setTask(statusRes.data);
            clearInterval(interval);
          }
        } catch (error) {
          console.error("Error polling for status:", error);
          clearInterval(interval);
        }
      }, 3000);
      return () => clearInterval(interval);
    }
  }, [task]);

  const handleNewTask = (newTask) => {
    setTask(newTask);
    setAnalytics(null); // Reset analytics for new task
  };

  return (
    <div className="app-container">
      <Navbar />
      <main className="main-content">
        <section className="video-section">
          {!task || task.status !== 'complete' ? (
            <FileUpload onNewTask={handleNewTask} taskStatus={task?.status} />
          ) : (
            <VideoPlayer videoPath={task.result_path} />
          )}
        </section>
        <aside className="analytics-sidebar">
          <AnalyticsPanel analytics={analytics} />
        </aside>
      </main>
    </div>
  );
}

// --- Child Components ---
const Navbar = () => (
  <header className="navbar">
    Crowd Analysis Dashboard
  </header>
);

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
    } catch (error) {
      console.error("Error uploading file:", error);
    }
  };

  return (
    <div className="upload-box">
      <h2>Analyze a New Video</h2>
      <form onSubmit={handleSubmit}>
        <input type="file" onChange={(e) => setSelectedFile(e.target.files[0])} accept="video/*" />
        <button type="submit">Upload & Analyze</button>
      </form>
      {taskStatus === 'processing' && <p>Processing, please wait...</p>}
      {taskStatus === 'failed' && <p>Processing failed.</p>}
    </div>
  );
};

const VideoPlayer = ({ videoPath }) => (
  <div className="video-player-box">
    <h2>Analysis Complete</h2>
    <video className="video-player" controls autoPlay muted loop>
      <source src={`${API_URL}/static/${videoPath}`} type="video/mp4" />
    </video>
  </div>
);

const AnalyticsPanel = ({ analytics }) => (
  <div className="analytics-box">
    <h2>Video Analytics</h2>
    {analytics ? (
      <>
        <MetricCard title="Peak Crowd Count" value={analytics.peak_count} />
        <MetricCard title="Average Crowd Count" value={analytics.average_count} />
        <MetricCard title="Total Frames Processed" value={analytics.total_frames} />
      </>
    ) : (
      <p>Upload a video to see analytics.</p>
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

