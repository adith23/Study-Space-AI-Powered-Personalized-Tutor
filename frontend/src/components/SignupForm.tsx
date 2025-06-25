import { useState } from "react";
import { signupUser } from "../services/auth";
import { useAuth } from "../contexts/AuthContext";
import { useNavigate } from "react-router-dom";

export default function SignupForm() {
  const { login } = useAuth();
  const navigate = useNavigate();
  const [form, setForm] = useState({ username: "", email: "", password: "" });
  const [error, setError] = useState<string | null>(null);

  const handleSignup = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    try {
      const res = await signupUser(form);
      login(res.access_token); // Auto-login after signup
      navigate("/");
    } catch (err: any) {
      setError(err.message || "Signup failed");
    }
  };

  return (
    <div className="max-w-sm mx-auto bg-white p-6 rounded-lg shadow-md">
      <h2 className="text-xl font-semibold mb-4">Signup</h2>
      {error && <div className="text-red-600 mb-2">{error}</div>}
      <form onSubmit={handleSignup}>
        <input
          type="text"
          placeholder="Username"
          className="w-full mb-3 px-4 py-2 border rounded"
          value={form.username}
          onChange={(e) => setForm({ ...form, username: e.target.value })}
          required
        />
        <input
          type="email"
          placeholder="Email"
          className="w-full mb-3 px-4 py-2 border rounded"
          value={form.email}
          onChange={(e) => setForm({ ...form, email: e.target.value })}
          required
        />
        <input
          type="password"
          placeholder="Password"
          className="w-full mb-3 px-4 py-2 border rounded"
          value={form.password}
          onChange={(e) => setForm({ ...form, password: e.target.value })}
          required
        />
        <button type="submit" className="w-full bg-green-600 text-white py-2 rounded hover:bg-green-700">
          Signup
        </button>
      </form>
    </div>
  );
}
