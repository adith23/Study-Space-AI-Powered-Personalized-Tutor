import { AuthProvider } from "./contexts/AuthContext";
import { useAuth } from "./contexts/AuthContext";
import { useEffect } from "react";
import { setAuthToken } from "./lib/api";
import LoginForm from "./components/LoginForm";
import SignupForm from "./components/SignupForm";
import Home from "./pages/home";
import { BrowserRouter as Router, Routes, Route, Navigate } from "react-router-dom";

function AppContent() {
  const { token } = useAuth();

  useEffect(() => {
    setAuthToken(token);
  }, [token]);

  return (
    <Router>
      <div className="p-6">
        <h1 className="text-2xl font-bold mb-8">Study Space</h1>
        <Routes>
          <Route path="/" element={token ? <Home /> : <Navigate to="/login" />} />
          <Route path="/login" element={!token ? <LoginForm /> : <Navigate to="/" />} />
          <Route path="/signup" element={!token ? <SignupForm /> : <Navigate to="/" />} />
        </Routes>
      </div>
    </Router>
  );
}

function App() {
  return (
    <AuthProvider>
        <AppContent />
    </AuthProvider>
  );
}

export default App;
